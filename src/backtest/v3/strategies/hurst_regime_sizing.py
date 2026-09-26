"""Family 044: Hurst-exponent (fractal trend-persistence) regime sizing
(Mandelbrot & Van Ness 1968; Peters 1994).

families/044-hurst-regime-sizing/prereg.md has the full mechanism and
rules. Summary: each trading day, estimate the asset's own trailing Hurst
exponent `H_t` via classical rescaled-range (R/S) analysis over a trailing
`hurst_window`-day window of daily log returns, using several sub-window
aggregation SCALES within that window simultaneously (not a single lag),
then a causal, point-in-time percentile rank `pctile_t` of `H_t` within its
own trailing `pctile_lookback` window. The sizing multiplier scales
CONTINUOUSLY with that percentile rank (identical functional form to
families 031/036/040's continuous percentile-driven multiplier, avoiding
the discrete-ladder cash-cap-nullification bug families 033/034 hit):
    m_t = clip(1 + k * (2 * pctile_t - 1), min_mult, max_mult)
A high H percentile (elevated, H>0.5-leaning -- trending/persistent regime,
long-range positive dependence across MULTIPLE scales) pushes m_t above 1
(buy more); a low H percentile (depressed, H<0.5-leaning --
mean-reverting/anti-persistent regime) pushes m_t below 1 (buy less/bank).
The order submitted every trading day is
`target_buy_usd = weekly_deposit * m_t`, capped at
`max_lump_multiple * weekly_deposit` and then at available cash (the
engine's own no-leverage cap, sec 3.2) -- never sells, never borrows. A
below-1.0-multiplier day banks the shortfall as cash (earning IRX),
available to fund a future above-1.0-multiplier day, the same reserve
mechanism families 003/005/015/016/017/030/031/035/036/040 use.

Rigorously distinct from family 036 (lag-1 sample autocorrelation, the
closest prior family): rho_1 = Cov(r_t, r_{t-1})/Var(r) measures serial
dependence between ADJACENT daily returns ONLY, at a single lag. The Hurst
exponent here is estimated from the SCALING BEHAVIOR of the range
statistic R/S across MULTIPLE aggregation scales simultaneously within the
same window (a fractal self-similarity/long-range-dependence measure) --
well known in the long-memory-process literature (fractional Gaussian
noise / ARFIMA-style processes) to pick up dependence structure at lags a
single lag-1 autocorrelation coefficient cannot see at all. See
prereg.md's concrete constructed divergence example (a synthetic series
with near-zero lag-1 autocorrelation but H materially different from 0.5).

Category: Trend / time-series momentum exit.

Parameters (4 tunable, <=5 per sec 3.4):
  hurst_window     -- trailing window (days) of daily log returns used to
                       estimate the Hurst exponent via R/S analysis
  pctile_lookback  -- trailing window (days) for the percentile rank of H
                       within its own recent history
  k                -- sensitivity of the multiplier to the percentile rank
  min_mult         -- lower clip bound on the multiplier

Fixed constants (not grid-varied): max_mult=2.0, max_lump_multiple=3.0,
MIN_SCALE=8 (smallest R/S sub-window scale used).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MAX_MULT = 2.0
MAX_LUMP_MULTIPLE = 3.0
MIN_SCALE = 8


HURST_SCALE_DIVISORS = (1, 2, 3, 4, 6, 8, 12, 16)


def _hurst_rs_single_window(window_ret: np.ndarray, min_scale: int = MIN_SCALE) -> float:
    """Classical rescaled-range (R/S) Hurst-exponent estimate for one
    trailing window of daily log returns. Splits the window into several
    sub-window SCALES (a geometric ladder: the full window divided by each
    of HURST_SCALE_DIVISORS = 1,2,3,4,6,8,12,16, deduplicated), computes
    the mean R/S statistic (range of the demeaned cumulative sum, divided
    by the population std) across the non-overlapping sub-windows at each
    scale, then fits log(R/S) vs. log(scale) by least squares -- the slope
    IS the Hurst exponent H. This is a multi-scale statistic BY
    CONSTRUCTION: unlike a single-lag autocorrelation, it looks at the
    range's growth rate across MANY block sizes simultaneously within the
    same window. A denser scale ladder than a simple halving-only ladder
    (n, n/2, n/4, n/8) was chosen deliberately: verified pre-grid (this
    family's prereg.md / run script) that the denser ladder materially
    reduces the well-documented small-sample upward bias of the naive R/S
    estimator (Peters 1994) -- a pure random-walk synthetic series' mean
    estimated H moves from ~0.64 (sparse 4-scale ladder) to ~0.55 (this
    denser ladder) at a 252-day window, closer to the theoretical 0.5,
    though a modest residual bias remains at these short window lengths
    and is documented as a known limitation rather than corrected away
    (no Anis-Lloyd-style bias correction is applied, to keep the parameter
    count and rule complexity within sec 3.4's ceiling). Returns NaN if
    fewer than 2 usable scales exist (too short a window) or if degenerate
    (zero variance at every scale)."""
    n = len(window_ret)
    scales = sorted(set(max(min_scale, n // d) for d in HURST_SCALE_DIVISORS), reverse=True)
    log_n, log_rs = [], []
    for scale in scales:
        if scale < min_scale or scale > n:
            continue
        n_seg = n // scale
        if n_seg < 1:
            continue
        rs_vals = []
        for i in range(n_seg):
            seg = window_ret[i * scale: (i + 1) * scale]
            mean = seg.mean()
            cum_dev = np.cumsum(seg - mean)
            R = cum_dev.max() - cum_dev.min()
            S = seg.std(ddof=0)
            if S > 0:
                rs_vals.append(R / S)
        if rs_vals:
            log_n.append(np.log(scale))
            log_rs.append(np.log(np.mean(rs_vals)))
    if len(log_n) < 2:
        return np.nan
    slope = float(np.polyfit(log_n, log_rs, 1)[0])
    return slope


def compute_hurst_signal(daily: pd.DataFrame, hurst_window: int) -> np.ndarray:
    """Returns H_t, the causal (no-lookahead) trailing Hurst exponent of
    daily log returns for each day, using only data through that day's
    close. NaN until hurst_window+1 return observations exist, or when the
    R/S estimate is undefined (degenerate/near-constant window)."""
    close = daily["Close"].to_numpy(dtype=float)
    log_ret = np.diff(np.log(close), prepend=np.log(close[0]))
    log_ret[0] = 0.0  # no return defined on day 0

    r = pd.Series(log_ret)
    h = r.rolling(hurst_window, min_periods=hurst_window).apply(_hurst_rs_single_window, raw=True)
    return h.to_numpy()


def compute_percentile_rank(hurst: np.ndarray, pctile_lookback: int) -> np.ndarray:
    """Returns pctile_t in [0, 1]: the causal, point-in-time rolling
    percentile rank of H_t within the trailing pctile_lookback window of H
    values ending at t (inclusive). Never uses a future H value, never uses
    a fixed universal threshold (e.g. the textbook H=0.5 cutoff) -- a
    percentile-relative threshold adapts to each asset's own realized H
    range instead, same convention as families 031/035/036/040/041/042.
    Defaults to 0.5 (neutral) until pctile_lookback days of valid H history
    exist."""
    s = pd.Series(hurst)

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
    daily: pd.DataFrame, hurst_window: int, pctile_lookback: int, k: float, min_mult: float,
    max_mult: float = MAX_MULT,
    hurst_cache: np.ndarray | None = None,
) -> np.ndarray:
    """hurst_cache: optionally pass a precomputed compute_hurst_signal(...)
    array (keyed only by (asset, hurst_window), shared across every k/
    min_mult/pctile_lookback grid arm that shares the same hurst_window) to
    avoid recomputing the expensive R/S rolling estimate once per grid
    config -- see scripts/v3/run_044_hurst_regime_sizing.py's cache."""
    hurst = hurst_cache if hurst_cache is not None else compute_hurst_signal(daily, hurst_window)
    pct = compute_percentile_rank(hurst, pctile_lookback)
    m = 1.0 + k * (2.0 * pct - 1.0)
    m = np.clip(m, min_mult, max_mult)
    return m


def make_hurst_regime_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    hurst_window: int = 126, pctile_lookback: int = 252, k: float = 1.0, min_mult: float = 0.5,
    max_mult: float = MAX_MULT, max_lump_multiple: float = MAX_LUMP_MULTIPLE,
    enabled: bool = True,
    hurst_cache: np.ndarray | None = None,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day, which is
    bit-for-bit plain DCA (used to prove the strategy nests DCA exactly)."""
    if enabled:
        m = compute_multiplier(daily, hurst_window, pctile_lookback, k, min_mult, max_mult,
                                hurst_cache=hurst_cache)
    else:
        m = np.ones(len(daily), dtype=float)

    lump_cap = max_lump_multiple * weekly_deposit

    def decide(t, cash):
        target_buy_usd = weekly_deposit * float(m[t])
        capped_buy_usd = min(target_buy_usd, lump_cap)
        # No sells; the engine's own cash cap (sec 3.2) enforces
        # buy_usd<=cash, so a shortfall on a low-multiplier day simply
        # banks as cash (earning IRX) until a later high-multiplier day
        # can spend it -- never leverage, never borrowing.
        return capped_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Trend / time-series momentum exit"

# Grid: hurst_window x pctile_lookback x k x min_mult = 3x2x3x2 = 36 (<=36 cap, 4 tunable params <=5)
GRID = {
    "hurst_window": [100, 126, 252],
    "pctile_lookback": [252, 504],
    "k": [0.5, 1.0, 1.5],
    "min_mult": [0.25, 0.5],
}
PRIMARY_CONFIG = {
    "hurst_window": 126, "pctile_lookback": 252, "k": 1.0, "min_mult": 0.5,
}


def grid_configs() -> list[dict]:
    out = []
    for hw in GRID["hurst_window"]:
        for pl in GRID["pctile_lookback"]:
            for k in GRID["k"]:
                for mm in GRID["min_mult"]:
                    out.append({
                        "hurst_window": hw, "pctile_lookback": pl, "k": k, "min_mult": mm,
                    })
    return out


# Import-time assertion (per families 021/030/036's lesson): PRIMARY_CONFIG
# must be a genuine member of the declared grid, verified before any
# module using this strategy can even be imported successfully.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of the declared grid"
