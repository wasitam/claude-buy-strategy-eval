"""Family 049: Ulcer Index (drawdown-severity-weighted volatility) sizing
(Martin & McCann 1989).

families/049-ulcer-index-sizing/prereg.md has the full mechanism, rules,
and the required rigorous distinction from families 014/037 (and the brief
distinction from family 003). Summary: for each asset, compute a LOCAL
rolling running peak (`running_max_t`, trailing `ui_window`-day rolling
max, unlike families 014/037's expanding-or-multi-year all-time-high), the
daily percentage drawdown from it (`ddpct_t <= 0`), and the Ulcer Index
`UI_t = sqrt(mean(ddpct_i^2 over the trailing ui_window-day window))` --
the root-mean-square of the daily percentage drawdown, combining BOTH
depth and persistence in a single number. A causal, point-in-time
percentile rank `pctile_t` of `UI_t` within its own trailing
`pctile_lookback`-day history drives a CONTINUOUS sizing multiplier:
    m_t = clip(1 - k * (2 * pctile_t - 1), min_mult, max_mult)
A high UI percentile (elevated -- frequent/deep/persistent drawdowns)
pushes m_t toward min_mult (buy less/bank); a low UI percentile
(depressed -- shallow/brief/absent drawdowns) pushes m_t toward max_mult
(buy more/normal). The order submitted every trading day is
`target_buy_usd = weekly_deposit * m_t`, capped at
`max_lump_multiple * weekly_deposit` and then at available cash (the
engine's own no-leverage cap, sec 3.2) -- never sells, never borrows. A
below-1.0-multiplier week's shortfall banks as cash (earning IRX),
available to fund a later above-1.0-multiplier week -- the same reserve
mechanism families 003/005/014/030/031/035/036/037/040/044 use.

Category: Sizing / valuation.

Parameters (4 tunable, <=5 per sec 3.4):
  ui_window        -- trailing window (days), used for BOTH the local
                       running-peak reference and the RMS averaging window.
  pctile_lookback  -- trailing window (days) for the percentile rank of UI
                       within its own recent history.
  k                -- sensitivity of the multiplier to the percentile rank.
  min_mult         -- lower clip bound on the multiplier.

Fixed constants (not grid-varied): max_mult=2.0, max_lump_multiple=3.0.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MAX_MULT = 2.0
MAX_LUMP_MULTIPLE = 3.0


def compute_ulcer_index(close: np.ndarray, ui_window: int) -> tuple[np.ndarray, np.ndarray]:
    """Causal Ulcer Index: running_max_t is a trailing rolling max over the
    last ui_window days (LOCAL peak, falls back to the expanding max while
    fewer observations exist -- min_periods=1, so the very first day uses a
    window of 1). ddpct_t = 100*(close_t - running_max_t)/running_max_t
    (<=0). UI_t = sqrt(rolling mean of ddpct_i^2 over the same trailing
    ui_window-day window ending at t). Both running_max_t and UI_t depend
    only on close_0..close_t at any t (strictly causal, no lookahead: a
    rolling window that only ever looks backward from t)."""
    s = pd.Series(np.asarray(close, dtype=float))
    running_max = s.rolling(ui_window, min_periods=1).max()
    ddpct = 100.0 * (s - running_max) / running_max
    ui = np.sqrt((ddpct ** 2).rolling(ui_window, min_periods=1).mean())
    return ui.to_numpy(), ddpct.to_numpy()


def compute_percentile_rank(ui: np.ndarray, pctile_lookback: int) -> np.ndarray:
    """Causal, point-in-time rolling percentile rank of UI_t within the
    trailing pctile_lookback window of UI values ending at t (inclusive).
    Never uses a future UI value. Defaults to 0.5 (neutral) until
    pctile_lookback days of valid UI history exist. Same convention as
    families 031/035/036/040/041/042/044."""
    s = pd.Series(ui)

    def _rank_last(window: np.ndarray) -> float:
        w = window[~np.isnan(window)]
        if len(w) == 0 or np.isnan(window[-1]):
            return np.nan
        return float(np.mean(w <= window[-1]))

    pct = s.rolling(pctile_lookback, min_periods=pctile_lookback).apply(_rank_last, raw=True)
    pct = pct.to_numpy()
    pct = np.where(np.isnan(pct), 0.5, pct)
    return pct


def compute_multiplier(
    daily: pd.DataFrame, ui_window: int, pctile_lookback: int, k: float, min_mult: float,
    max_mult: float = MAX_MULT,
    ui_cache: np.ndarray | None = None,
) -> np.ndarray:
    """ui_cache: optionally pass a precomputed compute_ulcer_index(...)[0]
    array (keyed only by (asset, ui_window), shared across every k/
    min_mult/pctile_lookback grid arm that shares the same ui_window) to
    avoid recomputing the rolling RMS once per grid config."""
    ui = ui_cache if ui_cache is not None else compute_ulcer_index(daily["Close"].to_numpy(), ui_window)[0]
    pct = compute_percentile_rank(ui, pctile_lookback)
    m = 1.0 - k * (2.0 * pct - 1.0)
    m = np.clip(m, min_mult, max_mult)
    return m


def make_ulcer_index_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    ui_window: int = 126, pctile_lookback: int = 252, k: float = 1.0, min_mult: float = 0.5,
    max_mult: float = MAX_MULT, max_lump_multiple: float = MAX_LUMP_MULTIPLE,
    enabled: bool = True,
    ui_cache: np.ndarray | None = None,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day, which is
    bit-for-bit plain DCA (used to prove the strategy nests DCA exactly --
    reference point 1 of the two-reference-point pattern; see prereg.md)."""
    if enabled:
        m = compute_multiplier(daily, ui_window, pctile_lookback, k, min_mult, max_mult, ui_cache=ui_cache)
    else:
        m = np.ones(len(daily), dtype=float)

    lump_cap = max_lump_multiple * weekly_deposit

    def decide(t, cash):
        target_buy_usd = weekly_deposit * float(m[t])
        capped_buy_usd = min(target_buy_usd, lump_cap)
        # No sells; the engine's own cash cap (sec 3.2) enforces
        # buy_usd<=cash, so a shortfall on a low-multiplier (elevated-UI)
        # week simply banks as cash (earning IRX) until a later
        # high-multiplier (depressed-UI) week can spend it -- never
        # leverage, never borrowing.
        return capped_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Sizing / valuation"

# Grid: ui_window x pctile_lookback x k x min_mult = 2x2x3x2 = 24 (<=36 cap, 4 tunable params <=5)
GRID = {
    "ui_window": [63, 126],
    "pctile_lookback": [252, 504],
    "k": [0.5, 1.0, 1.5],
    "min_mult": [0.25, 0.5],
}
PRIMARY_CONFIG = {
    "ui_window": 126, "pctile_lookback": 252, "k": 1.0, "min_mult": 0.5,
}


def grid_configs() -> list[dict]:
    out = []
    for uw in GRID["ui_window"]:
        for pl in GRID["pctile_lookback"]:
            for k in GRID["k"]:
                for mm in GRID["min_mult"]:
                    out.append({
                        "ui_window": uw, "pctile_lookback": pl, "k": k, "min_mult": mm,
                    })
    return out


# Import-time assertion (per families 021/030/036/044's lesson): PRIMARY_CONFIG
# must be a genuine member of the declared grid, verified before any module
# using this strategy can even be imported successfully.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of the declared grid"
