# Family 040: Rolling Sortino-ratio sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Sortino, F.A. and van der Meer, R. (1991), "Downside Risk," *Journal of
Portfolio Management* 17(4), 27-31 (introduces downside deviation as a
risk measure distinct from full/symmetric standard deviation -- risk is
recast as failing to meet a minimum acceptable return, not as dispersion
of any kind, sign included). Sortino, F.A. and Price, L.N. (1994),
"Performance Measurement in a Downside Risk Framework," *Journal of
Investing* 3(3), 59-64 (formalizes the Sortino ratio, `mean excess return
/ downside deviation`, as the standard risk-adjusted-return statistic
built on that downside-only risk measure -- the semi-deviation divisor
uses the FULL window length `n`, not merely the count of negative-return
days, the textbook convention followed here). Seed queue idea #41
(`research-loop-plan-v3.md` sec 7.3 addendum / `state/research_queue.md` /
this iteration's task instruction).

## Mechanism ("why would this work, and who is on the other side?")

Sortino & van der Meer's foundational critique of the ordinary Sharpe
ratio is that investors do not experience upside volatility as risk --
only failing to meet a minimum acceptable return (here, 0% daily log
return) is risk. The Sortino ratio operationalizes this by dividing mean
return by **downside deviation** (semi-deviation: only negative-return
days contribute to the sum of squared deviations that feeds the
denominator) rather than by the ordinary, symmetric standard deviation
that penalizes upside and downside moves equally. An asset whose recent
history has been *unevenly rewarding* -- meaningful upside moves,
consistently small and orderly downside moves -- reads as offering a much
better risk-adjusted trade-off under the Sortino convention than under
the Sharpe convention, precisely because Sortino does not charge the
asset for the very moves an investor is happy to receive. A DCA buyer who
sizes up when an asset's own trailing Sortino ratio sits high in its own
recent percentile (a "recently rewarding relative to its actual downside
risk, not its total dispersion" regime) and sizes down when it sits low
is betting that this downside-specific risk-adjusted-return signal
carries some short-to-medium-horizon persistence, in the same
Kelly-style-proxy tradition family 031 already tested with the ordinary
Sharpe ratio. The "other side" of this trade is whoever prices the asset
using total dispersion (an ordinary Sharpe-ratio-driven allocator, a
volatility-targeting fund, a risk-parity strategy) and therefore
under-weights an asset in exactly the upside-skewed-but-orderly-downside
regime this family's signal is designed to detect and lean into, or
over-weights an asset whose recent losses have been unusually large and
disorderly (elevated downside deviation) even if its total dispersion
(including calm upside moves) looks unremarkable by a symmetric measure.

**Explicit non-leverage clarification (required by research-loop-plan-v3.md
sec 3.4 / sec 2's "no leverage" rule, following family 031's own explicit
precedent since "Sortino ratio" sizing could likewise be mistaken for a
leverage/gearing rule):** this family never implements leverage or
borrowing of any kind. Every buy is capped at (a) a fixed multiple of the
weekly deposit (`max_lump_multiple`, a hard ceiling regardless of banked
cash) and (b) the engine's own unconditional cash cap (`buy_usd <= cash`,
`engine.py` sec 3.2), so the strategy can never spend more than it has
banked from actual past deposits plus earned interest -- exactly the same
no-borrowing, no-negative-cash constraint every prior family in this loop
satisfies. Stated here up front, before any code is written, so the
"Sortino ratio" framing in this family's name and motivation is never
mistaken for a levered risk-parity-style position.

## Required rigorous distinction from family 031 (Kelly-Sharpe sizing) -- primary burden

Family 031 and this family are the closest pair in the loop: both size
buys using a trailing **mean-to-risk ratio** over a comparable window,
both are single-asset, price-only, per-asset internal signals, and both
are framed as Kelly-style edge/odds proxies. The distinction must be
concrete and quantitative, not asserted:

- **Family 031's statistic (Sharpe ratio)**: `S_t = mean(r; trailing
  window) / std(r; trailing window)`, where `std` is the ordinary,
  SYMMETRIC standard deviation -- **every** day in the window, whether an
  up-day or a down-day, contributes to the denominator's sum of squared
  deviations from the mean, with equal weight per unit of deviation
  regardless of sign.
- **This family's statistic (Sortino ratio)**: `So_t = mean(r; trailing
  window) / downside_deviation(r; trailing window)`, where
  `downside_deviation = sqrt(mean(min(r_i, 0)^2, i in window))` -- **only
  negative-return days contribute anything at all** to the sum of squared
  deviations; every positive-return day contributes exactly **zero** to
  the denominator regardless of how large that day's gain was, while the
  divisor itself remains the full window length `n` (the Sortino & Price
  1994 convention, not `n` restricted to the count of negative days).

**These two ratios are NOT rescaled versions of each other.** They are
equal only in the special case where a window's upside and downside
volatility happen to be equal (a genuinely symmetric return distribution
over that window); whenever a trailing window's large moves are
concentrated on one side -- the common case for real asset return series,
which are rarely symmetric over any given 40-90 day window -- the two
ratios diverge, and can diverge by several multiples, as the concrete
example below demonstrates.

### Concrete numeric divergence example (real SP500 development data, 60-trading-day window, matching this family's primary `sortino_window`)

**Window: 1963-11-26 to 1964-02-20** (60 trading days, strictly pre-2020
development data), computed live by the module under test (see
`scripts/v3/run_040_sortino_sizing.py`), not hand-copied:

| Statistic | Value |
|---|---|
| Trailing mean daily log return | **+0.18153%** |
| Trailing standard deviation (symmetric, `ddof=1`) | **0.58438%** |
| Trailing downside deviation (semi-deviation, target=0) | **0.14487%** |
| Days positive / negative / zero (of 60) | **38 / 22 / 0** |
| Largest single up-day move in the window | **+3.902%** |
| Largest single down-day move in the window | **-0.635%** |
| **Sharpe ratio** (family 031's statistic) | **0.3106** |
| **Sortino ratio** (this family's statistic) | **1.2531** |

The window's full standard deviation (0.584%/day) is dominated by a
handful of large **up-day** outliers (the single largest day is +3.90%,
more than 6x any other day's magnitude in either direction), which the
symmetric Sharpe denominator charges the asset for exactly as if those
had been down-days. The downside deviation (0.145%/day, roughly 1/4 of
the full standard deviation) reflects only the window's down-days, all of
which are small and consistently sized (largest -0.635%). The result: an
essentially identical numerator (the same mean return) divided by two
denominators that differ by roughly **4x** (0.584% vs. 0.145%), producing
a Sortino ratio (1.2531) that is **more than 4x** the Sharpe ratio
(0.3106) for the exact same 60-day window of the exact same asset. A
signal built on the Sharpe ratio would rank this window as a
moderately-favorable risk-adjusted period; a signal built on the Sortino
ratio would rank the same window as a strongly-favorable one -- the two
statistics disagree substantially on how favorable this specific real
historical episode was, which is the concrete, non-hypothetical proof
this iteration's task requires. (Scanning all 5 core assets' 60-day
trailing windows in development data for the largest Sortino/Sharpe
ratio divergence surfaces several comparable real episodes -- e.g. BTC
2017-01-04, ratio 3.04x; SP500 1996-11-29, ratio 2.77x; GOLD 2001-10-08,
ratio 2.65x -- confirming this is not a cherry-picked one-off but a
recurring feature of real trailing-window return data whenever a
window's upside and downside volatility are unequal, exactly the
condition the mechanism above describes.)

### Why this is not merely "family 031 rescaled"

If the Sortino ratio were simply a monotonic rescaling of the Sharpe
ratio (e.g. `So_t = c * S_t` for some constant `c` that holds across
time and assets), then a percentile-rank signal built on either statistic
would produce **identical rankings**, and therefore identical sizing
multipliers, on every day -- family 040 would then be nothing more than
family 031 relabeled. The example above disproves this directly: the
ratio `So_t / S_t` is **4.03** for the 1964 SP500 window but, evaluated
across the development sample generally, this ratio varies continuously
and non-monotonically with how asymmetric each window's upside/downside
volatility happens to be (a window with symmetric up/down volatility
gives a ratio of exactly 1.0; a window dominated by downside outliers
instead of upside ones can push the ratio in the opposite direction,
below 1.0, since downside deviation would then be the LARGER
denominator). There is no single constant `c`, and no monotonic
transformation of one statistic reconstructs the other from window to
window -- they are governed by genuinely different information (the full
second moment vs. the downside-only second moment of the same return
series), and a percentile-rank-based sizing signal built on each will
therefore fire on different days, with different magnitudes, for the same
underlying price history.

## Category

**Sizing / valuation.** Judgment call, following family 031's own
precedent directly: this family's signal decides how much to buy *of a
single asset, from that asset's own history*, the same use-case as
families 003, 005, 014, 017, 020, 023, 026, 028, 030, 031, 035, 036, 039,
all filed under "Sizing / valuation" (or, for 003/031/035/036/039, a
mean-to-risk or higher-moment signal filed there by explicit judgment
call rather than under "Volatility targeting," on the grounds that the
signal's headline mechanism is a return-vs-risk (or shape) *ratio/
statistic used to decide how favorable a moment is to size up or down*,
not a risk-targeting rule that resizes purely to hold a constant realized
volatility level). Family 031's own prereg.md already settled this exact
category judgment call for the closest-related mean-to-risk-ratio
statistic (trailing Sharpe); this family's statistic (trailing Sortino)
is filed identically, for the identical reason, with no new judgment call
required. **Decision: Sizing / valuation.**

## Single-asset vs. portfolio scoping

Assessed as a **single-asset family across all 5 core assets** under sec
4.1's standard >=3/5 rule, the trailing-Sortino signal computed
independently per asset from that asset's own daily Close series --
directly following the precedent of families 001/003/005/014/017/020/
021/023/026/028/030/031/033/034/035/036/037/039 (each asset's own
internal signal, no capital ever rotating between assets).

## Data inputs and reachability (gate step)

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only,
  same as every prior family). **No external data dependency at all** --
  the trailing-Sortino signal is computed purely from the asset's own
  `Close` series (daily log returns, their trailing mean and trailing
  downside deviation), so there is no macro/alternative-data
  reachability question and no point-in-time / ALFRED-vintage concern.

## Gate: not a re-test of sec 7.2's closed list

Sec 7.2's closed list has no trailing-Sortino-ratio, downside-deviation,
or any mean-to-risk-ratio signal anywhere in it (v1 Signal A is a
single-day ATR/range-expansion percentile; v1 Signal B is a
trend-stretch/distance rule; v2 SmartDCA is a moving-average-distance
rule; v2 ADCA is a macro-driven rule; v2.1's Strategy D variants are
rate-regime rules). Not a re-test of any of them, and -- per the
dedicated section above -- not a re-test of family 031 either, since the
downside-only semi-deviation denominator is a materially different risk
statistic from the ordinary symmetric standard deviation, with a
concrete, quantified real-data divergence demonstrated above.

## Complexity ceiling check (sec 3.4)

- Rules fit on one page, computed from end-of-day data only. PASS.
- At most one order per asset per trading day (a single buy order, never
  a sell). PASS.
- At most 5 tunable parameters (4 grid-varied + 2 fixed constants,
  `max_mult` and `max_lump_multiple`, the same "N tunable + fixed
  constant(s)" pattern families 015/016/017/030/031 used). PASS.
- All data free and public, already-loaded OHLC only, no new source.
  PASS.
- Grid: 36 configurations (<=36 cap, at the ceiling), one primary
  configuration declared below before any testing. PASS.

## Exact rules

Computed at each trading day's close `t`, using only data available by
that close (strictly causal, no lookahead).

1. **Daily log return**: `r_t = ln(Close_t / Close_{t-1})` (`r_0 = 0` by
   convention, matching every prior family's warm-up convention).
2. **Downside deviation** (Sortino & Price 1994 semi-deviation, target
   (MAR) = 0, causal, over the trailing `sortino_window` trading days
   ending at `t` inclusive): `DD_t = sqrt(mean(min(r_i, 0)^2, i in
   window))`. Only negative-return days contribute a nonzero term to the
   sum inside the square root; every positive-return day contributes
   exactly zero regardless of its magnitude. The divisor of the mean
   inside the square root is the FULL window length (all `sortino_window`
   days), not merely the count of negative days -- the standard textbook
   convention.
3. **Trailing Sortino ratio**: `So_t = mean(r; trailing sortino_window
   days incl. t) / DD_t`. Undefined (NaN, treated as "no signal yet,"
   default multiplier 1.0) until `sortino_window` days of return history
   exist, or on the negligible-probability zero-downside-deviation case
   (a trailing window with no negative-return day at all).
4. **Causal, point-in-time percentile rank**: for each `t`, `pctile_t` =
   the fraction of days in the trailing `pctile_lookback` window ending at
   `t` (inclusive) whose `So` value is `<= So_t` (identical rolling
   percentile-rank construction to families 031/036/039's
   `compute_percentile_rank`, never a fixed whole-sample threshold, never
   a future value). `pctile_t in [0, 1]`; undefined (default 0.5, i.e.
   "neutral") until `pctile_lookback` days of `So` history exist.
5. **Continuous sizing multiplier** (no discrete threshold buckets --
   the multiplier scales continuously with how extreme today's trailing
   Sortino is relative to its own recent history, per this iteration's
   task instruction and family 039's precedent):
   `m_t = clip(1 + k * (2 * pctile_t - 1), min_mult, max_mult)`
   -- at `pctile_t = 1.0` (today's trailing Sortino is the highest in the
   lookback window, i.e. most elevated), `m_t = clip(1 + k, ..., max_mult)`,
   the LARGEST multiplier; at `pctile_t = 0.0` (today's trailing Sortino
   is the lowest, i.e. most depressed), `m_t = clip(1 - k, min_mult, ...)`,
   the SMALLEST multiplier; at `pctile_t = 0.5` (median), `m_t = 1.0`
   (plain DCA). `max_mult` is **fixed at 2.0** for every grid config and
   the primary (not grid-varied; mirrors family 031's own `max_mult`
   ceiling, kept fixed here so the grid isolates the effect of the
   tunable parameters below).
6. **Weekly decision (week-end days only, no sells ever, no leverage)**:
   `target_buy_usd = weekly_deposit * m_t`, capped at
   `max_lump_multiple * weekly_deposit` (a hard safety ceiling on any
   single lump buy even if a large cash reserve has banked up --
   **fixed at 3.0** for every grid config and the primary, matching
   family 031's own fixed ceiling value), then capped again at available
   cash (`min(cash, ...)`, the engine's own no-leverage, no-borrowing cap
   -- see the explicit no-leverage clarification above). A
   below-1.0-multiplier week (depressed trailing Sortino percentile)
   banks the shortfall as cash (earning IRX), available to fund a future
   above-1.0-multiplier week (elevated trailing Sortino percentile) --
   the same reserve mechanism families 003/005/015/016/017/030/031/039
   all use, never leverage or borrowing.
7. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the Sortino/percentile computation entirely and
   buys 100% of that week's cash on every week-end day (0 otherwise) --
   reproduces plain DCA bit-for-bit, the same disable-path pattern every
   prior v3 family uses.

**Critical check applied (families 014/033/037/039's now-4x-confirmed
lesson):** `min_mult` is fixed at values strictly below 1.0 in every grid
cell (0.25 or 0.5, never 1.0) precisely so the reserve-banking arm of this
continuous multiplier genuinely funds the boost arm rather than being
silently nullified by the engine's cash cap -- verified directly in the
pre-grid cash-reserve-dynamics check (below), not merely asserted.

## Parameters (4 tunable + 2 fixed, <=5 tunable per sec 3.4)

| Parameter | Grid values | Primary |
|---|---|---|
| `sortino_window` (trailing window for the Sortino ratio computation, trading days; mirrors family 031's `sharpe_window` grid for a clean, directly comparable window choice) | 40, 60, 90 | 60 |
| `pctile_lookback` (trailing window over which today's Sortino is percentile-ranked, trading days; mirrors family 031's own `pctile_lookback` grid, ~2yr and ~3yr) | 504, 756 | 504 |
| `k` (sensitivity: how strongly the multiplier moves away from 1.0 as the percentile rank moves away from 0.5) | 0.5, 1.0, 1.5 | 1.0 |
| `min_mult` (lower clip bound on the multiplier, always < 1.0) | 0.25, 0.5 | 0.5 |

Fixed constants (not grid-varied, matching family 031's convention):
`max_mult=2.0`, `max_lump_multiple=3.0`.

Grid: 3 (`sortino_window`) x 2 (`pctile_lookback`) x 3 (`k`) x 2
(`min_mult`) = **36 configurations** (<=36 cap, at the ceiling; 4 tunable
parameters, <=5).

## Primary configuration

`sortino_window=60, pctile_lookback=504, k=1.0, min_mult=0.5` (`max_mult=2.0`
and `max_lump_multiple=3.0` fixed for every config, primary included) --
chosen to exactly mirror family 031's own primary configuration's
parameter VALUES (`sharpe_window=60` -> `sortino_window=60`,
`pctile_lookback=504`, `k=1.0`, `min_mult=0.5`), so that any difference in
sec 4 outcomes between the two families is attributable to the
Sharpe-vs-Sortino statistic itself, not to a different choice of window
length or sensitivity.

## Expected sign of the effect

**Positive on both wealth and Sharpe**, if downside-specific risk-adjusted
momentum (as opposed to family 031's total-dispersion-adjusted momentum)
carries genuine short-to-medium-horizon persistence net of this
mechanism's own costs and its weekly (not continuous) decision cadence.
As with every prior timing/banking-mechanic family in this loop, this
only reallocates the *timing* of a fixed deposit stream, never total
capital deployed and never leverage (see the explicit no-leverage
clarification above), so even a real effect may show a modest absolute
wealth/Sharpe margin over DCA. Given that family 031 (the closest sibling
statistic) was itself a NEAR-MISS in this loop -- passing sec 4.1 (4/5
assets) and sec 4.4 (83.3% of its grid) but failing sec 4.2 (DSR
effectively zero) and sec 4.3 decisively (rolling windows below 60%,
bootstrap failing both legs, placebo landing at only the 33rd Sharpe
percentile) -- this family's result should be read with real skepticism
going in: swapping the symmetric denominator for a downside-only one is
a genuine, literature-motivated, economically distinct hypothesis, but it
is entirely possible that it inherits family 031's same underlying
weakness (a signal whose sec 4.1 edge, if any, is concentrated in a small
number of episodes that a trial-count-adjusted or resampling-based check
does not validate as real). This is flagged honestly, before any backtest
is run, following the same precedent family 031's own prereg.md set
relative to families 003/005.

## Implementation-check plan (sec 3.2, to be run in the implementation step)

1. `enabled=False` bypass reproduces plain DCA bit-for-bit (units and
   cash).
2. A second, real grid-shaped code path with `k=0.0` (going through the
   actual Sortino/percentile computation, not the bypass flag) also
   reproduces plain DCA bit-for-bit, since `m_t = clip(1 + 0*(...),
   min_mult, max_mult) = clip(1, ., .) = 1.0` for every day regardless of
   the underlying Sortino reading -- the two-reference-point degenerate-
   config pattern (families 020/033/034/035/039's precedent).
3. Downside-deviation formula correctness spot-check: confirm the
   computation only includes negative-return days (a toy constructed
   window with known values, verified live by the module under test, not
   hand-copied) -- required check (b) of this iteration's task
   instruction.
4. Cash and positions never negative, for the DCA baseline, the primary
   config, and the grid's most aggressive corner (`sortino_window=40,
   pctile_lookback=504, k=1.5, min_mult=0.25` -- the shortest, most
   reactive Sortino window, most extreme sensitivity, and lowest floor,
   i.e. the config expected to swing the multiplier hardest and most
   often).
5. Total capital deployed never exceeds cumulative deposits + interest,
   verified via the principled "never invest" ceiling-bound method
   (`state/bugfix_log.md`'s family-021 fix), for the primary config and
   the aggressive corner.
6. No-lookahead: perturbing all data after day `t` leaves every order
   on/before `t` unchanged, checked at two spot-check points deep into
   the development sample (well before 2020-01-01).
7. Point-in-time macro: N/A -- no macro/alternative data is used at all
   (the signal is computed purely from the asset's own OHLC, already
   point-in-time by construction; the percentile rank is itself
   explicitly constructed to be causal/rolling rather than a
   whole-sample-calibrated fixed threshold, per rule 4 above).
8. Cash-reserve-dynamics check (family 039's pattern, per this
   iteration's task instruction (e)): confirm the primary config's
   realized average cash balance meaningfully exceeds plain DCA's, and
   that the reserve is drawn down more on elevated-multiplier weeks than
   on depressed-multiplier weeks -- verifying `min_mult<1.0` genuinely
   funds the boost arm rather than being nullified by the cash cap.

## Pre-grid non-degeneracy check plan (to be run before the grid is trusted)

Before any grid backtest, the primary configuration's day-fraction with
`m_t` exactly 1.0 and the standard deviation of `m_t` will be computed
against development-window data for all 5 core assets (causal, using only
data through each day's own close). Because the multiplier is driven by a
percentile RANK (by construction close to uniformly distributed over
`[0, 1]` once the rolling window is full), a healthy signal is expected to
show the multiplier away from exactly 1.0 on the large majority of days
and meaningful dispersion (`std(m_t) > 0.01`) -- the run aborts if the
multiplier is stuck near 1.0 (>90% of days) or shows negligible dispersion
on any asset, or if fewer than `pctile_lookback` days of history exist for
any asset's development window (a hard prerequisite check on BTC in
particular, given its short ~5-year development sample). The pre-grid
step will also report the concrete Sortino/Sharpe real-data divergence
example above (recomputed live) and the downside-deviation
negative-days-only spot-check, both required by this iteration's task
instruction before the grid is trusted.

## Confirmation: all pre-grid checks touch only strictly-pre-2020 development data

Every spot-check and example above uses only `src.backtest.v3.data.load_dev()`
data (SP500/BTC/GOLD/SILVER/OIL, strictly before 2020-01-01) or a toy
constructed array with no calendar date at all -- no unseen ticker, no
2020+ date, is ever referenced during development, per this iteration's
task instruction (d).

## Scope

Single-asset family, tested across all 5 core assets under the standard
sec 4.1 >=3/5 rule (same precedent as families 001/003/005/014/017/020/
021/023/026/028/030/031/033/034/035/036/037/039): a purely price-only,
per-asset internal signal with no cross-asset comparison.
