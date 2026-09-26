"""Run family 035 (Parkinson range-based realized-vol sizing) end-to-end on
development data: Parkinson-estimator correctness spot-check -> concrete
numeric-divergence check vs. a close-to-close estimator (prereg.md's
required distinction from family 003) -> implementation checks -> pre-grid
non-degeneracy sanity check -> full grid -> trial logging -> DSR/N_eff ->
assess. Writes state/trials/new_035_*.csv, updates
state/trial_counter.json, and dumps results into
families/035-parkinson-vol-sizing/_run_output.json for the results.md
writer. Modeled directly on scripts/v3/run_034_low52wk_tilt.py's structure,
which was itself modeled on run_020, adapted for this family's
close-to-close-vs-range-based-estimator distinction from family 003
(vol_managed_sizing) instead of family 034's own distinction from family
020.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, metrics as v3met, dsr as v3dsr, checks as v3chk
from src.backtest.v3.strategies import parkinson_vol_sizing as pvs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "035-parkinson-vol-sizing")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]


def decider_builder_factory(daily, park_lookback_days, ref_lookback_days, min_mult, max_mult):
    def builder(enabled=True):
        return pvs.make_parkinson_vol_decider(
            daily, WEEKLY_DEPOSIT, park_lookback_days=park_lookback_days,
            ref_lookback_days=ref_lookback_days, min_mult=min_mult, max_mult=max_mult, enabled=enabled,
        )
    return builder


def check_parkinson_formula_spotcheck() -> dict:
    """Task-required check (b): verify the Parkinson estimator's formula
    (High/Low ratio, natural log, the 1/(4 ln 2) constant) against a few
    real, known-volatile days, computed BY HAND from raw prices, not by
    calling the module under test -- an independent re-derivation."""
    cases = [
        # (asset label used only for reporting, prior_close unused here since
        #  the Parkinson day-variance formula does not use Close at all --
        #  High/Low only), High, Low
        ("SILVER 2011-09-26 (large intraday range)", 30.78499984741211, 26.584999084472656),
        ("BTC 2015-11-04 (large intraday range)", 495.562012, 380.548004),
        ("SP500 1928-01-03 (degenerate, High==Low)", 17.760000, 17.760000),
    ]
    rows = []
    all_ok = True
    for label, high, low in cases:
        hand_log_range = np.log(high / low)
        hand_var = (hand_log_range ** 2) / (4.0 * np.log(2.0))
        # Cross-check against the module's own vectorized function on a
        # 1-row synthetic frame.
        df = pd.DataFrame({"High": [high], "Low": [low], "Close": [low], "Open": [low]})
        module_var = pvs.parkinson_daily_variance(df)[0]
        ok = bool(np.isclose(hand_var, module_var, atol=1e-12))
        all_ok = all_ok and ok
        rows.append({"case": label, "high": high, "low": low, "hand_computed_variance": float(hand_var),
                     "module_computed_variance": float(module_var), "match": ok})
    return {"cases": rows, "all_match": all_ok}


def check_numeric_divergence_vs_003(dev) -> dict:
    """Task-required concrete numeric-divergence check (c), and prereg.md's
    section (c): on real SILVER dev data, find the specific
    2011-09-26 day (a large high-low range with a close near the prior
    close) and show its single-day Parkinson-vol contribution is far
    larger than its single-day close-to-close-vol contribution -- proof
    the two estimators are not redundant on the same input."""
    daily = dev["prices"]["SILVER"]
    target = pd.Timestamp("2011-09-26")
    idx = daily.index.get_loc(target)
    prior_close = float(daily["Close"].iloc[idx - 1])
    close = float(daily["Close"].iloc[idx])
    high = float(daily["High"].iloc[idx])
    low = float(daily["Low"].iloc[idx])

    c2c_ret = np.log(close / prior_close)
    c2c_day_var = c2c_ret ** 2
    c2c_day_vol_ann = float(np.sqrt(c2c_day_var * 252))

    park_day_var = pvs.parkinson_daily_variance(daily)[idx]
    park_day_vol_ann = float(np.sqrt(park_day_var * 252))

    ratio = park_day_vol_ann / c2c_day_vol_ann if c2c_day_vol_ann > 0 else float("inf")
    return {
        "asset": "SILVER", "date": str(target.date()),
        "prior_close": prior_close, "close": close, "high": high, "low": low,
        "close_to_close_log_return": float(c2c_ret),
        "close_to_close_single_day_annualized_vol": c2c_day_vol_ann,
        "parkinson_single_day_annualized_vol": park_day_vol_ann,
        "ratio_parkinson_over_close_to_close": ratio,
        "divergence_confirmed": bool(ratio > 5.0),
    }


def check_flat_ratio_one_equals_dca(daily, rf) -> bool:
    """Family-specific second reference point (two-reference-point
    degenerate-config pattern, per family 014/020/033/034 precedent):
    min_mult=max_mult=1.0 (a real grid-arm-shaped code path forcing the
    clip band to a single point, run through the actual Parkinson
    computation, enabled=True, not the enabled=False bypass) must also
    reproduce plain DCA bit-for-bit, since clip(anything, 1.0, 1.0) == 1.0
    for every day regardless of the underlying ratio."""
    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    dca_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()

    flat_decide = pvs.make_parkinson_vol_decider(
        daily, WEEKLY_DEPOSIT, park_lookback_days=60, ref_lookback_days=252,
        min_mult=1.0, max_mult=1.0, enabled=True,
    )
    flat_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, flat_decide).to_frame()

    ok_units = np.allclose(dca_res["units"].to_numpy(), flat_res["units"].to_numpy(), atol=1e-8)
    ok_cash = np.allclose(dca_res["cash"].to_numpy(), flat_res["cash"].to_numpy(), atol=1e-6)
    return bool(ok_units and ok_cash)


def check_cash_reserve_dynamics(daily, rf) -> dict:
    """Task-required cash-reserve check, per family 033's lesson: with
    min_mult=0.5<1.0 in the primary config, confirm a genuine reserve is
    banked during high-recent-range-vol weeks (average cash share higher
    than plain DCA) and drawn down during low-recent-range-vol weeks
    (average cash share lower when m_t>1 than when m_t<1)."""
    cfg = pvs.PRIMARY_CONFIG
    decide = pvs.make_parkinson_vol_decider(daily, WEEKLY_DEPOSIT, **cfg)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide).to_frame()

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()

    avg_cash_strategy = float(res["cash"].mean())
    avg_cash_dca = float(res_dca["cash"].mean())

    m = pvs.compute_multiplier(daily, cfg["park_lookback_days"], cfg["ref_lookback_days"],
                                cfg["min_mult"], cfg["max_mult"])
    low_mult_tier = m < 1.0   # high recent range-vol -> under-invest -> should bank cash
    high_mult_tier = m > 1.0  # low recent range-vol -> over-invest -> should draw cash down
    n = min(len(res), len(m))
    avg_cash_low_mult = float(res["cash"].to_numpy()[:n][low_mult_tier[:n]].mean()) if low_mult_tier[:n].any() else float("nan")
    avg_cash_high_mult = float(res["cash"].to_numpy()[:n][high_mult_tier[:n]].mean()) if high_mult_tier[:n].any() else float("nan")

    return {
        "avg_cash_strategy": avg_cash_strategy,
        "avg_cash_dca_baseline": avg_cash_dca,
        "reserve_builds_up_vs_dca": bool(avg_cash_strategy > avg_cash_dca),
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
    # Ceiling on capital deployed vs cumulative deposits: the max extra
    # beyond deposits any decider could ever have earned on this path is
    # the interest earned by a 100%-cash ("never invest") decider (family
    # 021's bugfix-log fix -- a principled bound, not a flat percentage).
    cum_deposit = res["deposit"].cumsum().to_numpy()
    cum_deposit_ceiling = ceiling_res["deposit"].cumsum().to_numpy()
    interest_ceiling = ceiling_res["cash"].to_numpy() - cum_deposit_ceiling  # cash minus deposits = interest earned so far
    # Capital DEPLOYED (cumulative buy_usd) must never exceed cumulative
    # deposits + the never-invest ceiling's interest, plus a negligible
    # numerical tolerance.
    cum_buy = res["buy_usd"].cumsum().to_numpy()
    excess = cum_buy - cum_deposit
    bound = interest_ceiling + 1e-6
    return bool(np.all(excess <= bound))


def run_sanity_check(dev):
    """Pre-grid non-degeneracy sanity check: the primary config's
    multiplier must not be stuck at 1.0 (the "not enough history yet / no
    real range" default) for nearly the whole sample, and must show real
    dispersion (a materially different value than family 003's own
    close-to-close multiplier would show, spot-checked qualitatively).
    Also reports the fraction of degenerate High==Low days per asset per
    prereg.md's caveat (d)."""
    cfg = pvs.PRIMARY_CONFIG
    rows = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        m = pvs.compute_multiplier(daily, cfg["park_lookback_days"], cfg["ref_lookback_days"],
                                    cfg["min_mult"], cfg["max_mult"])
        n = len(m)
        frac_default_one = float(np.isclose(m, 1.0, atol=1e-9).mean())
        frac_degenerate_range_days = float((daily["High"].to_numpy() == daily["Low"].to_numpy()).mean())
        std_m = float(np.std(m))
        rows.append({
            "asset": asset, "dev_days": n,
            "frac_multiplier_exactly_1.0": frac_default_one,
            "frac_degenerate_high_eq_low_days": frac_degenerate_range_days,
            "std_multiplier": std_m,
            "non_degenerate": bool(frac_default_one <= 0.90 and std_m > 0.01),
        })
    return rows


def run_impl_checks(dev):
    out = {}
    daily = dev["prices"]["SP500"]
    rf = dev["rf"]
    builder = decider_builder_factory(daily, **pvs.PRIMARY_CONFIG)

    formula_check = check_parkinson_formula_spotcheck()
    out["formula_spotcheck"] = formula_check
    out["formula_correct"] = formula_check["all_match"]

    divergence_check = check_numeric_divergence_vs_003(dev)
    out["numeric_divergence_vs_003"] = divergence_check
    out["divergence_confirmed"] = divergence_check["divergence_confirmed"]

    cash_check = check_cash_reserve_dynamics(daily, rf)
    out["cash_reserve_check"] = cash_check
    out["reserve_builds_up_vs_dca"] = cash_check["reserve_builds_up_vs_dca"]
    out["reserve_drawn_down_on_high_mult_weeks"] = cash_check["reserve_drawn_down_on_high_mult_weeks"]

    out["degenerate_bypass_equals_dca"] = v3chk.check_degenerate_equals_dca(daily, rf, builder, WEEKLY_DEPOSIT)
    out["flat_ratio_one_grid_arm_equals_dca"] = check_flat_ratio_one_equals_dca(daily, rf)

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()
    out["no_negative_cash_units_dca"] = v3chk.check_no_negative_cash_or_units(res_dca)

    decide_primary = builder(enabled=True)
    res_primary = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_primary).to_frame()
    out["no_negative_cash_units_primary"] = v3chk.check_no_negative_cash_or_units(res_primary)
    out["capital_never_exceeds_deposits_primary"] = check_capital_never_exceeds_deposits(daily, rf, res_primary)

    aggressive_cfg = {"park_lookback_days": 20, "ref_lookback_days": 126, "min_mult": 0.25, "max_mult": 3.0}
    decide_agg = pvs.make_parkinson_vol_decider(daily, WEEKLY_DEPOSIT, **aggressive_cfg, enabled=True)
    res_agg = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_agg).to_frame()
    out["no_negative_cash_units_aggressive"] = v3chk.check_no_negative_cash_or_units(res_agg)
    out["capital_never_exceeds_deposits_aggressive"] = check_capital_never_exceeds_deposits(daily, rf, res_agg)

    out["no_lookahead"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=6000)
    out["no_lookahead_late"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=20000)
    out["point_in_time_macro"] = v3chk.check_point_in_time_macro()
    return out


def run_one(daily, rf, cfg, fee):
    decide = pvs.make_parkinson_vol_decider(daily, WEEKLY_DEPOSIT, **cfg)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def run_dca(daily, rf, fee):
    decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def cfg_id_for(ci, cfg):
    return f"cfg{ci:02d}_pl{cfg['park_lookback_days']}_rl{cfg['ref_lookback_days']}_mn{cfg['min_mult']}_mx{cfg['max_mult']}"


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    rf = dev["rf"]

    print("Running formula spot-check + numeric-divergence + implementation checks...")
    impl_checks = run_impl_checks(dev)
    print(json.dumps(impl_checks, indent=2, default=float))
    required = ["formula_correct", "divergence_confirmed",
                "reserve_builds_up_vs_dca", "reserve_drawn_down_on_high_mult_weeks",
                "degenerate_bypass_equals_dca", "flat_ratio_one_grid_arm_equals_dca",
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

    configs = pvs.grid_configs()
    assert len(configs) <= 36
    assert pvs.PRIMARY_CONFIG in configs
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
                   "park_lookback_days": cfg["park_lookback_days"], "ref_lookback_days": cfg["ref_lookback_days"],
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
        trial_id = f"new_035_{cfg_id}"
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

    primary_ci = configs.index(pvs.PRIMARY_CONFIG)
    primary_cfg_id = cfg_id_for(primary_ci, pvs.PRIMARY_CONFIG)
    primary_trial_id = f"new_035_{primary_cfg_id}"
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
        print("Sec 4.1 PASSED -- run scripts/v3/robustness_035_parkinson_vol_sizing.py next "
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
            s, _ = run_one(daily, rf, pvs.PRIMARY_CONFIG, fee)
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
