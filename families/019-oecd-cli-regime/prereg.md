# Family 019: OECD Composite Leading Indicator (CLI) regime switch

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

OECD Composite Leading Indicators (CLI) methodology — the OECD's
long-running, internationally standardized leading-indicator program,
built from a country-specific basket of series (orders, permits,
confidence surveys, interest-rate spreads, stock prices, etc.), each
detrended and amplitude-adjusted, then combined and normalized to a
long-term trend of 100. The CLI is explicitly designed and published to
turn ahead of the real-economy business cycle by design, and is widely
cited in both academic and central-bank/OECD practitioner literature
(e.g. OECD *Main Economic Indicators*, Nilsson & Guidetti (OECD, 2008)
*Predicting the business cycle: how good are early estimates?*) as a
leading indicator of turning points in industrial production and broader
real economic activity, ahead of most financial-market indicators.
US series used here: FRED `USALOLITONOSTSAM` — "Leading Indicators OECD:
Component series: BUS: Composite Leading Indicator: Normalised, Same
Period Previous Year Growth Rate: Total for United States" family, in
practice FRED's mirror of the OECD's normalized (trend-restored, mean
100) CLI level for the US, monthly. Seed queue item #19
(research-loop-plan-v3.md sec 7.3 replenishment; this iteration's task
brief).

## Mechanism ("why would this work, and who is on the other side?")

The CLI is a real-economy, leading composite of forward-looking business
and consumer signals (new orders, permits, confidence, spreads, and other
components), constructed specifically to move ahead of the actual
industrial-production/GDP cycle by several months. When the normalized
CLI reads persistently below its own trailing-normalized level (a
below-trend reading, itself already a leading indicator of a future
economic slowdown or recession), that is information that a recession or
growth slowdown is more likely on the horizon over which the CLI has
historically led activity — a period in which risk assets have, on
average, historically faced more downside volatility and drawdown risk
before any recovery becomes visible in the CLI itself. This family bets
that avoiding *concentrating new deposits* into that below-trend window
and redeploying the banked cash once the CLI recovers to/above its own
trailing-normalized threshold produces, on average, more favorable entry
prices than deploying steadily through the weak window — the same
"bank now, deploy the catch-up once conditions normalize" logic already
used by families 004/006/007/011/015, applied here to a leading real-
economy-activity signal instead of a calendar, price, or financial-
conditions signal. No leverage, no shorting, no external capital: this
is purely a **timing reallocation** of the same fixed weekly deposit
stream. The "other side" of this trade is whoever is willing to buy at
average pace right through a period the CLI is flagging as weakening —
either an investor with no access to (or no belief in) this leading
signal, or one who believes valuations at that point in the cycle already
price in the coming slowdown and prefers not to try to time around it.

## Category

**Regime switch (macro)** (research-loop-plan-v3.md sec 4.5's category
list; the task brief's own label for this idea).

## The triple distinction (required by this iteration's task; a reviewer
would ask)

Three macro regime-switch signals now exist or are being added in this
loop, and each answers a **categorically different question** from a
**genuinely different data source**:

1. **v2.1 Strategy D (sec 7.2 closed list — R1, R2a, R2b, R2b-inv, R2c,
   R3, R4, Combo, Control)** answers: *"is monetary policy tight or
   loose, and in which direction is it moving?"* Built entirely from
   **policy-rate and yield-curve data**: the Fed funds target midpoint
   (`DFEDTAR`/`DFEDTARU`/`DFEDTARL`), the 2-year Treasury yield relative
   to its own trailing mean (`DGS2`), the 10y-2y curve slope (`T10Y2Y`),
   10-year TIPS real yields (`DFII10`), and the FOMC dot-plot median
   (`FEDTARMD`). This is a **policy-stance** signal — it reflects what
   the central bank is doing (or is expected to do) to short-term rates,
   not what is happening in the real economy or in credit markets.

2. **Family 011 (credit-stress filter, already tested — REJECTED)**
   answers: *"how much compensation are corporate-bond investors
   demanding for default/liquidity risk right now, and how tight are
   financial conditions across money, credit, leverage and equity
   markets broadly?"* Built from **market-priced credit spreads and a
   financial-conditions index**: BAA−AAA corporate bond yields, or the
   Chicago Fed NFCI. This is a **financial-market-stress** signal — it
   reflects how bond and money markets are currently pricing risk, which
   can diverge sharply from both the real economy (credit spreads can
   blow out on pure liquidity/technical stress with no accompanying
   activity slowdown, e.g. some 2011, 2015-16 episodes) and from policy
   (the Fed can be cutting, i.e. R1/R2a reading "loose", while credit
   spreads are simultaneously blowing out, e.g. early 2007-08 — the two
   signal families have frequently diverged historically, which is the
   clearest evidence they are not proxies for one another).

3. **This family (OECD CLI regime)** answers: *"is the real economy's
   forward-looking activity trajectory — orders, permits, confidence,
   production-adjacent series, combined and normalized by the OECD's own
   established methodology — currently reading below or above its own
   trend?"* Built from a **real-economy composite leading-activity
   index**: `USALOLITONOSTSAM`, which contains none of BAA, AAA, NFCI,
   DFEDTAR/U/L, DGS2, T10Y2Y, DFII10 or FEDTARMD as inputs, is not a
   market price and is not a policy-rate series at all. Its components
   (new orders, building permits, consumer/business confidence surveys,
   equity prices as one minor sub-component, interest-rate spreads as
   another minor sub-component) are combined by the OECD specifically to
   proxy the **real production/activity cycle**, not financial
   conditions or monetary policy. Historically the CLI and credit
   spreads can and do diverge (the CLI is designed to lead the *real*
   cycle by ~6-9 months; credit-spread blowouts are frequently sudden,
   liquidity-driven, and can occur with little advance CLI deterioration,
   e.g. 1998 LTCM, parts of 2011); and the CLI is constructed from
   real-activity components with only a minor interest-rate/financial
   sub-component, unlike Strategy D's rate signals which are pure
   monetary-policy/yield-curve constructions.

**Summary table:**

| | v2.1 Strategy D | Family 011 | Family 019 (this) |
|---|---|---|---|
| Question answered | Is policy tight/loose? | Is credit/financial stress elevated? | Is real-economy leading activity below trend? |
| Data type | Policy rates, yield curve | Market-priced credit spreads, financial-conditions index | Real-economy composite leading-activity index |
| FRED series | DFEDTAR(U/L), DGS2, T10Y2Y, DFII10, FEDTARMD | BAA, AAA, NFCI | USALOLITONOSTSAM |
| Construction | Central-bank action / bond-market-implied policy path | Corporate-bond yield spread / ~100-input financial stress index | OECD-standardized, detrended & amplitude-adjusted composite of orders, permits, confidence, minor spread/equity inputs |
| Revision character | FEDTARMD is ALFRED-vintaged (dot plot); rate/curve series are not revised | Not revised (market prices / published yields) | **Revised** (this family's key data-handling difference — see below) |

This family's exact rule (a trailing-normalized threshold on
`USALOLITONOSTSAM`, banking deposits below it, deploying with catch-up
at/above it) is not a restatement, relabeling, or minor variant of any
rule in either the sec 7.2 closed list or family 011's already-tested
rules — none of those families' signal construction touches OECD CLI
data at all.

## Single-asset scoping (judgment call, stated explicitly)

Following the precedent set by families 006/007/011/015 (a macro or
calendar signal that does not depend on which of the 5 core assets it is
applied to gets tested on all 5 core assets under sec 4.1's standard
single-asset >=3/5 rule, using the existing single-asset `engine.py`,
rather than narrowed to one asset), this family is assessed as a
**single-asset family across all 5 core assets**, independently per
asset. The CLI is a US real-economy activity signal, not specific to any
one of gold/silver/oil/BTC/SP500 — the same "macro signal is
asset-agnostic" reasoning already used for families 006/007/011/015.

## Exact rules

Computed at each week-end decision day `t` (same weekly cadence as every
other v3 family), using only the point-in-time CLI value available as of
`t`'s close (see "Point-in-time / publication-lag discipline" below) and
the asset's own trading-day calendar/price for fills — the CLI signal
itself never depends on the asset being traded.

1. **Point-in-time construction.** The raw FRED `USALOLITONOSTSAM` series
   (monthly, observation date = the 1st of the reference month) is shifted
   forward by a fixed conservative publication lag (see below) before
   being forward-filled onto the asset's daily trading-day index, so the
   value "seen" on trading day `t` is only ever a value that had actually
   been published by `t`'s close.
2. **Normalization** (`normalization_method`):
   - `"zscore"`: at each week-end day `t`, compute
     `z_t = (CLI_t - trailing_mean) / trailing_std`, both trailing
     moments over the point-in-time signal's own observation dates in a
     trailing `lookback_years` window.
   - `"percentile"`: compute the point-in-time signal's percentile rank
     within the same trailing `lookback_years` window (purely
     backward-looking, expanding-until-full, `MIN_PERIODS` = the window
     length — same convention as family 011's percentile-rank
     construction).
3. **Threshold level** (`threshold_level`, an integer 0/1/2 selecting a
   method-specific numeric threshold, so a single grid dimension can vary
   both methods' strictness consistently):
   - `zscore` thresholds by level: `{0: -1.0, 1: -0.5, 2: 0.0}` (standard
     deviations below the trailing-normalized mean).
   - `percentile` thresholds by level: `{0: 20, 1: 30, 2: 40}` (percentile
     rank within the trailing window).
4. **Regime.** **Weak** if the normalized signal is *below* its
   threshold (`z_t < threshold` for zscore, or `pctile_t < threshold` for
   percentile); otherwise **strong**. Before enough history exists to
   fill the lookback window, the regime defaults to **strong** (behaves
   like plain DCA during signal warm-up — the same convention family 011
   uses).
5. **Weekly decision (week-end days only), no sells ever** (matching
   families 003/005/006/007/011's precedent — a pure timing/banking rule
   that never liquidates existing units, staying within the plan's
   no-leverage/no-shorting constraint by construction):
   - **Weak:** buy `weak_tilt_fraction * weekly_deposit`. The remainder
     is banked as cash (earning IRX, sec 3.2) until the regime next reads
     strong.
   - **Strong:** buy `min(cash, max_lump_multiple * weekly_deposit)` —
     this both makes the current week's normal deposit and, if there is
     banked cash from a prior weak stretch, deploys a capped catch-up
     lump, cash-capped so this can never become leverage.
6. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the signal/regime computation entirely and buys
   100% of that week's cash on every week-end day (0 otherwise) —
   reproduces plain DCA bit-for-bit, same pattern as every prior v3
   family's disable path. As family 010/011 flagged explicitly: a grid
   config with `weak_tilt_fraction=0` and `enabled=True` is **NOT**
   equivalent to DCA — the regime computation still runs and could in
   principle mark historical weeks weak even near the mildest threshold.
   Only `enabled=False` is checked against the DCA baseline.

## Point-in-time / publication-lag discipline (sec 3.2 bullet 4)

**Data reachability, verified live before writing this pre-registration:**
`USALOLITONOSTSAM` is reachable via FRED's `fredgraph.csv` endpoint (the
same mechanism `fetch_fred_macro()` already uses for family 011's BAA/AAA/
NFCI series). It returns monthly observations from **1955-01-01** through
**2024-01-01** (829 rows) — ample coverage for every core asset's
development period, including BTC's short 2014-2019 window. No
substitution was needed (contrast with family 008's precedent, which the
task brief flagged as the fallback pattern if this series had been
blocked).

**Revision character — this is the substantive difference from family
011's BAA/AAA/NFCI series, and the reason this family's data handling
gets extra scrutiny per the task brief:**
- `USALOLITONOSTSAM` **is** an ALFRED-vintaged (revisable) series — the
  OECD/FRED do restate CLI history as later source data (permits,
  orders, confidence surveys) revises and as the detrending/amplitude-
  adjustment recomputes with a longer sample. This was checked directly
  against ALFRED's real vintage list for this series
  (`https://alfred.stlouisfed.org/series/downloaddata?seid=USALOLITONOSTSAM`),
  mirroring exactly how `src/backtest/v2/regimes.py`'s R4 (`FEDTARMD` dot
  plot) checks its own vintage list before using it.
- **Finding (documented honestly, the same way `regimes.py`'s own R4
  docstring documents FEDTARMD's vintage-coverage gap):** ALFRED's
  vintage history for `USALOLITONOSTSAM` only goes back to
  **2018-07-17** in practice (62 vintages, 2018-07-17 through
  2025-11-17) — nowhere near covering this family's development period
  (each core asset's start of history through 2019-12-31, i.e.
  1955/1968/2014 through 2019 depending on the asset). True
  vintage-by-vintage point-in-time reconstruction, the way R4 does for
  `FEDTARMD` post-2015-12-16, is therefore **not usable** for the bulk of
  this family's development sample, exactly the same kind of
  data-availability wall `regimes.py`'s own docstring calls out for R4.
- **Resolution (the same choice family 011 made for BAA/AAA, applied
  here for the same underlying reason — a conservative fixed lag
  standing in for unavailable full vintage history):** a fixed
  **60-calendar-day** publication lag is applied from each observation
  date before the value becomes usable, deliberately more conservative
  than family 011's 45-day BAA/AAA lag and matching the OECD's own
  documented release schedule (CLI data for month *M* is typically
  released by the OECD in the first half of month *M*+2, i.e. roughly
  5-6 weeks after month-end; 60 days is a safety margin on top of that
  schedule, guarding against both slow releases and the fact that this
  family cannot fully model revision risk with a fixed lag alone — see
  the caveat immediately below).
- **Known, honestly-flagged limitation:** a fixed publication lag
  protects against *look-ahead in availability timing* (the value used
  on trading day `t` was not yet published as of `t`, under the
  documented schedule) but does **not** fully protect against
  *look-ahead in the value itself* being a later-revised (and therefore
  more informative-looking) figure than what would actually have been
  published in real time, for the pre-2018-07 portion of the sample
  where true ALFRED vintages are unavailable. This is the same category
  of honestly-disclosed weakness the plan already accepts for BTC's short
  development window (sec 5.1, sec 12) — flagged here before any
  backtest is run, not discovered afterward, and will be repeated in
  results.md regardless of verdict.
- The lagged series is then forward-filled onto the asset's daily trading
  index (`.reindex(daily_index, method="ffill")` after the lag shift),
  mirroring family 011's `_lagged_pointintime()` -> reindex -> ffill
  pattern exactly.
- Verified by the standard no-lookahead implementation check (perturbing
  asset price data), plus the same macro-specific extra check family 011
  introduced: recomputing the regime with the lag shortened to 0 days
  must produce a *different* regime reading than the documented 60-day
  lag on at least some historical dates, proving the lag is doing
  something real (not a no-op), while every real backtest below uses the
  documented 60-day lag only.

## Data inputs

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only,
  same as every prior family).
- `USALOLITONOSTSAM` from FRED, via the existing
  `src.backtest.v3.data.fetch_fred_macro(series_id)` helper (no changes
  to `data.py` needed — this is the same gated entry point family 011
  already uses, so the raw-data-leak static check's allowlist stays
  accurate with no edits).

## Parameters (4 tunable, comfortably under the plan's <=5 ceiling)

| Parameter | Grid values | Primary |
|---|---|---|
| `normalization_method` | `zscore`, `percentile` | `zscore` |
| `lookback_years` | 5, 10 | 10 |
| `threshold_level` | 0, 1, 2 | 1 |
| `weak_tilt_fraction` | 0.0, 0.25 | 0.0 |

`max_lump_multiple` is fixed at **6** for every grid config and the
primary (not grid-varied) — the same value families 006/007/011 used as
their "headroom essentially never binds" setting, keeping this family at
4 *tunable* (grid-varied) parameters plus 1 fixed constant, i.e.
effectively 4 tunable parameters.

`normalization_method=zscore` is primary as the more standard, unit-free
"how many trailing standard deviations below the normalized mean"
construction, directly matching how the CLI's own normalization (mean
100, amplitude-adjusted) is designed to be read. `lookback_years=10` is
primary as a business-cycle-length window (long enough to span at least
one full CLI cycle — the OECD's own documented average full CLI cycle
length is roughly 4-6 years trough-to-trough for the US, so 10 years
comfortably spans more than one cycle without being so long it barely
updates), matching family 011's own `lookback_years=10` primary choice
and reasoning. `threshold_level=1` (z <= -0.5) is primary as a
moderately-below-trend threshold — not the most extreme (`level 0`,
z <= -1.0, would only flag the sharpest slowdowns) and not the mildest
(`level 2`, z <= 0.0, would flag roughly half of all history as "weak"
by construction under a review of typical CLI dispersion, an
uninformatively broad definition) — a no-look choice based on where the
signal is designed to be informative, not on any development-data
result. `weak_tilt_fraction=0.0` (full banking during the weak regime)
is primary as the "purest" test of the timing-shift hypothesis, matching
family 006/007/011's own primary choice for the analogous parameter.

## Grid

2 (`normalization_method`) x 2 (`lookback_years`) x 3 (`threshold_level`)
x 2 (`weak_tilt_fraction`) = **24 configurations** (<=36 cap).

## Primary configuration

`normalization_method=zscore, lookback_years=10, threshold_level=1,
weak_tilt_fraction=0.0` (`max_lump_multiple=6` fixed for all configs).

## Pre-grid non-degeneracy sanity check (required by this iteration's
task, before any grid run)

Before the full grid is trusted, the primary config's below-threshold
("weak") condition will be checked against each asset's own trading-day
index to confirm it fires non-trivially — neither near-0% nor near-100%
of development days — following the convention established in families
015/016/018. Result recorded in results.md before any backtest numbers
are trusted.

## Expected sign

**Positive on both wealth and Sharpe, if the CLI's leading-indicator
mechanism is real and its "avoid depositing steadily into a weakening
economy, catch up once it normalizes" logic survives this loop's
fee/robustness bar** — stated honestly as the family's central
hypothesis, not a certainty. As with family 011 (and families
003/005/006/007/010 before it), this mechanism only reallocates *timing*
of a fixed deposit stream, never total capital deployed, so even a real
effect may show a small absolute margin over DCA, and per family
010/011's now-documented pattern, a pass driven by a handful of large
historical slowdown episodes (e.g. 2001, 2008-09, 2015-16 mid-cycle
slowdown, 2020) is exactly the kind of few-dominant-episode result DSR
and the placebo circular-shift test are designed to catch — this
family's own results should be read with that precedent in mind before
drawing conclusions from sec 4.1 alone.
