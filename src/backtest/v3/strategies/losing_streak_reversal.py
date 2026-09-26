"""Family 030: losing-streak (consecutive-down-days) contrarian sizing
(Jegadeesh 1990; Lehmann 1990, short-horizon return reversal).

families/030-losing-streak-reversal/prereg.md has the full mechanism and
rules. Summary: a DISCRETE, magnitude-blind count of consecutive
same-direction daily closes (a streak LENGTH -- only the SIGN of each
day's price change matters, never its magnitude) is used to flag an
"elevated" buy state after `streak_threshold`+ consecutive down-closes, and
a "reduced" buy state after `streak_threshold`+ consecutive up-closes. Once
triggered, that state persists for `decay_days` trading days (a
decay/duration state machine with memory -- family 017's RSI2 has no
analogue for this: RSI2 is a stateless day-by-day smoothed ratio,
recomputed fresh every day with no memory of when an extreme reading
occurred). Deposits are sized UP during an elevated window (cash- and
lump-capped, never leverage) and sized DOWN during a reduced window (the
remainder banked as cash to fund a future elevated window) -- the same
"bank on the down leg, spend the bank on the up-conviction leg" reserve
mechanism families 003/005/015/016/017 use. No sells, ever.

Category: Sizing / valuation.

Parameters (4 tunable + 1 fixed, all <=5):
  streak_threshold   -- consecutive same-direction closes needed to trigger
                         (shared by the down- and up-streak legs)
  buy_mult_streak    -- multiple of weekly_deposit targeted during an
                         elevated (losing-streak) window
  decay_days         -- trading days the elevated/reduced state persists
                         after the most recent qualifying trigger
  max_lump_multiple  -- hard ceiling, as a multiple of weekly_deposit, on
                         any single buy regardless of banked cash
  buy_mult_winning   -- fixed at 0.5 (not grid-varied), fraction of
                         weekly_deposit still bought during a reduced
                         (winning-streak) window
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_streaks(daily: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Causal (no-lookahead), magnitude-blind consecutive-same-direction-day
    counts. down_streak[t] = number of consecutive days ending at t
    (inclusive) with a strictly negative close-to-close change; 0 if today
    is not a down day (a flat day resets it to 0 too, per prereg.md's
    strict `dir_t = -1` rule). up_streak is symmetric for strictly positive
    changes. Undefined first day (t=0) is treated as 0/0 (no streak yet)."""
    close = daily["Close"].to_numpy(dtype=float)
    n = len(close)
    delta = np.diff(close, prepend=np.nan)
    down_streak = np.zeros(n, dtype=int)
    up_streak = np.zeros(n, dtype=int)
    for t in range(n):
        d = delta[t]
        if np.isnan(d):
            continue
        if d < 0:
            down_streak[t] = down_streak[t - 1] + 1 if t > 0 else 1
        elif d > 0:
            up_streak[t] = up_streak[t - 1] + 1 if t > 0 else 1
        # d == 0 (flat): both remain 0 for this day (already initialized)
    return down_streak, up_streak


def compute_state(daily: pd.DataFrame, streak_threshold: int, decay_days: int) -> np.ndarray:
    """Returns an array of strings: 'elevated', 'reduced', or 'normal'.
    'elevated' takes priority if both windows are simultaneously active
    (per prereg.md's documented priority rule). Strictly causal: last_down/
    last_up trigger indices are updated day by day using only data through
    that day's own close."""
    down_streak, up_streak = compute_streaks(daily)
    n = len(down_streak)
    state = np.full(n, "normal", dtype=object)

    last_down = -10 ** 9
    last_up = -10 ** 9
    for t in range(n):
        if down_streak[t] >= streak_threshold:
            last_down = t
        if up_streak[t] >= streak_threshold:
            last_up = t
        if t - last_down <= decay_days:
            state[t] = "elevated"
        elif t - last_up <= decay_days:
            state[t] = "reduced"
        else:
            state[t] = "normal"
    return state


def make_losing_streak_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    streak_threshold: int = 3, buy_mult_streak: float = 2.0,
    decay_days: int = 5, max_lump_multiple: float = 3.0,
    buy_mult_winning: float = 0.5,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the streak computation entirely and
    buys the full week's cash every week-end day (0 otherwise), which is
    bit-for-bit plain DCA."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)
    state = compute_state(daily, streak_threshold, decay_days) if enabled else None

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        st = state[t]
        if st == "elevated":
            target_buy_usd = buy_mult_streak * weekly_deposit
            capped_buy_usd = min(target_buy_usd, max_lump_multiple * weekly_deposit)
            final_buy_usd = min(cash, capped_buy_usd)
        elif st == "reduced":
            final_buy_usd = buy_mult_winning * weekly_deposit
        else:
            final_buy_usd = weekly_deposit
        return final_buy_usd, 0.0, {"streak_state": st}

    return decide


def make_decider_from_state(
    daily: pd.DataFrame, weekly_deposit: float, state: np.ndarray,
    buy_mult_streak: float = 2.0, max_lump_multiple: float = 3.0,
    buy_mult_winning: float = 0.5,
):
    """Same weekly decision rule as make_losing_streak_decider, but driven
    by an arbitrary pre-computed `state` array -- used by the placebo
    circular-shift robustness test (sec 4.3), which shifts the signal's
    TIMING while keeping its overall elevated/reduced/normal frequency
    identical."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)

    def decide(t, cash):
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        st = state[t]
        if st == "elevated":
            target_buy_usd = buy_mult_streak * weekly_deposit
            capped_buy_usd = min(target_buy_usd, max_lump_multiple * weekly_deposit)
            final_buy_usd = min(cash, capped_buy_usd)
        elif st == "reduced":
            final_buy_usd = buy_mult_winning * weekly_deposit
        else:
            final_buy_usd = weekly_deposit
        return final_buy_usd, 0.0, {"streak_state": st}

    return decide


CATEGORY = "Sizing / valuation"

# Grid: streak_threshold x buy_mult_streak x decay_days x max_lump_multiple
# = 3x2x3x2 = 36 (<=36 cap, 4 tunable params <=5; buy_mult_winning fixed at
# 0.5, not grid-varied)
GRID = {
    "streak_threshold": [2, 3, 4],
    "buy_mult_streak": [1.5, 2.0],
    "decay_days": [3, 5, 10],
    "max_lump_multiple": [2.5, 3.0],
}
BUY_MULT_WINNING = 0.5
PRIMARY_CONFIG = {
    "streak_threshold": 3, "buy_mult_streak": 2.0, "decay_days": 5,
    "max_lump_multiple": 3.0, "buy_mult_winning": BUY_MULT_WINNING,
}


def grid_configs() -> list[dict]:
    out = []
    for st in GRID["streak_threshold"]:
        for bms in GRID["buy_mult_streak"]:
            for dd in GRID["decay_days"]:
                for mlm in GRID["max_lump_multiple"]:
                    out.append({
                        "streak_threshold": st, "buy_mult_streak": bms,
                        "decay_days": dd, "max_lump_multiple": mlm,
                        "buy_mult_winning": BUY_MULT_WINNING,
                    })
    return out


# Module-import-time assertion (family 021's lesson, state/bugfix_log.md):
# verify PRIMARY_CONFIG is a genuine member of the declared grid before
# anything else in this module can be used.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG must be a member of grid_configs()"
