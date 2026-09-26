"""Family 034: 52-week-low proximity contrarian tilt.

families/034-52wk-low-tilt/prereg.md has the full mechanism, rules, and the
required distinctions from families 014 and 020 (especially the
family-020 sign-inversion point: this family's ladder must be increasing
in proximity to the LOW, the literal opposite reference extremum from
family 020's proximity-to-HIGH ladder). Summary: track each asset's own
trailing 52-week-low close price, causally. Proximity ratio
`prox_low_t = low52_t / close_t in (0, 1]` (=1.0 exactly on a new 52-week
low). Buy multiplier is a 3-tier step ladder of `prox_low_t`, INCREASING as
price gets closer to its 52-week low (the opposite ordering of family 020's
52-week-high ladder, which increases as price gets closer to its high):
`mult_far` while `prox_low_t < far_thresh` (far ABOVE the low), `mult_mid`
while `far_thresh <= prox_low_t < near_thresh`, `mult_near` while
`prox_low_t >= near_thresh` (AT/near the low) (`mult_far < mult_mid <
mult_near`). The order submitted each week's decision day is
`buy_usd = min(weekly_deposit * m_t, weekly_deposit * max_lump_cap)`, never
a sell; the engine's own cash cap (sec 3.2) turns a far-above-low week's
(m_t<1) shortfall into banked cash (earning IRX) that only then funds a
later near-low (m_t>1) week -- the same reserve mechanism families
003/005/014/020 use, never leverage or borrowing.

Category: Sizing / valuation.

Parameters (4 of the allowed 5, all in this module):
  window_def   -- "trading252" (rolling min over trailing 252 trading days)
                   or "calendar" (rolling min over trailing 365 calendar
                   days on the asset's own trading-day index).
  ladder        -- bundled preset name selecting (far_thresh, near_thresh,
                    mult_far, mult_mid); see LADDER_PRESETS below.
  mult_near     -- buy multiplier while prox_low_t >= near_thresh (the "buy
                    MORE near the low" regime).
  max_lump_cap  -- ceiling on buy_usd as a multiple of weekly_deposit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252

LADDER_PRESETS = {
    "mild":       {"far_thresh": 0.80, "near_thresh": 0.95, "mult_far": 0.65, "mult_mid": 0.85},
    "moderate":   {"far_thresh": 0.80, "near_thresh": 0.95, "mult_far": 0.50, "mult_mid": 0.75},
    "aggressive": {"far_thresh": 0.70, "near_thresh": 0.97, "mult_far": 0.30, "mult_mid": 0.60},
    "flat":       {"far_thresh": 0.80, "near_thresh": 0.95, "mult_far": 1.0,  "mult_mid": 1.0},
}


def compute_low52(close: np.ndarray, index: pd.DatetimeIndex, window_def: str) -> np.ndarray:
    """Causal trailing 52-week low: low52_t depends only on close_0..close_t.
    "trading252" -> rolling min over the trailing 252 trading days (falls
    back to the expanding min while fewer observations exist).
    "calendar" -> rolling min over the trailing 365 calendar days on the
    asset's own trading-day index (date-indexed rolling window)."""
    s = pd.Series(close, index=index)
    if window_def == "trading252":
        low52 = s.rolling(window=TRADING_DAYS_PER_YEAR, min_periods=1).min()
    elif window_def == "calendar":
        low52 = s.rolling(window="365D", min_periods=1).min()
    else:
        raise ValueError(f"unknown window_def: {window_def!r}")
    return low52.to_numpy()


def compute_proximity_to_low(daily: pd.DataFrame, window_def: str) -> np.ndarray:
    """prox_low_t = low52_t / close_t, in (0, 1]; =1.0 exactly on a new
    52-week low (since low52_t = close_t that day). This is the mirror
    image of high52wk_tilt.compute_proximity's prox_t = close_t/high52_t --
    here the reference extremum (a running MINIMUM, not maximum) sits in
    the NUMERATOR, so the ratio is largest (closest to 1) when price is
    closest to its own trailing low, not its trailing high."""
    close = daily["Close"].to_numpy()
    low52 = compute_low52(close, daily.index, window_def)
    prox_low = low52 / close
    return np.clip(prox_low, 0.0, 1.0)  # numerically prox_low<=1 by construction; clip guards fp noise


def compute_multiplier(
    daily: pd.DataFrame, window_def: str, ladder: str,
    mult_near: float, max_lump_cap: float,
) -> np.ndarray:
    prox_low = compute_proximity_to_low(daily, window_def)
    preset = LADDER_PRESETS[ladder]
    m = np.where(
        prox_low >= preset["near_thresh"], mult_near,
        np.where(prox_low >= preset["far_thresh"], preset["mult_mid"], preset["mult_far"]),
    )
    m = np.minimum(m, max_lump_cap)
    return m


def make_low52wk_tilt_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    window_def: str = "trading252", ladder: str = "moderate",
    mult_near: float = 1.5, max_lump_cap: float = 3.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day (skips the
    proximity/ladder computation entirely), which is bit-for-bit plain DCA
    (reference point 1 of the two-reference-point pattern; see prereg.md)."""
    if enabled:
        m = compute_multiplier(daily, window_def, ladder, mult_near, max_lump_cap)
    else:
        m = np.ones(len(daily), dtype=float)

    def decide(t, cash):
        target_buy_usd = weekly_deposit * float(m[t])
        # No sells; the engine's own cash cap (sec 3.2) enforces buy_usd<=cash,
        # so a shortfall on a far-above-low (m_t<1) week simply banks as cash
        # (earning IRX) until a later near-low (m_t>1) week can spend it.
        return target_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Sizing / valuation"

# Grid: window_def(2) x ladder(4) x mult_near(2) x max_lump_cap(2) = 32 (<=36 cap, 4 params <=5)
GRID = {
    "window_def": ["trading252", "calendar"],
    "ladder": ["mild", "moderate", "aggressive", "flat"],
    "mult_near": [1.5, 2.0],
    "max_lump_cap": [2.0, 3.0],
}
PRIMARY_CONFIG = {
    "window_def": "trading252", "ladder": "moderate",
    "mult_near": 1.5, "max_lump_cap": 3.0,
}


def grid_configs() -> list[dict]:
    out = []
    for wd in GRID["window_def"]:
        for lad in GRID["ladder"]:
            for mn in GRID["mult_near"]:
                for mlc in GRID["max_lump_cap"]:
                    out.append({
                        "window_def": wd, "ladder": lad,
                        "mult_near": mn, "max_lump_cap": mlc,
                    })
    return out


# Task instruction (a): verify PRIMARY_CONFIG is a genuine member of the
# declared grid at import time, before any backtest can run.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of grid_configs()"

# Task instruction (b)/(c): sign and cash-reserve sanity, checked structurally
# here (the empirical top/bottom-quartile check itself runs in the run
# script on real data, per prereg.md's "Implementation checks" sec 8).
_primary_ladder = LADDER_PRESETS[PRIMARY_CONFIG["ladder"]]
assert _primary_ladder["mult_far"] < _primary_ladder["mult_mid"] < PRIMARY_CONFIG["mult_near"], (
    "ladder must be increasing in proximity to the LOW (mult_far < mult_mid < mult_near)"
)
assert _primary_ladder["mult_far"] < 1.0, (
    "family-033 lesson: the 'far from low' (normal) state's multiplier must be "
    "strictly below 1.0 so a cash reserve actually accumulates"
)
assert PRIMARY_CONFIG["mult_near"] > 1.0, "the 'near low' regime must buy MORE than plain DCA"
