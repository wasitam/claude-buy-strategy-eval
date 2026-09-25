# Family 002 results: dual momentum rotation (Antonacci 2014)

**Verdict: NEAR-MISS** (passes sec 4.1; fails sec 4.2, sec 4.3 (bootstrap and
placebo), and sec 4.4; holdout not opened per sec 8 step 8, "finalists
only" -- this family never reached finalist status).

Assessed as a **Portfolio** family throughout, per the win-rule
interpretation pre-registered in `prereg.md` (dual momentum's mechanism
requires cross-asset ranking and has no meaningful single-asset
decomposition; see "Ambiguity resolved" below for the full reasoning).

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`) reproduces fixed-weight 5-asset DCA exactly (bit-for-bit on units and pooled cash) | PASS |
| Cash and positions never negative (fixed-weight DCA baseline) | PASS |
| Cash and positions never negative (primary dual-momentum config) | PASS |
| No-lookahead: perturbing all 5 assets' data after day t leaves every order on/before t unchanged | PASS |
| Point-in-time macro data | N/A (price/IRX-only strategy; vacuously satisfied) |

## Shared calendar (judgment call, per prereg.md)

The portfolio decision calendar is `^GSPC`'s own NYSE trading-day index (plan
sec 3.2's explicit instruction), clipped to start once every core asset has
data -- i.e. **2014-09-17** (BTC's first date) through **2019-12-31**, 1,332
trading days (~5.3 years). Gold, silver, oil and BTC OHLC are forward-filled
onto this shared calendar to handle small exchange-holiday mismatches. This
means family 002's effective development period is much shorter than family
001's (which could use each asset's own, longer history independently) --
the portfolio can only exist once all 5 assets do. This is a direct
consequence of testing a true cross-asset rotation strategy and is flagged
here as a real limitation, on top of the plan's own documented BTC caveat
(sec 12).

## Primary configuration: `lookback_days=252, top_n=1, abs_mom_buffer_bps=0`

### sec 4.1 (Portfolio line) -- beats fixed-weight 5-asset DCA on wealth AND Sharpe, both fee levels

| Fee | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both) |
|---|---|---|---|---|---|
| 0.1% | 4.373 | 2.937 | 0.956 | 0.802 | **YES** |
| 0.25% | 4.279 | 2.932 | 0.948 | 0.798 | **YES** |

**sec 4.1: PASS** at both fee levels. The primary configuration holds only
the single best-momentum core asset each week (or cash, if none qualifies);
over 2014-09/2019-12 that was disproportionately BTC, whose ~5-year run
dominates the wealth figure (see "Judgment calls / caveats" below).

### sec 4.2 -- Deflated Sharpe Ratio >= 0.95

- Raw weekly Sharpe of the primary config's excess-return series (strategy
  minus fixed-weight DCA, weekly, @0.1% fee): **0.110/week** (annualized
  ~0.79) -- clearly positive, unlike family 001.
- `N` (raw trial count at this assessment): **226** (196 seeded + 18 from
  family 001 + 12 new from this family's grid).
- `N_eff` (average-linkage clustering, distance sqrt(0.5(1-rho)), rho>=0.5
  threshold): **32** clusters.
- **DSR (N_eff-based, used for the decision): 0.299** -- positive raw Sharpe,
  but well below the 0.95 bar once deflated for 32 effective trials and the
  series' skew/kurtosis (skew 0.59, kurtosis 6.70 -- fat-tailed, consistent
  with a concentrated single-asset-at-a-time rotation).
- DSR (raw-N, conservative reference): 0.066.

**sec 4.2: FAIL.**

### sec 4.3 -- robust across time and resamples

Rolling windows (portfolio NAV vs. fixed-weight DCA, 3-year windows, 20
trading-day step -- 5-year windows do not fit meaningfully in a 5.3-year
development span, so only 3-year windows are reported, per prereg.md's
robustness-adaptation note):

| Window | n windows | % beats wealth | % beats Sharpe |
|---|---|---|---|
| Portfolio 3y | 29 | 72.4% | 72.4% |

**Rolling windows: PASS** (>60% bar on both wealth and Sharpe).

Block bootstrap (4-week blocks, same block starts shared across all 5 assets
per plan sec 4.3; **60 sims** per variant -- see "Judgment calls" below):

| Variant | beats wealth | beats Sharpe |
|---|---|---|
| Raw path | 45.0% | 18.3% |
| Detrended | 31.7% | 31.7% |

**Block bootstrap: FAIL** on both variants (need a majority, i.e. >50%; raw
path misses on wealth and badly misses on Sharpe, detrended misses on both).

Placebo (circular-shift the primary config's week-end target-weight
sequence, 60 sims):

- Real wealth/invested = 4.373, percentile among placebo runs: **56.7th**.
- Real Sharpe = 0.956, percentile among placebo runs: **56.7th**.

**Placebo: FAIL** (need >= 95th percentile; the real result is barely above
the placebo median, meaning an arbitrarily-timed version of the same
rotation pattern does nearly as well -- the specific temporal alignment of
the signal is not doing much of the work here, most of the edge over DCA in
this development window plausibly comes from being concentrated in
some risky asset rather than diversified across all 5, not from the
momentum *timing* itself).

**sec 4.3 overall: FAIL** (rolling windows pass, but bootstrap and placebo
both fail; sec 4.3 requires all of these checks, not just one).

### sec 4.4 -- robust across parameters (grid diagnostic)

| config_id | lookback_days | top_n | buffer_bps | beats DCA @0.1% (wealth+Sharpe) |
|---|---|---|---|---|
| cfg00 | 126 | 1 | 0 | YES |
| cfg01 | 126 | 1 | 50 | YES |
| cfg02 | 126 | 2 | 0 | no |
| cfg03 | 126 | 2 | 50 | no |
| cfg04 | 189 | 1 | 0 | YES |
| cfg05 | 189 | 1 | 50 | YES |
| cfg06 | 189 | 2 | 0 | no |
| cfg07 | 189 | 2 | 50 | no |
| cfg08 (primary) | 252 | 1 | 0 | YES |
| cfg09 | 252 | 1 | 50 | YES |
| cfg10 | 252 | 2 | 0 | no |
| cfg11 | 252 | 2 | 50 | no |

**6 of 12 configurations (50.0%) beat DCA** at 0.1% fees. The pattern is
completely clean: every `top_n=1` config passes, every `top_n=2` config
fails, regardless of lookback or buffer -- i.e. the "edge" here is really
"be concentrated in one asset" more than any specific momentum-window
choice. **sec 4.4: FAIL** (need >= 2/3 = 8/12).

CSCV probability of backtest overfitting (diagnostic, portfolio-level grid,
8 splits, 70 combinations): **PBO = 0.443**. Roughly a coin flip -- the grid's
best in-sample configuration ranks out-of-sample about as often below
median as above it. This is a meaningfully higher PBO than family 001's
(0.0), consistent with a smaller, more concentrated grid where `top_n=1` vs
`top_n=2` is doing most of the differentiating work rather than the
lookback/buffer parameters carrying independent information.

### sec 4.5 -- distinctness

Not applicable; this family did not become a finalist.

## Verdict

**NEAR-MISS.** The primary configuration passes sec 4.1 (beats fixed-weight
5-asset DCA on wealth AND Sharpe at both fee levels) -- the first family in
this loop to do so -- but fails sec 4.2 (DSR 0.299 < 0.95), sec 4.3 (block
bootstrap and placebo both fail majority/percentile bars, though rolling
windows pass), and sec 4.4 (only 50% of the grid beats DCA, below the 2/3
bar). Per sec 8 step 8, holdout data was **not** opened -- holdout access is
reserved for finalists only, and every one of sec 4.2/4.3/4.4 independently
fails to clear its bar. Logged as a near-miss per sec 8 step 7's definition
("passes sec 4.1 but not sec 4.2-4.4; logged but not promoted").

## Judgment calls made in this iteration

1. **Win-rule interpretation (sec 4.1 "Portfolio" vs. "Single-asset").**
   Pre-registered *before* any backtest in `prereg.md`: dual momentum's
   mechanism is inherently cross-asset (relative-momentum ranking has no
   single-asset analogue), and sec 4.5 lists "Cross-asset rotation /
   relative strength" as its own mechanism category -- the same status v2's
   fixed-weight rebalanced portfolios (C1/C2/C3) had. This family was
   therefore assessed under sec 4.1/4.3/5.3's "Portfolio" lines throughout:
   one NAV series (pooled $2,500/week) vs. fixed-weight 5-asset DCA, rather
   than 5 independent single-asset in/cash decisions. This is a real
   ambiguity in the charter and the alternative reading (forcing a per-asset
   "3 of 5" decomposition) was considered and rejected as inconsistent with
   what the strategy's own mechanism measures.
2. **Shared portfolio calendar and rebalance cadence.** Per plan sec 3.2
   ("For the portfolio calendar, use NYSE trading days"), used `^GSPC`'s own
   trading-day index, clipped to BTC's start date (2014-09-17) since a
   5-asset portfolio can't exist before all 5 assets do; other assets'
   OHLC forward-filled onto that calendar. Rebalance cadence fixed at
   **weekly** (matching the deposit cadence) rather than a tunable grid
   parameter, to keep the parameter count at 3 (well under the 5-parameter
   ceiling) and the grid's backtest cost bounded; documented in `prereg.md`
   before any backtest ran, per the plan's own allowance for pre-declared
   engineering judgment calls.
3. **Reduced bootstrap/placebo simulation counts (60, not the plan's
   default 500).** Consistent with the precedent set in family 001
   (`state/bugfix_log.md`, `families/001-trend-exit/results.md` judgment
   call #3) and `src/backtest/v2/robustness.py`'s own docstring: each
   portfolio-level simulation reruns the full 5-asset engine (~5x the cost
   of a single-asset simulation), so 60 sims (half of family 001's
   already-reduced 120) was used for both bootstrap variants and the
   placebo test. Declared in `prereg.md` before any backtest ran.
4. **Only 3-year rolling windows reported, not 5-year.** The BTC-gated
   development span is ~5.3 years total, so a 5-year rolling window (with a
   20-trading-day step) produces at most a handful of nearly-identical,
   heavily-overlapping windows -- not a meaningful independent robustness
   check. Declared as a robustness-adaptation note in `prereg.md` before any
   backtest ran.
5. **BTC concentration is the dominant driver of this result, and it is a
   known weakness (plan sec 12).** The grid pattern in sec 4.4 above
   (every `top_n=1` config passes, every `top_n=2` config fails, regardless
   of lookback/buffer) and the placebo test's near-median percentile (56.7,
   not >=95) both point the same direction: most of this family's edge over
   fixed-weight DCA in development is explained by "concentrate in one
   asset during a strong multi-year BTC bull run" rather than by the
   momentum-timing mechanism itself adding value beyond what a
   randomly-timed rotation into a similarly concentrated position would
   have captured. Combined with BTC's short (~5-year) development history,
   this is exactly the kind of result the plan's DSR/bootstrap/placebo
   battery exists to catch, and it did: sec 4.1 alone would have made this
   family look like a strong candidate, but sec 4.2-4.4 correctly flag it as
   not yet trustworthy.
