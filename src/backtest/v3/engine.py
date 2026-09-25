"""Daily-resolution single-asset engine (research-loop-plan-v3.md sec 3.2).

Calendar: the asset's own daily trading index (NYSE trading days for SP500/
gold/silver/oil futures; BTC/ETH trade every calendar day). Weeks are formed
by grouping the index into ISO week buckets on that same calendar, so
"week's last trading day" is well defined for every asset without forcing a
shared cross-asset calendar (only needed for single-asset tests here; a
portfolio engine sharing one calendar is deferred until a portfolio-category
family is tested -- noted as a scope judgment call in family 001's results).

Per trading day t:
  1. Fill yesterday's pending order at today's OPEN. Sells first, then buys.
     Buys capped by available cash -> cash never negative. Sells capped by
     held units -> units never negative.
  2. If t is the LAST trading day of its calendar week: credit cash interest
     for the day, then credit that week's $500 deposit.
     Otherwise: still credit one day of cash interest (cash earns IRX/252
     every day it sits idle, deposit or not).
  3. Compute the decision at today's CLOSE using only data through today.
     `decide(t, cash) -> (buy_usd, sell_usd, extra)`. This becomes tomorrow's
     pending order.
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
    total_value_pre_deposit: np.ndarray  # V_t: value at close of day t, before any deposit credited that day
    invested: np.ndarray
    buy_usd: np.ndarray
    sell_usd: np.ndarray
    fees_paid: np.ndarray
    is_week_end: np.ndarray
    extra: dict = field(default_factory=dict)

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "units": self.units, "cash": self.cash, "deposit": self.deposit,
                "V": self.total_value_pre_deposit, "invested": self.invested,
                "buy_usd": self.buy_usd, "sell_usd": self.sell_usd,
                "fees_paid": self.fees_paid, "is_week_end": self.is_week_end,
            },
            index=self.index,
        )


def week_end_flags(index: pd.DatetimeIndex) -> np.ndarray:
    """True on the last trading day of each ISO calendar week, on THIS asset's
    own trading-day index."""
    iso_week = pd.Index(index).isocalendar()[["year", "week"]].apply(tuple, axis=1)
    iso_week = np.asarray(iso_week)
    flags = np.zeros(len(index), dtype=bool)
    for i in range(len(index)):
        if i == len(index) - 1 or iso_week[i] != iso_week[i + 1]:
            flags[i] = True
    return flags


def run_single_asset(
    daily: pd.DataFrame,
    weekly_deposit: float,
    daily_rf: pd.Series,
    decide: Callable[[int, float], tuple[float, float, dict]],
    fee: float = 0.001,
) -> EngineResult:
    idx = daily.index
    n = len(idx)
    opens = daily["Open"].to_numpy()
    closes = daily["Close"].to_numpy()
    rf = daily_rf.reindex(idx).fillna(0.0).to_numpy()
    is_week_end = week_end_flags(idx)

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
    extras = []

    pending_buy_usd = 0.0
    pending_sell_units = 0.0

    for t in range(n):
        # (1) fill yesterday's order at today's open: sells first, then buys
        fee_paid = 0.0
        if t >= 1:
            if pending_sell_units > 0 and units > 0:
                sell_units = min(pending_sell_units, units)
                proceeds = sell_units * opens[t]
                fee_amt = proceeds * fee
                cash += proceeds - fee_amt
                units -= sell_units
                fee_paid += fee_amt
            if pending_buy_usd > 0 and cash > 0:
                spend = min(pending_buy_usd, cash)
                fee_amt = spend * fee
                bought_units = (spend - fee_amt) / opens[t]
                units += bought_units
                cash -= spend
                fee_paid += fee_amt
            pending_buy_usd = 0.0
            pending_sell_units = 0.0
        fees_arr[t] = fee_paid

        # (2) daily cash interest, then weekly deposit on the week's last trading day
        cash *= 1.0 + rf[t]
        V_t = cash + units * closes[t]
        deposit_today = weekly_deposit if is_week_end[t] else 0.0
        cash += deposit_today
        invested_cum += deposit_today

        # (3) decide (uses data through today's close only) -> tomorrow's order
        buy_usd, sell_usd, extra = decide(t, cash)
        buy_usd = max(0.0, min(buy_usd, cash))
        sell_usd = max(0.0, sell_usd)
        pending_buy_usd = buy_usd
        pending_sell_units = sell_usd / max(closes[t], 1e-9)
        extras.append(extra)

        units_arr[t] = units
        cash_arr[t] = cash
        deposit_arr[t] = deposit_today
        V_arr[t] = V_t
        invested_arr[t] = invested_cum
        buy_arr[t] = buy_usd
        sell_arr[t] = sell_usd

    return EngineResult(
        index=idx, units=units_arr, cash=cash_arr, deposit=deposit_arr,
        total_value_pre_deposit=V_arr, invested=invested_arr,
        buy_usd=buy_arr, sell_usd=sell_arr, fees_paid=fees_arr,
        is_week_end=is_week_end, extra={"per_day": extras},
    )


def make_dca_decider(weekly_deposit: float):
    """Buy the whole deposit each week's decision day; degenerate baseline."""
    def decide(t, cash):
        return cash, 0.0, {}
    return decide
