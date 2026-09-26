# Family 052 results: ISM Manufacturing PMI regime deposit sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively
(beats DCA on wealth AND Sharpe on **0/5** core assets, need >=3/5, at
both fee levels -- it loses on wealth on every asset and wins Sharpe on
only one, OIL). The grid diagnostic fails just as decisively (0/24, 0%,
of the configurations reach the majority-of-assets bar, need >=2/3). DSR
is effectively zero. Holdout was **not** opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family across all 5 core assets**
(independently per asset, sec 4.1's standard >=3/5 rule), following the
precedent families 006/007/011/015/019/032/050 set for an asset-agnostic
macro/survey signal. Category: **Regime switch (macro / credit /
sentiment)**.

## Required step 1: data reachability (verified live before any design work)

FRED's historical `NAPM` mnemonic for the ISM Manufacturing PMI, and
every other plausible mnemonic tried (`NAPMPMI`, `NAPMPI`, `NAPMNOI`,
`NAPMEI`, `NAPMSDI`, `NAPMPRI`, `NAPMII`, `NAPMBI`, `NAPMEXI`, `NAPMIMP`,
`ISM_MAN_PMI`, `ISM`), returned **404 Not Found**. A live FRED site
search for "ISM Manufacturing PMI" returned **"Displaying 0 series"** --
confirming the task brief's own stated expectation that FRED discontinued
direct redistribution of the ISM PMI (reportedly ~2016, over ISM
licensing). `MANEMP` (manufacturing employment level, a hard-data
headcount, not a survey diffusion index) is reachable but is not a
substitute. Alternative live sources were then investigated and all
confirmed unreachable: DBnomics's API (`403`/`EGRESS_BLOCKED`),
`forecasts.org`, `eco3min.fr`, `ycharts.com` and `multpl.com` (all
`EGRESS_BLOCKED` by this session's network egress proxy).

**Resolution, per the task's explicit allowance for this exact
contingency (family 051's hard-coded FOMC-calendar precedent):** the
development-period-only (1948-2019) monthly PMI level is **reconstructed
from this session's own training-era knowledge**, using anchor points at
specific, well-documented historical levels/turning points with monthly
values between anchors linearly interpolated -- never independently
recalled month by month. This is hard-coded directly in
`src/backtest/v3/strategies/ism_pmi_regime.py` (`ANCHORS`), not in a
`data/*.csv` file (which is gitignored as a live-fetch cache directory in
this repo). **Disclosed limitation:** confidence is materially higher for
1990-2019 (closer to this session's higher-fidelity macro-narrative
knowledge) and materially lower for 1948-1989 (a stylized cyclical
reconstruction keyed to NBER recession/expansion dates rather than
remembered specific prints) -- read any pre-1990 SP500/GOLD/SILVER
dev-period result with this in mind. A documentation-only CSV of the
reconstructed series is at
`families/052-ism-pmi-regime/ISM_PMI_reconstructed_for_review.csv`.

## Required step 2: point-in-time / publication-lag handling

The ISM releases month M's PMI on the first business day of month M+1
(~32 calendar days after the reference month's 1st). A conservative
**35-calendar-day publication lag** is applied to every reconstructed
observation before it is usable in the backtest, verified to actually
matter (not a no-op): shortening the lag to 0 days changes the regime
reading on **3.83%** of SP500 trading days vs. the documented 35-day lag.

## Required step 3: concrete real dev-period divergence from family 019 (OECD CLI)

Both episodes below were checked against family 019's own **live-fetched**
`USALOLITONOSTSAM` FRED series (not asserted from memory) before this
family's prereg.md was written.

**2019 trade-war manufacturing slowdown (timing divergence, the
dev-period-ending episode):** the OECD CLI's own trough in this episode
falls in **September 2019** (98.961) and is **already rising** by
December 2019 (99.156, three straight months up) -- while the
reconstructed ISM PMI has **not yet turned** by the dev-period's own
final month, continuing to fall through December 2019 (~47.2, its lowest
reconstructed reading of the whole episode). A narrower, manufacturing-
concentrated slowdown (crossing into outright PMI "contraction" in
August 2019) against a broader, smoothed composite that barely dips and
has already resumed rising.

**1998 Asian-financial-crisis episode (magnitude divergence):** the OECD
CLI's entire 1998 dip is under 1.1 index points (99.78 low vs. 100.87
peak, a mild wobble), while the reconstructed PMI swings into outright
survey-defined contraction (~46-47) over the same months -- the acute
export/manufacturing-specific shock registered far more sharply in the
single manufacturing survey than in the broader, smoothed composite.

Brief distinctions from families 011/050 (credit spreads, no
manufacturing-survey content) and 027 (`T10Y2Y` term-structure slope, not
a survey) also documented in prereg.md.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`) reproduces plain DCA exactly (bit-for-bit) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (principled ceiling bound) | PASS |
| No-lookahead: perturbing all data after day t leaves every order on/before t unchanged (t=6000) | PASS |
| No-lookahead, second spot-check deep into the sample (t=20000) | PASS |
| Point-in-time macro: shortening the documented 35-day publication lag to 0 days changes SOME historical regime readings, proving the lag isn't a no-op | PASS -- 3.83% of SP500 trading days differ |

**Judgment call documented in prereg.md before implementation** (families
010/011/019/032/050's degenerate-config-trap precedent): a grid config
with `weak_tilt_fraction=0` and `enabled=True` is **not** the degenerate
DCA case, because the regime/percentile/persistence computation still
runs. Only `enabled=False` (which bypasses that computation entirely) is
the true degenerate case, and that is what the implementation check above
verifies.

## Pre-grid sanity checks (all passed)

**Non-degeneracy:** the primary configuration's `weak` flag fires
non-trivially on every core asset -- SP500 25.1%, GOLD 29.6%, SILVER
29.6%, BTC 28.2%, OIL 29.6% of dev days (all comfortably inside the (2%,
98%) sanity band).

**Known-episode check (strictly within dev dates):** the primary
configuration's regime reading during Sep 2008-Mar 2009 (the post-Lehman
manufacturing collapse, the most severe well-known ISM episode) reads
**weak 100.0%** of the window (reconstructed PMI fell from 43.5 to 39.2,
min 32.9) -- confirming the signal construction correctly identifies the
well-known ISM collapse before any grid result was trusted.

## Primary configuration: `lookback_years=10, weak_pctile=30, weak_tilt_fraction=0.0, persistence_months=1` (`max_lump_multiple=6` fixed)

### Per-asset result (vs. plain DCA), at 0.1% fees

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 84.4733x | 85.2772x | 0.15239 | 0.15310 | NO (loses both, razor-thin) |
| GOLD | 2.1907x | 2.2312x | 0.4895 | 0.5049 | NO (loses both) |
| SILVER | 1.6703x | 1.6867x | 0.3281 | 0.3197 | NO (loses wealth) |
| BTC | 8.7841x | 9.8557x | 1.0326 | 1.0673 | NO (loses both) |
| OIL | 1.1506x | 1.1799x | 0.2469 | 0.2278 | NO (loses wealth) |

At 0.25% fees the picture is unchanged: the primary loses wealth on all
5 assets and wins Sharpe only on OIL (0.2457 vs. 0.2263). **sec 4.1:
0/5 at both fee levels -- decisive FAIL** (need >=3/5).

## sec 4.2: Deflated Sharpe Ratio

Pooled excess-return series (weekly, equal-weight average across the 5
assets): raw Sharpe **-0.00924/week** (-6.66%/yr annualized), skew
+1.55, kurtosis 171.7 (fat right tail driven by the rare large catch-up
lumps, similar in shape to several prior rejected regime families).

- **N_eff-based DSR: 1.24e-22** (N_eff = 134, out of raw N = 1,555 total
  trials -- seed 196 + new 1,359).
- **Raw-N DSR: 7.37e-22** (N = 1,555).

Both are effectively zero. **sec 4.2 FAIL.**

## sec 4.4: grid robustness (diagnostic)

24 configurations (`lookback_years` x `weak_pctile` x
`weak_tilt_fraction` x `persistence_months` = 2x3x2x2). **0/24 (0%)**
configurations reach the majority-of-assets bar (need >=3/5 assets
beating DCA on both wealth and Sharpe at 0.1% fees) -- need >=2/3 for a
pass. The best any single config achieved was 1/5 assets (several
configs, mostly the `weak_pctile=20` and `weak_tilt_fraction=0.25`
corners, which move closer to plain DCA by construction). This is one of
the weakest grid outcomes of any family in this loop so far, tied with
families 047 (0/36), 048 (0/18) and 051 (0/16). **sec 4.4 FAIL.**

**CSCV PBO = 0.386** (probability of backtest overfitting, on the
SP500-only weekly-return grid, 8 splits, 70 combinations) -- middling
among this loop's rejected families (neither the lowest like family
051's 0.0, nor the highest like family 047's 0.857), consistent with a
grid that has some genuine but weak and inconsistent directional
structure (the `weak_pctile=20` block is uniformly slightly less bad than
the `weak_pctile=30`/`40` blocks) rather than pure noise.

## sec 4.3: not run

Per this loop's established time-boxing precedent (families
044/046/047/048/049/050/051), sec 4.3 (rolling windows, block bootstrap,
placebo circular-shift) is **not run**, since sec 4.1 already fails
decisively (0/5, the worst possible outcome) and sec 4.4 also fails
decisively (0/24). This is logged honestly as a gap, not a fabricated
result.

## Trial accounting sanity check

`state/trial_counter.json`: `seed=196` (unchanged), `new` went from 1335
-> **1359** (+24, one row per grid config), `families_new` went from 49
-> **50** (+1). `_run_output.json`'s `n_total_raw` = 1,555 = seed (196) +
new (1,359), matching exactly. `n_eff` = 134.

## Bugs

None caught in this iteration; no `state/bugfix_log.md` entry needed.

## Summary

A genuinely different macro data type from every prior regime family in
this loop (a single-country, single-survey manufacturing diffusion index,
rather than a composite leading index, a credit spread, a monetary
aggregate, or a yield-curve slope), with a rigorously-verified real
divergence from family 019's OECD CLI and honest disclosure of the
reconstruction methodology this iteration's data-unavailability forced.
Despite the mechanism's plausibility and a correctly-verified signal
construction (the known-episode check nailed the 2008-09 collapse), the
primary configuration's timing/banking mechanic produced **no edge
at all** on this development sample -- the worst sec 4.1 result (0/5) and
tied-worst sec 4.4 result (0%) of any macro regime-switch family tested
in this loop to date (families 011, 019, 032, 050 all managed at least
2/5 on sec 4.1). Whether this reflects the underlying ISM PMI mechanism
genuinely having no timing edge for buy-and-hold deposit sizing, or an
artifact of this family's necessarily-reconstructed (rather than
live-fetched) input series, cannot be fully disentangled here -- flagged
honestly as a limitation of this iteration's result, not resolved by
retuning (per sec 5.4's holdout-discipline spirit, applied here even
though the holdout itself was never opened). Holdout not opened
(rejected, not a finalist).
