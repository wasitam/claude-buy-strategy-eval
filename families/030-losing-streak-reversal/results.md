# Family 030 results: Losing-streak (consecutive-down-days) contrarian sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively:
it beats plain DCA on wealth AND Sharpe on only **2 of 5** core assets
(need >=3) at both fee levels. Sec 4.4's grid diagnostic also fails: only
**10 of 36 (27.8%)** configs reach the combined wealth-AND-Sharpe majority
bar (need >=2/3 = 24/36). DSR is effectively zero. Holdout was **not**
opened.

## Primary-config-in-grid verification (per family 021's lesson)

Verified programmatically at module import time (`assert PRIMARY_CONFIG in
grid_configs()` inside `losing_streak_reversal.py` itself) and
re-confirmed in the run script before any backtest: `PRIMARY_CONFIG =
{streak_threshold=3, buy_mult_streak=2.0, decay_days=5,
max_lump_multiple=3.0, buy_mult_winning=0.5}` is a genuine member of the
36-config grid (`cfg21_st3_bm2.0_dd5_ml3.0`). No mismatch found.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`, bypasses the streak computation entirely, buys 100% of cash every week-end day) reproduces plain DCA exactly (bit-for-bit on units and cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (aggressive grid corner: `streak_threshold=2, buy_mult_streak=2.0, decay_days=10, max_lump_multiple=3.0`) | PASS |
| Capital never exceeds cumulative deposits + interest, verified via the principled "never invest" ceiling-bound method (family 021's fix) -- primary config | PASS |
| Same capital-neutrality check -- aggressive grid corner | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged, checked at two spot-check points (`t=6000`, `t=20000`, both deep in the pre-2020 dev sample) | PASS (both) |
| Point-in-time macro data | N/A -- price-only signal (the asset's own daily Close, a raw consecutive-direction count), no macro/ALFRED series |

## Pre-grid non-degeneracy sanity check (per prereg.md, run before the grid)

Confirmed on real development data, using the primary configuration's own
streak/decay computation, **before** trusting any grid result. The
elevated (losing-streak) and reduced (winning-streak) state fractions are
both required to fall in a broad `(1%, 60%)` band, with at least 5
qualifying triggers of each kind, on every asset:

| Asset | Dev days | Frac. elevated | Frac. reduced | # down-streak triggers | # up-streak triggers | Non-degenerate? |
|---|---|---|---|---|---|---|
| SP500 | 23,109 | 37.88% | 37.89% | 2,473 | 3,487 | PASS |
| GOLD | 4,848 | 34.82% | 32.18% | 466 | 600 | PASS |
| SILVER | 4,850 | 32.89% | 34.91% | 442 | 643 | PASS |
| BTC | 1,932 | 31.47% | 39.80% | 155 | 290 | PASS |
| OIL | 4,857 | 36.94% | 35.43% | 508 | 637 | PASS |

The 3-consecutive-down-day trigger with a 5-day decay window fires
non-trivially and with comparable frequency to its winning-streak mirror
on every one of the 5 core assets -- the mechanism is doing what it is
pre-registered to do (a genuinely common, not-degenerate discrete-count
signal) before any grid result was trusted. Note the up-streak trigger
fires somewhat more often than the down-streak trigger on every asset,
consistent with these assets' positive long-run drift over their
development windows (upward-biased random walks produce more qualifying
up-runs than down-runs of the same length, all else equal) -- a real,
expected feature of the data, not a bug.

## Primary configuration: `streak_threshold=3, buy_mult_streak=2.0, decay_days=5, max_lump_multiple=3.0, buy_mult_winning=0.5`

### Sec 4.1 result (vs. plain per-asset DCA), development windows (BTC-gated)

| Asset | Strategy wealth/invested (0.1%) | DCA wealth/invested (0.1%) | Strategy Sharpe (0.1%) | DCA Sharpe (0.1%) | Beats DCA (both, 0.1%)? |
|---|---|---|---|---|---|
| SP500 | 85.174x | 85.277x | 0.15278 | 0.15310 | NO |
| GOLD | 2.230x | 2.231x | 0.50627 | 0.50492 | NO (wealth loses narrowly; Sharpe wins) |
| SILVER | 1.687x | 1.687x | 0.32134 | 0.31968 | NO (wealth loses narrowly; Sharpe wins) |
| BTC | 9.589x | 9.856x | 1.06522 | 1.06731 | NO |
| OIL | 1.184x | 1.180x | 0.23163 | 0.22782 | **YES** |

At 0.1% fees: **2/5** assets beat DCA on both wealth AND Sharpe (OIL
cleanly; GOLD and SILVER win Sharpe alone but lose narrowly on wealth;
SP500 and BTC lose on both). At 0.25% fees: also **2/5** (same pattern,
unchanged by the higher fee since this is a low-turnover, buy-only
strategy). **Sec 4.1: FAIL** at both fee levels (need >=3/5).

### Grid diagnostic (sec 4.4)

**10 of 36 configurations (27.8%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets, 0.1% fee) -- need >=2/3 (24/36). The
strongest corners are the lowest-threshold arms (`streak_threshold=2`,
which triggers most often): `cfg06`/`cfg07`
(`streak_threshold=2, buy_mult_streak=2.0, decay_days=3`) reach 4/5 on
wealth (3/5 combined), the grid's best single result, but no configuration
anywhere in the 36-arm grid reaches 4/5 or 5/5 on the combined
wealth-AND-Sharpe bar. Higher streak thresholds (3, 4 -- rarer, longer
streaks) consistently perform worse than `streak_threshold=2`, a sensible
pattern (a 3-4-day streak trigger is already a fairly demanding, low-
frequency condition on daily closes; requiring longer streaks thins the
sample of "elevated" weeks further without a compensating increase in the
strength of the rebound). **Sec 4.4: FAIL** (need >=24/36; got 10/36).

CSCV probability of backtest overfitting (36-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.0** -- the
grid's ranking of configurations is reproduced out-of-sample with no
overfitting signal detected by this diagnostic (a genuinely differentiated,
not merely noisy, grid, even though the top of that ranking still loses to
DCA outright).

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series
  (equal-weight average of the 5 per-asset excess series, strategy weekly
  NAV return minus DCA weekly NAV return): **-0.01148/week** (annualized
  ~-8.28%) -- negative.
- `N` (raw trial count, whole-loop pool): **905** (196 seeded + 673 from
  families 001-029 + 36 new from this family's grid) -- matches the
  task's sanity check (196+673=869 prior; +36 new = 905).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **74** clusters
  (up from family 029's 72 -- this family's 36 grid configs contribute 2
  new distinct clusters).
- **DSR (N_eff-based): 2.02e-23** -- essentially zero.
- DSR (raw-N, conservative reference): 9.42e-25.

**Sec 4.2: FAIL**, driven by the negative raw pooled excess-return Sharpe
(-0.0115/week) against an SR0 threshold of 0.1455/week at this loop's
N_eff=74 -- a wide margin, not a borderline miss.

### Robustness (sec 4.3)

**Not run.** Per the task's explicit instruction and established loop
precedent (families 006/007/008/011/013/029, most recently), sec 4.1's
2/5-asset result is already a decisive fail (need >=3/5), so the
rolling-window / block-bootstrap / placebo battery was skipped.

## Verdict

**REJECTED.** Sec 4.1 fails at both fee levels (2/5 assets, need >=3/5).
Sec 4.4's grid diagnostic also fails (10/36 = 27.8%, need >=24/36).
DSR is essentially zero (N_eff-based: 2.02e-23), driven by a negative raw
pooled excess-return Sharpe. Holdout was **not** opened.

## Interpretation

This family's discrete, magnitude-blind consecutive-down-day streak count
fires non-trivially on every core asset (confirmed by the pre-grid sanity
check) but the resulting "buy more after N down days, buy less after N up
days" sizing rule does not translate into a robust wealth-AND-Sharpe edge
over plain weekly DCA on this development data: only OIL shows a clean
win, GOLD and SILVER show a genuine Sharpe improvement that is not enough
to offset a small wealth shortfall (consistent with this being a
pure-timing, never-more-total-capital reallocation of a fixed deposit
stream, per prereg.md's own flagged caveat), and SP500/BTC show no
improvement at all. The grid pattern (lower streak thresholds, which
trigger more often on shorter/noisier streaks, perform somewhat better
than longer, rarer streak thresholds) is consistent with a diffuse,
low-conviction short-horizon reversal effect rather than a sharp,
economically strong one at any tested parameterization -- a genuine,
non-parameter-tunable negative result for this discrete streak-count
construction of the short-horizon reversal hypothesis, distinct from (and
not contradicted by) family 017's own separately-tested RSI2-ratio
construction of a related hypothesis.
