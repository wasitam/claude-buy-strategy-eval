"""Robustness diagnostics for family 001's primary configuration (plan sec 4.3).
Since the primary config already fails sec 4.1 (1/5 assets beat DCA, needs
>=3/5), this is diagnostic-only, run at REDUCED simulation counts (documented
judgment call, same scoping precedent as v2/robustness.py's own docstring:
"Given the size of this project's grid, this module runs a reduced
simulation count... consistent with how v1's robustness suite was scoped.")
n_sims=120 instead of the plan's 500, given SP500's 92-year daily history
makes each simulation ~1.9s (500 sims x 2 variants x 5 assets would run
>1hr). Rolling windows use the full window counts (cheap: short windows).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.backtest.v3 import data as v3data, engine as v3eng, robustness as v3rob
from src.backtest.v3.strategies import trend_exit as te

ROOT = os.path.dirname(os.path.abspath(__file__))
FAM_DIR = os.path.join(ROOT, "families", "001-trend-exit")
WEEKLY_DEPOSIT = 500.0
FEE = 0.001
ASSETS_WINDOWS = {"SP500": [3, 5], "GOLD": [3, 5], "SILVER": [3, 5], "OIL": [3, 5], "BTC": [2]}
N_SIMS = 120


def strat_builder(daily):
    return te.make_trend_exit_decider(daily, WEEKLY_DEPOSIT, **te.PRIMARY_CONFIG)


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

    # --- block bootstrap (raw + detrended), reduced n_sims, one representative asset: SP500 ---
    daily = dev["prices"]["SP500"]
    for detrend in [False, True]:
        df = v3rob.block_bootstrap(daily, rf, WEEKLY_DEPOSIT, strat_builder, bench_builder,
                                    n_sims=N_SIMS, block_weeks=4, detrend=detrend, fee=FEE)
        beats_wealth_maj = float((df["strat_wealth_over_invested"] > df["bench_wealth_over_invested"]).mean())
        beats_sharpe_maj = float((df["strat_sharpe"] > df["bench_sharpe"]).mean())
        key = "detrended" if detrend else "raw"
        out["bootstrap"][key] = {"n_sims": N_SIMS, "pct_beats_wealth": beats_wealth_maj, "pct_beats_sharpe": beats_sharpe_maj}
        print(f"bootstrap {key}: beats_wealth={beats_wealth_maj:.2%} beats_sharpe={beats_sharpe_maj:.2%}")

    # --- placebo circular shift on the SMA-distance signal, SP500 ---
    sma = pd.Series(daily["Close"]).rolling(te.PRIMARY_CONFIG["sma_days"], min_periods=te.PRIMARY_CONFIG["sma_days"]).mean()
    signal_raw = (daily["Close"].to_numpy() - sma.fillna(daily["Close"]).to_numpy())

    decide_real = strat_builder(daily)
    res_real = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_real, fee=FEE).to_frame()
    from src.backtest.v3 import metrics as v3met
    s_real = v3met.summarize(res_real, rf, daily["Close"].iloc[-1])

    def strategy_decide_from_signal(shifted_signal):
        above = shifted_signal > 0

        def decide(t, cash):
            buy_usd = cash if above[t] else 0.0
            return buy_usd, 0.0, {}
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
