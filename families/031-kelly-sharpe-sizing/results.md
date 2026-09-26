# Family 031 results: Kelly-fraction-style trailing-Sharpe sizing

**Verdict: NEAR-MISS.** The primary configuration passes sec 4.1 (beats
DCA on wealth AND Sharpe on **4 of 5** core assets at both fee levels) and
sec 4.4's grid diagnostic (83.3% of the 36-config grid clears the
combined majority bar, well above the 2/3 requirement), but **fails sec
4.2** (Deflated Sharpe Ratio is essentially zero, ~2.1e-22, against a
0.95 threshold) **and sec 4.3** (rolling windows land just under 60%,
block bootstrap fails on both raw and Sharpe-detrended checks, and the
placebo circular-shift result lands at the 33rd Sharpe percentile, far
short of the required 95th). Holdout was **not** opened (not a
finalist).

## Category and synthesis distinction (from families 003, 005, 025, 020)

Filed as **Sizing / valuation** (justified explicitly in prereg.md over
"Volatility targeting": the signal's numerator, not just its denominator,
drives the reading, so it is not a pure risk-targeting rule). The
trailing-Sharpe signal (`mean(trailing log return) / std(trailing log
return)`, both annualized) is a genuine **ratio of return to risk**, not
a re-combination of any single prior family's ingredient in isolation:

- **Family 003** (vol-managed sizing) uses realized volatility ALONE
  (`sigma_ref / sigma_recent`) -- no return/momentum term at all.
- **Family 005** (tsmom sizing) uses the SIGN of trailing return ALONE --
  no volatility normalization at all.
- **Family 025** (VRP sizing) uses a spread between two DIFFERENT
  volatility measures (implied vs. realized) -- no return term at all.
- **Family 020** (52-week-high tilt) uses price-LEVEL proximity to a
  reference high -- neither a return-rate nor a volatility term.

**Concrete numeric contrast, computed on real development data** (60-day
trailing window, annualized, primary config's `sharpe_window`):

| Asset & date | Trailing mean return | Trailing vol | Trailing Sharpe |
|---|---|---|---|
| BTC, 2018-01-22 | **+129.1%** | **120.9%** | **1.0677** |
| SP500, 1993-12-20 | **+7.48%** | **7.00%** | **1.0678** |

BTC's return and vol on that date are each **~17x** SP500's on its date,
yet the trailing Sharpe is essentially identical (1.0677 vs. 1.0678).
Family 031 would size both days' buys the same way (same reading of
"comparable risk-adjusted edge"). Family 003 (vol alone) would size BTC
far more conservatively, reading its 17x-higher vol as "dangerous" with
no way to know the return was proportionally as large. Family 005 (sign
alone) would size both identically as "positive," collapsing a 17x
difference in the magnitude of the underlying edge into the same bucket
-- unable to distinguish BTC's outsized move from SP500's modest one. A
second real-data pair on the negative side (BTC 2018-02-03: mean -109.8%,
vol 123.2%, Sharpe -0.8911; GOLD 2017-11-28: mean -9.56%, vol 10.72%,
Sharpe -0.8912) makes the same point in reverse. Neither prior family's
signal, nor a naive average of what each would independently output,
reconstructs this ratio-based reading -- confirmed with real numbers, not
hypothetical ones, per this iteration's task instruction.

## Primary-config-in-grid verification

Verified programmatically at module import time (`assert PRIMARY_CONFIG
in grid_configs()` inside `kelly_sharpe_sizing.py` itself, executed
automatically on import) and re-confirmed in the run script before any
grid backtest: `PRIMARY_CONFIG = {sharpe_window=60, pctile_lookback=504,
k=1.0, min_mult=0.5}` (`max_mult=2.0` and `max_lump_multiple=3.0` fixed)
is a genuine member of the 36-config grid (`cfg15_sw60_pl504_k1.0_mm0.5`).
No mismatch found.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`, bypasses the Sharpe/percentile computation entirely, buys 100% of cash every week-end day) reproduces plain DCA exactly (bit-for-bit on units and cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (aggressive grid corner: `sharpe_window=40, pctile_lookback=504, k=1.5, min_mult=0.25`) | PASS |
| Capital never exceeds cumulative deposits + interest, verified via the principled "never invest" ceiling-bound method (family 021's fix) -- primary config | PASS |
| Same capital-neutrality check -- aggressive grid corner | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged, checked at two spot-check points (`t=6000`, `t=20000`, both deep in the pre-2020 dev sample) | PASS (both) |
| Point-in-time macro data | N/A -- price-only signal (the asset's own daily log returns), no macro/ALFRED series |

## Pre-grid non-degeneracy sanity check (per prereg.md, run before the grid)

Confirmed on real development data, using the primary configuration's own
trailing-Sharpe/percentile-rank computation, **before** trusting any grid
result. By construction (a percentile rank over a full rolling window is
close to uniformly distributed on `[0, 1]`), the elevated (`m_t > 1`) and
depressed (`m_t < 1`) fractions are expected near 50% once
`pctile_lookback` (504 trading days, ~2 years) of Sharpe history exists,
required to fall in a broad `(20%, 80%)` band on every asset:

| Asset | Dev days | Days w/ Sharpe history | Elevated frac. | Depressed frac. | Non-degenerate? |
|---|---|---|---|---|---|
| SP500 | 23,109 | 23,050 | 46.25% | 51.13% | PASS |
| GOLD | 4,848 | 4,789 | 45.01% | 43.25% | PASS |
| SILVER | 4,850 | 4,791 | 44.25% | 44.04% | PASS |
| BTC | 1,932 | 1,873 | 32.19% | 38.51% | PASS |
| OIL | 4,857 | 4,798 | 44.97% | 43.40% | PASS |

BTC's development window is short (per the plan's own flagged caveat,
sec 12) but still comfortably clears `pctile_lookback=504` days, and both
fractions land inside the sanity band on every asset -- the percentile-
rank multiplier fires close to its expected ~50/50 split everywhere,
confirming the signal is not degenerate before any grid result is
trusted.

## Primary configuration: `sharpe_window=60, pctile_lookback=504, k=1.0, min_mult=0.5` (`max_mult=2.0`, `max_lump_multiple=3.0` fixed)

### Sec 4.1 result (vs. plain per-asset DCA), development windows (BTC-gated)

| Asset | Strategy wealth/invested (0.1%) | DCA wealth/invested (0.1%) | Strategy Sharpe (0.1%) | DCA Sharpe (0.1%) | Beats DCA (both, 0.1%)? |
|---|---|---|---|---|---|
| SP500 | 85.2806x | 85.2772x | 0.15311 | 0.15310 | **YES** (razor-thin) |
| GOLD | 2.2314x | 2.2312x | 0.50496 | 0.50492 | **YES** (razor-thin) |
| SILVER | 1.6868x | 1.6867x | 0.31970 | 0.31968 | **YES** (razor-thin) |
| BTC | 9.8522x | 9.8557x | 1.06723 | 1.06731 | NO |
| OIL | 1.1806x | 1.1799x | 0.22792 | 0.22782 | **YES** |

At 0.1% fees: **4/5** assets beat DCA on both wealth AND Sharpe (every
margin is small; BTC is the sole, narrow loser). At 0.25% fees: also
**4/5**, same pattern. **Sec 4.1: PASS** at both fee levels (need >=3/5).
Every margin is very thin -- consistent with this being a pure-timing,
never-more-total-capital reallocation of a fixed deposit stream (flagged
in prereg.md's own expected-sign caveat).

### Grid diagnostic (sec 4.4)

**30 of 36 configurations (83.3%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets, 0.1% fee) -- well above the 2/3 (24/36)
requirement, the best sec 4.4 result of any family in this loop so far.
The strongest corners cluster at the longer `sharpe_window=90` and
`pctile_lookback=756` (3-year) settings (several reach 4/5 wealth and 5/5
Sharpe), while the weakest corners are `k=1.0`/`k=1.5` with
`min_mult=0.25` at the shorter `pctile_lookback=504` (e.g. `cfg02`,
`cfg14`, `cfg16` fall to 1-2/5) -- a sensible pattern: a low `min_mult`
combined with high sensitivity `k` produces the most aggressive cash-
banking-and-lump-buying behavior, which appears to hurt more often than
it helps at the shorter, noisier 2-year percentile-reference window.
**Sec 4.4: PASS** (need >=24/36; got 30/36).

CSCV probability of backtest overfitting (36-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.271** --
moderate, meaning the grid's in-sample ranking of configurations is only
partially reproduced out-of-sample, a caution flag consistent with the
DSR and sec 4.3 results below.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series
  (equal-weight average of the 5 per-asset excess series, strategy weekly
  NAV return minus DCA weekly NAV return): **0.003878/week** (annualized
  ~2.80%) -- small and positive, but the excess-return series has extreme
  negative skew (-6.27) and kurtosis (307.2), a classic "many small wins,
  rare large losses" signature for a lump-buy-after-elevated-signal
  mechanism.
- `N` (raw trial count, whole-loop pool): **941** (196 seeded + 709 from
  families 001-030 + 36 new from this family's grid) -- matches the
  task's sanity check (196+745=941, where 745=709+36).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **74**
  clusters (unchanged from family 030 -- this family's 36 grid configs
  did not open a new cluster distinct from the existing 74).
- **DSR (N_eff-based): 2.07e-22** -- essentially zero, against an
  SR0 threshold of 0.1452/week at this loop's N_eff=74.
- DSR (raw-N, conservative reference): 2.69e-23.

**Sec 4.2: FAIL**, decisively -- the raw pooled excess-return Sharpe
(0.00388/week) is far below the SR0 bar this loop's accumulated trial
count now demands, despite the positive sec 4.1 asset count.

### Robustness (sec 4.3, run in full since sec 4.1 passed, n_sims=60 time-budget)

- **Rolling windows** (3y/5y for SP500/GOLD/SILVER/OIL, 2y for BTC,
  3,439 total windows): pooled **56.4% wealth / 57.9% Sharpe** -- both
  **below** the required >60%. BTC's 2-year windows are a striking
  0.00%/0.00% (the strategy never beats DCA in any 2-year BTC window in
  this development sample), while OIL's 5-year windows are a strong
  88.9%/86.1% -- a highly asset-dependent, not uniformly robust, pattern.
  **FAIL**.
- **Block bootstrap** (500-run budget honored at the n_sims=60
  time-boxed convention, SP500, 4-week blocks): raw-path
  **43.3%/43.3%** (below majority on both), detrended **76.7%
  wealth / 43.3% Sharpe** (wealth passes, Sharpe does not -- both
  required). **FAIL**.
- **Placebo** (circular-shift the primary config's own multiplier array
  `m_t`, SP500, 60 shifts): the real result lands at the **68.3rd
  percentile on wealth** and the **33.3rd percentile on Sharpe** -- far
  short of the required >=95th on either metric, and actually *below*
  the median placebo draw on Sharpe. **FAIL** -- the specific temporal
  alignment of the trailing-Sharpe-percentile signal is not doing
  identifiable work beyond what a randomly-shifted version of the same
  signal's overall multiplier distribution would produce.

**Sec 4.3: FAIL** on all three sub-checks.

## Verdict

**NEAR-MISS.** Sec 4.1 passes decisively (4/5 assets, both fee levels)
and sec 4.4's grid diagnostic passes strongly (83.3%, the loop's best
result so far on this check) -- but sec 4.2 (DSR effectively zero) and
sec 4.3 (rolling windows below 60%, bootstrap fails on both legs, placebo
lands at only the 33rd Sharpe percentile) both fail. Logged, not
promoted. Holdout was **not** opened.

## Interpretation

This family's central hypothesis -- that a ratio-based, risk-adjusted
momentum signal would improve on families 003's (vol-only) and 005's
(return-sign-only) own underwhelming individual results by combining
their ingredients -- produces the strongest sec 4.1/4.4 combination of
any family in this loop, but the improvement does not survive contact
with sec 4.2's trial-count-adjusted bar or sec 4.3's resampling and
placebo battery. The extreme negative skew and kurtosis of the pooled
excess-return series (-6.27 / 307.2) suggest the sec 4.1 win is
concentrated in a small number of episodes where a large lump buy,
triggered by an elevated trailing-Sharpe percentile, happened to precede
a strong subsequent move -- exactly the pattern the DSR and placebo
circular-shift test are designed to catch, and exactly what happened here.
BTC is the one asset where the signal shows no edge at all in any
rolling window (0% in all 72 two-year BTC windows), consistent with its
short development history and high, regime-dependent volatility making a
percentile-ranked Sharpe reading noisy relative to its own trailing
distribution. This is a genuine, non-parameter-tunable negative result
for the risk-adjusted-momentum-ratio construction of the Kelly-sizing
hypothesis on this development data, distinct from (and a more thorough
test of) families 003's and 005's own separately-tested single-ingredient
versions -- as prereg.md's own honest expected-sign caveat anticipated
was a real possibility given both parent families' weak individual
results.
