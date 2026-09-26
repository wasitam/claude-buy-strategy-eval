# Family 035 results: Parkinson range-based realized-volatility sizing

**Verdict: NEAR-MISS.** The primary configuration passes sec 4.1 narrowly
(beats DCA on final wealth AND Sharpe on **exactly 3 of 5** core assets, at
both fee levels -- the minimum passing count). It fails sec 4.2 decisively
(DSR effectively zero: `3.24e-25` at N_eff, `3.27e-27` at raw N, driven by
a slightly negative raw pooled excess-return Sharpe, `-0.0048`), and fails
two of sec 4.3's three legs: the pooled rolling-window pass rate is
51.7%/51.0% (wealth/Sharpe), short of the required >60%, and the placebo
test's real result lands at only the 78th/58th percentile of 60
circular-shifted runs (need >=95th). Sec 4.4's grid diagnostic passes
strongly (100% of the 36-config grid clears the majority-of-assets bar,
the strongest grid pass rate of any family so far), and the bootstrap's
detrended-wealth leg passes (65%) though its other three legs (raw wealth
43.3%, raw Sharpe 43.3%, detrended Sharpe 43.3%) do not. Holdout was
**not** opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family** (sec 4.1's Single-asset line), across
all 5 core assets, category **Volatility targeting** (the seed queue's own
categorization of idea #38/idea-#35-in-sequence, matching family 003's
category). Source: Parkinson, M. (1980), *The Extreme Value Method for
Estimating the Variance of the Rate of Return*, Journal of Business. Signal:
each day's Parkinson variance contribution `p_t = (ln(High_t/Low_t))^2 /
(4*ln(2))`, averaged over a trailing `park_lookback_days` window and
annualized to give `sigma_recent_t`, compared against the same statistic
over a longer `ref_lookback_days` reference window (`sigma_ref_t`). The
sizing multiplier `m_t = clip(sigma_ref_t/sigma_recent_t, min_mult,
max_mult)` scales the weekly deposit up when recent range-vol is LOW
relative to the reference, down when HIGH -- identical inverse-vol-scaling
mechanic and clip convention to family 003, but computed from a genuinely
different raw input.

## The required rigorous distinction from family 003 (full reasoning in
prereg.md)

**(a) Formula:** family 003's `sigma_recent_t` is the close-to-close
sample standard deviation of daily log returns (`std(diff(log(Close)))`,
Close-only input); this family's is `sqrt(mean((ln(High/Low))^2) /
(4*ln(2)) * 252)` (High/Low-only input, Close never used in the vol
calculation).

**(b) Why this is a different estimator, not a re-parameterization:** the
two formulas are functions of disjoint raw inputs computing the same
underlying target (return volatility) by two different statistical routes
(a close-to-close sample-variance estimator vs. an extreme-value/range
estimator). No choice of either family's grid parameters can reproduce the
other's output, because the two computations never touch the same numbers.

**(c) Concrete numeric-divergence example, verified on real dev-period
data at run time** (not hand-copied -- see
`scripts/v3/run_035_parkinson_vol_sizing.py::check_numeric_divergence_vs_003`):
SILVER (`SI=F`), 2011-09-26: prior close `$30.051`, close `$29.927`
(`-0.413%` close-to-close log return -- essentially flat), High `$30.785`
/ Low `$26.585` (a `14.67%` log high-low range, from the immediate
aftermath of the September 2011 silver selloff). Single-day, annualized
contributions:
- Close-to-close: `6.56%`.
- Parkinson: `139.84%`.
- **Ratio: 21.3x** -- confirming the two estimators are not redundant: a
  close-to-close-only signal treats this day as ordinary, while the
  Parkinson signal registers it as one of the most volatile days in the
  sample.

**(d) Data-availability caveat, checked pre-grid:** some early SP500
(pre-1962, 36.99% of its full dev history) and early GOLD/SILVER
(pre-2000-08, ~20-31%) daily bars in this vendor's feed carry `High == Low
== Close` -- a data-vintage limitation. On a trailing window made entirely
of such days, `sigma_recent_t` correctly evaluates to 0 and the strategy
defaults to `m_t = 1.0` (plain DCA), same convention as family 003's own
"not enough history yet" default. BTC and OIL have 0% degenerate-range
days in dev data; confirmed in the pre-grid sanity check below.

## Formula spot-check (task-required check (b))

Independently re-derived the Parkinson formula by hand for 3 known cases
and cross-checked against the module's own vectorized implementation:

| Case | High | Low | Hand-computed variance | Module variance | Match |
|---|---|---|---|---|---|
| SILVER 2011-09-26 (large range) | 30.7850 | 26.5850 | 0.0077600 | 0.0077600 | PASS |
| BTC 2015-11-04 (large range) | 495.562 | 380.548 | 0.0251528 | 0.0251528 | PASS |
| SP500 1928-01-03 (High==Low) | 17.76 | 17.76 | 0.0 | 0.0 | PASS |

All 3 cases match to floating-point precision, including the degenerate
`High==Low` case evaluating to exactly 0 (not NaN or an error).

## Cash-reserve dynamics check (family 033's lesson, required this
iteration)

With `min_mult=0.5 < 1.0`, the primary config's SP500 average cash balance
(`$107.66`) is materially higher than the plain-DCA baseline's (`$103.88`)
-- a genuine reserve is banked -- and average cash during high-multiplier
(low-recent-range-vol, `m_t > 1`) weeks (`$103.62`) is lower than during
low-multiplier (high-recent-range-vol, `m_t < 1`) weeks (`$117.88`) -- the
banked reserve is actually drawn down when the low-vol signal fires. Both
checks **PASS**.

## Pre-grid non-degeneracy sanity check

| Asset | Dev days | Frac. `m_t == 1.0` (default) | Frac. degenerate `High==Low` days | Std(m_t) | Non-degenerate? |
|---|---|---|---|---|---|
| SP500 | 23,109 | 36.83% | 36.99% | 0.194 | PASS |
| GOLD | 4,848 | 5.18% | 20.15% | 0.263 | PASS |
| SILVER | 4,850 | 5.18% | 31.13% | 0.282 | PASS |
| BTC | 1,932 | 12.99% | 0.00% | 0.412 | PASS |
| OIL | 4,857 | 5.19% | 0.00% | 0.219 | PASS |

SP500's higher `frac_default_1.0` tracks its higher fraction of
degenerate-range dev days (pre-1962 vendor data), consistent with caveat
(d) above and not a sign of a broken signal -- SP500 still clears the
non-degeneracy bar with `std(m_t) = 0.194` and the majority of its history
(63%) has a genuine, non-default multiplier.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Parkinson formula spot-check (3 known cases, hand vs. module) | PASS (all match) |
| Numeric-divergence check vs. close-to-close estimator (SILVER 2011-09-26) | PASS (21.3x ratio, > 5x threshold) |
| Cash-reserve check: avg cash, strategy vs. DCA baseline | PASS (strategy > DCA) |
| Cash-reserve check: avg cash, high-mult tier vs. low-mult tier | PASS (high-mult < low-mult) |
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Real `min_mult=max_mult=1.0` grid-shaped code path (not the bypass) also reproduces plain DCA bit-for-bit | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (most aggressive grid corner: `pl=20, rl=126, min=0.25, max=3.0`) | PASS |
| Capital deployed never exceeds cumulative deposits + interest, principled "never invest" ceiling bound (primary config) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (most aggressive grid corner) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000` and `t=20000`) | PASS |
| Point-in-time macro data | N/A -- price-only signal, no macro dependency |

## Primary configuration: `park_lookback_days=60, ref_lookback_days=252, min_mult=0.5, max_mult=2.0`

(Identical numeric values to family 003's own primary config -- deliberate,
to isolate the estimator swap as the only difference; see prereg.md.)

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.27867 | 85.27722 | 0.153098 | 0.153097 | YES (razor-thin) |
| GOLD | 2.23143 | 2.23123 | 0.505001 | 0.504917 | YES |
| SILVER | 1.68695 | 1.68666 | 0.319737 | 0.319677 | YES |
| BTC | 9.85211 | 9.85568 | 1.067200 | 1.067309 | NO (both lose) |
| OIL | 1.18004 | 1.17986 | 0.227776 | 0.227824 | NO (wealth wins, Sharpe loses by a hair) |

**Sec 4.1: PASS** -- 3/5 core assets (SP500, GOLD, SILVER) at both 0.1%
and 0.25% fees, exactly the minimum passing count. Every passing margin is
extremely small in absolute terms (SP500 in particular passes by a hair on
both metrics) -- the strategy is not decisively beating DCA on any asset.

### Grid diagnostic (sec 4.4)

**36 of 36 configurations (100%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees -- need >=2/3 (24/36), the
strongest grid pass rate of any family tested in this loop so far. Every
config shows the identical per-asset pattern seen in the primary config
(4/5 wealth, 3/5 combined wealth-and-Sharpe, driven by BTC and OIL failing
the combined bar) across the full lookback-window x clip-bound grid --
CSCV PBO of 0.029 (the lowest, i.e. best, of any family so far) confirms
this is not a lucky single corner of the grid but a robust pattern across
essentially the whole declared grid.

### Sec 4.2: Deflated Sharpe Ratio -- FAIL

- `N_eff = 105` (raw `N = 1069`, seed 196 + new 873 across all families
  tested through family 035).
- DSR (N_eff-based): **3.24e-25** (need >= 0.95).
- DSR (raw-N, conservative reference): **3.27e-27**.
- Both are driven by the primary config's pooled excess-return series
  having a slightly *negative* raw weekly Sharpe (`-0.0048`, annualized
  `-0.034`) -- the strategy's small final-wealth edge on SP500/GOLD/SILVER
  does not translate into a positive risk-adjusted excess-return series
  once pooled across all 5 assets (BTC and OIL's losses pull the pooled
  series negative on a risk-adjusted basis), so no amount of N_eff
  adjustment can rescue a DSR built on a negative underlying Sharpe.

### Sec 4.3: Robustness -- FAIL (2 of 3 legs)

- **Rolling windows:** pooled across all 9 window/asset combinations
  (3439 total windows), **51.7%** beat DCA on wealth and **51.0%** on
  Sharpe -- need >60%. By asset: GOLD (73-77%) and OIL (67-73%) clear the
  bar comfortably; SILVER is borderline (58-59%); SP500 (40-48%) and BTC
  (29-36%) fail decisively, dragging the pooled rate below the 60% bar.
- **Block bootstrap** (SP500, n=60 sims): raw beats DCA on 43.3%/43.3%
  (wealth/Sharpe, fail -- need a majority); detrended beats DCA on
  65.0%/43.3% (wealth passes, Sharpe still fails).
- **Placebo** (SP500, 60 circular shifts of the primary config's own
  `m_t` signal): the real result lands at the **78th percentile** (wealth)
  and **58th percentile** (Sharpe) of the shifted-signal distribution --
  need >=95th. The specific temporal alignment of the Parkinson signal is
  not doing enough work relative to a randomly-shifted version of the same
  multiplier sequence.

## Assessment summary

| Check | Result | Pass? |
|---|---|---|
| Sec 4.1 (beats DCA >=3/5, both fees) | 3/5 at both fees | PASS |
| Sec 4.2 (DSR >= 0.95) | 3.24e-25 (N_eff), 3.27e-27 (raw N) | FAIL |
| Sec 4.3 rolling windows (>60% majority) | 51.7% wealth / 51.0% Sharpe | FAIL |
| Sec 4.3 bootstrap (majority beats DCA) | raw 43.3%/43.3%; detrended 65.0%/43.3% | FAIL (3 of 4 legs) |
| Sec 4.3 placebo (>=95th percentile) | 78th (wealth) / 58th (Sharpe) percentile | FAIL |
| Sec 4.4 (>=2/3 of grid beats DCA majority) | 36/36 (100%) | PASS |

**Verdict: NEAR-MISS.** Logged, not promoted to finalist. Holdout not
opened, per sec 5.4 (holdout is reserved for finalists only).

## Judgment calls

1. **Grid mirrors family 003's exactly** (same lookback windows, same clip
   bounds), a deliberate design choice per prereg.md's "Parameters"
   section, so that any future comparison between the two families
   isolates the vol-estimator swap as the only difference. This meant no
   additional grid latitude was spent exploring parameter values unique to
   the Parkinson estimator (e.g. shorter lookback windows that might
   better exploit its lower estimation-noise property) -- a reasonable
   trade-off given the family's primary purpose this iteration was the
   rigorous distinction from family 003, not maximizing this family's own
   chance of passing.
2. **"Numeric divergence" threshold set at >5x** in the implementation
   check (`divergence_confirmed`) -- an arbitrary but generous bar given
   the actual measured divergence was ~21x; any reasonable threshold well
   below that would have passed.
3. Both family 003 (REJECTED) and this family (NEAR-MISS) show the same
   qualitative pattern: a genuine, small, narrowly-passing sec 4.1 result
   that does not survive sec 4.2's trial-count adjustment or sec 4.3's
   placebo/bootstrap legs. This is consistent with the loop's own
   observation (family 034's results.md and others) that this style of
   narrow 3/5 pass, on this development sample, tends not to be robust --
   read as a mild update against pursuing further minor variants on
   inverse-volatility per-asset sizing (family 003's category) without a
   materially different economic mechanism, though the loop makes no
   binding rule change from this observation alone.
