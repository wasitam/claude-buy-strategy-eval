"""Benchmark strategies, all funded with the same total dollars the signal
strategy actually deployed (spec section 5)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .engine import run_backtest


def dca(weekly: pd.DataFrame, total_invested: float, weekly_rf: pd.Series) -> pd.DataFrame:
    """Spread total_invested evenly across every week, buying at that week's open."""
    idx = weekly.index
    n = len(idx)
    per_week = total_invested / n
    opens = weekly["Open"].to_numpy()
    closes = weekly["Close"].to_numpy()
    units = 0.0
    units_arr = np.zeros(n)
    invested_arr = np.zeros(n)
    for t in range(n):
        units += per_week / opens[t]
        units_arr[t] = units
        invested_arr[t] = per_week * (t + 1)
    total_value = units_arr * closes
    nav = total_value / invested_arr
    nav = nav / nav[0] if nav[0] else nav
    return pd.DataFrame(
        {"units": units_arr, "cash": 0.0, "market_value": total_value,
         "total_value": total_value, "invested": invested_arr, "nav": nav},
        index=idx,
    )


def buy_and_hold(weekly: pd.DataFrame, total_invested: float) -> pd.DataFrame:
    """All dollars invested on day one (first week's open)."""
    idx = weekly.index
    n = len(idx)
    price0 = weekly["Open"].iloc[0]
    units = total_invested / price0
    closes = weekly["Close"].to_numpy()
    total_value = units * closes
    invested_arr = np.full(n, total_invested)
    nav = total_value / total_invested
    return pd.DataFrame(
        {"units": units, "cash": 0.0, "market_value": total_value,
         "total_value": total_value, "invested": invested_arr, "nav": nav},
        index=idx,
    )


def buy_only(
    weekly: pd.DataFrame, buy_signal: pd.Series, weekly_rf: pd.Series,
    fee: float = 0.001, buy_amount: float = 500.0,
) -> pd.DataFrame:
    """Same buy rule, no sells at all -- isolates whether the sell rule helps."""
    no_sell = pd.Series(False, index=weekly.index)
    return run_backtest(weekly, buy_signal, no_sell, weekly_rf, fee=fee, buy_amount=buy_amount)


def rebalance_band(
    weekly: pd.DataFrame,
    total_invested: float,
    target_weight: float,
    weekly_rf: pd.Series,
    trigger_band: float = 0.02,
    destination_band: float = 0.0175,
    fee: float = 0.001,
) -> pd.DataFrame:
    """Vanguard-style band rebalancing between the asset and a cash sleeve.

    Deploys the full pool at week 0 (target_weight in the asset, rest in cash),
    then only trades when the asset's weight drifts more than `trigger_band`
    away from target, rebalancing back to the edge of a tighter
    `destination_band` (not all the way to target) -- per the spec's citation
    of Vanguard's band-rebalancing research.
    """
    idx = weekly.index
    n = len(idx)
    opens = weekly["Open"].to_numpy()
    closes = weekly["Close"].to_numpy()
    rf = weekly_rf.reindex(idx).fillna(0.0).to_numpy()

    cash = total_invested * (1 - target_weight)
    units = (total_invested * target_weight) / opens[0]
    # fee on the initial purchase
    units *= (1 - fee)

    units_arr = np.zeros(n)
    cash_arr = np.zeros(n)
    for t in range(n):
        cash *= 1.0 + rf[t]
        mv = units * closes[t]
        weight = mv / (mv + cash) if (mv + cash) > 0 else target_weight
        if weight > target_weight + trigger_band:
            # sell down to target + destination_band
            target_mv = (target_weight + destination_band) * (mv + cash)
            sell_value = mv - target_mv
            if sell_value > 0:
                sell_units = sell_value / closes[t]
                sell_units = min(sell_units, units)
                proceeds = sell_units * closes[t] * (1 - fee)
                units -= sell_units
                cash += proceeds
        elif weight < target_weight - trigger_band:
            target_mv = (target_weight - destination_band) * (mv + cash)
            buy_value = target_mv - mv
            if buy_value > 0:
                buy_value = min(buy_value, cash)
                buy_units = (buy_value * (1 - fee)) / closes[t]
                units += buy_units
                cash -= buy_value
        units_arr[t] = units
        cash_arr[t] = cash

    total_value = units_arr * closes + cash_arr
    invested_arr = np.full(n, total_invested)
    nav = total_value / total_invested
    return pd.DataFrame(
        {"units": units_arr, "cash": cash_arr, "market_value": units_arr * closes,
         "total_value": total_value, "invested": invested_arr, "nav": nav},
        index=idx,
    )
