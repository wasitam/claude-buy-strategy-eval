"""Run family 029 (risk-parity/inverse-vol rebalancing) end-to-end on
development data: implementation checks -> pre-grid non-degeneracy sanity
check -> full grid -> trial logging -> DSR/N_eff -> assess (portfolio
win-rule per prereg.md). Writes state/trials/new_029_*.csv, updates
state/trial_counter.json, and dumps results into
families/029-risk-parity-rebalance/_run_output.json for the results.md
writer.
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
from src.backtest.v3 import portfolio_robustness as v3prob
from src.backtest.v3.engine import week_end_flags
from src.backtest.v3.strategies import risk_parity_rebalance as rp
from src.backtest.v3.strategies import momentum_rebalance as mr

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "029-risk-parity-rebalance")
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
    decide = rp.make_risk_parity_decider(
        closes, index, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **cfg, enabled=enabled,
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
    assert idx[-1] < pd.Timestamp("2020-01-01"), "dev calendar must never touch 2020+"

    print("Running implementation checks...")
    impl_checks = {}

    # 1. degenerate (enabled=False) == fixed-weight DCA (bit-for-bit)
    dca_decide = v3pe.make_fixed_weight_dca_decider(WEEKLY_DEPOSIT_PER_ASSET, ASSETS)
    dca_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, dca_decide, fee=0.001)
    deg_decide = rp.make_risk_parity_decider(
        closes, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, enabled=False,
    )
    deg_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, deg_decide, fee=0.001)
    ok_units = all(np.allclose(dca_res.units[a], deg_res.units[a], atol=1e-6) for a in ASSETS)
    ok_cash = np.allclose(dca_res.cash, deg_res.cash, atol=1e-4)
    impl_checks["degenerate_enabled_false_equals_fixed_weight_dca"] = bool(ok_units and ok_cash)

    # 2. family-specific: equal_vol_override=True == family 013's
    #    independently-built equal-weight weekly-rebalance reference
    #    (v2 Strategy C1-equivalent, NOT plain DCA -- prereg.md check #2)
    eq_cfg = {"vol_lookback_days": 126, "min_weight": 0.05, "max_weight": 0.40, "smoothing_halflife_days": 0}
    eq_decide = rp.make_risk_parity_decider(
        closes, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **eq_cfg,
        equal_vol_override=True, enabled=True,
    )
    eq_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, eq_decide, fee=0.001)
    ew_decide = mr.make_equal_weight_rebalance_decider(closes, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS)
    ew_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, ew_decide, fee=0.001)
    ok_units2 = all(np.allclose(eq_res.units[a], ew_res.units[a], atol=1e-6) for a in ASSETS)
    ok_cash2 = np.allclose(eq_res.cash, ew_res.cash, atol=1e-4)
    impl_checks["equal_vol_override_equals_family013_equal_weight_reference"] = bool(ok_units2 and ok_cash2)
    differs_from_dca = not (
        all(np.allclose(dca_res.units[a], eq_res.units[a], atol=1e-6) for a in ASSETS)
        and np.allclose(dca_res.cash, eq_res.cash, atol=1e-4)
    )
    impl_checks["equal_vol_override_differs_from_plain_dca"] = bool(differs_from_dca)

    # 3. cash and positions never negative (DCA baseline and primary config)
    def no_neg(res):
        if (res.cash < -1e-6).any():
            return False
        for a in ASSETS:
            if (res.units[a] < -1e-6).any():
                return False
        return True
    impl_checks["no_negative_cash_units_dca"] = no_neg(dca_res)

    primary_decide = rp.make_risk_parity_decider(
        closes, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **rp.PRIMARY_CONFIG, enabled=True,
    )
    primary_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, primary_decide, fee=0.001)
    impl_checks["no_negative_cash_units_primary"] = no_neg(primary_res)

    # 4. no-lookahead: perturb all data after t_check, confirm orders on/before
    #    t_check unchanged
    rng = np.random.default_rng(29)
    t_check = len(idx) - 400
    perturbed = {a: aligned[a].copy() for a in ASSETS}
    noise = 1.0 + rng.normal(0, 0.2, size=len(idx) - t_check - 1)
    for a in ASSETS:
        for col in ["Open", "High", "Low", "Close"]:
            perturbed[a].iloc[t_check + 1:, perturbed[a].columns.get_loc(col)] = (
                perturbed[a].iloc[t_check + 1:][col].to_numpy() * noise
            )
    closes_pert = {a: perturbed[a]["Close"].to_numpy() for a in ASSETS}
    decide_a = rp.make_risk_parity_decider(
        closes, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **rp.PRIMARY_CONFIG, enabled=True,
    )
    res_a = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, decide_a, fee=0.001)
    decide_b = rp.make_risk_parity_decider(
        closes_pert, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **rp.PRIMARY_CONFIG, enabled=True,
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
    impl_checks["capital_neutrality"] = True  # always 100% invested, no cash-parking leg -- N/A by construction

    print(json.dumps(impl_checks, indent=2))
    if not all(impl_checks.values()):
        raise SystemExit("Implementation checks FAILED -- stopping before any trusted backtest.")

    # Pre-grid non-degeneracy sanity check (prereg.md): primary config's
    # risk-parity weights must actually differ meaningfully from equal
    # weight -- BTC should get a materially SMALLER average target weight
    # than GOLD, and below the 0.20 equal-weight baseline.
    primary_weights = rp.compute_target_weights(
        closes, idx, rp.PRIMARY_CONFIG["vol_lookback_days"], rp.PRIMARY_CONFIG["min_weight"],
        rp.PRIMARY_CONFIG["max_weight"], smoothing_halflife_days=rp.PRIMARY_CONFIG["smoothing_halflife_days"],
    )
    avg_w = primary_weights.mean()
    print("Average target weights (primary config):")
    print(avg_w.to_string())
    non_degeneracy = {
        "avg_weight_btc": float(avg_w["BTC"]),
        "avg_weight_gold": float(avg_w["GOLD"]),
        "btc_below_gold": bool(avg_w["BTC"] < avg_w["GOLD"]),
        "btc_below_equal_weight": bool(avg_w["BTC"] < 0.20),
        "all_avg_weights": {a: float(avg_w[a]) for a in ASSETS},
    }
    print(json.dumps(non_degeneracy, indent=2))
    if not (non_degeneracy["btc_below_gold"] and non_degeneracy["btc_below_equal_weight"]):
        raise SystemExit("Pre-grid non-degeneracy check FAILED -- BTC does not get a materially "
                          "smaller risk-parity weight than gold on real data. Stopping before the grid.")

    configs = rp.grid_configs()
    assert len(configs) <= 36
    assert rp.PRIMARY_CONFIG in configs
    print(f"Grid: {len(configs)} configs")

    dca_cache = {}
    for fee in FEES:
        dca_cache[fee] = run_dca(aligned, daily_rf, closes, fee)[0]

    grid_rows = []
    trial_series = {}
    per_config_weekly = {}

    new_trial_count = 0
    for ci, cfg in enumerate(configs):
        cfg_id = (f"cfg{ci:02d}_vl{cfg['vol_lookback_days']}_mn{cfg['min_weight']}"
                  f"_mx{cfg['max_weight']}_sm{cfg['smoothing_halflife_days']}")
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
        trial_id = f"new_029_{cfg_id}"
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

    primary_ci = configs.index(rp.PRIMARY_CONFIG)
    primary_cfg_id = (f"cfg{primary_ci:02d}_vl{rp.PRIMARY_CONFIG['vol_lookback_days']}"
                      f"_mn{rp.PRIMARY_CONFIG['min_weight']}_mx{rp.PRIMARY_CONFIG['max_weight']}"
                      f"_sm{rp.PRIMARY_CONFIG['smoothing_halflife_days']}")
    primary_trial_id = f"new_029_{primary_cfg_id}"
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
        "non_degeneracy": non_degeneracy,
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

    # sec 4.3 robustness, only if sec 4.1 passes (families 006/007/008/011/013 precedent)
    if check_4_1["pass"]:
        print("Sec 4.1 passed -- running sec 4.3 robustness battery (n_sims=60 time budget)...")

        def strat_builder(assets_win, idx_win):
            c = {a: assets_win[a]["Close"].to_numpy() for a in ASSETS}
            iwe = week_end_flags(idx_win)
            return rp.make_risk_parity_decider(
                c, idx_win, iwe, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **rp.PRIMARY_CONFIG, enabled=True,
            )

        def bench_builder(assets_win, idx_win):
            return v3pe.make_fixed_weight_dca_decider(WEEKLY_DEPOSIT_PER_ASSET, ASSETS)

        roll_rows = []
        for wy in [3, 5]:
            rdf = v3prob.rolling_windows_portfolio(
                aligned, daily_rf, WEEKLY_DEPOSIT_PER_ASSET, strat_builder, bench_builder,
                window_years=wy, step_days=20, fee=0.001,
            )
            rdf["window_years"] = wy
            roll_rows.append(rdf)
        rolling_df = pd.concat(roll_rows, ignore_index=True) if roll_rows else pd.DataFrame()
        rolling_df.to_csv(os.path.join(FAM_DIR, "rolling_windows.csv"), index=False)
        roll_pass_wealth = float(rolling_df["beats_wealth"].mean()) if len(rolling_df) else float("nan")
        roll_pass_sharpe = float(rolling_df["beats_sharpe"].mean()) if len(rolling_df) else float("nan")
        check_4_3_rolling = {
            "n_windows": int(len(rolling_df)), "frac_beat_wealth": roll_pass_wealth,
            "frac_beat_sharpe": roll_pass_sharpe,
            "pass": bool(roll_pass_wealth > 0.6 and roll_pass_sharpe > 0.6),
        }
        print("Rolling windows:", check_4_3_rolling)

        boot_raw = v3prob.block_bootstrap_portfolio(
            aligned, daily_rf, WEEKLY_DEPOSIT_PER_ASSET, strat_builder, bench_builder,
            n_sims=60, block_weeks=4, detrend=False, seed=291, fee=0.001,
        )
        boot_det = v3prob.block_bootstrap_portfolio(
            aligned, daily_rf, WEEKLY_DEPOSIT_PER_ASSET, strat_builder, bench_builder,
            n_sims=60, block_weeks=4, detrend=True, seed=292, fee=0.001,
        )
        boot_raw.to_csv(os.path.join(FAM_DIR, "bootstrap_raw.csv"), index=False)
        boot_det.to_csv(os.path.join(FAM_DIR, "bootstrap_detrended.csv"), index=False)

        def boot_pass_fracs(df):
            beats_w = (df["strat_wealth_over_invested"] > df["bench_wealth_over_invested"]).mean()
            beats_s = (df["strat_sharpe"].fillna(-np.inf) > df["bench_sharpe"].fillna(-np.inf)).mean()
            return float(beats_w), float(beats_s)

        raw_w, raw_s = boot_pass_fracs(boot_raw)
        det_w, det_s = boot_pass_fracs(boot_det)
        check_4_3_bootstrap = {
            "n_sims_each": 60,
            "raw_frac_beat_wealth": raw_w, "raw_frac_beat_sharpe": raw_s,
            "detrended_frac_beat_wealth": det_w, "detrended_frac_beat_sharpe": det_s,
            "pass": bool(raw_w > 0.5 and raw_s > 0.5 and det_w > 0.5 and det_s > 0.5),
        }
        print("Block bootstrap:", check_4_3_bootstrap)

        # placebo: circular-shift the primary config's week-end target-weight sequence
        primary_weekend_weights = primary_weights.loc[idx[is_week_end]]

        def decide_from_shifted(shifted_weights):
            return rp.make_decider_from_weekend_weights(shifted_weights, is_week_end, idx, closes, ASSETS)

        real_s, real_res = run_one(aligned, daily_rf, closes, rp.PRIMARY_CONFIG, is_week_end, idx, 0.001, enabled=True)
        placebo_df, pctile_wealth, pctile_sharpe = v3prob.placebo_circular_shift_portfolio(
            aligned, daily_rf, WEEKLY_DEPOSIT_PER_ASSET, primary_weekend_weights, is_week_end, ASSETS,
            decide_from_shifted, None,
            real_s["wealth_over_invested"], real_s["sharpe"],
            n_sims=60, seed=293, fee=0.001,
        )
        placebo_df.to_csv(os.path.join(FAM_DIR, "placebo.csv"), index=False)
        check_4_3_placebo = {
            "n_sims": 60, "real_pctile_wealth": pctile_wealth, "real_pctile_sharpe": pctile_sharpe,
            "pass": bool(pctile_wealth >= 95.0 and pctile_sharpe >= 95.0),
        }
        print("Placebo:", check_4_3_placebo)

        out["check_4_3_rolling"] = check_4_3_rolling
        out["check_4_3_bootstrap"] = check_4_3_bootstrap
        out["check_4_3_placebo"] = check_4_3_placebo
    else:
        print("Sec 4.1 FAILED -- skipping sec 4.3 robustness battery per established precedent.")
        out["check_4_3_rolling"] = None
        out["check_4_3_bootstrap"] = None
        out["check_4_3_placebo"] = None

    with open(os.path.join(FAM_DIR, "_run_output.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)
    print("Wrote", os.path.join(FAM_DIR, "_run_output.json"))
    return out


if __name__ == "__main__":
    main()
