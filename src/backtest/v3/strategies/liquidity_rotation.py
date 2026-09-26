"""Family 043: Amihud-illiquidity cross-asset rotation (Amihud 2002,
applied cross-sectionally; Longstaff 2004; Vayanos 2004 flight-to-
liquidity framing).

families/043-liquidity-rotation/prereg.md has the full mechanism, rules
and the required rigorous distinction from family 021 (within-asset
time-series sizing) plus the brief distinction from families 002 (return-
based rotation) and 010 (fixed 2-asset price-ratio rotation). Summary:
reuses family 021's exact per-asset Amihud-ratio / causal-percentile-rank
computation (`amihud_illiquidity.compute_illiq` /
`_trailing_pctile_rank_ignoring_nan`, same undefined-day handling rule),
then RANKS the 5 assets' own-history percentiles AGAINST EACH OTHER each
week-end and rebalances the pooled $2,500 deposit toward the `top_n`
currently-most-liquid (lowest-percentile) assets at equal weight --
family 002's rebalance-to-target-weight portfolio mechanics, a different
weight table.

Category: Cross-asset rotation / relative strength.

Parameters (<=5, all in this module):
  illiq_lookback      -- trailing window (trading days) for each asset's
                          own causal Amihud-percentile rank (default 252)
  top_n               -- number of currently-most-liquid assets held at
                          equal weight (default 1)
  signal_smooth_days  -- trailing smoothing window (days) on each asset's
                          percentile series before cross-sectional
                          ranking; 1 = no smoothing (default 10)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import amihud_illiquidity as ami


def compute_own_percentile(daily: pd.DataFrame, illiq_lookback: int) -> np.ndarray:
    """Per-asset causal trailing percentile rank (0-100, NaN before
    warm-up or on undefined-Amihud days) of the asset's OWN Amihud ratio.
    Reuses family 021's exact computation unmodified -- this family's
    rigorous distinction from 021 is in what happens AFTER this step
    (cross-sectional ranking vs. within-asset regime triggering), not in
    the underlying statistic itself. See prereg.md."""
    illiq = ami.compute_illiq(daily)
    return ami._trailing_pctile_rank_ignoring_nan(illiq, illiq_lookback)


def compute_target_weights(
    aligned: dict, index: pd.DatetimeIndex,
    illiq_lookback: int, top_n: int, signal_smooth_days: int,
) -> pd.DataFrame:
    """Returns a DataFrame indexed by `index`, one column per asset, giving
    the target weight (sums to 1 every row -- always fully invested, no
    cash leg) at each day's close -- causal only. `aligned`: name -> daily
    OHLCV DataFrame (must include Close and Volume), all sharing `index`."""
    names = list(aligned.keys())
    n = len(index)
    n_assets = len(names)

    pctile_cols = {}
    for a in names:
        raw = compute_own_percentile(aligned[a], illiq_lookback)
        s = pd.Series(raw, index=index)
        if signal_smooth_days > 1:
            # NaN-tolerant trailing mean: pandas rolling().mean() excludes
            # NaNs from the window average as long as >=min_periods valid
            # (non-NaN) observations exist -- never fabricates a reading
            # from pure warm-up/undefined days.
            s = s.rolling(signal_smooth_days, min_periods=1).mean()
        pctile_cols[a] = s
    pctile_df = pd.DataFrame(pctile_cols, columns=names)

    valid = pctile_df.notna().to_numpy()
    # ascending rank: lowest percentile (most liquid relative to its own
    # history) is most favored. Invalid entries pushed to +inf so they
    # never get picked; stable sort keeps ties in a fixed, deterministic
    # asset order.
    ranked = np.where(valid, pctile_df.to_numpy(), np.inf)
    order = np.argsort(ranked, axis=1, kind="stable")

    weights = np.zeros((n, n_assets))
    for i in range(n):
        picks = []
        for j in order[i]:
            if not valid[i, j]:
                break
            picks.append(j)
            if len(picks) >= top_n:
                break
        if not picks:
            # Total warm-up fallback (no asset has a defined signal yet):
            # equal-weight all 5, never zero-weight everything simultaneously.
            weights[i, :] = 1.0 / n_assets
        else:
            w = 1.0 / len(picks)
            for j in picks:
                weights[i, j] = w
    return pd.DataFrame(weights, index=index, columns=names)


def make_liquidity_rotation_decider(
    aligned: dict, index: pd.DatetimeIndex, is_week_end: np.ndarray,
    weekly_deposit_per_asset: float, asset_names: list,
    illiq_lookback: int = 252, top_n: int = 1, signal_smooth_days: int = 10,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it always buys each asset's own $500 deposit
    share and never sells/reallocates -- bit-for-bit fixed-weight 5-asset
    DCA. Matches portfolio_engine.run_portfolio's decide(t, cash,
    total_value, units_now) signature, same as family 002's decider."""
    closes_np = {a: aligned[a]["Close"].to_numpy() for a in asset_names}
    if enabled:
        weights = compute_target_weights(aligned, index, illiq_lookback, top_n, signal_smooth_days)
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
            current_value = units_now.get(a, 0.0) * closes_np[a][t]
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


def make_equal_weight_rebalance_decider(asset_names: list, closes_np: dict, is_week_end: np.ndarray):
    """Independent SECOND reference point (families 013/029's two-
    reference-point precedent): a fixed 1/n_assets target weight,
    rebalanced weekly -- the v2 Strategy-C1-equivalent construction (same
    shape as family 013's own reference decider). Built independently of
    `compute_target_weights` so it can verify that this family's
    `top_n=5` grid arm (which also collapses to always-1/5-each)
    reproduces it bit-for-bit, without sharing any weight-computation code
    path with `compute_target_weights`."""
    n_assets = len(asset_names)
    w = 1.0 / n_assets

    def decide(t, cash, total_value, units_now):
        if not bool(is_week_end[t]):
            return {a: 0.0 for a in asset_names}, {a: 0.0 for a in asset_names}, {}
        buy_usd, sell_usd = {}, {}
        for a in asset_names:
            current_value = units_now.get(a, 0.0) * closes_np[a][t]
            target_value = w * total_value
            diff = target_value - current_value
            if diff > 0:
                buy_usd[a], sell_usd[a] = diff, 0.0
            else:
                buy_usd[a], sell_usd[a] = 0.0, -diff
        return buy_usd, sell_usd, {}
    return decide


CATEGORY = "Cross-asset rotation / relative strength"

# Grid: illiq_lookback(2) x top_n(3) x signal_smooth_days(2) = 12 (<=36, 3 tunable params <=5)
GRID = {
    "illiq_lookback": [126, 252],
    "top_n": [1, 2, 3],
    "signal_smooth_days": [1, 10],
}
PRIMARY_CONFIG = {"illiq_lookback": 252, "top_n": 1, "signal_smooth_days": 10}


def grid_configs() -> list[dict]:
    out = []
    for lb in GRID["illiq_lookback"]:
        for n in GRID["top_n"]:
            for sm in GRID["signal_smooth_days"]:
                out.append({"illiq_lookback": lb, "top_n": n, "signal_smooth_days": sm})
    return out


# Import-time assertion: PRIMARY_CONFIG must be an actual member of GRID
# (family 021's lesson, logged in state/bugfix_log.md -- checked
# programmatically here, not just by eye, before any backtest can import
# this module).
assert PRIMARY_CONFIG["illiq_lookback"] in GRID["illiq_lookback"]
assert PRIMARY_CONFIG["top_n"] in GRID["top_n"]
assert PRIMARY_CONFIG["signal_smooth_days"] in GRID["signal_smooth_days"]
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of grid_configs()"
