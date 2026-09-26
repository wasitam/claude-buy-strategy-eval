# Family 048 results: Tolerance-band (drift-triggered) rebalancing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 (loses to
fixed-weight 5-asset DCA on wealth, despite winning on Sharpe) at both fee
levels, and the failure is not a primary-config-specific accident: **0/18
(0%)** of the grid's configurations beat DCA on wealth AND Sharpe together
-- the same BTC-dominance failure mode families 013 (`tilt_strength=0`,
NOT a finalist path) and 029 (risk-parity, REJECTED) both hit, now confirmed
for a third, mechanistically distinct fixed-equal-weight-target rebalancing
design.

## Required concrete distinction check (run before the grid, per prereg.md)

Confirmed on real dev-period data, primary config (`band_pct=0.05,
min_days_between_rebalances=5`), before the grid or any results were
trusted:

| Check | Result |
|---|---|
| `PRIMARY_CONFIG` is a member of `GRID` (import-time assertion) | Caught a real mismatch pre-run -- see "Judgment calls" below -- then PASS |
| Rebalance-event count | 30 events out of 277 week-ends (10.8% of week-ends trigger a rebalance) |
| Inter-rebalance gap coefficient of variation | **1.159** -- far from the 0 a fixed calendar cadence would show (a weekly/monthly/quarterly rule has CV=0 by construction) |
| Dispersion-vs-rebalance point-biserial correlation | **+0.452** -- rebalance week-ends have materially higher cross-asset return dispersion than non-rebalance week-ends |

**Distinction check: PASS on both legs.** Confirms the family's own
required claim: rebalance timing is a genuine function of realized price
divergence, not a disguised fixed cadence. This is a different mechanism
axis from v2's closed C1/C2/C3 (calendar-triggered, CV=0 by construction)
and from families 002/043 (which asset to favor) and 013/029 (what the
target itself should be) -- verified concretely, not just asserted, per
this iteration's task instruction.

## Complexity gate (sec 3.4)

2 tunable parameters (<=5); 18-configuration grid (<=36); one order per
asset per trading day; price-only signal (no external data dependency at
all -- the only family in this loop with zero data-reachability risk by
construction).

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`) reproduces fixed-weight 5-asset DCA exactly (bit-for-bit on units and pooled cash) | PASS |
| **Second reference point** (families 013/029/043 precedent): `band_pct=0.0, min_days_between_rebalances=0` reproduces an INDEPENDENTLY-built equal-weight weekly-rebalance reference bit-for-bit | PASS |
| That same config **differs** from plain fixed-weight DCA | PASS (confirmed to differ) |
| Cash and positions never negative (DCA baseline and primary config) | PASS |
| No-lookahead: perturbing all 5 assets' data after day t leaves every order on/before t unchanged | PASS |
| Point-in-time macro data | N/A -- price-only signal, no macro/ALFRED series |

## Shared calendar

Same construction as families 002/013/029/043: `^GSPC`'s own NYSE
trading-day index, clipped to start once every core asset has data (BTC's
first date, 2014-09-17), through 2019-12-31 -- **1,332 trading days
(~5.3 years)**, the same BTC-gated short development span every prior
5-asset portfolio family in this loop has hit (plan sec 12's known
caveat). Re-verified programmatically (`idx[-1] < 2020-01-01`) never to
touch the sealed holdout period, per this iteration's explicit
instruction.

## Primary configuration: `band_pct=0.05, min_days_between_rebalances=5`

### Sec 4.1 (Portfolio line) -- beats fixed-weight 5-asset DCA on wealth AND Sharpe, both fee levels

| Fee | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Strategy turnover | DCA turnover | Total fees paid | Beats DCA (both)? |
|---|---|---|---|---|---|---|---|---|
| 0.1% | 2.013 | 2.937 | 1.060 | 0.802 | 3.51x | 1.00x | $2,427 | **NO** (Sharpe wins, wealth loses) |
| 0.25% | 2.005 | 2.932 | 1.047 | 0.798 | 3.50x | (unreported, ~1.00x) | $6,053 | **NO** |

**Sec 4.1: FAIL** at both fee levels -- decisively on wealth (2.01x vs
2.94x invested, a ~31% wealth shortfall) even though the strategy clears
the Sharpe half of the bar comfortably. Per the prereg's own expected-sign
framing (a transaction-cost/Sharpe story, not a return-forecasting one),
the Sharpe win is exactly the kind of result the mechanism predicted --
but sec 4.1 requires wealth AND Sharpe together, and the wealth leg fails
by a wide, DCA-benchmark-relevant margin, so the family cannot pass on the
strength of the Sharpe leg alone.

**Turnover/fee comparison (the family's own hypothesized channel):**
Contrary to the "avoid unnecessary turnover" framing, the primary config's
turnover (3.51x total notional traded / total invested) is **more than
3x DCA's own turnover floor (1.00x)**, not lower -- DCA structurally has
the lowest possible turnover in this comparison set because it never
sells anything; any rule that periodically sells the fast-growing winner
(BTC) back down to a fixed 20% necessarily generates real sell-side
turnover that a buy-only benchmark cannot match. What the mechanism *does*
show, confirming it operates as designed: turnover falls **monotonically**
as `band_pct` widens (5.08x at `band_pct=0.02` down to 2.04x at
`band_pct=0.15`, holding `min_days_between_rebalances` fixed at its
cadence-matched value) -- the tolerance band is doing its intended job of
suppressing unnecessary rebalances relative to an always-rebalance
(`band_pct=0`) rule, it just cannot close the gap to a benchmark that never
sells at all. Total fees paid scale the same way ($3,514 at the tightest
band down to $1,410 at the widest, vs. DCA's much smaller pure-deposit fee
base).

### Sec 4.2 -- Deflated Sharpe Ratio >= 0.95

- Raw weekly Sharpe of the primary config's excess-return series:
  **-0.0791/week** (annualized ~-0.570) -- genuinely negative.
- `N` (raw trial count at this assessment): **1,467** (196 seed + 1,271
  new through this family, consistent with `state/trial_counter.json`:
  seed 196 + new 1271 = 1467).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **134**
  clusters.
- **DSR (N_eff-based, used for the decision): 0.000127.** Skew -1.303,
  kurtosis 14.51 (left-skewed, fat-tailed).
- DSR (raw-N, conservative reference): 0.000128.

**Sec 4.2: FAIL**, decisively (effectively zero either way).

### Sec 4.3 -- not run

Per established precedent (families 001/006/019/021/023/024/044/045/047),
sec 4.3 is only run when sec 4.1 passes. Here sec 4.1 fails not just for
the primary config but for **every single one of the 18 grid
configurations** (see below) -- a decisive, grid-wide result -- so sec 4.3
was not run, an explicit logged gap rather than a fabricated result.

### Sec 4.4 -- robust across parameters (grid diagnostic)

| band_pct \ min_days | 0 | 5 | 20 |
|---|---|---|---|
| 0.02 | no | no | no |
| 0.03 | no | no | no |
| 0.05 (primary col) | no | **no (primary)** | no |
| 0.08 | no | no | no |
| 0.10 | no | no | no |
| 0.15 | no | no | no |

**0 of 18 configurations (0.0%) beat DCA** on wealth AND Sharpe at 0.1%
fees -- decisively below the 2/3 (12/18) requirement, and the weakest
possible grid outcome (tied with family 047's 0/36 for "uniformly fails
everywhere"). Every config's Sharpe beats DCA's 0.802 (range 1.006-1.112),
but every config's wealth falls short of DCA's 2.937x (range 1.95x-2.14x)
-- the Sharpe-wins/wealth-loses pattern is uniform across the entire grid,
not a lucky or unlucky primary-config draw.

**Sec 4.4: FAIL**, decisively.

CSCV probability of backtest overfitting (diagnostic, portfolio-level
grid, 8 splits, 70 combinations): **PBO = 0.714** -- one of the higher
overfitting-risk values in this loop (behind only family 047's 0.857),
though with the whole grid already uniformly failing sec 4.1's win-rule,
this is best read as "the ranking among a set of uniformly-losing
configurations is itself unstable," not "there is a hidden good config the
CSCV method would help surface."

### Sec 4.5 -- distinctness

Not applicable; this family did not become a finalist.

## Verdict

**REJECTED.** Fails sec 4.1 at the primary config and across the entire
grid (0/18, 0%) -- the wealth leg loses to DCA by a wide margin even
though the Sharpe leg wins comfortably and as predicted by the prereg's
own transaction-cost framing. DSR effectively zero (sec 4.2 FAIL). Sec 4.3
not run (sec 4.1 already fails decisively across the whole grid, per
established precedent). CSCV PBO=0.714 (elevated). Holdout **not**
opened (rejected, not a finalist, per sec 8 step 8).

## Interpretation

This is the third fixed-equal-weight-target rebalancing design in this
loop (after family 013's `tilt_strength=0` corner and family 029's
risk-parity target) to lose decisively to DCA on wealth over this specific
BTC-gated 2014-2019 development window: BTC's return so thoroughly
dominates the other 4 assets' combined compounding that *any* rule
periodically trimming BTC back toward a bounded (here, fixed 20%) target
gives up a large share of BTC's own run-up, regardless of how cleverly the
rebalance *timing* is chosen. The drift-band trigger's genuine, verified
distinction from v2's closed C1/C2/C3 (path-dependent timing vs. fixed
calendar) and from families 002/013/029/043 (a fixed target enforced only
when meaningfully drifted, rather than a varying target or a cross-asset
rotation) does not change this outcome, because the underlying exposure
problem -- holding a bounded 20% of a single dominant winner instead of an
unbounded, ever-larger share -- is a property of the *target itself* being
fixed and equal, not of *when* it gets enforced. The Sharpe-side result
(every grid config beats DCA's Sharpe, uniformly) is consistent with the
prereg's own expected-sign framing: a tolerance-band rule does deliver a
smoother, higher-Sharpe ride than buy-and-hold DCA over this window, and
does reduce turnover monotonically as the band widens relative to an
always-rebalance rule -- but sec 4.1's combined wealth-AND-Sharpe bar,
applied against a benchmark that structurally never sells its winners,
is not clearable by a fixed-target design in a BTC-dominated development
window, band-triggered or not.

## Judgment calls made in this iteration

1. **Caught and fixed a real `PRIMARY_CONFIG`-grid mismatch before any
   backtest ran.** The prereg's first draft declared `band_pct=0.05` as
   primary against a grid of `[0.02, 0.04, 0.06, 0.08, 0.10, 0.15]`, which
   does not contain 0.05 -- the import-time assertion (family 021's own
   lesson, applied here as a hard `assert` rather than a runtime check)
   caught this immediately on the first module import, before the grid or
   any implementation check ran. Fixed by swapping the grid's second value
   from 0.04 to 0.03 (keeping 0.05 as the natural primary), and updated
   `prereg.md`'s grid table to match, documented here in the open per the
   plan's incremental-commit discipline (this is exactly the kind of
   pre-run catch the assertion exists for, not a silent edit).
2. **Rebalance-check cadence fixed at weekly (deposit day), not a tunable
   grid parameter**, per family 002/010/013's precedent for keeping
   cadence-like choices out of the grid and per the task's own framing
   ("checked at each week-end decision day"). This kept the family at 2
   tunable parameters, well under the 5-parameter ceiling, while still
   giving the drift trigger meaningful room to act (band_pct spans a
   6-value range, min_days_between_rebalances a 3-value range).
3. **Non-trigger week-ends invest the deposit only (no rebalancing of
   existing holdings)**, matching a literal reading of the queue's own
   "avoid unnecessary turnover/fees between rebalances" framing -- existing
   positions are left completely alone unless the band is breached, so the
   strategy behaves exactly like plain DCA between trigger events. This
   choice is what makes the turnover-vs-band-width monotonic relationship
   interpretable as the mechanism's intended cost-avoidance behavior.
4. **Reported turnover and total fees prominently** (not just the sec 4.1
   pass/fail), per the task's explicit instruction that this family's own
   hypothesized channel is fees/turnover/Sharpe rather than raw wealth --
   the results above show the mechanism doing exactly what it claims
   (turnover falls monotonically as the band widens) even though it still
   cannot outrun DCA's structural zero-sell turnover floor, and even
   though the wealth leg's failure is unrelated to the turnover story (it
   is driven by the fixed-target's bounded BTC exposure, not by fee drag).
5. **Sec 4.3 skipped entirely** (not even partially run), since sec 4.1
   failed not just for the primary config but for all 18 grid
   configurations uniformly -- a more decisive, faster-to-establish
   failure than several prior families (e.g. 046/047) needed a partial
   sec 4.2/4.3 run to confirm. Logged here as an explicit, reasoned gap
   per this iteration's time-budget instruction.
