"""Family 048: Tolerance-band ("drift-triggered") rebalancing across the 5
core assets (Donohue & Yip 2003; Masters 2003 -- transaction-cost-driven
rebalancing literature).

families/048-drift-band-rebalance/prereg.md has the full mechanism and
rules. Summary: the target weight is FIXED equal weight (1/5 each, never
recomputed from any signal -- unlike families 013/029). Checked at each
week-end decision day, a rebalance to that fixed target fires only when
some asset's actual weight has drifted more than `band_pct` away from 0.2
AND at least `min_days_between_rebalances` trading days have elapsed since
the last rebalance event. Between triggers, the week's $500-per-asset
deposit is simply invested (like plain DCA), and existing holdings are left
untouched -- the "avoid unnecessary turnover" half of the mechanism.

Category: Rebalancing / allocation.

Parameters (<=5, both in this module):
  band_pct                    -- symmetric tolerance band around the fixed
                                   20% target (default 0.05)
  min_days_between_rebalances -- cooldown floor in trading days, guards
                                   against pathological whipsaw (default 5)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TARGET_WEIGHT = 0.2  # fixed, equal, never recomputed -- not a tunable parameter


def make_drift_band_rebalance_decider(
    closes: dict, index: pd.DatetimeIndex, is_week_end: np.ndarray,
    weekly_deposit_per_asset: float, asset_names: list,
    band_pct: float = 0.05, min_days_between_rebalances: int = 5,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by
    implementation check #1: it always buys each asset's own $500 deposit
    share and never sells/reallocates -- bit-for-bit fixed-weight 5-asset
    DCA. Matches portfolio_engine.run_portfolio's decide(t, cash,
    total_value, units_now) signature. `extra["rebalanced"]` (bool) is
    used by the pre-grid distinction check to build the rebalance-event
    series without re-deriving the trigger logic."""
    n_assets = len(asset_names)
    state = {"last_rebalance_t": None}

    def decide(t, cash, total_value, units_now):
        if not enabled:
            buy_usd = {a: weekly_deposit_per_asset for a in asset_names}
            total = sum(buy_usd.values())
            if total > cash and total > 0:
                scale = max(cash, 0.0) / total
                buy_usd = {a: v * scale for a, v in buy_usd.items()}
            return buy_usd, {a: 0.0 for a in asset_names}, {"rebalanced": False}

        if not bool(is_week_end[t]):
            return {a: 0.0 for a in asset_names}, {a: 0.0 for a in asset_names}, {"rebalanced": False}

        # current weights, using this week's already-credited deposit and total_value (013/029/043 convention)
        current_value = {a: units_now.get(a, 0.0) * closes[a][t] for a in asset_names}
        weights = {a: (current_value[a] / total_value if total_value > 0 else 0.0) for a in asset_names}
        max_abs_drift = max(abs(weights[a] - TARGET_WEIGHT) for a in asset_names)

        last_t = state["last_rebalance_t"]
        cooldown_ok = (last_t is None) or (t - last_t >= min_days_between_rebalances)
        trigger = (max_abs_drift > band_pct) and cooldown_ok

        if not trigger:
            buy_usd = {a: weekly_deposit_per_asset for a in asset_names}
            return buy_usd, {a: 0.0 for a in asset_names}, {"rebalanced": False}

        state["last_rebalance_t"] = t
        buy_usd, sell_usd = {}, {}
        for a in asset_names:
            target_value = TARGET_WEIGHT * total_value
            diff = target_value - current_value[a]
            if diff > 0:
                buy_usd[a], sell_usd[a] = diff, 0.0
            else:
                buy_usd[a], sell_usd[a] = 0.0, -diff
        return buy_usd, sell_usd, {"rebalanced": True, "max_abs_drift": max_abs_drift}

    return decide


def make_equal_weight_rebalance_decider(
    closes: dict, index: pd.DatetimeIndex, is_week_end: np.ndarray,
    weekly_deposit_per_asset: float, asset_names: list,
):
    """Family-specific implementation check #2 reference: a SEPARATE,
    independently-built decider that rebalances weekly toward a fixed
    equal-weight (1/n_assets each) target, with NO drift/trigger logic at
    all -- the direct v2-Strategy-C1-equivalent reference this family's
    band_pct=0, min_days_between_rebalances=0 config is checked against
    (prereg.md check #2). Reproduces momentum_rebalance.py's identically-
    named helper's behavior, kept as a local, independent copy per family
    013/029/043's own practice of building a fresh reference each time."""
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
                buy_usd[a], sell_usd[a] = diff, 0.0
            else:
                buy_usd[a], sell_usd[a] = 0.0, -diff
        return buy_usd, sell_usd, {}

    return decide


def make_decider_from_weekend_rebalance_flags(
    weekend_flags: pd.Series, is_week_end: np.ndarray, index: pd.DatetimeIndex,
    closes: dict, asset_names: list, weekly_deposit_per_asset: float,
):
    """Placebo helper: builds a decide fn that looks up a precomputed
    {week-end date -> rebalance?} flag (e.g. a circularly shifted version
    of the real trigger sequence) instead of recomputing drift, while still
    filling orders against the REAL price path. On a flagged week-end, it
    rebalances fully to the fixed 20% target; otherwise it just deposits
    (exactly the real strategy's own non-trigger behavior)."""
    weekend_dates = weekend_flags.index

    def decide(t, cash, total_value, units_now):
        if not bool(is_week_end[t]):
            return {a: 0.0 for a in asset_names}, {a: 0.0 for a in asset_names}, {}
        date = index[t]
        pos = weekend_dates.get_indexer([date])[0]
        if pos < 0:
            pos = min(range(len(weekend_dates)), key=lambda i: abs((weekend_dates[i] - date).days))
        rebalance = bool(weekend_flags.iloc[pos])
        if not rebalance:
            return {a: weekly_deposit_per_asset for a in asset_names}, {a: 0.0 for a in asset_names}, {}
        current_value = {a: units_now.get(a, 0.0) * closes[a][t] for a in asset_names}
        buy_usd, sell_usd = {}, {}
        for a in asset_names:
            target_value = TARGET_WEIGHT * total_value
            diff = target_value - current_value[a]
            if diff > 0:
                buy_usd[a], sell_usd[a] = diff, 0.0
            else:
                buy_usd[a], sell_usd[a] = 0.0, -diff
        return buy_usd, sell_usd, {}

    return decide


CATEGORY = "Rebalancing / allocation"

# Grid: band_pct x min_days_between_rebalances = 6 x 3 = 18 configs (<=36, 2 params <=5)
GRID_BAND_PCT = [0.02, 0.03, 0.05, 0.08, 0.10, 0.15]
GRID_MIN_DAYS = [0, 5, 20]
PRIMARY_CONFIG = {"band_pct": 0.05, "min_days_between_rebalances": 5}


def grid_configs() -> list[dict]:
    out = []
    for bp in GRID_BAND_PCT:
        for md in GRID_MIN_DAYS:
            out.append({"band_pct": bp, "min_days_between_rebalances": md})
    return out


assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG must be a member of grid_configs()"
