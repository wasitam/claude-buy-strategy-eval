"""Family 027: yield-curve slope (2s10s) inversion regime filter
(Estrella & Mishkin 1998).

families/027-yield-curve-regime/prereg.md has the full mechanism and
rules. Summary: a point-in-time, asset-agnostic macro regime signal (the
Treasury 10y-2y spread, T10Y2Y) is used to bank deposits while the curve
is confirmed-inverted (persistence-filtered) and for a lag-motivated
banking-window extension afterward, and deploy a capped catch-up lump
during "normal" weeks -- the same banking/cash-cap mechanic families
006/007/010/011 use, never leverage or shorting. No sells, ever.

Category: Regime switch (macro / credit / sentiment).

Parameters (4 tunable + 1 fixed, all <=5 total):
  invert_threshold      -- T10Y2Y level below which a day counts as inverted
  persistence_days      -- consecutive trading days below threshold needed
                            to confirm inversion (noise filter)
  banking_window_days    -- trailing-day window (calendar days) over which
                            "any confirmed inversion" keeps banking active
                            after de-inversion (models the recession lag)
  stress_tilt_fraction  -- fraction of deposit still bought while banking
  max_lump_multiple     -- fixed at 6.0 (not grid-varied), catch-up cap
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import data as v3data

# Publication-lag convention (prereg.md "Point-in-time construction"):
# T10Y2Y is a same-day market-observable Treasury-yield spread, published
# with roughly a 1-business-day practical lag; a conservative 2-calendar-
# day lag is applied.
T10Y2Y_LAG_DAYS = 2


def _lagged_pointintime(raw: pd.Series, lag_days: int) -> pd.Series:
    """Shifts each observation forward by lag_days (so it only becomes
    'seen' that many calendar days after its observation date), matching
    family 011's (credit_stress_filter.py) fetch-raw -> lag -> reindex ->
    ffill pattern, itself mirroring src/backtest/v2/regimes.py."""
    s = raw.copy()
    s.index = s.index + pd.Timedelta(days=lag_days)
    return s.sort_index()


def fetch_raw_signal() -> pd.Series:
    """Raw (unlagged) T10Y2Y series, as of its own observation date."""
    return v3data.fetch_fred_macro("T10Y2Y")


def compute_banking(
    daily: pd.DataFrame, invert_threshold: float, persistence_days: int,
    banking_window_days: int, lag_override_days: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Returns (banking, confirmed_inverted) boolean arrays aligned to
    daily.index. Uses ONLY the point-in-time T10Y2Y signal (no asset
    price). Before the signal's first usable date, defaults to NOT
    banking (behaves like plain DCA during signal warm-up, matching
    family 011's convention).

    confirmed_inverted_t: inverted_raw has held True for the trailing
    persistence_days CONSECUTIVE observations of the signal's own (daily)
    observation series (computed on the signal's own dense daily calendar,
    not the asset's trading-day calendar, so persistence_days means
    calendar days of an inverted signal, not asset trading days).

    banking_t: True if confirmed_inverted has been True at any point
    within the trailing banking_window_days CALENDAR days ending at t
    (inclusive), modeling the post-inversion recession-risk lag.
    """
    raw = fetch_raw_signal()
    lag = lag_override_days if lag_override_days is not None else T10Y2Y_LAG_DAYS
    lagged = _lagged_pointintime(raw, lag)

    # Build a dense daily calendar over the lagged signal's own span so
    # persistence_days is measured in genuine consecutive calendar days
    # (T10Y2Y is a business-day series; forward-filling weekends/holidays
    # onto a dense daily index before the persistence/rolling-window logic
    # keeps "N consecutive days" well-defined and avoids silently treating
    # a Fri-then-Mon gap as non-consecutive).
    dense_idx = pd.date_range(lagged.index.min(), lagged.index.max(), freq="D")
    dense = lagged.reindex(dense_idx).ffill()

    inverted_raw = (dense < invert_threshold)
    confirmed = inverted_raw.rolling(persistence_days, min_periods=persistence_days).min().astype(bool)
    confirmed = confirmed.fillna(False)

    banking_window = max(int(banking_window_days), 1)
    banking = confirmed.rolling(banking_window, min_periods=1).max().astype(bool)

    # Align onto the asset's own daily trading index.
    confirmed_aligned = confirmed.reindex(daily.index, method="ffill").fillna(False).to_numpy().astype(bool)
    banking_aligned = banking.reindex(daily.index, method="ffill").fillna(False).to_numpy().astype(bool)
    return banking_aligned, confirmed_aligned


def make_yield_curve_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    invert_threshold: float = 0.0, persistence_days: int = 5,
    banking_window_days: int = 252, stress_tilt_fraction: float = 0.0,
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
    banking = (
        compute_banking(daily, invert_threshold, persistence_days, banking_window_days, _lag_override_days)[0]
        if enabled else None
    )

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if banking[t]:
            target_buy_usd = stress_tilt_fraction * weekly_deposit
        else:
            target_buy_usd = min(cash, max_lump_multiple * weekly_deposit)
        return target_buy_usd, 0.0, {"banking": bool(banking[t])}

    return decide


def make_decider_from_banking_array(
    daily: pd.DataFrame, weekly_deposit: float, banking: np.ndarray,
    stress_tilt_fraction: float = 0.0, max_lump_multiple: float = 6.0,
):
    """Same banking/lump decision rule as make_yield_curve_decider, but
    driven by an arbitrary pre-computed `banking` boolean array instead of
    recomputing it from T10Y2Y -- used by the placebo circular-shift
    robustness test (sec 4.3), which shifts the regime's TIMING while
    keeping its overall banking/normal frequency identical."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)

    def decide(t, cash):
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if banking[t]:
            target_buy_usd = stress_tilt_fraction * weekly_deposit
        else:
            target_buy_usd = min(cash, max_lump_multiple * weekly_deposit)
        return target_buy_usd, 0.0, {"banking": bool(banking[t])}

    return decide


CATEGORY = "Regime switch (macro / credit / sentiment)"

# Grid: invert_threshold x persistence_days x banking_window_days x
# stress_tilt_fraction = 2x2x3x2 = 24 (<=36 cap; max_lump_multiple fixed
# at 6, not grid-varied)
GRID = {
    "invert_threshold": [0.0, -0.10],
    "persistence_days": [5, 20],
    "banking_window_days": [0, 252, 504],
    "stress_tilt_fraction": [0.0, 0.25],
}
MAX_LUMP_MULTIPLE = 6.0
PRIMARY_CONFIG = {
    "invert_threshold": 0.0, "persistence_days": 5,
    "banking_window_days": 252, "stress_tilt_fraction": 0.0,
    "max_lump_multiple": MAX_LUMP_MULTIPLE,
}


def grid_configs() -> list[dict]:
    out = []
    for it in GRID["invert_threshold"]:
        for pd_ in GRID["persistence_days"]:
            for bw in GRID["banking_window_days"]:
                for tf in GRID["stress_tilt_fraction"]:
                    out.append({
                        "invert_threshold": it, "persistence_days": pd_,
                        "banking_window_days": bw, "stress_tilt_fraction": tf,
                        "max_lump_multiple": MAX_LUMP_MULTIPLE,
                    })
    return out


# Import-time assertion (family 021's lesson, applied proactively here):
# PRIMARY_CONFIG must be a genuine member of the declared grid.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of the declared grid"
