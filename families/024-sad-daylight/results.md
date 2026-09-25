# Family 024 results: SAD (Seasonal Affective Disorder) / daylight-length deposit timing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively:
it beats plain DCA on wealth AND Sharpe on **0 of 5** core assets (need
>=3), at both 0.1% and 0.25% fees -- the strategy beats DCA's Sharpe on
4/5 assets but loses on WEALTH on all 5/5 assets, so the combined
wealth-AND-Sharpe requirement is never met anywhere. Sec 4.4's grid
diagnostic fails equally decisively: **0 of 18** configurations (0.0%)
reach the combined wealth-AND-Sharpe majority bar -- need >=2/3 (12/18).
Sec 4.2's Deflated Sharpe is effectively zero (negative raw pooled excess
Sharpe). Sec 4.3 (rolling windows / bootstrap / placebo) was **not** run,
per this loop's established precedent of running it only when sec 4.1
passes. Holdout was **not** opened.

## Astronomical sanity spot-check (before any backtest was trusted)

`daylight_hours()` was verified against known solstice/equinox values at
the fixed 40N reference latitude across 4 separate years (2001, 2004 leap,
2016 leap, 2019): Dec 21 gives ~9.16h (known ~9h20m=9.33h), Jun 21 gives
~14.84h (known ~14h49m=14.82h), both equinoxes give ~11.90-11.94h (known
~12h00m) -- correctly signed (Dec 21 shortest, Jun 21 longest) and within
a few minutes of the true values on every year checked, confirming no
day-of-year indexing bug before any price data was touched.

## Primary-config-in-grid verification (per family 021's lesson)

Verified programmatically at module import time (`sad_daylight.py` asserts
`PRIMARY_CONFIG in grid_configs()` on import, raising `AssertionError`
otherwise) and re-checked in the run script before the grid ran. Primary
config `tilt_strength=0.5, power=1.0, max_lump_multiple=8` is a genuine
member of the 18-config grid; no mismatch found.

## Pre-grid non-degeneracy sanity check (per prereg.md, run before the grid)

| Asset | n trading days | mult(t) min | mult(t) max | mult(t) std | Distinct values | Non-degenerate? |
|---|---|---|---|---|---|---|
| SP500 | 23,109 | 0.500 | 1.500 | 0.345 | 183 | PASS |
| GOLD | 4,848 | 0.500 | 1.500 | 0.344 | 183 | PASS |
| SILVER | 4,850 | 0.500 | 1.500 | 0.344 | 183 | PASS |
| BTC | 1,932 | 0.500 | 1.500 | 0.347 | 183 | PASS |
| OIL | 4,857 | 0.500 | 1.500 | 0.344 | 183 | PASS |

The multiplier spans its full designed [0.5, 1.5] range on every asset
(`tilt_strength=0.5` gives `1 -/+ 0.5`), varies continuously through the
year (183 distinct values -- one per roughly 2-day step, since daylight
length changes smoothly), and is symmetric with the expected standard
deviation across all 5 assets regardless of trading-calendar length --
confirms the daylight-length signal fires non-trivially, exactly as
designed, before any backtest result was trusted.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (aggressive corner: `tilt_strength=0.7, power=2.0, max_lump_multiple=12`) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000` and `t=20000`; the signal is a deterministic calendar function with no price dependence, so this is a trivial pass in principle, and was still run and verified explicitly per the task's instruction) | PASS |
| Point-in-time macro data | N/A -- calendar-only signal, no macro dependence |
| Capital deployed never exceeds cumulative deposits + interest (primary config and aggressive corner, family 021's principled-bound method: a "never invest" reference run gives the interest ceiling) | PASS |

No implementation-check failures or bugfixes were needed for this family
(no entry added to `state/bugfix_log.md`).

## Primary configuration: `tilt_strength=0.5, power=1.0, max_lump_multiple=8`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.23765 | 85.27722 | 0.153607 | 0.153097 | NO (wealth loses) |
| GOLD | 2.215679 | 2.231232 | 0.506154 | 0.504917 | NO (wealth loses) |
| SILVER | 1.676190 | 1.686660 | 0.322341 | 0.319677 | NO (wealth loses) |
| BTC | 9.626186 | 9.855679 | 1.099233 | 1.067309 | NO (wealth loses) |
| OIL | 1.161864 | 1.179855 | 0.224341 | 0.227824 | NO (both lose) |

**Sec 4.1: FAIL** -- 0/5 core assets beat DCA on wealth AND Sharpe (need
>=3), at both 0.1% and 0.25% fees (0.25% results qualitatively identical:
still 0/5). The strategy beats DCA on SHARPE on 4/5 assets (SP500, GOLD,
SILVER, BTC) -- consistent with the banking mechanic smoothing the weekly
return path, the same pattern family 018's Halloween strategy showed -- but
loses on WEALTH on every single asset, including OIL where it loses on
both metrics. Since sec 4.1 requires BOTH metrics simultaneously, the
Sharpe-only wins do not count.

### Grid diagnostic (sec 4.4)

**0 of 18 configurations (0.0%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fee -- need >=2/3 (12/18). Every
single config in the grid shows the identical pattern as the primary:
4/5 assets beat DCA on Sharpe alone, but 0/5 beat DCA on wealth, for every
combination of `tilt_strength in {0.3, 0.5, 0.7}`, `power in {1.0, 2.0}`
and `max_lump_multiple in {4, 8, 12}`. This is a strikingly uniform result
across the whole grid -- stronger tilts, sharper power shaping, and larger
burst caps all leave the wealth shortfall qualitatively unchanged, which
points to a structural mismatch between the signal and the wealth outcome
rather than a parameter-tuning problem within this design.

**Sec 4.4: FAIL** (need >=12/18; got 0/18 = 0.0%).

CSCV probability of backtest overfitting (18-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.0** -- the
grid's in-sample ranking of configs reliably predicts out-of-sample
ranking within the grid's own resamples, consistent with family 023's
reading: this is a consistently weak signal across the grid, not a
noisily-overfit one that got randomly lucky/unlucky by parameter choice.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  **-0.010749** (weekly, **-0.07751 annualized**) -- **negative**.
- `N` (raw trial count, whole-loop pool): **725** (196 seeded + 529 new,
  matching `state/trial_counter.json["new"]` = 529 after this family:
  196 + 529 = 725).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **70**
  clusters (unchanged from family 023's 70 -- this family's 18-config grid
  added 0 new distinct clusters at the rho>=0.5 threshold; its excess
  series correlate highly enough with existing seasonal-timing/banking
  clusters, e.g. family 018's, to be absorbed into them).
- **DSR (N_eff-based): ~3.73e-26** -- effectively zero (a negative raw
  Sharpe can never clear a positive `SR0` threshold at any `N`).
- DSR (raw-N, conservative reference): ~1.38e-28, also effectively zero.

**Sec 4.2: FAIL**, decisively.

## Verdict

**REJECTED.** Sec 4.1 fails decisively (0/5 core assets beat DCA on both
wealth and Sharpe; need >=3/5). Sec 4.4 fails decisively (0/18 grid configs
reach the majority bar; need >=12/18, and the failure pattern is uniform
across the entire grid, not a lucky/unlucky-corner issue). Sec 4.2 fails
decisively (DSR ~0, negative raw pooled excess Sharpe). Sec 4.3 was not
run (only run when sec 4.1 passes, per this loop's established
precedent). Holdout was **not** opened.

## Interpretation

The banking-and-burst mechanic (identical in spirit to family 018's) does
reliably smooth the weekly return path -- Sharpe improves on 4/5 assets,
every single grid config, regardless of tilt strength, shape or burst
cap -- but it does so at the cost of wealth on every asset tested,
including in cases (OIL) where even Sharpe does not improve. The
mechanism concentrates buying into the winter/spring half of the year
(when daylight is lengthening) and reduces buying in the summer/fall half
(when daylight is shortening), which is the opposite of a dip-buying
strategy: it buys MORE, not less, near the summer solstice (historically
often a period of elevated valuations after a spring rally) and buys LESS
near the point of maximal risk-aversion at the winter solstice, when -- if
KKL's own realized-return finding holds over this development sample --
prices should already be relatively depressed and a rebound imminent.
Unlike family 018 (which at least cleared 2/5 on sec 4.1), this family's
0/5 result suggests either that the daylight-length signal, tested as a
smooth continuous year-round function rather than KKL's original
fall-specific piecewise regressor, is too diffuse to capture a genuine
seasonal wealth effect on this development sample and these 5 broad
assets, or that any real SAD-related mispricing (if it exists at all in
recent decades) has been substantially arbitraged away or was never large
enough to survive transaction costs and a fixed-dollar-deposit framing
outside the tightly-defined equity-index panels KKL originally studied.
The uniformity of the 0/18 grid result and the low CSCV PBO both argue
against this being an unlucky primary-configuration draw -- the family as
designed does not produce a wealth edge anywhere in its parameter space.

## Files

- `src/backtest/v3/strategies/sad_daylight.py`
- `scripts/v3/run_024_sad_daylight.py`
- `families/024-sad-daylight/grid_results.csv`, `_primary_per_asset.csv`, `_run_output.json`
- `state/trials/new_024_*.csv` (18 files)
