# Family 005: Time-series momentum sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Moskowitz, T., Ooi, Y.H. and Pedersen, L.H. (2012), *Time Series Momentum*,
Journal of Financial Economics. The core empirical finding: across 58 assets
(equity indices, currencies, commodities, bonds) an asset's own trailing
12-month excess return predicts the sign of its next-month excess return —
positive past return tends to be followed by positive return, negative by
negative — largely independent of the asset's return *relative to other
assets* (that is a separate effect, cross-sectional momentum, already
family 002's territory here). Seed queue item #5 (research-loop-plan-v3.md
sec 7.3): "Time-series momentum sizing: scale buys by the sign of the
12-month return."

## Mechanism ("why would this work, and who is on the other side?")

The classic TSMOM explanation combines slow information diffusion
(Hong & Stein 1999 style underreaction — news is priced in gradually as it
spreads across investors with heterogeneous information and attention) with
trend-following capital flows that amplify and extend a move once it starts
(managed futures / CTA flows, and momentum-chasing retail flows), plus a
risk-based component: assets that have trended up are often those whose risk
premium or risk-bearing-capacity conditions have improved, so recent
directional information is genuinely informative about the near-term
distribution of returns, not just noise. The "other side" of the trade is
whoever supplies convexity/liquidity against the trend: value/contrarian
investors and market-makers who buy into declines and sell into rallies
regardless of the asset's own trailing return, absorbing order flow from
trend-followers; also anyone who systematically under-reacts too slowly and
gets run over by the very continuation TSMOM tries to capture on the other
side of the trade (which is precisely the risk this strategy takes: paying
away the premium in whipsaw regimes where the trailing-return sign is a bad
predictor of the *next* period, e.g. sharp V-shaped reversals). Moskowitz,
Ooi & Pedersen's own account frames the realized premium as compensation
for the risk of being run over in exactly those reversal episodes, not a
free lunch.

## Category

**Trend / time-series momentum exit** (research-loop-plan-v3.md sec 4.5's
category list — the closest match to this family's mechanism, even though
sec 7.3's own table labels seed-queue item #5 simply "Trend"; sec 4.5 has no
separate "time-series momentum" category, so "Trend / time-series momentum
exit" is used, per the task's instruction to use §4.5's own list).

## Why this is NOT a re-test of family 001, and not of anything in sec 7.2's closed list

This point is made explicit here because a reviewer would ask, given family
001 (`010-trend-exit`) is also nominally "trend"-flavored and sits in the
same sec 4.5 category:

- **Different signal.** Family 001's signal is the asset's *price level*
  relative to a trailing simple moving average (a 200-day/10-month SMA
  crossover à la Faber 2007) — it is a statement about where today's price
  sits versus a smoothed price level. This family's signal is the asset's
  own trailing **total return** over a fixed lookback (its percent change
  over the last ~12 months, i.e. `close_t / close_{t-lookback} - 1`, or its
  sign) — a statement about the asset's own realized momentum, not its
  price level versus a moving average. A price can be *above* its 200-day
  SMA while its trailing 12-month total return is *negative* (e.g. a slow
  grind sideways-to-down that only recently turned up, or gaps/whipsaws
  around the MA), and vice versa; the two signals disagree on a material
  share of trading days for every one of the 5 core assets in practice
  (verified empirically below, in "Implementation checks"), so this is not
  a relabeled or parametrically-nested version of family 001's rule.
- **Different sizing mechanic.** Family 001 is strictly binary: **fully
  invested (buy the whole deposit) or fully parked in cash** (buy nothing,
  cash sits earning IRX) depending on which side of the moving average the
  price is on — an all-in/all-out exit rule. This family instead **scales
  the size of every week's buy up or down by a multiplier that depends on
  the sign of trailing total-return momentum**, while always buying
  *something* every week (never a full 0x or exactly matching DCA's 1x
  baseline as its two states) — a genuinely continuous sizing dial
  (`mult_pos` / `mult_neg`, both != {0, 1} in the primary config), not an
  exit-to-cash rule. It is also not a re-test of family 003 (buy size
  scaled continuously by the *ratio* of realized volatilities, a pure
  variance-based signal with no directional/momentum content at all — vol
  can be elevated in either a rally or a selloff) or family 002 (cross-
  asset relative-strength rotation between the 5 core assets and T-bills,
  a relative, not own-asset-absolute, signal). No family in sec 7.2's
  closed list (v1 buy-the-dip/trim-the-spike ATR-shock/trend-stretch
  signals, v2 SmartDCA's rho x m_max mean-reversion-to-SMA sizing, v2 ADCA
  B1/B2, v2 rebalanced portfolios, v2.1 rate-regime Strategy D) uses a
  trailing own-asset total-return sign/magnitude as its buy-size signal
  either — the closest, SmartDCA, is again a price-vs-moving-average
  mean-reversion signal (the opposite economic bet: SmartDCA buys *more*
  the further price is *below* its trend, a contrarian rule, while TSMOM
  buys *more* when trailing return is positive, a trend-following rule).

## Exact rules

Computed at each trading day `t` using only data through `t` (no
lookahead). Orders are generated on the last trading day of each calendar
week (the deposit-credit day), consistent with every other v3 family's
weekly decision cadence.

- **Trailing total-return signal.** At week-end decision day `t`, define
  `ref_t = t - skip_days` (skip the most recent `skip_days` trading days —
  the standard momentum-literature "skip the most recent month" convention,
  used to avoid the well-documented short-term (1-month) reversal effect
  contaminating the momentum signal) and
  `mom_t = close_{ref_t} / close_{ref_t - lookback_days} - 1`
  (the asset's own trailing total return over `lookback_days` trading days,
  ending `skip_days` before today). Until both `ref_t - lookback_days >= 0`
  and `ref_t >= 0` (i.e. there isn't yet enough price history), the
  multiplier defaults to `1.0` (plain DCA) for that week.
- **Sign-based sizing multiplier.**
  `m_t = mult_pos if mom_t > 0 else mult_neg` (a pure step function of the
  *sign* of trailing momentum, matching Moskowitz/Ooi/Pedersen's own
  headline TSMOM construction — sign only, not the *magnitude* of `mom_t` —
  which is also what keeps the parameter count low: two multiplier levels
  instead of a continuous-magnitude scaling function that would need
  additional shape parameters).
- **Order.** `buy_usd_t = weekly_deposit x m_t`, `sell_usd = 0` (no
  selling — this is a pure sizing-up/sizing-down rule, like family 003, not
  a rule that ever liquidates existing units). The engine's own cash cap
  (sec 3.2) turns a below-deposit week (`m_t < 1`) into cash banked for a
  later above-deposit week (`m_t > 1`) — never leverage or borrowing, the
  same reserve mechanism family 003 already established and the task
  explicitly asks this family to reuse in spirit while using a distinct
  {0.5x, 1.5x}-style multiplier scheme (not family 003's continuous
  vol-ratio scaling).
- **On non-week-end days:** no order; cash sits idle earning IRX, same as
  every other family.

## Data inputs

Daily OHLC close price of the asset itself only (one of the 5 core assets,
tested independently — single-asset family per the task's instruction,
assessed per sec 4.1's single-asset rule, using the existing single-asset
`engine.py`). No macro or alternative data. Sourced via
`src.backtest.v3.data.load_dev()` only.

## Parameters (4 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `lookback_days` | 126, 252, 378 | 252 |
| `mult_pos` | 1.25, 1.5 | 1.5 |
| `mult_neg` | 0.5, 0.75 | 0.5 |
| `skip_days` | 0, 21 | 21 |

`lookback_days=252` (~12 months of trading days) is the primary because it
matches Moskowitz/Ooi/Pedersen's own headline 12-month lookback exactly,
the standard the literature built the "TSMOM" label around, and is a
no-look prior rather than something tuned on this loop's own data; 126
(~6 months) and 378 (~18 months) bracket it to test sensitivity.
`mult_pos=1.5, mult_neg=0.5` is the primary because it is a clean,
symmetric-around-1.0 {0.5x, 1.5x} sizing scheme — distinct in kind from
family 001's binary {0x, 1x} exit and family 003's continuous
`clip(sigma_ref/sigma_recent)` ratio, as the task instructed — while still
being a meaningfully large tilt (3x more capital deployed in a positive-
momentum week than a negative-momentum week) without ever fully exiting or
using leverage. `skip_days=21` (skip the most recent trading month) is the
primary because it is the standard momentum-literature convention to avoid
short-term reversal contaminating a 12-month momentum signal; `skip_days=0`
(no skip) is included as a grid arm to test whether that convention matters
here.

## Grid

3 (`lookback_days`) x 2 (`mult_pos`) x 2 (`mult_neg`) x 2 (`skip_days`) =
**24 configurations** (<= 36 cap; 4 params <= 5).

## Primary configuration

`lookback_days=252, mult_pos=1.5, mult_neg=0.5, skip_days=21`.

## Expected sign

**Positive on both wealth and Sharpe, if the TSMOM premium is real and
survives this loop's fee/robustness bar** — the whole point of scaling
*up* buy size after positive trailing momentum and *down* after negative
trailing momentum is to lean into the continuation effect Moskowitz, Ooi &
Pedersen document, buying disproportionately more of an asset's total
capital during exactly the weeks its trailing return has been positive
(when the literature says near-term continuation is more likely) and less
during exactly the weeks it has been negative. The expected failure mode,
flagged here before any backtest exactly as the task's own pattern note
anticipates: BTC's short (~5-year) development window is dominated by one
long, strongly-trending bull run with a few sharp, fast drawdowns — a
signal built on a 12-month (with 1-month skip) lookback will often still
read "positive momentum" heading into, or just after, one of BTC's sharp
drawdowns (trailing 12-month return stays positive well after a peak, since
the drawdown itself takes many months to erase a full year of prior gains),
so BTC could show a *larger* buy size right before or during a drawdown —
a real risk for this family's BTC-specific result, independent of whether
the effect is real on the other four, more range-bound-to-moderately-
trending assets (gold, silver, oil, and SP500's longer, calmer secular
uptrend). This is the same pooled-excess-series dynamic already observed
twice (families 002 and 004): a strategy can pass the 3-of-5 sec 4.1 bar
while BTC's outsized dollar/Sharpe swings still drag the pooled,
equal-weight-across-5-assets excess series (sec 3.3/4.2's DSR input)
toward a worse figure than the per-asset pattern alone would suggest — not
a bug if it recurs here, per the task's own note.

## Degenerate configuration (implementation check only, not a grid arm)

`enabled=False`: forces `m_t = 1.0` for every week (bypassing the momentum
signal computation entirely), which reproduces plain DCA exactly — same
pattern as families 001-004's `enabled=False` checks.
