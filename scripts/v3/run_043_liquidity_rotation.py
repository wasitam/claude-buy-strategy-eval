"""Run family 043 (Amihud-illiquidity cross-asset rotation) end-to-end on
development data: pre-grid non-degeneracy checks -> implementation checks
-> full grid -> trial logging -> DSR/N_eff -> assess (portfolio win-rule
per prereg.md). Writes state/trials/new_043_*.csv, updates
state/trial_counter.json, and dumps results into
families/043-liquidity-rotation/_run_output.json for the results.md
writer.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, metrics as v3met, dsr as v3dsr
from src.backtest.v3 import portfolio_engine as v3pe
from src.backtest.v3.engine import week_end_flags
from src.backtest.v3.strategies import liquidity_rotation as lr

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "043-liquidity-rotation")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT_PER_ASSET = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]
BOOTSTRAP_PLACEBO_SIMS = 60  # cost-scoped down from plan's 500; run only if sec 4.1 passes (see prereg.md)


def build_shared_calendar(dev):
    prices = dev["prices"]
    start = max(df.index.min() for df in prices.values())
    idx = prices["SP500"].index
    idx = idx[idx >= start]
    aligned = {a: prices[a].reindex(idx).ffill().bfill() for a in ASSETS}
    return idx, aligned


def run_one(assets_ohlc, daily_rf, closes, idx, is_week_end, cfg, fee):
    decide = lr.make_liquidity_rotation_decider(
        assets_ohlc, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **cfg, enabled=True,
    )
    res = v3pe.run_portfolio(assets_ohlc, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, decide, fee=fee)
    frame = res.to_frame()
    final_wealth = float(res.cash[-1] + sum(res.units[a][-1] * closes[a][-1] for a in ASSETS))
    s = v3met.summarize_portfolio(frame, daily_rf, final_wealth)
    return s, res


def run_dca(assets_ohlc, daily_rf, closes, fee):
    decide = v3pe.make_fixed_weight_dca_decider(WEEKLY_DEPOSIT_PER_ASSET, ASSETS)
    res = v3pe.run_portfolio(assets_ohlc, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, decide, fee=fee)
    frame = res.to_frame()
    final_wealth = float(res.cash[-1] + sum(res.units[a][-1] * closes[a][-1] for a in ASSETS))
    s = v3met.summarize_portfolio(frame, daily_rf, final_wealth)
    return s, res


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    idx, aligned = build_shared_calendar(dev)
    daily_rf = dev["rf"].reindex(idx).ffill().fillna(0.0)
    closes = {a: aligned[a]["Close"].to_numpy() for a in ASSETS}
    is_week_end = week_end_flags(idx)
    print(f"Shared calendar: {len(idx)} days, {idx[0].date()} -> {idx[-1].date()}")

    # Sanity: confirm the shared calendar never touches 2020+ (dev gate is
    # enforced by v3data.load_dev() itself, but re-verified here per this
    # iteration's explicit instruction never to spot-check 2020+ dates).
    assert idx[-1] < pd.Timestamp("2020-01-01"), "shared calendar leaks into the sealed holdout period"

    # --- Pre-grid non-degeneracy / weight-dynamics checks (per prereg.md, before any grid is trusted) ---
    print("Pre-grid non-degeneracy checks (primary config)...")
    weights_primary = lr.compute_target_weights(aligned, idx, **lr.PRIMARY_CONFIG)
    weekend_weights = weights_primary.loc[is_week_end]

    # (a) PRIMARY_CONFIG is a member of GRID -- already asserted at import
    # time in liquidity_rotation.py; re-confirmed here against the actual
    # enumerated grid list.
    configs = lr.grid_configs()
    assert lr.PRIMARY_CONFIG in configs, "PRIMARY_CONFIG not in grid_configs()"

    # (b) selection is not frozen on one fixed asset / one fixed order:
    # per-asset selection frequency among week-end days, and how often the
    # selected set changes week-to-week (turnover).
    selected = (weekend_weights > 0).astype(int)
    selection_freq = {a: float(selected[a].mean()) for a in ASSETS}
    picks_per_week = selected.apply(lambda row: frozenset(row.index[row.astype(bool)]), axis=1)
    turnover = float((picks_per_week != picks_per_week.shift(1)).iloc[1:].mean())
    # own-history percentile cross-correlation: if the 5 assets' percentile
    # series were near-perfectly correlated, "currently most liquid of the
    # 5" would degenerate to a fixed, time-invariant ranking.
    pctile_cols = {}
    for a in ASSETS:
        raw = lr.compute_own_percentile(aligned[a], lr.PRIMARY_CONFIG["illiq_lookback"])
        pctile_cols[a] = pd.Series(raw, index=idx)
    pctile_df = pd.DataFrame(pctile_cols)
    xcorr = pctile_df.corr()
    max_offdiag_corr = float(xcorr.where(~np.eye(len(ASSETS), dtype=bool)).abs().max().max())

    non_degenerate = (
        all(0.02 < f < 0.98 for f in selection_freq.values())
        and 0.02 < turnover < 0.98
        and max_offdiag_corr < 0.9
    )
    print("  selection_freq:", selection_freq)
    print("  turnover:", turnover, "max_offdiag_pctile_corr:", max_offdiag_corr)
    print("  non_degenerate:", non_degenerate)
    pre_grid_checks = {
        "selection_freq": selection_freq, "turnover": turnover,
        "max_offdiag_pctile_corr": max_offdiag_corr, "non_degenerate": bool(non_degenerate),
        "primary_config_in_grid": True, "dev_calendar_end": str(idx[-1].date()),
    }
    if not non_degenerate:
        raise SystemExit("Pre-grid non-degeneracy check FAILED -- stopping before any trusted backtest.")

    print("Running implementation checks...")
    impl_checks = {}

    # 1. degenerate (enabled=False) == fixed-weight DCA (bit-for-bit)
    dca_decide = v3pe.make_fixed_weight_dca_decider(WEEKLY_DEPOSIT_PER_ASSET, ASSETS)
    dca_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, dca_decide, fee=0.001)
    deg_decide = lr.make_liquidity_rotation_decider(
        aligned, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, enabled=False,
    )
    deg_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, deg_decide, fee=0.001)
    ok_units = all(np.allclose(dca_res.units[a], deg_res.units[a], atol=1e-6) for a in ASSETS)
    ok_cash = np.allclose(dca_res.cash, deg_res.cash, atol=1e-4)
    impl_checks["degenerate_enabled_false_equals_fixed_weight_dca"] = bool(ok_units and ok_cash)

    # 2. SECOND reference point (families 013/029 precedent): top_n=5 (all
    #    5 assets always selected -> collapses to 1/5 each every week) must
    #    reproduce an INDEPENDENTLY-built equal-weight weekly-rebalance
    #    reference decider, bit-for-bit, and must differ from plain DCA.
    top5_cfg = {"illiq_lookback": 252, "top_n": 5, "signal_smooth_days": 10}
    top5_decide = lr.make_liquidity_rotation_decider(
        aligned, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **top5_cfg, enabled=True,
    )
    top5_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, top5_decide, fee=0.001)
    ew_decide = lr.make_equal_weight_rebalance_decider(ASSETS, closes, is_week_end)
    ew_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, ew_decide, fee=0.001)
    ok_units2 = all(np.allclose(top5_res.units[a], ew_res.units[a], atol=1e-6) for a in ASSETS)
    ok_cash2 = np.allclose(top5_res.cash, ew_res.cash, atol=1e-4)
    impl_checks["top_n_5_equals_equal_weight_rebalance_reference"] = bool(ok_units2 and ok_cash2)
    differs_from_dca = not (
        all(np.allclose(dca_res.units[a], top5_res.units[a], atol=1e-6) for a in ASSETS)
        and np.allclose(dca_res.cash, top5_res.cash, atol=1e-4)
    )
    impl_checks["top_n_5_differs_from_plain_dca"] = bool(differs_from_dca)

    # 3. cash and positions never negative (DCA baseline, primary config, top_n=1 most-concentrated corner)
    def no_neg(res):
        if (res.cash < -1e-6).any():
            return False
        for a in ASSETS:
            if (res.units[a] < -1e-6).any():
                return False
        return True
    impl_checks["no_negative_cash_units_dca"] = no_neg(dca_res)

    primary_decide = lr.make_liquidity_rotation_decider(
        aligned, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **lr.PRIMARY_CONFIG, enabled=True,
    )
    primary_res = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, primary_decide, fee=0.001)
    impl_checks["no_negative_cash_units_primary"] = no_neg(primary_res)

    # 4. no-lookahead: perturb all 5 assets' data after t_check, confirm
    #    orders on/before t_check unchanged.
    rng = np.random.default_rng(3)
    t_check = len(idx) - 400
    perturbed = {a: aligned[a].copy() for a in ASSETS}
    noise = 1.0 + rng.normal(0, 0.2, size=len(idx) - t_check - 1)
    for a in ASSETS:
        for col in ["Open", "High", "Low", "Close"]:
            perturbed[a].iloc[t_check + 1:, perturbed[a].columns.get_loc(col)] = (
                perturbed[a].iloc[t_check + 1:][col].to_numpy() * noise
            )
    decide_a = lr.make_liquidity_rotation_decider(
        aligned, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **lr.PRIMARY_CONFIG, enabled=True,
    )
    res_a = v3pe.run_portfolio(aligned, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, decide_a, fee=0.001)
    decide_b = lr.make_liquidity_rotation_decider(
        perturbed, idx, is_week_end, WEEKLY_DEPOSIT_PER_ASSET, ASSETS, **lr.PRIMARY_CONFIG, enabled=True,
    )
    res_b = v3pe.run_portfolio(perturbed, WEEKLY_DEPOSIT_PER_ASSET, daily_rf, decide_b, fee=0.001)
    ok = True
    for a in ASSETS:
        ba = res_a.buy_usd[a][:t_check + 1]
        bb = res_b.buy_usd[a][:t_check + 1]
        sa = res_a.sell_usd[a][:t_check + 1]
        sb = res_b.sell_usd[a][:t_check + 1]
        if not (np.allclose(ba, bb, atol=1e-6) and np.allclose(sa, sb, atol=1e-6)):
            ok = False
    impl_checks["no_lookahead"] = ok
    impl_checks["point_in_time_macro"] = True  # price+volume only, no ALFRED-vintage series

    print(json.dumps(impl_checks, indent=2))
    if not all(impl_checks.values()):
        raise SystemExit("Implementation checks FAILED -- stopping before any trusted backtest.")

    assert len(configs) <= 36
    print(f"Grid: {len(configs)} configs")

    dca_cache = {}
    for fee in FEES:
        dca_cache[fee] = run_dca(aligned, daily_rf, closes, fee)[0]

    grid_rows = []
    trial_series = {}
    per_config_weekly = {}

    new_trial_count = 0
    for ci, cfg in enumerate(configs):
        cfg_id = f"cfg{ci:02d}_lb{cfg['illiq_lookback']}_n{cfg['top_n']}_sm{cfg['signal_smooth_days']}"
        row = {"config_id": cfg_id, **cfg}
        excess_by_fee = {}
        for fee in FEES:
            s, res = run_one(aligned, daily_rf, closes, idx, is_week_end, cfg, fee)
            dca_s = dca_cache[fee]
            row[f"wealth_over_invested_fee{fee}"] = s["wealth_over_invested"]
            row[f"sharpe_fee{fee}"] = s["sharpe"]
            row[f"dca_wealth_over_invested_fee{fee}"] = dca_s["wealth_over_invested"]
            row[f"dca_sharpe_fee{fee}"] = dca_s["sharpe"]
            beats_wealth = s["wealth_over_invested"] > dca_s["wealth_over_invested"]
            beats_sharpe = (s["sharpe"] if not np.isnan(s["sharpe"]) else -np.inf) > \
                           (dca_s["sharpe"] if not np.isnan(dca_s["sharpe"]) else -np.inf)
            row[f"beats_dca_fee{fee}"] = bool(beats_wealth and beats_sharpe)
            per_config_weekly.setdefault(cfg_id, {})[fee] = s["weekly_returns"]
            if fee == 0.001:
                idx_w = s["weekly_returns"].index
                dret = dca_s["weekly_returns"].reindex(idx_w).fillna(0.0)
                excess_by_fee[fee] = (s["weekly_returns"] - dret).dropna()
        grid_rows.append(row)

        pooled = excess_by_fee[0.001]
        trial_id = f"new_043_{cfg_id}"
        trial_series[trial_id] = pooled
        pooled.rename("excess_return").reset_index().rename(columns={"index": "date"}).to_csv(
            os.path.join(TRIALS_DIR, f"{trial_id}.csv"), index=False
        )
        new_trial_count += 1
        print(f"  {cfg_id}: beats_dca@0.1%={row['beats_dca_fee0.001']} beats_dca@0.25%={row['beats_dca_fee0.0025']}")

    grid_df = pd.DataFrame(grid_rows)
    grid_df.to_csv(os.path.join(FAM_DIR, "grid_results.csv"), index=False)

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

    primary_ci = configs.index(lr.PRIMARY_CONFIG)
    primary_cfg_id = (
        f"cfg{primary_ci:02d}_lb{lr.PRIMARY_CONFIG['illiq_lookback']}"
        f"_n{lr.PRIMARY_CONFIG['top_n']}_sm{lr.PRIMARY_CONFIG['signal_smooth_days']}"
    )
    primary_trial_id = f"new_043_{primary_cfg_id}"
    primary_series = trial_series[primary_trial_id]

    dsr_neff = v3dsr.deflated_sharpe_ratio(primary_series.to_numpy(), cluster_sharpes, n_eff)
    dsr_rawn = v3dsr.deflated_sharpe_ratio(
        primary_series.to_numpy(),
        np.array([v3dsr._sharpe(s.dropna().to_numpy()) for s in all_series.values()]),
        len(all_series),
    )
    print("DSR (N_eff):", dsr_neff)
    print("DSR (raw N):", dsr_rawn)

    # --- sec 4.1 (Portfolio line): beats fixed-weight 5-asset DCA on wealth+Sharpe, both fees ---
    primary_row = grid_df[grid_df["config_id"] == primary_cfg_id].iloc[0]
    check_4_1 = {
        "beats_dca_fee0.1pct": bool(primary_row["beats_dca_fee0.001"]),
        "beats_dca_fee0.25pct": bool(primary_row["beats_dca_fee0.0025"]),
        "pass": bool(primary_row["beats_dca_fee0.001"] and primary_row["beats_dca_fee0.0025"]),
    }

    # --- sec 4.4: >=2/3 of grid beats DCA at 0.1% fee (portfolio-level, wealth+sharpe) ---
    frac_grid_pass = float(grid_df["beats_dca_fee0.001"].mean())
    check_4_4_grid = {"frac_grid_configs_beat_dca": frac_grid_pass, "pass": frac_grid_pass >= 2 / 3}

    cscv_returns = {cfg_id: per_config_weekly[cfg_id][0.001] for cfg_id in grid_df["config_id"].unique()}
    cscv = v3dsr.cscv_pbo(cscv_returns, n_splits=8)
    print("CSCV PBO (portfolio grid):", cscv)

    out = {
        "impl_checks": impl_checks,
        "pre_grid_checks": pre_grid_checks,
        "n_seed": counter["seed"], "n_new": new_trial_count, "n_total_raw": len(all_series),
        "n_eff": n_eff,
        "dsr_neff": dsr_neff, "dsr_rawn": dsr_rawn,
        "check_4_1": check_4_1,
        "check_4_4_grid": check_4_4_grid,
        "cscv_pbo": cscv,
        "primary_cfg_id": primary_cfg_id,
        "primary_trial_id": primary_trial_id,
        "shared_calendar_start": str(idx[0].date()),
        "shared_calendar_end": str(idx[-1].date()),
        "n_calendar_days": len(idx),
    }
    with open(os.path.join(FAM_DIR, "_run_output.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)
    print("Wrote", os.path.join(FAM_DIR, "_run_output.json"))
    return out, primary_res, dca_res, aligned, closes, idx, is_week_end, daily_rf, grid_df, dca_cache


if __name__ == "__main__":
    main()
