# Family 050 results: Money-market funding-stress (TED spread) regime sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 (beats DCA
on wealth AND Sharpe on only 2/5 core assets, need >=3/5, at both fee
levels). The grid diagnostic fails just as decisively (only 4/24, 16.7%,
of the configurations reach the majority-of-assets bar, need >=2/3). DSR
is effectively zero. Holdout was **not** opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family across all 5 core assets**
(independently per asset, sec 4.1's standard >=3/5 rule), following the
precedent families 006/007/011/015/019/027/032 set for an asset-agnostic
macro/financial signal. Category: **Regime switch (macro / credit /
sentiment)**.

### Required concrete distinction from family 011 (verified before any design work)

Fetched both series live from FRED and computed the required real
dev-period divergence example (full method and numbers in prereg.md):

- Full-history correlation of the two series' trailing-10-year monthly
  z-scores: **+0.286** (low).
- **Aug-Sep 2007** (TED spread's own textbook onset episode): TED z-score
  **+2.98 / +3.93** (deep in its own top decile) while the BAA-AAA
  corporate spread's z-score sat at **-0.10 / -0.17** (below its own
  trailing mean) -- the interbank funding market froze months before
  corporate credit spreads reacted.
- **Dec 2001-Feb 2002** (mirror-image divergence): corporate-spread
  z-score **+4.55 / +4.48 / +4.51** (near record highs, dot-com-bust
  credit deterioration) while TED's z-score sat at **-1.51 / -1.76 /
  -1.72** (below trailing mean, ample Fed-eased bank-system liquidity).

Both real episodes confirm the two signals are not proxies for one
another, in opposite directions. Brief distinctions from family 032 (M2,
a monetary-quantity aggregate, not a spread) and family 019 (OECD CLI, a
composite multi-series real-activity index, not a market-quoted spread)
are also documented in prereg.md.

## Data reachability

`TEDRATE` (legacy TED spread) confirmed live reachable via FRED's
`fredgraph.csv` endpoint (the same `fetch_fred_macro()` helper families
011/019/027/032 already use). Coverage: **1986-01-02 through 2022-01-21**
(8,853 daily rows, discontinued after that date) -- comfortably covers
the entire dev period (through 2019-12-31), so **no substitute
construction was needed**; `TEDRATE` alone was used, per the primary
source named in the queue item. GOLD/SILVER/OIL/BTC's dev histories are
fully inside TED's coverage window; SP500's dev history (from 1927-12-30)
has a pre-1986 warm-up gap defaulting to "calm," the same limitation
families 011/019/032 already flagged for their own macro series.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`, bypasses the regime/signal computation entirely, buys 100% of cash every week-end day) reproduces plain DCA exactly (bit-for-bit) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (principled ceiling bound, not flat tolerance -- cash never goes negative) | PASS |
| No-lookahead: perturbing all data after day t leaves every order on/before t unchanged (t=6000) | PASS |
| No-lookahead, second spot-check deep into the sample (t=20000) | PASS |
| Point-in-time macro: shortening the documented 2-day publication lag to 0 days must change SOME historical regime readings, proving the lag isn't a no-op | PASS -- 1.18% of trading days' regime reading differs between the documented 2-day lag and a 0-day lag, on SP500 |

**Judgment call documented in prereg.md before implementation** (families
010/011/019/032's degenerate-config-trap precedent): a grid config with
`stress_tilt_fraction=0` and `enabled=True` is **not** the degenerate DCA
case, because the regime/percentile/persistence computation still runs.
Only `enabled=False` (which bypasses that computation entirely) is the
true degenerate case, and that is what the implementation check above
verifies.

## Pre-grid sanity checks (all passed)

**Non-degeneracy:** the primary configuration's `stressed` flag fires
non-trivially on every core asset -- SP500 4.99%, GOLD 12.33%, SILVER
12.33%, BTC 9.78%, OIL 12.31% of dev days (all comfortably inside the
(2%, 98%) sanity band; SP500's lower rate reflects its long pre-1986
warm-up era defaulting to "calm").

**Known-episode check (strictly within dev dates):** the primary
configuration's regime reading during Aug 2007-Mar 2008 (the TED
spread's own textbook onset episode, the source literature's own
reference episode) reads **stressed 95.1%** of the window (max TED
2.420, vs 0.610 at window start) -- confirming the signal construction
correctly identifies the well-known TED-spread onset before any grid
result was trusted.

## Primary configuration: `lookback_years=10, stress_pctile=80, stress_tilt_fraction=0.0, persistence_days=1` (`max_lump_multiple=6` fixed)

### Per-asset result (vs. plain DCA), at 0.1% fees

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.2838x | 85.2772x | 0.15310 | 0.15310 | YES (razor-thin on both) |
| GOLD | 2.2163x | 2.2312x | 0.5084 | 0.5049 | NO (loses wealth) |
| SILVER | 1.6830x | 1.6867x | 0.3196 | 0.3197 | NO (loses both, razor-thin) |
| BTC | 9.8633x | 9.8557x | 1.0675 | 1.0673 | YES |
| OIL | 1.1874x | 1.1799x | 0.2242 | 0.2278 | NO (loses Sharpe) |

**Beats DCA count (wealth AND Sharpe): 2/5 at 0.1% fees, 2/5 at 0.25% fees**
(SP500 and BTC; every margin -- wins and losses alike -- is small).

**sec 4.1: FAIL** (need >=3/5 at both fee levels; got 2/5 at both).

### Why the primary configuration falls just short

The 10-year-lookback, 80th-percentile primary configuration bites on a
small, plausible fraction of days (5-12%), and the required known-episode
check confirms it correctly flags the 2007-08 TED onset. But at
`persistence_days=1` (no whipsaw filter) and `stress_tilt_fraction=0.0`
(full banking), the rule also flags a number of smaller, less
economically meaningful TED upticks throughout the sample (1998 LTCM,
2000-01, and various minor prints) whose subsequent price action does not
reliably favor delayed deployment as cleanly as the 2007-09 episode does
-- the net effect nets out to a near-wash on 3 of 5 assets (SP500, SILVER
razor-thin either way) and a genuine loss on GOLD and OIL, where the
banked cash from smaller TED upticks is redeployed at prices that are not,
on average, more favorable than steady DCA would have achieved. Unlike
family 011's corporate-spread rule (which failed uniformly and decisively
on every asset, driven by spreads that stay elevated for years after an
acute shock), this family's near-miss pattern is a genuinely close,
mixed result -- consistent with the mechanism's own faster-mean-reverting
character, it just isn't fast or reliable enough at this exact parameter
choice to clear the >=3/5 combined bar.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled 5-asset excess-return
  series: **-0.01344/week** (annualized ~-9.69%) -- negative, consistent
  with the primary config's narrow sec 4.1 failure.
- `N` (raw trial count, whole-loop pool): **1,515** (196 seeded + 1,295
  from families 001-049 + 24 new from this family's grid).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **134**
  clusters (up from family 049's 134 -- this family's 24 grid configs did
  not add any new distinct cluster; consistent with the primary's small,
  narrow-margin excess-return series clustering with existing "banking/
  timing, small negative edge" trial clusters already in the pool).
- **DSR (N_eff-based): 3.82e-27** -- essentially zero.
- DSR (raw-N, conservative reference): 1.32e-26.

**sec 4.2: FAIL**, overwhelmingly -- expected given the negative raw
Sharpe alone; this would fail regardless of trial count. Skew (-9.93) and
kurtosis (434.2) are extreme, reflecting the small number of large
historical TED-stress episodes dominating the pooled excess-return
distribution's tails.

### Grid diagnostic (sec 4.4)

**4 of 24 configurations (16.7%) reach the majority-of-assets bar** (>=3/5
core assets beating DCA on both wealth and Sharpe at 0.1% fees) -- cfg04
through cfg07, the entire `lookback_years=5, stress_pctile=80` block
(both `stress_tilt_fraction` and both `persistence_days` values), each
reaching 3/5 (SP500, BTC, and one of GOLD/SILVER/OIL depending on the
config). The grid is genuinely informative, not pure noise: the
`stress_pctile=90` block (cfg08-11) fails almost completely (0-1/5), and
the `lookback_years=10, stress_pctile=80` block (cfg16-19, including the
primary) sits in between at 2/5 -- the shorter 5-year lookback at the
80th percentile is directionally the strongest corner of the grid, but no
config reaches the required 16/24 (2/3) majority-of-configs bar, and per
sec 4.4's own rule the grid is diagnostic only -- this cannot promote a
different configuration to primary status.

**sec 4.4: FAIL** (4/24 = 16.7%, need >=66.7%).

CSCV probability of backtest overfitting (24-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.186** --
notably lower (better) than most REJECTED families in this loop, consistent
with the grid being genuinely differentiated by `stress_pctile` (a real,
monotonic signal in the threshold) rather than dominated by noise -- a
secondary diagnostic only; it does not change the decisive 2/5 sec 4.1
failure or the 16.7% sec 4.4 failure.

### Robustness (sec 4.3)

**Not run.** Per established precedent (sec 4.1 already fails decisively;
only attempted when sec 4.1 passes), the rolling-window / block-bootstrap
/ placebo battery was skipped.

## Verdict

**REJECTED.** Sec 4.1 fails at 2/5 core assets (need >=3/5) at both fee
levels -- a genuinely close, mixed result (SP500 and BTC beat DCA by
razor-thin margins; SILVER is a near-tie loss; GOLD and OIL lose more
clearly on one metric each), not a uniform failure like family 011's.
Sec 4.4's grid diagnostic shows the mechanism is directionally sensitive
to the threshold (the 5-year/80th-percentile corner is meaningfully
stronger than the 10-year primary, and the 90th-percentile corner is
uniformly weak), but no grid corner reaches the required 2/3
majority-of-configs bar, so per sec 4.4 the primary's own honest,
pre-registered parameter choice is what stands. DSR is effectively zero,
driven by a small negative raw excess-return Sharpe with extreme tail
risk (a handful of large historical TED-stress episodes dominate the
pooled distribution). Holdout was **not** opened.

## Interpretation

The prereg's central hypothesis -- that the TED spread's faster mean-
reversion (vs. family 011's slower corporate-credit-spread mean-reversion)
would let this family's "bank during stress, deploy once it resolves"
mechanic clear the sec 4.1 bar where family 011 failed uniformly -- is
**partially supported but not confirmed**: this family does come much
closer to passing (2/5, mixed and narrow-margin) than family 011 did
(0/5, uniform and decisive), and the grid shows a real, monotonic
sensitivity to the stress threshold rather than family 011's flat 0/24
failure across the whole grid. But "closer" is not "passing," and the
persistence-days=1, stress_tilt_fraction=0.0 primary configuration --
chosen for literature-faithfulness, not for backtest performance -- still
falls one asset short of the majority bar. This is a genuinely
informative negative result: it suggests interbank-funding-stress timing
as specified here (a percentile-threshold banking rule keyed to TEDRATE
alone) sits meaningfully closer to a real, exploitable signal than the
corporate-credit-spread version, without actually clearing this loop's
bar -- a different outcome, and a different lesson, than family 011's.

## Grid-counted marker note

Following families 010/011/019/032's documented degenerate-config trap:
`enabled=False` is the **only** true degenerate case here too. A grid
config with `stress_tilt_fraction=0` and `enabled=True` is **not**
equivalent to DCA even during a period with zero stressed weeks in the
lookback window, because the regime/percentile/persistence computation
still runs. This was flagged in prereg.md before implementation, and only
`enabled=False` was checked against the DCA baseline (implementation
checks table above).
