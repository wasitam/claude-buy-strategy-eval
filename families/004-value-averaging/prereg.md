# Family 004: Value averaging (target-path contributions)

**Status:** pre-registered. Committed before any backtest is run on development
data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Edleson, M. (1991), *Value Averaging: The Safe and Easy Strategy for Higher
Investment Returns*. The core idea: instead of investing a fixed dollar
amount each period (dollar-cost averaging), set a target *account value*
path and each period buy or sell whatever is needed to bring the account to
that period's target value. Because the rule buys more dollars when the
account is below its target (typically after a price decline) and buys
fewer, or sells, when the account is above its target (typically after a
price rise), it mechanically front-loads shares purchased during weak
markets and back-loads them out of strong markets — the reverse of what a
naive investor does when they chase performance.

**Hayley's critique** (Hayley, S. (2014), *Value Averaging: A Critical
Analysis*, or similar circulating practitioner/academic critiques of
Edleson's original IRR-based framing — cited generically per seed queue item
#4, research-loop-plan-v3.md sec 7.3): value averaging's headline IRR
advantage over DCA in Edleson's own and later studies is substantially an
artifact of the fact that VA and DCA are compared with **different, path-
dependent total committed capital** — VA demands larger lump sums after
selloffs (more total capital committed, arriving disproportionately at good
entry prices, which mechanically inflates IRR) and can withdraw capital
(effectively negative net contributions) after rallies. An IRR comparison
across two strategies that invest different total dollar amounts, on
different schedules, is not a fair test of the sizing *rule* itself, since
some of VA's apparent edge is just "invest more, and earlier, when prices
are lower" — a capital-timing advantage available to any strategy with
extra capital on tap, not a property of the value-averaging rule per se.

## How this family addresses Hayley's critique (capital-neutrality design)

This family is deliberately constructed so that VA and DCA draw from the
**same funding source and the same total contribution schedule**, and is
**scored on final wealth given identical total capital deployed, not IRR**
(research-loop-plan-v3.md sec 7.3 item 4, and the objective in sec 1/§4.1
"beats DCA on final wealth AND Sharpe, using identical deposits," sec 2).
Concretely:

- **Same $500/week deposit schedule as DCA, no exceptions.** Exactly as
  every other v3 family, $500 is credited to the account's cash balance
  every week (engine sec 3.2) — VA never receives, and DCA never receives,
  an extra dollar of external capital. This is enforced by using the
  existing `engine.run_single_asset` unmodified: it credits `weekly_deposit`
  on each calendar week's last trading day regardless of which decider is
  plugged in.
- **No external capital, no leverage, no borrowing.** A VA "buy" order can
  only ever spend cash the account already holds (accumulated deposits +
  earned interest + prior sale proceeds) — the engine's own cash cap (sec
  3.2, "Buys are capped by available cash, so cash never goes negative") is
  the enforcement mechanism, identical to every other v3 family. **This is
  the answer to "how does VA source extra buys when the account is behind
  target": from an accumulating cash buffer only** (unspent prior deposits
  sitting in cash, earning IRX while they wait), **never from a fresh
  capital injection.** If the target's implied catch-up buy exceeds
  available cash, the strategy buys only what cash allows that week (a
  smaller-than-target buy, same partial-fill logic already used by every
  other family in this loop) and the shortfall persists into future weeks'
  gaps rather than being funded externally.
- **Selling when ahead of target is real cash raised, not left uninvested.**
  When the account is ahead of its target value (after a rally), the
  `allow_sells` grid arm sells units back to cash; that cash is not removed
  from the account (no withdrawal) — it stays in the account earning IRX
  and is available to fund a future catch-up buy, or simply remains part of
  final wealth if never redeployed. Total capital **deployed** (net dollars
  actually invested in the asset, cumulative buys minus cumulative sell
  proceeds) can therefore never exceed cumulative deposits-to-date at any
  point in the backtest — the same invariant checked by the sec 3.2
  implementation check ("cash never goes negative") already guarantees this
  mechanically, since a buy order that would require more than deposited-
  to-date cash simply cannot be filled.
- **A magnitude cap (`max_multiple_of_deposit`) additionally bounds any
  single week's buy or sell to a small multiple of the base $500 deposit.**
  This is the "no leverage" design decision called out in the task: even
  though the cash cap already prevents borrowing, an *uncapped* VA rule can
  still demand a buy many multiples of $500 after a severe, multi-year
  selloff (if enough cash has piled up in the buffer) — a lumpy, path-
  dependent contribution pattern that is exactly the kind of design choice
  Hayley's critique says matters. Capping the weekly action at
  `max_multiple_of_deposit x $500` keeps VA's week-to-week cash flow in the
  same order of magnitude as DCA's constant $500/week, rather than letting
  it occasionally look like a large lump-sum investor. This cap is a grid
  parameter (below) so its effect on the win rate can be assessed directly.

Net effect: VA and DCA in this family always have **byte-for-byte identical
cumulative deposit schedules** (both are $500 x number of weeks elapsed at
every point in time), and VA's total capital *deployed* is always **less
than or equal to** DCA's cumulative deposits (DCA deploys 100% of every
deposit immediately; VA may leave some of it in cash if the account is
already at or above target). This is a strictly *harder* bar for VA than
Hayley's critique demands (which only asks for equal *total* contributions
by the end) — here VA can never even temporarily out-commit DCA at any
intermediate date, not just on average — which is why the family is judged
purely on final wealth and Sharpe (sec 4.1) rather than IRR: IRR would still
reward VA for early large draws even under this capital-neutral construction
in a way final wealth does not.

## Mechanism ("why would this work, and who is on the other side?")

A target value path `V_target(w)` (an assumed-return growth path — see
"Exact rules") is compared each week to the account's actual value. Buying
more when actual value is below target, and less (or selling) when it's
above, is mechanically a **contrarian, price-level-based rebalancing rule**:
after a price decline (actual value falls below the path), more of the next
dollars go toward that asset at the lower price; after a price rise (actual
value rises above the path), fewer dollars (or a sale) follow. The economic
claim (Edleson 1991, and the broader tactical-rebalancing/contrarian
literature it sits within) is that this captures a small amount of the same
"buy dips, trim rallies" edge as fixed-weight rebalancing between assets,
but applied along the time axis of a single accumulating position instead of
across assets — assuming the asset's price is mean-reverting around its own
growth trend over the relevant horizon (which need not be true, and is the
main risk: a persistently trending asset, e.g. one on a multi-year rising
trend, gets systematically *under*-bought by VA relative to DCA precisely
when it is compounding fastest). The "other side" of the trade is DCA
investors who buy the same dollar amount regardless of the account's recent
path, so they neither anti-chase dips nor trim rallies. Once the funding
schedule is made identical (see above), any wealth or Sharpe edge for VA
over DCA has to come from this timing tilt being profitable on net — exactly
the effect Hayley's critique says is *not* automatic and is frequently
overstated in the literature's IRR-based framing.

## Category

**Sizing** (research-loop-plan-v3.md sec 4.5's "Sizing / valuation" category
— matches the seed queue's own category tag for item #4, sec 7.3).

## Why this is not a re-test of a closed family (sec 7.2), and how it differs from prior v3 families

No family in sec 7.2's closed list (v1 buy-the-dip/trim-the-spike, v2
SmartDCA, v2 ADCA B1/B2, v2 rebalanced portfolios, v2.1 rate-regime Strategy
D) uses a **target account-value path** as its signal. The closest is v2
SmartDCA, whose signal is price level relative to a trailing moving average
(a *price* reference). Value averaging's reference is instead the account's
own **cumulative invested value against an assumed-return growth path** — a
function of the account's trading history and an assumed forward return
rate, not of the asset's own trailing price statistics at all. Two VA
accounts holding the same asset but with different starting dates, or that
happened to buy/sell at different fills earlier in the path, can have
different signals today even with identical current prices — this
path-dependence (and the explicit sell-when-ahead mechanic funded only from
the account's own accumulated cash, capped at a multiple of the base
deposit) has no analog in SmartDCA or any other prior v2/v3 family. It is
also distinct from this loop's own three prior v3 families: 001 (price vs.
trailing SMA, a binary in/cash trend signal), 002 (cross-asset relative
momentum rotation), and 003 (buy size scaled by the asset's own realized
variance ratio, no account-value target at all, no selling). None of the
four families for this loop, and none of the closed v1/v2/v2.1 list,
compares the account's *value* to a growth-path *target* and sells to fund a
future buy from that same accumulating cash buffer.

## Exact rules

Computed at each trading day `t` using only data through `t` (no lookahead).
Orders are only generated on the same day a weekly deposit is credited (the
last trading day of each calendar week, matching every other family's
deposit-day convention) — VA is a weekly-rebalanced rule here, consistent
with the $500/week deposit cadence; it does not re-target daily.

- **Target growth path.** Let `w` = 1, 2, 3, ... index the calendar weeks
  elapsed so far (the week whose deposit was just credited is week `w`).
  Assume a constant per-week growth rate `r = (1 + annual_growth_rate)^(1/52) - 1`
  implied by the tunable annual rate `annual_growth_rate`. The target value
  after `w` weekly deposits, **if every deposit had earned exactly that
  assumed rate from the week it was made through week `w`**, is the standard
  future-value-of-an-annuity formula:
  `V_target(w) = weekly_deposit x ((1+r)^w - 1) / r` (for `r` near 0, the
  limit `weekly_deposit x w` is used). This is exactly the amount a plain-
  DCA investor's account would be worth at week `w` if the asset had
  compounded at the assumed rate every week since week 1 — the canonical
  Edleson-style linear/constant-assumed-return target path. (The path
  *shape* — a constant assumed compounding rate — is fixed by design, not a
  tunable grid parameter; only its rate is tunable, to keep the parameter
  count low while still letting the grid test whether the strategy's edge
  is sensitive to how aggressive the assumed growth path is.)
- **Actual account value at week `w`'s decision:** `V_actual = shadow_units x close_t`,
  tracked via the strategy's own causal simulation of its own past fills
  (identical fill mechanics — next-day open, fee, sells-before-buys — to the
  engine itself, so it exactly matches the real engine state at every step;
  this is necessary because the single-asset engine's `decide(t, cash)`
  interface does not pass current units back to the decider, only cash, so
  the strategy tracks its own position causally using only its own past
  orders and past (already-realized, same-day-or-earlier) prices).
- **Gap:** `gap = V_target(w) - V_actual`.
- **If `gap > 0` (behind target):** submit a buy order of
  `buy_usd = min(gap, max_multiple_of_deposit x weekly_deposit, cash)` —
  capped by (a) the magnitude cap, and (b) actual cash on hand (the
  no-external-capital, no-leverage rule; see above). This is funded **only**
  from the accumulating cash buffer of past deposits/interest/sale proceeds,
  never a fresh injection.
- **If `gap < 0` (ahead of target) and `allow_sells` is true:** submit a
  sell order of `sell_usd = min(-gap, max_multiple_of_deposit x weekly_deposit, V_actual)`
  — capped by the same magnitude cap and by the account's own current
  value (cannot sell more than is held). Proceeds go to cash, not
  withdrawn.
- **If `gap < 0` and `allow_sells` is false:** no order (the "no-sell VA"
  variant some practitioners prefer, to avoid whipsaw/turnover/taxes) — that
  week's action is simply "do nothing," the same as DCA would do only if its
  deposit were $0 that week, except DCA always invests its own $500
  regardless. This is included as a grid arm, not the primary configuration
  (see below), since it is a real practitioner variant worth testing
  separately.
- **On non-week-end days:** no order (buy_usd = sell_usd = 0); cash sits
  idle earning IRX, same as every other family's between-deposit days.

## Data inputs

Daily OHLC close/open price of the asset itself only (one of the 5 core
assets, tested independently — single-asset family, per the task's
instruction to assess this as single-asset using the existing `engine.py`).
No macro or alternative data. Sourced via `src.backtest.v3.data.load_dev()`
only.

## Parameters (3 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `annual_growth_rate` | 0.06, 0.10, 0.14 | 0.10 |
| `max_multiple_of_deposit` | 2, 4, 8 | 4 |
| `allow_sells` | True, False | True |

`annual_growth_rate=0.10` (the primary) matches Edleson's own commonly-cited
~10%/year assumed-growth illustration and is close to long-run blended
equity/commodity historical CAGR, a reasonable "no-look" prior rather than
something tuned to any one asset's own realized return (which would leak
information from the very data being tested). `max_multiple_of_deposit=4`
keeps any single week's action within 4x the base $500 deposit ($2,000),
bounding lumpiness while still letting the rule meaningfully deviate from
DCA after a real drawdown. `allow_sells=True` is the primary because it is
the *classic*, full Edleson value-averaging rule (the literature's actual
subject); the no-sell variant is a secondary grid arm.

## Grid

3 x 3 x 2 = **18 configurations** (<= 36 cap; well under, since 3 params
each have a small, economically meaningful set of values rather than being
stretched to fill the ceiling).

## Primary configuration

`annual_growth_rate=0.10, max_multiple_of_deposit=4, allow_sells=True`.

## Expected sign

**Ambiguous-to-modest on final wealth, but this is a stated expectation
going in, not a hedge added after seeing results.** Precisely because this
family is deliberately constructed to remove the capital-timing advantage
that Hayley's critique identifies as the main driver of VA's textbook IRR
edge, the wealth effect under a capital-neutral construction is expected to
be small and could go either way asset-by-asset, similar in spirit to family
003's own near-null wealth finding under a similarly capital-neutral
(reserve-based) construction. Any genuine edge must come from the
"contrarian re-timing along the account's own value path" effect described
in "Mechanism" being real and net-positive, which is a real but weaker
channel than the literature's own (capital-timing-inflated) headline claims.
**Sharpe** is expected to benefit somewhat more consistently than wealth, if
at all, since systematically buying more after declines and less/selling
after rallies should reduce the variance of invested-dollar-weighted returns
relative to DCA's constant exposure — the same qualitative channel family
003 targeted directly via variance, but here targeted indirectly via price
level versus an assumed growth path. The effect should be more pronounced,
in either direction, for assets whose prices show more mean-reversion around
a trend (equities, precious metals) than for a strongly trending asset like
BTC over its short development history, where VA's under-buying during the
fastest compounding periods is expected to be a real headwind.

## Degenerate configuration (implementation check only, not a grid arm)

`enabled=False`: bypasses the target-path calculation entirely and returns
`buy_usd = cash, sell_usd = 0` on **every** trading day (not just week-ends)
— bit-for-bit identical to `engine.make_dca_decider`'s own decision rule,
reproducing plain DCA exactly (same pattern as families 001-003's
`enabled=False` checks).
