"""Family 037: drawdown-DURATION (time-underwater) sizing (seed queue #35).

families/037-drawdown-duration/prereg.md has the full mechanism, rules, and
the required rigorous distinction from family 014. Summary: track each
asset's own trailing reference-high close price, causally (same
`ATH_t` definition family 014 uses). The signal is NOT the percentage
shortfall from that high (family 014's statistic) but the count of
trading days elapsed since the close last touched or exceeded that high,
`dur_t` -- a pure elapsed-time counter with zero dependence on how far
below the high today's close currently sits. Buy multiplier is a 3-tier
step ladder of `dur_t`: `near_high_mult` while `dur_t < dur1_days`,
`mult_tier1` while `dur1_days <= dur_t < dur2_days`, `mult_tier2` while
`dur_t >= dur2_days`. The order submitted each week's decision day is
`buy_usd = min(weekly_deposit * m_t, weekly_deposit * max_lump_cap)`,
never a sell; the engine's own cash cap (sec 3.2) turns a
`near_high_mult < 1` week's shortfall into banked cash (earning IRX) that
only then funds a later `m_t > 1` week -- the same reserve mechanism
families 003/005/014 use, never leverage or borrowing.

Category: Sizing / valuation.

Parameters (4 of the allowed 5, all in this module):
  ath_lookback_years -- None (unbounded, expanding-window running max) or a
                          number of years (trailing rolling-window running
                          max), same role as family 014's parameter of the
                          same name.
  ladder              -- bundled preset name selecting (dur1_days,
                          dur2_days, mult_tier1, mult_tier2); see
                          LADDER_PRESETS below.
  near_high_mult       -- buy multiplier while dur_t < dur1_days.
  max_lump_cap         -- ceiling on buy_usd as a multiple of weekly_deposit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252

LADDER_PRESETS = {
    "mild":       {"dur1_days": 63,  "dur2_days": 252, "mult_tier1": 1.25, "mult_tier2": 1.75},
    "moderate":   {"dur1_days": 63,  "dur2_days": 252, "mult_tier1": 1.5,  "mult_tier2": 2.0},
    "aggressive": {"dur1_days": 126, "dur2_days": 504, "mult_tier1": 2.0,  "mult_tier2": 3.0},
    "flat":       {"dur1_days": 63,  "dur2_days": 252, "mult_tier1": 1.0,  "mult_tier2": 1.0},
}


def compute_ath(close: np.ndarray, ath_lookback_years: float | None) -> np.ndarray:
    """Causal trailing reference-high: ATH_t depends only on close_0..close_t.
    Unbounded (None) -> expanding running max. Bounded -> trailing rolling
    running max over round(252*ath_lookback_years) trading days (falls back
    to the expanding max while fewer observations exist). Identical
    definition to family 014's compute_ath, kept for direct comparability
    of the reference-point choice between the two families."""
    s = pd.Series(close)
    if ath_lookback_years is None:
        ath = s.cummax()
    else:
        window = max(1, round(TRADING_DAYS_PER_YEAR * ath_lookback_years))
        ath = s.rolling(window=window, min_periods=1).max()
    return ath.to_numpy()


def compute_drawdown(close: np.ndarray, ath_lookback_years: float | None) -> np.ndarray:
    """Family 014's statistic (percentage-magnitude shortfall), computed
    here ONLY for the required distinction check against this family's own
    duration statistic -- not used anywhere in this family's own decider."""
    ath = compute_ath(close, ath_lookback_years)
    dd = 1.0 - close / ath
    return np.clip(dd, 0.0, None)


def compute_days_since_peak(close: np.ndarray, ath_lookback_years: float | None) -> np.ndarray:
    """This family's defining statistic: a strictly causal count of trading
    days since the close last touched or exceeded the reference high
    ATH_t. dur_t = 0 on any day close_t >= ATH_t (a new/matched high),
    else dur_t = dur_{t-1} + 1. The depth ratio close_t/ATH_t never enters
    this computation at all -- the distinction from compute_drawdown
    above."""
    ath = compute_ath(close, ath_lookback_years)
    is_high = close >= ath - 1e-12
    n = len(close)
    dur = np.zeros(n, dtype=float)
    running = 0
    for t in range(n):
        if is_high[t]:
            running = 0
        else:
            running += 1
        dur[t] = running
    return dur


def compute_multiplier(
    daily: pd.DataFrame, ath_lookback_years: float | None, ladder: str,
    near_high_mult: float, max_lump_cap: float,
) -> np.ndarray:
    close = daily["Close"].to_numpy()
    dur = compute_days_since_peak(close, ath_lookback_years)
    preset = LADDER_PRESETS[ladder]
    m = np.where(
        dur < preset["dur1_days"], near_high_mult,
        np.where(dur < preset["dur2_days"], preset["mult_tier1"], preset["mult_tier2"]),
    )
    m = np.minimum(m, max_lump_cap)
    return m


def make_drawdown_duration_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    ath_lookback_years: float | None = None, ladder: str = "moderate",
    near_high_mult: float = 1.0, max_lump_cap: float = 3.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day (skips the
    duration/ladder computation entirely), which is bit-for-bit plain DCA
    (reference point 1 of the two-reference-point pattern; see
    prereg.md)."""
    if enabled:
        m = compute_multiplier(daily, ath_lookback_years, ladder, near_high_mult, max_lump_cap)
    else:
        m = np.ones(len(daily), dtype=float)

    def decide(t, cash):
        target_buy_usd = weekly_deposit * float(m[t])
        # No sells; the engine's own cash cap (sec 3.2) enforces buy_usd<=cash,
        # so a shortfall on a near-high (m_t<1) week simply banks as cash
        # (earning IRX) until a later long-duration (m_t>1) week spends it.
        return target_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Sizing / valuation"

# Grid: ath_lookback_years(2) x ladder(4) x near_high_mult(2) x max_lump_cap(2) = 32 (<=36 cap, 4 params <=5)
GRID = {
    "ath_lookback_years": [None, 10],
    "ladder": ["mild", "moderate", "aggressive", "flat"],
    "near_high_mult": [0.75, 1.0],
    "max_lump_cap": [2.0, 3.0],
}
PRIMARY_CONFIG = {
    "ath_lookback_years": None, "ladder": "moderate",
    "near_high_mult": 1.0, "max_lump_cap": 3.0,
}


def grid_configs() -> list[dict]:
    out = []
    for al in GRID["ath_lookback_years"]:
        for lad in GRID["ladder"]:
            for nhm in GRID["near_high_mult"]:
                for mlc in GRID["max_lump_cap"]:
                    out.append({
                        "ath_lookback_years": al, "ladder": lad,
                        "near_high_mult": nhm, "max_lump_cap": mlc,
                    })
    return out


assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG must be a member of the declared grid"
