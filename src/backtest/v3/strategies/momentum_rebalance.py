"""Family 013: Momentum-tilted rebalancing across the 5 core assets
(Asness, Moskowitz & Pedersen, 2013 momentum literature, layered on v2's
confirmed fixed-weight rebalancing premium).

families/013-momentum-rebalance/prereg.md has the full mechanism and rules.
Summary: each week, compute a cross-sectional, standardized trailing-
momentum z-score per asset (relative to the other 4), tilt the equal-weight
(1/5 each) target proportionally to that z-score, clip each asset's target
weight to [min_weight, max_weight] (no leverage, no negative/short
weights), renormalize to sum to 1 (always 100% invested, no cash-parking
leg), and rebalance the pooled portfolio toward that tilted target weekly,
the same day the pooled $2,500 deposit is credited.

Category: Rebalancing / allocation.

Parameters (<=5, all in this module):
  lookback_days  -- trailing total-return lookback window (default 252, ~12mo)
  tilt_strength  -- weight shift per unit of standardized relative momentum
                     (default 1.0); tilt_strength=0 collapses to a fixed
                     equal-weight weekly rebalance (v2 Strategy C1's
                     mechanism, NOT plain DCA -- see prereg.md)
  min_weight     -- floor per asset (default 0.05)
  max_weight     -- cap per asset (default 0.40)
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_target_weights(
    closes: dict, index: pd.DatetimeIndex,
    lookback_days: int, tilt_strength: float, min_weight: float, max_weight: float,
) -> pd.DataFrame:
    """Returns a DataFrame indexed by `index`, one column per asset, giving
    the target weight (always sums to 1, in [min_weight, max_weight] per
    asset before renormalization) at each day's close -- causal only (uses
    data through day t)."""
    names = list(closes.keys())
    n_assets = len(names)
    close_df = pd.DataFrame({a: closes[a] for a in names}, index=index)
    mom = close_df / close_df.shift(lookback_days) - 1.0
    mom = mom.fillna(0.0)  # neutral (0 momentum) until enough history -- never excludes the asset

    mean_mom = mom.mean(axis=1)
    std_mom = mom.std(axis=1, ddof=0)
    z = mom.sub(mean_mom, axis=0).div(std_mom.clip(lower=0.0) + 1e-6, axis=0)

    base = 1.0 / n_assets
    raw_w = base * (1.0 + tilt_strength * z)
    clipped = raw_w.clip(lower=min_weight, upper=max_weight)
    total = clipped.sum(axis=1)
    weights = clipped.div(total, axis=0)
    return weights


def make_momentum_rebalance_decider(
    closes: dict, index: pd.DatetimeIndex, is_week_end: np.ndarray,
    weekly_deposit_per_asset: float, asset_names: list,
    lookback_days: int = 252, tilt_strength: float = 1.0,
    min_weight: float = 0.05, max_weight: float = 0.40,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it always buys each asset's own $500 deposit
    share and never sells/reallocates -- bit-for-bit fixed-weight 5-asset
    DCA. Matches portfolio_engine.run_portfolio's decide(t, cash,
    total_value, units_now) signature."""
    if enabled:
        weights = compute_target_weights(closes, index, lookback_days, tilt_strength, min_weight, max_weight)
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


def make_equal_weight_rebalance_decider(
    closes: dict, index: pd.DatetimeIndex, is_week_end: np.ndarray,
    weekly_deposit_per_asset: float, asset_names: list,
):
    """Family-specific implementation check #2 reference: a SEPARATE,
    independently-built decider that rebalances weekly toward a fixed
    equal-weight (1/n_assets each) target, with NO momentum computation at
    all -- the direct v2-Strategy-C1-equivalent reference this family's
    tilt_strength=0 config is checked against (prereg.md check #2)."""
    n_assets = len(asset_names)
    w = 1.0 / n_assets

    def decide(t, cash, total_value, units_now):
        if not bool(is_week_end[t]):
            return {a: 0.0 for a in asset_names}, {a: 0.0 for a in asset_names}, {}
        buy_usd, sell_usd = {}, {}
        for a in asset_names:
            current_value = units_now.get(a, 0.0) * closes[a][t]
            target_value = w * total_value
            diff = target_value - current_value
            if diff > 0:
                buy_usd[a] = diff
                sell_usd[a] = 0.0
            else:
                buy_usd[a] = 0.0
                sell_usd[a] = -diff
        return buy_usd, sell_usd, {}

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


CATEGORY = "Rebalancing / allocation"

# Grid: lookback_days x tilt_strength x bound-pair = 2 x 4 x 2 = 16 configs (<=36, 4 params <=5)
GRID_LOOKBACK = [126, 252]
GRID_TILT = [0.0, 0.5, 1.0, 2.0]
GRID_BOUND_PAIRS = [(0.10, 0.30), (0.05, 0.40)]  # (min_weight, max_weight)
PRIMARY_CONFIG = {"lookback_days": 252, "tilt_strength": 1.0, "min_weight": 0.05, "max_weight": 0.40}


def grid_configs() -> list[dict]:
    out = []
    for lb in GRID_LOOKBACK:
        for ts in GRID_TILT:
            for mn, mx in GRID_BOUND_PAIRS:
                out.append({"lookback_days": lb, "tilt_strength": ts, "min_weight": mn, "max_weight": mx})
    return out
