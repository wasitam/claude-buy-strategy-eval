# Family 003: Volatility-managed sizing

**Status:** pre-registered. Committed before any backtest is run on development
data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Moreira, A. and Muir, T. (2017), *Volatility-Managed Portfolios*, Journal of
Finance; Harvey, C., Hoyle, E., Korgaonkar, R., Rattray, S., Sargaison, M.
and van Hemert, O. (2018), *The Impact of Volatility Targeting*, Journal of
Portfolio Management. The core empirical finding: scaling exposure to an
asset (or factor) inversely to its recent realized variance — buying/holding
more when recent volatility is low relative to its own longer-run level,
less when recent volatility is high — improves realized Sharpe ratio,
because variance is highly persistent (clusters) while expected returns are
far less predictable from the same signal, so scaling by 1/variance mostly
avoids the worst-variance regimes rather than timing returns per se. Seed
queue item #3 (research-loop-plan-v3.md sec 7.3).

## Mechanism ("why would this work, and who is on the other side?")

Realized variance is strongly autocorrelated (volatility clustering — a
well-documented stylized fact since Engle's ARCH/GARCH literature), so
today's realized vol is informative about tomorrow's, even though today's
return tells us almost nothing about tomorrow's return. A fixed-dollar DCA
buyer commits the same $500 every week regardless of the variance regime,
so a disproportionate share of their invested-dollar-weighted exposure sits
in the choppiest, highest-variance stretches (which is also where volatility
risk premia and crash risk concentrate — e.g. 2008, 2020, BTC's periodic
50%+ drawdown regimes). Vol-managed sizing instead re-times the SAME total
deposit stream: it under-invests (relative to plain DCA) during high-realized-
-variance weeks, banking the shortfall as interest-earning cash, and
over-invests (again relative to plain DCA, but capped and funded only from
that banked cash — no leverage, no borrowing) during subsequent low-realized-
-variance weeks. Average capital committed over time is unchanged; only the
week-to-week timing of when it gets committed shifts. The "other side" of
this trade is holders who buy a constant dollar amount every period
independent of the variance regime (plain DCA investors, or any
constant-mix rebalancer) — they are, on average, buying a larger fraction of
their eventual position during exactly the periods this strategy is
avoiding. The cost paid is the risk that low realized vol does not predict a
calm next period (a "quiet before the storm" — e.g. a low-vol melt-up that
reverses sharply before the reserve is caught up in re-investing), and that
capping the multiplier means the strategy still cannot avoid variance spikes
it has not yet seen.

## Category

**Volatility targeting** (research-loop-plan-v3.md sec 4.5).

## Why this is not a re-test of a closed family (sec 7.2), and how it differs from SmartDCA specifically

None of the v1/v2/v2.1 closed families scale buy size by the asset's own
**realized volatility**. The closest superficially similar closed family is
v2's SmartDCA (rho x m_max x sweep grid): SmartDCA scales the weekly buy
size by how far the **price** sits below/above a **trailing moving average**
(a trend/valuation-style signal — the input is the *level* of price relative
to its own recent trend, and the mechanism claimed is "buy more when the
asset looks cheap relative to its recent trend"). This family's signal is
instead the **second moment of returns** (realized variance), entirely
independent of the sign or level of price relative to any trend — a asset
whose price is flat and range-bound has LOW realized vol here regardless of
where it sits versus its moving average, and a sharply falling OR sharply
rising asset both register HIGH realized vol and get sized DOWN here, which
SmartDCA's price-level-vs-trend signal cannot express (SmartDCA would size
a sharp rally as "expensive, size down" and a sharp selloff as "cheap, size
up" — opposite of what this family does for a selloff). This is also a
different mechanism category on the plan's own sec 4.5 list (Volatility
targeting vs. Sizing/valuation), and a reviewer checking "is this just
SmartDCA with a different name" can verify by construction: the two signals
are functions of different moments of the same price series (level vs.
variance) and diverge in sign on any sharp-move week (up or down). Also
distinct from family 001 (price-vs-SMA trend exit, a binary in/cash signal
gating deposits, not a continuous size multiplier) and family 002
(cross-asset relative-momentum rotation, not a per-asset sizing rule).

## Exact rules

Computed causally at each trading day `t`'s close, using only data through
`t` (no lookahead):

- **Recent realized vol** `sigma_recent_t`: annualized standard deviation of
  daily log returns over the trailing `vol_lookback_days` trading days
  (`std(diff(log(close)), ddof=1) * sqrt(252)`).
- **Reference (long-run) vol** `sigma_ref_t`: the same annualized realized-vol
  calculation over the trailing `ref_lookback_days` trading days (a longer
  window, the asset's own recent-history baseline — this makes the target
  vol level adaptive per asset rather than a single fixed number that would
  be miscalibrated across assets as different as gold and BTC).
- While fewer than `ref_lookback_days` observations exist (not enough
  history for either window), the multiplier defaults to 1.0 (plain DCA)
  until both windows are computable.
- **Sizing multiplier:** `m_t = clip(sigma_ref_t / sigma_recent_t, min_mult, max_mult)`.
  Note the direction: `sigma_recent_t` LOW relative to `sigma_ref_t` gives
  `m_t > 1` (buy more); `sigma_recent_t` HIGH relative to `sigma_ref_t` gives
  `m_t < 1` (buy less) — this is the inverse-variance-scaling direction the
  source literature specifies (Moreira & Muir's headline result is that
  scaling exposure inversely to variance raises Sharpe; the naive
  "buy-more-when-vol-is-high" direction is explicitly NOT what is tested
  here, and is not part of the grid).
- **Order generation (every trading day):** `target_buy_usd_t = weekly_deposit * m_t`.
  The order submitted is `buy_usd = min(cash, target_buy_usd_t)` (engine's
  existing cash cap — sec 3.2 — already enforces this; no separate logic is
  needed since cash is $0 on every non-deposit day unless a reserve has
  accumulated). No sell orders are ever generated (deposits-only strategy,
  same convention as family 001's primary configuration).
- This produces exactly the reserve mechanism described in "Mechanism"
  above: on a high-`m_t` (low-recent-vol) week with no accumulated reserve,
  the order is capped at that week's own $500 deposit (same as plain DCA);
  reserve only exists to draw down when a preceding low-`m_t` (high-recent-
  vol) week banked cash instead of spending it. No leverage or borrowing is
  ever possible because `buy_usd` is capped by available cash at every step
  (engine sec 3.2, same invariant checked in sec 3.2 implementation check 2).

## Data inputs

Daily OHLC close price of the asset itself only (one of the 5 core assets,
tested independently — single-asset family). No macro or alternative data.
Sourced via `src.backtest.v3.data.load_dev()` only.

## Parameters (4 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `vol_lookback_days` | 20, 40, 60 (~1, ~2, ~3 trading months) | 60 |
| `ref_lookback_days` | 126, 252 (~6, ~12 trading months) | 252 |
| `min_mult` | 0.25, 0.5 | 0.5 |
| `max_mult` | 1.5, 2.0, 3.0 | 2.0 |

## Grid

3 x 2 x 2 x 3 = **36 configurations** (= 36 cap, at the limit).

## Primary configuration

`vol_lookback_days=60, ref_lookback_days=252, min_mult=0.5, max_mult=2.0` —
a ~3-month recent-vol window scaled against the trailing 12-month baseline,
with a moderate 0.5x-2x band (never sizes below half or above double a
plain-DCA week's deposit), consistent with Moreira & Muir's own moderate
scaling bounds and the plan's no-leverage constraint (the upper bound can
only ever be realized when a reserve has already been banked, never through
borrowing).

## Expected sign

Positive, primarily on **Sharpe**: by construction the strategy avoids
committing a disproportionate share of the deposit stream during the
highest-realized-variance weeks (where crash risk and drawdown risk
concentrate) and shifts that capital into calmer, lower-variance weeks,
which the source literature finds raises risk-adjusted return even when raw
average return is roughly unchanged. The effect on **final wealth** is
expected to be smaller and could go either way asset-by-asset — since total
capital committed over time is approximately unchanged (only its timing
shifts), any wealth improvement must come from a timing correlation between
low-recent-vol weeks and subsequently favorable near-term price action
(a real but weaker and less mechanically guaranteed effect than the
Sharpe channel). Both effects should be more pronounced in assets with more
persistent, clustered volatility (equities, BTC) than in assets whose
volatility is more uniform through time.

## Degenerate configuration (implementation check only, not a grid arm)

`enabled=False`: bypasses the vol calculation entirely and forces `m_t = 1.0`
for every day, which reproduces plain DCA exactly, bit-for-bit (same pattern
as family 001's `enabled=False` and family 002's `enabled=False` degenerate
checks). This is distinct from, and in addition to, the `min_mult=max_mult=1`
special case (which also collapses to DCA-equivalent buy amounts but through
the multiplier arithmetic rather than bypassing it, and is not itself part
of the grid).
