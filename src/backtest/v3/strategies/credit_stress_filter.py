"""Family 011: credit-stress risk-off filter (Gilchrist & Zakrajsek 2012).

families/011-credit-stress-filter/prereg.md has the full mechanism and
rules. Summary: a point-in-time, asset-agnostic macro regime signal (the
BAA-AAA corporate credit spread, or the Chicago Fed NFCI) is used to bank
deposits during "stressed" weeks (percentile-rank of the signal within its
own trailing lookback window >= stress_pctile) and deploy a capped
catch-up lump during "calm" weeks -- the same banking/cash-cap mechanic
families 006/007/010 use, never leverage or shorting. No sells, ever.

Category: Regime switch (macro / credit / sentiment).

Parameters (4 tunable + 1 fixed, all <=5 total):
  signal_choice          -- "credit_spread" (BAA-AAA) or "nfci"
  lookback_years         -- trailing window for the regime percentile rank
  stress_pctile          -- percentile threshold marking "stressed"
  stress_tilt_fraction   -- fraction of deposit still bought while stressed
  max_lump_multiple      -- fixed at 6.0 (not grid-varied), catch-up cap
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import data as v3data

# Publication-lag convention (prereg.md "Point-in-time / publication-lag
# discipline"): BAA/AAA are monthly, observation date = 1st of month;
# NFCI is weekly, observation date = the index-week's Friday.
CREDIT_SPREAD_LAG_DAYS = 45
NFCI_LAG_DAYS = 8


def _lagged_pointintime(raw: pd.Series, lag_days: int) -> pd.Series:
    """Shifts each observation forward by lag_days (so it only becomes
    'seen' that many calendar days after its observation date), matching
    src/backtest/v2/regimes.py's fetch-raw -> lag/vintage -> reindex ->
    ffill pattern."""
    s = raw.copy()
    s.index = s.index + pd.Timedelta(days=lag_days)
    return s.sort_index()


def fetch_raw_signal(signal_choice: str) -> pd.Series:
    """Raw (unlagged) FRED series, as of its own observation date."""
    if signal_choice == "credit_spread":
        baa = v3data.fetch_fred_macro("BAA")
        aaa = v3data.fetch_fred_macro("AAA")
        idx = baa.index.union(aaa.index)
        return (baa.reindex(idx).ffill() - aaa.reindex(idx).ffill()).dropna()
    elif signal_choice == "nfci":
        return v3data.fetch_fred_macro("NFCI")
    else:
        raise ValueError(f"unknown signal_choice {signal_choice!r}")


def _stressed_at_signal_dates(signal_choice: str, lookback_years: int, stress_pctile: float,
                               lag_override_days: int | None = None) -> pd.Series:
    """Computes the stressed/not-stressed boolean at the (few hundred) raw
    signal observation dates only -- O(n^2) in the signal's own low-
    frequency observation count (~1300 for monthly BAA/AAA since 1919,
    ~2900 for weekly NFCI since 1971), not in the asset's daily trading-day
    count, which would make this quadratic in the wrong (large) dimension.
    Index = the point-in-time 'usable from' date (observation date + lag).
    Percentile rank is computed over a trailing window of
    lookback_years*365.25 calendar days of the signal's OWN observation
    dates, so a monthly series' effective lookback in months is unaffected
    by how many trading days any given asset happens to have."""
    raw = fetch_raw_signal(signal_choice)
    lag = lag_override_days if lag_override_days is not None else (
        CREDIT_SPREAD_LAG_DAYS if signal_choice == "credit_spread" else NFCI_LAG_DAYS
    )
    lagged = _lagged_pointintime(raw, lag)
    vals = lagged.to_numpy()
    dates = lagged.index.values.astype("datetime64[D]")
    window_days = int(lookback_years * 365.25)
    n = len(vals)
    stressed = np.zeros(n, dtype=bool)
    for i in range(n):
        window_start = dates[i] - np.timedelta64(window_days, "D")
        lo = np.searchsorted(dates, window_start, side="left")
        window_vals = vals[lo:i + 1]
        if len(window_vals) < 2:
            continue
        pct = 100.0 * (window_vals <= vals[i]).mean()
        stressed[i] = pct >= stress_pctile
    return pd.Series(stressed, index=lagged.index)


def compute_stressed(daily: pd.DataFrame, signal_choice: str, lookback_years: int,
                      stress_pctile: float, lag_override_days: int | None = None) -> np.ndarray:
    """Boolean array, True = stressed regime, aligned to daily.index. Uses
    ONLY the point-in-time signal (no asset price). Before the signal's
    first usable ('point-in-time') date, defaults to NOT stressed (behaves
    like plain DCA during signal warm-up, per prereg.md)."""
    stressed_at_signal_dates = _stressed_at_signal_dates(
        signal_choice, lookback_years, stress_pctile, lag_override_days
    )
    daily_range = pd.date_range(daily.index.min() - pd.Timedelta(days=1), daily.index.max(), freq="D")
    full = stressed_at_signal_dates.reindex(
        stressed_at_signal_dates.index.union(daily_range)
    ).sort_index().ffill().reindex(daily_range).fillna(False)
    aligned = full.reindex(daily.index, method="ffill").fillna(False)
    return aligned.to_numpy().astype(bool)


def make_credit_stress_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    signal_choice: str = "credit_spread", lookback_years: int = 10,
    stress_pctile: float = 80.0, stress_tilt_fraction: float = 0.0,
    max_lump_multiple: float = 6.0, enabled: bool = True,
    _lag_override_days: int | None = None,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the regime computation entirely and
    buys the full week's cash every week-end day (0 otherwise), which is
    bit-for-bit plain DCA. A grid config with stress_tilt_fraction=0 and
    enabled=True is NOT the degenerate case (prereg.md "Grid-counted
    marker note") -- the regime computation still runs."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)
    stressed = (
        compute_stressed(daily, signal_choice, lookback_years, stress_pctile, _lag_override_days)
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
    """Same banking/lump decision rule as make_credit_stress_decider, but
    driven by an arbitrary pre-computed `stressed` boolean array instead of
    recomputing it from a FRED signal -- used by the placebo circular-shift
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

# Grid: signal_choice x lookback_years x stress_pctile x stress_tilt_fraction
# = 2x2x3x2 = 24 (<=36 cap; max_lump_multiple fixed at 6, not grid-varied)
GRID = {
    "signal_choice": ["credit_spread", "nfci"],
    "lookback_years": [5, 10],
    "stress_pctile": [70, 80, 90],
    "stress_tilt_fraction": [0.0, 0.25],
}
MAX_LUMP_MULTIPLE = 6.0
PRIMARY_CONFIG = {
    "signal_choice": "credit_spread", "lookback_years": 10,
    "stress_pctile": 80, "stress_tilt_fraction": 0.0,
    "max_lump_multiple": MAX_LUMP_MULTIPLE,
}


def grid_configs() -> list[dict]:
    out = []
    for sc in GRID["signal_choice"]:
        for lb in GRID["lookback_years"]:
            for pc in GRID["stress_pctile"]:
                for tf in GRID["stress_tilt_fraction"]:
                    out.append({
                        "signal_choice": sc, "lookback_years": lb,
                        "stress_pctile": pc, "stress_tilt_fraction": tf,
                        "max_lump_multiple": MAX_LUMP_MULTIPLE,
                    })
    return out
