# Family 036: Return-autocorrelation regime sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Lo, A.W. and MacKinlay, A.C. (1988), "Stock Market Prices Do Not Follow
Random Walks: Evidence from a Simple Specification Test," *Review of
Financial Studies* 1(1), 41-66. Lo & MacKinlay's variance-ratio test
rejected the random-walk hypothesis for weekly US equity index returns,
finding significant positive short-horizon serial correlation, i.e.
returns are not independent draws but show a measurable tendency toward
either continuation (trending, positive autocorrelation) or reversal
(choppy/mean-reverting, negative autocorrelation) from one period to the
next. Seed queue item #36 (`state/research_queue.md`), category **Trend /
time-series momentum exit** as listed there.

## Mechanism ("why would this work, and who is on the other side?")

The lag-1 sample autocorrelation of an asset's own trailing daily log
returns, `rho_1 = corr(r_t, r_{t-1})` over a trailing window, measures the
**serial dependence structure** of the return-generating process itself,
independent of the returns' level (mean) or dispersion (variance). A
positive and elevated `rho_1` means the asset's recent daily price changes
have been serially reinforcing one another (an up day tends to be followed
by another up day, and a down day by another down day) -- consistent with
slow information diffusion, momentum trading/herding, or order-flow
autocorrelation documented in the market-microstructure and behavioral-
finance literature (Lo & MacKinlay 1988; Jegadeesh & Titman 1993's
momentum literature at longer horizons; Cutler, Poterba & Summers 1990's
"positive feedback trading" mechanism at short horizons). In that regime, a
DCA buyer benefits from sizing up: a recent uptrend is more likely, on the
margin, to still be in progress. A negative and depressed `rho_1` means
daily price changes have been tending to reverse day over day (an up day
tends to be followed by a down day) -- consistent with bid-ask bounce,
liquidity-provision/market-making activity absorbing order flow, or
short-horizon overreaction-and-correction dynamics (Jegadeesh 1990; Lehmann
1990, the same short-horizon-reversal literature family 030's streak
signal draws on). In that regime, a DCA buyer benefits from sizing down (or
holding cash): today's move is more likely to partially reverse tomorrow,
so committing a large lump today is more likely to be followed by a better
entry price shortly after.

**Who is on the other side:** a constant-dollar DCA buyer who does not
condition buy size on the serial-correlation structure of recent returns
at all -- exactly the same benchmark this whole loop tests against. The
economic rent this strategy attempts to capture is compensation for
correctly timing entries around a real, transient regime feature (serial
dependence), not a risk premium; the risk paid is that `rho_1`, estimated
from a finite trailing sample of noisy daily returns, is itself a noisy
statistic (its own sampling variance can be large relative to its typical
magnitude for daily asset returns, which are usually close to 0), so the
signal can easily misfire, and the regime can flip shortly after the
strategy sizes up or down on it.

## Category

**Trend / time-series momentum exit** (research-loop-plan-v3.md sec 4.5),
matching the seed queue's own categorization of idea #36.

## Why this is not a re-test, and the required fourfold rigorous distinction
from families 003, 005, 030 and 031

None of families 003/005/030/031 is a closed family (sec 7.2's list is
v1/v2/v2.1 work only), but each is the closest prior family by using a
per-asset trailing-return-derived signal to size a DCA buy, so per this
iteration's explicit brief the fourfold distinction must be made
rigorously, with a concrete constructed example, not just asserted.

**(a) What each family's statistic actually measures.**

| Family | Statistic | What it captures |
|---|---|---|
| 003 (vol-managed sizing) | `sigma_recent = std(r)` over a trailing window | The **dispersion** (second moment) of returns -- how big the moves have been, regardless of sign or order |
| 005 (TSMOM sizing) | `sign(trailing 12-month return)` | The **level/direction** (first moment / running sum) of returns -- whether the asset is net up or down over the window, regardless of how it got there |
| 030 (losing-streak reversal) | Consecutive-same-direction-day **count** | A **discrete, magnitude-blind streak length** -- how many days in a row moved the same direction, ignoring the size of each day's move and ignoring every day's relationship with the *next* day beyond an unbroken run |
| 031 (Kelly-Sharpe sizing) | `mean(r) / std(r)` over a trailing window | A **ratio of the first and second moments** (risk-adjusted return level) -- how big the average move has been relative to its dispersion, with no dependency-structure component at all |
| **036 (this family)** | `rho_1 = corr(r_t, r_{t-1})` over a trailing window | The **serial dependence structure** of consecutive returns -- whether one day's return tends to predict the *sign and rough size* of the *next* day's return, entirely independent of the returns' own mean or variance |

Formally, `rho_1 = Cov(r_t, r_{t-1}) / Var(r)`. The numerator is a genuinely
different statistical object (a lag-1 autocovariance) from every one of
003/005/030/031's inputs; the denominator normalizes out the variance
family 003 measures directly, so `rho_1` is by construction invariant to
uniform rescaling of the return series' dispersion in a way none of the
other four statistics are.

**(b) Why no choice of any other family's grid parameters can reproduce
this family's signal, or vice versa.** `rho_1` is a function of the *joint*
distribution of consecutive return pairs `(r_t, r_{t-1})` within the
window; it is well-defined (and can take any value in `[-1, 1]`) for return
series that share an *identical* mean, an *identical* variance, an
*identical* streak-length profile, and hence an *identical* family-031
Sharpe ratio -- proven by direct construction in (c) below. Since
003/005/030/031's outputs are, by definition, unchanged between two return
paths that differ only in the *order* in which the same multiset of daily
returns occurs, and `rho_1` is exactly the statistic most sensitive to that
ordering (it is the correlation between a return and the return
immediately preceding it), none of the four prior families' signals can
recover any information about `rho_1`, and `rho_1` alone does not recover
any of the four prior signals either (many different `(mean, variance,
streak, Sharpe)` tuples are consistent with any given `rho_1`).

**(c) Concrete constructed numeric example (verified programmatically at
implementation-check time against the module's own vectorized
`compute_autocorr_signal`, not hand-copied -- see
`scripts/v3/run_036_autocorr_regime_sizing.py::check_toy_distinctiveness_example`).**
Two toy 8-day return paths, using only the values `+1%` and `-1%` (four of
each):

- **Path A (choppy / day-to-day reversal):**
  `[+1, -1, -1, +1, -1, +1, -1, +1]` (%)
- **Path B (trending / paired-run persistence):**
  `[-1, -1, +1, +1, -1, -1, +1, +1]` (%)

Both paths are *permutations of the identical multiset* of eight daily
returns, so:

| Statistic | Path A | Path B | Identical? |
|---|---|---|---|
| Mean return (family 005's underlying level) | `0.000000` | `0.000000` | YES |
| Sample variance, `ddof=1` (family 003's statistic) | `1.142857` (%^2) | `1.142857` (%^2) | YES |
| `sign(sum of returns)` (family 005's exact statistic) | `0` (flat) | `0` (flat) | YES |
| `mean/std` "Sharpe" (family 031's statistic) | `0.000000` | `0.000000` | YES |
| Max consecutive-same-direction streak (family 030's statistic) | `2` | `2` | YES |
| **Lag-1 autocorrelation `rho_1` (this family's statistic)** | **`-0.750000`** | **`+0.166667`** | **NO -- decisively different** |

Every one of families 003, 005, 030 and 031's signals is **exactly
identical** on these two paths -- a strategy sized off any of those four
statistics alone would treat Path A and Path B as indistinguishable, and
would apply the identical buy multiplier to both. This family's signal
correctly identifies Path A as strongly choppy/mean-reverting
(`rho_1 = -0.75`, close to the theoretical minimum of `-1` for a
period-2-alternating pattern) and Path B as mildly trending/persistent
(`rho_1 = +0.167`), the exact economic distinction the mechanism section
above describes -- proof that lag-1 autocorrelation carries information
about a return path's structure that the level, dispersion, streak-count
and Sharpe-ratio statistics cannot see at all, by direct construction
rather than by assertion.

**(d) Qualitative real-data support (not the primary proof, which is (c)'s
exact construction).** The same qualitative pattern is visible in real
daily data: a real trending run (several consecutive same-direction daily
closes of moderate, fairly uniform size) produces a materially higher
`rho_1` over its own trailing window than a real choppy run of similar
mean and volatility but frequent day-to-day sign reversals -- confirmed
empirically in the implementation-check spot-check below (checkpoint (b)
of the task brief), rather than asserted from the toy example alone.

## Exact rules

Computed causally at each trading day `t`'s close, using only Close prices
through `t` (no lookahead):

- **Daily log returns:** `r_t = ln(Close_t / Close_{t-1})`.
- **Lag-1 sample autocorrelation** `rho_1_t`: the Pearson correlation
  coefficient between `{r_i}` and `{r_{i-1}}` for `i` ranging over the
  trailing `ac_window` days ending at `t` (i.e. `ac_window` return pairs,
  `ac_window + 1` raw returns). Undefined (NaN) until `ac_window + 1`
  return observations exist, or when the trailing window has zero variance
  (a degenerate constant-return window, e.g. an illiquid/stale-price
  stretch) -- in either case the signal defaults to a neutral percentile of
  `0.5` (see below), the same "not enough information yet" convention as
  every prior sizing family in this loop.
- **Causal, point-in-time percentile rank** `pctile_t`: the fraction of
  the trailing `pctile_lookback` days' own `rho_1` values (excluding
  nothing forward-looking) that are `<= rho_1_t`, i.e. a **relative**
  (self-referential, per-asset, per-period) threshold rather than an
  absolute cutoff on `rho_1`'s bounded `[-1, 1]` range -- because realized
  daily-return lag-1 autocorrelation for real assets is typically
  concentrated in a much narrower band than the theoretical `[-1, 1]`
  range (single-digit-percent to low-double-digit-percent magnitudes are
  typical), a percentile-relative threshold adapts to each asset's own
  realized range instead of requiring an arbitrary universal cutoff.
  Defaults to `0.5` (neutral) until `pctile_lookback` days of `rho_1`
  history exist.
- **Sizing multiplier** (continuous, no discrete "otherwise" state --
  avoiding families 033/034's discrete-multiplier pitfall by construction):
  `m_t = clip(1 + k * (2 * pctile_t - 1), min_mult, max_mult)`. A high
  percentile (elevated, positive `rho_1` -- trending/persistent regime)
  pushes `m_t` above 1 (buy more); a low percentile (depressed, negative
  `rho_1` -- choppy/mean-reverting regime) pushes `m_t` below 1 (buy less).
  Identical continuous-multiplier functional form to family 031's
  percentile-driven sizing rule (same clip convention, same "no discrete
  bucket, no exactly-1.0 otherwise state" property), applied to a
  different underlying statistic.
- **Order generation (every trading day):** `target_buy_usd_t =
  weekly_deposit * m_t`, capped at `max_lump_multiple * weekly_deposit`,
  then at available cash (the engine's own no-leverage cap, sec 3.2). No
  sell orders are ever generated. A below-1.0-multiplier day banks the
  shortfall as cash (earning IRX), available to fund a future
  above-1.0-multiplier day -- the same reserve mechanism families
  003/005/015/016/017/030/031/035 use.

## Data inputs

Daily Close price of the asset itself only (one of the 5 core assets,
tested independently -- single-asset family). No macro or alternative
data. Sourced via `src.backtest.v3.data.load_dev()` only.

## Parameters (4 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `ac_window` | 20, 40, 60 (trading days; the task brief's suggested 20-60-day range for the autocorrelation computation window) | 40 |
| `pctile_lookback` | 252, 504 (~1, ~2 trading years -- the window over which the percentile rank is computed) | 252 |
| `k` | 0.5, 1.0, 1.5 (sensitivity of the multiplier to the percentile rank) | 1.0 |
| `min_mult` | 0.25, 0.5 (lower clip bound) | 0.5 |

Fixed constants (not grid-varied, per family 031's own precedent):
`max_mult = 2.0`, `max_lump_multiple = 3.0`.

## Grid

3 x 2 x 3 x 2 = **36 configurations** (= 36 cap, at the limit).

## Primary configuration

`ac_window=40, pctile_lookback=252, k=1.0, min_mult=0.5` (`max_mult=2.0`,
`max_lump_multiple=3.0` fixed).

## Expected sign

Positive, primarily on **Sharpe** rather than final wealth, for the same
structural reason as families 003/031: total capital committed over the
full development period is approximately unchanged (only its week-to-week
timing shifts, since every below-1.0 week banks cash that a later
above-1.0 week spends), so the Sharpe channel (buying more during
genuinely persistent/trending regimes and less during genuinely
choppy/reversal-prone regimes) is the more mechanically plausible primary
effect. The wealth effect is a secondary, exploratory hypothesis and could
go either way, consistent with Lo & MacKinlay's own finding that the
economic magnitude of short-horizon return predictability, even when
statistically significant, is modest.

## Degenerate configuration (implementation check only, not a grid arm)

`enabled=False`: bypasses the autocorrelation/percentile computation
entirely and forces `m_t = 1.0` for every day, reproducing plain DCA
exactly, bit-for-bit (same pattern as families 003/030/031's `enabled=False`
degenerate check). A second reference point (two-reference-point
degenerate-config pattern, families 014/020/033/034/035 precedent):
`k=0.0` (a real grid-shaped code path, not the bypass) also forces
`m_t = clip(1 + 0, min_mult, max_mult) = 1.0` for every day regardless of
`pctile_t`, and must independently reproduce plain DCA bit-for-bit too.

## Pre-grid checks required before running the full grid (per this
iteration's task brief)

1. `PRIMARY_CONFIG` verified to be a member of `grid_configs()` via an
   import-time `assert` (family 021/030's lesson).
2. Autocorrelation computation correctness spot-check: a known trending
   window vs. a known choppy window on real dev data, confirming the
   sign/magnitude of `rho_1` make directional sense (task checkpoint (b)).
3. The toy numeric-distinctiveness example above, recomputed
   programmatically against the module's own function at run time (task
   checkpoint (c)).
4. Confirmation that no dev-period sanity check or spot-check ever reads a
   date on or after 2020-01-01 or an unseen ticker (task checkpoint (d) --
   this family uses only `load_dev()`, whose own gate enforces this, plus
   an explicit assertion in the run script that every date referenced in
   any printed check is `< 2020-01-01`).
5. Since this family uses a **continuous** multiplier with no discrete
   "otherwise" state, family 033/034's "otherwise multiplier must be below
   1.0, not exactly 1.0" lesson does not directly apply to a discrete
   bucket -- instead, the equivalent cash-reserve-dynamics check (family
   033's underlying lesson, generalized) is run pre-grid: confirm the
   primary config's average cash balance exceeds the plain-DCA baseline's,
   and that cash is drawn down further during high-multiplier
   (elevated-`rho_1`-percentile) weeks than during low-multiplier
   (depressed-`rho_1`-percentile) weeks -- i.e. a genuine reserve builds up
   and draws down as intended (task checkpoint (e)).
