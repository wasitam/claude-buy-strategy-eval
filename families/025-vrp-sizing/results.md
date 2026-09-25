# Family 025 results: Variance risk premium (VRP) sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively:
it beats plain DCA on **0 of 5** core assets, on wealth AND Sharpe, at
either fee level (need >=3). Sec 4.4's grid diagnostic fails completely:
**0 of 36** configurations (0.0%) reach the combined wealth-AND-Sharpe
majority bar (need >=2/3 = 24/36) -- every single config in the 36-config
grid loses on wealth on all 5 assets, at both fees. Sec 4.2's Deflated
Sharpe is effectively zero (negative raw pooled excess Sharpe). Sec 4.3
was **not** run, per this loop's established precedent of running it only
when sec 4.1 passes. Holdout was **not** opened.

## Rigorous distinction from families 003 and 016, verified on real data

prereg.md's required numeric-contrast argument (VIX-elevated does not
imply VRP-elevated, and vice versa) was additionally verified mechanically
before the grid ran, per the task's explicit instruction, by
cross-tabulating this family's primary-config `elevated_t` flag against
family 016's own primary-config `elevated_t` flag (VIX alone, top decile
of its own trailing percentile), recomputed on the same 5 assets' dates:

| Asset | This family's elevated frac | This family's compressed frac | Family 016's elevated frac | Flag agreement | Days where ONLY this family flags elevated | Days where ONLY family 016 flags elevated |
|---|---|---|---|---|---|---|
| SP500 | 3.52% | 3.96% | 4.09% | 95.89% | 409 | 540 |
| GOLD | 12.85% | 14.40% | 11.06% | 90.57% | 272 | 185 |
| SILVER | 15.40% | 18.37% | 11.05% | 85.67% | 453 | 242 |
| BTC | 14.23% | 16.98% | 9.83% | 78.42% | 251 | 166 |
| OIL | 13.05% | 15.30% | 11.06% | 88.00% | 340 | 243 |

On every asset a substantial number of days fire ONE family's elevated
flag but not the other's (e.g. BTC: 251 days this family alone flags
elevated, 166 days family 016 alone flags elevated, only 24 days both
agree, out of 1,932 development days) -- confirming mechanically, not just
by prereg-text argument, that the spread logic is genuinely implemented
and does not accidentally collapse onto family 016's VIX-alone signal.
This matches prereg.md's worked numeric-contrast examples (a live-crisis
week where realized vol has caught up with VIX compresses the spread even
though VIX itself reads "elevated," and vice versa for a deceptively calm
VIX print sitting on unusually quiet realized vol). The run script's
sanity/distinctness gate (`distinct_from_016`, requiring `flag_agreement
< 98%` AND at least one disagreement day) passed on all 5 assets before
the grid was trusted.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (aggressive corner: `rv_lookback=20, elevated_pct=80, compressed_pct=20, buy_multiplier=3.0`) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (primary config and aggressive corner, family 021's principled "never invest" ceiling-bound method) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000` and `t=20000`; covers both the VIX-alignment leg and the realized-vol rolling-window leg) | PASS |
| Point-in-time macro data | N/A -- VIX is a daily market-price series, no ALFRED vintage concern (same as family 016) |

## Primary-config-in-grid verification

Verified programmatically at module import time
(`src/backtest/v3/strategies/vrp_sizing.py` asserts `PRIMARY_CONFIG in
grid_configs()` on import, per family 021's lesson) -- primary config
`rv_lookback=60, elevated_pct=90, compressed_pct=10, buy_multiplier=2.0`
is confirmed a genuine member of the 36-config grid.

## Pre-grid non-degeneracy check (per prereg.md, before the grid ran)

All 5 assets' elevated/compressed regime frequencies for the primary
config were non-trivial (3.5%-15.4% elevated, 4.0%-18.4% compressed --
see table above), neither near-0% nor near-100%, confirming the VRP
spread signal fires genuinely and non-degenerately on every asset, before
any backtest result was trusted.

## Primary configuration: `rv_lookback=60, elevated_pct=90, compressed_pct=10, buy_multiplier=2.0`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 78.261 | 85.277 | 0.15611 | 0.15310 | NO (wealth fails) |
| GOLD | 2.163 | 2.231 | 0.49935 | 0.50492 | NO |
| SILVER | 1.629 | 1.687 | 0.30852 | 0.31968 | NO |
| BTC | 9.471 | 9.856 | 1.07234 | 1.06731 | NO (wealth fails) |
| OIL | 1.155 | 1.180 | 0.21456 | 0.22782 | NO |

**Sec 4.1: FAIL** -- 0/5 core assets beat DCA on wealth AND Sharpe (need
>=3), at both 0.1% and 0.25% fees (0.25% results qualitatively identical,
see `_primary_per_asset.csv`). SP500 and BTC beat DCA on Sharpe alone
(consistent with the banking mechanic smoothing weekly returns, the same
pattern seen in every prior timing/banking family in this loop) but lose
on wealth on every single asset -- since sec 4.1 requires both metrics
simultaneously, none of these count.

### Grid diagnostic (sec 4.4)

**0 of 36 configurations (0.0%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fee -- need >=2/3 (24/36). Every
config loses on wealth on all 5 assets; the best any config manages is
3/5 assets beating on Sharpe ALONE (`cfg02`, `rv_lookback=20,
elevated_pct=80, compressed_pct=10, buy_multiplier=3.0`), never
accompanied by a wealth win anywhere. This is a uniform failure across the
entire parameter space, not a lucky/unlucky-corner issue.

**Sec 4.4: FAIL** (need >=24/36; got 0/36 = 0.0%).

CSCV probability of backtest overfitting (36-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.471** -- notably
higher than families 023/024's near-zero PBO. Read together with the
uniform 0/36 wealth failure, this suggests the grid's in-sample vs.
out-of-sample config ranking is close to a coin flip -- consistent with a
genuinely weak, noise-dominated signal across the grid (not a reliably
bad one nor a reliably lucky one), rather than evidence that any config
would look different out of sample. It does not change the sec 4.1/4.4
verdict, which rests on the decisive, uniform wealth shortfall itself.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  **-0.044932** (weekly, **-0.32401 annualized**) -- negative.
- `N` (raw trial count, whole-loop pool): **761** (196 seeded + 565 new,
  matching `state/trial_counter.json["new"]` = 565 after this family:
  196 + 565 = 761 = 725 + 36, consistent with family 024's 725-trial mark
  plus this family's 36-config grid).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **70**
  clusters (unchanged from families 023/024 -- this family's 36-config
  grid added 0 new distinct clusters at the rho>=0.5 threshold; its
  excess series correlate highly enough with existing sizing/vol/timing
  clusters, including families 003's and 016's own, to be absorbed into
  them).
- **DSR (N_eff-based): ~1.33e-40** -- effectively zero (a negative raw
  Sharpe can never clear a positive `SR0` threshold at any `N`).
- DSR (raw-N, conservative reference): ~9.73e-44, also effectively zero.

**Sec 4.2: FAIL**, decisively.

## Verdict

**REJECTED.** Sec 4.1 fails decisively (0/5 core assets beat DCA on both
wealth and Sharpe; need >=3/5). Sec 4.4 fails decisively (0/36 grid
configs reach the majority bar; need >=24/36, uniform failure across the
entire grid). Sec 4.2 fails decisively (DSR ~0, negative raw pooled excess
Sharpe). Sec 4.3 was not run (only run when sec 4.1 passes, per this
loop's established precedent). Holdout was **not** opened.

## Interpretation

The VRP-spread signal, like families 003's realized-vol signal and 016's
VIX-alone signal before it, reliably smooths the weekly return path on
some assets (SP500, BTC beat DCA on Sharpe alone) via the same
banking-and-burst reallocation mechanic every timing family in this loop
shares, but produces no wealth edge anywhere in its 36-point parameter
space, on any of the 5 core assets. Two candidate readings, consistent
with each other: (1) buying more when implied vol runs unusually far
above trailing realized vol tends to buy INTO episodes where realized vol
is about to catch up with (or has recently undershot relative to) implied
-- i.e., episodes still early in a vol-expansion regime -- rather than
genuinely mean-reverting panics, so the extra buying is not, on this
development sample, well-timed; and (2) as with family 016, VIX is an
SP500-specific implied-vol proxy applied cross-asset to gold/silver/BTC/
oil, whose own realized-vol dynamics are not driven by the same
equity-option-priced risk-premium channel the VRP literature was built
around, diluting whatever genuine premium effect might exist for SP500
itself. The markedly higher CSCV PBO (0.471, vs. near-zero for families
023/024) suggests the grid's internal config ranking carries little
out-of-sample information either way -- a diffuse, noise-dominated
parameter space rather than a reliably-wrong or reliably-lucky one -- but
this is a secondary diagnostic only; the decisive result is the uniform
0/36 wealth failure itself, which the CSCV reading does not change.

## Files

- `src/backtest/v3/strategies/vrp_sizing.py`
- `scripts/v3/run_025_vrp_sizing.py`
- `families/025-vrp-sizing/grid_results.csv`, `_primary_per_asset.csv`, `_run_output.json`
- `state/trials/new_025_*.csv` (36 files)
