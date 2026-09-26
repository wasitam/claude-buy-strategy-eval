"""Family 039: Realized-kurtosis (fat-tail) sizing (Bali, Cakici & Whitelaw
2011; Kraus & Litzenberger 1976).

families/039-realized-kurtosis-sizing/prereg.md has the full mechanism,
rules and the required rigorous distinction from family 023 (realized
skewness). Summary: `Kurt_t` is the standard demeaned excess-kurtosis
(fourth standardized moment) of the trailing `kurt_window` daily log
returns, `mean((r-r_bar)^4)/mean((r-r_bar)^2)^2 - 3`. A causal,
point-in-time rolling percentile rank `pctile_t` of `Kurt_t` within its
own trailing `pctile_lookback` history drives a continuous sizing
multiplier (same functional form as family 036's autocorrelation sizing,
sign INVERTED):

    m_t = clip(1 - k * (2 * pctile_t - 1), min_mult, max_mult)

High trailing-kurtosis percentile (fat-tailed/crash-prone regime) ->
LOW multiplier (reduced buying, banks a reserve). Low trailing-kurtosis
percentile (thin-tailed/calm regime) -> HIGH multiplier (increased
buying, draws the reserve down). `min_mult` is always < 1.0 (the
014/033/037 lesson) so the reserve genuinely funds the boost arm. Never a
sell; never leverage; cash never goes negative (engine's own cap, sec
3.2).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MAX_MULT = 2.0
MAX_LUMP_MULTIPLE = 3.0


def compute_realized_kurtosis(daily: pd.DataFrame, kurt_window: int) -> np.ndarray:
    """Causal trailing excess kurtosis of daily log returns (standard
    demeaned fourth-standardized-moment estimator):
        Kurt_t = mean((r_i - r_bar)^4, i in trailing window incl. t) /
                 mean((r_i - r_bar)^2, i in trailing window incl. t)^2 - 3
    NaN until `kurt_window` trading days of return history exist (warm-up),
    or on the negligible-probability zero-variance window case."""
    close = daily["Close"].to_numpy(dtype=float)
    log_ret = np.empty(len(close))
    log_ret[0] = np.nan
    log_ret[1:] = np.log(close[1:] / close[:-1])
    r = pd.Series(log_ret)

    def _kurt_last(window: np.ndarray) -> float:
        w = window[~np.isnan(window)]
        if len(w) < kurt_window:
            return np.nan
        m = w.mean()
        dev = w - m
        s2 = np.mean(dev ** 2)
        if s2 <= 0.0:
            return np.nan
        s4 = np.mean(dev ** 4)
        return float(s4 / (s2 ** 2) - 3.0)

    kurt = r.rolling(kurt_window, min_periods=kurt_window).apply(_kurt_last, raw=True)
    return kurt.to_numpy()


def compute_percentile_rank(kurt: np.ndarray, pctile_lookback: int) -> np.ndarray:
    """Causal, point-in-time rolling percentile rank of Kurt_t within the
    trailing pctile_lookback window of past Kurt values ending at t
    (inclusive). Never uses a future Kurt value, never a fixed
    whole-sample threshold. Defaults to 0.5 (neutral) until
    pctile_lookback days of valid Kurt history exist. Identical
    construction to family 036's compute_percentile_rank."""
    s = pd.Series(kurt)

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
    daily: pd.DataFrame, kurt_window: int, pctile_lookback: int, k: float, min_mult: float,
    max_mult: float = MAX_MULT,
) -> np.ndarray:
    kurt = compute_realized_kurtosis(daily, kurt_window)
    pct = compute_percentile_rank(kurt, pctile_lookback)
    m = 1.0 - k * (2.0 * pct - 1.0)
    m = np.clip(m, min_mult, max_mult)
    return m


def make_realized_kurtosis_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    kurt_window: int = 90, pctile_lookback: int = 252, k: float = 1.0, min_mult: float = 0.5,
    max_mult: float = MAX_MULT, max_lump_multiple: float = MAX_LUMP_MULTIPLE,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day, which is
    bit-for-bit plain DCA (used to prove the strategy nests DCA exactly)."""
    if enabled:
        m = compute_multiplier(daily, kurt_window, pctile_lookback, k, min_mult, max_mult)
    else:
        m = np.ones(len(daily), dtype=float)

    lump_cap = max_lump_multiple * weekly_deposit

    def decide(t, cash):
        target_buy_usd = weekly_deposit * float(m[t])
        capped_buy_usd = min(target_buy_usd, lump_cap)
        # No sells; the engine's own cash cap (sec 3.2) enforces
        # buy_usd<=cash, so a shortfall on a low-multiplier (elevated
        # kurtosis) day simply banks as cash (earning IRX) until a later
        # high-multiplier (depressed kurtosis) day can spend it -- never
        # leverage, never borrowing.
        return capped_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Volatility targeting"

# Grid: kurt_window x pctile_lookback x k x min_mult = 2x2x3x2 = 24 (<=36 cap, 4 tunable params <=5)
GRID = {
    "kurt_window": [60, 90],
    "pctile_lookback": [252, 504],
    "k": [0.5, 1.0, 1.5],
    "min_mult": [0.25, 0.5],
}
PRIMARY_CONFIG = {
    "kurt_window": 90, "pctile_lookback": 252, "k": 1.0, "min_mult": 0.5,
}


def grid_configs() -> list[dict]:
    out = []
    for kw in GRID["kurt_window"]:
        for pl in GRID["pctile_lookback"]:
            for k in GRID["k"]:
                for mm in GRID["min_mult"]:
                    out.append({
                        "kurt_window": kw, "pctile_lookback": pl, "k": k, "min_mult": mm,
                    })
    return out


# Import-time assertion (per families 021/030/036's lesson): PRIMARY_CONFIG
# must be a genuine member of the declared grid.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of the declared grid"

# Import-time assertion (families 014/033/037's now-3x-confirmed lesson):
# every grid cell's min_mult must be strictly below 1.0, or the engine's
# no-leverage cash cap silently nullifies the reserve-banking arm.
for _mm in GRID["min_mult"]:
    assert _mm < 1.0, f"min_mult={_mm!r} must be < 1.0 (families 014/033/037 lesson)"
