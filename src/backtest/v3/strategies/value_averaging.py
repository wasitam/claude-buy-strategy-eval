"""Family 004: value averaging (Edleson 1991, with Hayley's critique noted).

families/004-value-averaging/prereg.md has the full mechanism and rules.
Summary: each week, compare the account's actual value to a target value
implied by a constant assumed-annual-growth path (`annual_growth_rate`), and
buy (if behind target) or sell (if ahead, when `allow_sells`) enough to close
the gap -- capped both by a magnitude cap (`max_multiple_of_deposit` x the
base $500 weekly deposit) and by actual cash/units on hand (no leverage, no
external capital: see prereg.md's "How this family addresses Hayley's
critique" section). This keeps VA's total deployed capital always <= DCA's
cumulative deposits at every point in time, so the family can be scored on
final wealth (not IRR) on a genuinely capital-neutral basis.

Category: Sizing.

Parameters (<=5, all in this module):
  annual_growth_rate      -- assumed annual growth rate of the target-value path
  max_multiple_of_deposit -- cap on any single week's buy or sell, as a
                             multiple of the base $500 weekly deposit
  allow_sells             -- if True, sell when ahead of target (classic VA);
                             if False, only pause/reduce buys (no-sell VA)

The single-asset engine's `decide(t, cash)` interface does not pass the
decider its own current units (only cash), so this decider tracks its own
position causally via a shadow simulation of its own past fills, using the
exact same next-day-open / sells-before-buys / fee mechanics as
`engine.run_single_asset` itself (see prereg.md). Because every buy this
decider ever submits is already capped by the real `cash` value the engine
hands it each call, the engine's own fill can never diverge from what this
shadow assumes (no further clipping happens downstream), so the shadow stays
exactly in sync with the engine's real state at every step.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..engine import week_end_flags

WEEKS_PER_YEAR = 52.0


def target_value_path(weekly_deposit: float, annual_growth_rate: float, n_weeks: int) -> np.ndarray:
    """V_target(w) for w=1..n_weeks: future value of an annuity of
    `weekly_deposit` compounding at the per-week rate implied by
    `annual_growth_rate`, i.e. what a plain-DCA account would be worth at
    week w if the asset had compounded at exactly that assumed rate every
    week since week 1. index 0 unused (w is 1-indexed); array has length
    n_weeks+1 so it can be indexed directly by w."""
    r = (1.0 + annual_growth_rate) ** (1.0 / WEEKS_PER_YEAR) - 1.0
    w = np.arange(0, n_weeks + 1, dtype=float)
    if abs(r) < 1e-12:
        return weekly_deposit * w
    return weekly_deposit * (((1.0 + r) ** w - 1.0) / r)


def make_value_averaging_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    annual_growth_rate: float = 0.10, max_multiple_of_deposit: float = 4.0,
    allow_sells: bool = True,
    fee: float = 0.001,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it returns buy_usd=cash, sell_usd=0 on EVERY day
    (not just week-ends), bit-for-bit identical to engine.make_dca_decider,
    which reproduces plain DCA exactly."""
    opens = daily["Open"].to_numpy()
    closes = daily["Close"].to_numpy()
    n = len(daily)
    is_week_end = week_end_flags(daily.index)
    week_num = np.cumsum(is_week_end)  # at a week-end day t, week_num[t] = count of week-ends through and incl. t
    n_weeks = int(week_num[-1])
    v_target = target_value_path(weekly_deposit, annual_growth_rate, n_weeks) if enabled else None

    cap = max_multiple_of_deposit * weekly_deposit

    state = {"shadow_units": 0.0, "pending_buy_usd": 0.0, "pending_sell_units": 0.0}

    def decide(t, cash):
        if not enabled:
            return cash, 0.0, {}

        # (1) settle yesterday's own pending order at TODAY's open, using the
        # same fee / sells-first-then-buys mechanics as the real engine, to
        # keep the shadow position in sync with the engine's true state.
        if t >= 1:
            if state["pending_sell_units"] > 0 and state["shadow_units"] > 0:
                sell_units = min(state["pending_sell_units"], state["shadow_units"])
                state["shadow_units"] -= sell_units
            if state["pending_buy_usd"] > 0:
                spend = state["pending_buy_usd"]
                bought_units = (spend * (1.0 - fee)) / opens[t]
                state["shadow_units"] += bought_units
            state["pending_buy_usd"] = 0.0
            state["pending_sell_units"] = 0.0

        buy_usd = 0.0
        sell_usd = 0.0
        gap = None
        if is_week_end[t]:
            w = int(week_num[t])
            current_value = state["shadow_units"] * closes[t]
            target = float(v_target[w])
            gap = target - current_value
            if gap > 0:
                buy_usd = min(gap, cap, max(cash, 0.0))
            elif gap < 0 and allow_sells:
                sell_usd = min(-gap, cap, current_value)

        state["pending_buy_usd"] = buy_usd
        state["pending_sell_units"] = sell_usd / max(closes[t], 1e-9)

        return buy_usd, sell_usd, {"gap": gap, "shadow_units": state["shadow_units"]}

    return decide


CATEGORY = "Sizing"

# Grid: annual_growth_rate x max_multiple_of_deposit x allow_sells = 3x3x2 = 18 (<=36 cap, 3 params <=5)
GRID = {
    "annual_growth_rate": [0.06, 0.10, 0.14],
    "max_multiple_of_deposit": [2, 4, 8],
    "allow_sells": [True, False],
}
PRIMARY_CONFIG = {
    "annual_growth_rate": 0.10, "max_multiple_of_deposit": 4, "allow_sells": True,
}


def grid_configs() -> list[dict]:
    out = []
    for g in GRID["annual_growth_rate"]:
        for k in GRID["max_multiple_of_deposit"]:
            for s in GRID["allow_sells"]:
                out.append({"annual_growth_rate": g, "max_multiple_of_deposit": k, "allow_sells": s})
    return out
