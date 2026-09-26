"""Family 035: Parkinson range-based realized-volatility sizing (Parkinson
1980).

families/035-parkinson-vol-sizing/prereg.md has the full mechanism and
rules. Summary: instead of family 003's close-to-close sample-variance
realized-vol estimator, this family estimates realized volatility from each
day's own HIGH-LOW trading range (the Parkinson 1980 extreme-value
estimator), which uses a genuinely different raw input (High/Low, never
Close) and is a statistically more efficient estimator of the same
underlying quantity. The sizing multiplier is
`m_t = clip(sigma_ref_t / sigma_recent_t, min_mult, max_mult)` -- LOW recent
range-vol relative to the reference gives m_t > 1 (buy more), HIGH recent
range-vol gives m_t < 1 (buy less). Same reserve mechanism as family 003:
`target_buy_usd_t = weekly_deposit * m_t`, capped at available cash by the
engine's own cash constraint (sec 3.2) -- never leverage or borrowing.

Category: Volatility targeting.

Parameters (<=5, all in this module):
  park_lookback_days -- trailing window for the "recent" Parkinson range-vol
  ref_lookback_days    -- trailing window for the "reference" (baseline) range-vol
  min_mult              -- lower clip bound on the sizing multiplier
  max_mult                -- upper clip bound on the sizing multiplier
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252.0
PARKINSON_CONST = 4.0 * np.log(2.0)


def parkinson_daily_variance(daily: pd.DataFrame) -> np.ndarray:
    """p_t = (ln(High_t/Low_t))^2 / (4*ln(2)), the Parkinson (1980) per-day
    variance contribution, computed from that day's own High/Low only
    (Close never enters this calculation). High==Low (a degenerate/no-range
    data day -- see prereg.md caveat (d)) correctly evaluates to exactly
    0.0, not NaN or an error."""
    high = daily["High"].to_numpy()
    low = daily["Low"].to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        log_range = np.log(high / low)
    log_range = np.where(np.isfinite(log_range), log_range, 0.0)
    return (log_range ** 2) / PARKINSON_CONST


def compute_multiplier(
    daily: pd.DataFrame, park_lookback_days: int, ref_lookback_days: int,
    min_mult: float, max_mult: float,
) -> np.ndarray:
    """Returns m_t, the causal (no-lookahead) sizing multiplier for each day,
    using only data through that day's close. Defaults to 1.0 (plain DCA)
    until both rolling windows are computable, or if the recent window's
    Parkinson variance is exactly 0 (a window made entirely of degenerate
    High==Low days -- avoids a division by zero)."""
    p = parkinson_daily_variance(daily)
    p_s = pd.Series(p)

    mean_recent = p_s.rolling(park_lookback_days, min_periods=park_lookback_days).mean()
    mean_ref = p_s.rolling(ref_lookback_days, min_periods=ref_lookback_days).mean()

    sigma_recent = np.sqrt(mean_recent.to_numpy() * TRADING_DAYS_PER_YEAR)
    sigma_ref = np.sqrt(mean_ref.to_numpy() * TRADING_DAYS_PER_YEAR)

    with np.errstate(divide="ignore", invalid="ignore"):
        raw_ratio = sigma_ref / sigma_recent

    m = np.clip(raw_ratio, min_mult, max_mult)
    have_both = (~mean_recent.isna().to_numpy()) & (~mean_ref.isna().to_numpy()) & (sigma_recent > 0)
    m = np.where(have_both, m, 1.0)
    return m


def make_parkinson_vol_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    park_lookback_days: int = 60, ref_lookback_days: int = 252,
    min_mult: float = 0.5, max_mult: float = 2.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day, which is
    bit-for-bit plain DCA (used to prove the strategy nests DCA exactly)."""
    if enabled:
        m = compute_multiplier(daily, park_lookback_days, ref_lookback_days, min_mult, max_mult)
    else:
        m = np.ones(len(daily), dtype=float)

    def decide(t, cash):
        target_buy_usd = weekly_deposit * float(m[t])
        # No sells; the engine's own cash cap (sec 3.2) enforces buy_usd<=cash,
        # so a shortfall on a low-multiplier day/week simply banks as cash
        # (earning IRX) until a later high-multiplier day can spend it.
        return target_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Volatility targeting"

# Grid: park_lookback_days x ref_lookback_days x min_mult x max_mult = 3x2x2x3 = 36 (<=36 cap, 4 params <=5)
# Deliberately mirrors family 003's exact grid values -- see prereg.md's
# "Parameters" section for why (isolates the estimator swap as the only
# difference from family 003).
GRID = {
    "park_lookback_days": [20, 40, 60],
    "ref_lookback_days": [126, 252],
    "min_mult": [0.25, 0.5],
    "max_mult": [1.5, 2.0, 3.0],
}
PRIMARY_CONFIG = {
    "park_lookback_days": 60, "ref_lookback_days": 252, "min_mult": 0.5, "max_mult": 2.0,
}


def grid_configs() -> list[dict]:
    out = []
    for v in GRID["park_lookback_days"]:
        for r in GRID["ref_lookback_days"]:
            for lo in GRID["min_mult"]:
                for hi in GRID["max_mult"]:
                    out.append({
                        "park_lookback_days": v, "ref_lookback_days": r,
                        "min_mult": lo, "max_mult": hi,
                    })
    return out


assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG must be a member of the declared grid"
