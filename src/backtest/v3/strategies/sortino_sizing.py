"""Family 040: Rolling Sortino-ratio sizing (Sortino & van der Meer 1991;
Sortino & Price 1994).

families/040-sortino-sizing/prereg.md has the full mechanism, rules and
the required rigorous distinction from family 031 (Kelly-Sharpe sizing).
Summary: `Sortino_t` is the trailing `sortino_window`-day mean daily log
return divided by the trailing DOWNSIDE deviation (semi-deviation: only
negative-return days contribute to the sum of squares in the numerator of
the deviation; the denominator of the deviation itself is the FULL window
length, the standard Sortino & Price (1994) convention, target=0). A
causal, point-in-time rolling percentile rank `pctile_t` of `Sortino_t`
within its own trailing `pctile_lookback` history drives a continuous
sizing multiplier (same functional form as family 031's Kelly-Sharpe
sizing, sign NOT inverted -- elevated own-percentile Sortino -> buy MORE):

    m_t = clip(1 + k * (2 * pctile_t - 1), min_mult, max_mult)

Never a sell; never leverage; cash never goes negative (engine's own cap,
sec 3.2).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MAX_MULT = 2.0
MAX_LUMP_MULTIPLE = 3.0


def compute_downside_deviation(window: np.ndarray) -> float:
    """Sortino & Price (1994) semi-deviation, target (MAR) = 0: only
    negative-return days contribute to the sum of squares; the divisor is
    the FULL window length `n` (not just the count of negative days) --
    the standard textbook convention, distinct from a "mean of negative
    days only" statistic."""
    downside = np.minimum(window, 0.0)
    return float(np.sqrt(np.mean(downside ** 2)))


def compute_rolling_sortino(daily: pd.DataFrame, sortino_window: int) -> np.ndarray:
    """Causal trailing Sortino ratio of daily log returns:
        Sortino_t = mean(r; trailing sortino_window days incl. t) /
                    downside_deviation(r; trailing sortino_window days incl. t)
    NaN until `sortino_window` days of return history exist (warm-up), or
    on the negligible-probability zero-downside-deviation case (a window
    with no negative days at all)."""
    close = daily["Close"].to_numpy(dtype=float)
    log_ret = np.empty(len(close))
    log_ret[0] = np.nan
    log_ret[1:] = np.log(close[1:] / close[:-1])
    r = pd.Series(log_ret)

    def _sortino_last(window: np.ndarray) -> float:
        w = window[~np.isnan(window)]
        if len(w) < sortino_window:
            return np.nan
        m = w.mean()
        dd = compute_downside_deviation(w)
        if dd <= 0.0:
            return np.nan
        return float(m / dd)

    sortino = r.rolling(sortino_window, min_periods=sortino_window).apply(_sortino_last, raw=True)
    return sortino.to_numpy()


def compute_percentile_rank(sortino: np.ndarray, pctile_lookback: int) -> np.ndarray:
    """Causal, point-in-time rolling percentile rank of Sortino_t within
    the trailing pctile_lookback window of past Sortino values ending at t
    (inclusive). Never uses a future Sortino value, never a fixed
    whole-sample threshold. Defaults to 0.5 (neutral) until
    pctile_lookback days of valid Sortino history exist. Identical
    construction to families 036/039's compute_percentile_rank."""
    s = pd.Series(sortino)

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
    daily: pd.DataFrame, sortino_window: int, pctile_lookback: int, k: float, min_mult: float,
    max_mult: float = MAX_MULT,
) -> np.ndarray:
    sortino = compute_rolling_sortino(daily, sortino_window)
    pct = compute_percentile_rank(sortino, pctile_lookback)
    m = 1.0 + k * (2.0 * pct - 1.0)
    m = np.clip(m, min_mult, max_mult)
    return m


def make_sortino_sizing_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    sortino_window: int = 60, pctile_lookback: int = 504, k: float = 1.0, min_mult: float = 0.5,
    max_mult: float = MAX_MULT, max_lump_multiple: float = MAX_LUMP_MULTIPLE,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day, which is
    bit-for-bit plain DCA (used to prove the strategy nests DCA exactly).

    Explicit no-leverage clarification (research-loop-plan-v3.md sec 3.4 /
    sec 2's "no leverage" rule, family 031's own precedent): "Sortino
    ratio" sizing could be mistaken for a leverage/gearing rule since it
    scales a position by a risk-adjusted-return statistic. It is not.
    Every buy here is capped at (a) a fixed multiple of the weekly deposit
    (`max_lump_multiple`, a hard ceiling regardless of banked cash) and
    (b) the engine's own unconditional cash cap (`buy_usd <= cash`,
    `engine.py` sec 3.2), so the strategy can never spend more than it has
    banked from actual past deposits plus earned interest -- no borrowing,
    no negative cash, ever.
    """
    if enabled:
        m = compute_multiplier(daily, sortino_window, pctile_lookback, k, min_mult, max_mult)
    else:
        m = np.ones(len(daily), dtype=float)

    lump_cap = max_lump_multiple * weekly_deposit

    def decide(t, cash):
        target_buy_usd = weekly_deposit * float(m[t])
        capped_buy_usd = min(target_buy_usd, lump_cap)
        # No sells; the engine's own cash cap (sec 3.2) enforces
        # buy_usd<=cash, so a shortfall on a low-multiplier (depressed
        # Sortino percentile) week simply banks as cash (earning IRX)
        # until a later high-multiplier (elevated Sortino percentile) week
        # can spend it -- never leverage, never borrowing.
        return capped_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Sizing / valuation"

# Grid: sortino_window x pctile_lookback x k x min_mult = 3x2x3x2 = 36 (<=36 cap, 4 tunable params <=5)
GRID = {
    "sortino_window": [40, 60, 90],
    "pctile_lookback": [504, 756],
    "k": [0.5, 1.0, 1.5],
    "min_mult": [0.25, 0.5],
}
PRIMARY_CONFIG = {
    "sortino_window": 60, "pctile_lookback": 504, "k": 1.0, "min_mult": 0.5,
}


def grid_configs() -> list[dict]:
    out = []
    for sw in GRID["sortino_window"]:
        for pl in GRID["pctile_lookback"]:
            for k in GRID["k"]:
                for mm in GRID["min_mult"]:
                    out.append({
                        "sortino_window": sw, "pctile_lookback": pl, "k": k, "min_mult": mm,
                    })
    return out


# Import-time assertion (per families 021/030/036/039's lesson):
# PRIMARY_CONFIG must be a genuine member of the declared grid.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of the declared grid"

# Import-time assertion (families 014/033/037/039's now-4x-confirmed
# lesson): every grid cell's min_mult must be strictly below 1.0, or the
# engine's no-leverage cash cap silently nullifies the reserve-banking arm.
for _mm in GRID["min_mult"]:
    assert _mm < 1.0, f"min_mult={_mm!r} must be < 1.0 (families 014/033/037/039 lesson)"

assert len(grid_configs()) <= 36, "grid exceeds sec 3.4's 36-configuration cap"
