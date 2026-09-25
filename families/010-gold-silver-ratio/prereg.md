# Family 010: Gold/silver ratio rotation

**Status:** pre-registered. Committed before any backtest is run on development
data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Relative-value commodity literature on the gold/silver price ratio: the
ratio (ounces of silver needed to buy one ounce of gold) has a long
documented history (used by practitioners and precious-metals researchers
going back decades) of mean-reverting around a slowly drifting long-run
range, with tactical "ratio trading" (swap into the cheap metal, swap back
when the ratio normalizes) a standard relative-value technique in that
literature. Seed queue item #10 (research-loop-plan-v3.md sec 7.3).

## Mechanism ("why would this work, and who is on the other side?")

Gold and silver are both monetary/precious metals with correlated but not
identical drivers (silver has a larger industrial-demand component; gold has
a larger monetary/reserve-asset component), so their relative price can
drift away from its historical range for cyclical reasons (e.g. an
industrial-demand shock to silver, or a flight-to-gold episode) without
either metal's *absolute* valuation case changing much. The ratio's
historical range has provided a weak anchor: when it's unusually high
(silver historically cheap vs. gold), forward silver returns relative to
gold have tended to be better than average, and vice versa when the ratio
is unusually low. The "other side" of this trade is capital that treats
gold and silver as interchangeable "precious metals exposure" and buys
whichever is more convenient/liquid at the time regardless of the relative
price (ETF flows, jewelry/industrial fabrication demand that responds to
absolute price and availability, not relative value), plus investors who
simply buy-and-hold a fixed metals allocation without ever rebalancing
between the two. The cost paid for the mechanism, if real, is concentration
risk (the strategy is never diversified 50/50, it's persistently tilted)
and the risk that "mean reversion" in a two-century price ratio is really a
slow regime drift (e.g. structurally rising industrial demand for silver,
or structurally rising monetary demand for gold) that a trailing percentile
signal will misread as "cheap" or "rich" right before the regime changes
further in the same direction — the classic relative-value risk of betting
against a trend that turns out not to be mean-reverting after all.

## Category

**Cross-asset rotation / relative strength** (research-loop-plan-v3.md sec
4.5).

## Relationship to closed families (sec 7.2) and to family 002

None of the v1/v2/v2.1 closed families (sec 7.2) used a two-asset relative
price ratio as a rotation signal at all — the closed rebalancing families
(C1/C2/C3) used fixed target weights, not a signal-driven tilt. Family 002
(dual momentum, this loop, NEAR-MISS) is superficially similar in category
("Cross-asset rotation / relative strength") but uses **trailing absolute
and relative total-return momentum** across all 5 core assets plus a cash
leg, and can exit entirely to T-bills. This family uses a **completely
different signal** (a valuation-style mean-reversion percentile rank of one
asset's price *relative to* a second, specific asset — not trailing return
momentum, and not compared against a risk-free hurdle), is scoped to
exactly 2 assets by construction (gold and silver — the ratio has no
meaning for SP500/BTC/oil), and is **never in cash** (it always holds 100%
of deposited capital across the two metals, tilted by the signal, unlike
dual momentum's cash-parking absolute-momentum gate). This is a materially
different mechanism and is not a re-test of family 002 or of any sec 7.2
closed family.

## The 2-asset assessment-scoping decision (a real interpretive gap, resolved here)

Sec 4.1 gives two lines: "Single-asset: beats DCA on >=3 of 5 core assets"
and "Portfolio: beats fixed-weight 5-asset DCA." Neither line describes a
rotation strictly between a **subset** of 2 of the 5 core assets. This
family's mechanism (like family 002's) *requires* comparing two assets
against each other — the gold/silver ratio is not decomposable into two
independent single-asset "buy more / buy less" decisions without
destroying the relative-value signal itself (the ratio's percentile rank is
only meaningful as a joint quantity). But unlike family 002, this
mechanism structurally cannot be extended to a 5-asset portfolio: there is
no economically meaningful "SP500/oil ratio" or "BTC/gold ratio" under the
same mean-reversion rationale (those pairs don't share the
monetary/precious-metals economic linkage the mechanism's rationale relies
on), so this is a genuine 2-of-5 subset case, not a disguised 5-asset
portfolio and not a disguised single-asset test either.

**Decision: assess this family as a 2-asset portfolio family**, using the
task instruction's suggested path:
- **Deposits:** $1,000/week combined ($500 gold-equivalent + $500
  silver-equivalent), consistent with the plan's $500/asset funding
  convention (sec 2, sec 3.2) applied to this family's 2-asset universe
  rather than the 5-asset universe.
- **Benchmark:** fixed-weight 2-asset DCA — $500/week into gold and $500/week
  into silver, every week, never rebalanced. This is the natural
  restriction of the plan's "fixed-weight 5-asset DCA" concept (sec 3.2) to
  the 2 assets this mechanism is actually about, exactly as family 002's
  5-asset fixed-weight DCA benchmark is the natural analogue at 5 assets.
- **Win rule:** sec 4.1's "Portfolio" line, substituting the 2-asset
  benchmark above for the 5-asset one — beat fixed-weight 2-asset DCA on
  final wealth AND Sharpe, at both 0.1% and 0.25% fees.
- **DSR (sec 4.2):** computed on this family's own excess-return series
  (strategy weekly NAV return minus the 2-asset fixed-weight DCA's weekly
  NAV return), not the standard 5-asset pooled excess series, since this
  family is not part of the standard 5-asset pool — the same documented
  deviation family 008 used for its SP500-only diagnostic, flagged
  explicitly again here in results.md. Unlike family 008, this DSR/N_eff
  computation is NOT purely diagnostic — it is a scored, decisive check,
  because (unlike CAPE valuation) this family's mechanism structurally
  can be a finalist under the 2-asset-portfolio reading above.
- **Holdout scoping (if this family becomes a finalist):** the plan's sec
  5.3 "Portfolio" holdout line requires both a core-asset holdout portfolio
  (2020+) and an **unseen 5-asset portfolio** (^NDX, ^N225, HG=F, PL=F,
  ETH-USD) — but there is no comparable "unseen ratio pair" analogous to
  gold/silver among the 5 unseen assets (no second precious/industrial
  metal pair exists in the unseen set — platinum (`PL=F`) is a precious
  metal but copper (`HG=F`) is industrial-only, and the two don't share
  gold/silver's specific monetary-vs-industrial mechanism rationale from
  the "Mechanism" section above closely enough to treat as a like-for-like
  test of *this* mechanism). **If this family reaches the holdout step**,
  it will be scoped to **core-asset gold/silver data only, 2020-01-01
  onward** (the direct analogue of sec 5.3's core-asset holdout leg), with
  the unseen-asset leg explicitly waived and documented as not applicable
  for the same structural reason as the 2-asset assessment-scoping decision
  above — this will be spelled out again in `prereg_final.md` if and when
  that point is reached, not decided retroactively after seeing a holdout
  result.

This family is **not** assessed under sec 4.1's single-asset ">=3/5 core
assets" line: unlike family 008/CAPE (a single-asset mechanism scored on
its one eligible asset as an explicitly non-passing diagnostic), this
mechanism is a genuine 2-asset rotation with a real portfolio-style
benchmark available (fixed-weight 2-asset DCA), so — unlike family 008 —
it has a real, scoreable pass path and is not capped at "diagnostic only."

## Exact rules

**Shared calendar:** gold's (`GC=F`) own daily trading-day index (COMEX
futures trade on essentially the same NYSE-adjacent calendar as SP500, and
gold has the earlier data-start of the two metals by 2 days — see the data
check below), clipped to start once both gold and silver have data.
Silver's OHLC is forward-filled onto this shared calendar (handles small
exchange-specific holiday mismatches), the same alignment approach as
family 002's prereg.md.

**Signal, computed at each shared-calendar day `t`'s close, using only data
through `t` (no lookahead):**
- `ratio_t = close_gold,t / close_silver,t` (ounces of silver per ounce of
  gold).
- `pctile_t` = the **trailing percentile rank of `ratio_t` within the
  trailing `ratio_window_years * 252`-trading-day window ending at `t`**
  (inclusive of `t`, i.e. `ratio_t`'s own rank among the last N
  observations including itself — strictly historical, no future data).
  Implemented via a rolling-window percentile rank (pandas
  `rolling(window).rank(pct=True)`), which by construction only ever looks
  backward from each row. Before `min_periods` (fixed at 504 trading days,
  ~2 years) observations are available, the signal is inactive and the
  target weight is the neutral 50/50 split (matches family 008's
  precedent of treating an insufficiently-seasoned signal as neutral/
  non-qualifying rather than extrapolating).
- **Dead zone:** if `low_pctile <= pctile_t <= high_pctile` (where
  `low_pctile = band` and `high_pctile = 100 - band`), the target weight is
  neutral 50/50 — no tilt.
- **Above the dead zone** (`pctile_t > high_pctile`, i.e. the ratio is
  historically high, silver is cheap relative to gold): tilt toward
  silver. Target silver weight rises linearly from 0.5 (at
  `pctile_t = high_pctile`) to `0.5 + max_tilt / 2` (at `pctile_t = 100`);
  gold weight is `1 - silver weight`.
- **Below the dead zone** (`pctile_t < low_pctile`, ratio historically low,
  gold is cheap relative to silver): tilt toward gold, symmetric
  construction — gold weight rises linearly from 0.5 (at
  `pctile_t = low_pctile`) to `0.5 + max_tilt / 2` (at `pctile_t = 0`).
- `max_tilt = 0` collapses the signal to always-50/50 regardless of
  `pctile_t` — the degenerate/benchmark-equivalence case.

**Rebalance cadence:** the target weight vector is recomputed and the
2-asset portfolio is rebalanced toward it **weekly**, on the shared
calendar's last trading day of each ISO week — the same day the pooled
$1,000 deposit is credited. This matches family 002's precedent exactly
(weekly cadence, deposit day = rebalance day), keeps the grid's backtest
cost bounded, and is within the "at most daily" complexity ceiling (sec
3.4).

**Orders:** on a rebalance day, for each of gold/silver the target dollar
value is `target_weight * total_portfolio_value` (cash + gold value +
silver value at that day's close, including that day's $1,000 deposit).
The order is `target_dollar - current_dollar_value` (positive = buy,
negative = sell). All orders fill at the **next** trading day's open —
sells first (both assets), then buys, buys capped by available pooled cash
(engine sec 3.2, `portfolio_engine.py`). Unlike family 002, there is **no
cash-parking leg** — the target weights always sum to exactly 1 (always
fully invested across gold+silver; the signal only ever decides the split
between them, never whether to hold cash), which is a direct consequence
of this being a relative-value rotation between two assets rather than a
trend-following in/out-of-market signal.

**Degenerate case (`enabled=False`, implementation check only, not a grid
arm):** bypasses the ratio/percentile computation and the weight-based
rebalancing logic entirely and, each week, submits a buy order for exactly
$500 into gold and $500 into silver and nothing else (no selling, no
reallocation of existing holdings) — this reproduces fixed-weight 2-asset
DCA exactly, bit-for-bit, the same pattern families 001/002 used for their
degenerate checks. Note `max_tilt=0` (a real grid value, `enabled=True`) is
**not** equivalent to this degenerate case: it still rebalances toward the
always-50/50 target weight every week, which sells the relatively
appreciated metal and buys the relatively cheap one to hold the mix at
50/50 — a constant-mix strategy, not DCA's never-rebalanced
accumulate-only path. This distinction was confirmed empirically during
implementation and is documented here explicitly (see results.md).

## Data inputs

Daily OHLC close of gold (`GC=F`) and silver (`SI=F`) only, and the daily
risk-free rate (IRX, for the pooled cash account's interest accrual between
rebalances), all sourced via `src.backtest.v3.data.load_dev()` only. No
macro or alternative data — the ratio is computed purely from the two
assets' own prices.

## Parameters (3 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `ratio_window_years` | 10, 15, 20 | 20 |
| `band` (dead-zone half-width; `low_pctile=band`, `high_pctile=100-band`) | 10, 20, 30 | 20 |
| `max_tilt` (max deviation from 50/50 at the most extreme percentile) | 0.4, 0.7, 1.0 | 0.7 |

(Rebalance cadence and `min_periods=504` days are fixed, not tunable, per
the judgment calls above — 2 tunable-but-fixed items, keeping the family at
3 of the allowed 5 tunable parameters.)

**Grid:** 3 x 3 x 3 = **27 configurations** (<=36, per sec 3.4).

**Primary configuration:** `ratio_window_years=20, band=20, max_tilt=0.7`
— the longest available trailing window given gold/silver's ~19.3-year
development history (effectively close to an expanding window over most of
the sample), a literature-standard quintile-style dead-zone split (band=20
=> dead zone is the middle 60 percentile points, tilt zones are the top/
bottom quintiles — the same 20/80 threshold convention family 008 used for
its primary config), and a moderate (not maximal) tilt strength, chosen
before any backtest is run on development data.

## Expected sign of the effect

Positive: the strategy should beat fixed-weight 2-asset DCA on both final
wealth and Sharpe, because tilting new capital toward the historically
cheaper metal (by the ratio) should, if the mean-reversion premise in the
literature holds, capture some of that metal's subsequent relative
outperformance without ever fully exiting either asset (so the strategy
retains both metals' long-run secular returns, unlike a trend-exit
strategy that can sit out of the market entirely).

## Implementation checks to run (sec 3.2, before any results count)

1. Degenerate config (`max_tilt=0`, or equivalently `enabled=False` in the
   strategy module) reproduces fixed-weight 2-asset DCA exactly (bit-for-bit
   on gold/silver units and pooled cash).
2. Cash and positions (both gold and silver) never negative, for both the
   DCA baseline and the primary config.
3. No-lookahead test: perturbing all gold/silver OHLC data strictly after
   day `t` must leave every order on/before day `t` unchanged — this is
   especially important for this family since the rolling-percentile
   signal (`rolling(window).rank(pct=True)`) must be strictly point-in-time
   (each day's percentile rank must depend only on that day's and prior
   days' ratio values, never a future one).
4. Point-in-time macro data: not applicable — this family uses only price
   data (gold/silver OHLC) and IRX, no ALFRED-vintage macro series.
