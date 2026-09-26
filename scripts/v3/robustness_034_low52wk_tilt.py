"""Robustness diagnostics for family 034's primary configuration (plan sec
4.3). Modeled directly on scripts/v3/robustness_020_high52wk_tilt.py (same
single-asset, continuous-sizing-multiplier pattern): rolling windows (3y/5y
for SP500/GOLD/SILVER/OIL, 2y for BTC), block bootstrap raw+detrended, and
placebo circular-shift -- at the n_sims=60 time-budget declared in
prereg.md, run only if sec 4.1 passes.

Placebo signal here is the strategy's own sizing multiplier m_t (a step
function of prox_low_t = low52_t/close_t, per prereg.md) -- circular-
shifting m_t and rerunning tests whether the specific temporal alignment of
the 52-week-low proximity signal (not just "some correlated step-function
multiplier sequence") is doing the work.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, robustness as v3rob, metrics as v3met
from src.backtest.v3.strategies import low52wk_tilt as l52

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAM_DIR = os.path.join(ROOT, "families", "034-52wk-low-tilt")
WEEKLY_DEPOSIT = 500.0
FEE = 0.001
ASSETS_WINDOWS = {"SP500": [3, 5], "GOLD": [3, 5], "SILVER": [3, 5], "OIL": [3, 5], "BTC": [2]}
N_SIMS = 60


def strat_builder(daily):
    return l52.make_low52wk_tilt_decider(daily, WEEKLY_DEPOSIT, **l52.PRIMARY_CONFIG)


def bench_builder(daily):
    return v3eng.make_dca_decider(WEEKLY_DEPOSIT)


def main():
    dev = v3data.load_dev()
    rf = dev["rf"]
    out = {"rolling_windows": {}, "bootstrap": {}, "placebo": {}}

    # --- rolling windows ---
    total_windows = 0
    beat_wealth = 0
    beat_sharpe = 0
    for asset, years_list in ASSETS_WINDOWS.items():
        daily = dev["prices"][asset]
        for yrs in years_list:
            df = v3rob.rolling_windows(daily, rf, WEEKLY_DEPOSIT, strat_builder, bench_builder, window_years=yrs, step_days=20, fee=FEE)
            if len(df) == 0:
                continue
            total_windows += len(df)
            beat_wealth += int(df["beats_wealth"].sum())
            beat_sharpe += int(df["beats_sharpe"].sum())
            out["rolling_windows"][f"{asset}_{yrs}y"] = {
                "n_windows": len(df),
                "pct_beats_wealth": float(df["beats_wealth"].mean()),
                "pct_beats_sharpe": float(df["beats_sharpe"].mean()),
            }
            print(f"rolling {asset} {yrs}y: n={len(df)} beat_wealth={df['beats_wealth'].mean():.2%} beat_sharpe={df['beats_sharpe'].mean():.2%}")
    out["rolling_windows"]["_overall"] = {
        "n_windows": total_windows,
        "pct_beats_wealth": beat_wealth / total_windows if total_windows else float("nan"),
        "pct_beats_sharpe": beat_sharpe / total_windows if total_windows else float("nan"),
    }

    # --- block bootstrap (raw + detrended), n_sims=60 time-budget, one representative asset: SP500 ---
    daily = dev["prices"]["SP500"]
    for detrend in [False, True]:
        df = v3rob.block_bootstrap(daily, rf, WEEKLY_DEPOSIT, strat_builder, bench_builder,
                                    n_sims=N_SIMS, block_weeks=4, detrend=detrend, fee=FEE)
        beats_wealth_maj = float((df["strat_wealth_over_invested"] > df["bench_wealth_over_invested"]).mean())
        beats_sharpe_maj = float((df["strat_sharpe"] > df["bench_sharpe"]).mean())
        key = "detrended" if detrend else "raw"
        out["bootstrap"][key] = {"n_sims": N_SIMS, "pct_beats_wealth": beats_wealth_maj, "pct_beats_sharpe": beats_sharpe_maj}
        print(f"bootstrap {key}: beats_wealth={beats_wealth_maj:.2%} beats_sharpe={beats_sharpe_maj:.2%}")

    # --- placebo: circular-shift the primary config's own sizing multiplier m_t, SP500 ---
    signal_raw = l52.compute_multiplier(daily, l52.PRIMARY_CONFIG["window_def"], l52.PRIMARY_CONFIG["ladder"],
                                         l52.PRIMARY_CONFIG["mult_near"], l52.PRIMARY_CONFIG["max_lump_cap"])

    decide_real = strat_builder(daily)
    res_real = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_real, fee=FEE).to_frame()
    s_real = v3met.summarize(res_real, rf, daily["Close"].iloc[-1])

    def strategy_decide_from_signal(shifted_signal):
        def decide(t, cash):
            return WEEKLY_DEPOSIT * float(shifted_signal[t]), 0.0, {}
        return decide

    df_pl, pct_w, pct_s = v3rob.placebo_circular_shift(
        daily, rf, WEEKLY_DEPOSIT, signal_raw, strategy_decide_from_signal, bench_builder,
        s_real["wealth_over_invested"], s_real["sharpe"], n_sims=N_SIMS, fee=FEE,
    )
    out["placebo"] = {"n_sims": N_SIMS, "real_wealth_over_invested": s_real["wealth_over_invested"],
                       "real_sharpe": s_real["sharpe"], "percentile_wealth": pct_w, "percentile_sharpe": pct_s}
    print(f"placebo: real percentile wealth={pct_w:.1f} sharpe={pct_s:.1f}")

    with open(os.path.join(FAM_DIR, "_robustness_output.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)
    print("done")


if __name__ == "__main__":
    main()
