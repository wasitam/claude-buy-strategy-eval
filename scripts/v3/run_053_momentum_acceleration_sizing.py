"""Run family 053 (momentum acceleration / "velocity of momentum" sizing)
end-to-end on development data: toy-arithmetic divergence check -> real
dev-period level-vs-acceleration divergence check (prereg.md's required
distinction from families 005/013/002) -> 2020+/unseen-ticker no-touch
assertion -> implementation checks -> pre-grid non-degeneracy check ->
full grid -> trial logging -> DSR/N_eff -> assess. Writes
state/trials/new_053_*.csv, updates state/trial_counter.json, and dumps
results into families/053-momentum-acceleration-sizing/_run_output.json
for the results.md writer. Modeled directly on
scripts/v3/run_044_hurst_regime_sizing.py's structure (continuous-
percentile-driven multiplier, same clip convention).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, metrics as v3met, dsr as v3dsr, checks as v3chk
from src.backtest.v3.strategies import momentum_acceleration_sizing as mas

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "053-momentum-acceleration-sizing")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]
HOLDOUT_CUTOFF = pd.Timestamp("2020-01-01")


def decider_builder_factory(daily, lookback_days, lag_days, k, min_mult, mom_cache=None):
    def builder(enabled=True):
        return mas.make_momentum_acceleration_decider(
            daily, WEEKLY_DEPOSIT, lookback_days=lookback_days, lag_days=lag_days,
            pctile_lookback=mas.PCTILE_LOOKBACK, k=k, min_mult=min_mult,
            max_mult=mas.MAX_MULT, max_lump_multiple=mas.MAX_LUMP_MULTIPLE,
            enabled=enabled, mom_cache=mom_cache,
        )
    return builder


def check_toy_divergence() -> dict:
    """Task-required checkpoint (b) of prereg.md: the constructed toy
    monthly-return example, recomputed here by direct arithmetic (not
    hand-copied), showing mom_now > 0 (level says "buy more") while
    accel < 0 (this family says "buy less")."""
    monthly_returns = {
        -5: 0.13, -4: 0.12, -3: 0.11, -2: 0.10, -1: 0.09, 0: 0.08,
        1: 0.07, 2: 0.06, 3: 0.05, 4: 0.04, 5: 0.03, 6: 0.02, 7: 0.01,
        8: 0.0, 9: 0.0, 10: 0.0, 11: 0.0, 12: 0.0,
    }

    def mom_at(end_month):
        prod = 1.0
        for m in range(end_month - 11, end_month + 1):
            prod *= (1.0 + monthly_returns[m])
        return prod - 1.0

    mom_now = mom_at(12)
    mom_past = mom_at(6)
    accel = mom_now - mom_past
    return {
        "mom_now": mom_now, "mom_past": mom_past, "accel": accel,
        "level_positive": bool(mom_now > 0), "accel_negative": bool(accel < 0),
        "divergence_demonstrated": bool(mom_now > 0 and accel < 0),
    }


def check_real_data_divergence(dev) -> dict:
    """Task-required checkpoint (c) of prereg.md: three real dev-period
    readings of this family's own production compute_momentum_level /
    compute_acceleration functions (SP500 2004-07-06, GOLD 2007-02-09,
    BTC 2018-03-26), lookback_days=252, lag_days=126 (the primary config),
    proving the level-vs-acceleration sign divergence on real data, not
    just a synthetic construction. Verifies every date used is strictly
    before the sealed holdout cutoff."""
    checks = {
        "SP500": "2004-07-06",
        "GOLD": "2007-02-09",
        "BTC": "2018-03-26",
    }
    lookback_days, lag_days = 252, 126
    out = {}
    dates_ok = True
    for asset, date_str in checks.items():
        ts = pd.Timestamp(date_str)
        if ts >= HOLDOUT_CUTOFF:
            dates_ok = False
        daily = dev["prices"][asset]
        mom = mas.compute_momentum_level(daily, lookback_days)
        accel = mas.compute_acceleration(daily, lookback_days, lag_days, mom_cache=mom)
        idx = daily.index.get_indexer([ts], method="nearest")[0]
        mom_now = float(mom[idx])
        mom_past = float(mom[idx - lag_days]) if idx - lag_days >= 0 else float("nan")
        out[asset] = {
            "date": str(daily.index[idx].date()), "mom_now": mom_now,
            "mom_past": mom_past, "accel": float(accel[idx]),
            "level_positive": bool(mom_now > 0), "accel_negative": bool(accel[idx] < 0),
        }
    divergence_all = all(v["level_positive"] and v["accel_negative"] for v in out.values())
    return {"by_asset": out, "dates_all_pre_holdout": dates_ok, "divergence_demonstrated_all": divergence_all}


def check_flat_k_zero_equals_dca(daily, rf) -> bool:
    """Family-specific second reference point (two-reference-point
    degenerate-config pattern, per families 014/020/033/034/035/036/044
    precedent): k=0.0 (a real grid-shaped code path, not the enabled=False
    bypass) forces m_t=clip(1+0*(...), min_mult, max_mult)=1.0 for every
    day regardless of pctile_t, since min_mult<1.0<max_mult always holds on
    the declared grid -- must also reproduce plain DCA bit-for-bit."""
    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    dca_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()

    flat_decide = mas.make_momentum_acceleration_decider(
        daily, WEEKLY_DEPOSIT, lookback_days=252, lag_days=126,
        pctile_lookback=252, k=0.0, min_mult=0.5, enabled=True,
    )
    flat_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, flat_decide).to_frame()

    ok_units = np.allclose(dca_res["units"].to_numpy(), flat_res["units"].to_numpy(), atol=1e-8)
    ok_cash = np.allclose(dca_res["cash"].to_numpy(), flat_res["cash"].to_numpy(), atol=1e-6)
    return bool(ok_units and ok_cash)


def check_cash_reserve_dynamics(daily, rf, mom_cache) -> dict:
    """Cash-reserve check (family 033's lesson, generalized by families
    036/044's precedent for a continuous multiplier): with min_mult=0.5<1.0
    in the primary config, confirm a genuine reserve is banked overall and
    drawn down further during high-percentile (accelerating, m_t>1) weeks
    than during low-percentile (decelerating, m_t<1) weeks."""
    cfg = mas.PRIMARY_CONFIG
    decide = mas.make_momentum_acceleration_decider(
        daily, WEEKLY_DEPOSIT, **cfg, pctile_lookback=mas.PCTILE_LOOKBACK,
        max_mult=mas.MAX_MULT, max_lump_multiple=mas.MAX_LUMP_MULTIPLE, mom_cache=mom_cache,
    )
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide).to_frame()

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()

    avg_cash_strategy = float(res["cash"].mean())
    avg_cash_dca = float(res_dca["cash"].mean())

    m = mas.compute_multiplier(daily, cfg["lookback_days"], cfg["lag_days"], mas.PCTILE_LOOKBACK,
                                cfg["k"], cfg["min_mult"], max_mult=mas.MAX_MULT, mom_cache=mom_cache)
    low_mult_tier = m < 1.0
    high_mult_tier = m > 1.0
    n = min(len(res), len(m))
    avg_cash_low_mult = float(res["cash"].to_numpy()[:n][low_mult_tier[:n]].mean()) if low_mult_tier[:n].any() else float("nan")
    avg_cash_high_mult = float(res["cash"].to_numpy()[:n][high_mult_tier[:n]].mean()) if high_mult_tier[:n].any() else float("nan")
    pct_diff = abs(avg_cash_strategy - avg_cash_dca) / max(avg_cash_dca, 1e-9)

    return {
        "avg_cash_strategy": avg_cash_strategy,
        "avg_cash_dca_baseline": avg_cash_dca,
        "cash_meaningfully_differs_from_dca": bool(pct_diff > 0.05),
        "avg_cash_low_multiplier_weeks": avg_cash_low_mult,
        "avg_cash_high_multiplier_weeks": avg_cash_high_mult,
        "reserve_drawn_down_on_high_mult_weeks": bool(avg_cash_high_mult < avg_cash_low_mult),
    }


def check_capital_never_exceeds_deposits(daily, rf, res: pd.DataFrame) -> bool:
    """Principled-bound version of the capital-neutrality check (family
    021's bugfix-log lesson): compare capital deployed vs. cumulative
    deposits against the "never invest" ceiling (max possible interest any
    cash trajectory on this same daily_rf path could have earned), not a
    flat percentage tolerance."""
    never_invest_decide = lambda t, cash: (0.0, 0.0, {})
    ceiling_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, never_invest_decide).to_frame()
    cum_deposit = res["deposit"].cumsum().to_numpy()
    cum_deposit_ceiling = ceiling_res["deposit"].cumsum().to_numpy()
    interest_ceiling = ceiling_res["cash"].to_numpy() - cum_deposit_ceiling
    cum_buy = res["buy_usd"].cumsum().to_numpy()
    excess = cum_buy - cum_deposit
    bound = interest_ceiling + 1e-6
    return bool(np.all(excess <= bound))


def run_sanity_check(dev, mom_caches):
    """Pre-grid non-degeneracy sanity check: the primary config's
    multiplier must not be stuck at 1.0 for nearly the whole sample, and
    must show real dispersion."""
    cfg = mas.PRIMARY_CONFIG
    rows = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        m = mas.compute_multiplier(daily, cfg["lookback_days"], cfg["lag_days"], mas.PCTILE_LOOKBACK,
                                    cfg["k"], cfg["min_mult"], max_mult=mas.MAX_MULT,
                                    mom_cache=mom_caches[(asset, cfg["lookback_days"])])
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


def run_impl_checks(dev, mom_caches):
    out = {}
    daily = dev["prices"]["SP500"]
    rf = dev["rf"]
    primary_cache = mom_caches[("SP500", mas.PRIMARY_CONFIG["lookback_days"])]
    builder = decider_builder_factory(daily, **mas.PRIMARY_CONFIG, mom_cache=primary_cache)

    toy = check_toy_divergence()
    out["toy_divergence"] = toy
    out["toy_divergence_demonstrated"] = toy["divergence_demonstrated"]

    real_div = check_real_data_divergence(dev)
    out["real_data_divergence"] = real_div
    out["real_divergence_demonstrated"] = real_div["divergence_demonstrated_all"]
    out["real_divergence_dates_pre_holdout"] = real_div["dates_all_pre_holdout"]

    out["degenerate_bypass_equals_dca"] = v3chk.check_degenerate_equals_dca(daily, rf, builder, WEEKLY_DEPOSIT)
    out["flat_k_zero_grid_arm_equals_dca"] = check_flat_k_zero_equals_dca(daily, rf)

    cash_check = check_cash_reserve_dynamics(daily, rf, primary_cache)
    out["cash_reserve_check"] = cash_check
    out["cash_meaningfully_differs_from_dca"] = cash_check["cash_meaningfully_differs_from_dca"]
    out["reserve_drawn_down_on_high_mult_weeks"] = cash_check["reserve_drawn_down_on_high_mult_weeks"]

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()
    out["no_negative_cash_units_dca"] = v3chk.check_no_negative_cash_or_units(res_dca)

    decide_primary = builder(enabled=True)
    res_primary = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_primary).to_frame()
    out["no_negative_cash_units_primary"] = v3chk.check_no_negative_cash_or_units(res_primary)
    out["capital_never_exceeds_deposits_primary"] = check_capital_never_exceeds_deposits(daily, rf, res_primary)

    aggressive_cfg = {"lookback_days": 126, "lag_days": 63, "k": 1.5, "min_mult": 0.25}
    decide_agg = mas.make_momentum_acceleration_decider(
        daily, WEEKLY_DEPOSIT, **aggressive_cfg, pctile_lookback=mas.PCTILE_LOOKBACK,
        max_mult=mas.MAX_MULT, max_lump_multiple=mas.MAX_LUMP_MULTIPLE, enabled=True,
        mom_cache=mom_caches[("SP500", 126)],
    )
    res_agg = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_agg).to_frame()
    out["no_negative_cash_units_aggressive"] = v3chk.check_no_negative_cash_or_units(res_agg)
    out["capital_never_exceeds_deposits_aggressive"] = check_capital_never_exceeds_deposits(daily, rf, res_agg)

    out["no_lookahead"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=6000)
    out["no_lookahead_late"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=20000)
    out["point_in_time_macro"] = v3chk.check_point_in_time_macro()
    return out


def run_one(daily, rf, cfg, fee, mom_cache):
    decide = mas.make_momentum_acceleration_decider(
        daily, WEEKLY_DEPOSIT, **cfg, pctile_lookback=mas.PCTILE_LOOKBACK,
        max_mult=mas.MAX_MULT, max_lump_multiple=mas.MAX_LUMP_MULTIPLE, mom_cache=mom_cache,
    )
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def run_dca(daily, rf, fee):
    decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def cfg_id_for(ci, cfg):
    return f"cfg{ci:02d}_lb{cfg['lookback_days']}_lag{cfg['lag_days']}_k{cfg['k']}_mn{cfg['min_mult']}"


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    rf = dev["rf"]

    print("Building per-(asset, lookback_days) momentum-level cache...")
    mom_caches = {}
    for asset in ASSETS:
        daily = dev["prices"][asset]
        for lb in mas.GRID["lookback_days"]:
            mom_caches[(asset, lb)] = mas.compute_momentum_level(daily, lb)
            print(f"  cached ({asset}, lookback_days={lb})")

    print("Running toy + real-data divergence checks + implementation checks...")
    impl_checks = run_impl_checks(dev, mom_caches)
    print(json.dumps(impl_checks, indent=2, default=float))
    required = ["toy_divergence_demonstrated", "real_divergence_demonstrated", "real_divergence_dates_pre_holdout",
                "degenerate_bypass_equals_dca", "flat_k_zero_grid_arm_equals_dca",
                "cash_meaningfully_differs_from_dca", "reserve_drawn_down_on_high_mult_weeks",
                "no_negative_cash_units_dca", "no_negative_cash_units_primary",
                "capital_never_exceeds_deposits_primary", "no_negative_cash_units_aggressive",
                "capital_never_exceeds_deposits_aggressive", "no_lookahead", "no_lookahead_late",
                "point_in_time_macro"]
    if not all(impl_checks[k] for k in required):
        raise SystemExit("Implementation checks FAILED -- stopping before any trusted backtest.")

    print("Running pre-grid non-degeneracy sanity check...")
    sanity = run_sanity_check(dev, mom_caches)
    print(json.dumps(sanity, indent=2))
    for row in sanity:
        if not row["non_degenerate"]:
            raise SystemExit(f"Sanity check FAILED for {row['asset']}: "
                              f"frac_default_1.0={row['frac_multiplier_exactly_1.0']:.4f} "
                              f"std_m={row['std_multiplier']:.4f} -- degenerate multiplier, stopping before grid.")

    configs = mas.grid_configs()
    assert len(configs) <= 36
    assert mas.PRIMARY_CONFIG in configs
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
            mom_cache = mom_caches[(asset, cfg["lookback_days"])]
            row = {"config_id": cfg_id, "asset": asset,
                   "lookback_days": cfg["lookback_days"], "lag_days": cfg["lag_days"],
                   "k": cfg["k"], "min_mult": cfg["min_mult"]}
            for fee in FEES:
                s, res = run_one(daily, rf, cfg, fee, mom_cache)
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
        trial_id = f"new_053_{cfg_id}"
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

    primary_ci = configs.index(mas.PRIMARY_CONFIG)
    primary_cfg_id = cfg_id_for(primary_ci, mas.PRIMARY_CONFIG)
    primary_trial_id = f"new_053_{primary_cfg_id}"
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
        print("Sec 4.1 PASSED -- run scripts/v3/robustness_053_momentum_acceleration_sizing.py next "
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
        mom_cache = mom_caches[(asset, mas.PRIMARY_CONFIG["lookback_days"])]
        row = {"asset": asset}
        for fee in FEES:
            s, _ = run_one(daily, rf, mas.PRIMARY_CONFIG, fee, mom_cache)
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
