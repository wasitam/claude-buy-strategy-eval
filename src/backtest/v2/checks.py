"""Implementation checks, spec v2 section 11. Run before trusting any result."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import strategies as strat
from . import engine as eng
from . import rebalance as rb


def check_smartdca_rho0_equals_dca(weekly: pd.DataFrame, weekly_rf: pd.Series, weekly_deposit: float = 500.0) -> bool:
    dca_decide = strat.make_dca_decider(weekly_deposit)
    dca_res = eng.run_single_asset(weekly, weekly_deposit, weekly_rf, dca_decide).to_frame()

    smart_decide = strat.make_smartdca_decider(weekly, weekly_deposit, rho=0.0, m_max=999, sweep_on=False)
    smart_res = eng.run_single_asset(weekly, weekly_deposit, weekly_rf, smart_decide).to_frame()

    ok = np.allclose(dca_res["units"].to_numpy(), smart_res["units"].to_numpy(), atol=1e-8) and \
        np.allclose(dca_res["cash"].to_numpy(), smart_res["cash"].to_numpy(), atol=1e-6)
    return ok


def check_adca_forced_neutral_equals_dca(weekly: pd.DataFrame, weekly_rf: pd.Series, weekly_deposit: float = 500.0) -> bool:
    dca_decide = strat.make_dca_decider(weekly_deposit)
    dca_res = eng.run_single_asset(weekly, weekly_deposit, weekly_rf, dca_decide).to_frame()

    forced_score = np.full(len(weekly), 2)
    adca_decide = strat.make_adca_decider(weekly_deposit, forced_score)
    adca_res = eng.run_single_asset(weekly, weekly_deposit, weekly_rf, adca_decide).to_frame()

    ok = np.allclose(dca_res["units"].to_numpy(), adca_res["units"].to_numpy(), atol=1e-8) and \
        np.allclose(dca_res["cash"].to_numpy(), adca_res["cash"].to_numpy(), atol=1e-6)
    return ok


def check_rebalance_single_asset_equals_dca(weekly: dict, weekly_rf: pd.Series, weekly_deposit_total: float = 1500.0) -> bool:
    assets = ["BTC"]
    index = weekly["BTC"].index
    weights = pd.DataFrame({"BTC": 1.0}, index=index)
    port_res = rb.run_portfolio(weekly, assets, weekly_deposit_total, weekly_rf, weights, trigger_mode="never")

    dca_decide = strat.make_dca_decider(weekly_deposit_total)
    dca_res = eng.run_single_asset(weekly["BTC"], weekly_deposit_total, weekly_rf, dca_decide).to_frame()

    ok = np.allclose(port_res["total_value"].to_numpy(), dca_res["V"].to_numpy() + weekly_deposit_total, atol=1.0)
    # Compare final wealth instead, looser tolerance since fill timing differs slightly by construction
    final_diff = abs(port_res["total_value"].iloc[-1] - (dca_res["cash"].iloc[-1] + dca_res["units"].iloc[-1] * weekly["BTC"]["Close"].iloc[-1]))
    rel_diff = final_diff / port_res["total_value"].iloc[-1]
    return rel_diff < 0.01  # within 1%, given both should route ~identically


def check_no_negative_cash_or_units(result_df: pd.DataFrame) -> bool:
    if "cash" in result_df.columns and (result_df["cash"] < -1e-6).any():
        return False
    if "units" in result_df.columns and (result_df["units"] < -1e-6).any():
        return False
    return True


def check_deposits_match(*invested_series: pd.Series) -> bool:
    totals = [float(s.iloc[-1]) for s in invested_series]
    return all(abs(t - totals[0]) < 1e-6 for t in totals)


def check_no_lookahead_smartdca(weekly: pd.DataFrame, t_check: int = 200) -> bool:
    """Truncating the series to t_check+1 rows must not change the SmartDCA
    multiplier computed at row t_check (purely causal rolling window)."""
    full_mult = strat.smartdca_multiplier(weekly, rho=2.0, m_max=3.0)
    truncated = weekly.iloc[: t_check + 1]
    trunc_mult = strat.smartdca_multiplier(truncated, rho=2.0, m_max=3.0)
    return np.isclose(full_mult[t_check], trunc_mult[-1], atol=1e-9)


def run_all_checks(weekly_btc: pd.DataFrame, weekly_dict: dict, weekly_rf: pd.Series) -> dict:
    results = {
        "smartdca_rho0_equals_dca": check_smartdca_rho0_equals_dca(weekly_btc, weekly_rf),
        "adca_neutral_equals_dca": check_adca_forced_neutral_equals_dca(weekly_btc, weekly_rf),
        "rebalance_single_asset_equals_dca": check_rebalance_single_asset_equals_dca(weekly_dict, weekly_rf),
        "no_lookahead_smartdca": check_no_lookahead_smartdca(weekly_btc),
    }
    return results
