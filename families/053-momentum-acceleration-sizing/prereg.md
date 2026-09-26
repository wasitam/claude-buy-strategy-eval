# Family 053: Momentum acceleration ("velocity of momentum") sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Novy-Marx, R. (2012), "Is Momentum Really Momentum?," *Journal of
Financial Economics* 103(3), 429-453 -- the "momentum of momentum" /
intermediate-horizon persistence finding: recent past performance's
*own trend* (whether a stock's momentum ranking is itself improving or
deteriorating) carries information beyond the momentum level itself.
Gao, L., Han, Y., Li, S.Z. and Zhou, G. (2018), "Market Intraday
Momentum," *Journal of Financial Economics* -- momentum-of-momentum /
acceleration framing more generally. Seed queue item #56
(`state/research_queue.md`, table row `| 56 |`), category
**Trend / time-series momentum exit** as listed there.

## Mechanism ("why would this work, and who is on the other side?")

An asset's trailing total return over a fixed lookback (its "momentum
level") is a first-derivative-of-price statistic: it says whether the
asset has gone up or down, and by how much, over the window. It says
nothing about whether that trend is *itself* gaining or losing steam.
Two assets can share an identical trailing-12-month return of +20% while
one got there by accelerating (a small early gain followed by a large
recent gain) and the other by decelerating (a large early gain followed
by a small, fading recent gain) -- the same level, two very different
underlying dynamics. This family measures the **second derivative**:
compare the asset's own trailing momentum level *today* against the same
statistic computed as of `lag_days` trading days ago (i.e. "the same
trailing-N-day return, M days earlier"). A positive difference
(momentum accelerating) is read as evidence the trend is gaining
strength -- consistent with the slow-information-diffusion/underreaction
story (Hong & Stein 1999) still being in its early-to-middle innings,
where trend-following flows (CTAs, momentum funds, retail chasers) have
further room to keep building into the move -- so this family buys more.
A negative difference (momentum decelerating, even while still
positive) is read as evidence the trend is running out of steam --
consistent with the underreaction/information-diffusion process being
closer to complete, or with trend-following capital beginning to
crowd/exhaust, which the momentum-crash literature (Daniel & Moskowitz
2016) associates with a materially elevated risk of a sharp reversal --
so this family buys less, banking cash instead. The "other side" of the
trade is: (a) a time-series-momentum investor who sizes purely on the
*sign* of the level (family 005's own mechanism) and is blind to whether
that level is gaining or losing steam, and so keeps buying the same
disproportionate amount straight through a decelerating, crash-prone
late-stage trend that this family would have already started trimming;
and (b) a momentum-of-momentum-agnostic market-maker/contrarian who
absorbs the flow this family avoids providing during exactly those
decelerating windows. The risk paid if the mechanism does not hold:
whipsaw around noisy short-run changes in a lookback statistic that is
itself already noisy (a difference of two already-noisy momentum
estimates), which the divergence proof and grid below are designed to
surface honestly.

## Category

**Trend / time-series momentum exit** (research-loop-plan-v3.md sec 4.5),
matching the seed queue's own categorization of idea #56.

## Required distinction from families 005, 013 and 002 (constructed concretely, not just asserted)

### (a) What each family's statistic actually measures

| Family | Statistic | Order of the derivative | What it is blind to |
|---|---|---|---|
| 005 (TSMOM sizing) | `sign(mom_t)`, `mom_t = close_t/close_{t-N} - 1` | **First derivative, sign only** (a single point-in-time level, binarized) | Whether `mom_t` is itself rising or falling -- a trend that has been decelerating for months but is still barely positive reads identically to a trend accelerating hard, as long as both are `>0` |
| 013 (momentum-tilted rebalancing) | Cross-sectional rank/level of trailing momentum across the 5 assets, used to set **portfolio weights** | **First derivative, cross-sectional level** | The asset's own rate of change of that level over time -- 013 only ever asks "who is currently strongest," never "is the currently-strongest asset's own momentum itself gaining or losing steam" |
| 002 (dual momentum) | `mom_t` used as a **binary admission/ranking filter** (absolute momentum vs. cash; relative momentum ranking) | **First derivative, level, gated/binary** | Same blindness as 005/013 -- once an asset passes the level filter or wins the cross-sectional rank, dual momentum treats it identically regardless of whether that level is freshly built or already fading |
| **053 (this family)** | `accel_t = mom_t - mom_{t-lag}`, the **change in the trailing-momentum level itself** over `lag_days` | **Second derivative** (own-asset, own-time-series) | N/A -- this is precisely the statistic none of 005/013/002 compute |

`accel_t` is not a relabeling, rescaling, or parametric special case of any
of 005/013/002's own statistics: it is a *difference of two* momentum-level
observations taken at different points in time, a genuinely higher-order
object those three families' own signal-generating code paths never
construct at all (verified below by direct construction, not assertion).

### (b) Constructed toy example: level and acceleration disagree in sign

```
Asset with a single decelerating uptrend, sampled monthly, monthly return
declining by 1 percentage point per month, from +13% (month -5) down to
0% (month 8 onward):

Month  -5   -4   -3   -2   -1    0    1    2    3    4    5    6    7    8+
Return +13% +12% +11% +10% +9%  +8%  +7%  +6%  +5%  +4%  +3%  +2%  +1%  0%
```

Trailing 12-month momentum level measured at month 12 (`mom_now`, using
months 1-12's monthly returns, all still positive but strictly smaller
each month than the one before): `mom_now = 1.07 x 1.06 x ... x 1.00^5 - 1
= +31.4%` (comfortably positive -- **level says "buy more," per families
005/002/013**). The *same* trailing-12-month statistic measured 6 months
earlier, at month 6 (`mom_past`, using months -5..6's returns -- the
trend's earlier, faster-growing phase): `mom_past = 1.13 x 1.12 x ... x
1.02 - 1 = +136.7%`. Since `mom_past > mom_now`, `accel = mom_now -
mom_past = -105.3%` -- decisively negative, so **this family's own
acceleration signal says "buy less."** The two signals disagree in the
sign of their *implied action* (more vs. less than baseline) even though
the level itself never turns negative at any point in the construction --
exactly the "still-positive but decelerating trend" case the task
requires be constructed concretely (verified by direct arithmetic,
`scripts/v3/run_053_momentum_acceleration_sizing.py::check_toy_divergence`).

### (c) Concrete real dev-period example (verified programmatically against this family's own production signal function, `lookback_days=252, lag_days=126`, `load_dev()` only, no lookahead)

| Asset | Date | `mom_now` (level, 252d) | `mom_past` (same stat, 126d earlier) | `accel = mom_now - mom_past` | Family 005's read (sign of level) | This family's read (sign of acceleration) |
|---|---|---|---|---|---|---|
| SP500 | 2004-07-06 | **+13.2%** | +21.9% | **-8.7%** | positive -> buy more | negative -> buy less |
| GOLD | 2007-02-09 | **+21.3%** | +46.1% | **-24.7%** | positive -> buy more | negative -> buy less |
| BTC | 2018-03-26 | **+268.4%** | +565.7% | **-297.3%** | positive -> buy more | negative -> buy less |

All three are real, dev-period-only (`<2020-01-01`), causal, no-lookahead
readings of the exact `compute_signal()`/`compute_acceleration()` functions
this family's strategy module implements (recomputed live in
`scripts/v3/run_053_momentum_acceleration_sizing.py::check_level_vs_acceleration_divergence`,
not hand-copied). On each of these three real dates, on three different
assets, the trailing 12-month momentum level is decisively positive
(family 005/002/013 would all read "strong, buy/admit/tilt toward this
asset") while the level is decelerating sharply relative to where it
stood 6 months earlier (this family reads "buy less, bank cash"). BTC's
2018-03-26 reading is a particularly clean real-world illustration of the
mechanism's own hypothesis: deep in the aftermath of BTC's Dec-2017 peak,
trailing 12-month momentum was still extraordinarily positive (the base
effect of the 2017 run-up had not yet rolled off), but decelerating
violently -- and the following months saw BTC's drawdown continue,
consistent with (not proof of) the momentum-crash risk the mechanism
section names as the risk this family is designed to sidestep.

### (d) Why this also is not a re-test of anything in sec 7.2's closed list

None of v1's ATR-shock/trend-stretch signals, v2's SmartDCA (price-vs-
moving-average mean reversion), ADCA B1/B2, the fixed-target rebalanced
portfolios C1/C2/C3, or v2.1's rate-regime Strategy D compute a
difference of the asset's own trailing-return statistic at two different
points in time. The closest is SmartDCA's rho-weighted mean-reversion
signal, which compares *price* to a *moving average of price* at a single
point in time (a level-vs-level-at-one-time comparison), never a
level-vs-itself-at-two-different-times comparison -- a different
statistical object entirely.

## Exact rules

Computed causally at each week-end decision day `t` (the deposit-credit
day, same weekly cadence as every other v3 family), using only Close
prices through `t` (no lookahead):

- **Momentum level at a reference point.** For any reference index `ref`,
  `mom(ref) = close_ref / close_{ref - lookback_days} - 1` (the asset's own
  trailing total return over `lookback_days` trading days ending at
  `ref`). Undefined (`NaN`) if `ref - lookback_days < 0`.
- **Momentum today vs. `lag_days` ago.** `mom_now_t = mom(t)`,
  `mom_past_t = mom(t - lag_days)`.
- **Acceleration.** `accel_t = mom_now_t - mom_past_t`. Undefined until
  both `mom_now_t` and `mom_past_t` are defined, i.e. until
  `t - lag_days - lookback_days >= 0`; while undefined, the multiplier
  defaults to `1.0` (plain DCA), the same "not enough history yet"
  convention as every prior sizing family in this loop.
- **Causal, point-in-time percentile rank** `pctile_t`: the fraction of
  the trailing `pctile_lookback` days' own `accel_t` values (purely
  backward-looking, expanding-until-full) that are `<= accel_t` -- the
  same relative-threshold convention families 031/035/036/039/040/041/
  042/044 already use (adapts to each asset's own realized acceleration
  range instead of an arbitrary universal zero cutoff). Defaults to `0.5`
  (neutral) until `pctile_lookback` days of `accel_t` history exist.
  `pctile_lookback` is fixed at **252** (not grid-varied; see Parameters
  below) for every configuration.
- **Sizing multiplier** (continuous, no discrete "otherwise" state --
  family 039's established continuous-percentile-scaled-multiplier
  design pattern, avoiding families 033/034's discrete-ladder cash-cap-
  nullification pitfall by construction):
  `m_t = clip(1 + k * (2 * pctile_t - 1), min_mult, max_mult)`. A high
  percentile (accelerating momentum) pushes `m_t` above 1 (buy more); a
  low percentile (decelerating momentum, even while the level itself is
  still positive) pushes `m_t` below 1 (buy less). `max_mult` is fixed at
  **2.0** for every configuration (not grid-varied).
- **Order generation (every trading day):**
  `target_buy_usd_t = weekly_deposit * m_t`, capped at
  `max_lump_multiple * weekly_deposit` (fixed at **3.0**), then at
  available cash (the engine's own no-leverage cap, sec 3.2). No sell
  orders are ever generated -- a pure sizing-up/sizing-down rule, matching
  families 003/005/031/036/039/040/044's own precedent. A below-1.0-
  multiplier week banks the shortfall as cash (earning IRX), available to
  fund a future above-1.0-multiplier week -- never leverage or borrowing.

## Data inputs

Daily Close price of the asset itself only (one of the 5 core assets,
tested independently -- single-asset family). No macro or alternative
data. Sourced via `src.backtest.v3.data.load_dev()` only. Identically
testable on all 5 core assets by construction (price-only signal).

## Parameters (4 tunable, comfortably under the plan's <=5 ceiling)

| Parameter | Grid values | Primary |
|---|---|---|
| `lookback_days` | 126, 252, 378 (trading days -- brackets the standard ~12-month TSMOM window, matching family 005's own grid) | 252 |
| `lag_days` | 63, 126 (~3 months, ~6 months -- how far back the "earlier" momentum reading is taken) | 126 |
| `k` | 0.5, 1.0, 1.5 (sensitivity of the multiplier to the acceleration percentile rank) | 1.0 |
| `min_mult` | 0.25, 0.5 (lower clip bound -- deliberately `<1.0`, per families 014/033/037's own documented cash-cap-nullification lesson: a primary-config floor `>=1.0` would nullify the reserve-banking mechanism under the engine's no-leverage cap) | 0.5 |

Fixed constants (not grid-varied, per families 031/036/044's own
precedent): `pctile_lookback = 252`, `max_mult = 2.0`,
`max_lump_multiple = 3.0`.

`lookback_days=252` (~12 months) is primary because it matches the
standard TSMOM/12-month-momentum literature convention (Moskowitz, Ooi &
Pedersen 2012; family 005's own primary choice), a no-look prior rather
than something tuned on this loop's own data. `lag_days=126` (~6 months)
is primary because it is a natural "half the momentum window" comparison
point -- long enough that the two momentum readings draw on largely
non-overlapping return histories (only 126 of 252 days overlap), so the
difference reflects a genuine shift in the trend's own pace rather than
near-total overlap noise, while still being much shorter than
`lookback_days` itself (an intermediate-horizon comparison, matching
Novy-Marx's own "intermediate horizon" framing). `k=1.0` and `min_mult=0.5`
are primary for the same reasons families 036/039/040/044 give: a
moderate, not-most-aggressive point on each grid, with the floor
deliberately below 1.0.

## Grid

3 (`lookback_days`) x 2 (`lag_days`) x 3 (`k`) x 2 (`min_mult`) =
**36 configurations** (= 36 cap, at the limit; 4 tunable params <= 5).

## Primary configuration

`lookback_days=252, lag_days=126, k=1.0, min_mult=0.5`
(`pctile_lookback=252, max_mult=2.0, max_lump_multiple=3.0` fixed).

## Pre-grid non-degeneracy check required before running the full grid

Before the full grid is trusted, the primary config's multiplier must not
be stuck at 1.0 for nearly the whole sample and must show real dispersion
on all 5 core assets, following the convention established in families
036/039/040/044. Result recorded in `results.md` before any backtest
number is trusted.

## Expected sign

Positive, primarily on **Sharpe** rather than final wealth, for the same
structural reason as families 003/031/036/039/040/044: total capital
committed over the full development period is approximately unchanged
(only its week-to-week timing shifts, since every below-1.0 week banks
cash a later above-1.0 week spends), so the Sharpe channel (buying more
while a trend is genuinely gaining strength, less while it is losing
strength even though still positive, sidestepping some of the momentum-
crash risk Daniel & Moskowitz (2016) document) is the more mechanically
plausible primary effect. The wealth effect is a secondary, exploratory
hypothesis. A null result is a realistic possibility: `accel_t` is a
difference of two already-noisy trailing-return estimates, so it may
prove too noisy at these window lengths to move the needle, consistent
with families 036/040/041/044's own near-miss/rejected outcomes using an
analogous continuous-percentile functional form applied to a different
underlying statistic. BTC's short (~5-year) development window is again
flagged as a known weakness (per plan sec 5.1/12), and its 2018-03-26
divergence example above shows the acceleration signal reading strongly
negative deep in a real, subsequently-realized drawdown -- suggestive of
the intended mechanism, but a single anecdote, not a backtest result.

## Degenerate configuration (implementation check only, not a grid arm)

`enabled=False`: bypasses the acceleration/percentile computation
entirely and forces `m_t = 1.0` for every day, reproducing plain DCA
exactly, bit-for-bit (same pattern as families 003/030/031/036/044's
`enabled=False` degenerate check). Second reference point (two-reference-
point degenerate-config pattern, families 014/020/033/034/035/036/044
precedent): `k=0.0` (a real grid-shaped code path, not the bypass) also
forces `m_t = clip(1 + 0, min_mult, max_mult) = 1.0` for every day
regardless of `pctile_t`, and must independently reproduce plain DCA
bit-for-bit too.
