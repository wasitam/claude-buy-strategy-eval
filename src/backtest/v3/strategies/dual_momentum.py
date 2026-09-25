"""Family 002: Dual momentum rotation across the 5 core assets + T-bills
(Antonacci, 2014).

families/002-dual-momentum/prereg.md has the full mechanism and rules.
Summary: each week, rank the 5 core assets by trailing `lookback_days` total
return (relative momentum), keep only those beating the T-bill's trailing
return over the same window plus `abs_mom_buffer_bps` (absolute momentum
filter), and hold the top `top_n` of the survivors at equal weight; the rest
of the portfolio (including all of it, if nothing survives the absolute
filter) sits in cash/T-bills. Rebalanced weekly, the same day the pooled
$2,500 deposit is credited.

Category: Cross-asset rotation / relative strength.

Parameters (<=5, all in this module):
  lookback_days       -- trailing total-return lookback window (default 252, ~12mo)
  top_n               -- number of top-ranked qualifying assets to hold (default 1)
  abs_mom_buffer_bps  -- extra margin (bps) required above the T-bill hurdle
                         for an asset to qualify (default 0)
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_target_weights(
    closes: dict, daily_rf: pd.Series, index: pd.DatetimeIndex,
    lookback_days: int, top_n: int, abs_mom_buffer_bps: float,
) -> pd.DataFrame:
    """Returns a DataFrame indexed by `index`, one column per asset, giving
    the target weight (0..1) at each day's close -- causal only (uses data
    through day t). Columns sum to <=1; the residual is cash."""
    names = list(closes.keys())
    close_df = pd.DataFrame({a: closes[a] for a in names}, index=index)
    ret = close_df / close_df.shift(lookback_days) - 1.0  # trailing total return, NaN until lookback_days obs exist

    rf_cum = (1.0 + daily_rf.reindex(index).fillna(0.0)).cumprod()
    rf_trailing = rf_cum / rf_cum.shift(lookback_days) - 1.0

    buffer = abs_mom_buffer_bps / 10000.0
    qualifies = ret.sub(rf_trailing, axis=0) > buffer
    qualifies = qualifies.fillna(False)

    ranked = ret.where(qualifies, other=-np.inf)
    weights = pd.DataFrame(0.0, index=index, columns=names)
    # rank each row descending; keep top_n among qualifying assets
    order = np.argsort(-ranked.to_numpy(), axis=1)
    ranked_np = ranked.to_numpy()
    for i in range(len(index)):
        picks = []
        for j in order[i]:
            if ranked_np[i, j] == -np.inf:
                break
            picks.append(j)
            if len(picks) >= top_n:
                break
        if picks:
            w = 1.0 / len(picks)
            for j in picks:
                weights.iloc[i, j] = w
    return weights


def make_dual_momentum_decider(
    closes: dict, daily_rf: pd.Series, index: pd.DatetimeIndex, is_week_end: np.ndarray,
    weekly_deposit_per_asset: float, asset_names: list,
    lookback_days: int = 252, top_n: int = 1, abs_mom_buffer_bps: float = 0.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it always buys each asset's own $500 deposit share
    and never sells/reallocates -- bit-for-bit fixed-weight 5-asset DCA.
    Matches portfolio_engine.run_portfolio's decide(t, cash, total_value,
    units_now) signature; units_now is supplied by the engine each call so
    rebalancing orders (target dollar value - current dollar value) can be
    computed on rebalance days."""
    if enabled:
        weights = compute_target_weights(closes, daily_rf, index, lookback_days, top_n, abs_mom_buffer_bps)
    else:
        weights = None

    def decide(t, cash, total_value, units_now):
        if not enabled:
            buy_usd = {a: weekly_deposit_per_asset for a in asset_names}
            total = sum(buy_usd.values())
            if total > cash and total > 0:
                scale = max(cash, 0.0) / total
                buy_usd = {a: v * scale for a, v in buy_usd.items()}
            return buy_usd, {a: 0.0 for a in asset_names}, {}

        if not bool(is_week_end[t]):
            return {a: 0.0 for a in asset_names}, {a: 0.0 for a in asset_names}, {}

        target_w = weights.iloc[t]
        buy_usd, sell_usd = {}, {}
        for a in asset_names:
            current_value = units_now.get(a, 0.0) * closes[a][t]
            target_value = float(target_w[a]) * total_value
            diff = target_value - current_value
            if diff > 0:
                buy_usd[a] = diff
                sell_usd[a] = 0.0
            else:
                buy_usd[a] = 0.0
                sell_usd[a] = -diff
        return buy_usd, sell_usd, {"target_weights": target_w.to_dict()}

    return decide


def make_decider_from_weekend_weights(weekend_weights: pd.DataFrame, is_week_end: np.ndarray,
                                       index: pd.DatetimeIndex, closes: dict, asset_names: list):
    """Placebo helper: builds a decide fn that looks up a target-weight row
    from a precomputed {week-end date -> weights} table (e.g. a circularly
    shifted version of the real signal) instead of recomputing momentum,
    while still filling orders against the REAL price path."""
    weekend_dates = weekend_weights.index

    def decide(t, cash, total_value, units_now):
        if not bool(is_week_end[t]):
            return {a: 0.0 for a in asset_names}, {a: 0.0 for a in asset_names}, {}
        date = index[t]
        pos = weekend_dates.get_indexer([date])[0]
        if pos < 0:
            pos = min(range(len(weekend_dates)), key=lambda i: abs((weekend_dates[i] - date).days))
        target_w = weekend_weights.iloc[pos]
        buy_usd, sell_usd = {}, {}
        for a in asset_names:
            current_value = units_now.get(a, 0.0) * closes[a][t]
            target_value = float(target_w[a]) * total_value
            diff = target_value - current_value
            if diff > 0:
                buy_usd[a], sell_usd[a] = diff, 0.0
            else:
                buy_usd[a], sell_usd[a] = 0.0, -diff
        return buy_usd, sell_usd, {}

    return decide


CATEGORY = "Cross-asset rotation / relative strength"

# Grid: lookback_days x top_n x abs_mom_buffer_bps = 3 x 2 x 2 = 12 configs (<=36, 3 params <=5)
GRID = {
    "lookback_days": [126, 189, 252],
    "top_n": [1, 2],
    "abs_mom_buffer_bps": [0, 50],
}
PRIMARY_CONFIG = {"lookback_days": 252, "top_n": 1, "abs_mom_buffer_bps": 0}


def grid_configs() -> list[dict]:
    out = []
    for l in GRID["lookback_days"]:
        for n in GRID["top_n"]:
            for b in GRID["abs_mom_buffer_bps"]:
                out.append({"lookback_days": l, "top_n": n, "abs_mom_buffer_bps": b})
    return out
