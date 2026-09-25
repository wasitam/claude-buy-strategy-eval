"""Family 022: Presidential election-cycle deposit timing
(Santa-Clara & Valkanov 2003, "The Presidential Puzzle").

families/022-election-cycle/prereg.md has the full mechanism and rules.
Summary: a purely calendar-based execution-timing shift within a fixed
$500/week deposit schedule, at QUADRENNIAL periodicity (~4 calendar
years / ~1,008 trading days) -- distinct from family 006's monthly
turn-of-month window, family 007's weekly day-of-week window, and family
018's annual Halloween/Sell-in-May window. Unlike all three, the regime
label is not a modular function of month-of-year or day-of-week: it is
computed by mapping the calendar year to its position (1-4) in the actual
US presidential election cycle (elections in years divisible by 4).

  - "Weak years" (the first `n_weak_years` of the 4-year cycle, default
    post-election year + midterm year): buy only
    `(1 - bank_fraction) * weekly_deposit`, banking the remainder as cash
    (earning IRX, engine sec 3.2) until the next strong-year week.
  - "Strong years" (the remaining years of the cycle, default
    pre-election year + election year): buy up to
    `max_lump_multiple * weekly_deposit`, cash-capped (deploys cash
    banked from prior weak-year weeks -- never leverage).
Never sells. No price or macro data is used in the signal at all -- only
the calendar year of each trading day, known in advance (every US
presidential election date used in this backtest is already historical).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import engine as eng


def cycle_year(year: int) -> int:
    """Maps a calendar year to its 1-4 position in the 4-year US
    presidential term: 4 = a presidential election year (year % 4 == 0,
    e.g. 2000, 2004, ..., 2020, 2024); 1 = the post-election year
    (year % 4 == 1, e.g. 2021); 2 = the midterm year (year % 4 == 2,
    e.g. 2022); 3 = the pre-election year (year % 4 == 3, e.g. 2023)."""
    m = year % 4
    return 4 if m == 0 else m


def compute_is_strong_year(
    daily: pd.DataFrame, n_weak_years: int, include_election_year_in_strong: bool,
) -> np.ndarray:
    """Marks each trading day True if its calendar year falls in a
    "strong" cycle-year. weak_years = the first n_weak_years of {1,2,3,4};
    strong_years = the rest, with year 4 (the election year itself) moved
    into weak_years when include_election_year_in_strong is False.
    Calendar-only, no price dependence -- computed once for the whole
    trading-day index, exactly like halloween_seasonal.compute_is_strong_season."""
    weak_years = set(range(1, n_weak_years + 1))
    strong_years = set(range(1, 5)) - weak_years
    if not include_election_year_in_strong and 4 in strong_years:
        strong_years.discard(4)
        weak_years.add(4)
    idx = pd.DatetimeIndex(daily.index)
    years = idx.year.to_numpy()
    cyc = np.array([cycle_year(int(y)) for y in years])
    is_strong = np.isin(cyc, list(strong_years))
    return is_strong


def make_election_cycle_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    n_weak_years: int = 2, include_election_year_in_strong: bool = True,
    bank_fraction: float = 0.5, max_lump_multiple: float = 8.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the cycle computation entirely and
    buys the full week's cash every week-end day (0 otherwise), which is
    bit-for-bit plain DCA (used to prove the strategy nests DCA exactly)."""
    is_week_end = eng.week_end_flags(daily.index)
    is_strong = compute_is_strong_year(daily, n_weak_years, include_election_year_in_strong) if enabled else None

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
            target_buy_usd = (1.0 - bank_fraction) * weekly_deposit
        return target_buy_usd, 0.0, {"is_strong_year": bool(is_strong[t])}

    return decide


CATEGORY = "Seasonality / execution timing"

# Grid: n_weak_years x include_election_year_in_strong x bank_fraction x
# max_lump_multiple = 2x2x3x2 = 24 (<=36 cap, 4 params <=5)
GRID = {
    "n_weak_years": [2, 1],
    "include_election_year_in_strong": [True, False],
    "bank_fraction": [0.3, 0.5, 0.7],
    "max_lump_multiple": [4, 8],
}
PRIMARY_CONFIG = {
    "n_weak_years": 2, "include_election_year_in_strong": True,
    "bank_fraction": 0.5, "max_lump_multiple": 8,
}

# Pre-backtest verification (family 021's lesson): every PRIMARY_CONFIG
# value must actually be a member of its GRID list, checked at import time.
for _k, _v in PRIMARY_CONFIG.items():
    assert _v in GRID[_k], f"PRIMARY_CONFIG[{_k}]={_v!r} not in GRID[{_k}]={GRID[_k]!r}"


def grid_configs() -> list[dict]:
    out = []
    for nw in GRID["n_weak_years"]:
        for ie in GRID["include_election_year_in_strong"]:
            for bf in GRID["bank_fraction"]:
                for ml in GRID["max_lump_multiple"]:
                    out.append({
                        "n_weak_years": nw, "include_election_year_in_strong": ie,
                        "bank_fraction": bf, "max_lump_multiple": ml,
                    })
    return out


assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of grid_configs()"
