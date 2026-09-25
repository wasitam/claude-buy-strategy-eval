# Family 011 results: Credit-stress risk-off filter

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively
— it beats plain DCA on neither wealth nor Sharpe on **any** of the 5 core
assets, at either fee level. The grid diagnostic fails just as decisively
(0% of the 24 configurations reach the majority-of-assets bar). DSR is
effectively zero. Holdout was **not** opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family across all 5 core assets**
(independently per asset, sec 4.1's standard >=3/5 rule), following the
precedent families 006/007 set for an asset-agnostic macro/calendar
signal. This is explicitly **not** a re-test of v2.1 Strategy D (sec 7.2
closed list): Strategy D's R1–R4/Combo/Control signals are built entirely
from interest-rate data (Fed funds target, 2y yield, curve slope, TIPS
real yields, the FOMC dot plot); this family's signal (BAA−AAA credit
spread, or the Chicago Fed NFCI) is built from corporate-bond and broad
financial-conditions data that never appears in `src/backtest/v2/regimes.py`
— a different data source and a different economic question ("how
stressed are credit/financial markets" vs. "is monetary policy tight or
loose"), with historically frequent divergence between the two (e.g. early
2007–08, when the Fed was already cutting while credit spreads were
actively blowing out).

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`, bypasses the regime/signal computation entirely, buys 100% of cash every week-end) reproduces plain DCA exactly (bit-for-bit on units and cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| No-lookahead: perturbing all data after day t leaves every order on/before t unchanged (interior spot-check, t=6000) | PASS |
| No-lookahead, second spot-check deep into the sample (t=20000, well past the 1971+ NFCI-availability period) | PASS |
| Point-in-time macro data: the documented publication lag (45 calendar days for BAA/AAA, 8 for NFCI) must produce **at least one** historical date where the regime reading differs from a 0-day-lag (no-lag) version, proving the lag isn't a no-op | PASS -- 6.80% of trading days' regime reading differs between the documented lag and a 0-day lag, on the primary config's signal/window/threshold |

**Judgment call documented in prereg.md before implementation** (following
family 010's degenerate-config-trap precedent): a grid config with
`stress_tilt_fraction=0` and `enabled=True` is **not** the degenerate DCA
case, because the regime/percentile computation still runs and can mark
weeks stressed. Only `enabled=False` (which bypasses that computation
entirely) is the true degenerate case, and that is what the implementation
check above verifies.

## Primary configuration: `signal_choice=credit_spread, lookback_years=10, stress_pctile=80, stress_tilt_fraction=0.0` (`max_lump_multiple=6` fixed)

### Per-asset result (vs. plain DCA), at 0.1% fees

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 83.035x | 85.277x | 0.15007 | 0.15310 | NO |
| GOLD | 2.094x | 2.231x | 0.4621 | 0.5049 | NO |
| SILVER | 1.533x | 1.687x | 0.2748 | 0.3197 | NO |
| BTC | 9.704x | 9.856x | 1.0623 | 1.0673 | NO |
| OIL | 1.101x | 1.180x | 0.1754 | 0.2278 | NO |

**Beats DCA count (wealth AND Sharpe): 0/5 at 0.1% fees, 0/5 at 0.25% fees.**
Every asset comes in slightly *behind* DCA on both metrics, not ahead on
some and behind on others — a uniform, not asset-specific, shortfall.

**sec 4.1: FAIL** (need >=3/5 at both fee levels; got 0/5 at both).

### Why the primary configuration underperforms

At `lookback_years=10, stress_pctile=80`, the credit-spread signal spends
roughly the top quintile of its trailing-10-year window "stressed" by
construction, and `stress_tilt_fraction=0.0` fully banks deposits during
those weeks. Two effects compound against this configuration specifically:
(1) the BAA−AAA spread is **persistently elevated for long stretches**
around and after major credit events (2000-03, 2007-11, 2015-16, 2020-21)
— once a stress episode pushes the trailing-window percentile above 80,
the spread's slow mean-reversion (spreads stay elevated for quarters to
years after the acute shock, well past the point risk assets have already
substantially recovered) means deposits get banked for far longer than the
"buy after the acute phase resolves" mechanism intends, missing much of
the recovery rally the mechanism was designed to buy into; (2) unlike
families 006/007/010, this signal has essentially no seasonal or
short-cycle regularity to average out — a handful of multi-year stress
regimes dominate the entire banking/deployment pattern, so a single
mistimed regime (banking through 2009-11's strong equity recovery while
credit spreads were still normalizing from their 2008-09 peak, for
example) can drag down the whole-sample result on its own.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled 5-asset excess-return
  series: **-0.0335/week** (annualized ~-24.1%) — negative, consistent
  with the primary config's sec 4.1 failure on every asset.
- `N` (raw trial count, whole-loop pool): **435** (196 seeded + 215 from
  families 001-010 + 24 new from this family's grid).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **40**
  clusters (up from family 010's 39 — this family's 24 grid configs add
  exactly 1 new distinct cluster).
- **DSR (N_eff-based): 5.03e-39** — essentially zero.
- DSR (raw-N, conservative reference): 1.77e-48.

**sec 4.2: FAIL**, overwhelmingly — expected given the negative raw Sharpe
alone; this would fail regardless of trial count.

### Grid diagnostic (sec 4.4)

**0 of 24 configurations (0.0%) reach the majority-of-assets bar** (>=3/5
core assets beating DCA on both wealth and Sharpe at 0.1% fees) — the
worst grid result of any family in this loop to date, tied with families
006/007's 0/24. The best individual configs (`nfci, lookback_years=5,
stress_pctile=70`: 4/5 assets beat on Sharpe alone, but only 1/5 on wealth,
so still short of the combined bar) hint that a shorter-lookback,
lower-threshold NFCI variant might be directionally closer, but no grid
config reaches the 3/5-combined bar required, and per sec 4.4's own rule
the grid is diagnostic only — this cannot promote a different
configuration to primary status.

**sec 4.4: FAIL.**

CSCV probability of backtest overfitting (24-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.771** — high,
consistent with a grid where whichever configuration looks best on one
data split tends to look mediocre-to-bad on another, i.e. there is no
robust "best corner" of this grid at all, just noise around a
mechanism that does not work as specified.

### Robustness (sec 4.3)

**Not run.** Per the task's explicit instruction and the precedent set by
families 006/007/008 (sec 4.1 already decisive as a fail; only attempted
if sec 4.1 passes), the rolling-window / block-bootstrap / placebo battery
was skipped. A robustness script
(`scripts/v3/robustness_011_credit_stress_filter.py`) was written and is
available for reuse, but was not executed, since sec 4.1's 0/5 result
already settles the verdict.

## Verdict

**REJECTED.** Sec 4.1 fails on every one of the 5 core assets at both fee
levels (0/5, the worst possible sec 4.1 outcome, tied with no prior family
in this loop — families 006/007/008 each passed on at least 1 asset).
Sec 4.4's grid diagnostic fails just as completely (0/24 configs reach the
majority bar), and CSCV PBO is the highest (worst) of any family so far
(0.771), meaning even the grid's best-looking corners do not generalize
across resampled splits. DSR is essentially zero, driven by a genuinely
negative raw excess-return Sharpe, not merely a high trial-count penalty.
Holdout was **not** opened.

## Interpretation: why this family fails more completely than families 006-010

Every prior "banking/timing" family in this loop (003, 005, 006, 007, 010)
at minimum passed sec 4.1 on 1+ assets, and several (003's precedent
notwithstanding) showed at least directionally-positive raw effects even
where DSR ultimately failed. This family fails uniformly across all 5
assets and both fee levels, which points to a specific mechanism problem
rather than only a "too few independently-timed episodes, DSR/placebo
catches it" story (family 010's pattern): the credit-spread/NFCI signal's
mean-reversion is simply too slow relative to how quickly risk assets
recover from the acute phase of a credit-stress episode, so the "bank
during stress, deploy in the calm that follows" mechanic ends up banking
through a large share of the recovery it was designed to buy into, on
every asset tested — a structural timing mismatch between the credit
cycle's mean-reversion speed and the price recovery's, not a sampling or
overfitting artifact. This is a genuinely informative negative result for
the credit-stress-filter idea as specified here (a percentile-threshold,
banking-based deposit-timing rule) — it does not rule out other ways of
using credit-spread information (e.g. a continuous sizing multiplier
instead of a hard banking threshold, or a faster-mean-reverting spread
construction), but those would be materially different mechanisms
requiring their own pre-registration, not a retune of this family.

## Data reachability

No issues. FRED's `BAA`, `AAA` and `NFCI` series were all directly
reachable via `fred.stlouisfed.org/graph/fredgraph.csv` (confirmed at the
start of this iteration) — no substitute source was needed, unlike family
008's CAPE data. Each asset's own OHLC and IRX are already-cached core-
asset series reachable via `src.backtest.v3.data.load_dev()`.
