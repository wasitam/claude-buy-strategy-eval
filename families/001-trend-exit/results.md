# Family 001 results: 10-month/200-day trend exit (Faber 2007)

**Verdict: REJECTED** (fails sec 4.1; holdout not opened per sec 8 step 8,
"finalists only").

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate parameters reproduce DCA exactly (disabled trend filter vs. plain DCA, bit-for-bit on units and cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary trend-exit config) | PASS |
| No-lookahead: perturbing all data after day t leaves every order on/before t unchanged | PASS |
| Point-in-time macro data | N/A (price-only strategy; vacuously satisfied) |

## Primary configuration: `sma_days=210, confirm_days=0, sell_on_exit=0`

### sec 4.1 — beats DCA on wealth AND Sharpe, >= 3 of 5 core assets, both fee levels

At 0.1% fees:

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both) |
|---|---|---|---|---|---|
| SP500 | 88.997 | 85.277 | 0.184 | 0.153 | **YES** |
| GOLD | 2.221 | 2.231 | 0.504 | 0.505 | no |
| SILVER | 1.659 | 1.687 | 0.313 | 0.320 | no |
| BTC | 9.695 | 9.856 | 1.058 | 1.067 | no |
| OIL | 1.167 | 1.180 | 0.215 | 0.228 | no |

**1 of 5** assets beat DCA on both metrics (need >= 3). At 0.25% fees the
result is the same, 1 of 5 (SP500 only). **sec 4.1: FAIL.**

The pattern is consistent with the mechanism working exactly as designed on
the one asset with the longest, most sustained multi-decade drawdowns (the
1929-32, 1973-74, 2000-02, 2008-09 SP500 bear markets), but losing more to
whipsaw than it saves elsewhere on gold, silver, oil and BTC, whose
development-period drawdowns in this sample were either shorter or choppier.

### sec 4.2 — Deflated Sharpe Ratio >= 0.95

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  0.00335/week (annualized ~0.024) — essentially zero, consistent with the
  4/5-asset underperformance above.
- `N` (raw trial count at this assessment): **214** (196 seeded + 18 new
  from this family's grid).
- `N_eff` (average-linkage clustering, distance sqrt(0.5(1-rho)), rho>=0.5
  threshold): **30** clusters.
- **DSR (N_eff-based, used for the decision): 9.3e-21** — far below 0.95.
- DSR (raw-N, conservative reference): 2.3e-40.

**sec 4.2: FAIL**, overwhelmingly so — the near-zero raw Sharpe means no
amount of trial-count generosity would clear the 0.95 bar here.

### sec 4.3 — robust across time and resamples

Rolling windows (development period, 20-trading-day step), primary config
vs. DCA, percent of windows the strategy beats DCA on wealth / Sharpe
(need > 60% on each):

| Window | n windows | % beats wealth | % beats Sharpe |
|---|---|---|---|
| SP500 3y | 1118 | 27.3% | 26.4% |
| SP500 5y | 1093 | 34.1% | 40.2% |
| GOLD 3y | 205 | 12.7% | 6.3% |
| GOLD 5y | 180 | 12.2% | 13.3% |
| SILVER 3y | 205 | 7.8% | 2.9% |
| SILVER 5y | 180 | 5.0% | 3.9% |
| OIL 3y | 206 | 20.9% | 12.1% |
| OIL 5y | 180 | 32.8% | 21.7% |
| BTC 2y | 72 | 20.8% | 22.2% |

None of the 9 window/asset combinations reach the 60% bar. **sec 4.3
(rolling windows): FAIL.**

Block bootstrap (SP500, 4-week blocks; reduced to 120 sims/variant from the
plan's 500 — see "Judgment calls" below): raw-path beats DCA on wealth in
32.5% of histories and on Sharpe in 34.2% — well under a majority.
**sec 4.3 (bootstrap, raw path): FAIL.** The detrended-bootstrap run and the
500-run placebo circular-shift test were stopped before completing (see
judgment call #3 below) once the raw bootstrap, both rolling-window
sweeps, the full grid and the DSR calculation had already independently and
conclusively failed sec 4.1/4.2/4.3/4.4 — running the remaining diagnostics
to completion would not change the verdict.

### sec 4.4 — robust across parameters (grid diagnostic)

Best any of the 18 grid configurations manages is **2 of 5** core assets
beating DCA on both wealth and Sharpe at 0.1% fees (the `sell_on_exit=1`
arms, i.e. Faber's classic full-liquidation variant, consistently edge out
the deposit-only arms 2/5 vs 1/5, but neither reaches 3/5). **0 of 18**
configurations (0%) reach the majority-of-assets bar. **sec 4.4: FAIL**
(need >= 2/3 = 12/18).

CSCV probability of backtest overfitting (diagnostic, SP500 grid, 8 splits,
70 combinations): **PBO = 0.0**. This says the grid's in-sample best
configuration also tends to rank well out-of-sample — i.e., the grid isn't
overfit to noise, it's just consistently mediocre across the board. That is
consistent with, not contradictory to, the sec 4.1/4.3/4.4 failures above.

### sec 4.5 — distinctness

Not applicable; this family did not become a finalist.

## Verdict

**REJECTED.** The primary configuration fails sec 4.1 (only 1/5 assets, not
the required >=3/5) and every downstream check (4.2 DSR, 4.3 rolling windows
and bootstrap, 4.4 grid majority). Per sec 8 step 8, holdout data was **not**
opened — holdout access is reserved for finalists only, and this family never
reached finalist status.

## Judgment calls made in this iteration (per the plan's own allowance)

1. **Seed trial count and excess-return reconstruction (sec 6.3).** Counted
   196 prior configurations as seed trials, from 8 of the CSV files under
   `reports/` (`reports/grid_metrics.csv`, `reports/v2/adca_grid.csv`,
   `adca_grid_extra.csv`, `five_asset_rebalance_frequency.csv`,
   `rebalance_grid.csv`, `regime_switch_headline.csv`, `smartdca_grid.csv`,
   `smartdca_grid_extra.csv`). Excluded 3 files
   (`reports/v2/fed_cycles.csv`, `regime_switch_periods.csv`,
   `regime_switch_percycle.csv`) as per-period/per-cycle re-expressions of
   configurations already counted in `regime_switch_headline.csv`, not
   distinct new trials. Rebuilding all 196 configurations' exact
   excess-return series with the v3 engine was judged infeasible in this
   iteration (different weekly engine, 5-asset portfolios, and intermediate
   state not persisted to disk for several of them); their series were
   instead approximated as correlated synthetic Gaussian series (shared
   per-source-file/per-asset factor + idiosyncratic noise, lightly biased by
   each row's own reported Sharpe) purely so N_eff clustering has realistic
   correlation structure to group on. See `scripts_v3_seed_trials.py`'s
   docstring. This makes `N_eff=30` a rough estimate, not exact — but since
   the primary configuration's raw Sharpe is already ~0 and DSR is many
   orders of magnitude below 0.95, no plausible correction to N_eff changes
   the verdict.
2. **Portfolio engine deferred.** `src/backtest/v3/engine.py` implements the
   single-asset daily loop only (all that family 001 needs). A shared-
   calendar portfolio engine is deferred until a portfolio-category family
   (e.g. seed queue #2, dual momentum rotation) is actually tested.
3. **Reduced bootstrap/placebo simulation counts.** The plan specifies 500
   runs; this iteration used 120 for the block-bootstrap and placebo
   diagnostics (rolling windows used their full, cheap window counts), the
   same reduced-count scoping precedent documented in
   `src/backtest/v2/robustness.py`'s own docstring, because SP500's
   92-year daily development history makes each full-history simulation
   ~1.9s and this family was already unambiguously rejected on sec 4.1 and
   4.2 before the robustness suite even ran.
4. **`sell_on_exit` grid arm is diagnostic-only, not primary-eligible.** The
   seed-queue wording for idea #1 describes only deposit disposition
   ("park deposits in cash"), not liquidation of existing holdings, so the
   deposit-only variant was declared primary in `prereg.md` before any
   backtest ran; the classic Faber full-liquidation variant
   (`sell_on_exit=1`) was included in the grid as a robustness comparison
   only, per sec 4.4's "only the primary configuration can become a
   finalist" rule.
