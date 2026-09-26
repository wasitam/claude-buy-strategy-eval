# Family 039: Realized-kurtosis (fat-tail) sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Bali, T.G., Cakici, N. and Whitelaw, R.F. (2011), "Maxing Out: Stocks as
Lotteries and the Cross-Section of Expected Returns," *Journal of
Financial Economics* 99(2), 427-446 (extreme-outcome/tail-risk sizing
literature, the same "MAX effect" family the loop's family 023
[realized skewness] already drew on for its lottery-preference framing);
Kraus, A. and Litzenberger, R.H. (1976), "Skewness Preference and the
Valuation of Risk Assets," *Journal of Finance* 31(4), 1085-1100 (the
classical higher-moment asset-pricing framework that motivates both
skewness- and kurtosis-based risk premia -- investors dislike both
negative skewness and excess kurtosis (fat tails) and demand compensation
for holding assets exposed to either, but the two are formally distinct
moments of the return distribution, established there and re-verified
concretely below). Seed queue idea #40 (research-loop-plan-v3.md sec 7.3
addendum, `state/research_queue.md`).

## Mechanism ("why would this work, and who is on the other side?")

Realized kurtosis is the **fourth standardized moment** of an asset's
recent daily-return distribution: `Kurt_t = E[(r-mu)^4] / Var(r)^2 - 3`
(excess kurtosis, so a Normal reference distribution reads exactly 0).
It measures **tail thickness relative to a Normal reference, independent
of direction** -- a return series with occasional very large moves of
*either sign*, embedded in an otherwise quiet history, has high excess
kurtosis regardless of whether those large moves are up or down. A
"fat-tailed" recent regime (elevated trailing kurtosis) is empirical
evidence that the asset's return-generating process has recently been
drawing from a distribution more prone to extreme outliers -- a
**crash-prone/turbulence-prone** state, in the sense of Kraus &
Litzenberger's kurtosis-averse investor and the broader tail-risk
literature (Bali, Cakici & Whitelaw's MAX effect documents the mirror
lottery-seeking side: investors overpay for a chance at a single large
positive outlier). A risk-averse DCA buyer who is unconcerned with timing
market direction but does care about avoiding buying heavily into a
statistically demonstrated turbulence regime can re-time (not resize) the
same total deposit stream: buy a *reduced* share while the asset's own
trailing excess kurtosis sits in the high tail of its own recent history
(elevated crash-proneness, whichever direction the next big move turns
out to be), and buy a *increased* share while trailing kurtosis sits in
the low tail (a calmer, thinner-tailed regime, closer to Normal), banking
the shortfall from calm-regime weeks as cash to fund fat-tail-regime
underweighting -- no leverage, no borrowing, no view on sign or direction,
only on tail *thickness*. The "other side" of this trade is compositional:
during a fat-tailed regime, market participants who must transact
regardless of tail risk (index funds' scheduled flows, forced sellers,
option dealers delta-hedging into realized gamma) absorb the liquidity
this family declines to add to; during a calm/thin-tailed regime, this
family adds liquidity that turbulence-averse investors have temporarily
withdrawn, in exchange for typically better average execution.

## Category

**Volatility targeting.** (Reduces exposure specifically when the asset's
own recent-return statistical process signals elevated risk of extreme
outcomes -- the same "de-risk when the recent regime looks dangerous"
logic as families 003/031/035, but keyed on the fourth moment (tail
thickness) rather than the second moment (dispersion) or a ratio of the
first two moments.)

## Required rigorous distinction from family 023 (realized skewness) -- primary burden

Family 023 and this family are the closest pair in the loop so far: both
are trailing-window, price-only, higher-standardized-moment statistics of
an asset's own daily-return distribution, both categorized among
higher-moment distributional-shape signals, and both drawn from adjacent
literature (Amaya et al. 2015 realized skewness / Bali-Cakici-Whitelaw
MAX-effect kurtosis-and-lottery framing). The distinction must be made
concrete and precise, not asserted:

- **Family 023's statistic (realized SKEWNESS, third standardized
  moment)** measures **asymmetry**: whether a recent return history's
  large moves have tended to be predominantly on the down side or the up
  side. It **has a sign**. A return series and its exact sign-flipped
  mirror image (negate every daily return) have realized skewness values
  that are equal in magnitude but **opposite in sign**.
- **This family's statistic (realized KURTOSIS, fourth standardized
  moment)** measures **tail thickness relative to Normal, regardless of
  direction**. It is **direction-blind by construction**: a return series
  and its sign-flipped mirror image have **identical** realized kurtosis,
  because the statistic raises deviations to the 4th power (always
  non-negative) rather than the 3rd (sign-preserving). A symmetric
  fat-tailed distribution -- heavy on *both* sides equally -- has **high
  kurtosis and exactly zero skew**. A lopsided-but-thin-tailed
  distribution can have **strong skew and only ordinary kurtosis**.
  Neither moment is recoverable from the other: the third and fourth
  standardized moments are, in general, mathematically independent
  functionals of a distribution (e.g. any symmetric distribution has
  skew identically 0 regardless of its kurtosis, and distributions exist
  with matched skew and arbitrarily different kurtosis).

### Concrete numeric divergence example (constructed, computed at run time by the module under test, not by hand -- see `scripts/v3/run_039_realized_kurtosis_sizing.py`)

**Path A -- symmetric fat tails, near-zero skew, high kurtosis:** 18 days
of a flat 0.0% return, plus one day of **+6%** and one day of **-6%**
(the two outliers exactly offsetting so the window's mean is exactly 0,
making the distribution perfectly symmetric about its own mean):

| Statistic | Value |
|---|---|
| Realized skewness (family 023's un-demeaned formula, and the ordinary demeaned formula -- both give the same sign/magnitude story on this exactly-symmetric construction) | **0.0** (exactly, by construction: a perfectly symmetric distribution) |
| Realized excess kurtosis (this family's formula) | **+7.0** (a Normal reference reads 0; this is a strongly leptokurtic, fat-tailed 20-day window) |

**Path B -- moderate one-sided skew, ordinary (near-Normal) kurtosis:**
16 days of a **-0.5%** return, plus 4 days of **+2.0%** (many small losses,
occasionally punctuated by a few moderate -- not extreme -- gains; no
single day is a large outlier relative to the others):

| Statistic | Value |
|---|---|
| Realized skewness | **+1.50** (a clearly, strongly positively skewed 20-day window) |
| Realized excess kurtosis | **+0.25** (close to the Normal reference of 0 -- an ordinary, unremarkable tail thickness) |

Path A has essentially zero skew but 28x the excess kurtosis of Path B;
Path B has a strong, unambiguous skew reading but a near-Normal kurtosis
reading barely above Path A's rounding noise. The two statistics'
*rankings of these two windows are inverted relative to each other*,
which is the concrete proof this iteration's task requires: a family-023-
style skewness screen would flag Path B as the more extreme window and
Path A as unremarkable; this family's kurtosis screen flags exactly the
opposite. Neither can substitute for the other.

### Real-data confirmation that kurtosis tracks tail-thickness/crash episodes specifically (not skew)

Pre-grid formula/sign spot-check (SP500 dev data, 90-day trailing window,
**strictly pre-2020**): the well-documented 1987-10-19 "Black Monday"
crash. The trailing 90-day excess-kurtosis reading peaks at **51.41 on
1987-10-19 itself** (the crash day), against a **2017 calm-year** 90-day
excess-kurtosis median of only **2.77** (mean 2.77, std 1.02, max 5.16) --
an order-of-magnitude difference, confirming the statistic spikes
specifically around a real historical tail event, as the mechanism
requires, and is not degenerate or noise-dominated. (October 1987
overall: 90-day trailing kurtosis mean 14.95, ranging 0.43-51.41 across
that quarter -- both the run-up and the immediate aftermath show elevated
readings, consistent with the crash's well-documented fat-tailed
character.)

## Brief distinction from family 003 (realized variance) and family 031 (mean/variance ratio)

- **Family 003 (vol-managed sizing):** sizes on trailing realized
  **VARIANCE**, the **second** standardized moment -- pure dispersion,
  with **zero shape information**: it cannot distinguish a calm-looking
  series with two rare huge outliers (high kurtosis) from an equally
  dispersed series where every day contributes similarly to the variance
  (low kurtosis) as long as the *total* sum-of-squared-deviations
  matches. Variance treats all deviations equally regardless of how
  concentrated they are among a few extreme days vs. spread evenly; this
  family's fourth-moment statistic is specifically sensitive to that
  concentration (a few huge deviations inflate the 4th power far more
  than an even spread of the same total squared deviation).
- **Family 031 (Kelly-Sharpe sizing):** sizes on the trailing
  **mean-to-volatility ratio** (a Sharpe-style first-moment-over-second-
  moment statistic) -- a measure of risk-adjusted *drift*, with, like
  family 003, **no higher-moment/shape component at all**. Two return
  series with identical means and variances but very different tail
  behavior (one Normal, one a rare-huge-outlier mixture) give family 031
  the *same* signal and family 003 the *same* signal, but give this
  family (039) very different signals.

## Exact rules

1. Daily (log) return: `r_t = ln(Close_t / Close_{t-1})`.
2. Trailing realized excess kurtosis (causal, `kurt_window` trading days
   including day `t`, standard demeaned fourth-standardized-moment
   estimator, matching Bali-Cakici-Whitelaw/Kraus-Litzenberger's
   textbook definition, deliberately the ordinary DEMEANED formula --
   unlike family 023's un-demeaned Neuberger skewness formula -- since
   kurtosis has no scale-invariance shortcut analogous to skewness's
   `sum(r^3)/sum(r^2)^1.5` and the standard finance/statistics literature
   on realized kurtosis uses the demeaned form):

   `Kurt_t = mean((r_i - r_bar)^4, i in window) /
             mean((r_i - r_bar)^2, i in window)^2  -  3`

   where `r_bar` is the trailing window's own mean return. Undefined
   (NaN, treated as neutral) until `kurt_window` trading days of return
   history exist, or on the negligible-probability zero-variance case.
3. Causal, point-in-time **percentile rank** of `Kurt_t` within its own
   trailing `pctile_lookback`-day window of past `Kurt` values (inclusive
   of day `t`; identical rolling-percentile-rank construction to family
   036's `compute_percentile_rank`, never a fixed whole-sample threshold,
   never a future value). Defaults to 0.5 (neutral) until
   `pctile_lookback` days of valid `Kurt` history exist.
4. **Sizing multiplier** on each trading day, continuous in the
   percentile rank (same functional form as family 036's autocorrelation
   sizing, sign INVERTED since this family reduces size when the
   percentile is HIGH, unlike family 036 which increases size when its
   percentile is high):

   `m_t = clip(1 - k * (2 * pctile_t - 1), min_mult, max_mult)`

   - `pctile_t = 1.0` (kurtosis at the top of its own recent range --
     most fat-tailed/crash-prone) gives `m_t = clip(1-k, min_mult, max_mult)`,
     the SMALLEST multiplier -- reduced buying, banking the shortfall.
   - `pctile_t = 0.0` (kurtosis at the bottom of its own recent range --
     thinnest-tailed/calmest) gives `m_t = clip(1+k, min_mult, max_mult)`,
     the LARGEST multiplier -- increased buying, drawing down the banked
     reserve.
   - `pctile_t = 0.5` (median/neutral) gives `m_t = 1.0` exactly -- plain
     DCA for that day.
5. Order submitted every trading day: `target_buy_usd = weekly_deposit *
   m_t`, capped at `max_lump_multiple * weekly_deposit` (fixed constant,
   not grid-varied, matching family 036's convention) and then at
   available cash by the engine's own no-leverage cap (sec 3.2). Never a
   sell, never leverage, never borrowing -- a below-1.0-multiplier day
   banks the shortfall as cash (earning IRX), available to fund a later
   above-1.0-multiplier day, the same reserve mechanism families
   003/005/015/016/017/023/030/031/035/036 already use.

**Critical check applied (families 014/033/037's now-3x-confirmed
lesson):** `min_mult` is fixed at values strictly below 1.0 in every grid
cell (0.25 or 0.5, never 1.0) precisely so the reserve-banking arm of this
continuous multiplier genuinely funds the boost arm rather than being
silently nullified by the engine's cash cap -- verified directly in the
pre-grid cash-reserve-dynamics check below, not merely asserted.

## Parameters (4 tunable, <=5 per sec 3.4)

| Param | Meaning | Grid values |
|---|---|---|
| `kurt_window` | Trailing window (trading days) for `Kurt_t` | 60, 90 |
| `pctile_lookback` | Trailing window (trading days) for the percentile rank of `Kurt_t` | 252, 504 |
| `k` | Sensitivity of the multiplier to the percentile rank | 0.5, 1.0, 1.5 |
| `min_mult` | Lower clip bound on the multiplier (always < 1.0) | 0.25, 0.5 |

Fixed constants (not grid-varied, matching family 036's convention):
`max_mult=2.0`, `max_lump_multiple=3.0`.

Grid: 2 x 2 x 3 x 2 = **24 configurations** (<=36 cap; 4 tunable
parameters <=5).

## Primary configuration

`kurt_window=90, pctile_lookback=252, k=1.0, min_mult=0.5` (`max_mult=2.0,
max_lump_multiple=3.0` fixed). `kurt_window=90` mirrors family 023's own
primary `skew_window=90` choice for a clean, directly comparable window
length between the two higher-moment families being distinguished here;
`pctile_lookback=252, k=1.0, min_mult=0.5` exactly mirrors family 036's
own primary configuration's shape, for consistency with this loop's other
continuous-percentile-multiplier family.

## Expected sign of the effect

Beats DCA on final wealth AND Sharpe: buying less during elevated-
trailing-kurtosis (fat-tailed/crash-prone) episodes -- funded from a
reserve banked during depressed-trailing-kurtosis (thin-tailed/calm)
episodes -- is expected to avoid committing capital just ahead of or
during a statistically-flagged turbulence regime, re-timing (not
increasing) the same total deposit stream toward calmer windows.

## Pre-grid checks to run before trusting the grid (per this iteration's task instruction)

(a) `PRIMARY_CONFIG` membership in `grid_configs()` verified via an
    import-time assertion in `realized_kurtosis_sizing.py`.
(b) Kurtosis-computation correctness spot-check against the 1987-10-19
    Black Monday episode (above) -- confirms sign/magnitude sanity
    (kurtosis spikes near a real crash episode).
(c) The skewness/kurtosis divergence example (above), computed live by
    the module under test, not hand-copied.
(d) Confirm no dev-period sanity check references a 2020+ date or an
    unseen ticker (both checks above use SP500 dev data only: 1987-10 and
    2017, and the constructed toy paths use no real dates at all).
(e) `min_mult` fixed below 1.0 in every grid cell (0.25, 0.5), verified
    directly via the cash-reserve-dynamics check.

## Scope

Single-asset family, tested across all 5 core assets under the standard
sec 4.1 >=3/5 rule (same precedent as families 001/003/005/014/017/020/
021/023/026/028/030/031/033/034/035/036/037): a purely price-only,
per-asset internal signal with no cross-asset comparison.
