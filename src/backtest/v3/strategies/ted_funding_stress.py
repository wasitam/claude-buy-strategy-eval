"""Family 050: money-market funding-stress (TED spread) regime sizing.

families/050-ted-funding-stress/prereg.md has the full mechanism and
rules. Summary: a point-in-time, asset-agnostic macro regime signal (the
TED spread, FRED TEDRATE -- 3-month LIBOR minus the 3-month T-bill yield,
the classic interbank funding/liquidity-stress gauge) is used to bank
deposits during "stressed" weeks (percentile-rank of the signal within
its own trailing lookback window >= stress_pctile, confirmed for
persistence_days consecutive observations) and deploy a capped catch-up
lump during "calm" weeks -- the same banking/cash-cap mechanic families
006/007/010/011/019/032 use, never leverage or shorting. No sells, ever.

Category: Regime switch (macro / credit / sentiment).

Parameters (4 tunable + 1 fixed, all <=5 total):
  lookback_years         -- trailing window for the regime percentile rank
  stress_pctile          -- percentile threshold marking "stressed"
  stress_tilt_fraction   -- fraction of deposit still bought while stressed
  persistence_days       -- consecutive stressed observations required to
                             flip the regime to stressed (whipsaw filter);
                             flipping back to calm has no persistence
                             requirement
  max_lump_multiple      -- fixed at 6.0 (not grid-varied), catch-up cap
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import data as v3data

# Publication-lag convention (prereg.md "Point-in-time / publication-lag
# discipline"): TEDRATE is a daily, market-quoted, never-revised rate
# spread -- no meaningful economic lag, but a conservative 2-calendar-day
# lag is applied anyway, matching family 027's own convention for a daily
# market-quoted FRED series (T10Y2Y).
TED_LAG_DAYS = 2


def _lagged_pointintime(raw: pd.Series, lag_days: int) -> pd.Series:
    """Shifts each observation forward by lag_days (so it only becomes
    'seen' that many calendar days after its observation date), matching
    families 011/019/027/032's fetch-raw -> lag -> reindex -> ffill
    pattern."""
    s = raw.copy()
    s.index = s.index + pd.Timedelta(days=lag_days)
    return s.sort_index()


def fetch_raw_signal() -> pd.Series:
    """Raw (unlagged) FRED TEDRATE series, as of its own observation date."""
    return v3data.fetch_fred_macro("TEDRATE").dropna()


def _stressed_at_signal_dates(lookback_years: int, stress_pctile: float,
                               persistence_days: int,
                               lag_override_days: int | None = None) -> pd.Series:
    """Computes the stressed/not-stressed boolean at the (few thousand)
    raw TEDRATE observation dates only -- O(n^2) in the signal's own daily
    observation count (~8,850 since 1986), not in the asset's (possibly
    much larger, e.g. SP500 since 1927) daily trading-day count. Index =
    the point-in-time 'usable from' date (observation date + lag).
    Percentile rank is computed over a trailing window of
    lookback_years*365.25 calendar days of the signal's OWN observation
    dates. The regime flips to stressed only after persistence_days
    consecutive raw-percentile-stressed observations in a row; it flips
    back to calm on the first observation whose percentile drops below
    the threshold (asymmetric, matching prereg.md's "confirmed stress,
    immediate release" rule)."""
    raw = fetch_raw_signal()
    lag = lag_override_days if lag_override_days is not None else TED_LAG_DAYS
    lagged = _lagged_pointintime(raw, lag)
    vals = lagged.to_numpy()
    dates = lagged.index.values.astype("datetime64[D]")
    window_days = int(lookback_years * 365.25)
    n = len(vals)
    raw_stressed = np.zeros(n, dtype=bool)
    for i in range(n):
        window_start = dates[i] - np.timedelta64(window_days, "D")
        lo = np.searchsorted(dates, window_start, side="left")
        window_vals = vals[lo:i + 1]
        if len(window_vals) < 2:
            continue
        pct = 100.0 * (window_vals <= vals[i]).mean()
        raw_stressed[i] = pct >= stress_pctile

    stressed = np.zeros(n, dtype=bool)
    run = 0
    state = False
    for i in range(n):
        if raw_stressed[i]:
            run += 1
        else:
            run = 0
            state = False
        if run >= persistence_days:
            state = True
        stressed[i] = state
    return pd.Series(stressed, index=lagged.index)


def compute_stressed(daily: pd.DataFrame, lookback_years: int, stress_pctile: float,
                      persistence_days: int = 1,
                      lag_override_days: int | None = None) -> np.ndarray:
    """Boolean array, True = stressed regime, aligned to daily.index. Uses
    ONLY the point-in-time TED signal (no asset price). Before the
    signal's first usable ('point-in-time') date, defaults to NOT stressed
    (behaves like plain DCA during signal warm-up, per prereg.md)."""
    stressed_at_signal_dates = _stressed_at_signal_dates(
        lookback_years, stress_pctile, persistence_days, lag_override_days
    )
    daily_range = pd.date_range(daily.index.min() - pd.Timedelta(days=1), daily.index.max(), freq="D")
    full = stressed_at_signal_dates.reindex(
        stressed_at_signal_dates.index.union(daily_range)
    ).sort_index().ffill().reindex(daily_range).fillna(False)
    aligned = full.reindex(daily.index, method="ffill").fillna(False)
    return aligned.to_numpy().astype(bool)


def make_ted_stress_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    lookback_years: int = 10, stress_pctile: float = 80.0,
    stress_tilt_fraction: float = 0.0, persistence_days: int = 1,
    max_lump_multiple: float = 6.0, enabled: bool = True,
    _lag_override_days: int | None = None,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the regime computation entirely and
    buys the full week's cash every week-end day (0 otherwise), which is
    bit-for-bit plain DCA. A grid config with stress_tilt_fraction=0 and
    enabled=True is NOT the degenerate case (families 010/011/019/032's
    documented marker-note precedent) -- the regime computation still
    runs."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)
    stressed = (
        compute_stressed(daily, lookback_years, stress_pctile, persistence_days, _lag_override_days)
        if enabled else None
    )

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if stressed[t]:
            target_buy_usd = stress_tilt_fraction * weekly_deposit
        else:
            target_buy_usd = min(cash, max_lump_multiple * weekly_deposit)
        return target_buy_usd, 0.0, {"stressed": bool(stressed[t])}

    return decide


def make_decider_from_stressed_array(
    daily: pd.DataFrame, weekly_deposit: float, stressed: np.ndarray,
    stress_tilt_fraction: float = 0.0, max_lump_multiple: float = 6.0,
):
    """Same banking/lump decision rule as make_ted_stress_decider, but
    driven by an arbitrary pre-computed `stressed` boolean array instead
    of recomputing it from FRED -- used by the placebo circular-shift
    robustness test (sec 4.3), which shifts the regime's TIMING while
    keeping its overall stressed/calm frequency identical."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)

    def decide(t, cash):
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if stressed[t]:
            target_buy_usd = stress_tilt_fraction * weekly_deposit
        else:
            target_buy_usd = min(cash, max_lump_multiple * weekly_deposit)
        return target_buy_usd, 0.0, {"stressed": bool(stressed[t])}

    return decide


CATEGORY = "Regime switch (macro / credit / sentiment)"

# Grid: lookback_years x stress_pctile x stress_tilt_fraction x
# persistence_days = 2x3x2x2 = 24 (<=36 cap; max_lump_multiple fixed at 6,
# not grid-varied)
GRID = {
    "lookback_years": [5, 10],
    "stress_pctile": [70, 80, 90],
    "stress_tilt_fraction": [0.0, 0.25],
    "persistence_days": [1, 3],
}
MAX_LUMP_MULTIPLE = 6.0
PRIMARY_CONFIG = {
    "lookback_years": 10, "stress_pctile": 80,
    "stress_tilt_fraction": 0.0, "persistence_days": 1,
    "max_lump_multiple": MAX_LUMP_MULTIPLE,
}


def grid_configs() -> list[dict]:
    out = []
    for lb in GRID["lookback_years"]:
        for pc in GRID["stress_pctile"]:
            for tf in GRID["stress_tilt_fraction"]:
                for pd_ in GRID["persistence_days"]:
                    out.append({
                        "lookback_years": lb, "stress_pctile": pc,
                        "stress_tilt_fraction": tf, "persistence_days": pd_,
                        "max_lump_multiple": MAX_LUMP_MULTIPLE,
                    })
    return out


assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG must be a member of grid_configs()"
