"""Performance, risk, and risk-adjusted metrics (spec section 6)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import brentq

WEEKS_PER_YEAR = 52.0


def xirr(cashflow_dates: list, cashflow_amounts: list) -> float | None:
    """Money-weighted annualized return solved from irregular cash flows.
    Convention: outflows (money the investor puts in) are negative, the
    terminal liquidation value is positive."""
    d0 = cashflow_dates[0]
    t = np.array([(d - d0).days / 365.0 for d in cashflow_dates])
    amt = np.array(cashflow_amounts, dtype=float)

    def npv(r):
        return np.sum(amt / (1.0 + r) ** t)

    try:
        return brentq(npv, -0.999999, 50.0, maxiter=200)
    except ValueError:
        return None


def max_drawdown(nav: pd.Series) -> tuple[float, int]:
    """Returns (max_drawdown_fraction, longest_weeks_underwater)."""
    running_max = nav.cummax()
    dd = nav / running_max - 1.0
    max_dd = dd.min()

    underwater = dd < -1e-9
    longest = 0
    cur = 0
    for uw in underwater:
        if uw:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0
    return float(max_dd), longest


def max_underwater_vs_money_in(total_value: pd.Series, invested: pd.Series) -> float:
    """Peak-to-trough of (value - cumulative invested), as a fraction of the
    peak of that series (or in dollars if peak <= 0)."""
    surplus = total_value - invested
    running_max = surplus.cummax()
    drawdown = surplus - running_max
    return float(drawdown.min())


def annualized_vol(nav: pd.Series) -> float:
    r = nav.pct_change().dropna()
    return float(r.std() * np.sqrt(WEEKS_PER_YEAR))


def sharpe_ratio(nav: pd.Series, weekly_rf: pd.Series) -> float:
    r = nav.pct_change().dropna()
    rf = weekly_rf.reindex(r.index).fillna(0.0)
    excess = r - rf
    if excess.std() == 0 or len(excess) == 0:
        return float("nan")
    return float(excess.mean() / excess.std() * np.sqrt(WEEKS_PER_YEAR))


def sortino_ratio(nav: pd.Series, weekly_rf: pd.Series) -> float:
    r = nav.pct_change().dropna()
    rf = weekly_rf.reindex(r.index).fillna(0.0)
    excess = r - rf
    downside = excess[excess < 0]
    dd_std = downside.std()
    if not dd_std or np.isnan(dd_std) or dd_std == 0:
        return float("nan")
    return float(excess.mean() / dd_std * np.sqrt(WEEKS_PER_YEAR))


def annualized_return(nav: pd.Series) -> float:
    n_weeks = len(nav) - 1
    if n_weeks <= 0 or nav.iloc[0] <= 0:
        return float("nan")
    total_return = nav.iloc[-1] / nav.iloc[0]
    years = n_weeks / WEEKS_PER_YEAR
    if total_return <= 0 or years <= 0:
        return float("nan")
    return float(total_return ** (1.0 / years) - 1.0)


def calmar_ratio(nav: pd.Series) -> float:
    ann_ret = annualized_return(nav)
    max_dd, _ = max_drawdown(nav)
    if max_dd == 0 or np.isnan(max_dd):
        return float("nan")
    return float(ann_ret / abs(max_dd))


def avg_cost_basis(result: pd.DataFrame, weekly: pd.DataFrame, buy_amount: float = 500.0) -> float:
    """Average $ paid per unit across all buys (dollars spent / gross units bought,
    i.e. NOT netting out later sells)."""
    trades = result["trade"].fillna("")
    buy_weeks = trades.str.contains("BUY")
    if buy_weeks.sum() == 0:
        return float("nan")
    prices = weekly.loc[buy_weeks, "Open"]
    gross_units = (buy_amount * 0.999) / prices  # net of the 0.1% fee, same as the engine
    total_spent = buy_amount * buy_weeks.sum()
    total_units = gross_units.sum()
    return float(total_spent / total_units) if total_units > 0 else float("nan")


def summarize(
    result: pd.DataFrame,
    weekly: pd.DataFrame,
    weekly_rf: pd.Series,
    buy_amount: float = 500.0,
) -> dict:
    nav = result["nav"]
    invested = result["invested"]
    total_value = result["total_value"]
    ending_wealth = float(total_value.iloc[-1])
    total_invested = float(invested.iloc[-1])

    # XIRR from actual buy cash flows + terminal value
    trades = result["trade"].fillna("")
    buy_dates = result.index[trades.str.contains("BUY")]
    dates = list(buy_dates) + [result.index[-1]]
    amounts = [-buy_amount] * len(buy_dates) + [ending_wealth]
    xirr_val = xirr([d.to_pydatetime() for d in dates], amounts) if len(buy_dates) > 0 else None

    max_dd, longest_uw = max_drawdown(nav)

    return {
        "ending_wealth": ending_wealth,
        "total_invested": total_invested,
        "wealth_over_invested": ending_wealth / total_invested if total_invested else float("nan"),
        "xirr": xirr_val,
        "max_drawdown": max_dd,
        "longest_weeks_underwater": longest_uw,
        "max_underwater_vs_money_in": max_underwater_vs_money_in(total_value, invested),
        "annualized_vol": annualized_vol(nav),
        "sharpe": sharpe_ratio(nav, weekly_rf),
        "sortino": sortino_ratio(nav, weekly_rf),
        "calmar": calmar_ratio(nav),
        "annualized_return": annualized_return(nav),
        "avg_cost_basis": avg_cost_basis(result, weekly, buy_amount) if "trade" in result.columns else float("nan"),
        "n_buys": result.attrs.get("n_buys", int(trades.str.contains("BUY").sum())),
        "n_sells": result.attrs.get("n_sells", int(trades.str.contains("SELL").sum())),
    }


def signal_forward_returns(
    weekly: pd.DataFrame, signal_bool: pd.Series, horizons_months: tuple[int, ...] = (1, 3, 6, 12)
) -> dict:
    """Average forward return at each horizon after every week the signal fired,
    vs. the unconditional average forward return over the same horizon (spec 6,
    'signal quality')."""
    close = weekly["Close"]
    out = {}
    weeks_per_month = WEEKS_PER_YEAR / 12.0
    for m in horizons_months:
        h = max(1, round(m * weeks_per_month))
        fwd_ret = close.shift(-h) / close - 1.0
        cond = fwd_ret[signal_bool.reindex(fwd_ret.index).fillna(False)]
        out[f"{m}m"] = {
            "signal_avg": float(cond.mean()) if len(cond.dropna()) else float("nan"),
            "unconditional_avg": float(fwd_ret.mean()),
            "n_signal_obs": int(cond.dropna().shape[0]),
        }
    return out
