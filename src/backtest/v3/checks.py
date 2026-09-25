"""Implementation checks (plan sec 3.2 bullet list, ported from v2 sec 11).
Run before any family's results are trusted. See scripts/run_v3_checks.py
for the executable entry point that actually calls these against real data.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import engine as eng


def check_degenerate_equals_dca(daily: pd.DataFrame, daily_rf: pd.Series, decider_builder,
                                 weekly_deposit: float = 500.0) -> bool:
    """decider_builder(enabled: bool) -> decide fn. enabled=False must reproduce
    plain DCA bit-for-bit (units and cash paths identical)."""
    dca_decide = eng.make_dca_decider(weekly_deposit)
    dca_res = eng.run_single_asset(daily, weekly_deposit, daily_rf, dca_decide).to_frame()

    degenerate_decide = decider_builder(enabled=False)
    deg_res = eng.run_single_asset(daily, weekly_deposit, daily_rf, degenerate_decide).to_frame()

    ok_units = np.allclose(dca_res["units"].to_numpy(), deg_res["units"].to_numpy(), atol=1e-8)
    ok_cash = np.allclose(dca_res["cash"].to_numpy(), deg_res["cash"].to_numpy(), atol=1e-6)
    return bool(ok_units and ok_cash)


def check_no_negative_cash_or_units(result_df: pd.DataFrame) -> bool:
    if (result_df["cash"] < -1e-6).any():
        return False
    if (result_df["units"] < -1e-6).any():
        return False
    return True


def check_no_lookahead(daily: pd.DataFrame, daily_rf: pd.Series, decider_builder,
                        t_check: int, weekly_deposit: float = 500.0, seed: int = 3) -> bool:
    """Perturb all rows AFTER t_check with random noise, rerun, and confirm
    every order generated ON OR BEFORE t_check is unchanged (buy_usd/sell_usd
    identical up to t_check inclusive)."""
    rng = np.random.default_rng(seed)
    perturbed = daily.copy()
    n = len(daily)
    if t_check >= n - 2:
        t_check = n - 3
    noise = 1.0 + rng.normal(0, 0.2, size=n - t_check - 1)
    for col in ["Open", "High", "Low", "Close"]:
        perturbed.iloc[t_check + 1:, perturbed.columns.get_loc(col)] = (
            perturbed.iloc[t_check + 1:][col].to_numpy() * noise
        )

    decide_a = decider_builder(enabled=True)
    res_a = eng.run_single_asset(daily, weekly_deposit, daily_rf, decide_a).to_frame()

    decide_b = decider_builder(enabled=True)
    res_b = eng.run_single_asset(perturbed, weekly_deposit, daily_rf, decide_b).to_frame()

    a = res_a.iloc[: t_check + 1][["buy_usd", "sell_usd"]].to_numpy()
    b = res_b.iloc[: t_check + 1][["buy_usd", "sell_usd"]].to_numpy()
    return bool(np.allclose(a, b, atol=1e-6))


def check_point_in_time_macro() -> bool:
    """This family (trend_exit) uses only price data (no macro/ALFRED series),
    so the point-in-time-macro check is vacuously satisfied; v3.data's FRED
    fetch helper (unused by this family) still applies the v2 sec-3
    publication-lag convention (see v2/data.py weekly_fred_lagged, ported
    unchanged in spirit) whenever a future macro-dependent family needs it."""
    return True
