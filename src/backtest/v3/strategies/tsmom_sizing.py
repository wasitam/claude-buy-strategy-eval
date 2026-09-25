"""Family 005: time-series momentum sizing (Moskowitz, Ooi & Pedersen 2012).

families/005-tsmom-sizing/prereg.md has the full mechanism and rules.
Summary: each week-end decision day, compute the asset's own trailing total
return over `lookback_days` trading days, ending `skip_days` before today
(the standard "skip the most recent month" momentum convention). The sizing
multiplier is a pure step function of the SIGN of that trailing return:
`m_t = mult_pos if mom_t > 0 else mult_neg`. The order submitted that week is
`buy_usd = weekly_deposit * m_t` (never sells); the engine's own cash cap
(sec 3.2) turns a below-deposit week (m_t < 1) into banked cash that is only
then available to fund an above-deposit week (m_t > 1) later -- the same
reserve mechanism family 003 uses, never leverage or borrowing.

Category: Trend / time-series momentum exit.

Parameters (<=5, all in this module):
  lookback_days -- trailing window for the momentum signal (trading days)
  mult_pos       -- buy-size multiplier when trailing momentum is positive
  mult_neg       -- buy-size multiplier when trailing momentum is negative
  skip_days      -- most-recent days excluded from the lookback window
                     (skip-the-most-recent-month convention)
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_signal(daily: pd.DataFrame, lookback_days: int, skip_days: int) -> np.ndarray:
    """Returns mom_t, the causal (no-lookahead) trailing total-return signal
    for each day, using only data through that day's close. NaN until enough
    history exists (ref_t - lookback_days >= 0)."""
    close = daily["Close"].to_numpy()
    n = len(close)
    mom = np.full(n, np.nan)
    for t in range(n):
        ref_t = t - skip_days
        base_t = ref_t - lookback_days
        if ref_t >= 0 and base_t >= 0:
            mom[t] = close[ref_t] / close[base_t] - 1.0
    return mom


def compute_multiplier(daily: pd.DataFrame, lookback_days: int, skip_days: int,
                        mult_pos: float, mult_neg: float) -> np.ndarray:
    mom = compute_signal(daily, lookback_days, skip_days)
    m = np.where(mom > 0, mult_pos, mult_neg)
    m = np.where(np.isnan(mom), 1.0, m)  # not enough history yet -> default to plain DCA
    return m


def make_tsmom_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    lookback_days: int = 252, skip_days: int = 21,
    mult_pos: float = 1.5, mult_neg: float = 0.5,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day, which is
    bit-for-bit plain DCA (used to prove the strategy nests DCA exactly)."""
    if enabled:
        m = compute_multiplier(daily, lookback_days, skip_days, mult_pos, mult_neg)
    else:
        m = np.ones(len(daily), dtype=float)

    def decide(t, cash):
        target_buy_usd = weekly_deposit * float(m[t])
        # No sells; the engine's own cash cap (sec 3.2) enforces buy_usd<=cash,
        # so a shortfall on a low-multiplier week simply banks as cash (earning
        # IRX) until a later high-multiplier week can spend it.
        return target_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Trend / time-series momentum exit"

# Grid: lookback_days x mult_pos x mult_neg x skip_days = 3x2x2x2 = 24 (<=36 cap, 4 params <=5)
GRID = {
    "lookback_days": [126, 252, 378],
    "mult_pos": [1.25, 1.5],
    "mult_neg": [0.5, 0.75],
    "skip_days": [0, 21],
}
PRIMARY_CONFIG = {
    "lookback_days": 252, "skip_days": 21, "mult_pos": 1.5, "mult_neg": 0.5,
}


def grid_configs() -> list[dict]:
    out = []
    for lb in GRID["lookback_days"]:
        for mp in GRID["mult_pos"]:
            for mn in GRID["mult_neg"]:
                for sk in GRID["skip_days"]:
                    out.append({
                        "lookback_days": lb, "skip_days": sk,
                        "mult_pos": mp, "mult_neg": mn,
                    })
    return out
