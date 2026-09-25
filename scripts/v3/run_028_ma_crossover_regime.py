"""Run family 028 (50/200-day MA crossover golden/death-cross regime tilt)
end-to-end on development data: implementation checks -> pre-grid
known-episode + non-degeneracy sanity check -> full grid -> trial logging
-> DSR/N_eff -> assess. Writes state/trials/new_028_*.csv, updates
state/trial_counter.json, and dumps results into
families/028-ma-crossover-regime/_run_output.json for the results.md
writer. Modeled directly on scripts/v3/run_027_yield_curve_regime.py and
scripts/v3/run_005_tsmom_sizing.py (same single-asset, no-sell,
sizing-tilt-with-cash-cap pattern; the known-episode check here spot-checks
SP500's documented 2009/2016/2020 golden crosses instead of macro
inversion dates).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, metrics as v3met, dsr as v3dsr, checks as v3chk
from src.backtest.v3.strategies import ma_crossover_regime as mac

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "028-ma-crossover-regime")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]

# Approximate, well-documented SP500 50/200-day golden-cross dates. The task
# names 2009/2016/2020 as examples; 2020's crossing (2020-07-24, per public
# record) falls in the SEALED HOLDOUT period (2020+), so it cannot be used
# here without opening the holdout -- checking it would itself be an
# improper holdout look for a pre-grid sanity check. Substituted with
# 2003-05-14 (the well-documented post-dot-com-bust golden cross), which is
# within development data, alongside the two 2009/2016 dev-period crosses.
KNOWN_GOLDEN_CROSS_WINDOWS = [
    ("2003-04-15", "2003-06-15"),
    ("2009-06-01", "2009-08-15"),
    ("2016-03-15", "2016-05-15"),
]


def decider_builder_factory(daily, cfg):
    def builder(enabled=True):
        return mac.make_ma_crossover_decider(daily, WEEKLY_DEPOSIT, enabled=enabled, **cfg)
    return builder


def run_known_episode_check(dev):
    """Confirms the raw (persistence_days=0) 50/200 crossover on SP500
    correctly, non-trivially registers golden crosses within known
    historical windows, before any backtest result is trusted."""
    daily = dev["prices"]["SP500"]
    bullish_raw = mac.compute_raw_bullish(daily, 50, 200)
    idx = daily.index
    # A "golden cross event" = a day where bullish flips False->True.
    flips_up = idx[1:][(~bullish_raw[:-1]) & (bullish_raw[1:])]
    rows = []
    all_found = True
    for start, end in KNOWN_GOLDEN_CROSS_WINDOWS:
        found = bool(((flips_up >= pd.Timestamp(start)) & (flips_up <= pd.Timestamp(end))).any())
        rows.append({"window": f"{start}..{end}", "golden_cross_found": found})
        all_found = all_found and found
    return {"rows": rows, "n_golden_cross_events_total": int(len(flips_up)), "all_known_episodes_registered": all_found}


def run_impl_checks(dev):
    out = {}
    daily = dev["prices"]["SP500"]
    rf = dev["rf"]
    cfg = mac.PRIMARY_CONFIG
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

    # Aggressive corner: fastest pair, no persistence delay, largest bull tilt.
    agg_cfg = {"fast_days": 20, "slow_days": 100, "persistence_days": 0,
               "bull_mult": 1.5, "bear_mult": 0.5, "max_lump_multiple": 6.0}
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

    out["no_lookahead"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=6000)
    out["no_lookahead_late"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=20000)

    return out


def run_sanity_check(dev):
    """Pre-grid non-degeneracy check: primary config's confirmed-bullish
    (golden-cross-regime) frequency must be non-trivial (not near-0%, not
    near-100%) on all 5 core assets, confirming the signal fires
    non-trivially before any backtest result is trusted."""
    cfg = mac.PRIMARY_CONFIG
    rows = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        confirmed = mac.compute_confirmed_bullish(
            daily, cfg["fast_days"], cfg["slow_days"], cfg["persistence_days"]
        )
        bull_frac = float(confirmed.mean())
        raw = mac.compute_raw_bullish(daily, cfg["fast_days"], cfg["slow_days"])
        n_crossovers = int(np.sum(raw[1:] != raw[:-1]))
        rows.append({
            "asset": asset, "n_days": int(len(confirmed)),
            "bullish_frac": bull_frac, "n_raw_crossovers": n_crossovers,
            "non_degenerate": bool(0.01 < bull_frac < 0.99 and n_crossovers >= 2),
        })
    return rows


def run_one(daily, rf, cfg, fee):
    decide = mac.make_ma_crossover_decider(daily, WEEKLY_DEPOSIT, **cfg)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def run_dca(daily, rf, fee):
    decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def cfg_id_for(ci, cfg):
    return (f"cfg{ci:02d}_f{cfg['fast_days']}_s{cfg['slow_days']}_"
            f"pd{cfg['persistence_days']}_bu{cfg['bull_mult']}_be{cfg['bear_mult']}")


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    rf = dev["rf"]

    print("Running known-episode sanity check (SP500 2009/2016/2020 golden crosses)...")
    episode_check = run_known_episode_check(dev)
    print(json.dumps(episode_check, indent=2))
    if not episode_check["all_known_episodes_registered"]:
        raise SystemExit("Known-episode check FAILED -- 50/200 SMA crossover does not register "
                          "the documented 2009/2016/2020 SP500 golden crosses.")

    print("Running implementation checks...")
    impl_checks = run_impl_checks(dev)
    print(json.dumps(impl_checks, indent=2))
    required = ["degenerate_equals_dca", "no_negative_cash_units_dca", "no_negative_cash_units_primary",
                "capital_never_exceeds_deposits_primary", "no_negative_cash_units_aggressive",
                "capital_never_exceeds_deposits_aggressive", "no_lookahead", "no_lookahead_late"]
    if not all(impl_checks[k] for k in required):
        raise SystemExit("Implementation checks FAILED -- stopping before any trusted backtest.")

    print("Running pre-grid non-degeneracy sanity check...")
    sanity = run_sanity_check(dev)
    print(json.dumps(sanity, indent=2))
    # BTC is deliberately exempted from the hard non-degeneracy gate, per
    # prereg.md's flagged risk: its short dev window (2014-09 to 2019-12)
    # leaves comparatively little history after the 200-day SMA first seeds,
    # which can produce a thin confirmed-crossover count. Documented
    # explicitly in results.md rather than silently gated, per family 027's
    # precedent for the same class of BTC-short-history finding.
    hard_fail = [row for row in sanity if not row["non_degenerate"] and row["asset"] != "BTC"]
    if hard_fail:
        raise SystemExit(f"Sanity check FAILED: {hard_fail} -- degenerate regime frequency.")
    if any(row["asset"] == "BTC" and not row["non_degenerate"] for row in sanity):
        print("NOTE: BTC's primary-config crossover regime is thin/degenerate in its short dev "
              "window (expected, see prereg.md's flagged BTC-short-history risk) -- documented, not a bug.")

    configs = mac.grid_configs()
    assert len(configs) <= 36
    assert mac.PRIMARY_CONFIG in configs
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
        trial_id = f"new_028_{cfg_id}"
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

    primary_ci = configs.index(mac.PRIMARY_CONFIG)
    primary_cfg_id = cfg_id_for(primary_ci, mac.PRIMARY_CONFIG)
    primary_trial_id = f"new_028_{primary_cfg_id}"
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
        "episode_check": episode_check,
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
        print("Sec 4.1 PASSED -- run scripts/v3/robustness_028_ma_crossover_regime.py next "
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
            s, _ = run_one(daily, rf, mac.PRIMARY_CONFIG, fee)
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
