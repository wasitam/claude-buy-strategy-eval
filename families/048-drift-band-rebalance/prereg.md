# Family 048: Tolerance-band ("drift-triggered") rebalancing of the 5-asset portfolio

**Status:** pre-registered. Committed before any backtest is run on development
data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Donohue, C. and Yip, K. (2003), "Optimal Portfolio Rebalancing with
Transaction Costs," *Journal of Portfolio Management* 29(4), 49-63; Masters,
S.J. (2003), "Rebalancing," *Journal of Portfolio Management* 29(3), 52-57.
Seed queue item #49 (research-loop-plan-v3.md sec 7.3): "rebalance back to
FIXED equal target weights ... only when any asset's current weight drifts
outside a symmetric band around its target ... rather than on a fixed
calendar cadence regardless of drift."

## Mechanism ("why would this work, and who is on the other side?")

Donohue & Yip and Masters both make the same practical point about
rebalancing a multi-asset portfolio: a **calendar-triggered** rule (rebalance
every week/month/quarter regardless of how far weights have actually
drifted) pays transaction costs on rebalances that do little risk-control
work (weights barely drifted) and, less often, lets a large drift run for a
whole calendar period before correcting it. A **tolerance-band** (drift-
triggered) rule instead rebalances only when a position's actual weight has
moved far enough from its target to matter, and skips the trade entirely
when it hasn't. The economic case is explicitly a **transaction-cost/
turnover-minimization** argument, not a return-forecasting one: the same
long-run mean-reversion/volatility-harvesting premium that motivates any
fixed-target rebalance (v2's closed C1/C2/C3) is preserved (this family
rebalances to the same fixed equal-weight target C1 used), while unnecessary
trades between meaningfully-drifted states are avoided, which should show up
as **lower turnover and fees, and consequently a Sharpe/wealth edge that
comes disproportionately from the cost side rather than from timing return
better than a fixed calendar would.** The "other side" of the trade is
investors who rebalance on a fixed calendar regardless of drift (v2's own
C1/C2/C3, and every calendar-cadence member of that closed sweep) — they pay
some rebalancing costs during low-dispersion periods that a drift-band rule
would skip, and, in the (see below) less common alternative case, may let a
large drift run for longer between scheduled dates than a band rule would
tolerate. Because the mechanism is fee-side, not return-side, per the task's
explicit framing this family's expected sign is read primarily on
**Sharpe and turnover/fees**, not necessarily on raw final wealth — a wealth
edge is plausible (fewer fee-drags compound) but is not the primary
hypothesis, and a result that improves Sharpe/fees without clearly improving
wealth would not be dismissed as a mechanism failure the way it would be for
a return-forecasting family. (Sec 4.1's combined wealth-AND-Sharpe bar is
still the one this family must clear to become a finalist — this note is
about how to *interpret* the numbers, not a request to relax the bar.)

## Category

**Rebalancing / allocation** (research-loop-plan-v3.md sec 4.5).

## Why this is NOT a re-test of sec 7.2's closed C1/C2/C3 (required case)

v2's C1, C2 and C3 rebalanced-portfolio families (closed, sec 7.2, "5-asset
rebalancing-frequency sweep") used a **fixed target weight vector** and
varied only the **pre-declared calendar frequency** at which the portfolio
was rebalanced back to it (weekly / monthly / quarterly) — the trigger for
every rebalance event in that sweep is the calendar date alone, never a
function of how far prices have actually drifted. This family also uses a
fixed, equal-weight target (identical in kind to C1's target — no momentum
or risk-parity tilt, per the task's explicit framing) but its **trigger is
path-dependent**: whether a rebalance fires on any given week-end depends on
the realized price divergence of the 5 assets since the last rebalance, not
on which week-end it is. `band_pct=0` (checked every week-end, since real
price paths essentially never leave weights at exactly the target) is the
one config in this family's grid that behaves like continuous calendar
rebalancing (see "Implementation checks" — it reproduces an equal-weight
weekly-rebalance reference, i.e. C1's own mechanism) — the point of that
degenerate config is exactly to confirm that this family's design "contains"
C1 as one *boundary case* of a strictly larger, materially different trigger
space, the same nesting relationship family 013 established for its own
`tilt_strength=0` config. Every `band_pct > 0` configuration produces
rebalance events whose *timing* cannot be described by any fixed calendar
frequency at all — the number of rebalances and the calendar dates they land
on are outputs of the realized price path, not inputs chosen in advance.
This is the genuinely different mechanism axis the task requires, and it is
verified concretely below (not merely asserted): rebalance events must
cluster during high cross-asset dispersion periods rather than falling on a
fixed schedule.

**Note on the prior iteration's judgment call (family 029, this loop):**
family 029's iteration considered a literal drift-band trigger for its own
queue item (#29) and judged it "too close in spirit" to C1-C3, refining that
item into risk-parity instead. This iteration's task instructions explicitly
revisit the literal drift-band framing for a *different* queue item (#49)
with a more detailed, concrete distinction requirement (the calendar-vs-
path-dependent-trigger argument above, plus the required real-data
clustering verification) — the two iterations reached different conclusions
about the same underlying idea because #49's task instructions supply the
sharper argument and the concrete verification step that #29's iteration
judged was missing. Both are documented here for the record.

## Why this is NOT a re-test of families 002, 013, 029 or 043 (this loop)

- **Families 002 (dual momentum) and 043 (liquidity rotation)** both ask
  "which asset(s) should the marginal deposit favor right now" — a
  cross-sectional selection/rotation question, answered by ranking the 5
  assets against each other on a return or liquidity statistic. This family
  asks neither: it never ranks the assets against each other, and every
  asset always keeps the same 20% target regardless of any cross-sectional
  comparison.
- **Families 013 (momentum-tilted rebalancing) and 029 (risk-parity
  rebalancing)** both ask "what should each asset's TARGET weight be" — the
  target vector itself is a function of trailing return (013) or trailing
  volatility (029), time-varying week to week even absent any drift. This
  family's target is **always exactly 20% per asset, fixed for the entire
  backtest** — never recomputed from any signal. The only thing that varies
  is **when** the (constant) target is enforced.
- Put together: 002/043 vary "which assets", 013/029 vary "what target",
  this family varies "when to enforce a target that never changes" — three
  genuinely different axes of the same broad "rebalancing/rotation" design
  space, not three readings of the same axis.

## Required concrete distinction check: rebalances cluster with dispersion, not calendar

Run on real SP500/GOLD/SILVER/BTC/OIL development data, primary config,
before any grid or robustness work (see `scripts/v3/run_048_drift_band_rebalance.py`
"pre-grid checks" section for the actual numbers, reported in `results.md`):

1. **Inter-rebalance gap irregularity.** For a genuinely calendar-triggered
   rule (weekly/monthly/quarterly, C1-C3's own design), the number of
   trading days between consecutive rebalance events is constant by
   construction (0 variance). This family's rebalance-event gaps must show
   material dispersion (a non-trivial coefficient of variation), confirming
   the trigger is not secretly reducible to a fixed cadence.
2. **Dispersion correlation.** Build a weekly cross-sectional dispersion
   series (the standard deviation, across the 5 assets, of that week's
   simple return) and a binary "a rebalance fired this week-end" indicator
   from the primary config's real run. The point-biserial correlation
   between the two must be **materially positive** — rebalance weeks must
   have higher average cross-asset dispersion than non-rebalance weeks. A
   near-zero or negative correlation would mean the trigger is not actually
   responding to realized divergence, undermining the family's own
   mechanism claim, and would be reported as a failed check, not
   suppressed.
3. Both checks must pass (irregular gaps AND positive dispersion
   correlation) before the grid is trusted; a failure here would be a
   design/implementation problem, not a market-outcome finding, and would
   stop the iteration before any results count (same discipline as the
   pre-grid non-degeneracy checks family 021/043 introduced).

## Win-rule interpretation

Assessed under sec 4.1's **"Portfolio"** line, directly following families
002/010/013/029/043's precedent: one NAV series (pooled $2,500/week deposit
across the 5-asset universe) compared against **fixed-weight 5-asset DCA**
($500/week into each asset, never rebalanced), on final wealth AND Sharpe,
at both fee levels. Per the mechanism note above, turnover and total fees
are also reported prominently in results.md alongside the sec 4.1 numbers,
since they are this family's own hypothesized channel.

## Exact rules

**Shared calendar:** identical construction to families 002/013/029/043:
`^GSPC`'s own NYSE trading-day index, clipped to start once every core asset
has data (BTC is shortest), every other asset's OHLC forward-filled onto
that shared calendar.

**Fixed target:** `target_weight_a = 1/5` for every asset `a`, for the
entire backtest — never recomputed, never tilted by any signal.

**Trigger, checked at each shared-calendar week-end (the same day the
pooled $2,500 deposit is credited, matching the deposit cadence, per
family 002/010/013's precedent for fixing the check cadence rather than
making it a tunable):**
- At week-end `t`, using that day's close (including that week's deposit,
  already credited by the engine before `decide()` is called — same
  convention as families 013/029/043), compute each asset's actual weight
  `w_a,t = value_a,t / total_value_t`.
- `drift_a,t = w_a,t - 0.2`.
- **Trigger fires** iff `max_a |drift_a,t| > band_pct` **AND** at least
  `min_days_between_rebalances` shared-calendar trading days have elapsed
  since the last rebalance event (or no rebalance has happened yet). The
  cooldown guards against pathological whipsaw if a very small `band_pct`
  is paired with a volatile week (per the task's own suggested guard).
- **If the trigger fires:** submit orders that move every asset exactly to
  its 20% target dollar value (`target_value_a = 0.2 x total_value_t`,
  `order_a = target_value_a - value_a,t`), sells and buys filled next open
  per the engine's usual mechanics; record this as a rebalance event
  (resets the cooldown clock).
- **If the trigger does not fire:** no rebalancing of existing holdings —
  the week's $500-per-asset deposit is simply invested into each asset at
  its own $500 share (identical to a single week of plain DCA), leaving
  existing positions untouched. This is the "avoid unnecessary turnover"
  half of the mechanism: between triggers, the strategy behaves exactly
  like DCA.
- On non-week-end days, no orders are placed (matches every prior
  portfolio family in this loop).

**Degenerate case:** `band_pct=0.0, min_days_between_rebalances=0` triggers
essentially every week-end (real price paths leave weights at exactly 0.2
only by coincidence), so the strategy rebalances to the fixed 20% target
every week — this is **not** plain DCA; it is equivalent to v2's Strategy C1
(equal-weight weekly rebalancing), the same distinction family 013 had to
make explicit for its own `tilt_strength=0` config. Two independent
implementation-check reference points are used (see below), following
family 013/029/043's precedent.

## Data inputs

Daily OHLC close of all 5 core assets, and the daily risk-free rate (IRX),
sourced via `src.backtest.v3.data.load_dev()` only. No macro or alternative
data — the signal is computed purely from the 5 assets' own prices and
portfolio bookkeeping (no external data dependency at all).

## Parameters (2 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `band_pct` (symmetric tolerance band around each 20% target; trigger if any asset's weight strays by more than this many percentage points) | 0.02, 0.04, 0.06, 0.08, 0.10, 0.15 | 0.05 |
| `min_days_between_rebalances` (cooldown floor, trading days, to avoid pathological whipsaw) | 0, 5, 20 | 5 |

Target weight (0.2 each) and check cadence (weekly, at deposit time) are
fixed by design, not tunable grid parameters, per the task's framing and
family 002/010/013's precedent for keeping cadence-like choices out of the
grid. This keeps the family at 2 tunable parameters, comfortably under the
5-parameter ceiling.

## Grid

`band_pct` (6) x `min_days_between_rebalances` (3) = **18 configurations**
(<= 36 cap).

## Primary configuration

`band_pct=0.05, min_days_between_rebalances=5` — a 5-percentage-point
absolute band around the 20% target (a 25% relative deviation, within the
range of bands commonly discussed in the practitioner rebalancing
literature, e.g. Masters 2003's illustrative examples), paired with a
1-week cooldown floor (matching the deposit/decision cadence itself, so the
cooldown never blocks two consecutive week-end triggers but does prevent a
same-week re-trigger pathology) — chosen before any backtest is run on
development data.

## Expected sign of the effect

Per the mechanism section above: **primarily a Sharpe/turnover/fee effect**,
not a return-forecasting one. The strategy should show materially lower
turnover and total fees paid than v2's C1 (always-rebalance) reference and
than the primary config's own `band_pct=0` grid corner, while retaining most
of the fixed-target rebalancing premium that motivated C1/C2/C3 in the first
place (large drifts still get corrected, just not on every single week-end).
A Sharpe edge over fixed-weight DCA is the primary hypothesis; a wealth edge
is plausible but secondary, and — per the task's explicit framing — the
family's numbers are read with the transaction-cost-minimization story in
mind rather than a forced return-forecasting narrative if the wealth leg
under-performs while turnover/Sharpe clearly improve.

## Implementation checks to run (sec 3.2, before any results count)

1. Degenerate config (`enabled=False`, bypasses the drift/trigger
   computation entirely, buys exactly each asset's own $500 deposit share
   every week, no selling) reproduces fixed-weight 5-asset DCA exactly,
   bit-for-bit on units and pooled cash.
2. Family-specific second reference point (families 013/029/043
   precedent): `band_pct=0.0, min_days_between_rebalances=0, enabled=True`
   (the strategy's real always-trigger grid corner) reproduces an
   INDEPENDENTLY-built equal-weight weekly-rebalance reference (fixed
   20%/asset target, rebalanced every week, no drift logic) bit-for-bit on
   units and pooled cash — confirming the "degenerate here means
   C1-equivalent, not DCA-equivalent" claim above, not merely asserting it.
   Also confirmed to differ from plain DCA.
3. Cash and positions never negative, for both the DCA baseline and the
   primary config.
4. No-lookahead test: perturbing all 5 assets' OHLC data strictly after day
   `t` must leave every order on/before day `t` unchanged — the drift/
   trigger computation at day `t` depends only on that day's and prior
   days' portfolio state.
5. Point-in-time macro data: not applicable — this family uses only price
   data and portfolio bookkeeping, no macro/ALFRED-vintage series.
6. **Pre-grid distinction check (this family's own required addition, see
   above):** rebalance-event gap irregularity (non-trivial coefficient of
   variation) and a materially positive dispersion-vs-rebalance-event
   point-biserial correlation, both verified on real dev-period data with
   the primary config before the grid is trusted.

## Robustness adaptations (sec 4.3, portfolio-level, only if sec 4.1 passes)

Directly following families 002/013/029/043's precedent: rolling windows
(3-year, on the portfolio NAV), block bootstrap (4-week blocks, same block
start indices shared across all 5 assets, raw + detrended), and placebo
(circular-shift the weekly rebalance-event/target-weight sequence).
Bootstrap/placebo run counts scoped to **60 simulations each** (cost-scoped
down from the plan's default 500, declared here before any backtest, actual
count confirmed again in results.md). Per established precedent, sec 4.3 is
only run in full if sec 4.1 passes first; if an early leg of sec 4.2/4.3
already decisively settles the verdict within this iteration's time budget,
the remaining legs are stopped and the gap is logged explicitly in
results.md rather than fabricated, per this iteration's task instructions.
