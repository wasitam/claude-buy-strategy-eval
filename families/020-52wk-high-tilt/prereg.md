# Family 020: 52-week-high proximity momentum tilt

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

George, T.J. and Hwang, C.-Y. (2004), "The 52-Week High and Momentum
Investing," *Journal of Finance* 59(5), 2145-2176. Seed research queue idea
#20 (research-loop-plan-v3.md sec 7.3 / `state/research_queue.md`): "buy
size scales up as an asset's own trailing close approaches (or sits at/near)
its trailing 52-week high, scales down the further below it the price sits
-- a price-anchoring momentum signal, price-only (no external data
dependency), testable identically on all 5 core assets."

## Mechanism ("why would this work, and who is on the other side?")

George & Hwang's central empirical finding is that a stock's (or asset's)
**nearness to its own 52-week high** predicts near-term continuation, and
that this forecasting power is *separate from, and additive to*, plain
trailing-return momentum (Jegadeesh & Titman 1993 style signals, the same
family of signal already tested in this loop as family 005's sign-only
12-month return sizing). Their explanation is an anchoring-and-adjustment
story (Tversky & Kahneman 1974): investors use the 52-week high as a highly
salient reference point and are reluctant to bid a price all the way up to
a new high even when fundamental news fully justifies it, so the market's
response to genuinely good news is muted exactly while price sits close to
(but has not yet cleared) its high; the news gets slowly and only partially
incorporated, generating a short-run continuation drift as later buyers
adjust their anchor upward and price catches up. Conversely, when price is
far below its 52-week high, investors anchor on how much has already been
lost from the recent peak and are reluctant to buy even on good news
("it can't be a real bottom, it's still 40% off the high"), which the
literature associates with continued underperformance (weaker forward
returns) rather than the strong "underwater = discount, buy more" story
this loop's own family 014 (drawdown-from-high reserve deployment) tested
and found no support for.

**Who is on the other side?** Investors who mechanically anchor on the
52-week-high reference point and under-react to news near it are the
counterparties funding the effect -- by construction, they are slower to
bid price up to a new high than fundamentals warrant, so a rule that buys
disproportionately into that under-reaction window is systematically taking
the other side of their reluctance. A flat-DCA investor (this family's own
benchmark) is simply indifferent to the signal and captures none of this
tilt either way. The mechanism can fail if the anchoring effect has been
arbitraged away in the post-2004-publication period (a standard
"discovered anomaly decays" risk, flagged honestly here before any
backtest), or if a given core asset's price-discovery process (e.g. BTC,
which trades continuously with a much shorter and more volatile history)
does not share the equity-market institutional structure (analyst coverage,
staggered information diffusion, retail anchoring on a salient 52-week
number reported in financial media) that George & Hwang's original
mechanism relies on.

## Category

**Trend / time-series momentum exit** (research-loop-plan-v3.md sec 4.5) --
matches the seed queue's own categorization of idea #20.

## The required triple distinction (task instruction: get this right before
running the grid, especially the family-014 sign point)

### vs. family 001 (10-month/200-day trend exit, REJECTED)
Family 001 is a **binary** in/out switch: fully invested in the market when
price is above a trailing moving average, fully parked in cash (100% out)
when below it. This family is **always invested** (it never exits to 100%
cash by rule -- see "exact rules" below) and its signal is a **continuous
proximity ratio** (price relative to the trailing 52-week high), not a
binary above/below-average state relative to a smoothed trend line. The
reference object is also different: a moving average (recomputed from a
rolling window of many recent prices, itself smoothly trending) vs. a
52-week-high (a single running maximum of past closes, a ratchet that only
ever holds steady or steps up).

### vs. family 005 (time-series momentum sizing, NEAR-MISS)
Family 005's signal is the **sign** of the trailing 12-month **total
return** (`close_t/close_{t-252}-1 > 0` or `<0`) -- a return-based,
two-state (positive/negative) signal with no reference to any specific
past price level. This family's signal is the **level** of price relative
to a specific anchor price (the trailing 52-week high) -- a continuous
ratio `prox_t = close_t / high52_t in (0, 1]` that can be, e.g., 0.97 or
0.60, not merely "positive" or "negative." The two signals frequently
disagree: an asset that is up 8% over the trailing year but has pulled back
15% from an interim high set 3 months ago has `mom_t > 0` (family 005 says
"buy more") while sitting at `prox_t = 0.85` under a plausible near-thresh
of 0.95 (this family's ladder would size it in its *middle*, not top,
tier) -- the two signals are measuring genuinely different things
(direction of the whole trailing year vs. distance from the single highest
price point within a rolling 52-week window) and George & Hwang's own
finding is precisely that 52-week-high proximity forecasts **in addition
to**, not merely as a restatement of, trailing-return momentum.

### vs. family 014 (drawdown-from-high reserve deployment, REJECTED) --
the sign-inversion point the task flags as most important

Family 014 also anchors on a running maximum of past price (`ATH_t`, but
**all-time**, i.e. the full-history or a many-years-capped expanding/
rolling maximum) and computes a drawdown depth `dd_t = 1 - close_t/ATH_t`.
**Family 014's ladder INCREASES the buy multiplier the FURTHER below the
reference the price sits** (`near_high_mult` a low/neutral baseline near
the high, `mult_tier1 < mult_tier2` rising as `dd_t` deepens) -- a
value/mean-reversion logic: buy more the deeper underwater, on the theory
that large drawdowns from an all-time high are followed by
above-average forward returns.

**This family (idea #20) does the mechanical opposite: it INCREASES the
buy multiplier the CLOSER to the reference the price sits, and DECREASES
it the further below.** Concretely, defining this family's own proximity
ratio `prox_t = close_t / high52_t in (0, 1]` (the mirror image of family
014's `dd_t = 1 - close_t/ATH_t`, since `prox_t = 1 - dd52_t` using a
52-week rather than all-time high), the ladder multiplier `m_t` is
**increasing** in `prox_t` (equivalently, decreasing in `dd52_t`) -- the
literal opposite monotonic relationship from family 014's `m_t` increasing
in `dd_t`. This is a momentum/trend-continuation logic (buy more near a
recent high because under-reaction near a salient anchor predicts further
upside), the polar opposite of family 014's value/mean-reversion logic (buy
more far below an all-time high because deep drawdowns predict a rebound).

**And the reference window itself is different and shorter:** family 014
uses the asset's **all-time** high (optionally capped at a 10-year rolling
window, still far longer than a year), a reference that can go years
without changing at all during a sustained drawdown, encoding "how far
below the best price ever recorded." This family uses a strictly **trailing
52-week** (~1-year) high, a reference that resets on a much shorter,
rolling annual cadence and can never reflect a multi-year-old peak, encoding
"how close to the best price seen in roughly the last year." A single asset
can simultaneously read as "far below its all-time high" (family 014's
`dd_t` large) while also reading as "at or very near its own 52-week high"
(this family's `prox_t` near 1, if the all-time high was set years before
the current 52-week window) -- the two signals are not two parameterizations
of the same statistic, they can and do point in opposite directions on the
same asset on the same day.

**Sign-correctness verification, run before trusting any grid result (task
instruction):** because the intended sign is the literal inverse of family
014's, the implementation checks below include an explicit empirical
assertion, run on real SP500 development data before the grid, that days
in the top quartile of `prox_t` (closest to the 52-week high) have a
**strictly higher** mean buy multiplier than days in the bottom quartile
(furthest below it) -- catching a sign bug (e.g. an accidentally-inverted
ladder lookup that would silently reproduce family 014's logic instead)
before any backtest number is trusted.

## Win-rule interpretation

Assessed as a **single-asset family** (sec 4.1's "Single-asset" line, per
the seed queue's own framing and this loop's established precedent for
per-asset internal signals -- same as families 001/003/005/014/017): beats
DCA on final wealth AND Sharpe on at least 3 of the 5 core assets, at both
fee levels, using the existing single-asset `engine.py` unmodified -- this
signal is entirely per-asset, using each asset's own price history only,
exactly like families 001/003/004/005/006/007/014/016/017.

## Exact rules

Computed independently for each asset, using only that asset's own OHLC
close prices, causally (no lookahead):

1. **Trailing 52-week high, `high52_t`,** two window definitions:
   - **`trading252`:** a rolling causal maximum over the trailing 252
     trading days (`max(close_{t-251}, ..., close_t)`, falling back to the
     expanding max while fewer than 252 observations exist) -- the
     standard "52 trading weeks" convention used elsewhere in this loop
     (e.g. family 005's `lookback_days=252` momentum window).
   - **`calendar`:** a rolling causal maximum over the trailing 365
     calendar days on the asset's own trading-day index (implemented as a
     date-indexed rolling window, `close.rolling("365D").max()`), which can
     include a slightly different number of trading days depending on
     holidays/weekends -- the literal "52 weeks" reading George & Hwang use
     (a fixed calendar span, not a fixed trading-day count).
   Both are causal by construction (a rolling/expanding maximum computed
   only from `close_0..close_t`, verified by the no-lookahead check below).
2. **Proximity ratio:** `prox_t = close_t / high52_t`, always `<= 1`
   because `high52_t` is a running maximum that includes `close_t` itself
   (so `prox_t = 1.0` exactly on any day the asset closes at a new 52-week
   high).
3. **Ladder multiplier, `m_t`,** a discrete step function of `prox_t` with
   two breakpoints `(far_thresh, near_thresh)` and three tier multipliers
   `(mult_far, mult_mid, mult_near)`, **increasing in `prox_t`** (the
   inverse ordering of family 014's ladder, which increases in `dd_t`,
   i.e. decreases in `prox_t`):
   - `prox_t < far_thresh` (far below the 52-week high): `m_t = mult_far`
     (smallest buy).
   - `far_thresh <= prox_t < near_thresh`: `m_t = mult_mid`.
   - `prox_t >= near_thresh` (at/near the 52-week high): `m_t = mult_near`
     (largest buy -- the "buy MORE near the high" element of the family,
     required `mult_near > mult_mid > mult_far`, i.e. `mult_near > 1`).
4. **Order:** `buy_usd_t = min(weekly_deposit * m_t, weekly_deposit *
   max_lump_cap)`, never a sell. The engine's own cash cap (sec 3.2:
   `buy_usd <= cash`) enforces "cash-capped, no leverage" mechanically -- a
   below-1x week (`m_t < 1`, when price is far below its 52-week high)
   banks the unspent share of that week's deposit as cash (earning IRX),
   which becomes available to fund a later above-1x week once price moves
   back near a 52-week high -- the same implicit-reserve pattern already
   used and accepted for families 003, 005 and 014. `max_lump_cap` is a
   hard ceiling on how large a single week's buy can be relative to the
   plain $500 deposit, independent of how much banked cash is available.
5. **Decision cadence:** the multiplier is recomputed at every trading
   day's close (needed because `high52_t`/`prox_t` change daily), but
   since deposits only arrive on each week's last trading day,
   `buy_usd_t` is only non-zero on week-end decision days -- identical
   cadence to every other single-asset family in this loop.

## Data inputs

Daily OHLC close of each of the 5 core assets, individually, plus the
daily risk-free rate (IRX) for cash interest -- all sourced via
`src.backtest.v3.data.load_dev()` only. No macro or alternative data
(price-only signal).

## Parameters (4 of the allowed 5)

| Parameter | Meaning | Grid values | Primary |
|---|---|---|---|
| `window_def` | 52-week-high window definition | `trading252`, `calendar` | `trading252` |
| `ladder` | Bundled `(far_thresh, near_thresh, mult_far, mult_mid)` preset (see below) -- one logical parameter selecting among named presets, same bundling convention family 014 used | `mild`, `moderate`, `aggressive`, `flat` | `moderate` |
| `mult_near` | Buy multiplier while `prox_t >= near_thresh` (the "buy MORE near the high" regime) | `1.5`, `2.0` | `1.5` |
| `max_lump_cap` | Ceiling on `buy_usd` as a multiple of the plain $500 deposit | `2.0`, `3.0` | `3.0` |

**Ladder presets** (bundling `far_thresh`, `near_thresh`, `mult_far`,
`mult_mid` into one selectable parameter, mirroring family 014's bundling
convention but with the tier ordering inverted -- `mult_far < mult_mid <
mult_near` throughout, buy size RISING with proximity to the high):

| Preset | `far_thresh` | `near_thresh` | `mult_far` | `mult_mid` |
|---|---|---|---|---|
| `mild` | 0.80 | 0.95 | 0.65 | 0.85 |
| `moderate` (primary) | 0.80 | 0.95 | 0.50 | 0.75 |
| `aggressive` | 0.70 | 0.97 | 0.30 | 0.60 |
| `flat` | 0.80 | 0.95 | 1.0 | 1.0 |

`flat` is the family's **true zero-effect grid arm** (see "Implementation
checks" below): with `mult_far = mult_mid = 1.0`, *when also paired with*
`mult_near = 1.0` (not a grid value, but exercised directly by the
zero-effect implementation check), `m_t = 1.0` for every day regardless of
`prox_t` -- i.e. a real, independently-computed member of the signal-
computation code path (not a special bypass) that is expected, by
construction, to reduce to plain DCA once every tier multiplier is 1.0.

## Grid

`window_def` (2) x `ladder` (4) x `mult_near` (2) x `max_lump_cap` (2) =
**32 configurations** (<= 36 cap, 4 tunable parameters <= 5).

## Primary configuration

`window_def=trading252` (the standard trading-day convention used
elsewhere in this loop, e.g. family 005's 252-day lookback, and the
simpler, unambiguous reading of "52 weeks" for a daily engine), `ladder=
moderate` (a middle-of-the-road preset, not the most aggressive), `mult_
near=1.5` (a meaningful but not extreme tilt at the high, chosen before
seeing any results), `max_lump_cap=3.0` (generous enough not to bind the
primary ladder's own 1.5x ceiling, so the cap is a genuine tail control
rather than a routinely-binding constraint) -- all chosen before any
backtest is run on development data.

## Expected sign of the effect

Positive: the strategy should beat plain DCA on both final wealth and
Sharpe, because it buys systematically more of each asset while price sits
near its own trailing 52-week high (per George & Hwang's continuation
finding, under-reaction near a salient anchor point predicts further
near-term upside) and systematically less while price sits far below that
recent high (avoiding disproportionate exposure during the anchoring-driven
under-reaction to bad news the same literature associates with continued
underperformance), funded entirely by deposits the strategy itself banked
during far-below-high periods rather than by leverage or externally
sourced capital.

## Implementation checks to run (sec 3.2, before any results count) --
two-reference-point pattern (per family 014's precedent) plus an explicit
sign check

1. **Explicit bypass flag, matching plain DCA bit-for-bit.** A module-level
   `enabled=False` path that skips the proximity/ladder computation
   entirely and submits exactly `weekly_deposit` as the buy order every
   week, no sells -- checked against `v3chk.check_degenerate_equals_dca`.
2. **True zero-effect grid arm, verified independently against plain DCA.**
   The real grid configuration `ladder=flat` combined with `mult_near=1.0`
   (any `window_def`/`max_lump_cap`, since neither affects the result once
   every tier's multiplier is 1.0) is run through the *actual*
   proximity/ladder computation (`enabled=True`, not the bypass path) and
   its resulting units/cash path is checked bit-for-bit against an
   independently-run plain-DCA reference -- confirming the ladder-based
   signal path itself, not just the bypass flag, collapses to DCA when
   every tier multiplier is 1.0. `mult_near=1.0` is not itself a pre-
   declared grid value (the grid only explores `1.5`/`2.0`), so this
   zero-effect configuration is run as a direct code-path check rather
   than counted as one of the 32 pre-declared grid trials.
3. Cash and positions never negative, for both the DCA baseline and the
   primary config.
4. **No-lookahead test, with particular attention to the 52-week-high
   tracker's causality** (task instruction): perturbing all of an asset's
   OHLC data strictly after day `t` must leave every order on/before day
   `t` unchanged. Because `high52_t` is computed from a strictly causal
   rolling/expanding maximum over `close_0..close_t` only (never `close_
   {t+1}` or later), this check specifically confirms no future high can
   leak backward into `high52_t` at any earlier `t`. Run at a spot-check
   deep into the sample, per prior families' precedent.
5. Point-in-time macro data: not applicable -- price-only signal, no
   ALFRED-vintage macro series.
6. **Total capital deployed never exceeds cumulative deposits plus
   interest** (task instruction): confirmed by construction, since
   `buy_usd_t = min(..., cash)` inside the engine already forbids spending
   more than is on hand, and verified empirically as an additional sanity
   bound on cumulative buys vs. cumulative deposits, following family
   014's precedent, for the primary config and the most aggressive grid
   corner (`ladder=aggressive, mult_near=2.0, max_lump_cap=3.0`).
7. **Pre-grid non-degeneracy sanity check** (established convention, task
   instruction, adapted here for this family's ladder shape): the primary
   config's 3-tier ladder has no tier equal to exactly 1.0x (mult_far=0.50,
   mult_mid=0.75, mult_near=1.5), so `m_t != 1.0` trivially on ~100% of
   days by construction -- not itself a meaningful non-degeneracy signal
   for this family. The substantive check instead confirms price is not
   stuck in a single ladder tier for nearly the whole development sample:
   each of the near-high, middle, and far-below-high tiers must claim
   between 2% and 98% of development days, on each of the 5 core assets,
   before any grid backtest is trusted. This is the meaningful analogue,
   for a 3-tier ladder, of the binary-signal convention used in prior
   families (e.g. 019's weak/strong regime frequency check).
8. **Sign-correctness check** (task instruction, required specifically for
   this family given the family-014 sign-inversion point above): on SP500
   development data, using the primary config, confirm the mean buy
   multiplier on days in the top quartile of `prox_t` (closest to the
   52-week high) is **strictly greater than** the mean buy multiplier on
   days in the bottom quartile (furthest below the 52-week high) -- i.e.
   near-high days get systematically LARGER buy orders than far-below-high
   days, verifying the ladder is not accidentally wired with family 014's
   inverted sign.

## Robustness adaptations (sec 4.3, only if sec 4.1 passes)

Directly following families 003/005/006/007/014/017's single-asset
precedent: rolling windows (3-year and 5-year for SP500/gold/silver/oil,
2-year for BTC, per sec 4.3's own text), block bootstrap (4-week blocks,
raw + detrended), and placebo (circular-shift the daily `prox_t` proximity
signal, since it is this family's timing signal in the sec 4.3 sense).
Bootstrap/placebo run counts scoped to **60 simulations each**
(established time-budget convention), declared here before any backtest,
actual count confirmed again in results.md. Sec 4.3 is only run in full if
sec 4.1 passes first, per prior families' precedent.
