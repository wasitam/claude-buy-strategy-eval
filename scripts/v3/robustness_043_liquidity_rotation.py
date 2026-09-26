"""Sec 4.3 robustness checks for family 043 (Amihud-illiquidity cross-asset
rotation), primary config, portfolio-level. Run ONLY because sec 4.1
passed on the primary config (see _run_output.json) -- established loop
precedent. Counts scoped down from the plan's 500 per prereg.md's
cost-scoping judgment call (60 sims for bootstrap/placebo, matching
families 001/002/013/029's convention).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, metrics as v3met
from src.backtest.v3 import portfolio_engine as v3pe
from src.backtest.v3 import portfolio_robustness as v3prob
from src.backtest.v3.engine import week_end_flags
from src.backtest.v3.strategies import liquidity_rotation as lr

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAM_DIR = os.path.join(ROOT, "families", "043-liquidity-rotation")
WEEKLY_DEPOSIT_PER_ASSET = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]
N_SIMS = 60


def build_shared_calendar(dev):
    prices = dev["prices"]
    start = max(df.index.min() for df in prices.values())
    idx = prices["SP500"].index
    idx = idx[idx >= start]
    aligned = {a: prices[a].reindex(idx).ffill().bfill() for a in ASSETS}
    return idx, aligned


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    idx, aligned = build_shared_calendar(dev)
    daily_rf = dev["rf"].reindex(idx).ffill().fillna(0.0)
    closes = {a: aligned[a]["Close"].to_numpy() for a in ASSETS}
    is_week_end = week_end_flags(idx)

    def s_builder(aw, iw):
        we = week_end_flags(iw)
        return lr.make_liquidity_rotation_decider(aw, iw, we, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **lr.PRIMARY_CONFIG, enabled=True)

    def b_builder(aw, iw):
        return v3pe.make_fixed_weight_dca_decider(WEEKLY_DEPOSIT_PER_ASSET, ASSETS)

    # --- sec 4.3 rolling windows: 3-year (BTC-gated dev history is only
    # ~5.3 years total, same constraint family 002 hit) ---
    print("Rolling windows (3y, step 20 trading days)...")
    rw3 = v3prob.rolling_windows_portfolio(aligned, daily_rf, WEEKLY_DEPOSIT_PER_ASSET, s_builder, b_builder,
                                            window_years=3, step_days=20, fee=0.001)
    print(f"  n windows={len(rw3)}, beats_wealth={rw3['beats_wealth'].mean():.3f}, beats_sharpe={rw3['beats_sharpe'].mean():.3f}")

    # --- sec 4.3 block bootstrap (shared blocks across assets), raw + detrended ---
    print(f"Block bootstrap raw ({N_SIMS} sims)...")
    bs_raw = v3prob.block_bootstrap_portfolio(aligned, daily_rf, WEEKLY_DEPOSIT_PER_ASSET, s_builder, b_builder,
                                               n_sims=N_SIMS, block_weeks=4, detrend=False, fee=0.001)
    bs_raw["beats_wealth"] = bs_raw["strat_wealth_over_invested"] > bs_raw["bench_wealth_over_invested"]
    bs_raw["beats_sharpe"] = bs_raw["strat_sharpe"] > bs_raw["bench_sharpe"]
    print(f"  beats_wealth={bs_raw['beats_wealth'].mean():.3f}, beats_sharpe={bs_raw['beats_sharpe'].mean():.3f}")

    print(f"Block bootstrap detrended ({N_SIMS} sims)...")
    bs_det = v3prob.block_bootstrap_portfolio(aligned, daily_rf, WEEKLY_DEPOSIT_PER_ASSET, s_builder, b_builder,
                                               n_sims=N_SIMS, block_weeks=4, detrend=True, fee=0.001)
    bs_det["beats_wealth"] = bs_det["strat_wealth_over_invested"] > bs_det["bench_wealth_over_invested"]
    bs_det["beats_sharpe"] = bs_det["strat_sharpe"] > bs_det["bench_sharpe"]
    print(f"  beats_wealth={bs_det['beats_wealth'].mean():.3f}, beats_sharpe={bs_det['beats_sharpe'].mean():.3f}")

    # --- sec 4.3 placebo: circular-shift the week-end target-weight sequence ---
    print(f"Placebo circular shift ({N_SIMS} sims)...")
    real_decide = lr.make_liquidity_rotation_decider(aligned, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET,
                                                       ASSETS, **lr.PRIMARY_CONFIG, enabled=True)
    real_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, real_decide, fee=0.001)
    real_fw = float(real_res.cash[-1] + sum(real_res.units[a][-1] * closes[a][-1] for a in ASSETS))
    real_s = v3met.summarize_portfolio(real_res.to_frame(), daily_rf, real_fw)

    weights_full = lr.compute_target_weights(aligned, idx, **lr.PRIMARY_CONFIG)
    weekend_weights = weights_full.loc[is_week_end]

    def strategy_decide_from_weekend_weights(shifted):
        from src.backtest.v3.strategies.dual_momentum import make_decider_from_weekend_weights
        return make_decider_from_weekend_weights(shifted, is_week_end, idx, closes, ASSETS)

    placebo_df, pctile_wealth, pctile_sharpe = v3prob.placebo_circular_shift_portfolio(
        aligned, daily_rf, WEEKLY_DEPOSIT_PER_ASSET, weekend_weights, is_week_end, ASSETS,
        strategy_decide_from_weekend_weights, None,
        real_s["wealth_over_invested"], real_s["sharpe"], n_sims=N_SIMS, fee=0.001,
    )
    print(f"  real wealth/invested={real_s['wealth_over_invested']:.3f} (percentile among placebos: {pctile_wealth:.1f})")
    print(f"  real sharpe={real_s['sharpe']:.3f} (percentile among placebos: {pctile_sharpe:.1f})")

    out = {
        "rolling_3y": {"n_windows": int(len(rw3)), "beats_wealth_frac": float(rw3["beats_wealth"].mean()) if len(rw3) else float("nan"),
                       "beats_sharpe_frac": float(rw3["beats_sharpe"].mean()) if len(rw3) else float("nan")},
        "bootstrap_raw": {"n_sims": N_SIMS, "beats_wealth_frac": float(bs_raw["beats_wealth"].mean()),
                           "beats_sharpe_frac": float(bs_raw["beats_sharpe"].mean())},
        "bootstrap_detrended": {"n_sims": N_SIMS, "beats_wealth_frac": float(bs_det["beats_wealth"].mean()),
                                 "beats_sharpe_frac": float(bs_det["beats_sharpe"].mean())},
        "placebo": {"n_sims": N_SIMS, "real_wealth_over_invested": real_s["wealth_over_invested"],
                    "real_sharpe": real_s["sharpe"], "percentile_wealth": pctile_wealth, "percentile_sharpe": pctile_sharpe},
    }
    with open(os.path.join(FAM_DIR, "_robustness_output.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)
    print("Wrote", os.path.join(FAM_DIR, "_robustness_output.json"))


if __name__ == "__main__":
    main()
