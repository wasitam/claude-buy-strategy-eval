"""v3 metrics: NAV/Sharpe/etc. per v2 sec 8.1 convention, applied to the
week-end resample of the daily engine output (weekly returns, as v2 defines
them), plus the pooled excess-return series (plan sec 3.3).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..v2 import metrics as v2met  # reuse nav_series / drawdown / sharpe / etc. definitions verbatim

WEEKS_PER_YEAR = 52.0


def weekly_from_daily(result_df: pd.DataFrame, close: pd.Series) -> pd.DataFrame:
    """Collapse the daily engine frame onto week-end rows (V, deposit, invested,
    units, cash at each week's last trading day), matching v2's weekly V/deposit
    semantics exactly so v2's nav_series() applies unmodified."""
    week_id = result_df["is_week_end"].to_numpy().cumsum()
    week_id = np.where(result_df["is_week_end"].to_numpy(), week_id, week_id)  # each day belongs to the week ending on the next flagged day
    # a day belongs to the week whose end is the next (or same) is_week_end==True day
    end_of_week = week_id  # already: index i has week_id = number of week-ends at or before i for i itself, but
    # for non-week-end days we want the FOLLOWING week-end's id, so recompute via reverse fill
    rev = result_df["is_week_end"].to_numpy()[::-1]
    grp = np.cumsum(rev)[::-1]
    grp = grp.max() - grp  # 0-based, increases each time we cross a week-end walking forward
    sums = result_df.groupby(grp)[["deposit", "fees_paid", "buy_usd", "sell_usd"]].sum()
    wk = result_df[result_df["is_week_end"]].copy()
    wk_grp = grp[result_df["is_week_end"].to_numpy()]
    for col in ["deposit", "fees_paid", "buy_usd", "sell_usd"]:
        wk[col] = sums.loc[wk_grp, col].to_numpy()
    return wk


def weekly_rf(daily_rf: pd.Series, week_index: pd.DatetimeIndex) -> pd.Series:
    """Compound daily rf within each week to get a weekly rf, aligned to week-end dates."""
    r = (1.0 + daily_rf).cumprod()
    at_weekends = r.reindex(week_index)
    prev = at_weekends.shift(1).fillna(r.iloc[0] / (1.0 + daily_rf.iloc[0]))
    return (at_weekends / prev - 1.0).fillna(0.0)


def summarize(daily_result_df: pd.DataFrame, daily_rf: pd.Series, final_close: float) -> dict:
    wk = weekly_from_daily(daily_result_df, None)
    V = wk["V"].to_numpy()
    deposit = wk["deposit"].to_numpy()
    nav = v2met.nav_series(V, deposit)
    total_invested = float(wk["invested"].iloc[-1])
    final_wealth = float(daily_result_df["cash"].iloc[-1] + daily_result_df["units"].iloc[-1] * final_close)
    max_dd, longest_uw = v2met.max_drawdown(nav)
    rfw = weekly_rf(daily_rf, wk.index).reindex(wk.index).fillna(0.0).to_numpy()

    avg_cash_share = float((wk["cash"] / wk["V"].clip(lower=1e-9)).clip(0, 1).mean())
    n_buys = int((wk["buy_usd"] > 0).sum())
    n_sells = int((wk["sell_usd"] > 0).sum())
    total_fees = float(wk["fees_paid"].sum())
    turnover = float((wk["buy_usd"].sum() + wk["sell_usd"].sum()) / max(total_invested, 1e-9))

    weekly_returns = pd.Series(nav).pct_change().dropna()
    excess = (weekly_returns.to_numpy() - rfw[1:]) if len(rfw) == len(nav) else weekly_returns.to_numpy()

    return {
        "total_invested": total_invested,
        "final_wealth": final_wealth,
        "wealth_over_invested": final_wealth / total_invested if total_invested else float("nan"),
        "nav": nav,
        "week_index": wk.index,
        "max_drawdown": max_dd,
        "longest_weeks_underwater": longest_uw,
        "cagr": v2met.cagr(nav),
        "annualized_vol": v2met.annualized_vol(nav),
        "sharpe": v2met.sharpe(nav, rfw),
        "sortino": v2met.sortino(nav, rfw),
        "calmar": v2met.calmar(nav),
        "n_buys": n_buys,
        "n_sells": n_sells,
        "total_fees": total_fees,
        "avg_cash_share": avg_cash_share,
        "turnover": turnover,
        "weekly_returns": weekly_returns,
        "weekly_rf": rfw,
    }


def pooled_excess_series(per_asset_weekly_returns: dict, per_asset_dca_weekly_returns: dict) -> pd.Series:
    """Equal-weight average of each asset's (strategy - DCA) weekly return series
    (plan sec 3.3), aligned on the union of week-end dates."""
    excess = {}
    for name, sret in per_asset_weekly_returns.items():
        dret = per_asset_dca_weekly_returns[name]
        idx = sret.index.union(dret.index)
        excess[name] = sret.reindex(idx).fillna(0.0) - dret.reindex(idx).fillna(0.0)
    df = pd.DataFrame(excess)
    return df.mean(axis=1).dropna()
