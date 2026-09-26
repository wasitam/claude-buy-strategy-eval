"""Family 053: momentum acceleration ("velocity of momentum") sizing
(Novy-Marx 2012's "momentum of momentum"; Gao, Han, Li & Zhou 2018).

families/053-momentum-acceleration-sizing/prereg.md has the full mechanism
and rules. Summary: at each week-end decision day t, compute the asset's
own trailing total-return momentum level over `lookback_days` trading days,
both TODAY (`mom_now`) and as of `lag_days` trading days ago (`mom_past`,
the *same* statistic, just measured earlier). The signal is the
ACCELERATION `accel_t = mom_now_t - mom_past_t` -- the change in the
momentum level itself, a second-derivative-of-price statistic, not the
level (family 013/002) or the sign of the level (family 005). `accel_t` is
converted to a causal, point-in-time percentile rank within its own
trailing history, then to a CONTINUOUS sizing multiplier (family 039's
established percentile-scaled-multiplier design pattern, not a discrete
ladder): `m_t = clip(1 + k*(2*pctile_t - 1), min_mult, max_mult)`.

Category: Trend / time-series momentum exit.

Parameters (<=5, all in this module):
  lookback_days   -- trailing window for the momentum-LEVEL statistic
  lag_days        -- how far back the "earlier" momentum reading is taken
  k               -- sensitivity of the multiplier to the accel percentile
  min_mult        -- lower clip bound (deliberately <1.0, per families
                     014/033/037's cash-cap-nullification lesson)

Fixed constants (not grid-varied): pctile_lookback=252, max_mult=2.0,
max_lump_multiple=3.0.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_momentum_level(daily: pd.DataFrame, lookback_days: int) -> np.ndarray:
    """Returns mom(t) = close_t / close_{t-lookback_days} - 1 for each day t,
    using only data through t (no lookahead). NaN until t - lookback_days >= 0."""
    close = daily["Close"].to_numpy()
    n = len(close)
    mom = np.full(n, np.nan)
    for t in range(lookback_days, n):
        mom[t] = close[t] / close[t - lookback_days] - 1.0
    return mom


def compute_acceleration(daily: pd.DataFrame, lookback_days: int, lag_days: int,
                          mom_cache: np.ndarray | None = None) -> np.ndarray:
    """Returns accel(t) = mom(t) - mom(t - lag_days), the causal (no-lookahead)
    change in the trailing-momentum LEVEL over lag_days. NaN until both
    mom(t) and mom(t-lag_days) are defined, i.e. t - lag_days - lookback_days >= 0."""
    mom = mom_cache if mom_cache is not None else compute_momentum_level(daily, lookback_days)
    n = len(mom)
    accel = np.full(n, np.nan)
    for t in range(n):
        t_past = t - lag_days
        if t_past >= 0 and not np.isnan(mom[t]) and not np.isnan(mom[t_past]):
            accel[t] = mom[t] - mom[t_past]
    return accel


def compute_causal_percentile(values: np.ndarray, pctile_lookback: int) -> np.ndarray:
    """Causal, point-in-time percentile rank of values[t] within the trailing
    pctile_lookback days of values (itself), expanding-until-full, purely
    backward-looking (families 031/035/036/039/040/041/042/044 convention).
    Defaults to 0.5 (neutral) until pctile_lookback observations of a
    non-NaN value exist, or while values[t] itself is NaN.

    Vectorized via a sliding-window view over the VALID (non-NaN) values
    only, then scattered back to the original day-index positions -- this
    is bit-for-bit equivalent to a naive per-day python loop over an
    expanding-then-fixed trailing window of the asset's own valid history
    (verified by an explicit unit check in
    scripts/v3/run_053_momentum_acceleration_sizing.py), but avoids an
    O(n * pctile_lookback) pure-python loop that is prohibitively slow on
    SP500's ~23,000-day development history."""
    n = len(values)
    pctile = np.full(n, 0.5)
    valid_mask = ~np.isnan(values)
    valid_idx = np.flatnonzero(valid_mask)
    valid_vals = values[valid_idx]
    m = len(valid_vals)
    if m <= pctile_lookback:
        return pctile
    # windows_all[j] = valid_vals[j : j+pctile_lookback] for every valid j.
    # The reference (naive) semantics compare "today's" value against the
    # PRIOR pctile_lookback values only (today is not yet in the window at
    # the moment the naive loop checks its length), so the window ending
    # right BEFORE today's value at valid position i is windows_all[i -
    # pctile_lookback], and today's value is valid_vals[i]. Dropping the
    # last row of windows_all (which would pair with an out-of-range i==m)
    # gives exactly the valid (window, current-value) pairs for
    # i = pctile_lookback .. m-1.
    windows_all = np.lib.stride_tricks.sliding_window_view(valid_vals, pctile_lookback)
    windows = windows_all[:-1]
    current_vals = valid_vals[pctile_lookback:]
    pct_valid = (windows <= current_vals[:, None]).mean(axis=1)
    target_positions = valid_idx[pctile_lookback:]
    pctile[target_positions] = pct_valid
    return pctile


def compute_multiplier(daily: pd.DataFrame, lookback_days: int, lag_days: int,
                        pctile_lookback: int, k: float, min_mult: float,
                        max_mult: float = 2.0, mom_cache: np.ndarray | None = None) -> np.ndarray:
    accel = compute_acceleration(daily, lookback_days, lag_days, mom_cache=mom_cache)
    pctile = compute_causal_percentile(accel, pctile_lookback)
    m = 1.0 + k * (2.0 * pctile - 1.0)
    m = np.clip(m, min_mult, max_mult)
    # Not enough history yet (accel undefined) -> default to plain DCA.
    m = np.where(np.isnan(accel), 1.0, m)
    return m


def make_momentum_acceleration_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    lookback_days: int = 252, lag_days: int = 126,
    pctile_lookback: int = 252, k: float = 1.0, min_mult: float = 0.5,
    max_mult: float = 2.0, max_lump_multiple: float = 3.0,
    enabled: bool = True, mom_cache: np.ndarray | None = None,
    m_cache: np.ndarray | None = None,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day, which is
    bit-for-bit plain DCA (proves the strategy nests DCA exactly).
    m_cache (a pure performance optimization, no effect on any result):
    a precomputed multiplier array for this exact (lookback_days, lag_days,
    pctile_lookback, k, min_mult) combination, reused across fee levels in
    the run script instead of recomputing the same multiplier twice."""
    if not enabled:
        m = np.ones(len(daily), dtype=float)
    elif m_cache is not None:
        m = m_cache
    else:
        m = compute_multiplier(daily, lookback_days, lag_days, pctile_lookback, k, min_mult,
                                max_mult=max_mult, mom_cache=mom_cache)

    cap = max_lump_multiple * weekly_deposit

    def decide(t, cash):
        target_buy_usd = min(weekly_deposit * float(m[t]), cap)
        # No sells; the engine's own cash cap (sec 3.2) enforces buy_usd<=cash,
        # so a below-1.0-multiplier week simply banks cash (earning IRX) until
        # a later above-1.0-multiplier week can spend it -- never leverage.
        return target_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Trend / time-series momentum exit"

# Grid: lookback_days x lag_days x k x min_mult = 3x2x3x2 = 36 (= 36 cap, 4 params <= 5)
GRID = {
    "lookback_days": [126, 252, 378],
    "lag_days": [63, 126],
    "k": [0.5, 1.0, 1.5],
    "min_mult": [0.25, 0.5],
}
PRIMARY_CONFIG = {
    "lookback_days": 252, "lag_days": 126, "k": 1.0, "min_mult": 0.5,
}
PCTILE_LOOKBACK = 252
MAX_MULT = 2.0
MAX_LUMP_MULTIPLE = 3.0


def grid_configs() -> list[dict]:
    out = []
    for lb in GRID["lookback_days"]:
        for lag in GRID["lag_days"]:
            for k in GRID["k"]:
                for mn in GRID["min_mult"]:
                    out.append({
                        "lookback_days": lb, "lag_days": lag, "k": k, "min_mult": mn,
                    })
    return out


assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG must be a member of grid_configs()"
