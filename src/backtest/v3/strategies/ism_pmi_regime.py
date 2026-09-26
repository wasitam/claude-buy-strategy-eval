"""Family 052: ISM Manufacturing PMI regime deposit sizing.

families/052-ism-pmi-regime/prereg.md has the full mechanism, the
required reachability investigation (FRED's ISM/NAPM series is
discontinued; DBnomics/forecasts.org/eco3min.fr/ycharts.com/multpl.com
were all EGRESS_BLOCKED), the disclosed reconstruction methodology, and
the required concrete divergence example against family 019's OECD CLI.
Summary: a point-in-time, asset-agnostic macro regime signal (the ISM
Manufacturing PMI, a single monthly business-survey diffusion index) is
used to bank deposits during "weak" months (percentile-rank of the level
within its own trailing lookback window < weak_pctile, confirmed for
persistence_months consecutive monthly observations) and deploy a capped
catch-up lump during "strong" months -- the same banking/cash-cap
mechanic families 006/007/010/011/019/032/050 use, never leverage or
shorting. No sells, ever.

Category: Regime switch (macro / credit / sentiment).

Parameters (4 tunable + 1 fixed, all <=5 total):
  lookback_years       -- trailing window (years) for the regime percentile rank
  weak_pctile          -- percentile threshold marking "weak"
  weak_tilt_fraction    -- fraction of deposit still bought while weak
  persistence_months   -- consecutive weak monthly observations required to
                           flip the regime to weak (whipsaw filter); flipping
                           back to strong has no persistence requirement
  max_lump_multiple    -- fixed at 6.0 (not grid-varied), catch-up cap

Data: the PMI series is NOT a live fetch (see prereg.md "Required step
1" -- NAPM and every other plausible FRED mnemonic returned 404, a live
FRED site search for "ISM Manufacturing PMI" returned 0 results, and
DBnomics/forecasts.org/eco3min.fr/ycharts.com/multpl.com were all
EGRESS_BLOCKED in this session). Per the task's explicit allowance for
this contingency (the same allowance family 051 used for its hard-coded
FOMC calendar), the monthly PMI level is reconstructed below from ANCHOR
points at specific, well-documented historical levels/turning points
(this session's own training-era knowledge), with monthly values between
anchors linearly interpolated -- never independently recalled month by
month. Confidence is materially higher for 1990-2019, materially lower
for 1948-1989 (a stylized cyclical reconstruction keyed to NBER
recession/expansion dates); see prereg.md for the full disclosure. Kept
as a hard-coded constant directly in this module (not a data/*.csv file)
because data/*.csv is gitignored as a live-fetch cache directory in this
repo, and this is deliberately NOT a live fetch -- the same reasoning
family 051 used to hard-code its FOMC dates directly in
pre_fomc_drift.py rather than in a data file. Because this never touches
fetch_fred_macro(), fetch_yf_macro(), load_dev() or open_holdout(), the
raw-data-leak static check's allowlist needs no changes for this family.
scripts/v3/build_ism_pmi_reconstructed.py mirrors this ANCHORS list for
documentation/inspection purposes only (writes a CSV a reviewer can open;
not used by this module or by the run script).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Publication-lag convention (prereg.md "Required step 2"): the ISM
# releases month M's PMI on the first business day of month M+1 (~32
# calendar days after the reference month's 1st). A conservative 35-
# calendar-day lag is applied, matching family 050/019's own
# "safety margin over the documented schedule" convention.
PMI_LAG_DAYS = 35

# (year-month, PMI level) anchor points, 1948-01 through 2019-12 (the dev
# period only -- this backtest never uses a date on or after 2020-01-01).
# See module docstring and prereg.md "Required step 1" for the full
# sourcing/confidence discussion.
ANCHORS = [
    ("1948-01", 52.0), ("1948-11", 45.0), ("1949-06", 36.0), ("1949-10", 40.0),
    ("1950-03", 58.0), ("1950-09", 75.0), ("1951-06", 58.0), ("1952-06", 52.0),
    ("1953-01", 58.0), ("1953-07", 50.0), ("1954-05", 38.0), ("1955-06", 62.0),
    ("1956-06", 55.0), ("1957-08", 48.0), ("1958-04", 39.0), ("1958-10", 55.0),
    ("1959-06", 60.0), ("1960-04", 48.0), ("1961-02", 42.0), ("1962-06", 56.0),
    ("1965-06", 62.0), ("1966-06", 58.0), ("1968-06", 56.0), ("1969-12", 50.0),
    ("1970-11", 40.0), ("1971-06", 55.0), ("1972-06", 58.0), ("1973-06", 62.0),
    ("1973-11", 55.0), ("1974-06", 45.0), ("1975-03", 33.0), ("1975-09", 48.0),
    ("1976-06", 55.0), ("1977-06", 58.0), ("1978-06", 60.0), ("1979-06", 55.0),
    ("1980-01", 45.0), ("1980-07", 40.0), ("1980-10", 50.0), ("1981-07", 48.0),
    ("1982-06", 38.0), ("1982-11", 33.0), ("1983-06", 55.0), ("1984-01", 69.0),
    ("1984-06", 60.0), ("1985-06", 50.0), ("1986-06", 52.0), ("1987-06", 58.0),
    ("1988-06", 60.0), ("1989-06", 52.0), ("1990-01", 50.0), ("1990-07", 47.0),
    ("1990-10", 40.0), ("1991-01", 39.0), ("1991-03", 40.0), ("1991-09", 48.0),
    ("1992-06", 55.0), ("1993-06", 50.0), ("1994-01", 56.0), ("1994-06", 58.0),
    ("1994-12", 60.0), ("1995-06", 47.0), ("1995-12", 46.5), ("1996-06", 51.0),
    ("1997-06", 55.0), ("1998-01", 49.0), ("1998-08", 47.0), ("1998-12", 46.2),
    ("1999-06", 50.0), ("1999-12", 55.0), ("2000-06", 56.0), ("2000-08", 49.5),
    ("2001-01", 41.2), ("2001-03", 43.0), ("2001-09", 47.0), ("2001-11", 44.5),
    ("2001-12", 43.7), ("2002-02", 49.9), ("2002-06", 56.0), ("2002-12", 52.0),
    ("2003-03", 46.0), ("2003-06", 49.8), ("2003-12", 59.0), ("2004-01", 63.6),
    ("2004-06", 61.0), ("2004-12", 58.0), ("2005-06", 53.0), ("2005-12", 57.0),
    ("2006-06", 54.0), ("2006-12", 51.4), ("2007-06", 56.0), ("2007-12", 48.4),
    ("2008-06", 49.5), ("2008-09", 43.5), ("2008-10", 38.9), ("2008-11", 36.2),
    ("2008-12", 32.9), ("2009-01", 35.6), ("2009-06", 44.8), ("2009-08", 52.9),
    ("2009-12", 54.9), ("2010-05", 59.7), ("2010-12", 56.8), ("2011-06", 55.3),
    ("2011-11", 52.7), ("2012-07", 49.8), ("2012-12", 50.7), ("2013-06", 50.9),
    ("2013-12", 57.0), ("2014-08", 59.0), ("2014-12", 55.1), ("2015-06", 53.5),
    ("2015-11", 48.6), ("2015-12", 48.0), ("2016-01", 48.2), ("2016-08", 49.4),
    ("2016-09", 51.5), ("2016-12", 54.5), ("2017-06", 57.8), ("2017-12", 59.7),
    ("2018-08", 61.3), ("2018-12", 54.1), ("2019-01", 56.6), ("2019-06", 51.7),
    ("2019-08", 49.1), ("2019-10", 48.3), ("2019-12", 47.2),
]


def _lagged_pointintime(raw: pd.Series, lag_days: int) -> pd.Series:
    """Shifts each observation forward by lag_days (so it only becomes
    'seen' that many calendar days after its observation date), matching
    families 011/019/032/050's fetch-raw -> lag -> reindex -> ffill
    pattern."""
    s = raw.copy()
    s.index = s.index + pd.Timedelta(days=lag_days)
    return s.sort_index()


def fetch_raw_signal() -> pd.Series:
    """Raw (unlagged) reconstructed ISM PMI series, as of its own
    observation date (the 1st of the reference month). NOT a live fetch
    -- built by linear interpolation between the hard-coded ANCHORS above.
    See module docstring and prereg.md."""
    idx = pd.to_datetime([f"{ym}-01" for ym, _ in ANCHORS])
    vals = [v for _, v in ANCHORS]
    anchor_series = pd.Series(vals, index=idx).sort_index()
    full_idx = pd.date_range(anchor_series.index.min(), anchor_series.index.max(), freq="MS")
    monthly = anchor_series.reindex(anchor_series.index.union(full_idx)).sort_index()
    monthly = monthly.interpolate(method="index").reindex(full_idx)
    return monthly.dropna().sort_index()


def _weak_at_signal_dates(lookback_years: int, weak_pctile: float,
                           persistence_months: int,
                           lag_override_days: int | None = None) -> pd.Series:
    """Computes the weak/not-weak boolean at the (few hundred) raw PMI
    observation dates only. Index = the point-in-time 'usable from' date
    (observation date + lag). Percentile rank is computed over a trailing
    window of lookback_years*365.25 calendar days of the signal's OWN
    observation dates. The regime flips to weak only after
    persistence_months consecutive raw-percentile-weak observations in a
    row; it flips back to strong on the first observation whose
    percentile is at/above the threshold (asymmetric, matching family
    050's 'confirmed weakness, immediate release' rule)."""
    raw = fetch_raw_signal()
    lag = lag_override_days if lag_override_days is not None else PMI_LAG_DAYS
    lagged = _lagged_pointintime(raw, lag)
    vals = lagged.to_numpy()
    dates = lagged.index.values.astype("datetime64[D]")
    window_days = int(lookback_years * 365.25)
    n = len(vals)
    raw_weak = np.zeros(n, dtype=bool)
    for i in range(n):
        window_start = dates[i] - np.timedelta64(window_days, "D")
        lo = np.searchsorted(dates, window_start, side="left")
        window_vals = vals[lo:i + 1]
        if len(window_vals) < 2:
            continue
        pct = 100.0 * (window_vals <= vals[i]).mean()
        raw_weak[i] = pct < weak_pctile

    weak = np.zeros(n, dtype=bool)
    run = 0
    state = False
    for i in range(n):
        if raw_weak[i]:
            run += 1
        else:
            run = 0
            state = False
        if run >= persistence_months:
            state = True
        weak[i] = state
    return pd.Series(weak, index=lagged.index)


def compute_weak(daily: pd.DataFrame, lookback_years: int, weak_pctile: float,
                  persistence_months: int = 1,
                  lag_override_days: int | None = None) -> np.ndarray:
    """Boolean array, True = weak regime, aligned to daily.index. Uses
    ONLY the point-in-time PMI signal (no asset price). Before the
    signal's first usable ('point-in-time') date (1948-01 + lag),
    defaults to NOT weak (behaves like plain DCA during signal warm-up,
    per prereg.md)."""
    weak_at_signal_dates = _weak_at_signal_dates(
        lookback_years, weak_pctile, persistence_months, lag_override_days
    )
    daily_range = pd.date_range(daily.index.min() - pd.Timedelta(days=1), daily.index.max(), freq="D")
    full = weak_at_signal_dates.reindex(
        weak_at_signal_dates.index.union(daily_range)
    ).sort_index().ffill().reindex(daily_range).fillna(False)
    aligned = full.reindex(daily.index, method="ffill").fillna(False)
    return aligned.to_numpy().astype(bool)


def make_ism_pmi_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    lookback_years: int = 10, weak_pctile: float = 30.0,
    weak_tilt_fraction: float = 0.0, persistence_months: int = 1,
    max_lump_multiple: float = 6.0, enabled: bool = True,
    _lag_override_days: int | None = None,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the regime computation entirely and
    buys the full week's cash every week-end day (0 otherwise), which is
    bit-for-bit plain DCA. A grid config with weak_tilt_fraction=0 and
    enabled=True is NOT the degenerate case (families 010/011/019/032/050's
    documented marker-note precedent) -- the regime computation still
    runs."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)
    weak = (
        compute_weak(daily, lookback_years, weak_pctile, persistence_months, _lag_override_days)
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
    """Same banking/lump decision rule as make_ism_pmi_decider, but driven
    by an arbitrary pre-computed `weak` boolean array instead of
    recomputing it from the reconstructed series -- used by the placebo
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


CATEGORY = "Regime switch (macro / credit / sentiment)"

# Grid: lookback_years x weak_pctile x weak_tilt_fraction x
# persistence_months = 2x3x2x2 = 24 (<=36 cap; max_lump_multiple fixed at
# 6, not grid-varied)
GRID = {
    "lookback_years": [5, 10],
    "weak_pctile": [20, 30, 40],
    "weak_tilt_fraction": [0.0, 0.25],
    "persistence_months": [1, 2],
}
MAX_LUMP_MULTIPLE = 6.0
PRIMARY_CONFIG = {
    "lookback_years": 10, "weak_pctile": 30,
    "weak_tilt_fraction": 0.0, "persistence_months": 1,
    "max_lump_multiple": MAX_LUMP_MULTIPLE,
}


def grid_configs() -> list[dict]:
    out = []
    for lb in GRID["lookback_years"]:
        for pc in GRID["weak_pctile"]:
            for tf in GRID["weak_tilt_fraction"]:
                for pm in GRID["persistence_months"]:
                    out.append({
                        "lookback_years": lb, "weak_pctile": pc,
                        "weak_tilt_fraction": tf, "persistence_months": pm,
                        "max_lump_multiple": MAX_LUMP_MULTIPLE,
                    })
    return out


assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG must be a member of grid_configs()"
