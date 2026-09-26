"""Run family 033 (volume-confirmed breakout sizing) end-to-end on
development data: pre-grid feasibility/non-degeneracy checks ->
implementation checks (including a Volume-aware no-lookahead test) -> full
grid -> trial logging -> DSR/N_eff -> assess. Writes
state/trials/new_033_*.csv, updates state/trial_counter.json, and dumps
results into families/033-volume-breakout/_run_output.json for the
results.md writer. Modeled on scripts/v3/run_028_ma_crossover_regime.py
and scripts/v3/run_021_amihud_illiquidity.py (the loop's other
Volume-using family).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, metrics as v3met, dsr as v3dsr, checks as v3chk
from src.backtest.v3.strategies import volume_breakout as vb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "033-volume-breakout")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]


def decider_builder_factory(daily, cfg):
    def builder(enabled=True):
        return vb.make_volume_breakout_decider(daily, WEEKLY_DEPOSIT, enabled=enabled, **cfg)
    return builder


def check_no_lookahead_with_volume(daily, daily_rf, decider_builder, t_check, weekly_deposit=500.0, seed=3):
    """This family's signal reads BOTH Close and Volume, so the standard
    check_no_lookahead (which only perturbs OHLC) is not sufficient on its
    own -- per this iteration's task brief, the trailing-volume-average
    computation must also be verified strictly causal. Perturbs Volume (in
    addition to OHLC) for every row AFTER t_check and confirms every order
    generated ON OR BEFORE t_check is unchanged."""
    rng = np.random.default_rng(seed)
    perturbed = daily.copy()
    perturbed["Volume"] = perturbed["Volume"].astype(float)
    n = len(daily)
    if t_check >= n - 2:
        t_check = n - 3
    noise = 1.0 + rng.normal(0, 0.2, size=n - t_check - 1)
    for col in ["Open", "High", "Low", "Close"]:
        perturbed.iloc[t_check + 1:, perturbed.columns.get_loc(col)] = (
            perturbed.iloc[t_check + 1:][col].to_numpy() * noise
        )
    # Volume-specific perturbation: replace future volume with a materially
    # different, always-positive random draw (not just multiplicative noise
    # on top of possibly-zero volume days), scaled to the asset's own
    # trailing volume level so it stays a plausible volume series.
    vol = perturbed["Volume"].to_numpy()
    future_vol_scale = np.nanmedian(vol[: t_check + 1][vol[: t_check + 1] > 0]) if (vol[: t_check + 1] > 0).any() else 1.0
    vol_noise = rng.uniform(0.1, 5.0, size=n - t_check - 1) * (future_vol_scale if np.isfinite(future_vol_scale) else 1.0)
    perturbed.iloc[t_check + 1:, perturbed.columns.get_loc("Volume")] = vol_noise

    decide_a = decider_builder(enabled=True)
    res_a = v3eng.run_single_asset(daily, weekly_deposit, daily_rf, decide_a).to_frame()

    decide_b = decider_builder(enabled=True)
    res_b = v3eng.run_single_asset(perturbed, weekly_deposit, daily_rf, decide_b).to_frame()

    a = res_a.iloc[: t_check + 1][["buy_usd", "sell_usd"]].to_numpy()
    b = res_b.iloc[: t_check + 1][["buy_usd", "sell_usd"]].to_numpy()
    return bool(np.allclose(a, b, atol=1e-6))


def run_sanity_checks(dev):
    """Pre-grid sanity checks (this iteration's task brief):
    (a) primary config in grid -- verified by module-import-time assertion
        in volume_breakout.py already; re-confirmed below.
    (b) the joint price+volume trigger fires non-trivially on every asset,
        and strictly less often than the price-only leg alone (proof the
        AND is actually binding, not a near-tautology with either leg)."""
    cfg = vb.PRIMARY_CONFIG
    rows = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        high = vb.compute_trailing_high(daily, cfg["window"])
        close = daily["Close"].to_numpy()
        price_only = np.isfinite(high) & (close > high)
        joint = vb.compute_joint_breakout(daily, cfg["window"], cfg["volume_surge_multiple"])
        n = len(daily)
        rows.append({
            "asset": asset, "n_days": n,
            "price_only_frac": float(price_only.mean()),
            "joint_frac": float(joint.mean()),
            "joint_rarer_than_price_only": bool(joint.mean() < price_only.mean()),
            "joint_non_degenerate": bool(0.001 < joint.mean() < 0.5),
        })
    return rows


def run_impl_checks(dev):
    out = {}
    daily = dev["prices"]["SP500"]
    rf = dev["rf"]
    cfg = vb.PRIMARY_CONFIG
    builder = decider_builder_factory(daily, cfg)

    out["degenerate_equals_dca"] = v3chk.check_degenerate_equals_dca(daily, rf, builder, WEEKLY_DEPOSIT)

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()
    out["no_negative_cash_units_dca"] = v3chk.check_no_negative_cash_or_units(res_dca)

    # Capital-vs-deposits check, family 021's principled-bound method: a
    # "never invest" reference run gives the true maximum interest ceiling
    # any cash trajectory could have earned on this asset's daily_rf path.
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
    out["capital_never_exceeds_deposits_plus_interest"] = bool(
        np.all(excess.to_numpy() <= max_interest_ceiling.to_numpy() + tol)
    )

    # Aggressive grid corner: shortest window, lowest surge threshold,
    # largest breakout multiplier, lowest normal multiplier.
    agg_cfg = {"window": 20, "volume_surge_multiple": 1.5, "breakout_buy_mult": 2.5,
               "normal_buy_mult": 0.75, "max_lump_multiple": 4.0}
    agg_builder = decider_builder_factory(daily, agg_cfg)
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

    # Standard OHLC-only no-lookahead check (families 001-032 convention).
    out["no_lookahead"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=6000)
    out["no_lookahead_late"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=20000)

    # Volume-aware no-lookahead check (this family's own extra requirement,
    # per this iteration's task brief): the trailing-volume-average leg
    # must also be strictly causal.
    out["no_lookahead_with_volume"] = check_no_lookahead_with_volume(daily, rf, builder, t_check=6000)
    out["no_lookahead_with_volume_late"] = check_no_lookahead_with_volume(daily, rf, builder, t_check=20000)

    return out


def run_one(daily, rf, cfg, fee):
    decide = vb.make_volume_breakout_decider(daily, WEEKLY_DEPOSIT, **cfg)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def run_dca(daily, rf, fee):
    decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def cfg_id_for(ci, cfg):
    return (f"cfg{ci:02d}_w{cfg['window']}_vsm{cfg['volume_surge_multiple']}"
            f"_bbm{cfg['breakout_buy_mult']}_nbm{cfg['normal_buy_mult']}")


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    rf = dev["rf"]

    print("Running pre-grid sanity checks (joint trigger non-degeneracy)...")
    sanity = run_sanity_checks(dev)
    print(json.dumps(sanity, indent=2))
    for row in sanity:
        if not row["joint_non_degenerate"]:
            raise SystemExit(f"Sanity check FAILED for {row['asset']}: joint_frac={row['joint_frac']:.4f} "
                              "outside (0.1%, 50%) -- degenerate joint trigger, stopping before grid.")
        if not row["joint_rarer_than_price_only"]:
            raise SystemExit(f"Sanity check FAILED for {row['asset']}: joint condition ({row['joint_frac']:.4f}) "
                              f"is not rarer than the price-only leg ({row['price_only_frac']:.4f}) -- the AND "
                              "is not binding, signal construction bug.")
    print("Non-degeneracy PASSED on all 5 assets: joint AND fires non-trivially and strictly "
          "less often than the price-only leg alone.")

    print("Running implementation checks...")
    impl_checks = run_impl_checks(dev)
    print(json.dumps(impl_checks, indent=2))
    required = ["degenerate_equals_dca", "no_negative_cash_units_dca", "no_negative_cash_units_primary",
                "capital_never_exceeds_deposits_plus_interest", "no_negative_cash_units_aggressive",
                "capital_never_exceeds_deposits_aggressive", "no_lookahead", "no_lookahead_late",
                "no_lookahead_with_volume", "no_lookahead_with_volume_late"]
    if not all(impl_checks[k] for k in required):
        raise SystemExit("Implementation checks FAILED -- stopping before any trusted backtest.")

    configs = vb.grid_configs()
    assert len(configs) <= 36
    assert vb.PRIMARY_CONFIG in configs
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
        trial_id = f"new_033_{cfg_id}"
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

    primary_ci = configs.index(vb.PRIMARY_CONFIG)
    primary_cfg_id = cfg_id_for(primary_ci, vb.PRIMARY_CONFIG)
    primary_trial_id = f"new_033_{primary_cfg_id}"
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
        print("Sec 4.1 PASSED -- run scripts/v3/robustness_033_volume_breakout.py next "
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
            s, _ = run_one(daily, rf, vb.PRIMARY_CONFIG, fee)
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
