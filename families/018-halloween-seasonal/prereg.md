# Family 018: "Halloween effect" / Sell-in-May seasonal deposit timing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Bouman, S. and Jacobsen, B. (2002), *The Halloween Indicator, "Sell in May
and Go Away": Another Puzzle*, American Economic Review 92(5), 1618-1635 --
using data from 37 countries, find that average stock returns from November
through April are significantly higher than average stock returns from May
through October in most of the markets tested, a pattern that is stable
over long samples and cannot be fully explained by known risk factors or by
the January effect alone. Follow-up literature (Jacobsen, B. and Zhang,
C.Y. (2020), "The Halloween Indicator: everywhere and always," updates the
original result with an even longer sample (over 300 years for the UK) and
confirms the effect's persistence and pervasiveness across markets) is
consistent with the original finding, not independently re-verified here.
Research queue idea #18 (`state/research_queue.md`): "'Halloween effect' /
Sell-in-May seasonal deposit timing."

## Mechanism ("why would this work, and who is on the other side?")

The literature's leading explanations are behavioral/institutional, not a
claim about a fundamental mispricing any rational arbitrageur could easily
correct away: (1) **vacation/risk-aversion cycle** -- Bouman & Jacobsen's
own preferred explanation links the effect to the northern-hemisphere
summer vacation period, when trading desks are thinner, institutional
decision-makers are away, and risk appetite for new positions is lower,
producing systematically weaker summer price action; (2) **fund-flow and
mandate-review cycles** -- many institutional allocators conduct
mid-year/summer portfolio reviews and are more likely to reduce risk ahead
of vacations and re-engage after Labor Day; (3) **a documented,
long-lived seasonal regularity that persists despite being widely known**
-- Bouman & Jacobsen and the follow-up literature explicitly note the
puzzle is that the pattern survives publication (a "puzzle" precisely
because simple risk-based explanations do not fully account for it), which
the loop treats as a literature fact to test empirically, not as proof the
edge is real out of sample. The "other side" of the trade is, as with
families 006 and 007, whoever supplies liquidity against this recurring,
largely non-informational summer risk-reduction pattern -- market-makers
and other liquidity providers compensated (on average, historically) for
absorbing summer selling/thin-trading pressure, while carrying the risk
that the pattern fails to repeat or reverses in any given year.

**Scope caveat, identical in spirit to families 006/007's, stated here
because it drives this family's design below:** like 006/007, this
strategy never changes *how much* total capital gets deployed (no sizing
tilt tied to price or a regime signal, no exit-to-cash on a value
condition, no leverage) -- it only changes **which weeks of the year each
dollar of the existing $500/week deposit schedule gets spent on**. The
number of shares bought only depends on the price paid on the week of
execution, not on which week the decision was computed, so this mechanism
can only help if November-April price action is, on average, no worse
(and per Bouman & Jacobsen, measurably better in aggregate return terms)
than the May-October weeks a fixed schedule would otherwise spend the same
dollars on.

## Category

**Seasonality / execution timing** (research-loop-plan-v3.md sec 4.5's
category list; matches families 006's and 007's category -- the three are
related mechanisms at three different, explicitly distinct calendar
granularities, addressed in full below).

## Why this is NOT a re-test of families 006, 007, or sec 7.2's closed list

- **Not a re-test of sec 7.2's closed list:** no family in that list (v1
  buy-the-dip/trim-the-spike, v2 SmartDCA, v2 ADCA B1/B2, v2 rebalanced
  portfolios C1-C3, v2.1 rate-regime Strategy D) uses any calendar-based
  signal at all.
- **Not a re-test of family 006 (turn-of-month) or family 007
  (day-of-week) -- explicit, load-bearing distinction, since all three
  share the "Seasonality / execution timing" category:** the three
  families operate at **three different calendar granularities, each an
  order of magnitude apart, with independent economic rationales and
  independent anchor literature**:
  - **Family 006** is a **monthly** cycle: `f(day-of-month)`, a ~4-trading-day
    window recurring every ~21 trading days, motivated by payroll/pension
    contribution and fund-rebalancing flow cycles (Ariel 1987; Lakonishok &
    Smidt 1988).
  - **Family 007** is a **weekly** cycle: `f(day-of-week)`, a single weekday
    recurring every ~5 (equity) or 7 (BTC) calendar days, motivated by
    crypto-specific weekday/weekend liquidity-composition shifts (Caporale &
    Plastun 2019).
  - **This family (018)** is an **annual** cycle: `f(month-of-year)`, a
    ~6-calendar-month window (November-April) recurring exactly once per
    year, motivated by a summer vacation/risk-aversion and mandate-review
    cycle documented across 37 countries over long samples (Bouman &
    Jacobsen 2002).
  A month has ~21 trading days, a week has ~5, and a year has ~252 -- the
  window widths here differ from family 006's by a factor of roughly 50
  and from family 007's by a factor of roughly 250. None of the three
  signals is a special case or a minor variant of either of the others:
  each is evaluated on an entirely different, non-nested calendar period
  (day-of-week vs. day-of-month vs. month-of-year), each cites independent
  literature with an independent proposed mechanism, and each was
  motivated (in the seed queue, sec 7.3) by evidence anchored to a
  different asset class (006: equities; 007: Bitcoin; 018: a broad
  37-country equity panel). This mirrors sec 7.2's own re-test standard
  ("a different signal definition or a different mechanism") and the
  precedent already established between families 001/005 (both "trend"
  in flavor, held to be distinct because their exact signal definitions
  and time horizons differ) and between 006/007 themselves.

## Single-asset vs. multi-asset scoping (judgment call, per the task's
explicit instruction to follow the 006/007 precedent)

Bouman & Jacobsen's literature is a broad, 37-country equity-market
finding, not asset-specific to a single instrument the way family 007's
BTC-only anchor citation was -- if anything this family's literature
grounding is closer to family 006's (equity-market-anchored, but with a
structural claim -- a vacation/risk-reduction cycle -- that does not
logically require the asset to be equity). Following the task's explicit
instruction and family 006/007's own precedent:

**Decision: test on all 5 core assets, scored under sec 4.1's standard
>= 3/5 rule.** Reasoning, directly parallel to 006/007's prereg.md
sections:

1. **The mechanism's structural claim (a summer risk-reduction/thin-trading
   cycle) is not logically restricted to equities.** Commodity futures
   (gold, silver, oil) have their own well-documented summer-liquidity and
   trading-desk-vacation patterns, and even BTC, despite trading 24/7 with
   no institutional close, is held by market participants (funds, desks,
   market-makers) who are themselves subject to the same human
   vacation/mandate-review calendar Bouman & Jacobsen's mechanism invokes.
2. **Uniform application across families matters more than a one-off
   exception.** Every family tested so far in this loop that reached this
   scoping question (006, 007, and implicitly 001-005/010/013/014's own
   asset-agnostic framing) applied the same >= 3/5-across-5-assets rule
   regardless of whether the motivating literature was asset- or
   region-specific. Carving out an exception here would break that
   consistency without a textual basis in the charter.
3. **This is the conservative, not the favorable, choice.** Testing all 5
   assets makes the family *harder* to pass than restricting to a
   pure-equity SP500-only test would -- a null or negative result on
   gold/silver/BTC/oil directly lowers the count needed to pass sec 4.1,
   exactly the honest, non-cherry-picked test this loop is designed to run.
4. **Deviation considered and rejected**, for the same reasons families
   006 and 007 gave: sec 4.1 as written has no defined single-asset pass
   path outside the 5-asset >= 3/5 structure, and no strong reason was
   found to depart from the established precedent.

## Exact rules

Computed at each trading day `t` using only calendar information (the
asset's own trading-day index and each day's calendar month) -- no price or
macro dependence in the signal at all, so no-lookahead is automatically
satisfied for the signal itself (the calendar is known in advance; only
*prices*, not *dates*, are unknown ahead of time). Decisions and orders are
generated only on the last trading day of each calendar week (the
deposit-credit day), matching family 006's and every other v3 family's
weekly decision cadence -- unlike family 007, the annual window here is
wide enough (~26 weeks) that it is guaranteed to be evaluated correctly at
weekly granularity without needing a within-week evaluation rule.

- **Seasonal window.** For each calendar year, the **strong season** runs
  from `strong_season_start_month` (day 1) through the day before
  `weak_season_start_month` (day 1) of the same year; the **weak season**
  runs from `weak_season_start_month` (day 1) through the day before
  `strong_season_start_month` (day 1) of the following year (the window
  wraps across the calendar year boundary, e.g. the primary
  November-April strong season spans two calendar years). A given week-end
  decision day `t` is "in the strong season" if `t`'s calendar date falls
  in that window.
- **Weekly decision (week-end days only).**
  - If the week-end day is in the strong season: buy
    `min(cash, max_lump_multiple * weekly_deposit)`. `cash` includes this
    week's $500 deposit plus any cash banked from prior weak-season weeks
    (and the interest it has earned, sec 3.2). The `max_lump_multiple` cap
    (cash-capped, never leverage -- the engine's own buy-capped-at-cash
    rule is also a hard floor under this) keeps any single week's purchase
    from becoming an unboundedly large one-shot bet even after a full
    ~6-month weak season has banked cash; because this window is much
    wider than family 006's ~4-trading-day TOM window, the cap values
    tested here are correspondingly larger (see Parameters below).
  - If the week-end day is in the weak season: buy
    `mild_tilt_fraction * weekly_deposit`. The remainder,
    `(1 - mild_tilt_fraction) * weekly_deposit`, is banked as cash
    (earning IRX per sec 3.2) until the next strong-season week.
    `mild_tilt_fraction = 0.0` (the primary) is the "aggressive" reshaping
    variant (bank the entire weak-season week's deposit); `0.5` is a
    milder tilt that still buys half of every weak-season week's deposit
    on schedule.
  - **No sells, ever.** Like families 003, 005, 006 and 007, this is a
    pure timing/sizing-within-a-fixed-schedule rule, never a rule that
    liquidates existing units.
- **On non-week-end days:** no order is generated (buy_usd = sell_usd = 0),
  matching family 006's cadence exactly.
- **Total capital deployed is unchanged.** Every dollar bought traces back
  to the identical $500/week deposit schedule DCA uses (plus the same IRX
  interest on idle cash both strategies would otherwise earn) -- this
  family reallocates *when* within the fixed weekly schedule each dollar
  is spent, never *how much* gets deposited or deployed in total. An
  explicit implementation check (below) verifies cumulative capital
  deployed never exceeds DCA's cumulative deposits + interest, path-wise,
  mirroring families 004/006/007's identical check.
- **No forced-deploy / banking-window rule needed (unlike family 007).**
  Unlike family 007's `target_weekday=Sunday` edge case (which never
  occurs at all on 4 of the 5 assets' own trading calendars, requiring a
  forced-deploy safety valve), this family's strong season occurs exactly
  once, reliably, every calendar year on every asset's trading calendar --
  there is no scenario in which the strong season fails to occur, so no
  analogous safety-valve parameter is needed, keeping this family at 4
  tunable parameters like family 006 and 007.

## Data inputs

Daily OHLC close price of the asset itself only (each of the 5 core
assets, tested independently -- single-asset family, assessed per sec
4.1's single-asset rule, per the scoping decision above, using the
existing single-asset `engine.py`). The seasonal signal uses **only the
asset's own trading-day calendar** (calendar month; no price, no macro
data). Sourced via `src.backtest.v3.data.load_dev()` only.

## Parameters (4 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `strong_season_start_month` | 11 (Nov), 10 (Oct) | 11 |
| `weak_season_start_month` | 5 (May), 4 (Apr) | 5 |
| `mild_tilt_fraction` | 0.0, 0.5 | 0.0 |
| `max_lump_multiple` | 6, 12 | 6 |

`strong_season_start_month=11, weak_season_start_month=5` (November-April
strong / May-October weak) is the primary because it is the literal
Bouman & Jacobsen (2002) headline "Sell in May, buy back on Halloween"
window -- a no-look prior from the literature, not something tuned on this
loop's own data. The `(10, 4)` grid arm (October-March strong /
April-September weak) tests a one-month-earlier shift of the same window,
per the task's explicit instruction to grid a couple of window-boundary
variants. `mild_tilt_fraction=0.0` (full banking through the weak season)
is the primary for the same reason families 006/007 chose it: the purest
test of the timing-shift hypothesis; `0.5` tests a milder reshaping.
`max_lump_multiple=6` is the primary -- six times the weekly deposit is
modest headroom relative to a full ~26-week weak season's banked cash
(worth up to ~26x a single week's deposit if never partially deployed), so
the cap is expected to bind repeatedly across most of the strong season's
~26 weekly buy opportunities, spreading the deployment out rather than
dumping the whole banked pot in a single week -- this is a deliberate,
literature-consistent choice (the primary hypothesis is that November-April
price action broadly, not any single week within it, is favorable, so
spreading the catch-up buying across the whole strong season is the more
faithful test of Bouman & Jacobsen's own return-window finding).
`max_lump_multiple=12` is included as a grid arm testing a much looser cap
that empties a full season's bank in roughly half as many weeks.

## Grid

2 (`strong_season_start_month`) x 2 (`weak_season_start_month`) x 2
(`mild_tilt_fraction`) x 2 (`max_lump_multiple`) = **16 configurations**
(<= 36 cap; 4 params <= 5).

## Primary configuration

`strong_season_start_month=11, weak_season_start_month=5,
mild_tilt_fraction=0.0, max_lump_multiple=6`.

## Pre-backtest non-degeneracy sanity check (required before the grid runs)

Because this is a **fixed calendar split** (not a data-derived threshold
like families 011/014/015/016/017's signals), the strong-season condition
is expected to fire on a date-count share close to (though not exactly, since
months have unequal lengths) 6/12 = 50% of trading days for every asset,
essentially by construction. This is confirmed directly against each
asset's own trading-day index (not merely asserted) before any backtest is
trusted, using the exact same `strong_season_start_month=11,
weak_season_start_month=5` primary window -- see the "Pre-backtest sanity
check" section of `results.md` for the per-asset table. Values far from
~50% (e.g. from an off-by-one month-boundary bug) would indicate an
implementation error, not a real finding, and would block the grid run
until fixed.

## Expected sign

**Positive on both wealth and Sharpe on a majority of the 5 core assets,
if the Bouman & Jacobsen effect is real, broad-based (as their own
37-country panel suggests), and survives this loop's fee/robustness bar --
this is a stronger prior expectation than families 006's (SP500-specific)
or 007's (BTC-specific) asymmetric priors, precisely because the anchor
literature here is not confined to one asset class.** That said, several
risks are flagged honestly before any backtest is run: (1) **as with
families 003/005/006/007, this mechanism never changes total capital
deployed, only timing within a fixed schedule**, so even a genuine effect
may show a small absolute wealth/Sharpe margin over DCA, and the pooled
excess-return series feeding sec 4.2's DSR test may be dominated by
higher-moment (skew/kurtosis) risk from lump-sum concentration
(`mild_tilt_fraction=0.0` buys larger, less frequent chunks than DCA)
rather than by a large mean shift; (2) **BTC and crypto more broadly did
not exist during most of Bouman & Jacobsen's sample** and trades on a
fundamentally different (24/7, no institutional close) calendar than the
equity/commodity markets the literature studies, so BTC's result is the
single most uncertain of the five, similar in spirit to family 007's own
caveat about its literature not transferring cleanly to non-crypto assets;
(3) **the effect, even where real historically, is well known and
extensively published (a "puzzle" specifically because it persists despite
publication)** -- if any erosion over time has occurred, this loop's
long development-history assets (SP500, gold, silver, oil, all spanning
decades) are better positioned to detect it than BTC's short (~5-year)
development window.

## Degenerate configuration (implementation check only, not a grid arm)

`enabled=False`: bypasses the seasonal-window computation entirely and
forces the exact same decision DCA's own decider makes (buy 100% of that
week's cash on every week-end day, 0 on every other day) -- reproduces
plain DCA bit-for-bit, same pattern as families 001-007's `enabled=False`
checks.

## Additional implementation check (beyond the standard four, per the
task's instruction, mirroring family 004/006/007's capital-neutrality
check exactly)

**Total capital deployed never exceeds cumulative deposits.** Verified
path-wise: cumulative `buy_usd` (this family never sells, so net deployed
== gross bought) must never exceed DCA's own cumulative cash generated
(cumulative deposits + interest on idle cash), at every trading day across
the full development history.

## No-lookahead test note

Trivial for this family by construction -- the signal is a pure function
of the calendar date only, computed once from the trading-day index with
no price dependence at all, so a perturbation of prices after day `t`
cannot possibly change the signal on or before `t`. Still run explicitly
(per the task's instruction) as a spot-check on the engine's actual order
generation, exactly as families 006/007 did, rather than assumed from the
signal's construction alone.
