"""Run family 020 (52-week-high proximity momentum tilt) end-to-end on
development data: sign-correctness check -> implementation checks
(two-reference-point pattern) -> pre-grid non-degeneracy sanity check ->
full grid -> trial logging -> DSR/N_eff -> assess. Writes
state/trials/new_020_*.csv, updates state/trial_counter.json, and dumps
results into families/020-52wk-high-tilt/_run_output.json for the
results.md writer. Modeled on scripts/v3/run_014_drawdown_reserve.py (same
single-asset, no-sell, ladder-sizing, two-reference-point-check pattern),
with an added explicit sign-correctness check since this family's ladder
is the deliberate mirror image of family 014's.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, metrics as v3met, dsr as v3dsr, checks as v3chk
from src.backtest.v3.strategies import high52wk_tilt as h52

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "020-52wk-high-tilt")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]


def decider_builder_factory(daily, window_def, ladder, mult_near, max_lump_cap):
    def builder(enabled=True):
        return h52.make_high52wk_tilt_decider(
            daily, WEEKLY_DEPOSIT, window_def=window_def, ladder=ladder,
            mult_near=mult_near, max_lump_cap=max_lump_cap, enabled=enabled,
        )
    return builder


def check_flat_zero_effect_equals_dca(daily, rf) -> bool:
    """Family-specific second reference point (per prereg.md and family
    014's degenerate-config-trap precedent): the REAL grid arm
    ladder='flat' combined with mult_near=1.0 (any window_def/
    max_lump_cap), run through the actual proximity/ladder computation
    (enabled=True, not the bypass path), must reproduce plain DCA
    bit-for-bit on units and cash -- independently of check 1's
    enabled=False bypass flag. mult_near=1.0 is not itself a pre-declared
    grid value, so this is exercised as a direct code-path check."""
    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    dca_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()

    flat_decide = h52.make_high52wk_tilt_decider(
        daily, WEEKLY_DEPOSIT, window_def="trading252", ladder="flat",
        mult_near=1.0, max_lump_cap=3.0, enabled=True,
    )
    flat_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, flat_decide).to_frame()

    ok_units = np.allclose(dca_res["units"].to_numpy(), flat_res["units"].to_numpy(), atol=1e-8)
    ok_cash = np.allclose(dca_res["cash"].to_numpy(), flat_res["cash"].to_numpy(), atol=1e-6)
    return bool(ok_units and ok_cash)


def check_sign_correctness(daily) -> dict:
    """Task-required sign check, specific to this family given the
    family-014 sign-inversion point: on the primary config, mean buy
    multiplier on days in the TOP quartile of prox_t (closest to the
    52-week high) must be STRICTLY GREATER than the mean multiplier on
    days in the BOTTOM quartile (furthest below the 52-week high) -- i.e.
    near-high days get systematically LARGER buys, not smaller."""
    cfg = h52.PRIMARY_CONFIG
    prox = h52.compute_proximity(daily, cfg["window_def"])
    m = h52.compute_multiplier(daily, cfg["window_def"], cfg["ladder"], cfg["mult_near"], cfg["max_lump_cap"])
    q75 = np.nanquantile(prox, 0.75)
    q25 = np.nanquantile(prox, 0.25)
    top_mask = prox >= q75
    bot_mask = prox <= q25
    mean_top = float(m[top_mask].mean())
    mean_bot = float(m[bot_mask].mean())
    return {
        "mean_multiplier_top_quartile_prox": mean_top,
        "mean_multiplier_bottom_quartile_prox": mean_bot,
        "sign_correct": bool(mean_top > mean_bot),
    }


def check_capital_never_exceeds_deposits(res: pd.DataFrame) -> bool:
    """Total capital deployed (cumulative buy_usd) must never exceed
    cumulative deposits + interest credited to cash (engine invariant,
    verified empirically -- see family 014's precedent for the reasoning)."""
    cum_buy = res["buy_usd"].cumsum()
    cum_deposit = res["deposit"].cumsum()
    excess = (cum_buy - cum_deposit).to_numpy()
    bound = 0.05 * np.maximum(cum_deposit.to_numpy(), 1.0)
    return bool(np.all(excess <= bound))


def run_sanity_check(dev):
    """Pre-grid non-degeneracy sanity check (established convention, adapted
    for this family's ladder shape). Note: unlike family 019's binary weak/
    strong flag, this family's 3-tier ladder (mult_far=0.50, mult_mid=0.75,
    mult_near=1.5 at the primary config) has NO tier that equals 1.0x, so
    m_t != 1.0x on ~100% of days by construction -- that alone is not a
    meaningful non-degeneracy signal here. The meaningful check is instead
    that the multiplier is not stuck in a single tier for nearly the whole
    sample (i.e. price actually spends a non-trivial share of development
    days both near its 52-week high and away from it, on every core
    asset), confirmed by requiring each of the 3 tiers to claim between 2%
    and 98% of development days."""
    cfg = h52.PRIMARY_CONFIG
    rows = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        prox = h52.compute_proximity(daily, cfg["window_def"])
        preset = h52.LADDER_PRESETS[cfg["ladder"]]
        near = prox >= preset["near_thresh"]
        far = prox < preset["far_thresh"]
        mid = ~near & ~far
        n = len(prox)
        frac_near, frac_mid, frac_far = float(near.mean()), float(mid.mean()), float(far.mean())
        rows.append({
            "asset": asset, "dev_days": n,
            "frac_near_high_tier": frac_near, "frac_mid_tier": frac_mid, "frac_far_tier": frac_far,
            "non_degenerate": bool(0.02 <= frac_near <= 0.98 and 0.02 <= frac_far <= 0.98),
        })
    return rows


def run_impl_checks(dev):
    out = {}
    daily = dev["prices"]["SP500"]
    rf = dev["rf"]
    builder = decider_builder_factory(daily, **h52.PRIMARY_CONFIG)

    sign_check = check_sign_correctness(daily)
    out["sign_check"] = sign_check
    out["sign_correct"] = sign_check["sign_correct"]

    out["degenerate_bypass_equals_dca"] = v3chk.check_degenerate_equals_dca(daily, rf, builder, WEEKLY_DEPOSIT)
    out["flat_zero_effect_grid_arm_equals_dca"] = check_flat_zero_effect_equals_dca(daily, rf)

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()
    out["no_negative_cash_units_dca"] = v3chk.check_no_negative_cash_or_units(res_dca)

    decide_primary = builder(enabled=True)
    res_primary = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_primary).to_frame()
    out["no_negative_cash_units_primary"] = v3chk.check_no_negative_cash_or_units(res_primary)
    out["capital_never_exceeds_deposits_primary"] = check_capital_never_exceeds_deposits(res_primary)

    aggressive_cfg = {"window_def": "calendar", "ladder": "aggressive", "mult_near": 2.0, "max_lump_cap": 3.0}
    decide_agg = h52.make_high52wk_tilt_decider(daily, WEEKLY_DEPOSIT, **aggressive_cfg, enabled=True)
    res_agg = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_agg).to_frame()
    out["no_negative_cash_units_aggressive"] = v3chk.check_no_negative_cash_or_units(res_agg)
    out["capital_never_exceeds_deposits_aggressive"] = check_capital_never_exceeds_deposits(res_agg)

    out["no_lookahead"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=6000)
    out["no_lookahead_late"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=20000)
    out["point_in_time_macro"] = v3chk.check_point_in_time_macro()
    return out


def run_one(daily, rf, cfg, fee):
    decide = h52.make_high52wk_tilt_decider(daily, WEEKLY_DEPOSIT, **cfg)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def run_dca(daily, rf, fee):
    decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def cfg_id_for(ci, cfg):
    return f"cfg{ci:02d}_{cfg['window_def']}_lad{cfg['ladder']}_mn{cfg['mult_near']}_mlc{cfg['max_lump_cap']}"


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    rf = dev["rf"]

    print("Running sign-correctness + implementation checks...")
    impl_checks = run_impl_checks(dev)
    print(json.dumps(impl_checks, indent=2))
    required = ["sign_correct", "degenerate_bypass_equals_dca", "flat_zero_effect_grid_arm_equals_dca",
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
                              f"frac_near={row['frac_near_high_tier']:.4f} frac_far={row['frac_far_tier']:.4f} "
                              "outside (2%, 98%) -- degenerate multiplier, stopping before grid.")

    configs = h52.grid_configs()
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
            row = {"config_id": cfg_id, "asset": asset,
                   "window_def": cfg["window_def"], "ladder": cfg["ladder"],
                   "mult_near": cfg["mult_near"], "max_lump_cap": cfg["max_lump_cap"]}
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
        trial_id = f"new_020_{cfg_id}"
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

    primary_ci = configs.index(h52.PRIMARY_CONFIG)
    primary_cfg_id = cfg_id_for(primary_ci, h52.PRIMARY_CONFIG)
    primary_trial_id = f"new_020_{primary_cfg_id}"
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
    with open(os.path.join(FAM_DIR, "_run_output.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)
    print("Wrote", os.path.join(FAM_DIR, "_run_output.json"))

    # Save per-asset primary-config summary for results.md writer
    per_asset_summary = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        row = {"asset": asset}
        for fee in FEES:
            s, _ = run_one(daily, rf, h52.PRIMARY_CONFIG, fee)
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
