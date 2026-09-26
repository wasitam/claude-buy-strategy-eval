# Family 032: M2 money-supply growth regime switch

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Friedman, M. and Schwartz, A.J. (1963), *A Monetary History of the United
States, 1867-1960* — the foundational quantity-theory case that changes in
the money supply are a leading driver of nominal asset prices and economic
activity, with monetary expansion historically preceding periods of
asset-price inflation and monetary contraction preceding tightening/
liquidity-stress episodes. Contemporary practitioner and academic
attention to M2 specifically intensified around 2021-2023, when the
US experienced first the fastest M2 growth on record (2020-21 pandemic-
era expansion, partly mechanical from stimulus/QE) and then, in
2022-2023, the first sustained year-over-year *contraction* in M2 since
the Great Depression era — an event widely discussed in Fed and market
commentary (e.g. St. Louis Fed's own FRED blog and economist commentary,
various sell-side strategist notes) as a historically rare tightening-
liquidity signal. Seed queue item #32 (research-loop-plan-v3.md sec 7.3
replenishment; this iteration's task brief): "M2 money-supply growth
regime."

## Mechanism ("why would this work, and who is on the other side?")

M2 (currency, checking deposits, savings deposits, small time deposits and
retail money-market funds) is the broadest widely-tracked, free, monthly
measure of the quantity of money circulating in the economy. The
liquidity/monetary-quantity-channel story: when M2 growth is
**accelerating** relative to its own recent trend, more money is chasing
the same stock of financial and real assets, historically associated with
asset-price inflation and liquidity-driven rallies across risk assets
(equities, commodities) and especially inflation hedges such as gold.
When M2 growth is **decelerating or outright contracting** relative to
its own trend — a rare but historically notable event, most dramatically
the 2022-2023 M2 contraction — that signals tightening liquidity
conditions in the banking system, historically associated with weaker
forward returns as the flow of new money available to bid up asset prices
shrinks. This family bets that banking new deposits (rather than investing
them immediately) during a decelerating-M2-growth window, and deploying
with a capped catch-up lump once M2 growth reaccelerates relative to its
own trend, produces on average more favorable entry prices than investing
steadily through a liquidity-tightening window — the same banking/
cash-cap deposit-timing mechanic already used by families 004/006/007/
011/015/019/027 (bank now, catch-up lump later, cash-capped, never
leverage) applied here to a monetary-aggregate (quantity-of-money) signal
instead of a calendar, price, credit-spread, real-activity or policy-rate
signal. The "other side" of this trade is whoever continues to invest at
a steady pace through a liquidity-tightening window and is compensated
(in expectation) for bearing that risk — either an investor with no
access to or no belief in the M2 signal, or one who believes asset prices
already reflect the tightening and that trying to time around it forgoes
more upside (from being out of the market) than it saves.

## Category

**Regime switch (macro)** (research-loop-plan-v3.md sec 4.5's category
list; matches families 011/019/027's category label for the same
reason — a macro leading/coincident indicator regime signal driving a
banking/timing decision, no leverage or shorting).

## The fourfold macro-signal distinction (required by this iteration's
task brief; this loop now has 4 macro-regime families and each must be
shown to test something genuinely separate)

This loop has accumulated four macro regime-switch families. Each answers
a **categorically different question**, from a **genuinely different
data source**, with a **different transmission-mechanism story**:

1. **v2.1 Strategy D (sec 7.2 closed list — R1, R2a, R2b, R2b-inv, R2c,
   R3, R4, Combo, Control)** answers: *"is monetary POLICY tight or
   loose, and in which direction is it moving?"* Built entirely from
   **policy-rate and yield-curve data**: the Fed funds target midpoint
   (`DFEDTAR`/`DFEDTARU`/`DFEDTARL`), the 2-year Treasury yield relative
   to its own trailing mean (`DGS2`), the 10y-2y curve slope (`T10Y2Y`),
   10-year TIPS real yields (`DFII10`), and the FOMC dot-plot median
   (`FEDTARMD`). Transmission story: the **price of money** (short-term
   interest rates) set by central-bank action or expected central-bank
   action.

2. **Family 011 (credit-stress filter, already tested — REJECTED)**
   answers: *"how much compensation are corporate-bond investors
   demanding for default/liquidity risk right now, and how tight are
   financial conditions across money, credit, leverage and equity
   markets broadly?"* Built from **market-priced credit spreads and a
   financial-conditions index**: BAA−AAA corporate bond yields, or the
   Chicago Fed NFCI. Transmission story: the **market's own real-time
   pricing of credit and liquidity risk** across intermediaries and
   borrowers — a spread/risk-premium signal, not a quantity signal.

3. **Family 019 (OECD CLI regime, already tested — REJECTED)** answers:
   *"is the real economy's forward-looking activity trajectory — orders,
   permits, confidence, production-adjacent series — currently reading
   below or above its own trend?"* Built from a **real-economy composite
   leading-activity index**: `USALOLITONOSTSAM`. Transmission story: the
   **real side of the economy** (production, orders, sentiment) leading
   the business cycle, with money and credit only minor sub-components of
   the composite.

4. **Family 027 (yield-curve regime, already tested)** answers: *"does
   the shape of the Treasury yield curve (2s10s) indicate the bond market
   expects a future policy easing / recession?"* Built from **Treasury
   yield-curve shape**: `DGS2`, `DGS10` (or `T10Y2Y`). Transmission
   story: the **term structure of interest rates** and what it reveals
   about market expectations of future short-rate policy — a curve-shape
   signal, not a monetary-quantity signal, and not identical to Strategy
   D's level-of-policy-rate signals (a curve can invert with rates flat
   or falling, and vice versa).

5. **This family (M2 growth regime)** answers: *"is the quantity of
   money circulating in the economy — M2, the broadest widely-tracked
   monetary aggregate — growing faster or slower than its own recent
   trend?"* Built from **M2SL (FRED), a monetary aggregate: the actual
   stock of money (currency, checking/savings/small-time deposits, retail
   money funds)**, not a yield, not a spread, not a real-activity
   composite index, and not a policy-rate/curve-shape construction.
   `M2SL` contains none of `DFEDTAR(U/L)`, `DGS2`, `DGS10`, `T10Y2Y`,
   `DFII10`, `FEDTARMD`, `BAA`, `AAA`, `NFCI` or `USALOLITONOSTSAM` as
   inputs and is not derived from any of them. Transmission story: the
   **quantity-of-money / liquidity channel** (Friedman-Schwartz) — more or
   less money circulating, mechanically available to bid on financial and
   real assets — independent of what interest rates or credit spreads are
   doing at the same moment. Historically the two can and do diverge
   sharply: the Fed can hold the policy rate flat while M2 growth
   decelerates purely from the unwind of pandemic-era stimulus flows
   (2022-23, where M2 contracted even as Strategy D's rate-regime signals
   were reading a still-hiking/tightening-but-different-shaped policy
   path, and credit spreads (family 011) and the CLI (family 019) each
   moved on their own, only partially correlated timelines); conversely,
   M2 growth accelerated sharply in 2020-21 for reasons (pandemic fiscal
   transfers and QE-driven deposit creation) largely independent of the
   yield curve's shape or the OECD CLI's own then-collapsing reading
   during the same window (CLI fell sharply in the 2020 COVID shock while
   M2 growth was simultaneously *accelerating* — the clearest possible
   evidence these two signals are not proxies for one another).

**Summary table:**

| | v2.1 Strategy D | Family 011 | Family 019 | Family 027 | Family 032 (this) |
|---|---|---|---|---|---|
| Question answered | Is policy tight/loose? | Is credit/financial stress elevated? | Is real-economy leading activity below trend? | Does the curve shape signal future easing/recession? | Is the quantity of money growing faster or slower than trend? |
| Data type | Policy rates, yield curve level | Market-priced credit spreads, financial-conditions index | Real-economy composite leading-activity index | Treasury yield-curve shape (2s10s) | Monetary aggregate (quantity of money) |
| FRED series | DFEDTAR(U/L), DGS2, T10Y2Y, DFII10, FEDTARMD | BAA, AAA, NFCI | USALOLITONOSTSAM | DGS2, DGS10 / T10Y2Y | M2SL |
| Transmission channel | Price of money (policy rate) | Market pricing of default/liquidity risk | Real-economy activity cycle | Bond-market expectations of future policy | Quantity-of-money / liquidity channel |
| Revision character | FEDTARMD is ALFRED-vintaged; rate/curve series are not | Not revised (market prices) | Revised (ALFRED vintages from 2018-07 only) | Not revised (market yields) | Revised, but ALFRED vintages available back to **1980-02-08** (see below) |

This family's exact rule (a trailing-normalized threshold on the M2SL
year-over-year growth rate, banking deposits below it, deploying with
catch-up at/above it) is not a restatement, relabeling, or minor variant
of any rule in the sec 7.2 closed list or families 011/019/027's
already-tested rules — none of those families' signal construction
touches M2SL or any monetary-aggregate data at all.

## Single-asset scoping (judgment call, stated explicitly)

Following the precedent set by families 006/007/011/015/019/027 (a macro
signal that does not depend on which of the 5 core assets it is applied
to gets tested on all 5 core assets under sec 4.1's standard single-asset
>=3/5 rule, using the existing single-asset `engine.py`, rather than
narrowed to one asset), this family is assessed as a **single-asset
family across all 5 core assets**, independently per asset. M2 growth is
a US monetary-aggregate signal, not specific to any one of gold/silver/
oil/BTC/SP500 — the same "macro signal is asset-agnostic" reasoning
already used for families 006/007/011/015/019/027, and consistent with
gold specifically being one of the mechanism's own stated inflation-hedge
beneficiaries (the mechanism narrative in the task brief), which if
anything argues M2 should be tested broadly, not narrowed to gold alone.

## Exact rules

Computed at each week-end decision day `t` (same weekly cadence as every
other v3 family), using only the point-in-time M2 growth signal available
as of `t`'s close (see "Point-in-time / publication-lag discipline"
below) and the asset's own trading-day calendar/price for fills — the M2
signal itself never depends on the asset being traded.

1. **Point-in-time construction.** The raw FRED `M2SL` series (monthly,
   observation date = the 1st of the reference month) is shifted forward
   by a fixed conservative publication lag (see below) before any growth
   rate or normalization is computed, so every derived value "seen" on
   trading day `t` is built only from M2SL levels that had actually been
   published by `t`'s close.
2. **Growth rate.** At each (lagged) M2SL observation date, compute the
   year-over-year growth rate over a trailing `yoy_window_months` window:
   `g_i = M2SL[i] / M2SL[i - yoy_window_months] - 1` (both endpoints
   already point-in-time-lagged, so `g_i` itself requires no separate
   lag).
3. **Trend-relative normalization.** At each growth-rate observation,
   compute its z-score against its own trailing `lookback_years`-year
   window of prior growth-rate observations: `z_i = (g_i - trailing_mean)
   / trailing_std`.
4. **Threshold level** (`threshold_level`, an integer 0/1/2 selecting a
   z-score threshold, matching family 019's convention): thresholds by
   level `{0: -1.0, 1: -0.5, 2: 0.0}` standard deviations below the
   trailing-normalized mean growth rate.
5. **Regime.** **Decelerating** if `z_i < threshold`; otherwise
   **accelerating/normal**. Before enough history exists to fill both the
   `yoy_window_months` growth-rate lookback and the `lookback_years`
   normalization window, the regime defaults to **accelerating/normal**
   (behaves like plain DCA during signal warm-up — the same convention
   families 011/019 use).
6. **Weekly decision (week-end days only), no sells ever** (matching
   families 003/005/006/007/011/019/027's precedent — a pure
   timing/banking rule that never liquidates existing units, staying
   within the plan's no-leverage/no-shorting constraint by construction):
   - **Decelerating:** buy `decel_tilt_fraction * weekly_deposit`. The
     remainder is banked as cash (earning IRX, sec 3.2) until the regime
     next reads accelerating/normal.
   - **Accelerating/normal:** buy `min(cash, max_lump_multiple *
     weekly_deposit)` — this both makes the current week's normal deposit
     and, if there is banked cash from a prior decelerating stretch,
     deploys a capped catch-up lump, cash-capped so this can never become
     leverage.
7. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the signal/regime computation entirely and buys
   100% of that week's cash on every week-end day (0 otherwise) —
   reproduces plain DCA bit-for-bit, same pattern as every prior v3
   family's disable path. As families 010/011/019 flagged explicitly: a
   grid config with `decel_tilt_fraction=0` and `enabled=True` is **NOT**
   equivalent to DCA — the regime computation still runs. Only
   `enabled=False` is checked against the DCA baseline.

## Point-in-time / publication-lag discipline (sec 3.2 bullet 4)

**Data reachability, verified live before writing this pre-registration:**
`M2SL` is reachable via FRED's `fredgraph.csv` endpoint (the same
mechanism `fetch_fred_macro()` already uses for families 011/019/027).
It returns monthly observations from **1959-01-01** through the present
(812 rows as of this check) — ample coverage for every core asset's
development period, including BTC's short 2014-2019 window.

**Revision character:** `M2SL` **is** an ALFRED-vintaged (revisable)
series — the Fed does restate M2 history, for example on benchmark
revisions to component data or (rarely) definitional changes, though
historically less dramatically than survey/composite series like the
OECD CLI. Checked directly against ALFRED's own metadata page for this
series (`https://alfred.stlouisfed.org/series/downloaddata?seid=M2SL`),
mirroring how family 019 checked `USALOLITONOSTSAM`'s vintage coverage
and how `src/backtest/v2/regimes.py`'s R4 checks `FEDTARMD`'s vintage
list. **Finding:** ALFRED's page reports **"First Vintage: 1980-02-08"**
for `M2SL` — real vintage coverage starts materially earlier than family
019's OECD CLI series (which only had usable ALFRED vintages from
2018-07), but still leaves the **1959-1980** portion of this family's
development sample (SP500's dev history starts well before 1980) without
true vintage-by-vintage reconstruction available. Full vintage-by-vintage
backtesting (fetching each historical vintage and reconstructing exactly
what was known on each date) is not attempted here, for the same
time-budget reason families 011/019/027 did not attempt it — instead, a
fixed conservative publication lag stands in for the (partially
available) vintage history, exactly as those three prior macro families
did.
- **Publication lag.** The Fed's H.6 statistical release publishes each
  month's M2 figure roughly 3-5 weeks after month-end (e.g. January's M2
  level is typically released in late February). A **45-calendar-day**
  lag is applied from each observation date before the value becomes
  usable — the same conservative lag family 011 used for its monthly
  BAA/AAA series, and comfortably past the H.6 release's typical
  turnaround.
- **Known, honestly-flagged limitation** (same category family 019's
  prereg.md already flagged for its own series, and the plan already
  accepts for BTC's short development window, sec 5.1/sec 12): a fixed
  publication lag protects against look-ahead in *availability timing*
  but does not fully protect against look-ahead in the *value itself*
  being a later-revised (and possibly more informative-looking) figure
  than what would actually have been published in real time, for the
  pre-1980 portion of the sample where true ALFRED vintages are
  unavailable. Flagged here before any backtest is run, and will be
  repeated in results.md regardless of verdict.

## Pre-grid sanity checks (run before the grid, per this iteration's task
brief)

1. **Non-degeneracy:** the primary configuration's `decelerating`
   condition must fire non-trivially (not near-0%, not near-100% of dev
   days) on every core asset.
2. **Known-episode check, strictly within dev dates (pre-2020):** the
   primary configuration's growth-rate/z-score reading during the
   well-documented 2008-09 QE-era M2 acceleration (the Fed's
   post-Lehman balance-sheet expansion, roughly late 2008 through 2009)
   must read as **accelerating** (z at or above the decelerating
   threshold, i.e. NOT flagged "decelerating") — confirming the signal
   construction correctly identifies a real, well-known M2 regime shift
   before any grid result is trusted. This spot-check stays strictly
   within development dates (2008-09 is years before the 2020-01-01
   holdout cutoff) and is checked, never the reverse: the loop does not
   search for whichever episode happens to look best, it confirms the
   single episode named in the task brief itself.

## Data inputs

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only,
  same as every prior family).
- `M2SL` from FRED, via `src.backtest.v3.data.fetch_fred_macro("M2SL")`
  (the same helper families 011/019/027 already use — no new data-access
  code needed, keeping the `fredgraph.csv` raw-data-leak check's
  allowlist unchanged).

## Parameters (4 tunable + 1 fixed, all <=5 total)

| Parameter | Grid values | Primary |
|---|---|---|
| `yoy_window_months` | 6, 12 | 12 |
| `lookback_years` | 5, 10 | 10 |
| `threshold_level` | 0, 1, 2 | 1 |
| `decel_tilt_fraction` | 0.0, 0.25 | 0.0 |

`max_lump_multiple` is fixed at **6** for every grid config and the
primary (not varied in the grid) — the same value families 011/019 used
as their "headroom essentially never binds" setting, so the grid's 4
varied dimensions isolate the M2-growth signal's construction and
threshold rather than the catch-up cap. This keeps the family at 4
*tunable* (grid-varied) parameters plus 1 fixed constant, i.e.
**effectively 4 tunable parameters, comfortably under the plan's <=5
ceiling** (and even counting `max_lump_multiple` as a declared-but-fixed
5th parameter stays at the ceiling, not over it).

`yoy_window_months=12` is primary because the task brief's own mechanism
description names "trailing 12-month YoY % change" explicitly, and it is
the standard, most widely cited convention for "M2 growth rate" in both
academic and financial-press usage — a no-look choice based on the
brief's own wording and standard convention, not any development-data
result. `lookback_years=10` is primary as a business-cycle-length window
(long enough to span at least one full monetary cycle), matching families
011/019's own primary reasoning for the analogous parameter.
`threshold_level=1` (z < -0.5) is primary as the middle of the three
grid levels, matching family 019's own primary choice for the analogous
parameter. `decel_tilt_fraction=0.0` (full banking while decelerating)
is primary as the "purest" test of the timing-shift hypothesis, matching
families 006/007/011/019's own primary choice for the analogous
parameter.

## Grid

2 (`yoy_window_months`) x 2 (`lookback_years`) x 3 (`threshold_level`) x
2 (`decel_tilt_fraction`) = **24 configurations** (<=36 cap).

## Primary configuration

`yoy_window_months=12, lookback_years=10, threshold_level=1,
decel_tilt_fraction=0.0` (`max_lump_multiple=6` fixed for all configs).

## Expected sign

**Positive on both wealth and Sharpe, if the quantity-of-money/liquidity-
channel mechanism is real and its "buy after a liquidity tightening
resolves" logic survives this loop's fee/robustness bar** — stated
honestly as the family's central hypothesis, not a certainty. A genuine
risk flagged before any backtest, informed by families 003/005/006/007/
010/011/019/027's now-consistent pattern in this loop: like those
families, this mechanism only reallocates *timing* of a fixed deposit
stream (never total capital deployed, no leverage), so even a real effect
may show a small absolute wealth/Sharpe margin over DCA. A further risk
specific to this family: genuine M2 growth *deceleration* episodes are
rare in the pre-1980-2019 dev sample used here (most obviously the
2022-23 contraction is itself in the sealed holdout, unavailable to this
family entirely) — so, per family 027's own honestly-flagged caution
about "rare, clustered" macro regime signals, even a real effect risks
being a small-sample, few-dominant-episode result, exactly the class of
result sec 4.2's DSR and sec 4.3's placebo test are designed to catch,
and exactly the failure mode families 011/019/027 and 031 have each
already hit in this loop.
