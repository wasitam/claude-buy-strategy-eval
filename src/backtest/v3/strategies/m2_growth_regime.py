"""Family 032: M2 money-supply growth regime switch.

families/032-m2-growth-regime/prereg.md has the full mechanism and rules.
Summary: a point-in-time, asset-agnostic macro regime signal (FRED M2SL,
the US M2 monetary aggregate) is used to compute a trailing year-over-year
growth rate, trend-normalize it via a trailing z-score, and bank deposits
during "decelerating" weeks (the trend-relative z-score reads below its
own threshold) while deploying a capped catch-up lump during
"accelerating/normal" weeks -- the same banking/cash-cap mechanic families
004/006/007/011/015/019/027 use, never leverage or shorting. No sells,
ever.

Category: Regime switch (macro).

Structurally modeled directly on
src/backtest/v3/strategies/oecd_cli_regime.py (same lag -> reindex -> ffill
pattern, same degenerate/placebo-array decider shapes), adapted to a
growth-rate-then-zscore construction instead of a level-zscore/percentile
construction, and to M2SL's own conservative publication lag.

Parameters (4 tunable + 1 fixed, all <=5 total):
  yoy_window_months   -- months in the M2SL year-over-year growth window
  lookback_years       -- trailing window for the growth rate's own z-score
  threshold_level      -- 0/1/2, selects a z-score threshold
  decel_tilt_fraction   -- fraction of deposit still bought while decelerating
  max_lump_multiple     -- fixed at 6.0 (not grid-varied), catch-up cap
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import data as v3data

M2_SERIES_ID = "M2SL"

# Publication-lag convention (prereg.md "Point-in-time / publication-lag
# discipline"): M2SL is monthly, observation date = 1st of the reference
# month. ALFRED true vintages only cover 1980-02-08+; a conservative fixed
# lag stands in for full vintage reconstruction over the pre-1980 portion
# of the development sample (same choice families 011/019 made for their
# own series).
M2_LAG_DAYS = 45

ZSCORE_THRESHOLDS = {0: -1.0, 1: -0.5, 2: 0.0}


def _lagged_pointintime(raw: pd.Series, lag_days: int) -> pd.Series:
    """Shifts each observation forward by lag_days (so it only becomes
    'seen' that many calendar days after its observation date), matching
    src/backtest/v2/regimes.py's and oecd_cli_regime.py's fetch-raw ->
    lag -> reindex -> ffill pattern."""
    s = raw.copy()
    s.index = s.index + pd.Timedelta(days=lag_days)
    return s.sort_index()


def fetch_raw_signal() -> pd.Series:
    """Raw (unlagged) FRED M2SL series, as of its own observation date."""
    return v3data.fetch_fred_macro(M2_SERIES_ID)


def _decelerating_at_signal_dates(yoy_window_months: int, lookback_years: int, threshold_level: int,
                                   lag_override_days: int | None = None) -> pd.Series:
    """Computes the decelerating/not-decelerating boolean at the (few
    hundred) raw M2SL observation dates only -- O(n^2) in the signal's own
    low-frequency (monthly, ~800 obs since 1959) observation count, not in
    the asset's daily trading-day count. Index = the point-in-time 'usable
    from' date (observation date + lag). Both steps -- the YoY growth rate
    and its own trailing z-score -- are computed entirely from already-
    lagged M2SL levels, so no additional lag is needed for the derived
    series."""
    raw = fetch_raw_signal()
    lag = lag_override_days if lag_override_days is not None else M2_LAG_DAYS
    lagged = _lagged_pointintime(raw, lag)
    vals = lagged.to_numpy()
    dates = lagged.index.values.astype("datetime64[D]")
    n = len(vals)

    # YoY growth rate: g_i = vals[i] / vals[i - yoy_window_months] - 1.
    # M2SL is monthly with one observation per calendar month, so the
    # window is expressed as a fixed number of prior OBSERVATIONS (not
    # calendar days) -- exactly yoy_window_months months back, matching
    # the raw (unlagged) series' own monthly cadence.
    growth = np.full(n, np.nan)
    for i in range(yoy_window_months, n):
        base = vals[i - yoy_window_months]
        if base != 0 and not np.isnan(base):
            growth[i] = vals[i] / base - 1.0

    threshold = ZSCORE_THRESHOLDS[threshold_level]
    window_days = int(lookback_years * 365.25)
    decel = np.zeros(n, dtype=bool)
    for i in range(n):
        if np.isnan(growth[i]):
            continue
        window_start = dates[i] - np.timedelta64(window_days, "D")
        lo = np.searchsorted(dates, window_start, side="left")
        window_growth = growth[lo:i + 1]
        window_growth = window_growth[~np.isnan(window_growth)]
        if len(window_growth) < 2:
            continue
        mu = window_growth.mean()
        sigma = window_growth.std(ddof=1)
        if sigma <= 0:
            continue
        z = (growth[i] - mu) / sigma
        decel[i] = z < threshold

    return pd.Series(decel, index=lagged.index), pd.Series(growth, index=lagged.index)


def compute_decelerating(daily: pd.DataFrame, yoy_window_months: int, lookback_years: int,
                          threshold_level: int, lag_override_days: int | None = None) -> np.ndarray:
    """Boolean array, True = decelerating regime, aligned to daily.index.
    Uses ONLY the point-in-time M2SL signal (no asset price). Before the
    signal's first usable ('point-in-time') date, defaults to NOT
    decelerating (behaves like plain DCA during signal warm-up, per
    prereg.md)."""
    decel_at_signal_dates, _ = _decelerating_at_signal_dates(
        yoy_window_months, lookback_years, threshold_level, lag_override_days
    )
    daily_range = pd.date_range(daily.index.min() - pd.Timedelta(days=1), daily.index.max(), freq="D")
    full = decel_at_signal_dates.reindex(
        decel_at_signal_dates.index.union(daily_range)
    ).sort_index().ffill().reindex(daily_range).fillna(False)
    aligned = full.reindex(daily.index, method="ffill").fillna(False)
    return aligned.to_numpy().astype(bool)


def make_m2_regime_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    yoy_window_months: int = 12, lookback_years: int = 10,
    threshold_level: int = 1, decel_tilt_fraction: float = 0.0,
    max_lump_multiple: float = 6.0, enabled: bool = True,
    _lag_override_days: int | None = None,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the regime computation entirely and
    buys the full week's cash every week-end day (0 otherwise), which is
    bit-for-bit plain DCA. A grid config with decel_tilt_fraction=0 and
    enabled=True is NOT the degenerate case (same "grid-counted marker
    note" families 010/011/019 already established) -- the regime
    computation still runs."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)
    decel = (
        compute_decelerating(daily, yoy_window_months, lookback_years, threshold_level, _lag_override_days)
        if enabled else None
    )

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if decel[t]:
            target_buy_usd = decel_tilt_fraction * weekly_deposit
        else:
            target_buy_usd = min(cash, max_lump_multiple * weekly_deposit)
        return target_buy_usd, 0.0, {"decelerating": bool(decel[t])}

    return decide


def make_decider_from_decel_array(
    daily: pd.DataFrame, weekly_deposit: float, decel: np.ndarray,
    decel_tilt_fraction: float = 0.0, max_lump_multiple: float = 6.0,
):
    """Same banking/lump decision rule as make_m2_regime_decider, but
    driven by an arbitrary pre-computed `decel` boolean array instead of
    recomputing it from the FRED M2SL signal -- used by the placebo
    circular-shift robustness test (sec 4.3), which shifts the regime's
    TIMING while keeping its overall decelerating/normal frequency
    identical."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)

    def decide(t, cash):
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if decel[t]:
            target_buy_usd = decel_tilt_fraction * weekly_deposit
        else:
            target_buy_usd = min(cash, max_lump_multiple * weekly_deposit)
        return target_buy_usd, 0.0, {"decelerating": bool(decel[t])}

    return decide


CATEGORY = "Regime switch (macro)"

# Grid: yoy_window_months x lookback_years x threshold_level x decel_tilt_fraction
# = 2x2x3x2 = 24 (<=36 cap; max_lump_multiple fixed at 6, not grid-varied)
GRID = {
    "yoy_window_months": [6, 12],
    "lookback_years": [5, 10],
    "threshold_level": [0, 1, 2],
    "decel_tilt_fraction": [0.0, 0.25],
}
MAX_LUMP_MULTIPLE = 6.0
PRIMARY_CONFIG = {
    "yoy_window_months": 12, "lookback_years": 10,
    "threshold_level": 1, "decel_tilt_fraction": 0.0,
    "max_lump_multiple": MAX_LUMP_MULTIPLE,
}


def grid_configs() -> list[dict]:
    out = []
    for yw in GRID["yoy_window_months"]:
        for lb in GRID["lookback_years"]:
            for tl in GRID["threshold_level"]:
                for tf in GRID["decel_tilt_fraction"]:
                    out.append({
                        "yoy_window_months": yw, "lookback_years": lb,
                        "threshold_level": tl, "decel_tilt_fraction": tf,
                        "max_lump_multiple": MAX_LUMP_MULTIPLE,
                    })
    return out


assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG must be a member of the declared grid"
