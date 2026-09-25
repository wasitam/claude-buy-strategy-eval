"""Daily-resolution PORTFOLIO engine (research-loop-plan-v3.md sec 3.2 +
family 002's prereg.md, "shared calendar" judgment call).

Deferred from family 001 (single-asset only) until a portfolio-category
family (family 002, dual momentum rotation) actually needed it -- see family
001's results.md judgment call #2.

Shared calendar: the portfolio's decision calendar is one asset's own daily
trading-day index (the caller passes already-aligned/ffilled per-asset OHLC
frames sharing one DatetimeIndex -- see scripts/v3/run_002_dual_momentum.py
for how that index is built from SP500's own NYSE trading days, per plan sec
3.2's explicit instruction). One pooled cash account (not per-asset), since
deposits and rebalances move money between assets.

Per shared-calendar day t:
  1. Fill yesterday's pending per-asset orders at today's OPEN. Sells across
     ALL assets first, then buys across all assets, in a fixed asset order.
     Buys capped by the single pooled cash balance so cash never goes
     negative; sells capped by each asset's held units so no position goes
     negative.
  2. Credit one day of cash interest on the pooled cash balance. If t is the
     last trading day of its ISO calendar week, credit the pooled weekly
     deposit (weekly_deposit_per_asset * n_assets).
  3. Compute the decision at today's CLOSE using only data through today:
     `decide(t, cash, total_value) -> ({asset: buy_usd}, {asset: sell_usd}, extra)`.
     This becomes tomorrow's pending per-asset orders.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from .engine import week_end_flags


@dataclass
class PortfolioResult:
    index: pd.DatetimeIndex
    asset_names: list
    units: dict          # asset -> np.ndarray
    cash: np.ndarray
    deposit: np.ndarray
    total_value_pre_deposit: np.ndarray  # V_t: cash + sum(units*close) at close of day t, before that day's deposit
    buy_usd: dict         # asset -> np.ndarray
    sell_usd: dict        # asset -> np.ndarray
    fees_paid: np.ndarray
    is_week_end: np.ndarray
    extra: dict = field(default_factory=dict)

    def to_frame(self) -> pd.DataFrame:
        """A single-asset-engine-shaped frame (V, deposit, invested, cash,
        fees_paid, buy_usd, sell_usd, is_week_end) so metrics.summarize_generic
        can consume it without knowing about the multi-asset internals."""
        return pd.DataFrame(
            {
                "cash": self.cash, "deposit": self.deposit,
                "V": self.total_value_pre_deposit,
                "invested": np.cumsum(self.deposit),
                "buy_usd": sum(self.buy_usd.values()),
                "sell_usd": sum(self.sell_usd.values()),
                "fees_paid": self.fees_paid, "is_week_end": self.is_week_end,
            },
            index=self.index,
        )


def run_portfolio(
    assets: dict,  # name -> daily OHLC df, ALL sharing the same DatetimeIndex
    weekly_deposit_per_asset: float,
    daily_rf: pd.Series,
    decide: Callable[[int, float, float, dict], tuple],
    fee: float = 0.001,
) -> PortfolioResult:
    names = list(assets.keys())
    idx = next(iter(assets.values())).index
    for name in names:
        assert assets[name].index.equals(idx), f"asset {name} not on shared calendar"
    n = len(idx)
    n_assets = len(names)
    opens = {a: assets[a]["Open"].to_numpy() for a in names}
    closes = {a: assets[a]["Close"].to_numpy() for a in names}
    rf = daily_rf.reindex(idx).fillna(0.0).to_numpy()
    is_week_end = week_end_flags(idx)

    units = {a: 0.0 for a in names}
    cash = 0.0

    units_arr = {a: np.zeros(n) for a in names}
    cash_arr = np.zeros(n)
    deposit_arr = np.zeros(n)
    V_arr = np.zeros(n)
    buy_arr = {a: np.zeros(n) for a in names}
    sell_arr = {a: np.zeros(n) for a in names}
    fees_arr = np.zeros(n)
    extras = []

    pending_buy_usd = {a: 0.0 for a in names}
    pending_sell_usd = {a: 0.0 for a in names}

    for t in range(n):
        fee_paid = 0.0
        if t >= 1:
            # sells first, across all assets
            for a in names:
                su = pending_sell_usd[a]
                if su > 0 and units[a] > 0:
                    sell_units = min(su / max(opens[a][t], 1e-9), units[a])
                    proceeds = sell_units * opens[a][t]
                    fee_amt = proceeds * fee
                    cash += proceeds - fee_amt
                    units[a] -= sell_units
                    fee_paid += fee_amt
            # then buys, capped by the single pooled cash balance
            for a in names:
                bu = pending_buy_usd[a]
                if bu > 0 and cash > 0:
                    spend = min(bu, cash)
                    fee_amt = spend * fee
                    bought_units = (spend - fee_amt) / max(opens[a][t], 1e-9)
                    units[a] += bought_units
                    cash -= spend
                    fee_paid += fee_amt
            pending_buy_usd = {a: 0.0 for a in names}
            pending_sell_usd = {a: 0.0 for a in names}
        fees_arr[t] = fee_paid

        cash *= 1.0 + rf[t]
        total_pos_value = sum(units[a] * closes[a][t] for a in names)
        V_t = cash + total_pos_value
        deposit_today = weekly_deposit_per_asset * n_assets if is_week_end[t] else 0.0
        cash += deposit_today
        total_value_now = cash + total_pos_value  # includes today's deposit, for the decision

        buy_usd, sell_usd, extra = decide(t, cash, total_value_now, dict(units))
        # normalize/clamp: sells cannot exceed held value, total buys cannot exceed cash
        for a in names:
            buy_usd[a] = max(0.0, buy_usd.get(a, 0.0))
            sell_usd[a] = max(0.0, sell_usd.get(a, 0.0))
        total_buy = sum(buy_usd.values())
        if total_buy > cash and total_buy > 0:
            scale = cash / total_buy
            buy_usd = {a: v * scale for a, v in buy_usd.items()}
        for a in names:
            pending_buy_usd[a] = buy_usd[a]
            pending_sell_usd[a] = sell_usd[a]
            buy_arr[a][t] = buy_usd[a]
            sell_arr[a][t] = sell_usd[a]
            units_arr[a][t] = units[a]
        extras.append(extra)

        cash_arr[t] = cash
        deposit_arr[t] = deposit_today
        V_arr[t] = V_t

    return PortfolioResult(
        index=idx, asset_names=names, units=units_arr, cash=cash_arr,
        deposit=deposit_arr, total_value_pre_deposit=V_arr,
        buy_usd=buy_arr, sell_usd=sell_arr, fees_paid=fees_arr,
        is_week_end=is_week_end, extra={"per_day": extras},
    )


def make_fixed_weight_dca_decider(weekly_deposit_per_asset: float, asset_names: list):
    """Degenerate/benchmark decider: each week, buy exactly that asset's own
    $500 share of the deposit, never sell, never reallocate existing
    holdings -- reproduces fixed-weight 5-asset DCA exactly."""
    def decide(t, cash, total_value, units_now):
        buy_usd = {a: weekly_deposit_per_asset for a in asset_names}
        # only spend what's actually available this step (matches single-asset engine's cap)
        total = sum(buy_usd.values())
        if total > cash and total > 0:
            scale = max(cash, 0.0) / total
            buy_usd = {a: v * scale for a, v in buy_usd.items()}
        sell_usd = {a: 0.0 for a in asset_names}
        return buy_usd, sell_usd, {}
    return decide
