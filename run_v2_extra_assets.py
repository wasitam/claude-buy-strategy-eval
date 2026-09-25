"""Extends the v2 SmartDCA / ADCA tests to oil and an energy stock, to check
whether the gold/silver-like (non-100x, non-short-timeframe) findings hold
on a third kind of asset. Strategy C (rebalanced portfolio) is intentionally
NOT extended here -- it's a fixed BTC/gold/silver construct in the spec.

Assets added:
  - CL=F  : WTI crude oil continuous futures ("oil index"), same =F
            convention the spec already uses for gold/silver.
  - XLE   : Energy Select Sector SPDR ETF ("energy stock" -- a basket of
            energy equities, since a single stock's idiosyncratic risk
            makes it a poor stand-in for "energy" generally).

Run with:  .venv/bin/python run_v2_extra_assets.py
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
from backtest.v2 import metrics as met
from backtest.v2 import robustness as rob
from backtest.v2 import report as rpt

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports", "v2")
os.makedirs(REPORTS_DIR, exist_ok=True)

FEE = 0.001
SINGLE_DEPOSIT = 500.0
SMARTDCA_GRID = [(rho, m_max, sweep) for rho in (1, 2, 3) for m_max in (2, 3) for sweep in (False, True)]
ADCA_VARIANTS = ["B1", "B2"]
N_ROLLING_STEP = 13
N_BOOTSTRAP_SINGLE = 200
N_PLACEBO = 200

EXTRA_TICKERS = {"OIL": "CL=F", "ENERGY": "XLE"}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    log("Fetching extra assets (oil, energy) + shared series...")
    raw = {}
    for name, ticker in EXTRA_TICKERS.items():
        raw[name] = d2.fetch_yf(name, ticker, force=False)
        log(f"{name} ({ticker}): {len(raw[name])} rows, {raw[name].index.min().date()} -> {raw[name].index.max().date()}")
    raw["IRX"] = d2.fetch_yf("IRX", "^IRX", force=False)
    raw["VIX"] = d2.fetch_yf("VIX", "^VIX", force=False)
    raw["UNRATE"] = d2.fetch_fred("UNRATE", force=False)
    raw["TCU"] = d2.fetch_fred("TCU", force=False)

    weekly = {name: d2.to_weekly_wfri(d2.clean_ohlc(raw[name])) for name in EXTRA_TICKERS}
    rf = {a: d2.weekly_rf_rate(raw["IRX"], w.index) for a, w in weekly.items()}
    vix = {a: d2.weekly_vix(raw["VIX"], w.index) for a, w in weekly.items()}
    unrate = {a: d2.weekly_fred_lagged(raw["UNRATE"], "UNRATE", w.index) for a, w in weekly.items()}
    tcu = {a: d2.weekly_fred_lagged(raw["TCU"], "TCU", w.index) for a, w in weekly.items()}
    for name, w in weekly.items():
        log(f"{name}: {len(w)} weekly candles, {w.index.min().date()} -> {w.index.max().date()}")

    # ---------------- SmartDCA full grid ----------------
    smartdca_rows = []
    dca_bench_cache = {}
    for asset, w in weekly.items():
        rf_a = rf[asset]
        dca_decide = strat.make_dca_decider(SINGLE_DEPOSIT)
        dca_res = eng.run_single_asset(w, SINGLE_DEPOSIT, rf_a, dca_decide).to_frame()
        dca_s = met.summarize(dca_res, rf_a, w["Close"].iloc[-1])
        dca_bench_cache[asset] = (dca_res, dca_s)
        for rho, m_max, sweep in SMARTDCA_GRID:
            decide = strat.make_smartdca_decider(w, SINGLE_DEPOSIT, rho, m_max, sweep)
            res = eng.run_single_asset(w, SINGLE_DEPOSIT, rf_a, decide).to_frame()
            s = met.summarize(res, rf_a, w["Close"].iloc[-1])
            smartdca_rows.append({
                "asset": asset, "rho": rho, "m_max": m_max, "sweep": sweep,
                **{k: v for k, v in s.items() if k != "nav"},
                "dca_wealth_over_invested": dca_s["wealth_over_invested"],
                "dca_sharpe": dca_s["sharpe"], "dca_avg_cost_per_unit": dca_s["avg_cost_per_unit"],
                "dca_max_drawdown": dca_s["max_drawdown"],
            })
    smartdca_df = pd.DataFrame(smartdca_rows)
    smartdca_df.to_csv(os.path.join(REPORTS_DIR, "smartdca_grid_extra.csv"), index=False)
    log(f"SmartDCA extra grid: {len(smartdca_df)} rows")

    # ---------------- ADCA B1/B2 ----------------
    adca_rows = []
    adca_scores = {}
    for asset, w in weekly.items():
        rf_a = rf[asset]
        dca_res, dca_s = dca_bench_cache[asset]
        score_b1 = strat.adca_regime_score_b1(w, vix[asset], unrate[asset], tcu[asset])
        score_b2 = strat.adca_regime_score_b2(w, vix[asset])
        adca_scores[asset] = {"B1": score_b1, "B2": score_b2}
        for variant, score in [("B1", score_b1), ("B2", score_b2)]:
            decide = strat.make_adca_decider(SINGLE_DEPOSIT, score)
            res = eng.run_single_asset(w, SINGLE_DEPOSIT, rf_a, decide).to_frame()
            s = met.summarize(res, rf_a, w["Close"].iloc[-1])
            adca_rows.append({
                "asset": asset, "variant": variant,
                **{k: v for k, v in s.items() if k != "nav"},
                "dca_wealth_over_invested": dca_s["wealth_over_invested"],
                "dca_sharpe": dca_s["sharpe"], "dca_max_drawdown": dca_s["max_drawdown"],
            })
    adca_df = pd.DataFrame(adca_rows)
    adca_df.to_csv(os.path.join(REPORTS_DIR, "adca_grid_extra.csv"), index=False)
    log(f"ADCA extra grid: {len(adca_df)} rows")

    # ---------------- Deep dive + robustness (same shape as run_v2.py) ----------------
    deep_dive = {"smartdca": {}, "adca": {}}
    SMARTDCA_PRIMARY = (2, 3, True)
    for asset, w in weekly.items():
        rf_a = rf[asset]
        dca_res, dca_s = dca_bench_cache[asset]
        rho, m_max, sweep = SMARTDCA_PRIMARY
        decide = strat.make_smartdca_decider(w, SINGLE_DEPOSIT, rho, m_max, sweep)
        res = eng.run_single_asset(w, SINGLE_DEPOSIT, rf_a, decide).to_frame()
        s = met.summarize(res, rf_a, w["Close"].iloc[-1])
        slug = f"smartdca_{asset}"
        fig_value = rpt.plot_value_vs_deposits(res, dca_res, w["Close"].iloc[-1], w["Close"].iloc[-1],
                                                f"{asset} SmartDCA (rho=2,m_max=3,sweep=on) vs DCA", f"{slug}_value.png")
        fig_dd = rpt.plot_nav_drawdown(s["nav"], dca_s["nav"], w.index, f"{asset} SmartDCA drawdown vs DCA", f"{slug}_dd.png")
        fig_buy = rpt.plot_buy_amounts(w, res["buy_usd"].to_numpy(), f"{asset} SmartDCA weekly buy amount vs price", f"{slug}_buys.png")

        log(f"  SmartDCA {asset}: rolling windows...")
        strat_builder = lambda ww, rho=rho, m_max=m_max, sweep=sweep: strat.make_smartdca_decider(ww, SINGLE_DEPOSIT, rho, m_max, sweep)
        bench_builder = lambda ww: strat.make_dca_decider(SINGLE_DEPOSIT)
        rolling = {}
        for wy in (3, 5):
            rw = rob.rolling_windows_single_asset(w, rf_a, SINGLE_DEPOSIT, strat_builder, bench_builder, wy, step_weeks=N_ROLLING_STEP)
            fig_rw = rpt.plot_rolling_window_summary(rw, f"{asset} SmartDCA {wy}y rolling windows vs DCA", f"{slug}_rolling{wy}y.png")
            rolling[wy] = {"n_windows": len(rw), "win_rate_wealth": float(rw["beats_wealth"].mean()) if len(rw) else np.nan,
                            "win_rate_sharpe": float(rw["beats_sharpe"].mean()) if len(rw) else np.nan, "fig": fig_rw}

        log(f"  SmartDCA {asset}: block bootstrap...")
        bb_raw = rob.block_bootstrap_single_asset(w, rf_a, SINGLE_DEPOSIT, strat_builder, bench_builder, n_sims=N_BOOTSTRAP_SINGLE, detrend=False)
        bb_dt = rob.block_bootstrap_single_asset(w, rf_a, SINGLE_DEPOSIT, strat_builder, bench_builder, n_sims=N_BOOTSTRAP_SINGLE, detrend=True)
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

    for asset, w in weekly.items():
        rf_a = rf[asset]
        dca_res, dca_s = dca_bench_cache[asset]
        deep_dive["adca"][asset] = {}
        for variant in ADCA_VARIANTS:
            score = adca_scores[asset][variant]
            decide = strat.make_adca_decider(SINGLE_DEPOSIT, score)
            res = eng.run_single_asset(w, SINGLE_DEPOSIT, rf_a, decide).to_frame()
            s = met.summarize(res, rf_a, w["Close"].iloc[-1])
            slug = f"adca_{variant}_{asset}"
            fig_value = rpt.plot_value_vs_deposits(res, dca_res, w["Close"].iloc[-1], w["Close"].iloc[-1],
                                                    f"{asset} ADCA {variant} vs DCA", f"{slug}_value.png")
            fig_dd = rpt.plot_nav_drawdown(s["nav"], dca_s["nav"], w.index, f"{asset} ADCA {variant} drawdown vs DCA", f"{slug}_dd.png")

            log(f"  ADCA {variant} {asset}: rolling windows...")
            if variant == "B1":
                strat_builder = lambda ww: strat.make_adca_decider(SINGLE_DEPOSIT, strat.adca_regime_score_b1(
                    ww, d2.weekly_vix(raw["VIX"], ww.index), d2.weekly_fred_lagged(raw["UNRATE"], "UNRATE", ww.index),
                    d2.weekly_fred_lagged(raw["TCU"], "TCU", ww.index)))
            else:
                strat_builder = lambda ww: strat.make_adca_decider(SINGLE_DEPOSIT, strat.adca_regime_score_b2(ww, d2.weekly_vix(raw["VIX"], ww.index)))
            bench_builder = lambda ww: strat.make_dca_decider(SINGLE_DEPOSIT)
            rolling = {}
            for wy in (3, 5):
                rw = rob.rolling_windows_single_asset(w, rf_a, SINGLE_DEPOSIT, strat_builder, bench_builder, wy, step_weeks=N_ROLLING_STEP)
                fig_rw = rpt.plot_rolling_window_summary(rw, f"{asset} ADCA {variant} {wy}y rolling windows vs DCA", f"{slug}_rolling{wy}y.png")
                rolling[wy] = {"n_windows": len(rw), "win_rate_wealth": float(rw["beats_wealth"].mean()) if len(rw) else np.nan,
                                "win_rate_sharpe": float(rw["beats_sharpe"].mean()) if len(rw) else np.nan, "fig": fig_rw}

            log(f"  ADCA {variant} {asset}: block bootstrap + placebo...")
            bb_raw = rob.block_bootstrap_single_asset(w, rf_a, SINGLE_DEPOSIT, strat_builder, bench_builder, n_sims=N_BOOTSTRAP_SINGLE, detrend=False)
            bb_dt = rob.block_bootstrap_single_asset(w, rf_a, SINGLE_DEPOSIT, strat_builder, bench_builder, n_sims=N_BOOTSTRAP_SINGLE, detrend=True)
            win_rates = {
                "wealth\n(raw)": float((bb_raw["strat_wealth_over_invested"] > bb_raw["bench_wealth_over_invested"]).mean()),
                "sharpe\n(raw)": float((bb_raw["strat_sharpe"] > bb_raw["bench_sharpe"]).mean()),
                "wealth\n(detrended)": float((bb_dt["strat_wealth_over_invested"] > bb_dt["bench_wealth_over_invested"]).mean()),
                "sharpe\n(detrended)": float((bb_dt["strat_sharpe"] > bb_dt["bench_sharpe"]).mean()),
            }
            fig_bb = rpt.plot_win_rate_bar(win_rates, f"{asset} ADCA {variant} block-bootstrap win rate vs DCA", f"{slug}_bootstrap.png")

            placebo_df, pw, psh = rob.placebo_adca(w, rf_a, SINGLE_DEPOSIT, score, s["wealth_over_invested"], s["sharpe"], n_sims=N_PLACEBO)
            fig_placebo = rpt.plot_distribution(placebo_df, s["wealth_over_invested"], "wealth_over_invested",
                                                 f"{asset} ADCA {variant} placebo (shuffled regime) wealth/invested", f"{slug}_placebo.png")

            deep_dive["adca"][asset][variant] = {
                "metrics": {k: v for k, v in s.items() if k != "nav"},
                "dca_metrics": {k: v for k, v in dca_s.items() if k != "nav"},
                "figs": {"value": fig_value, "dd": fig_dd, "bootstrap": fig_bb, "placebo": fig_placebo},
                "rolling": rolling, "bootstrap_win_rates": win_rates,
                "placebo_percentile_wealth": pw, "placebo_percentile_sharpe": psh,
            }

    heatmap_figs = {}
    for asset in weekly:
        sub = smartdca_df[(smartdca_df["asset"] == asset) & (smartdca_df["sweep"] == True)]
        heatmap_figs[f"smartdca_{asset}_wealth"] = rpt.plot_grid_heatmap(
            sub, "rho", "m_max", "wealth_over_invested", f"{asset} SmartDCA (sweep=on) — wealth/invested by rho x m_max",
            f"heatmap_smartdca_{asset}_wealth.png")
        heatmap_figs[f"smartdca_{asset}_cost"] = rpt.plot_grid_heatmap(
            sub, "rho", "m_max", "avg_cost_per_unit", f"{asset} SmartDCA (sweep=on) — avg cost/unit by rho x m_max",
            f"heatmap_smartdca_{asset}_cost.png")

    def _clean(obj):
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, (np.floating, np.integer, np.bool_)):
            return obj.item()
        if isinstance(obj, (pd.Timestamp,)):
            return str(obj)
        return obj

    with open(os.path.join(REPORTS_DIR, "deep_dive_extra.json"), "w") as f:
        json.dump(_clean(deep_dive), f, indent=2, default=str)

    log("Writing extra-assets report...")
    from write_report_v2_extra import write_report_v2_extra
    write_report_v2_extra(smartdca_df, adca_df, deep_dive, heatmap_figs, weekly)

    log("Done.")


if __name__ == "__main__":
    main()
