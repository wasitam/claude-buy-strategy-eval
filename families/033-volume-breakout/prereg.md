# Family 033: Volume-confirmed breakout sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Karpoff, J.M. (1987), "The Relation Between Price Changes and Trading
Volume: A Survey," *Journal of Financial and Quantitative Economics*
22(1), 109-126 -- the foundational survey establishing that trading volume
carries information about the strength/conviction behind a price move
(volume is higher when new information triggers disagreement/revaluation),
not just noise. Lee, C.M.C. & Swaminathan, B. (2000), "Price Momentum and
Trading Volume," *Journal of Finance* 55(5), 2017-2069 -- shows past
trading volume predicts both the magnitude and duration of future price
momentum, with high-volume winners displaying more persistent continuation
than low-volume winners over intermediate horizons. Seed queue idea #33
(research-loop-plan-v3.md sec 7.3 addendum): volume-confirmed breakout
sizing.

## Mechanism ("why would this work, and who is on the other side?")

A price breakout to a new trailing-N-day high is ambiguous on its own: it
could be a durable shift driven by genuine new information broadly
absorbed by the market, or a thin, low-conviction move that reverses
quickly (a "false breakout"). Karpoff's volume-information link and Lee &
Swaminathan's volume-momentum result together suggest that trading volume
is the discriminator: a breakout accompanied by unusually heavy volume
(well above the asset's own recent trailing average) indicates broad
participation and revaluation -- more investors are actively repricing the
asset, not just a handful of traders drifting price on thin liquidity.
Lee & Swaminathan's finding that high-volume price moves show MORE
continuation (not less, and not mean-reversion) is the specific
directional prediction this family bets on: buying more into a
volume-confirmed breakout tilts a fixed-dollar DCA stream toward moments
when the market has just re-priced the asset with broad participation,
ahead of the intermediate-term continuation the volume-momentum literature
documents. The economic "other side" of this trade is participants who
react slowly to the same public volume+price information -- investors who
mechanically buy on a fixed calendar schedule regardless of signal
(exactly what plain DCA does), or who are underweight and adjust with a
lag as the breakout's information diffuses -- the same slow-diffusion
mechanism Lee & Swaminathan's own paper invokes to explain the
volume-conditioned continuation they document. This family re-times the
SAME total deposit stream (no leverage, no borrowing): it buys more on a
volume-confirmed breakout week's decision day, funded from cash normally
allocated on non-breakout weeks (when `normal_buy_mult<1`) or from banked
interest/prior slack, and buys at (or below) the normal rate otherwise.

## Category

**Trend / time-series momentum exit** (same category as families
001/005/020/028 -- see the required fourfold distinction below).

## The joint price+volume condition (why this is not a re-test of 001/005/020/028)

This loop already has four trend-family precedents, and this iteration's
task requires an explicit distinction from all four. None of the four
references trading volume at all -- each is a pure price-level or
pure-return signal:

| | Family 001 | Family 005 | Family 020 | Family 028 | Family 033 (this) |
|---|---|---|---|---|---|
| Signal type | Single MA vs. price level | Sign of trailing total return (TSMOM) | Price proximity to trailing 52-week high | Dual-MA crossover (fast vs. slow SMA) | **Joint** price breakout AND volume surge |
| Inputs | Close, one SMA | Close only (12-month return) | Close, trailing max(Close) | Close, two SMAs | Close **and Volume** |
| Uses trading volume? | No | No | No | No | **Yes -- required, not optional** |
| Regime/tilt logic | Binary: above/below one MA | Binary: positive/negative trailing return | Continuous ladder on proximity ratio | Binary: fast MA above/below slow MA, with persistence filter | Binary: BOTH a new N-day high AND a volume surge over its own trailing average must hold simultaneously |

The defining, load-bearing difference is the **AND**: family 033's signal
is false whenever either leg alone is true but the other is false -- a
price breakout on ordinary volume does NOT trigger the tilt, and a volume
surge with no price breakout does NOT trigger the tilt either. None of
families 001/005/020/028 has a volume leg to combine with anything, so
none of them could produce this joint condition even by construction.
Concretely, this family's joint condition is a **subset** of family 020's
"new/near trailing high" condition (which fires on price alone) --
family 033 requires the SAME price condition (a new trailing high, though
over a materially shorter window: 20-60 trading days here vs. family 020's
~252-trading-day/365-calendar-day window) PLUS an independent volume
condition that family 020 does not check at all. Family 033 is
economically distinct from family 020 for the same reason Lee &
Swaminathan's volume-conditioned continuation result is distinct from a
pure 52-week-high momentum result (George & Hwang 2004, family 020's own
source): the hypothesis under test here is specifically that volume
*confirmation* matters, not that price-level proximity alone matters.
The pre-grid sanity check (below, run after implementation, before the
grid) verifies concretely that the joint AND condition fires strictly less
often than the price-only leg alone on every asset -- direct evidence the
two families are not silently identical in practice either.

## Data prerequisite: reusing family 021's Volume-feasibility finding

Per this iteration's task instruction, this family reuses family 021's
already-established Volume-data feasibility finding
(`families/021-amihud-illiquidity/prereg.md`) rather than re-deriving it:
`src/backtest/v3/data.py`'s `_fetch_yf_raw` already includes a `Volume`
column for all 5 core assets (added for family 021), with the following
dev-period coverage already documented there:

| Asset | Dev days | Zero/missing-volume days | Coverage | Notes (per family 021) |
|---|---|---|---|---|
| SP500 (`^GSPC`) | 23,109 | 5,496 | 76.2% | All zero-volume days are 1927-1949 (pre-modern-reporting era); zero occurrences after 2010: 0. |
| GOLD (`GC=F`) | 4,848 | 410 | 91.5% | Scattered gaps 2000-2019, workable. |
| SILVER (`SI=F`) | 4,850 | 662 | 86.4% | Noisiest of the 5; still a minority of days. |
| BTC (`BTC-USD`) | 1,932 | 0 | 100.0% | Fully reliable. |
| OIL (`CL=F`) | 4,857 | 6 | 99.9% | All 6 zero days fall in one 2000-2001 window. |

This family's own trailing-volume-average computation applies the same
"never fabricate a signal from a bad volume print" rule family 021
established: a zero/missing-volume day is excluded from the trailing
average's population (not treated as zero, not imputed), and the trailing
average is only trusted once at least half of the trailing window has
valid volume observations (`MIN_VALID_VOLUME_FRAC = 0.5`); otherwise the
volume-surge leg (and hence the whole joint condition) cannot fire that
day. A day whose OWN volume is zero/missing also cannot itself register a
volume surge (there is nothing to compare). Given the coverage table
above, no asset's gaps are severe or clustered enough (over a 20-60
trading-day window) to make this warm-up/trust rule bind often outside
SP500's pre-1950 era, which is itself far outside the window sizes tested
here relative to the length of SP500's post-1950 dev history.

## Exact rules

For each core asset, on each trading day `t` (using a shared lookback
`window` for both legs, one of this family's 4 tunable parameters, kept
equal across the two legs deliberately -- both describe "the asset's own
recent trading regime" over the same horizon, avoiding a 5th free
parameter for no added economic content):

1. **Trailing high (price leg, strictly causal, excludes day t itself):**
   `high_t = max(Close_{t-window} .. Close_{t-1})`. Undefined (no signal
   yet) until `window` full trading days have elapsed.
2. **Trailing volume average (volume leg, strictly causal, excludes day t
   itself, ignores invalid volume days in its population):**
   `vol_avg_t = mean(Volume_s for s in {t-window..t-1} where Volume_s is
   finite and > 0)`, only trusted once >= `window * MIN_VALID_VOLUME_FRAC`
   valid observations exist in that trailing window; otherwise undefined.
3. **Price breakout leg:** `price_breakout_t = (high_t is defined) AND
   (Close_t > high_t)`.
4. **Volume surge leg:** `volume_surge_t = (Volume_t is finite and > 0)
   AND (vol_avg_t is defined and trustworthy) AND (Volume_t >
   volume_surge_multiple * vol_avg_t)`.
5. **Joint breakout condition (the entire mechanism -- BOTH must hold):**
   `joint_t = price_breakout_t AND volume_surge_t`.
6. **Weekly order (decision at week-end close, filled next open, per sec
   3.2):** `buy_usd_t = min(weekly_deposit * m_t, max_lump_multiple *
   weekly_deposit)`, where `m_t = breakout_buy_mult` if `joint_t` else
   `normal_buy_mult`. Never a sell. The engine's own cash cap (sec 3.2)
   turns a `normal_buy_mult<1` week's shortfall into banked cash (earning
   IRX), available to help fund a later `breakout_buy_mult>1` week -- the
   same reserve mechanism families 003/005/014/020/021/028 all use, never
   leverage or borrowing.

## Parameters (4 tunable, <=5)

1. `window` (trading days) -- shared trailing-high AND trailing-volume-
   average lookback. Grid: `[20, 40, 60]` (roughly 1, 2, 3 trading months
   -- a materially shorter, more tactical horizon than family 020's
   ~252-trading-day 52-week-high window, by design: this is a
   short-horizon breakout-confirmation signal, not a long-horizon
   proximity tilt).
2. `volume_surge_multiple` -- how far above its own trailing average a
   day's volume must be to count as a "surge." Grid: `[1.5, 2.0]` (the
   task brief's own suggested 1.5x-2x range).
3. `breakout_buy_mult` -- buy-size multiplier on a confirmed joint
   breakout week. Grid: `[1.5, 2.0, 2.5]`.
4. `normal_buy_mult` -- buy-size multiplier otherwise ("scale down/normal"
   per the task brief). Grid: `[0.75, 1.0]` (1.0 = literally normal/DCA
   rate on non-breakout weeks, funding the multiplier purely from cash
   interest/slack; 0.75 = an explicit scale-down that self-funds part of
   the breakout-week multiplier from banked cash).

`max_lump_multiple = 4.0` is a fixed (non-tunable) cash-capped ceiling on
any single week's buy relative to `weekly_deposit`, matching family 021's
convention -- headroom essentially never binds at this grid's multiplier
range but guards against a pathological reserve buildup.

## Grid (<=36 configs) and primary configuration

Grid size: `3 (window) x 2 (volume_surge_multiple) x 3 (breakout_buy_mult)
x 2 (normal_buy_mult) = 36` configs (at the 36-config cap).

**Primary configuration** (declared before any backtest, verified by a
module-level assertion in `volume_breakout.py` that it is a genuine member
of `grid_configs()`, per family 021's bugfix-log lesson):

```
PRIMARY_CONFIG = {
    "window": 40, "volume_surge_multiple": 1.5,
    "breakout_buy_mult": 2.0, "normal_buy_mult": 1.0,
}
```

(`max_lump_multiple=4.0` fixed.)

## Expected sign of the effect

Positive: the primary configuration is expected to beat plain DCA on final
wealth AND Sharpe, per the Lee & Swaminathan continuation hypothesis --
buying more into volume-confirmed breakouts should capture a
disproportionate share of subsequent momentum continuation relative to a
fixed-dollar buyer who is indifferent to the volume-confirmation signal.

## Complexity ceiling (sec 3.4) and closed-family check (sec 7.2)

- One page of rules, computable end-of-day: yes (above).
- At most one order per asset per trading day: yes (one weekly buy
  decision; no sells).
- At most 5 tunable parameters: yes (4).
- Free public data only: yes (yfinance OHLCV, already cached for the 5
  core assets, no new source).
- Grid <=36 with one declared primary: yes (36 configs, one primary).
- Not a re-test of sec 7.2's closed list: none of the closed v1/v2/v2.1
  families (ATR shock, trend stretch, SmartDCA, ADCA B1/B2, rebalanced
  portfolios C1-C3, rate-regime switch D and its variants) reference
  trading volume, a price-breakout condition, or a joint AND of two
  signals at all -- unrelated mechanisms and unrelated data.
