"""Family 038: Consumer-sentiment contrarian regime.

families/038-consumer-sentiment-contrarian/prereg.md has the full mechanism
and rules. Summary: a point-in-time, asset-agnostic macro/sentiment regime
signal (FRED UMCSENT, the University of Michigan Consumer Sentiment Index)
is trend-normalized via a trailing zscore/percentile, and banks deposits
during "euphoric" weeks (the normalized signal reads AT OR ABOVE its own
threshold -- the mirror-image direction of families 019/032's "below
threshold = weak" convention, since this family's mechanism is contrarian
on ELEVATED sentiment) while deploying a capped catch-up lump during
"normal/depressed" weeks -- the same banking/cash-cap mechanic families
004/006/007/011/015/016/019/027/032 use, never leverage or shorting. No
sells, ever.

Category: Regime switch (macro / credit / sentiment).

Structurally modeled directly on
src/backtest/v3/strategies/m2_growth_regime.py (same lag -> reindex ->
ffill pattern, same degenerate/placebo-array decider shapes), adapted to
UMCSENT's own trend-normalization-only construction (no growth-rate step,
since a sentiment INDEX level is the direct object of interest here, not a
level's own growth rate the way M2's monetary-quantity mechanism required)
and to UMCSENT's own conservative publication lag and ABOVE-threshold
(contrarian) trigger direction.

Parameters (4 tunable + 1 fixed, all <=5 total):
  normalization_method   -- "zscore" or "percentile"
  lookback_years          -- trailing window for the normalization
  threshold_level         -- 0/1/2, selects a method-specific numeric threshold
  euphoric_tilt_fraction   -- fraction of deposit still bought while euphoric
  max_lump_multiple        -- fixed at 6.0 (not grid-varied), catch-up cap
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import data as v3data

SENTIMENT_SERIES_ID = "UMCSENT"

# Publication-lag convention (prereg.md "Point-in-time / publication-lag
# discipline"): UMCSENT is monthly, observation date = 1st of the reference
# month, with both a preliminary (mid-month) and final (end-of-month)
# reading published WITHIN that same reference month. A 35-calendar-day lag
# is comfortably past even the final release for that same month.
SENTIMENT_LAG_DAYS = 35

ZSCORE_THRESHOLDS = {0: 0.5, 1: 1.0, 2: 1.5}
PCTILE_THRESHOLDS = {0: 80.0, 1: 90.0, 2: 95.0}


def _lagged_pointintime(raw: pd.Series, lag_days: int) -> pd.Series:
    """Shifts each observation forward by lag_days (so it only becomes
    'seen' that many calendar days after its observation date), matching
    src/backtest/v2/regimes.py's and oecd_cli_regime.py's/m2_growth_regime.py's
    fetch-raw -> lag -> reindex -> ffill pattern."""
    s = raw.copy()
    s.index = s.index + pd.Timedelta(days=lag_days)
    return s.sort_index()


def fetch_raw_signal() -> pd.Series:
    """Raw (unlagged) FRED UMCSENT series, as of its own observation date."""
    return v3data.fetch_fred_macro(SENTIMENT_SERIES_ID)


def _euphoric_at_signal_dates(normalization_method: str, lookback_years: int, threshold_level: int,
                               lag_override_days: int | None = None) -> tuple[pd.Series, pd.Series]:
    """Computes the euphoric/not-euphoric boolean at the (few hundred) raw
    UMCSENT observation dates only -- O(n^2) in the signal's own
    low-frequency (monthly, ~670 obs since 1952) observation count, not in
    the asset's daily trading-day count. Index = the point-in-time 'usable
    from' date (observation date + lag)."""
    raw = fetch_raw_signal()
    lag = lag_override_days if lag_override_days is not None else SENTIMENT_LAG_DAYS
    lagged = _lagged_pointintime(raw, lag)
    vals = lagged.to_numpy()
    dates = lagged.index.values.astype("datetime64[D]")
    window_days = int(lookback_years * 365.25)
    n = len(vals)
    euphoric = np.zeros(n, dtype=bool)
    stat = np.full(n, np.nan)

    if normalization_method == "zscore":
        threshold = ZSCORE_THRESHOLDS[threshold_level]
    elif normalization_method == "percentile":
        threshold = PCTILE_THRESHOLDS[threshold_level]
    else:
        raise ValueError(f"unknown normalization_method {normalization_method!r}")

    for i in range(n):
        window_start = dates[i] - np.timedelta64(window_days, "D")
        lo = np.searchsorted(dates, window_start, side="left")
        window_vals = vals[lo:i + 1]
        if len(window_vals) < 2:
            continue
        if normalization_method == "zscore":
            mu = window_vals.mean()
            sigma = window_vals.std(ddof=1)
            if sigma <= 0:
                continue
            z = (vals[i] - mu) / sigma
            stat[i] = z
            euphoric[i] = z >= threshold
        else:  # percentile
            pct = 100.0 * (window_vals <= vals[i]).mean()
            stat[i] = pct
            euphoric[i] = pct >= threshold

    return pd.Series(euphoric, index=lagged.index), pd.Series(stat, index=lagged.index)


def compute_euphoric(daily: pd.DataFrame, normalization_method: str, lookback_years: int,
                      threshold_level: int, lag_override_days: int | None = None) -> np.ndarray:
    """Boolean array, True = euphoric regime, aligned to daily.index. Uses
    ONLY the point-in-time UMCSENT signal (no asset price). Before the
    signal's first usable ('point-in-time') date, defaults to NOT euphoric
    (behaves like plain DCA during signal warm-up, per prereg.md)."""
    euphoric_at_signal_dates, _ = _euphoric_at_signal_dates(
        normalization_method, lookback_years, threshold_level, lag_override_days
    )
    daily_range = pd.date_range(daily.index.min() - pd.Timedelta(days=1), daily.index.max(), freq="D")
    full = euphoric_at_signal_dates.reindex(
        euphoric_at_signal_dates.index.union(daily_range)
    ).sort_index().ffill().reindex(daily_range).fillna(False)
    aligned = full.reindex(daily.index, method="ffill").fillna(False)
    return aligned.to_numpy().astype(bool)


def make_sentiment_regime_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    normalization_method: str = "zscore", lookback_years: int = 10,
    threshold_level: int = 1, euphoric_tilt_fraction: float = 0.0,
    max_lump_multiple: float = 6.0, enabled: bool = True,
    _lag_override_days: int | None = None,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the regime computation entirely and
    buys the full week's cash every week-end day (0 otherwise), which is
    bit-for-bit plain DCA. A grid config with euphoric_tilt_fraction=0 and
    enabled=True is NOT the degenerate case (same "grid-counted marker
    note" families 010/011/019/032 already established) -- the regime
    computation still runs."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)
    euphoric = (
        compute_euphoric(daily, normalization_method, lookback_years, threshold_level, _lag_override_days)
        if enabled else None
    )

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if euphoric[t]:
            target_buy_usd = euphoric_tilt_fraction * weekly_deposit
        else:
            target_buy_usd = min(cash, max_lump_multiple * weekly_deposit)
        return target_buy_usd, 0.0, {"euphoric": bool(euphoric[t])}

    return decide


def make_decider_from_euphoric_array(
    daily: pd.DataFrame, weekly_deposit: float, euphoric: np.ndarray,
    euphoric_tilt_fraction: float = 0.0, max_lump_multiple: float = 6.0,
):
    """Same banking/lump decision rule as make_sentiment_regime_decider, but
    driven by an arbitrary pre-computed `euphoric` boolean array instead of
    recomputing it from the FRED UMCSENT signal -- used by the placebo
    circular-shift robustness test (sec 4.3), which shifts the regime's
    TIMING while keeping its overall euphoric/normal frequency identical."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)

    def decide(t, cash):
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if euphoric[t]:
            target_buy_usd = euphoric_tilt_fraction * weekly_deposit
        else:
            target_buy_usd = min(cash, max_lump_multiple * weekly_deposit)
        return target_buy_usd, 0.0, {"euphoric": bool(euphoric[t])}

    return decide


CATEGORY = "Regime switch (macro / credit / sentiment)"

# Grid: normalization_method x lookback_years x threshold_level x euphoric_tilt_fraction
# = 2x2x3x2 = 24 (<=36 cap; max_lump_multiple fixed at 6, not grid-varied)
GRID = {
    "normalization_method": ["zscore", "percentile"],
    "lookback_years": [5, 10],
    "threshold_level": [0, 1, 2],
    "euphoric_tilt_fraction": [0.0, 0.25],
}
MAX_LUMP_MULTIPLE = 6.0
PRIMARY_CONFIG = {
    "normalization_method": "zscore", "lookback_years": 10,
    "threshold_level": 1, "euphoric_tilt_fraction": 0.0,
    "max_lump_multiple": MAX_LUMP_MULTIPLE,
}


def grid_configs() -> list[dict]:
    out = []
    for nm in GRID["normalization_method"]:
        for lb in GRID["lookback_years"]:
            for tl in GRID["threshold_level"]:
                for tf in GRID["euphoric_tilt_fraction"]:
                    out.append({
                        "normalization_method": nm, "lookback_years": lb,
                        "threshold_level": tl, "euphoric_tilt_fraction": tf,
                        "max_lump_multiple": MAX_LUMP_MULTIPLE,
                    })
    return out


assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG must be a member of the declared grid"
