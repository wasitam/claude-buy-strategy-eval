# Family 007: Day-of-week deposit timing (BTC weekend effect)

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Caporale, G.M. and Plastun, A. (2019), *The day of the week effect in the
cryptocurrency market*, Research in International Business and Finance /
Finance Research Letters — examining Bitcoin, Litecoin, Ripple and Dash
(2013-2017), find a statistically significant **positive abnormal return on
Mondays specific to Bitcoin** (not present in the other three coins tested),
and document that a trading rule built around it shows profit potential
before costs. A related and broader literature (surveyed briefly, not all
independently re-verified here, consistent with how prior families such as
006 cite a small number of anchor papers rather than an exhaustive review):
Kaiser, L. (2019), *Seasonality in cryptocurrencies*, Finance Research
Letters, documents other cryptocurrency calendar patterns including
weekend-specific return/volatility differences, attributed to crypto
markets' 24/7 trading with no institutional close and a materially
different (more retail-heavy, thinner) weekend liquidity/participant mix
than weekday sessions when institutional desks are active. Seed queue item
#7 (research-loop-plan-v3.md sec 7.3): "Day-of-week deposit timing (BTC
weekend effect)."

## Mechanism ("why would this work, and who is on the other side?")

Unlike traditional equity/commodity markets, crypto trades every calendar
day with no exchange close, no market-maker specialist system, and no
single dominant institutional participant base — weekday sessions see
heavier participation from institutional and algorithmic desks (which
mostly operate on a Monday-Friday business calendar even when trading a
24/7 asset), while weekends see a shift toward a thinner, more
retail-dominated order flow. This composition shift is the leading
candidate explanation in the literature above for why average returns
differ systematically by day of week for Bitcoin specifically (documented:
a positive abnormal Monday effect) — thinner weekend liquidity plausibly
produces a different, less efficiently-arbitraged price-formation process
over the weekend that partially resolves into Monday's session, when
institutional flow returns. The "other side" of this trade is, as in
family 006's turn-of-month mechanism, whoever supplies liquidity against
this recurring pattern without being able to fully arbitrage it away —
plausibly because (a) the absolute edge is small per dollar relative to
transaction costs for any strategy that trades specifically to exploit it,
and (b) unlike turn-of-month flows (driven by large, price-insensitive
institutional payment cycles), the weekday/weekend liquidity-composition
effect is a persistent *structural* feature of how crypto trades (not a
recurring event a sophisticated desk can simply front-run once and be
done), so it need not fully compete away even if partially known.

**Scope caveat, identical in spirit to family 006's, stated here because it
drives this family's design below:** like family 006, this strategy never
changes *how much* total capital gets deployed (no sizing tilt, no
exit-to-cash, no leverage) — it only changes **which trading day(s) of the
week each dollar of the existing $500/week deposit schedule gets spent
on**. The number of shares bought only depends on the price paid on the
day of execution, not on which day the decision was computed, so this
mechanism can only help if the target day of week's price action is, on
average, no worse (and per Caporale & Plastun for BTC/Monday, measurably
better in aggregate return terms) than whichever arbitrary day a fixed
weekly schedule would otherwise have executed on. This is the same
*execution-timing-within-a-fixed-schedule* bet as family 006, just with
weekly (day-of-week) periodicity instead of monthly (turn-of-month)
periodicity, and a different, crypto-specific economic rationale
(weekday/weekend liquidity composition, not payroll/pension/rebalancing
cycles).

## Category

**Seasonality / execution timing** (research-loop-plan-v3.md sec 4.5's
category list; matches sec 7.3's own label for seed-queue item #7 exactly,
and matches family 006's category — the two are related mechanisms at
different calendar granularities, addressed explicitly below).

## Why this is NOT a re-test of anything in sec 7.2's closed list, or of family 006

- **Not a re-test of sec 7.2's closed list**: no family in that list (v1
  buy-the-dip/trim-the-spike, v2 SmartDCA, v2 ADCA B1/B2, v2 rebalanced
  portfolios C1-C3, v2.1 rate-regime Strategy D) uses any calendar-based
  signal at all — every one of those rules is a function of price, realized
  volatility or a macro/policy-rate regime.
- **Not a re-test of family 006**: both families share the same *category*
  (Seasonality / execution timing) and the same high-level shape (bank
  non-target-period deposits, deploy a lump at the target period), but they
  operate at **different calendar granularities with different, independent
  economic rationales**: family 006's signal is `f(day-of-month)` (a
  monthly-periodicity institutional payment/rebalancing-flow story, tested
  primarily for equities), while this family's signal is `f(day-of-week)` (a
  weekly-periodicity liquidity-composition story, tested primarily for
  crypto). A month has ~21 trading days and this family's window is a
  single weekday recurring every ~5 (equity) or 7 (BTC) calendar days — the
  window widths, periodicities, and the literature motivating each are
  disjoint. This mirrors how, e.g., families 001 (10-month/200-day trend
  exit) and 005 (TSMOM sizing) were both accepted as "not a re-test of each
  other" despite sharing a broad "trend" flavor, because their exact signal
  definitions and mechanisms differ (sec 7.2's own re-test standard: "a
  different signal definition or a different mechanism").

## Single-asset vs. multi-asset scoping (judgment call, per the task's explicit instruction)

Sec 7.3 lists idea #7 as scoped to "Day-of-week deposit timing (**BTC**
weekend effect)" — narrower in its literature grounding than idea #6 even
was, since Caporale & Plastun's own finding is that the Monday effect is
**specific to Bitcoin** among the four coins they tested (not found in
Litecoin, Ripple or Dash). The task instructs following **family 006's
precedent for consistency**: test the mechanism (day-of-week execution
timing within a fixed deposit schedule) across all 5 core assets under sec
4.1's standard >= 3/5 rule, even though the literature motivation is
BTC/crypto-specific, and document this explicitly here.

**Decision: follow family 006's precedent — test on all 5 core assets,
scored under sec 4.1's standard >= 3/5 rule.** Reasoning, directly
parallel to family 006's prereg.md:

1. **The mechanism's *structural* claim (a day-of-week price/liquidity
   pattern) is not logically restricted to crypto**, even though the
   specific empirical finding motivating it (BTC's Monday effect) is.
   Traditional markets have their own well-studied (if largely arbitraged
   by now) day-of-week patterns in the older equity-market literature
   (French 1980; Gibbons & Hess 1981), so testing day-of-week timing on
   SP500/gold/silver/oil is not asking those assets to exhibit a
   *crypto-specific* pattern, only *some* day-of-week pattern, however
   large or small.
2. **Uniform application across families matters more than a one-off
   exception.** Four of the five families tested so far that reached this
   scoping question (001-005 implicitly via their own asset-agnostic
   grounding, and 006 explicitly) applied the same >= 3/5-across-5-assets
   rule regardless of whether the motivating literature was asset-specific.
   Carving out BTC-only scoring here — after the task itself flags family
   006 as the controlling precedent — would break that consistency without
   a textual basis in the charter, and would also make this family's trial
   count non-comparable to every other single-asset family's (sec 4.1's
   rule structurally assumes 5 assets).
3. **This is the conservative, not the favorable, choice.** As with family
   006, testing all 5 assets makes the family *harder* to pass than
   restricting to BTC alone would (where a strong, real Monday effect might
   plausibly clear a hypothetical single-asset bar on its own) — a null or
   negative result on 4 of 5 assets directly lowers the count needed to
   pass sec 4.1, exactly the kind of honest, non-cherry-picked test this
   loop is designed to run.
4. **Deviation considered and rejected.** A BTC-only scoring rule was
   considered (since idea #7's literature grounding is narrower than idea
   #6's — a single-coin finding, not even a broad equity-index one), but
   sec 4.1 as written has no defined single-asset pass path outside the
   5-asset >= 3/5 structure, and the task explicitly asks for family 006's
   precedent to be followed absent a strong reason to deviate. No such
   strong reason was found: the mechanism itself is asset-agnostic in
   structure even where the anchor citation is not, exactly as concluded
   for family 006.

## Exact rules

Computed using only the asset's own trading-day calendar (day-of-week and
ISO week grouping) — no price or macro dependence in the signal itself, so
no-lookahead is automatically satisfied for the signal (only *prices*, not
*dates* or *day-of-week*, are unknown ahead of time).

Unlike family 006 (whose calendar signal only had to be evaluated on the
week's single decision day, since the deposit-credit day and the TOM
window's binary state coincided with that same day), **this family's
decision must be evaluated on every trading day, not only the week's
deposit-credit day**, because the target day of week will usually differ
from whichever day is that asset's own week-end/deposit day (Friday for
SP500/gold/silver/oil, Sunday for BTC under `engine.week_end_flags`'s ISO
week-end rule). This is a deliberate, pre-registered cadence difference
from family 006, driven purely by the mechanism's own calendar geometry,
not a design choice made to favor any particular result.

- **Target day of week.** One of `{Monday, Friday, Sunday}` (a single
  categorical parameter, `target_weekday`, with 3 candidate values — not
  all 7 — per the task's explicit instruction to keep the grid small).
  Monday is the literal Caporale & Plastun anchor (buy right before the
  session that historically shows BTC's positive abnormal return). Friday
  is included as a plausible alternative pre-weekend liquidity-shift day
  that also exists as an ordinary trading day for every core asset. Sunday
  is included as the literal "weekend" day named in the seed-queue idea's
  own title, even though it is **not a trading day at all** for
  SP500/gold/silver/oil (their trading-day index simply never contains a
  Sunday) — for those four assets, `target_weekday=Sunday` structurally
  degenerates to "no target day ever occurs," and the `banking_window_weeks`
  forced-deploy rule below (not present in family 006, added specifically
  for this reason) prevents that from silently becoming an indefinite,
  uncapped cash drag. This is flagged here, before any backtest, exactly as
  the "Expected sign" section below anticipates.
- **On each trading day `t`:**
  - **If `t`'s day-of-week equals `target_weekday`:** buy
    `min(cash, max_lump_multiple * weekly_deposit)`. `cash` includes any
    deposit credited that day (if `t` is also the week's deposit day) plus
    all cash banked from prior non-target days (and the interest it has
    earned, sec 3.2).
  - **If `t`'s day-of-week does not equal `target_weekday`:** buy
    `mild_tilt_fraction * weekly_deposit / (number of non-target trading
    days in `t`'s ISO week)`, cash-capped. This spreads the "mild tilt"
    portion of a week's deposit evenly across that week's non-target
    trading days rather than concentrating it on one arbitrary day, and
    `mild_tilt_fraction = 0.0` (the primary, matching family 006's primary
    choice) makes this term identically zero, i.e. full banking between
    target days.
  - **Banking-window forced deploy (new relative to family 006, needed
    because a target day of week can go arbitrarily long without occurring
    on a given asset's own trading calendar — literally forever for
    `target_weekday=Sunday` on the 4 non-BTC assets):** if more than
    `banking_window_weeks * 7` **calendar days** have elapsed since cash
    was last spent (via either a target-day buy or a prior forced deploy),
    the day's buy is topped up by
    `min(remaining cash, max_lump_multiple * weekly_deposit)` regardless of
    whether `t` is a target day. This keeps the same cash-capped,
    no-leverage discipline as an ordinary target-day buy, and bounds how
    long any dollar can sit idle uninvested, which is both economically
    sensible (an investor would not accept literally never buying) and
    necessary to keep the strategy well-defined on assets whose calendar
    never contains the target day.
  - **No sells, ever** — like families 003, 005 and 006, this is a pure
    timing/sizing-within-a-fixed-schedule rule, never a rule that
    liquidates existing units.
- **Total capital deployed is unchanged.** Every dollar bought traces back
  to the identical $500/week deposit schedule DCA uses (plus the same IRX
  interest on idle cash both strategies would otherwise earn) — this
  family reallocates *when within the week* each dollar is spent, never
  *how much* gets deposited or deployed in total. The same explicit
  implementation check family 004/006 use (cumulative capital deployed
  never exceeds DCA's cumulative deposits + interest, path-wise) is run
  here unchanged.

## Data inputs

Daily OHLC close price of the asset itself only (each of the 5 core assets,
tested independently — single-asset family, assessed per sec 4.1's
single-asset rule, per the scoping decision above, using the existing
single-asset `engine.py`). The day-of-week signal uses **only the asset's
own trading-day calendar** (no price, no macro data). Sourced via
`src.backtest.v3.data.load_dev()` only.

## Parameters (4 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `target_weekday` | Monday, Friday, Sunday | Monday |
| `mild_tilt_fraction` | 0.0, 0.5 | 0.0 |
| `max_lump_multiple` | 3, 6 | 6 |
| `banking_window_weeks` | 2, 4 | 4 |

`target_weekday=Monday` is the primary because it is the literal
Caporale & Plastun (2019) anchor finding — a no-look prior from the
literature, not something tuned on this loop's own data. Friday and Sunday
bracket it as plausible alternative weekly-periodicity days. `max_lump_multiple`
and `mild_tilt_fraction` grid values and primary choices mirror family
006's exactly (same reasoning: 0.0 tilt is the purest test of the
timing-shift hypothesis; a multiple of 6 gives headroom worth ~6 weeks of
banked deposit so the cap essentially never binds under normal
once-a-week target-day cadence, while 3 is included specifically to test a
tighter, binding cap). `banking_window_weeks=4` is the primary — wide
enough that it essentially never binds when `target_weekday` is an
ordinary weekday that recurs every calendar week (worst case ~1 week
between occurrences), but short enough to force a deploy well before an
excessive cash drag could accumulate on the `target_weekday=Sunday` grid
arm for the 4 non-BTC assets; `banking_window_weeks=2` is included to test
a materially tighter forced-deploy cadence.

## Grid

3 (`target_weekday`) x 2 (`mild_tilt_fraction`) x 2 (`max_lump_multiple`) x
2 (`banking_window_weeks`) = **24 configurations** (<= 36 cap; 4 params
<= 5).

## Primary configuration

`target_weekday=Monday, mild_tilt_fraction=0.0, max_lump_multiple=6,
banking_window_weeks=4`.

## Expected sign

**Positive on both wealth and Sharpe on BTC specifically, if the
Caporale & Plastun Monday effect is real and survives this loop's fee/
robustness bar — this is the family's strongest and most literature-
grounded expectation, directly analogous to family 006's SP500-specific
expectation.** For SP500, gold, silver and oil, the expected sign is
stated here honestly as **uncertain to negative, not confidently
positive** — the mechanism's motivating rationale (24/7 trading,
weekday/weekend liquidity-composition shift) is specifically a crypto
market-structure feature that traditional exchange-traded assets do not
share (they have no weekend trading session at all), so this family may
pass on BTC alone and fail on some or all of the other four — the same
asymmetric-pass pattern already observed for family 006's SP500-specific
result, just with the roles of "the one literature-grounded asset" and
"the four out-of-scope assets" reversed (BTC here vs. SP500 there). A
further, BTC-specific structural risk flagged before any backtest: as with
family 006, this mechanism never changes *total* capital deployed, only
*timing* within a fixed schedule, so — consistent with the pattern already
observed in 003/005/006 — even a genuine effect may show a very small
absolute wealth/Sharpe margin over DCA, and the pooled excess-return series
feeding sec 4.2's DSR test may again be dominated by higher-moment
(skew/kurtosis) risk from lump-sum concentration (`mild_tilt_fraction=0.0`
buys larger, less frequent chunks than DCA) rather than by a large mean
shift. A second, more specific risk: on the 4 non-BTC assets, the
`target_weekday=Sunday` grid arm structurally forces the strategy toward
`banking_window_weeks`-cadence forced deploys rather than true target-day
buys (since Sunday never occurs on those calendars) — this grid arm is
therefore expected, ex ante, to behave closer to "deposit every N weeks
regardless of day" than to any genuine day-of-week timing bet on those
four assets, and is retained in the grid deliberately as an honest,
pre-registered edge case rather than removed after the fact.

## Degenerate configuration (implementation check only, not a grid arm)

`enabled=False`: bypasses the day-of-week/banking-window computation
entirely and forces the exact same decision DCA's own decider makes (buy
100% of that week's cash on every week-end day, 0 on every other day) —
reproduces plain DCA bit-for-bit, same pattern as families 001-006's
`enabled=False` checks.

## Additional implementation check (beyond the standard four, per the
task's instruction, mirroring family 004/006's capital-neutrality check
exactly)

**Total capital deployed never exceeds cumulative deposits.** Verified
path-wise: cumulative `buy_usd` (this family never sells, so net deployed
== gross bought) must never exceed DCA's own cumulative cash generated
(cumulative deposits + interest on idle cash), at every trading day across
the full development history.
