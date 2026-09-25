# Family 028 results: 50/200-day moving-average crossover regime tilt ("golden cross" / "death cross")

**Verdict: NEAR-MISS.** The primary configuration passes sec 4.1 (beats
plain DCA on wealth AND Sharpe on **3 of 5** core assets, at both fee
levels) and sec 4.4's grid diagnostic (**28/36, 77.8%**, of configurations
reach the combined majority bar -- the strongest sec 4.4 result of any
family tested in this loop so far). It **fails sec 4.2** (Deflated Sharpe
effectively zero) and **fails sec 4.3** (block bootstrap and placebo both
fail, though rolling windows pass). Per research-loop-plan-v3.md sec 8
step 7, a family that passes sec 4.1 but not sec 4.2-4.4 is a **near-miss**
-- logged, not promoted. Holdout was **not** opened.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (aggressive corner: `fast_days=20, slow_days=100, persistence_days=0, bull_mult=1.5`) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (primary and aggressive corner, family 021's principled "never invest" ceiling-bound method) | PASS |
| **No-lookahead**, spot-checked at `t=6000` and `t=20000`, perturbing all OHLC strictly after the check point | PASS |

This family uses only each asset's own daily Close (no macro/external
data), so it carries no publication-lag / point-in-time-macro risk at all
-- a genuine simplicity advantage over the loop's recent macro-regime
families (011/015/019/027).

## Pre-grid known-episode sanity check (signal correctness, before any backtest)

The raw (`persistence_days=0`) 50-day/200-day SMA crossover on SP500 was
spot-checked against well-documented historical golden crosses. The task
names 2009, 2016 and 2020 as examples. **2020's crossing (2020-07-24,
public record) falls inside the sealed 2020+ holdout period** -- checking
it here, before any finalist has been identified or the holdout properly
opened per sec 5.2, would itself have been an improper holdout look
(caught and corrected before the grid ran; see `state/bugfix_log.md`).
Substituted with 2003-05-14 (the well-documented post-dot-com-bust golden
cross), alongside the still-valid 2009 and 2016 windows, all three within
development data:

| Window | Golden cross found? |
|---|---|
| 2003-04-15 .. 2003-06-15 | YES |
| 2009-06-01 .. 2009-08-15 | YES |
| 2016-03-15 .. 2016-05-15 | YES |

47 total raw golden-cross events registered on SP500's full development
history (1928-2019), confirming the signal fires correctly and
non-trivially before any backtest result was trusted.

## Pre-grid non-degeneracy check (primary config, before the grid ran)

| Asset | Bullish (golden-cross regime) frac | Raw crossovers | Non-degenerate? |
|---|---|---|---|
| SP500 | 67.5% | 94 | YES |
| GOLD | 72.9% | 20 | YES |
| SILVER | 56.8% | 26 | YES |
| BTC | 69.0% | 7 | YES |
| OIL | 62.4% | 28 | YES |

BTC's short development window (2014-09 to 2019-12) still produces 7
raw crossovers and a non-degenerate 69.0% bullish fraction -- unlike
family 027's macro signal, this family's per-asset price-derived signal
did **not** turn out to be degenerate on BTC, so no BTC exemption was
needed here.

## Primary-config-in-grid verification

Verified both **programmatically** (`assert PRIMARY_CONFIG in
grid_configs()` in the run script) and via an explicit
**module-import-time assertion** in
`src/backtest/v3/strategies/ma_crossover_regime.py` itself (`assert
PRIMARY_CONFIG in grid_configs()` runs on import, per family 021's
lesson) -- primary config `fast_days=50, slow_days=200,
persistence_days=5, bull_mult=1.5, bear_mult=0.5` is confirmed a genuine
member of the 36-config grid.

## Primary configuration: `fast_days=50, slow_days=200, persistence_days=5, bull_mult=1.5, bear_mult=0.5` (`max_lump_multiple=6` fixed)

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.287 | 85.277 | 0.153101 | 0.153097 | YES (razor-thin on both, 92-year history) |
| GOLD | 2.2314 | 2.2312 | 0.50495 | 0.50492 | YES |
| SILVER | 1.6867 | 1.6867 | 0.31956 | 0.31968 | NO (Sharpe loses, narrowly) |
| BTC | 9.85702 | 9.85568 | 1.067445 | 1.067309 | YES |
| OIL | 1.18038 | 1.17986 | 0.227714 | 0.227824 | NO (Sharpe loses, narrowly) |

**Sec 4.1: PASS** -- 3/5 core assets (SP500, GOLD, BTC) beat DCA on
wealth AND Sharpe together, at both 0.1% and 0.25% fees (qualitatively
identical at 0.25%, see `_primary_per_asset.csv`). Every asset beats DCA
on wealth alone; the two failing assets (SILVER, OIL) lose only on
Sharpe, and by a small margin. As with family 027's SP500 result, the
margins here are consistently thin relative to the raw wealth multiples
-- this mechanism only reallocates the *timing* of a fixed deposit
stream (a persistent tilt toward buying more in a historically
bull-confirming regime and less in a bear-confirming one), never total
capital deployed, so even where it wins the absolute margin over
multi-decade compounding is modest, consistent with every other
timing/tilt family in this loop.

### Grid diagnostic (sec 4.4)

**28/36 (77.8%)** configurations reach the combined majority-of-assets
bar (need >=24/36 = 2/3) -- **PASS**, the strongest sec 4.4 grid result
of any family tested in this loop to date. Breaking down by `ma_pair`:
the (20,100) pair reaches 4/5 assets on 8/12 of its configs (persistence
0 or 5) and 4/5 or 3/5 with `persistence_days=10`; the (50,200) and
(50,150) pairs mostly cluster around 3/5-4/5 with `persistence_days<=5`,
dropping to 2/5 at `persistence_days=10` for both. Longer confirmation
delays consistently weaken the signal across all three pairs -- a
sensible pattern (waiting 10 days to confirm a regime flip both misses
some of the move and still doesn't fully eliminate whipsaw). The primary
config sits in the (50,200) pair's `persistence_days=5` group (3/5,
passing sec 4.1), not the grid's strongest corner -- per sec 4.4's
diagnostic-only rule, the primary configuration's pre-registered,
literature-faithful choice is what is assessed, not the best-looking
grid cell.

## CSCV probability of backtest overfitting

**PBO = 0.171** (12/70 combinatorial splits show the in-sample-best
configuration underperforming out-of-sample median) -- moderate, higher
than family 027's 0.057 but still well below 0.5, consistent with a
grid that is genuinely differentiated by its parameters (`ma_pair` and
`persistence_days` both drive real, monotone-ish performance
differences) rather than a flat field of noise.

## Deflated Sharpe Ratio (sec 4.2)

At this loop's current trial count (857 raw trials, **N_eff = 72**
clusters after average-linkage clustering at rho>=0.5), the primary
config's pooled excess-return series has annualized Sharpe
**-0.0379** (slightly negative, despite the 3/5-asset sec 4.1 pass --
the pooled series averages across all 5 assets' weekly excess returns
equally, and SILVER/OIL's Sharpe losses pull the pooled mean down even
though 3 of 5 assets individually beat DCA on both metrics). The
required threshold SR0 at N_eff=72 is **0.1463**. **DSR is effectively
zero** (3.42e-27) -- far below the required 0.95. Extreme negative skew
(-8.83) and very high kurtosis (337.6) in the weekly excess-return
series reflect a small number of large negative jumps dominating the
distribution (consistent with a trend-tilt strategy occasionally being
badly wrong-footed at a whipsaw reversal). At raw N (857, no
clustering), DSR is even smaller (3.68e-28).

## Robustness (sec 4.3, run in full since sec 4.1 passed; n_sims=60 time budget)

### Rolling windows

| Window set | n | Beats wealth | Beats Sharpe |
|---|---|---|---|
| SP500 3y | 1118 | 56.4% | 57.7% |
| SP500 5y | 1093 | 71.5% | 74.7% |
| GOLD 3y | 205 | 68.8% | 59.5% |
| GOLD 5y | 180 | 97.8% | 90.6% |
| SILVER 3y | 205 | 66.3% | 66.3% |
| SILVER 5y | 180 | 81.7% | 77.2% |
| OIL 3y | 206 | 65.5% | 66.0% |
| OIL 5y | 180 | 81.7% | 80.6% |
| BTC 2y | 72 | 41.7% | 43.1% |
| **Overall (pooled)** | **3439** | **67.6%** | **67.8%** |

**PASS** -- pooled pass rate exceeds the required >60% threshold on both
wealth and Sharpe, though BTC's 2-year windows fail outright (41.7%/
43.1%) and SP500's shorter 3-year windows are close to a coin flip
(56.4%/57.7%) -- the 5-year windows across every asset except BTC (which
has no 5-year window available in its short dev history) are
consistently strong (71.5%-97.8%).

### Block bootstrap (60 sims each, SP500 representative)

| Path | Beats wealth (majority) | Beats Sharpe (majority) |
|---|---|---|
| Raw | 46.7% | 45.0% |
| Detrended | 73.3% | 51.7% |

**FAIL** -- the raw-path bootstrap does not reach a majority on either
metric (46.7%/45.0%, both below 50%), and the detrended path's Sharpe
result (51.7%) is only barely above a coin flip. This is the sharpest
divergence in this family's results: rolling windows on the *actual*
historical path pass comfortably, but resampled synthetic paths built
from the same underlying return distribution do not reproduce the edge
reliably -- consistent with the strategy benefiting disproportionately
from the specific historical sequencing of trends in SP500's real path
(exactly what a block bootstrap is designed to stress-test for).

### Placebo (circular-shift the primary config's own confirmed-bullish array, 60 sims, SP500)

Real result: wealth/invested = 85.287, Sharpe = 0.15310.
Percentile of the real result within 60 circularly-shifted-signal runs:
**76.7th (wealth)**, **41.7th (Sharpe)**. **FAIL** -- need >=95th
percentile on both; the Sharpe result is not even above the shifted
median, meaning most random temporal alignments of a same-frequency
bull/bear regime produce as good or better Sharpe than the real,
correctly-aligned crossover signal. This is the most direct evidence
against the mechanism specifically working *because of* its temporal
alignment with SP500's actual historical trend structure, as opposed to
simply being "some persistent regime that spends most of its time
tilted bullish in an asset that trends up over 92 years."

## Distinction from family 001 (10-month/200-day trend exit)

Family 001's signal is price level vs. a **single** ~200-day SMA
(binary invest/park-in-cash). This family's signal is a relationship
**between two** moving averages of price (never compares price to a
moving average directly), and the action is a continuous buy-size tilt
with a banked-cash catch-up mechanic, never a binary exit. See
`prereg.md`'s full argument, including the empirical observation that
the two signals frequently disagree in exactly the transition periods
after a sharp rebound (price can clear its 200-day SMA well before the
50-day SMA clears the 200-day SMA).

## Distinction from family 005 (time-series momentum sizing)

Family 005's signal is the sign of a **point-to-point trailing total
return** (no moving average anywhere in its construction --
`tsmom_sizing.py`'s `compute_signal` never computes a rolling mean of
price). This family's signal is built entirely from two rolling means
and is structurally slower/more lagged by construction, not merely by
parameter-tuning coincidence, since a moving-average crossover requires
the *average* of the recent window to clear the *average* of the longer
window, not just the two endpoint prices a trailing-return signal uses.

## Distinction from v1's closed-list Signal B ("trend-stretch")

v1 Signal B (`btc-gold-silver-backtest-spec.md` sec 3.2) is `(close -
MA_40w) / ATR_14w`, a **single**-moving-average distance measure
converted to an ATR-normalized percentile-of-own-distribution threshold,
triggering a buy/trim(sell). No second moving average, no crossover
concept, no persistence-confirmation filter, and a percentile threshold
rather than a levels-based crossover test -- not a re-test on any
reading of sec 7.2.

## Judgment calls made this iteration

1. **Holdout-period known-episode substitution.** The task named 2020 as
   one of three SP500 golden-cross spot-check dates, but 2020-07-24
   falls inside the sealed holdout. Substituted 2003-05-14 (equally
   well-documented) to keep the sanity check entirely within development
   data. Logged in `state/bugfix_log.md` since it was caught after an
   initial failed run but before any backtest result was trusted or
   computed.
2. **`ma_pair` treated as one categorical tunable parameter** (3
   literature-motivated pairs) rather than an independent cross-product
   of `fast_days` x `slow_days`, to keep the grid at the golden/death-
   cross MECHANISM (short MA vs. long MA, both in the "medium/long-term
   trend" range) per the task's explicit instruction, rather than
   drifting into unrelated pairs (e.g. a 5-day/20-day short-term-noise
   construction).
3. **BTC needed no short-history exemption** in this family, unlike
   family 027 -- the primary config's confirmed-bullish signal is
   non-degenerate on BTC (69.0% bullish, 7 raw crossovers), so the
   pre-grid sanity gate did not need to except it.
4. **Reported the block-bootstrap/placebo divergence from rolling
   windows plainly** rather than downplaying it: this is read as the
   single most informative piece of evidence this family produced,
   consistent with the concern already flagged in `prereg.md`'s
   "Expected sign" section that a famous, heavily-followed signal is at
   real risk of reflecting a generic "spends most of its time bullish in
   a trending asset" pattern rather than a specifically well-timed
   crossover edge.
