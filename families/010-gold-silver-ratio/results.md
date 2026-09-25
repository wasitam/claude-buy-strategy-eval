# Family 010 results: Gold/silver ratio rotation

**Verdict: NEAR-MISS.** The primary configuration passes sec 4.1 (beats
fixed-weight 2-asset DCA on wealth AND Sharpe, at both fee levels) more
decisively than any prior family in this loop — every one of its 27 grid
configurations does too — and clears sec 4.4's grid-robustness bar and most
of sec 4.3's robustness battery. But its Deflated Sharpe Ratio is
essentially zero (sec 4.2 fails badly), and one leg of the placebo test
(wealth) falls short of the 95th-percentile bar, so it is **not** a
finalist. Holdout was **not** opened (reserved for finalists only, per
task instruction step 7).

## 2-asset assessment-scoping decision (recap; full reasoning in prereg.md)

This family is a genuine rotation strictly between 2 of the 5 core assets
(gold, silver) — the ratio has no meaning for the other 3. It was assessed
as a **2-asset portfolio family**: $1,000/week combined deposit ($500
gold-equivalent + $500 silver-equivalent), benchmarked against fixed-weight
2-asset DCA ($500/week into each metal, never rebalanced), under sec 4.1's
"Portfolio" line adapted to 2 assets. DSR/N_eff (sec 4.2) is computed on
this family's own excess-return series (strategy vs. its own 2-asset DCA
benchmark), not the standard 5-asset pooled series, since this family is
not part of the standard 5-asset pool — the same documented deviation
family 008 used, but here it is a **scored, decisive** check (not purely
diagnostic), because this mechanism has a real, scoreable pass path as a
2-asset portfolio, unlike family 008's structurally single-asset CAPE
mechanism. See prereg.md for the full reasoning, including why the sec 5.3
"unseen 5-asset portfolio" holdout leg would need to be waived (moot here,
since this family did not reach the holdout step).

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`, bypasses the ratio/percentile signal entirely, buys $500 gold + $500 silver every week) reproduces fixed-weight 2-asset DCA exactly (bit-for-bit on units and cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| No-lookahead: perturbing all data after day t leaves every order on/before t unchanged (primary config, standard interior spot-check) | PASS |
| No-lookahead, targeted at the rolling-percentile ratio construction, right after the signal first becomes active (`MIN_PERIODS=504` days in) | PASS |
| Point-in-time macro data | PASS (vacuous — price-only signal, no ALFRED-vintage series) |

**Judgment call found during implementation, documented in prereg.md:**
`max_tilt=0` (a real grid value, signal enabled) is **not** equivalent to
the DCA benchmark, because it still rebalances toward the always-50/50
target every week — selling the relatively appreciated metal, buying the
cheap one — a constant-mix strategy, not DCA's never-rebalanced
accumulate-only path. Only `enabled=False` (which bypasses the
weight-based rebalancing logic entirely) is the true degenerate case, and
that check passes as shown above. This was caught by an initial
implementation check that assumed the two were equivalent; the check was
corrected before any grid results were generated, so no results were
affected.

## Primary configuration: `ratio_window_years=20, band=20, max_tilt=0.7`

(20-year trailing percentile window — effectively close to an expanding
window over most of gold/silver's ~19.3-year development history; the
same 20/80 dead-zone threshold convention family 008 used for its primary
config; a moderate, not maximal, tilt strength.)

### 2-asset portfolio result (GOLD+SILVER, vs. fixed-weight 2-asset DCA)

At 0.1% fees:

| | Strategy | 2-asset DCA |
|---|---|---|
| Wealth / invested | 2.2615x | 1.9589x |
| Sharpe (weekly NAV returns) | 0.4600 | 0.3947 |

**Beats DCA (both wealth AND Sharpe): YES.**

At 0.25% fees:

| | Strategy | 2-asset DCA |
|---|---|---|
| Wealth / invested | 2.1650x | 1.9560x |
| Sharpe (weekly NAV returns) | 0.4428 | 0.3923 |

**Beats DCA (both wealth AND Sharpe): YES.**

**sec 4.1 (Portfolio line, 2-asset scoping): PASS** — the primary config
beats fixed-weight 2-asset DCA on both final wealth and Sharpe, at both fee
levels. Full numeric detail is in `grid_results.csv` (row
`cfg22_w20_b20_t0.7`).

### Deflated Sharpe Ratio (sec 4.2 — scored, not diagnostic; computed on this family's own 2-asset excess series)

- Raw weekly Sharpe of the primary config's excess-return series (vs. its
  own 2-asset DCA benchmark): **0.02145/week** (annualized ~15.5%) —
  positive, consistent with the primary config's sec 4.1 pass, but the
  excess series has very heavy tails (skew **4.92**, kurtosis **74.9**) —
  a handful of large relative-value payoff weeks dominate the sample, the
  classic overfitting-vulnerable shape DSR is designed to penalize.
- `N` (raw trial count at this assessment, whole-loop pool): **411** (196
  seeded + 188 from families 001-008 + 27 new from this family's grid).
- `N_eff` (average-linkage clustering, distance sqrt(0.5(1-rho)), rho>=0.5
  threshold): **39** clusters (up from family 008's 38 — this family's 27
  grid configs add exactly 1 new distinct cluster; the other 26 correlate
  >=0.5 with each other or with prior clusters, expected given they all
  share the same underlying gold/silver-ratio signal at different
  window/band/tilt settings).
- **DSR (N_eff-based): 7.88e-06** — far below the 0.95 bar.
- DSR (raw-N, conservative reference): 1.31e-07.

**sec 4.2: FAIL.** Despite the strong sec 4.1 result, the DSR calculation
penalizes both the trial count (this is the 411th trial-eligible
configuration this loop has looked at across all families) and the excess
series' extreme kurtosis — a Sharpe ratio built on a small number of very
large weeks is exactly the pattern DSR is built to distrust, regardless of
how good the raw sec 4.1 wealth/Sharpe comparison looks.

### Robustness (sec 4.3 — run, since sec 4.1 passed decisively: 27/27 grid configs beat DCA at both fees)

60 sims for bootstrap/placebo (cost-scoped down from the plan's 500, per
family 002's established precedent — each sim reruns the full 2-asset
portfolio engine). Rolling windows use both 3-year and 5-year windows
(gold/silver's ~19.3-year development history supports both, per the
plan's explicit "3-year and 5-year windows for ... gold, silver..." line —
unlike family 002's BTC-gated portfolio, which only had enough history for
2-year windows).

| Check | Wealth pass rate | Sharpe pass rate | Bar | Result |
|---|---|---|---|---|
| Rolling 3y (205 windows, step 20d) | 67.8% | 78.5% | >60% each | **PASS** (both) |
| Rolling 5y (180 windows, step 20d) | 72.2% | 75.0% | >60% each | **PASS** (both) |
| Block bootstrap, raw (60 sims) | 63.3% | 60.0% | majority (>50%) | **PASS** (both) |
| Block bootstrap, detrended (60 sims) | 60.0% | 63.3% | majority (>50%) | **PASS** (both) |
| Placebo circular-shift (60 sims), wealth | real at 88.3rd pctile | -- | >=95th | **FAIL** |
| Placebo circular-shift (60 sims), Sharpe | -- | real at 95.0th pctile | >=95th | **PASS** (exactly at the bar) |

**sec 4.3: mixed, net FAIL.** Rolling windows and block bootstrap both pass
comfortably on both metrics (this family's strongest robustness showing of
any family so far in this loop). But the placebo test — which asks whether
the *specific timing* of the ratio signal, not just being invested in
gold/silver at all, matters — shows the real wealth result sits at only
the 88.3rd percentile of circularly-shifted placebos (needs >=95th), while
Sharpe just barely clears the bar at exactly the 95.0th percentile. Read
together with the DSR failure and the excess series' heavy right tail
(skew 4.92, kurtosis 74.9), this points toward the same interpretation:
being invested in gold+silver in a way that spends more time away from
50/50 (any of the 27 grid configs) captured most of the wealth outcome,
while the ratio signal's exact timing (what the placebo test isolates)
contributes less than the raw sec 4.1 pass rate would suggest on its own.

### Grid diagnostic (sec 4.4)

**27 of 27 configurations (100%) beat DCA on wealth AND Sharpe at both fee
levels** — comfortably above the 2/3 bar, and the strongest grid pass rate
of any family in this loop to date (family 002's next-best was 50%).
Every combination of `ratio_window_years` (10/15/20), `band` (10/20/30) and
`max_tilt` (0.4/0.7/1.0) passes, which is itself informative: the effect
does not depend sensitively on any one parameter choice within the tested
ranges — see the CSCV result below for the overfitting-risk read on this.

**sec 4.4: PASS.**

CSCV probability of backtest overfitting (full 27-config grid, 8 splits,
70 combinations, 2-asset portfolio weekly returns at 0.1% fee): **PBO =
0.129** — low, consistent with a grid where the effect (or at least
"being tilted away from 50/50 in gold/silver during this ~19-year window")
holds up broadly across resampled splits rather than being carried by one
overfit corner of the grid. This PBO reading and the placebo-test failure
are not contradictory: CSCV asks whether the *best* grid config generalizes
across data splits (it does, broadly, because nearly the whole grid works),
while the placebo test asks whether the *specific signal timing* beats
noise-timed exposure to the same assets (it does not clear the bar on
wealth) — two different, complementary questions, both answered honestly
here.

## Verdict

**NEAR-MISS.** Sec 4.1 passes decisively (27/27 grid configs, both fee
levels) and sec 4.4 passes (100% grid pass rate, low CSCV PBO). Sec 4.3
is mixed: rolling windows and block bootstrap both pass clearly, but the
placebo test's wealth leg falls short of the 95th-percentile bar. Sec 4.2
fails badly (DSR = 7.88e-06 << 0.95), driven by this family's now-heavier
trial count (411 raw, N_eff=39) and by the excess-return series' extreme
kurtosis (74.9) — a small number of very large relative-value weeks
dominate the primary config's edge over DCA, exactly the fragile shape DSR
is designed to catch. Logged as near-miss, not promoted to finalist status.
Holdout was **not** opened.

## Interpretation: why sec 4.1 passed so cleanly but sec 4.2/placebo did not

The gold/silver ratio's development-period behavior (2000-2019) includes
one dominant regime: gold's much stronger secular bull run relative to
silver through the 2000s vs. silver's sharper boom-bust around 2011, plus
silver's higher volatility generally. Any
strategy that tilts away from a flat 50/50 mix toward the currently-cheap
metal captures some of this relative-price swing whichever direction the
signal points, which is consistent with **every** grid config passing sec
4.1 (the effect is not narrowly tuned) but the placebo test not clearing
its bar on wealth (randomly-timed tilts away from 50/50 also capture a lot
of the same swing, since the underlying driver is largely one or two
multi-year relative-price regimes rather than many independent, correctly-
timed rotations). This is a genuinely informative near-miss: it suggests
the *direction* of tilting (gold-cheap vs. silver-cheap) may carry real
information, but the loop's own DSR/placebo battery — exactly the checks
sec 4 exists to run — correctly flags that the sample is not yet large or
varied enough to be confident this is skill rather than one or two
dominant relative-price regimes in a ~19-year window.

## Data reachability

No issues. Gold (`GC=F`) and silver (`SI=F`) daily OHLC and IRX are all
already-cached core-asset series reachable via `src.backtest.v3.data.load_dev()`;
no new data source was needed for this family.
