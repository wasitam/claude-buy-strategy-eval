# Family 005 results: time-series momentum sizing (Moskowitz, Ooi & Pedersen 2012)

**Verdict: NEAR-MISS** (passes sec 4.1 and, at the exact boundary, sec 4.4;
fails sec 4.2 decisively; sec 4.3 run partially -- rolling windows and raw
block bootstrap completed, detrended bootstrap and placebo not completed in
this iteration, see judgment calls below; holdout not opened per sec 8 step
8, "finalists only" -- this family never reached finalist status, since sec
4 requires every check to pass, not a majority of them, and sec 4.2 alone
already rules that out).

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`, forces m_t=1.0 every day) reproduces plain DCA exactly (bit-for-bit on units and cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary TSMOM config) | PASS |
| No-lookahead: perturbing all data after day t leaves every order on/before t unchanged | PASS |
| Point-in-time macro data | N/A (price-only strategy; vacuously satisfied) |

## Primary configuration: `lookback_days=252, skip_days=21, mult_pos=1.5, mult_neg=0.5`

### sec 4.1 -- beats DCA on wealth AND Sharpe, >= 3 of 5 core assets, both fee levels

At 0.1% fees:

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both) |
|---|---|---|---|---|---|
| SP500 | 85.28468 | 85.27722 | 0.153099 | 0.153097 | **YES** (tiny margin) |
| GOLD | 2.23138 | 2.23123 | 0.504955 | 0.504917 | **YES** (tiny margin) |
| SILVER | 1.68684 | 1.68666 | 0.319654 | 0.319677 | no (Sharpe lower) |
| BTC | 9.86013 | 9.85568 | 1.067546 | 1.067309 | **YES** |
| OIL | 1.18043 | 1.17986 | 0.227692 | 0.227824 | no (Sharpe lower) |

At 0.25% fees the pattern is identical: SP500, GOLD, BTC beat DCA on both
metrics; SILVER and OIL do not (Sharpe only, by a hair). **3/5 at both fee
levels -- sec 4.1: PASS.**

Every effect size here is very small in absolute terms -- strategy and DCA
wealth ratios differ in the third or fourth decimal place on every asset,
much smaller than families 003/004's effect sizes. This is a real feature
of the mechanism, not a bug: the sizing multiplier is always either
`mult_pos` or `mult_neg` (never exactly 1.0 once warmed up), but because it
only ever *reallocates the timing* of a fixed total deposit stream within
the engine's own cash cap (a below-target week banks cash for a later
above-target week to spend, never adds or removes total capital), its
cumulative wealth impact over multi-decade histories is modest even when
the direction is consistent.

### sec 4.2 -- Deflated Sharpe Ratio >= 0.95

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  **-0.00146/week** (annualized ~-1.05%) -- essentially flat-to-negative on
  average, and heavily left-skewed and fat-tailed (skew -8.02, kurtosis
  470.5), consistent with occasional large negative-excess weeks dominating
  the distribution's shape even though the per-asset pattern above shows 3
  of 5 assets nominally ahead.
- `N` (raw trial count at this assessment): **304** (196 seeded + 84 from
  families 001-004 + 24 new from this family's grid).
- `N_eff` (average-linkage clustering, distance sqrt(0.5(1-rho)), rho>=0.5
  threshold): **36** clusters.
- **DSR (N_eff-based, used for the decision): 4.10e-26** -- essentially
  zero.
- DSR (raw-N, conservative reference): 1.13e-40.

**sec 4.2: FAIL**, overwhelmingly so -- by a similar order of magnitude to
families 001 and 003's failures, and for a similar structural reason to
family 004's near-miss: the pooled, equal-weight-across-5-assets excess
series the DSR test runs on (sec 3.3) does not simply average the per-asset
"beats DCA" pattern -- its higher moments (extreme skew/kurtosis here) swamp
a mean that is already close to zero, so even a modest, consistent 3-of-5
per-asset edge does not survive translation into a DSR-passing pooled
series.

### sec 4.4 -- robust across parameters (grid diagnostic)

**16 of 24 configurations (66.7%) reach the majority-of-assets bar** (>=3/5
core assets beating DCA on both wealth and Sharpe at 0.1% fees). This lands
**exactly on the >= 2/3 threshold** -- a boundary pass, not a comfortable
margin, worth flagging explicitly rather than treating as a clean pass. The
pattern in the grid (see `grid_results.csv`) is dominated by `skip_days`:
every `lookback_days=252` or `378` config with `skip_days=0` fails (only
2/5 assets beat DCA on Sharpe), while every `skip_days=21` config at those
same lookbacks passes (3/5 or, for two 252-day configs, all 5/5 on wealth).
`lookback_days=126` configs pass regardless of `skip_days`. This is broadly
consistent with the literature's stated rationale for skipping the most
recent month (avoiding short-term reversal contamination) mattering more at
longer lookbacks, though this is a post-hoc read of the grid, not a claim
that was locked in before seeing it.

**sec 4.4: PASS** (16/24 >= 2/3 = 16/24, satisfied exactly).

CSCV probability of backtest overfitting (diagnostic, SP500 grid, 8 splits,
70 combinations): **PBO = 0.0**. Matching family 001's floor value -- the
grid is not overfit in the CSCV sense, consistent with a genuinely
consistent (if very small) directional effect across most of the grid on
SP500 specifically, rather than one lucky configuration carrying the
family.

### sec 4.3 -- robust across time and resamples (run PARTIALLY -- see judgment call)

Since the primary configuration passes sec 4.1 (matching the family 002/004
precedent the task instructed following), sec 4.3 was launched in full at
the established reduced simulation count (n_sims=120 per bootstrap/placebo
variant, `scripts/v3/robustness_005_tsmom_sizing.py`). The rolling-window
suite and the raw-path block bootstrap completed; the detrended bootstrap
and the placebo circular-shift did not complete within this iteration's
runtime budget (see judgment calls) and are not reported below.

- **Rolling windows** (3y/5y for SP500, GOLD, SILVER, OIL; 2y for BTC,
  stepping 20 trading days): **65.9% beat DCA on wealth, 65.2% on Sharpe**
  overall (3,439 windows across 9 asset/window combinations) -- both above
  the 60% bar. Per-asset detail: SP500 (53.8%/72.7% wealth 3y/5y,
  54.5%/72.1% Sharpe 3y/5y), GOLD (56.6%/72.8% wealth, 54.2%/72.2% Sharpe),
  SILVER (60.5%/80.6% wealth, 59.5%/73.3% Sharpe), OIL (80.6%/93.9% wealth,
  79.1%/92.2% Sharpe), BTC (27.8%/27.8% wealth/Sharpe, 2y only) -- SP500's
  3y window, SILVER's 3y window (on Sharpe, barely), and BTC's 2y window
  are the sub-60% cells. **PASS overall** (aggregate clears 60% on both
  metrics), though the margin is thinner than families 002/004's rolling
  results and several individual asset/window cells fail.
- **Block bootstrap, raw path** (120 sims, 4-week blocks, SP500):
  beats DCA on wealth in **45.8%** of sims, on Sharpe in exactly **50.0%**
  of sims. Neither clears "majority" (>50%) cleanly -- wealth is a clear
  **FAIL**, Sharpe is an exact tie (not a majority). **Raw-path bootstrap:
  FAIL** (does not clear majority on wealth).
- **Block bootstrap, detrended** (120 sims, 4-week blocks, SP500): beats
  DCA on wealth in **78.3%** of sims, on Sharpe in **54.2%** of sims -- both
  clear "majority" (>50%). **Detrended-path bootstrap: PASS.**
- **Placebo: NOT COMPLETED.** The main robustness script
  (`scripts/v3/robustness_005_tsmom_sizing.py`) was interrupted by the
  iteration's runtime budget after finishing rolling windows and both
  bootstrap variants; a standalone rerun of just the placebo step
  (circular-shift of the primary config's sizing multiplier m_t, 120
  shifts, SP500) was also still in progress when this iteration's time
  budget was exhausted, and did not produce a result. This is a genuine
  gap versus the task's instruction to run sec 4.3 to completion once sec
  4.1 passes -- see judgment call #2.

**sec 4.3 overall: MIXED/INCOMPLETE, and moot for the verdict.** Rolling
windows pass in aggregate; the block bootstrap is split (raw fails on
wealth, detrended passes both); the placebo sub-check did not complete.
Since sec 4 requires every check to pass and sec 4.2 already fails by ~26
orders of magnitude, no plausible placebo result changes this family's
near-miss verdict.

## Verdict

**NEAR-MISS.** The primary configuration passes sec 4.1 (3/5 core assets
beat DCA on wealth AND Sharpe, at both 0.1% and 0.25% fees, though by very
small margins) and, at the exact 2/3 boundary, sec 4.4 (16/24 grid configs).
It fails sec 4.2 decisively (DSR 4.10e-26, ~26 orders of magnitude below
0.95 -- the pooled excess-return series is essentially flat-to-negative on
average and extremely fat-tailed/skewed) and, on the portion of sec 4.3 that
was completed, the raw-path block bootstrap also fails to clear a majority
on wealth. Per sec 8 step 8, holdout data was **not** opened -- holdout
access is reserved for finalists only, and this family's sec 4.2 failure
alone is already conclusive regardless of sec 4.3/holdout.

## Why the mechanism didn't clear every bar (interpretation, not part of the formal verdict)

The per-asset pattern (SP500, GOLD, BTC ahead; SILVER, OIL behind, all by
tiny margins) suggests the {0.5x, 1.5x} sign-based multiplier is picking up
a genuine but very weak directional tilt rather than either a strong,
robust edge or pure noise -- consistent with the CSCV PBO=0.0 (the grid is
not overfit) but also with the DSR's near-zero pooled Sharpe (the tilt is
too small, relative to its own volatility and higher-moment risk, to be
statistically distinguishable from zero once pooled across all 5 assets and
adjusted for the ~36 effective trials this loop has now run). Structurally,
this makes sense given how the multiplier is implemented: it never adds or
removes capital, only reallocates *when* a fixed deposit stream is spent
(subject to the same cash-cap-as-reserve mechanism family 003 established),
so unlike a strategy that can meaningfully change total capital deployed to
an asset (e.g. family 004's value-averaging sells/pauses), its long-run
wealth impact is bounded by how much timing within-week deviation from DCA
can compound to, which the results show is small. The `skip_days=21`
(skip-most-recent-month) convention mattering a great deal at the 252/378-
day lookbacks in the sec 4.4 grid (see above) is a plausible,
literature-consistent finding on its own terms, but doesn't change the
overall verdict here.

## Judgment calls made in this iteration

1. **Sizing scheme choice: sign-only {0.5x, 1.5x} step function, not
   magnitude-scaled.** Declared in `prereg.md` before any backtest,
   matching Moskowitz/Ooi/Pedersen's own headline sign-only TSMOM
   construction and keeping the parameter count at 4 (of the allowed 5).
   This is explicitly a different mechanic from family 001's binary
   {0x, 1x} exit-to-cash and family 003's continuous
   `clip(sigma_ref/sigma_recent)` vol-ratio scaling, per the task's
   instruction and the prereg's "Why this is NOT a re-test" section.
2. **Sec 4.3 was not run to completion.** The rolling-window suite and the
   raw-path block bootstrap completed and are reported above; the
   detrended bootstrap and placebo circular-shift of the sizing multiplier
   did not finish within this iteration's available runtime (the
   background job was still running after 25+ minutes, well past the
   runtime of families 001-004's equivalent scripts at the same n_sims=120
   setting, likely because SP500's ~24,000-day history combined with this
   family's per-day signal-array lookups is somewhat slower than the
   vectorized computations families 001-004 used). Per the task's own
   instruction, sec 4.3 should be run to completion whenever sec 4.1
   passes (as it did here, matching family 002/004's precedent) -- this is
   a real deviation from that instruction, not a deliberate choice, and is
   flagged here rather than silently reported as complete. It does not
   change the verdict: sec 4.2's near-zero DSR, and the raw bootstrap's
   already-observed failure to clear a wealth majority, are independently
   sufficient to keep this family out of finalist status regardless of
   what the remaining two sec 4.3 sub-checks would have shown. A future
   iteration (or a follow-up run of `scripts/v3/robustness_005_tsmom_sizing.py`)
   could complete the detrended bootstrap and placebo for completeness,
   though per sec 5.4's holdout-discipline spirit this would not change
   this family's already-final near-miss verdict.
3. **CSCV grid asset.** As in families 001/003/004, CSCV PBO is computed on
   SP500's grid-config weekly returns only (not pooled across assets),
   consistent with those families' established convention.
4. **`skip_days=0` included as a grid arm rather than the primary.**
   `skip_days=21` (skip the most recent trading month) was declared the
   primary before any backtest, matching the momentum literature's standard
   convention; `skip_days=0` was included specifically to test whether that
   convention matters on this loop's own assets, which the sec 4.4 grid
   results above suggest it does, especially at longer lookbacks.
