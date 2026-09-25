"""Chart generation for v2 (spec section 13, deliverable 2)."""
from __future__ import annotations

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

V2_REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "reports", "v2")
FIG_DIR = os.path.join(V2_REPORTS_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def _save(fig, name):
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    # Returned path is relative to reports/v2/ (where report.md lives), e.g. "figures/x.png".
    return os.path.relpath(path, V2_REPORTS_DIR)


def plot_value_vs_deposits(result_df, bench_df, closes_final_strat, closes_final_bench, title, name):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    strat_value = result_df["cash"] + result_df["units"] * closes_final_strat
    bench_value = bench_df["cash"] + bench_df["units"] * closes_final_bench
    ax.plot(result_df.index, strat_value, color="#2e8b57", label="Strategy — total value")
    ax.plot(result_df.index, result_df["invested"], color="#888888", linestyle="--", label="Cumulative deposits")
    ax.plot(bench_df.index, bench_value, color="#3b6fa0", label="Benchmark — total value")
    ax.set_title(title)
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.25)
    return _save(fig, name)


def plot_nav_drawdown(nav_strat, nav_bench, index, title, name):
    fig, ax = plt.subplots(figsize=(11, 3.5))
    dd_s = nav_strat / pd.Series(nav_strat).cummax().to_numpy() - 1.0
    dd_b = nav_bench / pd.Series(nav_bench).cummax().to_numpy() - 1.0
    ax.fill_between(index, dd_s * 100, 0, color="#2e8b57", alpha=0.4, label="Strategy")
    ax.plot(index, dd_b * 100, color="#3b6fa0", linewidth=1.0, label="Benchmark")
    ax.set_ylabel("% drawdown")
    ax.set_title(title)
    ax.legend(loc="lower left", fontsize=8)
    ax.grid(alpha=0.25)
    return _save(fig, name)


def plot_buy_amounts(weekly, buy_usd, title, name):
    fig, ax1 = plt.subplots(figsize=(11, 4))
    ax2 = ax1.twinx()
    ax1.plot(weekly.index, weekly["Close"], color="#3b6fa0", linewidth=0.9)
    ax1.set_yscale("log")
    ax1.set_ylabel("Price (log)", color="#3b6fa0")
    ax2.bar(weekly.index, buy_usd, width=5, color="#2e8b57", alpha=0.55)
    ax2.set_ylabel("$ bought that week", color="#2e8b57")
    ax1.set_title(title)
    return _save(fig, name)


def plot_portfolio_weights(result_df, assets, title, name):
    fig, ax = plt.subplots(figsize=(11, 4))
    cols = [f"w_{a}" for a in assets if f"w_{a}" in result_df.columns]
    if f"w_CASH" in result_df.columns:
        cols.append("w_CASH")
    ax.stackplot(result_df.index, [result_df[c] * 100 for c in cols], labels=[c[2:] for c in cols], alpha=0.85)
    rb_dates = result_df.index[result_df["rebalanced"]]
    for d in rb_dates[:: max(1, len(rb_dates) // 60) or 1]:
        ax.axvline(d, color="black", alpha=0.08, linewidth=0.6)
    ax.set_ylabel("Weight (%)")
    ax.set_title(title + f"  ({int(result_df['rebalanced'].sum())} rebalances, faint lines)")
    ax.legend(loc="upper left", fontsize=8, ncol=len(cols))
    return _save(fig, name)


def plot_rolling_window_summary(rw_df, title, name):
    fig, ax = plt.subplots(figsize=(11, 3.5))
    diff = rw_df["strat_wealth_over_invested"] - rw_df["bench_wealth_over_invested"]
    colors = np.where(diff > 0, "#2e8b57", "#b03a2e")
    ax.bar(range(len(rw_df)), diff, color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Rolling window index (chronological)")
    ax.set_ylabel("Strategy − Benchmark (wealth/invested)")
    ax.set_title(title)
    ax.grid(alpha=0.25, axis="y")
    return _save(fig, name)


def plot_distribution(dist_df, real_value, col, title, name):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(dist_df[col].dropna(), bins=40, color="#7f9cc4", alpha=0.85)
    ax.axvline(real_value, color="#b03a2e", linewidth=2, label=f"Real = {real_value:.3f}")
    ax.set_title(title)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    return _save(fig, name)


def plot_win_rate_bar(win_rates: dict, title, name):
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = list(win_rates.keys())
    vals = [win_rates[k] * 100 for k in labels]
    ax.bar(labels, vals, color="#4c7fb0")
    ax.axhline(50, color="#888", linestyle="--", linewidth=1)
    ax.set_ylabel("Strategy win rate vs benchmark (%)")
    ax.set_title(title)
    ax.set_ylim(0, 100)
    for i, v in enumerate(vals):
        ax.text(i, v + 1, f"{v:.0f}%", ha="center", fontsize=8)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right", fontsize=8)
    return _save(fig, name)


def plot_grid_heatmap(grid_df, index_col, columns_col, value_col, title, name):
    pivot = grid_df.pivot_table(index=index_col, columns=columns_col, values=value_col, aggfunc="mean")
    fig, ax = plt.subplots(figsize=(5.5, 4))
    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            v = pivot.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, shrink=0.8)
    return _save(fig, name)
