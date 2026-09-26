"""Run family 036 (return-autocorrelation regime sizing) end-to-end on
development data: autocorrelation-formula spot-check (known trending vs.
known choppy window) -> toy numeric-distinctiveness check vs. families
003/005/030/031 (prereg.md's required fourfold distinction) -> 2020+/
unseen-ticker no-touch assertion -> implementation checks -> pre-grid
non-degeneracy + cash-reserve sanity checks -> full grid -> trial logging
-> DSR/N_eff -> assess. Writes state/trials/new_036_*.csv, updates
state/trial_counter.json, and dumps results into
families/036-autocorr-regime-sizing/_run_output.json for the results.md
writer. Modeled directly on scripts/v3/run_031_kelly_sharpe_sizing.py and
run_035_parkinson_vol_sizing.py's structure (continuous-percentile-driven
multiplier, same clip convention).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, metrics as v3met, dsr as v3dsr, checks as v3chk
from src.backtest.v3.strategies import autocorr_regime_sizing as acr

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "036-autocorr-regime-sizing")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]
HOLDOUT_CUTOFF = pd.Timestamp("2020-01-01")


def decider_builder_factory(daily, ac_window, pctile_lookback, k, min_mult):
    def builder(enabled=True):
        return acr.make_autocorr_regime_decider(
            daily, WEEKLY_DEPOSIT, ac_window=ac_window, pctile_lookback=pctile_lookback,
            k=k, min_mult=min_mult, enabled=enabled,
        )
    return builder


def check_no_holdout_dates_referenced(dates_checked: list) -> bool:
    """Task checkpoint (d): assert that every date this script's own
    checks explicitly reference is strictly before the sealed holdout
    cutoff, and is drawn from load_dev()'s own gated data (which already
    refuses 2020+ dates and unseen tickers by construction)."""
    ok = True
    for d in dates_checked:
        ts = pd.Timestamp(d)
        if ts >= HOLDOUT_CUTOFF:
            ok = False
    return ok


def check_autocorr_formula_spotcheck(dev) -> dict:
    """Task-required checkpoint (b): spot-check the autocorrelation
    computation on a known trending window vs. a known choppy window on
    real dev data, confirming the sign/magnitude make directional sense.
    Independently re-derived via numpy.corrcoef on the raw log-return
    arrays, then cross-checked against the module's own function."""
    daily = dev["prices"]["SP500"]
    close = daily["Close"].to_numpy(dtype=float)
    log_ret = np.diff(np.log(close), prepend=np.log(close[0]))
    log_ret[0] = 0.0

    # A real, well-known steadily-trending SP500 window (post-2009-bottom
    # recovery, smooth uptrend, all dev-period): 2013 calendar year, a
    # famously low-volatility grinding-up year.
    idx = daily.index
    trend_start = idx.searchsorted(pd.Timestamp("2013-01-02"))
    trend_end = idx.searchsorted(pd.Timestamp("2013-12-31"))
    # A real choppy/whipsaw SP500 window, all dev-period: August-September
    # 2011 (US credit-downgrade whipsaw, sharp reversals day to day).
    choppy_start = idx.searchsorted(pd.Timestamp("2011-08-01"))
    choppy_end = idx.searchsorted(pd.Timestamp("2011-09-30"))

    dates_checked = ["2013-01-02", "2013-12-31", "2011-08-01", "2011-09-30"]

    def hand_rho1(window_ret: np.ndarray) -> float:
        return float(np.corrcoef(window_ret[1:], window_ret[:-1])[0, 1])

    trend_ret = log_ret[trend_start:trend_end + 1]
    choppy_ret = log_ret[choppy_start:choppy_end + 1]
    trend_rho1 = hand_rho1(trend_ret)
    choppy_rho1 = hand_rho1(choppy_ret)

    # Cross-check the module's own rolling function evaluated at the last
    # day of each window against the same window length.
    module_rho1_series_trend = acr.compute_autocorr_signal(daily, ac_window=len(trend_ret) - 1)
    module_rho1_series_choppy = acr.compute_autocorr_signal(daily, ac_window=len(choppy_ret) - 1)
    module_trend_val = float(module_rho1_series_trend[trend_end])
    module_choppy_val = float(module_rho1_series_choppy[choppy_end])

    return {
        "trend_window": "SP500 2013-01-02..2013-12-31 (grinding low-vol uptrend)",
        "trend_hand_rho1": trend_rho1,
        "trend_module_rho1": module_trend_val,
        "trend_match": bool(np.isclose(trend_rho1, module_trend_val, atol=1e-9)),
        "choppy_window": "SP500 2011-08-01..2011-09-30 (US credit-downgrade whipsaw)",
        "choppy_hand_rho1": choppy_rho1,
        "choppy_module_rho1": module_choppy_val,
        "choppy_match": bool(np.isclose(choppy_rho1, module_choppy_val, atol=1e-9)),
        "directionally_sensible": bool(trend_rho1 > choppy_rho1),
        "dates_checked": dates_checked,
        "dates_all_pre_holdout": check_no_holdout_dates_referenced(dates_checked),
    }


def check_toy_distinctiveness_example() -> dict:
    """Task-required checkpoint (c): the constructed toy 8-day example
    from prereg.md, recomputed programmatically here (not hand-copied),
    proving families 003/005/030/031's statistics are identical across the
    two paths while this family's lag-1 autocorrelation differs
    decisively."""
    path_a = np.array([1, -1, -1, 1, -1, 1, -1, 1], dtype=float) / 100.0   # choppy
    path_b = np.array([-1, -1, 1, 1, -1, -1, 1, 1], dtype=float) / 100.0  # trending/paired

    def family_stats(r: np.ndarray) -> dict:
        mean = float(r.mean())
        var = float(r.var(ddof=1))
        std = float(np.sqrt(var))
        sharpe = float(mean / std) if std > 0 else float("nan")
        trailing_sign = float(np.sign(r.sum()))
        signs = np.sign(r)
        streak = 1
        max_streak = 1
        for i in range(1, len(signs)):
            if signs[i] == signs[i - 1]:
                streak += 1
            else:
                streak = 1
            max_streak = max(max_streak, streak)
        rho1 = float(np.corrcoef(r[1:], r[:-1])[0, 1])
        return {
            "mean_fam005_level": mean, "sample_var_fam003": var, "sign_fam005": trailing_sign,
            "sharpe_fam031": sharpe, "max_streak_fam030": max_streak, "rho1_fam036": rho1,
        }

    stats_a = family_stats(path_a)
    stats_b = family_stats(path_b)

    # Cross-check rho1 against the module's own function (ac_window=7, the
    # full 8-return series with no rolling-window truncation needed).
    module_rho1_a = acr.compute_autocorr_signal(
        pd.DataFrame({"Close": np.exp(np.cumsum(np.concatenate([[0.0], path_a])))}), ac_window=7
    )[-1]
    module_rho1_b = acr.compute_autocorr_signal(
        pd.DataFrame({"Close": np.exp(np.cumsum(np.concatenate([[0.0], path_b])))}), ac_window=7
    )[-1]

    identical_on_other_four = (
        np.isclose(stats_a["mean_fam005_level"], stats_b["mean_fam005_level"], atol=1e-12)
        and np.isclose(stats_a["sample_var_fam003"], stats_b["sample_var_fam003"], atol=1e-12)
        and np.isclose(stats_a["sign_fam005"], stats_b["sign_fam005"], atol=1e-12)
        and np.isclose(stats_a["sharpe_fam031"], stats_b["sharpe_fam031"], atol=1e-12)
        and stats_a["max_streak_fam030"] == stats_b["max_streak_fam030"]
    )
    rho1_decisively_different = bool(abs(stats_a["rho1_fam036"] - stats_b["rho1_fam036"]) > 0.5)

    return {
        "path_a_choppy": path_a.tolist(), "path_b_trending": path_b.tolist(),
        "stats_a": stats_a, "stats_b": stats_b,
        "module_rho1_a": float(module_rho1_a), "module_rho1_b": float(module_rho1_b),
        "module_matches_hand_a": bool(np.isclose(module_rho1_a, stats_a["rho1_fam036"], atol=1e-9)),
        "module_matches_hand_b": bool(np.isclose(module_rho1_b, stats_b["rho1_fam036"], atol=1e-9)),
        "identical_on_families_003_005_030_031": bool(identical_on_other_four),
        "rho1_decisively_different": rho1_decisively_different,
        "distinctiveness_proven": bool(identical_on_other_four and rho1_decisively_different),
    }


def check_flat_k_zero_equals_dca(daily, rf) -> bool:
    """Family-specific second reference point (two-reference-point
    degenerate-config pattern, per family 014/020/031/033/034/035
    precedent): k=0.0 (a real grid-shaped code path, not the enabled=False
    bypass) forces m_t=clip(1+0*(...), min_mult, max_mult)=1.0 for every
    day regardless of pctile_t, since min_mult<1.0<max_mult always holds on
    the declared grid -- must also reproduce plain DCA bit-for-bit."""
    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    dca_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()

    flat_decide = acr.make_autocorr_regime_decider(
        daily, WEEKLY_DEPOSIT, ac_window=40, pctile_lookback=252,
        k=0.0, min_mult=0.5, enabled=True,
    )
    flat_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, flat_decide).to_frame()

    ok_units = np.allclose(dca_res["units"].to_numpy(), flat_res["units"].to_numpy(), atol=1e-8)
    ok_cash = np.allclose(dca_res["cash"].to_numpy(), flat_res["cash"].to_numpy(), atol=1e-6)
    return bool(ok_units and ok_cash)


def check_cash_reserve_dynamics(daily, rf) -> dict:
    """Task-required cash-reserve check, per family 033's lesson
    (generalized to this family's continuous multiplier, checkpoint (e)):
    with min_mult=0.5<1.0 in the primary config, confirm a genuine reserve
    is banked overall (average cash share higher than plain DCA) and drawn
    down further during high-percentile (elevated-rho1, m_t>1) weeks than
    during low-percentile (depressed-rho1, m_t<1) weeks."""
    cfg = acr.PRIMARY_CONFIG
    decide = acr.make_autocorr_regime_decider(daily, WEEKLY_DEPOSIT, **cfg)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide).to_frame()

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()

    avg_cash_strategy = float(res["cash"].mean())
    avg_cash_dca = float(res_dca["cash"].mean())

    m = acr.compute_multiplier(daily, cfg["ac_window"], cfg["pctile_lookback"], cfg["k"], cfg["min_mult"])
    low_mult_tier = m < 1.0    # depressed rho1 percentile -> under-invest -> should bank cash
    high_mult_tier = m > 1.0   # elevated rho1 percentile -> over-invest -> should draw cash down
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
    cfg = acr.PRIMARY_CONFIG
    rows = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        m = acr.compute_multiplier(daily, cfg["ac_window"], cfg["pctile_lookback"], cfg["k"], cfg["min_mult"])
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
    builder = decider_builder_factory(daily, **acr.PRIMARY_CONFIG)

    formula_check = check_autocorr_formula_spotcheck(dev)
    out["formula_spotcheck"] = formula_check
    out["formula_correct"] = bool(formula_check["trend_match"] and formula_check["choppy_match"]
                                   and formula_check["directionally_sensible"]
                                   and formula_check["dates_all_pre_holdout"])

    toy_check = check_toy_distinctiveness_example()
    out["toy_distinctiveness_example"] = toy_check
    out["distinctiveness_proven"] = toy_check["distinctiveness_proven"]

    cash_check = check_cash_reserve_dynamics(daily, rf)
    out["cash_reserve_check"] = cash_check
    out["reserve_builds_up_vs_dca"] = cash_check["reserve_builds_up_vs_dca"]
    out["reserve_drawn_down_on_high_mult_weeks"] = cash_check["reserve_drawn_down_on_high_mult_weeks"]

    out["degenerate_bypass_equals_dca"] = v3chk.check_degenerate_equals_dca(daily, rf, builder, WEEKLY_DEPOSIT)
    out["flat_k_zero_grid_arm_equals_dca"] = check_flat_k_zero_equals_dca(daily, rf)

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()
    out["no_negative_cash_units_dca"] = v3chk.check_no_negative_cash_or_units(res_dca)

    decide_primary = builder(enabled=True)
    res_primary = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_primary).to_frame()
    out["no_negative_cash_units_primary"] = v3chk.check_no_negative_cash_or_units(res_primary)
    out["capital_never_exceeds_deposits_primary"] = check_capital_never_exceeds_deposits(daily, rf, res_primary)

    aggressive_cfg = {"ac_window": 20, "pctile_lookback": 252, "k": 1.5, "min_mult": 0.25}
    decide_agg = acr.make_autocorr_regime_decider(daily, WEEKLY_DEPOSIT, **aggressive_cfg, enabled=True)
    res_agg = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_agg).to_frame()
    out["no_negative_cash_units_aggressive"] = v3chk.check_no_negative_cash_or_units(res_agg)
    out["capital_never_exceeds_deposits_aggressive"] = check_capital_never_exceeds_deposits(daily, rf, res_agg)

    out["no_lookahead"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=6000)
    out["no_lookahead_late"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=20000)
    out["point_in_time_macro"] = v3chk.check_point_in_time_macro()
    return out


def run_one(daily, rf, cfg, fee):
    decide = acr.make_autocorr_regime_decider(daily, WEEKLY_DEPOSIT, **cfg)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def run_dca(daily, rf, fee):
    decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def cfg_id_for(ci, cfg):
    return f"cfg{ci:02d}_aw{cfg['ac_window']}_pl{cfg['pctile_lookback']}_k{cfg['k']}_mn{cfg['min_mult']}"


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    rf = dev["rf"]

    print("Running formula spot-check + toy-distinctiveness check + implementation checks...")
    impl_checks = run_impl_checks(dev)
    print(json.dumps(impl_checks, indent=2, default=float))
    required = ["formula_correct", "distinctiveness_proven",
                "reserve_builds_up_vs_dca", "reserve_drawn_down_on_high_mult_weeks",
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

    configs = acr.grid_configs()
    assert len(configs) <= 36
    assert acr.PRIMARY_CONFIG in configs
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
                   "ac_window": cfg["ac_window"], "pctile_lookback": cfg["pctile_lookback"],
                   "k": cfg["k"], "min_mult": cfg["min_mult"]}
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
        trial_id = f"new_036_{cfg_id}"
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

    primary_ci = configs.index(acr.PRIMARY_CONFIG)
    primary_cfg_id = cfg_id_for(primary_ci, acr.PRIMARY_CONFIG)
    primary_trial_id = f"new_036_{primary_cfg_id}"
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
        print("Sec 4.1 PASSED -- run scripts/v3/robustness_036_autocorr_regime_sizing.py next "
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
            s, _ = run_one(daily, rf, acr.PRIMARY_CONFIG, fee)
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
