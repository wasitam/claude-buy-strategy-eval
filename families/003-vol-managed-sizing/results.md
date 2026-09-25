# Family 003 results: volatility-managed sizing (Moreira & Muir 2017)

**Verdict: REJECTED** (fails sec 4.1; holdout not opened per sec 8 step 8,
"finalists only" -- this family never reached finalist status).

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`, m_t forced to 1.0) reproduces plain DCA exactly (bit-for-bit on units and cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary vol-managed config) | PASS |
| No-lookahead: perturbing all data after day t leaves every order on/before t unchanged | PASS |
| Point-in-time macro data | N/A (price-only strategy; vacuously satisfied) |

## Primary configuration: `vol_lookback_days=60, ref_lookback_days=252, min_mult=0.5, max_mult=2.0`

### sec 4.1 -- beats DCA on wealth AND Sharpe, >= 3 of 5 core assets, both fee levels

At 0.1% fees:

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both) |
|---|---|---|---|---|---|
| SP500 | 85.275 | 85.277 | 0.15310 | 0.15310 | no |
| GOLD | 2.2313 | 2.2312 | 0.50494 | 0.50492 | **YES** |
| SILVER | 1.6869 | 1.6867 | 0.31970 | 0.31968 | **YES** |
| BTC | 9.8524 | 9.8557 | 1.06721 | 1.06731 | no |
| OIL | 1.1800 | 1.1799 | 0.22773 | 0.22782 | no |

At 0.25% fees the pattern is identical: **2 of 5** (GOLD, SILVER). **sec 4.1:
FAIL** (need >= 3/5 at both fee levels).

The magnitude of the effect is tiny in every direction (differences in the
4th-5th significant digit of wealth/invested and Sharpe on every asset).
This is the expected signature of the mechanism as designed: the average
sizing multiplier over the full development history is close to 1.0 (mean
~1.10, computed over SP500's 92-year history with the primary bounds), since
the reserve-and-drawdown mechanism (sec on "Exact rules" in prereg.md) is
symmetric by construction and total capital committed stays close to $500/
week on average -- what moves is *when* it's committed, and on 92 years of
SP500 data at weekly resolution that timing shift nets out to essentially
nothing on final wealth or Sharpe, in either direction, on 3 of 5 assets.

### sec 4.2 -- Deflated Sharpe Ratio >= 0.95

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  **-0.01086/week** (annualized ~-0.078) -- slightly negative on average,
  consistent with the near-null sec 4.1 result above.
- `N` (raw trial count at this assessment): **262** (196 seeded + 30 from
  families 001/002 + 36 new from this family's grid).
- `N_eff` (average-linkage clustering, distance sqrt(0.5(1-rho)), rho>=0.5
  threshold): **33** clusters.
- **DSR (N_eff-based, used for the decision): 1.05e-30** -- essentially zero.
  The pooled excess series is also extremely fat-tailed and negatively
  skewed (skew -14.9, kurtosis 846 -- a handful of large negative
  excess-return weeks, likely fee-driven whipsaw around the multiplier
  clip boundaries, dominate the distribution's shape even though the mean
  is near zero).
- DSR (raw-N, conservative reference): 2.07e-52.

**sec 4.2: FAIL**, overwhelmingly so.

### sec 4.4 -- robust across parameters (grid diagnostic)

**12 of 36 configurations (33.3%) reach the majority-of-assets bar** (>=3/5
core assets beating DCA on both wealth and Sharpe at 0.1% fees) -- the
`vol_lookback_days in {20,40}` x `ref_lookback_days=126` arms cleanly pass
(4/5 assets each), while every `ref_lookback_days=252` arm and every
`vol_lookback_days=60` arm caps out at 3/5 or fewer once the fee/Sharpe
combination is checked, so 24 of the 36 configs are majority-fail. **sec
4.4: FAIL** (need >= 2/3 = 24/36; only 12/36 pass).

CSCV probability of backtest overfitting (diagnostic, SP500 grid, 8 splits,
70 combinations): **PBO = 0.286**. Lower than family 002's 0.443 but higher
than family 001's 0.0 -- consistent with a grid where the `ref_lookback_days`
parameter is doing real, somewhat overfit-prone differentiating work (shorter
reference windows systematically pass more often) rather than the grid being
either uniformly mediocre (001) or a near coin-flip (002).

### sec 4.3 -- robust across time and resamples

**Not run to completion.** Per the same judgment call and precedent as
family 001 (`state/bugfix_log.md`, `families/001-trend-exit/results.md`
judgment call #3): sec 4.1 (2/5 assets, need >=3/5), sec 4.2 (DSR ~1e-30 vs.
0.95 bar), and sec 4.4 (12/36 = 33% of the grid, need >=67%) had already
independently and conclusively failed before the rolling-window/bootstrap/
placebo suite (which reruns the full single-asset engine hundreds of times
across 5 assets and 2 window lengths) completed. Running it to completion
would not change the verdict -- a family failing sec 4.1 alone cannot become
a finalist regardless of sec 4.3's outcome (sec 4 requires every check to
pass). The robustness script (`scripts/v3/robustness_003_vol_managed_sizing.py`)
is implemented and ready to run to completion if a future iteration needs
its full numbers (e.g. to compare robustness profiles across rejected
families), but was not executed to completion in this iteration.

### sec 4.5 -- distinctness

Not applicable; this family did not become a finalist.

## Verdict

**REJECTED.** The primary configuration fails sec 4.1 (only 2/5 assets beat
DCA on both wealth and Sharpe, at both fee levels; need >= 3/5), sec 4.2 (DSR
1.05e-30, far below 0.95), and sec 4.4 (only 12/36 = 33.3% of the grid clears
the majority-of-assets bar, need >= 2/3 = 24/36). Per sec 8 step 8, holdout
data was **not** opened -- holdout access is reserved for finalists only,
and this family never reached finalist status.

## Why the mechanism didn't clear the bar (interpretation, not part of the formal verdict)

The strategy is constructed to be capital-neutral on average (the reserve
mechanism means total dollars committed over the full sample stays close to
plain DCA's $500/week, only the timing shifts), so any edge over DCA has to
come entirely from a genuine, exploitable correlation between "recent
realized vol below its own longer-run baseline" and "subsequently favorable
near-term price action" -- exactly the weaker, less mechanically-guaranteed
channel flagged as the wealth-effect risk in prereg.md's "Expected sign"
section. On 3 of 5 core assets (SP500, BTC, OIL) that correlation, at these
parameter settings and over these development samples, nets out to
essentially zero to slightly negative; only GOLD and SILVER show a (tiny,
economically negligible) positive edge. This is broadly consistent with the
literature's own scope conditions: Moreira & Muir's headline Sharpe
improvement is documented for diversified equity-factor portfolios rebalanced
more frequently than weekly, not single-asset weekly-DCA deposit timing,
and the fat-tailed, negatively-skewed excess-return series (sec 4.2) suggests
whatever edge exists is being partly offset by occasional sharp misses
around the multiplier's clip boundaries.

## Judgment calls made in this iteration

1. **Reference vol window instead of a fixed absolute target-vol level.**
   Declared in `prereg.md` before any backtest: rather than a single
   fixed target-vol number (which would be miscalibrated across assets as
   different as gold, ~15-20% annualized, and BTC, ~60-80%+), the "target"
   is each asset's own trailing `ref_lookback_days` realized vol, making the
   comparison adaptive per asset. This keeps the parameter count at 4 (one
   under the 5-parameter ceiling) while covering the mechanism's inverse-
   variance-scaling core idea.
2. **Reduced/incomplete sec 4.3 robustness run**, following the family 001
   precedent (`state/bugfix_log.md`, `families/001-trend-exit/results.md`
   judgment call #3): the rolling-window/bootstrap/placebo suite was
   started at the plan's already-reduced n_sims=120 (single-asset
   precedent) but was not run to completion, since sec 4.1, 4.2 and 4.4 had
   already independently and conclusively rejected the family. This mirrors
   family 001's own documented stopping point.
3. **Grid sized at exactly 36 configurations (the hard cap).** Declared in
   `prereg.md` before any backtest: 4 params x (3x2x2x3) = 36 is at, not
   under, the plan's sec 3.4 ceiling. This was a deliberate choice to give
   the sec 4.4 grid-majority diagnostic more resolution across all four
   parameters (vol_lookback_days, ref_lookback_days, min_mult, max_mult)
   rather than dropping a parameter's grid resolution to leave headroom.
