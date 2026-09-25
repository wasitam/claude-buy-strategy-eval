"""Family 010: Gold/silver ratio rotation (relative-value commodity
literature).

families/010-gold-silver-ratio/prereg.md has the full mechanism, rules, and
the 2-asset assessment-scoping decision. Summary: each week, compute the
trailing percentile rank of the gold/silver price ratio within a rolling
`ratio_window_years` window (strictly point-in-time), and tilt the target
weight between gold and silver away from 50/50 toward whichever metal is
historically cheap relative to the other -- silver when the ratio is
historically high (above `100 - band` percentile), gold when the ratio is
historically low (below `band` percentile). Inside the [band, 100-band]
dead zone, the target stays 50/50. Always fully invested across the two
metals (no cash leg) -- this is a relative-value split, not a trend-exit
signal. Rebalanced weekly, the same day the pooled $1,000 deposit
($500 gold-equivalent + $500 silver-equivalent) is credited.

Category: Cross-asset rotation / relative strength.

Parameters (<=5, all in this module):
  ratio_window_years -- trailing window (years) for the ratio's percentile
                         rank (default 20)
  band                -- dead-zone half-width in percentile points;
                          low_pctile=band, high_pctile=100-band (default 20)
  max_tilt             -- max deviation from 50/50 at the most extreme
                          percentile (0..1; default 0.7)

`min_periods` (504 trading days, ~2 years) and the weekly rebalance cadence
are fixed, not tunable -- see prereg.md.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MIN_PERIODS = 504  # ~2 years; signal is inactive (neutral 50/50) before this


def compute_target_weights(
    close_gold: pd.Series, close_silver: pd.Series, index: pd.DatetimeIndex,
    ratio_window_years: float, band: float, max_tilt: float,
) -> pd.DataFrame:
    """Returns a DataFrame indexed by `index` with columns ["GOLD", "SILVER"]
    giving each day's target weight (sums to 1 every row) -- causal only
    (each row's percentile rank uses only that day's and prior days' ratio
    values, via a strictly-trailing rolling window)."""
    window_days = int(round(ratio_window_years * 252))
    ratio = pd.Series(close_gold, index=index) / pd.Series(close_silver, index=index)
    # rolling(window).rank(pct=True): each row's percentile rank among the
    # trailing `window` observations INCLUDING itself -- strictly backward-
    # looking by construction (no future data enters row t's computation).
    pctile = ratio.rolling(window=window_days, min_periods=MIN_PERIODS).rank(pct=True) * 100.0

    low_pctile = band
    high_pctile = 100.0 - band

    silver_w = pd.Series(0.5, index=index)
    # above the dead zone: tilt toward silver, linear from 0.5 at
    # high_pctile to 0.5+max_tilt/2 at pctile=100
    above = pctile > high_pctile
    span_hi = max(100.0 - high_pctile, 1e-9)
    silver_w[above] = 0.5 + 0.5 * max_tilt * ((pctile[above] - high_pctile) / span_hi).clip(0, 1)
    # below the dead zone: tilt toward gold, linear from 0.5 at low_pctile
    # to 0.5+max_tilt/2 at pctile=0 (i.e. silver weight falls symmetrically)
    below = pctile < low_pctile
    span_lo = max(low_pctile, 1e-9)
    silver_w[below] = 0.5 - 0.5 * max_tilt * ((low_pctile - pctile[below]) / span_lo).clip(0, 1)
    # inactive signal (not enough history yet) stays neutral 0.5
    silver_w[pctile.isna()] = 0.5

    gold_w = 1.0 - silver_w
    return pd.DataFrame({"GOLD": gold_w, "SILVER": silver_w}, index=index)


def make_gold_silver_ratio_decider(
    closes: dict, index: pd.DatetimeIndex, is_week_end: np.ndarray,
    weekly_deposit_per_asset: float, asset_names: list,
    ratio_window_years: float = 20.0, band: float = 20.0, max_tilt: float = 0.7,
    enabled: bool = True,
):
    """enabled=False (or max_tilt=0) is the degenerate/disable path used by
    the implementation check: it always buys each metal's own $500 deposit
    share and never sells/reallocates -- bit-for-bit fixed-weight 2-asset
    DCA. Matches portfolio_engine.run_portfolio's
    decide(t, cash, total_value, units_now) signature."""
    if enabled:
        weights = compute_target_weights(
            closes["GOLD"], closes["SILVER"], index, ratio_window_years, band, max_tilt,
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
                buy_usd[a], sell_usd[a] = diff, 0.0
            else:
                buy_usd[a], sell_usd[a] = 0.0, -diff
        return buy_usd, sell_usd, {"target_weights": target_w.to_dict()}

    return decide


def make_decider_from_weekend_weights(weekend_weights: pd.DataFrame, is_week_end: np.ndarray,
                                       index: pd.DatetimeIndex, closes: dict, asset_names: list):
    """Placebo helper: builds a decide fn that looks up a target-weight row
    from a precomputed {week-end date -> weights} table (e.g. a circularly
    shifted version of the real signal) instead of recomputing the ratio,
    while still filling orders against the REAL price path. Mirrors
    dual_momentum.make_decider_from_weekend_weights exactly."""
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

# Grid: ratio_window_years x band x max_tilt = 3 x 3 x 3 = 27 (<=36, 3 params <=5)
GRID = {
    "ratio_window_years": [10, 15, 20],
    "band": [10, 20, 30],
    "max_tilt": [0.4, 0.7, 1.0],
}
PRIMARY_CONFIG = {"ratio_window_years": 20, "band": 20, "max_tilt": 0.7}


def grid_configs() -> list[dict]:
    out = []
    for w in GRID["ratio_window_years"]:
        for b in GRID["band"]:
            for m in GRID["max_tilt"]:
                out.append({"ratio_window_years": w, "band": b, "max_tilt": m})
    return out
