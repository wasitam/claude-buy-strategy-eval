# Family 028: 50/200-day moving-average crossover regime tilt ("golden cross" / "death cross")

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Brock, W., Lakonishok, J. and LeBaron, B. (1992), *Simple Technical
Trading Rules and the Stochastic Properties of Stock Returns*, Journal of
Finance 47(5), 1731-1764 — the classic academic study of moving-average
crossover rules (they test variable-length and fixed-length short/long MA
crossovers, e.g. 1-50, 1-150, 5-150, 1-200 day pairs, on the Dow Jones
1897-1986) and find the buy signals following a crossover earn higher and
less volatile returns than sell signals, a result that survived their own
bootstrap re-sampling. The specific 50-day/200-day pair (the "golden
cross" when the 50-day crosses above the 200-day, "death cross" when it
crosses below) is the most widely cited and followed version of this rule
in subsequent practitioner and financial-press use, and is the version
named in seed queue item #28. Seed queue item #28 (idea list, added per
family 026/027's precedent of adding replacement ideas): "50/200-day
moving-average crossover regime tilt ('golden cross'/'death cross')."

## Mechanism ("why would this work, and who is on the other side?")

A 50-day SMA crossing above a 200-day SMA (golden cross) means the
medium-term average price has recently moved above the long-term average
price with enough persistence to flip the ordering of the two averages —
a smoothed, lagging confirmation that a broad uptrend has taken hold
relative to the trailing year of price history (and the reverse for a
death cross). Brock/Lakonishok/LeBaron's own finding, and the subsequent
practitioner literature, is that returns following a golden cross have
historically been higher and less volatile than returns following a
death cross, plausibly because (a) trend-following flows (CTAs,
momentum funds, and retail traders who explicitly watch this exact
indicator) mechanically reinforce the regime once it is visibly
established, and (b) the crossover is a genuinely lagging, smoothed
signal, so it tends to catch the *middle* of sustained trends rather
than tops or bottoms, which is precisely when trend-following has
historically worked best in the time-series-momentum literature (Moskowitz,
Ooi & Pedersen 2012 — already the basis for family 005 in this loop). A
tilt rule that increases buy size in a confirmed golden-cross regime and
reduces it in a confirmed death-cross regime is a bet that this
historically documented asymmetry is real and persists at a magnitude
that survives transaction costs and this loop's robustness bar. The
"other side" of this trade is whoever is willing to sell into a
strengthening uptrend or buy into a weakening one — value/contrarian
investors, market-makers absorbing trend-follower order flow, and anyone
who believes (correctly, in many periods) that by the time a 200-day
lagging average confirms a trend, much of the move is already priced in.
A known risk to the mechanism, stated honestly before any backtest:
golden/death crosses are a **famous, heavily-followed** signal — if
their historical edge was ever real, it is one of the most likely trend
signals to have been arbitraged away by widespread mechanical following,
and the signal is also well known for generating costly whipsaws in
sideways/choppy markets (a well-documented real-world problem this
family's persistence-confirmation parameter is designed to partially
address, not eliminate).

## Category

**Trend / time-series momentum exit** (research-loop-plan-v3.md sec 4.5's
category list; matches family 001's and family 005's category label,
since this is a trend-following mechanism operating on regime tilts to
deposit sizing, not a rotation, valuation, or vol-targeting rule).

## Rigorous distinction from family 001 (10-month/200-day trend exit)

Family 001's signal is **price level relative to a single 200ish-day
SMA** (`close_t > SMA_210(close)_t`) — a binary in-market/out-of-market
test comparing *today's price* against *one* smoothed trailing average.
Its action is binary: invest the full weekly deposit while price is above
the average, park it entirely in cash while below (with an optional
sell-on-exit variant). This family's signal is the **relationship
between two different moving averages of price** (`SMA_50_t` vs.
`SMA_200_t`) — price itself never directly enters the signal test at
all; the comparison is medium-term-average-vs-long-term-average, not
price-vs-one-average. These are mathematically and economically distinct
constructions: family 001's signal can be above/below its average while
this family's two averages are in either crossover state (e.g. price can
be above its 200-day SMA while the 50-day SMA is still below the 200-day
SMA, shortly after a sharp rally off a bottom — a common empirical
pattern, since the 50-day reacts faster to a rebound than the 200-day
does, so the two signals frequently disagree in exactly the transition
periods where the distinction matters most). This family's action is
also different: a **continuous buy-size tilt** (multiply the weekly
deposit by `bull_mult` or `bear_mult`), never a binary all-in/all-out
switch, and every dollar routed to cash under a bearish tilt is banked
and later available as a capped catch-up lump (the same reserve mechanic
family 003/005 use), whereas family 001's out-of-market cash is not
capped or explicitly recycled as a lump-sum catch-up feature. A single
moving average vs. two moving averages, and a binary exit vs. a
continuous tilt with banked catch-up, are both independently sufficient
grounds for distinctness; this family has both.

## Rigorous distinction from family 005 (time-series momentum sizing)

Family 005's signal is the **sign of the asset's own trailing total
return** over a lookback window (`close[t-skip]/close[t-skip-lookback] -
1`), skipping the most recent month per the standard TSMOM convention —
a point-to-point return comparison between two specific historical
prices, with no moving average anywhere in its construction. This
family's signal is a **relationship between two moving averages**, which
is a fundamentally different statistic: a moving average smooths an
entire trailing window of daily closes, so the crossover signal reacts
to the *shape* and *persistence* of the price path over both windows
simultaneously, not just the two endpoint prices a trailing-return
calculation uses. The two signals can and do disagree: a sharp V-shaped
recovery can flip trailing 12-month total return positive (dominated by
the recent sharp rally) well before the slower 50-day SMA has crossed
back above the 200-day SMA (which requires the *average* of the last 50
days, not just the most recent move, to clear the *average* of the last
200 days) — moving-average crossovers are structurally slower and more
lagged than a point-to-point trailing-return signal by construction, not
merely by parameter-tuning coincidence. This is exactly the distinction
the task's brief requires ("sign of trailing 12-month total return... not
a moving-average relationship at all") — confirmed here by construction,
not merely asserted: family 005's `compute_signal` never computes a
rolling mean of price anywhere in its code path
(`src/backtest/v3/strategies/tsmom_sizing.py`), while this family's
signal is entirely built from two rolling means.

## Distinction from v1's closed-list Signal B ("trend-stretch")

Checked directly against `btc-gold-silver-backtest-spec.md` sec 3.2 (the
governing spec, since research-loop-plan-v3.md sec 7.2 references it only
by name): v1 Signal B is `distance[t] = (close[t] - MA_40w[t]) /
ATR_14w[t]` — **price minus a single 40-week (~200-day) moving average**,
normalized by ATR and converted to a **percentile-of-own-trailing-
distribution** threshold, triggering a buy/sell(trim) when that
normalized distance ranks in the bottom/top `p%` of its own trailing
history. This is the same family of construction as family 001 (a single
moving average, compared against price, not against a second moving
average) with an ATR-normalized percentile threshold layered on top,
and it trims/sells existing holdings on an extreme reading rather than
tilting deposit size on a persistent regime. It shares no structural
element with this family's dual-moving-average crossover: no second
moving average, no crossover/regime concept, no persistence-confirmation
filter, and a percentile-of-own-distribution decision rule rather than a
levels-based crossover test. Not a re-test on any reading of sec 7.2.

## Re-test question against sec 7.2's closed list generally

Reviewed the full sec 7.2 closed list: v1 Signal A (ATR shock, unrelated
— a normalized-move shock detector, no moving average at all), v2
SmartDCA (rho x m_max valuation-anchored sizing, unrelated), v2 ADCA
B1/B2 (macro/asset-native regime switches unrelated to moving averages),
v2 rebalanced portfolios C1-C3 (allocation/rebalancing-frequency rules,
not a timing signal), and v2.1 Strategy D's R1-R4/Combo (Fed-funds
level, DGS2-vs-own-trailing-mean, yield-curve-slope-vs-own-trailing-mean,
TIPS real yield, and a meta-ensemble vote over two other pre-existing
strategies — already argued in detail, and distinguished from, family
027's own prereg.md; none of Strategy D's 8 signals involves a
crossover between two price-derived moving averages of the *same
asset*, and Strategy D's `R2b`/`R2b-inv` compare the yield-curve slope
itself against its own trailing mean, a single-series-vs-its-own-average
construction structurally identical in *class* to family 001's
single-MA test, not this family's dual-MA-of-price construction). None
of the closed-list families test a relationship between two differently-
lengthed moving averages of the same asset's own price. This is a
genuinely new construction in this loop, matching the task's framing
exactly.

## Single-asset vs. multi-asset scoping

The moving-average crossover is computed independently per asset from
that asset's own price history (unlike family 027's asset-agnostic macro
signal), matching the precedent set by families 001/003/005/014/017/020/
021/023/026 (a per-asset internal price/volume-derived signal gets
tested on all 5 core assets under sec 4.1's standard >=3/5 rule). Assessed
as a **single-asset family across all 5 core assets**, independently per
asset, using `engine.py`.

## Exact rules

Computed at each trading day `t`'s close, using only that asset's own
price data through `t` (strictly causal, no cross-asset dependency,
unlike family 027's shared macro signal):

1. **Two simple moving averages of close price**: `SMA_fast_t` (window
   `fast_days`) and `SMA_slow_t` (window `slow_days`), each a plain
   trailing rolling mean of `Close`, `min_periods=window` (NaN, hence "no
   signal yet," before enough history exists).
2. **Raw crossover state**: `bullish_raw_t = SMA_fast_t > SMA_slow_t`
   (golden-cross regime) once both averages exist; before that, defaults
   to `True` (no signal yet -> default to plain-DCA-equivalent behavior,
   matching family 001's and 005's own convention for the same reason).
3. **Persistence/confirmation filter** (reduces whipsaw, the classic
   real-world problem with golden/death crosses explicitly named in the
   task): the regime only flips when `bullish_raw` has been continuously
   at its new value for `persistence_days` consecutive trading days (a
   rolling all-equal confirmation window) — same mechanical pattern as
   family 001's `confirm_days` and family 027's `persistence_days`,
   applied here to a crossover-state boolean instead of a price-vs-SMA
   boolean or a macro-threshold boolean.
4. **Weekly decision (week-end days only), no sells ever** (matching
   family 005's own precedent for a sizing-tilt family — a pure buy-size
   tilt rule, never a rule that liquidates existing units, staying within
   the plan's no-leverage/no-shorting constraint by construction):
   `target_buy_usd = weekly_deposit * (bull_mult if confirmed_bullish_t
   else bear_mult)`. The engine's own cash cap (sec 3.2) enforces
   `buy_usd <= cash`, so a below-1x week (death-cross regime, `bear_mult
   < 1`) simply banks the shortfall as cash (earning IRX) until a later
   above-1x week (golden-cross regime) can spend it, exactly family
   005's `make_tsmom_decider` mechanic — never leverage or borrowing.
5. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the crossover computation entirely and sets the
   multiplier to `1.0` for every day, reproducing plain DCA bit-for-bit —
   same pattern as every prior v3 family's disable path.

## Pre-grid sanity checks required before the grid is trusted (per the task)

1. **PRIMARY_CONFIG membership**: verified both programmatically
   (`assert PRIMARY_CONFIG in grid_configs()`) and via an explicit
   module-import-time assertion in
   `src/backtest/v3/strategies/ma_crossover_regime.py`, per family 021's
   lesson (`state/bugfix_log.md`).
2. **Known-episode spot-check**: the raw (`persistence_days=0`) 50/200
   crossover on SP500 must register golden crosses at dates consistent
   with well-documented historical SP500 golden crosses. The task names
   2009, 2016 and 2020 as examples; 2020's crossing (2020-07-24, public
   record) falls inside the **sealed holdout period** (2020+), so
   checking it here — before any finalist has been identified or the
   holdout properly opened per sec 5.2 — would itself be an improper
   holdout look. The check instead spot-checks the two 2009/2016 dates
   plus 2003-05-14 (the well-documented post-dot-com-bust golden cross),
   all within development data — checked in the run script before any
   backtest result is trusted.
3. **BTC short-history caveat**: BTC's development window (2014-09 to
   2019-12, the plan's own flagged short-history weakness, sec 12) may
   produce a degenerate or near-zero confirmed-crossover count for the
   longer MA-window grid arms (slow_days up to 200 requires ~10 months
   of BTC history just to seed the first SMA reading, leaving a
   comparatively short remaining window for crossovers to occur and
   persist). If this happens on BTC specifically, it will be documented
   honestly as a data-limitation finding, per family 027's precedent —
   not treated as a bug, and not used to justify excluding BTC from the
   sec 4.1 >=3/5 count.

## Data inputs

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only,
  same as every prior family). No macro or external data — this family
  is pure price-derived, so it also carries no publication-lag /
  point-in-time-macro risk at all (a genuine simplicity advantage over
  the loop's recent macro-regime families).

## Parameters (4 tunable, <=5 total)

| Parameter | Grid values | Primary |
|---|---|---|
| `ma_pair` (fast_days, slow_days) | (50,200), (20,100), (50,150) | (50, 200) |
| `persistence_days` | 0, 5, 10 | 5 |
| `bull_mult` | 1.25, 1.5 | 1.5 |
| `bear_mult` | 0.5, 0.75 | 0.5 |

`ma_pair` is treated as one categorical tunable parameter (three
literature-motivated pairs, all sharing the golden/death-cross
MECHANISM — a short-vs-long MA crossover — rather than drifting into an
unrelated family; per the task's explicit instruction to "keep to the
golden/death cross mechanism, don't drift into being a different
family," fast is always materially shorter than slow and both remain in
the "medium-term vs. long-term trend" range, never e.g. a 5-day/20-day
pair that would be a short-term/noise-following construction instead).
`max_lump_multiple` is fixed at **6** for every grid config and the
primary (not varied in the grid), matching family 011's and 027's own
convention ("headroom essentially never binds"). This keeps the family
at 4 *tunable* (grid-varied) parameters, comfortably under the plan's <=5
ceiling.

`(50, 200)` is primary because it is literally the textbook golden-cross/
death-cross definition (the version named in the task and the most
widely cited in both the academic literature — Brock/Lakonishok/LeBaron's
own 1-200-day variant is the closest of their tested pairs — and the
financial press) — a no-look choice based on convention, not any
development-data result. `persistence_days=5` (one trading week) is
primary as a minimal, literature-motivated whipsaw filter, matching
family 027's own primary choice for an analogous parameter, and directly
addresses the task's named real-world whipsaw concern without requiring
an unrealistically long confirmation window. `bull_mult=1.5,
bear_mult=0.5` are primary as the same symmetric-tilt magnitudes family
005 (the loop's other trend-tilt family) already uses as its own
primary, for direct comparability and because they are round,
literature-unmotivated-but-conventional choices made before any
development-data result, not tuned to this family's own grid.

## Grid

3 (`ma_pair`) x 3 (`persistence_days`) x 2 (`bull_mult`) x 2 (`bear_mult`)
= **36 configurations** (at the <=36 cap).

## Primary configuration

`ma_pair=(50, 200), persistence_days=5, bull_mult=1.5, bear_mult=0.5`
(`max_lump_multiple=6` fixed for all configs).

## Expected sign

**Positive on both wealth and Sharpe, if the golden-cross/death-cross
trend-confirmation asymmetry documented in Brock/Lakonishok/LeBaron
(1992) and the broader trend-following literature is real and persists
at a magnitude that survives this loop's fee/robustness bar** — stated
honestly as the family's central hypothesis, not a certainty. Genuine
risks flagged before any backtest: (1) this is one of the most
famous and widely mechanically-followed trend signals in existence,
raising real concern that any historical edge has been substantially
arbitraged away in-sample, particularly in the more recent (development)
years; (2) the classic whipsaw problem in choppy/sideways markets, which
`persistence_days` only partially mitigates (a genuine limitation, not a
promise the filter eliminates whipsaw losses); (3) like family 005 (the
loop's closest prior trend-tilt family), this mechanism only reallocates
buy-size tilt over a fixed deposit stream (never total capital deployed,
no leverage), so even a real effect may show a modest absolute wealth/
Sharpe margin over DCA; (4) BTC's short development history may produce
a thin or degenerate confirmed-crossover count for some grid arms
(flagged above) — any BTC-dependent result should be read with the
caution the plan's own sec 12 already calls for generally.
