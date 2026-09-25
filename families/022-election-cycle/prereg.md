# Family 022: Presidential election-cycle deposit timing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Santa-Clara, P. and Valkanov, R. (2003), "The Presidential Puzzle:
Political Cycles and the Stock Market," *Journal of Finance* 58(5),
1841-1872 -- documents that average US equity excess returns are
significantly higher during the second half of the four-year
presidential term (the two years leading up to, and including, a
presidential election) than during the first half (the two years right
after an election, including the midterm year), a pattern the authors
show survives standard risk-factor controls and is not explained by
business-cycle variables alone. Research queue idea #22
(`state/research_queue.md`).

## Mechanism ("why would this work, and who is on the other side?")

Santa-Clara & Valkanov's own leading explanation is **political**, not a
standard risk-based story: incumbent administrations (and the Federal
Reserve, to the extent monetary policy is not fully independent of the
political cycle) have a demonstrated incentive to steer fiscal policy,
transfer payments, and regulatory posture toward stimulating the economy
in the run-up to a re-election vote, and to defer painful adjustments
(tax increases, spending cuts, rate hikes) into the first half of a new
term when the next election is furthest away. If that incentive
systematically shows up in realized market returns -- not merely in GDP
or election-year fiscal deficits, which are separately well documented --
then a fixed-dollar DCA buyer investing the same $500 every week
regardless of where the country sits in its 4-year election cycle is
leaving a persistent, low-frequency, non-random timing pattern on the
table. The "other side" of this trade is less a specific identifiable
counterparty than with a liquidity-based seasonal (families 006/007/018):
it is closer to **market participants who are aware of the effect but
cannot act on it patiently** (long political cycles are hard for
career-risk-constrained active managers to trade around, and the effect
is diffuse enough that no single actor can arbitrage it away cheaply) --
this is the same "well-published, persistent puzzle" caveat families
006/007/018 raise, doubly relevant here since Santa-Clara & Valkanov's
own paper title calls it a "puzzle" specifically because it resists a
clean risk-based explanation. This family reallocates the *timing* of the
same total $500/week deposit stream across the ~4-year cycle -- it never
changes how much total capital gets deployed, no leverage, no shorting.

## Category

**Seasonality / execution timing** (research-loop-plan-v3.md sec 4.5's
category list -- same category as families 006, 007 and 018, at a
**fourth, much longer, and qualitatively different calendar
granularity**, addressed in full below).

## Why this is NOT a re-test of families 006, 007, 018, or sec 7.2's closed list

- **Not a re-test of sec 7.2's closed list:** no family in that list (v1
  buy-the-dip/trim-the-spike, v2 SmartDCA, v2 ADCA B1/B2, v2 rebalanced
  portfolios C1-C3, v2.1 rate-regime Strategy D) uses any calendar-based
  signal at all.
- **Not a re-test of families 006 (turn-of-month), 007 (day-of-week), or
  018 (Halloween/Sell-in-May) -- explicit, load-bearing distinction,
  since all four families share the "Seasonality / execution timing"
  category.** The four operate at **four different calendar
  granularities, each roughly an order of magnitude apart from its
  neighbor, each anchored to an independent literature and an independent
  proposed mechanism, and -- critically for this family -- this is the
  only one of the four whose regime label is NOT a repeating pattern
  within a fixed, shorter-than-a-year period:**
  - **Family 006** is a **monthly** cycle: `f(day-of-month)`, a
    ~4-trading-day window recurring every ~21 trading days (payroll/fund-
    flow rebalancing cycle; Ariel 1987, Lakonishok & Smidt 1988).
  - **Family 007** is a **weekly** cycle: `f(day-of-week)`, a single
    weekday recurring every ~5-7 calendar days (crypto weekday/weekend
    liquidity-composition shift; Caporale & Plastun 2019).
  - **Family 018** is an **annual** cycle: `f(month-of-year)`, a
    ~6-calendar-month window recurring once per year (summer vacation/
    risk-aversion cycle; Bouman & Jacobsen 2002).
  - **This family (022)** is a **quadrennial** cycle: `f(year-of-US-
    presidential-term)`, a ~2-calendar-year window recurring once every
    **4 calendar years** (~1,008 trading days), anchored not to a
    repeating within-year calendar pattern at all but to the **actual US
    presidential election calendar** (2000, 2004, 2008, 2012, 2016, 2020,
    2024, ...) -- a fixed, externally-given sequence of specific years,
    not a modular function of month or weekday. Its window (~2 years) is
    roughly 4x family 018's (~0.5 years), ~100x family 006's, and ~500x
    family 007's, and unlike all three, "which regime am I in right now"
    cannot be computed from the calendar date alone via a simple modular
    function of month-of-year or day-of-week/month -- it requires mapping
    the **calendar year** to a **cycle-year-of-term** (1-4) via the actual
    sequence of US election years, a structurally different computation
    from any of 006/007/018's.
  Each family cites independent literature, proposes an independent
  economic mechanism (fund-flow/payroll timing vs. crypto weekend
  liquidity vs. summer vacation risk-reduction vs. election-cycle fiscal/
  political incentives), and is evaluated on an entirely different,
  non-nested calendar period. This directly follows sec 7.2's own
  re-test standard ("a different signal definition or a different
  mechanism") and the precedent family 018 already established relative
  to 006/007.

## Single-asset vs. multi-asset scoping (judgment call, per this
iteration's explicit task instruction to follow the 006/007/018 precedent)

**Decision: test on all 5 core assets, scored under sec 4.1's standard
>= 3/5 rule.** This is explicitly a US-politics-motivated signal (the
literature is a US equity-market finding, tied specifically to the US
presidential election calendar), directly paralleling family 006's
(SP500-anchored) and 007's (BTC-anchored) precedent of testing an
asset-specific-literature signal across all 5 assets anyway, because:

1. **The calendar-timing MECHANISM is asset-agnostic even though the
   motivating literature is US-equity-specific.** The signal itself
   (which cycle-year of the US presidential term today's calendar date
   falls in) requires no asset-specific fundamentals data -- it is a pure
   function of the calendar date, computable identically for gold,
   silver, oil, and BTC as for the S&P 500. If the mechanism's political/
   fiscal-policy channel operates through broad risk appetite, monetary
   policy, or dollar liquidity conditions (channels Santa-Clara & Valkanov
   and follow-up literature discuss alongside the pure equity-return
   result), it is not a priori restricted to equities -- commodities and
   BTC are each exposed to US monetary/fiscal conditions and dollar
   liquidity through their own channels, even though none of them is the
   asset the original literature tested.
2. **This is the 006/007 precedent, not the CAPE/family-008 precedent.**
   Family 008 (CAPE valuation) was scoped as SP500-only because its
   *signal itself* requires asset-specific fundamentals data (an S&P 500
   earnings/valuation series) that has no principled analogue for gold,
   BTC, or oil -- a structural data-availability constraint, not a
   judgment call about literature scope. This family's signal needs
   **no fundamentals data of any kind**, only the calendar date, so the
   family-008 rationale for narrowing to one asset does not apply here at
   all; the 006/007 (and 018) precedent of "asset-agnostic mechanism,
   asset-specific motivating literature -> test across all 5, score under
   the standard >=3/5 rule" is the directly applicable one.
3. **Uniform application across families matters more than a one-off
   exception**, and testing all 5 assets is the conservative choice (it
   makes the family strictly harder to pass than restricting to SP500
   alone would), for the same reasons families 006/007/018 gave.

## Exact rules

Computed at each trading day `t` from the calendar year of `t` alone (no
price or macro dependence in the signal), decided only on week-end
decision days (matching every other v3 family's weekly cadence).

- **Cycle-year computation.** For calendar year `Y`: `cycle_year(Y) = 4`
  if `Y mod 4 == 0` (a US presidential **election year**: 2000, 2004,
  2008, 2012, 2016, 2020, 2024, ...), else `cycle_year(Y) = Y mod 4`
  (`1` = the year immediately after an election / post-election year,
  e.g. 2021; `2` = the midterm-election year, e.g. 2022; `3` = the
  pre-election year, e.g. 2023). This mapping is a pure function of the
  calendar year with no lookahead risk: US presidential election years
  are fixed, publicly known facts on every date in this dataset (the
  next one is never in doubt more than ~2 years out, and every date used
  in this backtest is already historical).
- **Weak/strong split.** `weak_years` = the first `n_weak_years` of
  `{1,2,3,4}` (i.e. `{1}` if `n_weak_years=1`, or `{1,2}` if
  `n_weak_years=2`); `strong_years` = the remaining years, with year 4
  (the election year itself) additionally moved from `strong_years` into
  `weak_years` when `include_election_year_in_strong=False`. A week-end
  day is "in a strong year" if `cycle_year(t.year)` is in `strong_years`.
- **Weekly decision (week-end days only).**
  - Strong-year week: buy `min(cash, max_lump_multiple * weekly_deposit)`.
    `cash` includes this week's $500 deposit plus any cash banked from
    prior weak-year weeks (and the interest it has earned, sec 3.2).
    Cash-capped, never leverage.
  - Weak-year week: buy `(1 - bank_fraction) * weekly_deposit`. The
    remainder, `bank_fraction * weekly_deposit`, is banked as cash
    (earning IRX per sec 3.2) until the next strong-year week.
  - **No sells, ever.** Same pure timing-within-a-fixed-schedule pattern
    as families 003/005/006/007/018.
- **On non-week-end days:** no order is generated (`buy_usd = sell_usd =
  0`), matching every prior calendar-timing family's cadence.
- **Total capital deployed is unchanged.** Every dollar bought traces
  back to the identical $500/week deposit schedule DCA uses (plus the
  same IRX interest on idle cash both strategies would otherwise earn).
  An explicit implementation check (below) verifies this using family
  021's corrected principled-bound approach (capital deployed minus
  cumulative deposits must never exceed the "never invest, sit 100% in
  cash" control trajectory's own accumulated interest), not a flat
  percentage tolerance, given SP500's ~92-year development history.

## Risk flagged before any backtest (required by this iteration's task)

**2008 is exactly the kind of year that could distort this family's
result.** Under the primary config (`n_weak_years=2`,
`include_election_year_in_strong=True`), 2008 is `cycle_year=4` (the
final year of the 2004-2008 term) -- a **strong** year under this
definition, in which weak-year cash reserves banked over 2005-2006-2007
would be deployed at up to `max_lump_multiple` the weekly rate. 2008 is
also the global financial crisis year, one of the worst equity/commodity
drawdown years in the development sample. If the primary config's strong
regime happens to concentrate large catch-up buys into 2008's crash, that
is a real, mechanical confound this backtest cannot separate from a
genuine election-cycle effect using development data alone -- it is
disclosed here, before any grid is run, precisely because it cannot be
fixed by re-tuning after seeing results (sec 5.4's holdout-discipline
spirit applies equally to dev-data judgment calls: this family's design
is not altered in response to how 2008 plays out). The
`include_election_year_in_strong=False` grid arm is a genuine,
pre-declared alternative hypothesis (perhaps the election year itself,
with its heightened uncertainty, behaves differently from the pre-
election "run-up" years) that happens to also soften this exact
confound, but it was included in the grid because the literature itself
distinguishes "approaching an election" from "the election year," not
in order to dodge 2008 after the fact. 2000 (`cycle_year=4`, also a
strong year under the primary, and the start of the dot-com crash) is a
second, similar case worth the same caveat, at a milder scale.

## Data inputs

Daily OHLC close price of the asset itself only (each of the 5 core
assets, tested independently -- single-asset family, per the scoping
decision above). The cycle signal uses **only the calendar year of each
trading day** (no price, no macro data). Sourced via
`src.backtest.v3.data.load_dev()` only.

## Parameters (4 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `n_weak_years` | 2, 1 | 2 |
| `include_election_year_in_strong` | True, False | True |
| `bank_fraction` | 0.3, 0.5, 0.7 | 0.5 |
| `max_lump_multiple` | 4, 8 | 8 |

`n_weak_years=2` (weak = post-election year + midterm year, strong =
pre-election year + election year) is the literal Santa-Clara & Valkanov
(2003) headline split (first half vs. second half of the term) -- a
no-look prior from the literature. `n_weak_years=1` (weak = post-election
year only; strong = midterm + pre-election + election years) is a grid
arm testing a narrower "only the year right after an election is weak"
alternative. `include_election_year_in_strong=True` (the primary) matches
Santa-Clara & Valkanov's own "second half of term" framing literally,
which includes the election year itself; `False` is the pre-declared
alternative discussed in the risk section above. `bank_fraction=0.5` is
the primary (a middle value; banking half of every weak-year deposit is a
substantial but not extreme reshaping); `0.3` and `0.7` grid milder and
more aggressive banking. `max_lump_multiple=8` is the primary -- with a
weak period of up to 2 years (~104 weekly deposits) potentially banked
before a strong period begins, a cap of 8x a single week's deposit spreads
deployment across at least ~13 strong-year weeks rather than dumping the
whole reserve in one week; `4` is a tighter, more gradual cap tested as a
grid arm.

## Grid

2 (`n_weak_years`) x 2 (`include_election_year_in_strong`) x 3
(`bank_fraction`) x 2 (`max_lump_multiple`) = **24 configurations**
(<= 36 cap; 4 params <= 5).

## Primary configuration

`n_weak_years=2, include_election_year_in_strong=True, bank_fraction=0.5,
max_lump_multiple=8`.

**Explicit pre-backtest verification (per family 021's lesson):** every
value in the primary configuration above (`n_weak_years=2`,
`include_election_year_in_strong=True`, `bank_fraction=0.5`,
`max_lump_multiple=8`) is checked programmatically, before the grid runs,
to be a member of its corresponding `GRID[...]` list in
`src/backtest/v3/strategies/election_cycle.py`
(`assert PRIMARY_CONFIG[k] in GRID[k] for k in GRID`), and that
`PRIMARY_CONFIG in grid_configs()` -- the exact class of bug family 021
caught twice (once pre-backtest for `buy_multiplier`, once post-grid for
`calm_fraction`). This family's grid run script asserts both checks
before any backtest is trusted.

## Pre-backtest non-degeneracy sanity check (required before the grid runs)

Because this is a **fixed, externally-given calendar split** (not a
data-derived threshold), the primary config's strong-year condition is
expected to fire on close to (though not exactly, since development
history does not start or end on an exact 4-year boundary) 50% of
week-end decision days for every asset (`n_weak_years=2` splits the
4-year cycle exactly in half). This is confirmed directly against each
asset's own trading-day index before any backtest is trusted -- see the
"Pre-backtest sanity check" section of `results.md` for the per-asset
table, plus an explicit by-hand cross-check of `cycle_year()` against a
handful of known years (2000->4, 2004->4, 2008->4, 2012->4, 2016->4,
2020->4, 2001->1, 2002->2, 2003->3, 2021->1, 2022->2, 2023->3) run as an
assertion in the grid script before the sanity-frequency check. A
frequency far from ~50% (e.g. from an off-by-one modulo bug, or from
2008/2020 straddling the dev/holdout cutoff asymmetrically) would
indicate an implementation error or a genuinely lopsided development
sample, not a real finding, and would block the grid run until resolved.

## Expected sign

**Positive on both wealth and Sharpe on a majority of the 5 core assets,
if the Santa-Clara & Valkanov effect is real and its channel (political/
fiscal stimulus affecting broad risk appetite and dollar liquidity, not
just S&P 500 fundamentals specifically) transfers beyond US equities.**
That said, several risks are flagged honestly before any backtest is
run: (1) **this mechanism never changes total capital deployed, only
timing within a fixed schedule** (same caveat as 003/005/006/007/018),
so even a genuine effect may show a small absolute wealth/Sharpe margin;
(2) **the 2008 (and, milder, 2000) confound** flagged above is a real
risk that a positive result on SP500/GOLD/SILVER/OIL is partly an
artifact of exactly two crisis years landing in the "strong" bucket under
the primary split, not a repeating, generalizable cycle effect --
sec 4.3's rolling-window check (only run if sec 4.1 passes) is the main
tool available on development data to distinguish "robust across many
sub-windows" from "driven by one or two years," though with only ~5
complete 4-year cycles in the SP500/commodity development sample (fewer
for BTC) this family's rolling-window and bootstrap diagnostics should be
read with more caution than families 006/007/018's, which have many more
independent cycle repetitions in the same development span; (3) **BTC's
development window (2014-2019) contains at most one full 4-year cycle and
parts of two others**, the shortest and least informative of the 5 assets
for a 4-year-periodicity signal by a wide margin -- flagged as the single
most uncertain of the five results, in the same spirit as family 018's
own BTC caveat but more acute here given the cycle length; (4) **the
effect is a well-published "puzzle" specifically because it survives
standard controls yet resists a clean risk-based explanation** -- the
same erosion-over-time risk families 006/007/018 flag applies here too.

## Degenerate configuration (implementation check only, not a grid arm)

`enabled=False`: bypasses the cycle-year computation entirely and forces
the exact same decision DCA's own decider makes (buy 100% of that week's
cash on every week-end day, 0 on every other day) -- reproduces plain DCA
bit-for-bit, same pattern as families 001-018's `enabled=False` checks.

## Additional implementation check (mirroring families 004/006/007/018's
capital-neutrality check, using family 021's corrected principled bound)

**Total capital deployed never exceeds cumulative deposits + interest.**
Verified path-wise using the "never invest, sit 100% in cash" control
trajectory on the same `daily_rf` path as the accumulated-interest ceiling
(family 021's fix), not a flat percentage tolerance -- required here too,
since SP500's development history (~1928-2019, ~92 years) is exactly the
kind of long history family 021 found a flat-percentage check to be
miscalibrated for.

## No-lookahead test note

Trivial for this family by construction, more so than even family 018's:
the signal is a pure function of the calendar year (itself a pure
function of the calendar date) with no price dependence at all -- every
US presidential election date used anywhere in this backtest is already
historical fact, so a perturbation of prices after day `t` cannot possibly
change the cycle-year signal, let alone the order generated, on or before
day `t`. Still run explicitly as a spot-check on the engine's actual order
generation, exactly as families 006/007/018 did, rather than assumed from
the signal's construction alone.
