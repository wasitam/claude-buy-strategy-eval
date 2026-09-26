# Family 037: Drawdown-DURATION (time-underwater) sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Seed research queue item #35 (`state/research_queue.md`): "increase buy
size the longer an asset has gone, in trading days, since its last
all-time (or trailing-N-year) high close." Economically related to the
practitioner "time-to-recovery" / underwater-duration literature that
underlies the Calmar ratio (return over max drawdown *magnitude*) versus
the Sterling and, especially, the Martin (Ulcer Index) and Pain-Index
family of risk measures, which explicitly separate a drawdown's *depth*
from its *length* (the Ulcer Index integrates squared drawdown depth over
time, but the pure "days underwater" / "time-to-recovery" statistic used
here isolates length alone, with no depth term at all). Also related to
Ibbotson-Associates-style practitioner writing on the psychological and
behavioral effects of extended underwater periods, treated as distinct
from drawdown depth in that literature specifically because investor
fatigue and capitulation are documented to track how long a position has
gone without a new high, not how far below the old high it currently sits.

## Mechanism ("why would this work, and who is on the other side?")

**Why duration, not magnitude, might carry information magnitude alone
does not:**

1. **Duration-driven investor fatigue and capitulation, independent of
   depth.** A large body of behavioral-finance and flow literature
   documents that retail and even institutional investors reduce or halt
   contributions, or capitulate outright, as a function of how *long* they
   have watched a position sit below its old high-water mark -- patience is
   a depletable resource that erodes with elapsed time, not simply with
   the current percentage shortfall. A shallow-but-long grind (e.g. 13%
   below a two-year-old high for fourteen months) can exhaust
   buy-and-hold discipline and trigger "I'm tired of waiting" selling or
   contribution-pausing just as effectively as, or more effectively than,
   a much deeper but mercifully brief drawdown that resolves in a few
   weeks and never gives fatigue time to build. A rule that sizes
   purely off elapsed time since the last high is a mechanical way to buy
   more precisely during the stretches when this fatigue-driven,
   duration-specific selling pressure is at its most sustained -- a
   distinct flow story from family 014's "buy more the deeper it is"
   value/mean-reversion story.
2. **Calendar and structural selling pressure that scales with elapsed
   time, not depth.** Tax-loss harvesting (concentrated near calendar
   year-end, and re-triggered every year a position remains underwater,
   regardless of whether that year's shortfall is 10% or 40%), and
   periodic portfolio-rebalancing flows that trim long-underwater
   positions on a fixed schedule (quarterly/annual reviews) rather than in
   response to the live percentage drawdown, are both mechanically tied to
   *how long* a position has been away from its high, not to its current
   *depth* below that high. Both recur every period a drawdown persists,
   compounding with duration in a way a one-shot magnitude reading cannot
   capture.

**Who is on the other side?** Investors who reduce or halt contributions
purely because "it's been a long time and nothing has happened" -- a
documented behavioral pattern distinct from panic-selling into a sharp,
obviously large drawdown (the pattern family 014's mechanism targets) --
and investors whose tax-loss-harvesting or calendar-driven rebalancing
schedules sell out of long-underwater positions irrespective of current
depth. If a long-duration drawdown is instead a *structural* repricing
(the asset's fair value has genuinely fallen and stays there), the
mechanism fails by construction: it keeps buying more the longer the
asset fails to make a new high, with no depth-based brake, which is a
real risk this pre-registration flags before any backtest is run (an
asset that never again approaches its old peak within the horizon that
matters will simply accumulate a larger position at a permanently lower
value), consistent with sec 12's risk-disclosure spirit.

## Category

**Sizing / valuation** (research-loop-plan-v3.md sec 4.5) -- matches the
seed queue's own categorization of idea #35.

## The required rigorous distinction from family 014 -- with a concrete real-dev-data divergence example

Family 014's signal is `dd_t = max(0, 1 - close_t / ATH_t)`, the
**percentage-magnitude shortfall** from the trailing all-time-high --
computed from a single ratio of two prices (today's close and the
running-peak close), with **zero dependence on how many days have elapsed**
since the peak was set. A drawdown that opened yesterday and one that
opened three years ago register identically on family 014's signal if
today's close sits at the same percentage below the same peak.

This family's signal is `dur_t`, the **count of trading days** since the
close last touched (or exceeded) the running peak -- computed purely from
the *sequence of dates* on which new highs occurred, with **zero
dependence on how far below the peak today's close currently sits**. A 1%
shortfall that has persisted for two years and a 40% shortfall that opened
yesterday can register an *identical* `dur_t` if both drawdowns are, say,
five trading days old, or wildly different `dur_t` values despite
identical `dd_t`.

**Formally, these are mechanically independent statistics of the same
price path.** Fix any drawdown episode's *depth path* `dd_t` for
`t = 0, ..., T` (the exact sequence of percentage shortfalls each day).
The corresponding *duration path* `dur_t = t` for every day the episode
remains open is entirely determined by the calendar alone, not by any of
the `dd_t` values -- one can construct arbitrarily many different depth
paths (a V-shaped crash-and-instant-recovery reaching -40% on day 2 and
closing the episode by day 5; a slow grind reaching only -5% by day 5 and
staying open for 300 more days) that share nothing about their `dd_t`
values yet whose `dur_t` values are driven purely by when the episode
closes. Neither statistic can be recovered from the other without the
missing information (the exact price level, for duration-from-depth; the
exact date sequence, for depth-from-duration).

**Concrete real dev-period divergence, S&P 500 (`^GSPC`), both windows
entirely pre-2020 (verified programmatically at run time against the
module's own `compute_drawdown_and_duration`, not hand-copied -- see
`scripts/v3/run_037_drawdown_duration.py::check_real_divergence_example`):**

| Episode | Peak date (close) | Trough date (close) | New-high date | Max magnitude `dd` | Duration to new high |
|---|---|---|---|---|---|
| **Deep-but-brief**: Sept 2018 - Apr 2019 correction | 2018-09-20 (2930.75) | 2018-12-24 (2351.10) | 2019-04-23 (2933.68) | **~19.8%** (deep) | **~145 trading days** (brief, ~7 calendar months) |
| **Shallow-but-long**: May 2015 - Jul 2016 sideways grind | 2015-05-21 (2130.82) | 2016-02-11 (1829.08) | 2016-07-11 (2137.16) | **~14.2%** (shallower) | **~290 trading days** (long, ~14 calendar months) |

The deeper drawdown (2018, ~19.8%) resolved into a new high in **fewer**
trading days than the shallower drawdown (2015-16, ~14.2%), which
persisted roughly **twice as long**. Family 014's magnitude signal ranks
the 2018 episode as the more severe of the two (correctly, on its own
terms); this family's duration signal ranks the 2015-16 episode as the
more persistent of the two -- the opposite ordering. A magnitude-only rule
(family 014) would have sized its most aggressive buying into the 2018
trough and comparatively little into the 2015-16 grind (its shallow depth
never crosses family 014's deeper ladder tiers as decisively); a
duration-only rule (this family) does the reverse, sizing its most
aggressive buying into the second half of the 2015-16 grind (once
`dur_t` crosses the long-duration tier) and comparatively less into the
brief 2018 episode (which closes out before `dur_t` reaches the same
tier). Neither signal can be recovered from the other on this real
episode pair, exactly as the general argument above predicts. All dates
referenced are confirmed pre-2020 and drawn only from `load_dev()`.

**Also not a re-test of family 034 (52-week-low proximity tilt).** Family
034's reference point is a rolling 52-week LOW (a continuously-resetting
short window), and its signal is proximity to that low -- itself a
magnitude-style statistic (how close is today's close to the recent
floor), not a duration/elapsed-time statistic. This family's reference
point is the all-time (or long trailing-window) HIGH, and its signal
never touches price level at all once the peak date is fixed -- it counts
elapsed trading days only.

## Exact rules

Computed independently for each asset, using only that asset's own OHLC
close prices, causally (no lookahead):

1. **Trailing reference high, `ATH_t`:** identical definition to family
   014 (unbounded expanding-window causal running max, or a
   lookback-capped trailing rolling-window causal running max), so this
   family's reference-point choice is directly comparable to family 014's:
   - **Unbounded** (`ath_lookback_years = None`): `ATH_t = max(close_0, ..., close_t)`.
   - **Lookback-capped** (`ath_lookback_years = L`): `ATH_t = max(close_{t-W+1}, ..., close_t)`,
     `W = round(252 * L)` trading days (falls back to the expanding max
     while fewer than `W` observations exist).
2. **Days-since-peak counter, `dur_t`** (the family's defining statistic,
   strictly causal): `dur_t = 0` on any day the close is at or above
   `ATH_t` (a new or matched high); otherwise `dur_t = dur_{t-1} + 1`. This
   is a pure elapsed-trading-day counter, entirely blind to how far below
   `ATH_t` the close currently sits -- **the depth ratio `close_t/ATH_t`
   never appears in this computation at all**, which is precisely the
   distinction from family 014 above.
3. **Ladder multiplier, `m_t`,** a discrete step function of `dur_t` with
   two breakpoints `(dur1_days, dur2_days)` and three tier multipliers
   `(near_high_mult, mult_tier1, mult_tier2)`:
   - `dur_t < dur1_days`: `m_t = near_high_mult` (at or recently at a new
     high -- the "bank the reserve" regime).
   - `dur1_days <= dur_t < dur2_days`: `m_t = mult_tier1`.
   - `dur_t >= dur2_days`: `m_t = mult_tier2` (longest time underwater --
     the "deploy the reserve" regime).
4. **Order:** `buy_usd_t = min(weekly_deposit * m_t, weekly_deposit * max_lump_cap)`,
   never a sell. The engine's own cash cap (sec 3.2: `buy_usd <= cash`)
   enforces "cash-capped, no leverage" mechanically -- a below-1x week
   (`near_high_mult < 1`) banks the unspent share of that week's deposit
   as cash (earning IRX), which becomes available to fund a later
   above-1x week once the drawdown has run long enough, the same implicit
   reserve mechanism families 003/005/014 use, with no separate
   reserve-accounting parameter needed. `max_lump_cap` is a hard ceiling
   on a single week's buy relative to the plain $500 deposit, independent
   of banked cash available, matching family 014's anti-concentration
   control.
5. **Decision cadence:** the multiplier is recomputed at every trading
   day's close (needed because `dur_t` changes daily), but since deposits
   only arrive on each week's last trading day, `buy_usd_t` is only
   non-zero on week-end decision days -- identical cadence to every other
   single-asset family in this loop (satisfying sec 3.4's "at most one
   order per asset per trading day").

## Data inputs

Daily OHLC close of each of the 5 core assets, individually, plus the
daily risk-free rate (IRX) for cash interest -- all sourced via
`src.backtest.v3.data.load_dev()` only. No macro or alternative data.

## Parameters (4 of the allowed 5)

| Parameter | Meaning | Grid values | Primary |
|---|---|---|---|
| `ath_lookback_years` | Cap on how far back the running high is tracked (same role as family 014's parameter of the same name, kept for direct comparability) | `None` (unbounded), `10` | `None` |
| `ladder` | Bundled `(dur1_days, dur2_days, mult_tier1, mult_tier2)` preset (see below) -- one logical parameter, same bundling convention family 013/014 used | `mild`, `moderate`, `aggressive`, `flat` | `moderate` |
| `near_high_mult` | Buy multiplier while `dur_t < dur1_days` (the "bank the reserve" regime) | `0.75`, `1.0` | `1.0` |
| `max_lump_cap` | Ceiling on `buy_usd` as a multiple of the plain $500 deposit | `2.0`, `3.0` | `3.0` |

**Ladder presets** (bundling `dur1_days`, `dur2_days`, `mult_tier1`,
`mult_tier2` into one selectable parameter, mirroring family 014's
percentage-based tiers but expressed in trading-day counts instead of
percentage-magnitude thresholds, per this family's own duration-only
statistic):

| Preset | `dur1_days` | `dur2_days` | `mult_tier1` | `mult_tier2` |
|---|---|---|---|---|
| `mild` | 63 (~1 quarter) | 252 (~1 year) | 1.25 | 1.75 |
| `moderate` (primary) | 63 (~1 quarter) | 252 (~1 year) | 1.5 | 2.0 |
| `aggressive` | 126 (~half year) | 504 (~2 years) | 2.0 | 3.0 |
| `flat` | 63 | 252 | 1.0 | 1.0 |

`flat` is this family's **true zero-effect grid arm**: with
`mult_tier1 = mult_tier2 = 1.0`, every tier's multiplier equals the
near-high regime's baseline, so when *also* paired with
`near_high_mult = 1.0`, `m_t = 1.0` for every day regardless of `dur_t` --
a real, independently-computed grid member (not a bypass code path)
expected, by construction, to reduce to plain DCA. Per family 033/034's
lesson, `flat`'s tier multipliers being exactly `1.0` is fine here
specifically *because* `flat` is the designated zero-effect diagnostic
arm and is never combined with an "otherwise" state below 1 that is
supposed to represent a genuine reserve tier -- the genuine reserve
mechanism lives in `near_high_mult` (checked below to be `< 1.0` on the
grid arms that are meant to bank a reserve, `{0.75}`, distinct from the
`1.0` arm which intentionally has no reserve at all and is expected to
behave like DCA at the near-high tier).

## Grid

`ath_lookback_years` (2) x `ladder` (4) x `near_high_mult` (2) x
`max_lump_cap` (2) = **32 configurations** (<= 36 cap, 4 tunable
parameters <= 5).

## Primary configuration

`ath_lookback_years=None` (unbounded, the literal "all-time-high" reading,
matching family 014's primary choice of reference for direct
comparability), `ladder=moderate` (symmetric to family 014's own primary
ladder choice, translated from percentage tiers to day-count tiers),
`near_high_mult=1.0` (no reduction below the plain deposit near a fresh
high -- the reserve only ever grows from banked cash the strategy does not
need to spend at par, a conservative choice made before seeing any
results), `max_lump_cap=3.0` (generous enough not to bind the primary
ladder's own 2.0x ceiling) -- all chosen before any backtest is run on
development data.

## Expected sign of the effect

Positive: the strategy should beat plain DCA on both final wealth and
Sharpe, because it buys systematically more of each asset during the
stretches that (per the duration-driven-fatigue/calendar-selling
mechanism above) plausibly see forced or fatigue-driven selling pressure
concentrated by elapsed time rather than by current depth, funded
entirely by deposits the strategy itself banked during near-high periods
rather than by leverage or externally sourced capital.

## Implementation checks to run (sec 3.2, before any results count) -- two-reference-point pattern

Per the established convention (families 010/013/014's degenerate-config
lesson):

1. **Explicit bypass flag, matching plain DCA bit-for-bit.** A
   module-level `enabled=False` path that skips the duration/ladder
   computation entirely and submits exactly `weekly_deposit` every week,
   no sells -- checked against `v3chk.check_degenerate_equals_dca`.
2. **True zero-effect grid arm, verified independently against plain
   DCA.** The real grid configuration `ladder=flat, near_high_mult=1.0`
   (any `ath_lookback_years`/`max_lump_cap`) is run through the *actual*
   duration/ladder computation (`enabled=True`, not the bypass path) and
   checked bit-for-bit against an independently-run plain-DCA reference.
3. **Real-data divergence check** (`check_real_divergence_example`):
   programmatically recompute `dd_t` (family 014's statistic) and `dur_t`
   (this family's statistic) on real SP500 dev-period data across the two
   episodes tabulated above, confirm both are correctly identified from
   the module's own functions (not hand-copied constants), and confirm
   the magnitude ranking and the duration ranking of the two episodes
   disagree (2018 deeper but shorter; 2015-16 shallower but longer), and
   that both episodes' dates are entirely pre-2020.
4. **Pre-grid non-degeneracy sanity check:** the primary config's
   multiplier must not be stuck at `1.0` for nearly the whole sample and
   must show real dispersion across all 5 core assets, verified before
   the grid runs.
5. **Cash-reserve dynamics check** (family 033's lesson): with
   `near_high_mult` on the grid's reserve-bearing arm (`0.75 < 1.0`,
   confirmed below 1.0 per the family 033/034 lesson), average cash must
   exceed the plain-DCA baseline overall, and must be lower during
   long-duration (`m_t > 1`) weeks than during near-high (`m_t < 1`)
   weeks, evaluated on that reserve-bearing configuration (the primary
   config itself uses `near_high_mult=1.0`, so this specific dynamic
   check is run on the `near_high_mult=0.75` arm of the grid, in addition
   to the primary-config cash check against DCA).
6. Cash and positions never negative (DCA baseline, primary config, and
   an aggressive grid corner).
7. Capital deployed never exceeds cumulative deposits + interest, via the
   principled "never invest" ceiling bound (family 021's lesson), for the
   primary config and an aggressive grid corner.
8. No-lookahead perturbation test: the running peak (`ATH_t`) and the
   days-since-peak counter (`dur_t`) must be strictly causal -- perturbing
   all data after day `t` must leave every order on or before `t`
   unchanged, spot-checked at two separate indices.
9. `PRIMARY_CONFIG` is asserted (at run time) to be a literal member of
   `grid_configs()` before the grid is run.
10. No dev-period check (formula spot-check, divergence example, sanity
    check) references a date on/after 2020-01-01 or an unseen ticker --
    `load_dev()`'s own gate enforces the rest.
