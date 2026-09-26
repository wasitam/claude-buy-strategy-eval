# Family 038 results: Consumer-sentiment contrarian regime

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively:
only **1 of 5** core assets (SP500, and only barely) beat DCA on final
wealth AND Sharpe, at either fee level. Sec 4.4's grid diagnostic also
fails (8/24, 33.3%, clear the majority bar; need >=2/3 = 16/24). DSR is
effectively zero. Sec 4.3 (rolling windows/bootstrap/placebo) was **not**
run in full, per the loop's established time-budget convention (§4.3 only
run if §4.1 passes). Holdout was **not** opened (not a finalist).

## Scoping recap: idea #37 skipped, idea #39 taken instead

This iteration's task brief named idea #37 (overnight/intraday return-
split sizing) next, but flagged it as closely related to family 026
(already tested, REJECTED) and required a careful comparison before
proceeding. Full reasoning in `prereg.md`'s "Scoping decision" section;
summary: idea #37 as worded uses the **identical** Open/Close overnight-
vs-intraday decomposition and the **identical** relative-spread
comparison (overnight leg's trailing cumulative performance relative to
intraday's) that family 026 already tested to rejection, with the same
qualitative elevated-buy-more/otherwise-buy-less-or-normal sizing shape.
None of the task brief's suggested potential distinctions (a ratio instead
of a spread, a different window, a different asset scope, a different
sign convention) are actually present in idea #37 as stated -- they were
offered as hypothetically available paths to a distinction, not features
already built into #37. Constructing one of them now, after already
knowing family 026's exact construction and result, would be exactly the
kind of after-the-fact relabeling this loop's holdout/closed-family
discipline warns against, applied here by analogy to the loop's own prior
family. **Decision: idea #37 skipped entirely**, documented in
`state/research_queue.md` and `prereg.md`, per the task brief's option (b).
Idea #39 (consumer-sentiment contrarian regime) was taken as the
substitute, chosen over #40 (realized-kurtosis sizing) and #41 (rolling
Sortino-ratio sizing) as the most clearly distinct option: a macro/
sentiment regime-switch family built from a genuinely new data source
(a household-survey index), rather than another price-only single-asset
higher-moment sizing rule in a category (Sizing / valuation and
Volatility targeting via price-only trailing statistics) this loop has
already tested repeatedly (families 003, 005, 023, 030, 031, 034, 035,
036, 037).

## Category and the fivefold macro/sentiment distinction

Filed as **Regime switch (macro / credit / sentiment)**. This loop now has
7 regime-type families (v2.1 Strategy D, families 011, 016, 019, 027, 032,
and this one), each built from a genuinely different data source and
transmission channel -- full table in `prereg.md`. This family is the
first to use `UMCSENT`, the University of Michigan Consumer Sentiment
Index, a **household-survey** measure with no direct link to option
prices, credit spreads, policy rates, the yield curve, or the money
supply, and no shared input series with any of the other 6 families.

## Data reachability

`UMCSENT` confirmed live-reachable via `fetch_fred_macro()` (same
`fredgraph.csv` mechanism families 011/019/027/032 already use): 676
monthly observations, 1952-11-01 through the present. A conservative
**35-calendar-day** publication lag is applied (shorter than family 032's
45-day M2 lag, since both UMCSENT's preliminary and final readings land
within the reference month itself, unlike M2's post-month-end release).

## Pre-grid sanity checks

1. **Non-degeneracy** (primary config, all 5 core assets):

| Asset | Dev days | Euphoric days | Frac. euphoric |
|---|---|---|---|
| SP500 | 23,109 | 4,282 | 18.53% |
| GOLD | 4,848 | 1,211 | 24.98% |
| SILVER | 4,850 | 1,211 | 24.97% |
| BTC | 1,932 | 1,640 | **84.89%** |
| OIL | 4,857 | 1,217 | 25.06% |

All comfortably inside the (2%, 98%) sanity band. BTC's much higher
euphoric fraction is a direct, mechanical consequence of its short
2014-2019 development window overlapping a sustained multi-year period of
historically elevated `UMCSENT` readings (the post-2010s expansion),
not a bug -- flagged here as a real limitation this family inherits from
BTC's already-known short development sample (plan sec 5.1/12).

2. **Known-episode check (Jan-2000 dot-com-era euphoria, strictly within
   dev dates):** the primary config's z-score reading over 1999-06-01
   through 2000-05-31 (12 monthly observations, the well-documented
   consumer-confidence peak just before the dot-com crash) reads **100%**
   euphoric, with the z-statistic at 1.4887 at the window's start, peaking
   at 1.7533, and 1.4347 at the window's end -- correctly identifying this
   well-known sentiment-euphoria episode before the grid was trusted.
   **PASS.**

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (cash never negative under the engine's cash-capped fill logic) | PASS |
| No-lookahead perturbation test (`t=6000`, `t=20000`) | PASS |
| Point-in-time macro: 35-day lag actually changes some regime readings vs. 0-day lag (4.27% of days differ) -- not a no-op | PASS |
| `PRIMARY_CONFIG` is a member of `grid_configs()` (asserted at import time) | PASS |
| No dev-period check references a date on/after 2020-01-01 or an unseen ticker (Jan-2000 known-episode check is two decades pre-holdout) | PASS |

Note: this family has no ladder-style "otherwise multiplier" at all -- its
non-euphoric arm is a full-deploy-plus-catch-up-lump rule (structurally
the same shape as families 019/032's already-validated "accelerating/
normal" arm), so the near_high_mult-style cash-cap-nullification failure
mode that hit families 014/033/037 does not apply here: the "otherwise"
arm is deliberately the MOST aggressive arm, not a passive near-1.0x arm.
Confirmed directly: the primary config's per-asset results below are NOT
identical to DCA (unlike 014/033/037's primary configs), so no
nullification occurred.

## Primary configuration: `normalization_method=zscore, lookback_years=10, threshold_level=1, euphoric_tilt_fraction=0.0`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.29010 | 85.27722 | 0.15311 | 0.15310 | **YES** (razor-thin on both) |
| GOLD | 2.20944 | 2.23123 | 0.52296 | 0.50492 | NO (wealth loses) |
| SILVER | 1.68240 | 1.68666 | 0.33484 | 0.31968 | NO (wealth loses) |
| BTC | 4.99749 | 9.85568 | 0.90335 | 1.06731 | NO (loses both, badly) |
| OIL | 1.16453 | 1.17986 | 0.23586 | 0.22782 | NO (wealth loses) |

**Sec 4.1: FAIL** -- 1/5 core assets at both fee levels (need >=3/5). The
same 1/5 count holds at 0.25% fees. BTC's underperformance is severe (a
~49% relative wealth shortfall) and mechanically explained: BTC's own
development window sits almost entirely inside a historically
high-`UMCSENT` era, so the primary config's euphoric/bank-and-catch-up
rule spends 84.9% of BTC's development weeks banking cash instead of
buying, missing most of BTC's development-period appreciation. SP500's
"win" is a razor-thin numerical edge (0.015% on wealth, 0.0001 on Sharpe),
not a meaningful margin.

### Grid diagnostic (sec 4.4)

**8 of 24 configurations (33.3%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees -- need >=2/3 (16/24). The best
single configs reached 4/5 (`percentile` normalization, `lookback_years=5`,
higher thresholds), but the primary config's own `zscore`/`lookback_years=10`
corner underperforms most of the grid. CSCV PBO = **0.214** (moderate;
higher than family 032's 0.0-style degenerate grids, reflecting this
family's more continuous, non-bimodal grid-performance surface).

### Sec 4.2: Deflated Sharpe Ratio -- FAIL (reported for completeness; not required once sec 4.1 fails)

- `N_eff = 123` (raw `N = 1161`, seed 196 + new 965 across all families
  tested through this family: `196 + 941 (through family 037) + 24 (this
  family) = 1161`, sanity-checked against `state/trial_counter.json`'s own
  updated `new: 965`).
- DSR (N_eff-based): **~9.4e-26** (effectively zero). Raw pooled
  excess-return Sharpe is **-0.0297/week** (annualized ~-21.4%), with
  extreme skew (3.09) and kurtosis (167.9) driven by BTC's large, rare,
  and asymmetrically-timed excess-return swings.
- DSR (raw-N, conservative reference): **~4.5e-28**.

### Sec 4.3: not run in full

Sec 4.1 failed decisively (1/5, need >=3/5), so sec 4.3's rolling-window,
bootstrap and placebo legs were skipped per established loop precedent
(families 006/007/008/011/013/014/018/021/023/024/028/029/030/031/033/
036/037 and others: sec 4.3 is reserved for configurations that at least
clear the sec 4.1 bar).

## Assessment summary

| Check | Result | Pass? |
|---|---|---|
| Sec 4.1 (beats DCA >=3/5, both fees) | 1/5 at both fees | FAIL |
| Sec 4.2 (DSR >= 0.95) | ~9.4e-26 (N_eff), ~4.5e-28 (raw N) | FAIL |
| Sec 4.3 (rolling/bootstrap/placebo) | not run (sec 4.1 gate not cleared) | N/A |
| Sec 4.4 (>=2/3 of grid beats DCA majority) | 8/24 (33.3%) | FAIL |

**Verdict: REJECTED.** Logged, not promoted to finalist or near-miss (sec
4.1 itself fails outright -- only 1/5, and even that one asset's margin is
economically negligible). Holdout not opened, per sec 5.4.

## Judgment calls

1. **Idea #37 was skipped this iteration** (rather than tested) after a
   rigorous, honest side-by-side comparison against family 026 found it
   mechanically identical, not materially different -- documented fully
   in `prereg.md` and `state/research_queue.md`. This is the loop's first
   time a queued idea has been skipped entirely rather than tested or
   quietly re-parameterized; the reasoning is recorded for the final
   report's "what didn't get tested and why" section.
2. **Primary configuration chosen before any grid result was seen**
   (`zscore`, `lookback_years=10`, `threshold_level=1`,
   `euphoric_tilt_fraction=0.0`), matching families 019/032's own primary-
   selection reasoning for the analogous parameters. Per sec 4.4, no grid
   arm can be substituted for the primary regardless of the grid's own
   stronger-looking corners (e.g. `percentile`/`lookback_years=5`/
   `threshold_level=2`, which reached 4/5) -- the loop never switches to a
   better-looking configuration after seeing results.
3. **BTC's short development window interacting with a historically
   high-sentiment era is a genuine, mechanically-diagnosed limitation**,
   not a bug: with `UMCSENT` reading euphoric 84.9% of BTC's development
   weeks, the primary config's banking mechanic spent most of BTC's
   development period out of the market during one of its strongest
   appreciation stretches. This is a specific instance of the general BTC-
   short-development-window caution the plan (sec 5.1/12) and this loop's
   prior macro/regime families (011/019/027/032) have already flagged,
   here manifesting as a directly observable large-magnitude effect rather
   than just added noise.
4. This result adds a further data point (after families 011/019/027/032)
   to this loop's now-consistent finding that a single shared macro/
   sentiment regime signal, applied identically across all 5 core assets,
   tends to produce thin, inconsistently-signed per-asset sec 4.1 margins
   in this development sample -- consistent with the broader pattern this
   loop has documented across price-only trailing-statistic sizing
   families as well (families 003/014/030/031/034/035/036/037).
