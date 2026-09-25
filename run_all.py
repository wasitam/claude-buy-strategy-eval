"""End-to-end pipeline: fetch data -> weekly candles -> generic percentile
signal engine -> backtest engine -> benchmarks -> metrics grid -> robustness
tests -> charts -> markdown report.

Run with:  .venv/bin/python run_all.py
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from backtest import data as data_mod
from backtest.resample import to_weekly, weekly_risk_free_rate
from backtest import indicators as ind
from backtest.engine import run_backtest
from backtest import benchmarks as bm
from backtest import metrics as met
from backtest import robustness as rob
from backtest import report as rpt

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

P_GRID = [1, 2.5, 5, 10, 15]
DEFAULT_P = 5
FEE = 0.001
BUY_AMOUNT = 500.0
SELL_FRAC = 0.30

SIGNALS = {
    "Signal A (shock)": ind.signal_a_shock,
    "Signal B (trend-stretch)": ind.signal_b_trend_stretch,
}

ASSET_TICKER_NAMES = {"BTC": "BTC", "Gold": "GOLD", "Silver": "SILVER"}
ROLLING_WINDOW_YEARS = {"BTC": [2], "Gold": [3, 5], "Silver": [3, 5]}

# Robustness sim counts -- kept moderate so the full 6-combo suite finishes in
# a reasonable time; see reports/report.md for the scoping note.
N_MC_SIMS = 300
N_BOOTSTRAP_SIMS = 150


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def avg_invested_fraction(result: pd.DataFrame) -> float:
    weight = result["market_value"] / result["total_value"].replace(0, np.nan)
    return float(weight.fillna(0.0).mean())


def main():
    log("Fetching data (cached if already present)...")
    raw = data_mod.fetch_all(force=False)

    weekly = {}
    for name in ["BTC", "GOLD", "SILVER"]:
        weekly[name] = to_weekly(raw[name])
        log(f"{name}: {len(weekly[name])} weekly candles, "
            f"{weekly[name].index.min().date()} -> {weekly[name].index.max().date()}")

    weekly_rf_full = weekly_risk_free_rate(raw["IRX"])

    assets = {"BTC": weekly["BTC"], "Gold": weekly["GOLD"], "Silver": weekly["SILVER"]}
    weekly_rf = {name: weekly_rf_full.reindex(df.index).ffill().fillna(0.0) for name, df in assets.items()}

    # ---------------------------------------------------------------
    # 1) Headline metrics grid: every (asset x signal x p) combination
    # ---------------------------------------------------------------
    log("Running full grid (asset x signal x p)...")
    grid_rows = []
    grid_results_cache = {}  # (asset, signal_name, p) -> (result_df, buy, sell)
    for asset, wdf in assets.items():
        rf = weekly_rf[asset]
        for signal_name, signal_fn in SIGNALS.items():
            indicator = signal_fn(wdf)
            for p in P_GRID:
                buy, sell = ind.percentile_signal_to_trades(indicator, p)
                result = run_backtest(wdf, buy, sell, rf, fee=FEE, buy_amount=BUY_AMOUNT, sell_frac=SELL_FRAC)
                s = met.summarize(result, wdf, rf, buy_amount=BUY_AMOUNT)

                total_invested = s["total_invested"]
                row = {"asset": asset, "signal": signal_name, "p": p, **s}

                if total_invested > 0:
                    d = bm.dca(wdf, total_invested, rf)
                    bh = bm.buy_and_hold(wdf, total_invested)
                    bo = bm.buy_only(wdf, buy, rf, fee=FEE, buy_amount=BUY_AMOUNT)
                    tw = avg_invested_fraction(result)
                    rb = bm.rebalance_band(wdf, total_invested, target_weight=max(tw, 0.01), weekly_rf=rf)

                    row["dca_wealth_over_invested"] = float(d["total_value"].iloc[-1] / total_invested)
                    row["buy_and_hold_wealth_over_invested"] = float(bh["total_value"].iloc[-1] / total_invested)
                    bo_invested = bo["invested"].iloc[-1]
                    row["buy_only_wealth_over_invested"] = (
                        float(bo["total_value"].iloc[-1] / bo_invested) if bo_invested > 0 else float("nan")
                    )
                    row["rebalance_band_wealth_over_invested"] = float(rb["total_value"].iloc[-1] / total_invested)
                    row["avg_invested_fraction"] = tw
                else:
                    for k in ["dca_wealth_over_invested", "buy_and_hold_wealth_over_invested",
                              "buy_only_wealth_over_invested", "rebalance_band_wealth_over_invested",
                              "avg_invested_fraction"]:
                        row[k] = float("nan")

                grid_rows.append(row)
                grid_results_cache[(asset, signal_name, p)] = (result, buy, sell)

    grid_df = pd.DataFrame(grid_rows)
    grid_csv = os.path.join(REPORTS_DIR, "grid_metrics.csv")
    grid_df.to_csv(grid_csv, index=False)
    log(f"Grid complete: {len(grid_df)} rows -> {grid_csv}")

    # ---------------------------------------------------------------
    # 2) Deep dive at DEFAULT_P for every asset x signal: charts,
    #    robustness tests, signal-quality forward returns.
    # ---------------------------------------------------------------
    deep_dive = {}
    for asset, wdf in assets.items():
        rf = weekly_rf[asset]
        for signal_name, signal_fn in SIGNALS.items():
            key = f"{asset}__{signal_name}"
            log(f"Deep dive: {asset} / {signal_name} (p={DEFAULT_P})")
            result, buy, sell = grid_results_cache[(asset, signal_name, DEFAULT_P)]
            s = met.summarize(result, wdf, rf, buy_amount=BUY_AMOUNT)
            total_invested = s["total_invested"]
            if total_invested <= 0:
                log(f"  skipping {key}: zero signals at p={DEFAULT_P}")
                continue
            d = bm.dca(wdf, total_invested, rf)

            slug = key.replace(" ", "_").replace("(", "").replace(")", "")
            fig_price = rpt.plot_price_with_signals(wdf, buy, sell, asset, signal_name, DEFAULT_P, f"{slug}_price.png")
            fig_value = rpt.plot_value_vs_invested(result, d, asset, signal_name, DEFAULT_P, f"{slug}_value.png")
            fig_dd = rpt.plot_drawdown(result, d, asset, signal_name, DEFAULT_P, f"{slug}_drawdown.png")

            # --- Robustness test 1: random-timing Monte Carlo ---
            log(f"  random-timing MC ({N_MC_SIMS} sims)...")
            mc_df = rob.random_timing_mc(
                wdf, s["n_buys"], s["n_sells"], rf, n_sims=N_MC_SIMS, fee=FEE,
                buy_amount=BUY_AMOUNT, sell_frac=SELL_FRAC,
            )
            mc_pctile_wealth = rob.percentile_of_real(mc_df["wealth_over_invested"], s["wealth_over_invested"])
            mc_pctile_sharpe = rob.percentile_of_real(mc_df["sharpe"], s["sharpe"])
            mc_pctile_dd = rob.percentile_of_real(-mc_df["max_drawdown"], -s["max_drawdown"])
            fig_mc = rpt.plot_mc_distribution(
                mc_df, s["wealth_over_invested"], "wealth_over_invested",
                f"{asset} / {signal_name} (p={DEFAULT_P}) — random-timing MC: ending wealth/invested",
                f"{slug}_mc.png",
            )

            # --- Robustness test 2: block bootstrap (raw + detrended) ---
            log(f"  block bootstrap ({N_BOOTSTRAP_SIMS} sims x2)...")
            bb_raw = rob.block_bootstrap_test(wdf, signal_fn, DEFAULT_P, rf, n_sims=N_BOOTSTRAP_SIMS,
                                               fee=FEE, buy_amount=BUY_AMOUNT, sell_frac=SELL_FRAC, detrend=False)
            bb_dt = rob.block_bootstrap_test(wdf, signal_fn, DEFAULT_P, rf, n_sims=N_BOOTSTRAP_SIMS,
                                              fee=FEE, buy_amount=BUY_AMOUNT, sell_frac=SELL_FRAC, detrend=True)
            win_rates = {
                "return\n(raw)": float((bb_raw["strat_wealth_over_invested"] > bb_raw["dca_wealth_over_invested"]).mean()),
                "drawdown\n(raw)": float((bb_raw["strat_max_dd"] > bb_raw["dca_max_dd"]).mean()),
                "sharpe\n(raw)": float((bb_raw["strat_sharpe"] > bb_raw["dca_sharpe"]).mean()),
                "return\n(detrended)": float((bb_dt["strat_wealth_over_invested"] > bb_dt["dca_wealth_over_invested"]).mean()),
                "drawdown\n(detrended)": float((bb_dt["strat_max_dd"] > bb_dt["dca_max_dd"]).mean()),
                "sharpe\n(detrended)": float((bb_dt["strat_sharpe"] > bb_dt["dca_sharpe"]).mean()),
            }
            fig_bb = rpt.plot_bootstrap_winrate(
                win_rates, f"{asset} / {signal_name} (p={DEFAULT_P}) — block-bootstrap win rate vs DCA",
                f"{slug}_bootstrap.png",
            )

            # --- Robustness test 3: rolling windows ---
            rolling_results = {}
            for wy in ROLLING_WINDOW_YEARS[asset]:
                log(f"  rolling {wy}y windows...")
                rw_df = rob.rolling_windows_test(wdf, signal_fn, DEFAULT_P, rf, window_years=wy,
                                                  fee=FEE, buy_amount=BUY_AMOUNT, sell_frac=SELL_FRAC)
                scored = rw_df[~rw_df["low_signal_count"]]
                win_rate_return = float(scored["strat_beats_dca_return"].mean()) if len(scored) else float("nan")
                win_rate_dd = float(scored["strat_beats_dca_dd"].mean()) if len(scored) else float("nan")
                win_rate_sharpe = float(scored["strat_beats_dca_sharpe"].mean()) if len(scored) else float("nan")
                fig_rw = rpt.plot_rolling_window_summary(
                    rw_df, f"{asset} / {signal_name} (p={DEFAULT_P}) — {wy}y rolling windows",
                    f"{slug}_rolling{wy}y.png",
                )
                rolling_results[wy] = {
                    "n_windows": len(rw_df), "n_scored": len(scored),
                    "win_rate_return": win_rate_return, "win_rate_dd": win_rate_dd,
                    "win_rate_sharpe": win_rate_sharpe, "fig": fig_rw,
                    "last_window": rw_df.iloc[-1].to_dict() if len(rw_df) else None,
                }

            fwd_returns = {
                "buy_signal": met.signal_forward_returns(wdf, buy),
                "sell_signal": met.signal_forward_returns(wdf, sell),
            }

            deep_dive[key] = {
                "asset": asset, "signal": signal_name, "metrics": s,
                "figs": {"price": fig_price, "value": fig_value, "dd": fig_dd, "mc": fig_mc, "bootstrap": fig_bb},
                "mc_percentiles": {"wealth": mc_pctile_wealth, "sharpe": mc_pctile_sharpe, "drawdown": mc_pctile_dd},
                "bootstrap_win_rates": win_rates,
                "rolling": rolling_results,
                "fwd_returns": fwd_returns,
                "dca_wealth_over_invested": float(d["total_value"].iloc[-1] / total_invested),
            }

    # ---------------------------------------------------------------
    # 3) Grid heatmaps
    # ---------------------------------------------------------------
    log("Generating grid heatmaps...")
    heatmap_figs = {}
    for asset in assets:
        sub = grid_df[grid_df["asset"] == asset]
        heatmap_figs[f"{asset}_wealth"] = rpt.plot_grid_heatmap(
            sub, "wealth_over_invested", f"{asset} — ending wealth / invested (signal x p grid)",
            f"heatmap_{asset}_wealth.png",
        )
        heatmap_figs[f"{asset}_sharpe"] = rpt.plot_grid_heatmap(
            sub, "sharpe", f"{asset} — Sharpe ratio (signal x p grid)", f"heatmap_{asset}_sharpe.png",
        )

    # Save deep-dive results as JSON (minus DataFrames) for reproducibility / debugging.
    def _clean(obj):
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items() if k != "fig" or True}
        if isinstance(obj, (np.floating, np.integer)):
            return obj.item()
        if isinstance(obj, pd.Timestamp):
            return str(obj)
        return obj

    with open(os.path.join(REPORTS_DIR, "deep_dive.json"), "w") as f:
        json.dump(_clean(deep_dive), f, indent=2, default=str)

    log("Writing markdown report...")
    from write_report import write_report
    write_report(grid_df, deep_dive, heatmap_figs, assets, ROLLING_WINDOW_YEARS)

    log("Done.")


if __name__ == "__main__":
    main()
