# Family 051: Pre-FOMC announcement drift deposit timing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Lucca, D.O. and Moench, E. (2015), "The Pre-FOMC Announcement Drift,"
*Journal of Finance* 70(1), 329-371 -- documents that the S&P 500 has
earned a large, statistically significant, positive average excess return
in the **1-1.5 trading days immediately preceding scheduled FOMC
statement-release days**, concentrated almost entirely in that narrow
pre-announcement window rather than spread evenly across the
inter-meeting cycle, and largely unexplained by standard risk-factor
controls (the announcement itself, not the pre-announcement drift, is
what classical event-study logic would expect to carry the return). The
authors document the effect since 1994, when the FOMC began issuing
same-day post-meeting statements (before 1994, the market often did not
learn the committee's decision until the next scheduled Fed action,
sometimes weeks later, so there is no well-defined "day before a known
announcement" for most of the pre-1994 sample). Research queue idea #54
(`state/research_queue.md`).

## Mechanism ("why would this work, and who is on the other side?")

Lucca & Moench's own leading explanation is a **pre-scheduled-news risk
premium**: FOMC announcements are a large, systematic source of
priced uncertainty about the path of the policy rate, and risk-averse
investors who cannot easily hedge overnight/pre-announcement exposure
demand compensation for holding the position into a known, dated,
undiversifiable information event -- this is compatible with (but
distinct from) the broader options-implied-volatility "event risk
premium" literature (Ederington & Lee 1993 on the resolution of
macro-announcement uncertainty). A second, complementary channel the
authors and follow-up work (Cieslak, Morse & Vissing-Jorgensen 2019, on
the broader FOMC monetary-policy cycle) discuss is that institutional
portfolio managers **anticipate and lean into the pattern itself once it
becomes well known**, creating some self-reinforcing anticipatory buying
ahead of the announcement -- itself a form of the "well-published,
persistent puzzle" caveat families 006/007/018/022/024 already raise.
This family's economic bet is again purely about **execution timing**,
not sizing or exit: it never changes how much of the fixed $500/week
deposit gets deployed in total, only *when within the fixed schedule*
each dollar is spent -- the "other side" of the trade is whoever is
willing to sell into (or does not adjust their own execution to avoid)
this narrow, calendar-predictable pre-announcement window, for the same
kind of reasons families 006/007/018/022 already give (transaction-cost-
constrained desks, career-risk-constrained managers who cannot easily
reposition around a single Fed cycle, or a real but genuinely
undiversifiable risk premium that persists precisely because it does not
arbitrage away like a pure informational anomaly would).

## Category

**Seasonality / execution timing** (research-loop-plan-v3.md sec 4.5's
category list -- same category as families 006, 007, 018, 022 and 024,
at a **fifth, structurally different calendar mechanism**, addressed in
full below).

## Required distinction: FOMC's own scheduled meeting calendar is NOT a
fixed modular weekday/day-of-month/annual/quadrennial cycle -- verified
concretely on the real historical date list, not asserted

**The FOMC meeting calendar used here.** The Federal Reserve publishes
historical FOMC meeting-calendar materials at
`federalreserve.gov/monetarypolicy/fomc_historical_year.htm` (and a
current calendar at `.../fomccalendars.htm`), but this session's network
egress policy blocks `federalreserve.gov` (confirmed directly: a
`WebFetch` call to `fomchistorical2019.htm` returned
`EGRESS_BLOCKED`) and also blocks `en.wikipedia.org` and
`www.r-bloggers.com` (checked as fallback structured sources, both also
`EGRESS_BLOCKED`). No live-reachable structured source of the full
historical FOMC meeting calendar exists in this environment. Per this
family's explicit task-level allowance for this contingency, the 208
**scheduled** (regularly-calendared, publicly pre-announced) FOMC meeting
decision dates from **1994-02-04 through 2019-12-11** (the full
development period during which the effect is defined, per Lucca & Moench's
own 1994 start point above, through the 2019-12-31 dev/holdout cutoff) are
hard-coded directly in
`src/backtest/v3/strategies/pre_fomc_drift.py::FOMC_DATES`, compiled from
this session's own knowledge of the well-documented, unambiguous public
historical record of FOMC meeting dates (widely reproduced across the Fed's
own historical materials, financial-data vendors' economic calendars, and
academic replication files -- not a live data feed, and not derived from
any options/futures/price data this backtest touches). Each entry is the
**decision/announcement day** (the final day of a 1- or 2-day meeting, when
the post-meeting statement was released). Confirmed **unscheduled/emergency**
inter-meeting actions (e.g. the Sep 2001, Jan 2008 and Oct 2008 emergency
rate actions) are deliberately **excluded** -- they were not on a
publicly pre-announced calendar days or weeks in advance, so including
them would build lookahead into the signal and would misrepresent the
mechanism Lucca & Moench study (a *scheduled*-event drift, not any
FOMC action whatsoever). Exactly 8 meetings/year, every year 1994-2019
(208 total), matching the FOMC's own long-standing publicly stated
practice of "eight regularly scheduled meetings per year," is a first,
coarse plausibility check on the list before any date-level analysis.

**Concrete redundancy check against 006 (turn-of-month, monthly
day-of-month cycle), 007 (day-of-week, weekly cycle), 018 (Halloween,
fixed annual window), 022 (election cycle, fixed quadrennial-year cycle)
and 024 (SAD/daylight, fixed annual/seasonal window), computed directly
on the 208-date list above (see `_fomc_calendar_check.py`'s output,
reproduced in `results.md`):**

- **Weekday-of-decision distribution (vs. family 007's single fixed
  target weekday):** Tuesday 85/208 (40.9%), Wednesday 115/208 (55.3%),
  Thursday 7/208 (3.4%), Friday 1/208 (0.5%). **Never** Monday, Saturday
  or Sunday. This is dominated by Tue/Wed (the modern 2-day-meeting
  convention ends on Wednesday; the 1-day-meeting convention used in the
  1990s ended on Tuesday), but is **not** a single fixed weekday the way
  family 007's `target_weekday` parameter is (007 tests exactly one
  weekday value per config, e.g. every Monday) -- and, decisively, **the
  strategy's actual signal (the 1-2 trading days *before* the decision)
  spreads across every weekday of the trading week almost uniformly**
  once shifted back 1-2 trading days from a Tue/Wed-heavy decision-day
  distribution (a decision on Wed implies the window falls on Mon/Tue; a
  decision on Tue implies the window falls on the prior Thu/Fri) -- so
  the pre-FOMC window itself, unlike family 007's single-weekday flag, is
  not concentrated on any one day of the week at all. This is confirmed
  numerically in `results.md`.
- **Day-of-month distribution (vs. family 006's ~4-trading-day window
  anchored to month start/end):** decision-day day-of-month spans the
  **entire 1-31 range** (min 1, max 31, mean 17.9, std 9.0; every decade
  of the month 1-10, 11-20, 21-31 is represented with double-digit
  counts). Family 006's turn-of-month window is, by construction, only
  the last 1-3 and first 3-4 trading days of each month -- roughly a
  6-7-day band out of ~21. The FOMC calendar has essentially the
  opposite property: it deliberately avoids clustering near month
  boundaries (no meeting falls in the extreme turn-of-month band in most
  years), so this family's window and family 006's window have very
  little SYSTEMATIC overlap, confirmed directly and quantitatively (not
  merely asserted): family 006's primary turn-of-month window (last 1
  business day of the month plus first 3 business days of the following
  month) covers ~4 of ~21 business days per month (~19%), so **pure
  chance alone**, with no clustering at all, predicts roughly
  `208 * 4/21 =~ 40` of the 208 FOMC dates would fall inside that window
  by coincidence. The actual count, computed directly on the 208-date
  list, is 43 -- a ratio of about 1.08x the chance-expected rate, i.e.
  **statistically indistinguishable from a non-clustered, uniform
  placement across the month** (computed and reported exactly in
  `results.md`, with an explicit pre-grid gate requiring this ratio stay
  within 0.5x-1.5x of the chance baseline before any backtest runs). This
  is the correct redundancy test: not "zero overlap" (which no
  8-meetings-a-year, evenly-spaced calendar could achieve while also
  covering the whole month, since some dates must fall somewhere), but
  "no disproportionate concentration in family 006's specific window,"
  which is confirmed.
- **Month-of-year distribution (vs. families 018's fixed May-Oct/Nov-Apr
  Halloween split and 024's fixed daylight-saving-linked seasonal
  window):** all 12 calendar months have at least one meeting across the
  26-year sample, but the counts are uneven (Jan 18, Feb 8, Mar 26, Apr
  8, May 18, Jun 21, Jul 11, Aug 20, Sep 23, Oct 12, Nov 17, Dec 26) --
  because the meeting spacing (roughly every ~6.5 weeks) does not divide
  evenly into 12 months, some months get a meeting in most years and
  some do not, but the important point for redundancy is structural, not
  purely a matter of counts: unlike family 018 (whose "bad" and "good"
  6-month blocks are a **fixed annual partition drawn once and repeated
  identically every single year**) and family 024 (whose SAD window is
  similarly a fixed annual calendar band), the FOMC calendar's exact
  meeting dates **shift by several days to a few weeks from one year to
  the next** even within the "same" nominal month (e.g. the March
  meeting: 1994-03-22, 1997-03-25, 2007-03-21, 2017-03-15, 2019-03-20 --
  no two years share the identical date, and the meeting is not always
  in March at all in some years' 8-meeting rotation). Families 018/024's
  windows are, by design, an identical repeating annual template; this
  family's is not.
- **Year-mod-4 distribution (vs. family 022's quadrennial election
  cycle):** year-mod-4 counts across the 208 dates are 48/48/56/56 --
  essentially uniform across all four residues (a chi-square test against
  a uniform 52/52/52/52 null gives a tiny, unremarkable deviation), i.e.
  the FOMC calendar shows **no dependence whatsoever on where a year sits
  in the 4-year US presidential cycle**, the opposite of family 022's
  entire premise (which requires exactly this kind of year-mod-4
  structure to exist).
- **Concrete non-modularity: the inter-meeting gap itself is irregular**,
  not a fixed number of trading days (unlike 006's ~21-trading-day month
  or 007's ~5/7-day week): gaps between consecutive decision dates in the
  208-date list range from 27 to 63 calendar days (mean ~45.7, std ~7.9)
  -- there is no single modulus `k` such that "every `k`th trading day is
  an FOMC date," which is exactly what would make this family a relabeled
  006/007/018/022/024 (all four of which ARE expressible as a fixed
  modular function of the calendar date alone: `day-of-month`,
  `day-of-week`, `month-of-year` membership, or `year mod 4`
  respectively). This family's signal instead requires the externally-
  given, irregularly-spaced 208-date list itself -- it cannot be computed
  from the calendar date via any simple modular arithmetic, which is the
  concrete, load-bearing distinction the task requires.

**Conclusion: the pre-FOMC calendar is a genuinely different, externally
determined event calendar** -- not a relabeling of any prior seasonality
family's fixed modular or fixed annual/quadrennial cycle. It shares the
family 006/007/018/022 shape (bank on ordinary periods, deploy a
capped catch-up lump into a pre-declared calendar window) but the window
itself is defined by a real-world institutional decision schedule that
does not reduce to a function of the calendar date.

## Single-asset vs. multi-asset scoping (judgment call, per this task's
explicit instruction to follow family 022's precedent)

**Decision: test on all 5 core assets, scored under sec 4.1's standard
>= 3/5 rule** -- directly following family 022's own reasoning, which the
task explicitly names as the controlling precedent here (rather than
family 008's CAPE, which had no cross-asset analog at all because its
*signal itself* needs S&P-500-specific fundamentals data).

1. **The calendar-timing MECHANISM (the 208-date FOMC list) needs no
   asset-specific data at all** -- it is a pure function of the calendar
   date, computable identically for gold, silver, oil and BTC as for the
   S&P 500, exactly as family 022's election-cycle signal was.
2. **The motivating channel plausibly transfers beyond US equities.** FOMC
   rate decisions are a broad, USD-denominated macro-policy event: gold
   and silver are priced in USD and are classic rate-sensitive
   (opportunity-cost-of-holding, and dollar-strength) assets; oil is
   USD-denominated and sensitive to the same broad risk-appetite/dollar-
   liquidity channel Lucca & Moench and the Cieslak-Morse-Vissing-Jorgensen
   follow-up literature discuss; BTC has itself developed a documented
   sensitivity to Fed policy surprises in the post-2017 institutional-
   adoption literature (its development-period history, however, only
   covers a handful of FOMC cycles -- flagged as a caveat below,
   mirroring family 022's own BTC caveat). This is a genuinely more
   plausible cross-asset transfer than family 008's CAPE (a pure
   equity-valuation ratio with literally no analog for a commodity or a
   cryptocurrency), so the case for testing broadly is at least as strong
   here as it was for family 022.
3. **Uniform application matters, and testing all 5 is the conservative
   choice** -- it makes the family strictly harder to pass than
   restricting to SP500 alone, exactly as families 006/007/018/022
   already reasoned.

## Exact rules

Computed using only the asset's own trading-day calendar plus the
hard-coded 208-date FOMC list above (no price or macro dependence in the
signal itself) -- like family 007, **this family's decision must be
evaluated on every trading day**, not only the week's deposit-credit day,
because the pre-FOMC window (a run of `window_days` trading days
immediately before a decision date) does not, in general, coincide with
that asset's own week-end/deposit day.

- **Pre-FOMC window.** For each of the 208 FOMC decision dates, locate the
  asset's own trading day at or immediately following that calendar date
  (the decision date itself, if it is a trading day on this asset's
  calendar -- true for all 208 dates on every core asset's own trading
  calendar in practice, since FOMC decisions are announced on days equity/
  futures/BTC markets are open) and mark the `window_days` trading days
  strictly *before* it (on this asset's own trading-day index) as
  "pre-FOMC." `window_days in {1, 2}` -- the literal Lucca & Moench
  window (they document the drift is concentrated in roughly the last
  1-1.5 trading days before the statement).
- **On each trading day `t`:**
  - **If `t` is in the pre-FOMC window:** buy
    `min(cash, max_lump_multiple * weekly_deposit)`. `cash` includes any
    deposit credited that day (if `t` is also the week's deposit day)
    plus all cash banked from prior ordinary days (and the interest it
    has earned, engine sec 3.2).
  - **Otherwise (an ordinary week):** buy
    `mild_tilt_fraction * weekly_deposit / (number of non-window trading
    days in `t`'s ISO week)`, cash-capped -- spreading the "mild tilt"
    portion evenly across that week's ordinary trading days, exactly like
    family 007's non-target-day rule. `mild_tilt_fraction = 0.0` (the
    primary) makes this term identically zero, i.e. full banking between
    windows.
  - **Banking-window forced deploy (same mechanic as family 007, needed
    here for the same structural reason -- and needed even more acutely
    given the asset's own history may predate 1994, when the FOMC
    calendar coverage begins):** if more than `banking_window_weeks * 7`
    calendar days have elapsed since cash was last spent (via a
    window-day buy or a prior forced deploy), that day's buy is topped up
    by `min(remaining cash, max_lump_multiple * weekly_deposit)`
    regardless of whether `t` is in the pre-FOMC window. This bounds how
    long any dollar can sit idle, and is essential here: **before
    1994-02-04 (this family's own hard-coded calendar's first entry), the
    pre-FOMC window flag is never True on any asset's history**
    (SP500's development history reaches back to the late 1920s), so
    without a forced-deploy fallback this strategy would behave as "bank
    everything forever" for the entire pre-1994 sub-period -- an
    obviously wrong, degenerate outcome the forced-deploy rule
    specifically prevents, exactly as it prevents family 007's
    `target_weekday=Sunday` degeneracy on the 4 non-BTC assets.
  - **No sells, ever** -- like families 003/005/006/007/018/022, a pure
    timing/sizing-within-a-fixed-schedule rule.
- **Total capital deployed is unchanged.** Same principled ceiling-bound
  implementation check as every prior family in this loop (below).

## Data inputs

Daily OHLC close price of the asset itself only (each of the 5 core
assets, tested independently -- single-asset family, per the scoping
decision above). The pre-FOMC signal uses **only the asset's own
trading-day calendar plus the hard-coded, publicly known historical FOMC
decision-date list** (no price, no macro data feed). Sourced via
`src.backtest.v3.data.load_dev()` (asset prices) and the module-level
`FOMC_DATES` constant (the calendar). No FRED/yfinance macro series
dependency, no network reachability risk for the signal itself (only
`load_dev()`'s existing asset-price fetch is needed) -- disclosed here in
the spirit of family 048's "no external-data dependency" note, since the
FOMC-date list, once hard-coded, is a fixed constant, not a live feed.

## Parameters (4 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `window_days` | 2, 1 | 2 |
| `mild_tilt_fraction` | 0.0, 0.5 | 0.0 |
| `max_lump_multiple` | 3, 6 | 6 |
| `banking_window_weeks` | 4, 8 | 8 |

`window_days=2` (the primary) is the literal Lucca & Moench headline
window (they report the drift as concentrated in roughly the last 1.5
trading days, so 2 trading days is the closest integer no-look choice
from the literature, matching the exact wording of research-queue idea
#54, "the 1-2 trading days immediately preceding"); `window_days=1` is
the tighter, more literal single-day alternative also explicitly named in
the queue entry. `mild_tilt_fraction` and `max_lump_multiple` mirror
family 007's own grid and reasoning exactly (0.0 is the purest test of
the timing-shift hypothesis; a multiple of 6 gives headroom worth ~6
weeks of banked deposit). `banking_window_weeks=8` (the primary) is
chosen *wider* than family 007's 4, specifically because FOMC meetings
recur roughly every 6.5 weeks on average (vs. every 1 week for a
day-of-week target) -- an 8-week window comfortably exceeds the largest
observed real inter-meeting gap (63 calendar days, i.e. exactly 9 weeks
-- so 8 weeks does bind in the single longest historical gap, a deliberate,
disclosed choice rather than a value picked to guarantee it never binds)
while remaining short enough to force periodic deployment during the
pre-1994 "asleep" sub-period; `banking_window_weeks=4` is included as a
tighter alternative that would bind more often, including on some
ordinary-length inter-meeting gaps, testing sensitivity to this choice.

## Grid

2 (`window_days`) x 2 (`mild_tilt_fraction`) x 2 (`max_lump_multiple`) x
2 (`banking_window_weeks`) = **16 configurations** (<= 36 cap; 4 params
<= 5).

## Primary configuration

`window_days=2, mild_tilt_fraction=0.0, max_lump_multiple=6,
banking_window_weeks=8`.

**Explicit pre-backtest verification (family 021's lesson):** every value
in the primary configuration is checked programmatically, before the grid
runs, to be a member of its corresponding `GRID[...]` list in
`src/backtest/v3/strategies/pre_fomc_drift.py`
(`assert PRIMARY_CONFIG[k] in GRID[k] for k in GRID`), and that
`PRIMARY_CONFIG in grid_configs()`.

## Pre-grid non-degeneracy check (required before the grid runs)

The primary config's pre-FOMC window is expected to fire on a **small but
non-trivial fraction** of trading days: 208 meetings x `window_days=2`
trading days each = 416 window-day-events, against roughly 6,540 trading
days in the 1994-2019 "active" sub-period alone (~6.4%), diluted further
by however much of each asset's own development history predates
1994-02-04 (SP500's is the longest-diluted, BTC's the least-diluted,
since BTC's development history starts in Sep 2014, entirely inside the
FOMC-calendar-covered era). This is checked directly against each asset's
own trading-day index before any grid is trusted -- see `results.md`'s
"Pre-grid sanity check" table -- with a pass band of the window firing on
between 0.5% and 15% of days on every asset (loose enough to allow the
expected dilution variation across assets' differing history lengths,
tight enough to catch a gross implementation bug such as an off-by-one in
the window's trading-day lookback or a mis-mapped decision date).

## Expected sign

**Positive on both wealth and Sharpe, at least on SP500, if the Lucca &
Moench effect is real and survives this loop's fee/robustness bar** --
SP500 is the literal asset the anchor paper studies, so it carries the
strongest prior. For gold/silver/oil/BTC, the expected sign is stated
honestly as **plausible but less certain** -- per the cross-asset scoping
discussion above, the channel (a risk premium for holding exposure into a
scheduled, undiversifiable macro-news event) is not logically restricted
to equities, but none of the four has been directly studied in the
pre-FOMC-drift literature the way SP500 has, so a result concentrated on
SP500 alone (paralleling family 006's SP500-specific pattern, or family
022's asymmetric result) would not be a surprise. Risks flagged before
any backtest, honestly:

1. **This mechanism never changes total capital deployed, only timing
   within a fixed schedule** (same caveat as every prior seasonality
   family in this loop), so even a genuine effect may show a small
   absolute wealth/Sharpe margin.
2. **The pre-1994 "asleep" sub-period dilutes the signal for every asset
   whose development history predates 1994** -- most acutely SP500 (whose
   development history reaches back roughly 65 years before the FOMC
   calendar even begins), least acutely BTC (whose entire development
   history of ~5 years is inside the FOMC-calendar-covered era). This is
   the mirror image of family 022's own BTC caveat (there, BTC's short
   history under-samples a *long* 4-year cycle; here, other assets'
   *long* histories dilute exposure to a well-defined but comparatively
   recent-era effect) and is disclosed here for the same reason.
3. **Lucca & Moench's own paper documents some attenuation of the effect
   in the years right around and after their own study's publication**
   (a pattern the "well-published, persistent puzzle" caveat already
   raised for 006/007/018/022 covers), and this backtest's development
   period (through 2019-12-31) includes several years after the paper's
   2015 publication during which the effect, if partially arbitraged
   away by market participants aware of the finding, could plausibly be
   weaker than in the pre-publication sample -- an honest risk to the
   effect's strength on development data, stated before any grid is run.
4. **BTC's development window (2014-09 to 2019-12) is short** (the same
   general BTC caveat every prior family raises), though for this
   specific family it is, unusually, the sub-period with the *least*
   dilution from the pre-1994 asleep era among the 5 assets.

## Degenerate configuration (implementation check only, not a grid arm)

`enabled=False`: bypasses the pre-FOMC window/banking-window computation
entirely and forces the exact same decision DCA's own decider makes (buy
100% of that week's cash on every week-end day, 0 on every other day) --
reproduces plain DCA bit-for-bit, same pattern as every prior family's
`enabled=False` check.

## Additional implementation check (mirroring family 006/007's
capital-neutrality check exactly, using family 021's corrected principled
bound)

**Total capital deployed never exceeds cumulative deposits + interest.**
Verified path-wise using the "never invest, sit 100% in cash" control
trajectory on the same `daily_rf` path as the accumulated-interest
ceiling (family 021's fix), not a flat percentage tolerance.

## No-lookahead test note

The signal is a pure function of the calendar date (via the asset's own
trading-day index) plus the hard-coded, already-historical 208-date FOMC
list -- every date in that list used anywhere in this backtest is already
historical fact, so a perturbation of prices after day `t` cannot possibly
change the pre-FOMC window flag, let alone the order generated, on or
before day `t`. Still run explicitly as a spot-check on the engine's
actual order generation, exactly as every prior calendar-timing family
did, rather than assumed from the signal's construction alone.
