# Family 029: Risk-parity (inverse-volatility) rebalancing across the 5 core assets

**Status:** pre-registered. Committed before any backtest is run on development
data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Asness, C., Frazzini, A., Pedersen, L.H. (2012), *Leverage Aversion and Risk
Parity*, Financial Analysts Journal 68(1); the broader risk-parity /
inverse-volatility-weighting literature (Qian, E. (2005), "Risk Parity
Portfolios"; Bridgewater's "All Weather" construction as popularized in
practitioner writing). Seed queue idea #29 (research-loop-plan-v3.md sec
7.3 successor list, `state/research_queue.md`): "threshold/band-rebalancing
portfolio," refined per the task's guidance into a **risk-parity-style**
target-weight mechanism: rebalance the 5-asset portfolio toward weights set
inversely proportional to each asset's own trailing realized volatility,
rather than toward fixed equal weights (v2's closed C1-C3) or
momentum-dependent weights (this loop's family 013).

## Mechanism ("why would this work, and who is on the other side?")

The risk-parity/inverse-vol-weighting premise (Asness, Frazzini & Pedersen
2012) is that a portfolio's risk contribution, not its dollar allocation,
should be balanced across its components. A fixed equal-DOLLAR-weight
portfolio (v2's C1) is implicitly a high-RISK-weight bet on its most
volatile constituent: in this 5-asset universe, BTC's realized volatility is
several multiples of gold's or the S&P 500's, so an equal-dollar-weight
portfolio's day-to-day return variance is, in practice, dominated by BTC
alone even though BTC is only 1/5 of the dollars. Risk-parity weighting
corrects this by giving each asset a dollar weight inversely proportional to
its own volatility -- lower-volatility assets (gold, the S&P 500) get a
larger allocation, higher-volatility assets (BTC) get a smaller one -- so
that, approximately, each asset contributes a comparable share of the
portfolio's total variance rather than a comparable share of its dollars.
Layered on top of the same periodic-rebalancing discipline that v2's C1-C3
already confirmed beats never-rebalancing, the economic case is that a
risk-balanced mix realizes a higher Sharpe ratio per unit of leverage/risk
taken (the levered-risk-parity literature's headline claim), and, even
unlevered (as this family and this whole loop's "no leverage" ceiling
requires, sec 3.4), a volatility-weighted mix should have a smoother NAV
path than an equal-dollar mix dominated by its single most volatile
constituent, which can improve compounded (geometric) terminal wealth via
lower variance drag even without any change in the arithmetic-mean return
of the underlying assets. The "other side" of the trade is: (a) investors
who hold a fixed equal-dollar mix regardless of relative volatility (this
family's own benchmark, and v2's closed C1), effectively over-weighting
their portfolio's risk budget toward whichever asset happens to be most
volatile at any time; and (b) investors who chase whichever asset has
recently had the highest raw return without regard to the volatility they
are taking on to get it. The cost paid, if the mechanism doesn't hold, is
giving up some of BTC's (and other high-vol assets') outsized raw
compounding by structurally underweighting it relative to equal-dollar
DCA, plus the added turnover/fees of a weekly vol-driven rebalance, which
is why the family must still pass at 0.25% fees (sec 4.1).

## Category

**Rebalancing / allocation** (research-loop-plan-v3.md sec 4.5) -- not
"Volatility targeting" (sec 4.5's other listed category, which in this
loop's convention, family 003's vol-managed sizing, governs how much of a
SINGLE asset's OWN deposit stream to buy based on that asset's own
volatility, scaling total dollars invested up or down). This family never
changes how much total capital is deployed (it is always 100% invested,
exactly $2,500/week combined, like family 013); it only changes how that
fixed total is SPLIT across the 5 assets, based on their RELATIVE
volatilities to each other -- an allocation/rebalancing decision, not a
sizing decision. This family is scoped as a **5-asset portfolio family**,
assessed under sec 4.1's "Portfolio" line, directly following families
002/010/013's precedent.

## Why this is NOT a re-test of sec 7.2's closed C1/C2/C3 (required case)

v2's C1, C2 and C3 rebalanced-portfolio families (closed, sec 7.2, "5-asset
rebalancing-frequency sweep") used **fixed target weights** (equal-weight,
or another static allocation, set once and never revised) with periodic
rebalancing back to that same unchanging target; the only things C1/C2/C3
varied were the *fixed* target weights themselves and the rebalancing
*frequency*. v2's own report already found "rebalancing beats
never-rebalancing, frequency barely matters within a sensible range" using
those static targets. This family's target weights are **volatility-
dependent and time-varying**: every week, the target vector is recomputed
from each asset's own trailing realized volatility (a purely risk-based,
not momentum-based or price-level-based, statistic), so the portfolio's
target shifts continuously as relative volatilities shift -- the target
this family rebalances *toward* is a different object in kind from C1/C2/C3's
static targets, exactly as family 013's momentum-dependent tilt was. This
family's `equal_vol_override=True` diagnostic mode (see "Implementation
checks" below) collapses exactly to C1's fixed equal-weight weekly rebalance
-- the same "closed family nested as one degenerate corner of a strictly
larger, materially different parameter space" argument family 013 already
made and this loop accepted: the object under test here (whether
volatility-based dynamic targets beat static equal-dollar targets) was
never evaluated in v2, and no real (non-override) configuration in this
family's grid is equivalent to any C1/C2/C3 rule.

## Why this is NOT a re-test of family 013 (this loop, momentum-tilted rebalancing, REJECTED)

Family 013 and this family are both "dynamic-target weekly rebalancing
across the 5 core assets," but the two mechanisms driving the target weight
are fundamentally different inputs answering different questions:

| | Family 013 (momentum-tilted rebalancing) | Family 029 (this family, risk-parity rebalancing) |
|---|---|---|
| Signal input | Trailing **total return** (a directional/momentum signal: is this asset going up or down relative to the others?) | Trailing **realized volatility** (a risk/dispersion signal: how much does this asset's price move day to day, regardless of direction?) |
| Direction of the economic bet | Tilts weight TOWARD assets that have recently gone UP (trend-following / momentum premium) | Tilts weight AWAY from assets that move a lot in EITHER direction (risk-balancing, direction-agnostic) |
| What zero-signal collapses to | `tilt_strength=0`: exactly equal weight (C1-equivalent) | `equal_vol_override=True` (all assets assumed equally volatile): exactly equal weight (C1-equivalent) -- same degenerate corner, reached via an unrelated input |
| Relationship between the two assets' target weight, if asset A has both higher trailing return AND higher volatility than asset B (a common real-world pattern -- e.g. BTC vs. gold) | Weights A UP (rewards the higher return) | Weights A DOWN (penalizes the higher volatility) -- **the two mechanisms can and typically do point in OPPOSITE directions for the same asset pair** |
| Underlying literature/premise | Momentum / trend-following premium (underreaction, slow-moving capital) | Risk parity / leverage aversion (equalizing risk contribution, not chasing return) |

The last row is the decisive case: because BTC (this universe's highest-
volatility asset) has also, over the development window, been one of its
highest-trailing-return assets, family 013's momentum tilt and this
family's risk-parity tilt make **opposite** allocation calls for the same
asset in the same market conditions -- family 013 wants MORE BTC when its
trailing return is strong, this family wants LESS BTC whenever its
volatility is elevated, independent of its return. This is not a
re-parameterization of the same underlying idea; it is a different
economic question (return-chasing vs. risk-balancing) answered by a
different input variable, with a genuinely different, often contradictory,
practical implication for the same portfolio. This family's category
("Rebalancing / allocation") is the same declared category as family 013's
(both are dynamic-target rebalancing, not fixed-weight or momentum-
concentration rotation), which is consistent with sec 4.5's distinctness
rule applying at the level of the eventual 2 WINNERS' categories and
excess-return correlation, not at the level of every family sharing a
category needing to be mechanically identical -- the mechanism itself, per
the case made above and per sec 7.1(4)'s "different signal definition or a
different mechanism" bar for building on a related idea, is what matters,
and it is genuinely different here.

## Win-rule interpretation

Per the task instruction and directly following families 002/010/013's
precedent: this family is assessed under sec 4.1's **"Portfolio"** line --
one NAV series (pooled $2,500/week deposit, $500/asset-equivalent, across
the 5-asset universe, dynamically risk-parity-weighted and rebalanced)
compared against **fixed-weight 5-asset DCA** ($500/week into each of the 5
assets, never rebalanced), on final wealth AND Sharpe, at both fee levels.
The holdout pass rule (sec 5.3 "Portfolio" line) and sec 4.3's robustness
checks are adapted the same way families 002/013's were.

## Exact rules

**Shared calendar:** identical construction to families 002/013's: SP500's
own NYSE daily trading-day index, clipped to start once every core asset has
data (BTC is shortest), with every other asset's OHLC forward-filled onto
that shared calendar.

**Signal, computed at each shared-calendar day `t`'s close, using only data
through `t` (no lookahead):**
- For each asset `a`, daily log return `r_a,s = ln(close_a,s / close_a,s-1)`.
- Trailing realized volatility `vol_a,t = stdev(r_a,t-vol_lookback_days+1, ..., r_a,t)`
  (a rolling standard deviation of daily log returns over the trailing
  window ending at `t`, inclusive -- causal by construction, since a
  backward-looking rolling window can never see day `t+1` or later). During
  the startup ramp before `vol_lookback_days` observations exist, a
  shorter rolling window (`min_periods = max(5, vol_lookback_days // 4)`)
  is used instead of excluding the asset, and any still-undefined leading
  values are forward-filled (never backward-filled, which would leak future
  data) or, only for the very first day(s) where even that is unavailable,
  set to a fixed constant (0.02) -- this only ever touches the first few
  calendar days of the entire multi-decade series, long before the first
  weekly rebalance can occur.
- **Raw target weight, inversely proportional to volatility:**
  `raw_w_a,t = (1/vol_a,t) / sum_b(1/vol_b,t)` (the 5 assets' inverse
  volatilities, renormalized to sum to 1 -- this is the risk-parity
  allocation itself, before bounds).
- **Bounds (no leverage, no negative/short weights, no extreme
  concentration):** `raw_w_a,t` is clipped to `[min_weight, max_weight]`
  per asset, then **renormalized** to sum to exactly 1 (divide each by
  their sum) -- the portfolio is always exactly 100% invested (cash + all 5
  positions), never partially in cash, matching families 010/013's
  "no cash-parking leg" precedent for this mechanism category.
- **Optional smoothing:** if `smoothing_halflife_days > 0`, the clipped/
  renormalized weekly target-weight sequence is further smoothed with a
  causal exponentially-weighted moving average (`pandas .ewm(halflife=...,
  adjust=False)`, which by construction only ever averages a row with its
  own past, never a future row) to reduce week-to-week whipsaw and
  turnover as the rolling volatility estimate updates. Because each row
  already sums to 1 and already respects `[min_weight, max_weight]`
  elementwise, and EMA smoothing is a per-asset linear (convex) combination
  of past values, the smoothed sequence automatically still sums to 1 and
  still respects the same bounds -- no re-clip/renormalize is needed after
  smoothing. `smoothing_halflife_days=0` means no smoothing at all (the raw
  clipped/renormalized weight is used directly).

**Rebalance cadence:** weekly, on the shared calendar's last trading day of
each ISO week -- the same day the pooled $2,500 deposit is credited. Fixed,
not a tunable grid parameter, per families 002/010/013's precedent (matches
the deposit cadence, keeps grid cost bounded, stays within the "at most
daily" complexity ceiling).

**Orders:** on a rebalance day, for each asset the target dollar value is
`target_weight_a x total_portfolio_value` (cash + sum of all positions,
valued at that day's close, including that day's deposit). The order is
`target_dollar_a - current_dollar_value_a` (positive = buy, negative =
sell). All orders fill at the next trading day's open -- sells across all 5
assets first, then buys, buys capped by available pooled cash (engine sec
3.2, `portfolio_engine.py`). On non-rebalance days, no orders are placed.

**Degenerate case, and what "degenerate" means for this family (family
010/013's degenerate-config-trap lesson applies directly -- this family,
like 013, always rebalances, so it needs two distinct reference points,
not one):**
1. `enabled=False` (a strategy-module-level bypass flag, not a real grid
   arm): bypasses the volatility/weight computation entirely and, each
   week, submits a buy order for exactly that asset's own $500 deposit
   share and nothing else (no selling, no reallocation) -- the literal-DCA
   degenerate case required by sec 3.2 check 1's literal wording ("the
   degenerate parameters of every strategy must reproduce DCA exactly").
2. `equal_vol_override=True` (the family's **equal-vol-assumption edge
   case**, the task's suggested reference point for this family): forces
   every asset's estimated volatility to an identical constant value
   regardless of the real data, which collapses the inverse-vol formula to
   exactly `1/5` for every asset every week -- equivalent to v2's Strategy
   C1 (equal-weight weekly rebalancing), matched **independently** against
   family 013's separately-built `make_equal_weight_rebalance_decider`
   reference (a decider function built in a different module for a
   different family, with no shared code path to this family's weight
   computation, so agreement between the two is a genuine independent
   check, not a tautology). This confirms the same "degenerate here means
   C1-equivalent, not DCA-equivalent" pattern family 013 established: the
   real grid never actually sets a `smoothing_halflife_days` or
   `vol_lookback_days` value that forces `equal_vol_override`-equivalent
   behavior on real data (real assets never have exactly identical
   volatility), so `equal_vol_override` exists purely as an implementation-
   check bypass flag, analogous to family 013's `enabled=False`, not as a
   grid-swept parameter.

## Data inputs

Daily OHLC close of all 5 core assets, and the daily risk-free rate (IRX,
for the pooled cash account's interest accrual between rebalances), all
sourced via `src.backtest.v3.data.load_dev()` only. No macro or alternative
data -- the signal is computed purely from the 5 assets' own prices (their
own trailing realized volatility).

## Parameters (3 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `vol_lookback_days` (realized-volatility estimation window) | 63, 126, 252 (~3mo, ~6mo, ~12mo) | 126 |
| `min_weight` / `max_weight` (bound pair, see below) | 2 pairs | (0.05, 0.40) |
| `smoothing_halflife_days` (EMA smoothing of the weight sequence; 0 = none) | 0, 10 | 10 |

`min_weight` and `max_weight` are swept together as one "bound pair"
parameter taking one of 2 values (not as two independent axes, which would
produce nonsensical `min_weight > max_weight`-adjacent combinations),
exactly matching family 013's convention:

| Pair | `min_weight` | `max_weight` |
|---|---|---|
| A (tighter) | 0.10 | 0.30 |
| B (looser, primary) | 0.05 | 0.40 |

(Rebalance cadence is fixed at weekly, not a tunable grid parameter, per the
judgment call above -- this keeps the family at 3 tunable parameters:
`vol_lookback_days`, the bound-pair choice, and `smoothing_halflife_days`,
well under the 5-parameter ceiling.)

## Grid

`vol_lookback_days` (3) x bound-pair (2) x `smoothing_halflife_days` (2) =
**12 configurations** (<= 36 cap).

## Primary configuration

`vol_lookback_days=126, min_weight=0.05, max_weight=0.40,
smoothing_halflife_days=10` -- a ~6-month trailing volatility window (a
common risk-parity convention, long enough to smooth out short-term vol
spikes but short enough to adapt to genuine regime shifts within the
development period), the looser bound pair (0.05-0.40, matching family
013's primary bound choice, so a single asset can never exceed twice the
equal-weight base or fall below a quarter of it), and a modest smoothing
half-life (10 weekly steps, roughly 2.5 months) to reduce whipsaw/turnover
from week-to-week vol re-estimation without materially lagging genuine
volatility regime changes -- chosen before any backtest is run on
development data.

## Expected sign of the effect

Positive: the strategy should beat fixed-weight 5-asset DCA on both final
wealth and Sharpe. On Sharpe, the case is direct: down-weighting the
highest-volatility constituent (BTC) relative to equal-dollar weighting
should mechanically reduce the portfolio's total return variance, and if
the lower-volatility assets' risk-adjusted (not raw) returns are
comparable, per-unit-of-risk performance should improve. On wealth, the
case is less certain (an explicit tension flagged here before any
backtest, per sec 7.1(4)'s pre-registration discipline): the same
down-weighting of BTC that helps Sharpe could reduce final wealth in a
window where BTC's raw compounding materially outpaced the other 4
assets -- precisely the mechanism that caused family 013's momentum tilt
to fail sec 4.1's wealth leg despite passing its Sharpe leg. This family's
own primary configuration could plausibly show the same wealth/Sharpe
split family 013 did; that specific risk is called out here in advance so
it cannot be read as a post-hoc excuse if it occurs.

## Implementation checks to run (sec 3.2, before any results count)

1. Degenerate config (`enabled=False`, bypasses the volatility/weight
   computation entirely, buys exactly each asset's own $500 deposit share
   every week, no selling) reproduces fixed-weight 5-asset DCA exactly,
   bit-for-bit on units and pooled cash.
2. Family-specific check: `equal_vol_override=True` (the equal-vol-
   assumption edge case, `enabled=True`) reproduces family 013's
   independently-built equal-weight weekly-rebalance reference
   (`make_equal_weight_rebalance_decider`, fixed 20%/asset target,
   rebalanced weekly, no volatility computation) bit-for-bit on units and
   pooled cash -- confirming the "degenerate here means C1-equivalent, not
   DCA-equivalent" claim above with a genuinely independent reference, not
   merely asserting it. That same `equal_vol_override=True` config's
   result must also **differ** from plain (never-rebalanced) DCA.
3. Cash and positions never negative, for both the DCA baseline and the
   primary config.
4. No-lookahead test: perturbing all 5 assets' OHLC data strictly after
   day `t` must leave every order on/before day `t` unchanged -- the
   trailing-volatility signal at day `t` must depend only on that day's and
   prior days' returns, never a future one (this also validates the
   ffill/constant-fallback startup handling described above never reaches
   forward into perturbed data).
5. Point-in-time macro data: not applicable -- this family uses only price
   data (5 core assets' OHLC) and IRX, no ALFRED-vintage macro series.
6. Capital neutrality: not applicable in the sense families 004/006/007's
   check addresses (a single-asset strategy that can bank/delay deposits
   into cash) -- this family, like family 013, never parks any capital in
   cash outside the pooled portfolio (bounded weights always sum to 1, so
   the portfolio is always exactly 100% invested); there is no reserve
   mechanic that could violate capital neutrality.

## Pre-grid non-degeneracy sanity check (required before the grid runs, per the established convention -- families 015/016/.../028)

Before trusting any backtest result, confirm on real development data that
the primary configuration's risk-parity target weights actually differ
meaningfully from equal weight across the 5 assets -- specifically, that
BTC (this universe's highest-volatility asset by a wide margin) receives a
materially SMALLER average target weight than gold (a lower-volatility
asset) under the primary configuration's realized-volatility estimates.
If this comparison does not hold clearly on real data, the mechanism is not
doing what it is pre-registered to do and the run must stop for
re-examination before any grid result is trusted. (Concretely checked in
`scripts/v3/run_029_risk_parity_rebalance.py` before the grid loop: the
primary config's average `target_weights["BTC"]` over the shared calendar
must be materially below its average `target_weights["GOLD"]`, and below
the equal-weight baseline of 0.20; results reported in `results.md`.)

## Robustness adaptations (sec 4.3, portfolio-level, only if sec 4.1 passes)

Directly following families 002/013's precedent: rolling windows (3-year,
on the portfolio NAV), block bootstrap (4-week blocks, same block start
indices shared across all 5 assets, raw + detrended), and placebo
(circular-shift the weekly target-weight sequence). Bootstrap/placebo run
counts scoped to **60 simulations each** (families 002/010/011/013
precedent -- cost-scoped down from the plan's default 500, since each
simulation reruns the full 5-asset portfolio engine), declared here before
any backtest, actual count confirmed again in results.md. Per families
006/007/008/011/013's precedent, sec 4.3 is only run in full if sec 4.1
passes first.
