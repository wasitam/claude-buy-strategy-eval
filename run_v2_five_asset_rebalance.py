"""How often should you rebalance a stocks/gold/silver/BTC/oil portfolio?

Extends Strategy C's portfolio engine (spec v2 section 6, unchanged code) from
3 assets to 5: S&P 500 ('^GSPC'), gold, silver, BTC, oil (CL=F). Two target-
weight schemes (C1 equal-weight, C2 inverse-volatility) are each tested
against a sweep of rebalancing triggers -- both drift bands (tight to loose)
and fixed calendar schedules (monthly to annual) -- to see how the choice of
rebalancing frequency actually trades off return, risk, turnover, and fees.

Run with:  .venv/bin/python run_v2_five_asset_rebalance.py
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
from backtest.v2 import rebalance as rb
from backtest.v2 import metrics as met
from backtest.v2 import robustness as rob
from backtest.v2 import report as rpt

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports", "v2")
os.makedirs(REPORTS_DIR, exist_ok=True)

FEE = 0.001
PORTFOLIO_DEPOSIT = 1500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]
TICKERS = {"SP500": "^GSPC", "GOLD": "GC=F", "SILVER": "SI=F", "BTC": "BTC-USD", "OIL": "CL=F"}

TRIGGER_GRID = [
    "bands_2_10", "bands_5_25", "bands_10_50", "bands_20_100",
    "calendar_1", "calendar_3", "calendar_6", "calendar_12",
    "never",
]
SCHEMES = ["C1", "C2"]
ROBUSTNESS_TRIGGERS = ["bands_5_25", "calendar_3", "calendar_12"]  # representative: tight-band, quarterly, annual
N_ROLLING_STEP = 13
N_BOOTSTRAP = 60


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    log("Fetching data...")
    raw = {}
    for name, ticker in TICKERS.items():
        raw[name] = d2.fetch_yf(name, ticker, force=False)
    raw["IRX"] = d2.fetch_yf("IRX", "^IRX", force=False)

    weekly_full = {a: d2.to_weekly_wfri(d2.clean_ohlc(raw[a])) for a in ASSETS}
    # BTC has the shortest history -- align every asset to BTC's era + 52-week warm-up (spec 6.5 pattern)
    btc_start = weekly_full["BTC"].index.min() + pd.Timedelta(weeks=52)
    idx = weekly_full["SP500"].index[weekly_full["SP500"].index >= btc_start]
    for a in ASSETS:
        idx = idx.intersection(weekly_full[a].index)
    weekly = {a: weekly_full[a].reindex(idx).ffill() for a in ASSETS}
    rf = d2.weekly_rf_rate(raw["IRX"], idx)
    for a in ASSETS:
        log(f"{a}: {len(weekly[a])} weekly candles in the shared era, {idx.min().date()} -> {idx.max().date()}")

    closes = {a: weekly[a]["Close"] for a in ASSETS}

    log("Sweeping rebalancing frequency x weighting scheme...")
    rows = []
    weights_cache = {}
    for scheme in SCHEMES:
        weights = rb.build_target_weights(scheme, closes, ASSETS, idx)
        weights_cache[scheme] = weights
        for trigger in TRIGGER_GRID:
            res = rb.run_portfolio(weekly, ASSETS, PORTFOLIO_DEPOSIT, rf, weights, trigger_mode=trigger, fee=FEE)
            s = met.summarize_portfolio(res, rf)
            n_weeks = len(idx)
            avg_weeks_between_rebalances = n_weeks / s["n_rebalances"] if s["n_rebalances"] else np.nan
            rows.append({
                "scheme": scheme, "trigger": trigger,
                **{k: v for k, v in s.items() if k != "nav"},
                "avg_weeks_between_rebalances": avg_weeks_between_rebalances,
                "fees_pct_of_invested": s["total_fees"] / s["total_invested"] if s["total_invested"] else np.nan,
            })
            log(f"  {scheme} {trigger}: wealth/inv={s['wealth_over_invested']:.2f} sharpe={s['sharpe']:.2f} "
                f"maxdd={s['max_drawdown']:.1%} n_rebal={s['n_rebalances']} fees=${s['total_fees']:.0f}")
    freq_df = pd.DataFrame(rows)
    freq_df.to_csv(os.path.join(REPORTS_DIR, "five_asset_rebalance_frequency.csv"), index=False)

    # ---------------- charts: metric vs frequency ----------------
    log("Charting metric-vs-frequency curves...")
    freq_figs = {}
    for scheme in SCHEMES:
        sub = freq_df[freq_df["scheme"] == scheme].copy()
        sub = sub[sub["trigger"] != "never"]
        order = ["bands_2_10", "bands_5_25", "bands_10_50", "bands_20_100", "calendar_1", "calendar_3", "calendar_6", "calendar_12"]
        sub["trigger"] = pd.Categorical(sub["trigger"], categories=order, ordered=True)
        sub = sub.sort_values("trigger")
        freq_figs[f"{scheme}_metrics"] = _plot_frequency_tradeoff(sub, scheme)

    # ---------------- weights chart for one scheme ----------------
    res_c2_band = rb.run_portfolio(weekly, ASSETS, PORTFOLIO_DEPOSIT, rf, weights_cache["C2"], trigger_mode="bands_5_25", fee=FEE)
    fig_weights = rpt.plot_portfolio_weights(res_c2_band, ASSETS, "5-asset C2 (inverse-vol) portfolio weights, 5/25 bands", "five_asset_C2_bands525_weights.png")

    # ---------------- robustness on representative frequencies ----------------
    log("Robustness: rolling windows + bootstrap on representative frequencies...")
    robustness_results = {}
    for scheme in SCHEMES:
        robustness_results[scheme] = {}
        weights = weights_cache[scheme]
        for trigger in ROBUSTNESS_TRIGGERS:
            log(f"  {scheme} {trigger}: rolling windows...")
            rolling = {}
            for wy in (2, 3):
                rw = rob.rolling_windows_portfolio(weekly, ASSETS, rf, PORTFOLIO_DEPOSIT, scheme, trigger, wy, step_weeks=N_ROLLING_STEP)
                fig_rw = rpt.plot_rolling_window_summary(
                    rw, f"5-asset {scheme} {trigger} — {wy}y rolling windows vs fixed-weight",
                    f"five_asset_{scheme}_{trigger}_rolling{wy}y.png")
                rolling[wy] = {"n_windows": len(rw), "win_rate_wealth": float(rw["beats_wealth"].mean()) if len(rw) else np.nan,
                                "win_rate_sharpe": float(rw["beats_sharpe"].mean()) if len(rw) else np.nan, "fig": fig_rw}
            log(f"  {scheme} {trigger}: block bootstrap...")
            bb = rob.block_bootstrap_portfolio(weekly, ASSETS, rf, PORTFOLIO_DEPOSIT, scheme, trigger, n_sims=N_BOOTSTRAP, detrend=False)
            bb_dt = rob.block_bootstrap_portfolio(weekly, ASSETS, rf, PORTFOLIO_DEPOSIT, scheme, trigger, n_sims=N_BOOTSTRAP, detrend=True)
            win_rates = {
                "wealth\n(raw)": float((bb["strat_wealth_over_invested"] > bb["bench_wealth_over_invested"]).mean()),
                "sharpe\n(raw)": float((bb["strat_sharpe"] > bb["bench_sharpe"]).mean()),
                "wealth\n(detrended)": float((bb_dt["strat_wealth_over_invested"] > bb_dt["bench_wealth_over_invested"]).mean()),
                "sharpe\n(detrended)": float((bb_dt["strat_sharpe"] > bb_dt["bench_sharpe"]).mean()),
            }
            fig_bb = rpt.plot_win_rate_bar(win_rates, f"5-asset {scheme} {trigger} bootstrap win rate vs fixed-weight",
                                            f"five_asset_{scheme}_{trigger}_bootstrap.png")
            row = freq_df[(freq_df.scheme == scheme) & (freq_df.trigger == trigger)].iloc[0]
            robustness_results[scheme][trigger] = {
                "headline": {k: (float(row[k]) if isinstance(row[k], (int, float, np.floating, np.integer)) else row[k])
                             for k in ["wealth_over_invested", "sharpe", "max_drawdown", "n_rebalances", "total_fees", "fees_pct_of_invested"]},
                "rolling": rolling, "bootstrap_win_rates": win_rates, "fig_bootstrap": fig_bb,
            }

    def _clean(obj):
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, (np.floating, np.integer, np.bool_)):
            return obj.item()
        if isinstance(obj, pd.Timestamp):
            return str(obj)
        return obj

    with open(os.path.join(REPORTS_DIR, "five_asset_robustness.json"), "w") as f:
        json.dump(_clean(robustness_results), f, indent=2, default=str)

    log("Writing report...")
    from write_report_v2_five_asset import write_report_five_asset
    write_report_five_asset(freq_df, freq_figs, fig_weights, robustness_results, weekly, ASSETS)

    log("Done.")


def _plot_frequency_tradeoff(sub: pd.DataFrame, scheme: str) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    x = range(len(sub))
    labels = sub["trigger"].tolist()

    axes[0].plot(x, sub["wealth_over_invested"], marker="o", color="#2e8b57")
    axes[0].set_title(f"{scheme}: wealth/invested")
    axes[1].plot(x, sub["sharpe"], marker="o", color="#3b6fa0")
    axes[1].set_title(f"{scheme}: Sharpe")
    axes[2].plot(x, sub["n_rebalances"], marker="o", color="#b03a2e", label="# rebalances")
    ax2b = axes[2].twinx()
    ax2b.plot(x, sub["fees_pct_of_invested"] * 100, marker="s", color="#7f5aa2", label="fees % of invested")
    axes[2].set_title(f"{scheme}: turnover & fees")
    axes[2].set_ylabel("# rebalances", color="#b03a2e")
    ax2b.set_ylabel("fees (% of invested)", color="#7f5aa2")

    for ax in axes:
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax.grid(alpha=0.25)

    fig.tight_layout()
    path = os.path.join(REPORTS_DIR, "figures", f"five_asset_{scheme}_frequency_tradeoff.png")
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return os.path.relpath(path, REPORTS_DIR)


if __name__ == "__main__":
    main()
