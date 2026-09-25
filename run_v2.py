"""v2 end-to-end pipeline: SmartDCA / ADCA / Rebalanced-portfolio backtests
against DCA and its variants, per btc-gold-silver-backtest-spec-v2.md.

Run with:  .venv/bin/python run_v2.py
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from backtest.v2 import data as d2
from backtest.v2 import engine as eng
from backtest.v2 import strategies as strat
from backtest.v2 import rebalance as rb
from backtest.v2 import metrics as met
from backtest.v2 import robustness as rob
from backtest.v2 import checks as chk
from backtest.v2 import report as rpt

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports", "v2")
os.makedirs(REPORTS_DIR, exist_ok=True)

FEE = 0.001
SINGLE_DEPOSIT = 500.0
PORTFOLIO_DEPOSIT = 1500.0

SMARTDCA_GRID = [(rho, m_max, sweep) for rho in (1, 2, 3) for m_max in (2, 3) for sweep in (False, True)]
ADCA_VARIANTS = ["B1", "B2"]
REBALANCE_GRID = [
    ("C1", "bands_5_25"), ("C2", "bands_5_25"),
    ("C1", "bands_10_50"), ("C2", "bands_10_50"),
    ("C1", "calendar_quarterly"), ("C2", "calendar_quarterly"),
    ("C3", "bands_5_25"),
]

N_ROLLING_STEP = 13
N_BOOTSTRAP_SINGLE = 200
N_BOOTSTRAP_PORTFOLIO = 60
N_PLACEBO = 200


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    log("Fetching data...")
    raw = d2.fetch_all(force=False)
    wbtc = d2.to_weekly_wfri(d2.clean_ohlc(raw["BTC"]))
    wgold = d2.to_weekly_wfri(d2.clean_ohlc(raw["GOLD"]))
    wsilver = d2.to_weekly_wfri(d2.clean_ohlc(raw["SILVER"]))
    for name, w in [("BTC", wbtc), ("GOLD", wgold), ("SILVER", wsilver)]:
        bad = d2.flag_bad_ticks(w)
        log(f"{name}: {len(w)} weekly candles, {w.index.min().date()} -> {w.index.max().date()}, "
            f"{int(bad.sum())} weeks flagged >50% move")

    weekly_single = {"BTC": wbtc, "GOLD": wgold, "SILVER": wsilver}
    rf_single = {a: d2.weekly_rf_rate(raw["IRX"], w.index) for a, w in weekly_single.items()}
    vix_single = {a: d2.weekly_vix(raw["VIX"], w.index) for a, w in weekly_single.items()}
    unrate_single = {a: d2.weekly_fred_lagged(raw["UNRATE"], "UNRATE", w.index) for a, w in weekly_single.items()}
    tcu_single = {a: d2.weekly_fred_lagged(raw["TCU"], "TCU", w.index) for a, w in weekly_single.items()}

    # --- Implementation checks (spec 11) ---
    log("Running implementation checks...")
    checks = chk.run_all_checks(wbtc, {"BTC": wbtc}, rf_single["BTC"])
    for k, v in checks.items():
        log(f"  {k}: {'PASS' if v else 'FAIL'}")
    with open(os.path.join(REPORTS_DIR, "implementation_checks.json"), "w") as f:
        json.dump({k: bool(v) for k, v in checks.items()}, f, indent=2)

    # =========================================================================
    # Strategy A: SmartDCA -- full grid, all 3 assets
    # =========================================================================
    log("Strategy A (SmartDCA): running full grid...")
    smartdca_rows = []
    dca_bench_cache = {}
    for asset, w in weekly_single.items():
        rf = rf_single[asset]
        dca_decide = strat.make_dca_decider(SINGLE_DEPOSIT)
        dca_res = eng.run_single_asset(w, SINGLE_DEPOSIT, rf, dca_decide).to_frame()
        dca_s = met.summarize(dca_res, rf, w["Close"].iloc[-1])
        dca_bench_cache[asset] = (dca_res, dca_s)

        for rho, m_max, sweep in SMARTDCA_GRID:
            decide = strat.make_smartdca_decider(w, SINGLE_DEPOSIT, rho, m_max, sweep)
            res = eng.run_single_asset(w, SINGLE_DEPOSIT, rf, decide).to_frame()
            s = met.summarize(res, rf, w["Close"].iloc[-1])
            smartdca_rows.append({
                "asset": asset, "rho": rho, "m_max": m_max, "sweep": sweep,
                **{k: v for k, v in s.items() if k != "nav"},
                "dca_wealth_over_invested": dca_s["wealth_over_invested"],
                "dca_sharpe": dca_s["sharpe"], "dca_avg_cost_per_unit": dca_s["avg_cost_per_unit"],
                "dca_max_drawdown": dca_s["max_drawdown"],
            })
    smartdca_df = pd.DataFrame(smartdca_rows)
    smartdca_df.to_csv(os.path.join(REPORTS_DIR, "smartdca_grid.csv"), index=False)
    log(f"  {len(smartdca_df)} rows -> smartdca_grid.csv")

    # =========================================================================
    # Strategy B: ADCA -- B1 and B2, all 3 assets
    # =========================================================================
    log("Strategy B (ADCA): running B1 + B2 on all assets...")
    adca_rows = []
    adca_scores = {}
    for asset, w in weekly_single.items():
        rf = rf_single[asset]
        dca_res, dca_s = dca_bench_cache[asset]
        score_b1 = strat.adca_regime_score_b1(w, vix_single[asset], unrate_single[asset], tcu_single[asset])
        score_b2 = strat.adca_regime_score_b2(w, vix_single[asset])
        adca_scores[asset] = {"B1": score_b1, "B2": score_b2}
        for variant, score in [("B1", score_b1), ("B2", score_b2)]:
            decide = strat.make_adca_decider(SINGLE_DEPOSIT, score)
            res = eng.run_single_asset(w, SINGLE_DEPOSIT, rf, decide).to_frame()
            s = met.summarize(res, rf, w["Close"].iloc[-1])
            adca_rows.append({
                "asset": asset, "variant": variant,
                **{k: v for k, v in s.items() if k != "nav"},
                "dca_wealth_over_invested": dca_s["wealth_over_invested"],
                "dca_sharpe": dca_s["sharpe"], "dca_max_drawdown": dca_s["max_drawdown"],
            })
    adca_df = pd.DataFrame(adca_rows)
    adca_df.to_csv(os.path.join(REPORTS_DIR, "adca_grid.csv"), index=False)
    log(f"  {len(adca_df)} rows -> adca_grid.csv")

    # =========================================================================
    # Strategy C: rebalanced portfolio -- 3-asset era + gold/silver-only era
    # =========================================================================
    log("Strategy C: building portfolio eras...")
    btc_start = wbtc.index.min() + pd.Timedelta(weeks=52)  # spec 6.5 warm-up
    idx3 = wbtc.index[wbtc.index >= btc_start].intersection(wgold.index).intersection(wsilver.index)
    weekly3 = {"BTC": wbtc.reindex(idx3).ffill(), "GOLD": wgold.reindex(idx3).ffill(), "SILVER": wsilver.reindex(idx3).ffill()}
    rf3 = d2.weekly_rf_rate(raw["IRX"], idx3)
    assets3 = ["BTC", "GOLD", "SILVER"]

    gs_start = wgold.index.min() + pd.Timedelta(weeks=52)
    idx2 = wgold.index[wgold.index >= gs_start].intersection(wsilver.index)
    weekly2 = {"GOLD": wgold.reindex(idx2).ffill(), "SILVER": wsilver.reindex(idx2).ffill()}
    rf2 = d2.weekly_rf_rate(raw["IRX"], idx2)
    assets2 = ["GOLD", "SILVER"]

    eras = {"BTC+Gold+Silver": (weekly3, assets3, rf3, idx3), "Gold+Silver only": (weekly2, assets2, rf2, idx2)}

    rebalance_rows = []
    rebalance_bench_cache = {}
    era_target_weights = {}
    for era_name, (weekly_e, assets_e, rf_e, idx_e) in eras.items():
        closes_e = {a: weekly_e[a]["Close"] for a in assets_e}
        for scheme, trigger in REBALANCE_GRID:
            weights = rb.build_target_weights(scheme, closes_e, assets_e, idx_e)
            era_target_weights[(era_name, scheme)] = weights
            res = rb.run_portfolio(weekly_e, assets_e, PORTFOLIO_DEPOSIT, rf_e, weights, trigger_mode=trigger, fee=FEE)
            s = met.summarize_portfolio(res, rf_e)

            fixed_res = rb.run_portfolio(weekly_e, assets_e, PORTFOLIO_DEPOSIT, rf_e, weights, trigger_mode="never", fee=FEE)
            fixed_s = met.summarize_portfolio(fixed_res, rf_e)
            rebalance_bench_cache[(era_name, scheme, trigger)] = (res, s, fixed_res, fixed_s, weights)

            rebalance_rows.append({
                "era": era_name, "scheme": scheme, "trigger": trigger,
                **{k: v for k, v in s.items() if k != "nav"},
                "fixed_wealth_over_invested": fixed_s["wealth_over_invested"],
                "fixed_sharpe": fixed_s["sharpe"], "fixed_max_drawdown": fixed_s["max_drawdown"],
            })

        # single-asset DCA benchmarks at $1500/wk
        for a in assets_e:
            decide = strat.make_dca_decider(PORTFOLIO_DEPOSIT)
            res = eng.run_single_asset(weekly_e[a], PORTFOLIO_DEPOSIT, rf_e, decide).to_frame()
            s = met.summarize(res, rf_e, weekly_e[a]["Close"].iloc[-1])
            rebalance_rows.append({
                "era": era_name, "scheme": f"100% {a} DCA", "trigger": "n/a",
                "total_invested": s["total_invested"], "final_wealth": s["final_wealth"],
                "wealth_over_invested": s["wealth_over_invested"], "max_drawdown": s["max_drawdown"],
                "longest_weeks_underwater": s["longest_weeks_underwater"], "cagr": s["cagr"],
                "annualized_vol": s["annualized_vol"], "sharpe": s["sharpe"], "sortino": s["sortino"],
                "calmar": s["calmar"], "n_rebalances": 0, "total_fees": s["total_fees"],
                "avg_cash_share": s["avg_cash_share"],
                "fixed_wealth_over_invested": np.nan, "fixed_sharpe": np.nan, "fixed_max_drawdown": np.nan,
            })
    rebalance_df = pd.DataFrame(rebalance_rows)
    rebalance_df.to_csv(os.path.join(REPORTS_DIR, "rebalance_grid.csv"), index=False)
    log(f"  {len(rebalance_df)} rows -> rebalance_grid.csv")

    # =========================================================================
    # Deep dive + robustness: representative variants
    # =========================================================================
    log("Deep dive + robustness...")
    deep_dive = {"smartdca": {}, "adca": {}, "rebalance": {}}

    SMARTDCA_PRIMARY = (2, 3, True)  # rho=2, m_max=3, sweep=on
    for asset, w in weekly_single.items():
        rf = rf_single[asset]
        dca_res, dca_s = dca_bench_cache[asset]
        rho, m_max, sweep = SMARTDCA_PRIMARY
        decide = strat.make_smartdca_decider(w, SINGLE_DEPOSIT, rho, m_max, sweep)
        res = eng.run_single_asset(w, SINGLE_DEPOSIT, rf, decide).to_frame()
        s = met.summarize(res, rf, w["Close"].iloc[-1])

        slug = f"smartdca_{asset}"
        fig_value = rpt.plot_value_vs_deposits(res, dca_res, w["Close"].iloc[-1], w["Close"].iloc[-1],
                                                f"{asset} SmartDCA (rho=2,m_max=3,sweep=on) vs DCA", f"{slug}_value.png")
        fig_dd = rpt.plot_nav_drawdown(s["nav"], dca_s["nav"], w.index, f"{asset} SmartDCA drawdown vs DCA", f"{slug}_dd.png")
        fig_buy = rpt.plot_buy_amounts(w, res["buy_usd"].to_numpy(), f"{asset} SmartDCA weekly buy amount vs price", f"{slug}_buys.png")

        log(f"  SmartDCA {asset}: rolling windows...")
        strat_builder = lambda ww, rho=rho, m_max=m_max, sweep=sweep: strat.make_smartdca_decider(ww, SINGLE_DEPOSIT, rho, m_max, sweep)
        bench_builder = lambda ww: strat.make_dca_decider(SINGLE_DEPOSIT)
        wy_list = [2, 3] if asset == "BTC" else [3, 5]
        rolling = {}
        for wy in wy_list:
            rw = rob.rolling_windows_single_asset(w, rf, SINGLE_DEPOSIT, strat_builder, bench_builder, wy, step_weeks=N_ROLLING_STEP)
            fig_rw = rpt.plot_rolling_window_summary(rw, f"{asset} SmartDCA {wy}y rolling windows vs DCA", f"{slug}_rolling{wy}y.png")
            rolling[wy] = {"n_windows": len(rw), "win_rate_wealth": float(rw["beats_wealth"].mean()) if len(rw) else np.nan,
                            "win_rate_sharpe": float(rw["beats_sharpe"].mean()) if len(rw) else np.nan, "fig": fig_rw}

        log(f"  SmartDCA {asset}: block bootstrap...")
        bb_raw = rob.block_bootstrap_single_asset(w, rf, SINGLE_DEPOSIT, strat_builder, bench_builder, n_sims=N_BOOTSTRAP_SINGLE, detrend=False)
        bb_dt = rob.block_bootstrap_single_asset(w, rf, SINGLE_DEPOSIT, strat_builder, bench_builder, n_sims=N_BOOTSTRAP_SINGLE, detrend=True)
        win_rates = {
            "wealth\n(raw)": float((bb_raw["strat_wealth_over_invested"] > bb_raw["bench_wealth_over_invested"]).mean()),
            "sharpe\n(raw)": float((bb_raw["strat_sharpe"] > bb_raw["bench_sharpe"]).mean()),
            "wealth\n(detrended)": float((bb_dt["strat_wealth_over_invested"] > bb_dt["bench_wealth_over_invested"]).mean()),
            "sharpe\n(detrended)": float((bb_dt["strat_sharpe"] > bb_dt["bench_sharpe"]).mean()),
        }
        fig_bb = rpt.plot_win_rate_bar(win_rates, f"{asset} SmartDCA block-bootstrap win rate vs DCA", f"{slug}_bootstrap.png")

        deep_dive["smartdca"][asset] = {
            "metrics": {k: v for k, v in s.items() if k != "nav"},
            "dca_metrics": {k: v for k, v in dca_s.items() if k != "nav"},
            "figs": {"value": fig_value, "dd": fig_dd, "buys": fig_buy, "bootstrap": fig_bb},
            "rolling": rolling, "bootstrap_win_rates": win_rates,
        }

    for asset, w in weekly_single.items():
        rf = rf_single[asset]
        dca_res, dca_s = dca_bench_cache[asset]
        deep_dive["adca"][asset] = {}
        for variant in ADCA_VARIANTS:
            score = adca_scores[asset][variant]
            decide = strat.make_adca_decider(SINGLE_DEPOSIT, score)
            res = eng.run_single_asset(w, SINGLE_DEPOSIT, rf, decide).to_frame()
            s = met.summarize(res, rf, w["Close"].iloc[-1])
            slug = f"adca_{variant}_{asset}"
            fig_value = rpt.plot_value_vs_deposits(res, dca_res, w["Close"].iloc[-1], w["Close"].iloc[-1],
                                                    f"{asset} ADCA {variant} vs DCA", f"{slug}_value.png")
            fig_dd = rpt.plot_nav_drawdown(s["nav"], dca_s["nav"], w.index, f"{asset} ADCA {variant} drawdown vs DCA", f"{slug}_dd.png")

            log(f"  ADCA {variant} {asset}: rolling windows...")
            strat_builder = (
                (lambda ww: strat.make_adca_decider(SINGLE_DEPOSIT, strat.adca_regime_score_b1(
                    ww, d2.weekly_vix(raw["VIX"], ww.index), d2.weekly_fred_lagged(raw["UNRATE"], "UNRATE", ww.index),
                    d2.weekly_fred_lagged(raw["TCU"], "TCU", ww.index))))
                if variant == "B1" else
                (lambda ww: strat.make_adca_decider(SINGLE_DEPOSIT, strat.adca_regime_score_b2(ww, d2.weekly_vix(raw["VIX"], ww.index))))
            )
            bench_builder = lambda ww: strat.make_dca_decider(SINGLE_DEPOSIT)
            wy_list = [2, 3] if asset == "BTC" else [3, 5]
            rolling = {}
            for wy in wy_list:
                rw = rob.rolling_windows_single_asset(w, rf, SINGLE_DEPOSIT, strat_builder, bench_builder, wy, step_weeks=N_ROLLING_STEP)
                fig_rw = rpt.plot_rolling_window_summary(rw, f"{asset} ADCA {variant} {wy}y rolling windows vs DCA", f"{slug}_rolling{wy}y.png")
                rolling[wy] = {"n_windows": len(rw), "win_rate_wealth": float(rw["beats_wealth"].mean()) if len(rw) else np.nan,
                                "win_rate_sharpe": float(rw["beats_sharpe"].mean()) if len(rw) else np.nan, "fig": fig_rw}

            log(f"  ADCA {variant} {asset}: block bootstrap + placebo...")
            bb_raw = rob.block_bootstrap_single_asset(w, rf, SINGLE_DEPOSIT, strat_builder, bench_builder, n_sims=N_BOOTSTRAP_SINGLE, detrend=False)
            bb_dt = rob.block_bootstrap_single_asset(w, rf, SINGLE_DEPOSIT, strat_builder, bench_builder, n_sims=N_BOOTSTRAP_SINGLE, detrend=True)
            win_rates = {
                "wealth\n(raw)": float((bb_raw["strat_wealth_over_invested"] > bb_raw["bench_wealth_over_invested"]).mean()),
                "sharpe\n(raw)": float((bb_raw["strat_sharpe"] > bb_raw["bench_sharpe"]).mean()),
                "wealth\n(detrended)": float((bb_dt["strat_wealth_over_invested"] > bb_dt["bench_wealth_over_invested"]).mean()),
                "sharpe\n(detrended)": float((bb_dt["strat_sharpe"] > bb_dt["bench_sharpe"]).mean()),
            }
            fig_bb = rpt.plot_win_rate_bar(win_rates, f"{asset} ADCA {variant} block-bootstrap win rate vs DCA", f"{slug}_bootstrap.png")

            placebo_df, pw, psh = rob.placebo_adca(w, rf, SINGLE_DEPOSIT, score, s["wealth_over_invested"], s["sharpe"], n_sims=N_PLACEBO)
            fig_placebo = rpt.plot_distribution(placebo_df, s["wealth_over_invested"], "wealth_over_invested",
                                                 f"{asset} ADCA {variant} placebo (shuffled regime) wealth/invested", f"{slug}_placebo.png")

            deep_dive["adca"][asset][variant] = {
                "metrics": {k: v for k, v in s.items() if k != "nav"},
                "dca_metrics": {k: v for k, v in dca_s.items() if k != "nav"},
                "figs": {"value": fig_value, "dd": fig_dd, "bootstrap": fig_bb, "placebo": fig_placebo},
                "rolling": rolling, "bootstrap_win_rates": win_rates,
                "placebo_percentile_wealth": pw, "placebo_percentile_sharpe": psh,
            }

    REBALANCE_PRIMARY = [("C2", "bands_5_25"), ("C3", "bands_5_25")]
    for era_name, (weekly_e, assets_e, rf_e, idx_e) in eras.items():
        deep_dive["rebalance"][era_name] = {}
        for scheme, trigger in REBALANCE_PRIMARY:
            res, s, fixed_res, fixed_s, weights = rebalance_bench_cache[(era_name, scheme, trigger)]
            slug = f"rebalance_{era_name.replace(' ', '').replace('+','')}_{scheme}"
            fig_weights = rpt.plot_portfolio_weights(res, assets_e, f"{era_name}: {scheme} portfolio weights over time", f"{slug}_weights.png")
            fig_dd = rpt.plot_nav_drawdown(s["nav"], fixed_s["nav"], idx_e, f"{era_name}: {scheme} drawdown vs fixed-weight never-rebalanced", f"{slug}_dd.png")

            log(f"  Rebalance {era_name} {scheme}: rolling windows...")
            wy_list = [2, 3] if era_name.startswith("BTC") else [3, 5]
            rolling = {}
            for wy in wy_list:
                rw = rob.rolling_windows_portfolio(weekly_e, assets_e, rf_e, PORTFOLIO_DEPOSIT, scheme, trigger, wy, step_weeks=N_ROLLING_STEP)
                fig_rw = rpt.plot_rolling_window_summary(rw, f"{era_name}: {scheme} {wy}y rolling windows vs fixed-weight", f"{slug}_rolling{wy}y.png")
                rolling[wy] = {"n_windows": len(rw), "win_rate_wealth": float(rw["beats_wealth"].mean()) if len(rw) else np.nan,
                                "win_rate_sharpe": float(rw["beats_sharpe"].mean()) if len(rw) else np.nan, "fig": fig_rw}

            log(f"  Rebalance {era_name} {scheme}: block bootstrap...")
            bb_raw = rob.block_bootstrap_portfolio(weekly_e, assets_e, rf_e, PORTFOLIO_DEPOSIT, scheme, trigger, n_sims=N_BOOTSTRAP_PORTFOLIO, detrend=False)
            bb_dt = rob.block_bootstrap_portfolio(weekly_e, assets_e, rf_e, PORTFOLIO_DEPOSIT, scheme, trigger, n_sims=N_BOOTSTRAP_PORTFOLIO, detrend=True)
            win_rates = {
                "wealth\n(raw)": float((bb_raw["strat_wealth_over_invested"] > bb_raw["bench_wealth_over_invested"]).mean()),
                "sharpe\n(raw)": float((bb_raw["strat_sharpe"] > bb_raw["bench_sharpe"]).mean()),
                "wealth\n(detrended)": float((bb_dt["strat_wealth_over_invested"] > bb_dt["bench_wealth_over_invested"]).mean()),
                "sharpe\n(detrended)": float((bb_dt["strat_sharpe"] > bb_dt["bench_sharpe"]).mean()),
            }
            fig_bb = rpt.plot_win_rate_bar(win_rates, f"{era_name}: {scheme} block-bootstrap win rate vs fixed-weight", f"{slug}_bootstrap.png")

            placebo_info = None
            if scheme == "C3":
                log(f"  Rebalance {era_name} C3: placebo trend-filter shuffle...")
                pdf, pw, psh = rob.placebo_c3_trend(weekly_e, assets_e, rf_e, PORTFOLIO_DEPOSIT, weights,
                                                     s["wealth_over_invested"], s["sharpe"], n_sims=N_PLACEBO, trigger_mode=trigger)
                fig_placebo = rpt.plot_distribution(pdf, s["wealth_over_invested"], "wealth_over_invested",
                                                     f"{era_name}: C3 placebo (shuffled trend filter) wealth/invested", f"{slug}_placebo.png")
                placebo_info = {"percentile_wealth": pw, "percentile_sharpe": psh, "fig": fig_placebo}

            deep_dive["rebalance"][era_name][scheme] = {
                "metrics": {k: v for k, v in s.items() if k != "nav"},
                "fixed_metrics": {k: v for k, v in fixed_s.items() if k != "nav"},
                "figs": {"weights": fig_weights, "dd": fig_dd, "bootstrap": fig_bb},
                "rolling": rolling, "bootstrap_win_rates": win_rates, "placebo": placebo_info,
            }

    # =========================================================================
    # Grid heatmaps
    # =========================================================================
    log("Generating grid heatmaps...")
    heatmap_figs = {}
    for asset in weekly_single:
        sub = smartdca_df[(smartdca_df["asset"] == asset) & (smartdca_df["sweep"] == True)]
        heatmap_figs[f"smartdca_{asset}_wealth"] = rpt.plot_grid_heatmap(
            sub, "rho", "m_max", "wealth_over_invested", f"{asset} SmartDCA (sweep=on) — wealth/invested by rho x m_max",
            f"heatmap_smartdca_{asset}_wealth.png")
        heatmap_figs[f"smartdca_{asset}_cost"] = rpt.plot_grid_heatmap(
            sub, "rho", "m_max", "avg_cost_per_unit", f"{asset} SmartDCA (sweep=on) — avg cost/unit by rho x m_max",
            f"heatmap_smartdca_{asset}_cost.png")

    # Save deep dive as JSON
    def _clean(obj):
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, (np.floating, np.integer, np.bool_)):
            return obj.item()
        if isinstance(obj, (pd.Timestamp,)):
            return str(obj)
        return obj

    with open(os.path.join(REPORTS_DIR, "deep_dive.json"), "w") as f:
        json.dump(_clean(deep_dive), f, indent=2, default=str)

    log("Writing markdown report...")
    from write_report_v2 import write_report_v2
    write_report_v2(smartdca_df, adca_df, rebalance_df, deep_dive, heatmap_figs, checks, eras)

    log("Done.")


if __name__ == "__main__":
    main()
