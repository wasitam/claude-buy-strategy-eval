# Family 051 results: Pre-FOMC announcement drift deposit timing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively
(beats DCA on wealth AND Sharpe on only **1/5** core assets, need >=3/5,
at both fee levels). The grid diagnostic fails just as decisively (**0 of
16, 0%**, configurations reach the majority-of-assets bar, need >=2/3).
DSR is effectively zero, driven by a genuinely negative raw pooled
excess-return Sharpe. Holdout was **not** opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family across all 5 core assets**
(independently per asset, sec 4.1's standard >=3/5 rule), following
family 022's own precedent for a US-specific macro event applied to all 5
core assets (the FOMC calendar-timing mechanism itself needs no
asset-specific data, and the rate-decision channel plausibly transfers
beyond US equities to USD-denominated commodities and BTC). Category:
**Seasonality / execution timing**.

## Required distinction from families 006/007/018/022/024 (verified concretely, not asserted)

Computed directly on the 208 hard-coded FOMC decision dates
(1994-02-04..2019-12-11, exactly 8/year every year -- confirmed
programmatically before any date-level analysis):

- **Weekday distribution (vs. family 007's single fixed weekday):**
  Tuesday 85/208 (40.9%), Wednesday 115/208 (55.3%), Thursday 7/208
  (3.4%), Friday 1/208 (0.5%) -- never Monday, Saturday or Sunday.
  Dominated by Tue/Wed (the 1-day/2-day meeting conventions), but **not**
  a single fixed weekday, unlike family 007's `target_weekday`.
- **Day-of-month distribution (vs. family 006's ~4-trading-day
  turn-of-month band):** spans the entire 1-31 range (min 1, max 31, mean
  17.9, std 9.0). Overlap with family 006's own primary TOM window (last
  1 + first 3 business days of the month, ~19% of the month by
  construction): **43 of 208 dates (20.7%)** -- essentially identical to
  the **39.6 dates (19%) pure chance alone predicts** with zero
  clustering (ratio **1.09x** chance, gated in the run script to fall
  within 0.5x-1.5x before any backtest was trusted). This is the correct
  redundancy test: not "zero overlap" (impossible for any calendar that
  must place 8 dates somewhere in the month), but "no disproportionate
  concentration in family 006's specific window," which is confirmed.
- **Month-of-year distribution (vs. families 018's fixed 6-month
  Halloween window and 024's fixed seasonal SAD window):** all 12 months
  represented (Jan 18, Feb 8, Mar 26, Apr 8, May 18, Jun 21, Jul 11, Aug
  20, Sep 23, Oct 12, Nov 17, Dec 26), and, critically, the exact date
  within a given month **shifts by days to weeks from year to year**
  (e.g. the March meeting: 1994-03-22, 1997-03-25, 2007-03-21,
  2017-03-15, 2019-03-20 -- no two years share a date), unlike 018/024's
  identical repeating annual template.
- **Year-mod-4 distribution (vs. family 022's quadrennial election
  cycle):** 48/48/56/56 across the four residues -- essentially uniform,
  no dependence on the US presidential cycle at all.
- **Non-modularity:** inter-meeting gaps range 34-58 calendar days (mean
  45.6, std 5.6) -- irregular, not a fixed modulus, unlike 006's ~21
  trading-day month or 007's ~5/7-day week.

**Conclusion, confirmed on real dates rather than asserted: the pre-FOMC
calendar is a genuinely different, externally determined event calendar**,
not a relabeling of any prior seasonality family's fixed modular or fixed
annual/quadrennial cycle.

## Data reachability

`federalreserve.gov`, `en.wikipedia.org` and `www.r-bloggers.com` were all
confirmed **`EGRESS_BLOCKED`** via direct `WebFetch` calls in this
session -- no live-reachable structured source of the historical FOMC
meeting calendar exists in this environment. Per this family's explicit
task-level allowance for this contingency, the 208 scheduled decision
dates (1994-02-04..2019-12-11) were hard-coded in
`src/backtest/v3/strategies/pre_fomc_drift.py::FOMC_DATES`, compiled from
this session's own knowledge of the well-documented public historical
FOMC record; unscheduled/emergency actions (Sep 2001, Jan/Oct 2008) were
deliberately excluded since they were not on a publicly pre-announced
calendar. The signal itself needs no external data feed at runtime (only
the asset's own price history via `load_dev()` plus this fixed constant)
-- no network-reachability risk for the backtest itself.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`, bypasses the pre-FOMC/banking-window computation entirely, buys 100% of cash every week-end day) reproduces plain DCA exactly (bit-for-bit) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config, SP500) | PASS |
| Cash and positions never negative (primary config, BTC -- extra check, BTC's entire history is inside the FOMC-calendar-covered era) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (principled ceiling bound: cash never negative) | PASS |
| No-lookahead: perturbing all data after day t leaves every order on/before t unchanged (SP500, t=6000) | PASS |
| No-lookahead, second spot-check deep into the sample (SP500, t=20000) | PASS |
| No-lookahead (BTC, t=1000) | PASS |
| Point-in-time: price/calendar-only signal, no macro data feed at all -- vacuously satisfied | PASS |

## Redundancy gate and pre-grid sanity checks (all passed)

**Redundancy gate:** exactly 8 meetings/year every year (1994-2019);
overlap with family 006's TOM window at 1.09x the chance-expected rate
(within the pre-declared 0.5x-1.5x band) -- both checked programmatically
before any backtest, per prereg.md.

**Non-degeneracy:** the primary configuration's pre-FOMC window flag
fires on a small but non-trivial fraction of trading days on every asset,
diluted by how much of each asset's own history predates the 1994-02-04
FOMC-calendar-coverage start (SP500's history reaches back to 1927,
diluting it the most; BTC's 2014-09 start is entirely inside the
FOMC-calendar era, diluting it the least):

| Asset | Dev days | Window-day count | Fraction | Dev-history start |
|---|---|---|---|---|
| SP500 | 23,109 | 416 | 1.80% | 1927-12-30 |
| GOLD | 4,848 | 310 | 6.39% | 2000-08-30 |
| SILVER | 4,850 | 310 | 6.39% | 2000-08-30 |
| BTC | 1,932 | 84 | 4.35% | 2014-09-17 |
| OIL | 4,857 | 310 | 6.38% | 2000-08-23 |

All 5 fall inside the pre-declared (0.5%, 15%) sanity band; the pattern
(SP500 lowest, GOLD/SILVER/OIL similar mid-range, BTC in between) exactly
matches the expected dilution ordering from each asset's own development
history length relative to 1994.

## Primary configuration: `window_days=2, mild_tilt_fraction=0.0, max_lump_multiple=6, banking_window_weeks=8`

### Per-asset result (vs. plain DCA), at 0.1% fees

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 67.957x | 85.277x | 0.16230 | 0.15310 | NO (loses wealth) |
| GOLD | 2.2207x | 2.2312x | 0.5121 | 0.5049 | NO (loses wealth) |
| SILVER | 1.6841x | 1.6867x | 0.3281 | 0.3197 | NO (loses wealth) |
| BTC | 9.3851x | 9.8557x | 1.0881 | 1.0673 | NO (loses wealth) |
| OIL | 1.1883x | 1.1799x | 0.23840 | 0.22782 | **YES** |

**Beats DCA count (wealth AND Sharpe): 1/5 at 0.1% fees, 1/5 at 0.25%
fees** (OIL only). The pattern is strikingly uniform: the primary config
**wins Sharpe on 4/5 assets** (SP500, GOLD, SILVER, OIL) and **wins
wealth on only 1/5** (OIL) -- SP500/GOLD/SILVER/BTC all lose wealth while
winning (or, for BTC, also winning) Sharpe. This is the same
Sharpe-wins/wealth-loses divergence pattern family 048 (drift-band
rebalance) showed on its own portfolio-level result, here showing up
asset-by-asset within a single-asset family.

**sec 4.1: FAIL, decisively** (need >=3/5 at both fee levels; got 1/5 at
both).

### Why the primary configuration fails

`max_lump_multiple=6` combined with a fairly wide `banking_window_weeks=8`
means the primary spends most of an ordinary inter-meeting cycle banking
cash (`mild_tilt_fraction=0.0`) and then deploys a large, concentrated
lump into the 2-trading-day pre-FOMC window itself. Since the underlying
asset's price still has to rise, fall, or stay flat over the following
week regardless of which 2 days the lump landed on, this concentrates
each week's capital into a narrower, higher-variance execution window
than DCA's own smooth weekly schedule -- exactly the mechanism the
Lucca & Moench literature's OWN claimed edge would need to overcome
(a real average outperformance in that narrow window), and on this
backtest's development sample it does not overcome it on 4 of 5 assets'
wealth outcome, even though the same concentration mechanically raises
the return-per-unit-of-volatility ratio (Sharpe) on most assets by
smoothing out variance elsewhere in the cycle. The result is a
strategy that looks attractive on a risk-adjusted (Sharpe) basis almost
everywhere but fails the loop's stricter **both-wealth-AND-Sharpe**
requirement on all but OIL.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled 5-asset excess-return
  series: **-0.0311/week** (annualized ~-22.4%) -- clearly negative.
- `N` (raw trial count, whole-loop pool): **1,531** (196 seeded + 1,319
  from families 001-050 + 16 new from this family's grid).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **134**
  clusters (unchanged from family 050 -- this family's 16 grid configs
  did not add a new distinct cluster, consistent with the primary's
  negative, moderately fat-tailed excess-return series clustering with
  existing trial clusters already in the pool).
- **DSR (N_eff-based): 3.77e-30** -- essentially zero.
- DSR (raw-N, conservative reference): 1.62e-29.

**sec 4.2: FAIL**, overwhelmingly -- expected given the negative raw
Sharpe alone. Skew (-0.30) and kurtosis (17.7) are moderate by this
loop's standards (nowhere near families 046/047's extreme 1000+
kurtosis), consistent with a lump-sum-concentration mechanism whose
pooled excess-return distribution is negatively but not pathologically
skewed.

### Grid diagnostic (sec 4.4)

**0 of 16 configurations (0%) reach the majority-of-assets bar** (>=3/5
core assets beating DCA on both wealth and Sharpe at 0.1% fees) -- the
weakest possible grid outcome, tied with families 047 and 048. The grid
is not flat noise, though: `beats_wealth@0.1%` is 0 or 1 out of 5 on
every single one of the 16 configs (OIL is consistently the only asset
that ever wins wealth, across every parameter combination), while
`beats_sharpe@0.1%` ranges from 1/5 (the tightest, `window_days=1,
max_lump_multiple=3, banking_window_weeks=8` corner) up to 5/5 (several
wider-lump/longer-banking corners) -- confirming the Sharpe-wins/
wealth-loses split is a structural property of this mechanism across the
whole parameter space, not an artifact of the primary's specific choice.
No config reaches the 3/5 combined bar needed even once.

**sec 4.4: FAIL** (0/16 = 0%, need >=66.7%).

CSCV probability of backtest overfitting (16-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.0** -- the
lowest (best) PBO diagnostic of any family in this loop so far, because
every one of the 16 configs' SP500 return series shares the same
consistent sign/rank ordering (none reaches the wealth bar at all on
SP500), leaving no genuine "overfitting to noise" pattern for CSCV to
detect -- a diagnostic only; it does not change the decisive sec 4.1/4.4
failures.

### Robustness (sec 4.3)

**Not run.** Per established precedent (sec 4.1 already fails decisively;
only attempted when sec 4.1 passes), the rolling-window / block-bootstrap
/ placebo battery was skipped.

## Verdict

**REJECTED.** Sec 4.1 fails decisively at 1/5 core assets (need >=3/5) at
both fee levels -- only OIL beats DCA on both wealth and Sharpe under the
primary configuration; SP500, GOLD, SILVER and BTC all lose on wealth
despite 3 of the 4 also winning on Sharpe. Sec 4.4's grid diagnostic
confirms this is a structural, not a primary-config-specific, pattern:
0/16 grid configs reach the combined majority bar, and the
Sharpe-wins/wealth-loses split holds across essentially the entire grid.
DSR is effectively zero, driven by a clearly negative raw pooled
excess-return Sharpe. Holdout was **not** opened.

## Interpretation

The prereg's central hypothesis -- that Lucca & Moench's documented
pre-FOMC equity drift, applied as a pure execution-timing lump-sum tilt
within a fixed $500/week schedule, would beat DCA on SP500 at least, with
plausible (if less certain) transfer to gold/silver/oil/BTC -- is **not
confirmed on development data**. SP500, the literature's own anchor
asset, loses on wealth under the primary configuration despite a real
(if small) Sharpe improvement -- the concentration of capital into the
narrow 2-day pre-announcement window raised risk-adjusted return but not
absolute terminal wealth over this development sample. This is
consistent with, but does not by itself confirm, the honestly-flagged
risk in prereg.md that (a) the effect may have partially attenuated in
the post-2015-publication years included in this development sample, and
(b) a pure execution-timing-within-a-fixed-schedule mechanism (never
changing total capital deployed) can only move the needle by a small
absolute margin even if the underlying return pattern is real -- here,
that margin was not merely small but negative on 4 of 5 assets. OIL is
the sole asset that clears the combined bar, an interesting but isolated
result that this loop's rules do not allow promoting to primary-config
status (sec 4.4: the grid is diagnostic only).

## Redundancy-check bugfix note (see `state/bugfix_log.md`)

The run script's first-draft redundancy gate against family 006's
turn-of-month window used an arbitrary hard threshold (raw overlap count
> 20 fails) rather than the correct chance-expected baseline, and would
have wrongly aborted this family before any backtest even though the
measured overlap (43/208, 1.09x chance) is the textbook expected result
for a non-clustered calendar. Fixed before any grid or trial was counted;
full detail in `state/bugfix_log.md` and prereg.md's own updated text.
