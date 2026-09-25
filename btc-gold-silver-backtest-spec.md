# BTC / Gold / Silver Rule-Based Accumulation Backtest — Project Spec

Status: **Design fully approved. Nothing left to decide. Go straight to fetching data and building the backtest.**

This document is a complete handoff of a project scoped across a chat with Claude (claude.ai). It stalled only because the sandbox couldn't reach Yahoo Finance's domains — a coding environment with normal internet access should be able to proceed immediately.

---

## 1. Goal

Backtest a simple, rule-based weekly accumulation/trimming strategy on **BTC, Gold, and Silver**, for **long-term investing**. The buy/sell signal is for **cost and risk management**, not trading for profit — the investor accumulates over time regardless, the rule just tries to time individual purchases/trims a bit better than doing it on a fixed schedule.

Core question the whole project is designed to answer: **is this rule actually adding value, or would you get the same-looking result from any rule at all because BTC (and lately gold/silver) went up a lot?**

---

## 2. Core mechanics (agreed — do not re-litigate)

- Build **weekly candles** from daily OHLC (standard resample: week's open = first daily open, high = max daily high, low = min daily low, close = last daily close).
- **Buy $500** of the asset when a "crash-like" signal fires.
- **Sell 30% of current holdings** (not 30% of portfolio value in dollars — 30% of the coin/oz position) when a "spike-like" signal fires.
- Trades fill at **next week's open** — never the signal week itself. No lookahead, ever, at any stage of signal computation.
- **0.1% fee** per trade (buy or sell).
- Each asset (BTC, Gold, Silver) is backtested **independently**, starting from zero holdings.
- Cash raised from sells **earns the risk-free rate** (from ^IRX, 13-week T-bill) rather than sitting idle or funding future buys. This isolates the trading rule's effect instead of letting cash-drag or cash-reinvestment assumptions muddy the comparison.
- **Ignore taxes.**
- The $500 size is arbitrary and doesn't affect any percentage-based result — everything scales with it. Only the **signal parameters** and the **30% sell fraction** actually matter to the shape of the results.

---

## 3. Signal design — final version (the key design decision, evolved over the chat)

### 3.1 Where we started, and why we moved off it

Original idea: buy when a weekly candle drops **more than 3× ATR**, sell on the mirror image (14-week ATR).

Problems identified and agreed:
- A 3×-ATR weekly move is roughly a 5-standard-deviation event under normal-distribution math. Even accounting for fat tails, this would fire only a handful of times across an entire asset's history — too rare to evaluate, and possibly **zero signals** in a 2-year window.
- A fixed multiplier requires manual tuning per asset and goes stale as volatility regimes shift.
- Real-world evidence this staleness is a real problem: fixed-threshold cycle indicators for BTC — the **Mayer Multiple** (price ÷ 200-day MA, classic overbought line ~2.4×) and the **MVRV Z-Score** — both **failed to fire cleanly at BTC's actual October 2025 top** (~$126,198), ahead of a subsequent >50% drawdown into mid-2026. Their peak values have been shrinking cycle over cycle as the market matures, so a fixed line calibrated on old cycles increasingly misses new ones.

### 3.2 Final approach: percentile-of-own-distribution triggers

Instead of a fixed multiplier, express "how extreme is this" as **where it ranks in its own trailing distribution**, computed **causally** (only past data, rolling trailing lookback window, e.g. ~104 weeks / 2 years, expanding until that much history exists). This:

- Needs **no manual retuning** — it self-adjusts to each asset's own volatility regime over time.
- Lets you **directly control trade frequency** by picking a percentile (e.g. "bottom 5%" ≈ roughly 5% of weeks trigger a buy, by construction) instead of hoping a fixed multiplier happens to fire often enough.
- **Generalizes to any indicator** — build one generic engine (`indicator series in → buy/sell dates out`) and multiple indicator definitions can plug into it without touching the backtest engine itself. This was an explicit ask from the user: "now we can plug in any indicator to our system while keeping principle intact."

**Signal A — shock/crash detector (successor to the original ATR idea):**
- `normalized_move[t] = (close[t] - close[t-1]) / ATR_14w[t-1]` (use the **previous** week's ATR so the crash candle itself can't inflate the threshold that catches it).
- Buy when `normalized_move[t]` ranks in the **bottom p%** of its trailing distribution (last ~104 weeks, or expanding if not enough history yet).
- Sell when it ranks in the **top p%**.

**Signal B — trend-stretch detector (Mayer-Multiple / Faber-inspired):**
- `distance[t] = (close[t] - MA_40w[t]) / ATR_14w[t]` — distance from the ~200-day moving average, expressed in ATR units rather than raw price so it's comparable across regimes and assets.
- Buy when in the **bottom p%** of trailing distribution (deeply below trend — catches *slow grinding declines* that Signal A would miss, since a slow bleed rarely produces a single giant candle).
- Sell when in the **top p%** (deeply above trend).

**Parameter grid:** test `p ∈ {1, 2.5, 5, 10, 15}` for both signals, on all three assets. Report every result — no cherry-picking a single lucky combination. A rule only "counts" as good if it works broadly across this grid, not just at one setting.

### 3.3 Why Signal A alone isn't enough (research-grounded)

- Big weekly/monthly moves in commodities and crypto tend to **persist for 1–12 months before partially reversing**, not mean-revert immediately (Moskowitz/Ooi/Pedersen time-series momentum; Liu & Tsyvinski found the same pattern specifically in BTC — a stronger week tends to be followed by *more* upside the next week, not less).
- Caporale & Plastun found statistical overreaction patterns in crypto, but a rule that bets on the reversal of those overreactions was **not profitable** in their tests.
- Practical implication: **selling 30% right after a huge up-week risks selling into a rally that keeps running.** This is exactly the kind of thing the robustness tests below are designed to catch.
- Faber's 10-month/40-week moving-average trend filter, in his published backtest, cut max drawdown sharply (roughly 46% → under 10% in the classic example) while keeping competitive returns — this is the direct inspiration for Signal B and for using a trend-stretch measure alongside a pure shock measure.

---

## 4. Data

| Ticker | Purpose | Expected history |
|---|---|---|
| `BTC-USD` | Bitcoin daily OHLC | since ~Sept 2014 |
| `GC=F` | Gold continuous futures daily OHLC | since ~2000 |
| `SI=F` | Silver continuous futures daily OHLC | since ~2000 |
| `^IRX` | 13-week T-bill rate (risk-free rate, cash yield) | long history |

Fetch via `yfinance`:

```python
import yfinance as yf

tickers = {
    "BTC-USD": "BTC-USD",
    "GC_F": "GC=F",
    "SI_F": "SI=F",
    "IRX": "^IRX",
}

data = {}
for name, ticker in tickers.items():
    df = yf.Ticker(ticker).history(period="max", auto_adjust=False)
    df.to_csv(f"{name}.csv")
    data[name] = df
    print(name, len(df), df.index.min(), df.index.max())
```

**Known blocker (why this project stalled in the claude.ai chat):** the claude.ai code-execution sandbox could not reach `query1.finance.yahoo.com` / `query2.finance.yahoo.com` / `fc.yahoo.com`, returning `HTTP Error 403: Host not in allowlist`, even after:
- adding those three domains explicitly under Settings → Capabilities → Additional allowed domains, and
- switching the allowlist mode to "All domains" entirely,
— both **mid-session**, in the same conversation and in a fresh conversation. The error was byte-for-byte identical every time, which strongly suggests the sandbox's network egress permissions are fixed as a token/config at **session start** and don't pick up settings changes made afterward, rather than the specific domains being the issue. **A normal coding environment (this one) with standard internet access should not hit this at all** — this note is just so you don't waste time assuming there's something wrong with the tickers or the allowlist domains themselves.

If for some reason `yfinance` itself has issues (rate limiting, crumb/cookie auth changes — it's had breaking changes before), fall back to Yahoo's chart API directly:
`https://query1.finance.yahoo.com/v8/finance/chart/{TICKER}?range=max&interval=1d`

---

## 5. Benchmarks

Every benchmark is funded with **the same total dollars** the signal strategy actually deployed, so comparisons are apples-to-apples:

1. **DCA** — total dollars spread evenly across every week in the period.
2. **Buy-and-hold** — all dollars invested on day one.
3. **Buy-only variant of Signal A/B** — same buy rule, no sells at all. Isolates whether the 30%-sell rule is actually helping or just adding noise/cost.
4. **Rebalancing-band strategy** — hold a target % allocation in the asset vs. cash; trade only when actual weight drifts past a band (Vanguard-style: e.g. ~200bps trigger band, rebalance back to a ~175bps destination rather than exactly to target, per their published research showing no single "optimal" threshold but band-based beating pure calendar-based rebalancing). Set the target weight equal to the signal strategy's own **average invested fraction** over the backtest, so it's a fair comparison rather than an arbitrary target.

---

## 6. Metrics

**Lead with:**
- **Ending wealth ÷ total money invested**, on matched budgets across all strategies/benchmarks. This is the primary headline number.

**Secondary:**
- **XIRR** (money-weighted annualized return) — compute it, but don't lead with it. Value Averaging research shows IRR-style metrics can be **systematically biased in favor of buy-more-when-cheap strategies** without that bias reflecting real extra profit — same trap could apply here, so treat XIRR as informative, not authoritative.

**Risk:**
- Max drawdown, computed on a **synthetic NAV/unit-price basis** (like a fund's unit price) so new deposits can't mask real losses or manufacture fake "recoveries."
- Longest time underwater.
- Max underwater vs. money-in (peak-to-trough of `value - cumulative invested`).
- Annualized volatility.

**Risk-adjusted:**
- Sharpe, Sortino (downside-only), Calmar (annual return ÷ max drawdown).

**Cost management (this is the part the user actually cares about most, since the strategy's purpose is cost/risk management, not alpha):**
- Average cost basis of the signal strategy vs. DCA's average cost basis.

**Signal quality (does the signal actually contain information?):**
- Average forward returns at 1/3/6/12 months after every buy signal and every sell signal, compared against the asset's **unconditional** average return over the same horizons. This is the most direct test of whether there's any real edge at all, independent of the backtest's overall P&L.

---

## 7. Robustness tests (all three required — this was the user's original concern and is the heart of the project)

The user's own stated worry: *"BTC rose a lot lately, it can be easy to get a good win despite bad strategy."* All three tests below exist to answer that directly.

1. **Random-timing Monte Carlo.** Keep real prices. Place the **same number of buys and sells** as the real strategy, but on **randomly chosen weeks**, repeated 1,000 times. Report what percentile the real strategy's return / drawdown / Sharpe falls at versus this random distribution. Unless the real strategy beats something like 95% of random-timing runs, its results are coming from the market's overall rise, not from the signal. **This is the single most important test in the whole project.**

2. **Block-bootstrap shuffled histories.** Resample **month-long chunks** of the real weekly candle series **with replacement** to build 1,000 alternate price histories (some end up more bullish than actual history, some more bearish, since resampling with replacement can repeat a bad month multiple times or skip it entirely). Run the strategy vs. DCA on each alternate history and report the win rate on return, drawdown, and Sharpe. Do this once as-is, and once with the average per-period trend removed from the chunks first (de-trended), to separate "the rule exploits genuine crash/rebound structure" from "the rule just rides whatever trend is present."
   - **Important implementation note the user flagged and we corrected:** naively shuffling the *order* of months does **not** create a meaningful test, because total compounded return is order-independent under multiplication — shuffling order alone won't remove BTC's overall trend. **Resampling with replacement** (so some months can repeat or vanish) is what actually creates varied alternate histories, and is the version to implement.

3. **Rolling windows.** Every **2-year window** for BTC; every **3-year and 5-year window** for gold and silver. Report the % of windows where the rule beats DCA on return/drawdown/Sharpe. Explicitly call out as named stress tests:
   - BTC's 2018 bear market and 2022 bear market,
   - Gold/silver's 2011–2015 bear market,
   - **The most recent 2 years for BTC specifically** — this window already contains both the Oct 2025 ATH (~$126,198) and the subsequent >50% drawdown, so it's a genuine up-and-down test of the rule, not just "did it ride a bull run."
   - Caveat to report alongside this: a window with only one or two trade signals in it is an anecdote, not evidence — flag low-signal-count windows rather than treating them as equally informative.

Also worth testing (secondary, time permitting): sensitivity of results to the 30% sell fraction (grid it 10%–50%) and to higher trading fees, to check the rule isn't fragile to small parameter changes.

---

## 8. Research grounding (for context — don't need to re-derive any of this)

- **Maggiulli, "Even God Couldn't Beat Dollar-Cost Averaging"** — an investor who perfectly timed every dip bottom between all-time highs still lost to plain monthly DCA in over 70% of 40-year rolling US-stock windows. This is the bar the strategy needs to clear; "makes money" is not sufic.
- **Moskowitz, Ooi & Pedersen — time-series momentum** — returns persist 1–12 months before partially reversing across 58 futures markets including commodities (a later replication found the commodity-specific effect weaker post-2009 — worth checking against the actual gold/silver backtest window).
- **Liu & Tsyvinski, "Risks and Returns of Cryptocurrency"** — BTC shows weekly time-series momentum: a stronger week tends to be followed by continued strength, not reversal.
- **Caporale & Plastun** — crypto shows statistical overreaction on extreme days, but betting on the reversal wasn't profitable in their tests; betting on continuation was no better than random either.
- **Faber, "A Quantitative Approach to Tactical Asset Allocation"** — a 10-month/40-week moving-average trend filter cut drawdowns sharply while keeping competitive returns. Basis for Signal B.
- **Mayer Multiple / MVRV Z-Score** — useful concepts, but fixed-threshold versions go stale as market structure evolves; both failed to cleanly flag BTC's actual October 2025 top. Direct justification for using percentile-of-own-distribution instead of fixed levels everywhere in this system.
- **Parkinson / Garman-Klass / Yang-Zhang volatility estimators** — high-low-range-based volatility measures are ~5–14× more statistically efficient than close-to-close. Not required for v1 (which uses standard ATR), but a natural refinement later.
- **Vanguard rebalancing research** — no single "optimal" rebalancing threshold or frequency exists, but band-based rebalancing modestly outperforms pure calendar-based rebalancing. Basis for the rebalancing-band benchmark.
- **Edleson / Value Averaging critique** — VA's apparently superior IRR is largely a measurement artifact of how IRR treats buy-more-when-cheap cash flow timing, not necessarily real extra profit. Reason XIRR is treated as secondary, not primary, in this project's metrics.

---

## 9. Deliverables

1. Headline metrics table per asset × per signal × per parameter (p-grid) — in-chat or in whatever output format the coding session naturally produces.
2. A report with charts:
   - price with buy/sell markers,
   - account value vs. money-in vs. DCA,
   - drawdown curves,
   - random-timing Monte Carlo distribution (with real strategy's position marked),
   - block-bootstrap win-rate results,
   - rolling-window win-rate summary,
   - a heatmap of results across the (signal × p × asset) parameter grid.
3. The full, reusable Python script/notebook, so this can be rerun later on fresh data without rebuilding it from scratch.

---

## 10. Status

Design is fully approved by the user across multiple rounds of discussion in the source chat. **Nothing about the strategy, signals, benchmarks, metrics, or robustness tests remains to be decided.** The only blocker was sandbox network access to Yahoo Finance, which a normal coding session should not have. Proceed straight to data fetch → weekly candle construction → generic percentile signal engine → backtest engine → benchmarks → metrics → robustness tests → charts/report.
