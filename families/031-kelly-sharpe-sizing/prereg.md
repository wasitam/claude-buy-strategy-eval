# Family 031: Kelly-fraction-style trailing-Sharpe sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Kelly, J.L. (1956), "A New Interpretation of Information Rate," *Bell
System Technical Journal* 35(4), 917-926 (the original criterion: size a
repeated bet proportional to `edge / odds`, i.e. proportional to a
risk-adjusted edge, not to edge or risk alone). Thorp, E.O. (2006), "The
Kelly Criterion in Blackjack, Sports Betting, and the Stock Market," in
*Handbook of Asset and Liability Management*, and Thorp's earlier
practitioner applications of fractional-Kelly position sizing to public
markets, where the "edge/odds" ratio for a tradable asset is commonly
proxied, in the absence of a true edge estimate, by the asset's own
trailing realized **Sharpe ratio** (mean excess return divided by return
volatility over a recent window) -- a direct, standard finance analogue of
Kelly's `edge/odds` for a continuously-traded asset rather than a discrete
bet. Seed queue idea #31 (`research-loop-plan-v3.md` sec 7.3 / this
iteration's task instruction).

## Mechanism ("why would this work, and who is on the other side?")

The classical Kelly criterion sizes a bet in proportion to `edge / odds`:
more capital when the expected payoff per unit of risk is high, less (or
none) when it is low or negative. For a continuously-traded asset with no
single discrete "bet," the standard practitioner proxy for "current edge
per unit of risk" is the asset's own trailing realized Sharpe ratio: mean
return over a recent window, divided by that same window's realized
volatility. A high trailing Sharpe means the asset has recently delivered
strong returns *relative to how much risk it took to deliver them* --
recent risk-adjusted momentum that a Kelly-style bettor would lean into,
under the (contestable, but literature-motivated) view that risk-adjusted
momentum has some short-to-medium-horizon persistence (the time-series
momentum effect of Moskowitz, Ooi & Pedersen (2012), refined here to a
risk-adjusted rather than raw-return version). A low or negative trailing
Sharpe means recent performance has been poor *relative to* the risk
taken -- exactly the condition under which a risk-averse, edge-sizing
bettor reduces commitment, distinct from merely "vol was high" (which
alone says nothing about whether that vol was compensated) or merely "the
raw return was negative" (which alone says nothing about whether the
asset was simply in a high-vol regime where a modest negative return is
unremarkable noise, or a low-vol regime where the same negative return is
a much stronger signal). The "other side" of this trade is whoever is
willing to sell into an asset with strong recent risk-adjusted performance
(because they have shorter horizons, liquidity needs, or don't
differentiate risk-adjusted from raw momentum) and whoever keeps buying
into an asset with poor recent risk-adjusted performance (anchoring,
sunk-cost, or return-chasing investors who look at raw returns or price
levels rather than a risk-adjusted ratio) -- this family bets that a
DCA-style buyer earmarking incrementally more capital for
recently-risk-adjusted-strong assets, and less for recently-risk-adjusted-
weak ones, beats a constant-size, indifferent buyer net of costs.

**Explicit non-leverage clarification (required by research-loop-plan-v3.md
sec 3.4 / sec 2's "no leverage" rule):** this family borrows Kelly's
*proportional-sizing logic* and its *name* only. It never implements
literal Kelly leverage (which for a genuine edge/odds estimate can call
for position sizes far above 100% of bankroll, financed with borrowing).
Every buy in this family is capped at (a) a fixed multiple of the weekly
deposit (`max_lump_multiple`, a hard ceiling regardless of banked cash)
and (b) the engine's own unconditional cash cap (`buy_usd <= cash`,
`engine.py` sec 3.2), so the strategy can never spend more than it has
banked from actual past deposits plus earned interest -- exactly the same
no-borrowing, no-negative-cash constraint every prior family in this loop
satisfies. This is stated here up front, before any code is written, so
the "Kelly" framing in this family's name and motivation is never
mistaken for literal fractional-Kelly leverage.

## Signal construction: a RATIO of return-to-risk, not either alone (required distinction from families 003, 005, 025, 020)

This family's core, pre-declared design choice is to size buys using the
**trailing Sharpe ratio** -- `S_t = mean(daily log return, trailing
sharpe_window days) / std(daily log return, trailing sharpe_window days)`,
both annualized -- a genuinely different statistic from every prior
sizing family that used a return signal OR a volatility signal in
isolation, or a spread between two different volatility measures, or a
price-level distance:

| Family | Signal | What it uses | What it discards |
|---|---|---|---|
| **003 (vol-managed sizing)** | `sigma_ref / sigma_recent` | Volatility (recent vs. reference) **only** | The sign or magnitude of the trailing RETURN plays no role at all: a recent, sharply-*positive*-drift high-vol regime and a recent, sharply-*negative*-drift high-vol regime get the identical (low) multiplier, since only the vol ratio is read. |
| **005 (tsmom sizing)** | `sign(trailing total return)` | The **sign** of the trailing RETURN only | Volatility plays no role at all: a small positive return achieved with very low vol (a strong, "quiet" edge) and the same small positive return achieved with very high vol (a weak, "noisy" edge, arguably no edge once risk-adjusted) get the identical multiplier, since only the sign of the raw return is read -- magnitude of either return or vol is discarded. |
| **025 (VRP sizing)** | `implied_vol - realized_vol` (a spread between two DIFFERENT volatility measures) | Two volatility measures against each other | No return/momentum information enters the signal at all -- it is a pure volatility-vs-volatility spread, structurally unrelated to a return-to-risk ratio. |
| **020 (52-week-high tilt)** | Price level relative to its own trailing 52-week high | Price-LEVEL proximity to a reference point | Neither the recent RETURN's magnitude nor the recent VOLATILITY enters at all -- it is a pure positional/anchoring statistic (how close is today's price to a historical reference price), not a return or risk statistic of any kind. |
| **031 (this family)** | `mean(trailing return) / std(trailing return)` | **Both** the trailing RETURN and the trailing VOLATILITY, combined as a ratio | Nothing pre-combined away: the ratio's numerator (families 005's territory) and denominator (family 003's/025's territory, restricted to realized vol) are both explicitly present and jointly determine the reading. |

**This is not simply "003 and 005 averaged together."** A ratio and a
convex combination of two separately-computed multipliers behave
completely differently on realistic data, and the concrete numeric
contrast below (computed on real development data, not hypothetical
numbers, per this iteration's task instruction) demonstrates why:

### Concrete numeric contrast (real development data, 60-trading-day trailing window, annualized)

| Asset & date | Trailing mean return (ann.) | Trailing vol (ann.) | Trailing Sharpe `S_t` |
|---|---|---|---|
| **BTC, 2018-01-22** | **+129.1%** | **120.9%** | **1.0677** |
| **SP500, 1993-12-20** | **+7.48%** | **7.00%** | **1.0678** |

These two (asset, date) pairs have an **essentially identical trailing
Sharpe** (1.0677 vs. 1.0678, a difference of 0.0001) -- this family's
signal would size both days' buys almost identically (same percentile
rank, same multiplier). But:
- **Family 003** (inverse-vol sizing) reads BTC's 120.9% trailing vol as
  roughly **17x** SP500's 7.00% trailing vol on that day, and would size
  BTC's buy far more conservatively than SP500's on this basis ALONE --
  it has no way to "know" that BTC's return was also proportionally huge,
  because it never looks at the return at all.
- **Family 005** (sign-of-return sizing) reads both days identically as
  "positive trailing return" (a binary bucket), collapsing BTC's +129.1%
  and SP500's +7.48% -- a 17x difference in the magnitude of the
  underlying edge -- into the exact same multiplier, because it never
  looks at volatility (or return magnitude) at all.
- **Family 031** (this family) reads both days as the same *quality* of
  risk-adjusted edge (comparable Sharpe), which is the economically
  coherent Kelly-style reading: BTC's much larger return was exactly
  proportionally compensated by its much larger risk, so a risk-adjusted
  bettor should treat the two opportunities similarly, not treat BTC as
  either "worse" (family 003's read, driven by vol alone) or
  "indistinguishable in quality from any other positive-return day"
  (family 005's read, which cannot tell a strong risk-adjusted edge from
  a weak one as long as both are merely positive).

A second real contrast, in the opposite direction, using a second window
(also 60 trading days) makes the point that **a near-identical trailing
Sharpe can also mask very different family-003/005 readings on the
NEGATIVE side**:

| Asset & date | Trailing mean return (ann.) | Trailing vol (ann.) | Trailing Sharpe `S_t` |
|---|---|---|---|
| **BTC, 2018-02-03** | **-109.8%** | **123.2%** | **-0.8911** |
| **GOLD, 2017-11-28** | **-9.56%** | **10.72%** | **-0.8912** |

Again, essentially identical trailing Sharpe (-0.8911 vs. -0.8912). Family
003 would read BTC's 123.2% vol as far more "dangerous" than GOLD's
10.72% and cut BTC's buy multiplier much harder on vol grounds alone,
regardless of the fact that BTC's return was also far more negative in
exact proportion. Family 005 would read both as simply "negative trailing
return," an identical bucket, unable to distinguish a mild, low-vol
losing streak (GOLD) from a violent, high-vol one (BTC) that arguably
represents the *same* relative degree of "recent underperformance per
unit of risk taken." Family 031's ratio construction is the only one of
the three that reads these as the same underlying condition (a
comparably poor recent risk-adjusted edge) -- neither "003 alone" nor
"005 alone" nor a naive average of the two multipliers they would each
independently produce reconstructs this ratio-based reading, since an
average of two heterogeneous multipliers computed by two different
statistics is not the same object as one multiplier computed from the
ratio of the two underlying raw statistics themselves. This is the
concrete sense in which family 031 is a genuine synthesis, not a
recombination of already-computed family-003 and family-005 outputs.

## Distinction from family 025 (VRP sizing) and family 020 (52-week-high tilt)

Already covered in the table above: family 025's signal is a spread
between two DIFFERENT volatility measures (implied minus realized) with
no return/momentum term at all, and family 020's signal is a price-LEVEL
proximity statistic with neither a return-rate nor a volatility term at
all. Neither can be reparameterized into a return/volatility ratio: family
025's signal is undefined (has no return component to vary) if implied
vol data were unavailable, whereas family 031's signal is undefined only
if realized return or vol themselves cannot be computed (i.e., during the
initial warm-up window) -- they measure structurally unrelated things.

## Category

**Sizing / valuation.** Judgment call, explicitly justified: this family's
signal decides how much to buy *of a single asset, from that asset's own
history*, exactly the same use-case as families 003, 005, 014, 017, 020,
023, 026, 028 and 030, all filed under "Sizing / valuation" (family 003
and family 005, whose logic this family synthesizes, are themselves
formally filed as "Volatility targeting" and "Trend / time-series
momentum exit" respectively in sec 7.3/prior prereg.md files -- but that
reflects each of THEIR single-ingredient signals, not a rule that any
Sharpe-flavored signal must inherit one parent's category). Sec 4.5's
category list offers "Volatility targeting" as an alternative, but that
category is reserved, by this loop's own precedent (family 003), for
strategies whose entire signal IS a volatility measure used to target a
level or ratio of realized risk; this family's defining, headline
mechanism is Kelly's edge/odds logic -- an edge (return) signal
*normalized* by risk, not a risk-targeting rule that happens to reference
returns. The output multiplier here is driven as much by the numerator
(momentum/edge, family 005's territory) as the denominator (risk, family
003's territory), and the "Sizing / valuation" category's own precedent
(family 017's RSI2, family 020's 52-week-high, family 030's streak count)
already covers signals that are fundamentally about "is this a favorable
moment to size up or down," which is exactly this family's framing.
**Decision: Sizing / valuation.**

## Single-asset vs. portfolio scoping

Assessed as a **single-asset family across all 5 core assets** under sec
4.1's standard >=3/5 rule, the trailing-Sharpe signal computed
independently per asset from that asset's own daily Close series --
directly following the precedent of families 001/003/005/014/017/020/
021/023/026/028/030 (each asset's own internal signal, no capital ever
rotating between assets).

## Data inputs and reachability (gate step)

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only,
  same as every prior family). **No external data dependency at all** --
  the trailing-Sharpe signal is computed purely from the asset's own
  `Close` series (daily log returns, their trailing mean and trailing
  standard deviation), so there is no macro/alternative-data reachability
  question and no point-in-time / ALFRED-vintage concern.

## Gate: not a re-test of sec 7.2's closed list

Sec 7.2's closed list has no trailing-Sharpe-ratio or return-to-vol-ratio
signal anywhere in it (v1 Signal A is a single-day ATR/range-expansion
percentile; v1 Signal B is a trend-stretch/distance rule; v2 SmartDCA is
a moving-average-distance rule; v2 ADCA is a macro-driven rule; v2.1's
Strategy D variants are rate-regime rules). Not a re-test of any of them.

## Complexity ceiling check (sec 3.4)

- Rules fit on one page, computed from end-of-day data only. PASS.
- At most one order per asset per trading day (a single buy order, never
  a sell). PASS.
- At most 5 tunable parameters (4 grid-varied + 2 fixed constants,
  `max_mult` and `max_lump_multiple`, the same "N tunable + fixed
  constant(s)" pattern families 015/016/017/030 used). PASS.
- All data free and public, already-loaded OHLC only, no new source.
  PASS.
- Grid: 36 configurations (<=36 cap), one primary configuration declared
  below before any testing. PASS.

## Exact rules

Computed at each trading day's close `t`, using only data available by
that close (strictly causal, no lookahead).

1. **Daily log return**: `r_t = ln(Close_t / Close_{t-1})` (`r_0 = 0` by
   convention, matching every prior family's warm-up convention).
2. **Trailing Sharpe signal**: over the trailing `sharpe_window` trading
   days ending at `t` (inclusive), compute the annualized mean and
   annualized standard deviation of `r`, and:
   `S_t = mean(r; trailing sharpe_window) * 252 / (std(r; trailing sharpe_window, ddof=1) * sqrt(252))`.
   `S_t` is undefined (treated as "no signal yet," default multiplier
   1.0) until `sharpe_window` days of history exist, or if the trailing
   standard deviation is exactly zero.
3. **Point-in-time percentile rank (the "elevated/depressed" threshold, made continuous and adaptive rather than a fixed global cutoff)**:
   for each `t`, compute `pctile_t` = the fraction of days in the trailing
   `pctile_lookback` window ending at `t` (inclusive) whose `S_t'` value is
   `<= S_t` (a causal, point-in-time, adaptive rolling percentile rank --
   never uses any future `S` value, and never uses a fixed global
   threshold calibrated on the whole sample, which would leak
   development-period-wide information into an early-period decision).
   `pctile_t in [0, 1]`; undefined (default 0.5, i.e. "neutral") until
   `pctile_lookback` days of `S` history exist.
4. **Continuous Kelly-style multiplier** (no discrete threshold buckets --
   the multiplier scales continuously with how extreme today's trailing
   Sharpe is relative to its own recent history, per this iteration's
   task instruction):
   `m_t = clip(1 + k * (2 * pctile_t - 1), min_mult, max_mult)`
   -- at `pctile_t = 1.0` (today's trailing Sharpe is the highest in the
   lookback window), `m_t = clip(1 + k, ..., max_mult)`; at
   `pctile_t = 0.0` (today's trailing Sharpe is the lowest), `m_t =
   clip(1 - k, min_mult, ...)`; at `pctile_t = 0.5` (median), `m_t = 1.0`
   (plain DCA). `max_mult` is **fixed at 2.0** for every grid config and
   the primary (not grid-varied; mirrors family 003's and family 005's
   own `max_mult`/`mult_pos` ceilings of 1.5-2.0, kept fixed here so the
   grid isolates the effect of the tunable parameters below).
5. **Weekly decision (week-end days only, no sells ever, no leverage)**:
   `target_buy_usd = weekly_deposit * m_t`, capped at
   `max_lump_multiple * weekly_deposit` (a hard safety ceiling on any
   single lump buy even if a large cash reserve has banked up --
   **fixed at 3.0** for every grid config and the primary, matching
   family 030's and family 028's own fixed ceiling value), then capped
   again at available cash (`min(cash, ...)`, the engine's own
   no-leverage, no-borrowing cap -- see the explicit no-leverage
   clarification above). A below-1.0-multiplier week (low trailing
   Sharpe) banks the shortfall as cash (earning IRX), available to fund
   a future above-1.0-multiplier week -- the same reserve mechanism
   families 003/005/015/016/017/030 all use, never leverage or
   borrowing.
6. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the Sharpe/percentile computation entirely and
   buys 100% of that week's cash on every week-end day (0 otherwise) --
   reproduces plain DCA bit-for-bit, the same disable-path pattern every
   prior v3 family uses.

## Parameters (4 tunable + 2 fixed, <=5 tunable per sec 3.4)

| Parameter | Grid values | Primary |
|---|---|---|
| `sharpe_window` (trailing window for the mean/vol computation, trading days) | 40, 60, 90 | 60 |
| `pctile_lookback` (trailing window over which today's Sharpe is percentile-ranked, trading days; ~2yr and ~3yr) | 504, 756 | 504 |
| `k` (sensitivity: how strongly the multiplier moves away from 1.0 as the percentile rank moves away from 0.5) | 0.5, 1.0, 1.5 | 1.0 |
| `min_mult` (lower clip bound on the multiplier) | 0.25, 0.5 | 0.5 |

`max_mult` is fixed at **2.0** and `max_lump_multiple` is fixed at **3.0**
for every grid config and the primary (not grid-varied) -- two fixed
safety/ceiling constants, keeping this family at 4 tunable parameters,
at/under the plan's <=5 ceiling (the same "N tunable + fixed constant(s)"
pattern families 015/016/017/030 used, here with two fixed constants
instead of one since both an upside and a lump-size ceiling are needed).

`sharpe_window=60` (about 3 trading months) is primary as the
middle grid value and a standard "quarterly" lookback used widely in the
trailing-Sharpe/vol-targeting literature (also family 003's own
`vol_lookback_days` grid includes 60 as a value). `pctile_lookback=504`
(about 2 trading years) is primary as the shorter, more adaptive of the
two grid values -- a 2-year rolling reference window that can track a
genuine multi-year regime shift without requiring the full multi-decade
SP500 history to fill first, important given BTC's short (~5-year)
development window (per the plan's own flagged BTC caveat, sec 12).
`k=1.0` is primary as the middle grid value, a clean, easily-explained "at
the extremes, the multiplier moves a full 1.0 away from the DCA baseline"
rule. `min_mult=0.5` mirrors family 003's own primary `min_mult=0.5` for
direct comparability across the loop's vol/return-based sizing families.

## Grid

3 (`sharpe_window`) x 2 (`pctile_lookback`) x 3 (`k`) x 2 (`min_mult`) =
**36 configurations** (<=36 cap, at the ceiling).

## Primary configuration

`sharpe_window=60, pctile_lookback=504, k=1.0, min_mult=0.5` (`max_mult=2.0`
and `max_lump_multiple=3.0` fixed for every config, primary included).

## Expected sign

**Positive on both wealth and Sharpe**, if risk-adjusted momentum (as
opposed to raw-return momentum, family 005's already-tested hypothesis,
or inverse-vol alone, family 003's already-tested hypothesis) carries
genuine short-to-medium-horizon persistence net of this mechanism's own
costs and its weekly (not continuous) decision cadence. As with every
prior timing/banking-mechanic family in this loop, this only reallocates
the *timing* of a fixed deposit stream, never total capital deployed and
never leverage (see the explicit no-leverage clarification above), so
even a real effect may show a modest absolute wealth/Sharpe margin over
DCA. Given that families 003 (vol-managed) and 005 (tsmom, sign-only) were
each themselves near-miss/rejected in this loop (003: REJECTED; 005:
NEAR-MISS -- see `state/ledger.csv`), this family's synthesis result
should be read with real skepticism going in: it is entirely possible
that combining two previously underwhelming single-ingredient signals
into a ratio does not "average out" to something stronger, and a rejected
or near-miss outcome here would not be surprising. This is flagged
honestly, before any backtest is run, per the same precedent the loop's
other syntheses/mirror-image families (e.g. family 030 vs. 017) have
followed.

## Implementation-check plan (sec 3.2, to be run in the implementation step)

1. `enabled=False` bypass reproduces plain DCA bit-for-bit (units and
   cash).
2. Cash and positions never negative, for the DCA baseline, the primary
   config, and the grid's most aggressive corner (`sharpe_window=40,
   pctile_lookback=504, k=1.5, min_mult=0.25` -- the shortest, most
   reactive Sharpe window, most extreme sensitivity, and lowest floor,
   i.e. the config expected to swing the multiplier hardest and most
   often).
3. Total capital deployed never exceeds cumulative deposits + interest,
   verified via the principled "never invest" ceiling-bound method
   (`state/bugfix_log.md`'s family-021 fix), for the primary config and
   the aggressive corner.
4. No-lookahead: perturbing all data after day `t` leaves every order
   on/before `t` unchanged, checked at two spot-check points deep into
   the development sample (well before 2020-01-01).
5. Point-in-time macro: N/A -- no macro/alternative data is used at all
   (the signal is computed purely from the asset's own OHLC, already
   point-in-time by construction; the percentile rank is itself
   explicitly constructed to be causal/rolling rather than a
   whole-sample-calibrated fixed threshold, per rule 3 above).

## Pre-grid non-degeneracy check plan (to be run before the grid is trusted)

Before any grid backtest, the primary configuration's elevated
(`m_t > 1.0`) and depressed (`m_t < 1.0`) day-fractions will be computed
against development-window data for all 5 core assets (causal, using only
data through each day's own close). Because the multiplier is driven by a
percentile RANK (by construction close to uniformly distributed over
`[0, 1]` once the rolling window is full), both fractions are expected to
land close to 50% on every asset once `pctile_lookback` days of history
exist -- a very different, and by-construction far less likely to be
degenerate, non-degeneracy profile than the discrete-threshold families
(017/030) that could plausibly trigger on a small minority of days. The
run aborts if either fraction falls outside a broad `(20%, 80%)` band on
any asset, or if fewer than `pctile_lookback` days of history exist for
any asset's development window (a hard prerequisite check on BTC in
particular, given its short ~5-year development sample) -- and the run
will also report the concrete numeric contrast (real BTC/GOLD/SILVER/
SP500/OIL trailing-Sharpe values on real dates) demonstrating the signal
is not secretly redundant with family 003 or family 005, per this
iteration's task instruction, before the grid is trusted.
