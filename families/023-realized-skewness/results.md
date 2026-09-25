# Family 023 results: Realized-skewness sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1: it beats
plain DCA on wealth AND Sharpe on only **2 of 5** core assets (need >=3),
at both 0.1% and 0.25% fees. Sec 4.4's grid diagnostic fails decisively:
only **1 of 32** configs (3.1%) reaches the combined wealth-AND-Sharpe
majority bar (>=3/5 assets) -- need >=2/3 (22/32). Sec 4.2's Deflated
Sharpe is effectively zero (negative raw pooled excess Sharpe). Sec 4.3
(rolling windows / bootstrap / placebo) was **not** run, per this loop's
established precedent of running it only when sec 4.1 passes. Holdout was
**not** opened.

## Primary-config-in-grid verification (per family 021's lesson)

Checked programmatically at module import time and re-verified in the run
script before any backtest: every value in `PRIMARY_CONFIG` (`skew_window=
90, neg_threshold=-0.5, pos_threshold=0.5, buy_multiplier=2.0,
reduce_fraction=0.85`) is a member of its `GRID[...]` list, and
`PRIMARY_CONFIG in grid_configs()`. Both asserted (`realized_skewness.py`
raises `AssertionError` at import time otherwise); no mismatch was found.

## Pre-grid non-degeneracy sanity check (per prereg.md, run before the grid)

| Asset | n week-end days | Frac. negative-skew regime | Frac. positive-skew regime | Non-degenerate? |
|---|---|---|---|---|
| SP500 | 4,801 | 17.93% | 18.43% | PASS |
| GOLD | 1,010 | 22.48% | 24.06% | PASS |
| SILVER | 1,010 | 32.67% | 14.85% | PASS |
| BTC | 277 | 29.24% | 29.96% | PASS |
| OIL | 1,011 | 15.63% | 17.61% | PASS |

All 5 assets land comfortably inside the pre-declared (2%, 60%) band for
both regimes, on every asset -- the fixed-threshold design (`RSkew_t <
-0.5` / `RSkew_t > 0.5`) is not degenerate on any core asset. SILVER shows
the most skew-regime asymmetry (32.7% negative vs. 14.9% positive), a
real, not-fabricated feature of its return distribution over the
development period, not a bug. Confirms the realized-skewness computation
and threshold design fire non-trivially on every asset before any backtest
result is trusted.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (aggressive corner: `skew_window=60, neg_threshold=-0.25, pos_threshold=0.25, buy_multiplier=2.0, reduce_fraction=0.85`) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000` and `t=20000`, specifically exercising `RSkew_t`'s strict causality) | PASS |
| Point-in-time macro data | N/A -- price-only signal, no macro dependence |
| Capital deployed never exceeds cumulative deposits + interest (primary config and aggressive corner, family 021's principled-bound method: a "never invest" reference run gives the interest ceiling) | PASS |

No implementation-check failures or bugfixes were needed for this family
(no entry added to `state/bugfix_log.md`).

## Primary configuration: `skew_window=90, neg_threshold=-0.5, pos_threshold=0.5, buy_multiplier=2.0, reduce_fraction=0.85`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.38691 | 85.27722 | 0.154074 | 0.153097 | YES |
| GOLD | 2.218929 | 2.231232 | 0.501252 | 0.504917 | NO (both lose) |
| SILVER | 1.682382 | 1.686660 | 0.318681 | 0.319677 | NO (both lose) |
| BTC | 9.885967 | 9.855679 | 1.071211 | 1.067309 | YES |
| OIL | 1.178521 | 1.179855 | 0.227083 | 0.227824 | NO (both lose) |

**Sec 4.1: FAIL** -- 2/5 core assets beat DCA on wealth AND Sharpe (need
>=3), at both 0.1% and 0.25% fees (0.25% results qualitatively identical:
still 2/5). Only SP500 and BTC clear the bar; GOLD, SILVER and OIL lose on
both metrics.

### Grid diagnostic (sec 4.4)

**Only 1 of 32 configurations (3.1%) reaches the combined wealth-AND-
Sharpe majority bar** (>=3/5 assets) at 0.1% fee -- need >=2/3 (22/32).
The single config that clears it is `cfg07_sw60_nt-0.5_pt0.5_bm2.0_rf0.95`
(3/5 assets), not the declared primary. Every one of the 8 `skew_window=
90` configs manages only 2/5 assets on both wealth and Sharpe counts
individually -- the longer 90-day skewness window (the primary's own
choice) is uniformly weaker than the shorter 60-day window across the
whole grid, the opposite of what might have been hoped from using a
longer, presumably less noisy, skewness estimation window. The `neg_
threshold=-0.25` (narrower, more easily triggered negative-skew regime)
arms generally do a little better on the wealth-count metric than `neg_
threshold=-0.5`, but no config combination reaches a majority bar with
`skew_window=90`.

**Sec 4.4: FAIL** (need >=22/32; got 1/32 = 3.1%).

CSCV probability of backtest overfitting (32-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.0** -- the
grid's in-sample ranking of configs reliably predicts their out-of-sample
performance within the grid's own resamples (unlike family 022's 0.614).
This is consistent with the grid's configs being fairly stably ordered
(all clustered around "weak," rather than noisily flipping rank), not with
a fluke: the family is consistently weak rather than erratically weak.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  **-0.017166** (weekly, **-0.12378 annualized**) -- **negative**.
- `N` (raw trial count, whole-loop pool): **707** (196 seeded + 511 new,
  matching `state/trial_counter.json["new"]` = 511 after this family:
  196 + 511 = 707).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **70**
  clusters (up from families 020-022's 69 -- this family's 32-config grid
  added exactly 1 new distinct cluster at the rho>=0.5 threshold).
- **DSR (N_eff-based): ~1.81e-30** -- effectively zero (a negative raw
  Sharpe can never clear a positive `SR0` threshold at any `N`).
- DSR (raw-N, conservative reference): ~9.19e-34, also effectively zero.

**Sec 4.2: FAIL**, decisively.

## Verdict

**REJECTED.** Sec 4.1 fails (2/5 core assets, need >=3). Sec 4.4 fails
(1/32 grid configs reach the majority bar; need >=22/32). Sec 4.2 fails
decisively (DSR ~0, negative raw pooled excess Sharpe). Sec 4.3 was not
run (only run when sec 4.1 passes, per this loop's established
precedent). Holdout was **not** opened.

## Interpretation

SP500 and BTC individually clear the wealth-AND-Sharpe bar under the
primary configuration, but GOLD, SILVER and OIL all lose on both metrics
-- a similar equity/crypto-vs-commodities split to several prior sizing
families in this loop (e.g. family 022's SP500/BTC-only pattern). The
grid diagnostic is decisively negative (only 1/32 configs, and not the
primary, clears the majority bar), and the low CSCV PBO (0.0) indicates
this is a consistently weak signal across the grid rather than one that
got unlucky on its particular primary choice. A plausible reading: the
Amaya et al. (2015) realized-skewness effect was documented in a large
cross-section of individual equities (where a same-day comparison across
thousands of stocks gives the third moment real discriminating power);
applied to a handful of broad, already-diversified or single-name assets
one at a time, with no cross-sectional comparison, the same statistic
appears to carry little exploitable timing information for a fixed-dollar
DCA buyer, at least at the tested window lengths and thresholds.

## Files

- `src/backtest/v3/strategies/realized_skewness.py`
- `scripts/v3/run_023_realized_skewness.py`
- `families/023-realized-skewness/grid_results.csv`, `_primary_per_asset.csv`, `_run_output.json`
- `state/trials/new_023_*.csv` (32 files)
