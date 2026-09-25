"""Family 001: 10-month / 200-day moving-average trend exit (Faber, 2007).

families/001-trend-exit/prereg.md has the full mechanism and rules. Summary:
buy the weekly deposit in full while the asset's close is above its
`sma_days`-day simple moving average; while it is below, park that week's
deposit in cash (earning IRX) instead of buying. No selling of existing
holdings in the primary configuration (a `sell_on_exit` grid arm tests the
classic Faber variant that DOES sell to cash on a cross-below, as a
diagnostic, but is not eligible to become the primary/finalist config -- see
prereg.md).

Category: Trend / time-series momentum exit.

Parameters (<=5, all in this module):
  sma_days      -- lookback for the simple moving average (default 210, ~10 months)
  confirm_days  -- consecutive days the close must stay below (or above) the
                   SMA before the state actually flips (0 = flip immediately)
  sell_on_exit  -- 0/1: if 1, sell 100% of holdings to cash on a confirmed
                   cross-below (classic Faber); if 0, only deposits are toggled
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_signal(daily: pd.DataFrame, sma_days: int, confirm_days: int) -> np.ndarray:
    """Returns a boolean array, `invested_state[t]` = True if new deposits
    should be invested at day t's decision (close of day t), causal only
    (uses data through t). Before enough history exists for the SMA, defaults
    to True (invested) -- there is no signal yet, so a DCA baseline is used,
    which also makes the sma_days->None disabled path (below) exact."""
    close = daily["Close"].to_numpy()
    n = len(close)
    sma = pd.Series(close).rolling(sma_days, min_periods=sma_days).mean().to_numpy()
    above = close > sma
    above = np.where(np.isnan(sma), True, above)  # no signal yet -> default invested (matches DCA there)

    if confirm_days <= 0:
        return above

    state = np.ones(n, dtype=bool)  # start invested
    run = 0
    cur = True
    for t in range(n):
        if above[t] == cur:
            run = 0
        else:
            run += 1
            if run >= confirm_days:
                cur = above[t]
                run = 0
        state[t] = cur
    return state


def make_trend_exit_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    sma_days: int = 210, confirm_days: int = 0, sell_on_exit: int = 0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces `above`=True for every day, which is
    bit-for-bit plain DCA (used to prove the strategy nests DCA exactly)."""
    if enabled:
        invested_state = compute_signal(daily, sma_days, confirm_days)
    else:
        invested_state = np.ones(len(daily), dtype=bool)

    prev_state = {"was_invested": True}

    def decide(t, cash):
        is_invested_now = bool(invested_state[t])
        sell_usd = 0.0
        if sell_on_exit and prev_state["was_invested"] and not is_invested_now:
            sell_usd = 1e18  # engine caps sells at held units; this just signals "sell everything"
        prev_state["was_invested"] = is_invested_now
        buy_usd = cash if is_invested_now else 0.0
        return buy_usd, sell_usd, {"invested_state": is_invested_now}

    return decide


CATEGORY = "Trend / time-series momentum exit"

# Grid: sma_days x confirm_days x sell_on_exit = 3 x 3 x 2 = 18 configs (<=36, 3 params <=5)
GRID = {
    "sma_days": [189, 210, 231],       # ~9, ~10, ~11 trading months
    "confirm_days": [0, 3, 5],
    "sell_on_exit": [0, 1],
}
PRIMARY_CONFIG = {"sma_days": 210, "confirm_days": 0, "sell_on_exit": 0}


def grid_configs() -> list[dict]:
    out = []
    for s in GRID["sma_days"]:
        for c in GRID["confirm_days"]:
            for x in GRID["sell_on_exit"]:
                out.append({"sma_days": s, "confirm_days": c, "sell_on_exit": x})
    return out
