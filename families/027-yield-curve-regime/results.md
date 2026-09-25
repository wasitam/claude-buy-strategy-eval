# Family 027 results: Yield-curve slope (2s10s) inversion regime filter

**Verdict: REJECTED.** The primary configuration fails sec 4.1: it beats
plain DCA on wealth AND Sharpe together on only **2 of 5** core assets at
either fee level (need >=3). Sec 4.4's grid diagnostic also fails: only
**11/24 (45.8%)** configurations reach the combined wealth-AND-Sharpe
majority bar (need >=2/3 = 16/24). Sec 4.2's Deflated Sharpe is
effectively zero. Sec 4.3 was **not** run, per this loop's established
precedent of running it only when sec 4.1 passes. Holdout was **not**
opened.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (aggressive corner: `invert_threshold=-0.10, persistence_days=5, banking_window_days=504`) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (primary and aggressive corner, family 021's principled "never invest" ceiling-bound method) | PASS |
| **No-lookahead**, spot-checked at `t=6000` and `t=20000`, perturbing all OHLC strictly after the check point | PASS |
| Point-in-time macro (T10Y2Y, 2-calendar-day publication lag) -- lag-sensitivity check: shortening the lag to 0 days changes 0.074% of historical banking-regime readings vs. the documented lag, confirming the lag has a real, nonzero effect (not a no-op) | PASS |

## Pre-grid known-episode sanity check (data reachability + signal correctness, before any backtest)

`T10Y2Y` fetched via `fetch_fred_macro("T10Y2Y")` -- already cached from
v2.1's Strategy D usage, confirming reachability through v3's `data.py`
gate too: 1976-06-01 through the present, 12,577 daily observations.
Confirmed the raw signal correctly registers all three known
development-period inversion episodes named in the task before trusting
the backtest:

| Year | Min spread | Fraction of days negative |
|---|---|---|
| 1989 | -0.45 | 66.0% |
| 2000 | -0.52 | 90.4% |
| 2006 | -0.19 | 65.2% |
| 2007 | -0.15 | 28.7% (curve re-steepening mid-year, consistent with the documented history of that episode) |

All above the 20% sanity threshold, confirming the signal fires
non-trivially and matches known history before any backtest result was
trusted.

## Pre-grid non-degeneracy check (primary config, before the grid ran)

| Asset | Banking frac | Confirmed-inverted frac | Non-degenerate? |
|---|---|---|---|
| SP500 | 12.83% | 6.28% | YES |
| GOLD | 16.21% | 6.23% | YES |
| SILVER | 16.23% | 6.23% | YES |
| BTC | 0.00% | 0.00% | **NO -- flagged, not a bug (see below)** |
| OIL | 16.29% | 6.32% | YES |

**BTC exemption, judgment call (stated explicitly per the task's
instructions):** BTC's development window (2014-09 to 2019-12, the plan's
own already-flagged short-history weakness, sec 12) contains only a
single brief, 3-day near-inversion (2019-08-27 to 08-29, minimum spread
-0.04), which never reaches the primary config's `persistence_days=5`
consecutive-day confirmation threshold. This is a genuine feature of a
rare, clustered macro event (the full available Treasury history has only
~4 distinct inversion episodes) landing outside BTC's short window -- not
an implementation bug. The signal registers correctly on the other 4
assets' full histories and against all 4 known historical episodes above.
BTC's primary-config run is therefore observationally identical to plain
DCA in development data. The grid run proceeded rather than hard-failing
on this single, well-understood, pre-flagged exception (prereg.md's
"Expected sign" section already named exactly this risk before any
backtest was run).

## Primary-config-in-grid verification

Verified programmatically at **module import time**
(`src/backtest/v3/strategies/yield_curve_regime.py` asserts
`PRIMARY_CONFIG in grid_configs()` on import, per family 021's lesson) --
primary config `invert_threshold=0.0, persistence_days=5,
banking_window_days=252, stress_tilt_fraction=0.0` is confirmed a genuine
member of the 24-config grid.

## Primary configuration: `invert_threshold=0.0, persistence_days=5, banking_window_days=252, stress_tilt_fraction=0.0` (`max_lump_multiple=6` fixed)

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.298 | 85.277 | 0.153100 | 0.153097 | YES (razor-thin on both) |
| GOLD | 2.159 | 2.231 | 0.51200 | 0.50492 | NO (wealth fails) |
| SILVER | 1.660 | 1.687 | 0.34839 | 0.31968 | NO (wealth fails) |
| BTC | 9.856 | 9.856 | 1.06731 | 1.06731 | NO (identical -- regime never triggers in dev window) |
| OIL | 1.181 | 1.180 | 0.27541 | 0.22782 | YES |

**Sec 4.1: FAIL** -- 2/5 core assets beat DCA on wealth AND Sharpe (need
>=3/5), at both 0.1% and 0.25% fees (results qualitatively identical at
0.25%, see `_primary_per_asset.csv`). SP500's win is a razor-thin margin
on both metrics (the banking mechanic barely alters SP500's dev-period
path, since 2/5 core assets have most of the primary config's inversions
concentrated pre-BTC-era anyway); OIL wins genuinely on both; SILVER and
OIL both show a large Sharpe improvement but SILVER fails on wealth,
GOLD loses on both.

### Grid diagnostic (sec 4.4)

**11 of 24 configurations (45.8%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fee -- below the required >=2/3
(16/24). The strongest single configs are the two `invert_threshold=-0.10,
persistence_days=5, banking_window_days=0` configs (`cfg12`/`cfg13`),
reaching 4/5 assets on both metrics -- notably a *tighter* threshold
(-0.10 rather than 0.0) with **no** banking-window extension, the
opposite parameter direction from the primary config's more literature-
faithful choices (0.0 threshold, 252-day extension). This is exactly the
"grid diagnostic is diagnostic only, never switch to a better-looking
config" discipline sec 4.4 exists to enforce -- `cfg12`/`cfg13` cannot
become the finalist even though they outperform the primary config in
this diagnostic.

**Sec 4.4: FAIL** (need >=16/24; got 11/24 = 45.8%).

CSCV probability of backtest overfitting (24-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.057** -- low,
meaning the grid's in-sample config ranking is largely reproduced
out-of-sample. Read together with the roughly coin-flip 45.8% majority
rate (well short of the 2/3 bar but far from a uniform 0% failure like
family 026's), this indicates a **genuinely mixed, moderately
inconsistent** signal across the parameter space -- some corners of the
grid (tighter threshold, no lag extension) do meaningfully better than
others, but the loop's literature-faithful primary configuration choice
does not land in that stronger region, and no config in the grid is
promotable regardless.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  **0.008216** (weekly, **0.05924 annualized**) -- small and positive,
  unlike family 026's negative result, but far too small relative to the
  trial count to be distinguishable from noise.
- `N` (raw trial count, whole-loop pool): **821** (196 seeded + 625 new,
  matching `state/trial_counter.json["new"]` = 625 after this family:
  196 + 625 = 821, consistent with family 026's 797-trial mark plus this
  family's 24-config grid).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **71**
  clusters (up from 70 after family 026 -- this family's grid added
  exactly 1 new distinct cluster, meaning most of its 24 configs'
  excess-return series correlate highly enough with existing timing/
  banking-mechanic clusters to be absorbed, but at least one configuration
  is distinct enough to form its own cluster).
- **DSR (N_eff-based): ~2.69e-22** -- effectively zero. `SR0` (the
  expected-max-Sharpe-under-the-null threshold at this N_eff) is
  **0.1466**, far above the primary config's raw annualized Sharpe of
  0.0592.
- DSR (raw-N, conservative reference): ~8.52e-24, also effectively zero.

**Sec 4.2: FAIL**, decisively -- the small positive raw Sharpe is
completely swamped by the number of configurations this loop has now
tried.

## Verdict

**REJECTED.** Sec 4.1 fails (2/5 core assets beat DCA on both wealth and
Sharpe; need >=3/5 -- GOLD loses on both metrics, SILVER and BTC fail on
wealth, only SP500 by a razor-thin margin and OIL genuinely pass). Sec 4.4
fails (11/24 = 45.8% of the grid reaches the majority bar; need >=2/3 =
16/24 -- a moderately mixed rather than uniformly weak result, but still
short of the bar, and the primary config's literature-faithful parameter
choices do not fall in the grid's stronger region). Sec 4.2 fails
decisively (DSR ~2.7e-22; the small positive raw pooled Sharpe, 0.0592
annualized, is far below the ~0.147 threshold this loop's trial count now
demands). Sec 4.3 was not run (only run when sec 4.1 passes, per this
loop's established precedent). Holdout was **not** opened.

## Interpretation

The 2s10s Treasury yield-curve-inversion regime filter, adapted from
Estrella & Mishkin (1998) to a deposit-banking/timing mechanic, shows a
genuinely mixed (not uniformly weak, unlike family 026) result across its
24-point parameter space: nearly half the grid clears the sec 4.1-style
majority bar in isolation, and the strongest corners of the grid (a
tighter -0.10 threshold with no lag extension) come close to a real edge
on 4/5 assets. But (1) the primary configuration -- chosen honestly from
the cited literature's own textbook threshold and a conservative
mid-range lag estimate, before any result was seen -- lands in a weaker
region of the grid than several other configs, which sec 4.4 exists
precisely to prevent the loop from chasing after the fact; (2) the
absolute effect size is small even where it exists (consistent with every
other banking-mechanic family in this loop -- the mechanism only
reallocates timing of a fixed deposit stream, never total capital
deployed); and (3) with 821 raw trials / 71 effective clusters now
accumulated across this loop, the DSR bar has risen high enough that even
this family's small positive raw Sharpe cannot clear it. This is broadly
consistent with the risk flagged in prereg.md's own "Expected sign"
section before any backtest ran: yield-curve inversions are rare,
clustered events, and this family's own honest primary-config choice
happened not to land on the specific narrow parameter corner that shows
the strongest (still non-promotable) grid result.

## Distinction from family 011 and v2.1 Strategy D (summary; full argument in prereg.md)

- **Family 011** (BAA-AAA credit spread / NFCI): a market-priced
  credit-stress / financial-conditions signal, built from corporate bond
  markets, answering "how much default/liquidity risk compensation do
  bond investors demand right now." This family's `T10Y2Y` signal is
  built entirely from risk-free Treasury yields and answers a different
  question ("what does the market expect the future path of short rates,
  relative to long rates, to be"). The two series have historically
  diverged sharply (2005-06's curve inversion preceded 2007-08's
  credit-spread blowout by well over a year, with BAA-AAA *tight*, not
  stressed, during the inversion itself) -- direct evidence they are not
  proxies for one another.
- **v2.1 Strategy D** (the closest prior family, since `T10Y2Y` is
  literally one of Strategy D's 8 ensemble-vote signals, `R2b-inv`):
  distinguished on **both** of sec 7.2's disjunctive grounds. Mechanism:
  Strategy D uses the yield-curve signal as one of 8 votes in an ensemble
  that selects **which of two other pre-existing strategies (SmartDCA or
  plain DCA) to run** -- a meta-strategy-selection mechanism -- whereas
  this family uses the signal alone as a **direct banking/timing decision**
  (bank vs. deploy), the same primitive families 004/006/007/010/011
  already use, with no dependency on or reference to any other strategy.
  Signal definition: `R2b-inv` is a simple `slope<0` snapshot with a
  shared 2-week whipsaw filter applied uniformly across Strategy D's 8
  unrelated signals; this family adds an explicit persistence-confirmation
  requirement and, more materially, a lag-motivated post-inversion
  banking-window extension (up to 2 years) that has no analogue anywhere
  in `regimes.py`. Honestly flagged: the data series is the same, and
  `R2b-inv`'s standalone (non-ensemble) explanatory power was never itself
  isolated or reported in v2.1, so this family's isolated test answers a
  question Strategy D's ensemble-level result cannot answer either way --
  judged a materially different family under sec 7.2's own disjunctive
  rule, but flagged as this loop's closest proximity yet to a closed prior
  result.
