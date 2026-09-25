"""Family 023: Realized-skewness sizing (Neuberger 2012; Amaya, Christoffersen,
Jacobs & Vasquez 2015).

families/023-realized-skewness/prereg.md has the full mechanism, rules and
the required triple distinction from families 003/016/017. Summary:
RSkew_t = sqrt(skew_window) * sum(r_i^3) / (sum(r_i^2))^1.5 over the
trailing `skew_window` daily returns (Neuberger/Amaya et al.'s realized-
skewness formula -- an un-demeaned, scale-invariant third-moment
statistic). Deposits are sized UP (buy_multiplier * weekly_deposit,
cash-capped) on a week-end decision day where RSkew_t < neg_threshold
(negative-skew regime, elevated crash-risk premium), sized DOWN
(reduce_fraction * weekly_deposit, banking the remainder) where
RSkew_t > pos_threshold (positive-skew regime), and left at plain DCA
otherwise (neutral). No sells, ever; no leverage; cash never goes
negative. Same weekly-decision-cadence pattern as families 003/016/021.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import engine as eng


def compute_realized_skewness(daily: pd.DataFrame, skew_window: int) -> np.ndarray:
    """Causal trailing realized skewness (Neuberger 2012; Amaya et al. 2015):
    RSkew_t = sqrt(skew_window) * sum(r_i^3, i in trailing window incl. t) /
              (sum(r_i^2, i in trailing window incl. t))^1.5
    NaN until `skew_window` trading days of return history exist (warm-up),
    and on the negligible-probability all-zero-return-window case."""
    close = daily["Close"].to_numpy()
    r = np.empty(len(close))
    r[0] = np.nan
    r[1:] = close[1:] / close[:-1] - 1.0
    r_series = pd.Series(r)

    sum_r3 = r_series.pow(3).rolling(skew_window, min_periods=skew_window).sum()
    sum_r2 = r_series.pow(2).rolling(skew_window, min_periods=skew_window).sum()

    with np.errstate(divide="ignore", invalid="ignore"):
        rskew = np.sqrt(skew_window) * sum_r3.to_numpy() / np.power(sum_r2.to_numpy(), 1.5)
    bad = ~np.isfinite(sum_r2.to_numpy()) | (sum_r2.to_numpy() <= 0.0)
    rskew = np.where(bad, np.nan, rskew)
    return rskew


def compute_regime(daily: pd.DataFrame, skew_window: int, neg_threshold: float,
                    pos_threshold: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Returns (rskew, negative_regime, positive_regime) boolean/float arrays
    aligned to daily.index. A day with undefined RSkew_t (warm-up) is
    neither negative nor positive (neutral by default -- plain DCA that
    week), matching families 001/011/015/016/021's warm-up convention."""
    rskew = compute_realized_skewness(daily, skew_window)
    defined = np.isfinite(rskew)
    negative = defined & (rskew < neg_threshold)
    positive = defined & (rskew > pos_threshold)
    return rskew, negative, positive


def make_realized_skewness_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    skew_window: int = 90, neg_threshold: float = -0.5, pos_threshold: float = 0.5,
    buy_multiplier: float = 2.0, reduce_fraction: float = 0.85,
    max_buy_multiple: float = 4.0,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the skewness/threshold computation
    entirely and buys the full week's cash every week-end day (0
    otherwise), which is bit-for-bit plain DCA."""
    is_week_end = eng.week_end_flags(daily.index)
    if enabled:
        _, negative, positive = compute_regime(daily, skew_window, neg_threshold, pos_threshold)
    else:
        negative = positive = None

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if negative[t]:
            target_buy_usd = min(cash, buy_multiplier * weekly_deposit, max_buy_multiple * weekly_deposit)
            info = {"skew_regime": "negative"}
        elif positive[t]:
            target_buy_usd = min(cash, reduce_fraction * weekly_deposit)
            info = {"skew_regime": "positive"}
        else:
            target_buy_usd = min(cash, weekly_deposit)
            info = {"skew_regime": "neutral"}
        return target_buy_usd, 0.0, info

    return decide


def make_decider_from_regime_arrays(
    daily: pd.DataFrame, weekly_deposit: float, negative: np.ndarray, positive: np.ndarray,
    buy_multiplier: float = 2.0, reduce_fraction: float = 0.85,
    max_buy_multiple: float = 4.0,
):
    """Same weekly decision rule as make_realized_skewness_decider, but
    driven by arbitrary pre-computed `negative`/`positive` boolean arrays --
    used by the placebo circular-shift robustness test (sec 4.3), which
    shifts the regime's TIMING while keeping its overall negative/positive/
    neutral frequency identical. Mirrors family 021's own placebo helper."""
    is_week_end = eng.week_end_flags(daily.index)

    def decide(t, cash):
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        if negative[t]:
            target_buy_usd = min(cash, buy_multiplier * weekly_deposit, max_buy_multiple * weekly_deposit)
        elif positive[t]:
            target_buy_usd = min(cash, reduce_fraction * weekly_deposit)
        else:
            target_buy_usd = min(cash, weekly_deposit)
        return target_buy_usd, 0.0, {}

    return decide


CATEGORY = "Sizing / valuation"

# Grid: skew_window(2) x neg_threshold(2) x pos_threshold(2) x buy_multiplier(2)
#       x reduce_fraction(2) = 32 (<=36 cap, 5 tunable params <=5)
GRID = {
    "skew_window": [60, 90],
    "neg_threshold": [-0.5, -0.25],
    "pos_threshold": [0.25, 0.5],
    "buy_multiplier": [1.5, 2.0],
    "reduce_fraction": [0.85, 0.95],
}
PRIMARY_CONFIG = {
    "skew_window": 90, "neg_threshold": -0.5, "pos_threshold": 0.5,
    "buy_multiplier": 2.0, "reduce_fraction": 0.85,
}

# Pre-backtest verification (family 021's lesson): every PRIMARY_CONFIG
# value must actually be a member of its GRID list, checked at import time.
for _k, _v in PRIMARY_CONFIG.items():
    assert _v in GRID[_k], f"PRIMARY_CONFIG[{_k}]={_v!r} not in GRID[{_k}]={GRID[_k]!r}"


def grid_configs() -> list[dict]:
    out = []
    for sw in GRID["skew_window"]:
        for nt in GRID["neg_threshold"]:
            for pt in GRID["pos_threshold"]:
                for bm in GRID["buy_multiplier"]:
                    for rf in GRID["reduce_fraction"]:
                        out.append({
                            "skew_window": sw, "neg_threshold": nt, "pos_threshold": pt,
                            "buy_multiplier": bm, "reduce_fraction": rf,
                        })
    return out


assert PRIMARY_CONFIG in grid_configs(), "PRIMARY_CONFIG is not a member of grid_configs()"
