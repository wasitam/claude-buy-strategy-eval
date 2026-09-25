"""Family 021: Amihud illiquidity-shock sizing (Amihud 2002).

families/021-amihud-illiquidity/prereg.md has the full mechanism, rules,
data-feasibility finding and the required distinction from families
003/016/017. Summary: illiq_t = |r_t| / (Close_t * Volume_t) (undefined
on zero/missing-volume days -- excluded from ranking, never fabricated).
A trailing causal percentile rank of illiq_t marks an "elevated" shock day
when it crosses elevated_pct; the elevated REGIME then persists for
decay_days trading days after its last trigger (a sticky window). Deposits
are sized UP (buy_multiplier * weekly_deposit, cash-capped) on a
week-end decision day that falls inside an elevated regime, funded by
banking (1 - calm_fraction) of every calm week's deposit as cash (earning
IRX). No sells, ever; no leverage; cash never goes negative. Same weekly-
decision-cadence pattern as family 016's VIX contrarian decider.

Category: Sizing / valuation.

Parameters (5 tunable + 1 fixed, all <=5):
  illiq_lookback    -- trailing window (trading days) for the percentile
                        rank of illiq_t (counting only defined values).
  elevated_pct      -- percentile threshold (0-100) marking a shock day.
  decay_days        -- how many trading days the elevated regime persists
                        after its last trigger.
  buy_multiplier    -- multiple of weekly_deposit bought on an elevated
                        week-end (cash-capped).
  calm_fraction     -- fraction of weekly_deposit bought on a calm
                        week-end (remainder banked to fund later buying).
  max_buy_multiple  -- fixed at 4.0 (not grid-varied), hard ceiling on any
                        single week's buy relative to weekly_deposit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import engine as eng

MIN_VALID_OBS = 20  # warm-up: fewer than this many valid illiq readings -> "not elevated"


def compute_illiq(daily: pd.DataFrame) -> np.ndarray:
    """Amihud ratio |r_t| / (Close_t * Volume_t), NaN wherever Volume_t is
    zero, missing, or dollar volume <= 0 (prereg.md's explicit handling
    rule -- never fabricate a signal from a bad volume print)."""
    close = daily["Close"].to_numpy()
    volume = daily["Volume"].to_numpy()
    ret = np.empty(len(close))
    ret[0] = np.nan
    ret[1:] = close[1:] / close[:-1] - 1.0
    dollar_vol = close * volume
    with np.errstate(divide="ignore", invalid="ignore"):
        illiq = np.abs(ret) / dollar_vol
    bad = ~np.isfinite(volume) | (volume <= 0) | ~np.isfinite(dollar_vol) | (dollar_vol <= 0)
    illiq = np.where(bad, np.nan, illiq)
    return illiq


def _trailing_pctile_rank_ignoring_nan(illiq: np.ndarray, lookback: int) -> np.ndarray:
    """Causal trailing percentile rank of illiq_t among the last `lookback`
    trading days' DEFINED (non-NaN) values only, including day t itself if
    defined. NaN days are excluded from the population and never rank (the
    output is NaN on those days, which compute_trigger treats as 'no
    trigger'). Needs >= MIN_VALID_OBS defined values in the trailing window
    before it produces anything (warm-up convention)."""
    # Vectorized equivalent of the causal trailing-window rank-among-valid-
    # values loop (same semantics, much faster than a per-day pandas slice):
    # for each t, out[t] = 100 * (count of valid window values <= illiq[t])
    # / (count of valid window values), using searchsorted on a running
    # sorted multiset of the trailing window's valid values.
    n = len(illiq)
    out = np.full(n, np.nan)
    valid = np.isfinite(illiq)
    import bisect
    window_sorted: list[float] = []
    for t in range(n):
        lo = t - lookback + 1
        if valid[t]:
            bisect.insort(window_sorted, illiq[t])
        # evict the value at index lo-1 if it just left the window and was valid
        evict_idx = lo - 1
        if evict_idx >= 0 and valid[evict_idx]:
            pos = bisect.bisect_left(window_sorted, illiq[evict_idx])
            if pos < len(window_sorted) and window_sorted[pos] == illiq[evict_idx]:
                window_sorted.pop(pos)
        if not valid[t] or len(window_sorted) < MIN_VALID_OBS:
            continue
        rank = bisect.bisect_right(window_sorted, illiq[t])
        out[t] = 100.0 * rank / len(window_sorted)
    return out


def compute_elevated_regime(daily: pd.DataFrame, illiq_lookback: int, elevated_pct: float,
                             decay_days: int) -> tuple[np.ndarray, np.ndarray]:
    """Returns (trigger, elevated_regime) boolean arrays aligned to
    daily.index. trigger[t] = illiq_t defined and its trailing percentile
    rank >= elevated_pct. elevated_regime[t] = a trigger occurred on any of
    the trailing decay_days trading days up to and including t (sticky
    window)."""
    illiq = compute_illiq(daily)
    pctile = _trailing_pctile_rank_ignoring_nan(illiq, illiq_lookback)
    trigger = np.nan_to_num(pctile, nan=-1.0) >= elevated_pct
    trig_series = pd.Series(trigger.astype(float))
    regime = trig_series.rolling(decay_days, min_periods=1).max().astype(bool).to_numpy()
    return trigger, regime


def make_amihud_illiquidity_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    illiq_lookback: int = 252, elevated_pct: float = 95.0, decay_days: int = 5,
    buy_multiplier: float = 2.0, calm_fraction: float = 0.90,
    max_buy_multiple: float = 4.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the Amihud/percentile/decay
    computation entirely and buys the full week's cash every week-end day
    (0 otherwise), which is bit-for-bit plain DCA."""
    is_week_end = eng.week_end_flags(daily.index)
    elevated = compute_elevated_regime(daily, illiq_lookback, elevated_pct, decay_days)[1] if enabled else None

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if elevated[t]:
            target_buy_usd = min(cash, buy_multiplier * weekly_deposit, max_buy_multiple * weekly_deposit)
        else:
            target_buy_usd = calm_fraction * weekly_deposit
        return target_buy_usd, 0.0, {"elevated_illiquidity": bool(elevated[t])}

    return decide


def make_decider_from_elevated_array(
    daily: pd.DataFrame, weekly_deposit: float, elevated: np.ndarray,
    buy_multiplier: float = 2.0, calm_fraction: float = 0.90,
    max_buy_multiple: float = 4.0,
):
    """Same weekly decision rule as make_amihud_illiquidity_decider, but
    driven by an arbitrary pre-computed `elevated` boolean array -- used by
    the placebo circular-shift robustness test (sec 4.3), which shifts the
    regime's TIMING while keeping its overall elevated/calm frequency
    identical. Mirrors family 016's own placebo helper."""
    is_week_end = eng.week_end_flags(daily.index)

    def decide(t, cash):
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if elevated[t]:
            target_buy_usd = min(cash, buy_multiplier * weekly_deposit, max_buy_multiple * weekly_deposit)
        else:
            target_buy_usd = calm_fraction * weekly_deposit
        return target_buy_usd, 0.0, {"elevated_illiquidity": bool(elevated[t])}

    return decide


CATEGORY = "Sizing / valuation"

# Grid: illiq_lookback(2) x elevated_pct(2) x decay_days(2) x buy_multiplier(2)
#       x calm_fraction(2) = 32 (<=36 cap, 5 tunable params <=5)
GRID = {
    "illiq_lookback": [126, 252],
    "elevated_pct": [90.0, 95.0],
    "decay_days": [5, 10],
    "buy_multiplier": [1.5, 2.0],
    "calm_fraction": [0.85, 0.95],
}
PRIMARY_CONFIG = {
    "illiq_lookback": 252, "elevated_pct": 95.0, "decay_days": 5,
    "buy_multiplier": 2.0, "calm_fraction": 0.90,
}


def grid_configs() -> list[dict]:
    out = []
    for lb in GRID["illiq_lookback"]:
        for ep in GRID["elevated_pct"]:
            for dd in GRID["decay_days"]:
                for bm in GRID["buy_multiplier"]:
                    for cf in GRID["calm_fraction"]:
                        out.append({
                            "illiq_lookback": lb, "elevated_pct": ep, "decay_days": dd,
                            "buy_multiplier": bm, "calm_fraction": cf,
                        })
    return out
