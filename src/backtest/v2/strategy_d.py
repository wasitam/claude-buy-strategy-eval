"""Strategy D: rate-regime switch (spec v2.1 section 15.4). TIGHT -> SmartDCA
(rho=2, m_max=3, sweep on); NOT-TIGHT -> DCA, deploying any reserve built up
during SMART over the next 13 weeks. Never sells.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import strategies as strat


def make_strategy_d_decider(weekly: pd.DataFrame, weekly_deposit: float, regime_tight: np.ndarray | pd.Series):
    """regime_tight: boolean array/Series, True = TIGHT (use SmartDCA this week)."""
    mult = strat.smartdca_multiplier(weekly, rho=2, m_max=3)
    tight = np.asarray(regime_tight, dtype=bool)
    sweep_cap = 26 * weekly_deposit

    state = {"prev_tight": None, "reserve_per_week": 0.0, "reserve_weeks_left": 0}

    def decide(t: int, cash_after_deposit: float):
        is_tight = bool(tight[t]) if t < len(tight) else False

        if is_tight:
            buy_usd = min(weekly_deposit * mult[t], cash_after_deposit)
            excess = (cash_after_deposit - buy_usd) - sweep_cap
            if excess > 0:
                buy_usd += excess
            state["reserve_weeks_left"] = 0  # cancel any pending DCA reserve schedule
            state["prev_tight"] = True
            return buy_usd, 0.0, {"state": "SMART", "mult": mult[t]}

        # NOT-TIGHT -> DCA state
        if state["prev_tight"] is True:
            # just transitioned SMART -> DCA: bank the current idle cash as R0,
            # spread over the next 13 weeks on top of the normal $500/week
            r0 = cash_after_deposit
            state["reserve_per_week"] = r0 / 13.0
            state["reserve_weeks_left"] = 13

        extra = 0.0
        if state["reserve_weeks_left"] > 0:
            extra = state["reserve_per_week"]
            state["reserve_weeks_left"] -= 1
        buy_usd = min(weekly_deposit + extra, cash_after_deposit)
        state["prev_tight"] = False
        return buy_usd, 0.0, {"state": "DCA", "extra": extra}

    return decide


def n_switches(regime_tight: np.ndarray) -> int:
    t = np.asarray(regime_tight, dtype=bool)
    return int(np.sum(t[1:] != t[:-1]))
