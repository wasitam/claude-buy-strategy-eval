# Family 026: Intraday/overnight return decomposition sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Lou, D., Polk, C. & Skouras, S. (2019), "A Tug of War: Overnight Versus
Intraday Expected Returns," *Journal of Financial Economics* 134(1),
192-213. LPS decompose each day's total return into an **intraday**
(open-to-close) leg and an **overnight** (close-to-open) leg and document
that the two legs have sharply different time-series and cross-sectional
properties: (1) a large, persistent share of many assets' long-run price
appreciation accrues **overnight**, while the intraday leg is comparatively
flat or even negative on average over long samples; (2) the overnight leg
exhibits **positive autocorrelation / continuation** at multiple horizons
(a stock or index whose overnight returns have recently been strong tends
to keep earning strong overnight returns), which LPS attribute to a
persistent, informed/fundamental component of order flow that
concentrates in the close-to-open window (e.g., overnight
information processing, institutional order-placement patterns); (3) the
intraday leg is comparatively noisier and more exposed to short-horizon
mean-reversion (retail/sentiment-driven order flow that gets partially
unwound within the same session). LPS frame this as a "tug of war" between
two return-generating clienteles operating on the same asset in different
parts of the trading day. Seed research queue idea #26
(research-loop-plan-v3.md sec 7.3 addendum, this iteration's task):
"Intraday/overnight return decomposition sizing."

## Explicit interpretation of the source (required: this is a less commonly
known effect than most ideas tested so far in this loop)

LPS's core empirical results are predominantly **cross-sectional** (sorting
many individual stocks on their own trailing overnight-minus-intraday
characteristic, then looking at return spreads between the resulting
portfolios). This loop tests **single, whole-asset time series** (SP500
index, gold, silver, BTC, oil), not a cross-section of securities, so this
family is necessarily an **adaptation** of the LPS finding to a
single-asset time-series setting, not a literal replication of their
cross-sectional sort. The adaptation we implement, stated explicitly:

- We take LPS's **continuation/persistence finding on the overnight leg**
  as the operative mechanism: an asset whose own trailing overnight
  (close-to-open) returns have recently been running unusually strong,
  relative to that asset's own history, is more likely (per LPS) to keep
  earning strong overnight returns going forward than an asset whose
  recent overnight returns have been weak or negative. This is a
  **direct/momentum sign on the overnight leg's own trailing level**, not
  a contrarian one.
- We do **not** trade a standalone momentum or reversal bet on the
  intraday leg alone. LPS document the intraday leg as noisier and more
  exposed to short-horizon reversal, which makes a standalone intraday
  momentum signal a weaker, less literature-grounded bet. Instead, the
  intraday leg's trailing cumulative return is used only as the
  **relative-strength denominator**: the signal this family sizes buys on
  is the **spread** between trailing cumulative overnight and trailing
  cumulative intraday returns, i.e. "how much of this asset's recent
  cumulative gain has come from the (persistent, per LPS) overnight leg
  relative to the (noisier, per LPS) intraday leg." A spread that is
  unusually elevated (overnight dominating intraday by an unusually wide
  margin, relative to its OWN trailing history) is this family's buy-more
  trigger; a spread that is unusually compressed or negative (intraday
  dominating, overnight weak or negative) is the buy-less trigger. This
  mirrors the same "rank a spread in its own trailing percentile"
  construction already used successfully (as a design pattern, independent
  of its own sec 4 outcome) by family 025's `VRP_t = IV_t - RV_t`, applied
  here to a genuinely different pair of legs (overnight vs. intraday
  return components of the SAME asset's own OHLC, not implied vs. realized
  volatility).
- **Sign, stated plainly:** elevated overnight-vs-intraday spread => buy
  MORE (direct/momentum bet on the persistent overnight component, per
  LPS's continuation finding). Compressed/negative spread => buy LESS
  (the asset's recent gains, if any, have been intraday-driven, the leg
  LPS document as noisier and more reversal-prone, so we do not chase it
  with extra buying).

## Mechanism ("why would this work, and who is on the other side?")

If a persistent, informed component of expected returns concentrates in
the overnight window (LPS's explanation: information that accumulates
while markets are closed gets impounded disproportionately at the open,
and a structural clientele -- e.g., institutions executing at the close/open
on information or flow that isn't fully arbitraged away intraday --
generates continuation in that leg specifically), then an asset currently
riding a strong overnight-return stretch (relative to its own trailing
intraday performance) is, per LPS, more likely than not to keep doing so
in the near term. Buying more into that stretch is a bet on capturing that
continuation. The "other side" is whoever is on the other end of the
overnight order flow LPS attribute the effect to -- e.g., market makers and
short-horizon intraday traders who are compensated (via the reversal LPS
document intraday) for absorbing/unwinding the flow that piles up
overnight, and who are not positioned to arbitrage away the overnight
continuation itself because doing so would require holding a costly
overnight position through the exact risk (gap risk, information risk)
that generates the premium in the first place.

## Category

**Sizing / valuation** (as specified in this iteration's task and matching
sec 4.5's list) -- a within-asset trailing-return-based sizing rule, not a
volatility measure (unlike family 025's VRP spread) and not a
cross-asset rotation signal.

## Genuinely new data dimension (required: must distinguish from all prior
families, not just a new parameterization of an existing signal)

**This is the first family in this loop to use the intraday/overnight
(Open/Close) return decomposition.** Every prior family that used daily
price data (001, 002, 005, 006, 007, 017, 018, 020, 022, 023, 024) built
its signal from **daily Close-to-Close returns or price levels** alone.
Family 021 (Amihud illiquidity) uses `High`, `Low` and `Volume` alongside
`Close`, but never splits a day's own return into its Open-to-Close and
Close-to-Open pieces -- it uses OHLCV as inputs to a liquidity-ratio
calculation, not as a return decomposition. Family 025 (VRP sizing) uses
Close-derived realized volatility compared against an external implied-vol
series (VIX); it also never touches `Open`. This family is the first to
compute `Open_t` as an economically meaningful decomposition point WITHIN
each trading day's own return -- a data dimension (the split point between
the overnight and intraday legs of a single day's return) that has no
analogue in any prior family's signal construction. None of sec 7.2's
closed v1/v2/v2.1 families used this decomposition either (buy-the-dip/
trim-the-spike, SmartDCA, ADCA B1/B2 and the C1-C3 rebalancing sweep, and
Strategy D's rate-regime switch, all listed in sec 7.2, are all built from
daily/weekly Close levels or external macro/rate series, never an
intraday/overnight split).

## Data inputs and reachability (gate step)

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only) --
  specifically `Open` and `Close`, both already present in the cached OHLC
  for all 5 core assets (confirmed at the gate step: `data.py`'s loader
  returns `["Open", "High", "Low", "Close", "Volume"]` for every ticker,
  no new external data source needed, matching this iteration's explicit
  data note).
- No macro, implied-vol or external series of any kind. No point-in-time/
  ALFRED-vintage concern.

## Exact rules

Computed at each trading day's close `t`, using only data available by
that close, and, per this iteration's explicit lookahead caution, **built
only from LAGGED, COMPLETE prior trading days** (day `t` itself is
excluded from the trailing-window sums; see "No-lookahead design" below
for why this is done even though day `t`'s own O/C split is, strictly,
already fully known and legally usable at day `t`'s own close per sec
3.2's decision timing rule).

1. **Daily intraday leg**: `intraday_t = Close_t / Open_t - 1`.
2. **Daily overnight leg**: `overnight_t = Open_t / Close_{t-1} - 1`
   (undefined/NaN on the asset's first trading day, which has no prior
   close).
3. **Lagged trailing cumulative sums**, over a trailing window of
   `lookback_days` COMPLETE prior trading days, ending at `t-1` (i.e.
   `intraday_t` and `overnight_t` themselves are NOT included in their own
   day's signal -- both trailing sums are computed on the series shifted
   forward by one day before the rolling window is applied):
   - `cum_overnight_t = sum(overnight_{t-lookback_days} .. overnight_{t-1})`
   - `cum_intraday_t = sum(intraday_{t-lookback_days} .. intraday_{t-1})`
   - `min_periods = lookback_days` (both legs); NaN until enough lagged
     history exists.
4. **Spread**: `spread_t = cum_overnight_t - cum_intraday_t` (in return
   units; can be negative).
5. **Trailing percentile rank of the SPREAD itself** (not of either leg
   alone): `percentile_t` = the percentage of the trailing
   `pctile_lookback`-day window of `spread` values (through and including
   `spread_t`, which is itself already fully lagged per step 3) that are
   `<=` `spread_t`. `min_periods = pctile_lookback`.
6. **Regime flags**:
   - `elevated_t = percentile_t >= elevated_pct` (overnight leg has been
     dominating the asset's own recent cumulative return by an unusually
     wide margin over its own trailing intraday leg -- buy MORE).
   - `compressed_t = percentile_t <= compressed_pct` (intraday leg has
     been dominating, or overnight has been outright negative relative to
     intraday -- buy LESS).
   - Otherwise, `normal_t`.
   - Before `percentile_t` exists (warm-up): defaults to `normal_t`
     (calm-fraction leg), matching the established warm-up convention
     (families 001/011/015/016/025).
7. **Weekly decision (week-end days only, no sells ever, no leverage)**:
   - **Elevated (`elevated_t`):** buy `min(cash, buy_multiplier *
     weekly_deposit, max_buy_multiple * weekly_deposit)`.
   - **Compressed (`compressed_t`):** buy `compressed_fraction *
     weekly_deposit` (fixed at 0.5, same fixed rate family 025 used for
     its own compressed leg -- buy noticeably less, not zero, to stay a
     reallocation-of-timing rule).
   - **Normal (neither):** buy `calm_fraction * weekly_deposit` (fixed at
     0.9, matching families 016/025's calm-week banking rate). The
     remainder in both the compressed and normal cases is banked as cash
     (earning IRX).
   - Genuine reallocation of the SAME total deposit stream over time,
     never leverage: cash never goes negative (engine's own cap, sec 3.2)
     and no capital beyond deposits + interest is ever spent.
8. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the decomposition/percentile computation entirely
   and buys 100% of that week's cash on every week-end day (0 otherwise) --
   reproduces plain DCA bit-for-bit.

### No-lookahead design (critical, per this iteration's explicit caution)

Sec 3.2's engine convention makes day `t`'s own full OHLC (hence its own
`intraday_t` and `overnight_t`) legally available to the decision computed
at day `t`'s own close -- there is no engine-level lookahead in using it.
However, this family's signal is explicitly meant to reflect **"recent
trailing history"** (a momentum/continuation bet), and including day `t`'s
own not-yet-fully-"settled-into-a-trend" observation in its own trailing
window blurs the distinction between "a signal built from history" and "a
signal partly built from the value being traded on." To keep the
construction unambiguous and conservative, and per this iteration's
explicit instruction, **both trailing sums (`cum_overnight_t` and
`cum_intraday_t`) are computed by shifting the daily leg series forward by
one day before the rolling window is applied** -- so `spread_t` and hence
`elevated_t`/`compressed_t` use ONLY complete days `t-lookback_days`
through `t-1`, never day `t`'s own leg values. This is verified
mechanically (not just by code inspection) via the sec 3.2 no-lookahead
perturbation test in the implementation-check step: perturbing all OHLC
data strictly after day `t_check`, including day `t_check`'s own Open (a
component of both day `t_check`'s `intraday` value and day `t_check+1`'s
`overnight` value), must leave every order generated on or before
`t_check` unchanged. This is a strictly stronger test than the standard
form used by prior families, because it specifically exercises the
Open-field lookahead risk this iteration flagged: the perturbation touches
`Open_{t_check+1}`, `Close_{t_check}` is untouched (day `t_check` and
everything before it, including `Open_{t_check}`, is left alone), and the
test confirms this does not leak into day `t_check`'s own order.

## Single-asset scoping

Assessed as a **single-asset family across all 5 core assets** under sec
4.1's standard >=3/5 rule, per-asset internal signal (no capital ever
moves between assets), same precedent as families 001/003/005/014/017/
020/021/023/025. Each asset's own OHLC drives its own decomposition
independently.

## Parameters (4 tunable, <=5)

| Parameter | Grid values | Primary |
|---|---|---|
| `lookback_days` (trailing window, COMPLETE lagged trading days, for both cumulative legs) | 10, 20, 40 | 20 |
| `elevated_pct` (percentile threshold on the spread for "elevated") | 80, 90 | 90 |
| `compressed_pct` (percentile threshold on the spread for "compressed") | 10, 20 | 10 |
| `buy_multiplier` (multiple of weekly deposit bought when elevated) | 1.5, 2.0, 3.0 | 2.0 |

Fixed (not grid-varied, do not count against the <=5 tunable-parameter
ceiling): `pctile_lookback = 252` (one trading year, the trailing window
over which the spread's own percentile is ranked -- matches families
016/025's "trailing year, no-look convention" choice, fixed before any
backtest), `max_buy_multiple = 4.0` (hard ceiling on any elevated week's
buy relative to the normal deposit, identical role to families 016/025's
fixed constant), `compressed_fraction = 0.5` and `calm_fraction = 0.9`
(fixed banking rates, matching family 025's own fixed values for the same
comparability reasons).

`lookback_days=20` (roughly one trading month) is primary as the middle
value of the 3-point grid -- a short-to-medium trailing window that is
long enough to average out single-day noise in the O/C split but short
enough to reflect "recent" continuation per LPS's own short-to-medium
horizon framing, chosen before any backtest, not fit to this signal.
`elevated_pct=90` / `compressed_pct=10` are primary as the symmetric,
literal top-decile/bottom-decile reading of "genuinely elevated" vs.
"genuinely compressed," mirroring families 016/025's own primary
threshold choices. `buy_multiplier=2.0` is primary for the same reason it
was primary in families 016/025: a clean, easily explained "buy twice as
much," the middle of the 3-point grid, fixed before any backtest.

## Grid

3 (`lookback_days`) x 2 (`elevated_pct`) x 2 (`compressed_pct`) x 3
(`buy_multiplier`) = **36 configurations** (at the <=36 cap).

## Primary configuration

`lookback_days=20, elevated_pct=90, compressed_pct=10, buy_multiplier=2.0`
(`pctile_lookback=252`, `max_buy_multiple=4.0`, `compressed_fraction=0.5`,
`calm_fraction=0.9` fixed for all configs).

## Expected sign

**Positive on both wealth and Sharpe**, if LPS's overnight-continuation
finding, adapted to a single-asset time series as described above, holds
up net of the mechanism's own costs: buying more specifically when the
asset's own recent cumulative gains have been unusually overnight-driven
(relative to its own intraday leg and its own trailing history) should
capture a genuine continuation effect in the persistent overnight
component. As with every prior timing/banking-mechanic family in this
loop, this only reallocates the *timing* of a fixed deposit stream, never
total capital deployed and never leverage. Weakest expected conviction for
the non-equity-index assets (gold, silver, oil, and especially BTC, which
trades 24/7 and so has no economically meaningful "overnight, market
closed" window in the same sense LPS's equity-market-hours framing
assumes -- flagged explicitly as a genuine limitation, not silently
absorbed: BTC's `overnight_t` and `intraday_t` legs are still well-defined
arithmetically from its own OHLC bar boundaries, but the LPS mechanism's
economic story, built on exchange closure and overnight information
accumulation, does not obviously transfer to a market that never closes).
Per family 016's own documented precedent, a sec 4.1 pass driven by a
small number of dominant historical episodes is exactly what sec 4.3's
placebo circular-shift and bootstrap tests are designed to catch, and this
family's results should be read with that precedent in mind before
drawing conclusions from sec 4.1 alone.

## Complexity ceiling check (sec 3.4)

- Rules fit on one page, computed from end-of-day OHLC data. PASS.
- At most one order per asset per trading day (one weekly buy). PASS.
- 4 tunable parameters (<=5). PASS.
- Data: cached OHLC only, already reachable, no new source. PASS.
- Grid: 36 configurations (<=36), one primary configuration declared above
  before any testing. PASS.

## Not a re-test of sec 7.2's closed list or any prior v3 family

No family in sec 7.2's closed list (v1 buy-the-dip/trim-the-spike,
v2 SmartDCA, v2 ADCA B1/B2, v2 C1-C3 rebalancing, v2.1 Strategy D) used an
intraday/overnight return decomposition -- all are built from Close-level
or external macro/rate data. No prior v3 family (001-025) used it either,
as documented in "Genuinely new data dimension" above. This is confirmed a
new signal, not a re-parameterization.

## Implementation-check plan (sec 3.2, to be run in the implementation step)

1. `enabled=False` bypass reproduces plain DCA bit-for-bit (units and cash).
2. Cash and positions never negative, for the DCA baseline, the primary
   config, and the grid's most aggressive corner (`lookback_days=10,
   elevated_pct=80, compressed_pct=20, buy_multiplier=3.0` -- shortest
   (noisiest) trailing window, loosest elevated/compressed thresholds,
   highest multiplier -- the config expected to trade most aggressively).
3. Total capital deployed never exceeds cumulative deposits + interest
   (primary config and the aggressive corner), via family 021's
   principled "never invest" ceiling-bound method.
4. **No-lookahead** (critical for this family, per this iteration's
   explicit caution): perturbing all OHLC data strictly after day
   `t_check`, including `Open_{t_check+1}` (which enters
   `overnight_{t_check+1}`, the day immediately after the check point),
   must leave every order generated on or before `t_check` unchanged.
   Checked at two spot-check points deep into the sample.
5. Point-in-time macro: N/A -- no macro/external series used at all (no
   ALFRED-vintage concern whatsoever, not even the VIX proxy families
   016/025 needed).
6. **Hand-checked O/C arithmetic** (required by this iteration's task,
   before the grid runs): on a handful of real development days for
   SP500, confirm `intraday_t + overnight_t` approximately reproduces that
   day's total Close-to-Close return (`Close_t/Close_{t-1} - 1`), modulo
   the small multiplicative-compounding cross-term
   (`(1+overnight_t)*(1+intraday_t) - 1` is the EXACT identity; the
   additive sum is only a first-order approximation) -- confirming the
   decomposition arithmetic itself, not just the code, is correct.
7. **Pre-grid non-degeneracy check** (required by this iteration's task,
   before the grid runs): compute the primary config's `elevated_t`/
   `compressed_t` regime frequencies directly on development data for all
   5 core assets (must be non-trivial: not near-0%, not near-100%) --
   confirming the trigger fires non-trivially on all 5 assets before any
   backtest result is trusted.

## Files (to be created in the implementation/run step)

- `src/backtest/v3/strategies/intraday_overnight.py`
- `scripts/v3/run_026_intraday_overnight.py`
- `families/026-intraday-overnight/results.md`, `grid_results.csv`,
  `_primary_per_asset.csv`, `_run_output.json`
- `state/trials/new_026_*.csv` (36 files)
