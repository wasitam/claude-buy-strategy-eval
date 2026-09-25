"""Family 017: RSI2 short-horizon mean-reversion sizing (Connors & Alvarez 2009).

families/017-rsi2-reversion/prereg.md has the full mechanism and rules.
Summary: each asset's OWN short-horizon (2-4 day) RSI oscillator, computed
purely from that asset's own daily Close series (no external data), flags
a short-term oversold state (RSI below oversold_threshold -- a recent run
of down-days) or overbought state (RSI above overbought_threshold -- a
recent run of up-days). Deposits are sized UP on an oversold week (lean
into the short-term dip, cash-capped) and sized DOWN on an overbought week
(bank the remainder as cash to fund a future oversold week). This is
deliberately a SHORT-HORIZON, per-asset, mean-reversion signal -- see
prereg.md's "Rigorous triple distinction" section for the explicit
non-re-test case against family 016 (shared VIX), family 003 (realized
variance) and families 001/005 (long-horizon trend-following). No sells,
ever; no leverage; cash never goes negative.

Category: Sizing / valuation.

Parameters (4 tunable + 1 fixed, all <=5):
  rsi_period            -- trailing window (trading days) for the RSI calc
  oversold_threshold    -- RSI below this = oversold, buy more
  overbought_threshold  -- RSI above this = overbought, buy less
  buy_mult_oversold     -- multiple of weekly_deposit bought when oversold
  buy_mult_overbought   -- fixed at 0.5 (not grid-varied), fraction of
                            weekly_deposit still bought on an overbought week
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_rsi(daily: pd.DataFrame, rsi_period: int) -> np.ndarray:
    """Causal (no-lookahead) simple (non-Wilder-smoothed) rolling-average
    gain/loss RSI, using only data through each day's own close. NaN until
    rsi_period+1 closes exist. See prereg.md for the exact edge-case rules
    (avg_loss=0 -> RSI=100; avg_gain=avg_loss=0 -> RSI=50)."""
    close = daily["Close"].to_numpy(dtype=float)
    n = len(close)
    delta = np.diff(close, prepend=np.nan)
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    gain[0] = np.nan
    loss[0] = np.nan

    rsi = np.full(n, np.nan)
    for t in range(rsi_period, n):
        window_gain = gain[t - rsi_period + 1: t + 1]
        window_loss = loss[t - rsi_period + 1: t + 1]
        if np.any(np.isnan(window_gain)):
            continue
        avg_gain = float(np.mean(window_gain))
        avg_loss = float(np.mean(window_loss))
        if avg_loss == 0.0 and avg_gain == 0.0:
            rsi[t] = 50.0
        elif avg_loss == 0.0:
            rsi[t] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[t] = 100.0 - 100.0 / (1.0 + rs)
    return rsi


def compute_state(daily: pd.DataFrame, rsi_period: int, oversold_threshold: float,
                   overbought_threshold: float) -> np.ndarray:
    """Returns an array of strings: 'oversold', 'overbought', or 'normal'
    (also 'normal' during warm-up, before RSI is defined -- matches every
    prior family's warm-up convention of defaulting to plain-DCA behavior)."""
    rsi = compute_rsi(daily, rsi_period)
    state = np.full(len(rsi), "normal", dtype=object)
    valid = ~np.isnan(rsi)
    state[valid & (rsi < oversold_threshold)] = "oversold"
    state[valid & (rsi > overbought_threshold)] = "overbought"
    return state


def make_rsi2_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    rsi_period: int = 2, oversold_threshold: float = 10.0,
    overbought_threshold: float = 90.0, buy_mult_oversold: float = 2.0,
    buy_mult_overbought: float = 0.5,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the RSI computation entirely and buys
    the full week's cash every week-end day (0 otherwise), which is
    bit-for-bit plain DCA."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)
    state = compute_state(daily, rsi_period, oversold_threshold, overbought_threshold) if enabled else None

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        st = state[t]
        if st == "oversold":
            target_buy_usd = min(cash, buy_mult_oversold * weekly_deposit)
        elif st == "overbought":
            target_buy_usd = buy_mult_overbought * weekly_deposit
        else:
            target_buy_usd = weekly_deposit
        return target_buy_usd, 0.0, {"rsi_state": st}

    return decide


def make_decider_from_state(
    daily: pd.DataFrame, weekly_deposit: float, state: np.ndarray,
    buy_mult_oversold: float = 2.0, buy_mult_overbought: float = 0.5,
):
    """Same weekly decision rule as make_rsi2_decider, but driven by an
    arbitrary pre-computed `state` array -- used by the placebo
    circular-shift robustness test (sec 4.3), which shifts the signal's
    TIMING while keeping its overall oversold/overbought/normal frequency
    identical."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)

    def decide(t, cash):
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        st = state[t]
        if st == "oversold":
            target_buy_usd = min(cash, buy_mult_oversold * weekly_deposit)
        elif st == "overbought":
            target_buy_usd = buy_mult_overbought * weekly_deposit
        else:
            target_buy_usd = weekly_deposit
        return target_buy_usd, 0.0, {"rsi_state": st}

    return decide


CATEGORY = "Sizing / valuation"

# Grid: rsi_period x oversold_threshold x overbought_threshold x
# buy_mult_oversold = 3x2x2x2 = 24 (<=36 cap; buy_mult_overbought fixed at
# 0.5, not grid-varied)
GRID = {
    "rsi_period": [2, 3, 4],
    "oversold_threshold": [10.0, 15.0],
    "overbought_threshold": [85.0, 90.0],
    "buy_mult_oversold": [1.5, 2.0],
}
BUY_MULT_OVERBOUGHT = 0.5
PRIMARY_CONFIG = {
    "rsi_period": 2, "oversold_threshold": 10.0, "overbought_threshold": 90.0,
    "buy_mult_oversold": 2.0, "buy_mult_overbought": BUY_MULT_OVERBOUGHT,
}


def grid_configs() -> list[dict]:
    out = []
    for rp in GRID["rsi_period"]:
        for ot in GRID["oversold_threshold"]:
            for obt in GRID["overbought_threshold"]:
                for bmo in GRID["buy_mult_oversold"]:
                    out.append({
                        "rsi_period": rp, "oversold_threshold": ot,
                        "overbought_threshold": obt, "buy_mult_oversold": bmo,
                        "buy_mult_overbought": BUY_MULT_OVERBOUGHT,
                    })
    return out
