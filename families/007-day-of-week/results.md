# Family 007 results: day-of-week deposit timing (Caporale & Plastun 2019, BTC weekend/Monday effect)

**Verdict: REJECTED** (fails sec 4.1 decisively -- only 1/5 core assets beat
DCA on wealth AND Sharpe together, need >= 3/5 -- and fails sec 4.4's grid
diagnostic at 0/24 configs, 0%, need >= 2/3; sec 4.2's DSR is also
essentially zero. Per family 006's established precedent, sec 4.3 (rolling
windows / bootstrap / placebo) was only to be attempted "if sec 4.1
passes" -- it does not, so sec 4.3 was not run at all.)

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`, forces same-day-full-deposit buy every week-end, bypassing the day-of-week/banking-window computation) reproduces plain DCA exactly (bit-for-bit on units and cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary day-of-week config) | PASS |
| Cash and positions never negative (`target_weekday=Sunday` config on BTC, the one asset where Sunday is an actual trading day) | PASS |
| No-lookahead: perturbing all data after day t leaves every order on/before t unchanged (primary config) | PASS |
| No-lookahead (`target_weekday=Sunday` config on BTC, extra check per this family's own less-standard cadence) | PASS |
| Point-in-time macro data | N/A (price/calendar-only strategy; vacuously satisfied) |
| Total capital deployed never exceeds the SAME $500/week deposit stream's own cumulative value (deposits + interest earned while un-invested), path-wise | PASS |

## Primary configuration: `target_weekday=Monday, mild_tilt_fraction=0.0, max_lump_multiple=6, banking_window_weeks=4`

(Matches Caporale & Plastun's (2019) own headline finding: a positive
abnormal Bitcoin return specifically on Mondays -- buy right before that
session, with full banking of non-Monday weeks' deposits between Monday
lumps.)

### sec 4.1 -- beats DCA on wealth AND Sharpe, >= 3 of 5 core assets, both fee levels

At 0.1% fees:

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both) |
|---|---|---|---|---|---|
| SP500 | 85.27935 | 85.27722 | 0.154224 | 0.153097 | **YES** (barely, on both) |
| GOLD | 2.23016 | 2.23123 | 0.508494 | 0.504917 | no (wealth lower) |
| SILVER | 1.68600 | 1.68666 | 0.321411 | 0.319677 | no (wealth lower) |
| BTC | 9.80402 | 9.85568 | 1.057197 | 1.067309 | **no -- fails on BOTH wealth and Sharpe** |
| OIL | 1.18076 | 1.17986 | 0.219931 | 0.227824 | no (Sharpe lower) |

At 0.25% fees the pattern is identical: only SP500 beats DCA on both
metrics. **1/5 at both fee levels -- sec 4.1: FAIL** (need >= 3/5).

**Notable, and worth flagging explicitly since it directly contradicts this
family's own pre-registered "Expected sign" (which called BTC the
family's "strongest and most literature-grounded expectation"):** BTC --
the one asset the Caporale & Plastun (2019) literature is actually about --
is the asset where the primary configuration fails most clearly, missing
on *both* wealth (9.80x invested vs DCA's 9.86x) and Sharpe (1.057 vs
1.067). SP500, which has no crypto-specific weekend-liquidity rationale at
all, is the only asset that (marginally) passes. This is the mirror image
of family 006's result, where the literature-anchor asset (SP500) was the
one that passed and the out-of-scope assets failed; here the
literature-anchor asset (BTC) is itself among the failures. The most
likely explanation, read from the mechanics: `mild_tilt_fraction=0.0`
(full banking) concentrates roughly 4/5 of every month's deposit into a
single weekly lump-sum Monday buy, and BTC's 2014-2019 development window
has strong, persistent upward drift -- so, exactly as in family 006's BTC
result, the opportunity cost of delaying most of the week's deposit by a
few days outweighs whatever Monday-specific price edge (if any, net of
this development sample's own noise) exists. A small, real Caporale &
Plastun-style Monday effect (if it exists at all on this specific
2014-2019 development slice, which is itself materially different from
their own 2013-2017 sample and includes BTC's short, volatile early
history) is not large enough to survive being netted against that banking
drag.

### sec 4.2 -- Deflated Sharpe Ratio >= 0.95

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  **-0.0176/week** (annualized ~-12.7%) -- negative on average, and
  extremely left-skewed and fat-tailed (skew -47.07, kurtosis 2901.2), the
  most extreme higher-moment profile of any family in this loop so far
  (family 006's kurtosis of 698.2 was the previous high) -- consistent
  with `mild_tilt_fraction=0.0` concentrating purchases into a single
  weekly lump far more often than family 006's monthly lump (a Monday
  recurs every ~7 calendar days vs. a turn-of-month window recurring
  roughly every ~30), which multiplies the number of large, discrete
  purchase events across the same development history and produces an
  even more concentrated tail-risk profile in the weekly excess-return
  series.
- `N` (raw trial count at this assessment): **352** (196 seeded + 132 from
  families 001-006 + 24 new from this family's grid).
- `N_eff` (average-linkage clustering, distance sqrt(0.5(1-rho)),
  rho >= 0.5 threshold): **38** clusters.
- **DSR (N_eff-based, used for the decision): 1.71e-77** -- essentially
  zero, an even more decisive failure than family 006's 5.83e-28.
- DSR (raw-N, conservative reference): 5.82e-110.

**sec 4.2: FAIL**, overwhelmingly so -- consistent with every prior family
that has reached this check.

### sec 4.4 -- robust across parameters (grid diagnostic)

**0 of 24 configurations (0.0%) reach the majority-of-assets bar** (>= 3/5
core assets beating DCA on both wealth and Sharpe at 0.1% fees) -- tied
with family 006 for the worst grid result of any family in this loop so
far. Looking at the per-config summary (`grid_results.csv`), the best any
single config does is 2/5 assets on wealth alone (the two
`target_weekday=Monday, banking_window_weeks=4` arms), while the wealth
and Sharpe splits never overlap enough on any config to clear 3/5 on both
jointly. **sec 4.4: FAIL** (need >= 16/24 = 2/3; got 0/24).

CSCV probability of backtest overfitting (diagnostic, computed on both
BTC's and SP500's grid, 8 splits, 70 combinations, since this family's
literature anchor is BTC specifically -- unlike family 006's SP500-only
CSCV, which is retained here too for cross-family comparability):

- BTC grid: **PBO = 0.429** (close to a coin flip -- noticeably worse than
  family 006's clean PBO=0.0, consistent with BTC's own excess-return
  series being the most erratic/inconsistent one in this family's grid,
  matching the higher-moment blowup noted under sec 4.2).
- SP500 grid: **PBO = 0.0** (not overfit -- SP500's small, marginal edge,
  where it exists at all in the grid, is at least directionally consistent
  across resampled train/test splits, similar to family 006's pattern).

### sec 4.3 -- not run (per family 006 precedent, since sec 4.1 did not pass)

sec 4.1 fails at 1/5 (need 3/5), sec 4.4 fails at 0/24 (need 16/24), and
sec 4.2's DSR is ~77 orders of magnitude below 0.95 (N_eff-based). All
three independently and jointly conclusive; sec 4.3 (rolling windows,
block bootstrap, placebo circular-shift) was not run at all for this
family, following the exact precedent set by family 006 and the task's
own explicit time-budget instruction for this iteration. This also kept
the grid run (24 configs x 5 assets x 2 fee levels) within the iteration's
time budget (completed in a few minutes).

## Verdict

**REJECTED.** The primary configuration fails sec 4.1 decisively (only
1/5 core assets -- SP500 alone -- beat DCA on wealth AND Sharpe together,
at both 0.1% and 0.25% fees; need >= 3/5), fails sec 4.4's grid diagnostic
at 0/24 configs (0%, need >= 2/3), and sec 4.2's DSR is effectively zero
(1.71e-77, need >= 0.95). Holdout was **not** opened -- holdout access is
reserved for finalists only, and this family never reached finalist
status.

## Why the mechanism didn't clear the bar (interpretation, not part of the formal verdict)

Unlike family 006 (where the equity-motivated turn-of-month effect cleanly
passed on the one equity asset and failed on everything else, exactly as
predicted), this family's result is messier and, if anything, a weaker
outcome for the underlying literature claim: the one asset the mechanism
was specifically motivated by (BTC, via Caporale & Plastun's Monday-effect
finding) fails outright on both wealth and Sharpe under the primary
configuration, while SP500 -- an asset with no day-of-week weekend-
liquidity rationale in this family's own mechanism section -- is the only
one that (marginally) passes. Two candidate readings, neither confirmable
without further work this iteration's budget does not call for: (1) the
Caporale & Plastun Monday effect, even if real in their own 2013-2017
sample, is small and fragile enough that it does not survive being netted
against this strategy's `mild_tilt_fraction=0.0` full-banking design's
opportunity-cost drag on an asset with BTC's strong secular 2014-2019
drift -- the same mechanical failure mode already seen in family 006's
BTC result and family 004's value-averaging BTC result; (2) SP500's
marginal pass may simply be noise from a design (weekly lump-sum
concentration) that was never motivated by any equity-specific literature
claim at all, and the CSCV PBO=0.0 on SP500's grid is at best weak
evidence against that read, not strong evidence for a real SP500 effect.
Both readings point the same direction for this family's verdict: reject.

## Single-vs-multi-asset scoping decision (recap; full reasoning in prereg.md)

Tested on **all 5 core assets** under sec 4.1's standard >= 3/5 rule,
following **family 006's precedent explicitly** (per the task's own
instruction), rather than restricting to BTC only, because: (1) the
mechanism's structural claim (a day-of-week price/liquidity pattern) is
not logically confined to crypto, even though the specific anchor finding
is; (2) uniform application across families (001-006 all used the same
5-asset rule) matters more than a one-off exception, especially since the
task explicitly named family 006 as the controlling precedent to follow
absent a strong reason to deviate, and no such strong reason was found;
(3) restricting to BTC-only would leave no defined sec 4.1 pass path at
all, since that check structurally requires 5 assets; (4) testing all 5
assets is the conservative choice. This family's actual result -- BTC
itself failing, SP500 marginally passing -- is a useful empirical data
point on the scoping question generally: it shows that "the literature-
anchor asset passes, the others don't" (family 006's pattern) is not a
given outcome of this uniform-scoring approach; sometimes, as here, even
the anchor asset fails while an out-of-scope asset marginally passes,
which is exactly the kind of honest, non-cherry-picked signal the uniform
rule is designed to surface rather than obscure.

## Judgment calls made in this iteration

1. **Decision cadence evaluated on every trading day, not only the week's
   deposit-credit day** -- a deliberate, pre-registered departure from
   family 006's cadence (which only needed to evaluate its calendar signal
   on the week's single decision day, since the deposit-credit day and the
   TOM window's state coincided). This family's target day of week usually
   differs from the asset's own week-end/deposit day (Friday for the 4
   non-BTC assets, Sunday for BTC under `engine.week_end_flags`), so the
   day-of-week signal genuinely needs daily evaluation. Declared in
   `prereg.md` before any backtest.
2. **`banking_window_weeks` forced-deploy rule added, not present in
   family 006.** Needed because `target_weekday=Sunday` never occurs at
   all on the 4 non-BTC assets' own trading calendars (they have no
   weekend trading day), which would otherwise make that grid arm bank
   cash indefinitely with no mechanism to ever deploy it. Declared and
   justified in `prereg.md` before any backtest; verified with an extra
   no-lookahead/non-negativity check specifically on the BTC/Sunday
   combination (the one case where Sunday genuinely is a trading day).
3. **CSCV PBO computed on both BTC's and SP500's grid** (rather than
   SP500-only, as family 006 did), since this family's literature anchor
   is BTC specifically, while SP500 is retained too for cross-family
   comparability with 006's own diagnostic. Declared here as an
   in-iteration choice, not tuned after seeing which asset looked better --
   both were always going to be reported regardless of outcome.
4. **sec 4.3 was not run at all**, following family 006's own precedent
   and this iteration's explicit time-budget instruction (attempt sec 4.3
   in full only if sec 4.1 passes). sec 4.1 fails outright (1/5) and sec
   4.4 fails at the floor (0/24), so nothing about the conclusive verdict
   depends on it, and skipping it kept the iteration within budget.
