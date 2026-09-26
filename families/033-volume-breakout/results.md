# Family 033 results: Volume-confirmed breakout sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 as
decisively as a strategy can fail: at `normal_buy_mult=1.0`, the cash cap
(sec 3.2) binds on every single decision day, so the strategy's wealth and
Sharpe are **bit-for-bit identical to plain DCA on all 5 core assets, at
both fee levels** -- not merely close, but numerically indistinguishable
to the last reported digit (see the per-asset table below). Sec 4.4's
grid diagnostic also fails uniformly (0/36 configs reach the combined
wealth-AND-Sharpe majority bar). Sec 4.2's DSR is exactly 0 (the primary's
pooled excess-return series is identically zero, since the strategy IS
DCA). Sec 4.3 was **not** run, per the loop's established time-budget
convention (run in full only if sec 4.1 passes). Holdout was **not**
opened (not a finalist).

## Category and the fourfold distinction from families 001/005/020/028

Filed as **Trend / time-series momentum exit** (research-loop-plan-v3.md
sec 4.5's category list), the same category as families 001, 005, 020 and
028. The required distinction (full argument in `prereg.md`): family 033
is the **first and only** trend family in this loop to reference trading
volume at all, and its entire mechanism is a **joint AND** of two
conditions -- a new N-day price high (a materially shorter 20-60 trading-
day window than family 020's ~252-day/365-calendar-day 52-week-high
window) **and** that day's volume exceeding `volume_surge_multiple` times
its own trailing average volume. Family 001 (single MA vs. price), family
005 (sign of trailing 12-month return), family 020 (price-only proximity
to a 52-week high) and family 028 (dual-MA crossover) each use price data
exclusively and have no volume leg to combine with anything. The pre-grid
sanity check below empirically confirms the AND is load-bearing: the joint
condition fires strictly less often than the price-only leg alone on every
one of the 5 core assets (e.g. SP500: 14.2% of days are a new 40-day high,
but only 0.6% are a new 40-day high WITH a qualifying volume surge).

## Data reachability: reusing family 021's Volume-feasibility finding

Per this iteration's task instruction, this family reused family 021's
already-established Volume-data feasibility finding
(`families/021-amihud-illiquidity/prereg.md`) rather than re-deriving it
from scratch: `Volume` coverage on development data is 76.2% (SP500, all
gaps pre-1950), 91.5% (GOLD), 86.4% (SILVER, the noisiest), 100.0% (BTC)
and 99.9% (OIL) -- no re-verification of the raw coverage numbers was
needed. This family's own trailing-volume-average computation applies the
same "never fabricate from a bad print" rule family 021 established:
zero/missing-volume days are excluded from the trailing average's
population (not imputed), and the average is only trusted once at least
half the trailing window has valid observations. No new Volume-data quirk
was found beyond what family 021 already documented.

## Pre-grid sanity checks (per prereg.md and this iteration's task brief)

1. **PRIMARY_CONFIG is a member of the declared grid:** verified via a
   module-level assertion in `volume_breakout.py`
   (`assert PRIMARY_CONFIG in grid_configs()`, executed automatically on
   import) and re-confirmed in the run script before the grid ran. No
   mismatch found (unlike family 021's first-run bug, caught here before
   any code ran at all).

2. **Joint price+volume trigger fires non-trivially, and strictly rarer
   than the price-only leg alone** (primary config: `window=40`,
   `volume_surge_multiple=1.5`):

| Asset | Dev days | Price-only-high frac. | Joint (price AND volume) frac. | Joint rarer than price-only? |
|---|---|---|---|---|
| SP500 | 23,109 | 14.22% | 0.60% | Yes |
| GOLD | 4,848 | 11.55% | 0.54% | Yes |
| SILVER | 4,850 | 10.37% | 0.70% | Yes |
| BTC | 1,932 | 11.18% | 5.59% | Yes |
| OIL | 4,857 | 10.62% | 0.45% | Yes |

All 5 assets land comfortably inside the (0.1%, 50%) non-degeneracy band,
and the joint condition is meaningfully rarer than the price-only leg on
every asset (by roughly 2x on BTC to over 20x on OIL/SP500/GOLD) --
concrete, pre-grid evidence the AND is doing real work, not a near-
tautology with either leg alone.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (aggressive grid corner: `window=20, volume_surge_multiple=1.5, breakout_buy_mult=2.5, normal_buy_mult=0.75`) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (primary; family 021's principled "never invest" ceiling bound) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (aggressive corner) | PASS |
| No-lookahead (OHLC only, families 001-032 convention; `t=6000`, `t=20000`) | PASS |
| **No-lookahead, Volume-aware** (this family's own extra requirement: perturbing future Volume, not just OHLC, with an independent random-magnitude draw scaled to the asset's own historical volume level; `t=6000`, `t=20000`) | PASS |

The Volume-aware no-lookahead check is this family's own addition beyond
the standard convention (per this iteration's task brief: "both the
trailing-high and trailing-volume-average computations must be strictly
causal"). It confirms `compute_trailing_volume_avg`'s `shift(1)` correctly
excludes day `t`'s own volume from its own trailing average, in addition
to the existing OHLC-based check covering the price leg.

## Sec 4.1 result (vs. plain per-asset DCA), development windows

Primary config: `window=40, volume_surge_multiple=1.5, breakout_buy_mult=2.0,
normal_buy_mult=1.0` (`max_lump_multiple=4.0` fixed).

| Asset | Strategy wealth/invested (0.1%) | DCA wealth/invested (0.1%) | Strategy Sharpe (0.1%) | DCA Sharpe (0.1%) | Beats DCA (both, 0.1%)? |
|---|---|---|---|---|---|
| SP500 | 85.27722 | 85.27722 | 0.153097 | 0.153097 | NO (identical) |
| GOLD | 2.23123 | 2.23123 | 0.504917 | 0.504917 | NO (identical) |
| SILVER | 1.68666 | 1.68666 | 0.319677 | 0.319677 | NO (identical) |
| BTC | 9.85568 | 9.85568 | 1.067309 | 1.067309 | NO (identical) |
| OIL | 1.17986 | 1.17986 | 0.227824 | 0.227824 | NO (identical) |

**0/5** assets beat DCA on both wealth AND Sharpe, at both 0.1% and 0.25%
fees -- and every number is bit-for-bit equal to DCA's own number, to the
6th significant digit shown. **Sec 4.1: FAIL**, as decisively as
possible.

### Why the primary is numerically identical to DCA: a genuine cash-cap no-op, not a bug

This is the key finding of this iteration, worth stating plainly. With
`normal_buy_mult=1.0`, a non-breakout week buys the FULL weekly deposit
(no reserve is ever banked above what interest alone contributes), and the
joint breakout trigger is rare (0.45%-5.6% of trading days, per the sanity
table above -- rarer still once restricted to WEEK-END decision days,
which is when the decider actually acts). On the occasional week whose
decision day falls on a breakout trigger, the target buy
(`breakout_buy_mult * weekly_deposit`, up to 2.0x) is capped by the
engine's own cash cap (sec 3.2: `buy_usd = max(0, min(buy_usd, cash))`) to
whatever cash is actually on hand -- and because no week ever banks a
reserve when `normal_buy_mult=1.0`, that cash is essentially just the
current week's own $500 deposit plus a negligible sliver of accumulated
interest. The requested 1.5x-2.5x multiplier therefore almost never has
the cash to actually execute above 1.0x, so the strategy's REALIZED buy
schedule collapses to plain DCA's own schedule -- verified directly: the
reported wealth/Sharpe numbers for the primary config match DCA's own
numbers to every digit shown, for all 5 assets, at both fee levels. This
is confirmed to be a **cash-cap mechanics effect, not a code bug**: the
implementation checks above (degenerate-equals-DCA, no-lookahead, no
negative cash) all pass on this exact configuration, and the grid's
`normal_buy_mult=0.75` arm (identical `window`/`volume_surge_multiple`/
`breakout_buy_mult`, only `normal_buy_mult` different) produces materially
different, non-DCA-identical results (see the grid diagnostic below) --
proof the code path is live and responsive to that one parameter, and that
`normal_buy_mult=1.0` specifically starves the mechanism of any reserve to
spend. This is a genuine, if unfortunate, primary-configuration design
choice: the intent in `prereg.md` was for `normal_buy_mult=1.0` to mean
"literally normal, funded from interest/slack alone," but the joint
condition's rarity combined with weekly (not daily) decision cadence means
that slack is never large enough to matter. Per sec 4.4, "the loop never
switches to a better-looking configuration after seeing results" -- the
primary's result stands as tested, and the queue-replenishment note below
flags this specific design trap for any future volume/breakout-sizing
family so it is not repeated.

## Grid diagnostic (sec 4.4)

**0 of 36 configurations (0.0%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets, 0.1% fee) -- a uniform failure across the
whole 36-config grid (need >=24/36 = 2/3). The grid splits cleanly into
two regimes that have nothing to do with `window`, `volume_surge_multiple`
or `breakout_buy_mult` (which have essentially NO visible effect on the
win counts) and everything to do with `normal_buy_mult`:

- **All 18 `normal_buy_mult=1.0` configs:** 0/5 wealth, 0/5 Sharpe (the
  cash-cap no-op described above, reproduced across every `window`/
  `volume_surge_multiple`/`breakout_buy_mult` combination).
- **All 18 `normal_buy_mult=0.75` configs:** 3/5 wealth, but only 2/5
  Sharpe (fails the combined wealth-AND-Sharpe bar on at least 1 of the
  3 wealth-winning assets) -- consistently, again regardless of `window`/
  `volume_surge_multiple`/`breakout_buy_mult`. This pattern (uniform
  across the breakout-signal parameters, sensitive only to the cash-
  banking parameter) is itself evidence that in this development sample,
  the differentiator is the interest-banking/timing effect of holding back
  25% of every non-breakout week's deposit as cash (which then compounds
  at historical IRX rates, particularly over SP500's ~92-year dev window,
  echoing family 021's own interest-income finding), not the volume-price
  breakout signal itself. **Sec 4.4: FAIL** (need >=24/36; got 0/36).

CSCV probability of backtest overfitting (36-config grid, 8 splits, 70
combinations, SP500 weekly strategy returns at 0.1% fee): **PBO = 0.0** --
the lowest of any family tested in this loop so far. This is consistent
with the grid's bimodal, parameter-insensitive structure described above:
with only two effectively distinct outcomes across all 36 configs (driven
entirely by `normal_buy_mult`), the in-sample best-vs-worst split ranking
reproduces trivially out-of-sample, which is a sign of a degenerate grid
rather than a genuinely well-behaved one -- reported as a diagnostic, not
overridden.

## Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series
  (equal-weight average of the 5 per-asset excess series, strategy weekly
  NAV return minus DCA weekly NAV return): **exactly 0** (the primary
  config's realized trading is identical to DCA, so its excess return is
  identically zero every week, on every asset).
- `N` (raw trial count, whole-loop pool): **1,001** (196 seeded + 769 from
  families 001-032 + 36 new from this family's grid).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **97**
  clusters (up from 79 at family 032 -- this family's 36 grid configs
  opened at least one new cluster distinct from the existing 79, though
  the bimodal grid means many of the 36 likely cluster tightly with each
  other or with existing near-zero-excess trials).
- **DSR (N_eff-based): 0.0** -- the primary's Sharpe is exactly 0, so no
  positive DSR is possible regardless of the SR0 threshold (SR0=0.139/week
  at this loop's N_eff=97).
- DSR (raw-N, conservative reference): 0.0 (SR0=0.146/week at raw N=1001).

**Sec 4.2: FAIL**, trivially -- a zero excess-return series cannot clear
any positive trial-adjusted bar.

## Sec 4.3

**Not run in full**, per the plan's own time-budget convention (rolling
windows / block bootstrap / placebo are only run in full when sec 4.1
passes) -- sec 4.1 already fails as decisively as possible (0/5 assets,
primary literally identical to DCA), so the n_sims=60 robustness battery
would not change the verdict.

## Verdict

**REJECTED.** Sec 4.1 fails as decisively as a strategy can fail (0/5
assets, primary config numerically identical to DCA due to a cash-cap
no-op), sec 4.4's grid diagnostic fails uniformly (0/36), and sec 4.2's
DSR is exactly zero. Sec 4.3 was not run per the established time-budget
convention. Holdout was **not** opened.

## Interpretation and a design lesson for the queue

The Karpoff/Lee-Swaminathan volume-confirmed-continuation hypothesis was
never actually tested at full strength by this family's primary
configuration: `normal_buy_mult=1.0` combined with the joint condition's
inherent rarity (0.45%-5.6% of trading days, fewer still on week-end
decision days specifically) meant the engine's cash cap prevented the
breakout multiplier from ever executing above 1.0x in practice, making the
"tested" strategy indistinguishable from plain DCA. The `normal_buy_mult=
0.75` grid arm, which DOES bank a usable reserve, shows a materially
different (3/5 wealth, 2/5 Sharpe) but still sub-4.1-bar pattern that
tracks family 021's own interest-income finding more than any volume-
price signal -- window/volume-surge-threshold/breakout-multiplier changes
produced no visible difference at all across the whole grid, suggesting
that even at `normal_buy_mult=0.75`, this development sample's rare
breakout events are too infrequent to be the actual source of whatever
edge exists (which looks like interest banking, not signal timing). A
future family testing a similarly rare, joint, or compound sizing signal
should set the primary configuration's "otherwise" multiplier below 1.0
(so a cash reserve exists to fund the signal at all) rather than exactly
1.0 -- flagged here explicitly so this specific trap is not repeated.
