"""Assemble reports/v2/report.md from the v2 grid results + deep-dive robustness."""
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


def fmt_money(x):
    try:
        return f"${x:,.0f}"
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


def rebalance_table_md(df: pd.DataFrame) -> str:
    cols = ["era", "scheme", "trigger", "wealth_over_invested", "fixed_wealth_over_invested",
            "max_drawdown", "fixed_max_drawdown", "sharpe", "fixed_sharpe", "n_rebalances"]
    lines = ["| Era | Scheme | Trigger | Wealth/Inv | Fixed-wt W/I | MaxDD | Fixed MaxDD | Sharpe | Fixed Sharpe | #Rebal |\n",
              "|---|---|---|---|---|---|---|---|---|---|\n"]
    for _, r in df[cols].iterrows():
        n_rebal = r["n_rebalances"]
        lines.append(
            f"| {r['era']} | {r['scheme']} | {r['trigger']} | {fmt_num(r['wealth_over_invested'])} "
            f"| {fmt_num(r['fixed_wealth_over_invested'])} | {fmt_pct(r['max_drawdown'])} | {fmt_pct(r['fixed_max_drawdown'])} "
            f"| {fmt_num(r['sharpe'])} | {fmt_num(r['fixed_sharpe'])} "
            f"| {int(n_rebal) if pd.notna(n_rebal) else 'n/a'} |\n"
        )
    return "".join(lines)


def write_report_v2(smartdca_df, adca_df, rebalance_df, deep_dive, heatmap_figs, checks, eras):
    md = []
    md.append("# BTC / Gold / Silver Accumulation — v2 Backtest Results\n\n")
    md.append(
        "Spec: [`btc-gold-silver-backtest-spec-v2.md`](../../btc-gold-silver-backtest-spec-v2.md). "
        "Live Yahoo Finance + FRED data. Reusable pipeline: `run_v2.py` + `src/backtest/v2/`.\n\n"
        "v1 tested buy-the-dip / trim-the-spike (results: [`../report.md`](../report.md)) and found it "
        "underperformed plain DCA. v2 tests three strategies that stay fully invested and change *how much* "
        "or *where* to buy, instead of *whether* to be in the market: **SmartDCA** (buy more below the trend, "
        "less above), **ADCA** (buy more in favorable macro/market regimes), and a **rebalanced BTC/gold/silver "
        "portfolio** (direct new money to whichever asset is most underweight; rebalance on drift bands).\n\n"
    )

    md.append("## Implementation checks (spec §11)\n\n")
    for k, v in checks.items():
        md.append(f"- {'✅' if v else '❌'} `{k}`\n")
    md.append("\n")

    md.append("## Scoping notes\n\n")
    md.append(
        "- Headline grids are run in full: SmartDCA (3 assets × 12 parameter combos = 36), ADCA (3 assets × "
        "2 variants = 6), rebalanced portfolio (7 grid rows × 2 eras = 14, plus single-asset benchmarks).\n"
        "- The robustness suite (rolling windows, block bootstrap, placebo) runs in depth on one representative "
        "variant per strategy family rather than the whole grid: SmartDCA at rho=2/m_max=3/sweep=on, both ADCA "
        "variants, and the rebalanced portfolio at C2 and C3 (both on 5/25 bands, the grid's primary trigger).\n"
        "- Block bootstrap uses 200 simulations per variant for single-asset strategies and 60 for the portfolio "
        "(more expensive per simulation); placebo tests use 200. The spec's 1,000-simulation target is reduced "
        "for runtime, consistent with how v1's robustness suite was scoped.\n"
        "- FRED's `UNRATE`/`TCU` are monthly; ADCA B1's 'last 12 available monthly values' is approximated as a "
        "trailing 52-week mean on the forward-filled weekly series.\n\n"
    )

    # --- Strategy A ---
    md.append("## Strategy A — SmartDCA\n\n")
    md.append(
        "Buys more when price is below its 52-week trend, less when above. **Caveat from the spec itself: "
        "the paper's 'guaranteed lower cost per unit' result assumes a fixed reference price; v2 uses a moving "
        "52-week average instead (since BTC rose ~100x, a fixed reference breaks). That trade lets the "
        "guarantee fail in practice** — see the cost-basis columns below.\n\n"
    )
    md.append(smartdca_table_md(smartdca_df))
    md.append("\nFull grid: [`smartdca_grid.csv`](smartdca_grid.csv)\n\n")
    for k in [k for k in heatmap_figs if k.startswith("smartdca_")]:
        md.append(f"![{k}]({heatmap_figs[k]})\n\n")

    for asset, dd in deep_dive["smartdca"].items():
        m, d = dd["metrics"], dd["dca_metrics"]
        md.append(f"### {asset} — SmartDCA deep dive (rho=2, m_max=3, sweep=on)\n\n")
        md.append(
            f"- Wealth/invested: **{fmt_num(m['wealth_over_invested'])}×** vs DCA **{fmt_num(d['wealth_over_invested'])}×** "
            f"(invested {fmt_money(m['total_invested'])} both)\n"
            f"- Avg cost per unit: **{fmt_num(m['avg_cost_per_unit'])}** vs DCA **{fmt_num(d['avg_cost_per_unit'])}** "
            f"({'LOWER — as guaranteed' if m['avg_cost_per_unit'] < d['avg_cost_per_unit'] else 'HIGHER — guarantee broke down'})\n"
            f"- MaxDD: {fmt_pct(m['max_drawdown'])} vs DCA {fmt_pct(d['max_drawdown'])}; "
            f"Sharpe: {fmt_num(m['sharpe'])} vs DCA {fmt_num(d['sharpe'])}; avg cash share: {fmt_pct(m['avg_cash_share'])}\n\n"
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

    # --- Strategy B ---
    md.append("## Strategy B — ADCA (Augmented DCA)\n\n")
    md.append("Buys more in 'aggressive' regimes (low VIX + favorable macro/trend), less in 'conservative' ones.\n\n")
    md.append(adca_table_md(adca_df))
    md.append("\nFull grid: [`adca_grid.csv`](adca_grid.csv)\n\n")

    for asset, variants in deep_dive["adca"].items():
        for variant, dd in variants.items():
            m, d = dd["metrics"], dd["dca_metrics"]
            md.append(f"### {asset} — ADCA {variant}\n\n")
            md.append(
                f"- Wealth/invested: **{fmt_num(m['wealth_over_invested'])}×** vs DCA **{fmt_num(d['wealth_over_invested'])}×**\n"
                f"- MaxDD: {fmt_pct(m['max_drawdown'])} vs DCA {fmt_pct(d['max_drawdown'])}; "
                f"Sharpe: {fmt_num(m['sharpe'])} vs DCA {fmt_num(d['sharpe'])}\n"
                f"- **Placebo test** (shuffled regime score, {200} sims): real result sits at the "
                f"**{fmt_num(dd['placebo_percentile_wealth'],1)}th percentile** on wealth, "
                f"**{fmt_num(dd['placebo_percentile_sharpe'],1)}th percentile** on Sharpe, of what a "
                f"regime score with NO real link to conditions would produce\n\n"
            )
            for fk in ["value", "dd"]:
                md.append(f"![{asset}_{variant}_{fk}]({dd['figs'][fk]})\n\n")
            md.append(f"![{asset}_{variant}_placebo]({dd['figs']['placebo']})\n\n")
            md.append("**Rolling windows vs DCA:**\n\n")
            for wy, r in dd["rolling"].items():
                md.append(f"- {wy}y: {r['n_windows']} windows, wins on wealth {fmt_pct(r['win_rate_wealth'])}, on Sharpe {fmt_pct(r['win_rate_sharpe'])}\n")
            md.append(f"\n**Block bootstrap win rate vs DCA:**\n\n")
            for k2, v in dd["bootstrap_win_rates"].items():
                md.append(f"- {k2.replace(chr(10), ' ')}: {fmt_pct(v)}\n")
            md.append(f"\n![{asset}_{variant}_bootstrap]({dd['figs']['bootstrap']})\n\n---\n\n")

    # --- Strategy C ---
    md.append("## Strategy C — Rebalanced BTC/Gold/Silver Portfolio\n\n")
    md.append(rebalance_table_md(rebalance_df))
    md.append("\nFull grid: [`rebalance_grid.csv`](rebalance_grid.csv)\n\n")

    for era_name, schemes in deep_dive["rebalance"].items():
        for scheme, dd in schemes.items():
            m, f = dd["metrics"], dd["fixed_metrics"]
            md.append(f"### {era_name} — {scheme} (5/25 bands) vs fixed-weight, never rebalanced\n\n")
            md.append(
                f"- Wealth/invested: **{fmt_num(m['wealth_over_invested'])}×** vs fixed-weight **{fmt_num(f['wealth_over_invested'])}×**\n"
                f"- MaxDD: {fmt_pct(m['max_drawdown'])} vs fixed-weight {fmt_pct(f['max_drawdown'])}; "
                f"Sharpe: {fmt_num(m['sharpe'])} vs fixed-weight {fmt_num(f['sharpe'])}; {m['n_rebalances']} rebalances triggered\n"
            )
            if dd["placebo"]:
                md.append(
                    f"- **Placebo test** (shuffled trend filter, {200} sims): real result sits at the "
                    f"**{fmt_num(dd['placebo']['percentile_wealth'],1)}th percentile** on wealth, "
                    f"**{fmt_num(dd['placebo']['percentile_sharpe'],1)}th percentile** on Sharpe\n"
                )
            md.append("\n")
            for fk in ["weights", "dd"]:
                md.append(f"![{era_name}_{scheme}_{fk}]({dd['figs'][fk]})\n\n")
            if dd["placebo"]:
                md.append(f"![{era_name}_{scheme}_placebo]({dd['placebo']['fig']})\n\n")
            md.append("**Rolling windows vs fixed-weight:**\n\n")
            for wy, r in dd["rolling"].items():
                md.append(f"- {wy}y: {r['n_windows']} windows, wins on wealth {fmt_pct(r['win_rate_wealth'])}, on Sharpe {fmt_pct(r['win_rate_sharpe'])}\n")
            md.append(f"\n**Block bootstrap win rate vs fixed-weight:**\n\n")
            for k2, v in dd["bootstrap_win_rates"].items():
                md.append(f"- {k2.replace(chr(10), ' ')}: {fmt_pct(v)}\n")
            md.append(f"\n![{era_name}_{scheme}_bootstrap]({dd['figs']['bootstrap']})\n\n---\n\n")

    md.append("## Reproducing this report\n\n")
    md.append(
        "```bash\n"
        "python3 -m venv .venv && source .venv/bin/activate\n"
        "pip install -r requirements.txt\n"
        "python run_v2.py\n"
        "```\n"
    )

    with open(os.path.join(REPORTS_DIR, "report.md"), "w") as f:
        f.write("".join(md))
