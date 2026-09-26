# Family 049: Ulcer Index (drawdown-severity-weighted volatility) sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Martin, P.G. and McCann, B.B. (1989), *The Investor's Guide to Fidelity
Funds*, Wiley (introduced the Ulcer Index); Martin, P.G., "Ulcer Index"
methodology note, tango.com (the RMS-drawdown formula and its use as a
downside-risk-adjusted sizing/allocation signal, distinct from ordinary
variance-based risk measures). Seed queue item #50
(research-loop-plan-v3.md sec 7.3, added this loop): "buy less/bank while
an asset's own trailing Ulcer Index ... sits high in its own trailing
percentile ... buy more/normal while it sits low."

## Mechanism ("why would this work, and who is on the other side?")

The Ulcer Index (`UI`) is a downside-risk statistic, unlike ordinary
variance/standard deviation, that penalizes **only** adverse moves relative
to a running peak, and penalizes them **quadratically** in both **how deep**
each day's shortfall is and **how many** days the shortfall persists (an
RMS statistic integrates depth-squared over the whole window, so a
drawdown that is both deep and long-lasting scores far higher than one that
is only deep-but-brief or only shallow-but-long, at the same average
magnitude -- see the required decoupling proof below). Two standard,
literature-grounded effects motivate scaling deposits down when this
statistic is locally elevated and up when it is locally depressed:

1. **Regime persistence of drawdown severity.** Realized-volatility and
   drawdown-severity regimes are well documented to cluster (GARCH-style
   volatility clustering, and specifically clustering of the *ulcer*/
   downside-risk statistic itself in the risk-adjusted-performance
   literature that popularized the Ulcer Index as a smoother substitute for
   plain standard deviation in Sharpe-like ratios). A period of severe,
   sustained drawdown is more likely to be followed by continued
   volatility and further downside than a calm period is -- a
   volatility-timing rationale in the same family as Moreira & Muir
   (2017)'s vol-managed sizing (this loop's family 003), but measured on a
   fundamentally different, asymmetric, peak-referenced statistic (see
   the distinction from family 003 below).
2. **Behavioral overreaction during protracted drawdowns creates a
   contrarian opportunity for a disciplined, mechanical buyer.** The
   severest Ulcer Index readings occur exactly when retail investors are
   most likely to reduce or halt contributions (the same behavioral pattern
   family 014's mechanism cites), so a rule that instead *reduces* buying
   only modestly during genuinely severe (deep-AND-persistent) drawdown
   regimes, while banking a larger reserve during genuinely calm regimes to
   deploy once the ulcer regime subsides, is a mechanical, emotion-free way
   to avoid buying into the single worst moments of a capitulation-driven
   selloff while still keeping money working across ordinary drawdowns.

**Who is on the other side?** Investors who deposit a flat amount
regardless of drawdown regime (the DCA benchmark) forgo this timing tilt
entirely. Investors who panic-sell or fully halt contributions during the
worst ulcer regimes are plausibly "funding" part of any edge this rule
captures (their forced/panic selling is this rule's counterparty). The
mechanism can fail if a severe, sustained drawdown regime is the *start* of
a structural decline rather than a cyclical one (the asset never
sufficiently recovers), a risk explicitly flagged before any backtest runs,
consistent with sec 12's honest-reporting spirit and with family 014's own
flagged risk of the same shape.

## Category

**Sizing / valuation** (research-loop-plan-v3.md sec 4.5) -- matches the
seed queue's own categorization of idea #50.

## Required rigorous distinction from family 014 (drawdown_reserve) and family 037 (drawdown_duration)

All three families share the same broad "size buys by how bad the current
drawdown situation is" territory, so this section is the primary gating
burden per this iteration's task instructions.

**Family 014's statistic** is `dd_t = max(0, 1 - close_t / ATH_t)`: a
**magnitude-only, memory-less snapshot** of how far *today's* close sits
below the trailing all-time-high. It carries zero information about how
long the asset has already been underwater, or about the shape of the
price path between the peak and today -- two days with an identical
`dd_t` reading are, by this statistic, indistinguishable, whether one is
day 2 of a fresh plunge and the other is day 400 of a grinding bear market.

**Family 037's statistic** is `dur_t`, a **pure elapsed-trading-day count**
since the close last touched or exceeded `ATH_t`. It carries zero
information about how deep the drawdown ever got -- a 1%-deep, 200-day
grind and a 60%-deep, 200-day crash register identically on `dur_t` alone.

**This family's statistic, the Ulcer Index, is the only one of the three
that combines BOTH depth AND persistence into a single number, via a
root-mean-square average over a trailing window `W` (the same window
serves as both the local running-peak reference and the RMS averaging
window, per Martin & McCann's original definition -- see "exact rules"
below):**

```
running_max_t  = max(close_{t-W+1}, ..., close_t)                (LOCAL peak, not all-time)
ddpct_i        = 100 * (close_i - running_max_i) / running_max_i  (<=0, for each day i in the window)
UI_t           = sqrt( mean_{i=t-W+1..t} [ ddpct_i^2 ] )
```

Two further, independent consequences distinguish `UI_t`'s reference point
itself from families 014/037's shared `ATH_t`: (a) `UI_t`'s running peak is
strictly **local** (a trailing `W`-day rolling max, `W` in the 60-126 day
range), whereas `ATH_t` is an **expanding or multi-year** running maximum
in both 014 and 037 -- so `UI_t` resets its reference every time a window's
worth of days elapses without incident, while `ATH_t` can stay pinned at a
years-old peak; (b) `UI_t` is a *quadratic* (RMS) average over many days at
once, not a single day's ratio (014) or a simple day-count (037) -- so it
is mathematically sensitive to the **product** of depth and duration in a
way neither prior statistic's own formula can express.

### Required decoupling proof (programmatically verified, not hand-copied -- see `scripts/v3/run_049_ulcer_index_sizing.py`)

**Proof 1 -- UI diverges from family 014's statistic even when family
014's statistic is held perfectly FIXED.** Two synthetic 126-day windows,
each a flat run at the local peak followed by a constant drawdown level
held to the end of the window (so each window's day-`t` "current drawdown
depth," family 014's exact statistic, is identical): both windows sit at a
**constant 15% drawdown** at the evaluation day (family 014 cannot tell
them apart, `dd_t = 0.15` for both), but one holds that depth for only 10
days (`dur_t=10`) and the other for 100 days (`dur_t=100`). Computed via
this family's own `compute_ulcer_index` function on the constructed price
paths: **`UI = 4.23`** for the 10-day episode vs. **`UI = 13.36`** for the
100-day episode -- more than a **3.2x** difference in the Ulcer Index
despite family 014's statistic being bit-for-bit identical between them.

**Proof 2 -- UI diverges from family 037's statistic even when family
037's statistic is held perfectly FIXED.** Two synthetic 126-day windows,
each held underwater for exactly **60 days** (family 037's exact
statistic, `dur_t=60` for both, cannot tell them apart), but one at a
constant 10% depth and the other at a constant 30% depth. Computed the
same way: **`UI = 6.90`** for the 10%-deep episode vs. **`UI = 20.70`**
for the 30%-deep episode -- exactly a **3.0x** difference (matching the
linear depth ratio, as the RMS formula predicts for two equal-duration,
constant-depth episodes) despite family 037's statistic being bit-for-bit
identical between them.

**Proof 3 -- real dev-period SP500 data, the two episodes family 037's own
`results.md` already established (both strictly pre-2020):** at
`ui_window=126`, computed by this family's own function on real SP500
close prices:

| Episode | Peak | Trough | Family 014's stat at trough (max `dd`) | Family 037's stat at trough (`dur_t`) | This family's stat at trough (`UI_126`) |
|---|---|---|---|---|---|
| Deep-but-brief (2018-19) | 2018-09-20 | 2018-12-24 | **19.78%** (larger) | **146 days** (smaller) | **5.96** |
| Shallow-but-long (2015-16) | 2015-05-21 | 2016-02-11 | **14.16%** (smaller) | **286 days** (larger) | **6.996** (larger) |

The shallower-but-longer 2015-16 episode scores a **higher** Ulcer Index
than the deeper-but-briefer 2018-19 episode -- the **opposite** ranking
from family 014's own magnitude statistic (which, being memory-less about
duration, ranks 2018-19 as the worse episode by depth alone) -- because
the RMS average integrates the shallower drawdown's much longer
persistence over the same 126-day window. This is the concrete,
programmatically-verified, real-data divergence the task requires, and it
independently confirms Proofs 1 and 2's synthetic construction is not an
artifact of contrived inputs.

**Conclusion:** no configuration of this family's statistic reduces to any
configuration of family 014's or family 037's statistic, and vice versa;
Proofs 1 and 2 show each prior family's statistic alone is provably
insufficient to determine this family's own value, in both directions
(depth held fixed, and duration held fixed). This is a materially
different mechanism, not a re-test of either family 014 or family 037.

## Brief distinction from family 003 (vol-managed sizing, ordinary return variance)

Family 003 (and its siblings) scale buys by ordinary realized
return **variance/standard deviation**: `std(r_t)` over a trailing window
of daily returns. Two structural differences from the Ulcer Index: (a)
variance is **symmetric** -- a day that gains 3% and a day that loses 3%
contribute identically to the statistic, whereas the Ulcer Index is
**strictly asymmetric**, using only the downside shortfall from a running
peak (an up day sets `ddpct_i = 0`, contributing nothing at all); and (b)
variance requires **no reference point whatsoever** (it is computed purely
from the return series itself), whereas the Ulcer Index is **defined
relative to a running peak price level**, so its value depends on the
whole shape of the price *path* since that peak, not just the distribution
of daily moves. A simple illustration: a steadily rising, choppy asset that
alternates +2%/-2% days around an upward trend has substantial return
variance but an Ulcer Index near zero (it barely if ever sits below its own
recent running high); a slow, low-volatility grinding decline (small daily
moves, but consistently negative, e.g. -0.3%/day for months) has low daily
return variance yet a **high** Ulcer Index (persistently and increasingly
far below its running peak). The two statistics are computed from
different information (path-relative-to-peak vs. distribution of daily
changes) and can move in opposite directions.

## Win-rule interpretation

Assessed as a **single-asset family** (sec 4.1's "Single-asset" line, as
instructed): beats DCA on final wealth AND Sharpe on at least 3 of the 5
core assets, at both fee levels, using the existing single-asset
`engine.py` unmodified -- identical scoping precedent to families
003/014/037/044 (a per-asset trailing-statistic signal, no portfolio
engine needed).

## Exact rules

Computed independently for each asset, using only that asset's own OHLC
close prices, causally (no lookahead):

1. **Local running peak, `running_max_t`:** the trailing rolling maximum
   close over the last `ui_window` trading days (falls back to the
   expanding max while fewer observations exist) -- **the same window
   length used for the RMS average below**, per Martin & McCann's original
   definition (this is a deliberately different reference-point choice
   from families 014/037's expanding-or-multi-year all-time-high; see the
   required distinction above).
2. **Daily percentage drawdown, `ddpct_t`:** `100 * (close_t -
   running_max_t) / running_max_t` (<=0; exactly 0 on any day that closes
   at or above the trailing `ui_window`-day high).
3. **Ulcer Index, `UI_t`:** `sqrt(mean(ddpct_i^2 for i in the trailing
   ui_window-day window ending at t))` -- the root-mean-square of the
   daily percentage drawdown, computed causally at every trading day's
   close.
4. **Causal, point-in-time percentile rank, `pctile_t` in `[0, 1]`:** the
   fraction of the trailing `pctile_lookback`-day window of `UI` values
   (ending at and including `t`) that are `<= UI_t`. Defaults to 0.5
   (neutral) until `pctile_lookback` days of valid `UI` history exist.
   Same rolling-percentile-rank convention as families 031/035/036/040/
   041/042/044.
5. **Continuous sizing multiplier, `m_t`** (a continuous percentile-scaled
   function, per this iteration's explicit instruction, NOT a discrete
   ladder -- avoiding the discrete-tier cash-cap-nullification failure
   mode families 014/037's own `near_high_mult=1.0` primary configs hit):
   ```
   m_t = clip(1 - k * (2 * pctile_t - 1), min_mult, max_mult)
   ```
   A high `UI` percentile (elevated -- frequent, deep, and/or persistent
   drawdown regime) pushes `m_t` toward `min_mult` (buy less/bank); a low
   `UI` percentile (depressed -- shallow, brief, or absent drawdowns)
   pushes `m_t` toward `max_mult` (buy more/normal). At `pctile_t=0.5`,
   `m_t=1.0` exactly (neutral, plain-deposit weeks).
6. **Order:** `target_buy_usd = weekly_deposit * m_t`, capped at
   `max_lump_multiple * weekly_deposit` and then at available cash (the
   engine's own no-leverage cap, sec 3.2) -- never a sell, never leverage.
   A below-1.0-multiplier week's shortfall banks as cash (earning IRX),
   available to fund a later above-1.0-multiplier week -- the same
   implicit-reserve mechanism families 003/005/014/030/031/035/036/037/
   040/044 use.
7. **Decision cadence:** identical to every other single-asset family in
   this loop -- the multiplier is recomputed at every trading day's close
   (needed because `UI_t`/`pctile_t` change daily), but `target_buy_usd` is
   only non-zero on week-end decision days (one order per asset per
   trading day, satisfying sec 3.4).

## Data inputs

Daily OHLC close of each of the 5 core assets, individually, plus the
daily risk-free rate (IRX) for cash interest -- all sourced via
`src.backtest.v3.data.load_dev()` only. No macro or alternative data (a
price-only signal, like families 001/003/005/014/017/020/021/023/026/028/
030/031/033/034/035/036/037/039/040/041/042/044/045/046/047).

## Parameters (4 of the allowed 5)

| Parameter | Meaning | Grid values | Primary |
|---|---|---|---|
| `ui_window` | Trailing window (days) serving as BOTH the local running-peak reference and the RMS averaging window for the Ulcer Index | `63`, `126` | `126` |
| `pctile_lookback` | Trailing window (days) for the causal percentile rank of `UI_t` within its own recent history | `252`, `504` | `252` |
| `k` | Sensitivity of the multiplier to the percentile rank | `0.5`, `1.0`, `1.5` | `1.0` |
| `min_mult` | Lower clip bound on the multiplier (the "buy less/bank" floor during elevated-`UI` regimes) | `0.25`, `0.5` | `0.5` |

Fixed constants (not grid-varied, to stay within the 5-parameter ceiling
while matching family 044's precedent exactly): `max_mult = 2.0` (the
"buy more/normal" ceiling during depressed-`UI` regimes -- a continuous
bound, not a discrete ladder step), `max_lump_multiple = 3.0` (cash-capped,
no-leverage ceiling on any single week's order relative to the plain
deposit).

## Grid

`ui_window` (2) x `pctile_lookback` (2) x `k` (3) x `min_mult` (2) = **24
configurations** (<= 36 cap, 4 tunable parameters <= 5).

## Primary configuration

`ui_window=126` (a roughly 6-month window, in the middle of the plan's own
suggested 60-126-day range, and long enough to let a genuine multi-month
drawdown regime register fully), `pctile_lookback=252` (one trading year,
matching family 044's own primary choice for direct comparability of the
continuous-percentile-multiplier design across families), `k=1.0`,
`min_mult=0.5` -- **deliberately `< 1.0`, per family 014/037's own explicit
documented lesson** (a `near_high_mult`/floor `>= 1.0` in the primary
config nullifies any reserve funding under the engine's no-leverage cash
cap, since no cash is ever banked in advance to fund a later above-1x
week) -- all chosen before any backtest is run on development data, and
verified pre-grid (per this iteration's task instruction) that the primary
config's realized average cash balance meaningfully differs from DCA's
(see `scripts/v3/run_049_ulcer_index_sizing.py`'s `check_cash_reserve_dynamics`).

## Expected sign of the effect

Positive: the strategy should beat plain DCA on both final wealth and
Sharpe, because it systematically reduces buying only during genuinely
severe (deep-AND-persistent, not merely deep-OR-persistent) drawdown
regimes -- funded entirely by a reserve banked during calmer regimes, never
by leverage -- and because avoiding the single worst capitulation-adjacent
weeks while buying more heavily during calm, low-ulcer regimes should
mechanically raise both terminal wealth and the volatility-adjusted return
relative to a flat deposit schedule that buys the same total dollar amount
irrespective of the drawdown-severity regime.

## Implementation checks to run (sec 3.2, before any results count)

Two-reference-point degenerate-config pattern (families 014/020/031/033/
034/035/036/037/044 precedent):

1. **Explicit bypass flag, matching plain DCA bit-for-bit.** A
   module-level `enabled=False` path that skips the Ulcer Index/percentile
   computation entirely and submits exactly `weekly_deposit` every week.
2. **Second, independent reference point:** the real grid-shaped code path
   `k=0.0` (not the bypass) forces `m_t = clip(1.0, min_mult, max_mult) =
   1.0` for every day regardless of `pctile_t` (since `min_mult < 1.0 <
   max_mult` always holds on the declared grid), verified to also
   reproduce plain DCA bit-for-bit -- this exercises the actual `UI_t`/
   `pctile_t` computation path, unlike check 1.
3. **Ulcer Index formula correctness spot-check** on a known real
   dev-period crash episode (SP500, the well-documented Q4 2018 selloff,
   entirely pre-2020): `UI_t` must spike sharply through the trough and
   decay back down after the recovery, confirmed programmatically.
4. **The required decoupling proofs above** (Proofs 1-3), run and asserted
   before the grid, per this iteration's task instruction.
5. Cash and positions never negative, for both the DCA baseline and the
   primary config, and for an aggressive grid corner.
6. **No-lookahead test:** perturbing all of an asset's OHLC data strictly
   after day `t` must leave every order on/before day `t` unchanged --
   spot-checked at two points deep into the sample, with particular
   attention to the rolling running-peak and RMS computations' causality
   (both are rolling-window statistics that must only ever look backward).
7. Point-in-time macro data: not applicable -- price-only signal.
8. **Total capital deployed never exceeds cumulative deposits plus
   interest**, via the principled "never invest" ceiling bound (family
   021's bugfix-log lesson), not a flat percentage tolerance.
9. **Pre-grid non-degeneracy sanity check:** the primary config's
   multiplier must show real dispersion (not stuck near 1.0 for nearly the
   whole sample) on every asset.
10. **Cash-reserve dynamics check:** confirm the primary config's average
    cash balance meaningfully differs from plain DCA's (per this
    iteration's explicit instruction), and that the reserve is drawn down
    more during high-multiplier (calm/low-`UI`) weeks than during
    low-multiplier (elevated/high-`UI`) weeks.
11. **`PRIMARY_CONFIG` is a member of `grid_configs()`**, asserted at
    import time (families 021/030/036/044's lesson).
12. **No dev-period check ever references a date on/after 2020-01-01 or an
    unseen ticker** -- re-verified explicitly for every real date this
    family's own checks cite (all four dates in Proof 3 above, all
    strictly pre-2020).

## Robustness adaptations (sec 4.3, only if sec 4.1 passes)

Directly following families 003/005/014/037/044's single-asset precedent:
rolling windows (3-year and 5-year for SP500/gold/silver/oil, 2-year for
BTC), block bootstrap (4-week blocks, raw + detrended), and placebo
(circular-shift the daily `UI_t`/`pctile_t` signal, since it is this
family's timing/regime signal in the sec 4.3 sense). Bootstrap/placebo run
counts scoped to **~60 simulations each** (established time-budget
convention), time-boxed per this iteration's explicit instruction: if
sec 4.2 or sec 4.3's earliest legs already decisively fail, the loop stops
early and logs the gap explicitly rather than completing every leg. Sec
4.3 is only run in full if sec 4.1 passes first, per established
precedent.
