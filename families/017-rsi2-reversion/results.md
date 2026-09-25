# Family 017 results: RSI2 short-horizon mean-reversion sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1: it beats
plain DCA on final wealth AND Sharpe on only **2 of 5** core assets at
both fee levels, short of the required 3/5 majority. Sec 4.4's grid
diagnostic also fails decisively: only **2 of 24** configurations (8.3%)
reach the combined majority bar (need >=16/24). DSR is effectively zero.
Holdout was **not** opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family** (sec 4.1's Single-asset line),
across all 5 core assets, category **Sizing / valuation**. Signal: each
asset's own trailing `rsi_period`-day (2, primary) RSI oscillator, computed
purely from that asset's own Close series (no external data). Oversold
(`RSI < oversold_threshold`) buys more (`buy_mult_oversold * deposit`,
cash-capped); overbought (`RSI > overbought_threshold`) buys less
(`buy_mult_overbought=0.5` fixed, banking the remainder); normal buys plain
DCA. No sells, ever; no leverage.

**Rigorous triple distinction (required by this iteration's task):**
prereg.md documents three independent, load-bearing non-re-test arguments:
(1) vs. family 016 (VIX contrarian) -- a per-asset own-price oscillator vs.
a single shared cross-market implied-vol signal, with per-asset readings
that can (and do) diverge on the same day, unlike VIX's identical
elevated/calm flag across all 5 assets; (2) vs. family 003 (vol-managed
sizing) -- a directional gain/loss-ratio oscillator vs. a direction-agnostic
realized-variance statistic, opposite sign logic and a different input
statistic entirely; (3) vs. families 001/005 (long-horizon trend exit /
12-month TSMOM) -- a 2-4 trading-day mean-reversion signal (buy more after
recent FALLS) vs. a 200-252+ trading-day trend-following signal (buy more
after recent RISES), opposite time horizon (three orders of magnitude) and
opposite economic logic (mean reversion vs. momentum persistence). Also
documented explicitly why this is not a re-test of v1's closed Signal A
(ATR shock, a range/dispersion statistic on a single day, vs. RSI2's
multi-day directional gain/loss-ratio oscillator).

## Pre-backtest non-degeneracy check (per the task's explicit instruction, following family 015/016's precedent after family 014's oversight)

Before any backtest, the primary config's (`rsi_period=2,
oversold_threshold=10, overbought_threshold=90`) oversold and overbought
frequencies were computed directly for all 5 core assets:

| Asset | Dev days | Oversold (RSI<10) | Frac. oversold | Overbought (RSI>90) | Frac. overbought |
|---|---|---|---|---|---|
| SP500 | 23,109 | 6,209 | 26.87% | 7,710 | 33.36% |
| GOLD | 4,848 | 1,219 | 25.14% | 1,497 | 30.88% |
| SILVER | 4,850 | 1,196 | 24.66% | 1,507 | 31.07% |
| BTC | 1,932 | 457 | 23.65% | 658 | 34.06% |
| OIL | 4,857 | 1,269 | 26.13% | 1,450 | 29.85% |

Every asset's oversold AND overbought frequencies are comfortably
non-degenerate (well within the pre-registered `(2%, 40%)` sanity band, and
consistent across all 5 assets) -- as expected, a 2-day RSI oscillates
frequently by construction, unlike the slower macro/regime signals of
families 011/014/015/016. This confirms the mechanism fires non-trivially
before any backtest is trusted.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (aggressive corner: `rsi_period=2, oversold_threshold=15, overbought_threshold=85, buy_mult_oversold=2.0`) | PASS |
| Total capital deployed never exceeds cumulative deposits + interest, within a 5% empirical bound (primary config) | PASS |
| Total capital deployed never exceeds cumulative deposits + interest (aggressive corner) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000` and `t=9500`) -- RSI2's 2-day lookback makes this an easy causality check (see prereg.md) | PASS |
| Point-in-time macro data | N/A -- RSI2 uses only the asset's own OHLC, no external/macro data at all |
| Primary-config regime non-degeneracy (pre-registered check, per-asset) | PASS -- see table above |

## Primary configuration: `rsi_period=2, oversold_threshold=10, overbought_threshold=90, buy_mult_oversold=2.0, buy_mult_overbought=0.5`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.358 | 85.277 | 0.15502 | 0.15310 | YES |
| GOLD | 2.227 | 2.231 | 0.50539 | 0.50492 | NO (wealth fails) |
| SILVER | 1.688 | 1.687 | 0.32253 | 0.31968 | YES |
| BTC | 9.750 | 9.856 | 1.07610 | 1.06731 | NO (wealth fails) |
| OIL | 1.177 | 1.180 | 0.23043 | 0.22782 | NO (wealth fails) |

**Sec 4.1: FAIL**, 2/5 core assets (SP500, SILVER) at both fee levels
(0.25% results are qualitatively identical -- see `_primary_per_asset.csv`),
short of the required 3/5 majority. Notably, the primary config's Sharpe
beats DCA on **all 5** assets -- the mechanism does smooth the return path
everywhere -- but wealth only beats DCA on 2 of 5 (GOLD, BTC, OIL lag on
final wealth despite the Sharpe improvement), so the combined bar fails on
3 of the 5 assets.

### Grid diagnostic (sec 4.4)

**2 of 24 configurations (8.3%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees -- both from the least
literal corner of the grid (`rsi_period=4, oversold_threshold=15,
overbought_threshold=85, buy_mult_oversold=2.0`, i.e. `cfg21` and `cfg23`,
the loosest thresholds and slowest RSI period tested, farthest from
Connors & Alvarez's canonical `rsi_period=2` / `10`/`90` convention). No
config anywhere in the grid at the canonical `rsi_period=2` reaches 3/5 on
wealth+Sharpe combined (the best `rsi_period=2` showing, `cfg03`/`cfg05`,
is exactly the primary config's own 2/5). Sharpe alone is easy to beat
(15 of 24 configs hit >=4/5 on Sharpe, many hit 5/5), but wealth is the
binding constraint everywhere (see `grid_results.csv` for the full
per-config breakdown).

**Sec 4.4: FAIL** (need >=2/3 = 16/24; got 2/24 = 8.3%).

CSCV probability of backtest overfitting (24-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.0** -- the
grid's corners are not "overfit" in the CSCV sense; the pattern (Sharpe
improves broadly, wealth lags on 3/5 assets at the primary and most grid
configs) is consistent across resampled splits rather than a lucky
in-sample fluke.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series
  (strategy weekly NAV return minus DCA weekly NAV return, averaged across
  the 5 assets): **+0.00208** (weekly, **+0.015 annualized**) -- barely
  positive, essentially indistinguishable from zero at this scale, and
  swamped by the trial-count penalty.
- `N` (raw trial count, whole-loop pool): **547** (196 seeded + 327 from
  families 001-016 + 24 new from this family's grid; matches the sanity
  check 196+351=547, `state/trial_counter.json["new"]`=351 after this
  family).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **60** clusters
  (up from 58 after family 016 -- this family's grid contributed 2 new
  distinct clusters not already covered by prior families' excess-return
  series).
- **DSR (N_eff-based): ~2.83e-25** -- effectively zero. The raw excess
  Sharpe (0.0021/week) is far below the SR0=0.151 threshold implied at
  this N_eff, and the series' high excess kurtosis (77.6, from a handful
  of dominant weekly episodes) further penalizes the DSR calculation.
- DSR (raw-N, conservative reference): ~1.76e-31, also effectively zero.

**Sec 4.2: FAIL**, decisively -- a barely-positive raw excess Sharpe cannot
clear the trial-count-adjusted DSR bar at either N or N_eff.

### Robustness (sec 4.3)

**Not run.** Per the established precedent (sec 4.3 is only attempted if
sec 4.1 passes first), and sec 4.1 fails (2/5, short of the 3/5 majority),
the rolling-window / block-bootstrap / placebo battery was skipped (the run
script is wired to run it automatically on a sec-4.1 pass, and correctly
skipped it here).

## Verdict

**REJECTED.** Sec 4.1 fails at both fee levels (2/5 core assets, short of
the 3/5 majority -- driven by Sharpe improving broadly while wealth lags on
3 of 5 assets). Sec 4.4's grid diagnostic fails (2/24, need >=16/24). DSR
is effectively zero (barely-positive raw Sharpe, swamped by the trial-count
penalty and high excess-kurtosis). Holdout was **not** opened.

## Interpretation

The RSI2 mechanism, at its canonical Connors & Alvarez parameters, produces
a genuinely different -- and directionally sensible-looking -- result from
every strictly-losing family so far: it improves risk-adjusted return
(Sharpe) on every single core asset, consistent with the literature's claim
that buying into short-term oversold dips smooths the entry-price path. But
it does not translate that into more final wealth on a majority of assets,
and the grid confirms this is not a fluke of the primary parameter choice:
even the two grid corners that do clear the wealth bar on 3/5 assets use a
slower, less literal RSI (`rsi_period=4`, wider `10`-point thresholds) than
Connors & Alvarez's own headline 2-period/10/90 rule, and even those
corners fail the deflated-Sharpe bar by construction (DSR is computed on
the PRIMARY config only, and even the near-miss corners share the same
weak raw-Sharpe order of magnitude). A plausible reading: at weekly deposit
cadence (this family's engine only sizes a once-a-week decision, not a
daily entry/exit as in the original RSI2 trading literature), a 2-4 day
reversal signal is mostly "stale" by the time the week's single decision is
made -- the RSI2 reading on the week-end day captures only the most recent
handful of sessions, and whichever few of those sessions happen to fall
immediately before the week-end decision day dominate the signal, diluting
the edge relative to a daily-frequency implementation. This is consistent
with, but does not confirm, the caveat flagged explicitly in prereg.md's
"Expected sign" section before any backtest was run. This does not rule out
a different RSI2 adaptation (e.g. reacting mid-week rather than only on
week-end days) but this specific family, as pre-registered and tested,
does not clear sec 4.1.

## Trial accounting

- Seed: 196 (unchanged).
- New before this family: 327 (families 001-016).
- New from this family's 24-config grid: 24.
- New total after this family: 327 + 24 = 351 (matches
  `state/trial_counter.json`).
- Raw N at assessment: 196 + 351 = **547** (matches `n_total_raw` in
  `_run_output.json`).
- N_eff at assessment: **60** (up from 58 -- 2 new distinct clusters).
- Families (new) count: 15 (was 14 before this family).

## Files

- `families/017-rsi2-reversion/prereg.md` -- pre-registration (committed
  before any backtest).
- `families/017-rsi2-reversion/grid_results.csv` -- full 24-config x
  5-asset x 2-fee grid.
- `families/017-rsi2-reversion/_primary_per_asset.csv` -- primary config's
  per-asset summary.
- `families/017-rsi2-reversion/_run_output.json` -- machine-readable
  summary of all checks above.
- `src/backtest/v3/strategies/rsi2_reversion.py` -- implementation.
- `scripts/v3/run_017_rsi2_reversion.py` -- end-to-end run script.
- `state/trials/new_017_*.csv` -- 24 new trial excess-return series.
