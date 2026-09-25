"""Family 028: 50/200-day moving-average crossover regime tilt
("golden cross" / "death cross") -- Brock, Lakonishok & LeBaron (1992).

families/028-ma-crossover-regime/prereg.md has the full mechanism and
rules. Summary: compute two simple moving averages of price, SMA_fast and
SMA_slow. A golden cross (SMA_fast crosses above SMA_slow) is a confirmed
bullish regime; a death cross (SMA_fast crosses below SMA_slow) is a
confirmed bearish regime, each requiring `persistence_days` consecutive
trading days to confirm (a whipsaw-reduction filter). The weekly order is
`buy_usd = weekly_deposit * (bull_mult if confirmed_bullish else
bear_mult)` -- never sells; the engine's own cash cap (sec 3.2) turns a
below-1x week into banked cash (earning IRX), available to fund a later
above-1x week, the same reserve mechanic family 005's TSMOM sizing uses.

Rigorously distinct from family 001 (single MA vs. price level, binary
in/out) and family 005 (sign of trailing total RETURN, no moving average
at all) -- see prereg.md for the full argument.

Category: Trend / time-series momentum exit.

Parameters (<=5, all in this module):
  fast_days, slow_days   -- the two SMA windows (grid varies the PAIR)
  persistence_days       -- consecutive trading days required to confirm
                             a regime flip (whipsaw-reduction filter)
  bull_mult              -- buy-size multiplier in a confirmed golden-cross
                             (bullish) regime
  bear_mult              -- buy-size multiplier in a confirmed death-cross
                             (bearish) regime
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_raw_bullish(daily: pd.DataFrame, fast_days: int, slow_days: int) -> np.ndarray:
    """Returns bullish_raw[t]: True if SMA_fast_t > SMA_slow_t (golden-cross
    regime, strictly causal -- each SMA at t uses only Close[<=t]). Before
    both SMAs exist, defaults to True (no signal yet -> default to
    plain-DCA-equivalent, matching families 001/005's own convention)."""
    close = daily["Close"]
    sma_fast = close.rolling(fast_days, min_periods=fast_days).mean()
    sma_slow = close.rolling(slow_days, min_periods=slow_days).mean()
    bullish = (sma_fast > sma_slow).to_numpy()
    no_signal_yet = sma_fast.isna().to_numpy() | sma_slow.isna().to_numpy()
    bullish = np.where(no_signal_yet, True, bullish)
    return bullish


def apply_persistence(bullish_raw: np.ndarray, persistence_days: int) -> np.ndarray:
    """Confirms a regime flip only after `persistence_days` consecutive
    trading days of the new raw state (rolling all-equal confirmation
    window). persistence_days<=0 -> passthrough (no confirmation delay)."""
    n = len(bullish_raw)
    if persistence_days <= 0:
        return bullish_raw.copy()
    state = np.ones(n, dtype=bool)  # start bullish (matches "no signal yet" default)
    run = 0
    cur = True
    for t in range(n):
        if bullish_raw[t] == cur:
            run = 0
        else:
            run += 1
            if run >= persistence_days:
                cur = bullish_raw[t]
                run = 0
        state[t] = cur
    return state


def compute_confirmed_bullish(daily: pd.DataFrame, fast_days: int, slow_days: int,
                               persistence_days: int) -> np.ndarray:
    raw = compute_raw_bullish(daily, fast_days, slow_days)
    return apply_persistence(raw, persistence_days)


def compute_multiplier(daily: pd.DataFrame, fast_days: int, slow_days: int,
                        persistence_days: int, bull_mult: float, bear_mult: float) -> np.ndarray:
    confirmed = compute_confirmed_bullish(daily, fast_days, slow_days, persistence_days)
    return np.where(confirmed, bull_mult, bear_mult).astype(float)


def make_ma_crossover_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    fast_days: int = 50, slow_days: int = 200, persistence_days: int = 5,
    bull_mult: float = 1.5, bear_mult: float = 0.5,
    max_lump_multiple: float = 6.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces the multiplier to 1.0 for every day,
    which is bit-for-bit plain DCA (used to prove the strategy nests DCA
    exactly)."""
    if enabled:
        m = compute_multiplier(daily, fast_days, slow_days, persistence_days, bull_mult, bear_mult)
    else:
        m = np.ones(len(daily), dtype=float)

    def decide(t, cash):
        target_buy_usd = weekly_deposit * float(m[t])
        # Cash-capped: never leverage. The engine's own cap (sec 3.2) turns a
        # below-1x week into banked cash, available for a later above-1x week.
        # max_lump_multiple bounds how large a single catch-up buy can be even
        # when a large cash reserve has built up (headroom essentially never
        # binds at the grid's bull_mult<=1.5, same convention as families
        # 011/027, kept here for parity and future-proofing against larger
        # bull_mult grid arms).
        capped_buy_usd = min(target_buy_usd, max_lump_multiple * weekly_deposit)
        return capped_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Trend / time-series momentum exit"

# Grid: ma_pair x persistence_days x bull_mult x bear_mult = 3x3x2x2 = 36 (<=36 cap, 4 tunable params <=5)
MA_PAIRS = [(50, 200), (20, 100), (50, 150)]
GRID = {
    "ma_pair": MA_PAIRS,
    "persistence_days": [0, 5, 10],
    "bull_mult": [1.25, 1.5],
    "bear_mult": [0.5, 0.75],
}
PRIMARY_CONFIG = {
    "fast_days": 50, "slow_days": 200, "persistence_days": 5,
    "bull_mult": 1.5, "bear_mult": 0.5,
}


def grid_configs() -> list[dict]:
    out = []
    for fast, slow in GRID["ma_pair"]:
        for pd_ in GRID["persistence_days"]:
            for bm in GRID["bull_mult"]:
                for be in GRID["bear_mult"]:
                    out.append({
                        "fast_days": fast, "slow_days": slow, "persistence_days": pd_,
                        "bull_mult": bm, "bear_mult": be,
                    })
    return out


# Module-import-time assertion (family 021's lesson, state/bugfix_log.md):
# verify PRIMARY_CONFIG is a genuine member of the declared grid before
# anything else in this module can be used.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG must be a member of grid_configs()"
