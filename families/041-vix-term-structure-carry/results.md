# Family 041 results: VIX futures term-structure carry (contango/backwardation)

**Verdict: NEAR-MISS.** The primary configuration passes sec 4.1 (beats
DCA on wealth AND Sharpe on **4 of 5** core assets at both fee levels) but
**fails sec 4.2** (Deflated Sharpe Ratio is essentially zero, ~1.09e-20,
against a 0.95 threshold), **fails sec 4.4** (only 55.6% of the 36-config
grid clears the combined majority bar, below the required 2/3), and
**fails sec 4.3 decisively on all three legs** (rolling windows,
bootstrap, and placebo all fall well short of their bars). Holdout was
**not** opened (not a finalist).

## Data-feasibility check (done first, per this iteration's task instruction)

`^VIX3M` (CBOE 3-Month Volatility Index) is reachable via yfinance --
`yf.Ticker("^VIX3M").history(period="max")` returns 5,081 daily rows,
**2006-07-17 through today**, a genuine term-structure counterpart to
spot `^VIX` (used unchanged by families 016/025), not a re-parameterization
of it. A first probe using `yf.download()`'s default window returned only
~22 rows for `^VIX3M`/`^VIX9D`/`^VIX6M`; using
`yf.Ticker(...).history(period="max")` (the same call
`src.backtest.v3.data._fetch_yf_raw` already uses for every other ticker
in this codebase) confirmed the full history above. **Verdict: feasible.**
Idea #42 proceeded as this iteration's family; no substitute idea was
needed (see `state/research_queue.md`'s entry for idea #42).

## Category and required distinction from families 016 and 025

Filed as **Carry / term structure** -- the first family in this loop to
use this category. Rigorously distinguished in `prereg.md` from family 016
(VIX *level* alone, a single point on the curve) and family 025 (VIX minus
each asset's own *realized* volatility, a cross-measure spread at a single
tenor): this family's signal, `ratio_t = VIX3M_t / VIX_t`, is a ratio of
two **implied**-volatility measures at two **different tenors** on the
**same curve**, and never touches realized volatility at all.

**Distinction-verification check, computed live on real overlapping
development data (2006-07-17..2019-12-31, SP500)** before any grid result
was trusted:

| Check | Result |
|---|---|
| Overlap days (both `^VIX` and `^VIX3M` available) | 3,389 |
| Fraction of days where this family's backwardation flag (`ratio_t<1`) agrees with family 016's own primary-config elevated-VIX-level flag | **92.4%** |
| Genuinely different (neither 0% nor 100% agreement)? | **Yes** |
| Correlation of the raw `VIX3M/VIX` ratio with the raw `^VIX` level | **-0.667** |
| Not simply a relabeling of the VIX level (`|corr| < 0.9`)? | **Yes** |

The two signals disagree on 7.6% of overlap days and are only moderately
(not near-perfectly) correlated -- confirming the term-structure ratio is
a genuinely different statistic from the VIX level alone, not an
accidental collapse onto family 016's signal.

## Single-asset scoping

Assessed as a **single-asset family across all 5 core assets** under sec
4.1's standard >=3/5 rule, following families 006/007/011/015/016/019/
025/027/032/038's precedent for a single shared, asset-agnostic market
signal applied independently per asset -- no capital ever moves between
assets.

## Data availability vs. each asset's development window

Computed live before trusting any backtest (matches `prereg.md`'s
documented expectations exactly):

| Asset | Dev days | `^VIX3M`-available dev days | Frac. available |
|---|---|---|---|
| SP500 | 23,109 | 3,389 | 14.7% |
| GOLD | 4,848 | 3,387 | 69.9% |
| SILVER | 4,850 | 3,387 | 69.8% |
| BTC | 1,932 | 1,932 | **100%** |
| OIL | 4,857 | 3,388 | 69.8% |

Before `^VIX3M` history exists (SP500's pre-2006 stretch, and every
asset's initial `ts_lookback` warm-up window), the multiplier defaults to
1.0 (neutral, plain-DCA-equivalent) -- confirmed by the pre-grid
non-degeneracy check below (SP500's much higher "frac. multiplier exactly
1.0" reflects this long pre-availability stretch, not a degenerate
signal within its available window).

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Distinction-verification vs. family 016 (genuinely different, not a relabeling) | PASS |
| Degenerate config (`enabled=False`) reproduces plain DCA exactly (bit-for-bit) | PASS |
| Second reference point: real `k=0.0` grid-shaped code path also reproduces plain DCA exactly | PASS |
| Cash-reserve-dynamics check (reserve builds up vs. DCA; drawn down on elevated-multiplier weeks) | PASS ($106.23 avg cash vs. DCA's $103.88; $132.80 on low-multiplier weeks vs. $110.91 on high-multiplier weeks) |
| Cash and positions never negative (DCA baseline, primary config, aggressive grid corner) | PASS |
| Capital never exceeds cumulative deposits + interest (principled "never invest" ceiling bound, primary and aggressive corner) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (`t=6000`, `t=20000`) | PASS (both) |
| Point-in-time macro data | N/A -- `^VIX`/`^VIX3M` are daily market-price series with no revision/publication-lag concern |

## Pre-grid non-degeneracy sanity check

Confirmed on real development data for all 5 core assets before trusting
any grid result:

| Asset | Dev days | Frac. multiplier == 1.0 | Std(multiplier) | Non-degenerate? |
|---|---|---|---|---|
| SP500 | 23,109 | 86.49% | 0.197 | PASS |
| GOLD | 4,848 | 35.62% | 0.427 | PASS |
| SILVER | 4,850 | 35.65% | 0.427 | PASS |
| BTC | 1,932 | 13.25% | 0.484 | PASS |
| OIL | 4,857 | 35.72% | 0.426 | PASS |

SP500's much higher "stuck at 1.0" fraction is expected and fully
explained by its long pre-2006 `^VIX3M`-unavailable stretch (documented
above), not by the signal being degenerate within its available window --
consistent with `^VIX`-based families 016/025's own analogous SP500
caveat.

## Primary configuration: `ts_lookback=252, k=1.0, min_mult=0.5, max_mult=2.0` (`max_lump_multiple=3.0` fixed)

### Sec 4.1 result (vs. plain per-asset DCA), development windows

| Asset | Strategy wealth/invested (0.1%) | DCA wealth/invested (0.1%) | Strategy Sharpe (0.1%) | DCA Sharpe (0.1%) | Beats DCA (both, 0.1%)? |
|---|---|---|---|---|---|
| SP500 | 85.27730 | 85.27722 | 0.153097 | 0.153097 | **YES** (razor-thin) |
| GOLD | 2.23119 | 2.23123 | 0.504917 | 0.504917 | NO (loses both, razor-thin) |
| SILVER | 1.68667 | 1.68666 | 0.319680 | 0.319677 | **YES** (razor-thin) |
| BTC | 9.85637 | 9.85568 | 1.067480 | 1.067309 | **YES** |
| OIL | 1.18034 | 1.17986 | 0.227906 | 0.227824 | **YES** |

At 0.1% fees: **4/5** assets beat DCA on both wealth AND Sharpe (SP500,
SILVER, BTC, OIL win; GOLD is the sole loser, and loses both metrics by a
razor-thin margin). At 0.25% fees: also **4/5**, same pattern. **Sec 4.1:
PASS** at both fee levels (need >=3/5). Every margin is small, consistent
with this being a pure-timing reallocation of a fixed deposit stream, not
a change in total capital deployed.

### Grid diagnostic (sec 4.4)

**20 of 36 configurations (55.6%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets, 0.1% fee) -- **below** the 2/3 (24/36)
requirement. **Sec 4.4: FAIL.** The grid shows a clear pattern: the
longer `ts_lookback=504` arms are the strongest (10/12 configs at 4/5),
the `ts_lookback=252` arms are mixed (ranging from 1/5 at high `k` with
`min_mult=0.25` up to 5/5 at `k=1.5, min_mult=0.5`), and the shorter
`ts_lookback=126` arms are uniformly the weakest (mostly 1-3/5, never
reaching 4/5) -- the primary's own `ts_lookback=252` choice sits in the
middle of this range rather than at either extreme, consistent with the
plan's own diagnostic-only framing of the grid (the loop never switches to
a better-looking configuration after seeing results).

CSCV probability of backtest overfitting (36-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.314** --
moderate, in a similar range to several other REJECTED/NEAR-MISS families
this loop (e.g. family 038's 0.214, family 039's 0.443).

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series
  (equal-weight average of the 5 per-asset excess series): **0.009094/
  week** (annualized ~6.56%) -- small and positive, with extreme positive
  skew (25.06) and kurtosis (1261.7), an even more extreme "many small
  wins, rare large gains from a thin tail" signature than most prior
  continuous-multiplier sizing families in this loop.
- `N` (raw trial count, whole-loop pool): **1,257** (196 seeded + 1,061
  new = 1,257, matching `state/trial_counter.json`'s updated `new: 1061` =
  1,025 through family 040 + 36 new from this family's grid).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **128**
  clusters (up from family 040's 126 -- this family's 36 grid configs
  opened 2 new clusters distinct from the existing 126).
- **DSR (N_eff-based): 1.089e-20** -- essentially zero, against an SR0
  threshold this loop's N_eff=128 now demands (SR0=0.1284/week).
- DSR (raw-N, conservative reference): 1.789e-22.

**Sec 4.2: FAIL**, decisively -- the raw pooled excess-return Sharpe
(0.00909/week) is far below the SR0 bar this loop's accumulated trial
count now demands, despite the positive sec 4.1 asset count.

### Robustness (sec 4.3, run in full since sec 4.1 passed, n_sims=60 time-budget)

- **Rolling windows** (3y/5y for SP500/GOLD/SILVER/OIL, 2y for BTC, 3,439
  total windows): pooled **23.4% wealth / 23.8% Sharpe** -- both **far
  below** the required >60%, the weakest rolling-window result of any
  NEAR-MISS family in this loop so far. SP500's own 3y/5y windows are
  particularly weak (8.5%/9.2% wealth, 9.4%/11.2% Sharpe), while OIL's 5y
  windows are the strongest leg (73.3%/66.7%) but still not enough to
  carry the pooled result. **FAIL, decisively.**
- **Block bootstrap** (500-run budget honored at the n_sims=60 time-boxed
  convention, SP500, 4-week blocks): raw-path **48.3%/50.0%** (below or at
  majority on both), detrended **53.3% wealth / 48.3% Sharpe** (wealth
  barely above majority, Sharpe below -- both required). **FAIL.**
- **Placebo** (circular-shift the primary config's own multiplier array
  `m_t`, SP500, 60 shifts): the real result lands at the **50.0th
  percentile on wealth** and the **46.7th percentile on Sharpe** -- almost
  exactly the *median* of the placebo distribution, far short of the
  required >=95th on either metric. This is one of the most decisive
  placebo failures in this loop: the primary config's own real result is
  statistically indistinguishable from a randomly time-shifted version of
  its own signal. **FAIL, decisively.**

**Sec 4.3: FAIL** on all three sub-checks, the rolling-window and placebo
legs particularly decisive.

## Assessment summary

| Check | Result | Pass? |
|---|---|---|
| Sec 4.1 (beats DCA >=3/5, both fees) | 4/5 at both fees | PASS |
| Sec 4.2 (DSR >= 0.95) | 1.09e-20 (N_eff), 1.79e-22 (raw N) | FAIL |
| Sec 4.3 (rolling/bootstrap/placebo) | rolling 23.4%/23.8% (need >60%); bootstrap raw+detrended FAIL; placebo 50.0th/46.7th pctile (need >=95th) | FAIL |
| Sec 4.4 (>=2/3 of grid beats DCA majority) | 20/36 (55.6%) | FAIL |

**Verdict: NEAR-MISS** (passes sec 4.1 only; fails sec 4.2, 4.3 AND 4.4).
Logged, not promoted to finalist. Holdout not opened, per sec 5.4.

## Interpretation

The term-structure ratio's sec 4.1 pass (4/5 core assets, razor-thin
margins) is, by every downstream check available, indistinguishable from
noise: the placebo circular-shift test lands almost exactly at the median
of 60 randomly time-shifted versions of the same signal (50.0th/46.7th
percentile), the rolling-window pass rate (23.4%/23.8%) is not merely
below the 60% bar but the weakest of any NEAR-MISS family logged in this
loop so far, and the grid diagnostic itself is mixed rather than uniformly
strong (55.6%, failing sec 4.4, unlike family 040's 83.3% or family 028's
77.8%). Taken together, this is a more decisive negative result than the
"sec 4.1 passes narrowly, DSR/placebo fail narrowly" pattern several
other continuous-sizing families in this loop showed (e.g. families
031/040): here, every downstream robustness check fails by a wide margin,
not a close one. A plausible reading, consistent with the "expected sign"
caveat already flagged in `prereg.md`: `^VIX3M`'s relatively short history
(2006+) gives this signal access to genuinely fewer distinct
contango/backwardation regime transitions in development data than
family 016's `^VIX`-level-based signal (1990+) saw, so whatever thin sec
4.1 signal exists is more likely attributable to a small number of
episodes (plausibly concentrated around 2008-09 and 2011) than to a
reliable, time-invariant term-structure carry effect -- exactly the kind
of few-dominant-episode result the rolling-window and placebo tests are
designed to catch, and did catch here more decisively than in most prior
families.

## Judgment calls

1. **Sign choice: the literature-faithful, non-contrarian carry-premium
   reading** (bank during backwardation, ride the carry premium during
   contango) was pre-registered as this family's primary mechanism,
   explicitly instead of a second contrarian "buy more into backwardation"
   variant -- since family 016 already tests a contrarian VIX-based bet,
   using the same sign here would have weakened this family's own
   mechanistic distinctness, not merely duplicated a parameter choice.
2. **Functional form: continuous percentile-scaled multiplier** (matching
   families 030/031/036/039/040's construction), not a discrete ladder, to
   avoid the confirmed cash-cap-nullification bug (families 014/033/037's
   documented failure mode) -- verified directly via the cash-reserve-
   dynamics check rather than merely asserted, and every grid cell's
   `min_mult` is asserted <1.0 at import time.
3. **Tenor-pair choice**: `^VIX`/`^VIX3M` (not `^VIX9D`/`^VIX6M` or some
   other pair) fixed rather than grid-varied, chosen as the most standard,
   most-cited pair in the cited literature and for its longer available
   history (2006 vs. 2008/2011) -- a pre-registered, not
   development-data-informed, choice.
4. This result adds the **first "Carry / term structure" category** data
   point to this loop's now-large set of REJECTED/NEAR-MISS VIX- and
   volatility-based timing signals (families 003/016/025/031/035/039/040
   and now 041) -- and, notably, is a more decisively negative NEAR-MISS
   than most of that set on the sec 4.3 robustness checks specifically,
   despite genuinely passing sec 4.1 and being mechanistically distinct
   from every prior VIX-based family per the distinction-verification
   check above.
