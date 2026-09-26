# Family 044: Hurst-exponent (fractal trend-persistence) regime sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Mandelbrot, B.B. and Van Ness, J.W. (1968), "Fractional Brownian Motions,
Fractional Noises and Applications," *SIAM Review* 10(4), 422-437 (the
Hurst exponent's mathematical formalization via self-similar/fractional
processes). Peters, E.E. (1994), *Fractal Market Analysis: Applying Chaos
Theory to Investment and Economics*, Wiley (rescaled-range/R-S Hurst-
exponent framework applied specifically to financial return series, and
its trending/H>0.5, random-walk/H~=0.5, mean-reverting/H<0.5
interpretation). Seed queue item #45 (`state/research_queue.md`), category
**Trend / time-series momentum exit** as listed there.

## Mechanism ("why would this work, and who is on the other side?")

The Hurst exponent `H` of an asset's own trailing daily return series,
estimated via classical rescaled-range (R/S) analysis (Peters 1994),
measures **long-range dependence** in the return-generating process: how
the range of the cumulative demeaned return series grows as a function of
the aggregation scale (sub-window length) used to measure it, across
**several scales simultaneously** within the same trailing window. `H~=0.5`
is consistent with a random walk (no persistent memory at any scale);
`H>0.5` indicates a **trending/persistent** regime, where the series
exhibits positive long-range dependence -- large moves tend to be followed,
on average and across multiple time horizons, by further moves in the same
direction, consistent with momentum/trend-following literature (Peters
1994; the broader long-memory-process literature, e.g. fractionally-
integrated ARFIMA-style processes, Granger & Joyeux 1980); `H<0.5`
indicates a **mean-reverting/anti-persistent** regime, where the series
tends to reverse itself across multiple horizons more often than a random
walk would. A DCA buyer who scales buy size UP when `H` sits high in its
own trailing percentile is betting that a genuinely persistent regime
(detected via this multi-scale statistic) is more likely, on the margin, to
continue than a random walk would predict; scaling DOWN (or banking) when
`H` sits low bets that a genuinely mean-reverting regime is more likely to
continue reversing, so committing a large lump today is more likely to be
followed by a better entry price.

**Who is on the other side:** a constant-dollar DCA buyer who never
conditions buy size on the return series' long-range dependence structure
at all -- the same benchmark this whole loop tests against. The economic
rent this strategy attempts to capture is compensation for correctly
timing entries around a real, transient regime feature (long-range serial
dependence structure), not a risk premium; the risk paid is that `H`,
estimated from a finite trailing sample via a classical R/S estimator with
a **well-documented small-sample upward bias** (Peters 1994's own caveat;
verified numerically below), is itself a noisy and biased statistic, so the
signal can misfire and the regime can flip shortly after the strategy sizes
up or down on it -- an even larger estimation-risk caveat than family 036's
already-noisy lag-1 autocorrelation, since a multi-scale statistic
estimated from a short window has fewer effectively independent
observations at its longer scales.

## Category

**Trend / time-series momentum exit** (research-loop-plan-v3.md sec 4.5),
matching the seed queue's own categorization of idea #45.

## Why this is not a re-test, and the required rigorous distinction from family 036

Family 036 (return-autocorrelation regime sizing) is not a closed family
(sec 7.2's list is v1/v2/v2.1 work only) but is the explicitly-named closest
prior family (per this iteration's task brief), since both measure "serial
dependence structure" of returns. The distinction must be made rigorously,
with a concrete numerical example, not just asserted.

### (a) What each family's statistic actually measures

| Family | Statistic | What it captures |
|---|---|---|
| 036 (lag-1 autocorrelation) | `rho_1 = Cov(r_t, r_{t-1}) / Var(r)` over a trailing window | **ONE-STEP** serial dependence only -- whether day `t`'s return predicts day `t-1`'s (a single lag, a single scale) |
| **044 (this family)** | `H` = the slope of `log(R/S)` vs. `log(scale)`, fit across **several sub-window aggregation scales** (a geometric ladder: the full window divided by 1, 2, 3, 4, 6, 8, 12, 16) within the same trailing window | **LONG-RANGE, MULTI-SCALE** dependence -- how the range of the cumulative return series grows across MULTIPLE time horizons simultaneously, a fundamentally different (fractal self-similarity) statistical object than any single-lag correlation |

`rho_1` is a function of the joint distribution of *adjacent* return pairs
only. `H` is fit from `R/S` values computed at 5-8 *different* block sizes
within the same window (for a 252-day window: block sizes 252, 126, 84, 63,
42, 31, 21, 16 after deduplication and the `min_scale=8` floor) -- it can
be, and by the theory of long-memory processes routinely is, materially
different from 0.5 even when `rho_1` is close to zero, whenever the
dependence structure operates at scales beyond a single day. This is a
well-known property of long-memory processes (fractional Gaussian
noise / ARFIMA-style processes, Granger & Joyeux 1980): the theoretical
fGn lag-1 autocorrelation is `2^(2H-1) - 1`, which is exactly zero **only**
at `H=0.5`, but a real (non-fGn) long-memory-like process can decouple the
two far more sharply, as demonstrated concretely below with a constructed
example -- family 036's statistic would read such a series as
"random/no memory" while this family's statistic correctly detects the
long-range structure.

### (b) Concrete constructed numeric example of the required divergence

Constructed synthetic series (n=252, matching the primary configuration's
`hurst_window`): daily "returns" are the sum of (i) a **slow, near-linear
sinusoidal drift** with a period 5x longer than the window (so it looks
almost like a persistent local trend across the whole window, but shifts
gently day to day) and (ii) **dominant i.i.d. Gaussian noise** whose
standard deviation is roughly 6-7x the drift's amplitude (so day-to-day,
the noise swamps the drift, keeping lag-1 autocorrelation pinned near
zero):

```
t = 0..251
drift(t) = 0.0015 * sin(2*pi*t / 1260)     # period = 5*252 days
noise(t) ~ N(0, 0.01)                       # i.i.d., dominant day-to-day
r(t) = drift(t) + noise(t)
```

Verified programmatically (`numpy.random.default_rng(7)`, reproduced live
in `scripts/v3/run_044_hurst_regime_sizing.py::check_lag1_vs_hurst_divergence`,
not hand-copied):

| Statistic | Value |
|---|---|
| Lag-1 sample autocorrelation, `rho_1` (family 036's exact statistic, `numpy.corrcoef`) | **+0.0034** (essentially zero -- family 036 would read this series as "random walk, no signal") |
| Hurst exponent `H` (this family's own `_hurst_rs_single_window`, the exact production function) | **0.692** (materially above 0.5 -- this family correctly detects a trending/persistent regime) |

Family 036's signal on this series is indistinguishable from pure noise
(`rho_1` near its theoretical zero for a true random walk); this family's
signal decisively flags the same series as persistent/trending, because
the slow, coherent sinusoidal drift inflates the growth rate of the
cumulative range across the LONGER sub-window scales (63, 84, 126, 252
days) even though it contributes almost nothing to the single-lag
covariance that dominates `rho_1` -- exactly the theoretical distinguishing
property the mechanism section above describes, demonstrated by direct
construction rather than assertion. (Neither family's grid parameters can
recover the other's signal from this series: family 036's `rho_1` on this
exact series is pinned near zero regardless of `ac_window` -- the noise
dominates every trailing window of daily-adjacent pairs -- while `H`
depends on the multi-scale range-growth structure that `rho_1` never
computes at all.)

### (c) Real-data qualitative cross-check (not the primary proof, which is (b)'s exact construction)

Also computed live (implementation-check time, per checkpoint (b) of the
task brief) on real SP500 development-period data: a genuinely persistent
AR(1)-style synthetic control at `rho=0.3` moves both statistics together
(mean lag-1 autocorrelation +0.293, mean `H` 0.593 across 200 seeds, n=252)
-- confirming this family's `H` estimator responds sensibly to *genuine*
short-range persistence too, so the family-036/family-044 divergence in (b)
above is a real property of *long-range-only* dependence structures, not an
artifact of the estimator failing to detect ordinary trending behavior that
family 036 would also catch. The two families overlap in what they can
detect (both correctly flag simple AR(1)-style persistence) but this
family additionally detects the class of long-range-only dependence
structures family 036 is structurally blind to, which (b) demonstrates
concretely.

## Exact rules

Computed causally at each trading day `t`'s close, using only Close prices
through `t` (no lookahead):

- **Daily log returns:** `r_t = ln(Close_t / Close_{t-1})`.
- **Trailing Hurst exponent** `H_t`: classical rescaled-range (R/S)
  estimate over the trailing `hurst_window` days of `r`. The window is
  split into non-overlapping sub-windows at each of several **scales**
  (`hurst_window` divided by each of `1, 2, 3, 4, 6, 8, 12, 16`,
  deduplicated, floored at a minimum scale of 8 days). At each scale, the
  mean `R/S` statistic (`R` = range of the demeaned cumulative sum of
  returns within the sub-window; `S` = the sub-window's own population
  standard deviation) is computed across all non-overlapping sub-windows
  of that scale, then `H_t` is the ordinary-least-squares slope of
  `log(mean R/S)` vs. `log(scale)` across the scales. Undefined (NaN)
  until `hurst_window + 1` return observations exist, or when fewer than 2
  usable scales exist, or every scale is degenerate (zero variance) -- in
  any of these cases the signal defaults to a neutral percentile of `0.5`,
  the same "not enough information yet" convention as every prior sizing
  family in this loop.
- **Known estimator bias (documented, not corrected):** the naive R/S
  estimator used here has a well-documented small-sample upward bias
  (Peters 1994) -- verified pre-grid below, a pure random-walk synthetic
  series' estimated `H` at `hurst_window=252` averages ~0.55, not exactly
  0.5. This is expected and does not undermine the strategy's mechanism,
  because the sizing signal uses a **relative, causal, point-in-time
  percentile rank** of `H_t` within its own trailing history (see below),
  not an absolute comparison against the textbook `H=0.5` threshold -- a
  constant estimator bias shifts the whole distribution but does not
  change an asset's relative position within its own trailing history. No
  Anis-Lloyd-style bias correction is applied, to keep parameter count and
  rule complexity within sec 3.4's ceiling.
- **Causal, point-in-time percentile rank** `pctile_t`: the fraction of the
  trailing `pctile_lookback` days' own `H_t` values (excluding nothing
  forward-looking) that are `<= H_t`, the same relative-threshold
  convention as families 031/035/036/040/041/042 (adapts to each asset's
  own realized `H` range and estimator bias, instead of an arbitrary
  universal `H=0.5` cutoff). Defaults to `0.5` (neutral) until
  `pctile_lookback` days of `H_t` history exist.
- **Sizing multiplier** (continuous, no discrete "otherwise" state --
  avoiding families 033/034's discrete-multiplier cash-cap-nullification
  pitfall by construction): `m_t = clip(1 + k * (2 * pctile_t - 1),
  min_mult, max_mult)`. A high percentile (elevated `H` -- trending/
  persistent regime) pushes `m_t` above 1 (buy more); a low percentile
  (depressed `H` -- mean-reverting/anti-persistent regime) pushes `m_t`
  below 1 (buy less). Identical continuous-multiplier functional form to
  families 031/036/040/041/042's percentile-driven sizing rule (same clip
  convention, same "no discrete bucket, no exactly-1.0 otherwise state"
  property), applied to a different underlying statistic.
- **Order generation (every trading day):** `target_buy_usd_t =
  weekly_deposit * m_t`, capped at `max_lump_multiple * weekly_deposit`,
  then at available cash (the engine's own no-leverage cap, sec 3.2). No
  sell orders are ever generated. A below-1.0-multiplier day banks the
  shortfall as cash (earning IRX), available to fund a future
  above-1.0-multiplier day -- the same reserve mechanism families
  003/005/015/016/017/030/031/035/036/040 use.

## Data inputs

Daily Close price of the asset itself only (one of the 5 core assets,
tested independently -- single-asset family). No macro or alternative
data. Sourced via `src.backtest.v3.data.load_dev()` only.

## Parameters (4 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `hurst_window` | 100, 126, 252 (trading days; the task brief's suggested 100-252-day range for a stable R/S estimate) | 126 |
| `pctile_lookback` | 252, 504 (~1, ~2 trading years -- the window over which the percentile rank is computed) | 252 |
| `k` | 0.5, 1.0, 1.5 (sensitivity of the multiplier to the percentile rank) | 1.0 |
| `min_mult` | 0.25, 0.5 (lower clip bound) | 0.5 |

Fixed constants (not grid-varied, per families 031/036's own precedent):
`max_mult = 2.0`, `max_lump_multiple = 3.0`, `min_scale = 8` (smallest R/S
sub-window scale, and the scale-divisor ladder `1,2,3,4,6,8,12,16`).

## Grid

3 x 2 x 3 x 2 = **36 configurations** (= 36 cap, at the limit).

## Primary configuration

`hurst_window=126, pctile_lookback=252, k=1.0, min_mult=0.5` (`max_mult=2.0`,
`max_lump_multiple=3.0` fixed).

## Expected sign

Positive, primarily on **Sharpe** rather than final wealth, for the same
structural reason as families 003/031/036: total capital committed over
the full development period is approximately unchanged (only its
week-to-week timing shifts, since every below-1.0 week banks cash that a
later above-1.0 week spends), so the Sharpe channel (buying more during
genuinely persistent/trending regimes detected via long-range dependence,
and less during genuinely mean-reverting regimes) is the more mechanically
plausible primary effect. The wealth effect is a secondary, exploratory
hypothesis and could go either way -- and given the known small-sample
estimator bias and the noisiness of a multi-scale statistic fit from a
short window, a null or negative result (consistent with families
036/040/041's own near-miss outcomes using the identical functional form
applied to different statistics) is a realistic possibility, per plan sec
12's own expectation that most families will not clear every bar.

## Degenerate configuration (implementation check only, not a grid arm)

`enabled=False`: bypasses the Hurst/percentile computation entirely and
forces `m_t = 1.0` for every day, reproducing plain DCA exactly, bit-for-bit
(same pattern as families 003/030/031/036's `enabled=False` degenerate
check). A second reference point (two-reference-point degenerate-config
pattern, families 014/020/033/034/035/036 precedent): `k=0.0` (a real
grid-shaped code path, not the bypass) also forces
`m_t = clip(1 + 0, min_mult, max_mult) = 1.0` for every day regardless of
`pctile_t`, and must independently reproduce plain DCA bit-for-bit too.

## Pre-grid checks required before running the full grid (per this
iteration's task brief)

1. `PRIMARY_CONFIG` verified to be a member of `grid_configs()` via an
   import-time `assert` (families 021/030/036's lesson).
2. Hurst-exponent computation correctness spot-check: a pure random-walk
   synthetic series gives `H` close to 0.5 (within the estimator's own
   documented small-sample bias, verified numerically: mean `H~=0.55` at
   `hurst_window=252` across many seeds), and a synthetic series with an
   injected persistent/trending structure (AR(1) with positive `rho`)
   gives `H` notably above 0.5, monotonically increasing with `rho` (task
   checkpoint (b)).
3. The constructed lag-1-autocorrelation-vs-Hurst divergence example above
   ((b) in the distinction section), recomputed programmatically against
   the module's own production function at run time, not hand-copied
   (task checkpoint (c)).
4. Confirmation that no dev-period sanity check or spot-check ever reads a
   date on or after 2020-01-01 or an unseen ticker (task checkpoint (d) --
   this family uses only `load_dev()`, whose own gate enforces this, plus
   an explicit assertion in the run script that every date referenced in
   any printed check is `< 2020-01-01`; all synthetic-series checks above
   use no real dates at all).
5. Cash-reserve-dynamics check (family 033's underlying lesson,
   generalized by family 036's own precedent for a continuous multiplier):
   confirm the primary config's average cash balance meaningfully differs
   from (exceeds) the plain-DCA baseline's, and that cash is drawn down
   further during high-multiplier (elevated-`H`-percentile) weeks than
   during low-multiplier (depressed-`H`-percentile) weeks -- i.e. a genuine
   reserve builds up and draws down as intended (task checkpoint (e)).
6. Pre-grid non-degeneracy sanity check: the primary config's multiplier
   must not be stuck at 1.0 for nearly the whole sample, and must show
   real dispersion, on all 5 core assets.

## Performance note (declared before the grid runs)

The R/S Hurst-exponent computation is materially more expensive than
family 036's lag-1-autocorrelation computation (multiple nested sub-window
scale loops per rolling step, evaluated via `pandas.Series.rolling(...).apply`).
Since the raw `H_t` signal depends only on `(asset, hurst_window)` -- not on
`pctile_lookback`, `k`, or `min_mult` -- the run script caches the raw
`compute_hurst_signal(...)` array per `(asset, hurst_window)` pair (15
combinations: 5 assets x 3 `hurst_window` values) and reuses it across all
36 grid configurations' shared `hurst_window` arm, rather than
recomputing it 36 x 5 = 180 times. This is a pure performance
optimization with no effect on any result (verified: passing the cached
array through `compute_multiplier`'s optional `hurst_cache` argument
produces bit-for-bit identical output to the uncached path).
