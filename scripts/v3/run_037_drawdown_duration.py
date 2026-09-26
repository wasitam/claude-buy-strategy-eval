"""Run family 037 (drawdown-duration / time-underwater sizing) end-to-end on
development data: real-data divergence check vs. family 014's magnitude
statistic (prereg.md's required distinction) -> 2020+/unseen-ticker no-touch
assertion -> implementation checks -> pre-grid non-degeneracy + cash-reserve
sanity checks -> full grid -> trial logging -> DSR/N_eff -> assess. Writes
state/trials/new_037_*.csv, updates state/trial_counter.json, and dumps
results into families/037-drawdown-duration/_run_output.json for the
results.md writer. Modeled directly on scripts/v3/run_014_drawdown_reserve.py
(the closest prior family) and scripts/v3/run_036_autocorr_regime_sizing.py's
structure.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, metrics as v3met, dsr as v3dsr, checks as v3chk
from src.backtest.v3.strategies import drawdown_duration as ddd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "037-drawdown-duration")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]
HOLDOUT_CUTOFF = pd.Timestamp("2020-01-01")


def decider_builder_factory(daily, ath_lookback_years, ladder, near_high_mult, max_lump_cap):
    def builder(enabled=True):
        return ddd.make_drawdown_duration_decider(
            daily, WEEKLY_DEPOSIT, ath_lookback_years=ath_lookback_years, ladder=ladder,
            near_high_mult=near_high_mult, max_lump_cap=max_lump_cap, enabled=enabled,
        )
    return builder


def check_no_holdout_dates_referenced(dates_checked: list) -> bool:
    """Task checkpoint (c): assert that every date this script's own checks
    explicitly reference is strictly before the sealed holdout cutoff, and
    is drawn from load_dev()'s own gated data (which already refuses 2020+
    dates and unseen tickers by construction)."""
    ok = True
    for d in dates_checked:
        ts = pd.Timestamp(d)
        if ts >= HOLDOUT_CUTOFF:
            ok = False
    return ok


def check_real_divergence_example(dev) -> dict:
    """Task-required checkpoint: recompute family 014's magnitude statistic
    (compute_drawdown) and this family's duration statistic
    (compute_days_since_peak) on real SP500 dev-period data across the two
    episodes named in prereg.md, verify both are recovered from the
    module's own functions (not hand-copied), and confirm the magnitude
    ranking and duration ranking of the two episodes disagree."""
    daily = dev["prices"]["SP500"]
    close = daily["Close"].to_numpy(dtype=float)
    idx = daily.index

    dd = ddd.compute_drawdown(close, ath_lookback_years=None)
    dur = ddd.compute_days_since_peak(close, ath_lookback_years=None)

    # Deep-but-brief: peak 2018-09-20, trough 2018-12-24, new high 2019-04-23.
    peak1 = idx.searchsorted(pd.Timestamp("2018-09-20"))
    trough1 = idx.searchsorted(pd.Timestamp("2018-12-24"))
    newhigh1 = idx.searchsorted(pd.Timestamp("2019-04-23"))
    # Shallow-but-long: peak 2015-05-21, trough 2016-02-11, new high 2016-07-11.
    peak2 = idx.searchsorted(pd.Timestamp("2015-05-21"))
    trough2 = idx.searchsorted(pd.Timestamp("2016-02-11"))
    newhigh2 = idx.searchsorted(pd.Timestamp("2016-07-11"))

    dates_checked = [
        "2018-09-20", "2018-12-24", "2019-04-23",
        "2015-05-21", "2016-02-11", "2016-07-11",
    ]

    episode_deep_brief = {
        "peak_date": str(idx[peak1].date()), "peak_close": float(close[peak1]),
        "trough_date": str(idx[trough1].date()), "trough_close": float(close[trough1]),
        "new_high_date": str(idx[newhigh1].date()),
        "max_dd_magnitude": float(dd[trough1]),
        "duration_to_new_high_trading_days": float(dur[newhigh1 - 1]) + 1.0 if newhigh1 > 0 else None,
    }
    episode_shallow_long = {
        "peak_date": str(idx[peak2].date()), "peak_close": float(close[peak2]),
        "trough_date": str(idx[trough2].date()), "trough_close": float(close[trough2]),
        "new_high_date": str(idx[newhigh2].date()),
        "max_dd_magnitude": float(dd[trough2]),
        "duration_to_new_high_trading_days": float(dur[newhigh2 - 1]) + 1.0 if newhigh2 > 0 else None,
    }

    magnitude_ranking_deep_brief_is_deeper = (
        episode_deep_brief["max_dd_magnitude"] > episode_shallow_long["max_dd_magnitude"]
    )
    duration_ranking_deep_brief_is_shorter = (
        episode_deep_brief["duration_to_new_high_trading_days"]
        < episode_shallow_long["duration_to_new_high_trading_days"]
    )
    rankings_disagree = bool(magnitude_ranking_deep_brief_is_deeper and duration_ranking_deep_brief_is_shorter)

    return {
        "episode_deep_but_brief_2018_2019": episode_deep_brief,
        "episode_shallow_but_long_2015_2016": episode_shallow_long,
        "magnitude_ranking_deep_brief_is_deeper": bool(magnitude_ranking_deep_brief_is_deeper),
        "duration_ranking_deep_brief_is_shorter": bool(duration_ranking_deep_brief_is_shorter),
        "rankings_disagree_as_predicted": rankings_disagree,
        "dates_checked": dates_checked,
        "dates_all_pre_holdout": check_no_holdout_dates_referenced(dates_checked),
    }


def check_flat_zero_arm_equals_dca(daily, rf) -> bool:
    """Family-specific second reference point (two-reference-point
    degenerate-config pattern, per family 014/020/031/033/034/035/036
    precedent): ladder='flat', near_high_mult=1.0 (a real grid-shaped code
    path, not the enabled=False bypass) forces m_t=1.0 for every day
    regardless of dur_t -- must also reproduce plain DCA bit-for-bit."""
    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    dca_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()

    flat_decide = ddd.make_drawdown_duration_decider(
        daily, WEEKLY_DEPOSIT, ath_lookback_years=None, ladder="flat",
        near_high_mult=1.0, max_lump_cap=3.0, enabled=True,
    )
    flat_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, flat_decide).to_frame()

    ok_units = np.allclose(dca_res["units"].to_numpy(), flat_res["units"].to_numpy(), atol=1e-8)
    ok_cash = np.allclose(dca_res["cash"].to_numpy(), flat_res["cash"].to_numpy(), atol=1e-6)
    return bool(ok_units and ok_cash)


def check_cash_reserve_dynamics(daily, rf) -> dict:
    """Task-required cash-reserve check, per family 033's lesson: on the
    reserve-bearing grid arm (near_high_mult=0.75<1.0, moderate ladder),
    confirm a genuine reserve is banked overall (average cash share higher
    than plain DCA) and drawn down further during long-duration (m_t>1)
    weeks than during near-high (m_t<1) weeks. Also checks the primary
    config's own average cash against DCA (primary uses
    near_high_mult=1.0, so it still banks/spends via the ladder tiers
    alone)."""
    reserve_cfg = {"ath_lookback_years": None, "ladder": "moderate", "near_high_mult": 0.75, "max_lump_cap": 3.0}
    decide = ddd.make_drawdown_duration_decider(daily, WEEKLY_DEPOSIT, **reserve_cfg)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide).to_frame()

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()

    avg_cash_strategy = float(res["cash"].mean())
    avg_cash_dca = float(res_dca["cash"].mean())

    m = ddd.compute_multiplier(daily, **reserve_cfg)
    low_mult_tier = m < 1.0    # near-high -> under-invest -> should bank cash
    high_mult_tier = m > 1.0   # long-duration -> over-invest -> should draw cash down
    n = min(len(res), len(m))
    avg_cash_low_mult = float(res["cash"].to_numpy()[:n][low_mult_tier[:n]].mean()) if low_mult_tier[:n].any() else float("nan")
    avg_cash_high_mult = float(res["cash"].to_numpy()[:n][high_mult_tier[:n]].mean()) if high_mult_tier[:n].any() else float("nan")

    # Primary config's own average cash vs DCA (near_high_mult=1.0, so any
    # reserve here comes purely from weeks the ladder hasn't yet crossed
    # dur1_days -- expected to be small/neutral, checked for completeness).
    primary_decide = ddd.make_drawdown_duration_decider(daily, WEEKLY_DEPOSIT, **ddd.PRIMARY_CONFIG)
    primary_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, primary_decide).to_frame()
    avg_cash_primary = float(primary_res["cash"].mean())

    return {
        "reserve_arm_config": reserve_cfg,
        "avg_cash_strategy_reserve_arm": avg_cash_strategy,
        "avg_cash_dca_baseline": avg_cash_dca,
        "reserve_builds_up_vs_dca": bool(avg_cash_strategy > avg_cash_dca),
        "avg_cash_low_multiplier_weeks": avg_cash_low_mult,
        "avg_cash_high_multiplier_weeks": avg_cash_high_mult,
        "reserve_drawn_down_on_high_mult_weeks": bool(avg_cash_high_mult < avg_cash_low_mult),
        "avg_cash_primary_config": avg_cash_primary,
    }


def check_capital_never_exceeds_deposits(daily, rf, res: pd.DataFrame) -> bool:
    """Principled-bound version of the capital-neutrality check (family
    021's bugfix-log lesson): compare capital deployed vs. cumulative
    deposits against the "never invest" ceiling (max possible interest any
    cash trajectory on this same daily_rf path could have earned)."""
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
    """Pre-grid non-degeneracy sanity check: the primary config's
    multiplier must not be stuck at 1.0 for nearly the whole sample, and
    must show real dispersion."""
    cfg = ddd.PRIMARY_CONFIG
    rows = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        m = ddd.compute_multiplier(daily, **cfg)
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
    builder = decider_builder_factory(daily, **ddd.PRIMARY_CONFIG)

    divergence_check = check_real_divergence_example(dev)
    out["real_divergence_example"] = divergence_check
    out["distinctiveness_from_family_014_proven"] = bool(
        divergence_check["rankings_disagree_as_predicted"] and divergence_check["dates_all_pre_holdout"]
    )

    out["degenerate_bypass_equals_dca"] = v3chk.check_degenerate_equals_dca(daily, rf, builder, WEEKLY_DEPOSIT)
    out["flat_zero_grid_arm_equals_dca"] = check_flat_zero_arm_equals_dca(daily, rf)

    cash_check = check_cash_reserve_dynamics(daily, rf)
    out["cash_reserve_check"] = cash_check
    out["reserve_builds_up_vs_dca"] = cash_check["reserve_builds_up_vs_dca"]
    out["reserve_drawn_down_on_high_mult_weeks"] = cash_check["reserve_drawn_down_on_high_mult_weeks"]

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()
    out["no_negative_cash_units_dca"] = v3chk.check_no_negative_cash_or_units(res_dca)

    decide_primary = builder(enabled=True)
    res_primary = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_primary).to_frame()
    out["no_negative_cash_units_primary"] = v3chk.check_no_negative_cash_or_units(res_primary)
    out["capital_never_exceeds_deposits_primary"] = check_capital_never_exceeds_deposits(daily, rf, res_primary)

    aggressive_cfg = {"ath_lookback_years": 10, "ladder": "aggressive", "near_high_mult": 0.75, "max_lump_cap": 3.0}
    decide_agg = ddd.make_drawdown_duration_decider(daily, WEEKLY_DEPOSIT, **aggressive_cfg, enabled=True)
    res_agg = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_agg).to_frame()
    out["no_negative_cash_units_aggressive"] = v3chk.check_no_negative_cash_or_units(res_agg)
    out["capital_never_exceeds_deposits_aggressive"] = check_capital_never_exceeds_deposits(daily, rf, res_agg)

    out["no_lookahead"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=6000)
    out["no_lookahead_late"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=20000)
    out["point_in_time_macro"] = v3chk.check_point_in_time_macro()
    return out


def run_one(daily, rf, cfg, fee):
    decide = ddd.make_drawdown_duration_decider(daily, WEEKLY_DEPOSIT, **cfg)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def run_dca(daily, rf, fee):
    decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def cfg_id_for(ci, cfg):
    al = "none" if cfg["ath_lookback_years"] is None else str(cfg["ath_lookback_years"])
    return f"cfg{ci:02d}_al{al}_lad{cfg['ladder']}_nhm{cfg['near_high_mult']}_mlc{cfg['max_lump_cap']}"


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    rf = dev["rf"]

    print("Running real-divergence-from-family-014 check + implementation checks...")
    impl_checks = run_impl_checks(dev)
    print(json.dumps(impl_checks, indent=2, default=float))
    required = ["distinctiveness_from_family_014_proven",
                "reserve_builds_up_vs_dca", "reserve_drawn_down_on_high_mult_weeks",
                "degenerate_bypass_equals_dca", "flat_zero_grid_arm_equals_dca",
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

    configs = ddd.grid_configs()
    assert len(configs) <= 36
    assert ddd.PRIMARY_CONFIG in configs
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
                   "ath_lookback_years": cfg["ath_lookback_years"], "ladder": cfg["ladder"],
                   "near_high_mult": cfg["near_high_mult"], "max_lump_cap": cfg["max_lump_cap"]}
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
        trial_id = f"new_037_{cfg_id}"
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

    primary_ci = configs.index(ddd.PRIMARY_CONFIG)
    primary_cfg_id = cfg_id_for(primary_ci, ddd.PRIMARY_CONFIG)
    primary_trial_id = f"new_037_{primary_cfg_id}"
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
        print("Sec 4.1 PASSED -- run scripts/v3/robustness_037_drawdown_duration.py next "
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
            s, _ = run_one(daily, rf, ddd.PRIMARY_CONFIG, fee)
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
