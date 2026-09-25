"""Assemble reports/report.md from the grid results + deep-dive robustness results."""
from __future__ import annotations

import os
import pandas as pd

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


def fmt_pct(x, dp=1):
    try:
        return f"{x*100:.{dp}f}%"
    except Exception:
        return "n/a"


def fmt_num(x, dp=3):
    try:
        return f"{x:.{dp}f}"
    except Exception:
        return "n/a"


def grid_table_md(grid_df: pd.DataFrame) -> str:
    cols = [
        "asset", "signal", "p", "n_buys", "n_sells", "wealth_over_invested",
        "dca_wealth_over_invested", "buy_and_hold_wealth_over_invested",
        "buy_only_wealth_over_invested", "rebalance_band_wealth_over_invested",
        "xirr", "max_drawdown", "sharpe", "sortino", "calmar", "avg_cost_basis",
    ]
    df = grid_df[cols].copy()
    header = ("| Asset | Signal | p% | #Buy | #Sell | Wealth/Inv | DCA | Buy&Hold | Buy-only | Rebal-band "
               "| XIRR | MaxDD | Sharpe | Sortino | Calmar | Avg cost |\n")
    header += "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    lines = [header]
    for _, r in df.iterrows():
        lines.append(
            f"| {r['asset']} | {r['signal'].replace('Signal ', '')} | {r['p']} | {int(r['n_buys'])} | {int(r['n_sells'])} "
            f"| {fmt_num(r['wealth_over_invested'],2)} | {fmt_num(r['dca_wealth_over_invested'],2)} "
            f"| {fmt_num(r['buy_and_hold_wealth_over_invested'],2)} | {fmt_num(r['buy_only_wealth_over_invested'],2)} "
            f"| {fmt_num(r['rebalance_band_wealth_over_invested'],2)} "
            f"| {fmt_pct(r['xirr']) if r['xirr'] is not None else 'n/a'} | {fmt_pct(r['max_drawdown'])} "
            f"| {fmt_num(r['sharpe'],2)} | {fmt_num(r['sortino'],2)} | {fmt_num(r['calmar'],2)} "
            f"| {fmt_num(r['avg_cost_basis'],2)} |\n"
        )
    return "".join(lines)


def fwd_returns_table_md(fwd_returns: dict, label: str) -> str:
    lines = [f"**{label}**\n\n", "| Horizon | Avg return after signal | Unconditional avg return | Edge | n obs |\n",
             "|---|---|---|---|---|\n"]
    for horizon, v in fwd_returns.items():
        edge = v["signal_avg"] - v["unconditional_avg"] if v["signal_avg"] == v["signal_avg"] else float("nan")
        lines.append(
            f"| {horizon} | {fmt_pct(v['signal_avg'])} | {fmt_pct(v['unconditional_avg'])} "
            f"| {fmt_pct(edge)} | {v['n_signal_obs']} |\n"
        )
    return "".join(lines)


def write_report(grid_df, deep_dive, heatmap_figs, assets, rolling_window_years):
    md = []
    md.append("# BTC / Gold / Silver Rule-Based Accumulation — Backtest Results\n\n")
    md.append(
        "Generated from live Yahoo Finance data via `yfinance`. Full spec: "
        "[`btc-gold-silver-backtest-spec.md`](../btc-gold-silver-backtest-spec.md). "
        "Reusable pipeline: `run_all.py` + `src/backtest/`.\n\n"
    )
    md.append("## Data coverage\n\n")
    for name, df in assets.items():
        md.append(f"- **{name}**: {len(df)} weekly candles, {df.index.min().date()} → {df.index.max().date()}\n")
    md.append("\n")

    md.append("## Scoping notes (read this first)\n\n")
    md.append(
        "- The **headline metrics grid** below covers the full spec'd grid: "
        "3 assets × 2 signals × p ∈ {1, 2.5, 5, 10, 15} = 30 combinations, run in full.\n"
        "- The **robustness suite** (random-timing Monte Carlo, block bootstrap, rolling windows) "
        "is compute-heavy (thousands of full backtests per combination), so it is run in depth "
        f"at **p = 5** for all 3 assets × 2 signals (6 combinations) rather than across all 30 grid "
        "points. Monte Carlo uses 300 simulations; block bootstrap uses 150 simulations per variant "
        "(raw + de-trended). p=5 sits in the middle of the tested grid and is not cherry-picked from "
        "the results.\n"
        "- Block-bootstrap synthetic price paths reconstruct OHLC from a resampled weekly log-return "
        "path; the Open/High/Low are approximated from the real series' median range-to-body ratio "
        "(intraweek range is not itself resampled). This is a documented simplification — it preserves "
        "the close-to-close return structure that both signals and the ATR indicator ultimately depend on.\n"
        "- Rebalance-band benchmark deploys its full budget as a lump sum at the start of the window "
        "(target weight = the signal strategy's own average invested fraction), rather than accumulating "
        "over time — this matches the spec's 'same total dollars' framing for a lump-sum comparison "
        "strategy.\n\n"
    )

    md.append("## 1. Headline metrics grid\n\n")
    md.append(
        "**Wealth/Inv** = ending wealth ÷ total money invested (primary metric, matched budgets across "
        "all strategies). **MaxDD** is computed on a synthetic NAV/unit-price basis so new deposits can't "
        "mask real losses.\n\n"
    )
    md.append(grid_table_md(grid_df))
    md.append("\nFull grid: [`grid_metrics.csv`](grid_metrics.csv)\n\n")

    md.append("## 2. Grid heatmaps\n\n")
    for k, path in heatmap_figs.items():
        md.append(f"![{k}]({os.path.relpath(path, REPORTS_DIR)})\n\n")

    md.append("## 3. Deep dive at p=5 (robustness tests)\n\n")
    for key, dd in deep_dive.items():
        s = dd["metrics"]
        md.append(f"### {dd['asset']} — {dd['signal']} (p=5)\n\n")
        md.append(
            f"- Trades: {s['n_buys']} buys, {s['n_sells']} sells, total invested "
            f"${s['total_invested']:,.0f}, ending wealth ${s['ending_wealth']:,.0f} "
            f"(**{fmt_num(s['wealth_over_invested'],2)}×** invested; DCA on the same budget: "
            f"**{fmt_num(dd['dca_wealth_over_invested'],2)}×**)\n"
            f"- XIRR: {fmt_pct(s['xirr']) if s['xirr'] is not None else 'n/a'}, "
            f"MaxDD: {fmt_pct(s['max_drawdown'])}, Sharpe: {fmt_num(s['sharpe'],2)}, "
            f"Sortino: {fmt_num(s['sortino'],2)}, Calmar: {fmt_num(s['calmar'],2)}\n"
            f"- Avg cost basis: ${fmt_num(s['avg_cost_basis'],2)}\n\n"
        )
        for fig_key in ["price", "value", "dd"]:
            md.append(f"![{key}_{fig_key}]({os.path.relpath(dd['figs'][fig_key], REPORTS_DIR)})\n\n")

        md.append("**Robustness test 1 — random-timing Monte Carlo (300 sims):** same number of buys/sells, "
                   "random weeks. Percentile of the real strategy within that random distribution "
                   "(need to clear ~95th percentile for the result to look like more than luck):\n\n")
        mcp = dd["mc_percentiles"]
        md.append(
            f"- Ending wealth/invested: **{fmt_num(mcp['wealth'],1)}th percentile**\n"
            f"- Sharpe: **{fmt_num(mcp['sharpe'],1)}th percentile**\n"
            f"- Max drawdown (higher/shallower = better): **{fmt_num(mcp['drawdown'],1)}th percentile**\n\n"
        )
        md.append(f"![{key}_mc]({os.path.relpath(dd['figs']['mc'], REPORTS_DIR)})\n\n")

        md.append("**Robustness test 2 — block bootstrap (150 sims × raw + de-trended):** win rate of the "
                   "strategy vs DCA on resampled alternate price histories:\n\n")
        for k2, v in dd["bootstrap_win_rates"].items():
            md.append(f"- {k2.replace(chr(10), ' ')}: {fmt_pct(v)}\n")
        md.append(f"\n![{key}_bootstrap]({os.path.relpath(dd['figs']['bootstrap'], REPORTS_DIR)})\n\n")

        md.append("**Robustness test 3 — rolling windows:**\n\n")
        for wy, rres in dd["rolling"].items():
            md.append(
                f"- {wy}y windows: {rres['n_windows']} total, {rres['n_scored']} scored "
                f"(rest flagged low-signal-count) — strategy beats DCA on return in "
                f"{fmt_pct(rres['win_rate_return'])} of scored windows, on drawdown in "
                f"{fmt_pct(rres['win_rate_dd'])}, on Sharpe in {fmt_pct(rres['win_rate_sharpe'])}\n"
            )
            if rres["last_window"]:
                lw = rres["last_window"]
                md.append(
                    f"  - Most recent {wy}y window ({str(lw['window_start'])[:10]} → {str(lw['window_end'])[:10]}, "
                    f"{lw['n_signals']} signals): strategy {fmt_num(lw['strat_wealth_over_invested'],2)}× "
                    f"vs DCA {fmt_num(lw['dca_wealth_over_invested'],2)}×, strategy MaxDD "
                    f"{fmt_pct(lw['strat_max_dd'])} vs DCA MaxDD {fmt_pct(lw['dca_max_dd'])}\n"
                )
            md.append(f"\n![{key}_rolling{wy}y]({os.path.relpath(rres['fig'], REPORTS_DIR)})\n\n")

        md.append("**Signal quality — forward returns after each signal fires, vs unconditional average:**\n\n")
        md.append(fwd_returns_table_md(dd["fwd_returns"]["buy_signal"], "After buy signals"))
        md.append("\n")
        md.append(fwd_returns_table_md(dd["fwd_returns"]["sell_signal"], "After sell signals"))
        md.append("\n---\n\n")

    md.append("## 4. Reproducing this report\n\n")
    md.append(
        "```bash\n"
        "python3 -m venv .venv && source .venv/bin/activate\n"
        "pip install -r requirements.txt\n"
        "python run_all.py\n"
        "```\n\n"
        "Data is cached in `data/*.csv` after the first fetch (delete those files, or pass "
        "`force=True` to `backtest.data.fetch_all`, to refresh from Yahoo Finance).\n"
    )

    with open(os.path.join(REPORTS_DIR, "report.md"), "w") as f:
        f.write("".join(md))
