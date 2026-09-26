"""Family 047: CBOE SKEW Index tail-risk-pricing regime sizing (CBOE SKEW
Index methodology; Bali & Murray 2013; Xing, Zhang & Zhao 2010).

families/047-skew-index-sizing/prereg.md has the full mechanism and
rules. Summary: `skew_t` = CBOE SKEW Index daily close (a shared,
cross-market signal -- the standardized asymmetry/shape of the S&P 500
30-day option-implied-volatility SMILE, i.e. how much more expensive
deep out-of-the-money puts are than a log-normal model implies -- NOT
the LEVEL of VIX (family 016), NOT a VIX-minus-realized-vol spread
(family 025), NOT a VIX3M/VIX cross-tenor term-structure ratio (family
041), and NOT VVIX's vol-of-vol level (family 046): all four of those
hold the smile shape fixed and vary a level, a level-spread, a cross-
tenor slope, or a second-order level, while SKEW holds the tenor and
underlying fixed and varies the smile's ASYMMETRY). A causal, point-in-
time rolling percentile rank `pctile_t` of `skew_t` within its own
trailing `skew_lookback` history drives a continuous, INVERTED sizing
multiplier (risk-off sign, per prereg.md's sign-decision reasoning):

    m_t = clip(1 - k * (2 * pctile_t - 1), min_mult, max_mult)

Elevated SKEW percentile (tail-crash pricing is expensive right now)
-> buy LESS (bank a reserve). Depressed SKEW percentile (tail pricing is
unremarkable) -> buy MORE (deploy normally, up to a capped catch-up
lump). Never a sell; never leverage; cash never goes negative (engine's
own cap, sec 3.2). Identical functional form and grid shape to family
046's vvix_regime_sizing.py, applied to a different, materially distinct
signal.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import data as v3data

SKEW_TICKER = "^SKEW"

MAX_LUMP_MULTIPLE = 3.0


def _aligned_skew_close(daily_index: pd.DatetimeIndex) -> pd.Series:
    """SKEW close, forward-filled causally onto the asset's own trading-day
    index. Never fills backward. Identical alignment method to families
    016/025/041/046's own _aligned_vix_close()/_aligned_vvix_close()."""
    skew = v3data.fetch_yf_macro(SKEW_TICKER)
    unioned = skew.reindex(skew.index.union(daily_index)).sort_index().ffill()
    return unioned.reindex(daily_index).ffill()


def compute_percentile_rank(skew: pd.Series, skew_lookback: int) -> np.ndarray:
    """Causal, point-in-time rolling percentile rank of skew_t within the
    trailing skew_lookback window of past SKEW values ending at t
    (inclusive). Defaults to 0.5 (neutral) until skew_lookback days of
    valid SKEW history exist (a non-issue for GOLD/SILVER/OIL/BTC, whose
    dev histories all start after SKEW's 1990-01-02 start; only SP500's
    pre-1990 era sees the neutral default). Identical construction to
    family 046's compute_percentile_rank."""

    def _rank_last(window: np.ndarray) -> float:
        w = window[~np.isnan(window)]
        if len(w) == 0 or np.isnan(window[-1]):
            return np.nan
        return float(np.mean(w <= window[-1]))

    pct = skew.rolling(skew_lookback, min_periods=skew_lookback).apply(_rank_last, raw=True)
    pct = pct.to_numpy()
    pct = np.where(np.isnan(pct), 0.5, pct)
    return pct


def compute_multiplier(
    daily: pd.DataFrame, skew_lookback: int, k: float, min_mult: float, max_mult: float,
) -> np.ndarray:
    skew = _aligned_skew_close(daily.index)
    pct = compute_percentile_rank(skew, skew_lookback)
    # INVERTED sign (risk-off: elevated percentile -> buy LESS), the same
    # inverted form families 041/045/046 use for their own signals.
    m = 1.0 - k * (2.0 * pct - 1.0)
    m = np.clip(m, min_mult, max_mult)
    return m


def make_skew_regime_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    skew_lookback: int = 252, k: float = 1.0, min_mult: float = 0.5, max_mult: float = 2.0,
    max_lump_multiple: float = MAX_LUMP_MULTIPLE,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day, which is
    bit-for-bit plain DCA (used to prove the strategy nests DCA exactly).

    Explicit no-leverage clarification (research-loop-plan-v3.md sec 3.4 /
    sec 2's "no leverage" rule, families 030/031/036/039/040/041/046's own
    precedent): every buy here is capped at (a) a fixed multiple of the
    weekly deposit (`max_lump_multiple`, a hard ceiling regardless of
    banked cash) and (b) the engine's own unconditional cash cap
    (`buy_usd <= cash`, `engine.py` sec 3.2), so the strategy can never
    spend more than it has banked from actual past deposits plus earned
    interest -- no borrowing, no negative cash, ever.
    """
    if enabled:
        m = compute_multiplier(daily, skew_lookback, k, min_mult, max_mult)
    else:
        m = np.ones(len(daily), dtype=float)

    lump_cap = max_lump_multiple * weekly_deposit

    def decide(t, cash):
        target_buy_usd = weekly_deposit * float(m[t])
        capped_buy_usd = min(target_buy_usd, lump_cap)
        # No sells; the engine's own cash cap (sec 3.2) enforces
        # buy_usd<=cash, so a shortfall on a low-multiplier (elevated-
        # SKEW-percentile) week simply banks as cash (earning IRX) until a
        # later high-multiplier (depressed-SKEW-percentile) week can spend
        # it -- never leverage, never borrowing.
        return capped_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Volatility targeting"

# Grid: skew_lookback x k x min_mult x max_mult = 3x3x2x2 = 36 (at the sec 3.4 cap)
GRID = {
    "skew_lookback": [126, 252, 504],
    "k": [0.5, 1.0, 1.5],
    "min_mult": [0.25, 0.5],
    "max_mult": [1.5, 2.0],
}
PRIMARY_CONFIG = {
    "skew_lookback": 252, "k": 1.0, "min_mult": 0.5, "max_mult": 2.0,
}


def grid_configs() -> list[dict]:
    out = []
    for sl in GRID["skew_lookback"]:
        for k in GRID["k"]:
            for mn in GRID["min_mult"]:
                for mx in GRID["max_mult"]:
                    out.append({"skew_lookback": sl, "k": k, "min_mult": mn, "max_mult": mx})
    return out


# Import-time assertion (per family 021's lesson): PRIMARY_CONFIG must be a
# genuine member of the declared grid.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of the declared grid"

# Import-time assertion (families 014/033/037/039/040/041/046's now-7x-
# confirmed lesson): every grid cell's min_mult must be strictly below 1.0,
# or the engine's no-leverage cash cap silently nullifies the reserve-
# banking arm.
for _mm in GRID["min_mult"]:
    assert _mm < 1.0, f"min_mult={_mm!r} must be < 1.0 (families 014/033/037/039/040/041/046 lesson)"

assert len(grid_configs()) <= 36, "grid exceeds sec 3.4's 36-configuration cap"
