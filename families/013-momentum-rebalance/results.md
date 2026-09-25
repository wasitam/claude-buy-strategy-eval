# Family 013 results: Momentum-tilted rebalancing

**Verdict: REJECTED.** The primary configuration fails sec 4.1: it beats
plain fixed-weight 5-asset DCA on Sharpe but **not** on final wealth, at
either fee level (sec 4.1 requires both). Only 2/16 (12.5%) grid
configurations reach the combined wealth-AND-Sharpe bar, both of them the
most aggressive `tilt_strength=2.0` arms — well short of sec 4.4's 2/3
threshold. DSR is effectively zero. Holdout was **not** opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **5-asset portfolio family** (sec 4.1's Portfolio line),
directly following family 002's and family 010's precedent, vs.
fixed-weight 5-asset DCA ($500/week/asset, never rebalanced, $2,500/week
combined). Explicitly **not** a re-test of sec 7.2's closed C1/C2/C3
(those used fixed target weights; this family's targets are
momentum-dependent and time-varying, with C1's equal-weight rebalance
nested as this family's `tilt_strength=0` limit — a strictly larger,
materially different mechanism, not the same rules re-run). Explicitly
**not** a re-test of family 002 either (dual momentum's binary in/out
rotation, can exit to 100% cash, category "Cross-asset rotation /
relative strength" vs. this family's continuous always-fully-invested
tilt, category "Rebalancing / allocation" — see prereg.md's full
side-by-side case).

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`, bypasses the momentum/weight computation entirely, buys each asset's own $500 deposit share every week, no selling) reproduces fixed-weight 5-asset DCA exactly (bit-for-bit on units and pooled cash) | PASS |
| **Family-specific check**: `tilt_strength=0, enabled=True` (a real grid arm) reproduces an independently-built equal-weight weekly-rebalance reference portfolio (v2 Strategy C1-equivalent) bit-for-bit on units and pooled cash | PASS |
| **Family-specific check**: that same `tilt_strength=0` config's result **differs** from plain (never-rebalanced) DCA -- confirming "degenerate" for this family means C1-equivalent, not DCA-equivalent, exactly as documented in prereg.md before any backtest ran | PASS (confirmed to differ) |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| No-lookahead: perturbing all 5 assets' data after day t leaves every order on/before t unchanged (spot-check t = n-400, deep into the sample) | PASS |
| Point-in-time macro data | N/A -- price-only signal (5 assets' own OHLC), no macro/ALFRED series |

**What "degenerate config" means for this family (per family 010's
degenerate-config-trap lesson, applied here as instructed):** unlike a
timing/banking strategy where the degenerate case is usually "the signal
never fires, so behavior reduces to plain DCA," a rebalancing family
*always* rebalances, even at its most neutral parameter setting. This
family therefore has **two** distinct implementation-check reference
points, both verified above: (1) `enabled=False`, a strategy-module-level
bypass flag used only to prove the module *can* reproduce DCA exactly
(required by sec 3.2 check 1's literal wording), and (2)
`tilt_strength=0, enabled=True`, the strategy's actual zero-tilt grid arm,
which is verified to equal a fixed equal-weight rebalance (C1-equivalent)
and to differ from plain DCA. Both were declared in prereg.md before any
backtest ran, not discovered afterward.

## Primary configuration: `lookback_days=252, tilt_strength=1.0, min_weight=0.05, max_weight=0.40`

### Sec 4.1 result (vs. fixed-weight 5-asset DCA), shared calendar 2014-09-17 to 2019-12-31 (BTC-gated)

| Fee | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (wealth)? | Beats DCA (Sharpe)? | Beats DCA (both)? |
|---|---|---|---|---|---|---|---|
| 0.1% | 2.629x | 2.937x | 0.9329 | 0.8017 | NO | YES | **NO** |
| 0.25% | 2.581x | 2.932x | 0.9153 | 0.7982 | NO | YES | **NO** |

**Sec 4.1: FAIL** at both fee levels — Sharpe improves meaningfully (the
tilt does reduce return volatility relative to fixed-weight DCA, plausibly
by trimming into strength and adding to weakness within its bounds more
than DCA's pure accumulate-and-hold does), but final wealth falls short by
a material margin (about 10-12% less wealth built on identical deposits).
The rebalancing/momentum tilt is giving up more upside (mechanically
selling down BTC and SP500 — this window's biggest compounders — whenever
their weight nears the 0.40 cap) than it recovers in downside protection.

### Grid diagnostic (sec 4.4)

**2 of 16 configurations (12.5%) reach the combined wealth-AND-Sharpe bar**
at 0.1% fees — both `tilt_strength=2.0` (`cfg07`: lookback=126,
bounds=(0.05,0.40); `cfg15`: lookback=252, bounds=(0.05,0.40)), i.e. only
the single most aggressive tilt setting in the grid, and only paired with
the looser (0.05, 0.40) bound pair, not the tighter (0.10, 0.30) pair.
Every `tilt_strength` in `{0.0, 0.5, 1.0}` fails on every lookback/bound
combination. This is a fairly clean monotonic pattern (stronger tilt does
progressively better, up to the grid's own ceiling) but it means the
primary configuration -- chosen *before* seeing any of this, at a
moderate, literature-anchored `tilt_strength=1.0` -- sits well short of
where the grid's only passing corner is. Per sec 4.4's own rule, this
grid result is diagnostic only and **cannot promote `cfg07`/`cfg15` to
primary status**; the family's verdict rests on the pre-declared primary
configuration, which fails.

**Sec 4.4: FAIL** (need >=2/3 = 11/16; got 2/16).

CSCV probability of backtest overfitting (16-config grid, 8 splits, 70
combinations, portfolio weekly returns at 0.1% fee): **PBO = 0.614** —
moderately high, consistent with a grid where the "best" configuration on
one data split is not reliably the best on another, i.e. even the
grid's two nominally-passing configs are not a robustly identifiable
"best corner."

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's portfolio excess-return series
  (strategy weekly NAV return minus fixed-weight-5-asset-DCA weekly NAV
  return): **-0.0499/week** (annualized ~-36.0%) — negative, consistent
  with the primary config's sec 4.1 wealth shortfall dominating the
  excess series even though per-period Sharpe alone favors the strategy.
- `N` (raw trial count, whole-loop pool): **451** (196 seeded + 239 from
  families 001-011 + 16 new from this family's grid) -- matches the task's
  sanity check (196+239=435 prior; +16 new = 451).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **40** clusters
  (unchanged from family 011's 40 -- this family's 16 grid configs cluster
  entirely into already-existing clusters, adding 0 new distinct ones).
- **DSR (N_eff-based): 3.44e-04** — essentially zero.
- DSR (raw-N, conservative reference): 6.49e-05.

**Sec 4.2: FAIL**, driven primarily by the negative raw excess-series
Sharpe (the wealth shortfall dominates the weekly-return-based excess
series even though Sharpe-on-NAV alone favors the strategy — these are
different objects: sec 4.1's Sharpe check is computed on each series'
own NAV path, while sec 4.2's DSR runs on the *difference* series,
which is more sensitive to the wealth-path gap), not just the trial-count
penalty, though the penalty (N_eff=40) would have made passing hard even
with a positive raw Sharpe.

### Robustness (sec 4.3)

**Not run.** Per the task's explicit instruction and the precedent set by
families 006/007/008/011 (sec 4.1 already decisive as a fail -- not a
near-miss, since the wealth leg misses outright at both fees -- only
attempted if sec 4.1 passes), the rolling-window / block-bootstrap /
placebo battery was skipped.

## Verdict

**REJECTED.** Sec 4.1 fails at both fee levels (Sharpe passes, wealth
does not -- both required). Sec 4.4's grid diagnostic fails (2/16, need
>=11/16), with only the grid's single most aggressive tilt setting
clearing the bar and even that pair only moderately CSCV-robust
(PBO=0.614). DSR is essentially zero (N_eff-based: 3.44e-04), driven by a
negative raw excess-series Sharpe. Holdout was **not** opened.

## Interpretation

The momentum tilt, at the literature-anchored moderate strength chosen as
primary (`tilt_strength=1.0`), improves risk-adjusted return (Sharpe) over
fixed-weight DCA but at the cost of giving up terminal wealth -- in this
development window (2014-09 to 2019-12, BTC-gated, so dominated by BTC's
and SP500's outsized compounding), the tilt's weight caps mechanically
trim the biggest winners on their way up more than they protect on the
way down, and the "buy relative losers" side of the mechanism does not
recover enough of that foregone upside from the assets it tilts into
(mostly gold, silver, oil in this window -- the weaker performers).
Only the grid's most extreme tilt setting (`tilt_strength=2.0`) reaches
both bars, and even there CSCV flags real overfitting risk. This reads as
a genuine mechanism weakness for this specific window and asset mix, not
an implementation bug: the base rebalancing premium (confirmed by v2's
closed C1/C2/C3) is a volatility-harvesting effect that works best among
assets with similar long-run trend strength; layering a momentum tilt on
top, in a 5-asset universe with one dramatically-outperforming asset
(BTC) and one strongly-trending one (SP500) over most of this window,
means the tilt spends much of its time fighting the very trend that is
carrying fixed-weight DCA's wealth lead, rather than harvesting
cross-sectional dispersion the way the Asness/Moskowitz/Pedersen
literature's more diversified equity/bond/commodity universes do. This is
an informative negative result for this specific mechanism (a continuous
z-score tilt on top of weekly rebalancing, bounded at these specific
weight caps) as specified -- it does not rule out other rebalancing-tilt
constructions (e.g. tilting rebalancing *frequency* rather than target
weight, or tilting only among the non-BTC assets), but those would be
materially different mechanisms requiring their own pre-registration.

## Data reachability

No issues. All 5 core assets' own OHLC and IRX are already-cached core-
asset series reachable via `src.backtest.v3.data.load_dev()`. No external
macro/alternative data was needed for this family's price-only signal.
