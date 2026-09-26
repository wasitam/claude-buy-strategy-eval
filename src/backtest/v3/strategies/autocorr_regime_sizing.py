"""Family 036: return-autocorrelation regime sizing (Lo & MacKinlay 1988).

families/036-autocorr-regime-sizing/prereg.md has the full mechanism and
rules. Summary: each trading day, compute the asset's own trailing lag-1
sample autocorrelation `rho_1_t` of daily log returns (Pearson correlation
between `r_i` and `r_{i-1}` over a trailing `ac_window`-day window), then a
causal, point-in-time percentile rank `pctile_t` of `rho_1_t` within its
own trailing `pctile_lookback` window. The sizing multiplier scales
CONTINUOUSLY with that percentile rank (no discrete threshold buckets,
same functional form as family 031's Kelly-Sharpe sizing):
    m_t = clip(1 + k * (2 * pctile_t - 1), min_mult, max_mult)
The order submitted every trading day is
`target_buy_usd = weekly_deposit * m_t`, capped at
`max_lump_multiple * weekly_deposit` and then at available cash (the
engine's own no-leverage cap, sec 3.2) -- never sells, never borrows. A
below-1.0-multiplier day banks the shortfall as cash (earning IRX),
available to fund a future above-1.0-multiplier day, the same reserve
mechanism families 003/005/015/016/017/030/031/035 use.

Rigorously distinct from family 003 (realized VARIANCE, second moment of
returns), family 005 (SIGN of trailing return, first moment), family 030
(discrete consecutive-day STREAK COUNT, magnitude-blind), and family 031
(return-to-vol SHARPE RATIO, a ratio of the first two moments): rho_1 is
the lag-1 sample autocorrelation, `Cov(r_t, r_{t-1}) / Var(r)`, a measure
of the SERIAL DEPENDENCE STRUCTURE of consecutive returns that is by
construction invariant to any reordering of the same multiset of daily
returns that changes none of families 003/005/030/031's statistics --
see prereg.md's constructed toy example.

Category: Trend / time-series momentum exit.

Parameters (4 tunable, <=5 per sec 3.4):
  ac_window        -- trailing window (days) of return pairs used to
                       compute the lag-1 sample autocorrelation
  pctile_lookback  -- trailing window (days) for the percentile rank of
                       rho_1 within its own recent history
  k                -- sensitivity of the multiplier to the percentile rank
  min_mult         -- lower clip bound on the multiplier

Fixed constants (not grid-varied): max_mult=2.0, max_lump_multiple=3.0.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MAX_MULT = 2.0
MAX_LUMP_MULTIPLE = 3.0


def compute_autocorr_signal(daily: pd.DataFrame, ac_window: int) -> np.ndarray:
    """Returns rho_1_t, the causal (no-lookahead) trailing lag-1 sample
    Pearson autocorrelation of daily log returns for each day, using only
    data through that day's close. NaN until ac_window+1 return
    observations exist, or when the trailing window of returns has zero
    variance (a degenerate constant-return stretch).

    Vectorized via pandas' rolling Pearson correlation between the return
    series and its own lag-1 shift: rho_1_t = corr(r_i, r_{i-1}) computed
    over the trailing ac_window aligned pairs (i in [t-ac_window+1, t]),
    identical definition to, but far faster than, a per-day
    np.corrcoef loop -- verified to match a hand/loop computation exactly
    in scripts/v3/run_036_autocorr_regime_sizing.py's formula spot-check."""
    close = daily["Close"].to_numpy(dtype=float)
    log_ret = np.diff(np.log(close), prepend=np.log(close[0]))
    log_ret[0] = 0.0  # no return defined on day 0

    r = pd.Series(log_ret)
    lag = r.shift(1)
    # min_periods=ac_window ensures a day-0-anchored full window; the first
    # ac_window rows (where lag[0] is NaN) are naturally excluded by
    # pandas' pairwise-complete-observations rolling corr, matching the
    # "needs ac_window+1 total return observations ending at t" causal rule.
    rho1 = r.rolling(ac_window, min_periods=ac_window).corr(lag)
    return rho1.to_numpy()


def compute_percentile_rank(rho1: np.ndarray, pctile_lookback: int) -> np.ndarray:
    """Returns pctile_t in [0, 1]: the causal, point-in-time rolling
    percentile rank of rho_1_t within the trailing pctile_lookback window
    of rho_1 values ending at t (inclusive). Never uses a future rho_1
    value, never uses a fixed whole-sample threshold. Defaults to 0.5
    (neutral) until pctile_lookback days of valid rho_1 history exist."""
    s = pd.Series(rho1)

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
    daily: pd.DataFrame, ac_window: int, pctile_lookback: int, k: float, min_mult: float,
    max_mult: float = MAX_MULT,
) -> np.ndarray:
    rho1 = compute_autocorr_signal(daily, ac_window)
    pct = compute_percentile_rank(rho1, pctile_lookback)
    m = 1.0 + k * (2.0 * pct - 1.0)
    m = np.clip(m, min_mult, max_mult)
    return m


def make_autocorr_regime_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    ac_window: int = 40, pctile_lookback: int = 252, k: float = 1.0, min_mult: float = 0.5,
    max_mult: float = MAX_MULT, max_lump_multiple: float = MAX_LUMP_MULTIPLE,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day, which is
    bit-for-bit plain DCA (used to prove the strategy nests DCA exactly)."""
    if enabled:
        m = compute_multiplier(daily, ac_window, pctile_lookback, k, min_mult, max_mult)
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

# Grid: ac_window x pctile_lookback x k x min_mult = 3x2x3x2 = 36 (<=36 cap, 4 tunable params <=5)
GRID = {
    "ac_window": [20, 40, 60],
    "pctile_lookback": [252, 504],
    "k": [0.5, 1.0, 1.5],
    "min_mult": [0.25, 0.5],
}
PRIMARY_CONFIG = {
    "ac_window": 40, "pctile_lookback": 252, "k": 1.0, "min_mult": 0.5,
}


def grid_configs() -> list[dict]:
    out = []
    for aw in GRID["ac_window"]:
        for pl in GRID["pctile_lookback"]:
            for k in GRID["k"]:
                for mm in GRID["min_mult"]:
                    out.append({
                        "ac_window": aw, "pctile_lookback": pl, "k": k, "min_mult": mm,
                    })
    return out


# Import-time assertion (per families 021/030's lesson): PRIMARY_CONFIG
# must be a genuine member of the declared grid, verified before any
# module using this strategy can even be imported successfully.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of the declared grid"
