# Family 039 results: Realized-kurtosis (fat-tail) sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1: only
**2 of 5** core assets (SILVER, OIL) beat DCA on final wealth AND Sharpe,
at both fee levels (need >=3/5). Sec 4.4's grid diagnostic also fails
(11/24, 45.8%; need >=2/3 = 16/24). DSR is effectively zero. Sec 4.3
(rolling windows/bootstrap/placebo) was **not** run, per the loop's
established time-budget convention (§4.3 only run if §4.1 passes).
Holdout was **not** opened (not a finalist).

## Category and required distinction from family 023 (realized skewness)

Filed as **Volatility targeting**. This is the closest pair of families
in the loop so far -- both trailing-window, price-only, higher-
standardized-moment signals of an asset's own return distribution's
shape. The required rigorous distinction (full mechanism-level argument
in `prereg.md`):

- **Family 023 (realized skewness, 3rd moment):** measures **asymmetry**
  (has a sign; a series and its sign-flipped mirror have equal-magnitude,
  opposite-signed skewness).
- **Family 039 (this family, realized kurtosis, 4th moment):** measures
  **tail thickness relative to Normal, direction-blind by construction**
  (a series and its sign-flipped mirror have **identical** kurtosis,
  since the 4th power is always non-negative).

**Concrete numeric divergence example** (constructed, computed live by
the run script, not hand-copied):

| Window | Construction | Skewness | Excess kurtosis |
|---|---|---|---|
| Path A | 18 days of 0.0% + one +6.0% day + one -6.0% day (symmetric outliers, mean exactly 0) | **0.0** (exactly) | **+7.0** |
| Path B | 16 days of -0.5% + 4 days of +2.0% (moderate one-sided tilt, no extreme outlier) | **+1.50** | **+0.25** |

Path A has zero skew but 28x Path B's excess kurtosis; Path B has a
strong, unambiguous skew reading but a near-Normal kurtosis reading. The
two statistics' rankings of these two windows are exactly inverted --
neither can substitute for the other.

**Real-data crash-episode spot-check** (SP500 dev data, 90-day trailing
window, strictly pre-2020): 90-day trailing excess kurtosis **peaks at
56.04 on 1987-10-19 itself (Black Monday)**, against a 2017 calm-year
median of only **3.00** -- an 18.7x spike, confirming the statistic
correctly identifies a real historical fat-tail/crash episode before the
grid was trusted.

## Brief distinction from families 003 (variance) and 031 (mean/vol ratio)

Family 003's realized variance (2nd moment) is pure dispersion with zero
shape information -- it cannot distinguish a calm series with two rare
huge outliers (high kurtosis) from an evenly dispersed series with the
same total squared deviation (low kurtosis). Family 031's Kelly-Sharpe
statistic is a mean/vol ratio with no higher-moment component at all --
two series with identical mean and variance but very different tail
behavior give family 031 (and family 003) identical signals, but very
different signals to this family.

## Pre-grid sanity checks

Non-degeneracy (primary config, all 5 core assets): multiplier
`frac_at_1.0` ranges 1.9%-17.8% and `std_multiplier` ranges 0.48-0.53
across all 5 assets -- comfortably non-degenerate.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Skew/kurtosis divergence example confirmed live (Path A/B, rankings invert) | PASS |
| Kurtosis crash-episode sign/magnitude spot-check (1987-10-19 peak, 18.7x calm-year median) | PASS |
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Second reference point: real `k=0.0` grid-shaped code path also reproduces plain DCA bit-for-bit | PASS |
| Cash and positions never negative (DCA, primary, aggressive grid corner) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (principled never-invest ceiling bound) | PASS |
| No-lookahead perturbation test (`t=6000`, `t=20000`) | PASS |
| `PRIMARY_CONFIG` is a member of `grid_configs()` (import-time assertion) | PASS |
| Every grid cell's `min_mult` < 1.0 (import-time assertion, per families 014/033/037's lesson) | PASS |
| Cash-reserve dynamics: average cash exceeds DCA baseline (123.53 vs 103.88) and is drawn down further on high-multiplier/depressed-kurtosis weeks (104.32) than banked on low-multiplier/elevated-kurtosis weeks (143.25) | PASS |
| No dev-period check references a date on/after 2020-01-01 or an unseen ticker (crash spot-check uses 1987 and 2017; divergence example uses no real dates at all) | PASS |

## Primary configuration: `kurt_window=90, pctile_lookback=252, k=1.0, min_mult=0.5` (`max_mult=2.0, max_lump_multiple=3.0` fixed)

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.27327 | 85.27722 | 0.15312 | 0.15310 | NO (wealth loses, Sharpe wins narrowly) |
| GOLD | 2.23116 | 2.23123 | 0.50488 | 0.50492 | NO (loses both, razor-thin) |
| SILVER | 1.68683 | 1.68666 | 0.31972 | 0.31968 | **YES** (razor-thin on both) |
| BTC | 9.84729 | 9.85568 | 1.06699 | 1.06731 | NO (loses both, razor-thin) |
| OIL | 1.18039 | 1.17986 | 0.22791 | 0.22782 | **YES** (both win) |

**Sec 4.1: FAIL** -- 2/5 core assets at both fee levels (need >=3/5,
identical count at 0.25% fees). Every margin, winning or losing, is
economically negligible (well under 0.1% on wealth for every asset) --
this primary config's continuous multiplier produces only a very mild
re-timing effect on net wealth/Sharpe in either direction, consistent
with `k=1.0`/`min_mult=0.5` being a moderate (not extreme) setting on
this statistic's own percentile scale.

### Grid diagnostic (sec 4.4)

**11 of 24 configurations (45.8%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees -- need >=2/3 (16/24). The
strongest grid corners use gentler sensitivity (`k=0.5`, both
`pctile_lookback` values, both `min_mult` values reach 4/5 at
`kurt_window=60` or `kurt_window=90` with `pctile_lookback=504`); higher
`k` (1.0, 1.5) mostly underperforms, including the primary config's own
`k=1.0` corner. CSCV PBO = **0.443** (moderate-high, among the higher
values in this loop, reflecting a continuous, non-bimodal grid-
performance surface with real disagreement between low-`k` and high-`k`
regions).

### Sec 4.2: Deflated Sharpe Ratio -- FAIL (reported for completeness)

- `N_eff = 126` (raw `N = 1185`, seed 196 + new 989 = 1185, matching
  `state/trial_counter.json`'s updated `new: 989` = 965 (through family
  038) + 24 (this family's grid)).
- DSR (N_eff-based): **~1.62e-22** (effectively zero). Raw pooled
  excess-return Sharpe is **-0.00775/week** (annualized ~-5.59%), with
  extreme negative skew (-6.17) and kurtosis (349.7) -- the pooled
  excess-return series itself is dominated by a handful of large,
  asymmetrically-timed drawdowns relative to DCA, an ironic but
  mechanically unsurprising feature for a family built on a fat-tail
  statistic.
- DSR (raw-N, conservative reference): **~7.50e-25**.

### Sec 4.3: not run in full

Sec 4.1 failed (2/5, need >=3/5), so sec 4.3's rolling-window, bootstrap
and placebo legs were skipped per established loop precedent (families
006/007/008/011/013/014/018/021/023/024/028/029/030/031/033/036/037/038
and others: sec 4.3 is reserved for configurations that at least clear
the sec 4.1 bar).

## Assessment summary

| Check | Result | Pass? |
|---|---|---|
| Sec 4.1 (beats DCA >=3/5, both fees) | 2/5 at both fees | FAIL |
| Sec 4.2 (DSR >= 0.95) | ~1.62e-22 (N_eff), ~7.50e-25 (raw N) | FAIL |
| Sec 4.3 (rolling/bootstrap/placebo) | not run (sec 4.1 gate not cleared) | N/A |
| Sec 4.4 (>=2/3 of grid beats DCA majority) | 11/24 (45.8%) | FAIL |

**Verdict: REJECTED.** Logged, not promoted to finalist or near-miss (sec
4.1 fails outright at the minimum threshold, 2/5, and every per-asset
margin -- winning or losing -- is economically negligible). Holdout not
opened, per sec 5.4.

## Judgment calls

1. **Design choice: continuous percentile-multiplier (family 036's
   functional form, sign-inverted) rather than a discrete tier ladder**,
   to keep the reserve-banking mechanism automatically safe from the
   014/033/037 cash-cap-nullification failure mode without relying on a
   single discrete "otherwise" tier -- verified directly via the
   cash-reserve-dynamics check (average cash exceeds DCA baseline and is
   drawn down more on boost weeks than on reduce weeks) rather than
   merely asserted. Every grid cell's `min_mult` is also asserted < 1.0
   at import time as an explicit belt-and-suspenders check.
2. **Kurtosis window mirrors family 023's own primary `skew_window=90`**
   choice, specifically to keep the two higher-moment families' window
   lengths comparable when contrasting them, per this iteration's task
   instruction.
3. **Standard demeaned excess-kurtosis formula** (not an un-demeaned
   scale-invariant variant analogous to family 023's Neuberger skewness
   formula) was used, since kurtosis has no equivalent scale-invariance
   shortcut and the mainstream realized-kurtosis literature (Bali-Cakici-
   Whitelaw) uses the demeaned form -- documented explicitly in
   `prereg.md`'s exact-rules section as a deliberate departure from
   family 023's formula choice, not an oversight.
4. This result adds a further data point (after families 003/030/031/
   034/035/036/037) to this loop's now-consistent finding that a
   continuous, price-only, single-asset trailing-statistic sizing signal
   applied identically across all 5 core assets tends to produce thin,
   inconsistently-signed sec 4.1 margins in this development sample --
   here the margins are smaller in magnitude than almost any prior
   family's (every per-asset win or loss is under 0.1% on wealth),
   suggesting the fourth-moment kurtosis signal, at the primary config's
   moderate sensitivity, carries essentially no economically meaningful
   information beyond noise for this loop's re-timing mechanism, distinct
   from (and weaker than) family 023's own skewness signal, which showed
   larger (if still ultimately rejected/near-miss-level) per-asset
   margins in its own results.
