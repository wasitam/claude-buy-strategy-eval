"""Run family 025 (VRP sizing) end-to-end on development data:
implementation checks -> pre-grid non-degeneracy + distinctness-from-016
sanity check -> full grid -> trial logging -> DSR/N_eff -> assess. Writes
state/trials/new_025_*.csv, updates state/trial_counter.json, and dumps
results into families/025-vrp-sizing/_run_output.json for the results.md
writer. Modeled on scripts/v3/run_016_vix_contrarian.py and
run_024_sad_daylight.py.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, metrics as v3met, dsr as v3dsr, checks as v3chk
from src.backtest.v3.strategies import vrp_sizing as vrp
from src.backtest.v3.strategies import vix_contrarian as vixc

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "025-vrp-sizing")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]

# Most-aggressive corner per prereg.md's implementation-check plan: shortest
# (noisiest) realized-vol window + loosest elevated/compressed thresholds +
# highest multiplier.
AGGRESSIVE_CORNER = {"rv_lookback": 20, "elevated_pct": 80.0, "compressed_pct": 20.0, "buy_multiplier": 3.0}


def decider_builder_factory(daily, cfg):
    def builder(enabled=True):
        return vrp.make_vrp_sizing_decider(daily, WEEKLY_DEPOSIT, enabled=enabled, **cfg)
    return builder


def run_impl_checks(dev):
    out = {}
    daily = dev["prices"]["SP500"]
    rf = dev["rf"]
    cfg = vrp.PRIMARY_CONFIG
    builder = decider_builder_factory(daily, cfg)

    out["degenerate_equals_dca"] = v3chk.check_degenerate_equals_dca(daily, rf, builder, WEEKLY_DEPOSIT)

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()
    out["no_negative_cash_units_dca"] = v3chk.check_no_negative_cash_or_units(res_dca)

    # Capital-vs-deposits check, family 021's principled-bound method: a
    # "never invest" reference run gives the true maximum interest ceiling.
    def never_invest(t, cash):
        return 0.0, 0.0, {}
    res_cash_only = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, never_invest).to_frame()
    cum_dep_ref = res_cash_only["deposit"].cumsum()
    max_interest_ceiling = (res_cash_only["cash"] - cum_dep_ref)

    decide_primary = builder(enabled=True)
    res_primary = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_primary).to_frame()
    out["no_negative_cash_units_primary"] = v3chk.check_no_negative_cash_or_units(res_primary)

    cum_buy = res_primary["buy_usd"].cumsum()
    cum_dep = res_primary["deposit"].cumsum()
    excess = cum_buy - cum_dep
    tol = 1e-6 * np.maximum(cum_dep.to_numpy(), 1.0)
    out["capital_never_exceeds_deposits_primary"] = bool(
        np.all(excess.to_numpy() <= max_interest_ceiling.to_numpy() + tol)
    )

    agg_builder = decider_builder_factory(daily, AGGRESSIVE_CORNER)
    decide_agg = agg_builder(enabled=True)
    res_agg = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_agg).to_frame()
    out["no_negative_cash_units_aggressive"] = v3chk.check_no_negative_cash_or_units(res_agg)
    cum_buy_a = res_agg["buy_usd"].cumsum()
    cum_dep_a = res_agg["deposit"].cumsum()
    excess_a = cum_buy_a - cum_dep_a
    tol_a = 1e-6 * np.maximum(cum_dep_a.to_numpy(), 1.0)
    out["capital_never_exceeds_deposits_aggressive"] = bool(
        np.all(excess_a.to_numpy() <= max_interest_ceiling.to_numpy() + tol_a)
    )

    out["no_lookahead"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=6000)
    out["no_lookahead_late"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=20000)
    out["point_in_time_macro"] = True  # VIX is a daily market-price series, no ALFRED vintage concern (same as family 016)
    return out


def run_sanity_and_distinctness_check(dev):
    """Pre-grid non-degeneracy check (primary config's elevated/compressed
    frequencies, all 5 assets) AND the required distinctness-from-016
    cross-tabulation: this family's elevated flag must NOT coincide with
    family 016's own primary-config elevated-VIX flag on every date."""
    cfg = vrp.PRIMARY_CONFIG
    rows = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        elevated, compressed = vrp.compute_regime_flags(
            daily, cfg["rv_lookback"], vrp.VRP_LOOKBACK, cfg["elevated_pct"], cfg["compressed_pct"]
        )
        n = len(elevated)
        elev_frac = float(elevated.mean())
        comp_frac = float(compressed.mean())

        # family 016's own primary-config elevated-VIX flag, recomputed on the
        # same asset's calendar, for the distinctness cross-tabulation.
        vix_elevated = vixc.compute_elevated(daily, vixc.PRIMARY_CONFIG["vix_lookback"], vixc.PRIMARY_CONFIG["elevated_pct"])
        both = int(np.sum(elevated & vix_elevated))
        vrp_only = int(np.sum(elevated & ~vix_elevated))
        vix_only = int(np.sum(vix_elevated & ~elevated))
        neither_elevated = int(np.sum(~elevated & ~vix_elevated))
        agreement_frac = float((elevated == vix_elevated).mean())

        rows.append({
            "asset": asset, "n_days": int(n),
            "elevated_frac": elev_frac, "compressed_frac": comp_frac,
            "non_degenerate": bool(0.01 < elev_frac < 0.5 and 0.01 < comp_frac < 0.5),
            "vix_elevated_frac_016": float(vix_elevated.mean()),
            "both_elevated_days": both, "vrp_only_elevated_days": vrp_only,
            "vix_only_elevated_days_016": vix_only, "neither_elevated_days": neither_elevated,
            "flag_agreement_frac": agreement_frac,
            "distinct_from_016": bool(agreement_frac < 0.98 and (vrp_only > 0 or vix_only > 0)),
        })
    return rows


def run_one(daily, rf, cfg, fee):
    decide = vrp.make_vrp_sizing_decider(daily, WEEKLY_DEPOSIT, **cfg)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def run_dca(daily, rf, fee):
    decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def cfg_id_for(ci, cfg):
    return f"cfg{ci:02d}_rv{cfg['rv_lookback']}_ep{cfg['elevated_pct']}_cp{cfg['compressed_pct']}_bm{cfg['buy_multiplier']}"


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    rf = dev["rf"]

    print("Running implementation checks...")
    impl_checks = run_impl_checks(dev)
    print(json.dumps(impl_checks, indent=2))
    required = ["degenerate_equals_dca", "no_negative_cash_units_dca", "no_negative_cash_units_primary",
                "capital_never_exceeds_deposits_primary", "no_negative_cash_units_aggressive",
                "capital_never_exceeds_deposits_aggressive", "no_lookahead", "no_lookahead_late",
                "point_in_time_macro"]
    if not all(impl_checks[k] for k in required):
        raise SystemExit("Implementation checks FAILED -- stopping before any trusted backtest.")

    print("Running pre-grid non-degeneracy + distinctness-from-016 sanity check...")
    sanity = run_sanity_and_distinctness_check(dev)
    print(json.dumps(sanity, indent=2))
    for row in sanity:
        if not row["non_degenerate"]:
            raise SystemExit(f"Sanity check FAILED for {row['asset']}: {row} -- degenerate regime frequency.")
        if not row["distinct_from_016"]:
            raise SystemExit(f"Distinctness check FAILED for {row['asset']}: {row} -- VRP signal collapsed "
                              "onto family 016's VIX-alone signal.")

    configs = vrp.grid_configs()
    assert len(configs) <= 36
    assert vrp.PRIMARY_CONFIG in configs
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
        trial_id = f"new_025_{cfg_id}"
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

    primary_ci = configs.index(vrp.PRIMARY_CONFIG)
    primary_cfg_id = cfg_id_for(primary_ci, vrp.PRIMARY_CONFIG)
    primary_trial_id = f"new_025_{primary_cfg_id}"
    primary_series = trial_series[primary_trial_id]

    dsr_neff = v3dsr.deflated_sharpe_ratio(primary_series.to_numpy(), cluster_sharpes, n_eff)
    dsr_rawn = v3dsr.deflated_sharpe_ratio(
        primary_series.to_numpy(),
        np.array([v3dsr._sharpe(s.dropna().to_numpy()) for s in all_series.values()]),
        len(all_series),
    )
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
        "sanity_distinctness_check": sanity,
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

    if check_4_1["pass"]:
        print("Sec 4.1 PASSED -- run scripts/v3/robustness_025_vrp_sizing.py next "
              "for sec 4.3 (rolling windows, bootstrap, placebo; n_sims~60).")
    else:
        print("Sec 4.1 FAILED -- skipping sec 4.3 per established loop precedent.")

    with open(os.path.join(FAM_DIR, "_run_output.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)
    print("Wrote", os.path.join(FAM_DIR, "_run_output.json"))

    per_asset_summary = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        row = {"asset": asset}
        for fee in FEES:
            s, _ = run_one(daily, rf, vrp.PRIMARY_CONFIG, fee)
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
