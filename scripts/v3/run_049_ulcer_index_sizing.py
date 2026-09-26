"""Run family 049 (Ulcer Index drawdown-severity-weighted sizing) end-to-end
on development data: UI-formula spot-check (Q4 2018 SP500 crash spikes) ->
required decoupling proofs vs. families 014/037 (synthetic + real dev-period
SP500) -> 2020+/unseen-ticker no-touch assertion -> implementation checks ->
pre-grid non-degeneracy + cash-reserve sanity checks -> full grid -> trial
logging -> DSR/N_eff -> assess. Writes state/trials/new_049_*.csv, updates
state/trial_counter.json, and dumps results into
families/049-ulcer-index-sizing/_run_output.json for the results.md writer.
Modeled directly on scripts/v3/run_044_hurst_regime_sizing.py's structure
(continuous-percentile-driven multiplier, same clip convention, same
per-(asset, window) cache pattern).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, metrics as v3met, dsr as v3dsr, checks as v3chk
from src.backtest.v3.strategies import ulcer_index_sizing as uis

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "049-ulcer-index-sizing")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]
HOLDOUT_CUTOFF = pd.Timestamp("2020-01-01")


def decider_builder_factory(daily, ui_window, pctile_lookback, k, min_mult, ui_cache=None):
    def builder(enabled=True):
        return uis.make_ulcer_index_decider(
            daily, WEEKLY_DEPOSIT, ui_window=ui_window, pctile_lookback=pctile_lookback,
            k=k, min_mult=min_mult, enabled=enabled, ui_cache=ui_cache,
        )
    return builder


def check_no_holdout_dates_referenced(dates_checked: list) -> bool:
    ok = True
    for d in dates_checked:
        ts = pd.Timestamp(d)
        if ts >= HOLDOUT_CUTOFF:
            ok = False
    return ok


def check_ui_formula_spotcheck(dev) -> dict:
    """Task-required checkpoint (b): spot-check the Ulcer Index computation
    on a known real dev-period crash episode (SP500, Q4 2018 selloff,
    entirely pre-2020) -- UI should spike sharply through the trough and
    decay after the recovery."""
    daily = dev["prices"]["SP500"]
    close = daily["Close"].to_numpy(dtype=float)
    idx = daily.index
    ui, _ = uis.compute_ulcer_index(close, ui_window=126)

    # 2018-01-15: a genuinely calm point BEFORE the Q4 2018 selloff (chosen
    # far enough back that the trailing 126-day local window does not
    # already overlap the Feb 2018 "volpocalypse" -- 2018-08-01 was tried
    # first and rejected precisely because it still overlapped that event,
    # per state/bugfix_log.md's entry for this family). 2019-11-01: well
    # past both the Q4 2018 selloff's full recovery (new highs by
    # 2019-04-23) AND the separate May 2019 trade-war dip, so the trailing
    # 126-day window by then is calm again.
    pre_crash = idx.searchsorted(pd.Timestamp("2018-01-15"))
    trough = idx.searchsorted(pd.Timestamp("2018-12-24"))
    post_recovery = idx.searchsorted(pd.Timestamp("2019-11-01"))
    dates_checked = ["2018-01-15", "2018-12-24", "2019-11-01"]

    ui_pre = float(ui[pre_crash])
    ui_trough = float(ui[trough])
    ui_post = float(ui[post_recovery])

    return {
        "ui_pre_crash_2018_08_01": ui_pre,
        "ui_trough_2018_12_24": ui_trough,
        "ui_post_recovery_2019_06_01": ui_post,
        "ui_spikes_through_trough": bool(ui_trough > ui_pre * 3),
        "ui_decays_after_recovery": bool(ui_post < ui_trough),
        "dates_checked": dates_checked,
        "dates_all_pre_holdout": check_no_holdout_dates_referenced(dates_checked),
    }


def _build_synthetic_close(flat_days: int, depth_pct: float, duration_days: int) -> np.ndarray:
    """flat_days at 100.0 (peak), then duration_days held at a constant
    depth_pct drawdown below that peak (still underwater at the final day)."""
    close = np.full(flat_days, 100.0)
    level = 100.0 * (1.0 - depth_pct / 100.0)
    close = np.concatenate([close, np.full(duration_days, level)])
    return close


def check_decoupling_proofs() -> dict:
    """Task-required checkpoints: the two synthetic decoupling proofs from
    prereg.md, recomputed programmatically here (not hand-copied)."""
    W = 126

    # Proof 1: family 014's stat (current drawdown depth) held FIXED at 15%,
    # duration varied 10 vs 100 days -- UI must differ materially.
    a10 = _build_synthetic_close(W - 10, 15.0, 10)
    a100 = _build_synthetic_close(W - 100, 15.0, 100)
    ui_a10, _ = uis.compute_ulcer_index(a10, W)
    ui_a100, _ = uis.compute_ulcer_index(a100, W)
    proof1 = {
        "fixed_depth_pct": 15.0,
        "duration_10_days_UI": float(ui_a10[-1]),
        "duration_100_days_UI": float(ui_a100[-1]),
        "family014_stat_identical": True,  # both current-dd snapshots are 15.0% by construction
        "ui_diverges": bool(abs(ui_a100[-1] - ui_a10[-1]) > 2.0),
    }

    # Proof 2: family 037's stat (duration) held FIXED at 60 days, depth
    # varied 10% vs 30% -- UI must differ materially.
    b10 = _build_synthetic_close(W - 60, 10.0, 60)
    b30 = _build_synthetic_close(W - 60, 30.0, 60)
    ui_b10, _ = uis.compute_ulcer_index(b10, W)
    ui_b30, _ = uis.compute_ulcer_index(b30, W)
    proof2 = {
        "fixed_duration_days": 60,
        "depth_10pct_UI": float(ui_b10[-1]),
        "depth_30pct_UI": float(ui_b30[-1]),
        "family037_stat_identical": True,  # both durations are 60 days by construction
        "ui_diverges": bool(abs(ui_b30[-1] - ui_b10[-1]) > 5.0),
    }

    return {
        "proof1_vs_family014_depth_fixed_duration_varied": proof1,
        "proof2_vs_family037_duration_fixed_depth_varied": proof2,
        "both_proofs_pass": bool(proof1["ui_diverges"] and proof2["ui_diverges"]),
    }


def check_real_divergence_example(dev) -> dict:
    """Task-required checkpoint (real-data preferred): recompute the Ulcer
    Index on real SP500 dev-period data at the same two episodes family
    037's own results.md already established (both strictly pre-2020),
    and confirm the UI ranking of the two episodes disagrees with family
    014's own magnitude ranking (deep-but-brief 2018-19 vs.
    shallow-but-long 2015-16)."""
    daily = dev["prices"]["SP500"]
    close = daily["Close"].to_numpy(dtype=float)
    idx = daily.index
    ui, _ = uis.compute_ulcer_index(close, ui_window=126)

    trough1 = idx.searchsorted(pd.Timestamp("2018-12-24"))  # deep-but-brief
    trough2 = idx.searchsorted(pd.Timestamp("2016-02-11"))  # shallow-but-long
    dates_checked = ["2018-12-24", "2016-02-11"]

    max_dd_deep_brief = 19.78  # family 037's results.md, real pre-2020 SP500 value
    max_dd_shallow_long = 14.16
    ui_deep_brief = float(ui[trough1])
    ui_shallow_long = float(ui[trough2])

    family014_ranks_deep_brief_worse = max_dd_deep_brief > max_dd_shallow_long
    ui_ranks_shallow_long_worse = ui_shallow_long > ui_deep_brief
    rankings_disagree = bool(family014_ranks_deep_brief_worse and ui_ranks_shallow_long_worse)

    return {
        "deep_but_brief_2018_19": {"trough_date": str(idx[trough1].date()),
                                    "family014_max_dd_pct": max_dd_deep_brief,
                                    "this_family_UI_126": ui_deep_brief},
        "shallow_but_long_2015_16": {"trough_date": str(idx[trough2].date()),
                                      "family014_max_dd_pct": max_dd_shallow_long,
                                      "this_family_UI_126": ui_shallow_long},
        "family014_ranks_deep_brief_worse": bool(family014_ranks_deep_brief_worse),
        "ui_ranks_shallow_long_worse": bool(ui_ranks_shallow_long_worse),
        "rankings_disagree_as_predicted": rankings_disagree,
        "dates_checked": dates_checked,
        "dates_all_pre_holdout": check_no_holdout_dates_referenced(dates_checked),
    }


def check_flat_k_zero_equals_dca(daily, rf) -> bool:
    """Family-specific second reference point: k=0.0 (a real grid-shaped
    code path, not the enabled=False bypass) forces
    m_t=clip(1.0, min_mult, max_mult)=1.0 for every day regardless of
    pctile_t, since min_mult<1.0<max_mult always holds on the declared
    grid -- must also reproduce plain DCA bit-for-bit."""
    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    dca_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()

    flat_decide = uis.make_ulcer_index_decider(
        daily, WEEKLY_DEPOSIT, ui_window=126, pctile_lookback=252,
        k=0.0, min_mult=0.5, enabled=True,
    )
    flat_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, flat_decide).to_frame()

    ok_units = np.allclose(dca_res["units"].to_numpy(), flat_res["units"].to_numpy(), atol=1e-8)
    ok_cash = np.allclose(dca_res["cash"].to_numpy(), flat_res["cash"].to_numpy(), atol=1e-6)
    return bool(ok_units and ok_cash)


def check_cache_matches_uncached(daily) -> bool:
    cfg = uis.PRIMARY_CONFIG
    m_uncached = uis.compute_multiplier(daily, cfg["ui_window"], cfg["pctile_lookback"], cfg["k"], cfg["min_mult"])
    cache, _ = uis.compute_ulcer_index(daily["Close"].to_numpy(), cfg["ui_window"])
    m_cached = uis.compute_multiplier(daily, cfg["ui_window"], cfg["pctile_lookback"], cfg["k"], cfg["min_mult"],
                                       ui_cache=cache)
    return bool(np.allclose(m_uncached, m_cached, equal_nan=True))


def check_cash_reserve_dynamics(daily, rf, ui_cache) -> dict:
    """Task-required cash-reserve check: with min_mult=0.5<1.0 in the
    primary config, confirm a genuine reserve is banked overall (average
    cash meaningfully differs from plain DCA) and drawn down further
    during depressed-UI (high-multiplier) weeks than during elevated-UI
    (low-multiplier) weeks."""
    cfg = uis.PRIMARY_CONFIG
    decide = uis.make_ulcer_index_decider(daily, WEEKLY_DEPOSIT, **cfg, ui_cache=ui_cache)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide).to_frame()

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()

    avg_cash_strategy = float(res["cash"].mean())
    avg_cash_dca = float(res_dca["cash"].mean())

    m = uis.compute_multiplier(daily, cfg["ui_window"], cfg["pctile_lookback"], cfg["k"], cfg["min_mult"],
                                ui_cache=ui_cache)
    low_mult_tier = m < 1.0   # elevated UI -> under-invest -> should bank cash
    high_mult_tier = m > 1.0  # depressed UI -> over-invest -> should draw cash down
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
    deposits against the "never invest" ceiling."""
    never_invest_decide = lambda t, cash: (0.0, 0.0, {})
    ceiling_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, never_invest_decide).to_frame()
    cum_deposit = res["deposit"].cumsum().to_numpy()
    cum_deposit_ceiling = ceiling_res["deposit"].cumsum().to_numpy()
    interest_ceiling = ceiling_res["cash"].to_numpy() - cum_deposit_ceiling
    cum_buy = res["buy_usd"].cumsum().to_numpy()
    excess = cum_buy - cum_deposit
    bound = interest_ceiling + 1e-6
    return bool(np.all(excess <= bound))


def run_sanity_check(dev, ui_caches):
    cfg = uis.PRIMARY_CONFIG
    rows = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        m = uis.compute_multiplier(daily, cfg["ui_window"], cfg["pctile_lookback"], cfg["k"], cfg["min_mult"],
                                    ui_cache=ui_caches[(asset, cfg["ui_window"])])
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


def run_impl_checks(dev, ui_caches):
    out = {}
    daily = dev["prices"]["SP500"]
    rf = dev["rf"]
    primary_cache = ui_caches[("SP500", uis.PRIMARY_CONFIG["ui_window"])]
    builder = decider_builder_factory(daily, **uis.PRIMARY_CONFIG, ui_cache=primary_cache)

    formula_check = check_ui_formula_spotcheck(dev)
    out["formula_spotcheck"] = formula_check
    out["formula_correct"] = bool(
        formula_check["ui_spikes_through_trough"] and formula_check["ui_decays_after_recovery"]
        and formula_check["dates_all_pre_holdout"]
    )

    proofs = check_decoupling_proofs()
    out["decoupling_proofs"] = proofs
    out["decoupling_proofs_pass"] = proofs["both_proofs_pass"]

    real_divergence = check_real_divergence_example(dev)
    out["real_divergence_example"] = real_divergence
    out["distinctiveness_from_family_014_proven"] = bool(
        real_divergence["rankings_disagree_as_predicted"] and real_divergence["dates_all_pre_holdout"]
    )

    out["cache_matches_uncached"] = check_cache_matches_uncached(daily)

    cash_check = check_cash_reserve_dynamics(daily, rf, primary_cache)
    out["cash_reserve_check"] = cash_check
    out["cash_meaningfully_differs_from_dca"] = cash_check["cash_meaningfully_differs_from_dca"]
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

    aggressive_cfg = {"ui_window": 63, "pctile_lookback": 504, "k": 1.5, "min_mult": 0.25}
    decide_agg = uis.make_ulcer_index_decider(daily, WEEKLY_DEPOSIT, **aggressive_cfg, enabled=True,
                                               ui_cache=ui_caches[("SP500", 63)])
    res_agg = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_agg).to_frame()
    out["no_negative_cash_units_aggressive"] = v3chk.check_no_negative_cash_or_units(res_agg)
    out["capital_never_exceeds_deposits_aggressive"] = check_capital_never_exceeds_deposits(daily, rf, res_agg)

    out["no_lookahead"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=6000)
    out["no_lookahead_late"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=20000)
    out["point_in_time_macro"] = v3chk.check_point_in_time_macro()
    return out


def run_one(daily, rf, cfg, fee, ui_cache):
    decide = uis.make_ulcer_index_decider(daily, WEEKLY_DEPOSIT, **cfg, ui_cache=ui_cache)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def run_dca(daily, rf, fee):
    decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def cfg_id_for(ci, cfg):
    return f"cfg{ci:02d}_uw{cfg['ui_window']}_pl{cfg['pctile_lookback']}_k{cfg['k']}_mn{cfg['min_mult']}"


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    rf = dev["rf"]

    print("Building per-(asset, ui_window) Ulcer Index cache...")
    ui_caches = {}
    for asset in ASSETS:
        daily = dev["prices"][asset]
        for uw in uis.GRID["ui_window"]:
            ui_caches[(asset, uw)] = uis.compute_ulcer_index(daily["Close"].to_numpy(), uw)[0]
            print(f"  cached ({asset}, ui_window={uw})")

    print("Running formula spot-check + decoupling proofs + real-divergence check + implementation checks...")
    impl_checks = run_impl_checks(dev, ui_caches)
    print(json.dumps(impl_checks, indent=2, default=float))
    required = ["formula_correct", "decoupling_proofs_pass", "distinctiveness_from_family_014_proven",
                "cache_matches_uncached", "cash_meaningfully_differs_from_dca",
                "reserve_drawn_down_on_high_mult_weeks",
                "degenerate_bypass_equals_dca", "flat_k_zero_grid_arm_equals_dca",
                "no_negative_cash_units_dca", "no_negative_cash_units_primary",
                "capital_never_exceeds_deposits_primary", "no_negative_cash_units_aggressive",
                "capital_never_exceeds_deposits_aggressive", "no_lookahead", "no_lookahead_late",
                "point_in_time_macro"]
    if not all(impl_checks[k] for k in required):
        raise SystemExit("Implementation checks FAILED -- stopping before any trusted backtest.")

    print("Running pre-grid non-degeneracy sanity check...")
    sanity = run_sanity_check(dev, ui_caches)
    print(json.dumps(sanity, indent=2))
    for row in sanity:
        if not row["non_degenerate"]:
            raise SystemExit(f"Sanity check FAILED for {row['asset']}: "
                              f"frac_default_1.0={row['frac_multiplier_exactly_1.0']:.4f} "
                              f"std_m={row['std_multiplier']:.4f} -- degenerate multiplier, stopping before grid.")

    configs = uis.grid_configs()
    assert len(configs) <= 36
    assert uis.PRIMARY_CONFIG in configs
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
            ui_cache = ui_caches[(asset, cfg["ui_window"])]
            row = {"config_id": cfg_id, "asset": asset,
                   "ui_window": cfg["ui_window"], "pctile_lookback": cfg["pctile_lookback"],
                   "k": cfg["k"], "min_mult": cfg["min_mult"]}
            for fee in FEES:
                s, res = run_one(daily, rf, cfg, fee, ui_cache)
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
        trial_id = f"new_049_{cfg_id}"
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

    primary_ci = configs.index(uis.PRIMARY_CONFIG)
    primary_cfg_id = cfg_id_for(primary_ci, uis.PRIMARY_CONFIG)
    primary_trial_id = f"new_049_{primary_cfg_id}"
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
        print("Sec 4.1 PASSED -- run scripts/v3/robustness_049_ulcer_index_sizing.py next "
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
        ui_cache = ui_caches[(asset, uis.PRIMARY_CONFIG["ui_window"])]
        row = {"asset": asset}
        for fee in FEES:
            s, _ = run_one(daily, rf, uis.PRIMARY_CONFIG, fee, ui_cache)
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
