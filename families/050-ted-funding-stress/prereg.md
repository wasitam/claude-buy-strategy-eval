# Family 050: Money-market funding-stress (TED spread) regime sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Poole, W. (2008 speeches, as President of the Federal Reserve Bank of St.
Louis) and Federal Reserve Bank of San Francisco, *FRBSF Economic Letter*
(2008), "The TED Spread"; Taylor, J.B. and Williams, J.C. (2009), "A Black
Swan in the Money Market," *American Economic Journal: Macroeconomics*
1(1), 58-83 — both establish the TED spread (3-month LIBOR/interbank rate
minus the 3-month T-bill yield) as the classic gauge of **interbank
funding/liquidity stress**: how much of a premium banks demand to lend
unsecured to one another over the risk-free short rate, historically
spiking sharply and abruptly at moments when banks doubt one another's
solvency or liquidity (most famously August 2007 through late 2008).
Seed queue item #53 (research-loop-plan-v3.md sec 7.3 replenishment,
`state/research_queue.md`): "Money-market funding-stress regime sizing."

## Mechanism ("why would this work, and who is on the other side?")

The TED spread widens when banks become reluctant to lend to each other
unsecured — a symptom of doubt about counterparty solvency/liquidity in
the banking system itself, distinct from doubt about corporate borrowers'
credit quality (family 011) or the quantity of money in circulation
(family 032). Historically, TED-spread spikes are sharp, short-lived
dislocations (days to a few months at the acute phase, even though some
episodes like 2007-09 have a long tail) driven by an acute funding
scramble — central banks (Fed, ECB, other G10 central banks) respond
quickly with liquidity facilities (TAF, swap lines, discount-window
easing) specifically designed to compress interbank spreads, which is
part of why the TED spread's spikes historically resolve faster than
BAA-AAA's multi-year post-crisis elevated readings (family 011's own
documented failure mode: "the credit-spread signal's mean-reversion is
too slow relative to how quickly risk assets recover"). This family bets
that banking new deposits during an acute funding-stress spike, and
deploying a capped catch-up lump once the spread normalizes, produces on
average more favorable entry prices than investing steadily through the
worst of an interbank liquidity scramble — the same banking/cash-cap
deposit-timing mechanic already used by families 004/006/007/011/015/019/
027/032 (bank now, catch-up lump later, cash-capped, never leverage)
applied here to an interbank-funding-liquidity signal instead of a
calendar, price, corporate-credit-spread, real-activity, policy-rate,
curve-shape or monetary-aggregate signal. The "other side" of this trade
is whoever continues to invest at a steady pace through an interbank
funding scramble and is compensated (in expectation) for bearing that
risk, or who correctly judges that risk-asset prices already reflect the
funding stress and that the eventual snap-back happens too fast for a
weekly-cadence deposit-timing rule to actually capture.

## Category

**Regime switch (macro / credit / sentiment)** (research-loop-plan-v3.md
sec 4.5's category list; matches the queue's own label for seed-queue
item #53, and families 011/019/027/032's category for the analogous
reason — a macro/financial-market stress signal driving a banking/timing
decision, no leverage or shorting).

## Required concrete distinction from family 011 (the closest analog)

Family 011 (credit-stress risk-off filter, REJECTED) uses the **BAA-AAA
corporate bond yield spread** (or the Chicago Fed NFCI) — a **corporate
credit-risk-premium** and broad financial-conditions signal, answering
"how much compensation are corporate-bond investors demanding for
default/liquidity risk right now?" This family's signal, the **TED
spread**, answers a categorically different, narrower question: "how
much of a premium do BANKS demand to lend to EACH OTHER, unsecured, over
the risk-free rate right now?" — the classic 2007-08 "banks won't lend to
each other" interbank-funding/liquidity signal, not a corporate-borrower
default-risk signal. `TEDRATE` contains neither `BAA` nor `AAA` as an
input (it is built from 3-month LIBOR and the 3-month T-bill yield) and
`BAA`/`AAA` contain no LIBOR/interbank-rate input at all — genuinely
different data sources.

**Concrete real dev-period divergence, verified on live FRED data before
any design work** (both series fetched via `fetch_fred_macro`, monthly-
averaged, each expressed as a trailing 10-year rolling z-score of its own
level, `n=410` overlapping months, full monthly-overlap history):

- **Full-history correlation of the two monthly z-score series: +0.286**
  — low, confirming the two signals are far from interchangeable proxies
  for one another, not merely "usually agree with some noise."
- **August-September 2007 (the TED spread's own textbook onset episode,
  the BNP Paribas funds freeze and the opening act of the global
  financial crisis):** TED spread z-score climbs sharply, **+2.98
  (Aug-07) then +3.93 (Sep-07)** — deep into its own top decile — while
  the BAA-AAA corporate spread's z-score is essentially flat at
  **-0.10 (Aug-07) and -0.17 (Sep-07)**, i.e. BELOW its own trailing
  mean. This is exactly the mechanism story: the interbank funding market
  froze months before corporate credit spreads meaningfully widened (the
  BAA-AAA spread's own z-score does not cross above +1 until December
  2007 — three to four months later). Family 011's signal would have read
  "calm" through the entire opening act of the funding crisis that gives
  the TED spread its name.
- **2001-2002 (the mirror-image divergence, dot-com-bust corporate credit
  deterioration with no interbank funding scramble):** the corporate
  spread's z-score is deeply elevated, **+4.55 (Dec-01), +4.48 (Jan-02),
  +4.51 (Feb-02)** — near the top of its entire history — while the TED
  spread's z-score is simultaneously DEPRESSED, **-1.51 (Dec-01), -1.76
  (Jan-02), -1.72 (Feb-02)** — well below its own trailing mean (the Fed's
  aggressive 2001 rate cuts left ample bank-system liquidity even as
  corporate default risk was being repriced upward after Enron/WorldCom-
  era accounting failures and the tech-sector default wave). Family 011's
  signal reads acutely "stressed" for over a year in a period this
  family's own signal reads calm-to-benign.

These two real, opposite-direction divergence episodes (2007 TED-leads /
credit-lags, and 2001-02 credit-leads / TED-lags) are the clearest
possible evidence the two signals are not proxies for one another, and
match the economic story exactly: TED spikes on ACUTE interbank funding
scrambles (fast-moving, bank-system-specific); BAA-AAA moves on slower,
broader corporate default-risk repricing that can run for a year or more
without any interbank funding stress at all.

## Brief distinction from families 032 (M2 growth) and 019 (OECD CLI)

- **Family 032 (M2 growth regime, REJECTED)** measures the year-over-year
  growth rate of the M2 monetary aggregate — a **quantity-of-money**
  signal (how much money is circulating), built from Fed H.6 data
  (`M2SL`), with no yield, spread or rate construction at all. This
  family's TED spread is a **price/spread** signal (a yield differential
  between two specific money-market instruments), not a stock-of-money
  quantity measure — categorically different data type and transmission
  story (liquidity QUANTITY vs. interbank funding-market PRICE of risk).
- **Family 019 (OECD CLI regime, REJECTED)** is a **composite, multi-
  series leading-activity index** (`USALOLITONOSTSAM`), aggregating many
  real-economy series (orders, permits, confidence, production-adjacent
  data) across economies with a built-in smoothing/detrending
  methodology, answering a real-side-of-the-economy question. This
  family's TED spread is a single, direct market-quoted interbank rate
  spread with no composite construction, no real-economy inputs, and no
  cross-country aggregation — a purely financial-market microstructure
  signal about the banking system's own funding conditions.

## Single-asset scoping (judgment call, stated explicitly)

Following the precedent set by families 006/007/011/015/019/027/032 (a
macro/financial signal that does not depend on which of the 5 core assets
it is applied to gets tested on all 5 core assets under sec 4.1's standard
single-asset >=3/5 rule, using the existing single-asset `engine.py`,
rather than narrowed to one asset), this family is assessed as a
**single-asset family across all 5 core assets**, independently per
asset. Interbank funding stress is a US/global banking-system signal, not
specific to any one of gold/silver/oil/BTC/SP500.

## Data reachability and history, verified live before writing this
pre-registration

`TEDRATE` (the legacy, discontinued TED spread) is directly reachable via
FRED's `fredgraph.csv` endpoint (the same `fetch_fred_macro()` helper
families 011/019/027/032 already use). It returns **daily observations
from 1986-01-02 through 2022-01-21** (8,853 rows, discontinued by FRED
after that date, consistent with the queue item's own note that it is
"discontinued ~2022") — this comfortably covers the **entire** dev period
(through 2019-12-31) with over 33 years of history before the discontinuation
date, so **no substitute construction (`USD3MTD156N` minus `DGS3MO`/`DTB3`)
is needed**; `TEDRATE` alone is the primary and only source used. Per-asset
dev-window overlap: SP500's dev history starts 1927-12-30 (TED coverage
only from 1986 — the same kind of pre-coverage warm-up gap families
011/019/032 already flagged for their own macro series, defaulting to
"calm" until the signal is usable); GOLD/SILVER/OIL's dev histories start
2000-08-23/30 (fully inside TED's 1986-2022 coverage); BTC's dev history
starts 2014-09-17 (fully inside TED's coverage). No asset requires
exclusion.

## Exact rules

Computed at each week-end decision day `t` (same weekly cadence as every
other v3 family), using only the point-in-time TED-spread signal
available as of `t`'s close (see "Point-in-time / publication-lag
discipline" below) and the asset's own trading-day calendar/price for
fills — the TED signal itself never depends on the asset being traded.

1. **Point-in-time construction.** The raw FRED `TEDRATE` series (daily,
   market-quoted) is shifted forward by a fixed conservative publication
   lag (see below) before any percentile computation, so every derived
   value "seen" on trading day `t` is built only from a TED-spread value
   that had actually been published by `t`'s close.
2. **Persistence-confirmed regime.** At each (lagged) TED-spread
   observation date, compute the value's percentile rank within its own
   trailing `lookback_years`-year window (a purely backward-looking,
   expanding-until-full rolling percentile). The regime flips to
   **stressed** only once the percentile rank has been `>= stress_pctile`
   for `persistence_days` consecutive (lagged) TED-spread observations in
   a row (a whipsaw-avoidance filter, since a daily market-quoted rate
   can print a single noisy elevated reading without a genuine funding-
   stress episode underway — `persistence_days=1` imposes no filter at
   all, the "purest" direct reading of the raw percentile rule). It flips
   back to **calm** the first observation the percentile rank drops below
   `stress_pctile`, with no persistence requirement on the way down
   (matching the "stress resolves, redeploy promptly" mechanism story —
   an asymmetric filter, confirmed-on-the-way-in, immediate-on-the-way-
   out). Before enough history exists to fill the `lookback_years`
   window, the regime defaults to **calm** (behaves like plain DCA during
   signal warm-up, the same convention families 011/019/032 use).
3. **Weekly decision (week-end days only), no sells ever** (matching
   families 003/005/006/007/011/019/027/032's precedent — a pure
   timing/banking rule that never liquidates existing units, staying
   within the plan's no-leverage/no-shorting constraint by construction):
   - **Stressed:** buy `stress_tilt_fraction * weekly_deposit`. The
     remainder is banked as cash (earning IRX, sec 3.2) until the regime
     next reads calm.
   - **Calm:** buy `min(cash, max_lump_multiple * weekly_deposit)` — this
     both makes the current week's normal deposit and, if there is banked
     cash from a prior stressed stretch, deploys a capped catch-up lump,
     cash-capped so this can never become leverage.
4. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the signal/regime computation entirely and buys
   100% of that week's cash on every week-end day (0 otherwise) —
   reproduces plain DCA bit-for-bit, same pattern as every prior v3
   family's disable path. As families 010/011/019/032 flagged explicitly:
   a grid config with `stress_tilt_fraction=0` and `enabled=True` is
   **NOT** equivalent to DCA — the regime computation still runs. Only
   `enabled=False` is checked against the DCA baseline.

## Point-in-time / publication-lag discipline (sec 3.2 bullet 4)

`TEDRATE` is a market-quoted, same-day-observable rate spread (unlike
family 011's monthly BAA/AAA average or family 032's monthly, later-
revised M2SL) — there is essentially no meaningful publication lag in the
economic sense (3-month LIBOR and the 3-month T-bill yield are both
observable at the close of the trading day they describe), the same
reasoning family 016 used for `^VIX` ("no lag concern -- the closing index
level is observable same-day") and family 027 used for `T10Y2Y`. Following
family 027's own conservative convention for a daily market-quoted FRED
series, a **2-calendar-day** lag is applied from each observation date
before the value becomes usable — deliberately conservative (protecting
against any FRED same-day-vs-next-business-day posting lag) even though
the true economic lag is close to zero. `TEDRATE` is **not** an
ALFRED-vintaged series (it is a market price snapshot, never later
revised), so no vintage-reconstruction gap applies here at all, unlike
families 019/032's partial ALFRED coverage caveat.

This is verified by the standard no-lookahead implementation check
(perturbing asset price data), plus the family-specific macro check every
prior macro family in this loop uses: recomputing the regime with the lag
shortened to 0 days must produce a different regime reading on at least
some historical dates than the documented 2-day-lag version, proving the
lag is doing something, not a no-op.

## Data inputs

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only,
  same as every prior family).
- `TEDRATE` from FRED, via `src.backtest.v3.data.fetch_fred_macro("TEDRATE")`
  (the same helper families 011/019/027/032 already use — no new
  data-access code needed, keeping the `fredgraph.csv` raw-data-leak
  check's allowlist unchanged).

## Parameters (4 tunable + 1 fixed, all <=5 total)

| Parameter | Grid values | Primary |
|---|---|---|
| `lookback_years` | 5, 10 | 10 |
| `stress_pctile` | 70, 80, 90 | 80 |
| `stress_tilt_fraction` | 0.0, 0.25 | 0.0 |
| `persistence_days` | 1, 3 | 1 |

`max_lump_multiple` is fixed at **6** for every grid config and the
primary (not varied in the grid) — the same value families 006/007/011/
019/032 used as their "headroom essentially never binds" setting, so the
grid's 4 varied dimensions isolate the TED-spread signal's construction
and threshold rather than the catch-up cap. This keeps the family at 4
*tunable* (grid-varied) parameters plus 1 fixed constant, i.e.
**effectively 4 tunable parameters, comfortably under the plan's <=5
ceiling** (and even counting `max_lump_multiple` as a declared-but-fixed
5th parameter stays at the ceiling, not over it).

`lookback_years=10` is primary as a business-cycle-length window (long
enough to span at least one full funding cycle), matching families
011/019/032's own primary reasoning for the analogous parameter.
`stress_pctile=80` matches the 20/80 dead-zone convention families
008/010/011 already established (top quintile of the trailing-window
signal = stressed). `stress_tilt_fraction=0.0` (full banking while
stressed) is primary as the "purest" test of the timing-shift hypothesis,
matching families 006/007/011/019/032's own primary choice for the
analogous parameter. `persistence_days=1` (no persistence filter) is
primary as the most direct, literature-faithful reading of "TED spread in
its own elevated percentile" with no discretionary whipsaw-avoidance
tuning layered on top — a no-look choice, not one informed by any
development-data result; `persistence_days=3` is included in the grid
only as a diagnostic robustness check on the primary's own most obvious
alternative reading.

## Grid

2 (`lookback_years`) x 3 (`stress_pctile`) x 2 (`stress_tilt_fraction`) x
2 (`persistence_days`) = **24 configurations** (<=36 cap).

## Primary configuration

`lookback_years=10, stress_pctile=80, stress_tilt_fraction=0.0,
persistence_days=1` (`max_lump_multiple=6` fixed for all configs).

## Pre-grid sanity checks (run before the grid, following families
019/032's precedent)

1. **Non-degeneracy:** the primary configuration's `stressed` condition
   must fire non-trivially (not near-0%, not near-100% of dev days) on
   every core asset.
2. **Known-episode check, strictly within dev dates (pre-2020):** the
   primary configuration's regime reading during the well-documented
   August 2007 - Q1 2008 TED-spread onset episode (the funding-market
   freeze that gives the spread its name) must read **stressed** for a
   clear majority of that window — confirming the signal construction
   correctly identifies a real, well-known TED-spread regime shift before
   any grid result is trusted. This spot-check stays strictly within
   development dates (all before the 2020-01-01 holdout cutoff) and
   checks the single episode named in the source literature itself, never
   the reverse.

## Expected sign

**Positive on both wealth and Sharpe, if the interbank-funding-stress
mechanism is real, its spikes are genuinely faster-mean-reverting than
family 011's corporate-credit signal, and its "buy after the funding
scramble resolves" logic survives this loop's fee/robustness bar** —
stated honestly as the family's central hypothesis, not a certainty. A
genuine risk flagged before any backtest, informed by families
003/005/006/007/010/011/019/027/032's now-consistent pattern in this
loop: like those families, this mechanism only reallocates *timing* of a
fixed deposit stream (never total capital deployed, no leverage), so even
a real effect may show a small absolute wealth/Sharpe margin over DCA. A
further, family-specific risk: genuine TED-spread stress episodes with
this magnitude are rare and clustered in the dev sample (most obviously
1987, 1998 (LTCM), 2000-01, and above all 2007-09 — the 2007-09 episode by
far the largest and longest, meaning the pooled 5-asset result could be
dominated by how well or badly this exact rule timed 2008-09's recovery
alone), exactly the class of few-dominant-episode result sec 4.2's DSR and
sec 4.3's placebo test are designed to catch, and exactly the failure mode
families 011/019/027/031/032 have each already hit in this loop.
