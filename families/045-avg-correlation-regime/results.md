# Family 045 results: Cross-asset average-correlation regime sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 (only 2/5
core assets beat DCA on wealth AND Sharpe, need >=3/5, at both fee
levels), sec 4.2 (DSR ~1.77e-42, raw pooled excess Sharpe genuinely
negative), and sec 4.4 (only 11.1% of the grid clears the majority bar,
need >=66.7%). Sec 4.3 was not run, per established loop precedent (sec
4.1 already fails). Holdout was **not** opened (rejected, not a
finalist).

## Required distinction 1: hybrid design vs. family 043 (verified, not just asserted)

Confirmed concretely before any grid result was trusted:

- **Cross-asset dependence of the INPUT**: perturbing GOLD's own price
  history (5% Gaussian noise injected into GOLD's Close from day 0
  onward, seed=11) changes SP500's own `avg_corr` signal on every day
  where the signal is defined -- proving asset A's signal is
  mathematically undefined from A's own price series alone, unlike every
  prior single-asset family in this loop.
- **Single-asset OUTPUT**: the decider's `decide(t, cash)` closure takes
  exactly `(t, cash)` -- the SAME signature every prior single-asset
  family's decider uses (`v3eng.run_single_asset`), structurally
  incapable of moving capital between assets (unlike family 043's
  portfolio `decide(t, cash, total_value, units_now)` signature, which
  can and does reallocate the pooled deposit across all 5 assets).

This completes family 043's distinction (documented in prereg.md) with
code, not just prose: family 043 is cross-asset OUTPUT / within-asset
INPUT (its own per-asset Amihud percentile is a purely within-asset
statistic; only the cross-sectional ranking and rebalancing action are
cross-asset); family 045 is the mirror image, cross-asset INPUT /
single-asset OUTPUT.

## Required distinction 2: price-only vs. every macro/credit/sentiment regime family

Confirmed by construction: `compute_avg_pairwise_corr` reads only the 5
core assets' own Close data (`load_dev()`'s own output), never calling
`fetch_fred_macro`/`fetch_yf_macro`/`yf.Ticker` -- no external data
source, no publication lag, no ALFRED/point-in-time vintage handling of
any kind, unlike every VIX-family (016/025/041/047) or credit/macro
family (011/019/027/032/038) in this loop.

## Crisis-window correlation-spike verification (real dev data, 2008 GFC -- required before proceeding)

**Important correction, caught and documented before trusting the
mechanism** (logged in `state/bugfix_log.md`): a naive Sep-Dec 2008
calendar window does **not** show an elevated `avg_corr` on SP500 (mean
percentile 46.8th, essentially at the neutral median, vs. a 2005 calm
reference's 45.8th) -- because a trailing `corr_window=126`-day estimator
ending in Sep-Dec 2008 mostly reflects the run-up MONTHS (roughly
Mar-Dec 2008), during which gold's classic flight-to-safety behavior
(SP500-GOLD correlation went sharply **negative**, mean -0.203 in this
window) offset oil's crash-together co-movement (SP500-OIL went sharply
**positive**, mean +0.142), netting the 3-leg average (BTC does not
exist yet) back down near zero -- an **estimator-lag effect, not evidence
against the mechanism**. Inspecting the monthly `avg_corr` time series
directly confirmed the genuine spike materializes with the estimator's
own inherent lag: `avg_corr` rises from -0.247 in Sep 2008 to +0.136 by
Dec 2008 and stays elevated (+0.15 to +0.20) through mid-2009, well above
both the whole-SP500-history mean (+0.073) and the 2005 calm reference.
Using the corrected window (**Dec 2008 - Jun 2009**, still real,
pre-2020, well-documented GFC-aftermath dev data): mean `avg_corr`
percentile **88.6th** vs. the 2005 calm reference's **45.8th** --
decisively confirming the statistic behaves as the mechanism requires,
once the estimator's own lag is accounted for. `dates_checked`:
2008-12-01, 2009-06-30, 2005-01-01, 2005-12-31 -- all strictly pre-2020.

## BTC's shorter history / the 3 data eras (verified concretely)

`load_dev()`'s real per-asset start dates create 3 eras for SP500's own
signal: **1927-12-30 to 2000-08-30** (SP500-only; zero of the other 4
core assets exist yet -- `avg_corr` undefined every day, `n=18,245` days,
`frac_multiplier_exactly_1.0=1.0`, **bit-for-bit plain DCA** by
construction, per rule 4's ">=2 valid legs" requirement); **2000-08-30 to
2014-09-17** (GOLD/SILVER/OIL exist, not BTC -- `n=3,532` days,
`frac_at_1.0=0.110`, `std=0.558`, genuinely non-degenerate); **2014-09-17
to 2019-12-31** (all 4 legs -- `n=1,332` days, `frac_at_1.0=0.002`,
`std=0.563`, genuinely non-degenerate). **No shared 5-asset calendar was
imposed** (unlike family 043's portfolio calendar, which had to start at
BTC's own start date): SP500 keeps its full ~92-year dev history, and the
signal gracefully falls back to neutral (`m_t=1.0`) rather than
truncating any asset's history. This also explains why the
**whole-history** cash-reserve-dynamics check needed to be **restricted
to the post-2000-08-30 era** (see next section) -- averaging over the
whole 92-year SP500 sample dilutes any real signal effect toward zero by
construction, since ~79% of SP500's dev days are the pre-2000
DCA-identical era.

## Sign-inversion spot-check (verified mechanically)

On real SP500 dev data: 2003-03-05 (lowest `avg_corr` percentile,
0.0040) gives `m_t=1.992` (buy nearly double); 2004-03-01 (highest
`avg_corr` percentile, 1.0) gives `m_t=0.500` (buy half) -- confirming
rule 6's stated sign (LOW correlation percentile -> buy MORE, HIGH -> buy
LESS), the necessary consequence of the mechanism's inverted functional
form relative to every prior continuous-percentile family in this loop.

## Complexity gate (sec 3.4)

4 tunable parameters (<=5); 36-configuration grid (<=36, at the cap); one
order per asset per trading day; Close-price-only data for all 5 core
assets, already confirmed reachable by every prior price-only family.
PASS.

## Pre-grid checks required before running the full grid (all passed after one correction)

| Check | Result |
|---|---|
| `PRIMARY_CONFIG` is a member of `GRID` (import-time assertion in `avg_correlation_regime.py`) | PASS |
| Crisis-window correlation-spike verification (2008 GFC) | PASS (after correcting the window for estimator lag -- see above, logged in `state/bugfix_log.md`) |
| Hybrid-design verification (cross-asset dependence of the input; single-asset shape of the decider signature) | PASS |
| Era-by-era non-degeneracy (SP500's 3 data eras) | PASS |
| Sign-inversion spot-check | PASS |
| No dev-period check or spot-check ever reads a date on/after 2020-01-01 or an unseen ticker | PASS (`dates_checked` for the crisis-window check are all 2005/2008/2009; all other checks are on real dev data already gated by `load_dev()`) |
| Cached vs. uncached `compute_multiplier` bit-for-bit identical | PASS |
| Cash-reserve dynamics (primary config, SP500, restricted to the post-2000-08-30 era where the signal is actually live): avg cash $122.03 vs. DCA baseline $103.82 (17.5% higher); drawn down on high-multiplier weeks ($103.93) vs. banked on low-multiplier weeks ($147.50) | PASS (after restricting to the signal-live era -- see above) |
| Pre-grid non-degeneracy (whole-history): multiplier not stuck at 1.0 on any of the 5 core assets | PASS (SP500 frac-at-1.0 80.6%, expected given its long pre-2000 DCA-identical era; GOLD/SILVER/OIL/BTC 8.0%-19.9%) |

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`) reproduces plain DCA exactly, bit-for-bit | PASS |
| Second reference point: `k=0.0` (real grid-shaped code path) also reproduces plain DCA bit-for-bit | PASS |
| Cash and positions never negative (DCA, primary, aggressive grid corner) | PASS |
| Capital never exceeds cumulative deposits + interest, via the principled never-invest-ceiling bound (primary and aggressive corner) | PASS |
| No-lookahead perturbation test (own asset's data), `t=6000` and `t=20000` | PASS |
| **No-lookahead perturbation test extended to the CROSS-ASSET inputs** (perturbing the OTHER 4 assets' data, not SP500's own, after the checkpoint day), `t=6000` and `t=20000` | PASS -- this family-specific extension (`checks.check_no_lookahead` alone would not have caught a lookahead bug entering through the cross-asset correlation inputs) confirmed no such bug exists |
| Point-in-time macro | N/A -- price-only signal, no external data |

## Primary configuration: `corr_window=126, pctile_lookback=252, k=1.0, min_mult=0.5`

(`max_mult=2.0`, `max_lump_multiple=3.0` fixed.)

### Sec 4.1 -- beats DCA on wealth AND Sharpe, per asset, at 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.277237 | 85.277223 | 0.153097 | 0.153097 | **YES** (razor-thin) |
| GOLD | 2.231068 | 2.231232 | 0.504896 | 0.504917 | no |
| SILVER | 1.686776 | 1.686660 | 0.319704 | 0.319677 | **YES** (razor-thin) |
| BTC | 9.847901 | 9.855679 | 1.067005 | 1.067309 | no |
| OIL | 1.179926 | 1.179855 | 0.227748 | 0.227824 | no (wins wealth, loses Sharpe) |

**Beats DCA count: 2/5 at 0.1% fee, 2/5 at 0.25% fee (both fall below the
>=3/5 bar). Sec 4.1: FAIL.** As with several prior modest-magnitude
sizing families, every asset's strategy-vs-DCA gap is small (3rd-5th
significant digit on wealth, similarly small on Sharpe) -- the primary
config perturbs plain DCA only slightly, consistent with the mechanism
section's own anticipation of a modest-magnitude effect, and with the
correlation-regime tilt's max multiplier range (0.5x-2.0x) landing
without a decisive directional edge on 3 of the 5 assets.

### Sec 4.2 -- Deflated Sharpe Ratio >= 0.95

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  **-0.02588/week** (annualized **-18.66%**) -- genuinely, substantially
  negative.
- `N` (raw trial count at this assessment): **1,377** (196 seed + 1,181
  new; sanity check: 196+1181=1377, matches `state/trial_counter.json`).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **133**
  clusters.
- **DSR (N_eff-based, used for the decision): 1.767e-42.** Skew -19.04,
  kurtosis 841.3 (extremely fat-tailed).
- DSR (raw-N, conservative reference): 1.517e-42.

**Sec 4.2: FAIL**, decisively -- the raw pooled excess-return Sharpe is
substantially negative, so no amount of trial-count adjustment could
produce a meaningful DSR.

### Sec 4.3 -- not run

Per established loop precedent (families 019/021/023/024/025/026/028/032/
042/044 etc.), sec 4.3 (rolling windows, block bootstrap, placebo) is
skipped when sec 4.1 already fails decisively.

### Sec 4.4 -- robust across parameters (grid diagnostic)

Only **4/36 (11.1%)** configurations reach the combined majority bar
(>=3/5 assets beating DCA on both wealth AND Sharpe at 0.1% fee) --
decisively below the 2/3 (24/36) requirement. The strongest single arms
(`cfg03` at `corr_window=60,k=1.0,min_mult=0.5`, and `cfg32/cfg33` at
`corr_window=126,pctile_lookback=504`) reach at most 4/5 on wealth and
2-4/5 on Sharpe, but no arm produces a clean 5/5 sweep and no clear
monotonic pattern across `corr_window`/`pctile_lookback` emerges (unlike,
e.g., family 044's cleaner longer-window-is-better pattern) -- consistent
with a genuinely noisy, parameter-sensitive grid rather than a broad,
robust edge. Full 36-row grid in
`families/045-avg-correlation-regime/grid_results.csv`.

**Sec 4.4: FAIL** (11.1% << 66.7% required).

CSCV probability of backtest overfitting (diagnostic, SP500 grid, 8
splits, 70 combinations): **PBO = 0.386** -- moderate, in the middle of
this loop's observed range, consistent with a diffuse, noise-dominated
grid rather than either a reliably weak one or an unusually overfit one.

### Sec 4.5 -- distinctness

Not applicable; this family did not become a finalist.

## Verdict

**REJECTED.** Fails sec 4.1 (2/5 assets beat DCA on wealth AND Sharpe,
need >=3/5, at both fee levels), sec 4.2 (DSR ~1.77e-42, raw pooled
excess Sharpe substantially negative), and sec 4.4 (only 11.1% of the
grid clears the majority bar, need >=66.7%; CSCV PBO=0.386, moderate).
Sec 4.3 not run per established precedent. Holdout not opened.

## Judgment calls made in this iteration

1. **Crisis-window date correction** (logged in `state/bugfix_log.md`):
   the initially-planned Sep-Dec 2008 calendar window for the required
   crisis-window verification did not show an elevated `avg_corr` on real
   data. Diagnosed as an estimator-lag effect (a trailing 126-day rolling
   correlation ending in Sep-Dec 2008 mostly reflects the run-up months,
   during which gold's flight-to-safety behavior and oil's crash-together
   behavior offset each other in the 3-leg pre-BTC average) rather than
   evidence the mechanism doesn't work, verified by inspecting the
   monthly `avg_corr` time series directly before adopting the corrected
   Dec 2008-Jun 2009 window -- caught and fixed BEFORE any grid result was
   computed or trusted, so no trial was affected.
2. **Cash-reserve-dynamics check restricted to the post-2000-08-30 era**
   for SP500 (logged in `state/bugfix_log.md`): a whole-92-year-history
   average dilutes any real cash-reserve effect toward zero by
   construction, since SP500's pre-2000 era is bit-for-bit DCA-identical
   (the correlation signal is undefined before 2 other core assets
   exist). Restricting the comparison to the era where the signal is
   actually live is the correct, non-cherry-picked way to ask whether the
   strategy meaningfully rebalances cash -- verified the restricted
   comparison (17.5% higher average cash) BEFORE trusting the grid, not
   after seeing a weak whole-history number and hunting for a fix.
3. **BTC's shorter history handled via a natural ">=2 valid legs"
   fallback**, not a shared, BTC-start-anchored calendar (family 043's
   portfolio-family approach). Each asset keeps its own full
   `load_dev()` history; the correlation signal itself degrades
   gracefully to neutral (`m_t=1.0`, bit-for-bit DCA) whenever fewer than
   2 of the other 4 core assets have started trading, rather than
   truncating any asset's history to BTC's 2014-2019 window. This
   preserves SP500's full ~92-year dev history and GOLD/SILVER/OIL's full
   ~19-year dev history, at the cost of a a long DCA-identical stretch
   for SP500's own pre-2000 era (documented as expected, not a bug).
4. **No-lookahead check extended to the cross-asset inputs**, a
   family-specific addition beyond the generic `checks.check_no_lookahead`
   (which only perturbs the primary asset's own data and would not catch
   a lookahead bug entering through the OTHER assets' price data feeding
   the correlation signal) -- written directly into the run script,
   following the precedent of family-specific check extensions logged in
   `state/bugfix_log.md`.
5. **Category filed as Regime switch (macro / credit / sentiment)**,
   matching the research queue's own categorization of idea #46 (a
   systemic-co-movement regime classification, structurally the same
   shape as this loop's other regime-switch families) despite the signal
   itself being price-only -- the required distinction from that whole
   family of priors is the INPUT (no external data at all), not the
   category.
