# Family 017: RSI2 short-horizon mean-reversion sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Connors, L. A. and Alvarez, C. (2009), *Short Term Trading Strategies That
Work*, Connors Research -- the book that popularized the 2-period RSI
("RSI2") as a short-horizon overbought/oversold trigger, with the
now-canonical heuristic that an asset closing with RSI2 below roughly 10
marks a short-term oversold extreme historically followed, on average, by
an above-average next-few-days bounce, and RSI2 above roughly 90 marks a
short-term overbought extreme. Also the broader academic short-horizon
reversal literature that predates and underlies the same empirical pattern:
Lehmann, B. N. (1990), "Fads, Martingales, and Market Efficiency,"
*Quarterly Journal of Economics* 105(1), and Jegadeesh, N. (1990),
"Evidence of Predictable Behavior of Security Returns," *Journal of
Finance* 45(3) -- both document short-horizon (weekly/monthly, in
Jegadeesh's case even at the few-days horizon Lehmann studies) return
reversals in individual securities, the same "recent losers bounce, recent
winners pull back" pattern RSI2 operationalizes as a bounded 0-100
oscillator. Seed queue idea #17 (research-loop-plan-v3.md sec 7.3
addendum / this iteration's task): "Short-horizon RSI2-style mean-reversion
sizing."

## Mechanism ("why would this work, and who is on the other side?")

RSI (Relative Strength Index, Wilder 1978) is a bounded 0-100 oscillator
computed purely from an asset's own recent up-day and down-day price
changes: it rises toward 100 after a run of gains and falls toward 0 after
a run of losses. At a very short lookback (2-4 trading days, as opposed to
Wilder's original 14-day convention), it becomes an extremely sensitive
short-horizon overbought/oversold gauge -- a reading near 0 means the asset
has fallen sharply over the last handful of days (short-term "oversold");
a reading near 100 means it has risen sharply over the same short window
("overbought"). The economic bet this family makes is that such short,
sharp moves are disproportionately driven by transient order-flow pressure
-- forced selling, stop-loss cascades, short-term liquidity demand, or
simple overreaction by momentum-chasing/panic-driven short-horizon traders
-- rather than a genuine repricing of fundamental value over a 2-4 day
window, and that this transient pressure tends to partially reverse within
the next few trading days (Lehmann 1990; Jegadeesh 1990). Buying
**more** than the normal weekly deposit specifically when the asset's own
RSI2 is deeply oversold, and buying **less** (banking the difference as
cash for a future oversold week) when it is overbought, aims to
systematically shift each week's fixed entry price toward these short-term
dips without changing the total capital deployed. The "other side" of this
trade is whoever creates the transient oversold pressure in the first
place -- margin-called or stop-loss-triggered short-horizon sellers,
liquidity-constrained market makers temporarily widening spreads and
marking prices down, or momentum/trend-following short-term traders
selling into weakness -- and is compensated for supplying that liquidity by
accepting a worse average price than a patient buyer with cash earmarked
specifically for those episodes; this family's investor bets that this
short-horizon overreaction-and-partial-reversal pattern persists often
enough, net of costs, to beat indiscriminate constant-size DCA.

## Rigorous triple distinction (required by this iteration's task, since a reviewer would ask)

This family's own-price, short-horizon oscillator signal must be
distinguished on three independent axes from three different prior
families that could superficially look similar. None of the three
distinctions is cosmetic -- each is a different input, a different
functional form, or a different time horizon, and no parameter setting of
family 017 nests or reduces to any of the three.

### (1) vs. family 016 (VIX contrarian): shared cross-market fear gauge vs. per-asset short-term price oscillator

| | Family 016 (VIX contrarian) | Family 017 (RSI2 reversion) |
|---|---|---|
| **Signal source** | The **CBOE VIX**, a single shared, cross-market signal derived entirely from S&P 500 **option prices** -- structurally identical across all 5 assets; gold, silver, BTC and oil have zero input into their own VIX-based signal. | Each asset's **own daily Close price series**, and nothing else -- no external data dependency of any kind. Five independently-computed signals, one per asset, each derived only from that asset's own price history. |
| **What is being measured** | The market's *implied* (options-priced, forward-looking) volatility/uncertainty, a single aggregate "fear" number. | The *realized, backward-looking* pattern of that specific asset's own recent gains vs. losses (a bounded ratio of average up-moves to average down-moves over the trailing `rsi_period` days) -- not a volatility measure at all, a directional short-term price-momentum-of-momentum oscillator. |
| **Trigger granularity** | One shared series (VIX), reindexed identically onto every asset's own calendar; a spike in SP500-option-implied vol triggers the SAME elevated-fear flag for gold, silver, BTC and oil regardless of what those assets' own prices are doing that day. | A genuinely per-asset calculation -- gold's RSI2 depends only on gold's own recent closes, oil's only on oil's, etc. Two assets can show opposite RSI2 readings (one oversold, one overbought) on the same day, which is structurally impossible for the shared, single-series VIX signal. |
| **Data dependency** | Requires a specific external index (`^VIX`) with its own coverage-start date (1990), creating the documented SP500 pre-1990 asymmetry in family 016's own results. | Requires nothing beyond the asset's own OHLC, already loaded for every family since 001 -- no external-data coverage gap of any kind, on any of the 5 core assets, for their entire development histories. |

In short: family 016 asks "is the *whole market* currently panicking, per
SP500 options, regardless of what this specific asset's own price is
doing?" Family 017 asks "has *this specific asset's own price*, on its own
terms, just moved sharply over the last 2-4 days?" These are different
signals by data source, by what they measure (implied cross-market fear
vs. realized per-asset price-run intensity), and by whether the signal can
ever differ across the 5 assets on the same calendar day (017: yes,
routinely; 016: no, never, by construction).

### (2) vs. family 003 (vol-managed sizing): realized *variance* (direction-agnostic) vs. price-momentum-based *oscillator* (directional)

Family 003 scales buy size by `1 / realized_variance` -- a smooth,
continuous, purely statistical measure of how *choppy* an asset's returns
have recently been, with **no view on the direction of the next move**:
a wildly volatile asset that is trending up just as much as down gets
sized down either way, purely because its variance is high. Family 017's
RSI2 is built entirely differently: it is the ratio of average trailing
**gains** to average trailing **losses** (a momentum-direction input, not
a dispersion/variance input) over a very short window, converted into a
bounded 0-100 oscillator, and it takes an explicit, directional view --
"this asset's price specifically FELL over the last 2-4 days, so it's a
buying opportunity" (oversold => buy more) is a fundamentally different
kind of claim than "this asset has been choppy lately, so let's hold less
of it regardless of which way it moved" (family 003's variance-targeting
logic). Two assets with identical trailing variance can have wildly
different RSI2 readings depending on whether that variance came from a
sharp fall (low RSI2, family 017 says buy more) or a sharp rise (high
RSI2, family 017 says buy less) -- a distinction family 003's variance
input cannot make at all, since variance from `(price-up)^2` and
`(price-down)^2` contribute identically to `realized_variance`. Different
input statistic entirely (dispersion vs. directional gain/loss ratio),
different economic story (risk-parity variance targeting vs. short-horizon
overreaction/reversal), and no nesting in either direction.

### (3) vs. families 001/005 (moving-average trend exit / 12-month TSMOM): opposite time horizon AND opposite economic logic

Families 001 (10-month/200-day moving-average trend exit) and 005
(12-month time-series momentum sizing) are both **long-horizon,
trend-following** signals: they ask "has this asset been broadly rising or
falling over the last several months to a year?" and size up (or stay
invested) when the trailing long-run trend is positive, size down (or exit
to cash) when it is negative -- betting that trends, once established,
**persist**. Family 017's RSI2 does the opposite on both axes at once:

| | Family 001/005 (long-horizon trend) | Family 017 (RSI2 reversion) |
|---|---|---|
| **Time horizon** | Trailing **200 trading days (~10 months) to 252+ trading days (~12 months)** -- multi-quarter to annual. | Trailing **2-4 trading days** -- a handful of sessions, three orders of magnitude shorter. |
| **Economic logic** | **Trend-following / momentum persistence**: a sustained multi-month up (down) move is expected to continue, so lean in (out) with it. | **Mean reversion**: a sharp *few-day* move is expected to partially *reverse*, so lean AGAINST the most recent direction. |
| **Sign relative to the most recent price move** | Buy more (or stay invested) after the asset has recently been RISING over months (positive trend => bullish continuation bet). | Buy more specifically after the asset has recently been FALLING over days (oversold => bullish reversal bet) -- the opposite recent-price-direction trigger for the same "buy more" action. |
| **What a losing streak means for buy size** | A sustained *downtrend* (family 001: exit to cash; family 005: `mult_neg<1`, buy less) is read as a bearish signal to de-risk. | A short *losing streak* (family 017: oversold) is read as a bullish signal to size UP -- the literal opposite response to a run of recent losses. |

No parameter setting of family 017 can reduce to family 001's or 005's
rule (RSI2's minimum meaningful lookback, 2 trading days, is far below any
sensible long-horizon trend window, and its economic sign is inverted
relative to trend-following even if the lookback were somehow stretched),
and vice versa -- trend-following and mean-reversion are, by definition,
opposite bets on the same underlying phenomenon (serial correlation in
returns): family 001/005 bet on positive serial correlation at a
multi-month horizon; family 017 bets on negative serial correlation at a
multi-day horizon. Both can be true simultaneously (momentum at long
horizons, reversal at short horizons is itself a well-documented joint
empirical pattern, e.g. Jegadeesh & Titman 1993 vs. Lehmann 1990/Jegadeesh
1990), which is precisely why they are not the same mechanism and are not
mutually exclusive as separate, distinctly-categorized families in this
loop.

## Category

**Sizing / valuation** (same category as families 003, 004, 008, 014, 016
-- all "increase/decrease the buy because a signal says this is a
relatively favorable/unfavorable entry point" mechanisms). Not "Trend /
time-series momentum exit" (families 001, 005): RSI2 is explicitly a
mean-reversion, not a trend-following, signal -- see distinction (3) above.
Not "Volatility targeting" (family 003): RSI2 is a directional
gain/loss-ratio oscillator, not a dispersion/variance statistic -- see
distinction (2) above.

## Single-asset vs. portfolio scoping

Assessed as a **single-asset family across all 5 core assets** under sec
4.1's standard >=3/5 rule, the RSI2 signal computed independently per
asset from that asset's own price series -- directly following the
precedent set by families 001, 003 and 005 (each asset's own internal
signal, tested per-asset via the existing single-asset `engine.py`, no
capital ever rotating between assets).

## Data inputs and reachability (gate step)

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only,
  same as every prior family). **No external data dependency at all** --
  RSI2 is computed purely from the asset's own `Close` series, so there is
  no macro/alternative-data reachability question and no point-in-time /
  ALFRED-vintage concern (documented explicitly, matching every prior
  price-only-signal family's "N/A" entry for that check).

## Gate: not a re-test of sec 7.2's closed list

Sec 7.2's closed list includes v1's Signal A ("buy-the-dip," an **ATR
shock** percentile rule) and Signal B ("trim-the-spike," a trend-stretch
rule). Signal A is the closest prior mechanism to RSI2 by surface intent
(both are "buy more after a short-term down-move" rules), so the
distinction is made explicit here: Signal A's trigger is an **ATR
(Average True Range) shock** -- a measure of a single day's (or a few
days') *range/volatility expansion* relative to a trailing ATR average,
i.e. "did today's trading range blow out relative to normal?", a pure
dispersion-of-price-range statistic with no reference to the direction or
cumulative magnitude of a multi-day run of gains vs. losses. RSI2 is
instead the **ratio of average gains to average losses over a trailing
2-4 day window**, a directional accumulation-of-price-change statistic --
an asset can show a large ATR shock from a single volatile
higher-high/lower-low day even while closing flat or up (RSI2 would then
read near 50, not oversold), and conversely can show a deeply oversold
RSI2 from several consecutive modest down-closes with no single-day range
expansion at all (ATR would then show no shock). Different input
statistic (range/dispersion vs. cumulative directional gain/loss ratio),
different functional form (ATR-shock percentile threshold on a single
day's range vs. RSI2's smoothed multi-day gain/loss ratio converted to a
bounded 0-100 oscillator), and no parameter setting of either rule
reduces to the other. This is a materially different signal definition per
sec 7.2's "materially different" bar.

## Complexity ceiling check (sec 3.4)

- Rules fit on one page, computed from end-of-day data only. PASS.
- At most one order per asset per trading day (a single buy order, never a
  sell). PASS.
- At most 5 tunable parameters (4 grid-varied + 1 fixed constant, same
  "4+1" pattern families 015/016 used). PASS.
- All data free and public, already-loaded OHLC only, no new source.
  PASS.
- Grid: 24 configurations (<=36 cap), one primary configuration declared
  below before any testing. PASS.

## Pre-backtest non-degeneracy check (per the task's explicit instruction, following family 015/016's precedent after family 014's oversight)

Before any backtest, the primary configuration's oversold-trigger frequency
(`RSI2 < 10`, `rsi_period=2`) was computed directly against
development-window data for all 5 core assets (causal, using only data
through each day's own close):

| Asset | Dev days (with RSI2 defined) | Oversold days (RSI2<10) | Frac. oversold | Overbought days (RSI2>90) | Frac. overbought |
|---|---|---|---|---|---|
| SP500 | see `_run_output.json` (populated by the run script before the grid) | | | | |
| GOLD | | | | | |
| SILVER | | | | | |
| BTC | | | | | |
| OIL | | | | | |

(Populated numerically by `scripts/v3/run_017_rsi2_reversion.py` before any
grid backtest is trusted -- the run aborts with a non-degeneracy failure if
any asset's oversold OR overbought fraction falls outside a broad
`(2%, 40%)` sanity band, the same style of guard used by family 016's
`primary_regime_nondegenerate` check. RSI2 at a 2-day lookback is expected,
by construction of the oscillator, to spend a non-trivial share of days in
both tails -- unlike family 015's DXY regime or family 011's credit-stress
signal, which are slower-moving and can plausibly sit degenerate near 0%
or 100%, a 2-day RSI naturally oscillates and should show meaningfully
more than a handful of percent in each tail on any asset with typical
day-to-day noise.)

## Exact rules

Computed at each trading day's close `t`, using only data available by
that close.

1. **RSI(rsi_period)**: a simple (non-Wilder-smoothed) rolling-average
   gain/loss oscillator over the trailing `rsi_period` daily closes,
   documented explicitly as this family's chosen simplification (Wilder's
   original 1978 formula uses an exponential/Wilder smoothing recursion
   seeded from a longer initial average; at a 2-4 day lookback the
   difference between Wilder smoothing and a plain trailing simple average
   is negligible and the simple-average form is fully causal, exactly
   reproducible, and avoids any path-dependent seeding-window ambiguity):
   - `delta_t = Close_t - Close_{t-1}`.
   - `avg_gain_t` = mean of `max(delta, 0)` over the trailing `rsi_period`
     days (through day `t`); `avg_loss_t` = mean of `max(-delta, 0)` over
     the same window.
   - `RS_t = avg_gain_t / avg_loss_t`; `RSI_t = 100 - 100 / (1 + RS_t)`.
   - Edge cases: if `avg_loss_t = 0` and `avg_gain_t > 0`, `RSI_t = 100`
     (all up days, no down days in the window). If `avg_gain_t = 0` and
     `avg_loss_t = 0` (flat window), `RSI_t = 50` (neutral).
   - `min_periods = rsi_period + 1` (need `rsi_period` deltas, i.e.
     `rsi_period + 1` closes). Before enough history exists, `RSI_t` is
     undefined and the signal defaults to the **normal** state (buy
     `1.0 * weekly_deposit`), matching every prior family's warm-up
     convention.
2. **Weekly decision (week-end days only, no sells ever, no leverage)**:
   - **Oversold** (`RSI_t < oversold_threshold`): buy
     `min(cash, buy_mult_oversold * weekly_deposit)`.
   - **Overbought** (`RSI_t > overbought_threshold`): buy
     `buy_mult_overbought * weekly_deposit` (< 1.0; the remainder is
     banked as cash, earning IRX, specifically to fund a future oversold
     week's extra buying).
   - **Normal** (`oversold_threshold <= RSI_t <= overbought_threshold`,
     or RSI undefined during warm-up): buy `1.0 * weekly_deposit` (plain
     DCA for that week).
   - This is the same "bank on the down leg, spend the bank on the
     up-conviction leg" reserve mechanism used by families 003, 005, 015
     and 016 -- no leverage, no borrowing: cash never goes negative
     (engine's own cap, sec 3.2), and the oversold leg's `min(cash, ...)`
     means a long stretch without any prior banked cash can only ever buy
     up to that week's own deposit, never more.
3. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the RSI computation entirely and buys 100% of that
   week's cash on every week-end day (0 otherwise) -- reproduces plain DCA
   bit-for-bit, same pattern as every prior v3 family's disable path.

## Parameters (4 tunable + 1 fixed, <=5 total, same "4+1" pattern as families 015/016)

| Parameter | Grid values | Primary |
|---|---|---|
| `rsi_period` (trailing window, trading days, for the RSI calc) | 2, 3, 4 | 2 |
| `oversold_threshold` (RSI below this = oversold, buy more) | 10, 15 | 10 |
| `overbought_threshold` (RSI above this = overbought, buy less) | 85, 90 | 90 |
| `buy_mult_oversold` (multiple of weekly deposit bought when oversold) | 1.5, 2.0 | 2.0 |

`buy_mult_overbought` is fixed at **0.5** for every grid config and the
primary (not grid-varied) -- the fraction of a normal deposit still bought
in an overbought week, keeping the banking mechanic's overbought-leg
"how much gets diverted to reserve" behavior identical across the whole
grid so the grid isolates the effect of the oversold-trigger parameters,
the same role family 016's fixed `max_buy_multiple` played. Keeps this
family at 4 tunable (grid-varied) parameters plus 1 fixed constant, at/under
the plan's <=5 ceiling.

`rsi_period=2` is primary as the canonical Connors & Alvarez (2009) RSI2
convention that gives this family its name, not a value chosen after
seeing any development-data result -- `rsi_period=3,4` are the grid's
slightly-smoothed diagnostic variants. `oversold_threshold=10` and
`overbought_threshold=90` are primary as Connors & Alvarez's own canonical
thresholds (their book's central rule uses exactly these two levels for a
2-period RSI), the more literal, higher-conviction reading of the
published mechanism, with `15`/`85` in the grid as looser diagnostic
variants. `buy_mult_oversold=2.0` (double the normal deposit on an
oversold week) is primary as a clean, easily-explained "buy twice as
much" rule, mirroring family 016's own `buy_multiplier=2.0` primary choice
for exactly the same "double on the signal day" logic and comparability
across families -- not the grid's more aggressive end, and not picked to
maximize any observed effect (fixed before any backtest was run).

## Grid

3 (`rsi_period`) x 2 (`oversold_threshold`) x 2 (`overbought_threshold`) x
2 (`buy_mult_oversold`) = **24 configurations** (<=36 cap).

## Primary configuration

`rsi_period=2, oversold_threshold=10, overbought_threshold=90,
buy_mult_oversold=2.0, buy_mult_overbought=0.5` (fixed).

## Expected sign

**Positive on both wealth and Sharpe**, if the short-horizon
overreaction-and-partial-reversal pattern documented by Connors & Alvarez
and the Lehmann (1990)/Jegadeesh (1990) academic reversal literature holds
up net of the mechanism's own costs and the weekly (not daily) decision
cadence this family's engine uses (the original RSI2 trading literature is
usually applied at DAILY entry/exit frequency with a short holding period
and often an explicit exit rule; this family instead applies it only to
size the fixed WEEKLY deposit decision, a much lower-frequency,
buy-only adaptation -- flagged here honestly, since a signal's edge
demonstrated at daily trading frequency need not survive being diluted
into a once-a-week deposit-sizing decision). Per family 010/011/015/016's
documented precedent, a sec 4.1 pass driven by a small number of dominant
short-horizon episodes clustering the pooled excess-return series is
exactly what the DSR and placebo circular-shift test (sec 4.3) are
designed to catch, and this family's own results should be read with that
precedent in mind before drawing conclusions from sec 4.1 alone. As with
every prior timing/banking-mechanic family, this only reallocates the
*timing* of a fixed deposit stream, never total capital deployed and never
leverage, so even a real effect may show a modest absolute wealth/Sharpe
margin over DCA.

## Implementation-check plan (sec 3.2, to be run in the implementation step)

1. `enabled=False` bypass reproduces plain DCA bit-for-bit (units and
   cash).
2. Cash and positions never negative, for the DCA baseline, the primary
   config, and the grid's most aggressive corner
   (`rsi_period=2, oversold_threshold=15, overbought_threshold=85,
   buy_mult_oversold=2.0` -- widest oversold/overbought bands (most days
   flagged in one tail or the other) combined with the highest oversold
   multiplier, i.e. the config expected to spend cash fastest/hardest).
3. Total capital deployed never exceeds cumulative deposits + interest
   (primary config and the aggressive corner).
4. No-lookahead: perturbing all data after day `t` leaves every order
   on/before `t` unchanged, checked at two spot-check points deep into the
   sample (following family 011/015/016's precedent of checking more than
   one `t`). RSI2's lookback is only 2-4 trading days, the shortest of any
   family in this loop -- causality should be trivial to verify here (a
   perturbation should have essentially zero ability to leak into an
   order many trading days earlier, and even the immediate few days before
   `t_check` must be checked carefully since the RSI window is so short
   that off-by-one indexing errors would show up immediately as a failed
   check, unlike a 200+ day window where such a bug could be masked).
5. Point-in-time macro: N/A -- no macro/alternative data is used at all
   (RSI2 is computed purely from the asset's own OHLC, already
   point-in-time by construction), documented explicitly rather than
   silently skipped, matching the precedent set by every prior
   price-only-signal family's "N/A" entry for this check.
