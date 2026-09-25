"""Family 019: OECD Composite Leading Indicator (CLI) regime switch.

families/019-oecd-cli-regime/prereg.md has the full mechanism and rules.
Summary: a point-in-time, asset-agnostic macro regime signal (FRED
USALOLITONOSTSAM, the OECD's normalized US composite leading indicator)
is used to bank deposits during "weak" weeks (the trailing-normalized
signal reads below its own threshold) and deploy a capped catch-up lump
during "strong" weeks -- the same banking/cash-cap mechanic families
004/006/007/011/015 use, never leverage or shorting. No sells, ever.

Category: Regime switch (macro).

Structurally modeled directly on src/backtest/v3/strategies/credit_stress_filter.py
(same banking/lump decider shape, same lag -> reindex -> ffill pattern,
same degenerate/placebo-array deciders) -- adapted to CLI's normalization
methods (zscore/percentile) and its own conservative publication lag.

Parameters (4 tunable + 1 fixed, all <=5 total):
  normalization_method  -- "zscore" or "percentile"
  lookback_years         -- trailing window for the normalization
  threshold_level        -- 0/1/2, selects a method-specific numeric threshold
  weak_tilt_fraction      -- fraction of deposit still bought while weak
  max_lump_multiple       -- fixed at 6.0 (not grid-varied), catch-up cap
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import data as v3data

CLI_SERIES_ID = "USALOLITONOSTSAM"

# Publication-lag convention (prereg.md "Point-in-time / publication-lag
# discipline"): USALOLITONOSTSAM is monthly, observation date = 1st of the
# reference month. ALFRED true vintages only cover 2018-07+, so a
# conservative fixed lag stands in for full vintage reconstruction over
# most of the development sample (same choice family 011 made for BAA/AAA).
CLI_LAG_DAYS = 60

ZSCORE_THRESHOLDS = {0: -1.0, 1: -0.5, 2: 0.0}
PCTILE_THRESHOLDS = {0: 20.0, 1: 30.0, 2: 40.0}


def _lagged_pointintime(raw: pd.Series, lag_days: int) -> pd.Series:
    """Shifts each observation forward by lag_days (so it only becomes
    'seen' that many calendar days after its observation date), matching
    src/backtest/v2/regimes.py's fetch-raw -> lag/vintage -> reindex ->
    ffill pattern and credit_stress_filter.py's own helper of the same
    name."""
    s = raw.copy()
    s.index = s.index + pd.Timedelta(days=lag_days)
    return s.sort_index()


def fetch_raw_signal() -> pd.Series:
    """Raw (unlagged) FRED CLI series, as of its own observation date."""
    return v3data.fetch_fred_macro(CLI_SERIES_ID)


def _weak_at_signal_dates(normalization_method: str, lookback_years: int, threshold_level: int,
                           lag_override_days: int | None = None) -> pd.Series:
    """Computes the weak/not-weak boolean at the (few hundred) raw CLI
    observation dates only -- O(n^2) in the signal's own low-frequency
    (monthly, ~800 obs since 1955) observation count, not in the asset's
    daily trading-day count. Index = the point-in-time 'usable from' date
    (observation date + lag). The trailing window is over the signal's OWN
    observation dates (lookback_years*365.25 calendar days), so a monthly
    series' effective lookback in months is unaffected by how many trading
    days any given asset happens to have."""
    raw = fetch_raw_signal()
    lag = lag_override_days if lag_override_days is not None else CLI_LAG_DAYS
    lagged = _lagged_pointintime(raw, lag)
    vals = lagged.to_numpy()
    dates = lagged.index.values.astype("datetime64[D]")
    window_days = int(lookback_years * 365.25)
    n = len(vals)
    weak = np.zeros(n, dtype=bool)

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
            weak[i] = z < threshold
        else:  # percentile
            pct = 100.0 * (window_vals <= vals[i]).mean()
            weak[i] = pct < threshold

    return pd.Series(weak, index=lagged.index)


def compute_weak(daily: pd.DataFrame, normalization_method: str, lookback_years: int,
                  threshold_level: int, lag_override_days: int | None = None) -> np.ndarray:
    """Boolean array, True = weak regime, aligned to daily.index. Uses ONLY
    the point-in-time CLI signal (no asset price). Before the signal's
    first usable ('point-in-time') date, defaults to NOT weak (behaves
    like plain DCA during signal warm-up, per prereg.md)."""
    weak_at_signal_dates = _weak_at_signal_dates(
        normalization_method, lookback_years, threshold_level, lag_override_days
    )
    daily_range = pd.date_range(daily.index.min() - pd.Timedelta(days=1), daily.index.max(), freq="D")
    full = weak_at_signal_dates.reindex(
        weak_at_signal_dates.index.union(daily_range)
    ).sort_index().ffill().reindex(daily_range).fillna(False)
    aligned = full.reindex(daily.index, method="ffill").fillna(False)
    return aligned.to_numpy().astype(bool)


def make_cli_regime_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    normalization_method: str = "zscore", lookback_years: int = 10,
    threshold_level: int = 1, weak_tilt_fraction: float = 0.0,
    max_lump_multiple: float = 6.0, enabled: bool = True,
    _lag_override_days: int | None = None,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the regime computation entirely and
    buys the full week's cash every week-end day (0 otherwise), which is
    bit-for-bit plain DCA. A grid config with weak_tilt_fraction=0 and
    enabled=True is NOT the degenerate case (same "grid-counted marker
    note" families 010/011 already established) -- the regime computation
    still runs."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)
    weak = (
        compute_weak(daily, normalization_method, lookback_years, threshold_level, _lag_override_days)
        if enabled else None
    )

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if weak[t]:
            target_buy_usd = weak_tilt_fraction * weekly_deposit
        else:
            target_buy_usd = min(cash, max_lump_multiple * weekly_deposit)
        return target_buy_usd, 0.0, {"weak": bool(weak[t])}

    return decide


def make_decider_from_weak_array(
    daily: pd.DataFrame, weekly_deposit: float, weak: np.ndarray,
    weak_tilt_fraction: float = 0.0, max_lump_multiple: float = 6.0,
):
    """Same banking/lump decision rule as make_cli_regime_decider, but
    driven by an arbitrary pre-computed `weak` boolean array instead of
    recomputing it from the FRED CLI signal -- used by the placebo
    circular-shift robustness test (sec 4.3), which shifts the regime's
    TIMING while keeping its overall weak/strong frequency identical."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)

    def decide(t, cash):
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if weak[t]:
            target_buy_usd = weak_tilt_fraction * weekly_deposit
        else:
            target_buy_usd = min(cash, max_lump_multiple * weekly_deposit)
        return target_buy_usd, 0.0, {"weak": bool(weak[t])}

    return decide


CATEGORY = "Regime switch (macro)"

# Grid: normalization_method x lookback_years x threshold_level x weak_tilt_fraction
# = 2x2x3x2 = 24 (<=36 cap; max_lump_multiple fixed at 6, not grid-varied)
GRID = {
    "normalization_method": ["zscore", "percentile"],
    "lookback_years": [5, 10],
    "threshold_level": [0, 1, 2],
    "weak_tilt_fraction": [0.0, 0.25],
}
MAX_LUMP_MULTIPLE = 6.0
PRIMARY_CONFIG = {
    "normalization_method": "zscore", "lookback_years": 10,
    "threshold_level": 1, "weak_tilt_fraction": 0.0,
    "max_lump_multiple": MAX_LUMP_MULTIPLE,
}


def grid_configs() -> list[dict]:
    out = []
    for nm in GRID["normalization_method"]:
        for lb in GRID["lookback_years"]:
            for tl in GRID["threshold_level"]:
                for tf in GRID["weak_tilt_fraction"]:
                    out.append({
                        "normalization_method": nm, "lookback_years": lb,
                        "threshold_level": tl, "weak_tilt_fraction": tf,
                        "max_lump_multiple": MAX_LUMP_MULTIPLE,
                    })
    return out
