# Family 035: Parkinson range-based realized-volatility sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Parkinson, M. (1980), *The Extreme Value Method for Estimating the Variance
of the Rate of Return*, Journal of Business, 53(1), 61-65. Parkinson showed
that a day's HIGH-LOW trading range carries information about that day's
realized volatility beyond what the close-to-close return alone captures,
and that an estimator built from the range is materially more statistically
efficient (lower variance for the same number of observations) than the
standard close-to-close sample-variance estimator, under a driftless
geometric Brownian motion assumption -- roughly 5x more efficient in the
idealized continuous-sampling case (i.e. ~5 close-only days' worth of
information from 1 range-based day). Seed queue item #35
(research-loop-plan-v3.md's `state/research_queue.md`), category
**Volatility targeting** as listed there. Also draws on the same underlying
economic mechanism cited in family 003's prereg.md (Moreira & Muir 2017;
Harvey et al. 2018): scaling a fixed deposit stream inversely to realized
volatility avoids committing a disproportionate share of capital during the
highest-variance regimes, because variance is persistent (clusters) while
returns are not.

## Mechanism ("why would this work, and who is on the other side?")

Same economic mechanism as family 003 (volatility clustering makes today's
realized vol informative about tomorrow's; a fixed-dollar DCA buyer
over-invests, in dollar-weighted terms, during exactly the highest-variance
weeks, where crash and drawdown risk concentrate). What differs here is
*how* "today's realized vol" is measured. Family 003 measures it from the
close-to-close return series alone -- a single number per day (the price at
the close), discarding everything that happened between the open and the
close. This family measures it from the day's full HIGH-LOW trading range
instead -- the extreme values the price actually touched intraday, which is
strictly more information about how volatile that day's price path was than
the single closing print. Parkinson (1980) formalizes this: for a
continuous driftless diffusion, the expected squared log-range is a known
multiple of the instantaneous variance, so `(1/(4 ln 2)) * E[(ln(H/L))^2]`
is an unbiased estimator of the daily variance, and because it uses the
(theoretically continuously-observed) extremes of the whole day's path
rather than one point sampled at the close, it converges to the true
variance with a smaller sample-to-sample variance than the close-to-close
estimator for the same number of days. The economic story for "who is on
the other side" is identical to family 003's: constant-dollar DCA buyers
and other constant-mix investors who do not condition their buy size on
volatility at all, of either kind. The risk paid is the same as family
003's (a low realized range does not guarantee a calm subsequent period),
plus a distinct risk specific to the estimator: a day that gaps and reverses
sharply intraday but closes near the prior close (a large range, a small
close-to-close move) will register as HIGH volatility under this
estimator even though a close-to-close-only measure would call that same
day calm -- see the concrete numeric example below. This is a feature for
the estimator's stated purpose (it is capturing real intraday variance the
close-only series misses) but means this family's sizing decisions will
sometimes diverge from family 003's on specific days, which is exactly the
point of testing it as a separate family.

## Category

**Volatility targeting** (research-loop-plan-v3.md sec 4.5). Same category
as family 003 -- see sec 4.5's requirement that the two eventual winners
come from *different* categories; a fully-fledged winner-pair decision is
irrelevant if this family is rejected or near-miss, but is noted here for
completeness since both are candidates in the same category.

## Why this is not a re-test of family 003 (or any closed family), and the
required rigorous distinction

Family 003 is not a closed family (sec 7.2's list is v1/v2/v2.1 work only),
but it is the closest prior family by economic motivation and by sizing
mechanic (inverse-volatility multiplier on the weekly deposit, min/max
clipped, no leverage), so per this iteration's explicit brief the
distinction must be made rigorously, not just asserted.

**(a) The mathematical formula difference.**

- **Family 003 (close-to-close):** `sigma_recent_t = std(diff(log(Close)),
  ddof=1, over trailing vol_lookback_days) * sqrt(252)` -- the classic
  close-to-close sample-standard-deviation-of-log-returns estimator. Its
  only raw input per day is that day's closing price; the day's intraday
  high and low never enter the calculation.
- **This family (Parkinson, 1980):** for each day `i`, define
  `r_i = ln(High_i / Low_i)`. The Parkinson daily variance estimate over a
  trailing window of `N` days is
  `sigma^2_daily = (1 / (4 * ln(2) * N)) * sum_{i in window}(r_i^2)`,
  annualized as `sigma_annual = sqrt(sigma^2_daily * 252)`. Its raw input
  per day is that day's High and Low; the closing price never enters the
  calculation at all (only the two intraday extremes do).

**(b) Why this is a different ESTIMATOR, not "family 003 with different
parameters."** The two formulas are functions of disjoint raw inputs
(High/Low only, vs. Close only) computing the same underlying target
quantity (daily return volatility) by two different statistical routes: one
treats each day as a single point sample (the close-to-close return) and
takes a sample variance across `N` such points; the other treats each day
as an extreme-value observation of the whole day's continuous price path
and averages a per-day range-based variance estimate across `N` days. No
choice of `vol_lookback_days`/`ref_lookback_days`/`min_mult`/`max_mult` in
family 003's grid can reproduce this family's output, and no choice of this
family's own grid parameters can reproduce family 003's output, because the
two computations never touch the same numbers (family 003 never reads
High/Low; this family never reads Close in the vol calculation). This
mirrors the literature's own framing (Parkinson 1980; the later
Garman-Klass, Rogers-Satchell and Yang-Zhang extensions) of range-based
estimators as a distinct *family* of realized-volatility estimators
alongside, not a variant of, close-to-close sample variance.

**(c) Concrete numeric-divergence example on real dev-period data.** SILVER
(`SI=F`), 2011-09-26: prior close `$30.051`, that day's close `$29.927`
(essentially flat, a `-0.413%` close-to-close log return), but High
`$30.785` / Low `$26.585` -- a huge `14.67%` log high-low range (silver
plunged intraday and rebounded to close near the prior day's level, in the
immediate aftermath of the September 2011 silver/gold selloff). Computing
each estimator's contribution from THIS SINGLE DAY's own inputs, annualized
the same way (`x * sqrt(252)`, single-day variance treated as the annualized
rate for comparability, not as a smoothed window estimate):
- Close-to-close: `(ln(29.927/30.051))^2 = 1.708e-5` daily variance ->
  annualized vol `= sqrt(1.708e-5 * 252) = 6.56%`.
- Parkinson: `(ln(30.785/26.585))^2 / (4*ln(2)) = 0.02151 / 2.7726 =
  7.759e-3` daily variance -> annualized vol `= sqrt(7.759e-3 * 252) =
  139.8%`.

The Parkinson estimate is **~21x** the close-to-close estimate for this
single day -- exactly the divergence pattern the task brief anticipates (a
volatile intraday session with a big high-low range but a close near the
prior close shows high Parkinson vol, low close-to-close vol), and proof
the two estimators are not redundant restatements of each other: a
strategy sized purely off family 003's close-to-close signal would treat
this day as ordinary/calm, while this family's signal registers it as one
of the most volatile days in the sample. (Re-run in
`scripts/v3/run_035_parkinson_vol_sizing.py::check_numeric_divergence_vs_003`
against the live data at run time, not hand-copied, so a data refresh
cannot silently invalidate this section.)

**(d) Data-availability caveat, checked pre-grid.** Some early SP500 daily
bars (pre-1962, ~37% of SP500's full dev history) and some early
GOLD/SILVER/OIL bars (pre-2000) in this vendor's feed carry `High == Low
== Close` (no genuine intraday range was recorded/available), which is a
data-vintage limitation, not a strategy bug. On any trailing window
entirely composed of such degenerate-range days, the Parkinson estimator
correctly evaluates to exactly 0, and the strategy defaults the sizing
multiplier to `1.0` (plain DCA) for that day rather than dividing by zero
-- the same "not enough information yet, default to DCA" convention family
003 uses when its own rolling windows are not yet full. BTC (`2014-09+`)
and all post-2000 SILVER/GOLD/OIL data have genuine High/Low every day
(confirmed in the pre-grid non-degeneracy check below), so this caveat is
material only for a portion of SP500's very long history.

## Exact rules

Computed causally at each trading day `t`'s close, using only OHLC data
through `t` (no lookahead):

- **Parkinson daily-variance series:** `p_t = (ln(High_t / Low_t))^2 / (4 *
  ln(2))` for every trading day `t` (using that day's own High/Low only).
- **Recent range-vol** `sigma_recent_t`: `sqrt(mean(p over trailing
  park_lookback_days) * 252)`.
- **Reference (long-run) range-vol** `sigma_ref_t`: the same calculation
  over the trailing `ref_lookback_days` (a longer window -- the asset's own
  adaptive baseline, identical convention to family 003).
- While fewer than `ref_lookback_days` observations exist, OR
  `sigma_recent_t` evaluates to exactly 0 (a window made entirely of
  degenerate `High==Low` days, see caveat (d) above), the multiplier
  defaults to 1.0 (plain DCA).
- **Sizing multiplier:** `m_t = clip(sigma_ref_t / sigma_recent_t, min_mult,
  max_mult)` -- LOW recent range-vol relative to the reference gives `m_t >
  1` (buy more); HIGH recent range-vol gives `m_t < 1` (buy less). Same
  inverse-vol-scaling direction and clipping convention as family 003
  (Moreira & Muir's headline direction; the naive opposite direction is not
  part of the grid).
- **Order generation (every trading day):** `target_buy_usd_t =
  weekly_deposit * m_t`. Submitted order is `buy_usd = min(cash,
  target_buy_usd_t)` (engine's cash cap, sec 3.2, enforces no leverage/no
  borrowing -- identical mechanism to family 003). No sell orders are ever
  generated.

## Data inputs

Daily OHLC (High, Low, Close) of the asset itself only (one of the 5 core
assets, tested independently -- single-asset family). No macro or
alternative data. Sourced via `src.backtest.v3.data.load_dev()` only.

## Parameters (4 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `park_lookback_days` | 20, 40, 60 (~1, ~2, ~3 trading months) | 60 |
| `ref_lookback_days` | 126, 252 (~6, ~12 trading months) | 252 |
| `min_mult` | 0.25, 0.5 | 0.5 |
| `max_mult` | 1.5, 2.0, 3.0 | 2.0 |

Deliberately mirrors family 003's exact parameter grid (same lookback
windows, same clip bounds) so that any eventual comparison between the two
families isolates the estimator swap (range-based vs. close-to-close) as
the only difference, not a difference in tuning latitude.

## Grid

3 x 2 x 2 x 3 = **36 configurations** (= 36 cap, at the limit).

## Primary configuration

`park_lookback_days=60, ref_lookback_days=252, min_mult=0.5, max_mult=2.0`
-- identical numeric values to family 003's own primary configuration, for
the same reason as the grid choice above (isolate the estimator swap).

## Expected sign

Positive, primarily on **Sharpe**, for the same reason given in family
003's prereg.md: total capital committed over time is approximately
unchanged (only its timing shifts), so the Sharpe channel (avoiding the
highest-range-volatility weeks) is the more mechanically guaranteed
effect, while the wealth effect is smaller and could go either way. Since
the Parkinson estimator is a more statistically efficient (lower-variance)
estimator of the same underlying quantity than the close-to-close
estimator, this family's signal is expected to react somewhat faster and
with less estimation noise to genuine volatility regime shifts than family
003's, particularly on assets/periods where a real trading range is
recorded, which could translate into modestly cleaner (less noisy) timing
of the reserve build-up/draw-down cycle -- but this is a secondary,
exploratory hypothesis, not a criterion that gates the family's verdict.

## Degenerate configuration (implementation check only, not a grid arm)

`enabled=False`: bypasses the Parkinson calculation entirely and forces
`m_t = 1.0` for every day, reproducing plain DCA exactly, bit-for-bit (same
pattern as family 003's `enabled=False` degenerate check).
