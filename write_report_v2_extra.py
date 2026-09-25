"""Assemble reports/v2/report_extra_assets.md (oil + energy ETF)."""
from __future__ import annotations

import os
import pandas as pd

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports", "v2")


def fmt_pct(x, dp=1):
    try:
        return f"{x*100:.{dp}f}%"
    except Exception:
        return "n/a"


def fmt_num(x, dp=2):
    try:
        return f"{x:.{dp}f}"
    except Exception:
        return "n/a"


def smartdca_table_md(df: pd.DataFrame) -> str:
    cols = ["asset", "rho", "m_max", "sweep", "n_buys", "wealth_over_invested", "dca_wealth_over_invested",
            "avg_cost_per_unit", "dca_avg_cost_per_unit", "max_drawdown", "dca_max_drawdown", "sharpe", "dca_sharpe"]
    lines = ["| Asset | rho | m_max | sweep | #Buy | Wealth/Inv | DCA W/I | Avg cost | DCA cost | MaxDD | DCA MaxDD | Sharpe | DCA Sharpe |\n",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"]
    for _, r in df[cols].iterrows():
        lines.append(
            f"| {r['asset']} | {r['rho']} | {r['m_max']} | {'on' if r['sweep'] else 'off'} | {int(r['n_buys'])} "
            f"| {fmt_num(r['wealth_over_invested'])} | {fmt_num(r['dca_wealth_over_invested'])} "
            f"| {fmt_num(r['avg_cost_per_unit'])} | {fmt_num(r['dca_avg_cost_per_unit'])} "
            f"| {fmt_pct(r['max_drawdown'])} | {fmt_pct(r['dca_max_drawdown'])} "
            f"| {fmt_num(r['sharpe'])} | {fmt_num(r['dca_sharpe'])} |\n"
        )
    return "".join(lines)


def adca_table_md(df: pd.DataFrame) -> str:
    cols = ["asset", "variant", "n_buys", "wealth_over_invested", "dca_wealth_over_invested",
            "max_drawdown", "dca_max_drawdown", "sharpe", "dca_sharpe", "avg_cash_share"]
    lines = ["| Asset | Variant | #Buy | Wealth/Inv | DCA W/I | MaxDD | DCA MaxDD | Sharpe | DCA Sharpe | Avg cash share |\n",
              "|---|---|---|---|---|---|---|---|---|---|\n"]
    for _, r in df[cols].iterrows():
        lines.append(
            f"| {r['asset']} | {r['variant']} | {int(r['n_buys'])} | {fmt_num(r['wealth_over_invested'])} "
            f"| {fmt_num(r['dca_wealth_over_invested'])} | {fmt_pct(r['max_drawdown'])} | {fmt_pct(r['dca_max_drawdown'])} "
            f"| {fmt_num(r['sharpe'])} | {fmt_num(r['dca_sharpe'])} | {fmt_pct(r['avg_cash_share'])} |\n"
        )
    return "".join(lines)


def write_report_v2_extra(smartdca_df, adca_df, deep_dive, heatmap_figs, weekly):
    md = []
    md.append("# SmartDCA / ADCA on Oil and an Energy Stock Index\n\n")
    md.append(
        "Extends [`report.md`](report.md)'s Strategy A (SmartDCA) and Strategy B (ADCA) tests — unchanged "
        "code, same parameter grids and robustness methodology — to two assets that, unlike BTC, did NOT rise "
        "~100x in a decade: **`CL=F`** (WTI crude oil continuous futures — same `=F` convention the spec "
        "already uses for gold/silver) and **`XLE`** (Energy Select Sector SPDR ETF, a basket of energy "
        "equities rather than one stock, so results aren't dominated by a single company's idiosyncratic risk). "
        "Strategy C (the rebalanced BTC/gold/silver portfolio) is a fixed 3-asset construct in the spec and is "
        "not extended here.\n\n"
    )
    for name, w in weekly.items():
        md.append(f"- **{name}**: {len(w)} weekly candles, {w.index.min().date()} → {w.index.max().date()}\n")
    md.append("\n")

    md.append("## Strategy A — SmartDCA\n\n")
    md.append(smartdca_table_md(smartdca_df))
    md.append("\nFull grid: [`smartdca_grid_extra.csv`](smartdca_grid_extra.csv)\n\n")
    for k in heatmap_figs:
        md.append(f"![{k}]({heatmap_figs[k]})\n\n")

    for asset, dd in deep_dive["smartdca"].items():
        m, d = dd["metrics"], dd["dca_metrics"]
        md.append(f"### {asset} — SmartDCA deep dive (rho=2, m_max=3, sweep=on)\n\n")
        md.append(
            f"- Wealth/invested: **{fmt_num(m['wealth_over_invested'])}×** vs DCA **{fmt_num(d['wealth_over_invested'])}×**\n"
            f"- Avg cost per unit: **{fmt_num(m['avg_cost_per_unit'])}** vs DCA **{fmt_num(d['avg_cost_per_unit'])}** "
            f"({'LOWER' if m['avg_cost_per_unit'] < d['avg_cost_per_unit'] else 'HIGHER'})\n"
            f"- MaxDD: {fmt_pct(m['max_drawdown'])} vs DCA {fmt_pct(d['max_drawdown'])}; "
            f"Sharpe: {fmt_num(m['sharpe'])} vs DCA {fmt_num(d['sharpe'])}\n\n"
        )
        for fk in ["value", "buys", "dd"]:
            md.append(f"![{asset}_{fk}]({dd['figs'][fk]})\n\n")
        md.append("**Rolling windows vs DCA:**\n\n")
        for wy, r in dd["rolling"].items():
            md.append(f"- {wy}y: {r['n_windows']} windows, wins on wealth {fmt_pct(r['win_rate_wealth'])}, on Sharpe {fmt_pct(r['win_rate_sharpe'])}\n")
            md.append(f"\n![{asset}_rolling{wy}]({r['fig']})\n\n")
        md.append("**Block bootstrap win rate vs DCA:**\n\n")
        for k2, v in dd["bootstrap_win_rates"].items():
            md.append(f"- {k2.replace(chr(10), ' ')}: {fmt_pct(v)}\n")
        md.append(f"\n![{asset}_bootstrap]({dd['figs']['bootstrap']})\n\n---\n\n")

    md.append("## Strategy B — ADCA\n\n")
    md.append(adca_table_md(adca_df))
    md.append("\nFull grid: [`adca_grid_extra.csv`](adca_grid_extra.csv)\n\n")

    for asset, variants in deep_dive["adca"].items():
        for variant, dd in variants.items():
            m, d = dd["metrics"], dd["dca_metrics"]
            md.append(f"### {asset} — ADCA {variant}\n\n")
            md.append(
                f"- Wealth/invested: **{fmt_num(m['wealth_over_invested'])}×** vs DCA **{fmt_num(d['wealth_over_invested'])}×**\n"
                f"- MaxDD: {fmt_pct(m['max_drawdown'])} vs DCA {fmt_pct(d['max_drawdown'])}; "
                f"Sharpe: {fmt_num(m['sharpe'])} vs DCA {fmt_num(d['sharpe'])}\n"
                f"- **Placebo test** (shuffled regime score, 200 sims): real result sits at the "
                f"**{fmt_num(dd['placebo_percentile_wealth'],1)}th percentile** on wealth, "
                f"**{fmt_num(dd['placebo_percentile_sharpe'],1)}th percentile** on Sharpe\n\n"
            )
            for fk in ["value", "dd"]:
                md.append(f"![{asset}_{variant}_{fk}]({dd['figs'][fk]})\n\n")
            md.append(f"![{asset}_{variant}_placebo]({dd['figs']['placebo']})\n\n")
            md.append("**Rolling windows vs DCA:**\n\n")
            for wy, r in dd["rolling"].items():
                md.append(f"- {wy}y: {r['n_windows']} windows, wins on wealth {fmt_pct(r['win_rate_wealth'])}, on Sharpe {fmt_pct(r['win_rate_sharpe'])}\n")
            md.append("\n**Block bootstrap win rate vs DCA:**\n\n")
            for k2, v in dd["bootstrap_win_rates"].items():
                md.append(f"- {k2.replace(chr(10), ' ')}: {fmt_pct(v)}\n")
            md.append(f"\n![{asset}_{variant}_bootstrap]({dd['figs']['bootstrap']})\n\n---\n\n")

    md.append("## Reproducing this report\n\n```bash\npython run_v2_extra_assets.py\n```\n")

    with open(os.path.join(REPORTS_DIR, "report_extra_assets.md"), "w") as f:
        f.write("".join(md))
