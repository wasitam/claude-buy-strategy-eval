# BTC / Gold / Silver Accumulation Backtest — Spec v2.1

**Status:** Design approved. Go straight to data fetch → engine → strategies → benchmarks → metrics → robustness → report. Nothing below is open for redesign; parameter grids are fixed in advance on purpose (see §9).

**What changed in v2.1:** Adds **Strategy D (§15)**, a rate-regime switch that runs SmartDCA during monetary tightening and plain DCA otherwise. It was motivated by v2 results (summarized in §15.1). The yield-curve slope (10-year minus 2-year Treasury) is included as a market-expectations signal, as requested. Everything in §1–§14 is unchanged.

**What changed from v1:** v1 tested a buy-the-dip / trim-the-spike rule (percentile-ranked ATR shocks and trend stretch; buy $500 on dips, sell 30% on spikes). Result: **lower return, lower max drawdown, and lower Sharpe than plain DCA.** Diagnosis, consistent with the literature: (1) cash waiting for dips gave up return, and (2) trims after big up-weeks sold into momentum. v2 replaces it with three strategies from the literature that keep money invested and change *how much* or *where* to buy, rather than *whether* to be in the market.

---

## 1. Goal

Find out whether any of these beat plain weekly DCA for a long-term accumulator of BTC, gold and silver:

- **A. SmartDCA** — buy more when price is below its average, less when above.
- **B. Augmented DCA (ADCA)** — buy more in "expansion" regimes, less in "contraction" regimes.
- **C. Rebalanced portfolio** — hold BTC/gold/silver as one portfolio with target weights; direct deposits to the most underweight asset; sell only when a band is breached.

"Beat" is defined strictly in §8. Not financial advice; this is a research backtest.

---

## 2. Shared setup (applies to every strategy and benchmark)

### 2.1 Funding model — the key to a fair comparison

- Every strategy receives the **same deposit stream**: **$500 per week per asset** for single-asset tests (A, B, DCA), **$1,500 per week** for portfolio tests (C and its benchmarks).
- Deposits land in a **cash account**. Each strategy decides how much cash to invest.
- Uninvested cash earns the T-bill rate: weekly interest = `cash × (IRX / 100) / 52`, using the latest ^IRX close.
- **Final wealth = asset holdings + cash.** Money a strategy holds back still counts, and so does the return it missed.
- **No borrowing.** A buy is capped at available cash. Cash can never go negative.

### 2.2 Weekly event loop

For each week `t` (weeks end Friday, `W-FRI`):

1. At the close of week `t`: value the account, credit one week of interest on cash, then deposit this week's cash.
2. Compute all signals using data **up to and including the close of week `t` only**.
3. Generate orders.
4. Fill orders at the **open of week `t+1`**, with a **0.1% fee** on every trade. Process sells first, then buys; scale buys down if fees or price moves leave less cash than planned.

### 2.3 Weekly candles

Resample daily data to `W-FRI`: open = first daily open, high = max high, low = min low, close = last close. BTC trades on weekends; its Saturday/Sunday bars fall into the following week. That's fine as long as all assets use the same rule.

### 2.4 Warm-up

Skip the first **52 weeks** of each series so every indicator has full history. Strategy C3 and ADCA's asset-native variant need up to **156 weeks** (3 years) for some medians; use an expanding window until 156 weeks exist, with a minimum of 52.

---

## 3. Data

| Series | Source | Use |
|---|---|---|
| `BTC-USD` | Yahoo | BTC prices, from Sept 2014 |
| `GC=F` | Yahoo | Gold continuous futures, from ~2000 |
| `SI=F` | Yahoo | Silver continuous futures, from ~2000 |
| `^IRX` | Yahoo | 13-week T-bill rate (cash yield, Sharpe risk-free rate) |
| `^VIX` | Yahoo | ADCA regime vote |
| `UNRATE` | FRED | ADCA regime vote (monthly) |
| `TCU` | FRED | ADCA regime vote (monthly) |
| `DFEDTAR`, `DFEDTARU`, `DFEDTARL` | FRED | Strategy D, R1: Fed target (single target to Dec 2008, then range) |
| `DGS2`, `DGS10`, `T10Y2Y` | FRED | Strategy D, R2a–R2c: 2-year yield and 10y–2y curve slope, from 1976 |
| `DFII10` | FRED | Strategy D, R3: 10-year real yield (TIPS), from 2003 |
| `FEDTARMD` (all vintages) | ALFRED | Strategy D, R4: dot-plot median, from 2012 |

```python
import yfinance as yf
import pandas as pd

for name, t in {"BTC-USD": "BTC-USD", "GC_F": "GC=F", "SI_F": "SI=F",
                "IRX": "^IRX", "VIX": "^VIX"}.items():
    yf.Ticker(t).history(period="max", auto_adjust=False).to_csv(f"data/{name}.csv")

for sid in ["UNRATE", "TCU"]:
    pd.read_csv(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}").to_csv(f"data/{sid}.csv", index=False)
```

**FRED publication lag (no lookahead):** a monthly value for month `M` is released during month `M+1`. To be safe, treat month `M`'s value as available **from the first day of month `M+2`**, then forward-fill to weekly.

**Data hygiene:** drop rows with non-positive prices; flag single-week moves above 50% on gold/silver for manual inspection (Yahoo futures data occasionally has bad ticks); forward-fill ^IRX gaps.

**Historical note:** the claude.ai sandbox couldn't reach Yahoo (`403 Host not in allowlist`) even after allowlist changes. A normal coding environment shouldn't have that problem. If `yfinance` breaks, Yahoo's chart API is `https://query1.finance.yahoo.com/v8/finance/chart/{TICKER}?range=max&interval=1d`.

---

## 4. Strategy A — SmartDCA

**Source:** Calvet, Herranz-Celotti & Valimamode (2023), "SmartDCA superiority", arXiv:2308.05200. They prove that buying amounts inversely related to price always gives a lower average cost per unit than DCA. **Caveat:** in their own Bitcoin table, one variant beat DCA's return on money invested while spending about $516 vs DCA's $1,827. Lower cost per unit on less money is not more wealth. That's why §2.1's funding model matters.

**Adaptation:** the paper uses the first price in the series as the reference. That breaks for an asset like BTC that rose by orders of magnitude, so v2 uses a moving reference.

**Rules (per asset, run separately on BTC, gold, silver):**

```
MA52     = 52-week simple moving average of weekly closes (through week t)
mult     = min( (MA52 / close_t) ** rho , m_max )
buy_usd  = min( 500 * mult , cash_after_deposit )

if sweep_on:
    cap = 26 * 500                      # $13,000 = 26 weeks of deposits
    excess = (cash_after_deposit - buy_usd) - cap
    if excess > 0:
        buy_usd += excess

SELL: never.
```

**Grid (12 variants per asset):** `rho ∈ {1, 2, 3}` × `m_max ∈ {2, 3}` × `sweep ∈ {off, on}`.

**Sanity check:** `rho = 0` must reproduce plain DCA exactly.

---

## 5. Strategy B — Augmented DCA (ADCA)

**Source:** Kapalczynski & Lien (2021), "Effectiveness of Augmented Dollar-Cost Averaging", *North American Journal of Economics and Finance* 56. Their rule invests more aggressively when the economy is expanding and more conservatively when contracting, using market volatility, unemployment and capacity utilization. They found risk-reduction benefits in the US stock market (1967–2018). Note the direction: this is closer to trend-following than to dip-buying.

**Regime score:** each week, count the true votes (0–3).

*Variant B1 — Macro (faithful to the paper):*
1. `VIX_close_t < median(VIX weekly closes, trailing 52 weeks)`
2. `UNRATE_latest_available < mean(last 12 available UNRATE values)`
3. `TCU_latest_available > mean(last 12 available TCU values)`

*Variant B2 — Asset-native (same idea, using the asset's own data):*
1. `VIX_close_t < median(VIX, trailing 52 weeks)` (same as B1)
2. `vol26_t < median(vol26 over trailing 156 weeks)`, where `vol26` = std of weekly log returns over the last 26 weeks
3. `close_t > SMA40_t` (40-week simple moving average)

**Buy rule:**

```
C = cash_after_deposit

score == 3  (Aggressive):    buy_usd = min(C, 500 + 0.25 * (C - 500))
score == 2  (Neutral):       buy_usd = min(C, 500)
score <= 1  (Conservative):  buy_usd = min(C, 250)

SELL: never.
```

In aggressive mode, 25% of any accumulated reserve is deployed each week, so a reserve built up during contraction gets invested geometrically once conditions improve.

**Variants:** B1, B2 — per asset. **Sanity check:** forcing `score == 2` every week must reproduce plain DCA exactly.

---

## 6. Strategy C — Rebalanced BTC / gold / silver portfolio

**Sources:** Bouchey, Nemtchinov, Paulsen & Stein (2012), "Volatility Harvesting", *Journal of Wealth Management* — rebalancing volatile assets with correlation below 1 adds compounded growth. The 5/25 band rule is a common practitioner rule (Swedroe). The trend filter in C3 follows Faber's 10-month moving-average rule and Detzel et al.'s evidence on Bitcoin.

**Deposit:** $1,500 per week into the portfolio's cash account.

### 6.1 Target weights

- **C1 — Equal weight:** `w_BTC = w_gold = w_silver = 1/3`.
- **C2 — Inverse volatility:** `sigma_i` = std of weekly log returns over the trailing 52 weeks. `w_i = (1/sigma_i) / Σ_j (1/sigma_j)`. Recompute in the **first week of each month**; hold constant until the next recompute.
- **C3 — Inverse volatility + trend filter:** start from C2's weights. At each **month-end close**, for each asset: if `close < SMA40`, halve its weight; the freed weight goes to a **T-bill cash sleeve**. Restore the full weight at the first month-end close back above `SMA40`. `w_cash = 1 − Σ w_i'`. Any change to the targets triggers a full rebalance (§6.3).

### 6.2 Buy rule — every week (deposit routing)

```
for each sleeve i (assets, plus cash sleeve in C3):
    w_actual_i = value_i / total_portfolio_value (after deposit)
    rel_dev_i  = (w_actual_i - w_target_i) / w_target_i
target_sleeve = argmin(rel_dev_i)       # most underweight, relative terms
put the entire weekly deposit into target_sleeve
```

If the most underweight sleeve is the C3 cash sleeve, the deposit stays in cash that week.

### 6.3 Sell rule — band trigger (checked weekly at the close)

An asset **breaches** its band if either is true:

- `|w_actual − w_target| > 0.05` (5 percentage points absolute), **or**
- `|w_actual − w_target| / w_target > 0.25` (25% relative)

On any breach — or any target change in C3 — **rebalance every sleeve back to target at the next open**. Sell overweight assets first; use the proceeds (plus any cash) to buy underweight assets. Proceeds never sit in cash unless the target includes a cash sleeve.

### 6.4 Grid (fixed in advance)

| Weights | Rebalancing trigger | Trend filter |
|---|---|---|
| C1 equal / C2 inverse-vol | 5/25 bands (**primary**) | off |
| C1 / C2 | 10/50 bands | off |
| C1 / C2 | Calendar: first week of each quarter, no bands | off |
| C3 | 5/25 bands (**primary**) | on |

### 6.5 Periods

- **BTC + gold + silver:** from BTC's first date plus warm-up (~Sept 2015 onward).
- **Gold + silver only:** same rules with two assets, from ~2001, for long-history evidence.

---

## 7. Benchmarks

| Benchmark | Compared against | Rule |
|---|---|---|
| **DCA, single asset** | A and B | Invest the full $500 every week, immediately. With a weekly income stream, this *is* the lump-sum equivalent. |
| **Fixed-weight DCA, never rebalanced** | C | $1,500/week split by C's target weights at the time of deposit; never sell. Isolates what rebalancing adds. |
| **100% BTC DCA** | C | $1,500/week into BTC only. "Just hold the winner" reference. |
| **100% gold DCA, 100% silver DCA** | C | $1,500/week into one asset. |

---

## 8. Metrics and win condition (fixed before testing)

### 8.1 Unit-price (NAV) series — use for all risk metrics

Deposits distort raw account value, so compute a fund-style return series:

```
V_t  = account value at close of week t, before this week's deposit
D_t  = deposit made at close of week t
r_t  = V_t / (V_{t-1} + D_{t-1}) - 1
NAV_t = NAV_{t-1} * (1 + r_t),   NAV_0 = 1
```

### 8.2 Headline metrics

- **Final wealth** on identical deposits (primary)
- CAGR of NAV
- Annualized volatility: `std(r) * sqrt(52)`
- **Sharpe:** `mean(r − rf_weekly) / std(r − rf_weekly) * sqrt(52)`, with `rf_weekly = IRX/100/52`
- **Sortino:** same, using downside deviation
- **Max drawdown** of NAV, **longest time underwater**
- **Calmar:** CAGR ÷ |max drawdown|

### 8.3 Diagnostics (report, but don't use to pick winners)

- **Average cash share** of the account — measures cash drag directly
- Number of trades, turnover, total fees
- XIRR (money-weighted return)
- **Average cost per unit.** *Not* a win criterion: for SmartDCA it's lower by mathematical identity (Cauchy-Schwarz), regardless of whether wealth is higher. Show it next to final wealth to demonstrate why it misleads.

### 8.4 Win condition — a strategy "wins" only if all three hold

1. Beats its benchmark on **both final wealth and Sharpe** over the full sample.
2. Beats its benchmark in **more than 60% of rolling windows** (§9.1).
3. Passes the robustness tests (§9.2–9.3) — real result above the 95th percentile of placebo runs where applicable, and wins in a majority of bootstrap histories.

---

## 9. Robustness

### 9.1 Rolling windows

- BTC: every 2- and 3-year window, stepping 4 weeks.
- Gold, silver, gold+silver portfolio: every 3- and 5-year window, stepping 4 weeks.
- Named stress periods: BTC 2018 bear, BTC 2022 bear, BTC from the Oct 2025 peak through the >50% drawdown into mid-2026; metals 2011–2015 bear.
- Report % of windows beating the benchmark on wealth and on Sharpe.

### 9.2 Block bootstrap (1,000 alternate histories)

- Resample **4-week blocks with replacement** from weekly candles (as returns relative to the prior close, so OHLC can be rebuilt).
- Run twice: **as-is**, and **detrended** (subtract the mean weekly log return from every week, so there's no built-in uptrend).
- **For portfolio tests, draw the same calendar blocks for all assets together**, so cross-asset correlations are preserved.
- Macro inputs for ADCA B1 are resampled with the same blocks as the prices.
- Report the fraction of histories where the strategy beats its benchmark on wealth, Sharpe and max drawdown.

### 9.3 Placebo tests (1,000 runs)

- **ADCA:** randomly circular-shift the regime-score series in time. This keeps the same number of aggressive / neutral / conservative weeks but breaks any link to real conditions.
- **C3 trend filter:** randomly circular-shift the on/off trend series the same way.
- Report the real result's percentile within the placebo distribution.

### 9.4 Grids

Report every variant in every grid (§4, §5, §6.4). Do not pick a best variant after seeing results. A strategy family is credible only if it works across most of its grid, not at one setting.

---

## 10. Hypotheses (write down now, check later)

- **SmartDCA:** lower average cost per unit (guaranteed), but likely **lower** final wealth than DCA without the sweep, because of cash drag. The sweep variant should close most of the gap.
- **ADCA:** similar return to DCA with somewhat lower drawdown; the placebo test decides whether the regimes carry real information.
- **Rebalancing:** best chance to beat its fixed-weight benchmark on Sharpe and drawdown. Probably won't beat 100% BTC DCA on raw return over BTC's full history, since rebalancing keeps selling the biggest winner.

---

## 11. Implementation checks (must pass before trusting any result)

1. SmartDCA with `rho = 0` equals plain DCA to the cent.
2. ADCA with the score forced to 2 equals plain DCA to the cent.
3. Rebalancing with one asset at 100% weight equals plain DCA of $1,500/week.
4. Total deposits are identical across every strategy and benchmark in a test.
5. Cash is never negative; no position is ever negative.
6. **No-lookahead test:** randomly perturb all data after week `t`; every order generated at or before week `t` must be unchanged.
7. FRED values are used only from month `M+2` onward.

---

8. Strategy D with the regime forced to "DCA" every week equals plain DCA; forced to "SMART" every week equals the fixed SmartDCA variant (§15.4).
9. Dot-plot values at week `t` come only from ALFRED vintages released before week `t`'s close.

## 12. Suggested repo layout

```
data/                     raw CSVs
src/
  data.py                 fetch, clean, resample to W-FRI, FRED lag handling
  engine.py               weekly event loop, cash/interest, fills, fees
  strategies/
    dca.py                single-asset DCA, fixed-weight DCA
    smartdca.py           Strategy A
    adca.py               Strategy B (B1, B2)
    rebalance.py          Strategy C (C1, C2, C3)
    rate_switch.py        Strategy D (§15)
  regimes.py              rate-regime signals R1–R4, control, combo
  metrics.py              NAV series, all §8 metrics
  robustness.py           rolling windows, block bootstrap, placebo
  report.py               tables + charts
tests/                    §11 checks
report/                   output tables, charts, summary
```

---

## 13. Deliverables

1. **Results table:** every strategy variant × asset (or portfolio) × metric, next to its benchmark.
2. **Charts:**
   - Account value vs cumulative deposits vs benchmark, per strategy
   - NAV drawdown curves
   - SmartDCA / ADCA buy amounts over time, with price
   - Portfolio weights over time for C1–C3, with rebalance dates marked
   - Rolling-window win-rate summary
   - Bootstrap and placebo distributions, with the real result marked
   - Grid heatmaps
3. **Short written verdict** per strategy against the §8.4 win condition.
4. **Reusable code** so the whole study can be rerun on fresh data.

---

## 14. Reference summary

- **Vanguard (2023)**, "Cost averaging: Invest now or temporarily hold your cash?" — lump sum beat cost averaging about two-thirds of the time; cash on the sidelines gives up the risk premium.
- **He & Wang (2022)**, "Does Market Timing Beat Dollar Cost Averaging?", *Journal of Finance Issues* — with regular contributions, no borrowing and no selling, market-timing rules tend to deliver results similar to DCA.
- **Calvet et al. (2023)**, arXiv:2308.05200 — SmartDCA; lower cost per unit is proven, but total spend differs from DCA.
- **Kapalczynski & Lien (2021)** — Augmented DCA; risk-reduction benefits in US stocks.
- **Bouchey et al. (2012)** — volatility harvesting via rebalancing.
- **Detzel, Liu, Strauss, Zhou & Zhu** — price-to-moving-average ratios predicted Bitcoin returns; MA strategies improved Sharpe and cut drawdowns vs buy-and-hold in their early-era sample.
- **Harvey et al. (2018)**, "The Impact of Volatility Targeting" — volatility scaling improves Sharpe for risk assets and reduces extreme returns.
- **Hayley (value averaging critique)** — IRR is systematically biased in favor of buy-more-when-cheap strategies; why XIRR is diagnostic only.

---

## 15. Strategy D — Rate-regime switch: SmartDCA in tightening, DCA otherwise (added in v2.1)

### 15.1 Motivation: v2 findings

- **SmartDCA vs DCA with the trend left in:** almost never wins on gold or silver.
- **Detrended block bootstrap:** SmartDCA wins **64–70%** of alternate histories. The buy-more-below-trend mechanic works on the *shape* of price moves; it's the *drift* that overwhelms it, because SmartDCA spends most weeks underweighting an asset that keeps rising.
- **Rolling 3-year windows, by date:** the last 8 windows (ending 2024–2026, all overlapping the gold/silver rally) are **0% wins** on both metals. Earlier windows are mixed: gold **37%**, silver **53%** (roughly a coin flip). Caveat: overlapping windows share most of their data, so these are far fewer independent observations than the window counts suggest.
- **BTC:** SmartDCA fails regardless of window. Strategy D is aimed at gold and silver; BTC is run for reference only.

**Hypothesis:** SmartDCA wins when drift is low. Monetary tightening lowers the drift of non-yielding assets like gold and silver by raising the opportunity cost of holding them. So: **tightening → SmartDCA; otherwise → DCA.**

**Known risks, stated in advance:**
- Gold's inverse link to real yields partly broke after 2022 (gold rose while real yields rose, widely attributed to central bank buying). The rates-to-drift channel may be weaker now than history suggests.
- The hypothesis was formed after seeing 2024–2026. That period **cannot count as confirmation** (see §15.6).

**Context at time of writing (Sept 2026):** the Fed raised rates on 16 Sept 2026 to 3.75%–4.00%, its first hike since 2023, and the September dot plot points to further hikes. All signals below are expected to read "tightening" today. That is a current reading, not evidence.

### 15.2 Data and point-in-time rules

| Signal input | Series | Available from | Point-in-time rule |
|---|---|---|---|
| Fed target | `DFEDTAR` until 2008-12-15; then midpoint of `DFEDTARU` and `DFEDTARL` | 1982 | Known on announcement day |
| 2-year yield | `DGS2` | 1976 | Daily; use last value on or before Friday's close |
| 10-year yield | `DGS10` | 1962 | Same |
| Curve slope | `T10Y2Y` (= `DGS10 − DGS2`) | 1976 | Same |
| 10-year real yield | `DFII10` | 2003 | Same |
| Dot-plot median | `FEDTARMD`, **all vintages from ALFRED** | Jan 2012 | Each vintage usable from the trading day **after** its release |

**Dot-plot data warning:** FRED's `FEDTARMD` page shows only the latest release; each release overwrites the previous one. A backtest must use ALFRED vintages to see what the dot plot said at each past meeting. The `fredapi` Python package (free FRED API key) supports this via `get_series_all_releases("FEDTARMD")`.

Forward-fill all series to the weekly Friday grid. Never use a value dated after week `t`'s close.

### 15.3 Regime signals (computed weekly at Friday close)

Each signal outputs **TIGHT** or **NOT-TIGHT**. Only TIGHT switches to SmartDCA.

| ID | Signal | TIGHT when |
|---|---|---|
| **R1** | Fed funds direction | Target midpoint at week `t` > target midpoint 26 weeks earlier |
| **R2a** | 2-year yield trend | `DGS2_t` > mean of `DGS2` over the last 26 weeks |
| **R2b** | Curve slope, flattening (**primary slope rule**) | `slope_t` < mean of slope over the last 26 weeks |
| **R2b-inv** | Curve slope, inversion (secondary) | `slope_t` < 0 |
| **R2c** | Bear flattening | R2a is TIGHT **and** R2b is TIGHT (2-year rising while the curve flattens) |
| **R3** | Real yield trend | `DFII10_t` > mean of `DFII10` over the last 26 weeks |
| **R4** | Dot plot | Latest-vintage median projection for the **next calendar year-end** > current target midpoint |
| **Combo** | Majority vote | At least 3 of {R1, R2a, R2b, R3} are TIGHT |
| **Control** | Price only, no rates | Asset's 26-week log return < 0 |

**Why the slope signals are defined this way:**
- Hiking cycles typically produce **bear flattening**: the 2-year rises faster than the 10-year because it reflects near-term policy. Cutting cycles typically produce **bull steepening**. So flattening is used as a market-implied tightening signal.
- The slope alone is ambiguous. **Bear steepening** (10-year rising faster, e.g. on inflation or term-premium fears) reads NOT-TIGHT under R2b even though rates are rising. **Bull flattening** (10-year falling faster, e.g. on recession fears) reads TIGHT under R2b even though policy may be easing. **R2c** removes both cases by requiring the 2-year to be rising as well. R2a, R2b and R2c are tested separately so their differences are visible.
- Inversion (R2b-inv) is a late-cycle "policy is tight" state and often persists into the early part of cutting cycles, so it's expected to be a lagging signal. Included for completeness.

**Why the control exists:** the hypothesis is really "switch when drift is low." If a rate signal can't beat a switch driven by the asset's own recent returns, rates add nothing.

**Anti-whipsaw rule (all signals):** the regime changes only after **2 consecutive weeks** of the new reading.

### 15.4 Switching rule (per asset)

**State SMART (signal TIGHT):** SmartDCA with one fixed variant, chosen now and not re-picked later:
`rho = 2`, `m_max = 3`, sweep **on** (26-week cap). Rules as in §4.

**State DCA (signal NOT-TIGHT):**
- Invest $500 every week.
- On entering DCA state, record the cash reserve `R0` built up during SMART. Each week, invest an extra `R0 / 13` until `R0` is used up (13 weeks). Capped by available cash.

**Selling:** never, in either state.

**Funding, fills, fees, interest:** exactly as §2.

### 15.5 Benchmarks

Strategy D must be compared against all three:

1. **Plain DCA** — $500/week, always.
2. **Always-on SmartDCA** — the same fixed variant (`rho = 2`, `m_max = 3`, sweep on), every week.
3. **Control switch** — Strategy D using the Control signal instead of a rate signal.

### 15.6 Samples

| Sample | Period | Role |
|---|---|---|
| **Primary** | Gold & silver, 2001-01 → 2023-12 | The real test. Predates the observations that produced the hypothesis. |
| Primary, R3 | 2003-01 → 2023-12 | `DFII10` starts in 2003. |
| Primary, R4 | 2012-01 → 2023-12 | Dot plot starts in 2012. Few cycles: treat as suggestive only. |
| Secondary | 2024-01 → latest | Report separately, labeled **"hypothesis-forming period — not confirmation."** |
| Reference | BTC, 2015 → latest | For completeness; no strong expectation. |

### 15.7 Tests and win condition

**Per-cycle table (required):**
- Derive Fed cycles from R1's target series: a cycle starts at the first move in a new direction (hike after cuts/hold, cut after hikes/hold). Long holds at zero rates are their own "hold" rows.
- For each cycle, simulate Strategy D and plain DCA **from zero holdings at the cycle start** to the cycle end, and report the difference in final wealth and Sharpe.
- Expected rows since 2001 include roughly: easing 2001–03, tightening 2004–06, easing 2007–08, hold 2009–15, tightening 2015–18, easing 2019–20, hold 2020–22, tightening 2022–23, easing 2024–25, tightening 2026–. Derive them from data, don't hard-code them.

**Placebo:** for each signal, circular-shift its regime series by a random offset, 1,000 times. This keeps the same number and length of TIGHT periods but breaks their link to real rates. Report the real result's percentile.

**Multiple-testing guard:** eight rate signals are tested (R1, R2a, R2b, R2b-inv, R2c, R3, R4, Combo). With that many tries, one can pass at the usual 5% level by luck.
- A **single** signal counts as a pass only if it lands in the **top 0.6%** of its placebo runs (5% ÷ 8).
- Alternatively, the **rate-regime idea as a family** counts as supported if **at least half** of the signals land in their top 5%.

**A signal "wins" only if, in the primary sample, all of these hold:**
1. Beats plain DCA **and** always-on SmartDCA on **both** final wealth and Sharpe.
2. Beats the Control switch on final wealth.
3. Wins the majority of **tightening** cycles in the per-cycle table.
4. Passes the placebo test under the multiple-testing guard above.

### 15.8 Diagnostics

- Share of weeks each signal reads TIGHT, and pairwise agreement between signals.
- Average cash share and number of state switches per strategy.
- **Current reading of every signal at the latest date**, clearly labeled as a reading, not a result.

### 15.9 Deliverables (in addition to §13)

- Regime timeline chart: gold and silver prices with each signal's TIGHT periods shaded underneath, plus Fed cycle boundaries.
- 2-year yield, 10-year yield and slope on one chart, with bear-flattening periods (R2c) highlighted.
- Per-cycle table (§15.7).
- Placebo histograms per signal with the real result marked.
- One-paragraph verdict per signal against §15.7, and one for the family as a whole.

### 15.10 References for §15

- FRED / ALFRED series notes for `FEDTARMD`: dot-plot projections are the midpoint of each participant's projected year-end target range; ALFRED holds past vintages.
- Janus Henderson (June 2026), "What's behind the divergence between gold and real Treasury yields" — gold tracked real yields closely from the late 1990s to 2020; since 2022, central bank buying has lifted gold's baseline, though real yields still drive short-horizon direction.
- Federal Reserve, FOMC statement and implementation note, 16 Sept 2026 — target range raised to 3.75%–4.00%.
