# Family 006: Turn-of-month deposit timing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Ariel, R.A. (1987), *A Monthly Effect in Stock Returns*, Journal of
Financial Economics — finds essentially all of the S&P 500's cumulative
return historically accrues around the turn of the month (the last trading
day of the month plus roughly the first half of the following month), with
the remainder of the month showing no significant drift on average.
Lakonishok, J. and Smidt, S. (1988), *Are Seasonal Anomalies Real? A
Ninety-Year Perspective*, Review of Financial Studies — using Dow Jones
data back to 1897, documents that a four-trading-day window (the last
trading day of the month plus the first three trading days of the next)
accounts for a disproportionate share of total monthly returns, and that
this pattern is stable across nine decades. Seed queue item #6
(research-loop-plan-v3.md sec 7.3): "Turn-of-month deposit timing (S&P
500)."

## Mechanism ("why would this work, and who is on the other side?")

The literature's leading explanations are institutional/flow-based, not a
claim about fundamental mispricing that a rational arbitrageur could easily
correct away: (1) **payment and payroll cycles** — pension contributions,
mutual-fund inflows, and payroll-linked retirement contributions (401(k)
style) cluster around month-end/month-start, creating a recurring wave of
buy-side order flow that has to be absorbed by dealers and market-makers at
those specific calendar dates; (2) **portfolio and index rebalancing /
window dressing** — institutional managers frequently mark and rebalance
positions at month-end, and mutual funds report holdings around this time,
concentrating discretionary buying near the boundary; (3) **settlement and
accounting cycles** that shift some fraction of routine transaction flow to
specific calendar days rather than spreading it uniformly. The "other side"
of the trade is whoever supplies liquidity against this recurring, largely
non-informational demand pulse — market-makers and other liquidity
providers who are willing to sell into the turn-of-month buying pressure
and are compensated (on average, historically) by a small, recurring
premium for doing so on predictable dates, while carrying the risk that
flows fail to materialize or reverse in any given month. Unlike a
information-based anomaly, this effect does not require anyone to be
"wrong" about fundamentals — it only requires that a recurring, largely
mechanical/institutional demand pulse is not fully arbitraged away by
short-horizon capital, plausibly because the effect is small per-dollar
relative to the transaction costs and risk of running a strategy that does
nothing except lean into ~4 trading days a month.

**Important scope caveat, stated here because it drives this family's
design below:** this strategy does **not** attempt to earn a *risk premium*
by holding a different asset mix — a DCA investor already owns the asset
every day, turn-of-month or not. What this family actually tests is
narrower and mechanically different from every prior family in this loop:
it never changes *how much* total capital gets deployed into the asset (no
sizing tilt, no exit-to-cash, no leverage) — it only changes **which
trading days each dollar of the existing $500/week deposit schedule gets
spent on**, shifting execution from "spend all of every week's deposit at
the next open, whichever day that is" (plain DCA) toward "bank a
non-turn-of-month week's deposit as cash and spend the accumulated cash in
a lump at the next turn-of-month window." Because the *number of shares*
bought only depends on *price paid*, not *when the decision is made*
independent of price, this mechanism can only help if turn-of-month price
action is expected, on average, to be no worse (and per the literature,
often measurably better in aggregate market return terms) than an
arbitrary weekly execution day — i.e. it is a bet that shifting *when*
within a existing, fixed deposit schedule you buy, not *how much*, can
systematically buy at incrementally more favorable average prices, given
that turn-of-month days show elevated returns not merely elevated
volatility. That is a genuinely different economic bet from every family
tested so far (001–005), which all changed *how much* capital a given week
deploys as a function of a trend/momentum/valuation/volatility signal; this
family instead reshapes *when* capital that is going to be deployed anyway
gets deployed, using a fixed, pre-known **calendar** signal rather than any
price-derived signal.

## Category

**Seasonality / execution timing** (research-loop-plan-v3.md sec 4.5's
category list, matching sec 7.3's own label for seed-queue item #6
exactly).

## Why this is NOT a re-test of anything in sec 7.2's closed list

No family in sec 7.2's closed list (v1 buy-the-dip/trim-the-spike, v2
SmartDCA, v2 ADCA B1/B2, v2 rebalanced portfolios C1–C3, v2.1 rate-regime
Strategy D) — nor any of this loop's own families 001–005 — uses a
**calendar-based** signal at all. Every prior family's buy/sell/size
decision is a function of *price or macro data* (a moving average, realized
volatility, cross-asset relative strength, a value-averaging target path, a
trailing-return sign, a policy-rate regime). This family's signal is purely
`f(calendar_date)` — entirely determined in advance by the NYSE trading
calendar, independent of any price, macro or volatility observation. This
is a structurally different class of rule (a fixed, price-independent
execution-timing shift within a fixed deposit schedule) from anything
tested in this loop so far, and the task's own framing of idea #6
("turn-of-month deposit timing... execution timing") explicitly
distinguishes "Seasonality / execution timing" as its own category
(sec 4.5), separate from every category used by families 001–005 (Trend /
TSMOM exit x2, Rotation, Volatility targeting, Sizing).

## Single-asset vs. multi-asset scoping (judgment call, stated explicitly)

Sec 7.3 lists idea #6 as scoped to "Turn-of-month deposit timing (S&P
500)" — the Ariel/Lakonishok-Smidt literature is specifically about US
equity markets (Dow Jones and S&P 500 respectively). But sec 4.1's
single-asset win rule requires assessment on **>= 3 of 5 core assets**, and
the task instructs choosing between (a) testing the mechanism on all 5
core assets under sec 4.1's standard rule, since the *mechanism*
(execution-timing shift within a fixed deposit schedule, using only a
calendar signal) is asset-agnostic even though the *motivating historical
evidence* is equity-specific, or (b) restricting to SP500 only and
documenting why testing a specifically-equity-motivated effect on
gold/silver/BTC/oil would be scientifically inappropriate.

**Decision: (a) — test on all 5 core assets, scored under sec 4.1's
standard >= 3/5 rule.** Reasoning:

1. **The mechanism itself carries no equity-specific assumption.** Unlike,
   say, a strategy keyed to an equity-specific fundamental (earnings
   yield, a policy-rate regime tied to equity risk premia), turn-of-month
   timing is a claim about *market microstructure and recurring
   institutional flow patterns around calendar dates* — a claim that does
   not structurally require the asset to be equity. Gold and silver
   futures, WTI crude futures, and (in a different, exchange-driven rather
   than payroll-driven form) even BTC all have their own institutional
   flow calendars — futures contract rolls, ETF/ETP creation-redemption
   cycles (GLD, SLV, USO), CTA/managed-futures month-end rebalancing, and
   for BTC, exchange and custodial rebalancing flows — so a *structurally
   analogous* (not identical) mechanism is plausible a priori, even though
   this pre-registration explicitly does **not** claim the Ariel/
   Lakonishok-Smidt equity-specific empirical magnitude transfers
   unchanged to other assets.
2. **The charter's own text says option (a) is the more defensible
   reading**, and sec 4.1 makes no exception for a family whose motivating
   literature happens to be asset-specific — every prior family (001–005)
   drew its literature from a single asset class or a specific paper's
   asset universe (e.g. TSMOM's 58-asset multi-class study, dual momentum's
   equity/bond original context) and was still tested across all 5 core
   assets under the same standard rule; carving out an exception here
   specifically for idea #6, after four families have already been held to
   the uniform rule, would be an ad hoc, non-uniform application of sec 4.1
   without a textual basis in the charter for doing so.
3. **The alternative (b) creates a structural problem the charter doesn't
   resolve.** If restricted to SP500 only, this family could never be
   scored under sec 4.1's single-asset rule at all (that rule requires 5
   assets), leaving no defined win path within sec 4 as written — the
   charter would have to be amended or a new one-off rule invented, which
   sec 8's autonomous-loop design does not authorize the loop to do
   unilaterally.
4. **This choice does not pre-judge the outcome.** Testing on all 5 assets
   makes it *harder*, not easier, for the family to pass sec 4.1 if the
   effect is genuinely equity-specific (a real possibility, flagged
   explicitly in "Expected sign" below) — it is the conservative, not the
   favorable, choice between (a) and (b), since a null effect on
   gold/silver/BTC/oil directly lowers the 3-of-5 count rather than being
   excluded from scoring.

This reasoning is written here, before any backtest, exactly as the task
requires ("a reviewer would ask").

## Exact rules

Computed at each trading day `t` using only calendar information (the
NYSE/asset's own trading-day index) — no price or macro dependence in the
signal at all, so no-lookahead is automatically satisfied for the signal
itself (the index of trading days is known in advance, like a real
calendar; only *prices*, not *dates*, are unknown ahead of time, and dates
are all this signal uses). Decisions and orders are generated only on the
last trading day of each calendar week (the deposit-credit day), matching
every other v3 family's weekly decision cadence — this also avoids a
same-week repeated-buy defect that would arise from evaluating the
calendar signal on every trading day while banked cash sits idle between
week-end decision days.

- **Turn-of-month (TOM) window.** For each calendar month present in the
  asset's trading-day index, the **last `days_before_month_end` trading
  days of that month** and the **first `days_after_month_start` trading
  days of the following month** are marked TOM days. A given week-end
  decision day `t` is "in the TOM window" if `t` itself is marked TOM.
- **Weekly decision (week-end days only).**
  - If the week-end day is in the TOM window: buy
    `min(cash, max_lump_multiple * weekly_deposit)`. `cash` includes this
    week's $500 deposit plus any cash banked from prior non-TOM weeks (and
    the interest it has earned, sec 3.2). The `max_lump_multiple` cap
    (cash-capped, never leverage — the engine's own buy-capped-at-cash rule
    also applies as a hard floor under this) keeps any single week's
    purchase from becoming an unboundedly large one-shot bet even if many
    consecutive non-TOM weeks have banked cash.
  - If the week-end day is **not** in the TOM window: buy
    `mild_tilt_fraction * weekly_deposit`. The remainder,
    `(1 - mild_tilt_fraction) * weekly_deposit`, is left as cash (banked,
    earning IRX per sec 3.2) until the next TOM window. `mild_tilt_fraction
    = 0.0` is the "aggressive" reshaping variant (bank the entire
    non-TOM-week deposit); `mild_tilt_fraction = 0.5` is a milder tilt that
    still buys half of every non-TOM week's deposit on schedule.
  - **No sells, ever.** Like families 003 and 005, this is a pure
    timing/sizing-within-a-fixed-schedule rule, never a rule that
    liquidates existing units.
- **On non-week-end days:** no order is generated (buy_usd = sell_usd = 0),
  regardless of whether that day is in the TOM window — this keeps the
  decision cadence identical to every other v3 family's weekly cadence and
  avoids the repeated-buy defect noted above. (A live trader implementing
  this by hand would place the actual order on the specific TOM trading
  day nearest the week-end decision, per the playbook that would accompany
  a winner; for backtesting purposes the engine's weekly decision-then-
  next-open-fill cadence, sec 3.2, is used unchanged from every prior
  family, since the TOM/non-TOM state of the week-end day itself already
  captures whether that week's fill lands inside or outside the window.)
- **Total capital deployed is unchanged.** Every dollar bought traces back
  to the identical $500/week deposit schedule DCA uses (plus the same IRX
  interest on idle cash both strategies would otherwise earn) — this
  family reallocates *when* within that fixed schedule each dollar is
  spent, never *how much* gets deposited or deployed in total. An explicit
  implementation check (below) verifies cumulative capital deployed never
  exceeds DCA's cumulative deposits + interest, path-wise.

## Data inputs

Daily OHLC close price of the asset itself only (each of the 5 core assets,
tested independently — single-asset family, assessed per sec 4.1's
single-asset rule, per the scoping decision above, using the existing
single-asset `engine.py`). The TOM signal itself uses **only the asset's
own trading-day calendar** (no price, no macro data). Sourced via
`src.backtest.v3.data.load_dev()` only.

## Parameters (4 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `days_before_month_end` | 1, 2, 3 | 1 |
| `days_after_month_start` | 3, 4 | 3 |
| `mild_tilt_fraction` | 0.0, 0.5 | 0.0 |
| `max_lump_multiple` | 3, 6 | 6 |

`days_before_month_end=1, days_after_month_start=3` is the primary because
it matches Lakonishok & Smidt's own headline four-trading-day TOM window
definition (last trading day of the month + first three trading days of
the next) exactly — a no-look prior from the literature, not something
tuned on this loop's own data. `days_before_month_end=2,3` bracket it to
test whether widening the pre-month-end leg changes the result.
`mild_tilt_fraction=0.0` (full banking between TOM windows) is the primary
because it is the "purest" test of the timing-shift hypothesis — the
0.5 arm exists to check whether a milder reshaping (still buying on
schedule most weeks, just tilting size toward TOM weeks) changes the
picture, since the fully-banked variant concentrates more risk into fewer,
larger purchases. `max_lump_multiple=6` is the primary — wide enough
headroom (worth ~6 weeks of banked deposit) that the cap essentially never
binds under the primary window width (a ~4-day window recurs roughly every
4.3 weeks, so a multiple below ~5 risks truncating a normal one-month
banking cycle); `max_lump_multiple=3` is included as a grid arm
specifically to test a materially tighter cash cap that *would* bind under
normal cadence, forcing some banked cash to roll over an extra cycle.

## Grid

3 (`days_before_month_end`) x 2 (`days_after_month_start`) x 2
(`mild_tilt_fraction`) x 2 (`max_lump_multiple`) = **24 configurations**
(<= 36 cap; 4 params <= 5).

## Primary configuration

`days_before_month_end=1, days_after_month_start=3, mild_tilt_fraction=0.0,
max_lump_multiple=6`.

## Expected sign

**Positive on both wealth and Sharpe on SP500 specifically, if the
Ariel/Lakonishok-Smidt effect is real and survives this loop's fee/
robustness bar — this is the family's strongest and most literature-
grounded expectation.** For gold, silver, oil and BTC, the expected sign is
stated here honestly as **uncertain, not confidently positive** — the
mechanism's institutional-flow rationale (payroll/pension contribution
cycles, month-end fund rebalancing) is a specifically *equity* market
institutional pattern; commodity futures and BTC have different (and, for
BTC, much less month-end-payroll-driven) flow structures, so this family
may well pass on SP500 alone and fail on some or all of the other four —
exactly the scenario the scoping decision above already anticipated and
chose to score honestly under the standard >= 3/5 rule rather than
excluding the harder-to-predict assets. A secondary, structural risk
flagged before any backtest: like families 003 and 005, this mechanism
never changes *total* capital deployed, only *timing* within a fixed
schedule, so — consistent with the pattern already observed in 003/005 —
even a genuine effect may show a very small absolute wealth/Sharpe margin
over DCA, and the pooled excess-return series feeding sec 4.2's DSR test
may again be dominated by higher-moment (skew/kurtosis) risk from lump-sum
concentration (mild_tilt_fraction=0.0 buys larger, less frequent chunks
than DCA, which by construction increases path variance even if the mean
effect is favorable) rather than by a large mean shift.

## Degenerate configuration (implementation check only, not a grid arm)

`enabled=False`: bypasses the TOM/calendar computation entirely and forces
the exact same decision DCA's own decider makes (buy 100% of that week's
cash on every week-end day, 0 on every other day) — reproduces plain DCA
bit-for-bit, same pattern as families 001-005's `enabled=False` checks.

## Additional implementation check (beyond the standard four, per the
task's instruction)

**Total capital deployed never exceeds cumulative deposits.** Verified
path-wise: cumulative `buy_usd` (this family never sells, so net deployed
== gross bought) must never exceed DCA's own cumulative cash generated
(cumulative deposits + interest on idle cash), at every trading day across
the full development history — mirroring family 004's capital-neutrality
check (`scripts/v3/run_004_value_averaging.py`).
