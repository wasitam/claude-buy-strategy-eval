"""Run family 051 (pre-FOMC announcement drift deposit timing) end-to-end
on development data: redundancy checks -> pre-grid sanity checks ->
implementation checks -> full grid -> trial logging -> DSR/N_eff -> assess.
Writes state/trials/new_051_*.csv, updates state/trial_counter.json, and
dumps results into families/051-pre-fomc-drift/_run_output.json for the
results.md writer. Modeled directly on scripts/v3/run_007_day_of_week.py
(same every-day-decision, banking + forced-deploy mechanic) and
scripts/v3/run_022_election_cycle.py (same cross-asset scoping precedent).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, metrics as v3met, dsr as v3dsr, checks as v3chk
from src.backtest.v3.strategies import pre_fomc_drift as pfd
from src.backtest.v3.strategies import turn_of_month as tom

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "051-pre-fomc-drift")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]


def decider_builder_factory(daily, cfg):
    def builder(enabled=True):
        return pfd.make_pre_fomc_decider(daily, WEEKLY_DEPOSIT, enabled=enabled, **cfg)
    return builder


def run_redundancy_checks():
    """Concrete redundancy check against families 006/007/018/022/024,
    computed directly on the hard-coded 208-date FOMC_DATES list (prereg.md
    'Required distinction' section). Returns a dict of the exact numbers
    reported in prereg.md/results.md."""
    dates = pfd.FOMC_DATES_TS
    n = len(dates)
    weekday_counts = pd.Series(dates.dayofweek).value_counts().sort_index().to_dict()
    dom = pd.Series(dates.day)
    month_counts = pd.Series(dates.month).value_counts().sort_index().to_dict()
    ymod4 = pd.Series(dates.year % 4).value_counts().sort_index().to_dict()
    gaps = pd.Series(dates).diff().dropna().dt.days
    per_year = pd.Series(dates.year).value_counts()

    # Overlap with family 006's own primary turn-of-month window (last 1
    # trading day of month, first 3 trading days of following month), using
    # a plain NYSE-ish calendar-day approximation to month-end/start
    # (business days) since this check only needs the DECISION dates
    # themselves, not a full trading-day index.
    bdays = pd.bdate_range(dates.min() - pd.Timedelta(days=10), dates.max() + pd.Timedelta(days=10))
    is_tom_bday = np.zeros(len(bdays), dtype=bool)
    period = bdays.to_period("M")
    dfb = pd.DataFrame({"pos": np.arange(len(bdays))}, index=bdays)
    for _, grp in dfb.groupby(period):
        positions = grp["pos"].to_numpy()
        if len(positions) >= 1:
            is_tom_bday[positions[-1:]] = True
        if len(positions) >= 3:
            is_tom_bday[positions[:3]] = True
        else:
            is_tom_bday[positions[:len(positions)]] = True
    tom_bdays = set(bdays[is_tom_bday])
    overlap = sum(1 for d in dates if d in tom_bdays)

    return {
        "n_meetings": int(n),
        "meetings_per_year_min_max": [int(per_year.min()), int(per_year.max())],
        "weekday_counts_mon0_sun6": {int(k): int(v) for k, v in weekday_counts.items()},
        "day_of_month_min_max_mean_std": [int(dom.min()), int(dom.max()), float(dom.mean()), float(dom.std())],
        "month_counts": {int(k): int(v) for k, v in month_counts.items()},
        "year_mod_4_counts": {int(k): int(v) for k, v in ymod4.items()},
        "inter_meeting_gap_days_min_max_mean_std": [
            int(gaps.min()), int(gaps.max()), float(gaps.mean()), float(gaps.std()),
        ],
        "overlap_with_family006_primary_tom_window": int(overlap),
    }


def run_sanity_checks(dev):
    """Pre-grid non-degeneracy check (prereg.md): the primary config's
    pre-FOMC window flag fires on a small but non-trivial fraction (0.5%-
    15%) of trading days on every core asset."""
    cfg = pfd.PRIMARY_CONFIG
    rows = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        is_pre = pfd.compute_is_pre_fomc(daily, cfg["window_days"])
        frac = float(is_pre.mean())
        rows.append({
            "asset": asset, "dev_days": len(is_pre), "window_days_count": int(is_pre.sum()),
            "frac_pre_fomc": frac, "first_date": str(daily.index.min().date()),
            "last_date": str(daily.index.max().date()),
        })
    return rows


def run_impl_checks(dev):
    out = {}
    daily = dev["prices"]["SP500"]
    rf = dev["rf"]
    cfg = pfd.PRIMARY_CONFIG
    builder = decider_builder_factory(daily, cfg)

    out["degenerate_equals_dca"] = v3chk.check_degenerate_equals_dca(daily, rf, builder, WEEKLY_DEPOSIT)

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()
    out["no_negative_cash_units_dca"] = v3chk.check_no_negative_cash_or_units(res_dca)

    decide_primary = builder(enabled=True)
    res_primary = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_primary).to_frame()
    out["no_negative_cash_units_primary"] = v3chk.check_no_negative_cash_or_units(res_primary)

    out["no_lookahead"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=6000)
    out["no_lookahead_late"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=20000)
    out["point_in_time_macro"] = True  # price/calendar-only signal, no macro data feed -- vacuously satisfied

    # BTC-specific extra check: BTC's development history (2014-09..2019-12)
    # is entirely inside the FOMC-calendar-covered era, unlike SP500's -- a
    # useful contrast worth checking explicitly (prereg.md's cross-asset
    # dilution discussion).
    btc_daily = dev["prices"]["BTC"]
    btc_builder = decider_builder_factory(btc_daily, cfg)
    decide_btc = btc_builder(enabled=True)
    res_btc = v3eng.run_single_asset(btc_daily, WEEKLY_DEPOSIT, rf, decide_btc).to_frame()
    out["no_negative_cash_units_primary_btc"] = v3chk.check_no_negative_cash_or_units(res_btc)
    out["no_lookahead_btc"] = v3chk.check_no_lookahead(btc_daily, rf, btc_builder, t_check=1000)

    # Extra check (prereg.md): total capital deployed never exceeds
    # cumulative deposits + interest. This family never sells, so net
    # deployed == gross bought; the engine unconditionally clips buy_usd to
    # available cash at fill time, so cash never going negative is the
    # principled ceiling bound (family 021's fix).
    out["capital_never_exceeds_deposits_plus_interest"] = bool((res_primary["cash"] >= -1e-6).all())

    return out


def run_one(daily, rf, cfg, fee):
    decide = pfd.make_pre_fomc_decider(daily, WEEKLY_DEPOSIT, **cfg)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def run_dca(daily, rf, fee):
    decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def cfg_id_for(ci, cfg):
    return (f"cfg{ci:02d}_wd{cfg['window_days']}_mt{cfg['mild_tilt_fraction']}"
            f"_ml{cfg['max_lump_multiple']}_bw{cfg['banking_window_weeks']}")


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    rf = dev["rf"]

    print("Running redundancy checks against families 006/007/018/022/024...")
    redundancy = run_redundancy_checks()
    print(json.dumps(redundancy, indent=2))
    if not (redundancy["meetings_per_year_min_max"][0] == 8 and redundancy["meetings_per_year_min_max"][1] == 8):
        raise SystemExit("Redundancy check FAILED: FOMC_DATES does not have exactly 8 meetings/year every year.")
    # The redundancy claim is NOT "zero overlap with family 006's TOM
    # window" -- family 006's window is ~4 of ~21 business days/month
    # (~19%), so pure chance alone predicts ~0.19*208=~40 overlaps even
    # with a perfectly uniform, non-clustered FOMC calendar. The actual
    # test is whether the FOMC calendar is DISPROPORTIONATELY concentrated
    # in that window (which would indicate a hidden TOM relabeling) vs.
    # roughly consistent with chance (confirming no such clustering).
    expected_chance_overlap = redundancy["n_meetings"] * (4.0 / 21.0)
    redundancy["expected_chance_overlap_with_tom_window"] = expected_chance_overlap
    ratio = redundancy["overlap_with_family006_primary_tom_window"] / expected_chance_overlap
    redundancy["overlap_vs_chance_ratio"] = ratio
    if not (0.5 <= ratio <= 1.5):
        raise SystemExit(f"Redundancy check FAILED: FOMC-date overlap with family 006's TOM window is "
                          f"{ratio:.2f}x the chance-expected rate -- this would indicate a hidden relabeling of "
                          "006 (if >1.5x) or an implausible anti-correlation (if <0.5x), stopping before any "
                          "backtest.")

    print("Running pre-grid non-degeneracy check...")
    sanity = run_sanity_checks(dev)
    print(json.dumps(sanity, indent=2))
    for row in sanity:
        if not (0.005 <= row["frac_pre_fomc"] <= 0.15):
            raise SystemExit(f"Sanity check FAILED for {row['asset']}: frac_pre_fomc={row['frac_pre_fomc']:.4f} "
                              "outside (0.5%, 15%) -- degenerate window, stopping before grid.")
    print("Pre-grid sanity check PASSED on all 5 assets.")

    print("Running implementation checks...")
    impl_checks = run_impl_checks(dev)
    print(json.dumps(impl_checks, indent=2))
    if not all(impl_checks.values()):
        raise SystemExit("Implementation checks FAILED -- stopping before any trusted backtest.")

    configs = pfd.grid_configs()
    assert len(configs) <= 36
    assert pfd.PRIMARY_CONFIG in configs
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
        trial_id = f"new_051_{cfg_id}"
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

    primary_ci = configs.index(pfd.PRIMARY_CONFIG)
    primary_cfg_id = cfg_id_for(primary_ci, pfd.PRIMARY_CONFIG)
    primary_trial_id = f"new_051_{primary_cfg_id}"
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

    # CSCV PBO diagnostic, pooled SP500 weekly strategy returns across the
    # grid (SP500 is this family's literature-anchor asset).
    cscv_sp500 = v3dsr.cscv_pbo({cfg_id: per_config_asset_weekly[(cfg_id, "SP500", 0.001)] for cfg_id in grid_df["config_id"].unique()}, n_splits=8)
    print("CSCV PBO (SP500 grid):", cscv_sp500)

    out = {
        "redundancy_checks": redundancy,
        "sanity_check": sanity,
        "impl_checks": impl_checks,
        "n_seed": counter["seed"], "n_new": new_trial_count, "n_total_raw": len(all_series),
        "n_eff": n_eff,
        "dsr_neff": dsr_neff, "dsr_rawn": dsr_rawn,
        "check_4_1": check_4_1,
        "check_4_4_grid": check_4_4_grid,
        "cscv_pbo_sp500": cscv_sp500,
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
            s, _ = run_one(daily, rf, pfd.PRIMARY_CONFIG, fee)
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
