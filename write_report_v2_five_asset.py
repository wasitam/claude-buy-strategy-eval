"""Assemble reports/v2/report_five_asset_rebalance.md."""
from __future__ import annotations

import os
import pandas as pd

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports", "v2")

TRIGGER_LABELS = {
    "bands_2_10": "2pp/10% bands (tightest)", "bands_5_25": "5pp/25% bands",
    "bands_10_50": "10pp/50% bands", "bands_20_100": "20pp/100% bands (loosest)",
    "calendar_1": "Monthly", "calendar_3": "Quarterly", "calendar_6": "Semiannual",
    "calendar_12": "Annual", "never": "Never (buy & hold weights)",
}


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


def freq_table_md(df: pd.DataFrame) -> str:
    cols = ["scheme", "trigger", "wealth_over_invested", "sharpe", "max_drawdown",
            "n_rebalances", "avg_weeks_between_rebalances", "total_fees", "fees_pct_of_invested"]
    lines = ["| Scheme | Trigger | Wealth/Inv | Sharpe | MaxDD | #Rebal | Avg wks/rebal | Total fees | Fees % of invested |\n",
              "|---|---|---|---|---|---|---|---|---|\n"]
    for _, r in df[cols].iterrows():
        lines.append(
            f"| {r['scheme']} | {TRIGGER_LABELS.get(r['trigger'], r['trigger'])} | {fmt_num(r['wealth_over_invested'])} "
            f"| {fmt_num(r['sharpe'])} | {fmt_pct(r['max_drawdown'])} | {int(r['n_rebalances'])} "
            f"| {fmt_num(r['avg_weeks_between_rebalances'],1)} | ${r['total_fees']:,.0f} | {fmt_pct(r['fees_pct_of_invested'],2)} |\n"
        )
    return "".join(lines)


def write_report_five_asset(freq_df, freq_figs, fig_weights, robustness_results, weekly, assets):
    md = []
    md.append("# How Often Should You Rebalance? Stocks / Gold / Silver / BTC / Oil\n\n")
    md.append(
        "Extends Strategy C's rebalanced-portfolio engine (unchanged code, spec section 6) from the original "
        "3 assets to 5: **S&P 500, gold, silver, BTC, and oil**, each getting an equal $300/week slice of a "
        "$1,500/week total deposit under equal-weight targets (or inverse-vol-weighted amounts under C2). Every "
        "asset is aligned to BTC's shorter history (its start + a 1-year warm-up), since BTC is the constraint.\n\n"
    )
    for a in assets:
        w = weekly[a]
        md.append(f"- **{a}**: {len(w)} weekly candles, {w.index.min().date()} → {w.index.max().date()}\n")
    md.append("\n")

    md.append(
        "## The direct question: how often to rebalance?\n\n"
        "Two target-weight schemes (**C1** equal-weight 20% each; **C2** inverse-volatility, so calmer assets "
        "like gold/silver naturally get a bigger slice than BTC) are each run under 9 rebalancing schedules, "
        "from very tight drift bands to a full year between rebalances, plus a 'never' baseline (buy whichever "
        "asset is most underweight each week, but never force a sell).\n\n"
    )
    md.append(freq_table_md(freq_df))
    md.append("\nFull sweep: [`five_asset_rebalance_frequency.csv`](five_asset_rebalance_frequency.csv)\n\n")

    for scheme in ["C1", "C2"]:
        md.append(f"![{scheme}_metrics]({freq_figs[f'{scheme}_metrics']})\n\n")

    md.append(f"![weights]({fig_weights})\n\n")

    md.append("## Robustness on three representative schedules\n\n")
    md.append(
        "Rolling windows and block bootstrap (60 sims per variant, raw + de-trended — reduced from the spec's "
        "1,000 for runtime, same scoping as the rest of v2) run on a tight band (5/25), a quarterly calendar, "
        "and an annual calendar, for both weighting schemes, against the same weights' fixed-weight/never-"
        "rebalanced benchmark.\n\n"
    )
    for scheme, triggers in robustness_results.items():
        for trigger, d in triggers.items():
            h = d["headline"]
            md.append(f"### {scheme} — {TRIGGER_LABELS.get(trigger, trigger)}\n\n")
            md.append(
                f"- Wealth/invested: **{fmt_num(h['wealth_over_invested'])}×**, Sharpe: {fmt_num(h['sharpe'])}, "
                f"MaxDD: {fmt_pct(h['max_drawdown'])}, {int(h['n_rebalances'])} rebalances "
                f"({fmt_pct(h['fees_pct_of_invested'],2)} of invested capital spent on fees)\n"
            )
            for wy, r in d["rolling"].items():
                md.append(f"- {wy}y rolling windows: wins on wealth {fmt_pct(r['win_rate_wealth'])}, on Sharpe {fmt_pct(r['win_rate_sharpe'])} "
                          f"(of {r['n_windows']} windows), vs fixed-weight/never-rebalanced\n")
            md.append("- Block bootstrap win rate vs fixed-weight: ")
            md.append(", ".join(f"{k.replace(chr(10), ' ')} {fmt_pct(v)}" for k, v in d["bootstrap_win_rates"].items()))
            md.append(f"\n\n![{scheme}_{trigger}_bootstrap]({d['fig_bootstrap']})\n\n")
            for wy, r in d["rolling"].items():
                md.append(f"![{scheme}_{trigger}_rolling{wy}]({r['fig']})\n\n")
            md.append("---\n\n")

    md.append("## Reproducing this report\n\n```bash\npython run_v2_five_asset_rebalance.py\n```\n")

    with open(os.path.join(REPORTS_DIR, "report_five_asset_rebalance.md"), "w") as f:
        f.write("".join(md))
