# Family 042 results: Realized-volatility term-structure (short-vs-long ratio) sizing

**Verdict: REJECTED.** The primary configuration **fails sec 4.1** (beats
DCA on wealth AND Sharpe on only **2 of 5** core assets at both fee
levels, need >=3/5), **fails sec 4.2** (DSR is essentially zero,
~1.29e-24), and **fails sec 4.4** decisively (only **5/36 (13.9%)**
grid configs clear the combined majority bar, far below the required
2/3). Per established loop precedent (e.g. families 006/007/023), sec 4.3
(rolling windows/bootstrap/placebo) was **not run** since sec 4.1 already
fails decisively. Holdout was **not** opened (not a finalist).

## Correction to the research queue's characterization of family 003

Idea #43's own queue entry (and this iteration's task brief) described
family 003 as "a single absolute realized-variance level, no term-
structure/ratio-of-two-windows component at all." On inspection of
`families/003-vol-managed-sizing/prereg.md` and
`src/backtest/v3/strategies/vol_managed_sizing.py`, **this is not
accurate**: family 003's own rule already computes `m_t =
clip(sigma_ref_t/sigma_recent_t, min_mult, max_mult)` -- a ratio of a
short (`vol_lookback_days`) and a long (`ref_lookback_days`) trailing
realized-vol window, i.e. already a short-vs-long ratio construction. This
is stated plainly in `prereg.md` rather than silently asserting a false
distinction. The genuine, verified distinction from family 003 that this
family relies on instead is in the FUNCTIONAL FORM applied to that ratio
(percentile-normalized vs. raw-ratio-clipped) plus a shorter short-window
grid (10-20 days vs. family 003's 20-60 days) -- see prereg.md's
"Rigorous distinction from family 003" section and the concrete
rank-reversal example below.

## Distinction-verification checks (both required by this iteration's brief, done first)

**Rank-reversal vs. family 003's raw-ratio-clip construction** (real GOLD
dev-period data, computed live before trusting any grid result):

| Date | Raw ratio | This family's own trailing percentile | Family-003-style multiplier (`clip(ratio,0.5,2.0)`) | This family's multiplier (`k=1.0,min_mult=0.5,max_mult=2.0`) |
|---|---|---|---|---|
| 2001-12-11 | 1.9743 (higher) | 0.500 (median) | **1.9744** (near max) | **1.000** (= plain DCA) |
| 2003-12-23 | 1.5340 (lower) | 1.000 (ceiling) | **1.5340** (moderate) | **2.000** (max) |

**Confirmed: genuine rank reversal** (family-003-style sizes 2001-12-11
above 2003-12-23; this family's percentile construction sizes them in the
exact opposite order).

**Ratio vs. single-window absolute level** (real GOLD data, 2009-02-23,
computed live): `sigma_short`=27.6% annualized, sitting at the **93rd
percentile** of its own history (a single-window level reading flags this
day as elevated/not-calm); yet `ratio_t`=1.153, whose own trailing
percentile is **1.0** (this family's signal flags the same day as the
single most "calm-relative-to-own-recent-past" reading of the year, because
the longer-run reference, `sigma_long`=31.8%, reflected the still-worse
GFC-crisis tail). **Confirmed: genuine divergence** -- the two statistics
rank the identical episode in opposite directions.

Both checks passed (`rank_reversal_confirmed: true`,
`ratio_vs_level_divergence_confirmed: true`), verifying this family's
signal is neither a re-parameterization of family 003 nor reducible to a
single-window absolute-vol-level rule.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Rank-reversal vs. family 003 (genuinely different, not a relabeling) | PASS |
| Ratio-vs-single-window-level divergence | PASS |
| Cash-reserve-dynamics check (reserve builds up vs. DCA; drawn down on high-multiplier weeks; meaningfully different from DCA's average) | PASS ($124.15 avg cash vs. DCA's $103.88; $144.14 on low-multiplier weeks vs. $104.89 on high-multiplier weeks) |
| Degenerate config (`enabled=False`) reproduces plain DCA exactly (bit-for-bit) | PASS |
| Second reference point: real `k=0.0` grid-shaped code path also reproduces plain DCA exactly | PASS |
| Cash and positions never negative (DCA baseline, primary config, aggressive grid corner) | PASS |
| Capital never exceeds cumulative deposits + interest (principled "never invest" ceiling bound, primary and aggressive corner) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (`t=6000`, `t=20000`) | PASS (both) |
| Point-in-time macro data | N/A -- price-only signal, no macro/ALFRED series at all |

## Pre-grid non-degeneracy sanity check

Confirmed on real development data for all 5 core assets before trusting
any grid result:

| Asset | Dev days | Frac. multiplier == 1.0 | Std(multiplier) | Non-degenerate? |
|---|---|---|---|---|
| SP500 | 23,109 | 2.46% | 0.524 | PASS |
| GOLD | 4,848 | 10.81% | 0.497 | PASS |
| SILVER | 4,850 | 10.72% | 0.505 | PASS |
| BTC | 1,932 | 26.50% | 0.447 | PASS |
| OIL | 4,857 | 10.67% | 0.498 | PASS |

All 5 assets show real dispersion in the multiplier, well below the 90%
"stuck at 1.0" threshold -- no availability caveat here (unlike VIX-based
families 016/025/041), since this signal is price-only and available for
each asset's full development window (minus the fixed 252-day warm-up).

## Primary configuration: `short_window=20, ts_lookback=252, k=1.0, min_mult=0.5` (`long_window=252, max_mult=2.0, max_lump_multiple=3.0` fixed)

### Sec 4.1 result (vs. plain per-asset DCA), development windows, 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.27128 | 85.27722 | 0.153067 | 0.153097 | NO (loses both, razor-thin) |
| GOLD | 2.23124 | 2.23123 | 0.504940 | 0.504917 | **YES** (razor-thin) |
| SILVER | 1.68667 | 1.68666 | 0.319673 | 0.319677 | NO (wins wealth, loses Sharpe, razor-thin) |
| BTC | 9.85090 | 9.85568 | 1.067182 | 1.067309 | NO (loses both) |
| OIL | 1.18027 | 1.17986 | 0.227897 | 0.227824 | **YES** |

At 0.1% fees: **2/5** assets beat DCA on both wealth AND Sharpe (GOLD,
OIL). At 0.25% fees: also **2/5**, same pattern. **Sec 4.1: FAIL** at both
fee levels (need >=3/5). Every margin is small, consistent with a
pure-timing reallocation of a fixed deposit stream rather than a change in
total capital deployed -- the same "razor-thin margins" pattern seen in
several other rejected/near-miss sizing families in this loop.

### Grid diagnostic (sec 4.4)

**Only 5 of 36 configurations (13.9%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets, 0.1% fee) -- far **below** the 2/3 (24/36)
requirement. **Sec 4.4: FAIL**, decisively -- one of the weakest grid
results in this loop so far (comparable to family 023's 3.1%). The
strongest arms cluster around `short_window=15-20, k>=1.0-1.5` (cfg14-16,
22, 28, 33, 35 each reach 3/5), but even these never exceed 3/5, and no
combination reaches 4/5 or 5/5 anywhere in the grid.

CSCV probability of backtest overfitting (36-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.571** -- the
highest (most overfitting-prone) PBO of any family in this loop so far,
consistent with the grid's own weak and inconsistent pattern (no config
dominates; the ranking of "best" configs is unstable across resamples).

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series
  (equal-weight average of the 5 per-asset excess series): **-0.01101/
  week** (annualized ~-7.94%) -- **negative**, unlike most prior
  continuous-multiplier sizing families in this loop, with extreme negative
  skew (-10.10) and kurtosis (400.9), signaling a small number of large
  negative excess-return episodes dominate the pooled series.
- `N` (raw trial count, whole-loop pool): **1,293** (196 seeded + 1,061
  through family 041 + 36 new from this family's grid).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **128**
  clusters (unchanged from family 041 -- this family's 36 grid configs
  did not open any new cluster distinct from the existing 128).
- **DSR (N_eff-based): 1.289e-24** -- essentially zero, decisively below
  the SR0 threshold (SR0=0.1284/week) this loop's accumulated trial count
  now demands, and made moot by the negative raw Sharpe itself.
- DSR (raw-N, conservative reference): 5.789e-26.

**Sec 4.2: FAIL**, decisively -- the pooled excess-return Sharpe is
negative, not merely too small.

## Assessment summary

| Check | Result | Pass? |
|---|---|---|
| Sec 4.1 (beats DCA >=3/5, both fees) | 2/5 at both fees | FAIL |
| Sec 4.2 (DSR >= 0.95) | 1.29e-24 (N_eff), 5.79e-26 (raw N); raw pooled Sharpe negative | FAIL |
| Sec 4.3 (rolling/bootstrap/placebo) | not run (sec 4.1 already decisively fails, per established precedent) | n/a |
| Sec 4.4 (>=2/3 of grid beats DCA majority) | 5/36 (13.9%) | FAIL |

**Verdict: REJECTED.** Logged, not promoted. Holdout not opened, per sec
5.4.

## Interpretation

Unlike family 041 (a near-miss that at least cleared sec 4.1 with a 4/5
pass before failing every downstream robustness check), this family fails
even the most basic sec 4.1 bar, and does so with a NEGATIVE pooled
excess-return Sharpe -- a more decisively negative result than most prior
"razor-thin margins" families in this loop. The grid diagnostic (13.9%,
the second-weakest of any family after family 023's 3.1%) and the highest
CSCV PBO (0.571) recorded in this loop together suggest the primary
config's specific parameter choice sits in an unlucky corner of a broadly
weak and unstable signal, not that a different primary would have fared
much better -- the strongest grid arms (short_window=15-20, k>=1.0)
plateau at 3/5, never reaching the 4/5+ level several near-miss families in
this loop achieved. A plausible economic reading: the percentile-
normalization step this family adds over family 003's raw-ratio-clip
(intended to make "unusually calm" adaptive per-asset) may, in practice,
amplify noise rather than signal -- ranking a moderate absolute ratio
value as "extreme" whenever it happens to be the most extreme reading
within a comparatively short recent history (as the 2003-12-23 example
above illustrates), which is a much noisier basis for sizing than family
003's fixed absolute thresholds, even though it is a genuinely different
(not merely re-parameterized) construction.

## Judgment calls

1. **Distinction from family 003 required an honest correction, not a
   restated assertion**: the seed queue's characterization of family 003
   as "a single absolute level" does not match family 003's actual
   pre-registered and implemented rule (a raw short-vs-long ratio,
   clipped directly). This family's real distinguishing feature is the
   percentile-normalization layer applied to that ratio (plus a shorter
   short-window grid), verified via a concrete rank-reversal example on
   real data, not the presence/absence of a ratio construction itself.
2. **Functional form: continuous percentile-scaled multiplier** (matching
   families 030/031/036/039/040/041's construction), not a discrete
   ladder, per this iteration's explicit instruction -- verified directly
   via the cash-reserve-dynamics check rather than merely asserted, and
   every grid cell's `min_mult` is asserted <1.0 at import time.
3. **Estimator choice**: plain close-to-close log-return realized vol
   (identical to family 003's estimator), not the Parkinson range
   estimator (family 035) -- a deliberate choice to isolate the
   term-structure-ratio/percentile-normalization idea from the separate
   estimator-choice axis family 035 already explores.
4. **`long_window` and `max_mult` fixed, not grid-varied**, to keep the
   family at 4 tunable parameters (short_window, ts_lookback, k, min_mult)
   under the plan's <=5 ceiling, per the same convention family 041 used
   for its own fixed `max_lump_multiple`.
5. This result adds a second REJECTED "Volatility targeting" data point
   (alongside families 003/035/039) to this loop's now-large set of
   realized/implied-volatility-based timing signals that have failed to
   clear sec 4.1, and is a more decisive negative than several of them
   (negative pooled Sharpe, highest CSCV PBO in the loop).
