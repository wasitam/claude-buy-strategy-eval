"""Family 045: Cross-asset average-correlation regime sizing (Longin &
Solnik 2001; Ang & Bekaert 2002).

families/045-avg-correlation-regime/prereg.md has the full mechanism and
rules. Summary: for each core asset `a`, compute the trailing average of
`a`'s pairwise return correlation against each of the OTHER 4 core assets
(a causal, cross-asset systemic-co-movement proxy computed purely from
already-loaded price data -- no external data), then a causal,
point-in-time percentile rank of that average within its own trailing
history, converted to a CONTINUOUS buy multiplier (never a discrete
ladder, per the established cash-cap-nullification lesson):

    m_t = clip(1 - k * (2 * pctile_t - 1), min_mult, max_mult)

Note the SIGN: this is the sign-inverse of every other continuous-
percentile family in this loop -- a LOW avg-correlation percentile
(diversification-rich regime) pushes m_t ABOVE 1 (buy more); a HIGH
avg-correlation percentile (systemic-stress, "correlations go to 1"
regime) pushes m_t BELOW 1 (buy less/bank a reserve).

Hybrid design (documented at length in prereg.md): cross-asset INPUT
(the signal is mathematically undefined from asset `a`'s own price
series alone), single-asset OUTPUT (each asset's own, separate weekly
buy is sized independently; no dollar ever moves between assets) -- the
mirror image of family 043's cross-asset-rotation OUTPUT.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MAX_MULT = 2.0
MAX_LUMP_MULTIPLE = 3.0
MIN_VALID_LEGS = 2  # avg_corr undefined unless >=2 of the other 4 assets have started trading


def _log_return(close: np.ndarray) -> np.ndarray:
    r = np.diff(np.log(close), prepend=np.log(close[0]))
    r[0] = 0.0
    return r


def _causal_forward_fill_close(other_close: pd.Series, target_index: pd.DatetimeIndex) -> pd.Series:
    """Aligns another asset's Close series onto `target_index` via a
    forward-fill-only reindex -- never backward-filled, so a day strictly
    before `other_close`'s own first real observation stays NaN (identical
    technique to families 016/025/041's _aligned_close() for an external
    macro series, applied here to another core asset's own price series
    instead)."""
    unioned = other_close.reindex(other_close.index.union(target_index)).sort_index().ffill()
    return unioned.reindex(target_index).ffill()


def compute_avg_pairwise_corr(
    asset_name: str, daily: pd.DataFrame, other_assets: dict[str, pd.DataFrame], corr_window: int,
) -> np.ndarray:
    """avg_corr_t^a: the causal, point-in-time trailing average of asset
    `asset_name`'s pairwise return correlation against each of the OTHER
    assets present in `other_assets` (keys other than asset_name are used;
    asset_name itself, if present as a key, is skipped). NaN wherever fewer
    than MIN_VALID_LEGS of the (up to 4) pairwise correlations are defined
    that day (see prereg.md's "BTC's shorter history" section: before
    2000ish only SP500 exists -- 0 legs; 2000-2014 GOLD/SILVER/OIL exist
    but not BTC -- up to 3 legs; 2014+ all 4 legs)."""
    idx = daily.index
    own_ret = _log_return(daily["Close"].to_numpy(dtype=float))
    own_s = pd.Series(own_ret, index=idx)

    pairwise = []
    for other_name, other_df in other_assets.items():
        if other_name == asset_name:
            continue
        aligned_close = _causal_forward_fill_close(other_df["Close"], idx)
        valid = aligned_close.notna().to_numpy()
        safe_close = np.where(valid, aligned_close.to_numpy(dtype=float), 1.0)
        aligned_ret = _log_return(safe_close)
        aligned_ret = np.where(valid, aligned_ret, np.nan)
        other_s = pd.Series(aligned_ret, index=idx)
        roll_corr = own_s.rolling(corr_window, min_periods=corr_window).corr(other_s)
        pairwise.append(roll_corr)

    if not pairwise:
        return np.full(len(idx), np.nan)

    stacked = pd.concat(pairwise, axis=1)
    n_valid = stacked.notna().sum(axis=1).to_numpy()
    avg_corr = stacked.mean(axis=1, skipna=True).to_numpy()
    avg_corr = np.where(n_valid >= MIN_VALID_LEGS, avg_corr, np.nan)
    return avg_corr


def compute_percentile_rank(avg_corr: np.ndarray, pctile_lookback: int) -> np.ndarray:
    """Causal, point-in-time rolling percentile rank of avg_corr_t within
    the trailing pctile_lookback window of past avg_corr values ending at
    t (inclusive). Defaults to 0.5 (neutral -- no tilt) until
    pctile_lookback days of valid avg_corr history exist, or whenever
    avg_corr_t itself is undefined (the ">=2 valid legs" fallback above).
    Identical construction to families 025/031/035/036/039/040/041/044."""
    s = pd.Series(avg_corr)

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
    asset_name: str, daily: pd.DataFrame, other_assets: dict[str, pd.DataFrame],
    corr_window: int, pctile_lookback: int, k: float, min_mult: float,
    max_mult: float = MAX_MULT,
    corr_cache: np.ndarray | None = None,
) -> np.ndarray:
    """corr_cache: optionally pass a precomputed compute_avg_pairwise_corr(...)
    array (keyed only by (asset_name, corr_window), shared across every k/
    min_mult/pctile_lookback grid arm that shares the same corr_window) to
    avoid recomputing the rolling cross-asset correlation once per grid
    config -- see scripts/v3/run_045_avg_correlation_regime.py's cache."""
    avg_corr = corr_cache if corr_cache is not None else compute_avg_pairwise_corr(
        asset_name, daily, other_assets, corr_window
    )
    pct = compute_percentile_rank(avg_corr, pctile_lookback)
    # Sign inverted relative to every other continuous-percentile family in
    # this loop (see module docstring / prereg.md rule 6): LOW avg-corr
    # percentile -> m_t ABOVE 1 (buy more, diversification-rich regime);
    # HIGH avg-corr percentile -> m_t BELOW 1 (buy less, systemic-stress
    # regime).
    m = 1.0 - k * (2.0 * pct - 1.0)
    m = np.clip(m, min_mult, max_mult)
    return m


def make_avg_correlation_regime_decider(
    asset_name: str, daily: pd.DataFrame, other_assets: dict[str, pd.DataFrame],
    weekly_deposit: float,
    corr_window: int = 126, pctile_lookback: int = 252, k: float = 1.0, min_mult: float = 0.5,
    max_mult: float = MAX_MULT, max_lump_multiple: float = MAX_LUMP_MULTIPLE,
    enabled: bool = True,
    corr_cache: np.ndarray | None = None,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day, which is
    bit-for-bit plain DCA (used to prove the strategy nests DCA exactly).

    Explicit no-leverage clarification (research-loop-plan-v3.md sec 3.4 /
    sec 2's "no leverage" rule, every prior continuous-sizing family's
    precedent): every buy here is capped at (a) a fixed multiple of the
    weekly deposit (`max_lump_multiple`, a hard ceiling regardless of
    banked cash) and (b) the engine's own unconditional cash cap
    (`buy_usd <= cash`, `engine.py` sec 3.2), so the strategy can never
    spend more than it has banked from actual past deposits plus earned
    interest -- no borrowing, no negative cash, ever. No dollar is ever
    moved from another asset's ledger (single-asset OUTPUT, per prereg.md's
    hybrid-design distinction from family 043): `other_assets` is used only
    to READ the other assets' own price history for the signal, never to
    fund this asset's buy.
    """
    if enabled:
        m = compute_multiplier(
            asset_name, daily, other_assets, corr_window, pctile_lookback, k, min_mult, max_mult,
            corr_cache=corr_cache,
        )
    else:
        m = np.ones(len(daily), dtype=float)

    lump_cap = max_lump_multiple * weekly_deposit

    def decide(t, cash):
        target_buy_usd = weekly_deposit * float(m[t])
        capped_buy_usd = min(target_buy_usd, lump_cap)
        # No sells; the engine's own cash cap (sec 3.2) enforces
        # buy_usd<=cash, so a shortfall on a low-multiplier (high-avg-corr,
        # systemic-stress-percentile) week simply banks as cash (earning
        # IRX) until a later high-multiplier (low-avg-corr,
        # diversification-rich-percentile) week can spend it -- never
        # leverage, never borrowing.
        return capped_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Regime switch (macro / credit / sentiment)"

# Grid: corr_window x pctile_lookback x k x min_mult = 3x2x3x2 = 36 (at the sec 3.4 cap, 4 tunable params <=5)
GRID = {
    "corr_window": [60, 90, 126],
    "pctile_lookback": [252, 504],
    "k": [0.5, 1.0, 1.5],
    "min_mult": [0.25, 0.5],
}
PRIMARY_CONFIG = {
    "corr_window": 126, "pctile_lookback": 252, "k": 1.0, "min_mult": 0.5,
}


def grid_configs() -> list[dict]:
    out = []
    for cw in GRID["corr_window"]:
        for pl in GRID["pctile_lookback"]:
            for k in GRID["k"]:
                for mm in GRID["min_mult"]:
                    out.append({"corr_window": cw, "pctile_lookback": pl, "k": k, "min_mult": mm})
    return out


# Import-time assertion (family 021's lesson): PRIMARY_CONFIG must be a
# genuine member of the declared grid.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of the declared grid"

# Import-time assertion (families 014/033/037/039/040/041/044's now-6x-
# confirmed lesson): every grid cell's min_mult must be strictly below 1.0,
# or the engine's no-leverage cash cap silently nullifies the reserve-
# banking arm.
for _mm in GRID["min_mult"]:
    assert _mm < 1.0, f"min_mult={_mm!r} must be < 1.0 (families 014/033/037/039/040/041/044 lesson)"

assert len(grid_configs()) <= 36, "grid exceeds sec 3.4's 36-configuration cap"
