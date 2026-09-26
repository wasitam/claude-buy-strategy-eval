"""Family 042: Realized-volatility term-structure (short-vs-long trailing-
window ratio) sizing (Christensen & Prabhala 1998; Bollerslev et al. 2018).

families/042-realvol-term-structure/prereg.md has the full mechanism and
rules. Summary: for each asset, compute its OWN realized volatility (close-
to-close log returns) over a SHORT trailing window and a LONGER trailing
window:

    ratio_t = sigma_long_t / sigma_short_t

`ratio_t > 1` means short-window ("now") realized vol sits BELOW the
asset's own longer-run ("normal") realized vol -- a "calm now relative to
its own recent-past normal" regime. `ratio_t < 1` means short-window vol
is elevated relative to the long-run reference. Unlike family 003 (which
clips this same kind of raw ratio directly against fixed absolute bounds),
this family takes a further, causal, point-in-time PERCENTILE RANK of
`ratio_t` within its own trailing history first, and maps THAT percentile
to a continuous sizing multiplier (identical functional form to families
030/031/036/039/040/041's percentile-to-multiplier construction):

    pctile_t = trailing percentile rank of ratio_t within its own history
    m_t = clip(1 + k * (2 * pctile_t - 1), min_mult, max_mult)

This makes "unusually calm" adaptive to each asset's OWN historical range
of ratio values (e.g. an asset whose ratio typically swings 0.5-3 needs a
much more extreme raw ratio to register as "unusually calm" than an asset
whose ratio typically sits in a tight 0.8-1.3 band) -- see prereg.md's
"Rigorous distinction from family 003" section for the concrete numeric
divergence check. Never a sell; never leverage; cash never goes negative
(engine's own cap, sec 3.2).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LONG_WINDOW = 252  # fixed, not grid-varied (the standard trailing-year reference)
MAX_MULT_FIXED = 2.0  # fixed, not grid-varied
MAX_LUMP_MULTIPLE = 3.0


def compute_realized_vol(daily: pd.DataFrame, window: int) -> pd.Series:
    """Annualized close-to-close realized volatility, trailing `window`
    trading days, causal (uses only data through t). Identical estimator
    to family 003's sigma_recent_t/sigma_ref_t (std of daily log returns,
    ddof=1, annualized by sqrt(252))."""
    log_ret = np.log(daily["Close"]).diff()
    return log_ret.rolling(window, min_periods=window).std(ddof=1) * np.sqrt(252.0)


def compute_ratio(daily: pd.DataFrame, short_window: int, long_window: int = LONG_WINDOW) -> pd.Series:
    """ratio_t = sigma_long_t / sigma_short_t. NaN until both windows are
    full. Elevated (>1) = short-window vol LOW relative to the asset's own
    longer-run reference ("calm now vs. own recent-past normal")."""
    sigma_short = compute_realized_vol(daily, short_window)
    sigma_long = compute_realized_vol(daily, long_window)
    ratio = sigma_long / sigma_short.replace(0.0, np.nan)
    return ratio


def compute_percentile_rank(ratio: pd.Series, ts_lookback: int) -> np.ndarray:
    """Causal, point-in-time rolling percentile rank of ratio_t within the
    trailing ts_lookback window of past ratio values ending at t
    (inclusive). Defaults to 0.5 (neutral) until ts_lookback days of valid
    ratio history exist. Identical construction to families 036/039/040/
    041's compute_percentile_rank."""

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
    daily: pd.DataFrame, short_window: int, ts_lookback: int, k: float, min_mult: float,
    max_mult: float = MAX_MULT_FIXED, long_window: int = LONG_WINDOW,
) -> np.ndarray:
    ratio = compute_ratio(daily, short_window, long_window)
    pct = compute_percentile_rank(ratio, ts_lookback)
    m = 1.0 + k * (2.0 * pct - 1.0)
    m = np.clip(m, min_mult, max_mult)
    return m


def make_realvol_term_structure_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    short_window: int = 20, ts_lookback: int = 252, k: float = 1.0, min_mult: float = 0.5,
    max_mult: float = MAX_MULT_FIXED, long_window: int = LONG_WINDOW,
    max_lump_multiple: float = MAX_LUMP_MULTIPLE,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day, which is
    bit-for-bit plain DCA (used to prove the strategy nests DCA exactly).

    No-leverage clarification (research-loop-plan-v3.md sec 3.4 / sec 2's
    "no leverage" rule, families 030/031/036/039/040/041's own precedent):
    every buy here is capped at (a) a fixed multiple of the weekly deposit
    (`max_lump_multiple`, a hard ceiling regardless of banked cash) and
    (b) the engine's own unconditional cash cap (`buy_usd <= cash`,
    `engine.py` sec 3.2), so the strategy can never spend more than it has
    banked from actual past deposits plus earned interest -- no borrowing,
    no negative cash, ever.
    """
    if enabled:
        m = compute_multiplier(daily, short_window, ts_lookback, k, min_mult, max_mult, long_window)
    else:
        m = np.ones(len(daily), dtype=float)

    lump_cap = max_lump_multiple * weekly_deposit

    def decide(t, cash):
        target_buy_usd = weekly_deposit * float(m[t])
        capped_buy_usd = min(target_buy_usd, lump_cap)
        # No sells; the engine's own cash cap (sec 3.2) enforces
        # buy_usd<=cash, so a shortfall on a low-multiplier (elevated-
        # short-vs-long-vol-percentile) week simply banks as cash (earning
        # IRX) until a later high-multiplier (calm-relative-to-own-normal
        # percentile) week can spend it -- never leverage, never borrowing.
        return capped_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Volatility targeting"

# Grid: short_window x ts_lookback x k x min_mult = 3x2x3x2 = 36 (at the sec 3.4 cap)
GRID = {
    "short_window": [10, 15, 20],
    "ts_lookback": [126, 252],
    "k": [0.5, 1.0, 1.5],
    "min_mult": [0.25, 0.5],
}
PRIMARY_CONFIG = {
    "short_window": 20, "ts_lookback": 252, "k": 1.0, "min_mult": 0.5,
}


def grid_configs() -> list[dict]:
    out = []
    for sw in GRID["short_window"]:
        for tl in GRID["ts_lookback"]:
            for k in GRID["k"]:
                for mn in GRID["min_mult"]:
                    out.append({"short_window": sw, "ts_lookback": tl, "k": k, "min_mult": mn})
    return out


# Import-time assertion (per family 021's lesson): PRIMARY_CONFIG must be a
# genuine member of the declared grid.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of the declared grid"

# Import-time assertion (families 014/033/037/039/040/041's now-6x-confirmed
# lesson): every grid cell's min_mult must be strictly below 1.0, or the
# engine's no-leverage cash cap silently nullifies the reserve-banking arm.
for _mm in GRID["min_mult"]:
    assert _mm < 1.0, f"min_mult={_mm!r} must be < 1.0 (families 014/033/037/039/040/041 lesson)"

# Short window must always be strictly shorter than the fixed long window,
# or the ratio's sign convention (calm-now vs. own-normal) is not meaningful.
for _sw in GRID["short_window"]:
    assert _sw < LONG_WINDOW, f"short_window={_sw!r} must be < LONG_WINDOW={LONG_WINDOW!r}"

assert len(grid_configs()) <= 36, "grid exceeds sec 3.4's 36-configuration cap"
