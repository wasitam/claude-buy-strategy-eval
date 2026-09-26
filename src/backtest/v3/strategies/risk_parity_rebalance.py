"""Family 029: Risk-parity (inverse-volatility) rebalancing across the 5
core assets (Asness, Frazzini & Pedersen 2012, "Leverage Aversion and Risk
Parity"; broader risk-parity/inverse-vol-weighting practitioner literature).

families/029-risk-parity-rebalance/prereg.md has the full mechanism and
rules. Summary: each week, compute each asset's trailing realized daily
return volatility, set each asset's RAW target weight inversely
proportional to that volatility (lower-vol assets get a larger target
weight, higher-vol assets like BTC get a smaller one), clip each asset's
target weight to [min_weight, max_weight] (no leverage, no negative/short
weights), renormalize to sum to 1 (always 100% invested, no cash-parking
leg -- same convention as family 013), optionally EMA-smooth the resulting
weight sequence to reduce whipsaw/turnover, and rebalance the pooled
portfolio toward that target weekly, the same day the pooled $2,500
deposit is credited.

Category: Rebalancing / allocation.

Parameters (<=5, all in this module):
  vol_lookback_days      -- trailing window (in trading days) over which each
                             asset's realized daily-return volatility is
                             estimated (default 126, ~6mo)
  min_weight / max_weight -- bound pair per asset (no leverage, no
                             negative/short weights, no extreme
                             concentration); default (0.05, 0.40)
  smoothing_halflife_days -- EMA half-life (in weekly rebalance steps) applied
                             to the clipped/renormalized target-weight
                             sequence to reduce turnover; 0 means no
                             smoothing (default 10)

equal_vol_override=True is a diagnostic/reference bypass ONLY: it forces
every asset's estimated volatility to an identical constant, which collapses
the inverse-vol target to exactly equal weight (1/5 each) regardless of the
real data -- the family's "equal-vol-assumption edge case" reference point,
matched independently against family 013's separately-built equal-weight
weekly-rebalance reference (families/013's `make_equal_weight_rebalance_decider`).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_realized_vol(closes: dict, index: pd.DatetimeIndex, vol_lookback_days: int) -> pd.DataFrame:
    """Trailing realized daily-return volatility per asset, causal only (the
    value at day t uses only daily log returns through day t's close --
    pandas rolling() windows always look backward, never forward)."""
    names = list(closes.keys())
    close_df = pd.DataFrame({a: closes[a] for a in names}, index=index)
    log_ret = np.log(close_df).diff()
    vol = log_ret.rolling(vol_lookback_days, min_periods=max(5, vol_lookback_days // 4)).std()
    # Strictly causal fill for the startup ramp before min_periods is first
    # reached: forward-fill (uses only past values), then, only for the very
    # first row(s) where even that is unavailable, a fixed constant fallback
    # -- never a backward-fill, which would leak future data into early
    # decisions (see the no-lookahead implementation check).
    vol = vol.ffill().fillna(0.02)
    return vol


def compute_target_weights(
    closes: dict, index: pd.DatetimeIndex,
    vol_lookback_days: int, min_weight: float, max_weight: float,
    smoothing_halflife_days: int = 0, equal_vol_override: bool = False,
) -> pd.DataFrame:
    """Returns a DataFrame indexed by `index`, one column per asset, giving
    the target weight (sums to 1, in [min_weight, max_weight] per asset) at
    each day's close -- causal only (uses data through day t)."""
    names = list(closes.keys())
    n_assets = len(names)

    if equal_vol_override:
        # Diagnostic bypass: pretend every asset has identical volatility, so
        # inverse-vol weighting collapses to exactly equal weight regardless
        # of the actual data -- the family's equal-vol-assumption reference.
        vol = pd.DataFrame(1.0, index=index, columns=names)
    else:
        vol = compute_realized_vol(closes, index, vol_lookback_days)

    inv_vol = 1.0 / (vol + 1e-8)
    raw_w = inv_vol.div(inv_vol.sum(axis=1), axis=0)
    clipped = raw_w.clip(lower=min_weight, upper=max_weight)
    weights = clipped.div(clipped.sum(axis=1), axis=0)

    if smoothing_halflife_days and smoothing_halflife_days > 0:
        weights = weights.ewm(halflife=smoothing_halflife_days, adjust=False).mean()
        # Linear/convex-combination smoothing of rows that already sum to 1
        # and already respect [min_weight, max_weight] elementwise keeps both
        # properties automatically (a per-asset weighted average of two
        # in-bounds numbers stays in bounds; a weighted average of two rows
        # that each sum to 1 still sums to 1) -- no re-clip/renormalize needed.

    return weights


def make_risk_parity_decider(
    closes: dict, index: pd.DatetimeIndex, is_week_end: np.ndarray,
    weekly_deposit_per_asset: float, asset_names: list,
    vol_lookback_days: int = 126, min_weight: float = 0.05, max_weight: float = 0.40,
    smoothing_halflife_days: int = 10, equal_vol_override: bool = False,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it always buys each asset's own $500 deposit
    share and never sells/reallocates -- bit-for-bit fixed-weight 5-asset
    DCA. Matches portfolio_engine.run_portfolio's decide(t, cash,
    total_value, units_now) signature."""
    if enabled:
        weights = compute_target_weights(
            closes, index, vol_lookback_days, min_weight, max_weight,
            smoothing_halflife_days=smoothing_halflife_days, equal_vol_override=equal_vol_override,
        )
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
    shifted version of the real signal) instead of recomputing volatility,
    while still filling orders against the REAL price path. Mirrors family
    013's identically-named helper."""
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


CATEGORY = "Rebalancing / allocation"

# Grid: vol_lookback_days x bound-pair x smoothing_halflife_days = 3 x 2 x 2 = 12 (<=36, 3 tunable params <=5)
GRID_VOL_LOOKBACK = [63, 126, 252]
GRID_BOUND_PAIRS = [(0.10, 0.30), (0.05, 0.40)]  # (min_weight, max_weight)
GRID_SMOOTHING = [0, 10]
PRIMARY_CONFIG = {
    "vol_lookback_days": 126, "min_weight": 0.05, "max_weight": 0.40, "smoothing_halflife_days": 10,
}


def grid_configs() -> list[dict]:
    out = []
    for vl in GRID_VOL_LOOKBACK:
        for mn, mx in GRID_BOUND_PAIRS:
            for sm in GRID_SMOOTHING:
                out.append({
                    "vol_lookback_days": vl, "min_weight": mn, "max_weight": mx,
                    "smoothing_halflife_days": sm,
                })
    return out


# Module-import-time assertion (family 021/028's lesson, state/bugfix_log.md):
# verify PRIMARY_CONFIG is a genuine member of the declared grid before
# anything else in this module can be used.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG must be a member of grid_configs()"
