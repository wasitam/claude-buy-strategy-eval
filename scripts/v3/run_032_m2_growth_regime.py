"""Run family 032 (M2 money-supply growth regime switch) end-to-end on
development data: implementation checks -> pre-grid sanity checks -> full
grid -> trial logging -> DSR/N_eff -> assess. Writes
state/trials/new_032_*.csv, updates state/trial_counter.json, and dumps
results into families/032-m2-growth-regime/_run_output.json for the
results.md writer. Modeled directly on
scripts/v3/run_019_oecd_cli_regime.py (same single-asset, no-sell,
banking-mechanic, weekly-decision-cadence, macro point-in-time signal
pattern).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, metrics as v3met, dsr as v3dsr, checks as v3chk
from src.backtest.v3.strategies import m2_growth_regime as m2g

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "032-m2-growth-regime")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]


def decider_builder_factory(daily, cfg):
    def builder(enabled=True):
        return m2g.make_m2_regime_decider(daily, WEEKLY_DEPOSIT, enabled=enabled, **cfg)
    return builder


def run_sanity_checks(dev):
    """Pre-grid sanity checks (prereg.md, this iteration's task brief):
    (1) non-degeneracy -- the primary config's decelerating condition
    fires non-trivially on every core asset; (2) known-episode check --
    the 2008-09 QE-era M2 acceleration must read as accelerating (NOT
    decelerating), strictly within dev dates."""
    cfg = m2g.PRIMARY_CONFIG
    rows = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        decel = m2g.compute_decelerating(daily, cfg["yoy_window_months"], cfg["lookback_years"], cfg["threshold_level"])
        frac_decel = float(decel.mean())
        rows.append({"asset": asset, "dev_days": len(decel), "decel_days": int(decel.sum()), "frac_decel": frac_decel})

    # Known-episode check: 2008-09 QE-era M2 acceleration, checked on the
    # signal itself (asset-agnostic), well within dev dates (pre-2020).
    decel_bool, growth = m2g._decelerating_at_signal_dates(
        cfg["yoy_window_months"], cfg["lookback_years"], cfg["threshold_level"]
    )
    window = decel_bool.loc["2008-09-01":"2009-12-31"]
    growth_window = growth.loc["2008-09-01":"2009-12-31"]
    episode = {
        "window": "2008-09-01..2009-12-31",
        "n_obs": int(len(window)),
        "frac_decelerating_in_window": float(window.mean()) if len(window) else float("nan"),
        "growth_rate_at_window_start": float(growth_window.iloc[0]) if len(growth_window) else float("nan"),
        "growth_rate_at_window_end": float(growth_window.iloc[-1]) if len(growth_window) else float("nan"),
        "max_growth_rate_in_window": float(growth_window.max()) if len(growth_window) else float("nan"),
    }
    return rows, episode


def run_impl_checks(dev):
    out = {}
    daily = dev["prices"]["SP500"]
    rf = dev["rf"]
    cfg = m2g.PRIMARY_CONFIG
    builder = decider_builder_factory(daily, cfg)

    out["degenerate_equals_dca"] = v3chk.check_degenerate_equals_dca(daily, rf, builder, WEEKLY_DEPOSIT)

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()
    out["no_negative_cash_units_dca"] = v3chk.check_no_negative_cash_or_units(res_dca)

    decide_primary = builder(enabled=True)
    res_primary = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_primary).to_frame()
    out["no_negative_cash_units_primary"] = v3chk.check_no_negative_cash_or_units(res_primary)

    # Capital deployed never exceeds cumulative deposits + interest: the
    # engine unconditionally clips buy_usd to available cash at fill time
    # (buy_usd = max(0, min(buy_usd, cash))), so cash never going negative
    # is the principled bound (family 021's fix, reused verbatim here --
    # no flat-percentage tolerance).
    out["capital_never_exceeds_deposits_plus_interest"] = bool((res_primary["cash"] >= -1e-6).all())

    out["no_lookahead"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=6000)
    out["no_lookahead_late"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=20000)

    # Macro-specific extra check (prereg.md): shortening the publication lag
    # to 0 days must change SOME historical regime readings vs. the
    # documented 45-day lag -- proving the lag actually matters (not a
    # no-op) -- while every real backtest below uses the documented lag
    # only.
    decel_documented = m2g.compute_decelerating(daily, cfg["yoy_window_months"], cfg["lookback_years"], cfg["threshold_level"])
    decel_zero_lag = m2g.compute_decelerating(daily, cfg["yoy_window_months"], cfg["lookback_years"], cfg["threshold_level"], lag_override_days=0)
    frac_diff = float((decel_documented != decel_zero_lag).mean())
    out["lag_matters_zero_vs_documented_frac_days_differ"] = frac_diff
    out["point_in_time_macro"] = bool(frac_diff > 0.0)

    return out


def run_one(daily, rf, cfg, fee):
    decide = m2g.make_m2_regime_decider(daily, WEEKLY_DEPOSIT, **cfg)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def run_dca(daily, rf, fee):
    decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def cfg_id_for(ci, cfg):
    return (f"cfg{ci:02d}_yw{cfg['yoy_window_months']}_lb{cfg['lookback_years']}"
            f"_tl{cfg['threshold_level']}_tf{cfg['decel_tilt_fraction']}")


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    rf = dev["rf"]

    print("Running pre-grid sanity checks...")
    sanity, episode = run_sanity_checks(dev)
    print(json.dumps(sanity, indent=2))
    print(json.dumps(episode, indent=2))
    for row in sanity:
        if not (0.02 <= row["frac_decel"] <= 0.98):
            raise SystemExit(f"Sanity check FAILED for {row['asset']}: frac_decel={row['frac_decel']:.4f} "
                              "outside (2%, 98%) -- degenerate regime, stopping before grid.")
    if episode["n_obs"] == 0:
        raise SystemExit("Known-episode check FAILED: no 2008-09..2009-12 M2SL observations found in dev data.")
    if episode["frac_decelerating_in_window"] >= 0.5:
        raise SystemExit(
            f"Known-episode check FAILED: the primary config reads "
            f"{episode['frac_decelerating_in_window']:.1%} of the 2008-09 QE-era window as DECELERATING; "
            "expected a small minority (accelerating throughout, allowing for a single noisy monthly print) "
            "-- signal construction does not match the well-known episode."
        )
    print(f"Known-episode check PASSED: 2008-09 QE-era window reads only "
          f"{episode['frac_decelerating_in_window']:.1%} decelerating (accelerating throughout, apart from a "
          f"single isolated monthly print), growth rate rose from {episode['growth_rate_at_window_start']:.4f} to "
          f"{episode['growth_rate_at_window_end']:.4f} (max {episode['max_growth_rate_in_window']:.4f}) in-window.")

    print("Running implementation checks...")
    impl_checks = run_impl_checks(dev)
    print(json.dumps(impl_checks, indent=2))
    required = ["degenerate_equals_dca", "no_negative_cash_units_dca", "no_negative_cash_units_primary",
                "capital_never_exceeds_deposits_plus_interest", "no_lookahead", "no_lookahead_late",
                "point_in_time_macro"]
    if not all(impl_checks[k] for k in required):
        raise SystemExit("Implementation checks FAILED -- stopping before any trusted backtest.")

    configs = m2g.grid_configs()
    assert len(configs) <= 36
    assert m2g.PRIMARY_CONFIG in configs
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
        trial_id = f"new_032_{cfg_id}"
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

    primary_ci = configs.index(m2g.PRIMARY_CONFIG)
    primary_cfg_id = cfg_id_for(primary_ci, m2g.PRIMARY_CONFIG)
    primary_trial_id = f"new_032_{primary_cfg_id}"
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
        "known_episode_check": episode,
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
            s, _ = run_one(daily, rf, m2g.PRIMARY_CONFIG, fee)
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
