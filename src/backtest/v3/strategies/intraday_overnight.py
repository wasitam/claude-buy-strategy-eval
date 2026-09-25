"""Family 026: Intraday/overnight return decomposition sizing
(Lou, Polk & Skouras 2019, "A Tug of War").

families/026-intraday-overnight/prereg.md has the full mechanism and
rules. Summary: each trading day's total return splits into an intraday
(open-to-close) leg and an overnight (close-to-open) leg. LPS document
that the overnight leg shows continuation/persistence while the intraday
leg is noisier and more reversal-prone. This family sizes buys on the
SPREAD between the trailing cumulative overnight leg and the trailing
cumulative intraday leg (an "overnight dominance" indicator), ranked in
its own trailing percentile: elevated spread (overnight has been
dominating the asset's recent cumulative return) -> buy MORE (a momentum/
continuation bet on the persistent overnight component); compressed
spread (intraday dominating, or overnight negative) -> buy LESS. Both
trailing sums are LAGGED (computed on the leg series shifted forward one
day before the rolling window), so day t's own O/C split never enters its
own signal -- see prereg.md's "No-lookahead design" section. No sells,
ever; no leverage; cash never goes negative.

Category: Sizing / valuation.

Parameters (4 tunable, <=5):
  lookback_days   -- trailing window (COMPLETE lagged trading days) for
                      both cumulative legs
  elevated_pct    -- percentile threshold on the spread for "elevated"
  compressed_pct  -- percentile threshold on the spread for "compressed"
  buy_multiplier  -- multiple of weekly_deposit bought when elevated

Fixed (not grid-varied): pctile_lookback=252 (trailing window for the
spread's own percentile rank), max_buy_multiple=4.0, compressed_fraction=
0.5, calm_fraction=0.9.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PCTILE_LOOKBACK = 252
MAX_BUY_MULTIPLE = 4.0
COMPRESSED_FRACTION = 0.5
CALM_FRACTION = 0.9


def compute_legs(daily: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Returns (intraday, overnight) daily leg return series, aligned to
    daily.index. intraday_t = Close_t/Open_t - 1. overnight_t =
    Open_t/Close_{t-1} - 1 (NaN on the first trading day, no prior close).
    """
    open_ = daily["Open"]
    close = daily["Close"]
    intraday = close / open_ - 1.0
    overnight = open_ / close.shift(1) - 1.0
    return intraday, overnight


def compute_spread(daily: pd.DataFrame, lookback_days: int) -> pd.Series:
    """spread_t = cum_overnight_t - cum_intraday_t, where BOTH trailing
    sums are computed on the leg series SHIFTED FORWARD BY ONE DAY before
    the rolling window is applied -- so spread_t uses only complete days
    t-lookback_days .. t-1, never day t's own intraday_t/overnight_t.
    Causal, no-lookahead by construction (see prereg.md)."""
    intraday, overnight = compute_legs(daily)
    cum_overnight = overnight.shift(1).rolling(lookback_days, min_periods=lookback_days).sum()
    cum_intraday = intraday.shift(1).rolling(lookback_days, min_periods=lookback_days).sum()
    return cum_overnight - cum_intraday


def compute_regime_flags(
    daily: pd.DataFrame, lookback_days: int, pctile_lookback: int,
    elevated_pct: float, compressed_pct: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Returns (elevated, compressed) boolean arrays aligned to daily.index.
    percentile_t is the trailing percentile rank of spread_t (itself
    already lagged) within the trailing pctile_lookback window of the
    spread SERIES ITSELF. Before enough history exists (warm-up), both
    flags default to False (the normal/calm-fraction regime)."""
    spread = compute_spread(daily, lookback_days)

    def _pctile_rank(window: np.ndarray) -> float:
        return float((window <= window[-1]).mean() * 100.0)

    percentile = spread.rolling(pctile_lookback, min_periods=pctile_lookback).apply(_pctile_rank, raw=True)
    elevated = (percentile >= elevated_pct).fillna(False).to_numpy()
    compressed = (percentile <= compressed_pct).fillna(False).to_numpy()
    return elevated, compressed


def make_intraday_overnight_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    lookback_days: int = 20, pctile_lookback: int = PCTILE_LOOKBACK,
    elevated_pct: float = 90.0, compressed_pct: float = 10.0,
    buy_multiplier: float = 2.0, max_buy_multiple: float = MAX_BUY_MULTIPLE,
    compressed_fraction: float = COMPRESSED_FRACTION, calm_fraction: float = CALM_FRACTION,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the decomposition computation
    entirely and buys the full week's cash every week-end day (0
    otherwise), which is bit-for-bit plain DCA."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)
    if enabled:
        elevated, compressed = compute_regime_flags(daily, lookback_days, pctile_lookback, elevated_pct, compressed_pct)
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
        return target_buy_usd, 0.0, {"io_regime": regime}

    return decide


def make_decider_from_flags(
    daily: pd.DataFrame, weekly_deposit: float, elevated: np.ndarray, compressed: np.ndarray,
    buy_multiplier: float = 2.0, max_buy_multiple: float = MAX_BUY_MULTIPLE,
    compressed_fraction: float = COMPRESSED_FRACTION, calm_fraction: float = CALM_FRACTION,
):
    """Same weekly decision rule as make_intraday_overnight_decider, but
    driven by arbitrary pre-computed elevated/compressed boolean arrays --
    used by the placebo circular-shift robustness test (sec 4.3), which
    shifts the regime's TIMING while keeping its overall frequency
    identical."""
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


CATEGORY = "Sizing / valuation"

# Grid: lookback_days x elevated_pct x compressed_pct x buy_multiplier
# = 3x2x2x3 = 36 (<=36 cap; pctile_lookback/max_buy_multiple/
# compressed_fraction/calm_fraction fixed, not grid-varied)
GRID = {
    "lookback_days": [10, 20, 40],
    "elevated_pct": [80.0, 90.0],
    "compressed_pct": [10.0, 20.0],
    "buy_multiplier": [1.5, 2.0, 3.0],
}
PRIMARY_CONFIG = {
    "lookback_days": 20, "elevated_pct": 90.0, "compressed_pct": 10.0, "buy_multiplier": 2.0,
}


def grid_configs() -> list[dict]:
    out = []
    for lb in GRID["lookback_days"]:
        for ep in GRID["elevated_pct"]:
            for cp in GRID["compressed_pct"]:
                for bm in GRID["buy_multiplier"]:
                    out.append({
                        "lookback_days": lb, "elevated_pct": ep,
                        "compressed_pct": cp, "buy_multiplier": bm,
                    })
    return out


# Primary-config-in-grid verification, per family 021's lesson (sec 4.4
# "primary configuration must be a genuine grid member" requirement,
# checked at import time so a mismatch is caught before any backtest runs).
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of the declared grid"
