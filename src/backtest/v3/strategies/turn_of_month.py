"""Family 006: turn-of-month deposit timing (Ariel 1987; Lakonishok & Smidt
1988).

families/006-turn-of-month/prereg.md has the full mechanism and rules.
Summary: a purely calendar-based execution-timing shift within a fixed
$500/week deposit schedule. On the week's last trading day (the same
decision cadence every other v3 family uses):
  - If that day falls within the "turn-of-month" (TOM) window -- the last
    `days_before_month_end` trading days of the month, or the first
    `days_after_month_start` trading days of the following month -- buy
    up to `max_lump_multiple * weekly_deposit`, cash-capped (this deploys
    any cash banked from prior non-TOM weeks, never leverage).
  - Otherwise, buy only `mild_tilt_fraction * weekly_deposit`, banking the
    remainder as cash (earning IRX, engine sec 3.2) until the next TOM
    window.
Never sells. No price or macro data is used in the signal at all -- only
the asset's own trading-day calendar, known in advance like any real
calendar (only *prices*, not *dates*, are unknown ahead of time).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import engine as eng


def compute_is_tom(daily: pd.DataFrame, days_before_month_end: int, days_after_month_start: int) -> np.ndarray:
    """Marks each trading day True if it is among the last
    `days_before_month_end` trading days of its calendar month, or the
    first `days_after_month_start` trading days of its calendar month
    (which, combined across consecutive months, forms the turn-of-month
    window straddling each month boundary). Calendar-only, no price
    dependence -- computed once for the whole trading-day index, exactly
    like engine.week_end_flags."""
    idx = daily.index
    is_tom = np.zeros(len(idx), dtype=bool)
    period = pd.Index(idx).to_period("M")
    df = pd.DataFrame({"pos": np.arange(len(idx))}, index=idx)
    for _, grp in df.groupby(period):
        positions = grp["pos"].to_numpy()
        if days_before_month_end > 0:
            is_tom[positions[-days_before_month_end:]] = True
        if days_after_month_start > 0:
            is_tom[positions[:days_after_month_start]] = True
    return is_tom


def make_tom_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    days_before_month_end: int = 1, days_after_month_start: int = 3,
    mild_tilt_fraction: float = 0.0, max_lump_multiple: float = 6.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the calendar computation entirely
    and buys the full week's cash every week-end day (0 otherwise), which
    is bit-for-bit plain DCA (used to prove the strategy nests DCA
    exactly)."""
    is_week_end = eng.week_end_flags(daily.index)
    is_tom = compute_is_tom(daily, days_before_month_end, days_after_month_start) if enabled else None

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if is_tom[t]:
            target_buy_usd = min(cash, max_lump_multiple * weekly_deposit)
        else:
            target_buy_usd = mild_tilt_fraction * weekly_deposit
        return target_buy_usd, 0.0, {"is_tom": bool(is_tom[t])}

    return decide


CATEGORY = "Seasonality / execution timing"

# Grid: days_before_month_end x days_after_month_start x mild_tilt_fraction
# x max_lump_multiple = 3x2x2x2 = 24 (<=36 cap, 4 params <=5)
GRID = {
    "days_before_month_end": [1, 2, 3],
    "days_after_month_start": [3, 4],
    "mild_tilt_fraction": [0.0, 0.5],
    "max_lump_multiple": [3, 6],
}
PRIMARY_CONFIG = {
    "days_before_month_end": 1, "days_after_month_start": 3,
    "mild_tilt_fraction": 0.0, "max_lump_multiple": 6,
}


def grid_configs() -> list[dict]:
    out = []
    for db in GRID["days_before_month_end"]:
        for da in GRID["days_after_month_start"]:
            for mt in GRID["mild_tilt_fraction"]:
                for ml in GRID["max_lump_multiple"]:
                    out.append({
                        "days_before_month_end": db, "days_after_month_start": da,
                        "mild_tilt_fraction": mt, "max_lump_multiple": ml,
                    })
    return out
