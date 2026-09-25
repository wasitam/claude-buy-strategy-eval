# Family 013: Momentum-tilted rebalancing across the 5 core assets

**Status:** pre-registered. Committed before any backtest is run on development
data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Asness, C., Moskowitz, T., Pedersen, L. (2013), *Value and Momentum
Everywhere*, Journal of Finance; and the broader time-series/cross-sectional
momentum literature (Moskowitz, Ooi & Pedersen 2012; Jegadeesh & Titman
1993). Seed queue item #13 (research-loop-plan-v3.md sec 7.3): "tilt the
target weights toward assets with strong recent trailing momentum and away
from those with weak/negative momentum, then rebalance toward those TILTED
(not fixed) targets on a regular schedule."

## Mechanism ("why would this work, and who is on the other side?")

v2's confirmed finding (sec 7.2's closed C1/C2/C3 families) is that
periodically rebalancing a multi-asset portfolio back toward a **fixed**
target beats never-rebalancing, because rebalancing mechanically sells
recent relative winners and buys recent relative losers, capturing a
mean-reversion/volatility-harvesting premium across assets whose relative
prices fluctuate around a roughly stable long-run mix. This family asks
whether that premium can be improved by making the *target itself* trend-
following: instead of always rebalancing back to a fixed 20% each, shift
the target weights toward whichever of the 5 assets currently show the
strongest trailing momentum, and away from the weakest/negative-momentum
ones, before executing the same weekly rebalance discipline. The economic
case for the tilt on top of rebalancing is the standard momentum premium
(underreaction to information, slow-moving trend-following capital
providing positive feedback for months) layered on top of the standard
rebalancing/volatility-harvesting premium — two documented effects
combined, not one substituting for the other. The "other side" of the
trade is: (a) investors who rebalance mechanically to a *fixed* mix
regardless of trend (giving up the momentum layer), one of whom is this
family's own benchmark; and (b) investors who chase very recent performance
without any equal-weight anchor or rebalancing discipline at all (pure
momentum funds with no mean-reversion/bounds), who take on more
concentration risk than this family's bounded tilt allows. The cost paid,
if the mechanism doesn't hold, is whipsaw around momentum turning points
and higher turnover/fees than a fixed-weight rebalance, which is why the
family must still pass at 0.25% fees (sec 4.1).

## Category

**Rebalancing / allocation** (research-loop-plan-v3.md sec 4.5) — not
"Cross-asset rotation / relative strength" (family 002's category). See the
explicit distinction from family 002 below; this family is scoped as a
**5-asset portfolio family**, assessed under sec 4.1's "Portfolio" line.

## Why this is NOT a re-test of sec 7.2's closed C1/C2/C3 (required case)

v2's C1, C2 and C3 rebalanced-portfolio families (closed, sec 7.2, "5-asset
rebalancing-frequency sweep") used **fixed target weights** — equal-weight
or another static allocation, set once and never revised — with periodic
rebalancing back to that same unchanging target. The only things C1/C2/C3
varied were the *fixed* target weights themselves and the rebalancing
*frequency*; the target vector at any two points in time was either
identical (same static allocation) or drawn from a small closed set of
static allocations, never a function of recent price history.

This family's target weights are **momentum-dependent and time-varying**:
every week, the target vector is recomputed from each asset's trailing
return relative to the other four, so the portfolio's target shifts
continuously as relative trends shift — the target the strategy rebalances
*toward* is a different object in kind, not just a different fixed number,
from C1/C2/C3's static targets. A degenerate/zero-tilt version of this
family (`tilt_strength=0`, see "Implementation checks" below) collapses
exactly to C1's fixed equal-weight weekly rebalance — which is precisely
the point: this family nests C1's mechanism as its `tilt_strength=0` limit
and asks whether adding a momentum-dependent tilt **on top of** that
already-tested, already-closed mechanism improves it. Nesting a closed
family as one degenerate corner of a strictly larger, materially different
parameter space is not the same as re-testing the closed family's exact
rules — the object under test here (the tilt itself, and whether dynamic
targets beat static ones) was never evaluated in v2, and no non-zero-tilt
configuration in this family's grid is equivalent to any C1/C2/C3 rule.

## Why this is NOT a re-test of family 002 (dual momentum, this loop, NEAR-MISS)

Family 002 and this family are both "momentum across the 5 core assets,"
but they are mechanistically distinct enough to warrant separate categories
(sec 4.5): family 002 is **binary in/out cross-asset rotation** — an
absolute-momentum admission gate (an asset must beat the T-bill hurdle to
qualify at all) followed by picking only the `top_n` qualifying assets at
equal weight, with everything else (including 100% of the portfolio, if
nothing qualifies) parked in cash. It can and does exit the risky-asset
universe entirely. This family is a **continuous weight-tilting rebalance**
that is always 100% invested across all 5 assets (like family 010's
gold/silver rotation, there is no cash-parking leg): every asset always
gets a strictly positive weight (bounded below by `min_weight > 0`), and
momentum only ever shifts *how much* of the portfolio each asset gets, not
*whether* it is held at all. Family 002's category is "Cross-asset rotation
/ relative strength" (concentration into the best asset(s), potential full
exit to cash); this family's category is "Rebalancing / allocation"
(continuous reallocation among a fixed all-five-asset roster, always fully
invested, mean-reversion-harvesting rebalance discipline as the base case
with a momentum tilt layered on). A `tilt_strength=0` config in this family
does not reduce to family 002's rule at any parameter setting (family 002's
zero-momentum limit is "buy nothing, sit in 100% cash," since nothing would
qualify under a zero-return-threshold read; this family's zero-tilt limit
is "always rebalance to equal weight, always fully invested" — the two
degenerate cases are opposite in kind, one collapsing to all-cash, the
other to a fully-invested static rebalance). This is a materially different
mechanism and is not a re-test of family 002.

## Win-rule interpretation

Per the task instruction and directly following family 002's and family
010's precedent: this family is assessed under sec 4.1's **"Portfolio"**
line — one NAV series (pooled $2,500/week deposit, $500/asset-equivalent,
across the 5-asset universe, dynamically tilted and rebalanced) compared
against **fixed-weight 5-asset DCA** ($500/week into each of the 5 assets,
never rebalanced — the same benchmark family 002 used), on final wealth AND
Sharpe, at both fee levels. The holdout pass rule (sec 5.3 "Portfolio"
line) and sec 4.3's robustness checks are adapted to the portfolio NAV the
same way family 002's were.

## Exact rules

**Shared calendar:** identical construction to family 002's: SP500's own
NYSE daily trading-day index, clipped to start once every core asset has
data (BTC is shortest), with every other asset's OHLC forward-filled onto
that shared calendar.

**Signal, computed at each shared-calendar day `t`'s close, using only data
through `t` (no lookahead):**
- For each asset `a`, trailing momentum `mom_a,t = close_a,t / close_a,t-lookback_days - 1`
  (simple trailing total return over the lookback window). While fewer than
  `lookback_days` observations exist for an asset, its momentum is treated
  as 0 (neutral) rather than excluded, since — unlike family 002 — this
  family never excludes an asset from the portfolio; a neutral (zero)
  momentum reading simply keeps that asset at its equal-weight base target
  until it has a full lookback history.
- Cross-sectional demeaned, standardized momentum score:
  `z_a,t = (mom_a,t - mean_b(mom_b,t)) / (std_b(mom_b,t) + 1e-6)`
  (the mean and std are taken across the 5 assets' `mom_b,t` values on day
  `t` — this puts the tilt on a comparable dimensionless scale regardless
  of each asset's absolute volatility or momentum magnitude, and is
  symmetric: the 5 raw tilts sum to a number very close to 0 before
  clipping).
- **Raw target weight:** `raw_w_a,t = (1/5) * (1 + tilt_strength * z_a,t)`.
- **Bounds (no leverage, no negative/short weights, no extreme
  concentration):** `raw_w_a,t` is clipped to `[min_weight, max_weight]`
  per asset.
- **Renormalize** the 5 clipped weights to sum to exactly 1 (divide each by
  their sum) — the portfolio is always exactly 100% invested (cash + all 5
  positions), never partially in cash, matching family 010's "no
  cash-parking leg" precedent for this mechanism category. `tilt_strength=0`
  makes every `z_a,t` term vanish from the formula regardless of its actual
  value, so `raw_w_a,t = 1/5` for all `a` identically — the clip and
  renormalize steps are then no-ops (0.2 is inside any sane `[min_weight,
  max_weight]` bound), so the target is exactly equal weight every week.

**Rebalance cadence:** weekly, on the shared calendar's last trading day of
each ISO week — the same day the pooled $2,500 deposit is credited. Fixed,
not a tunable grid parameter, per family 002's and 010's precedent (matches
the deposit cadence, keeps grid cost bounded, stays within the "at most
daily" complexity ceiling).

**Orders:** on a rebalance day, for each asset the target dollar value is
`target_weight_a x total_portfolio_value` (cash + sum of all positions,
valued at that day's close, including that day's deposit). The order is
`target_dollar_a - current_dollar_value_a` (positive = buy, negative =
sell). All orders fill at the next trading day's open — sells across all 5
assets first, then buys, buys capped by available pooled cash (engine sec
3.2, `portfolio_engine.py`). On non-rebalance days, no orders are placed.

**Degenerate case, and what "degenerate" means for this family (important
— family 010's degenerate-config-trap lesson applies directly):**
`tilt_strength=0` (a real, in-grid parameter value, `enabled=True`) makes
every week's target exactly equal-weight (1/5 each), so the strategy
**still rebalances weekly toward that fixed 20% target** — it sells
relative winners and buys relative losers every week to hold the mix at
20% each. This is **not** equivalent to plain (never-rebalanced) DCA; it is
equivalent to v2's Strategy C1 (equal-weight weekly rebalancing), the
fixed-weight member of the closed C1/C2/C3 family, per the "why this is not
a re-test" section above. The engine-level implementation check (sec 3.2
check 1, "degenerate parameters reproduce DCA exactly") therefore uses a
**separate `enabled=False` path** — bypassing the momentum/weight
computation entirely and, each week, submitting a buy order for exactly
that asset's own $500 deposit share and nothing else (no selling, no
reallocation) — which is the actual literal-DCA degenerate case, the same
pattern families 002/010 used. A second, family-specific implementation
check verifies that `tilt_strength=0, enabled=True` instead reproduces an
**equal-weight-rebalanced** reference portfolio (weekly rebalance to fixed
20%/asset, no momentum) bit-for-bit — confirming the strategy module's
zero-tilt limit really is C1-equivalent, not silently something else. Both
checks are run and reported in results.md, exactly as this section
declares before any backtest runs.

## Data inputs

Daily OHLC close of all 5 core assets, and the daily risk-free rate (IRX,
for the pooled cash account's interest accrual between rebalances), all
sourced via `src.backtest.v3.data.load_dev()` only. No macro or alternative
data — the signal is computed purely from the 5 assets' own prices.

## Parameters (4 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `lookback_days` (momentum lookback) | 126, 252 (~6mo, ~12mo) | 252 |
| `tilt_strength` (steepness: weight shift per unit of standardized relative momentum) | 0.0, 0.5, 1.0, 2.0 | 1.0 |
| `min_weight` / `max_weight` (bound pair, see below) | 2 pairs | (0.05, 0.40) |

`min_weight` and `max_weight` are not swept as two independent axes (which
would produce nonsensical `min_weight > max_weight`-adjacent combinations);
instead they are swept together as one "bound pair" parameter taking one of
2 values, so the grid stays a clean Cartesian product:

**Bound pairs actually used**, so this stays unambiguous:

| Pair | `min_weight` | `max_weight` |
|---|---|---|
| A (tighter) | 0.10 | 0.30 |
| B (looser, primary) | 0.05 | 0.40 |

(Rebalance cadence is fixed at weekly, not a tunable grid parameter, per
the judgment call above — this keeps the family at 4 tunable parameters:
`lookback_days`, `tilt_strength`, and the bound-pair choice, which is
logically one parameter taking one of 2 values even though it sets two
numbers at once; reported as 4 distinct tunables to stay conservative and
well under the 5-parameter ceiling.)

## Grid

`lookback_days` (2) x `tilt_strength` (4) x bound-pair (2) = **16
configurations** (<= 36 cap).

## Primary configuration

`lookback_days=252, tilt_strength=1.0, min_weight=0.05, max_weight=0.40`
(bound-pair B) — the literal 12-month momentum lookback (Asness/Moskowitz/
Pedersen's and family 002's own primary lookback), a moderate (not maximal)
tilt strength so the base rebalancing mechanism is not swamped, and the
looser bound pair (0.05-0.40) so the momentum tilt has meaningful room to
act while a single asset can never exceed twice the equal-weight base or
fall below a quarter of it — chosen before any backtest is run on
development data.

## Expected sign of the effect

Positive: the strategy should beat fixed-weight 5-asset DCA on both final
wealth and Sharpe, because it should retain v2's confirmed rebalancing
premium (selling relative winners / buying relative losers on a
schedule, still active at `tilt_strength=0` and, in a bounded way, at any
tilt strength since the mechanism always reverts toward the boundless
equal-weight anchor over time as momentum readings change sign) while
adding the momentum literature's documented cross-sectional trend premium
on top, without ever fully exiting any asset (bounded weights mean the
strategy retains meaningful exposure to all 5 assets' long-run secular
returns at all times, unlike family 002's binary rotation).

## Implementation checks to run (sec 3.2, before any results count)

1. Degenerate config (`enabled=False`, bypasses the momentum/weight
   computation entirely, buys exactly each asset's own $500 deposit share
   every week, no selling) reproduces fixed-weight 5-asset DCA exactly,
   bit-for-bit on units and pooled cash.
2. Family-specific check: `tilt_strength=0, enabled=True` (the strategy's
   real zero-tilt grid arm) reproduces a separately-built equal-weight
   weekly-rebalance reference portfolio (fixed 20%/asset target,
   rebalanced weekly, no momentum) bit-for-bit on units and pooled cash —
   confirming the documented "degenerate here means C1-equivalent, not
   DCA-equivalent" claim above, not merely asserting it.
3. Cash and positions never negative, for both the DCA baseline and the
   primary config.
4. No-lookahead test: perturbing all 5 assets' OHLC data strictly after
   day `t` must leave every order on/before day `t` unchanged — the
   cross-sectional z-score signal at day `t` must depend only on that day's
   and prior days' closes across all 5 assets, never a future one.
5. Point-in-time macro data: not applicable — this family uses only price
   data (5 core assets' OHLC) and IRX, no ALFRED-vintage macro series.

## Robustness adaptations (sec 4.3, portfolio-level, only if sec 4.1 passes)

Directly following family 002's precedent: rolling windows (3-year, on the
portfolio NAV), block bootstrap (4-week blocks, same block start indices
shared across all 5 assets, raw + detrended), and placebo (circular-shift
the weekly target-weight sequence). Bootstrap/placebo run counts scoped to
**60 simulations each** (family 002/010/011 precedent — cost-scoped down
from the plan's default 500, since each simulation reruns the full 5-asset
portfolio engine), declared here before any backtest, actual count
confirmed again in results.md. Per family 006/007/008/011's precedent, sec
4.3 is only run in full if sec 4.1 passes first.
