# Family 040 results: Rolling Sortino-ratio sizing

**Verdict: NEAR-MISS.** The primary configuration passes sec 4.1 (beats
DCA on wealth AND Sharpe on **4 of 5** core assets at both fee levels) and
sec 4.4's grid diagnostic (83.3% of the 36-config grid clears the
combined majority bar, well above the 2/3 requirement), but **fails sec
4.2** (Deflated Sharpe Ratio is essentially zero, ~4.34e-18, against a
0.95 threshold) **and sec 4.3** (rolling windows land just under 60%,
block bootstrap fails on both raw and Sharpe-detrended checks, and the
placebo circular-shift result lands at the 33rd Sharpe percentile, far
short of the required 95th). Holdout was **not** opened (not a
finalist). This is the same overall verdict pattern -- and, strikingly,
nearly the same numeric fingerprint -- as family 031 (Kelly-Sharpe
sizing), discussed below.

## Category and required distinction from family 031 (Kelly-Sharpe sizing) -- primary burden

Filed as **Sizing / valuation** (mirroring family 031's own category
judgment call). The trailing-Sortino signal (`mean(trailing log return) /
downside_deviation(trailing log return)`) is a genuinely different
statistic from family 031's trailing-Sharpe signal (`mean(trailing log
return) / std(trailing log return)`): the denominator changes from the
ordinary, symmetric standard deviation (every day, up or down,
contributes) to the downside-only semi-deviation (only negative-return
days contribute; positive-return days contribute exactly zero,
regardless of magnitude, with the divisor remaining the full window
length `n`, the Sortino & Price 1994 convention).

**Concrete numeric divergence example, computed live by the module under
test** (`scripts/v3/run_040_sortino_sizing.py`'s `check_sortino_sharpe_
divergence`), real SP500 development data, 60-trading-day window
(1963-11-26..1964-02-20):

| Statistic | Value |
|---|---|
| Trailing mean daily log return | +0.18153% |
| Trailing std (symmetric) | 0.58438% |
| Trailing downside deviation | 0.14487% |
| Days positive / negative (of 60) | 38 / 22 |
| Largest up-day / down-day move | +3.902% / -0.635% |
| **Sharpe ratio** (family 031's statistic) | **0.3106** |
| **Sortino ratio** (this family's statistic) | **1.2531** |

The window's large up-day outlier (+3.90%, the crash-fear-free case of a
single big rally day) inflates the symmetric standard deviation
(0.584%/day) roughly 4x above the downside deviation (0.145%/day), which
reflects only the window's small, orderly down-days (largest -0.635%).
The identical numerator divided by these two very different denominators
produces a Sortino ratio **more than 4x** the Sharpe ratio for the exact
same window of the exact same asset (**ratio 4.034x**, confirmed live,
`divergence_confirmed: true` in `_run_output.json`) -- concrete proof the
two statistics are not rescaled versions of each other and would rank
this window very differently (family 031's signal would read this window
as "moderately favorable"; this family's signal would read it as
"strongly favorable"). A downside-deviation formula correctness
spot-check (task-required check (b)) on a toy 5-day window
`[0.02, 0.05, 0.10, -0.03, -0.01]` confirms the computed value
(0.014142) exactly matches the hand-derived expected value and is
provably invariant to the magnitude of the positive days (changing them
to `[0.99, 1.50, 2.00, -0.03, -0.01]` leaves the downside deviation
unchanged) -- the denominator genuinely ignores upside moves entirely,
as the mechanism requires.

## Primary-config-in-grid verification

Verified programmatically at module import time (`assert PRIMARY_CONFIG
in grid_configs()` inside `sortino_sizing.py` itself) and re-confirmed in
the run script before any grid backtest: `PRIMARY_CONFIG = {sortino_
window=60, pctile_lookback=504, k=1.0, min_mult=0.5}` (`max_mult=2.0` and
`max_lump_multiple=3.0` fixed) is a genuine member of the 36-config grid
(`cfg15_sw60_pl504_k1.0_mn0.5`). No mismatch found.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Downside-deviation formula correctness (only negative days contribute; invariant to positive-day magnitude) | PASS |
| Sortino/Sharpe divergence example confirmed (ratio 4.034x, std > 3x downside deviation) | PASS |
| Degenerate config (`enabled=False`) reproduces plain DCA exactly (bit-for-bit) | PASS |
| Second reference point: real `k=0.0` grid-shaped code path also reproduces plain DCA exactly | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (aggressive grid corner: `sortino_window=40, pctile_lookback=504, k=1.5, min_mult=0.25`) | PASS |
| Capital never exceeds cumulative deposits + interest (principled "never invest" ceiling bound, family 021's fix) -- primary config | PASS |
| Same capital-neutrality check -- aggressive grid corner | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (`t=6000`, `t=20000`) | PASS (both) |
| Point-in-time macro data | N/A -- price-only signal, no macro/ALFRED series |

## Pre-grid checks (per this iteration's task instruction)

- **(a)** `PRIMARY_CONFIG` membership in `grid_configs()`: verified via
  import-time assertion. PASS.
- **(b)** Downside-deviation negative-days-only spot-check: PASS (above).
- **(c)** Sortino-vs-Sharpe divergence example on real data: PASS (above,
  ratio 4.034x).
- **(d)** No dev-period sanity check ever touches 2020+ data or an
  unseen ticker: confirmed -- every check above uses only
  `src.backtest.v3.data.load_dev()` (SP500, strictly pre-2020) or a toy
  array with no calendar date at all.
- **(e)** Cash-reserve-dynamics check (continuous-multiplier design,
  family 039's pattern): the primary config's average cash balance
  (**$123.83**) meaningfully exceeds plain DCA's baseline average
  (**$103.88**); the reserve is drawn down further on elevated-multiplier
  (high-Sortino-percentile) weeks (**$105.93** average cash) than on
  depressed-multiplier (low-Sortino-percentile) weeks (**$140.87**
  average cash), confirming `min_mult=0.5<1.0` genuinely funds the boost
  arm rather than being nullified by the engine's no-leverage cash cap
  (the families 014/033/037/039 lesson).

## Pre-grid non-degeneracy sanity check

Confirmed on real development data for all 5 core assets before trusting
any grid result -- the multiplier shows real dispersion and is rarely
stuck at the neutral 1.0 value:

| Asset | Dev days | Frac. multiplier == 1.0 | Std(multiplier) | Non-degenerate? |
|---|---|---|---|---|
| SP500 | 23,109 | 2.63% | 0.509 | PASS |
| GOLD | 4,848 | 11.80% | 0.481 | PASS |
| SILVER | 4,850 | 11.77% | 0.484 | PASS |
| BTC | 1,932 | 29.24% | 0.449 | PASS |
| OIL | 4,857 | 11.76% | 0.470 | PASS |

BTC's shorter development window (per the plan's own flagged caveat, sec
12) still comfortably clears `pctile_lookback=504` days.

## Primary configuration: `sortino_window=60, pctile_lookback=504, k=1.0, min_mult=0.5` (`max_mult=2.0`, `max_lump_multiple=3.0` fixed)

### Sec 4.1 result (vs. plain per-asset DCA), development windows

| Asset | Strategy wealth/invested (0.1%) | DCA wealth/invested (0.1%) | Strategy Sharpe (0.1%) | DCA Sharpe (0.1%) | Beats DCA (both, 0.1%)? |
|---|---|---|---|---|---|
| SP500 | 85.28052 | 85.27722 | 0.153104 | 0.153097 | **YES** (razor-thin) |
| GOLD | 2.23138 | 2.23123 | 0.504964 | 0.504917 | **YES** (razor-thin) |
| SILVER | 1.68683 | 1.68666 | 0.319697 | 0.319677 | **YES** (razor-thin) |
| BTC | 9.85226 | 9.85568 | 1.067234 | 1.067309 | NO (loses both, razor-thin) |
| OIL | 1.18055 | 1.17986 | 0.227921 | 0.227824 | **YES** |

At 0.1% fees: **4/5** assets beat DCA on both wealth AND Sharpe (every
winning margin is small; BTC is the sole, narrow loser). At 0.25% fees:
also **4/5**, same pattern (SP500/GOLD/SILVER/OIL win, BTC loses).
**Sec 4.1: PASS** at both fee levels (need >=3/5). Every margin is very
thin -- consistent with this being a pure-timing, never-more-total-
capital reallocation of a fixed deposit stream, and with the mechanism's
economically modest expected effect size flagged honestly in prereg.md.
**These per-asset results are numerically almost identical to family
031's own sec 4.1 table** (same 4 winners, same single loser BTC, all
margins similarly razor-thin) -- discussed further below.

### Grid diagnostic (sec 4.4)

**30 of 36 configurations (83.3%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets, 0.1% fee) -- well above the 2/3 (24/36)
requirement. The strongest corners cluster at the longer
`sortino_window=90`/`pctile_lookback=756` combination (several reach
4/5 wealth and 5/5 Sharpe), while the weakest corners are `k=1.0`/`k=1.5`
with `min_mult=0.25` at the shorter `pctile_lookback=504` (e.g. `cfg02`,
`cfg14`, `cfg16` fall to 1-2/5) -- the same qualitative pattern family
031's own grid diagnostic showed (aggressive, low-`min_mult`/high-`k`
corners at the shorter lookback underperform). **Sec 4.4: PASS** (need
>=24/36; got 30/36).

CSCV probability of backtest overfitting (36-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.357** --
moderate, in the same range as family 031's own 0.271 and consistent
with the DSR and sec 4.3 results below.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series
  (equal-weight average of the 5 per-asset excess series): **0.003693/
  week** (annualized ~2.66%) -- small and positive, with extreme
  negative skew (-6.16) and kurtosis (299.6), the same "many small wins,
  rare large losses" signature family 031's own excess-return series
  showed.
- `N` (raw trial count, whole-loop pool): **1221** (196 seeded + 1025
  new = 1221, matching `state/trial_counter.json`'s updated `new: 1025` =
  989 through family 039 + 36 new from this family's grid).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **126**
  clusters (unchanged from family 039 -- this family's 36 grid configs
  did not open a new cluster distinct from the existing 126).
- **DSR (N_eff-based): 4.335e-18** -- essentially zero, against an SR0
  threshold this loop's N_eff=126 now demands.
- DSR (raw-N, conservative reference): 9.918e-20.

**Sec 4.2: FAIL**, decisively -- the raw pooled excess-return Sharpe
(0.00369/week) is far below the SR0 bar this loop's accumulated trial
count now demands, despite the positive sec 4.1 asset count.

### Robustness (sec 4.3, run in full since sec 4.1 passed, n_sims=60 time-budget)

- **Rolling windows** (3y/5y for SP500/GOLD/SILVER/OIL, 2y for BTC, 3,439
  total windows): pooled **56.3% wealth / 57.8% Sharpe** -- both
  **below** the required >60%. BTC's 2-year windows are again a striking
  0.00%/0.00% (never beats DCA in any of 72 two-year BTC windows in this
  development sample, identical to family 031's own BTC-window result),
  while OIL's 5-year windows are the strongest leg at 87.8%/86.1%.
  **FAIL**.
- **Block bootstrap** (500-run budget honored at the n_sims=60 time-
  boxed convention, SP500, 4-week blocks): raw-path **45.0%/43.3%**
  (below majority on both), detrended **76.7% wealth / 43.3% Sharpe**
  (wealth passes, Sharpe does not -- both required). **FAIL**.
- **Placebo** (circular-shift the primary config's own multiplier array
  `m_t`, SP500, 60 shifts): the real result lands at the **68.3rd
  percentile on wealth** and the **33.3rd percentile on Sharpe** -- far
  short of the required >=95th on either metric, and below the median
  placebo draw on Sharpe. **FAIL**.

**Sec 4.3: FAIL** on all three sub-checks.

## Assessment summary

| Check | Result | Pass? |
|---|---|---|
| Sec 4.1 (beats DCA >=3/5, both fees) | 4/5 at both fees | PASS |
| Sec 4.2 (DSR >= 0.95) | 4.34e-18 (N_eff), 9.92e-20 (raw N) | FAIL |
| Sec 4.3 (rolling/bootstrap/placebo) | rolling 56.3%/57.8% (need >60%); bootstrap raw+detrended-Sharpe FAIL; placebo 68.3rd/33.3rd pctile (need >=95th) | FAIL |
| Sec 4.4 (>=2/3 of grid beats DCA majority) | 30/36 (83.3%) | PASS |

**Verdict: NEAR-MISS.** Logged, not promoted to finalist. Holdout not
opened, per sec 5.4.

## Interpretation

**This family's numeric fingerprint is remarkably close to family 031's
own results across nearly every check**: the same 4/5 sec 4.1 winners
(SP500, GOLD, SILVER, OIL) with the same single loser (BTC) at similarly
razor-thin margins; a similarly strong sec 4.4 grid pass rate (83.3% vs.
family 031's 83.3%); a similarly near-zero DSR; a rolling-window pass
rate just under 60% with an identical BTC 2-year 0%/0% signature; a
block-bootstrap pattern where the detrended wealth leg passes but every
Sharpe leg fails; and a placebo circular-shift result landing at almost
the same percentiles (68.3rd/33.3rd here vs. 68.3rd/33.3rd for family
031, an exact match on wealth and Sharpe both). Despite the concrete,
verified divergence between the two underlying statistics on individual
windows (the Sortino ratio can run 4x the Sharpe ratio on a genuinely
asymmetric-volatility window), the resulting **percentile ranks** the
two signals assign to most days across a multi-decade development sample
turn out to be highly similar in practice -- a real and informative
finding in its own right: single-window divergence in the raw statistic
does not guarantee divergence in the derived percentile-rank sizing
signal once that signal is aggregated over a multi-year rolling
reference window, because the Sortino and Sharpe percentile ranks
co-move closely whenever an asset's downside and upside volatility drift
together over time (as they often do, even when they differ
substantially in any single 60-day snapshot). This is a genuine,
non-parameter-tunable negative result for the downside-risk-adjusted-
momentum-ratio construction of the Sortino-sizing hypothesis on this
development data, distinct from (and a rigorous, literature-motivated
complement to) family 031's own separately-tested Sharpe-ratio version --
as prereg.md's own honest expected-sign caveat anticipated was a real
possibility given family 031's own weak sec 4.2/4.3 result.

## Judgment calls

1. **Design choice: continuous percentile-multiplier (family 031's own
   functional form, matching sign since elevated Sortino should size UP)**,
   rather than a discrete tier ladder, to keep the reserve-banking
   mechanism automatically safe from the 014/033/037/039
   cash-cap-nullification failure mode -- verified directly via the
   cash-reserve-dynamics check rather than merely asserted. Every grid
   cell's `min_mult` is also asserted < 1.0 at import time as an explicit
   belt-and-suspenders check.
2. **Parameter values chosen to exactly mirror family 031's own primary
   configuration values** (`sortino_window=60` matching `sharpe_window=
   60`, same `pctile_lookback=504`, `k=1.0`, `min_mult=0.5`), a deliberate
   design decision (stated in prereg.md before any backtest) so that any
   difference in sec 4 outcomes would be attributable to the Sharpe-vs-
   Sortino statistic itself rather than to a different choice of window
   or sensitivity -- this makes the strong numeric similarity of the two
   families' final results a more meaningful (not merely coincidental)
   comparison.
3. This result adds a further data point (after families 003/030/031/
   034/035/036/037/039) to this loop's now-consistent finding that a
   continuous, price-only, single-asset trailing-statistic sizing signal
   applied identically across all 5 core assets tends to clear sec 4.1
   and sec 4.4 on development data but fail sec 4.2/4.3's trial-count-
   adjusted and resampling-based checks -- and additionally shows that
   two economically distinct risk-adjusted-return ratios (Sharpe vs.
   Sortino) can produce almost indistinguishable final verdicts once
   converted to a rolling percentile-rank sizing signal, a useful
   negative-result nuance for any future family considering yet another
   mean-to-risk-ratio variant (e.g. a Calmar-ratio or Omega-ratio
   sizing signal) as a plausible source of a materially different
   result from this loop's existing 003/031/040 cluster.
