"""Family 031: Kelly-fraction-style trailing-Sharpe sizing (Kelly 1956;
Thorp 2006 fractional-Kelly practitioner applications).

families/031-kelly-sharpe-sizing/prereg.md has the full mechanism and
rules. Summary: each trading day, compute the asset's own trailing Sharpe
ratio `S_t` (annualized mean / annualized std of daily log returns over a
trailing `sharpe_window`), then a causal, point-in-time percentile rank
`pctile_t` of `S_t` within its own trailing `pctile_lookback` window. The
sizing multiplier scales CONTINUOUSLY with that percentile rank (no
discrete threshold buckets):
    m_t = clip(1 + k * (2 * pctile_t - 1), min_mult, max_mult)
The order submitted every week-end day is
`target_buy_usd = weekly_deposit * m_t`, capped at
`max_lump_multiple * weekly_deposit` and then at available cash (the
engine's own no-leverage cap, sec 3.2) -- never sells, never borrows. A
below-1.0-multiplier week banks the shortfall as cash (earning IRX),
available to fund a future above-1.0-multiplier week, the same reserve
mechanism families 003/005/015/016/017/030 use.

This is explicitly NOT literal Kelly leverage: `max_mult` and
`max_lump_multiple` are fixed safety ceilings, and the engine's cash cap
means this strategy can never spend more than has actually been deposited
plus earned interest. See prereg.md's "explicit non-leverage
clarification."

Category: Sizing / valuation.

Parameters (4 tunable, <=5 per sec 3.4):
  sharpe_window    -- trailing window (days) for the mean/vol computation
  pctile_lookback  -- trailing window (days) for the percentile rank
  k                -- sensitivity of the multiplier to the percentile rank
  min_mult         -- lower clip bound on the multiplier

Fixed constants (not grid-varied): max_mult=2.0, max_lump_multiple=3.0.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252.0

MAX_MULT = 2.0
MAX_LUMP_MULTIPLE = 3.0


def compute_sharpe_signal(daily: pd.DataFrame, sharpe_window: int) -> np.ndarray:
    """Returns S_t, the causal (no-lookahead) trailing annualized Sharpe
    ratio of daily log returns for each day, using only data through that
    day's close. NaN until sharpe_window days of history exist, or the
    trailing std is exactly zero."""
    close = daily["Close"].to_numpy()
    log_ret = np.diff(np.log(close), prepend=np.log(close[0]))
    log_ret[0] = 0.0  # no return defined on day 0
    ret_s = pd.Series(log_ret)

    mean_ann = ret_s.rolling(sharpe_window, min_periods=sharpe_window).mean() * TRADING_DAYS_PER_YEAR
    std_ann = ret_s.rolling(sharpe_window, min_periods=sharpe_window).std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)

    with np.errstate(divide="ignore", invalid="ignore"):
        sharpe = (mean_ann / std_ann).to_numpy()
    sharpe = np.where(std_ann.to_numpy() > 0, sharpe, np.nan)
    return sharpe


def compute_percentile_rank(sharpe: np.ndarray, pctile_lookback: int) -> np.ndarray:
    """Returns pctile_t in [0, 1]: the causal, point-in-time rolling
    percentile rank of S_t within the trailing pctile_lookback window of
    S values ending at t (inclusive). Never uses a future S value, never
    uses a fixed whole-sample threshold. Defaults to 0.5 (neutral) until
    pctile_lookback days of S history exist."""
    s = pd.Series(sharpe)
    valid = s.notna()

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
    daily: pd.DataFrame, sharpe_window: int, pctile_lookback: int, k: float, min_mult: float,
    max_mult: float = MAX_MULT,
) -> np.ndarray:
    sharpe = compute_sharpe_signal(daily, sharpe_window)
    pct = compute_percentile_rank(sharpe, pctile_lookback)
    m = 1.0 + k * (2.0 * pct - 1.0)
    m = np.clip(m, min_mult, max_mult)
    return m


def make_kelly_sharpe_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    sharpe_window: int = 60, pctile_lookback: int = 504, k: float = 1.0, min_mult: float = 0.5,
    max_mult: float = MAX_MULT, max_lump_multiple: float = MAX_LUMP_MULTIPLE,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day, which is
    bit-for-bit plain DCA (used to prove the strategy nests DCA exactly)."""
    if enabled:
        m = compute_multiplier(daily, sharpe_window, pctile_lookback, k, min_mult, max_mult)
    else:
        m = np.ones(len(daily), dtype=float)

    lump_cap = max_lump_multiple * weekly_deposit

    def decide(t, cash):
        target_buy_usd = weekly_deposit * float(m[t])
        capped_buy_usd = min(target_buy_usd, lump_cap)
        # No sells; the engine's own cash cap (sec 3.2) enforces
        # buy_usd<=cash, so a shortfall on a low-multiplier week simply
        # banks as cash (earning IRX) until a later high-multiplier week
        # can spend it -- never leverage, never borrowing.
        return capped_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Sizing / valuation"

# Grid: sharpe_window x pctile_lookback x k x min_mult = 3x2x3x2 = 36 (<=36 cap, 4 tunable params <=5)
GRID = {
    "sharpe_window": [40, 60, 90],
    "pctile_lookback": [504, 756],
    "k": [0.5, 1.0, 1.5],
    "min_mult": [0.25, 0.5],
}
PRIMARY_CONFIG = {
    "sharpe_window": 60, "pctile_lookback": 504, "k": 1.0, "min_mult": 0.5,
}


def grid_configs() -> list[dict]:
    out = []
    for sw in GRID["sharpe_window"]:
        for pl in GRID["pctile_lookback"]:
            for k in GRID["k"]:
                for mm in GRID["min_mult"]:
                    out.append({
                        "sharpe_window": sw, "pctile_lookback": pl, "k": k, "min_mult": mm,
                    })
    return out


# Import-time assertion (per families 021/030's lesson): PRIMARY_CONFIG
# must be a genuine member of the declared grid, verified before any
# module using this strategy can even be imported successfully.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of the declared grid"
