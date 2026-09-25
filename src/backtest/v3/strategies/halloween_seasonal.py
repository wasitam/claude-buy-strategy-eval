"""Family 018: "Halloween effect" / Sell-in-May seasonal deposit timing
(Bouman & Jacobsen 2002).

families/018-halloween-seasonal/prereg.md has the full mechanism and rules.
Summary: a purely calendar-based execution-timing shift within a fixed
$500/week deposit schedule, at ANNUAL periodicity -- distinct from family
006's monthly turn-of-month window and family 007's weekly day-of-week
window.

  - "Strong season" (default November-April): buy up to
    `max_lump_multiple * weekly_deposit`, cash-capped (deploys cash banked
    from prior weak-season weeks -- never leverage).
  - "Weak season" (default May-October): buy only
    `mild_tilt_fraction * weekly_deposit`, banking the remainder as cash
    (earning IRX, engine sec 3.2) until the next strong-season week.
Never sells. No price or macro data is used in the signal at all -- only
the asset's own trading-day calendar (calendar month), known in advance
like any real calendar.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import engine as eng


def compute_is_strong_season(daily: pd.DataFrame, strong_season_start_month: int, weak_season_start_month: int) -> np.ndarray:
    """Marks each trading day True if its calendar date falls in the
    strong season: [strong_season_start_month day 1, weak_season_start_month
    day 1) of the same calendar year if strong_season_start_month <
    weak_season_start_month, or wrapping across the year boundary
    otherwise (the primary case: strong season Nov (11) through the day
    before May (5), i.e. wraps Dec->Jan). Calendar-only, no price
    dependence -- computed once for the whole trading-day index, exactly
    like turn_of_month.compute_is_tom."""
    idx = pd.DatetimeIndex(daily.index)
    month = idx.month.to_numpy()
    if strong_season_start_month < weak_season_start_month:
        # Strong season does not wrap the year boundary, e.g. start=3, end=8
        is_strong = (month >= strong_season_start_month) & (month < weak_season_start_month)
    else:
        # Strong season wraps the year boundary (the primary case:
        # Nov-Apr strong, May-Oct weak): strong if month >= start OR
        # month < weak_start.
        is_strong = (month >= strong_season_start_month) | (month < weak_season_start_month)
    return is_strong


def make_halloween_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    strong_season_start_month: int = 11, weak_season_start_month: int = 5,
    mild_tilt_fraction: float = 0.0, max_lump_multiple: float = 6.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the seasonal computation entirely
    and buys the full week's cash every week-end day (0 otherwise), which
    is bit-for-bit plain DCA (used to prove the strategy nests DCA
    exactly)."""
    is_week_end = eng.week_end_flags(daily.index)
    is_strong = compute_is_strong_season(daily, strong_season_start_month, weak_season_start_month) if enabled else None

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if is_strong[t]:
            target_buy_usd = min(cash, max_lump_multiple * weekly_deposit)
        else:
            target_buy_usd = mild_tilt_fraction * weekly_deposit
        return target_buy_usd, 0.0, {"is_strong_season": bool(is_strong[t])}

    return decide


CATEGORY = "Seasonality / execution timing"

# Grid: strong_season_start_month x weak_season_start_month x
# mild_tilt_fraction x max_lump_multiple = 2x2x2x2 = 16 (<=36 cap, 4 params <=5)
GRID = {
    "strong_season_start_month": [11, 10],
    "weak_season_start_month": [5, 4],
    "mild_tilt_fraction": [0.0, 0.5],
    "max_lump_multiple": [6, 12],
}
PRIMARY_CONFIG = {
    "strong_season_start_month": 11, "weak_season_start_month": 5,
    "mild_tilt_fraction": 0.0, "max_lump_multiple": 6,
}


def grid_configs() -> list[dict]:
    out = []
    for ss in GRID["strong_season_start_month"]:
        for ws in GRID["weak_season_start_month"]:
            for mt in GRID["mild_tilt_fraction"]:
                for ml in GRID["max_lump_multiple"]:
                    out.append({
                        "strong_season_start_month": ss, "weak_season_start_month": ws,
                        "mild_tilt_fraction": mt, "max_lump_multiple": ml,
                    })
    return out
