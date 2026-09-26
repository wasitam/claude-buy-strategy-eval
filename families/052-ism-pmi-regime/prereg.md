# Family 052: ISM Manufacturing PMI regime deposit sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Institute for Supply Management (ISM) Manufacturing Report on Business
methodology (the "PMI", formerly published by the National Association of
Purchasing Management, hence its old FRED/ticker mnemonic `NAPM`) -- a
monthly diffusion index (0-100, 50 = the expansion/contraction boundary)
built from a survey of purchasing/supply managers at several hundred US
manufacturing firms across five equally-weighted sub-indices (new orders,
production, employment, supplier deliveries, inventories). One of the
most widely cited leading indicators of US manufacturing-sector activity
and, historically, of the broader business cycle (Koenig, E.F. (2002),
"Using the Purchasing Managers' Index to Assess the Economy's Strength
and the Likely Direction of Monetary Policy," Federal Reserve Bank of
Dallas *Economic and Financial Policy Review*). Seed queue item #55
(research-loop-plan-v3.md sec 7.3 replenishment; this iteration's task
brief).

## Mechanism ("why would this work, and who is on the other side?")

The ISM PMI is a fast, cheaply produced, forward-looking survey of the
people actually placing and filling manufacturing orders -- it typically
turns before hard production/GDP data because purchasing managers adjust
orders and inventories in anticipation of demand changes, not only in
response to them. When the PMI sits low and/or falling within its own
trailing history (a below-trend reading, conventionally read as
"contraction" once it crosses 50 but informative as a continuous
percentile well before that), that is evidence the real economy's
manufacturing engine is weakening -- a period in which risk assets have,
on average, historically faced more downside/drawdown risk before a
recovery becomes visible in hard data. This family bets that banking new
deposits during that weak-PMI window and redeploying the accumulated cash
as a catch-up lump once the PMI recovers to/above its own trailing
threshold produces, on average, more favorable entry prices than
depositing steadily straight through the weak window -- the same
"bank now, deploy the catch-up once conditions normalize" logic already
used by families 004/006/007/011/015/019/032/050, applied here to a
single-country, single-survey business-condition diffusion index instead
of a calendar, price, credit-spread, composite-leading-index or monetary
aggregate. No leverage, no shorting, no external capital: this is purely
a **timing reallocation** of the same fixed weekly deposit stream. The
"other side" of this trade is whoever keeps depositing at average pace
right through a PMI-flagged weakening window -- either an investor with
no access to (or no belief in) this signal, or one who believes prices
already reflect the coming slowdown and prefers not to try to time
around a well-published, 70-plus-year-old survey.

## Category

**Regime switch (macro / credit / sentiment)** (research-loop-plan-v3.md
sec 4.5's category list; the task brief's own label for this idea).

## Required step 1: ISM PMI reachability and history length (verified live before any design work)

Per this iteration's task brief, live reachability was checked directly
against FRED before writing any further code:

- `NAPM` (the historical FRED mnemonic for the ISM Manufacturing PMI
  Composite Index): **404 Not Found** on FRED's `fredgraph.csv` endpoint.
- A dozen other plausible FRED mnemonics were also tried live and all
  returned 404: `NAPMPMI`, `NAPMPI`, `NAPMNOI`, `NAPMEI`, `NAPMSDI`,
  `NAPMPRI`, `NAPMII`, `NAPMBI`, `NAPMEXI`, `NAPMIMP`, `ISM_MAN_PMI`,
  `ISM`.
- A live FRED website search for "ISM Manufacturing PMI"
  (`fred.stlouisfed.org/search?st=ISM+Manufacturing+PMI`) returned
  **"Displaying 0 series"** -- confirmed directly, not assumed.
- `MANEMP` (FRED, live, 200 OK, 1939-01-01 through the present) IS
  reachable, but it is manufacturing **employment level** (thousands of
  jobs), not the PMI diffusion index -- a different underlying concept
  entirely (a hard-data headcount series, not a forward-looking survey
  diffusion index), so it is not a substitute.
- This confirms the task brief's own stated expectation: FRED
  discontinued direct redistribution of the ISM PMI series (reportedly
  around 2016, over ISM licensing) and no FRED mnemonic for it exists
  today.
- Alternative live structured public sources were then investigated:
  - DBnomics (`api.db.nomics.world/v22/series/ISM/pmi`) -- confirmed
    `EGRESS_BLOCKED` (403 from this session's network egress proxy).
  - `forecasts.org` (`www.forecasts.org/data/data/NAPM.htm`, a
    commonly-cited free historical NAPM/ISM chart-and-table page) --
    confirmed `EGRESS_BLOCKED`.
  - `eco3min.fr`, `ycharts.com`, `multpl.com` (other candidate free
    ISM-PMI mirrors surfaced by web search) -- all confirmed
    `EGRESS_BLOCKED` by this session's network egress proxy.
  - No live-reachable, structured, free public source for the ISM
    Manufacturing PMI's historical monthly values exists in this
    session's environment, after genuine investigation of every
    plausible avenue above.

**Resolution, per the task's explicit allowance for exactly this
contingency (mirroring family 051's hard-coded FOMC calendar
precedent):** the monthly ISM Manufacturing PMI level for the
**development period only** (each core asset's start of history through
2019-12-31; this backtest never uses a date on or after 2020-01-01, so no
post-2019 value is needed or included) is **reconstructed from this
session's own training-era knowledge of the well-documented public
historical ISM/NAPM PMI record**, not downloaded from any live feed.

**Honest disclosure of construction method and confidence (required by
the task brief, following family 051's disclosure standard):**

- The series is built from a set of **anchor points** (roughly monthly
  resolution from 1990 onward, roughly quarterly-to-semiannual resolution
  1948-1989) at economically well-documented levels -- specific,
  frequently-cited historical prints (e.g. the Dec 2008 post-Lehman
  trough near 32.9; the Jan 2004 cycle high near 63.6; the Aug 2018
  multi-decade high near 61.3; the Aug 2019 first-sub-50 trade-war print
  near 49.1; the Dec 2019 dev-period-ending trough near 47.2) and
  well-documented NBER recession/expansion turning points -- with
  **monthly values in between linearly interpolated**, not independently
  recalled month by month.
- **Confidence is materially higher for 1990-2019** (specific prints are
  part of the well-known post-1990 macro narrative this session has
  higher-fidelity training knowledge of, including the 1998 Asian-crisis
  dip, the 2001 and 2007-09 recessions, the 2015-16 oil/dollar-driven
  manufacturing slowdown, and the 2018-19 trade-war slowdown) and
  **materially lower for 1948-1989**, where the pre-1990 anchors are a
  **stylized cyclical reconstruction** keyed to NBER recession/expansion
  dates and generic "trough/peak" diffusion-index levels typical of
  recessions/expansions of that era (with one specific named exception,
  the well-documented 1950 Korean-War industrial-mobilization spike),
  rather than remembered specific monthly prints.
- **This is a material, honestly-flagged limitation**, in the same
  spirit as the plan's own accepted BTC-short-history and family 019's
  ALFRED-vintage-gap caveats (sec 5.1, sec 12): pre-1990 dev-period
  results for SP500 (whose history starts 1927) should be read with this
  reconstruction's lower fidelity for that era in mind. GOLD's dev
  history starts 1975-01-02, SILVER 1979 (`SI=F`), OIL 1983-03-30, BTC
  2014-09-17 -- all four of those assets' entire dev histories fall
  inside the higher-confidence 1990-2019 window is FALSE for gold/silver
  (1975/1979-1989 falls in the lower-confidence stylized era), but true
  that BTC's and the majority of OIL's dev windows sit entirely in the
  higher-confidence 1990-2019+ era.
- The full anchor list and interpolation method are hard-coded directly
  in `src/backtest/v3/strategies/ism_pmi_regime.py` (`ANCHORS`,
  `fetch_raw_signal()`) -- not in a `data/*.csv` file, since `data/*.csv`
  is gitignored in this repo as a live-fetch cache directory, and this is
  deliberately **not** a live fetch (the same reasoning family 051 used
  to hard-code its FOMC dates directly in `pre_fomc_drift.py`).
  `scripts/v3/build_ism_pmi_reconstructed.py` is a documentation/
  inspection-only helper that calls that same function and writes
  `families/052-ism-pmi-regime/ISM_PMI_reconstructed_for_review.csv` so a
  reviewer can open the reconstructed series directly without running
  Python; it is not used by the strategy module or by the run script.
- Before 1948-01 (the reconstructed series' own start), and for any date
  the reconstructed series does not cover, the regime defaults to
  **strong/high** (behaves like plain DCA during signal warm-up) -- the
  same convention families 011/019/032/050 already use for their own
  pre-coverage eras.

## Required step 2: point-in-time / publication-lag properties (plan sec 3.2)

The ISM releases the Manufacturing PMI for reference month **M** on the
**first business day of month M+1** (its own long-standing, publicly
announced release calendar -- e.g. the December print is released the
first business day of the following January). This backtest must use
only data that would have been known at each historical decision date, so
the reconstructed monthly series (indexed, like every other FRED-style
macro series `fetch_fred_macro` returns, at the first-of-month reference
date) is **shifted forward by a fixed 35-calendar-day publication lag**
before being reindexed onto any asset's daily trading-day index -- a
deliberately conservative safety margin over the ISM's actual ~32-day
average gap (first-of-month reference date -> first business day of the
following month), matching family 050's own "safety margin over the
documented schedule" convention for TEDRATE's 2-day lag and family 019's
60-day margin over OECD's ~45-day documented schedule. Because this
family's PMI series is entirely reconstructed (not a live ALFRED-vintaged
feed), there is no revision-vintage question to resolve the way family
019 had to for `USALOLITONOSTSAM` -- the reconstructed values are treated
as final at the documented lag, and this is disclosed as a simplification
made possible only because the series is not sourced from a real
revisable feed.

This will be verified by the standard macro-specific extra implementation
check (families 011/019/050/032's precedent): recomputing the regime with
the lag shortened to 0 days must produce a *different* regime reading than
the documented 35-day lag on at least some historical dates, proving the
lag is doing something real, while every real backtest below uses the
documented 35-day lag only.

## Required step 3: concrete real dev-period divergence from family 019 (OECD CLI)

Family 019's signal (`USALOLITONOSTSAM`, the OECD's normalized US
Composite Leading Indicator) is a **smoothed, detrended, multi-series
composite** (new orders, permits, confidence surveys, interest-rate
spreads, equity prices, and more, combined and amplitude-adjusted by the
OECD's own long-running methodology) explicitly engineered to be a
*slow-moving* leading signal of the broader real-economy cycle. This
family's signal (the ISM PMI) is a **single monthly survey of
manufacturing purchasing managers only** -- no smoothing, no
multi-series averaging, no detrending -- and manufacturing is only one
(shrinking) slice of the broader US economy the OECD CLI is built to
track. The two should NOT move in lockstep at all times, and the
following real dev-period episode (fetched live from FRED for the OECD
CLI leg, exactly as family 019's own module does; the PMI leg uses this
family's reconstructed values, disclosed above) confirms a genuine
divergence:

**2019 trade-war manufacturing slowdown (timing divergence, the
dev-period-ending episode):**

| Month | OECD CLI (`USALOLITONOSTSAM`, live FRED) | Reconstructed ISM PMI |
|---|---|---|
| 2018-06 | 100.708 | ~57.0 (rising, mid-cycle strength) |
| 2019-01 | 99.676 (already declining) | ~56.6 (still comfortably expansionary) |
| 2019-06 | 99.080 | ~51.7 |
| 2019-08 | 98.961 | ~49.1 (**first sub-50 print**, outright contraction) |
| 2019-09 | 98.965 (**OECD CLI's own trough, already turning up**) | ~48.7 (still falling) |
| 2019-10 | 99.014 (rising) | 48.3 (still falling) |
| 2019-12 | 99.156 (rising for 3 straight months) | ~47.2 (**this family's own dev-period-ending trough**) |

The OECD CLI's own trough in this episode falls in **September 2019**
and it is already rising by December 2019 (99.156, up from its own
99.961 September low) -- while the reconstructed ISM PMI has **not yet
turned** by the dev-period's own final month, continuing to fall through
December 2019 (~47.2, its own lowest reconstructed reading of the entire
episode). This is exactly the kind of **timing divergence** the task
requires: a genuinely narrower, sharper, more manufacturing-concentrated
slowdown (that only shows up clearly as outright "contraction" in the
single-survey PMI, crossing 50 in August 2019) against a broader,
smoothed composite that barely dips and has already resumed rising by
the time the PMI is still near its own cycle low. (This asymmetry is
also the real, well-documented 2019 narrative: manufacturing entered a
mild "manufacturing recession" driven by tariffs/trade-war uncertainty
while services activity, which dominates the OECD CLI's broader
real-economy weighting, stayed comfortably expansionary throughout.)

**1998 Asian-financial-crisis episode (magnitude divergence, secondary
example):**

| Month | OECD CLI (`USALOLITONOSTSAM`, live FRED) | Reconstructed ISM PMI |
|---|---|---|
| 1997-10 | 100.870 (near-peak) | ~54.0 |
| 1998-08 | 99.863 (mild dip, ~1 point off peak) | ~47.0 (sharp dip, outright contraction) |
| 1998-12 | 100.021 (already recovering) | ~46.2 (this family's own reconstructed local low) |
| 1999-06 | 100.938 (comfortably above its own 1997 peak) | ~50.0 (still only just crossing back to neutral) |

The OECD CLI's entire 1998 Asian-crisis dip is under 1.1 index points
(99.78 low vs. 100.87 peak, a mild, brief wobble), while the reconstructed
PMI shows a much sharper swing into outright survey-defined contraction
(~46-47) over the same months -- a **magnitude divergence**: the acute
export/manufacturing-specific shock from the Asian crisis registered far
more sharply in the single manufacturing survey than in the broader,
smoothed composite, because the rest of the (much larger, services-
dominated) US economy kept growing solidly through 1998.

Both episodes were checked against family 019's own live-fetched
`USALOLITONOSTSAM` values (not asserted from memory) before this
prereg.md was written, per the task's explicit requirement to construct
this divergence before any design work.

**Brief distinction from families 011/050 (credit spreads) and 032 (M2):**
neither the BAA-AAA corporate spread, TEDRATE, nor M2 growth contains any
manufacturing-survey content at all -- they are a market-priced credit
spread, an interbank funding-stress spread, and a monetary-quantity
aggregate respectively, none of which asks purchasing managers anything
about their own orders, production or inventories. Brief distinction from
family 027 (`T10Y2Y` yield-curve slope): a market-priced term-structure
signal, not a survey of any kind.

## Single-asset scoping (judgment call, stated explicitly)

Following the precedent set by families 006/007/011/015/019/032/050 (a
macro/survey signal that does not depend on which of the 5 core assets it
is applied to gets tested on all 5 core assets under sec 4.1's standard
single-asset >=3/5 rule), this family is assessed as a **single-asset
family across all 5 core assets**, independently per asset. The ISM PMI
is a US real-economy manufacturing signal, not specific to any one of
gold/silver/oil/BTC/SP500 -- the same "macro signal is asset-agnostic"
reasoning already used for families 006/007/011/015/019/032/050.

## Exact rules

Computed at each week-end decision day `t` (same weekly cadence as every
other v3 family), using only the point-in-time PMI value available as of
`t`'s close (35-day lag, above) for fills -- the PMI signal itself never
depends on the asset being traded.

1. **Point-in-time construction.** The reconstructed monthly PMI series
   (observation date = the 1st of the reference month) is shifted forward
   by the fixed 35-calendar-day publication lag before being forward-
   filled onto the asset's daily trading-day index, so the value "seen"
   on trading day `t` is only ever a value that a real-time investor
   could have already known by `t`'s close under the ISM's own release
   schedule.
2. **Percentile rank.** At each week-end day `t`, compute the point-in-
   time PMI level's percentile rank within a trailing `lookback_years`
   window of the signal's own (point-in-time) observation dates (purely
   backward-looking, expanding-until-full, `MIN_PERIODS` = the window
   length -- same convention as families 011/050's percentile-rank
   construction). This directly operationalizes the queue item's own
   "low/falling ... high/rising" language: a low trailing percentile
   necessarily reflects both a low current level AND, given the ISM
   PMI's own historically mean-reverting/momentum-persistent monthly
   dynamics, a recent decline relative to the window; the same
   percentile-of-level convention families 011/019/050 already use for
   an analogous "low/falling vs. high/rising" macro framing.
3. **Persistence-confirmation whipsaw filter** (`persistence_months`,
   matching family 050's asymmetric TED-spread convention): the regime
   flips to **weak** only after `persistence_months` consecutive monthly
   point-in-time observations read below `weak_pctile`; it flips back to
   **strong** immediately on the first observation at/above the
   threshold (asymmetric: confirmed entry into weakness, immediate
   release on recovery).
4. **Regime.** **Weak** if the persistence-confirmed condition above
   holds; otherwise **strong**. Before enough history exists to fill the
   lookback window (or before the reconstructed series' own 1948-01
   start), the regime defaults to **strong** (behaves like plain DCA
   during signal warm-up, same convention as families 011/019/032/050).
5. **Weekly decision (week-end days only), no sells ever** (matching
   families 003/005/006/007/011/019/032/050's precedent -- a pure
   timing/banking rule that never liquidates existing units, staying
   within the plan's no-leverage/no-shorting constraint by construction):
   - **Weak:** buy `weak_tilt_fraction * weekly_deposit`. The remainder
     is banked as cash (earning IRX, sec 3.2) until the regime next reads
     strong.
   - **Strong:** buy `min(cash, max_lump_multiple * weekly_deposit)` --
     this both makes the current week's normal deposit and, if there is
     banked cash from a prior weak stretch, deploys a capped catch-up
     lump, cash-capped so this can never become leverage.
6. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the signal/regime computation entirely and buys
   100% of that week's cash on every week-end day (0 otherwise) --
   reproduces plain DCA bit-for-bit, same pattern as every prior v3
   family's disable path. As families 010/011/019/032/050 flagged
   explicitly: a grid config with `weak_tilt_fraction=0` and
   `enabled=True` is **NOT** equivalent to DCA -- the regime computation
   still runs and could in principle mark historical weeks weak even near
   the mildest threshold. Only `enabled=False` is checked against the DCA
   baseline.

## Data inputs

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only,
  same as every prior family).
- The reconstructed monthly ISM PMI series, hard-coded as `ANCHORS` and
  built by `fetch_raw_signal()` directly inside
  `src/backtest/v3/strategies/ism_pmi_regime.py` (disclosed above) --
  **not** routed through `fetch_fred_macro()` or `fetch_yf_macro()`,
  since it is not a live external fetch at all; this is documented
  explicitly so the raw-data-leak static check's allowlist and reviewer
  expectations stay accurate (`data.py` itself is untouched by this
  family, since it never touches `load_dev()`/`open_holdout()`'s gated
  OHLC data or any live macro feed).

## Parameters (4 tunable, comfortably under the plan's <=5 ceiling)

| Parameter | Grid values | Primary |
|---|---|---|
| `lookback_years` | 5, 10 | 10 |
| `weak_pctile` | 20, 30, 40 | 30 |
| `weak_tilt_fraction` | 0.0, 0.25 | 0.0 |
| `persistence_months` | 1, 2 | 1 |

`max_lump_multiple` is fixed at **6** for every grid config and the
primary (not grid-varied) -- the same value families 006/007/011/019/050
used as their "headroom essentially never binds" setting, keeping this
family at 4 *tunable* (grid-varied) parameters plus 1 fixed constant.

`lookback_years=10` is primary as a business-cycle-length window (spans
more than one full ISM cycle -- post-war US business cycles have
historically averaged roughly 5-6 years trough-to-trough), matching
family 011/019/050's own `lookback_years=10` primary choice and
reasoning. `weak_pctile=30` is primary as a moderately-below-trend
threshold -- not the most extreme (`20`, which would only flag the
sharpest slowdowns) and not the mildest (`40`, an uninformatively broad
definition) -- a no-look choice based on where the signal is designed to
be informative, not on any development-data result, matching family
019's own `threshold_level=1` (middle-of-three) reasoning.
`weak_tilt_fraction=0.0` (full banking during the weak regime) is primary
as the "purest" test of the timing-shift hypothesis, matching family
006/007/011/019/050's own primary choice for the analogous parameter.
`persistence_months=1` (no whipsaw-confirmation delay) is primary as the
simplest, most literal reading of "sits low/falling," matching family
050's own `persistence_days=1` primary choice.

## Grid

2 (`lookback_years`) x 3 (`weak_pctile`) x 2 (`weak_tilt_fraction`) x 2
(`persistence_months`) = **24 configurations** (<=36 cap).

## Primary configuration

`lookback_years=10, weak_pctile=30, weak_tilt_fraction=0.0,
persistence_months=1` (`max_lump_multiple=6` fixed for all configs).

## Pre-grid non-degeneracy sanity check (required by sec 8 step 6/task instructions, before any grid run)

Before the full grid is trusted, the primary config's weak-regime
condition will be checked against each asset's own trading-day index to
confirm it fires non-trivially -- neither near-0% nor near-100% of
development days -- following the convention established in families
015/016/018/050. Result recorded in results.md before any backtest
numbers are trusted.

## Expected sign

**Positive on both wealth and Sharpe, if the ISM PMI's leading-indicator
mechanism is real and its "avoid depositing steadily into a weakening
manufacturing sector, catch up once it normalizes" logic survives this
loop's fee/robustness bar** -- stated honestly as the family's central
hypothesis, not a certainty. As with families 011/019/032/050 before it,
this mechanism only reallocates *timing* of a fixed deposit stream, never
total capital deployed, so even a real effect may show a small absolute
margin over DCA. Family 050's own closely analogous result (a
faster-mean-reverting macro spread that still fell short of the sec 4.1
bar, 2/5) and family 019's own analogous composite-leading-indicator
result are the most directly relevant prior evidence, and this family's
own results should be read with that precedent in mind before drawing
conclusions from sec 4.1 alone -- a genuinely single-survey,
manufacturing-only signal may prove noisier (a smaller, more volatile
underlying sample of survey respondents than a composite of many series)
or, conversely, may prove more responsive/timely than either.
