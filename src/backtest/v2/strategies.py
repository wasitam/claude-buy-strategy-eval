"""Strategy A (SmartDCA) and Strategy B (ADCA), plus plain DCA -- spec v2 sections 4, 5, 7.

Each strategy precomputes its causal indicator series vectorized (fast), then
returns a `decide` closure the engine calls once per week with the live cash
balance (the only genuinely path-dependent piece, e.g. SmartDCA's sweep).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Strategy A: SmartDCA
# ---------------------------------------------------------------------------

def smartdca_multiplier(weekly: pd.DataFrame, rho: float, m_max: float) -> np.ndarray:
    """mult_t = min((MA52_t / close_t) ** rho, m_max), causal (MA52 uses data
    through week t)."""
    close = weekly["Close"]
    ma52 = close.rolling(52, min_periods=52).mean()
    ratio = (ma52 / close).clip(lower=1e-6)
    mult = np.power(ratio, rho)
    mult = mult.clip(upper=m_max)
    mult = mult.fillna(1.0)  # before 52 weeks of history, behave like plain DCA
    return mult.to_numpy()


def make_smartdca_decider(weekly: pd.DataFrame, weekly_deposit: float, rho: float, m_max: float, sweep_on: bool):
    mult = smartdca_multiplier(weekly, rho, m_max)
    sweep_cap = 26 * weekly_deposit

    def decide(t: int, cash_after_deposit: float):
        buy_usd = min(weekly_deposit * mult[t], cash_after_deposit)
        if sweep_on:
            excess = (cash_after_deposit - buy_usd) - sweep_cap
            if excess > 0:
                buy_usd += excess
        return buy_usd, 0.0, {"mult": mult[t]}

    return decide


# ---------------------------------------------------------------------------
# Strategy B: ADCA
# ---------------------------------------------------------------------------

def adca_regime_score_b1(weekly: pd.DataFrame, vix_weekly: pd.Series, unrate_weekly: pd.Series,
                          tcu_weekly: pd.Series) -> np.ndarray:
    idx = weekly.index
    vix = vix_weekly.reindex(idx).ffill()
    vote1 = vix < vix.rolling(52, min_periods=52).median()

    # UNRATE/TCU are monthly, forward-filled to weekly; "last 12 available monthly
    # values" (spec 5) is approximated as a trailing 52-week mean on that
    # forward-filled weekly series (~12 months).
    unrate = unrate_weekly.reindex(idx).ffill()
    unrate_ma12 = unrate.rolling(52, min_periods=52).mean()
    vote2 = unrate < unrate_ma12

    tcu = tcu_weekly.reindex(idx).ffill()
    tcu_ma12 = tcu.rolling(52, min_periods=52).mean()
    vote3 = tcu > tcu_ma12

    score = vote1.astype(int).fillna(0) + vote2.astype(int).fillna(0) + vote3.astype(int).fillna(0)
    # Until all three inputs have enough history, default to neutral (score=2)
    warm = vix.rolling(52, min_periods=52).mean().notna() & unrate_ma12.notna() & tcu_ma12.notna()
    score = score.where(warm, 2)
    return score.to_numpy()


def adca_regime_score_b2(weekly: pd.DataFrame, vix_weekly: pd.Series) -> np.ndarray:
    idx = weekly.index
    close = weekly["Close"]
    vix = vix_weekly.reindex(idx).ffill()
    vote1 = vix < vix.rolling(52, min_periods=52).median()

    log_ret = np.log(close).diff()
    vol26 = log_ret.rolling(26, min_periods=26).std()
    vol26_median_156 = vol26.rolling(156, min_periods=52).median()  # expanding-ish, min 52 per spec 2.4
    vote2 = vol26 < vol26_median_156

    sma40 = close.rolling(40, min_periods=40).mean()
    vote3 = close > sma40

    score = vote1.astype(int).fillna(0) + vote2.astype(int).fillna(0) + vote3.astype(int).fillna(0)
    warm = vix.rolling(52, min_periods=52).mean().notna() & vol26_median_156.notna() & sma40.notna()
    score = score.where(warm, 2)
    return score.to_numpy()


def make_adca_decider(weekly_deposit: float, score: np.ndarray):
    def decide(t: int, cash_after_deposit: float):
        s = score[t]
        if s == 3:
            buy_usd = min(cash_after_deposit, weekly_deposit + 0.25 * (cash_after_deposit - weekly_deposit))
        elif s == 2:
            buy_usd = min(cash_after_deposit, weekly_deposit)
        else:
            buy_usd = min(cash_after_deposit, weekly_deposit * 0.5)
        return max(buy_usd, 0.0), 0.0, {"score": s}

    return decide


# ---------------------------------------------------------------------------
# Plain DCA (benchmark for A and B)
# ---------------------------------------------------------------------------

def make_dca_decider(weekly_deposit: float):
    def decide(t: int, cash_after_deposit: float):
        return min(cash_after_deposit, weekly_deposit), 0.0, {}

    return decide
