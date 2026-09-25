"""Family 025: Variance risk premium (VRP) sizing (Bekaert & Hoerova 2014;
Carr & Wu 2009).

families/025-vrp-sizing/prereg.md has the full mechanism and rules.
Summary: VRP_t = IV_t - RV_t, where IV_t is the CBOE VIX close (a shared,
cross-market S&P-500-option-implied vol proxy, same as family 016) and
RV_t is EACH ASSET'S OWN trailing realized volatility (the same rolling
log-return-stdev calculation family 003 uses, re-expressed in vol-point
units comparable to VIX). This is deliberately a SPREAD, not either leg
alone: family 003 uses RV_t alone (inverse sign); family 016 uses IV_t
alone (direct sign, no realized-vol comparison). This family ranks the
SPREAD itself in its own trailing percentile and buys MORE when the
spread is elevated (implied running well above realized -- a rich
variance risk premium), buys LESS when the spread is compressed (realized
has caught up with or exceeded implied), and buys a fixed calm fraction
otherwise. No sells, ever; no leverage; cash never goes negative.

Category: Volatility targeting.

Parameters (4 tunable + fixed constants, <=5 tunable):
  rv_lookback     -- trailing window (trading days) for the asset's own
                      realized-vol leg
  elevated_pct    -- percentile threshold on the VRP SPREAD for "elevated"
  compressed_pct  -- percentile threshold on the VRP SPREAD for "compressed"
  buy_multiplier  -- multiple of weekly_deposit bought when elevated

Fixed (not grid-varied): vrp_lookback=252 (trailing window for the spread's
own percentile rank), max_buy_multiple=4.0, compressed_fraction=0.5,
calm_fraction=0.9.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import data as v3data

VIX_TICKER = "^VIX"
TRADING_DAYS_PER_YEAR = 252.0

VRP_LOOKBACK = 252
MAX_BUY_MULTIPLE = 4.0
COMPRESSED_FRACTION = 0.5
CALM_FRACTION = 0.9


def _aligned_vix_close(daily_index: pd.DatetimeIndex) -> pd.Series:
    """VIX close, forward-filled causally onto the asset's own trading-day
    index. Never fills backward. Identical alignment method to family
    016's _aligned_vix_close()."""
    vix = v3data.fetch_yf_macro(VIX_TICKER)
    unioned = vix.reindex(vix.index.union(daily_index)).sort_index().ffill()
    return unioned.reindex(daily_index).ffill()


def _realized_vol_pct(daily: pd.DataFrame, rv_lookback: int) -> pd.Series:
    """Trailing realized annualized volatility, in VIX-comparable
    percentage-point units (e.g. 20.0 means 20% annualized). Same rolling
    log-return-stdev calculation as family 003's compute_multiplier(),
    re-expressed as sigma*100 instead of a raw decimal ratio."""
    close = daily["Close"].to_numpy()
    log_ret = np.diff(np.log(close), prepend=np.log(close[0]))
    log_ret[0] = 0.0
    ret_s = pd.Series(log_ret, index=daily.index)
    rv = ret_s.rolling(rv_lookback, min_periods=rv_lookback).std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR) * 100.0
    return rv


def compute_vrp(daily: pd.DataFrame, rv_lookback: int) -> pd.Series:
    """VRP_t = IV_t - RV_t, causal, aligned to daily.index. NaN until both
    legs are available."""
    iv = _aligned_vix_close(daily.index)
    rv = _realized_vol_pct(daily, rv_lookback)
    return iv - rv


def compute_regime_flags(
    daily: pd.DataFrame, rv_lookback: int, vrp_lookback: int,
    elevated_pct: float, compressed_pct: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Returns (elevated, compressed) boolean arrays aligned to daily.index.
    Causal only: percentile_t is the trailing percentile rank of VRP_t
    within the trailing vrp_lookback window of the VRP SERIES ITSELF (not
    of IV_t alone, not of RV_t alone). Before enough history exists
    (warm-up, or pre-1990 VIX unavailability for any asset), both flags
    default to False (the normal/calm-fraction regime)."""
    vrp = compute_vrp(daily, rv_lookback)

    def _pctile_rank(window: np.ndarray) -> float:
        return float((window <= window[-1]).mean() * 100.0)

    percentile = vrp.rolling(vrp_lookback, min_periods=vrp_lookback).apply(_pctile_rank, raw=True)
    elevated = (percentile >= elevated_pct).fillna(False).to_numpy()
    compressed = (percentile <= compressed_pct).fillna(False).to_numpy()
    return elevated, compressed


def make_vrp_sizing_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    rv_lookback: int = 60, vrp_lookback: int = VRP_LOOKBACK,
    elevated_pct: float = 90.0, compressed_pct: float = 10.0,
    buy_multiplier: float = 2.0, max_buy_multiple: float = MAX_BUY_MULTIPLE,
    compressed_fraction: float = COMPRESSED_FRACTION, calm_fraction: float = CALM_FRACTION,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the VRP computation entirely and
    buys the full week's cash every week-end day (0 otherwise), which is
    bit-for-bit plain DCA."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)
    if enabled:
        elevated, compressed = compute_regime_flags(daily, rv_lookback, vrp_lookback, elevated_pct, compressed_pct)
    else:
        elevated = compressed = None

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if elevated[t]:
            target_buy_usd = min(cash, buy_multiplier * weekly_deposit, max_buy_multiple * weekly_deposit)
            regime = "elevated"
        elif compressed[t]:
            target_buy_usd = compressed_fraction * weekly_deposit
            regime = "compressed"
        else:
            target_buy_usd = calm_fraction * weekly_deposit
            regime = "normal"
        return target_buy_usd, 0.0, {"vrp_regime": regime}

    return decide


def make_decider_from_flags(
    daily: pd.DataFrame, weekly_deposit: float, elevated: np.ndarray, compressed: np.ndarray,
    buy_multiplier: float = 2.0, max_buy_multiple: float = MAX_BUY_MULTIPLE,
    compressed_fraction: float = COMPRESSED_FRACTION, calm_fraction: float = CALM_FRACTION,
):
    """Same weekly decision rule as make_vrp_sizing_decider, but driven by
    arbitrary pre-computed elevated/compressed boolean arrays -- used by
    the placebo circular-shift robustness test (sec 4.3), which shifts the
    regime's TIMING while keeping its overall frequency identical."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)

    def decide(t, cash):
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if elevated[t]:
            target_buy_usd = min(cash, buy_multiplier * weekly_deposit, max_buy_multiple * weekly_deposit)
        elif compressed[t]:
            target_buy_usd = compressed_fraction * weekly_deposit
        else:
            target_buy_usd = calm_fraction * weekly_deposit
        return target_buy_usd, 0.0, {}

    return decide


CATEGORY = "Volatility targeting"

# Grid: rv_lookback x elevated_pct x compressed_pct x buy_multiplier
# = 3x2x2x3 = 36 (<=36 cap; vrp_lookback/max_buy_multiple/compressed_fraction/
# calm_fraction fixed, not grid-varied)
GRID = {
    "rv_lookback": [20, 60, 120],
    "elevated_pct": [80.0, 90.0],
    "compressed_pct": [10.0, 20.0],
    "buy_multiplier": [1.5, 2.0, 3.0],
}
PRIMARY_CONFIG = {
    "rv_lookback": 60, "elevated_pct": 90.0, "compressed_pct": 10.0, "buy_multiplier": 2.0,
}


def grid_configs() -> list[dict]:
    out = []
    for rv in GRID["rv_lookback"]:
        for ep in GRID["elevated_pct"]:
            for cp in GRID["compressed_pct"]:
                for bm in GRID["buy_multiplier"]:
                    out.append({
                        "rv_lookback": rv, "elevated_pct": ep,
                        "compressed_pct": cp, "buy_multiplier": bm,
                    })
    return out


# Primary-config-in-grid verification, per family 021's lesson (sec 4.4
# "primary configuration must be a genuine grid member" requirement,
# checked at import time so a mismatch is caught before any backtest runs).
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of the declared grid"
