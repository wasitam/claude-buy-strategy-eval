"""Family 033: Volume-confirmed breakout sizing (Karpoff 1987; Lee &
Swaminathan 2000).

families/033-volume-breakout/prereg.md has the full mechanism, rules, data
feasibility (reusing family 021's Volume-coverage finding) and the
required fourfold distinction from families 001/005/020/028. Summary:
using one shared trailing window for both legs, a joint AND condition --
(a) Close_t is a new high over the trailing `window` days (strictly
causal, excludes day t itself), AND (b) Volume_t exceeds
`volume_surge_multiple` times its own trailing `window`-day average
volume (strictly causal, excludes day t itself, ignores invalid
zero/missing volume days in its population) -- triggers a larger weekly
buy (`breakout_buy_mult`); otherwise the weekly buy uses `normal_buy_mult`
("scale down/normal"). Never sells; the engine's own cash cap (sec 3.2)
turns a `normal_buy_mult<1` week's shortfall into banked cash (earning
IRX) that can fund a later breakout week -- the same reserve mechanism
families 003/005/014/020/021/028 all use, never leverage or borrowing.

Category: Trend / time-series momentum exit.

Parameters (4 of the allowed 5, all in this module):
  window                  -- shared trailing-high AND trailing-volume-
                              average lookback, trading days.
  volume_surge_multiple   -- how far above its own trailing average a
                              day's volume must be to count as a "surge".
  breakout_buy_mult       -- buy multiplier on a confirmed joint breakout
                              week.
  normal_buy_mult         -- buy multiplier otherwise.
  (max_lump_multiple is fixed at 4.0, not grid-varied.)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Minimum fraction of the trailing `window` that must have valid
# (non-zero, non-missing) volume observations before the trailing volume
# average is trusted at all -- family 021's Amihud precedent: never
# fabricate a signal from bad/missing volume data.
MIN_VALID_VOLUME_FRAC = 0.5


def compute_trailing_high(daily: pd.DataFrame, window: int) -> np.ndarray:
    """Causal trailing high EXCLUDING today: high_t = max(Close[t-window..
    t-1]). Strictly causal (shifted by 1 before the rolling max) so a
    breakout is 'closed today above the PRIOR window's high', not a
    tautology against today's own close. NaN during warm-up (no signal
    yet, fewer than `window` full prior trading days available)."""
    close = daily["Close"]
    shifted = close.shift(1)
    high = shifted.rolling(window, min_periods=window).max()
    return high.to_numpy()


def compute_trailing_volume_avg(daily: pd.DataFrame, window: int) -> tuple[np.ndarray, np.ndarray]:
    """Causal trailing average volume EXCLUDING today (shifted by 1),
    ignoring zero/missing volume days in the population entirely (never
    imputed as zero). Returns (avg, valid_frac); valid_frac is the
    fraction of the trailing `window` days that had a valid volume
    observation, used to gate whether the average is trustworthy."""
    vol = daily["Volume"].to_numpy()
    valid = np.isfinite(vol) & (vol > 0)
    vol_valid = np.where(valid, vol, np.nan)
    s = pd.Series(vol_valid, index=daily.index)
    shifted = s.shift(1)
    avg = shifted.rolling(window, min_periods=1).mean().to_numpy()
    n_valid = shifted.rolling(window, min_periods=1).count().to_numpy()
    valid_frac = n_valid / float(window)
    # Full warm-up: require `window` prior trading days to have elapsed at
    # all (matches compute_trailing_high's own warm-up), even though the
    # rolling call above uses min_periods=1 for a partial early estimate.
    t_idx = np.arange(len(vol))
    warmed_up = t_idx >= window
    avg = np.where(warmed_up, avg, np.nan)
    valid_frac = np.where(warmed_up, valid_frac, 0.0)
    return avg, valid_frac


def compute_joint_breakout(daily: pd.DataFrame, window: int, volume_surge_multiple: float) -> np.ndarray:
    """joint[t] = price_breakout[t] AND volume_surge[t] -- BOTH legs
    required (the entire mechanism; see prereg.md)."""
    close = daily["Close"].to_numpy()
    high = compute_trailing_high(daily, window)
    price_breakout = np.isfinite(high) & (close > high)

    vol = daily["Volume"].to_numpy()
    vol_today_valid = np.isfinite(vol) & (vol > 0)
    avg, valid_frac = compute_trailing_volume_avg(daily, window)
    avg_trustworthy = np.isfinite(avg) & (valid_frac >= MIN_VALID_VOLUME_FRAC)
    with np.errstate(invalid="ignore"):
        volume_surge = vol_today_valid & avg_trustworthy & (vol > volume_surge_multiple * avg)

    return price_breakout & volume_surge


def compute_multiplier(
    daily: pd.DataFrame, window: int, volume_surge_multiple: float,
    breakout_buy_mult: float, normal_buy_mult: float,
) -> np.ndarray:
    joint = compute_joint_breakout(daily, window, volume_surge_multiple)
    return np.where(joint, breakout_buy_mult, normal_buy_mult).astype(float)


def make_volume_breakout_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    window: int = 40, volume_surge_multiple: float = 1.5,
    breakout_buy_mult: float = 2.0, normal_buy_mult: float = 1.0,
    max_lump_multiple: float = 4.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it forces the multiplier to 1.0 for every day
    (skips the breakout/volume computation entirely), which is bit-for-bit
    plain DCA."""
    if enabled:
        m = compute_multiplier(daily, window, volume_surge_multiple, breakout_buy_mult, normal_buy_mult)
    else:
        m = np.ones(len(daily), dtype=float)

    def decide(t, cash):
        target_buy_usd = weekly_deposit * float(m[t])
        # Cash-capped: never leverage. The engine's own cap (sec 3.2) turns
        # a normal_buy_mult<1 week into banked cash, available for a later
        # breakout_buy_mult>1 week. max_lump_multiple bounds a single
        # catch-up buy even with a large banked reserve.
        capped_buy_usd = min(target_buy_usd, max_lump_multiple * weekly_deposit)
        return capped_buy_usd, 0.0, {"multiplier": float(m[t])}

    return decide


CATEGORY = "Trend / time-series momentum exit"

# Grid: window(3) x volume_surge_multiple(2) x breakout_buy_mult(3) x
# normal_buy_mult(2) = 36 (<=36 cap, 4 tunable params <=5)
GRID = {
    "window": [20, 40, 60],
    "volume_surge_multiple": [1.5, 2.0],
    "breakout_buy_mult": [1.5, 2.0, 2.5],
    "normal_buy_mult": [0.75, 1.0],
}
PRIMARY_CONFIG = {
    "window": 40, "volume_surge_multiple": 1.5,
    "breakout_buy_mult": 2.0, "normal_buy_mult": 1.0,
}


def grid_configs() -> list[dict]:
    out = []
    for w in GRID["window"]:
        for vsm in GRID["volume_surge_multiple"]:
            for bbm in GRID["breakout_buy_mult"]:
                for nbm in GRID["normal_buy_mult"]:
                    out.append({
                        "window": w, "volume_surge_multiple": vsm,
                        "breakout_buy_mult": bbm, "normal_buy_mult": nbm,
                    })
    return out


# Module-import-time assertion (family 021's lesson, state/bugfix_log.md):
# verify PRIMARY_CONFIG is a genuine member of the declared grid before
# anything else in this module can be used.
assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG must be a member of grid_configs()"
