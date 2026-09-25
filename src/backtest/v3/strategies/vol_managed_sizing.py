"""Family 003: volatility-managed sizing (Moreira & Muir 2017, Harvey et al.
2018).

families/003-vol-managed-sizing/prereg.md has the full mechanism and rules.
Summary: each trading day, compute a "recent" realized annualized volatility
(trailing `vol_lookback_days` daily log returns) and a "reference" realized
annualized volatility (trailing `ref_lookback_days`, a longer window --
adaptive per-asset baseline). The sizing multiplier is
`m_t = clip(sigma_ref_t / sigma_recent_t, min_mult, max_mult)` -- LOW recent
vol relative to the reference gives m_t > 1 (buy more), HIGH recent vol gives
m_t < 1 (buy less). The order submitted every day is
`target_buy_usd_t = weekly_deposit * m_t`; the engine's own cash cap (sec 3.2)
turns this into the reserve mechanism described in prereg.md: a shortfall
(m_t < 1 weeks) banks cash, which is only then available to fund a surplus
(m_t > 1 weeks) later -- never leverage or borrowing.

Category: Volatility targeting.

Parameters (<=5, all in this module):
  vol_lookback_days -- trailing window for the "recent" realized vol
  ref_lookback_days  -- trailing window for the "reference" (baseline) realized vol
  min_mult            -- lower clip bound on the sizing multiplier
  max_mult             -- upper clip bound on the sizing multiplier
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252.0


def compute_multiplier(
    daily: pd.DataFrame, vol_lookback_days: int, ref_lookback_days: int,
    min_mult: float, max_mult: float,
) -> np.ndarray:
    """Returns m_t, the causal (no-lookahead) sizing multiplier for each day,
    using only data through that day's close. Defaults to 1.0 (plain DCA)
    until both rolling windows are computable."""
    close = daily["Close"].to_numpy()
    log_ret = np.diff(np.log(close), prepend=np.log(close[0]))
    log_ret[0] = 0.0  # no return defined on day 0
    ret_s = pd.Series(log_ret)

    sigma_recent = ret_s.rolling(vol_lookback_days, min_periods=vol_lookback_days).std(ddof=1) * np.sqrt(
        TRADING_DAYS_PER_YEAR
    )
    sigma_ref = ret_s.rolling(ref_lookback_days, min_periods=ref_lookback_days).std(ddof=1) * np.sqrt(
        TRADING_DAYS_PER_YEAR
    )

    with np.errstate(divide="ignore", invalid="ignore"):
        raw_ratio = (sigma_ref / sigma_recent).to_numpy()

    m = np.clip(raw_ratio, min_mult, max_mult)
    have_both = (~sigma_recent.isna().to_numpy()) & (~sigma_ref.isna().to_numpy()) & (sigma_recent.to_numpy() > 0)
    m = np.where(have_both, m, 1.0)  # not enough history yet, or zero recent vol -> default to plain DCA
    return m


def make_vol_managed_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    vol_lookback_days: int = 60, ref_lookback_days: int = 252,
    min_mult: float = 0.5, max_mult: float = 2.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces m_t=1.0 for every day, which is
    bit-for-bit plain DCA (used to prove the strategy nests DCA exactly)."""
    if enabled:
        m = compute_multiplier(daily, vol_lookback_days, ref_lookback_days, min_mult, max_mult)
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

# Grid: vol_lookback_days x ref_lookback_days x min_mult x max_mult = 3x2x2x3 = 36 (<=36 cap, 4 params <=5)
GRID = {
    "vol_lookback_days": [20, 40, 60],
    "ref_lookback_days": [126, 252],
    "min_mult": [0.25, 0.5],
    "max_mult": [1.5, 2.0, 3.0],
}
PRIMARY_CONFIG = {
    "vol_lookback_days": 60, "ref_lookback_days": 252, "min_mult": 0.5, "max_mult": 2.0,
}


def grid_configs() -> list[dict]:
    out = []
    for v in GRID["vol_lookback_days"]:
        for r in GRID["ref_lookback_days"]:
            for lo in GRID["min_mult"]:
                for hi in GRID["max_mult"]:
                    out.append({
                        "vol_lookback_days": v, "ref_lookback_days": r,
                        "min_mult": lo, "max_mult": hi,
                    })
    return out
