"""Run family 013 (momentum-tilted rebalancing) end-to-end on development
data: implementation checks -> full grid -> trial logging -> DSR/N_eff ->
assess (portfolio win-rule per prereg.md). Writes
state/trials/new_013_*.csv, updates state/trial_counter.json, and dumps
results into families/013-momentum-rebalance/_run_output.json for the
results.md writer.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, metrics as v3met, dsr as v3dsr
from src.backtest.v3 import portfolio_engine as v3pe
from src.backtest.v3.engine import week_end_flags
from src.backtest.v3.strategies import momentum_rebalance as mr

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "013-momentum-rebalance")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT_PER_ASSET = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]


def build_shared_calendar(dev):
    prices = dev["prices"]
    start = max(df.index.min() for df in prices.values())
    idx = prices["SP500"].index
    idx = idx[idx >= start]
    aligned = {a: prices[a].reindex(idx).ffill().bfill() for a in ASSETS}
    return idx, aligned


def run_one(assets_ohlc, daily_rf, closes, cfg, is_week_end, index, fee, enabled=True):
    if enabled:
        decide = mr.make_momentum_rebalance_decider(
            closes, index, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **cfg, enabled=True,
        )
    else:
        decide = mr.make_momentum_rebalance_decider(
            closes, index, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, enabled=False,
        )
    res = v3pe.run_portfolio(assets_ohlc, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, decide, fee=fee)
    frame = res.to_frame()
    final_wealth = float(res.cash[-1] + sum(res.units[a][-1] * closes[a][-1] for a in ASSETS))
    s = v3met.summarize_portfolio(frame, daily_rf, final_wealth)
    return s, res


def run_dca(assets_ohlc, daily_rf, closes, fee):
    decide = v3pe.make_fixed_weight_dca_decider(WEEKLY_DEPOSIT_PER_ASSET, ASSETS)
    res = v3pe.run_portfolio(assets_ohlc, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, decide, fee=fee)
    frame = res.to_frame()
    final_wealth = float(res.cash[-1] + sum(res.units[a][-1] * closes[a][-1] for a in ASSETS))
    s = v3met.summarize_portfolio(frame, daily_rf, final_wealth)
    return s, res


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    idx, aligned = build_shared_calendar(dev)
    daily_rf = dev["rf"].reindex(idx).ffill().fillna(0.0)
    closes = {a: aligned[a]["Close"].to_numpy() for a in ASSETS}
    is_week_end = week_end_flags(idx)
    print(f"Shared calendar: {len(idx)} days, {idx[0].date()} -> {idx[-1].date()}")

    print("Running implementation checks...")
    impl_checks = {}

    # 1. degenerate (enabled=False) == fixed-weight DCA (bit-for-bit)
    dca_decide = v3pe.make_fixed_weight_dca_decider(WEEKLY_DEPOSIT_PER_ASSET, ASSETS)
    dca_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, dca_decide, fee=0.001)
    deg_decide = mr.make_momentum_rebalance_decider(
        closes, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, enabled=False,
    )
    deg_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, deg_decide, fee=0.001)
    ok_units = all(np.allclose(dca_res.units[a], deg_res.units[a], atol=1e-6) for a in ASSETS)
    ok_cash = np.allclose(dca_res.cash, deg_res.cash, atol=1e-4)
    impl_checks["degenerate_enabled_false_equals_fixed_weight_dca"] = bool(ok_units and ok_cash)

    # 2. family-specific: tilt_strength=0, enabled=True == independently-built
    #    equal-weight weekly-rebalance reference (v2 Strategy C1-equivalent,
    #    NOT plain DCA -- prereg.md check #2)
    zero_tilt_cfg = {"lookback_days": 252, "tilt_strength": 0.0, "min_weight": 0.05, "max_weight": 0.40}
    zero_tilt_decide = mr.make_momentum_rebalance_decider(
        closes, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **zero_tilt_cfg, enabled=True,
    )
    zero_tilt_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, zero_tilt_decide, fee=0.001)
    ew_decide = mr.make_equal_weight_rebalance_decider(closes, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS)
    ew_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, ew_decide, fee=0.001)
    ok_units2 = all(np.allclose(zero_tilt_res.units[a], ew_res.units[a], atol=1e-6) for a in ASSETS)
    ok_cash2 = np.allclose(zero_tilt_res.cash, ew_res.cash, atol=1e-4)
    impl_checks["zero_tilt_equals_equal_weight_rebalance_reference"] = bool(ok_units2 and ok_cash2)
    # and confirm it is NOT the same as plain DCA (must actually differ)
    differs_from_dca = not (
        all(np.allclose(dca_res.units[a], zero_tilt_res.units[a], atol=1e-6) for a in ASSETS)
        and np.allclose(dca_res.cash, zero_tilt_res.cash, atol=1e-4)
    )
    impl_checks["zero_tilt_differs_from_plain_dca"] = bool(differs_from_dca)

    # 3. cash and positions never negative (DCA baseline and primary config)
    def no_neg(res):
        if (res.cash < -1e-6).any():
            return False
        for a in ASSETS:
            if (res.units[a] < -1e-6).any():
                return False
        return True
    impl_checks["no_negative_cash_units_dca"] = no_neg(dca_res)

    primary_decide = mr.make_momentum_rebalance_decider(
        closes, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **mr.PRIMARY_CONFIG, enabled=True,
    )
    primary_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, primary_decide, fee=0.001)
    impl_checks["no_negative_cash_units_primary"] = no_neg(primary_res)

    # 4. no-lookahead: perturb all data after t_check, confirm orders on/before
    #    t_check unchanged
    rng = np.random.default_rng(13)
    t_check = len(idx) - 400
    perturbed = {a: aligned[a].copy() for a in ASSETS}
    noise = 1.0 + rng.normal(0, 0.2, size=len(idx) - t_check - 1)
    for a in ASSETS:
        for col in ["Open", "High", "Low", "Close"]:
            perturbed[a].iloc[t_check + 1:, perturbed[a].columns.get_loc(col)] = (
                perturbed[a].iloc[t_check + 1:][col].to_numpy() * noise
            )
    closes_pert = {a: perturbed[a]["Close"].to_numpy() for a in ASSETS}
    decide_a = mr.make_momentum_rebalance_decider(
        closes, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **mr.PRIMARY_CONFIG, enabled=True,
    )
    res_a = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, decide_a, fee=0.001)
    decide_b = mr.make_momentum_rebalance_decider(
        closes_pert, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **mr.PRIMARY_CONFIG, enabled=True,
    )
    res_b = v3pe.run_portfolio(perturbed, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, decide_b, fee=0.001)
    ok = True
    for a in ASSETS:
        ba, bb = res_a.buy_usd[a][:t_check + 1], res_b.buy_usd[a][:t_check + 1]
        sa, sb = res_a.sell_usd[a][:t_check + 1], res_b.sell_usd[a][:t_check + 1]
        if not (np.allclose(ba, bb, atol=1e-6) and np.allclose(sa, sb, atol=1e-6)):
            ok = False
    impl_checks["no_lookahead"] = ok
    impl_checks["point_in_time_macro"] = True  # price/IRX only, no ALFRED-vintage series

    print(json.dumps(impl_checks, indent=2))
    if not all(impl_checks.values()):
        raise SystemExit("Implementation checks FAILED -- stopping before any trusted backtest.")

    configs = mr.grid_configs()
    assert len(configs) <= 36
    print(f"Grid: {len(configs)} configs")

    dca_cache = {}
    for fee in FEES:
        dca_cache[fee] = run_dca(aligned, daily_rf, closes, fee)[0]

    grid_rows = []
    trial_series = {}
    per_config_weekly = {}

    new_trial_count = 0
    for ci, cfg in enumerate(configs):
        cfg_id = (f"cfg{ci:02d}_lb{cfg['lookback_days']}_ts{cfg['tilt_strength']}"
                  f"_mn{cfg['min_weight']}_mx{cfg['max_weight']}")
        row = {"config_id": cfg_id, **cfg}
        excess_by_fee = {}
        for fee in FEES:
            s, res = run_one(aligned, daily_rf, closes, cfg, is_week_end, idx, fee, enabled=True)
            dca_s = dca_cache[fee]
            row[f"wealth_over_invested_fee{fee}"] = s["wealth_over_invested"]
            row[f"sharpe_fee{fee}"] = s["sharpe"]
            row[f"dca_wealth_over_invested_fee{fee}"] = dca_s["wealth_over_invested"]
            row[f"dca_sharpe_fee{fee}"] = dca_s["sharpe"]
            beats_wealth = s["wealth_over_invested"] > dca_s["wealth_over_invested"]
            beats_sharpe = (s["sharpe"] if not np.isnan(s["sharpe"]) else -np.inf) > \
                           (dca_s["sharpe"] if not np.isnan(dca_s["sharpe"]) else -np.inf)
            row[f"beats_dca_fee{fee}"] = bool(beats_wealth and beats_sharpe)
            per_config_weekly.setdefault(cfg_id, {})[fee] = s["weekly_returns"]
            if fee == 0.001:
                idx_w = s["weekly_returns"].index
                dret = dca_s["weekly_returns"].reindex(idx_w).fillna(0.0)
                excess_by_fee[fee] = (s["weekly_returns"] - dret).dropna()
        grid_rows.append(row)

        pooled = excess_by_fee[0.001]
        trial_id = f"new_013_{cfg_id}"
        trial_series[trial_id] = pooled
        pooled.rename("excess_return").reset_index().rename(columns={"index": "date"}).to_csv(
            os.path.join(TRIALS_DIR, f"{trial_id}.csv"), index=False
        )
        new_trial_count += 1
        print(f"  {cfg_id}: beats_dca@0.1%={row['beats_dca_fee0.001']} beats_dca@0.25%={row['beats_dca_fee0.0025']}")

    grid_df = pd.DataFrame(grid_rows)
    grid_df.to_csv(os.path.join(FAM_DIR, "grid_results.csv"), index=False)

    counter_path = os.path.join(STATE_DIR, "trial_counter.json")
    marker_path = os.path.join(FAM_DIR, "_grid_counted.marker")
    with open(counter_path) as f:
        counter = json.load(f)
    if not os.path.exists(marker_path):
        counter["new"] = counter.get("new", 0) + new_trial_count
        counter["families_new"] = counter.get("families_new", 0) + 1
        with open(counter_path, "w") as f:
            json.dump(counter, f, indent=2)
        with open(marker_path, "w") as f:
            f.write("counted\n")

    all_series = {}
    for fn in os.listdir(TRIALS_DIR):
        if not fn.endswith(".csv"):
            continue
        tid = fn[:-4]
        df = pd.read_csv(os.path.join(TRIALS_DIR, fn))
        df["date"] = pd.to_datetime(df["date"], format="mixed")
        df = df.set_index("date")
        all_series[tid] = df["excess_return"]

    print(f"Total trials for N_eff: {len(all_series)}")
    n_eff, cluster_map = v3dsr.n_effective(all_series, rho_threshold=0.5)
    print(f"N_eff = {n_eff} (raw N = {len(all_series)})")
    cluster_sharpes = v3dsr.cluster_representative_sharpes(all_series, cluster_map)

    primary_ci = configs.index(mr.PRIMARY_CONFIG)
    primary_cfg_id = (f"cfg{primary_ci:02d}_lb{mr.PRIMARY_CONFIG['lookback_days']}"
                      f"_ts{mr.PRIMARY_CONFIG['tilt_strength']}_mn{mr.PRIMARY_CONFIG['min_weight']}"
                      f"_mx{mr.PRIMARY_CONFIG['max_weight']}")
    primary_trial_id = f"new_013_{primary_cfg_id}"
    primary_series = trial_series[primary_trial_id]

    dsr_neff = v3dsr.deflated_sharpe_ratio(primary_series.to_numpy(), cluster_sharpes, n_eff)
    dsr_rawn = v3dsr.deflated_sharpe_ratio(
        primary_series.to_numpy(),
        np.array([v3dsr._sharpe(s.dropna().to_numpy()) for s in all_series.values()]),
        len(all_series),
    )
    print("DSR (N_eff):", dsr_neff)
    print("DSR (raw N):", dsr_rawn)

    primary_row = grid_df[grid_df["config_id"] == primary_cfg_id].iloc[0]
    check_4_1 = {
        "beats_dca_fee0.1pct": bool(primary_row["beats_dca_fee0.001"]),
        "beats_dca_fee0.25pct": bool(primary_row["beats_dca_fee0.0025"]),
        "pass": bool(primary_row["beats_dca_fee0.001"] and primary_row["beats_dca_fee0.0025"]),
    }

    frac_grid_pass = float(grid_df["beats_dca_fee0.001"].mean())
    check_4_4_grid = {"frac_grid_configs_beat_dca": frac_grid_pass, "pass": frac_grid_pass >= 2 / 3}

    cscv_returns = {cfg_id: per_config_weekly[cfg_id][0.001] for cfg_id in grid_df["config_id"].unique()}
    cscv = v3dsr.cscv_pbo(cscv_returns, n_splits=8)
    print("CSCV PBO (portfolio grid):", cscv)

    out = {
        "impl_checks": impl_checks,
        "n_seed": counter["seed"], "n_new": new_trial_count, "n_total_raw": len(all_series),
        "n_eff": n_eff,
        "dsr_neff": dsr_neff, "dsr_rawn": dsr_rawn,
        "check_4_1": check_4_1,
        "check_4_4_grid": check_4_4_grid,
        "cscv_pbo": cscv,
        "primary_cfg_id": primary_cfg_id,
        "primary_trial_id": primary_trial_id,
        "shared_calendar_start": str(idx[0].date()),
        "shared_calendar_end": str(idx[-1].date()),
        "n_calendar_days": len(idx),
        "primary_wealth_over_invested_fee0.001": float(primary_row["wealth_over_invested_fee0.001"]),
        "primary_sharpe_fee0.001": float(primary_row["sharpe_fee0.001"]),
        "dca_wealth_over_invested_fee0.001": float(primary_row["dca_wealth_over_invested_fee0.001"]),
        "dca_sharpe_fee0.001": float(primary_row["dca_sharpe_fee0.001"]),
        "primary_wealth_over_invested_fee0.0025": float(primary_row["wealth_over_invested_fee0.0025"]),
        "primary_sharpe_fee0.0025": float(primary_row["sharpe_fee0.0025"]),
        "dca_wealth_over_invested_fee0.0025": float(primary_row["dca_wealth_over_invested_fee0.0025"]),
        "dca_sharpe_fee0.0025": float(primary_row["dca_sharpe_fee0.0025"]),
    }
    with open(os.path.join(FAM_DIR, "_run_output.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)
    print("Wrote", os.path.join(FAM_DIR, "_run_output.json"))
    return out


if __name__ == "__main__":
    main()
