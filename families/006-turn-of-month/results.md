# Family 006 results: turn-of-month deposit timing (Ariel 1987; Lakonishok & Smidt 1988)

**Verdict: REJECTED** (fails sec 4.1 decisively -- only 1/5 core assets beat
DCA on wealth AND Sharpe together, need >= 3/5 -- and fails sec 4.4's grid
diagnostic at 0/24 configs, 0%, need >= 2/3; sec 4.2's DSR is also
essentially zero. Per the task's explicit instruction for this family, sec
4.3 (rolling windows / bootstrap / placebo) was only to be attempted "if
sec 4.1 passes" -- it does not, so sec 4.3 was not run at all; nothing
about the already-conclusive verdict depends on it.)

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`, forces same-day-full-deposit buy every week-end, bypassing the TOM calendar computation) reproduces plain DCA exactly (bit-for-bit on units and cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary TOM config) | PASS |
| No-lookahead: perturbing all data after day t leaves every order on/before t unchanged | PASS |
| Point-in-time macro data | N/A (price/calendar-only strategy; vacuously satisfied) |
| Total capital deployed never exceeds the SAME $500/week deposit stream's own cumulative value (deposits + interest earned while un-invested), path-wise | PASS |

## Primary configuration: `days_before_month_end=1, days_after_month_start=3, mild_tilt_fraction=0.0, max_lump_multiple=6`

(Matches Lakonishok & Smidt's own headline four-trading-day turn-of-month
window: the last trading day of the month plus the first three trading
days of the next, with full banking between windows.)

### sec 4.1 -- beats DCA on wealth AND Sharpe, >= 3 of 5 core assets, both fee levels

At 0.1% fees:

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both) |
|---|---|---|---|---|---|
| SP500 | 85.71746 | 85.27722 | 0.156939 | 0.153097 | **YES** |
| GOLD | 2.22379 | 2.23123 | 0.509560 | 0.504917 | no (wealth lower) |
| SILVER | 1.67667 | 1.68666 | 0.322096 | 0.319677 | no (wealth lower) |
| BTC | 7.83824 | 9.85568 | 1.088392 | 1.067309 | no (wealth much lower) |
| OIL | 1.17294 | 1.17986 | 0.237648 | 0.227824 | no (wealth lower) |

At 0.25% fees the pattern is identical: only SP500 beats DCA on both
metrics. **1/5 at both fee levels -- sec 4.1: FAIL** (need >= 3/5).

The pattern is striking and, on reflection, economically coherent: on
**every one of the 4 non-SP500 assets, Sharpe improves** (the strategy's
weekly-return distribution is genuinely a bit smoother/better risk-adjusted
than DCA's) **but wealth falls short**, most dramatically on BTC
(7.84x invested vs. DCA's 9.86x -- a large gap). This is the direct,
predictable cost of `mild_tilt_fraction=0.0` (full banking): every non-TOM
week's $500 sits in cash for up to several weeks before being deployed as a
lump sum at the next TOM window, and on an asset with strong, persistent
upward drift over the development period (BTC's 2014-2019 window especially,
but also gold/silver/oil to lesser degrees), delaying purchase into a rising
market is a real opportunity cost that this strategy pays every single
non-TOM week, regardless of whether that week's TOM-window purchase later
gets a favorable turn-of-month price. Only SP500 -- the asset the
motivating literature is actually about -- shows enough of a turn-of-month
return edge to overcome this banking drag on wealth; the other four assets'
turn-of-month price edge (if any) is not large enough to compensate for
consistently buying later than DCA would have. This is exactly the
scenario flagged as a real possibility in `prereg.md`'s "Expected sign"
section before any backtest was run.

### sec 4.2 -- Deflated Sharpe Ratio >= 0.95

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  **-0.00686/week** (annualized ~-4.95%) -- negative on average, and
  heavily left-skewed and fat-tailed (skew -3.17, kurtosis 698.2), an even
  more extreme kurtosis than family 005's (470.5), consistent with the
  lump-sum concentration (`mild_tilt_fraction=0.0`, `max_lump_multiple=6`)
  producing occasional large single-week purchases that swing the
  excess-return distribution's tails harder than any prior family's more
  gradual sizing multipliers.
- `N` (raw trial count at this assessment): **328** (196 seeded + 108 from
  families 001-005 + 24 new from this family's grid).
- `N_eff` (average-linkage clustering, distance sqrt(0.5(1-rho)),
  rho >= 0.5 threshold): **37** clusters.
- **DSR (N_eff-based, used for the decision): 5.83e-28** -- essentially
  zero, in the same range as families 001, 003 and 005's decisive failures.
- DSR (raw-N, conservative reference): 9.76e-42.

**sec 4.2: FAIL**, overwhelmingly so -- consistent with every prior family
that has reached this check: even a favorable per-asset pattern (here, on
one asset only) does not survive being pooled equal-weight across all 5
assets and adjusted for this loop's growing effective trial count.

### sec 4.4 -- robust across parameters (grid diagnostic)

**0 of 24 configurations (0.0%) reach the majority-of-assets bar** (>= 3/5
core assets beating DCA on both wealth and Sharpe at 0.1% fees) -- the
worst grid result of any family in this loop so far (family 003's 33.3%
was the previous low). Looking at the per-config summary
(`grid_results.csv`), the best any single config does is 1/5 assets on
wealth (always SP500 when it happens), while Sharpe alone frequently beats
on 4/5 or 5/5 assets -- the wealth/Sharpe split described above under sec
4.1 recurs consistently across the entire grid, not just the primary
configuration. **sec 4.4: FAIL** (need >= 16/24 = 2/3; got 0/24).

CSCV probability of backtest overfitting (diagnostic, SP500 grid, 8 splits,
70 combinations): **PBO = 0.0**. As with every prior family this loop has
measured it on, the grid is not overfit in the CSCV sense -- the pattern
(SP500 alone shows a genuine, consistent edge; the other four assets
consistently do not) holds up across resampled train/test splits of the
grid, it just isn't a strong or broad enough pattern to pass this family's
other bars.

### sec 4.3 -- not run (per task instruction, since sec 4.1 did not pass)

The task's own guidance for this family was explicit: attempt sec 4.3 only
if sec 4.1 passes, since the verdict would likely be decidable from
sec 4.1/4.2/4.4 alone given the pattern in families 001-005. That is
exactly what happened here -- sec 4.1 fails at 1/5 (need 3/5), sec 4.4
fails at 0/24 (need 16/24), and sec 4.2's DSR is ~28 orders of magnitude
below 0.95. All three independently and jointly conclusive; sec 4.3 (rolling
windows, block bootstrap, placebo circular-shift) was not run at all for
this family, and no time budget was spent on it.

## Verdict

**REJECTED.** The primary configuration fails sec 4.1 decisively (only
1/5 core assets -- SP500 alone -- beat DCA on wealth AND Sharpe together,
at both 0.1% and 0.25% fees; need >= 3/5), fails sec 4.4's grid diagnostic
at 0/24 configs (0%, need >= 2/3), and sec 4.2's DSR is effectively zero
(5.83e-28, need >= 0.95). Holdout was **not** opened -- holdout access is
reserved for finalists only (plan sec 8 step 8), and this family never
reached finalist status.

## Why the mechanism didn't clear the bar (interpretation, not part of the formal verdict)

The turn-of-month effect's own literature is specifically about equity
markets (Dow Jones, S&P 500), and the result here is a clean confirmation
of that scope, not a refutation of the underlying equity finding: SP500 is
the one asset where the strategy beats DCA on both wealth and Sharpe at
both fee levels. The other four assets each show *higher Sharpe* under the
strategy (a real, consistent smoothing effect from concentrating purchases
into fewer, larger, and apparently somewhat-better-timed weeks) but *lower
wealth* -- the cost of the `mild_tilt_fraction=0.0` full-banking design,
which delays roughly 3/4 of every month's deposit by one to several weeks
in exchange for a shot at a better average price during the TOM window.
On assets with strong secular drift over the development period (BTC most
dramatically, but gold/silver/oil too, more mildly), that delay cost more
in missed appreciation than the turn-of-month price edge (if any exists on
those assets at all) recovered. This is consistent with the scoping
decision's own prediction in `prereg.md`: the mechanism's institutional-flow
rationale (payroll/pension cycles, month-end fund rebalancing) is a
specifically equity-market pattern, and extending it to commodities/BTC
without independent literature support for those markets was always the
riskier half of the sec 4.1 test -- which is exactly what the >= 3/5
uniform rule (chosen deliberately as the harder, more conservative option
over restricting to SP500-only) was designed to surface honestly.

## Single-vs-multi-asset scoping decision (recap; full reasoning in prereg.md)

Tested on **all 5 core assets** under sec 4.1's standard >= 3/5 rule (option
(a) from the task), rather than restricting to SP500 only (option (b)),
because: (1) the mechanism itself (a calendar-based execution-timing shift
within a fixed deposit schedule) carries no structural equity-specific
assumption, even though its *motivating historical evidence* is
equity-specific; (2) every prior family (001-005) drew its literature from
an asset-specific or asset-class-specific source and was still tested
uniformly across all 5 core assets, so carving out an exception for idea #6
alone would be an ad hoc, non-uniform application of sec 4.1 with no
textual basis; (3) restricting to SP500-only would leave no defined path to
a sec 4.1 verdict at all, since that check requires 5 assets; (4) testing
all 5 assets is the *conservative* choice -- it makes the family harder,
not easier, to pass if the effect is genuinely equity-specific, which this
family's actual result (SP500 alone beats DCA; BTC/gold/silver/oil do not)
now confirms empirically rather than merely in principle.

## Judgment calls made in this iteration

1. **Weekly decision cadence retained (calendar signal evaluated only on
   the week's last trading day), rather than evaluating the TOM signal on
   every trading day.** Declared in `prereg.md` before any backtest. This
   keeps the same decision cadence every other v3 family uses and avoids a
   repeated-buy defect that would otherwise arise from a nonzero banked
   cash balance being re-evaluated against a "buy X this week" target on
   every non-week-end day it happens to sit idle. A live implementation of
   this rule would place the actual order on the nearest TOM trading day
   near a given week-end decision, per a hypothetical playbook -- not
   relevant here since this family is rejected and produces no playbook.
2. **sec 4.3 was not run at all**, per the task's own explicit instruction
   for this specific family (unlike families 001/003/005, which attempted
   partial sec 4.3 runs before their own time budgets ran out). Since sec
   4.1 fails outright (1/5, not a near-boundary case) and sec 4.4 fails at
   the floor (0/24), this is not a deviation from instructions but exactly
   what was instructed, and it saved the runtime budget entirely -- the
   family's grid run (24 configs x 5 assets x 2 fee levels) completed in
   about 6 minutes.
3. **`max_lump_multiple` grid values (3, 6) chosen based on typical TOM
   recurrence cadence** (a ~4-day window recurs roughly every ~4.3 weeks,
   so multiples below ~5 were expected to bind under normal cadence,
   worth testing as a genuinely different capital-cap regime) -- declared
   in `prereg.md` before any backtest, not tuned after seeing results.
4. **CSCV grid asset.** As in every prior family, CSCV PBO is computed on
   SP500's grid-config weekly returns only (not pooled across assets),
   consistent with the established convention.
