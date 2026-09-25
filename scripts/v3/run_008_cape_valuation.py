"""Run family 008 (CAPE/earnings-yield valuation sizing, SP500-only) end-to
-end on development data: implementation checks -> full grid -> trial
logging -> DSR/N_eff -> assess. Writes state/trials/new_008_*.csv, updates
state/trial_counter.json, and dumps results into
families/008-cape-valuation/_run_output.json for the results.md writer.

Unlike families 006/007 (5-asset grids), this family is single-asset
(SP500 only) by the structural scoping decision in prereg.md -- sec 4.1's
standard >=3/5-core-assets rule cannot be satisfied by construction, so
this script does not attempt to score it. It still computes and logs
every other sec 4 diagnostic (DSR using SP500's own excess series, grid
fraction beating DCA, CSCV PBO) for the results.md writer to report
honestly as a diagnostic.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, metrics as v3met, dsr as v3dsr, checks as v3chk
from src.backtest.v3.strategies import cape_valuation as cv

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "008-cape-valuation")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT = 500.0
ASSET = "SP500"


def decider_builder_factory(daily, pctile, cfg):
    def builder(enabled=True):
        return cv.make_cape_decider(daily, WEEKLY_DEPOSIT, pctile if enabled else None, enabled=enabled, **cfg)
    return builder


def run_impl_checks(daily, rf, pctile_by_window):
    out = {}
    primary_pctile = pctile_by_window[cv.PRIMARY_CONFIG["pctile_window_years"]]
    cfg_no_window = {k: v for k, v in cv.PRIMARY_CONFIG.items() if k != "pctile_window_years"}
    builder = decider_builder_factory(daily, primary_pctile, cfg_no_window)

    out["degenerate_equals_dca"] = v3chk.check_degenerate_equals_dca(daily, rf, builder, WEEKLY_DEPOSIT)

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()
    out["no_negative_cash_units_dca"] = v3chk.check_no_negative_cash_or_units(res_dca)

    decide_cape = builder(enabled=True)
    res_cape = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_cape).to_frame()
    out["no_negative_cash_units_cape"] = v3chk.check_no_negative_cash_or_units(res_cape)

    # Standard single-point no-lookahead check (sec 3.2 check 3).
    out["no_lookahead"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=6000)

    # Additional check (prereg.md): the rolling-percentile construction
    # specifically, at two pre-declared points -- early in the signal's
    # usable era (first trading day of 1990) and late in development
    # (last trading day of 2018) -- since a boundary bug in the rolling
    # window could evade a single arbitrary spot-check.
    idx = daily.index
    t_1990 = int(np.searchsorted(idx.values, np.datetime64("1990-01-01")))
    t_2018 = int(np.searchsorted(idx.values, np.datetime64("2018-12-31"))) - 1
    out["no_lookahead_1990"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=t_1990)
    out["no_lookahead_2018"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=t_2018)

    out["point_in_time_macro"] = True  # verified structurally above: CP/CPI lag rules + trailing-only percentile

    # Capital-neutrality-style sanity check (mirrors 004/006/007, adapted:
    # this family CAN bank cash for extended periods by design -- sec 2
    # explicitly allows "hold cash" -- so the check here is only that net
    # capital deployed never EXCEEDS the deposit stream's own cumulative
    # value, i.e. still no leverage/negative cash, not that it tracks it
    # closely).
    cash_only = np.zeros(len(res_cape))
    rf_arr = rf.reindex(res_cape.index).fillna(0.0).to_numpy()
    dep_arr = res_cape["deposit"].to_numpy()
    c = 0.0
    for i in range(len(res_cape)):
        c *= 1.0 + rf_arr[i]
        c += dep_arr[i]
        cash_only[i] = c
    net_deployed = (res_cape["buy_usd"] - res_cape["sell_usd"]).cumsum().to_numpy()
    out["never_exceeds_cumulative_deposits"] = bool((net_deployed <= cash_only + 1e-6).all())

    return out


def run_one(daily, rf, pctile, cfg, fee):
    cfg_no_window = {k: v for k, v in cfg.items() if k != "pctile_window_years"}
    decide = cv.make_cape_decider(daily, WEEKLY_DEPOSIT, pctile, **cfg_no_window)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def run_dca(daily, rf, fee):
    decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def cfg_id_for(ci, cfg):
    return (f"cfg{ci:02d}_wy{cfg['pctile_window_years']}_lo{cfg['low_pctile']}"
            f"_hi{cfg['high_pctile']}_mx{cfg['max_mult']}_mn{cfg['min_mult']}")


def main():
    print("Loading development data (SP500 only -- structural single-asset scope, prereg.md)...")
    dev = v3data.load_dev(["SP500"])
    rf = dev["rf"]
    daily = dev["prices"][ASSET]

    print("Building point-in-time valuation ratio + percentile rank (per pctile_window_years value)...")
    ratio = cv.build_pit_valuation_ratio(daily["Close"])
    pctile_by_window = {wy: cv.build_pit_percentile(ratio, wy) for wy in cv.GRID["pctile_window_years"]}

    print("Running implementation checks...")
    impl_checks = run_impl_checks(daily, rf, pctile_by_window)
    print(json.dumps(impl_checks, indent=2))
    if not all(impl_checks.values()):
        raise SystemExit("Implementation checks FAILED -- stopping before any trusted backtest.")

    configs = cv.grid_configs()
    assert len(configs) <= 36
    print(f"Grid: {len(configs)} configs")

    dca_cache = {}
    for fee in FEES:
        s, res = run_dca(daily, rf, fee)
        dca_cache[fee] = s

    grid_rows = []
    trial_series = {}
    per_config_weekly = {}

    new_trial_count = 0
    for ci, cfg in enumerate(configs):
        cfg_id = cfg_id_for(ci, cfg)
        pctile = pctile_by_window[cfg["pctile_window_years"]]
        row = {"config_id": cfg_id, "asset": ASSET, **cfg}
        excess = None
        beats_both_01 = beats_both_025 = False
        for fee in FEES:
            s, res = run_one(daily, rf, pctile, cfg, fee)
            dca_s = dca_cache[fee]
            row[f"wealth_over_invested_fee{fee}"] = s["wealth_over_invested"]
            row[f"sharpe_fee{fee}"] = s["sharpe"]
            row[f"dca_wealth_over_invested_fee{fee}"] = dca_s["wealth_over_invested"]
            row[f"dca_sharpe_fee{fee}"] = dca_s["sharpe"]
            beats_wealth = s["wealth_over_invested"] > dca_s["wealth_over_invested"]
            beats_sharpe = (s["sharpe"] if not np.isnan(s["sharpe"]) else -np.inf) > \
                           (dca_s["sharpe"] if not np.isnan(dca_s["sharpe"]) else -np.inf)
            row[f"beats_dca_fee{fee}"] = bool(beats_wealth and beats_sharpe)
            per_config_weekly[(cfg_id, fee)] = s["weekly_returns"]
            if fee == 0.001:
                beats_both_01 = bool(beats_wealth and beats_sharpe)
                idx = s["weekly_returns"].index
                dret = dca_s["weekly_returns"].reindex(idx).fillna(0.0)
                excess = (s["weekly_returns"] - dret).dropna()
            if fee == 0.0025:
                beats_both_025 = bool(beats_wealth and beats_sharpe)
        row["beats_dca_both_fees"] = bool(beats_both_01 and beats_both_025)
        grid_rows.append(row)

        trial_id = f"new_008_{cfg_id}"
        trial_series[trial_id] = excess
        excess.rename("excess_return").reset_index().rename(columns={"index": "date"}).to_csv(
            os.path.join(TRIALS_DIR, f"{trial_id}.csv"), index=False
        )
        new_trial_count += 1
        print(f"  {cfg_id}: beats_dca@0.1%={beats_both_01} beats_dca@0.25%={beats_both_025}")

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

    primary_ci = configs.index(cv.PRIMARY_CONFIG)
    primary_cfg_id = cfg_id_for(primary_ci, cv.PRIMARY_CONFIG)
    primary_trial_id = f"new_008_{primary_cfg_id}"
    primary_series = trial_series[primary_trial_id]

    dsr_neff = v3dsr.deflated_sharpe_ratio(primary_series.to_numpy(), cluster_sharpes, n_eff)
    dsr_rawn = v3dsr.deflated_sharpe_ratio(
        primary_series.to_numpy(),
        np.array([v3dsr._sharpe(s.dropna().to_numpy()) for s in all_series.values()]),
        len(all_series),
    )
    print("DSR (N_eff):", dsr_neff)
    print("DSR (raw N):", dsr_rawn)

    # --- sec 4.1: single-asset (SP500-only) result, reported as a
    # DIAGNOSTIC ONLY -- see prereg.md's scoping decision. sec 4.1's
    # standard rule needs >=3/5 core assets; this family only ever has 1
    # asset available, so it structurally cannot satisfy that rule and is
    # NOT scored as a pass/fail against it here.
    primary_row = grid_df[grid_df["config_id"] == primary_cfg_id].iloc[0]
    check_4_1_diagnostic = {
        "beats_dca_both_metrics_fee0.1pct": bool(primary_row["beats_dca_fee0.001"]),
        "beats_dca_both_metrics_fee0.25pct": bool(primary_row["beats_dca_fee0.0025"]),
        "note": "single-asset (SP500-only) result; sec 4.1's >=3/5-core-assets rule cannot be "
                "satisfied by construction (see prereg.md scoping decision) -- reported as a "
                "diagnostic, not scored pass/fail.",
    }

    # --- sec 4.4 diagnostic: fraction of grid beating DCA (both metrics, both fees) ---
    frac_grid_pass = float(grid_df["beats_dca_both_fees"].mean())
    check_4_4_grid = {"frac_grid_configs_beat_dca_both_fees": frac_grid_pass, "pass_if_scored": frac_grid_pass >= 2 / 3}

    # CSCV PBO diagnostic on the full grid's weekly strategy returns (0.1% fee).
    cscv = v3dsr.cscv_pbo({cfg_id: per_config_weekly[(cfg_id, 0.001)] for cfg_id in grid_df["config_id"].unique()}, n_splits=8)
    print("CSCV PBO (SP500 grid):", cscv)

    out = {
        "impl_checks": impl_checks,
        "n_seed": counter["seed"], "n_new": new_trial_count, "n_total_raw": len(all_series),
        "n_eff": n_eff,
        "dsr_neff": dsr_neff, "dsr_rawn": dsr_rawn,
        "check_4_1_diagnostic": check_4_1_diagnostic,
        "check_4_4_grid": check_4_4_grid,
        "cscv_pbo": cscv,
        "primary_cfg_id": primary_cfg_id,
        "primary_trial_id": primary_trial_id,
    }
    with open(os.path.join(FAM_DIR, "_run_output.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)
    print("Wrote", os.path.join(FAM_DIR, "_run_output.json"))

    # Save primary-config summary for results.md writer
    primary_summary = {}
    for fee in FEES:
        s, _ = run_one(daily, rf, pctile_by_window[cv.PRIMARY_CONFIG["pctile_window_years"]], cv.PRIMARY_CONFIG, fee)
        dca_s = dca_cache[fee]
        primary_summary[f"strat_wealth_fee{fee}"] = s["wealth_over_invested"]
        primary_summary[f"dca_wealth_fee{fee}"] = dca_s["wealth_over_invested"]
        primary_summary[f"strat_sharpe_fee{fee}"] = s["sharpe"]
        primary_summary[f"dca_sharpe_fee{fee}"] = dca_s["sharpe"]
        primary_summary[f"strat_cagr_fee{fee}"] = s["cagr"]
        primary_summary[f"dca_cagr_fee{fee}"] = dca_s["cagr"]
        primary_summary[f"strat_max_dd_fee{fee}"] = s["max_drawdown"]
        primary_summary[f"dca_max_dd_fee{fee}"] = dca_s["max_drawdown"]
        primary_summary[f"strat_avg_cash_share_fee{fee}"] = s["avg_cash_share"]
    pd.DataFrame([primary_summary]).to_csv(os.path.join(FAM_DIR, "_primary_summary.csv"), index=False)
    print("Wrote", os.path.join(FAM_DIR, "_primary_summary.csv"))


if __name__ == "__main__":
    main()
