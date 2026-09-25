"""Assemble reports/v2/report_regime_switch.md (Strategy D)."""
from __future__ import annotations

import os
import pandas as pd

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports", "v2")
N_SIGNALS_FOR_GUARD = 8
GUARD_PCTILE = 100.0 / N_SIGNALS_FOR_GUARD / 100.0 * 5.0  # 5% / 8 = 0.625%


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


def headline_table_md(df: pd.DataFrame) -> str:
    cols = ["asset", "signal", "wealth_over_invested", "dca_wealth_over_invested", "smart_wealth_over_invested",
            "sharpe", "dca_sharpe", "smart_sharpe", "max_drawdown", "tight_share", "n_switches"]
    lines = ["| Asset | Signal | D Wealth/Inv | DCA W/I | SmartDCA W/I | D Sharpe | DCA Sharpe | SmartDCA Sharpe | MaxDD | %TIGHT | #Switches |\n",
              "|---|---|---|---|---|---|---|---|---|---|---|\n"]
    for _, r in df[cols].iterrows():
        lines.append(
            f"| {r['asset']} | {r['signal']} | {fmt_num(r['wealth_over_invested'])} | {fmt_num(r['dca_wealth_over_invested'])} "
            f"| {fmt_num(r['smart_wealth_over_invested'])} | {fmt_num(r['sharpe'])} | {fmt_num(r['dca_sharpe'])} "
            f"| {fmt_num(r['smart_sharpe'])} | {fmt_pct(r['max_drawdown'])} | {fmt_pct(r['tight_share'])} | {int(r['n_switches'])} |\n"
        )
    return "".join(lines)


def period_table_md(df: pd.DataFrame) -> str:
    cols = ["asset", "period", "signal", "wealth_over_invested", "dca_wealth_over_invested",
            "smart_wealth_over_invested", "sharpe", "dca_sharpe", "smart_sharpe"]
    lines = ["| Asset | Period | Signal | D W/I | DCA W/I | SmartDCA W/I | D Sharpe | DCA Sharpe | SmartDCA Sharpe |\n",
              "|---|---|---|---|---|---|---|---|---|\n"]
    for _, r in df[cols].iterrows():
        lines.append(
            f"| {r['asset']} | {r['period']} | {r['signal']} | {fmt_num(r['wealth_over_invested'])} "
            f"| {fmt_num(r['dca_wealth_over_invested'])} | {fmt_num(r['smart_wealth_over_invested'])} "
            f"| {fmt_num(r['sharpe'])} | {fmt_num(r['dca_sharpe'])} | {fmt_num(r['smart_sharpe'])} |\n"
        )
    return "".join(lines)


def cycles_table_md(df: pd.DataFrame) -> str:
    lines = ["| Type | Start | End |\n", "|---|---|---|\n"]
    for _, r in df.iterrows():
        lines.append(f"| {r['type']} | {str(r['start'])[:10]} | {str(r['end'])[:10]} |\n")
    return "".join(lines)


def percycle_summary_md(df: pd.DataFrame) -> str:
    lines = ["| Asset | Signal | Cycle type | # cycles | D beats DCA (wealth) | ... of which hikes |\n",
              "|---|---|---|---|---|---|\n"]
    for (asset, signal), g in df.groupby(["asset", "signal"]):
        hikes = g[g["cycle_type"] == "hike"]
        lines.append(
            f"| {asset} | {signal} | all | {len(g)} | {fmt_pct(g['d_beats_dca_wealth'].mean())} "
            f"| hikes: {fmt_pct(hikes['d_beats_dca_wealth'].mean()) if len(hikes) else 'n/a'} ({len(hikes)} cycles) |\n"
        )
    return "".join(lines)


def evaluate_win_condition(period_df, percycle_df, placebo_results):
    """Spec 15.7: a signal wins only if all four hold, evaluated on the
    Primary 2001-2023 gold+silver sample."""
    rows = []
    primary = period_df[period_df["period"] == "Primary 2001-2023"]
    for signal in primary["signal"].unique():
        if signal == "Control":
            continue
        checks = {}
        sub = primary[primary["signal"] == signal]
        # check 1: beats DCA and SmartDCA on BOTH wealth and Sharpe, on EVERY primary asset tested
        c1 = bool(((sub["wealth_over_invested"] > sub["dca_wealth_over_invested"]) &
                    (sub["sharpe"] > sub["dca_sharpe"]) &
                    (sub["wealth_over_invested"] > sub["smart_wealth_over_invested"]) &
                    (sub["sharpe"] > sub["smart_sharpe"])).all())
        checks["beats_dca_and_smart"] = c1
        # check 2: beats Control switch on final wealth
        control_sub = primary[primary["signal"] == "Control"]
        merged = sub.merge(control_sub[["asset", "wealth_over_invested"]], on="asset", suffixes=("", "_control"))
        c2 = bool((merged["wealth_over_invested"] > merged["wealth_over_invested_control"]).all()) if len(merged) else False
        checks["beats_control"] = c2
        # check 3: wins majority of TIGHTENING (hike) cycles
        cyc = percycle_df[(percycle_df["signal"] == signal) & (percycle_df["cycle_type"] == "hike")]
        c3 = bool(cyc["d_beats_dca_wealth"].mean() > 0.5) if len(cyc) else False
        checks["wins_majority_hike_cycles"] = c3
        # check 4: placebo, multiple-testing guard -- single signal must clear top 0.625th percentile
        pctiles = []
        for asset in primary["asset"].unique():
            p = placebo_results.get(asset, {}).get(signal)
            if p:
                pctiles.append(p["percentile_wealth"])
        c4 = bool(all(p >= (100 - GUARD_PCTILE) for p in pctiles)) if pctiles else False
        checks["passes_placebo_guard"] = c4
        checks["placebo_percentiles"] = pctiles

        checks["WINS"] = c1 and c2 and c3 and c4
        rows.append({"signal": signal, **checks})
    return pd.DataFrame(rows)


def write_report_regime_switch(headline_df, period_df, cycles_df, percycle_df, placebo_results, diag, figs, weekly):
    md = []
    md.append("# Strategy D — Rate-Regime Switch (SmartDCA in Tightening, DCA Otherwise)\n\n")
    md.append(
        "Spec: [`btc-gold-silver-backtest-spec-v2.1.md`](../../btc-gold-silver-backtest-spec-v2.1.md), section 15. "
        "Tests whether **switching to SmartDCA during monetary tightening and plain DCA otherwise** beats either "
        "strategy alone — motivated by v2's finding that SmartDCA only wins on gold/silver once you strip out the "
        "drift (detrended bootstrap: 64–70% win rate), and specifically loses in the recent gold/silver rally.\n\n"
    )

    md.append("## Scoping notes (read this first)\n\n")
    md.append(
        "- **R4 (dot plot)** uses real ALFRED vintages, fetched from ALFRED's actual FEDTARMD release-date "
        "dropdown. Those only go back to **2015-12-16**, not Jan 2012 as the spec's data table assumed — a real "
        "data-availability constraint, not a design choice. R4's usable sample is ~2016+ (spec itself already "
        "called this signal 'suggestive only, few cycles').\n"
        "- **Placebo sims reduced to 300** (from the spec's 1,000), same scoping as the rest of v2.\n"
        "- **Full placebo suite** (all 8 rate signals + Control) runs on **gold and silver**, the spec's actual "
        "primary hypothesis assets. **BTC, oil, and S&P 500** (added per your ask to cover the 'agreed' 5-asset "
        "set) get placebo tests on **Combo + Control only**, to keep runtime reasonable — the rate-regime "
        "*hypothesis itself* (opportunity cost of holding a non-yielding asset) was built around gold/silver "
        "specifically; BTC/oil/stocks are exploratory extensions, not the design target.\n"
        "- The **win condition** (spec §15.7, all 4 checks) is evaluated strictly on the **Primary 2001–2023 "
        "gold+silver sample**, exactly as the spec specifies.\n"
        "- Multiple-testing guard: 8 rate signals tested → a single signal needs to clear the "
        f"**top {GUARD_PCTILE:.3f}%** of its placebo distribution (5% ÷ 8) to count as a real pass.\n\n"
    )

    md.append("## Fed cycles (detected from the target-rate series)\n\n")
    md.append(
        "Heuristic: group consecutive weekly target-rate moves of the same sign into hike/ease cycles; a flat "
        "stretch longer than 26 weeks between moves becomes its own 'hold' cycle. A simplification of the spec's "
        "'derive from data, don't hard-code' instruction — matches the real historical Fed cycle shape closely "
        "(2001 easing, 2004-06 hiking, 2007-08 GFC easing, ZIRP hold to 2015, 2015-18 hiking, 2019 easing, "
        "COVID hold, 2022-23 hiking, 2024-25 easing, and the Sept 2026 hike the spec itself flagged).\n\n"
    )
    md.append(cycles_table_md(cycles_df))
    md.append("\n")

    md.append("## Headline comparison: all 5 assets × 9 signals (full history)\n\n")
    md.append(headline_table_md(headline_df))
    md.append("\nFull table: [`regime_switch_headline.csv`](regime_switch_headline.csv)\n\n")

    for k in ["GOLD_timeline", "SILVER_timeline", "yield_curve"]:
        if k in figs:
            md.append(f"![{k}]({figs[k]})\n\n")

    md.append("## Primary hypothesis test: gold & silver, 2001–2023 vs 2024+\n\n")
    md.append(
        "The **2001-2023 window predates** the 2024-2026 rally that motivated Strategy D in the first place, so "
        "it's the closest thing to a real out-of-sample test the available history allows. 2024+ is reported "
        "separately and explicitly **not treated as confirmation** (spec 15.6).\n\n"
    )
    md.append(period_table_md(period_df))
    md.append("\nFull table: [`regime_switch_periods.csv`](regime_switch_periods.csv)\n\n")

    md.append("## Per-cycle table (gold & silver, Combo and R2c signals)\n\n")
    md.append(percycle_summary_md(percycle_df))
    md.append("\nFull per-cycle detail: [`regime_switch_percycle.csv`](regime_switch_percycle.csv)\n\n")

    md.append("## Placebo tests\n\n")
    md.append("Real result's percentile within 300 circular-shifted placebo runs (higher = more likely real, not luck):\n\n")
    md.append("| Asset | Signal | Wealth percentile | Sharpe percentile |\n|---|---|---|---|\n")
    for asset, sigs in placebo_results.items():
        for sig, p in sigs.items():
            md.append(f"| {asset} | {sig} | {fmt_num(p['percentile_wealth'],1)} | {fmt_num(p['percentile_sharpe'],1)} |\n")
    md.append("\n")

    md.append("## Win condition verdict (spec §15.7, Primary gold+silver sample)\n\n")
    verdict_df = evaluate_win_condition(period_df, percycle_df, placebo_results)
    md.append("| Signal | Beats DCA & SmartDCA | Beats Control | Wins majority of hike cycles | Passes placebo guard | **WINS** |\n")
    md.append("|---|---|---|---|---|---|\n")
    n_family_pass = 0
    for _, r in verdict_df.iterrows():
        md.append(
            f"| {r['signal']} | {'✅' if r['beats_dca_and_smart'] else '❌'} | {'✅' if r['beats_control'] else '❌'} "
            f"| {'✅' if r['wins_majority_hike_cycles'] else '❌'} | {'✅' if r['passes_placebo_guard'] else '❌'} "
            f"| {'**YES**' if r['WINS'] else 'No'} |\n"
        )
    md.append("\n")
    any_win = bool(verdict_df["WINS"].any())
    md.append(
        f"**Individual-signal verdict:** {'at least one signal passes all four checks' if any_win else 'no individual signal passes all four checks'} "
        f"on the primary gold+silver sample.\n\n"
        "**Family-level check** (spec's alternative bar: at least half of the 8 rate signals land in the top 5% "
        "of their own placebo distribution, across gold+silver):\n\n"
    )
    family_hits = 0
    family_total = 0
    for asset in ["GOLD", "SILVER"]:
        for sig in ["R1", "R2a", "R2b", "R2b-inv", "R2c", "R3", "R4", "Combo"]:
            p = placebo_results.get(asset, {}).get(sig)
            if p:
                family_total += 1
                if p["percentile_wealth"] >= 95.0:
                    family_hits += 1
    md.append(f"- {family_hits} of {family_total} (asset × rate-signal) placebo results land in the top 5% on wealth "
               f"— {'clears' if family_total and family_hits/family_total >= 0.5 else 'does not clear'} the ≥50% family bar.\n\n")

    md.append("## Diagnostics\n\n")
    md.append("**Current signal readings (most recent week):**\n\n")
    md.append("| Asset | " + " | ".join(["R1", "R2a", "R2b", "R2b-inv", "R2c", "R3", "R4", "Combo", "Control"]) + " |\n")
    md.append("|---|" + "---|" * 9 + "\n")
    for asset, d in diag.items():
        cur = d["current_reading"]
        md.append(f"| {asset} | " + " | ".join("TIGHT" if cur.get(s) else "not" for s in
                   ["R1", "R2a", "R2b", "R2b-inv", "R2c", "R3", "R4", "Combo", "Control"]) + " |\n")
    md.append(
        "\n*(These are current readings as of the data pulled for this report, not a trading recommendation — "
        "spec 15.8.)*\n\n"
    )

    md.append("## Reproducing this report\n\n```bash\npython run_v2_regime_switch.py\n```\n")

    with open(os.path.join(REPORTS_DIR, "report_regime_switch.md"), "w") as f:
        f.write("".join(md))
