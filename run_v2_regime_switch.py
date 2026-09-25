"""Strategy D: rate-regime switch (spec v2.1 section 15). Tests whether
switching between SmartDCA (in monetary tightening) and plain DCA (otherwise)
beats either strategy alone, across 8 rate signals plus a price-only Control,
on the "agreed" 5-asset set: gold, silver, BTC, oil, S&P 500.

Scoping vs the spec, documented in the report:
  - R4 (dot plot) uses REAL ALFRED vintages (2015-12-16 onward -- that's
    what ALFRED's own vintage list for FEDTARMD actually contains, not
    Jan-2012 as the spec's data table assumed).
  - Placebo sims reduced from 1,000 to 300 (same scoping as the rest of v2).
  - Full placebo suite runs on gold/silver (the spec's primary hypothesis
    assets) across all 8 signals + Control; BTC/oil/S&P 500 get placebo on
    Combo + Control only, to keep runtime sane.
  - Per-cycle table computed for Combo and R2c (bear-flattening) on gold/silver.

Run with:  .venv/bin/python run_v2_regime_switch.py
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
from backtest.v2 import strategy_d as sd
from backtest.v2 import regimes as reg
from backtest.v2 import metrics as met
from backtest.v2 import robustness as rob
from backtest.v2 import report as rpt

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports", "v2")
os.makedirs(REPORTS_DIR, exist_ok=True)

FEE = 0.001
SINGLE_DEPOSIT = 500.0
ASSETS = {"GOLD": "GC=F", "SILVER": "SI=F", "BTC": "BTC-USD", "OIL": "CL=F", "SP500": "^GSPC"}
PRIMARY_ASSETS = ["GOLD", "SILVER"]  # spec's real hypothesis test
PRIMARY_START, PRIMARY_END = "2001-01-01", "2023-12-31"
SECONDARY_START = "2024-01-01"

RATE_SIGNALS = ["R1", "R2a", "R2b", "R2b-inv", "R2c", "R3", "R4", "Combo"]
N_SIGNALS_FOR_GUARD = 8  # per spec 15.7 multiple-testing guard
N_PLACEBO = 300
N_PLACEBO_LIMITED_SIGNALS = ["Combo", "Control"]  # for non-primary assets


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run_strategy_d(weekly, rf, regime_bool, deposit=SINGLE_DEPOSIT):
    decide = sd.make_strategy_d_decider(weekly, deposit, regime_bool.to_numpy() if hasattr(regime_bool, "to_numpy") else regime_bool)
    res = eng.run_single_asset(weekly, deposit, rf, decide).to_frame()
    return res, met.summarize(res, rf, weekly["Close"].iloc[-1])


def main():
    log("Fetching data...")
    fred_raw = {}
    for sid in ["DFEDTAR", "DFEDTARU", "DFEDTARL", "DGS2", "DGS10", "T10Y2Y", "DFII10"]:
        fred_raw[sid] = d2.fetch_fred(sid, force=False)
    raw = {}
    for name, ticker in ASSETS.items():
        raw[name] = d2.fetch_yf(name, ticker, force=False)
    raw["IRX"] = d2.fetch_yf("IRX", "^IRX", force=False)

    weekly = {a: d2.to_weekly_wfri(d2.clean_ohlc(raw[a])) for a in ASSETS}
    rf = {a: d2.weekly_rf_rate(raw["IRX"], weekly[a].index) for a in ASSETS}
    for a in ASSETS:
        log(f"{a}: {len(weekly[a])} weekly candles, {weekly[a].index.min().date()} -> {weekly[a].index.max().date()}")

    target_mid_daily = reg.fetch_fed_target_midpoint()

    log("Building regime signals per asset (this includes the R4 dot-plot loop, slow-ish)...")
    signals = {}
    for a in ASSETS:
        t0 = time.time()
        s = reg.build_all_signals(weekly[a].index, fred_raw, confirm_weeks=2)
        s["Control"] = reg.control_signal(weekly[a]["Close"])
        signals[a] = s
        log(f"  {a}: signals built in {time.time()-t0:.1f}s")

    # ---------------- Headline comparison table: all signals x all assets ----------------
    log("Running headline comparison (full history per asset)...")
    headline_rows = []
    strategy_d_results = {}  # (asset, signal) -> (res, s)
    for a in ASSETS:
        w = weekly[a]
        rf_a = rf[a]
        dca_decide = strat.make_dca_decider(SINGLE_DEPOSIT)
        dca_res = eng.run_single_asset(w, SINGLE_DEPOSIT, rf_a, dca_decide).to_frame()
        dca_s = met.summarize(dca_res, rf_a, w["Close"].iloc[-1])

        smart_decide = strat.make_smartdca_decider(w, SINGLE_DEPOSIT, 2, 3, True)
        smart_res = eng.run_single_asset(w, SINGLE_DEPOSIT, rf_a, smart_decide).to_frame()
        smart_s = met.summarize(smart_res, rf_a, w["Close"].iloc[-1])

        for sig_name in RATE_SIGNALS + ["Control"]:
            regime = signals[a][sig_name]
            res, s = run_strategy_d(w, rf_a, regime)
            strategy_d_results[(a, sig_name)] = (res, s)
            headline_rows.append({
                "asset": a, "signal": sig_name,
                **{k: v for k, v in s.items() if k != "nav"},
                "dca_wealth_over_invested": dca_s["wealth_over_invested"], "dca_sharpe": dca_s["sharpe"],
                "smart_wealth_over_invested": smart_s["wealth_over_invested"], "smart_sharpe": smart_s["sharpe"],
                "tight_share": float(regime.mean()), "n_switches": sd.n_switches(regime.to_numpy()),
            })
        log(f"  {a}: done")
    headline_df = pd.DataFrame(headline_rows)
    headline_df.to_csv(os.path.join(REPORTS_DIR, "regime_switch_headline.csv"), index=False)

    # ---------------- Primary hypothesis test: gold/silver, 2001-2023 vs 2024+ ----------------
    log("Primary hypothesis test: gold/silver primary (2001-2023) vs secondary (2024+) samples...")
    period_rows = []
    for a in PRIMARY_ASSETS:
        w_full = weekly[a]
        for period_name, start, end in [("Primary 2001-2023", PRIMARY_START, PRIMARY_END),
                                         ("Secondary 2024+ (hypothesis-forming)", SECONDARY_START, None)]:
            w = w_full.loc[start:end] if end else w_full.loc[start:]
            if len(w) < 60:
                continue
            rf_p = rf[a].reindex(w.index).ffill().fillna(0.0)
            dca_res = eng.run_single_asset(w, SINGLE_DEPOSIT, rf_p, strat.make_dca_decider(SINGLE_DEPOSIT)).to_frame()
            dca_s = met.summarize(dca_res, rf_p, w["Close"].iloc[-1])
            smart_res = eng.run_single_asset(w, SINGLE_DEPOSIT, rf_p, strat.make_smartdca_decider(w, SINGLE_DEPOSIT, 2, 3, True)).to_frame()
            smart_s = met.summarize(smart_res, rf_p, w["Close"].iloc[-1])
            for sig_name in RATE_SIGNALS + ["Control"]:
                regime = signals[a][sig_name].reindex(w.index).fillna(False)
                res, s = run_strategy_d(w, rf_p, regime)
                period_rows.append({
                    "asset": a, "period": period_name, "signal": sig_name,
                    **{k: v for k, v in s.items() if k != "nav"},
                    "dca_wealth_over_invested": dca_s["wealth_over_invested"], "dca_sharpe": dca_s["sharpe"],
                    "smart_wealth_over_invested": smart_s["wealth_over_invested"], "smart_sharpe": smart_s["sharpe"],
                })
    period_df = pd.DataFrame(period_rows)
    period_df.to_csv(os.path.join(REPORTS_DIR, "regime_switch_periods.csv"), index=False)

    # ---------------- Fed cycles + per-cycle table (gold/silver, Combo & R2c) ----------------
    log("Detecting Fed cycles + per-cycle table...")
    idx_ref = weekly["GOLD"].index
    daily_idx = pd.date_range(idx_ref.min() - pd.Timedelta(weeks=30), idx_ref.max(), freq="D")
    target_mid_w_ref = target_mid_daily.reindex(daily_idx).ffill().reindex(idx_ref, method="ffill")
    cycles = reg.detect_fed_cycles(target_mid_w_ref)
    cycles_out = cycles.copy()
    cycles_out["start"] = cycles_out["start"].astype(str)
    cycles_out["end"] = cycles_out["end"].astype(str)
    cycles_out.to_csv(os.path.join(REPORTS_DIR, "fed_cycles.csv"), index=False)

    percycle_rows = []
    for a in PRIMARY_ASSETS:
        w_full = weekly[a]
        rf_full = rf[a]
        for sig_name in ["Combo", "R2c"]:
            regime_full = signals[a][sig_name]
            for _, cyc in cycles.iterrows():
                w = w_full.loc[cyc["start"]:cyc["end"]]
                if len(w) < 20:
                    continue
                rf_c = rf_full.reindex(w.index).ffill().fillna(0.0)
                regime_c = regime_full.reindex(w.index).fillna(False)
                d_res, d_s = run_strategy_d(w, rf_c, regime_c)
                dca_res = eng.run_single_asset(w, SINGLE_DEPOSIT, rf_c, strat.make_dca_decider(SINGLE_DEPOSIT)).to_frame()
                dca_s = met.summarize(dca_res, rf_c, w["Close"].iloc[-1])
                percycle_rows.append({
                    "asset": a, "signal": sig_name, "cycle_type": cyc["type"],
                    "cycle_start": str(cyc["start"])[:10], "cycle_end": str(cyc["end"])[:10],
                    "n_weeks": len(w),
                    "d_wealth_over_invested": d_s["wealth_over_invested"], "dca_wealth_over_invested": dca_s["wealth_over_invested"],
                    "d_sharpe": d_s["sharpe"], "dca_sharpe": dca_s["sharpe"],
                    "d_beats_dca_wealth": d_s["wealth_over_invested"] > dca_s["wealth_over_invested"],
                })
    percycle_df = pd.DataFrame(percycle_rows)
    percycle_df.to_csv(os.path.join(REPORTS_DIR, "regime_switch_percycle.csv"), index=False)

    # ---------------- Placebo tests ----------------
    log("Placebo tests (this is the slow part)...")
    placebo_results = {}
    for a in ASSETS:
        placebo_results[a] = {}
        sig_list = (RATE_SIGNALS + ["Control"]) if a in PRIMARY_ASSETS else N_PLACEBO_LIMITED_SIGNALS
        w = weekly[a]
        rf_a = rf[a]
        for sig_name in sig_list:
            regime = signals[a][sig_name]
            _, s = strategy_d_results[(a, sig_name)]
            log(f"  placebo {a} {sig_name}...")
            df, pw, psh = rob.placebo_strategy_d(w, rf_a, SINGLE_DEPOSIT, regime.to_numpy(),
                                                  s["wealth_over_invested"], s["sharpe"], n_sims=N_PLACEBO)
            placebo_results[a][sig_name] = {"percentile_wealth": pw, "percentile_sharpe": psh}

    with open(os.path.join(REPORTS_DIR, "regime_switch_placebo.json"), "w") as f:
        json.dump(placebo_results, f, indent=2)

    # ---------------- Diagnostics: pairwise agreement + current readings ----------------
    log("Diagnostics...")
    diag = {}
    for a in ASSETS:
        sig_df = pd.DataFrame({k: v for k, v in signals[a].items() if k != "R4_valid_from"})
        agreement = {}
        cols = list(sig_df.columns)
        for i, c1 in enumerate(cols):
            for c2 in cols[i + 1:]:
                agreement[f"{c1} vs {c2}"] = float((sig_df[c1] == sig_df[c2]).mean())
        current = {c: bool(sig_df[c].iloc[-1]) for c in cols}
        diag[a] = {"pairwise_agreement": agreement, "current_reading": current}
    with open(os.path.join(REPORTS_DIR, "regime_switch_diagnostics.json"), "w") as f:
        json.dump(diag, f, indent=2)

    # ---------------- Charts ----------------
    log("Charting...")
    figs = {}
    for a in PRIMARY_ASSETS:
        w = weekly[a]
        figs[f"{a}_timeline"] = _plot_regime_timeline(w, signals[a]["Combo"], signals[a]["R2c"], cycles, a)

    figs["yield_curve"] = _plot_yield_curve(fred_raw, signals["GOLD"]["R2c"], weekly["GOLD"].index)

    log("Writing report...")
    from write_report_v2_regime_switch import write_report_regime_switch
    write_report_regime_switch(headline_df, period_df, cycles_out, percycle_df, placebo_results, diag, figs, weekly)

    log("Done.")


def _plot_regime_timeline(weekly, combo_signal, r2c_signal, cycles, asset_name):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(13, 4.5))
    ax.plot(weekly.index, weekly["Close"], color="#333333", linewidth=0.9)
    ax.set_yscale("log")
    ymin, ymax = ax.get_ylim()
    ax.fill_between(weekly.index, ymin, ymax, where=combo_signal.reindex(weekly.index).fillna(False).to_numpy(),
                     color="#b03a2e", alpha=0.15, step="mid", label="Combo TIGHT")
    ax.fill_between(weekly.index, ymin, ymax, where=r2c_signal.reindex(weekly.index).fillna(False).to_numpy(),
                     color="#3b6fa0", alpha=0.12, step="mid", label="R2c (bear-flattening) TIGHT")
    for _, cyc in cycles.iterrows():
        color = {"hike": "#b03a2e", "ease": "#2e8b57", "hold": "#888888"}[cyc["type"]]
        ax.axvline(pd.Timestamp(cyc["start"]), color=color, linewidth=0.6, alpha=0.5)
    ax.set_ylim(ymin, ymax)
    ax.set_title(f"{asset_name}: price with Combo / R2c TIGHT periods shaded, Fed cycle starts marked")
    ax.legend(loc="upper left", fontsize=8)
    path = os.path.join(REPORTS_DIR, "figures", f"regime_timeline_{asset_name}.png")
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return os.path.relpath(path, REPORTS_DIR)


def _plot_yield_curve(fred_raw, r2c_signal, index):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    daily_idx = pd.date_range(index.min() - pd.Timedelta(weeks=30), index.max(), freq="D")
    dgs2 = fred_raw["DGS2"]["DGS2"].reindex(daily_idx).ffill().reindex(index, method="ffill")
    dgs10 = fred_raw["DGS10"]["DGS10"].reindex(daily_idx).ffill().reindex(index, method="ffill")
    slope = fred_raw["T10Y2Y"]["T10Y2Y"].reindex(daily_idx).ffill().reindex(index, method="ffill")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 6), sharex=True)
    ax1.plot(index, dgs2, label="2-year", color="#3b6fa0")
    ax1.plot(index, dgs10, label="10-year", color="#b03a2e")
    ax1.legend(loc="upper left", fontsize=8)
    ax1.set_title("2y / 10y Treasury yields")
    ax2.plot(index, slope, color="#333333", linewidth=1.0)
    ax2.axhline(0, color="black", linewidth=0.6)
    ymin, ymax = ax2.get_ylim()
    ax2.fill_between(index, ymin, ymax, where=r2c_signal.reindex(index).fillna(False).to_numpy(),
                      color="#b03a2e", alpha=0.15, step="mid", label="R2c bear-flattening")
    ax2.set_ylim(ymin, ymax)
    ax2.set_title("10y-2y slope (T10Y2Y), bear-flattening (R2c) shaded")
    ax2.legend(loc="upper left", fontsize=8)
    path = os.path.join(REPORTS_DIR, "figures", "yield_curve.png")
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return os.path.relpath(path, REPORTS_DIR)


if __name__ == "__main__":
    main()
