"""Run family 047 (CBOE SKEW Index tail-risk-pricing regime sizing) end-to-
end on development data: reachability/warm-up availability table ->
distinction-verification cross-tabs vs. families 016/025/041/046 ->
implementation checks -> pre-grid non-degeneracy sanity check -> full grid
-> trial logging -> DSR/N_eff -> assess. Writes state/trials/new_047_*.csv,
updates state/trial_counter.json, and dumps results into
families/047-skew-index-sizing/_run_output.json for the results.md writer.
Modeled directly on scripts/v3/run_046_vvix_regime_sizing.py's structure.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, metrics as v3met, dsr as v3dsr, checks as v3chk
from src.backtest.v3.strategies import skew_index_sizing as sks
from src.backtest.v3.strategies import vix_contrarian as vc
from src.backtest.v3.strategies import vrp_sizing as vrp
from src.backtest.v3.strategies import vix_term_structure_carry as vtc
from src.backtest.v3.strategies import vvix_regime_sizing as vvs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "047-skew-index-sizing")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]


def check_skew_availability(dev) -> list[dict]:
    """Task-required: exact day counts of ^SKEW availability vs. each
    asset's own development window, computed live (not hand-copied from
    prereg.md)."""
    rows = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        raw_skew = v3data.fetch_yf_macro(sks.SKEW_TICKER)
        n = len(daily)
        n_avail = int((daily.index >= raw_skew.index.min()).sum())
        rows.append({
            "asset": asset, "dev_days": n, "skew_available_days": n_avail,
            "frac_available": n_avail / n if n else float("nan"),
            "dev_start": str(daily.index.min().date()), "dev_end": str(daily.index.max().date()),
            "skew_start": str(raw_skew.index.min().date()),
        })
    return rows


def check_distinction_from_priors(dev) -> dict:
    """Task-required distinction-verification check: cross-tabulate this
    family's elevated-SKEW flag (top-half of its own trailing percentile)
    against family 016's elevated-VIX-level flag, family 025's elevated-VRP
    flag, family 041's backwardation flag, and family 046's elevated-VVIX
    flag, plus raw level correlations, on real overlapping SP500
    development data."""
    daily = dev["prices"]["SP500"]
    both_start = pd.Timestamp("1990-01-02")

    skew_close = sks._aligned_skew_close(daily.index)
    pct_skew = sks.compute_percentile_rank(skew_close, sks.PRIMARY_CONFIG["skew_lookback"])
    elevated_skew = pct_skew >= 0.5

    elevated_016 = vc.compute_elevated(
        daily, vix_lookback=vc.PRIMARY_CONFIG["vix_lookback"], elevated_pct=vc.PRIMARY_CONFIG["elevated_pct"],
    )

    elevated_flag_025, _ = vrp.compute_regime_flags(
        daily, vrp.PRIMARY_CONFIG.get("rv_lookback", 60), vrp.VRP_LOOKBACK,
        vrp.PRIMARY_CONFIG.get("elevated_pct", 80.0), vrp.PRIMARY_CONFIG.get("compressed_pct", 20.0),
    )

    ratio_041 = vtc.compute_ratio(daily.index)
    backwardation_041 = (ratio_041 < 1.0).to_numpy()

    vvix_close = vvs._aligned_vvix_close(daily.index)
    pct_vvix = vvs.compute_percentile_rank(vvix_close, vvs.PRIMARY_CONFIG["vvix_lookback"])
    elevated_046 = pct_vvix >= 0.5

    n = min(len(elevated_skew), len(elevated_016), len(elevated_flag_025), len(backwardation_041), len(elevated_046))
    mask = (daily.index[:n] >= both_start)

    vix_close = vc._aligned_vix_close(daily.index)
    corr_skew_vix = float(pd.Series(skew_close.to_numpy()[:n][mask]).corr(pd.Series(vix_close.to_numpy()[:n][mask])))

    def agreement(a, b):
        aa, bb = a[:n][mask], b[:n][mask]
        return float((aa == bb).mean()) if mask.sum() else float("nan")

    return {
        "n_overlap_days": int(mask.sum()),
        "corr_skew_level_vs_vix_level": corr_skew_vix,
        "skew_not_a_relabeling_of_vix_level": bool(abs(corr_skew_vix) < 0.9),
        "frac_flag_agreement_vs_016_elevated_vix": agreement(elevated_skew, elevated_016),
        "frac_flag_agreement_vs_025_elevated_vrp": agreement(elevated_skew, elevated_flag_025),
        "frac_flag_agreement_vs_041_backwardation": agreement(elevated_skew, ~backwardation_041),
        "frac_flag_agreement_vs_046_elevated_vvix": agreement(elevated_skew, elevated_046),
        "genuinely_different_from_016": bool(0.0 < agreement(elevated_skew, elevated_016) < 1.0),
        "genuinely_different_from_025": bool(0.0 < agreement(elevated_skew, elevated_flag_025) < 1.0),
        "genuinely_different_from_041": bool(0.0 < agreement(elevated_skew, ~backwardation_041) < 1.0),
        "genuinely_different_from_046": bool(0.0 < agreement(elevated_skew, elevated_046) < 1.0),
    }


def check_divergence_examples(dev) -> dict:
    """Task-required: concrete real-data examples of SKEW/VIX divergence
    (Dec 2019: depressed VIX, elevated SKEW), inverse-divergence (Jan
    1991: elevated VIX, depressed SKEW), and a comovement/contrast episode
    (2008 GFC), on real pre-2020 dev data."""
    daily = dev["prices"]["SP500"]
    skew_close = sks._aligned_skew_close(daily.index)
    vix_close = vc._aligned_vix_close(daily.index)
    pct_skew = sks.compute_percentile_rank(skew_close, 252)
    idx = daily.index

    def row_at(date_str):
        d = pd.Timestamp(date_str)
        loc = idx.get_indexer([d], method="ffill")[0]
        return {
            "date": str(idx[loc].date()),
            "vix": float(vix_close.iloc[loc]),
            "skew": float(skew_close.iloc[loc]),
            "skew_pctile": float(pct_skew[loc]),
        }

    return {
        "divergence_case_dec_2019_complacent_vix_expensive_tails": row_at("2019-12-19"),
        "inverse_divergence_case_jan_1991_gulf_war": row_at("1991-01-14"),
        "comovement_case_2008_oct": row_at("2008-10-20"),
        "comovement_case_2008_nov": row_at("2008-11-24"),
    }


def decider_builder_factory(daily, skew_lookback, k, min_mult, max_mult):
    def builder(enabled=True):
        return sks.make_skew_regime_decider(
            daily, WEEKLY_DEPOSIT, skew_lookback=skew_lookback, k=k, min_mult=min_mult, max_mult=max_mult,
            enabled=enabled,
        )
    return builder


def check_flat_k_zero_equals_dca(daily, rf) -> bool:
    """Second reference point (two-reference-point degenerate-config
    pattern): a real k=0.0 grid-shaped code path (enabled=True, going
    through the actual percentile computation) must also reproduce plain
    DCA bit-for-bit."""
    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    dca_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()

    flat_decide = sks.make_skew_regime_decider(
        daily, WEEKLY_DEPOSIT, skew_lookback=252, k=0.0, min_mult=0.5, max_mult=2.0, enabled=True,
    )
    flat_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, flat_decide).to_frame()

    ok_units = np.allclose(dca_res["units"].to_numpy(), flat_res["units"].to_numpy(), atol=1e-8)
    ok_cash = np.allclose(dca_res["cash"].to_numpy(), flat_res["cash"].to_numpy(), atol=1e-6)
    return bool(ok_units and ok_cash)


def check_cash_reserve_dynamics(daily, rf) -> dict:
    cfg = sks.PRIMARY_CONFIG
    decide = sks.make_skew_regime_decider(daily, WEEKLY_DEPOSIT, **cfg)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide).to_frame()

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()

    avg_cash_strategy = float(res["cash"].mean())
    avg_cash_dca = float(res_dca["cash"].mean())

    m = sks.compute_multiplier(daily, cfg["skew_lookback"], cfg["k"], cfg["min_mult"], cfg["max_mult"])
    n = min(len(res), len(m))
    low_mult_tier = m[:n] < 1.0
    high_mult_tier = m[:n] > 1.0
    avg_cash_low_mult = float(res["cash"].to_numpy()[:n][low_mult_tier].mean()) if low_mult_tier.any() else float("nan")
    avg_cash_high_mult = float(res["cash"].to_numpy()[:n][high_mult_tier].mean()) if high_mult_tier.any() else float("nan")

    return {
        "avg_cash_strategy": avg_cash_strategy,
        "avg_cash_dca_baseline": avg_cash_dca,
        "reserve_builds_up_vs_dca": bool(avg_cash_strategy > avg_cash_dca),
        # low_mult (elevated SKEW, risk-off) is the "banking" tier and
        # high_mult (depressed SKEW) is the "spending" tier.
        "avg_cash_elevated_skew_weeks_low_mult": avg_cash_low_mult,
        "avg_cash_depressed_skew_weeks_high_mult": avg_cash_high_mult,
        "reserve_drawn_down_on_depressed_skew_weeks": bool(avg_cash_high_mult < avg_cash_low_mult),
    }


def check_capital_never_exceeds_deposits(daily, rf, res: pd.DataFrame) -> bool:
    never_invest_decide = lambda t, cash: (0.0, 0.0, {})
    ceiling_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, never_invest_decide).to_frame()
    cum_deposit = res["deposit"].cumsum().to_numpy()
    cum_deposit_ceiling = ceiling_res["deposit"].cumsum().to_numpy()
    interest_ceiling = ceiling_res["cash"].to_numpy() - cum_deposit_ceiling
    cum_buy = res["buy_usd"].cumsum().to_numpy()
    excess = cum_buy - cum_deposit
    bound = interest_ceiling + 1e-6
    return bool(np.all(excess <= bound))


def run_sanity_check(dev):
    cfg = sks.PRIMARY_CONFIG
    rows = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        m = sks.compute_multiplier(daily, cfg["skew_lookback"], cfg["k"], cfg["min_mult"], cfg["max_mult"])
        n = len(m)
        frac_default_one = float(np.isclose(m, 1.0, atol=1e-9).mean())
        std_m = float(np.std(m))
        rows.append({
            "asset": asset, "dev_days": n,
            "frac_multiplier_exactly_1.0": frac_default_one,
            "std_multiplier": std_m,
            "non_degenerate": bool(frac_default_one <= 0.90 and std_m > 0.01),
        })
    return rows


def run_impl_checks(dev):
    out = {}
    daily = dev["prices"]["SP500"]
    rf = dev["rf"]
    builder = decider_builder_factory(daily, **sks.PRIMARY_CONFIG)

    avail = check_skew_availability(dev)
    out["skew_availability"] = avail

    dist_check = check_distinction_from_priors(dev)
    out["distinction_from_priors"] = dist_check
    out["distinction_confirmed"] = (
        dist_check["genuinely_different_from_016"]
        and dist_check["genuinely_different_from_025"]
        and dist_check["genuinely_different_from_041"]
        and dist_check["genuinely_different_from_046"]
        and dist_check["skew_not_a_relabeling_of_vix_level"]
    )

    out["divergence_examples"] = check_divergence_examples(dev)

    cash_check = check_cash_reserve_dynamics(daily, rf)
    out["cash_reserve_check"] = cash_check
    out["reserve_builds_up_vs_dca"] = cash_check["reserve_builds_up_vs_dca"]
    out["reserve_drawn_down_on_depressed_skew_weeks"] = cash_check["reserve_drawn_down_on_depressed_skew_weeks"]

    out["degenerate_bypass_equals_dca"] = v3chk.check_degenerate_equals_dca(daily, rf, builder, WEEKLY_DEPOSIT)
    out["flat_k_zero_grid_arm_equals_dca"] = check_flat_k_zero_equals_dca(daily, rf)

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()
    out["no_negative_cash_units_dca"] = v3chk.check_no_negative_cash_or_units(res_dca)

    decide_primary = builder(enabled=True)
    res_primary = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_primary).to_frame()
    out["no_negative_cash_units_primary"] = v3chk.check_no_negative_cash_or_units(res_primary)
    out["capital_never_exceeds_deposits_primary"] = check_capital_never_exceeds_deposits(daily, rf, res_primary)

    aggressive_cfg = {"skew_lookback": 126, "k": 1.5, "min_mult": 0.25, "max_mult": 2.0}
    decide_agg = sks.make_skew_regime_decider(daily, WEEKLY_DEPOSIT, **aggressive_cfg, enabled=True)
    res_agg = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_agg).to_frame()
    out["no_negative_cash_units_aggressive"] = v3chk.check_no_negative_cash_or_units(res_agg)
    out["capital_never_exceeds_deposits_aggressive"] = check_capital_never_exceeds_deposits(daily, rf, res_agg)

    out["no_lookahead"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=6000)
    out["no_lookahead_late"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=20000)
    out["point_in_time_macro"] = v3chk.check_point_in_time_macro()
    return out


def run_one(daily, rf, cfg, fee):
    decide = sks.make_skew_regime_decider(daily, WEEKLY_DEPOSIT, **cfg)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def run_dca(daily, rf, fee):
    decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def cfg_id_for(ci, cfg):
    return f"cfg{ci:02d}_sl{cfg['skew_lookback']}_k{cfg['k']}_mn{cfg['min_mult']}_mx{cfg['max_mult']}"


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    rf = dev["rf"]

    print("Checking ^SKEW availability vs. each asset's dev window...")
    avail = check_skew_availability(dev)
    print(json.dumps(avail, indent=2))

    print("Running distinction-verification checks vs. families 016/025/041/046 + implementation checks...")
    impl_checks = run_impl_checks(dev)
    print(json.dumps(impl_checks, indent=2, default=float))
    required = ["distinction_confirmed", "reserve_builds_up_vs_dca", "reserve_drawn_down_on_depressed_skew_weeks",
                "degenerate_bypass_equals_dca", "flat_k_zero_grid_arm_equals_dca",
                "no_negative_cash_units_dca", "no_negative_cash_units_primary",
                "capital_never_exceeds_deposits_primary", "no_negative_cash_units_aggressive",
                "capital_never_exceeds_deposits_aggressive", "no_lookahead", "no_lookahead_late",
                "point_in_time_macro"]
    if not all(impl_checks[k] for k in required):
        raise SystemExit("Implementation checks FAILED -- stopping before any trusted backtest.")

    print("Running pre-grid non-degeneracy sanity check...")
    sanity = run_sanity_check(dev)
    print(json.dumps(sanity, indent=2))
    for row in sanity:
        if not row["non_degenerate"]:
            raise SystemExit(f"Sanity check FAILED for {row['asset']}: "
                              f"frac_default_1.0={row['frac_multiplier_exactly_1.0']:.4f} "
                              f"std_m={row['std_multiplier']:.4f} -- degenerate multiplier, stopping before grid.")

    configs = sks.grid_configs()
    assert len(configs) <= 36
    assert sks.PRIMARY_CONFIG in configs
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
            row = {"config_id": cfg_id, "asset": asset,
                   "skew_lookback": cfg["skew_lookback"], "k": cfg["k"],
                   "min_mult": cfg["min_mult"], "max_mult": cfg["max_mult"]}
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
        trial_id = f"new_047_{cfg_id}"
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

    primary_ci = configs.index(sks.PRIMARY_CONFIG)
    primary_cfg_id = cfg_id_for(primary_ci, sks.PRIMARY_CONFIG)
    primary_trial_id = f"new_047_{primary_cfg_id}"
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
        "skew_availability": avail,
        "sanity_check": sanity,
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
        print("Sec 4.1 PASSED -- run scripts/v3/robustness_047_skew_index_sizing.py next "
              "for sec 4.3 (rolling windows, bootstrap, placebo; n_sims~60).")
    else:
        print("Sec 4.1 FAILED -- skipping sec 4.3 per established loop precedent.")

    with open(os.path.join(FAM_DIR, "_run_output.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)
    print("Wrote", os.path.join(FAM_DIR, "_run_output.json"))

    # Save per-asset primary-config summary for results.md writer
    per_asset_summary = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        row = {"asset": asset}
        for fee in FEES:
            s, _ = run_one(daily, rf, sks.PRIMARY_CONFIG, fee)
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
