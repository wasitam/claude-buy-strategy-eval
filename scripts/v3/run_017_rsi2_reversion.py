"""Run family 017 (RSI2 short-horizon mean-reversion sizing) end-to-end on
development data: implementation checks -> non-degeneracy check -> full
grid -> trial logging -> DSR/N_eff -> assess -> (if sec 4.1 passes) sec 4.3
robustness. Writes state/trials/new_017_*.csv, updates
state/trial_counter.json, and dumps results into
families/017-rsi2-reversion/_run_output.json for the results.md writer.
Modeled directly on scripts/v3/run_016_vix_contrarian.py.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, metrics as v3met, dsr as v3dsr, checks as v3chk, robustness as v3rob
from src.backtest.v3.strategies import rsi2_reversion as rsi

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "017-rsi2-reversion")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]

# Most-aggressive corner per prereg.md's implementation-check plan: widest
# oversold/overbought bands (most days flagged in one tail or the other)
# combined with the highest oversold multiplier.
AGGRESSIVE_CORNER = {
    "rsi_period": 2, "oversold_threshold": 15.0, "overbought_threshold": 85.0,
    "buy_mult_oversold": 2.0, "buy_mult_overbought": rsi.BUY_MULT_OVERBOUGHT,
}


def decider_builder_factory(daily, cfg):
    def builder(enabled=True):
        return rsi.make_rsi2_decider(daily, WEEKLY_DEPOSIT, enabled=enabled, **cfg)
    return builder


def run_impl_checks(dev):
    out = {}
    daily = dev["prices"]["SP500"]
    rf = dev["rf"]
    cfg = rsi.PRIMARY_CONFIG
    builder = decider_builder_factory(daily, cfg)

    out["degenerate_equals_dca"] = v3chk.check_degenerate_equals_dca(daily, rf, builder, WEEKLY_DEPOSIT)

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()
    out["no_negative_cash_units_dca"] = v3chk.check_no_negative_cash_or_units(res_dca)

    decide_primary = builder(enabled=True)
    res_primary = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_primary).to_frame()
    out["no_negative_cash_units_primary"] = v3chk.check_no_negative_cash_or_units(res_primary)

    builder_agg = decider_builder_factory(daily, AGGRESSIVE_CORNER)
    decide_agg = builder_agg(enabled=True)
    res_agg = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_agg).to_frame()
    out["no_negative_cash_units_aggressive_corner"] = v3chk.check_no_negative_cash_or_units(res_agg)

    out["no_lookahead"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=6000)
    out["no_lookahead_late"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=9500)

    out["point_in_time_macro"] = True  # N/A: RSI2 uses only the asset's own OHLC (see prereg.md)

    return out, res_primary, res_agg


def check_capital_never_exceeds_deposits(res: pd.DataFrame) -> bool:
    """Total capital deployed (cumulative buy_usd) must never exceed
    cumulative deposits + interest credited to cash -- ported directly from
    scripts/v3/run_016_vix_contrarian.py's check of the same name."""
    cum_buy = res["buy_usd"].cumsum()
    cum_deposit = res["deposit"].cumsum()
    excess = (cum_buy - cum_deposit).to_numpy()
    bound = 0.05 * np.maximum(cum_deposit.to_numpy(), 1.0)
    return bool(np.all(excess <= bound))


def run_one(daily, rf, cfg, fee):
    decide = rsi.make_rsi2_decider(daily, WEEKLY_DEPOSIT, **cfg)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def run_dca(daily, rf, fee):
    decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def cfg_id_for(ci, cfg):
    return (f"cfg{ci:02d}_rp{cfg['rsi_period']}_ot{cfg['oversold_threshold']}"
            f"_obt{cfg['overbought_threshold']}_bmo{cfg['buy_mult_oversold']}")


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    rf = dev["rf"]

    print("Running implementation checks...")
    impl_checks, res_primary_sp, res_agg_sp = run_impl_checks(dev)
    impl_checks["capital_never_exceeds_deposits_primary"] = check_capital_never_exceeds_deposits(res_primary_sp)
    impl_checks["capital_never_exceeds_deposits_aggressive_corner"] = check_capital_never_exceeds_deposits(res_agg_sp)

    # Non-degeneracy sanity check (pre-registered in prereg.md): primary
    # config's oversold AND overbought frequencies must be nontrivial, on
    # EVERY core asset (not just SP500), before we trust the grid run at all.
    freq_table = {}
    for asset in ASSETS:
        daily_a = dev["prices"][asset]
        state_a = rsi.compute_state(
            daily_a, rsi.PRIMARY_CONFIG["rsi_period"],
            rsi.PRIMARY_CONFIG["oversold_threshold"], rsi.PRIMARY_CONFIG["overbought_threshold"],
        )
        n = len(state_a)
        n_oversold = int((state_a == "oversold").sum())
        n_overbought = int((state_a == "overbought").sum())
        freq_table[asset] = {
            "n_days": n, "n_oversold": n_oversold, "n_overbought": n_overbought,
            "frac_oversold": n_oversold / n, "frac_overbought": n_overbought / n,
        }
    impl_checks["primary_regime_nondegenerate"] = bool(all(
        0.02 < v["frac_oversold"] < 0.40 and 0.02 < v["frac_overbought"] < 0.40
        for v in freq_table.values()
    ))
    impl_checks["primary_regime_freq_by_asset"] = freq_table

    print(json.dumps(impl_checks, indent=2, default=float))
    required = ["degenerate_equals_dca", "no_negative_cash_units_dca", "no_negative_cash_units_primary",
                "no_negative_cash_units_aggressive_corner", "capital_never_exceeds_deposits_primary",
                "capital_never_exceeds_deposits_aggressive_corner",
                "no_lookahead", "no_lookahead_late", "point_in_time_macro", "primary_regime_nondegenerate"]
    if not all(impl_checks[k] for k in required):
        raise SystemExit("Implementation checks FAILED -- stopping before any trusted backtest.")

    configs = rsi.grid_configs()
    assert len(configs) <= 36
    print(f"Grid: {len(configs)} configs")

    dca_cache = {}
    for asset in ASSETS:
        daily = dev["prices"][asset]
        dca_cache[asset] = {}
        for fee in FEES:
            s, res = run_dca(daily, rf, fee)
            dca_cache[asset][fee] = s

    grid_rows = []
    trial_series = {}
    per_config_asset_weekly = {}

    new_trial_count = 0
    for ci, cfg in enumerate(configs):
        cfg_id = cfg_id_for(ci, cfg)
        per_asset_excess = {}
        beats_wealth_01 = beats_sharpe_01 = 0
        beats_both_025 = 0
        for asset in ASSETS:
            daily = dev["prices"][asset]
            row = {"config_id": cfg_id, "asset": asset, **cfg}
            for fee in FEES:
                s, res = run_one(daily, rf, cfg, fee)
                dca_s = dca_cache[asset][fee]
                row[f"wealth_over_invested_fee{fee}"] = s["wealth_over_invested"]
                row[f"sharpe_fee{fee}"] = s["sharpe"]
                row[f"dca_wealth_over_invested_fee{fee}"] = dca_s["wealth_over_invested"]
                row[f"dca_sharpe_fee{fee}"] = dca_s["sharpe"]
                beats_wealth = s["wealth_over_invested"] > dca_s["wealth_over_invested"]
                beats_sharpe = (s["sharpe"] if not np.isnan(s["sharpe"]) else -np.inf) > \
                               (dca_s["sharpe"] if not np.isnan(dca_s["sharpe"]) else -np.inf)
                row[f"beats_dca_fee{fee}"] = bool(beats_wealth and beats_sharpe)
                per_config_asset_weekly[(cfg_id, asset, fee)] = s["weekly_returns"]
                if fee == 0.001:
                    if beats_wealth:
                        beats_wealth_01 += 1
                    if beats_sharpe:
                        beats_sharpe_01 += 1
                if fee == 0.0025 and beats_wealth and beats_sharpe:
                    beats_both_025 += 1
                if fee == 0.001:
                    idx = s["weekly_returns"].index
                    dret = dca_s["weekly_returns"].reindex(idx).fillna(0.0)
                    per_asset_excess[asset] = (s["weekly_returns"] - dret).dropna()
            grid_rows.append(row)

        pooled = pd.concat(per_asset_excess.values(), axis=1).mean(axis=1).dropna() if per_asset_excess else pd.Series(dtype=float)
        trial_id = f"new_017_{cfg_id}"
        trial_series[trial_id] = pooled
        pooled.rename("excess_return").reset_index().rename(columns={"index": "date"}).to_csv(
            os.path.join(TRIALS_DIR, f"{trial_id}.csv"), index=False
        )
        new_trial_count += 1
        print(f"  {cfg_id}: beats_wealth@0.1%={beats_wealth_01}/5 beats_sharpe@0.1%={beats_sharpe_01}/5 "
              f"beats_both@0.25%={beats_both_025}/5")

    grid_df = pd.DataFrame(grid_rows)
    grid_df.to_csv(os.path.join(FAM_DIR, "grid_results.csv"), index=False)

    # --- Trial counter update (idempotent -- see state/bugfix_log.md) ---
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

    # --- Load ALL trials (seed + new) for N_eff ---
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

    primary_ci = configs.index(rsi.PRIMARY_CONFIG)
    primary_cfg_id = cfg_id_for(primary_ci, rsi.PRIMARY_CONFIG)
    primary_trial_id = f"new_017_{primary_cfg_id}"
    primary_series = trial_series[primary_trial_id]

    dsr_neff = v3dsr.deflated_sharpe_ratio(primary_series.to_numpy(), cluster_sharpes, n_eff)
    dsr_rawn = v3dsr.deflated_sharpe_ratio(primary_series.to_numpy(), np.array([v3dsr._sharpe(s.dropna().to_numpy()) for s in all_series.values()]), len(all_series))
    print("DSR (N_eff):", dsr_neff)
    print("DSR (raw N):", dsr_rawn)

    # --- sec 4.1: beats DCA >=3/5 at both fees, primary config ---
    primary_rows = grid_df[grid_df["config_id"] == primary_cfg_id]
    beats_01 = int(primary_rows["beats_dca_fee0.001"].sum())
    beats_025 = int(primary_rows["beats_dca_fee0.0025"].sum())
    check_4_1 = {"beats_dca_count_fee0.1pct": beats_01, "beats_dca_count_fee0.25pct": beats_025,
                 "pass": beats_01 >= 3 and beats_025 >= 3}

    # --- sec 4.4: >=2/3 of grid beats DCA (majority-of-assets rule per config), 0.1% fee ---
    grid_df["config_beats_majority"] = grid_df.groupby("config_id")["beats_dca_fee0.001"].transform(lambda s: s.sum() >= 3)
    frac_grid_pass = grid_df.drop_duplicates("config_id")["config_beats_majority"].mean()
    check_4_4_grid = {"frac_grid_configs_majority_beat_dca": float(frac_grid_pass), "pass": frac_grid_pass >= 2 / 3}

    # CSCV PBO diagnostic, pooled SP500 weekly strategy returns across the grid
    cscv_returns = {cfg_id: per_config_asset_weekly[(cfg_id, "SP500", 0.001)] for cfg_id in grid_df["config_id"].unique()}
    cscv = v3dsr.cscv_pbo(cscv_returns, n_splits=8)
    print("CSCV PBO (SP500 grid):", cscv)

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
    }

    # --- sec 4.3: only run in full if sec 4.1 passes (per established precedent) ---
    if check_4_1["pass"]:
        print("Sec 4.1 PASSED -- running sec 4.3 robustness battery (time-boxed, n_sims~60)...")
        rolling_summary = {}
        for asset in ASSETS:
            daily = dev["prices"][asset]
            window_years = 2 if asset == "BTC" else 3
            strat_builder = lambda w, cfg=rsi.PRIMARY_CONFIG: rsi.make_rsi2_decider(w, WEEKLY_DEPOSIT, **cfg)
            bench_builder = lambda w: v3eng.make_dca_decider(WEEKLY_DEPOSIT)
            rw = v3rob.rolling_windows(daily, rf, WEEKLY_DEPOSIT, strat_builder, bench_builder,
                                        window_years=window_years, step_days=20, fee=0.001)
            if len(rw) > 0:
                rolling_summary[asset] = {
                    "n_windows": len(rw),
                    "frac_beats_wealth": float(rw["beats_wealth"].mean()),
                    "frac_beats_sharpe": float(rw["beats_sharpe"].mean()),
                }
            else:
                rolling_summary[asset] = {"n_windows": 0}
        out["rolling_windows"] = rolling_summary

        bootstrap_summary = {}
        placebo_summary = {}
        for asset in ASSETS:
            daily = dev["prices"][asset]
            strat_builder = lambda w, cfg=rsi.PRIMARY_CONFIG: rsi.make_rsi2_decider(w, WEEKLY_DEPOSIT, **cfg)
            bench_builder = lambda w: v3eng.make_dca_decider(WEEKLY_DEPOSIT)
            bb = v3rob.block_bootstrap(daily, rf, WEEKLY_DEPOSIT, strat_builder, bench_builder,
                                        n_sims=60, block_weeks=4, detrend=False, fee=0.001)
            bootstrap_summary[asset] = {
                "n_sims": len(bb),
                "frac_beats_wealth": float((bb["strat_wealth_over_invested"] > bb["bench_wealth_over_invested"]).mean()),
                "frac_beats_sharpe": float((bb["strat_sharpe"] > bb["bench_sharpe"]).mean()),
            }

            # Placebo circular-shift: shift the RSI state array's TIMING.
            state_arr = rsi.compute_state(daily, rsi.PRIMARY_CONFIG["rsi_period"],
                                           rsi.PRIMARY_CONFIG["oversold_threshold"],
                                           rsi.PRIMARY_CONFIG["overbought_threshold"])
            real_s, _ = run_one(daily, rf, rsi.PRIMARY_CONFIG, 0.001)

            def strat_from_signal(shifted_state):
                return rsi.make_decider_from_state(
                    daily, WEEKLY_DEPOSIT, shifted_state,
                    buy_mult_oversold=rsi.PRIMARY_CONFIG["buy_mult_oversold"],
                    buy_mult_overbought=rsi.PRIMARY_CONFIG["buy_mult_overbought"],
                )

            dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
            pdf, pctile_w, pctile_s = v3rob.placebo_circular_shift(
                daily, rf, WEEKLY_DEPOSIT, state_arr, strat_from_signal, dca_decide,
                real_s["wealth_over_invested"], real_s["sharpe"], n_sims=60,
            )
            placebo_summary[asset] = {"n_sims": len(pdf), "pctile_wealth": pctile_w, "pctile_sharpe": pctile_s}

        out["block_bootstrap"] = bootstrap_summary
        out["placebo"] = placebo_summary
    else:
        print("Sec 4.1 FAILED -- skipping sec 4.3 robustness battery, per established precedent.")
        out["rolling_windows"] = "not run (sec 4.1 failed)"
        out["block_bootstrap"] = "not run (sec 4.1 failed)"
        out["placebo"] = "not run (sec 4.1 failed)"

    with open(os.path.join(FAM_DIR, "_run_output.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)
    print("Wrote", os.path.join(FAM_DIR, "_run_output.json"))

    # Save per-asset primary-config summary for results.md writer
    per_asset_summary = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        row = {"asset": asset}
        for fee in FEES:
            s, _ = run_one(daily, rf, rsi.PRIMARY_CONFIG, fee)
            dca_s = dca_cache[asset][fee]
            row[f"strat_wealth_fee{fee}"] = s["wealth_over_invested"]
            row[f"dca_wealth_fee{fee}"] = dca_s["wealth_over_invested"]
            row[f"strat_sharpe_fee{fee}"] = s["sharpe"]
            row[f"dca_sharpe_fee{fee}"] = dca_s["sharpe"]
        per_asset_summary.append(row)
    pd.DataFrame(per_asset_summary).to_csv(os.path.join(FAM_DIR, "_primary_per_asset.csv"), index=False)
    print("Wrote", os.path.join(FAM_DIR, "_primary_per_asset.csv"))


if __name__ == "__main__":
    main()
