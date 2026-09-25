"""Family 016: VIX contrarian fear-gauge sizing (Whaley 2000).

families/016-vix-contrarian/prereg.md has the full mechanism and rules.
Summary: the CBOE VIX (^VIX, S&P 500 option-implied vol -- a single shared
cross-market signal, NOT each asset's own realized volatility) spiking into
an elevated trailing percentile marks a "fear" regime. Deposits are sized
UP (buy_multiplier * weekly_deposit, cash-capped) during a confirmed
elevated-fear week, funded by banking a small fraction of every calm
week's deposit as cash (earning IRX). This is deliberately the OPPOSITE
sign and a different signal from family 003's vol_managed_sizing (each
asset's own realized vol, continuous, inverse relationship) -- see
prereg.md's "Rigorous distinction from family 003" section. No sells,
ever; no leverage; cash never goes negative.

Category: Sizing / valuation.

Parameters (4 tunable + 1 fixed, all <=5):
  vix_lookback     -- trailing window (trading days) for the VIX
                       percentile-rank calculation
  elevated_pct     -- percentile threshold for the elevated-fear flag
  buy_multiplier   -- multiple of weekly_deposit bought when elevated
  calm_fraction    -- fraction of deposit bought in calm weeks (remainder
                       banked to fund elevated-week extra buying)
  max_buy_multiple -- fixed at 4.0 (not grid-varied), hard ceiling on any
                       single week's buy relative to weekly_deposit
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import data as v3data

VIX_TICKER = "^VIX"


def _aligned_vix_close(daily_index: pd.DatetimeIndex) -> pd.Series:
    """VIX close, forward-filled causally onto the asset's own trading-day
    index (VIX trades on its own calendar, e.g. it is closed some days BTC
    trades). Never fills backward. Same alignment pattern as family 015's
    DXY helper."""
    vix = v3data.fetch_yf_macro(VIX_TICKER)
    unioned = vix.reindex(vix.index.union(daily_index)).sort_index().ffill()
    return unioned.reindex(daily_index).ffill()


def compute_elevated(daily: pd.DataFrame, vix_lookback: int, elevated_pct: float) -> np.ndarray:
    """Boolean array, True = elevated-fear regime, aligned to daily.index.
    Causal only: percentile_t uses only VIX closes through t (a trailing
    rolling percentile rank -- the fraction of the trailing vix_lookback
    closes, through and including day t, that are <= the close on day t).
    Before enough VIX history exists (warm-up, or pre-1990 for any asset's
    dev history that predates VIX), elevated defaults to False (calm/
    DCA-like), matching family 001/011/015's warm-up convention."""
    vix_close = _aligned_vix_close(daily.index)

    def _pctile_rank(window: np.ndarray) -> float:
        return float((window <= window[-1]).mean() * 100.0)

    percentile = vix_close.rolling(vix_lookback, min_periods=vix_lookback).apply(_pctile_rank, raw=True)
    elevated = (percentile >= elevated_pct).fillna(False).to_numpy()
    return elevated


def make_vix_contrarian_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    vix_lookback: int = 252, elevated_pct: float = 90.0,
    buy_multiplier: float = 2.0, calm_fraction: float = 0.9,
    max_buy_multiple: float = 4.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the VIX/percentile computation
    entirely and buys the full week's cash every week-end day (0
    otherwise), which is bit-for-bit plain DCA."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)
    elevated = compute_elevated(daily, vix_lookback, elevated_pct) if enabled else None

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if elevated[t]:
            target_buy_usd = min(cash, buy_multiplier * weekly_deposit, max_buy_multiple * weekly_deposit)
        else:
            target_buy_usd = calm_fraction * weekly_deposit
        return target_buy_usd, 0.0, {"elevated_fear": bool(elevated[t])}

    return decide


def make_decider_from_elevated_array(
    daily: pd.DataFrame, weekly_deposit: float, elevated: np.ndarray,
    buy_multiplier: float = 2.0, calm_fraction: float = 0.9,
    max_buy_multiple: float = 4.0,
):
    """Same weekly decision rule as make_vix_contrarian_decider, but driven
    by an arbitrary pre-computed `elevated` boolean array -- used by the
    placebo circular-shift robustness test (sec 4.3), which shifts the
    regime's TIMING while keeping its overall elevated/calm frequency
    identical."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)

    def decide(t, cash):
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if elevated[t]:
            target_buy_usd = min(cash, buy_multiplier * weekly_deposit, max_buy_multiple * weekly_deposit)
        else:
            target_buy_usd = calm_fraction * weekly_deposit
        return target_buy_usd, 0.0, {"elevated_fear": bool(elevated[t])}

    return decide


CATEGORY = "Sizing / valuation"

# Grid: vix_lookback x elevated_pct x buy_multiplier x calm_fraction
# = 2x2x3x2 = 24 (<=36 cap; max_buy_multiple fixed at 4.0, not grid-varied)
GRID = {
    "vix_lookback": [252, 504],
    "elevated_pct": [80.0, 90.0],
    "buy_multiplier": [1.5, 2.0, 3.0],
    "calm_fraction": [0.75, 0.9],
}
MAX_BUY_MULTIPLE = 4.0
PRIMARY_CONFIG = {
    "vix_lookback": 252, "elevated_pct": 90.0, "buy_multiplier": 2.0,
    "calm_fraction": 0.9, "max_buy_multiple": MAX_BUY_MULTIPLE,
}


def grid_configs() -> list[dict]:
    out = []
    for lb in GRID["vix_lookback"]:
        for ep in GRID["elevated_pct"]:
            for bm in GRID["buy_multiplier"]:
                for cf in GRID["calm_fraction"]:
                    out.append({
                        "vix_lookback": lb, "elevated_pct": ep,
                        "buy_multiplier": bm, "calm_fraction": cf,
                        "max_buy_multiple": MAX_BUY_MULTIPLE,
                    })
    return out
