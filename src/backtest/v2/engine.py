"""Single-asset weekly event-loop engine (spec v2 section 2.2).

Weekly cycle, for week t:
  1. At close of week t: value the account (V_t, before this week's deposit),
     credit one week of interest on cash, then deposit this week's cash.
  2. Compute signals using data up to and including close of week t only.
  3. Generate an order (buy_usd or sell_usd) for this week.
  4. Fill the PREVIOUS week's order at the open of week t (i.e. an order
     decided at week t-1 fills at week t's open) -- sells first, then buys,
     0.1% fee, buys capped by available cash.

A `decide` callback receives (t, cash_after_deposit, precomputed indicator
values at t) and returns (buy_usd, sell_usd, extra_dict). Indicator series
are precomputed vectorized ahead of time by each strategy module for speed;
only cash-dependent sizing (buy caps, sweeps) happens inside the loop.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd


@dataclass
class EngineResult:
    index: pd.DatetimeIndex
    units: np.ndarray
    cash: np.ndarray
    deposit: np.ndarray
    total_value_pre_deposit: np.ndarray  # V_t, for NAV (spec 8.1)
    invested: np.ndarray  # cumulative deposits
    buy_usd: np.ndarray  # ordered at t, fills at open of t+1
    sell_usd: np.ndarray  # ordered at t, fills at open of t+1
    fees_paid: np.ndarray  # fees paid on fills executed AT this week's open
    fill_buy_usd: np.ndarray  # actual $ spent on buys filled at this week's open
    fill_buy_units: np.ndarray  # actual units received from buys filled at this week's open
    extra: dict = field(default_factory=dict)

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "units": self.units,
                "cash": self.cash,
                "deposit": self.deposit,
                "V": self.total_value_pre_deposit,
                "invested": self.invested,
                "buy_usd": self.buy_usd,
                "sell_usd": self.sell_usd,
                "fees_paid": self.fees_paid,
                "fill_buy_usd": self.fill_buy_usd,
                "fill_buy_units": self.fill_buy_units,
            },
            index=self.index,
        )


def run_single_asset(
    weekly: pd.DataFrame,
    weekly_deposit: float,
    weekly_rf: pd.Series,
    decide: Callable[[int, float], tuple[float, float, dict]],
    fee: float = 0.001,
) -> EngineResult:
    """weekly: DataFrame with Open/Close indexed W-FRI.
    weekly_deposit: $ deposited into the cash account each week.
    weekly_rf: weekly risk-free rate series (already IRX/100/52), aligned to weekly.index.
    decide(t, cash_after_deposit) -> (buy_usd, sell_usd, extra_dict): the order
    to be filled at the NEXT week's open.
    """
    idx = weekly.index
    n = len(idx)
    opens = weekly["Open"].to_numpy()
    closes = weekly["Close"].to_numpy()
    rf = weekly_rf.reindex(idx).fillna(0.0).to_numpy()

    units = 0.0
    cash = 0.0
    invested_cum = 0.0

    units_arr = np.zeros(n)
    cash_arr = np.zeros(n)
    deposit_arr = np.zeros(n)
    V_arr = np.zeros(n)
    invested_arr = np.zeros(n)
    buy_arr = np.zeros(n)
    sell_arr = np.zeros(n)
    fees_arr = np.zeros(n)
    fill_buy_usd_arr = np.zeros(n)
    fill_buy_units_arr = np.zeros(n)
    extras = []

    pending_buy = 0.0
    pending_sell = 0.0

    for t in range(n):
        # --- (4) fill previous week's order at this week's open ---
        if t >= 1:
            fee_paid = 0.0
            if pending_sell > 0 and units > 0:
                sell_units = min(pending_sell, units)
                price = opens[t]
                proceeds = sell_units * price
                fee_amt = proceeds * fee
                cash += proceeds - fee_amt
                units -= sell_units
                fee_paid += fee_amt
            if pending_buy > 0 and cash > 0:
                spend = min(pending_buy, cash)
                price = opens[t]
                fee_amt = spend * fee
                bought_units = (spend - fee_amt) / price
                units += bought_units
                cash -= spend
                fee_paid += fee_amt
                fill_buy_usd_arr[t] = spend
                fill_buy_units_arr[t] = bought_units
            fees_arr[t] = fee_paid
            pending_buy = 0.0
            pending_sell = 0.0

        # --- (1) value account (V_t, pre-deposit), credit interest, deposit ---
        cash *= 1.0 + rf[t]
        V_t = cash + units * closes[t]  # NAV basis: after interest, before deposit
        cash += weekly_deposit
        invested_cum += weekly_deposit

        # --- (2)+(3) compute signal & generate this week's order (fills next week) ---
        buy_usd, sell_usd, extra = decide(t, cash)
        buy_usd = max(0.0, min(buy_usd, cash))  # no borrowing
        sell_usd = max(0.0, sell_usd)
        pending_buy = buy_usd
        pending_sell = sell_usd / max(closes[t], 1e-9)  # convert to units for next week's fill
        extras.append(extra)

        units_arr[t] = units
        cash_arr[t] = cash
        deposit_arr[t] = weekly_deposit
        V_arr[t] = V_t
        invested_arr[t] = invested_cum
        buy_arr[t] = buy_usd
        sell_arr[t] = sell_usd

    return EngineResult(
        index=idx, units=units_arr, cash=cash_arr, deposit=deposit_arr,
        total_value_pre_deposit=V_arr, invested=invested_arr,
        buy_usd=buy_arr, sell_usd=sell_arr, fees_paid=fees_arr,
        fill_buy_usd=fill_buy_usd_arr, fill_buy_units=fill_buy_units_arr,
        extra={"per_week": extras},
    )
