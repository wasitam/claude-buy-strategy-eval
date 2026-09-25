"""Core weekly backtest engine.

Mechanics (spec section 2):
- Buy $500 of the asset when a buy signal fired the PREVIOUS week (fills at
  this week's open -- never the signal week itself, no lookahead).
- Sell 30% of current unit holdings (not 30% of portfolio $) when a sell
  signal fired the previous week.
- 0.1% fee per trade (buy or sell), taken out of the traded notional.
- Cash raised from sells earns the risk-free rate instead of sitting idle or
  funding future buys.
- Starts from zero holdings, zero cash.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def run_backtest(
    weekly: pd.DataFrame,
    buy_signal: pd.Series,
    sell_signal: pd.Series,
    weekly_rf: pd.Series,
    fee: float = 0.001,
    buy_amount: float = 500.0,
    sell_frac: float = 0.30,
) -> pd.DataFrame:
    idx = weekly.index
    n = len(idx)
    rf = weekly_rf.reindex(idx).fillna(0.0).to_numpy()
    opens = weekly["Open"].to_numpy()
    closes = weekly["Close"].to_numpy()
    buy_prev = buy_signal.reindex(idx).fillna(False).to_numpy()
    sell_prev = sell_signal.reindex(idx).fillna(False).to_numpy()

    units = 0.0
    cash = 0.0
    invested = 0.0
    n_buys = 0
    n_sells = 0

    units_arr = np.zeros(n)
    cash_arr = np.zeros(n)
    invested_arr = np.zeros(n)
    flow_arr = np.zeros(n)  # external new money added this week (buys only)
    trade_arr = np.array([""] * n, dtype=object)

    for t in range(n):
        # cash earns the risk-free rate each week
        cash *= 1.0 + rf[t]

        flow = 0.0
        trade_note = []
        if t >= 1:
            if buy_prev[t - 1] and not np.isnan(opens[t]):
                price = opens[t]
                fee_amt = buy_amount * fee
                net = buy_amount - fee_amt
                units += net / price
                invested += buy_amount
                flow += buy_amount
                n_buys += 1
                trade_note.append("BUY")
            if sell_prev[t - 1] and units > 0 and not np.isnan(opens[t]):
                price = opens[t]
                sell_units = units * sell_frac
                proceeds = sell_units * price
                fee_amt = proceeds * fee
                cash += proceeds - fee_amt
                units -= sell_units
                n_sells += 1
                trade_note.append("SELL")

        units_arr[t] = units
        cash_arr[t] = cash
        invested_arr[t] = invested
        flow_arr[t] = flow
        trade_arr[t] = "+".join(trade_note)

    market_value = units_arr * closes
    total_value = market_value + cash_arr

    # Synthetic NAV / unit-price series: strip out the effect of new external
    # deposits (buys) so drawdown reflects real investment performance, not
    # new money arriving. Sells are internal (units -> cash) and are NOT
    # treated as external flows.
    nav = np.ones(n)
    for t in range(1, n):
        prev_v = total_value[t - 1]
        v = total_value[t]
        f = flow_arr[t]
        if prev_v > 1e-9:
            r = (v - f) / prev_v - 1.0
        else:
            r = 0.0
        nav[t] = nav[t - 1] * (1.0 + r)

    out = pd.DataFrame(
        {
            "units": units_arr,
            "cash": cash_arr,
            "market_value": market_value,
            "total_value": total_value,
            "invested": invested_arr,
            "flow": flow_arr,
            "nav": nav,
            "trade": trade_arr,
        },
        index=idx,
    )
    out.attrs["n_buys"] = n_buys
    out.attrs["n_sells"] = n_sells
    return out
