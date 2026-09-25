"""Chart generation (spec section 9, deliverable 2)."""
from __future__ import annotations

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports", "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def _save(fig, name):
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return os.path.relpath(path, os.path.join(FIG_DIR, "..", ".."))


def plot_price_with_signals(weekly, buy_signal, sell_signal, asset, signal_name, p, name):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(weekly.index, weekly["Close"], color="#3b6fa0", linewidth=0.9, label="Close")
    buy_pts = weekly.index[buy_signal.reindex(weekly.index).fillna(False)]
    sell_pts = weekly.index[sell_signal.reindex(weekly.index).fillna(False)]
    ax.scatter(buy_pts, weekly.loc[buy_pts, "Close"], marker="^", color="#2e8b57", s=28, zorder=3, label="Buy signal")
    ax.scatter(sell_pts, weekly.loc[sell_pts, "Close"], marker="v", color="#b03a2e", s=28, zorder=3, label="Sell signal")
    ax.set_title(f"{asset} — {signal_name} (p={p}) — price with buy/sell signals")
    ax.set_yscale("log")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.25)
    return _save(fig, name)


def plot_value_vs_invested(result, dca_result, asset, signal_name, p, name):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(result.index, result["total_value"], color="#2e8b57", label="Signal strategy — total value")
    ax.plot(result.index, result["invested"], color="#888888", linestyle="--", label="Signal strategy — money in")
    ax.plot(dca_result.index, dca_result["total_value"], color="#3b6fa0", label="DCA — total value")
    ax.set_title(f"{asset} — {signal_name} (p={p}) — account value vs money-in vs DCA")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.25)
    return _save(fig, name)


def plot_drawdown(result, dca_result, asset, signal_name, p, name):
    from .metrics import max_drawdown
    fig, ax = plt.subplots(figsize=(11, 3.5))
    nav = result["nav"]
    dd = nav / nav.cummax() - 1.0
    dca_nav = dca_result["nav"]
    dca_dd = dca_nav / dca_nav.cummax() - 1.0
    ax.fill_between(dd.index, dd.values * 100, 0, color="#2e8b57", alpha=0.4, label="Signal strategy")
    ax.plot(dca_dd.index, dca_dd.values * 100, color="#3b6fa0", linewidth=1.0, label="DCA")
    ax.set_title(f"{asset} — {signal_name} (p={p}) — drawdown (synthetic NAV basis)")
    ax.set_ylabel("% drawdown")
    ax.legend(loc="lower left", fontsize=8)
    ax.grid(alpha=0.25)
    return _save(fig, name)


def plot_mc_distribution(mc_df, real_value, stat_col, title, name, higher_is_better=True):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(mc_df[stat_col].dropna(), bins=40, color="#7f9cc4", alpha=0.85)
    ax.axvline(real_value, color="#b03a2e", linewidth=2, label=f"Real strategy = {real_value:.3f}")
    ax.set_title(title)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    return _save(fig, name)


def plot_bootstrap_winrate(win_rates: dict, title, name):
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = list(win_rates.keys())
    vals = [win_rates[k] * 100 for k in labels]
    ax.bar(labels, vals, color="#4c7fb0")
    ax.axhline(50, color="#888", linestyle="--", linewidth=1)
    ax.set_ylabel("Strategy win rate vs DCA (%)")
    ax.set_title(title)
    ax.set_ylim(0, 100)
    for i, v in enumerate(vals):
        ax.text(i, v + 1, f"{v:.0f}%", ha="center", fontsize=8)
    return _save(fig, name)


def plot_rolling_window_summary(rw_df, title, name):
    fig, ax = plt.subplots(figsize=(11, 3.5))
    colors = np.where(rw_df["low_signal_count"], "#cccccc", np.where(rw_df["strat_beats_dca_return"], "#2e8b57", "#b03a2e"))
    ax.bar(range(len(rw_df)), rw_df["strat_wealth_over_invested"] - rw_df["dca_wealth_over_invested"], color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Rolling window index (chronological)")
    ax.set_ylabel("Strategy − DCA (wealth/invested)")
    ax.set_title(title + "  (grey = low-signal-count window, flagged not scored)")
    ax.grid(alpha=0.25, axis="y")
    return _save(fig, name)


def plot_grid_heatmap(grid_df, value_col, title, name):
    """Heatmap of results across (signal x p) for one asset, or (asset x p) for one signal."""
    pivot = grid_df.pivot_table(index="p", columns="signal", values=value_col, aggfunc="mean")
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_ylabel("p (%)")
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            v = pivot.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, shrink=0.8)
    return _save(fig, name)
