"""NAV series and metrics per spec v2 section 8."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import brentq

WEEKS_PER_YEAR = 52.0


def nav_series(V: np.ndarray, deposit: np.ndarray) -> np.ndarray:
    """r_t = V_t / (V_{t-1} + D_{t-1}) - 1 ;  NAV_t = NAV_{t-1} * (1 + r_t), NAV_0 = 1
    (spec 8.1). V_t is account value at close of week t, before that week's deposit."""
    n = len(V)
    nav = np.ones(n)
    for t in range(1, n):
        denom = V[t - 1] + deposit[t - 1]
        r = (V[t] / denom - 1.0) if denom > 1e-9 else 0.0
        nav[t] = nav[t - 1] * (1.0 + r)
    return nav


def max_drawdown(nav: np.ndarray) -> tuple[float, int]:
    nav_s = pd.Series(nav)
    running_max = nav_s.cummax()
    dd = nav_s / running_max - 1.0
    max_dd = float(dd.min())
    underwater = dd < -1e-9
    longest = cur = 0
    for uw in underwater:
        cur = cur + 1 if uw else 0
        longest = max(longest, cur)
    return max_dd, longest


def cagr(nav: np.ndarray) -> float:
    n_weeks = len(nav) - 1
    if n_weeks <= 0 or nav[0] <= 0 or nav[-1] <= 0:
        return float("nan")
    years = n_weeks / WEEKS_PER_YEAR
    return float((nav[-1] / nav[0]) ** (1.0 / years) - 1.0)


def annualized_vol(nav: np.ndarray) -> float:
    r = pd.Series(nav).pct_change().dropna()
    return float(r.std() * np.sqrt(WEEKS_PER_YEAR))


def sharpe(nav: np.ndarray, weekly_rf: np.ndarray) -> float:
    r = pd.Series(nav).pct_change().dropna()
    rf = pd.Series(weekly_rf).reindex(r.index).fillna(0.0)
    excess = r - rf
    if excess.std() == 0 or len(excess) == 0:
        return float("nan")
    return float(excess.mean() / excess.std() * np.sqrt(WEEKS_PER_YEAR))


def sortino(nav: np.ndarray, weekly_rf: np.ndarray) -> float:
    r = pd.Series(nav).pct_change().dropna()
    rf = pd.Series(weekly_rf).reindex(r.index).fillna(0.0)
    excess = r - rf
    downside = excess[excess < 0]
    dd_std = downside.std()
    if not dd_std or np.isnan(dd_std) or dd_std == 0:
        return float("nan")
    return float(excess.mean() / dd_std * np.sqrt(WEEKS_PER_YEAR))


def calmar(nav: np.ndarray) -> float:
    c = cagr(nav)
    dd, _ = max_drawdown(nav)
    if not dd:
        return float("nan")
    return float(c / abs(dd))


def xirr(dates: list, amounts: list) -> float | None:
    d0 = dates[0]
    t = np.array([(d - d0).days / 365.0 for d in dates])
    amt = np.array(amounts, dtype=float)

    def npv(r):
        return np.sum(amt / (1.0 + r) ** t)

    try:
        return brentq(npv, -0.999999, 50.0, maxiter=200)
    except ValueError:
        return None


def avg_cost_per_unit(buy_usd: np.ndarray, closes: np.ndarray, fee: float = 0.001) -> float:
    """Dollar-weighted average price paid per unit across all buys, filled at
    the FOLLOWING week's open in the real engine -- here approximated using
    the signal week's close as a stand-in for reporting purposes is avoided;
    callers should pass the actual fill prices instead. See summarize()."""
    mask = buy_usd > 0
    if not mask.any():
        return float("nan")
    gross_units = (buy_usd[mask] * (1 - fee)) / closes[mask]
    return float(buy_usd[mask].sum() / gross_units.sum())


def summarize(result_df: pd.DataFrame, weekly_rf: pd.Series, final_close: float) -> dict:
    """result_df: output of EngineResult.to_frame(). final_close: last week's
    close price, used to mark remaining units to market for final wealth."""
    V = result_df["V"].to_numpy()
    deposit = result_df["deposit"].to_numpy()
    nav = nav_series(V, deposit)
    total_invested = float(result_df["invested"].iloc[-1])
    final_wealth = float(result_df["cash"].iloc[-1] + result_df["units"].iloc[-1] * final_close)
    max_dd, longest_uw = max_drawdown(nav)
    rf = weekly_rf.reindex(result_df.index).fillna(0.0).to_numpy()

    avg_cash_share = float((result_df["cash"] / result_df["V"].clip(lower=1e-9)).clip(0, 1).mean())

    filled = result_df[result_df["fill_buy_units"] > 0]
    avg_cost_per_unit = (
        float(filled["fill_buy_usd"].sum() / filled["fill_buy_units"].sum())
        if len(filled) else float("nan")
    )

    n_buys = int((result_df["buy_usd"] > 0).sum())
    n_sells = int((result_df["sell_usd"] > 0).sum())
    total_fees = float(result_df["fees_paid"].sum())

    return {
        "total_invested": total_invested,
        "final_wealth": final_wealth,
        "wealth_over_invested": final_wealth / total_invested if total_invested else float("nan"),
        "nav": nav,
        "max_drawdown": max_dd,
        "longest_weeks_underwater": longest_uw,
        "cagr": cagr(nav),
        "annualized_vol": annualized_vol(nav),
        "sharpe": sharpe(nav, rf),
        "sortino": sortino(nav, rf),
        "calmar": calmar(nav),
        "n_buys": n_buys,
        "n_sells": n_sells,
        "total_fees": total_fees,
        "avg_cash_share": avg_cash_share,
        "avg_cost_per_unit": avg_cost_per_unit,
    }


def summarize_portfolio(result_df: pd.DataFrame, weekly_rf: pd.Series) -> dict:
    """result_df: output of rebalance.run_portfolio()."""
    V = result_df["V"].to_numpy()
    deposit = result_df["deposit"].to_numpy()
    nav = nav_series(V, deposit)
    total_invested = float(result_df["invested"].iloc[-1])
    final_wealth = float(result_df["total_value"].iloc[-1])
    max_dd, longest_uw = max_drawdown(nav)
    rf = weekly_rf.reindex(result_df.index).fillna(0.0).to_numpy()

    return {
        "total_invested": total_invested,
        "final_wealth": final_wealth,
        "wealth_over_invested": final_wealth / total_invested if total_invested else float("nan"),
        "nav": nav,
        "max_drawdown": max_dd,
        "longest_weeks_underwater": longest_uw,
        "cagr": cagr(nav),
        "annualized_vol": annualized_vol(nav),
        "sharpe": sharpe(nav, rf),
        "sortino": sortino(nav, rf),
        "calmar": calmar(nav),
        "n_rebalances": int(result_df["rebalanced"].sum()),
        "total_fees": float(result_df["fees_paid"].sum()),
        "avg_cash_share": float((result_df["cash"] / result_df["total_value"].clip(lower=1e-9)).clip(0, 1).mean()),
    }
