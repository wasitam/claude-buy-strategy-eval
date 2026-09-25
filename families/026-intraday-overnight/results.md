# Family 026 results: Intraday/overnight return decomposition sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively:
it beats plain DCA on **0 of 5** core assets, on wealth AND Sharpe, at
either fee level (need >=3). Sec 4.4's grid diagnostic fails completely:
**0 of 36** configurations (0.0%) reach the combined wealth-AND-Sharpe
majority bar (need >=2/3 = 24/36) -- not one config in the 36-config grid
beats DCA on wealth AND Sharpe together on a majority (>=3/5) of assets.
Sec 4.2's Deflated Sharpe is effectively zero (negative raw pooled excess
Sharpe). Sec 4.3 was **not** run, per this loop's established precedent of
running it only when sec 4.1 passes. Holdout was **not** opened.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (aggressive corner: `lookback_days=10, elevated_pct=80, compressed_pct=20, buy_multiplier=3.0`) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (primary config and aggressive corner, family 021's principled "never invest" ceiling-bound method) | PASS |
| **No-lookahead**, spot-checked at `t=6000` and `t=20000`, perturbing all OHLC strictly after the check point (including `Open_{t+1}`, which enters `overnight_{t+1}`) -- every order on/before `t` unchanged | PASS |
| Point-in-time macro data | N/A -- no macro/external series used at all (not even a VIX proxy) |

## Hand-checked O/C decomposition arithmetic (required before the grid ran)

Spot-checked on 5 real SP500 development days spanning 1928-2007. The
exact multiplicative identity `(1+overnight_t)*(1+intraday_t) - 1`
reproduces the actual `Close_t/Close_{t-1} - 1` return to floating-point
precision on all 5 checked days; the simple additive sum
`intraday_t + overnight_t` matches it exactly on 4/5 days (one leg was
identically 0.0 that day) and is off by only `5.7e-8` on the fifth
(2007-08-27, a day with both legs nonzero) -- the expected second-order
compounding cross-term, negligible at these return magnitudes. Confirms
the decomposition arithmetic itself, not just the code, is correct.

## Pre-grid non-degeneracy check (before the grid ran)

Primary config's `elevated_t`/`compressed_t` regime frequencies, all 5
core assets:

| Asset | Elevated frac | Compressed frac |
|---|---|---|
| SP500 | 11.50% | 10.27% |
| GOLD | 11.22% | 11.04% |
| SILVER | 12.29% | 10.70% |
| BTC | 10.09% | 11.18% |
| OIL | 11.32% | 10.17% |

All non-trivial (comfortably inside the required (2%, 60%) band, and
notably close to a clean ~10%/10% split -- consistent with the
`elevated_pct=90`/`compressed_pct=10` primary thresholds firing close to
their nominal decile rate on every asset), confirming the trigger fires
genuinely and non-degenerately on all 5 assets before any backtest result
was trusted.

## Primary-config-in-grid verification

Verified programmatically at module import time
(`src/backtest/v3/strategies/intraday_overnight.py` asserts
`PRIMARY_CONFIG in grid_configs()` on import, per family 021's lesson) --
primary config `lookback_days=20, elevated_pct=90, compressed_pct=10,
buy_multiplier=2.0` is confirmed a genuine member of the 36-config grid.

## Primary configuration: `lookback_days=20, elevated_pct=90, compressed_pct=10, buy_multiplier=2.0`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 83.308 | 85.277 | 0.15380 | 0.15310 | NO (wealth fails) |
| GOLD | 2.195 | 2.231 | 0.50134 | 0.50492 | NO |
| SILVER | 1.664 | 1.687 | 0.31816 | 0.31968 | NO |
| BTC | 9.183 | 9.856 | 1.06575 | 1.06731 | NO |
| OIL | 1.178 | 1.180 | 0.22379 | 0.22782 | NO |

**Sec 4.1: FAIL** -- 0/5 core assets beat DCA on wealth AND Sharpe (need
>=3), at both 0.1% and 0.25% fees (0.25% results qualitatively identical,
see `_primary_per_asset.csv`). SP500 beats DCA on Sharpe alone by a hair
(consistent with the banking mechanic smoothing weekly returns, the same
pattern seen in every prior timing/banking family in this loop) but loses
on wealth; GOLD, SILVER, BTC and OIL lose on BOTH metrics outright -- a
weaker result even than most prior REJECTED sizing families, which
typically manage at least a Sharpe-only win on 2-4/5 assets via the
banking mechanic alone.

### Grid diagnostic (sec 4.4)

**0 of 36 configurations (0.0%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fee -- need >=2/3 (24/36). The best
any single config manages is 2/5 assets beating on BOTH wealth and Sharpe
together (several configs, e.g. `cfg08`, `cfg11`, `cfg25`, at 0.25% fee --
oddly slightly BETTER at the higher fee for a couple of configs, a
noise artifact of which asset's win/loss flips right at the margin, not a
real fee-robustness signal given the underlying wealth gaps are already
this format's decisive failure). No config anywhere in the 36-point grid
reaches the 3/5 majority sec 4.1 itself requires. This is a uniform
failure across the entire parameter space.

**Sec 4.4: FAIL** (need >=24/36; got 0/36 = 0.0%).

CSCV probability of backtest overfitting (36-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.0** -- the
lowest possible reading, meaning the grid's in-sample config ranking is
consistently reproduced out-of-sample rather than flipping by chance.
Read together with the uniform 0/36 majority failure, this indicates a
**reliably weak** signal (the grid isn't randomly lucky/unlucky at any
point; the whole parameter space is consistently mediocre-to-bad), not a
noise-dominated one.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  **-0.047849** (weekly, **-0.34504 annualized**) -- negative.
- `N` (raw trial count, whole-loop pool): **797** (196 seeded + 601 new,
  matching `state/trial_counter.json["new"]` = 601 after this family:
  196 + 601 = 797, consistent with family 025's 761-trial mark plus this
  family's 36-config grid).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **70**
  clusters (unchanged from families 023/024/025 -- this family's 36-config
  grid added 0 new distinct clusters at the rho>=0.5 threshold; its
  excess series correlate highly enough with existing timing/sizing
  clusters, unsurprising given the same weekly banking-and-burst mechanic
  every prior timing family in this loop shares, to be absorbed into
  them).
- **DSR (N_eff-based): ~1.71e-41** -- effectively zero (a negative raw
  Sharpe can never clear a positive `SR0` threshold at any `N`).
- DSR (raw-N, conservative reference): ~3.68e-44, also effectively zero.

**Sec 4.2: FAIL**, decisively.

## Verdict

**REJECTED.** Sec 4.1 fails decisively (0/5 core assets beat DCA on both
wealth and Sharpe; need >=3/5). Sec 4.4 fails decisively (0/36 grid
configs reach the majority bar; need >=24/36, uniform failure across the
entire grid). Sec 4.2 fails decisively (DSR ~0, negative raw pooled excess
Sharpe). Sec 4.3 was not run (only run when sec 4.1 passes, per this
loop's established precedent). Holdout was **not** opened.

## Interpretation

The overnight-vs-intraday spread, adapted from Lou, Polk & Skouras (2019)
to a single-asset time series, produces no wealth or Sharpe edge on any of
the 5 core assets across its entire 36-point parameter space -- a decisive,
uniform, and (per the CSCV PBO=0.0 reading) *reliably* weak result rather
than a noisy one. Two candidate readings, consistent with each other and
with the prereg.md's own flagged caveats: (1) LPS's continuation finding
is fundamentally a **cross-sectional** result (sorting many individual
stocks on their own overnight-minus-intraday characteristic and looking at
the spread PORTFOLIO's return); this family's necessary adaptation to a
single whole-asset time series -- betting that one asset's OWN trailing
overnight dominance predicts its OWN forward return -- may simply not
carry the same signal the cross-sectional sort captures, since the
cross-sectional effect could be substantially about which stocks get
sorted into which bucket at a point in time (a relative-ranking
phenomenon) rather than about any one asset's own absolute time-series
level persisting; and (2) as flagged explicitly in prereg.md before any
backtest ran, LPS's mechanism (overnight information accumulation while
markets are closed, exchange-open/close order-flow clienteles) is built on
equity-market trading-hours structure that has no clean analogue for BTC
(which trades 24/7 and has no true "market closed" overnight window in the
same sense) and only a partial one for the commodity futures (GOLD/
SILVER/OIL, which trade nearly around the clock on globex outside the
primary pit hours this loop's OHLC bars are built from) -- weakening the
economic story for 4 of the 5 core assets even before any numeric result
came in. SP500, the one asset where LPS's original equity-market
mechanism most directly applies, came closest to a mixed result (a
Sharpe-only win) but still lost decisively on wealth, arguing the
mechanism's practical edge, if any exists even for equities, was consumed
by (or never exceeded) the weekly banking-and-burst reallocation's own
costs and cash drag on this development sample.

## Files

- `src/backtest/v3/strategies/intraday_overnight.py`
- `scripts/v3/run_026_intraday_overnight.py`
- `families/026-intraday-overnight/grid_results.csv`, `_primary_per_asset.csv`, `_run_output.json`
- `state/trials/new_026_*.csv` (36 files)
