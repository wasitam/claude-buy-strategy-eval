"""Family 041: VIX futures term-structure carry (contango/backwardation)
(Simon & Campasano 2014; Cheng 2019).

families/041-vix-term-structure-carry/prereg.md has the full mechanism and
rules. Summary: `ratio_t = VIX3M_t / VIX_t` (a shared, cross-market
signal, both legs option-implied volatility at two DIFFERENT tenors on the
SAME curve -- never realized volatility, never either tenor alone). A
causal, point-in-time rolling percentile rank `pctile_t` of `ratio_t`
within its own trailing `ts_lookback` history drives a continuous sizing
multiplier (identical functional form to families 030/031/036/039/040's
own percentile-to-multiplier construction):

    m_t = clip(1 + k * (2 * pctile_t - 1), min_mult, max_mult)

Elevated ratio percentile (deep contango, the normal/calm state) -> buy
MORE (ride the carry premium). Depressed ratio percentile (backwardation
or shallow contango) -> buy LESS (bank a reserve). Never a sell; never
leverage; cash never goes negative (engine's own cap, sec 3.2).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import data as v3data

VIX_TICKER = "^VIX"
VIX3M_TICKER = "^VIX3M"

MAX_LUMP_MULTIPLE = 3.0


def _aligned_close(ticker: str, daily_index: pd.DatetimeIndex) -> pd.Series:
    """Causal forward-fill onto the asset's own trading-day index. Never
    fills backward. Identical alignment method to families 016/025's
    _aligned_vix_close()."""
    s = v3data.fetch_yf_macro(ticker)
    unioned = s.reindex(s.index.union(daily_index)).sort_index().ffill()
    return unioned.reindex(daily_index).ffill()


def compute_ratio(daily_index: pd.DatetimeIndex) -> pd.Series:
    """ratio_t = VIX3M_t / VIX_t, causal, aligned to daily_index. NaN
    wherever either leg is unavailable (pre-^VIX3M-start, or a warm-up gap
    in either series)."""
    vix = _aligned_close(VIX_TICKER, daily_index)
    vix3m = _aligned_close(VIX3M_TICKER, daily_index)
    ratio = vix3m / vix
    # Both legs individually ffilled already; a ratio is only valid where
    # BOTH legs have ever had a real observation by day t (not merely
    # forward-filled from before either series started at all).
    vix_ever = vix.notna()
    vix3m_ever = vix3m.notna()
    ratio = ratio.where(vix_ever & vix3m_ever)
    return ratio


def compute_percentile_rank(ratio: pd.Series, ts_lookback: int) -> np.ndarray:
    """Causal, point-in-time rolling percentile rank of ratio_t within the
    trailing ts_lookback window of past ratio values ending at t
    (inclusive). Defaults to 0.5 (neutral) until ts_lookback days of valid
    ratio history exist. Identical construction to families 036/039/040's
    compute_percentile_rank."""

    def _rank_last(window: np.ndarray) -> float:
        w = window[~np.isnan(window)]
        if len(w) == 0 or np.isnan(window[-1]):
            return np.nan
        return float(np.mean(w <= window[-1]))

    pct = ratio.rolling(ts_lookback, min_periods=ts_lookback).apply(_rank_last, raw=True)
    pct = pct.to_numpy()
    pct = np.where(np.isnan(pct), 0.5, pct)
    return pct


def compute_multiplier(
    daily: pd.DataFrame, ts_lookback: int, k: float, min_mult: float, max_mult: float,
) -> np.ndarray:
    ratio = compute_ratio(daily.index)
    pct = compute_percentile_rank(ratio, ts_lookback)
    m = 1.0 + k * (2.0 * pct - 1.0)
    m = np.clip(m, min_mult, max_mult)
    return m


def make_term_structure_carry_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    ts_lookback: int = 252, k: float = 1.0, min_mult: float = 0.5, max_mult: float = 2.0,
    max_lump_multiple: float = MAX_LUMP_MULTIPLE,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day, which is
    bit-for-bit plain DCA (used to prove the strategy nests DCA exactly).

    Explicit no-leverage clarification (research-loop-plan-v3.md sec 3.4 /
    sec 2's "no leverage" rule, families 030/031/036/039/040's own
    precedent): every buy here is capped at (a) a fixed multiple of the
    weekly deposit (`max_lump_multiple`, a hard ceiling regardless of
    banked cash) and (b) the engine's own unconditional cash cap
    (`buy_usd <= cash`, `engine.py` sec 3.2), so the strategy can never
    spend more than it has banked from actual past deposits plus earned
    interest -- no borrowing, no negative cash, ever.
    """
    if enabled:
        m = compute_multiplier(daily, ts_lookback, k, min_mult, max_mult)
    else:
        m = np.ones(len(daily), dtype=float)

    lump_cap = max_lump_multiple * weekly_deposit

    def decide(t, cash):
        target_buy_usd = weekly_deposit * float(m[t])
        capped_buy_usd = min(target_buy_usd, lump_cap)
        # No sells; the engine's own cash cap (sec 3.2) enforces
        # buy_usd<=cash, so a shortfall on a low-multiplier (backwardation-
        # percentile) week simply banks as cash (earning IRX) until a
        # later high-multiplier (deep-contango-percentile) week can spend
        # it -- never leverage, never borrowing.
        return capped_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Carry / term structure"

# Grid: ts_lookback x k x min_mult x max_mult = 3x3x2x2 = 36 (at the sec 3.4 cap)
GRID = {
    "ts_lookback": [126, 252, 504],
    "k": [0.5, 1.0, 1.5],
    "min_mult": [0.25, 0.5],
    "max_mult": [1.5, 2.0],
}
PRIMARY_CONFIG = {
    "ts_lookback": 252, "k": 1.0, "min_mult": 0.5, "max_mult": 2.0,
}


def grid_configs() -> list[dict]:
    out = []
    for tl in GRID["ts_lookback"]:
        for k in GRID["k"]:
            for mn in GRID["min_mult"]:
                for mx in GRID["max_mult"]:
                    out.append({"ts_lookback": tl, "k": k, "min_mult": mn, "max_mult": mx})
    return out


# Import-time assertion (per family 021's lesson): PRIMARY_CONFIG must be a
# genuine member of the declared grid.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of the declared grid"

# Import-time assertion (families 014/033/037/039/040's now-5x-confirmed
# lesson): every grid cell's min_mult must be strictly below 1.0, or the
# engine's no-leverage cash cap silently nullifies the reserve-banking arm.
for _mm in GRID["min_mult"]:
    assert _mm < 1.0, f"min_mult={_mm!r} must be < 1.0 (families 014/033/037/039/040 lesson)"

assert len(grid_configs()) <= 36, "grid exceeds sec 3.4's 36-configuration cap"
