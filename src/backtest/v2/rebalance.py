"""Strategy C: rebalanced BTC/gold/silver portfolio -- spec v2 section 6.

Two layers, deliberately decoupled:
  - TARGET WEIGHTS update on their own schedule (monthly recompute for C2/C3,
    constant for C1, plus C3's month-end trend filter).
  - REBALANCE TRADES (selling overweight sleeves to buy underweight ones)
    fire on whichever trigger the grid row specifies: 5/25 bands, 10/50
    bands, or a quarterly calendar with no band check at all.
Independent of both: every week's fresh deposit is always routed to
whichever sleeve is currently most underweight (spec 6.2) -- this happens
regardless of whether a full rebalance also fires that week.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CASH_SLEEVE = "CASH"


def build_target_weights(
    scheme: str, weekly_closes: dict[str, pd.Series], assets: list[str], index: pd.DatetimeIndex
) -> pd.DataFrame:
    """scheme in {'C1', 'C2', 'C3'}. Returns a DataFrame indexed like `index`
    with one column per asset (+ CASH for C3), summing to 1.0 each row."""
    n = len(index)
    closes = pd.DataFrame({a: weekly_closes[a].reindex(index).ffill() for a in assets})
    log_ret = np.log(closes).diff()
    vol52 = log_ret.rolling(52, min_periods=52).std()
    sma40 = closes.rolling(40, min_periods=40).mean()

    is_month_start = pd.Series(index.month, index=index) != pd.Series(index.month, index=index).shift(1).fillna(-1)
    is_month_start.iloc[0] = True

    cols = assets + ([CASH_SLEEVE] if scheme == "C3" else [])
    weights = pd.DataFrame(index=index, columns=cols, dtype=float)

    if scheme == "C1":
        for a in assets:
            weights[a] = 1.0 / len(assets)
        return weights

    # C2 / C3: inverse-volatility weights, recomputed at the first week of each month
    cur_w = {a: 1.0 / len(assets) for a in assets}
    halved = {a: False for a in assets}  # C3 trend-filter state
    is_month_end = is_month_start.shift(-1).fillna(True).to_numpy()  # week right before next month starts

    for t in range(n):
        if is_month_start.iloc[t]:
            inv_vol = {}
            for a in assets:
                v = vol52[a].iloc[t]
                inv_vol[a] = 1.0 / v if (v and not np.isnan(v) and v > 0) else None
            if all(v is not None for v in inv_vol.values()):
                total = sum(inv_vol.values())
                cur_w = {a: inv_vol[a] / total for a in assets}
            # else: not enough history yet -- keep previous (equal-weight init) weights

        if scheme == "C3" and is_month_end[t]:
            for a in assets:
                below = closes[a].iloc[t] < sma40[a].iloc[t] if not np.isnan(sma40[a].iloc[t]) else False
                halved[a] = bool(below)

        if scheme == "C3":
            eff = {}
            freed = 0.0
            for a in assets:
                w = cur_w[a]
                if halved[a]:
                    eff[a] = w / 2.0
                    freed += w / 2.0
                else:
                    eff[a] = w
            eff[CASH_SLEEVE] = freed
            for c in cols:
                weights.at[index[t], c] = eff[c]
        else:
            for a in assets:
                weights.at[index[t], a] = cur_w[a]

    return weights.astype(float)


def run_portfolio(
    weekly: dict[str, pd.DataFrame],
    assets: list[str],
    weekly_deposit_total: float,
    weekly_rf: pd.Series,
    target_weights: pd.DataFrame,
    trigger_mode: str = "bands_5_25",
    fee: float = 0.001,
) -> pd.DataFrame:
    """trigger_mode in {'bands_5_25', 'bands_10_50', 'calendar_quarterly', 'never'}.
    'never' is used for the fixed-weight-DCA-never-rebalanced benchmark: deposits
    still route to the most-underweight sleeve each week, but no full rebalance
    (sell) ever fires."""
    has_cash_sleeve = CASH_SLEEVE in target_weights.columns
    index = target_weights.index
    n = len(index)
    opens = {a: weekly[a]["Open"].reindex(index).to_numpy() for a in assets}
    closes = {a: weekly[a]["Close"].reindex(index).to_numpy() for a in assets}
    rf = weekly_rf.reindex(index).fillna(0.0).to_numpy()

    if trigger_mode == "bands_5_25":
        abs_band, rel_band = 0.05, 0.25
    elif trigger_mode == "bands_10_50":
        abs_band, rel_band = 0.10, 0.50
    elif trigger_mode in ("calendar_quarterly", "never"):
        abs_band = rel_band = None
    else:
        raise ValueError(trigger_mode)

    month_arr = pd.Series(index.month, index=index)
    quarter_start = (month_arr.isin([1, 4, 7, 10])) & (month_arr != month_arr.shift(1).fillna(-1))
    quarter_start.iloc[0] = True
    quarter_start = quarter_start.to_numpy()

    units = {a: 0.0 for a in assets}
    cash = 0.0
    invested_cum = 0.0

    # pending order for next week's open: dict[asset -> signed usd] (+buy / -sell), computed at end of week t
    pending: dict[str, float] = {}

    V_arr = np.zeros(n)
    deposit_arr = np.zeros(n)
    invested_arr = np.zeros(n)
    cash_arr = np.zeros(n)
    total_value_arr = np.zeros(n)
    fees_arr = np.zeros(n)
    rebalanced_flag = np.zeros(n, dtype=bool)
    weight_hist = {a: np.zeros(n) for a in assets}
    if has_cash_sleeve:
        weight_hist[CASH_SLEEVE] = np.zeros(n)

    for t in range(n):
        # --- fill previous week's orders at this week's open ---
        if t >= 1 and pending:
            fee_paid = 0.0
            # sells first
            for a, amt in pending.items():
                if amt < 0 and a != CASH_SLEEVE:
                    sell_usd = min(-amt, units[a] * opens[a][t])
                    sell_units = sell_usd / opens[a][t] if opens[a][t] > 0 else 0.0
                    sell_units = min(sell_units, units[a])
                    proceeds = sell_units * opens[a][t]
                    fee_amt = proceeds * fee
                    cash += proceeds - fee_amt
                    units[a] -= sell_units
                    fee_paid += fee_amt
            # then buys
            for a, amt in pending.items():
                if amt > 0 and a != CASH_SLEEVE:
                    spend = min(amt, cash)
                    if spend > 0 and opens[a][t] > 0:
                        fee_amt = spend * fee
                        units[a] += (spend - fee_amt) / opens[a][t]
                        cash -= spend
                        fee_paid += fee_amt
            fees_arr[t] = fee_paid
            pending = {}

        # --- value, interest, deposit ---
        cash *= 1.0 + rf[t]
        mv = {a: units[a] * closes[a][t] for a in assets}
        V_t = cash + sum(mv.values())
        cash += weekly_deposit_total
        invested_cum += weekly_deposit_total
        total_after_deposit = cash + sum(mv.values())

        # --- actual weights (sleeves = assets [+ cash sleeve if C3]) ---
        w_target = target_weights.loc[index[t]].to_dict()
        w_actual = {a: mv[a] / total_after_deposit if total_after_deposit > 0 else 0.0 for a in assets}
        if has_cash_sleeve:
            w_actual[CASH_SLEEVE] = cash / total_after_deposit if total_after_deposit > 0 else 0.0

        sleeves = assets + ([CASH_SLEEVE] if has_cash_sleeve else [])
        rel_dev = {}
        abs_dev = {}
        for s in sleeves:
            wt = w_target.get(s, 0.0) or 0.0
            wa = w_actual.get(s, 0.0)
            abs_dev[s] = wa - wt
            rel_dev[s] = (wa - wt) / wt if wt > 1e-9 else (0.0 if abs(wa - wt) < 1e-9 else np.inf)

        breach = False
        if trigger_mode == "never":
            breach = False
        elif trigger_mode == "calendar_quarterly":
            breach = bool(quarter_start[t])
        else:
            breach = any(abs(abs_dev[s]) > abs_band or abs(rel_dev[s]) > rel_band for s in sleeves)

        if breach:
            # full rebalance: target dollar value per sleeve, trade the difference
            new_pending = {}
            for a in assets:
                target_value = w_target.get(a, 0.0) * total_after_deposit
                diff = target_value - mv[a]
                new_pending[a] = diff  # +buy / -sell in dollars
            pending = new_pending
            rebalanced_flag[t] = True
        else:
            # route this week's deposit to the most-underweight sleeve (spec 6.2)
            asset_rel_dev = {a: rel_dev[a] for a in assets}  # never buy INTO the cash sleeve via routing
            target_sleeve = min(asset_rel_dev, key=asset_rel_dev.get)
            pending = {target_sleeve: weekly_deposit_total}

        V_arr[t] = V_t
        deposit_arr[t] = weekly_deposit_total
        invested_arr[t] = invested_cum
        cash_arr[t] = cash
        total_value_arr[t] = total_after_deposit
        for s in sleeves:
            weight_hist[s][t] = w_actual.get(s, 0.0)

    out = pd.DataFrame(
        {
            "V": V_arr, "deposit": deposit_arr, "invested": invested_arr,
            "cash": cash_arr, "total_value": total_value_arr,
            "fees_paid": fees_arr, "rebalanced": rebalanced_flag,
        },
        index=index,
    )
    for s, arr in weight_hist.items():
        out[f"w_{s}"] = arr
    out.attrs["final_units"] = units
    out.attrs["final_cash"] = cash
    return out
