# Family 030: Losing-streak (consecutive-down-days) contrarian sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Jegadeesh, N. (1990), "Evidence of Predictable Behavior of Security
Returns," *Journal of Finance* 45(3), 881-898, and Lehmann, B. N. (1990),
"Fads, Martingales, and Market Efficiency," *Quarterly Journal of
Economics* 105(1), 1-28 -- the classic short-horizon return-reversal
literature: individual securities that have recently underperformed over
a short window (days to a few weeks) tend, on average, to outperform over
the following short window, and vice versa for recent short-horizon
winners. Seed queue idea #30 (`state/research_queue.md`, added this loop).

## Mechanism ("why would this work, and who is on the other side?")

A short, discrete run of consecutive down-days in an asset's own daily
closing price is used here as a raw, unsmoothed signal that the asset has
just been under unusually persistent short-term selling pressure --
forced liquidation, stop-loss cascades, margin calls, tax-loss-adjacent
selling, or simple short-horizon panic/momentum-chasing by other market
participants -- rather than a genuine multi-day repricing of fundamental
value. The reversal literature's mechanism is that this kind of pressure
is disproportionately supplied by liquidity-constrained or
sentiment-driven short-horizon sellers, and that a patient buyer with
capital specifically earmarked for such episodes can capture a partial
rebound over the following days as that transient pressure fades and
liquidity providers/contrarian capital step back in. Symmetrically, a run
of consecutive up-days is read as a short-term overheated/euphoric episode
disproportionately driven by short-horizon momentum-chasers, and this
family banks a below-normal deposit during such a run (never sells) so
that capital is available for a future losing streak. The "other side" of
this trade is whoever creates and initially profits from the streak, i.e.
short-horizon momentum-chasing or forced-liquidation counterparties on the
way down, and momentum-chasing buyers driving the streak on the way up --
this family's investor bets that the reversal that follows a *discrete run
count* of consecutive down (or up) closes persists often enough, net of
costs, to beat indiscriminate constant-size DCA.

## Signal construction: a DISCRETE consecutive-day COUNT, not a ratio/oscillator (required distinction from family 017)

This family's core design choice, made explicit before any backtest, is to
use a **raw, unsmoothed count of consecutive same-direction daily closes**
(a streak LENGTH, an integer that only depends on the *sign* of each
day's price change, never its *magnitude*) as the trigger signal, rather
than any bounded gain/loss RATIO or oscillator. This is deliberately
**not** a re-parameterization of family 017's RSI2:

| | Family 017 (RSI2) | Family 030 (losing-streak count) |
|---|---|---|
| **Input statistic** | The **ratio** of the average MAGNITUDE of up-moves to the average magnitude of down-moves over a trailing window (`avg_gain / avg_loss`), converted into a smoothed, bounded 0-100 oscillator. | The **count** of consecutive days with the same SIGN of daily price change. Magnitude of any day's move plays no role at all -- a 0.01% down-day and a 5% down-day extend the streak identically. |
| **Functional form** | Continuous, bounded [0, 100]; every day's move (even a single large one inside the window) can shift the reading substantially via the gain/loss averages. | Discrete, unbounded non-negative integer; resets to 0 the instant a single day's direction flips, regardless of how large that reversing day's move is. |
| **Sensitivity to a single big up-day inside a down-window** | A single large up-day inside an otherwise-down window pulls RSI2 up smoothly (raises `avg_gain`), potentially by a lot, but does not necessarily flip the oversold/normal state discretely. | A single up-day of ANY size, however small, immediately resets the down-streak count to 0 -- an all-or-nothing, direction-only reset with no partial credit for magnitude. |
| **What "3" and "10" mean** | RSI2 has no natural integer streak count at all -- it is a smoothed ratio, not a tally. | A count of "3" literally means "3 consecutive down-closes," a directly interpretable, auditable integer with no smoothing parameter to tune (unlike RSI2's `rsi_period`, which changes how much weight recent vs. older days get within the ratio). |
| **Nesting** | No setting of `rsi_period`, `oversold_threshold` etc. can reduce to a pure streak-length count (RSI2 can never fully ignore magnitude, since `avg_gain`/`avg_loss` are magnitude-weighted means by construction). | No setting of this family's parameters can reproduce RSI2's magnitude-weighted ratio (a streak count structurally discards all magnitude information). |

Family 030 additionally introduces a genuinely new mechanical element that
family 017 has no analogue for at all: an explicit **decay/duration
window** (`decay_days`) during which the elevated (or reduced) buy state
persists *after* a trigger, rather than reacting instantaneously and
independently on every single day as RSI2 does. RSI2's state is a pure
function of the current day's smoothed ratio, recomputed fresh every day
with no memory of *when* the extreme reading occurred; family 030
explicitly tracks "how many trading days ago did the most recent
qualifying streak end" and keeps the elevated-buy state alive for a fixed
number of subsequent trading days (a state-machine-with-memory
construction, not a stateless day-by-day oscillator threshold). This is
an independent, non-cosmetic mechanical difference on top of the
count-vs-ratio distinction above.

## Distinction from family 023 (realized skewness)

Family 023's signal is a trailing-window **statistical moment** (the third
standardized moment of the daily-return distribution over a rolling
window, `skew_window` days) -- a continuous measure of the *asymmetry* of
the whole distribution of returns over that window, sensitive to the
magnitude and clustering of extreme moves regardless of their sequential
ordering (a skew-window containing one huge down day and several small up
days has the same skewness contribution structure regardless of which day
within the window the big move fell on, aside from the window boundary).
Family 030's streak count is explicitly **order-dependent and
magnitude-blind**: it only cares about the unbroken sequential run of
same-sign closes ending today, discarding all information about how large
any individual day's move was. A skewness statistic cannot recover a
streak count (magnitude-weighted vs. magnitude-blind) and a streak count
cannot recover a skewness statistic (sequential-order-dependent vs. a
window-level moment) -- neither nests the other.

## Distinction from family 003 (realized variance)

Family 003 scales buy size by `1 / realized_variance`, a direction-agnostic
dispersion statistic: `(price change)^2` contributes identically whether
the day was up or down, and a streak of alternating up/down days with
large moves produces high variance with no directional signal at all.
Family 030's streak count is purely directional (a run of down-days vs.
a run of up-days) and is completely insensitive to the magnitude that
drives variance -- a long streak of tiny down-ticks (near-zero variance
contribution) triggers this family's elevated-buy state exactly as
readily as a long streak of large down-days would, provided both are the
same LENGTH. No nesting in either direction, same conclusion family 017's
own prereg.md reached against family 003.

## Category

**Sizing / valuation** (same category as families 003, 004, 008, 014, 016,
017: "increase/decrease the buy because a signal says this is a
relatively favorable/unfavorable entry point").

## Single-asset vs. portfolio scoping

Assessed as a **single-asset family across all 5 core assets** under sec
4.1's standard >=3/5 rule, the streak signal computed independently per
asset from that asset's own daily Close series -- directly following the
precedent of families 001/003/005/014/017/020/021/023/026/028 (each
asset's own internal signal, no capital ever rotating between assets).

## Data inputs and reachability (gate step)

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only,
  same as every prior family). **No external data dependency at all** --
  the streak signal is computed purely from the asset's own `Close`
  series (the sign of `Close_t - Close_{t-1}`), so there is no
  macro/alternative-data reachability question and no point-in-time /
  ALFRED-vintage concern.

## Gate: not a re-test of sec 7.2's closed list

Sec 7.2's closed list includes v1's Signal A ("buy-the-dip," an ATR-shock
percentile rule keyed on a single day's trading-RANGE expansion) and
Signal B ("trim-the-spike," a trend-stretch rule). Neither closed rule
counts consecutive same-direction CLOSES at all; Signal A's trigger is a
single-day range-expansion statistic (can fire on one volatile day with no
directional persistence whatsoever), structurally different from a
multi-day consecutive-direction streak count. Not a re-test of either.

## Complexity ceiling check (sec 3.4)

- Rules fit on one page, computed from end-of-day data only. PASS.
- At most one order per asset per trading day (a single buy order, never a
  sell). PASS.
- At most 5 tunable parameters (4 grid-varied + 1 fixed constant, the same
  "4+1" pattern families 015/016/017 used). PASS.
- All data free and public, already-loaded OHLC only, no new source. PASS.
- Grid: 36 configurations (<=36 cap), one primary configuration declared
  below before any testing. PASS.

## Exact rules

Computed at each trading day's close `t`, using only data available by
that close (strictly causal).

1. **Direction**: `dir_t = sign(Close_t - Close_{t-1})` (`+1` up, `-1`
   down, `0` flat/unchanged; `dir_0` undefined on the first day).
2. **Streak length**: `down_streak_t` = the number of consecutive trading
   days ending at `t` (inclusive) with `dir <= 0`... **clarified**: a flat
   day (`dir_t = 0`) neither extends nor breaks a streak of the opposite
   sign nor counts as a down day itself -- only a strict `dir_t = -1`
   extends `down_streak_t` (`down_streak_t = down_streak_{t-1} + 1` if
   `dir_t = -1`, else `down_streak_t = 0`); symmetric for `up_streak_t`
   using `dir_t = +1`. This is a pure count of the sign of each day's
   price change, with no reference to the magnitude of any day's move.
3. **Trigger days**: `trigger_down_t = (down_streak_t >= streak_threshold)`;
   `trigger_up_t = (up_streak_t >= streak_threshold)`.
4. **Elevated/reduced-buy window (the decay/duration mechanic)**: let
   `last_down_t` = the most recent day `<= t` on which `trigger_down` was
   true (causal, tracked day by day; `-infinity` if never yet triggered),
   and `last_up_t` similarly for `trigger_up`. Define:
   - `days_since_down_t = t - last_down_t`
   - `days_since_up_t = t - last_up_t`
   - `state_t = "elevated"` if `days_since_down_t <= decay_days`;
     **else** `state_t = "reduced"` if `days_since_up_t <= decay_days`;
     **else** `state_t = "normal"`.
   - Priority rule (documented, not expected to bind often given
     `streak_threshold >= 2`): if both windows are simultaneously active
     (a losing-streak trigger and a winning-streak trigger both within
     `decay_days` of `t`), `"elevated"` takes priority, since this
     family's primary hypothesis under test is the losing-streak rebound,
     not the winning-streak pullback.
   - Before enough history exists for any streak to be defined (`t=0`),
     `state_t = "normal"` (matches every prior family's warm-up
     convention of defaulting to plain-DCA behavior).
5. **Weekly decision (week-end days only, no sells ever, no leverage)**:
   - **Elevated** (`state_t = "elevated"`): target buy =
     `buy_mult_streak * weekly_deposit`, capped at
     `max_lump_multiple * weekly_deposit` (the safety ceiling on any
     single lump buy even if a large cash reserve has banked up), then
     capped again at available cash (`min(cash, ...)`, the engine's own
     no-leverage cap).
   - **Reduced** (`state_t = "reduced"`): buy
     `buy_mult_winning * weekly_deposit` (< 1.0; the remainder is banked
     as cash, earning IRX, specifically to fund a future elevated week's
     extra buying) -- the same "bank on the down leg, spend the bank on
     the up-conviction leg" reserve mechanism families 003/005/015/016/017
     use.
   - **Normal**: buy `1.0 * weekly_deposit` (plain DCA for that week).
6. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the streak computation entirely and buys 100% of
   that week's cash on every week-end day (0 otherwise) -- reproduces
   plain DCA bit-for-bit, the same disable-path pattern every prior v3
   family uses.

## Parameters (4 tunable + 1 fixed, <=5 total)

| Parameter | Grid values | Primary |
|---|---|---|
| `streak_threshold` (consecutive same-direction closes needed to trigger, shared by the down- and up-streak legs) | 2, 3, 4 | 3 |
| `buy_mult_streak` (multiple of weekly deposit targeted during an elevated losing-streak window) | 1.5, 2.0 | 2.0 |
| `decay_days` (trading days the elevated/reduced state persists after the most recent qualifying trigger) | 3, 5, 10 | 5 |
| `max_lump_multiple` (hard ceiling, as a multiple of weekly deposit, on any single buy regardless of banked cash) | 2.5, 3.0 | 3.0 |

`buy_mult_winning` is fixed at **0.5** for every grid config and the
primary (not grid-varied) -- the fraction of a normal deposit still bought
during a reduced (winning-streak) window, keeping that leg's "how much
gets diverted to reserve" behavior identical across the whole grid so the
grid isolates the effect of the losing-streak-side parameters, the same
role family 017's fixed `buy_mult_overbought=0.5` played. Keeps this
family at 4 tunable (grid-varied) parameters plus 1 fixed constant, at/
under the plan's <=5 ceiling.

`streak_threshold=3` is primary as a middle-of-the-road, easily-explained
"3 down days in a row" rule (a round-number streak length with intuitive
appeal, neither the most permissive (`2`, which triggers very often) nor
the most restrictive (`4`) grid arm), fixed before any backtest was run.
`buy_mult_streak=2.0` mirrors family 017's own `buy_mult_oversold=2.0`
primary choice (a clean, easily-explained "buy twice as much" rule) for
direct comparability across the loop's sizing/valuation families.
`decay_days=5` (one trading week) is primary as the most easily-explained
duration ("the elevated window lasts about a week"), and is the grid's
middle value. `max_lump_multiple=3.0` matches family 028's own primary
ceiling value and is not expected to bind given `buy_mult_streak<=2.0`
(documented explicitly as a safety constant, not a lever expected to
drive results, same role it plays in family 028's prereg.md).

## Grid

3 (`streak_threshold`) x 2 (`buy_mult_streak`) x 3 (`decay_days`) x 2
(`max_lump_multiple`) = **36 configurations** (<=36 cap, at the ceiling).

## Primary configuration

`streak_threshold=3, buy_mult_streak=2.0, decay_days=5,
max_lump_multiple=3.0, buy_mult_winning=0.5` (fixed).

## Expected sign

**Positive on both wealth and Sharpe**, if the short-horizon
overreaction-and-partial-reversal pattern documented by Jegadeesh (1990)
and Lehmann (1990) holds up net of the mechanism's own costs and this
family's weekly (not daily) decision cadence -- the reversal literature is
usually studied at daily-to-weekly holding-period resolution with an
explicit re-entry/exit, whereas this family only ever sizes the fixed
weekly DEPOSIT decision (buy-only, no sells), a much lower-frequency
adaptation, flagged here honestly per family 017's own precedent for the
same caveat. As with every prior timing/banking-mechanic family, this only
reallocates the *timing* of a fixed deposit stream, never total capital
deployed and never leverage, so even a real effect may show a modest
absolute wealth/Sharpe margin over DCA. Per family 010/011/015/016/017's
documented precedent, a sec 4.1 pass driven by a small number of dominant
short-horizon episodes clustering the pooled excess-return series is
exactly what the DSR and placebo circular-shift test (sec 4.3) are
designed to catch, and this family's own results should be read with that
precedent in mind before drawing conclusions from sec 4.1 alone.

## Implementation-check plan (sec 3.2, to be run in the implementation step)

1. `enabled=False` bypass reproduces plain DCA bit-for-bit (units and
   cash).
2. Cash and positions never negative, for the DCA baseline, the primary
   config, and the grid's most aggressive corner
   (`streak_threshold=2, buy_mult_streak=2.0, decay_days=10,
   max_lump_multiple=3.0` -- the lowest trigger threshold (fires most
   often), longest decay window (elevated state persists longest), and
   highest multiplier/ceiling, i.e. the config expected to spend cash
   fastest/hardest).
3. Total capital deployed never exceeds cumulative deposits + interest,
   verified via the principled "never invest" ceiling-bound method
   (`state/bugfix_log.md`'s family-021 fix), for the primary config and
   the aggressive corner.
4. No-lookahead: perturbing all data after day `t` leaves every order
   on/before `t` unchanged, checked at two spot-check points deep into
   the development sample (well before 2020-01-01).
5. Point-in-time macro: N/A -- no macro/alternative data is used at all
   (the streak signal is computed purely from the asset's own OHLC,
   already point-in-time by construction), documented explicitly rather
   than silently skipped, matching every prior price-only-signal family's
   "N/A" entry for this check.

## Pre-grid non-degeneracy check plan (to be run before the grid is trusted)

Before any grid backtest, the primary configuration's elevated-state and
reduced-state frequency will be computed against development-window data
for all 5 core assets (causal, using only data through each day's own
close), and the run aborts if any asset's elevated OR reduced fraction
falls outside a broad `(1%, 60%)` sanity band -- a 3-consecutive-day
streak trigger with a 5-day decay window is expected, by construction, to
fire a non-trivial and roughly comparable share of days on both legs for
any asset with typical day-to-day noise, following family 017's own
non-degeneracy-band precedent for a short-horizon signal.
