# Family 043 results: Amihud-illiquidity cross-asset rotation

**Verdict: NEAR-MISS.** The primary configuration passes sec 4.1 (beats
fixed-weight 5-asset DCA on wealth AND Sharpe at both fee levels) -- the
second family in this loop to clear that bar, after family 002 -- but
fails sec 4.2 (DSR far below 0.95), sec 4.3 (bootstrap and placebo both
fail; only rolling windows pass), and sec 4.4 (only 1/12 grid
configurations, 8.3%, beat DCA -- the weakest grid-diagnostic result of
any family that has passed sec 4.1 so far). Holdout was **not** opened
(near-miss, not a finalist -- reserved for finalists only, per sec 8
step 8).

## Rigorous distinction from family 021 (verified, not just asserted)

Reused family 021's exact `compute_illiq` (Amihud ratio, undefined on
zero/missing-volume days) and `_trailing_pctile_rank_ignoring_nan`
per-asset percentile computation, unmodified -- confirming this family
shares the underlying *statistic* with 021 by construction, and the real
distinction is in what happens next. Verified concretely (pre-grid,
before any backtest was trusted):

- **Cross-sectional correlation check**: the 5 assets' own-history Amihud
  percentiles are only weakly correlated with each other (max pairwise
  |correlation| = **0.241**, primary config's `illiq_lookback=252`) --
  confirming "currently most liquid of the 5" is a genuinely time-varying,
  cross-sectional comparison, not a relabeling of a single asset's own
  fixed regime (021 never makes any such comparison at all -- it has no
  notion of "asset A vs. asset B," only "asset A now vs. asset A's own
  past").
- **Selection frequency** (primary config, week-end days, dev period):
  SP500 9.0%, GOLD 16.6%, SILVER 14.8%, BTC 57.8%, OIL 7.6% -- every asset
  is selected a non-trivial fraction of weeks (none frozen at 0% or 100%),
  and BTC's dominance (57.8%) is itself informative: BTC's own Amihud
  ratio sits in the "currently most liquid of the 5" position most often
  during its 2014-2019 development window, a genuinely different
  empirical fact from 021's per-asset regime-frequency table (10-19% per
  asset, no cross-asset comparison at all).
- **Turnover**: the selected set changes on 36.2% of week-to-week
  transitions -- neither frozen (~0%) nor pure noise (~100%).
- `top_n=5` (all 5 assets always selected) collapses to an always-fully-
  invested equal-weight rebalanced portfolio and reproduces an
  independently-built equal-weight-rebalance reference bit-for-bit (see
  implementation checks below) -- there is no parameter setting of this
  family that recovers "buy more of asset A specifically when A's own
  ratio is elevated" (021's rule); the two are not nested.

All of this confirms the mechanism categorization (Cross-asset rotation /
relative strength, vs. 021's Sizing / valuation) is a real, verified
difference in the signal's computed output, not merely a difference in
how it's described.

## Brief distinction from families 002 and 010 (verified)

- **Family 002** (dual momentum, return-based rotation, NEAR-MISS): this
  family's signal is a liquidity/impact statistic (Amihud ratio
  percentile), computed with zero reference to price returns beyond the
  `|r_t|` numerator's magnitude (which cancels in the percentile-rank
  comparison against the asset's own history, not against return level
  across assets). Always fully invested (no cash/T-bill leg), unlike 002's
  binary in/out absolute-momentum filter.
- **Family 010** (gold/silver ratio, fixed 2-asset price-ratio rotation,
  REJECTED): spans all 5 core assets, not a fixed pair, and its signal has
  no dependence on any pair's relative PRICE level -- it is a per-asset
  volume/impact statistic ranked cross-sectionally.

## Complexity gate (sec 3.4)

3 tunable parameters (<=5); 12-configuration grid (<=36); one order per
asset per trading day (weekly rebalance-to-target-weight, same mechanics
as families 002/013/029); Close+Volume data only, already confirmed
reachable for all 5 core assets by family 021's feasibility finding
(no new data-reachability risk).

## Pre-grid non-degeneracy checks (per prereg.md, run before the grid, primary config)

| Check | Result |
|---|---|
| `PRIMARY_CONFIG` is a member of `GRID` (import-time assertion in `liquidity_rotation.py`, re-confirmed in the run script against the enumerated grid list) | PASS |
| Per-asset selection frequency (week-end days): SP500 9.0%, GOLD 16.6%, SILVER 14.8%, BTC 57.8%, OIL 7.6% -- none frozen at ~0% or ~100% | PASS |
| Turnover (fraction of week-to-week transitions where the selected set changes): 36.2% -- neither frozen nor pure noise | PASS |
| Max pairwise cross-asset percentile correlation: 0.241 -- well below the 0.9 degenerate-order threshold | PASS |
| Shared calendar never touches 2020-01-01+ (re-verified with an explicit assertion in the run script, per this iteration's instruction never to spot-check 2020+ data) | PASS (calendar ends 2019-12-31) |

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`) reproduces fixed-weight 5-asset DCA exactly (bit-for-bit on units and pooled cash) | PASS |
| **Second reference point** (families 013/029 precedent): `top_n=5` (all 5 assets always selected, collapses to 1/5 each every week) reproduces an INDEPENDENTLY-built equal-weight weekly-rebalance reference decider bit-for-bit | PASS |
| That same `top_n=5` result **differs** from plain fixed-weight DCA (confirming "degenerate" here means the equal-weight-rebalance reference, not DCA -- same distinction family 013 had to make explicit) | PASS (confirmed to differ) |
| Cash and positions never negative (fixed-weight DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| No-lookahead: perturbing all 5 assets' data after day t leaves every order on/before t unchanged | PASS |
| Point-in-time macro data | N/A -- price+volume-only signal, no macro/ALFRED series |

## Shared calendar

Same construction as families 002/013/029: `^GSPC`'s own NYSE trading-day
index, clipped to start once every core asset has data (BTC's first
date, 2014-09-17) through 2019-12-31 -- **1,332 trading days (~5.3
years)**, the same BTC-gated short development span family 002 hit (plan
sec 12's known caveat).

## Primary configuration: `illiq_lookback=252, top_n=1, signal_smooth_days=10`

### Sec 4.1 (Portfolio line) -- beats fixed-weight 5-asset DCA on wealth AND Sharpe, both fee levels

| Fee | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both) |
|---|---|---|---|---|---|
| 0.1% | 4.917 | 2.937 | 1.085 | 0.802 | **YES** |
| 0.25% | 4.254 | 2.932 | 1.022 | 0.798 | **YES** |

**Sec 4.1: PASS** at both fee levels.

### Sec 4.2 -- Deflated Sharpe Ratio >= 0.95

- Raw weekly Sharpe of the primary config's excess-return series: **0.121/week**
  (annualized ~0.876) -- clearly positive.
- `N` (raw trial count at this assessment): **1,305** (196 seed + 1,109 new
  through this family, consistent with `state/trial_counter.json`: seed 196
  + new 1109 = 1305).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **130** clusters.
- **DSR (N_eff-based, used for the decision): 0.423.** Skew 0.134, kurtosis
  6.48 (fat-tailed, consistent with the concentrated `top_n=1` rotation).
- DSR (raw-N, conservative reference): 0.411.

**Sec 4.2: FAIL** (0.423 << 0.95).

### Sec 4.3 -- robust across time and resamples (run because sec 4.1 passed, per established precedent)

Rolling windows (3-year, 20-trading-day step; 5-year windows do not fit
meaningfully in the ~5.3-year development span, same adaptation family
002 used):

| Window | n windows | % beats wealth | % beats Sharpe |
|---|---|---|---|
| Portfolio 3y | 29 | 93.1% | 62.1% |

**Rolling windows: PASS** (both >60%, though Sharpe passes only narrowly).

Block bootstrap (4-week blocks shared across all 5 assets, 60 sims per
variant):

| Variant | beats wealth | beats Sharpe |
|---|---|---|
| Raw path | 11.7% | 3.3% |
| Detrended | 23.3% | 16.7% |

**Block bootstrap: FAIL**, decisively, on both variants and both metrics
(need a majority, >50%; the raw-path Sharpe pass rate of 3.3% is one of
the weakest bootstrap results of any family in this loop so far).

Placebo (circular-shift the primary config's week-end target-weight
sequence, 60 sims):

- Real wealth/invested = 4.917, percentile among placebo runs: **80.0th**.
- Real Sharpe = 1.085, percentile among placebo runs: **76.7th**.

**Placebo: FAIL** (need >=95th percentile; the real result beats most, but
not nearly enough, arbitrarily-timed relabelings of the same rotation
pattern to conclude the specific timing/ranking is doing decisive work,
rather than "hold a concentrated, frequently-BTC-heavy tilt during a BTC
bull run" alone).

**Sec 4.3 overall: FAIL** (rolling windows pass; bootstrap and placebo
both fail; all must pass).

### Sec 4.4 -- robust across parameters (grid diagnostic)

| config_id | illiq_lookback | top_n | signal_smooth_days | wealth/invested @0.1% | DCA wealth/invested | Sharpe @0.1% | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|---|---|---|
| cfg00 | 126 | 1 | 1 | 0.797 | 2.937 | -0.149 | 0.802 | no |
| cfg01 | 126 | 1 | 10 | 2.870 | 2.937 | 0.798 | 0.802 | no |
| cfg02 | 126 | 2 | 1 | 1.605 | 2.937 | 0.572 | 0.802 | no |
| cfg03 | 126 | 2 | 10 | 2.313 | 2.937 | 0.841 | 0.802 | no |
| cfg04 | 126 | 3 | 1 | 1.639 | 2.937 | 0.600 | 0.802 | no |
| cfg05 | 126 | 3 | 10 | 2.318 | 2.937 | 1.045 | 0.802 | no |
| cfg06 | 252 | 1 | 1 | 1.174 | 2.937 | 0.245 | 0.802 | no |
| **cfg07 (primary)** | 252 | 1 | 10 | 4.917 | 2.937 | 1.085 | 0.802 | **YES** |
| cfg08 | 252 | 2 | 1 | 2.294 | 2.937 | 0.853 | 0.802 | no |
| cfg09 | 252 | 2 | 10 | 2.266 | 2.937 | 0.793 | 0.802 | no |
| cfg10 | 252 | 3 | 1 | 1.565 | 2.937 | 0.593 | 0.802 | no |
| cfg11 | 252 | 3 | 10 | 2.367 | 2.937 | 1.031 | 0.802 | no |

**Only 1 of 12 configurations (8.3%) beats DCA** on wealth AND Sharpe at
0.1% fees -- decisively below the 2/3 (8/12) requirement, and among the
weakest grid results of any family that has cleared sec 4.1 in this loop.
The pattern is a single isolated combination (`illiq_lookback=252,
top_n=1, signal_smooth_days=10`) rather than a broad region of the grid:
every other `top_n=1` arm (both `illiq_lookback=126` variants and the
unsmoothed `signal_smooth_days=1` variant of `illiq_lookback=252`) fails
on wealth, most by a wide margin. This is a strong signal that the
primary config's result is a narrow, parameter-sensitive draw rather than
a robust edge -- exactly the kind of pattern sec 4.4 exists to catch, and
combined with the bootstrap/placebo failures above, points the same
direction as family 002's own BTC-concentration finding.

**Sec 4.4: FAIL.**

CSCV probability of backtest overfitting (diagnostic, portfolio-level
grid, 8 splits, 70 combinations): **PBO = 0.171.** Lower than family 002's
0.443, i.e. the grid is not classically "overfit" in the CSCV sense
(the best in-sample config still ranks well out-of-sample reasonably
often) -- but this is consistent with the grid being uniformly weak
rather than having one standout config surrounded by near-misses: only
cfg07 clears the DCA bar at all, so there is little room for CSCV's
rank-degradation pattern to show up.

### Sec 4.5 -- distinctness

Not applicable; this family did not become a finalist.

## Verdict

**NEAR-MISS.** Passes sec 4.1 (beats fixed-weight 5-asset DCA on wealth
AND Sharpe at both fee levels) but fails sec 4.2 (DSR 0.423 < 0.95), sec
4.3 (bootstrap and placebo fail decisively; only rolling windows pass),
and sec 4.4 (only 8.3% of the grid clears the bar, need >=66.7%). Per sec
8 step 8, holdout was **not** opened -- reserved for finalists only.
Logged as a near-miss per sec 8 step 7's definition.

## Judgment calls made in this iteration

1. **Rebalance-to-target-weight mechanics (full portfolio rebalancing),
   not deposit-only tilting.** The research queue's own idea #44 wording
   ("rotates the marginal weekly deposit") could be read as tilting only
   the new $2,500 contribution while leaving existing holdings untouched.
   Per this iteration's explicit task instruction to follow family 002's
   precedent and use `portfolio_engine.py`, this family instead computes
   a full target-weight table each week and rebalances existing holdings
   toward it (buy/sell the value difference), identical in mechanics to
   families 002/013/029. Declared in `prereg.md` before any backtest ran.
2. **Reused family 021's exact Amihud/percentile computation
   unmodified**, rather than re-deriving it, to keep the cross-021
   comparison mechanically apples-to-apples (any difference in results is
   attributable to the cross-sectional-ranking mechanism, not to a subtly
   different underlying statistic).
3. **Extended `robustness.py`/`portfolio_robustness.py` to support a
   synthetic Volume column during block bootstrap** (this family is the
   first to reach sec 4.3 with a Volume-dependent signal; family 021, the
   only other one, was rejected before reaching bootstrap). Small,
   contained, backward-compatible change -- logged in
   `state/bugfix_log.md` with full detail; no other family's robustness
   output is affected (the extension is opt-in via an optional
   parameter).
4. **Reduced bootstrap/placebo simulation counts (60, not the plan's
   default 500)**, matching families 001/002/013/029's precedent -- each
   portfolio-level simulation reruns the full 5-asset engine. Declared in
   `prereg.md` before any backtest ran.
5. **Only 3-year rolling windows reported**, for the same BTC-gated
   ~5.3-year development-span reason as family 002.
6. **BTC's dominant selection frequency (57.8% of week-ends) is a known,
   flagged limitation** (plan sec 12's BTC-short-history caveat, and the
   same concentration pattern family 002 found): the primary config's
   edge is plausibly explained in large part by "hold BTC when its own
   Amihud ratio happens to be the lowest of the 5, during BTC's 2014-2019
   bull run" rather than by the cross-asset liquidity-rotation mechanism
   generalizing broadly -- exactly what the grid-diagnostic (sec 4.4) and
   placebo (sec 4.3) failures independently point to.
