"""Family 007: day-of-week deposit timing (BTC weekend effect; Caporale &
Plastun 2019).

families/007-day-of-week/prereg.md has the full mechanism and rules.
Summary: a purely calendar-based execution-timing shift within a fixed
$500/week deposit schedule. Unlike family 006 (turn-of-month), the signal
must be evaluated on EVERY trading day, not only the week's deposit day,
because the target day of week usually differs from whichever day is the
asset's own week-end/deposit day.

  - If today's day-of-week equals `target_weekday`: buy up to
    `max_lump_multiple * weekly_deposit`, cash-capped (deploys any cash
    banked from prior non-target days -- never leverage).
  - Otherwise: buy `mild_tilt_fraction * weekly_deposit / (# non-target
    trading days in this ISO week)`, banking the remainder as cash
    (earning IRX, engine sec 3.2).
  - Banking-window forced deploy: if more than `banking_window_weeks * 7`
    calendar days have elapsed since cash was last spent, top up that
    day's buy with the remaining banked cash (still capped by
    `max_lump_multiple`). This bounds how long cash can sit idle, and is
    needed because `target_weekday=Sunday` never occurs at all on the 4
    non-BTC assets' own trading calendars.
Never sells. No price or macro data is used in the signal at all -- only
the asset's own trading-day calendar (day-of-week, ISO week), known in
advance like any real calendar.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import engine as eng

WEEKDAY_NAMES = {0: "Monday", 4: "Friday", 6: "Sunday"}
WEEKDAY_NUMS = {v: k for k, v in WEEKDAY_NAMES.items()}


def compute_target_and_week_counts(daily: pd.DataFrame, target_weekday: int) -> tuple[np.ndarray, np.ndarray]:
    """Returns (is_target, nontarget_count_in_week) arrays, calendar-only
    (no price dependence), computed once for the whole trading-day index --
    exactly the same pattern as turn_of_month.compute_is_tom."""
    idx = pd.DatetimeIndex(daily.index)
    is_target = np.asarray(idx.dayofweek == target_weekday)
    iso = idx.isocalendar()[["year", "week"]]
    wk = list(zip(iso["year"].to_numpy(), iso["week"].to_numpy()))
    df = pd.DataFrame({"wk": wk, "is_target": is_target})
    nontarget_count = df.groupby("wk")["is_target"].transform(lambda s: int((~s).sum())).to_numpy()
    nontarget_count = np.where(nontarget_count == 0, 1, nontarget_count)  # avoid /0 (never used when 0)
    return is_target, nontarget_count


def make_dow_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    target_weekday: int = 0, mild_tilt_fraction: float = 0.0,
    max_lump_multiple: float = 6.0, banking_window_weeks: float = 4.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the day-of-week computation entirely
    and buys the full week's cash every week-end day (0 otherwise), which
    is bit-for-bit plain DCA."""
    is_week_end = eng.week_end_flags(daily.index)
    if not enabled:
        def decide(t, cash):
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        return decide

    idx = pd.DatetimeIndex(daily.index)
    is_target, nontarget_count = compute_target_and_week_counts(daily, target_weekday)
    banking_window_days = banking_window_weeks * 7.0
    state = {"last_spend_idx": None}  # pd.Timestamp of last day cash was spent, or None (start)

    def decide(t, cash):
        target_today = bool(is_target[t])
        if target_today:
            buy = min(cash, max_lump_multiple * weekly_deposit)
        else:
            tilt_usd = mild_tilt_fraction * weekly_deposit / nontarget_count[t]
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

        return buy, 0.0, {"is_target": target_today, "forced": forced}

    return decide


CATEGORY = "Seasonality / execution timing"

# Grid: target_weekday x mild_tilt_fraction x max_lump_multiple x
# banking_window_weeks = 3x2x2x2 = 24 (<=36 cap, 4 params <=5)
GRID = {
    "target_weekday": ["Monday", "Friday", "Sunday"],
    "mild_tilt_fraction": [0.0, 0.5],
    "max_lump_multiple": [3, 6],
    "banking_window_weeks": [2, 4],
}
PRIMARY_CONFIG = {
    "target_weekday": "Monday", "mild_tilt_fraction": 0.0,
    "max_lump_multiple": 6, "banking_window_weeks": 4,
}


def _resolve(cfg: dict) -> dict:
    """Grid/primary configs store target_weekday as a name (human-readable,
    matches prereg.md); resolve to the int dayofweek the strategy fn needs."""
    out = dict(cfg)
    out["target_weekday"] = WEEKDAY_NUMS[cfg["target_weekday"]]
    return out


def grid_configs() -> list[dict]:
    out = []
    for tw in GRID["target_weekday"]:
        for mt in GRID["mild_tilt_fraction"]:
            for ml in GRID["max_lump_multiple"]:
                for bw in GRID["banking_window_weeks"]:
                    out.append({
                        "target_weekday": tw, "mild_tilt_fraction": mt,
                        "max_lump_multiple": ml, "banking_window_weeks": bw,
                    })
    return out
