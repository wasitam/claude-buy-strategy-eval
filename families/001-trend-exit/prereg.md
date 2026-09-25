# Family 001: 10-month / 200-day moving-average trend exit

**Status:** pre-registered. Committed before any backtest is run on development
data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Faber, M. T. (2007), *A Quantitative Approach to Tactical Asset Allocation*,
Journal of Wealth Management. The classic "10-month simple moving average"
timing rule: hold the asset while price is above its trailing 10-month (here,
~200-trading-day) simple moving average; hold cash/T-bills while below.
Seed queue item #1 (research-loop-plan-v3.md sec 7.3).

## Mechanism ("why would this work, and who is on the other side?")

The claim is that trend-following on a single asset's own price history earns
a premium by (a) avoiding the worst, most autocorrelated drawdown regimes
(crashes tend to trend downward for months, not spike-and-recover), and (b)
being systematically willing to step aside while discretionary/behavioral
investors continue buying into a downtrend out of anchoring or sunk-cost bias,
and while forced sellers (margin calls, redemptions) are still supplying
downward order flow the trend-follower has already avoided. The "other side"
of the trade is investors who hold through the SMA breach — often for tax,
mandate, or behavioral reasons — and effectively sell cheap into the
trend-follower's earlier exit, and later sell to the trend-follower again (at
a higher price, after the SMA reclaim) when re-entering. The cost paid for
this is whipsaw in choppy, range-bound markets, and the risk of missing sharp
V-shaped recoveries that reclaim the SMA quickly.

## Category

**Trend / time-series momentum exit** (research-loop-plan-v3.md sec 4.5).

## Relationship to closed families (sec 7.2)

None of the v1/v2/v2.1 closed families used a moving-average trend filter on
raw price to gate contributions. v1 Signal A/B used ATR shocks and percentile
trend-stretch signals (different mechanism: mean-reversion/shock detection,
not a trend-following MA crossover). v2.1 Strategy D used macro rate-regime
signals (FRED data), not price trend. This family is a different mechanism
and a different data input (own-price SMA only) and is not a re-test of any
closed family.

## Exact rules

Let `SMA_t` be the simple moving average of the daily close over the trailing
`sma_days` trading days (using data through day `t`'s close only — no
lookahead). Define `above_t = close_t > SMA_t`; while fewer than `sma_days`
observations exist, treat the asset as invested (defaults to plain DCA until
the indicator is computable).

If `confirm_days == 0`: the invested/cash state flips immediately with
`above_t`.

If `confirm_days > 0`: the state only flips after `above_t` (or its negation)
has held for `confirm_days` consecutive trading days (a debounce filter
against whipsaw).

Each trading week, the $500 deposit is credited at the week's last trading
day close (engine sec 3.2). At each day's close, if the current state is
"invested," the full available cash is submitted as a buy order (fills at
next day's open); if the state is "cash," no buy order is submitted and the
deposit continues to earn IRX/252 interest in the cash account.

`sell_on_exit` (grid diagnostic only, not part of the primary configuration):
if 1, existing holdings are fully liquidated (sell order for all units) on a
confirmed cross from invested->cash, replicating Faber's original all-in/
all-out timing rule; if 0 (primary), only new deposits are toggled and
existing holdings are held through the cash phase. The literal wording of
seed-queue idea #1 ("buy DCA while above... park deposits in cash while
below") describes only deposit disposition, so the deposit-only variant is
the primary configuration; `sell_on_exit=1` is tested across the grid as a
robustness/diagnostic comparison to the classic full-liquidation rule, but
per sec 4.4 only the pre-declared primary configuration is eligible to become
a finalist.

## Data inputs

Daily OHLC close price of the asset itself only (one of the 5 core assets,
tested independently — this is a single-asset family, not a portfolio). No
macro or alternative data. Sourced via `src.backtest.v3.data.load_dev()`
only.

## Parameters (3 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `sma_days` | 189, 210, 231 (~9, ~10, ~11 trading months) | 210 |
| `confirm_days` | 0, 3, 5 | 0 |
| `sell_on_exit` | 0, 1 | 0 |

## Grid

3 x 3 x 2 = **18 configurations** (<= 36 cap).

## Primary configuration

`sma_days=210, confirm_days=0, sell_on_exit=0` — the literal Faber 10-month
rule at daily resolution, no debounce, deposits-only toggle.

## Expected sign

Positive: higher final wealth and higher Sharpe than plain weekly DCA,
concentrated in assets with strong, sustained multi-year drawdowns (S&P 500,
oil, BTC) where avoiding sustained downtrends outweighs the whipsaw cost of
choppier periods (gold/silver, historically more range-bound in the
development sample).
