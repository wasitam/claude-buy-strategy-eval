# Family 029 results: Risk-parity (inverse-volatility) rebalancing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively:
it loses to fixed-weight 5-asset DCA on **final wealth** at both fee levels
by a wide margin, even though its Sharpe is competitive with (and, for
several grid arms, better than) DCA's. **0 of 12 (0%)** grid configurations
reach the combined wealth-AND-Sharpe bar -- not even the family's own most
favorable corner passes. DSR is effectively zero. Holdout was **not**
opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **5-asset portfolio family** (sec 4.1's Portfolio line),
directly following families 002/010/013's precedent, vs. fixed-weight
5-asset DCA ($500/week/asset, never rebalanced, $2,500/week combined).
Category: **Rebalancing / allocation**. Explicitly **not** a re-test of
sec 7.2's closed C1/C2/C3 (fixed target weights; this family's targets are
volatility-dependent and time-varying, with an `equal_vol_override=True`
diagnostic mode nested as this family's equal-vol degenerate corner -- a
strictly larger, materially different parameter space, not the same rules
re-run). Explicitly **not** a re-test of family 013 either (momentum-tilted
rebalancing, this loop, REJECTED): family 013's target weight is driven by
trailing **return** (a directional/momentum bet), this family's is driven
by trailing **volatility** (a risk/dispersion bet); the two point in
*opposite* directions for BTC, which has both this universe's highest
trailing return and its highest volatility over the dev window -- family
013 wants more BTC on strong returns, this family wants less BTC on high
volatility, independent of return. See prereg.md's full side-by-side case.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`, bypasses the volatility/weight computation entirely, buys each asset's own $500 deposit share every week, no selling) reproduces fixed-weight 5-asset DCA exactly (bit-for-bit on units and pooled cash) | PASS |
| **Family-specific check**: `equal_vol_override=True` (the equal-vol-assumption edge case) reproduces family 013's independently-built equal-weight weekly-rebalance reference (`make_equal_weight_rebalance_decider`, a different module, no shared code path) bit-for-bit on units and pooled cash | PASS |
| That same `equal_vol_override=True` config's result **differs** from plain (never-rebalanced) DCA | PASS (confirmed to differ) |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| No-lookahead: perturbing all 5 assets' data after day t leaves every order on/before t unchanged (spot-check t = n-400, deep into the dev sample, i.e. well before 2020) | PASS |
| Point-in-time macro data | N/A -- price-only signal (5 assets' own OHLC), no macro/ALFRED series |
| Capital neutrality | N/A -- always exactly 100% invested (bounded weights sum to 1 every week), no cash-parking leg to violate neutrality, same as family 013's precedent |

## Pre-grid non-degeneracy sanity check (per prereg.md, run before the grid)

Confirmed on real development data, using the primary configuration's own
volatility estimates, **before** trusting any grid result:

| Asset | Average target weight (primary config, full dev calendar) |
|---|---|
| SP500 | 0.318 |
| GOLD | 0.310 |
| SILVER | 0.183 |
| **BTC** | **0.070** |
| OIL | 0.118 |
| (equal weight reference) | 0.200 |

BTC's average risk-parity weight (0.070) is materially below both gold's
(0.310, PASS) and the 0.20 equal-weight baseline (PASS) -- the mechanism is
doing what it is pre-registered to do: down-weighting the universe's
highest-volatility asset well below an equal-dollar allocation. The grid
was trusted only after this check passed.

## Primary configuration: `vol_lookback_days=126, min_weight=0.05, max_weight=0.40, smoothing_halflife_days=10`

### Sec 4.1 result (vs. fixed-weight 5-asset DCA), shared calendar 2014-09-17 to 2019-12-31 (BTC-gated)

| Fee | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (wealth)? | Beats DCA (Sharpe)? | Beats DCA (both)? |
|---|---|---|---|---|---|---|---|
| 0.1% | 1.447x | 2.937x | 0.7890 | 0.8017 | NO | NO | **NO** |
| 0.25% | 1.440x | 2.932x | 0.7638 | 0.7982 | NO | NO | **NO** |

**Sec 4.1: FAIL** at both fee levels, and on both legs this time (unlike
family 013, which passed Sharpe and only missed wealth) -- the primary
config loses on wealth by roughly half (1.44-1.45x built vs. DCA's 2.93x
on identical deposits) and, at the moderate `smoothing_halflife_days=10`
setting, also loses narrowly on Sharpe. Down-weighting BTC to an average
7% allocation removed most of the exposure to this dev window's single
largest compounder (BTC roughly 40x'd over 2014-09 to 2019-12), and the
lower-volatility assets it shifted weight toward (mostly SP500 and gold)
did not generate enough risk-adjusted return in this window to offset
that lost upside, even net of the intended variance reduction.

### Grid diagnostic (sec 4.4)

**0 of 12 configurations (0%) reach the combined wealth-AND-Sharpe bar** at
either fee level. Every grid arm loses to DCA on wealth by a wide margin
(1.42x-1.60x vs. DCA's 2.94x); the *tighter* bound pair (0.10, 0.30, which
allows BTC even less room to matter) actually comes closest to matching
DCA's Sharpe (e.g. `cfg00`: vol_lookback=63, bounds=(0.10,0.30), no
smoothing -- Sharpe 0.977 vs. DCA's 0.802, a genuine Sharpe win) but still
misses on wealth (1.60x vs. 2.94x) badly enough that no configuration
clears the combined bar. This is a clean, uniform pattern across all 12
configs, not a narrow miss concentrated in one corner.

**Sec 4.4: FAIL** (need >=2/3 = 8/12; got 0/12).

CSCV probability of backtest overfitting (12-config grid, 8 splits, 70
combinations, portfolio weekly returns at 0.1% fee): **PBO = 0.386** --
moderate.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's portfolio excess-return series
  (strategy weekly NAV return minus fixed-weight-5-asset-DCA weekly NAV
  return): **-0.0957/week** (annualized ~-69.0%) -- strongly negative,
  driven by the primary config's large wealth shortfall.
- `N` (raw trial count, whole-loop pool): **869** (196 seeded + 661 from
  families 001-028 + 12 new from this family's grid) -- matches the task's
  sanity check (196+661=857 prior; +12 new = 869).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **72** clusters
  (unchanged from family 028's 72 -- this family's 12 grid configs cluster
  entirely into already-existing clusters, adding 0 new distinct ones).
- **DSR (N_eff-based): 1.29e-05** -- essentially zero.
- DSR (raw-N, conservative reference): 8.12e-06.

**Sec 4.2: FAIL**, driven primarily by the negative raw excess-series
Sharpe (the large wealth shortfall dominates the weekly-return-based
excess series), not just the trial-count penalty (SR0 threshold at this
loop's N_eff=72 is 0.146/week -- far above the primary config's actual
-0.096/week).

### Robustness (sec 4.3)

**Not run.** Per the task's explicit instruction and the precedent set by
families 006/007/008/011/013 (sec 4.1 already decisive as a fail --
loses on both wealth AND Sharpe at both fees, not a near-miss -- only
attempted if sec 4.1 passes), the rolling-window / block-bootstrap /
placebo battery was skipped.

## Verdict

**REJECTED.** Sec 4.1 fails at both fee levels, on both wealth and Sharpe.
Sec 4.4's grid diagnostic fails outright (0/12, need >=8/12) -- not a
single grid configuration clears the combined bar. DSR is essentially zero
(N_eff-based: 1.29e-05), driven by a strongly negative raw excess-series
Sharpe. Holdout was **not** opened.

## Interpretation

In this BTC-gated 2014-09-to-2019-12 development window, BTC is such a
dominant source of the 5-asset universe's total compounding that any
mechanism which structurally underweights it relative to equal-dollar DCA
-- whether family 013's rebalancing-toward-relative-losers or this
family's rebalancing-toward-lower-volatility-assets -- gives up more
terminal wealth than it recovers in risk-adjusted terms. Risk parity's
core premise (equalizing risk contribution improves Sharpe) shows some
support at the grid's tighter-bound corner (`cfg00`'s Sharpe of 0.977
genuinely beats DCA's 0.802), but even there the wealth cost of
underweighting BTC is too large to clear sec 4.1's "both wealth AND
Sharpe" bar. This reads as a genuine, non-parameter-tunable finding about
this specific development window (BTC's short, unusually strong dev-period
history dominates the comparison) rather than a bug or a fixable
implementation issue -- consistent with the plan's sec 12 caveat that
"BTC's development period is short... any BTC-dependent result should be
read with caution," and a second instance (after family 013) of a
rebalancing-style family failing specifically because it trims exposure to
this window's biggest compounder. A family in this category may do better
in a development window, or on a universe, where no single asset so
thoroughly dominates total portfolio compounding; that is a structural
observation for the report, not a reason to retune this family (sec 5.4/
7.1's discipline against tuning after seeing results applies equally to
non-holdout dev results here).

## Judgment calls

- **Vol estimator**: trailing realized volatility of daily log returns
  (simple rolling stdev), the most standard risk-parity convention,
  chosen over more elaborate estimators (EWMA, GARCH) to keep the family
  well under the 5-parameter ceiling and avoid adding tunable decay-rate
  parameters that would each need their own literature justification.
- **Smoothing implementation**: EMA smoothing of the already-clipped/
  renormalized weight sequence (rather than smoothing the raw volatility
  estimate before clipping) was chosen because it provably preserves both
  the sum-to-1 and per-asset-bound invariants without any re-clip step
  (a convex combination of two valid weight vectors is itself valid) --
  this was verified analytically in prereg.md before implementation, not
  discovered by trial and error.
- **Startup-period volatility fallback**: switched from an initially-coded
  backward-fill (which would have leaked future data into the first few
  days of the 1930s+ SP500 calendar) to a strictly causal forward-fill +
  constant fallback before running any backtest, per this iteration's
  explicit no-lookahead discipline -- caught during implementation, not
  after seeing results, so no bugfix-log entry was needed (no trial was
  run with the flawed version).
