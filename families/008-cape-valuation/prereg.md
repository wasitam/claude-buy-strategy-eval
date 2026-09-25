# Family 008: CAPE / earnings-yield valuation sizing (S&P 500)

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Shiller, R. (various; CAPE / cyclically-adjusted P/E, "Irrational
Exuberance" and ongoing public data updates); Campbell, J.Y. and Shiller,
R.J. (1998), *Valuation Ratios and the Long-Run Stock Market Outlook*,
Journal of Portfolio Management -- CAPE (price / 10-year trailing average
real earnings) predicts long-horizon forward equity returns, with low CAPE
associated with higher subsequent real returns and high CAPE with lower
ones. Asness, C., Ilmanen, A., Israelov, R. (2011) and related AQR
practitioner research on valuation-based tactical tilts (buy more when
cheap, less when expensive, never fully exiting) motivate using CAPE as a
continuous *sizing* signal rather than a binary in/out timing signal,
which is the shape of this family's mechanism. Seed queue item #8
(research-loop-plan-v3.md sec 7.3): "CAPE / earnings-yield valuation
sizing (S&P 500)."

## Mechanism ("why would this work, and who is on the other side?")

Shiller's CAPE (price divided by a 10-year trailing average of real
earnings, smoothing out the business cycle and one-off earnings spikes/
troughs) has been shown empirically to have meaningful explanatory power
for subsequent 10-year real equity returns: markets trading at low CAPE
(cheap relative to smoothed fundamentals) have historically gone on to
deliver higher long-run forward returns than markets trading at high CAPE
(expensive). The economic story is a **mean-reversion-in-valuation**
argument: extreme valuation levels (in either direction) are not
permanent, and eventually revert toward historical norms, either through
price moves, earnings catching up, or both. The "other side" of this
trade is whoever is willing to buy at rich valuations and sell (or simply
not participate) at cheap ones -- plausibly investors extrapolating
recent trends (buying more when prices have already run up, which is
exactly when CAPE tends to be high), or simply investors who cannot avoid
buying regardless of valuation (e.g. mechanical contribution schedules
like plain DCA itself, which is the very benchmark this family is tested
against). Unlike a binary trend-following exit (family 001) or a
regime-switch rule, this mechanism never fully exits the market -- it
only tilts the *size* of each week's purchase up when valuation is cheap
and down when it is expensive, always remaining invested, which is a
materially different mechanism shape from every other family tested so
far in this loop.

**Scope caveat, stated here because it drives this family's design
below:** like families 003/005/006/007, this strategy never changes
*how much total* capital eventually gets deployed in the very long run in
a way that would break capital neutrality with DCA in expectation over a
full valuation cycle (it has no sells, and the multiplier is a bounded
number applied to a bounded, symmetric-around-1.0-in-spirit sizing band)
-- but unlike those families, it *is* allowed to leave cash banked for
extended periods during a sustained rich-valuation regime, exactly as
sec 2's "Allowed actions" permits ("vary buy size / hold cash"). This is
flagged here, before any backtest, as the family's main structural risk:
if development-period valuation is persistently on one side of the
signal's threshold for years at a stretch (plausible, since valuation
regimes can be multi-year), the strategy's wealth outcome will be
dominated by *how much of the deposit stream got banked vs. deployed*
during that stretch, not by any within-week timing skill -- the same
"opportunity-cost of banking during a persistent regime" failure mode
already observed in families 006 and 007's BTC results.

## Category

**Sizing / valuation** (research-loop-plan-v3.md sec 4.5's category list;
matches sec 7.3's own label for seed-queue item #8 exactly).

## Why this is NOT a re-test of anything in sec 7.2's closed list, or of
## family 007's SmartDCA-adjacent v2 work

- **Not a re-test of sec 7.2's closed list.** The closest entry is v2
  SmartDCA (rho x m_max x sweep grid), but SmartDCA's signal is
  **price-vs-its-own-52-week moving-average trend** (a purely
  price-technical signal, no fundamentals, no earnings data of any kind)
  -- it sizes buys up when price is *below* its trailing trend and down
  when *above* it, a trend/mean-reversion-on-price rule. This family's
  signal is **price relative to a 10-year trailing average of real
  corporate earnings** -- a fundamentals-based valuation signal that
  requires external (non-price) economic data entirely absent from
  SmartDCA's design. The economic rationale is also different: SmartDCA's
  story is short-run price mean-reversion around a moving average;
  this family's story is long-run valuation mean-reversion around a
  smoothed earnings-based fair-value anchor. These are genuinely
  different mechanisms by every dimension sec 7.2 asks about (different
  signal definition, different data inputs, different economic
  rationale), not a parametrization of the same idea.
- **Not a re-test of family 004 (value averaging).** Value averaging's
  target-path reference point is a *deterministic, pre-specified growth
  path* (e.g. 10%/year), entirely independent of any market or economic
  data -- it does not use price, earnings, or valuation at all as an
  input signal (its "cheapness" concept is relative to the investor's own
  target trajectory, not relative to fundamentals).
- **Not a re-test of family 001 (trend exit) or family 005 (TSMOM
  sizing).** Both are price-only trend signals (moving-average level or
  sign of trailing return); neither uses any earnings, profits, or other
  fundamentals data.
- Also distinct from the other sec 7.2-closed v2/v2.1 rate-regime and
  rebalancing strategies (Strategy D uses Fed-funds/yield-curve/dot-plot
  data, not equity valuation; C1-C3 are cross-asset rebalancing rules
  with no valuation signal at all).

## Single-asset scoping decision: **structural gap, flagged explicitly**

This is the first family in the loop where the *mechanism itself*, not
merely the motivating literature, is only definable for one of the 5 core
assets. CAPE / earnings yield requires a well-defined "earnings" series
for the underlying asset. S&P 500 (`^GSPC`) has one (aggregate reported
corporate earnings). Gold (`GC=F`), silver (`SI=F`), oil (`CL=F`) and BTC
(`BTC-USD`) do not -- they produce no cash flows or earnings at all, so
"earnings yield" has no literal definition for them. Constructing ad hoc
per-asset analogues (e.g. gold's real-price-vs-trend, BTC's NVT ratio)
would each require an entirely different signal definition, different
data source, and arguably a different economic mechanism (network-value
arguments for BTC's NVT are not a "cheap relative to earnings" story at
all) -- exactly the kind of scope creep the task instructions for this
iteration warned against, and precisely NOT what sec 7.1(4)'s
pre-registration process is meant to sanction under a single family's
umbrella. Unlike families 006/007 (turn-of-month, day-of-week), where the
*mechanism* (a calendar-timing execution shift within a fixed deposit
schedule) is cleanly asset-agnostic even though the *motivating
literature* happened to be asset-specific (equities for 006, BTC for
007), here the mechanism **itself** cannot be defined for 4 of the 5 core
assets without inventing unrelated mechanisms for each one.

**Decision: option (b) from the task instructions.** This family is run
as a **documented SP500-only diagnostic**, explicitly **not eligible for
a sec 4.1 pass** under the standard >= 3/5-core-assets rule, rather than
forcing a same-mechanism test across all 5 assets (which sec 006/007's
precedent would otherwise suggest) or inventing four unrelated per-asset
proxy mechanisms under this family's name. Reasoning:

1. **Honesty over false uniformity.** Following the 006/007 precedent
   here would require either (a) skipping the other 4 assets silently
   (never done elsewhere in this loop, and not honestly comparable to how
   every prior single-asset family was scored), or (b) inventing
   fundamentally different signals for gold/silver/oil/BTC under this
   family's single pre-registration, which would conflate multiple
   distinct mechanisms and literatures into one family and make its
   "one page, at most 5 parameters" complexity ceiling (sec 3.4) and its
   single declared category (sec 4.5) meaningless -- a family cannot
   honestly declare "Sizing / valuation" via CAPE as its one mechanism
   while secretly running four unrelated mechanisms under the same
   verdict.
2. **Sec 4.1's >= 3/5 rule structurally cannot be satisfied by a
   single-asset test.** Even a very strong SP500 result cannot make this
   family a finalist under sec 4.1 as literally written, since a
   single-asset count can be at most 1/5 < 3/5. This is stated here,
   before any backtest, so the eventual verdict is not a post-hoc
   rationalization: **this family cannot become a finalist regardless of
   its SP500 result**, and holdout will not be opened for it (task
   instruction step 7; also consistent with sec 5.4's "holdout access is
   reserved for finalists only").
3. **Still useful as a diagnostic.** Running SP500 alone and reporting
   its full sec 4.1/4.2/4.4 battery honestly (results.md) gives the
   owner real signal on whether the CAPE-sizing idea has merit on the one
   asset it is actually defined for, without corrupting the family
   verdict system with an artificial pass/fail path that the charter
   never anticipated.
4. **Flag for the owner.** This is a genuine, structural gap between
   sec 4.1's ">= 3/5 core assets" win rule and any mechanism whose
   signal is fundamentals-based and asset-specific by construction
   (a fundamentals signal cannot be "extended" to assets with no
   fundamentals without becoming a different mechanism). Seed-queue idea
   #9 (BTC on-chain valuation: MVRV, realized price) and idea #12
   (commodity term-structure carry) have exactly the same structural
   issue -- an on-chain valuation signal is BTC/crypto-only by
   construction, and a term-structure carry signal needs a futures curve
   that literally does not exist for spot-only assets like BTC-USD or
   ^GSPC as tested in this loop. **The owner may want to revisit whether
   sec 4.1 should have a defined single-asset pass path (e.g., a higher
   bar applied to n=1) for mechanisms that are legitimately
   single-asset by construction**, rather than every such idea being
   structurally capped at "diagnostic only, cannot pass" regardless of
   result quality. No such revision is made here -- the charter is
   followed exactly as written, and this family is scored as
   structurally out of scope for sec 4.1, but the ambiguity is raised
   explicitly for the owner's judgment on future iterations.

**Consequence for accounting:** this family's grid trials, DSR, N_eff and
CSCV are still computed and logged in full (sec 4.2/4.4 diagnostics are
well-defined even for a single asset), and its DSR computation uses
SP500's own excess-return series directly (not a 5-asset pooled average,
since there are no other assets to pool) -- this deviation from the
standard pooled-excess-series DSR convention is called out explicitly in
results.md, since it changes what "N_eff" and "DSR" mean for this family
(a single-asset excess series is far more exposed to that one asset's own
idiosyncratic sample-path risk than a 5-asset-pooled series would be).
The family still counts as one of the 60 new-family budget slots (sec 6.1)
regardless of this scoping decision.

## Data reachability (checked live in this environment before design was
finalized)

Per the task's explicit instruction to check what is reachable (same
approach as v2's FRED/other macro fetches), the following were tried:

| Source | Result |
|---|---|
| `http://www.econ.yale.edu/~shiller/data/ie_data.xls` (Shiller's own CAPE spreadsheet) | HTTP 403 direct from the source server itself (not a proxy block) |
| `https://www.multpl.com/shiller-pe/table/by-month` | Egress-proxy policy denial (`connect_rejected`) |
| `https://data.nasdaq.com/api/v3/datasets/MULTPL/SHILLER_PE_RATIO_MONTH.csv` (Quandl/Nasdaq Data Link mirror) | Egress-proxy policy denial |
| `https://www.quandl.com/...` | Egress-proxy policy denial |
| `https://stooq.com/...` | Egress-proxy policy denial |
| `https://datahub.io/core/s-and-p-500/r/data.csv` | Egress-proxy policy denial |
| `https://img1.wsimg.com/...` (a known Shiller-data mirror host) | Egress-proxy policy denial |
| `https://fred.stlouisfed.org/graph/fredgraph.csv?id=CP` (Corporate Profits After Tax, NIPA) | **200 OK** |
| `https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL` (CPI-U) | **200 OK** |

No source that serves Shiller's own literal CAPE number, or any
third-party PE/earnings-multiple table, is reachable in this environment.
FRED (already the data source for every macro series this codebase uses,
per `src/backtest/v2/data.py`'s `fetch_fred` and `src/backtest/v2/
regimes.py`'s ALFRED vintage fetches) **is** reachable, and it hosts
public, free, long-history series that can be combined into a
Shiller-style P/E10 (CAPE-shaped) valuation ratio:

- `CP` -- Corporate Profits After Tax (NIPA, quarterly, nominal), 1947 to
  present. Used as the earnings-proxy input, in place of Shiller's own
  bottom-up S&P 500 reported EPS series (which is not reachable here).
- `CPIAUCSL` -- CPI-U (monthly), 1947 to present. Used to convert both
  the profits series and SP500's own price into real (inflation-adjusted)
  terms, exactly as Shiller's CAPE construction does.

**This is an explicit, documented substitution of the earnings input,
not a different mechanism.** The construction -- real price divided by a
smoothed multi-year average of real earnings -- is unchanged from
Shiller's CAPE; only the specific earnings series differs (aggregate
NIPA corporate profits rather than S&P 500's own reported EPS), because
the latter is not reachable in this environment. This is analogous to how
family 006 and 007 built calendar-timing mechanisms from the asset's own
trading-day index rather than a vendor calendar file -- using the best
available legitimate free data for the declared mechanism, not inventing
a new one. The resulting ratio's absolute *level* will not numerically
match Shiller's own published CAPE (different earnings base, different
units) -- **this is not a problem for the strategy's design**, because the
sizing signal only ever uses the ratio's own **point-in-time percentile
rank within its own trailing history** (see "Point-in-time discipline"
below), which is invariant to the ratio's absolute scale.

**Limitation, flagged explicitly:** `CP` is a NIPA series subject to
periodic BEA revision (comprehensive/annual benchmark revisions), and
this implementation uses FRED's **current, single-vintage** series with a
fixed publication-lag offset (see below) -- not a full ALFRED
point-in-time vintage series (unlike `regimes.py`'s `FEDTARMD` dot-plot
fetch, which does pull distinct ALFRED vintages by `vintage_date`). This
follows the **existing precedent already established in this codebase**
(`src/backtest/v2/data.py`'s `weekly_fred_lagged`, used for `UNRATE`/`TCU`
in Strategy D, applies a fixed lag to FRED's current series the same
way, not full ALFRED vintaging) rather than a new, weaker standard
invented for this family. Full ALFRED vintage-diffing for `CP` across
~300 quarters was considered and not attempted in this iteration's time
budget; the risk this leaves is that a quarter's real profits figure, as
used many years later in a 40-quarter trailing average, may reflect a
later BEA revision rather than the figure that was actually known at the
time -- profits revisions are typically modest in magnitude relative to
the multi-year smoothing window this signal already applies, but this is
a real, not fully eliminated, point-in-time gap and is reported as such
in results.md, not hidden.

## Point-in-time discipline (sec 3.2 check 4)

- **Publication lag, `CP` (quarterly):** a quarter's corporate-profits
  observation (FRED dates it to the quarter's *start* month) is treated
  as usable only from **6 calendar months after that start date** (i.e.
  ~3 months after the quarter's end) -- a conservative estimate of BEA's
  release cadence for corporate profits, which are finalized later than
  GDP's own headline advance estimate. This mirrors, but is more
  conservative than, `v2/data.py`'s existing 2-month lag convention for
  monthly `UNRATE`/`TCU` (a longer lag for a lower-frequency, later-
  finalized NIPA series is the conservative direction).
- **Publication lag, `CPIAUCSL` (monthly):** a month's CPI observation is
  usable from the first day of the month **2 months later**, identical
  to `v2/data.py`'s existing `weekly_fred_lagged` convention (reused
  directly, same lag value, for consistency with the rest of the
  codebase).
- **Real-terms construction:** each quarter's nominal corporate profits
  are deflated by CPI for that **same quarter** (CPI's own 2-month lag
  clears well before CP's 6-month lag does, so by the time a quarter's
  profits figure is usable at all, that quarter's CPI is already known --
  no additional gating needed there). The 40-quarter (10-year) trailing
  average of these real-profit figures is then itself release-lagged by
  the same `CP` publication-lag rule (keyed off its most recent
  contributing quarter), and forward-filled onto the daily calendar.
  Today's nominal SP500 close is deflated by the CPI level "as of day t"
  (point-in-time, 2-month lag) to get a real price in the same real-terms
  base. Ratio = real price (as of day t) / trailing-10-year average real
  earnings (as of day t, release-lag applied).
- **Percentile rank, point-in-time:** the sizing signal is this ratio's
  own **percentile rank within a trailing `pctile_window_years`-long
  window ending at day t (inclusive), using ONLY ratio values already
  computed as of day t** -- implemented as a trailing (not centered)
  rolling-window rank (`pandas.Series.rolling(window).rank(pct=True)`,
  which by construction only looks backward from each row), never a
  full-sample percentile. This directly satisfies the task's explicit
  point-in-time requirement for this family ("only use CAPE percentile
  ranks computable from data available up to that date, not the
  full-sample distribution"). Verified with an added no-lookahead
  perturbation check specifically targeting this construction (see
  "Additional implementation check" below), on top of the standard
  sec 3.2 check 3.
- **No price-lookahead in the ratio itself:** the ratio's numerator
  (real price) uses only today's close; the denominator (smoothed real
  earnings) depends only on macro data (CP, CPIAUCSL) and is entirely
  independent of price, so it introduces no price-lookahead risk at all
  -- only the standard macro-publication-lag risk addressed above.

## Exact rules

Computed once per asset (SP500 only) using
`src.backtest.v3.data.load_dev(["SP500"])` for price, and
`src.backtest.v2.data.fetch_fred("CP")` / `fetch_fred("CPIAUCSL")` for the
earnings/CPI inputs (same fetch/cache mechanism the rest of the codebase
already uses for macro data; the v3 data gate itself, `data.py`'s
`_ALLOWED_RAW_DATA_FUNCS` static check, only governs OHLC price data --
these macro series are handled exactly as `regimes.py` already does for
Strategy D's macro inputs, imported the same way).

- **On the week's last trading day (`is_week_end`, engine sec 3.2's
  existing convention -- the only day a decision needs to be made, since
  the valuation signal changes slowly and every deposit is credited on
  this day):**
  - Read `pctile_t`, this day's point-in-time percentile rank (0-100) of
    the valuation ratio within its own trailing `pctile_window_years`
    window. If not yet computable (insufficient trailing history --
    happens only in SP500's earliest development years, well before any
    macro data existed at all), **use multiplier = 1.0 (behaves exactly
    like plain DCA)** until the signal becomes available -- a
    pre-registered fallback, not a tuned choice.
  - Compute the sizing multiplier `m(pctile_t)`:
    - `pctile_t <= low_pctile`: `m = max_mult` (cheap -- buy more).
    - `pctile_t >= high_pctile`: `m = min_mult` (expensive -- buy less).
    - Otherwise: linear interpolation between `max_mult` (at
      `low_pctile`) and `min_mult` (at `high_pctile`).
  - Buy `min(cash, m * weekly_deposit)`. `cash` includes this week's
    $500 deposit plus any cash banked from prior weeks (when `m < 1`)
    plus interest earned on it (engine sec 3.2) -- so a sustained cheap
    regime can draw down banked cash faster than the current week's
    deposit alone, and a sustained expensive regime banks cash for a
    later cheap regime to draw on. No leverage: `m` is bounded by
    `[min_mult, max_mult]`, both pre-declared, and every buy is
    cash-capped by the engine itself (sec 3.2).
- **On every other trading day:** no order (0 buy, 0 sell) -- this
  family's signal only needs weekly evaluation, since the underlying
  quarterly-earnings-based ratio moves far too slowly to justify daily
  re-sizing, unlike family 007's day-of-week signal which genuinely
  needed daily evaluation for its own reasons.
- **No sells, ever** -- like every prior sizing/timing family in this
  loop (003/004/005/006/007), this is a pure buy-size-within-a-fixed-
  schedule rule, never a rule that liquidates existing units.

## Data inputs

- SP500 (`^GSPC`) daily OHLC via `src.backtest.v3.data.load_dev()` only.
- FRED `CP` (quarterly) and `CPIAUCSL` (monthly) via
  `src.backtest.v2.data.fetch_fred()` (same mechanism `regimes.py` already
  uses for other FRED series; cached under `data/CP.csv` and
  `data/CPIAUCSL.csv`).

## Parameters (5 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `pctile_window_years` | 15, 20 | 20 |
| `low_pctile` | 20, 30 | 20 |
| `high_pctile` | 70, 80 | 80 |
| `max_mult` | 1.5, 2.0 | 2.0 |
| `min_mult` | 0.3, 0.5 | 0.5 |

`pctile_window_years=20` is the primary -- long enough to span multiple
valuation cycles (the whole point of a percentile-rank approach is to
avoid a lookahead-biased fixed absolute CAPE threshold; a longer trailing
window is the more literature-faithful choice, closer to using "most of
the available history" the way Shiller's own commentary typically does,
while still being genuinely point-in-time). `low_pctile=20`/`high_pctile
=80` (bottom/top quintile) is the primary -- a clean, literature-standard
quintile split (Asness et al.-style valuation-quintile tilts), not tuned
on this loop's own data. `max_mult=2.0`/`min_mult=0.5` is the primary --
a full 4x range between the cheapest and richest sizing band, large
enough to be economically meaningful without being extreme, and
symmetric in log-space around 1.0 (`log(2.0) = -log(0.5)`), which is a
principled, not-tuned choice for where the deposit multiplier should be
"centered."

## Grid

2 (`pctile_window_years`) x 2 (`low_pctile`) x 2 (`high_pctile`) x 2
(`max_mult`) x 2 (`min_mult`) = **32 configurations** (<= 36 cap; 5 params
<= 5, at the parameter cap).

## Primary configuration

`pctile_window_years=20, low_pctile=20, high_pctile=80, max_mult=2.0,
min_mult=0.5`.

## Expected sign

**Positive on SP500's wealth and Sharpe, if the CAPE mean-reversion
literature's long-horizon return predictability holds up within this
strategy's specific construction (weekly buy-size tilts within a fixed
deposit schedule, not a standalone valuation-timed portfolio) and survives
this loop's fee/robustness bar.** This is stated as the loop's honest
prior, not a certainty: the literature's own predictive power is
documented primarily at long (5-10 year) forward horizons using total-
sample-regression methods, which is a different statistical claim from
"a weekly buy-size tilt, evaluated by final wealth and Sharpe of NAV
returns over one specific ~90-year development sample, passes sec 4.2's
DSR bar net of transaction costs." A real risk, flagged here before any
backtest, exactly parallel to every prior sizing/timing family's own
pre-registered risk: **CAPE has historically spent very long stretches on
one side of any given percentile threshold** (e.g., US equity valuations
were persistently elevated for most of the 1990s-2000s and again in the
2010s-2019 relative to their own trailing-20-year percentile in many
readings) -- if the development-period path happens to bank cash through
a multi-year rich-valuation stretch immediately followed by (or during) a
period of strong nominal price appreciation, this family could
underperform DCA on wealth for the same structural reason families 003,
006 and 007 did on their own most valuation/regime-sensitive assets,
regardless of whether the underlying mean-reversion thesis is directionally
correct over a longer horizon than this development sample covers.

## Degenerate configuration (implementation check only, not a grid arm)

`enabled=False`: bypasses the valuation-ratio/percentile/multiplier
computation entirely and forces the exact same decision DCA's own decider
makes (buy 100% of that week's cash on every week-end day, 0 on every
other day) -- reproduces plain DCA bit-for-bit, same pattern as families
001-007's `enabled=False` checks.

## Additional implementation check (beyond the standard four, specific to
this family's point-in-time percentile construction)

**No-lookahead check targeted at the percentile-rank construction
itself**, on top of the standard sec 3.2 check 3 (which perturbs price
data after day t and confirms orders on/before t are unchanged): since
this family's signal is a *rolling percentile rank* rather than a raw
level, a bug in the rolling-window construction (e.g. an off-by-one that
lets a centered or forward-looking window leak in) would not necessarily
be caught by a single spot-check far from the window boundary. This
family's `check_no_lookahead` call is run at **multiple `t_check` points
spanning both the start of the meaningful signal era (shortly after the
earliest point CP/CPIAUCSL data makes the ratio computable at all) and a
late point in the development sample**, not just one arbitrary interior
day, specifically to stress-test the rolling-percentile boundary
behavior. Declared here, before any backtest, exactly which two `t_check`
points will be used: the first trading day of 1990 (well after the
earliest 40-quarter real-earnings average becomes available, but still
early enough to be within a shorter effective percentile-window history)
and the last trading day of 2018 (near the end of the development
sample).
