# Family 021: Amihud illiquidity-shock sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Amihud, Y. (2002), "Illiquidity and Stock Returns: Cross-Section and
Time-Series Effects," *Journal of Financial Markets* 5(1), 31-56. Amihud's
ILLIQ measure, `|r_t| / dollar_volume_t`, proxies the price impact of a
dollar of trading -- how much the price moves per dollar traded. Amihud
documents both a cross-sectional illiquidity premium (less liquid stocks
earn higher average returns) and a time-series effect: expected market
illiquidity raises the ex-ante required return, and unexpected illiquidity
shocks depress contemporaneous prices. Seed queue idea #21
(research-loop-plan-v3.md sec 7.3 addendum, added by the prior iteration's
queue replenishment).

## Mechanism ("why would this work, and who is on the other side?")

A day (or short run of days) where an asset's own Amihud ratio spikes into
an elevated trailing percentile is a day where price moved unusually far
per dollar of trading volume -- a proxy for a forced-selling, liquidity-
withdrawal, or acute-uncertainty episode (margin calls, deleveraging,
thin order books) rather than an orderly repricing on fresh information.
Amihud's own time-series result, and the broader illiquidity-premium
literature that follows it, is that such episodes are disproportionately
compensated: investors who are willing/able to supply liquidity (buy) into
a price-impact spike are on average absorbing a temporary illiquidity
discount that tends to mean-revert as normal trading conditions return,
rather than a permanent repricing. A fixed-dollar DCA buyer invests the
same $500 every week regardless of the illiquidity regime, so this family
re-times the SAME total deposit stream: it buys more, funded from cash
banked during calm (low-illiquidity) weeks, specifically during and just
after an illiquidity-shock episode, and buys a slightly reduced share in
calm weeks to fund that reserve -- no leverage, no borrowing, average
capital committed over time unchanged. The "other side" of this trade is
whoever is forced to sell or withdraw liquidity during the shock (the
same margin-called/deleveraging/panicking participants Amihud's own paper
and the broader liquidity-premium literature identify) and is compensated
for that immediacy by giving up price to whoever supplies liquidity in
return -- this family's strategy, systematically, on the developed
hypothesis.

## Category

**Sizing / valuation.**

## Data prerequisite and feasibility finding (REQUIRED before implementation, per this iteration's task)

`src/backtest/v3/data.py`'s cached OHLC previously dropped the `Volume`
column entirely (`_fetch_yf_raw` selected only `["Open","High","Low",
"Close"]`). This family is the first to need Volume, so its feasibility had
to be verified, not assumed (per the queue's own caveat on idea #21).

**Finding:** yfinance's raw cached CSVs under `data/*.csv` already contain a
`Volume` column for all 5 core assets (yfinance returns it by default; the
v3 cache just wasn't selecting it) -- no re-fetch was needed. Checked
`Volume` coverage on development data (< 2020-01-01) for all 5 core assets:

| Asset | Ticker | Dev days | Zero/missing-volume days | Coverage | Notes |
|---|---|---|---|---|---|
| SP500 | `^GSPC` | 23,109 | 5,496 | 76.2% | All zero-volume days are 1927-12-30 to 1949-12-30 (index-era, pre-modern reporting). Zero occurrences after 2010: **0**. Fully reliable over the period this family's signal will actually be live (post-1950). |
| GOLD | `GC=F` | 4,848 | 410 | 91.5% | Zero days scattered 2000-2019; 28 after 2015-01-01. Minor, scattered gaps -- workable with an explicit missing-day handling rule (below). |
| SILVER | `SI=F` | 4,850 | 662 | 86.4% | Zero days scattered 2000-2019; 108 after 2015-01-01 -- the noisiest of the 5, consistent with SI=F's continuous-contract volume being thinner and more roll-sensitive than GC=F's. Still a minority of days; workable with the same handling rule, flagged as the weakest link. |
| BTC | `BTC-USD` | 1,932 | 0 | 100.0% | Fully reliable, as expected (spot/exchange-aggregated volume, no futures-roll artifact). |
| OIL | `CL=F` | 4,857 | 6 | 99.9% | All 6 zero days fall in a single 2000-2001 window; fully reliable afterward. |

**Decision (judgment call, documented per this iteration's task instruction):**
Volume is reliably available for all 5 core assets over the large majority
of each asset's development history -- no asset has a Volume gap severe or
concentrated enough to be unworkable (the >=3-of-5 threshold for a
structural, family-008-style scoping decision is not remotely approached;
at most one asset, SILVER, shows a mildly elevated gap rate). This family
therefore proceeds as a normal single-asset family across **all 5 core
assets**, option (a) is not needed (no asset is excluded), with an explicit,
declared rule for handling zero/missing-volume days rather than assuming
they are rare enough to ignore silently:

- On any day where `Volume_t` is zero, missing, or `dollar_volume_t <=0`,
  the Amihud ratio `ILLIQ_t` is **undefined** (not zero, not treated as
  "maximally liquid"). That day is **excluded** from both (i) the trailing
  percentile-rank window's population and (ii) triggering the elevated-
  illiquidity regime itself (a day with no valid ILLIQ reading cannot, by
  construction, be an illiquidity-shock day). It does not extend or reset
  an already-active elevated regime from a prior valid trigger, either.
  This is the conservative choice: it never fabricates an illiquidity
  signal from a bad volume print, at the cost of slightly understating
  the (already small) opportunity on GOLD/SILVER's scattered zero-volume
  days.
- No futures-roll-specific adjustment is applied to the continuous-contract
  volume series (GC=F/SI=F/CL=F) beyond the exclusion rule above --
  the pre-grid non-degeneracy sanity check (below, run before the grid)
  is the concrete test for whether roll artifacts are producing a
  degenerate (near-0% or near-100%) trigger rate on any commodity asset;
  if they were, that would show up there and force a re-scoping before
  any grid or robustness result is trusted.

`src/backtest/v3/data.py` was extended (small, contained change): `Volume`
is now included in `_fetch_yf_raw`'s returned/cached frame (not filtered to
`>0`, unlike OHLC -- a zero-volume row is a valid data point whose Amihud
ratio is undefined, not a row to silently drop). `load_dev()`/`open_holdout()`
gate logic, the dev/holdout cutoff, and `check_no_raw_data_leak()` are
otherwise unchanged and re-verified to still pass after the change (see
results.md's implementation-checks table).

## Exact rules

1. Daily return: `r_t = Close_t / Close_{t-1} - 1`.
2. Dollar volume: `dv_t = Close_t * Volume_t` (undefined if `Volume_t` is
   zero, missing, or `dv_t <= 0` -- see the handling rule above).
3. Amihud ratio: `illiq_t = |r_t| / dv_t` where `dv_t` is defined, else
   `illiq_t` is undefined (NaN, excluded from ranking).
4. Trailing percentile rank (causal, `illiq_lookback` trading days,
   counting only days with a defined `illiq`, minimum 20 valid
   observations before the signal can fire -- before that, defaults to
   "not elevated," the same warm-up convention families 001/011/015/016
   use): `pctile_t` = the fraction of defined `illiq` values in the
   trailing window (including day `t` itself, if defined) that are
   `<= illiq_t`.
5. **Trigger** on day `t` if `illiq_t` is defined and `pctile_t >=
   elevated_pct`.
6. **Elevated regime**: day `t` is in the elevated regime if a trigger
   occurred on any of the trailing `decay_days` trading days up to and
   including `t` (a sticky window, so a single shock's effect persists for
   the shock's assumed duration rather than requiring re-triggering every
   single day).
7. Decision, evaluated **only on each week's last trading day** (matching
   families 003/005/016/017's weekly-decision cadence -- the engine's
   deposit lands on that day, so the multiplier tilt has cash to act on):
   - If the week-end day is in the elevated regime:
     `buy_usd = min(cash, buy_multiplier * weekly_deposit,
     max_buy_multiple * weekly_deposit)`.
   - Otherwise (calm): `buy_usd = calm_fraction * weekly_deposit` (banks
     the `(1 - calm_fraction)` remainder as cash, earning IRX, funding
     later elevated-regime buying).
   - Never a sell. No leverage, no borrowing -- `buy_usd` is always
     cash-capped by the engine itself (sec 3.2), so an elevated-regime
     week with insufficient banked cash simply buys what's available.

## Parameters (5, all tunable; `max_buy_multiple` fixed, not grid-varied, same convention as family 016)

| Param | Meaning | Grid values |
|---|---|---|
| `illiq_lookback` | Trailing window (trading days) for the percentile rank | 126, 252 |
| `elevated_pct` | Percentile threshold (0-100) marking an illiquidity shock | 90, 95 |
| `decay_days` | How many trading days an elevated regime persists after its last trigger | 5, 10 |
| `buy_multiplier` | Multiple of `weekly_deposit` bought on an elevated-regime week-end (cash-capped) | 1.5, 2.0 |
| `calm_fraction` | Fraction of `weekly_deposit` bought on a calm week-end (remainder banked) | 0.85, 0.95 |
| `max_buy_multiple` (fixed) | Hard ceiling on any single week's buy relative to `weekly_deposit` | 4.0 |

Grid: 2 x 2 x 2 x 2 x 2 = **32 configurations** (<=36 cap; 5 tunable
parameters, at the sec 3.4 ceiling).

## Primary configuration

`illiq_lookback=252, elevated_pct=95, decay_days=5, buy_multiplier=2.0,
calm_fraction=0.95` (`max_buy_multiple=4.0` fixed).

## Expected sign of the effect

Beats DCA on final wealth AND Sharpe: buying more during illiquidity-shock
episodes (funded from a small reserve banked in calm weeks) is expected to
capture, on average, better entry prices than a constant weekly buy,
per Amihud's time-series illiquidity-premium finding.

## Required distinction from families 003, 016 and 017 (this iteration's task instruction)

All four families size buys using a signal derived from an asset's own (or
a shared) recent price/return behavior, so the distinction must be made
explicit and precise:

- **Family 003 (vol-managed sizing):** sizes inversely to each asset's own
  trailing **realized variance** (second moment of returns only -- no
  volume, no direction) -- buys **more in low-vol, less in high-vol**
  regimes, a direction-agnostic risk-avoidance bet. This family (021) does
  the opposite in spirit on the trigger dimension (buys **more** during an
  acute, high-impact episode, not less) and uses a completely different
  input (price impact **per dollar traded**, which requires volume; 003
  never touches volume at all).
- **Family 016 (VIX contrarian):** sizes using a single **shared,
  cross-market, option-implied volatility level** (`^VIX`, the SAME signal
  applied identically to all 5 assets, regardless of each asset's own
  trading conditions) -- a market-wide sentiment/fear gauge with no volume
  or liquidity component whatsoever. This family (021) uses each asset's
  **own**, asset-specific price-impact-per-dollar-traded ratio, computed
  purely from that asset's own price and volume, with no cross-asset or
  options-market input at all -- a liquidity/market-microstructure
  construct, not an implied-volatility level.
- **Family 017 (RSI2 mean-reversion):** a bounded 0-100 **oscillator**
  computed purely from the **ratio of recent average gains to average
  losses** in price alone (no volume at all) -- a short-horizon relative-
  strength/overbought-oversold statistic. This family (021) is not an
  oscillator and is not bounded; it is a **price-impact ratio**
  (`|return| / dollar volume`) whose defining feature is that it requires
  **both** price change **and** trading volume jointly -- an illiquidity/
  price-impact proxy, mechanistically and definitionally distinct from a
  pure-price relative-strength oscillator.

In short: 003 is a **direction-agnostic risk (2nd-moment) signal**; 016 is
a **market-wide, options-derived sentiment level**; 017 is a **pure-price
relative-strength oscillator**; 021 is an **asset-own price-impact-per-
dollar-traded (liquidity) signal**, the only one of the four that uses
volume at all. Not a re-test of sec 7.2's closed list either (v1's ATR-
shock signal A is a pure-price volatility-band trigger with no volume
term).

## Pre-grid non-degeneracy sanity check (to be run before the full grid, per the established convention)

Before trusting the grid, confirm the primary config's elevated-illiquidity
trigger fires non-trivially (not near-0%, not near-100%) on every asset --
the concrete test for whether futures-roll artifacts (flagged as a risk
above) are corrupting the signal on GOLD/SILVER/OIL. Requires each asset's
fraction of week-end decision days flagged "elevated regime" to fall
strictly between 2% and 60% (an upper bound well below 98%, since an
`elevated_pct=95` trigger with `decay_days<=10` should, by construction of
a 95th-percentile threshold applied to weekly-sampled days, never plausibly
approach the majority of weeks -- a materially higher rate than that would
itself be evidence of a roll-artifact-driven degenerate signal, not a
successful non-degeneracy pass).

## Implementation checks to run (sec 3.2, before any grid result is trusted)

1. `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash).
2. Cash and positions never negative, for the DCA baseline, the primary
   config, and the grid's most aggressive corner
   (`elevated_pct=90, buy_multiplier=2.0, calm_fraction=0.85,
   decay_days=10`).
3. Capital deployed never exceeds cumulative deposits + interest, for the
   primary config and the aggressive corner.
4. No-lookahead: perturbing all data after day `t` leaves every order
   on/before `t` unchanged (spot-checked at two points deep into
   development history, exercising the Amihud/percentile/decay
   computation specifically).
5. Point-in-time macro: N/A -- price-and-volume-only signal, no macro/FRED
   dependency.

## Files (to be produced by the implementation/run step)

- `src/backtest/v3/strategies/amihud_illiquidity.py`
- `scripts/v3/run_021_amihud_illiquidity.py`
- `families/021-amihud-illiquidity/grid_results.csv`,
  `_primary_per_asset.csv`, `_run_output.json`
- `state/trials/new_021_*.csv`
