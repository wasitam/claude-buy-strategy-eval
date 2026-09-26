"""Family 051: Pre-FOMC announcement drift deposit timing (Lucca & Moench
2015, "The Pre-FOMC Announcement Drift", Journal of Finance).

families/051-pre-fomc-drift/prereg.md has the full mechanism, the
concrete redundancy check against families 006/007/018/022/024, and the
cross-asset scoping decision (all 5 core assets). Summary: a purely
calendar-based execution-timing shift within a fixed $500/week deposit
schedule, keyed to the FOMC's OWN scheduled meeting calendar (208
hard-coded historical decision dates, 1994-02-04..2019-12-11, 8/year,
irregularly spaced -- NOT a modular function of weekday/day-of-month/
month/year-mod-4, verified concretely in prereg.md).

  - If today is within `window_days` trading days immediately before a
    scheduled FOMC decision date: buy up to
    `max_lump_multiple * weekly_deposit`, cash-capped (deploys any cash
    banked from prior ordinary days -- never leverage).
  - Otherwise (an ordinary week): buy `mild_tilt_fraction * weekly_deposit
    / (# non-window trading days in this ISO week)`, banking the
    remainder as cash (earning IRX, engine sec 3.2).
  - Banking-window forced deploy (same mechanic as family 007, needed
    here because the entire pre-1994 sub-period of any asset's history
    has no FOMC calendar coverage at all -- the window flag is never True
    before 1994-02-04): if more than `banking_window_weeks * 7` calendar
    days have elapsed since cash was last spent, that day's buy is topped
    up with the remaining banked cash (still capped by max_lump_multiple).
Never sells. No price or macro data feed is used in the signal -- only
the asset's own trading-day calendar and the hard-coded, already-
historical FOMC_DATES list below (a fixed constant, not a live feed).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import engine as eng

# Hard-coded, publicly known historical FOMC scheduled decision (statement
# release) dates, 1994-02-04 through 2019-12-11 (the development period,
# per prereg.md's source discussion: the FOMC began same-day post-meeting
# statements in Feb 1994, and this backtest never uses dates on or after
# 2020-01-01). Exactly 8 per year, every year -- the FOMC's own long-
# standing "eight regularly scheduled meetings per year" practice.
# Confirmed UNSCHEDULED/emergency inter-meeting actions (e.g. Sep 2001,
# Jan 2008, Oct 2008) are deliberately excluded: they were not on a
# publicly pre-announced calendar, so including them would build
# lookahead into the signal. Compiled from this session's own knowledge of
# the well-documented public historical FOMC meeting record (Federal
# Reserve historical materials, financial-data-vendor economic calendars,
# academic replication files) -- federalreserve.gov, en.wikipedia.org and
# www.r-bloggers.com were all confirmed EGRESS_BLOCKED in this session
# (no live-reachable structured source), so this list is hard-coded per
# this family's explicit task-level allowance for that contingency.
FOMC_DATES = [
    "1994-02-04", "1994-03-22", "1994-05-17", "1994-07-06", "1994-08-16", "1994-09-27", "1994-11-15", "1994-12-20",
    "1995-02-01", "1995-03-28", "1995-05-23", "1995-07-06", "1995-08-22", "1995-09-26", "1995-11-15", "1995-12-19",
    "1996-01-31", "1996-03-26", "1996-05-21", "1996-07-03", "1996-08-20", "1996-09-24", "1996-11-13", "1996-12-17",
    "1997-02-05", "1997-03-25", "1997-05-20", "1997-07-02", "1997-08-19", "1997-09-30", "1997-11-12", "1997-12-16",
    "1998-02-04", "1998-03-31", "1998-05-19", "1998-07-01", "1998-08-18", "1998-09-29", "1998-11-17", "1998-12-22",
    "1999-02-03", "1999-03-30", "1999-05-18", "1999-06-30", "1999-08-24", "1999-10-05", "1999-11-16", "1999-12-21",
    "2000-02-02", "2000-03-21", "2000-05-16", "2000-06-28", "2000-08-22", "2000-10-03", "2000-11-15", "2000-12-19",
    "2001-01-31", "2001-03-20", "2001-05-15", "2001-06-27", "2001-08-21", "2001-10-02", "2001-11-06", "2001-12-11",
    "2002-01-30", "2002-03-19", "2002-05-07", "2002-06-26", "2002-08-13", "2002-09-24", "2002-11-06", "2002-12-10",
    "2003-01-29", "2003-03-18", "2003-05-06", "2003-06-25", "2003-08-12", "2003-09-16", "2003-10-28", "2003-12-09",
    "2004-01-28", "2004-03-16", "2004-05-04", "2004-06-30", "2004-08-10", "2004-09-21", "2004-11-10", "2004-12-14",
    "2005-02-02", "2005-03-22", "2005-05-03", "2005-06-30", "2005-08-09", "2005-09-20", "2005-11-01", "2005-12-13",
    "2006-01-31", "2006-03-28", "2006-05-10", "2006-06-29", "2006-08-08", "2006-09-20", "2006-10-25", "2006-12-12",
    "2007-01-31", "2007-03-21", "2007-05-09", "2007-06-28", "2007-08-07", "2007-09-18", "2007-10-31", "2007-12-11",
    "2008-01-30", "2008-03-18", "2008-04-30", "2008-06-25", "2008-08-05", "2008-09-16", "2008-10-29", "2008-12-16",
    "2009-01-28", "2009-03-18", "2009-04-29", "2009-06-24", "2009-08-12", "2009-09-23", "2009-11-04", "2009-12-16",
    "2010-01-27", "2010-03-16", "2010-04-28", "2010-06-23", "2010-08-10", "2010-09-21", "2010-11-03", "2010-12-14",
    "2011-01-26", "2011-03-15", "2011-04-27", "2011-06-22", "2011-08-09", "2011-09-21", "2011-11-02", "2011-12-13",
    "2012-01-25", "2012-03-13", "2012-04-25", "2012-06-20", "2012-08-01", "2012-09-13", "2012-10-24", "2012-12-12",
    "2013-01-30", "2013-03-20", "2013-05-01", "2013-06-19", "2013-07-31", "2013-09-18", "2013-10-30", "2013-12-18",
    "2014-01-29", "2014-03-19", "2014-04-30", "2014-06-18", "2014-07-30", "2014-09-17", "2014-10-29", "2014-12-17",
    "2015-01-28", "2015-03-18", "2015-04-29", "2015-06-17", "2015-07-29", "2015-09-17", "2015-10-28", "2015-12-16",
    "2016-01-27", "2016-03-16", "2016-04-27", "2016-06-15", "2016-07-27", "2016-09-21", "2016-11-02", "2016-12-14",
    "2017-02-01", "2017-03-15", "2017-05-03", "2017-06-14", "2017-07-26", "2017-09-20", "2017-11-01", "2017-12-13",
    "2018-01-31", "2018-03-21", "2018-05-02", "2018-06-13", "2018-08-01", "2018-09-26", "2018-11-08", "2018-12-19",
    "2019-01-30", "2019-03-20", "2019-05-01", "2019-06-19", "2019-07-31", "2019-09-18", "2019-10-30", "2019-12-11",
]
FOMC_DATES_TS = pd.DatetimeIndex(sorted(pd.Timestamp(d) for d in FOMC_DATES))


def compute_is_pre_fomc(daily: pd.DataFrame, window_days: int) -> np.ndarray:
    """Marks each trading day True if it is one of the `window_days`
    trading days immediately BEFORE an FOMC decision date, on THIS asset's
    own trading-day index. For each FOMC date, the decision-day position
    is the first trading day on-or-after that calendar date (all 208
    hard-coded dates are, in practice, themselves trading days on every
    core asset's calendar); the window marks the window_days positions
    strictly before it. Calendar-only, no price dependence -- computed
    once for the whole trading-day index, like every prior calendar-timing
    family's compute_is_* helper."""
    idx = pd.DatetimeIndex(daily.index)
    n = len(idx)
    is_pre = np.zeros(n, dtype=bool)
    positions = idx.searchsorted(FOMC_DATES_TS, side="left")
    for pos in positions:
        pos = int(pos)
        if pos <= 0 or pos > n:
            continue
        lo = max(0, pos - window_days)
        is_pre[lo:pos] = True
    return is_pre


def make_pre_fomc_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    window_days: int = 2, mild_tilt_fraction: float = 0.0,
    max_lump_multiple: float = 6.0, banking_window_weeks: float = 8.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the pre-FOMC/banking-window
    computation entirely and buys the full week's cash every week-end day
    (0 otherwise), which is bit-for-bit plain DCA."""
    is_week_end = eng.week_end_flags(daily.index)
    if not enabled:
        def decide(t, cash):
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        return decide

    idx = pd.DatetimeIndex(daily.index)
    is_pre_fomc = compute_is_pre_fomc(daily, window_days)

    iso = idx.isocalendar()[["year", "week"]]
    wk = list(zip(iso["year"].to_numpy(), iso["week"].to_numpy()))
    df = pd.DataFrame({"wk": wk, "is_pre": is_pre_fomc})
    nonwindow_count = df.groupby("wk")["is_pre"].transform(lambda s: int((~s).sum())).to_numpy()
    nonwindow_count = np.where(nonwindow_count == 0, 1, nonwindow_count)

    banking_window_days = banking_window_weeks * 7.0
    state = {"last_spend_idx": None}

    def decide(t, cash):
        window_today = bool(is_pre_fomc[t])
        if window_today:
            buy = min(cash, max_lump_multiple * weekly_deposit)
        else:
            tilt_usd = mild_tilt_fraction * weekly_deposit / nonwindow_count[t]
            buy = min(cash, tilt_usd)

        last = state["last_spend_idx"]
        days_since = (idx[t] - last).days if last is not None else (idx[t] - idx[0]).days + 1
        forced = False
        if days_since >= banking_window_days and cash - buy > 1e-9:
            extra = min(cash - buy, max_lump_multiple * weekly_deposit - buy)
            if extra > 0:
                buy += extra
                forced = True

        if buy > 1e-9:
            state["last_spend_idx"] = idx[t]

        return buy, 0.0, {"is_pre_fomc": window_today, "forced": forced}

    return decide


CATEGORY = "Seasonality / execution timing"

# Grid: window_days x mild_tilt_fraction x max_lump_multiple x
# banking_window_weeks = 2x2x2x2 = 16 (<=36 cap, 4 params <=5)
GRID = {
    "window_days": [2, 1],
    "mild_tilt_fraction": [0.0, 0.5],
    "max_lump_multiple": [3, 6],
    "banking_window_weeks": [4, 8],
}
PRIMARY_CONFIG = {
    "window_days": 2, "mild_tilt_fraction": 0.0,
    "max_lump_multiple": 6, "banking_window_weeks": 8,
}

# Pre-backtest verification (family 021's lesson): every PRIMARY_CONFIG
# value must actually be a member of its GRID list, checked at import time.
for _k, _v in PRIMARY_CONFIG.items():
    assert _v in GRID[_k], f"PRIMARY_CONFIG[{_k}]={_v!r} not in GRID[{_k}]={GRID[_k]!r}"


def grid_configs() -> list[dict]:
    out = []
    for wd in GRID["window_days"]:
        for mt in GRID["mild_tilt_fraction"]:
            for ml in GRID["max_lump_multiple"]:
                for bw in GRID["banking_window_weeks"]:
                    out.append({
                        "window_days": wd, "mild_tilt_fraction": mt,
                        "max_lump_multiple": ml, "banking_window_weeks": bw,
                    })
    return out


assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of grid_configs()"
