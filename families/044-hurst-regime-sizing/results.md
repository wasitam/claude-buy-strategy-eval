# Family 044 results: Hurst-exponent (fractal trend-persistence) regime sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively
(only 2/5 core assets beat DCA on wealth AND Sharpe, need >=3/5, at both
fee levels) and sec 4.4 (only 16.7% of the grid clears the majority bar,
need >=66.7%). Sec 4.3 was not run, per established loop precedent (sec
4.1 already fails). Sec 4.2's DSR is effectively zero. Holdout was **not**
opened (rejected, not a finalist -- reserved for finalists only, per sec 8
step 8).

## Rigorous distinction from family 036 (verified, not just asserted)

Family 036 (lag-1 sample autocorrelation) is the closest prior family
(both measure "serial dependence structure" of returns), per this
iteration's explicit brief. Verified concretely, pre-grid:

**(a) Statistical object.** `rho_1 = Cov(r_t, r_{t-1})/Var(r)` (family
036) is a single-lag statistic. `H` (this family) is the OLS slope of
`log(mean R/S)` vs. `log(scale)` fit across 5-8 sub-window scales
(`hurst_window` divided by `1,2,3,4,6,8,12,16`) within the same trailing
window -- a genuinely multi-scale, fractal self-similarity statistic.

**(b) Constructed divergence example** (recomputed programmatically at
run time against the module's own production `_hurst_rs_single_window`,
`numpy.random.default_rng(7)`, n=252, matching the primary config's
`hurst_window`): a synthetic return series built from a slow sinusoidal
drift (amplitude 0.0015, period 1260 days = 5x the window) plus dominant
i.i.d. Gaussian noise (std 0.01, ~6.7x the drift amplitude):

| Statistic | Value |
|---|---|
| Lag-1 autocorrelation (family 036's exact statistic) | **+0.00342** (near zero -- family 036 reads this as pure noise) |
| Hurst exponent (this family's statistic) | **0.6923** (materially above 0.5 -- correctly detected as persistent/trending) |

Confirmed: `lag1_near_zero=True`, `hurst_materially_above_half=True`,
`divergence_demonstrated=True`. Neither family's grid parameters can
recover the other's signal from this exact series (rho_1 stays pinned
near zero for any `ac_window` since day-to-day noise dominates every
adjacent pair; H depends on the multi-scale range-growth structure rho_1
never computes).

**(c) Cross-check with genuine short-range persistence** (AR(1) synthetic
control, 200 seeds per rho, n=252): both statistics move together and
increase monotonically with `rho` (rho=0.0: mean H=0.544, mean lag1=-0.005;
rho=0.15: H=0.574, lag1=0.138; rho=0.3: H=0.604, lag1=0.287; rho=0.5:
H=0.643, lag1=0.489) -- confirming the two statistics agree on ordinary
short-range persistence, and the divergence in (b) is specifically a
property of long-range-only dependence that a single-lag statistic is
structurally blind to, not an estimator artifact.

## Complexity gate (sec 3.4)

4 tunable parameters (<=5); 36-configuration grid (<=36, at the cap); one
order per asset per trading day; Close-price-only data, already confirmed
reachable for all 5 core assets by every prior price-only family. PASS.

## Pre-grid checks required before running the full grid (all passed)

| Check | Result |
|---|---|
| `PRIMARY_CONFIG` is a member of `GRID` (import-time assertion in `hurst_regime_sizing.py`, re-confirmed in the run script) | PASS |
| R/S formula spot-check: random-walk synthetic (200 seeds, n=252) mean H=0.5546, within the documented small-sample bias (`|H-0.5|<0.1`) | PASS |
| AR(1) persistence spot-check: mean H strictly increasing with `rho` (0.544 -> 0.574 -> 0.604 -> 0.643 for rho=0.0/0.15/0.3/0.5), trending case (rho=0.3) H>0.55 | PASS |
| Lag-1-autocorrelation-vs-Hurst divergence example (see above) | PASS |
| No dev-period check or spot-check ever reads a date on/after 2020-01-01 or an unseen ticker (all formula/divergence checks are synthetic-only, `dates_checked=[]`; grid runs use only `load_dev()`, whose own gate enforces this) | PASS |
| Cached vs. uncached `compute_multiplier` bit-for-bit identical (performance-note check) | PASS |
| Cash-reserve dynamics (primary config, SP500): avg cash $123.13 vs. DCA baseline $103.88 (18.5% higher, `cash_meaningfully_differs_from_dca`); drawn down on high-multiplier weeks ($105.74) vs. banked on low-multiplier weeks ($141.69) | PASS |
| Pre-grid non-degeneracy: multiplier not stuck at 1.0 on any of the 5 core assets (frac-at-1.0 2.0%-19.7%, std 0.462-0.519) | PASS |

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`) reproduces plain DCA exactly, bit-for-bit | PASS |
| Second reference point: `k=0.0` (real grid-shaped code path) also reproduces plain DCA bit-for-bit | PASS |
| Cash and positions never negative (DCA, primary, aggressive grid corner) | PASS |
| Capital never exceeds cumulative deposits + interest, via the principled never-invest-ceiling bound (primary and aggressive corner) | PASS |
| No-lookahead perturbation test, `t=6000` and `t=20000` | PASS |
| Point-in-time macro | N/A -- price-only signal |

## Primary configuration: `hurst_window=126, pctile_lookback=252, k=1.0, min_mult=0.5`

(`max_mult=2.0`, `max_lump_multiple=3.0` fixed.)

### Sec 4.1 -- beats DCA on wealth AND Sharpe, per asset, at 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.2785 | 85.2772 | 0.153096 | 0.153097 | no (Sharpe loses, razor-thin) |
| GOLD | 2.2312 | 2.2312 | 0.504884 | 0.504917 | no |
| SILVER | 1.68670 | 1.68666 | 0.319680 | 0.319677 | **YES** (razor-thin) |
| BTC | 9.8523 | 9.8557 | 1.067212 | 1.067309 | no |
| OIL | 1.17994 | 1.17986 | 0.227844 | 0.227824 | **YES** (razor-thin) |

**Beats DCA count: 2/5 at 0.1% fee, 2/5 at 0.25% fee (both fall below the
>=3/5 bar). Sec 4.1: FAIL.** Every asset's strategy vs. DCA gap is
extremely small in absolute terms (differences in the 3rd-5th significant
digit on wealth and Sharpe alike) -- the primary config barely perturbs
plain DCA at all rather than decisively beating or losing to it, consistent
with the modest expected economic magnitude the mechanism section
anticipated and with a signal too noisy at this window length to move the
needle either way.

### Sec 4.2 -- Deflated Sharpe Ratio >= 0.95

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  **-0.00878/week** (annualized **-6.33%**) -- genuinely negative.
- `N` (raw trial count at this assessment): **1,341** (196 seed + 1,145
  new; sanity check: 196+1145=1341, matches `state/trial_counter.json`).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **132**
  clusters.
- **DSR (N_eff-based, used for the decision): 1.30e-22.** Skew 1.603,
  kurtosis 105.4 (fat-tailed).
- DSR (raw-N, conservative reference): 6.05e-23.

**Sec 4.2: FAIL**, decisively -- the raw pooled excess-return Sharpe is
negative, so no amount of trial-count adjustment could produce a
meaningful DSR.

### Sec 4.3 -- not run

Per established loop precedent (families 021/023/026/028/030/032/033/034
etc.), sec 4.3 (rolling windows, block bootstrap, placebo) is skipped when
sec 4.1 already fails decisively.

### Sec 4.4 -- robust across parameters (grid diagnostic)

| `hurst_window` | Best `beats_wealth@0.1%` count across its `pctile_lookback`x`k`x`min_mult` arms | Pattern |
|---|---|---|
| 100 | 2/5 (most arms 0-2/5) | Weakest window |
| 126 | 3/5 (best arms; primary's own window) | Mixed, no arm reaches 4/5 |
| 252 | 4/5 (best arms: cfg24/25/27/29, all `pctile_lookback=252`) | Strongest window, but Sharpe lags wealth |

Full 36-row grid in `families/044-hurst-regime-sizing/grid_results.csv`
and the run log. **Only 6/36 (16.7%) of configurations reach the combined
majority bar** (>=3/5 assets beating DCA on both wealth AND Sharpe at
0.1% fee) -- decisively below the 2/3 (24/36) requirement. The pattern:
longer `hurst_window` (252d) and lower `pctile_lookback` (252d) combined
with moderate-to-high `k` perform best, but even the single best arms
(cfg24/25/27/29, `hurst_window=252, pctile_lookback=252`) only reach 4/5
on wealth and 3/5 on Sharpe -- never a clean sweep, and the primary
config's own `hurst_window=126` arm caps out at 3/5 wealth / 2/5 Sharpe.

**Sec 4.4: FAIL** (16.7% << 66.7% required).

CSCV probability of backtest overfitting (diagnostic, SP500 grid, 8
splits, 70 combinations): **PBO = 0.486** -- one of the higher (more
overfitting-prone) CSCV results of any family in this loop so far,
consistent with a grid whose best-looking arms are unstable across splits
rather than reflecting a broad, robust edge.

### Sec 4.5 -- distinctness

Not applicable; this family did not become a finalist.

## Verdict

**REJECTED.** Fails sec 4.1 (2/5 assets beat DCA on wealth AND Sharpe,
need >=3/5, at both fee levels -- and every asset's margin is razor-thin
in either direction), sec 4.2 (DSR ~1.3e-22, raw pooled excess Sharpe
genuinely negative), and sec 4.4 (only 16.7% of the grid clears the
majority bar, need >=66.7%; CSCV PBO=0.486, elevated). Sec 4.3 not run
per established precedent. Holdout not opened.

## Judgment calls made in this iteration

1. **Denser R/S scale ladder than a simple halving-only ladder.**
   `hurst_window` divided by `1,2,3,4,6,8,12,16` (deduplicated, floored at
   `min_scale=8`) rather than just `1,2,4,8`, to reduce the well-documented
   small-sample upward bias of the naive R/S estimator (verified: mean
   estimated H for a pure random walk at a 252-day window moved from
   ~0.64 with the sparse 4-scale ladder to ~0.55 with this denser ladder,
   closer to the theoretical 0.5). No Anis-Lloyd-style bias correction was
   applied on top of this, to keep the rule within sec 3.4's complexity
   ceiling -- the residual bias is documented in `prereg.md` as a known
   limitation, and does not affect the strategy's mechanism because the
   sizing signal is a **relative** percentile rank within each asset's own
   trailing H history, not an absolute comparison against the textbook
   H=0.5 threshold.
2. **Per-`(asset, hurst_window)` raw-signal caching** in the run script
   (declared in `prereg.md`'s "Performance note" before the grid ran):
   the R/S computation is materially more expensive than family 036's
   lag-1-autocorrelation computation (a rolling Python-level R/S fit
   across multiple scales per day, ~1.4-24s per asset per window vs.
   sub-second for a rolling Pearson correlation), so the raw `H_t` array
   is computed once per of the 15 `(asset, hurst_window)` combinations and
   reused across all `pctile_lookback`x`k`x`min_mult` grid arms that share
   the same `hurst_window`, instead of recomputing it 36x5=180 times.
   Verified bit-for-bit identical to the uncached path before trusting any
   grid result.
3. **Synthetic-only pre-grid formula and divergence checks** (checkpoints
   (b) and (c) of this iteration's task brief) use no real asset dates at
   all, so the "never touch 2020+/unseen data" rule is trivially satisfied
   for those two checks; the `dates_checked=[]` field documents this
   explicitly in the run script's own output rather than leaving it
   implicit.
4. **Category filed as Trend / time-series momentum exit**, matching the
   research queue's own categorization of idea #45 (Hurst-exponent
   long-range persistence is, mechanistically, a trend/momentum-adjacent
   signal, distinguished from family 036's own filing under the same
   category by the multi-scale-vs-single-lag distinction above, not by a
   different category).
