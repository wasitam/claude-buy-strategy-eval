"""Sec 4.3 robustness checks for family 004 (value averaging), primary
config, single-asset. Run to completion (not stopped early) because the
primary config PASSES sec 4.1 (3/5 core assets at both fee levels) -- per
the task's own instruction and the family 002 precedent
(families/002-dual-momentum/results.md), a family that clears sec 4.1 gets
the full sec 4.3 suite even though sec 4.2/4.4 already fail, since that is
exactly when the robustness picture matters most for an honest report.

Run counts scoped down from the plan's 500, same judgment-call precedent as
families 001 and 002 (state/bugfix_log.md; family 001's docstring): n_sims=60
per bootstrap/detrend variant and per placebo run, matching family 002's own
reduced count (60), since SP500's ~96-year daily history makes each
full-history single-asset simulation multi-second and 500 sims x several
variants would be prohibitively slow for this iteration.

Placebo signal: VA's real per-DAY net order series (buy_usd - sell_usd from
the primary config's real SP500 run, nonzero only on week-end decision days)
is circular-shifted and replayed as an open-loop daily order schedule (still
capped by real cash on hand each day, so no leverage is ever possible even
in the shuffled placebo). This tests whether the SPECIFIC weeks VA chose to
buy extra / sell (its path-following timing) carry the edge, versus the same
multiset of order sizes landing on arbitrary days.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, robustness as v3rob, metrics as v3met
from src.backtest.v3.strategies import value_averaging as va

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAM_DIR = os.path.join(ROOT, "families", "004-value-averaging")
WEEKLY_DEPOSIT = 500.0
FEE = 0.001
ASSETS_WINDOWS = {"SP500": [3, 5], "GOLD": [3, 5], "SILVER": [3, 5], "OIL": [3, 5], "BTC": [2]}
N_SIMS = 60


def strat_builder(daily):
    return va.make_value_averaging_decider(daily, WEEKLY_DEPOSIT, fee=FEE, **va.PRIMARY_CONFIG)


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

    # --- block bootstrap (raw + detrended), reduced n_sims, representative asset: SP500 ---
    daily = dev["prices"]["SP500"]
    for detrend in [False, True]:
        df = v3rob.block_bootstrap(daily, rf, WEEKLY_DEPOSIT, strat_builder, bench_builder,
                                    n_sims=N_SIMS, block_weeks=4, detrend=detrend, fee=FEE)
        beats_wealth_maj = float((df["strat_wealth_over_invested"] > df["bench_wealth_over_invested"]).mean())
        beats_sharpe_maj = float((df["strat_sharpe"] > df["bench_sharpe"]).mean())
        key = "detrended" if detrend else "raw"
        out["bootstrap"][key] = {"n_sims": N_SIMS, "pct_beats_wealth": beats_wealth_maj, "pct_beats_sharpe": beats_sharpe_maj}
        print(f"bootstrap {key}: beats_wealth={beats_wealth_maj:.2%} beats_sharpe={beats_sharpe_maj:.2%}")

    # --- placebo circular shift on the real net-order-per-day series, SP500 ---
    decide_real = strat_builder(daily)
    res_real = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_real, fee=FEE).to_frame()
    s_real = v3met.summarize(res_real, rf, daily["Close"].iloc[-1])
    signal_raw = (res_real["buy_usd"] - res_real["sell_usd"]).to_numpy()

    def strategy_decide_from_signal(shifted_signal):
        def decide(t, cash):
            o = float(shifted_signal[t])
            if o > 0:
                return min(o, max(cash, 0.0)), 0.0, {}
            elif o < 0:
                return 0.0, -o, {}
            return 0.0, 0.0, {}
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
