"""Family 015: DXY (US Dollar Index) regime rotation.

families/015-dxy-regime/prereg.md has the full mechanism and rules.
Summary: a confirmed US Dollar Index (DX-Y.NYB) uptrend -- close above its
own trailing SMA, held continuously for confirm_days trading days -- marks
a "dollar-strength" regime. Deposits are banked as cash (earning IRX)
during a confirmed dollar-strength regime instead of buying, and deployed
with a capped catch-up lump once the regime reads calm. Same banking/
cash-cap mechanic as families 004/006/007/010/011. No sells, ever.

Category: Regime switch (macro / credit / sentiment).

Parameters (4 tunable + 1 fixed, all <=5):
  dxy_lookback     -- SMA window (trading days) for the DXY trend reference
  confirm_days     -- consecutive trading days raw_strong must hold before
                       the confirmed regime actually flips state
  threshold_pct    -- % buffer above the SMA required for raw_strong
  bank_fraction    -- fraction of deposit still bought while confirmed-strong
  max_lump_multiple -- fixed at 6.0 (not grid-varied), catch-up cap
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import data as v3data

DXY_TICKER = "DX-Y.NYB"


def _aligned_dxy_close(daily_index: pd.DatetimeIndex) -> pd.Series:
    """DXY close, forward-filled causally onto the asset's own trading-day
    index (the DXY trades on its own calendar, e.g. closed some days BTC
    trades). Never fills backward."""
    dxy = v3data.fetch_yf_macro(DXY_TICKER)
    unioned = dxy.reindex(dxy.index.union(daily_index)).sort_index().ffill()
    return unioned.reindex(daily_index).ffill()


def compute_confirmed(daily: pd.DataFrame, dxy_lookback: int, confirm_days: int,
                       threshold_pct: float) -> np.ndarray:
    """Boolean array, True = confirmed dollar-strength regime, aligned to
    daily.index. Causal only: SMA_t and raw_strong_t use only DXY closes
    through t. Before enough DXY history exists for the SMA, raw_strong
    defaults to False (calm/DCA-like), matching family 001/011's warm-up
    convention. Confirmation uses the same discrete state-machine pattern
    as trend_exit.compute_signal, starting in the calm (False) state."""
    dxy_close = _aligned_dxy_close(daily.index)
    sma = dxy_close.rolling(dxy_lookback, min_periods=dxy_lookback).mean()
    raw_strong = dxy_close > sma * (1.0 + threshold_pct / 100.0)
    raw_strong = raw_strong.fillna(False).to_numpy()

    n = len(raw_strong)
    if confirm_days <= 0:
        return raw_strong

    state = np.zeros(n, dtype=bool)  # start calm
    run = 0
    cur = False
    for t in range(n):
        if raw_strong[t] == cur:
            run = 0
        else:
            run += 1
            if run >= confirm_days:
                cur = raw_strong[t]
                run = 0
        state[t] = cur
    return state


def make_dxy_regime_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    dxy_lookback: int = 200, confirm_days: int = 10, threshold_pct: float = 0.0,
    bank_fraction: float = 0.0, max_lump_multiple: float = 6.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the DXY/SMA/confirmation computation
    entirely and buys the full week's cash every week-end day (0
    otherwise), which is bit-for-bit plain DCA."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)
    confirmed = (
        compute_confirmed(daily, dxy_lookback, confirm_days, threshold_pct)
        if enabled else None
    )

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if confirmed[t]:
            target_buy_usd = bank_fraction * weekly_deposit
        else:
            target_buy_usd = min(cash, max_lump_multiple * weekly_deposit)
        return target_buy_usd, 0.0, {"confirmed_strong": bool(confirmed[t])}

    return decide


def make_decider_from_confirmed_array(
    daily: pd.DataFrame, weekly_deposit: float, confirmed: np.ndarray,
    bank_fraction: float = 0.0, max_lump_multiple: float = 6.0,
):
    """Same banking/lump decision rule as make_dxy_regime_decider, but
    driven by an arbitrary pre-computed `confirmed` boolean array -- used
    by the placebo circular-shift robustness test (sec 4.3), which shifts
    the regime's TIMING while keeping its overall confirmed/calm
    frequency identical."""
    from .. import engine as eng
    is_week_end = eng.week_end_flags(daily.index)

    def decide(t, cash):
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if confirmed[t]:
            target_buy_usd = bank_fraction * weekly_deposit
        else:
            target_buy_usd = min(cash, max_lump_multiple * weekly_deposit)
        return target_buy_usd, 0.0, {"confirmed_strong": bool(confirmed[t])}

    return decide


CATEGORY = "Regime switch (macro / credit / sentiment)"

# Grid: dxy_lookback x confirm_days x threshold_pct x bank_fraction
# = 2x2x2x2 = 16 (<=36 cap; max_lump_multiple fixed at 6, not grid-varied)
GRID = {
    "dxy_lookback": [100, 200],
    "confirm_days": [5, 10],
    "threshold_pct": [0.0, 1.0],
    "bank_fraction": [0.0, 0.25],
}
MAX_LUMP_MULTIPLE = 6.0
PRIMARY_CONFIG = {
    "dxy_lookback": 200, "confirm_days": 10, "threshold_pct": 0.0,
    "bank_fraction": 0.0, "max_lump_multiple": MAX_LUMP_MULTIPLE,
}


def grid_configs() -> list[dict]:
    out = []
    for lb in GRID["dxy_lookback"]:
        for cd in GRID["confirm_days"]:
            for th in GRID["threshold_pct"]:
                for bf in GRID["bank_fraction"]:
                    out.append({
                        "dxy_lookback": lb, "confirm_days": cd,
                        "threshold_pct": th, "bank_fraction": bf,
                        "max_lump_multiple": MAX_LUMP_MULTIPLE,
                    })
    return out
