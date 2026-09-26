# Family 034: 52-week-low proximity contrarian tilt

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Contrarian / buy-the-dip value literature: the "52-week low effect" strand
that runs alongside (and, per several authors, independently of) George &
Hwang's own 52-week-high momentum finding -- see George, T.J. and Hwang,
C.-Y. (2004), "The 52-Week High and Momentum Investing," *Journal of
Finance* 59(5), 2145-2176, which itself notes that the 52-week LOW carries
separate predictive information from the 52-week HIGH, and the broader
buy-the-dip / mean-reversion-near-lows literature (e.g. Lehmann (1990) and
Jegadeesh (1990) short-horizon contrarian reversal work, and practitioner
"buy near 52-week lows" value screens, e.g. as popularized by O'Higgins-
style and Graham-descended low-price-relative-to-range screens). Seed
research queue idea #34 (research-loop-plan-v3.md sec 7.3 /
`state/research_queue.md`): "buy MORE as an asset's own trailing close
approaches (or sits at/near) its trailing 52-week LOW, scale DOWN the
further ABOVE it the price sits -- a contrarian/value-style signal on
distance-from-52-week-low (the opposite reference point and opposite sign
from family 020's 52-week-HIGH proximity momentum tilt, which buys MORE
near the high)."

## Mechanism ("why would this work, and who is on the other side?")

The core empirical claim, distinct from and in some tellings opposite to
George & Hwang's 52-week-HIGH continuation finding, is that proximity to an
asset's own trailing 52-week LOW is associated with a subsequent
**mean-reverting rebound**, not continued weakness:

1. **Anchoring-driven overreaction near a salient low, not underreaction.**
   The same anchoring-and-adjustment psychology (Tversky & Kahneman 1974)
   that George & Hwang use to explain underreaction near the 52-week HIGH
   has a documented mirror-image reading near the 52-week LOW: investors
   anchor on "how far this has fallen" and become disproportionately
   reluctant to buy exactly when a price is cheapest relative to its own
   recent range, over-extrapolating recent bad news and pushing price below
   what fundamentals justify (a short-horizon overreaction, in the
   De Bondt & Thaler (1985) contrarian tradition and the Lehmann
   (1990)/Jegadeesh (1990) short-horizon reversal literature), which then
   partially corrects once the selling pressure exhausts itself.
2. **Tax-loss selling and calendar-driven liquidity effects concentrate
   indiscriminate selling near 52-week lows**, particularly toward
   calendar year-end (the "January effect" literature), pushing price
   temporarily below fair value for reasons unrelated to the asset's own
   fundamentals -- a liquidity-provision rationale for why a disciplined,
   mechanical buyer stepping in near the low can earn a rebound that has
   nothing to do with forecasting skill.
3. **Behavioral capitulation.** Retail investors are well documented to cut
   or halt contributions exactly when an asset sits near its own trailing
   low (the same behavioral-finance DCA-interruption pattern cited in this
   loop's own family 014 prereg.md), so a rule that instead pre-commits to
   buying MORE there is, as with family 014, a disciplined counter to a
   known bad habit -- but via a different, shorter, and mechanically
   opposite-facing reference point (52-week LOW proximity, not all-time
   drawdown DEPTH; the distinction is made rigorous below).

**Who is on the other side?** Investors who panic-sell or freeze
contributions near a 52-week low, and momentum traders who short or avoid
assets precisely because they are near a fresh low (a "falling knife"
heuristic), are the plausible counterparties funding any measured effect --
this strategy is systematically buying into exactly the price weakness
those participants are selling into or avoiding. A flat-DCA investor (this
family's own benchmark) is indifferent to the signal and captures none of
the tilt either way. **This mechanism can fail, and the failure mode should
be stated honestly before any backtest is run:** a 52-week low can also
mark the start of a genuine structural decline (not every cheap price
rebounds -- the same "this drawdown never recovers" risk flagged in family
014's own prereg.md), and if the market has already priced in the
52-week-low anchoring effect post-publication of this literature, the
effect may be arbitraged away, particularly on the most liquid asset in
this universe (SP500). BTC in particular has no tax-loss-selling calendar
effect in the traditional sense and a much shorter, more volatile history,
so mechanism (2) above plausibly does not transfer to it at all.

## Category

**Sizing / valuation** (research-loop-plan-v3.md sec 4.5). The task brief
offered a choice between this and another sec 4.5 category; **Sizing /
valuation** is used because the signal's economic content is "how cheap is
this asset relative to its own recent trading range" (a valuation-style,
price-level anchor, exactly the framing the seed queue itself uses --
"Sizing / valuation" is the queue's own listed category for idea #34) --
not a trend-following continuation signal (which would be "Trend /
time-series momentum exit", the category family 020's opposite-signed
proximity-to-HIGH tilt correctly uses instead, precisely because that
family's economic story IS continuation/momentum). This family shares its
category with family 014 (drawdown-from-all-time-high reserve deployment),
which is expected and appropriate -- both are contrarian, valuation-style
sizing rules -- and the required rigorous distinction from family 014 is
made in full below.

## Why testing both this family (buy MORE near a 52-week LOW) and family
020 (buy MORE near a 52-week HIGH) is legitimate, not p-hacking

Both families are "distance from a 52-week extreme" constructions, so this
point must be made explicitly and honestly, per the task instruction.

**These are two independently-motivated, competing hypotheses from
separate literatures, not the same idea re-run with a flipped sign to see
which one happens to work:**

- Family 020's hypothesis (George & Hwang 2004) is a **continuation/
  underreaction** story: investors anchor on the 52-week HIGH and are slow
  to bid price up to a new high even on genuinely good news, so price near
  (but below) a fresh high keeps drifting up as the anchor is slowly
  revised -- an argument for buying MORE as price approaches the high,
  because being near the high is itself (weak) evidence of unexploited good
  news working through the market.
- This family's hypothesis (the De Bondt & Thaler 1985 / Lehmann 1990 /
  Jegadeesh 1990 short-horizon contrarian-reversal tradition, plus
  tax-loss-selling liquidity effects) is a **reversal/overreaction** story:
  investors anchor on the 52-week LOW and overreact to the bad news that
  put the price there, pushing it below fair value; the correction of that
  overreaction, not a continuation of it, is what a rule buying MORE near
  the low is trying to harvest.

Both effects have real, separate, peer-reviewed empirical support (the
citations above are not the same paper read two ways -- George & Hwang's
own high-proximity result and the classical short-horizon reversal
literature are different papers, different mechanisms, and, notably, not
even mutually exclusive: an asset can display high-proximity continuation
AND low-proximity reversal simultaneously, since they describe behavior at
opposite ends of the same 52-week range and needn't be mirror images of
each other statistically). Testing both directions is exactly the kind of
"two competing, independently pre-registered hypotheses, whichever the
data actually supports (if either) gets reported honestly" process sec 7.1
describes, not a search over signs until one clears the bar -- family 020
was pre-registered and assessed (NEAR-MISS) as its own family, on its own
schedule, entirely before this family's own pre-registration was written,
and this family's rules, grid and primary configuration are fixed here,
before any backtest, independent of family 020's already-known result.

## Distinction from family 020 (52-week-HIGH proximity momentum tilt)

Required by task instruction, made explicit and mechanical, not just
verbal:

| | Family 020 | Family 034 (this family) |
|---|---|---|
| Reference point | Trailing 52-week **HIGH**, `high52_t` | Trailing 52-week **LOW**, `low52_t` |
| Reference is a running... | **maximum** (ratchets up or holds, never falls) | **minimum** (ratchets down or holds, never rises) |
| Proximity ratio | `prox_t = close_t / high52_t <= 1`, `=1` on a new high | `prox_low_t = low52_t / close_t <= 1`, `=1` on a new low |
| Ladder direction | Buy multiplier **increases** as `prox_t` rises (closer to the high -> BIGGER buy) | Buy multiplier **increases** as `prox_low_t` rises (closer to the low -> BIGGER buy) |
| Economic story | Momentum / continuation (anchoring causes underreaction to good news near a high) | Contrarian / mean-reversion (anchoring causes overreaction to bad news near a low) |
| "Otherwise" tier | `mult_far` (far BELOW the high) `< 1`, smallest buy | `mult_far` (far ABOVE the low) `< 1`, smallest buy |
| "Signal" tier | `mult_near` (AT/NEAR the high) `> 1`, largest buy | `mult_near` (AT/NEAR the low) `> 1`, largest buy |

The two signals are **not** the same statistic with a relabeled sign: on
any given day, an asset's `prox_t` (distance below its own 52-week HIGH)
and `prox_low_t` (distance above its own 52-week LOW) are computed from two
different running extrema and can, and typically do, disagree about which
"tier" the asset is in -- an asset sitting exactly in the middle of its own
52-week range reads as roughly "mid-tier" on BOTH signals simultaneously,
while an asset that has been range-bound near a single price level for
months (52-week high and low close together) can read as simultaneously
"near its high" and "near its low" on the same day, something impossible
for two signals that were really the same construction with an inverted
sign. **Concrete numeric check (task instruction, run on real SP500
development data before trusting the grid, reported in results.md):**
compute the fraction of development days on which family 020's `prox_t`
tier and this family's `prox_low_t` tier disagree (are not both
simultaneously "near-extreme" or both simultaneously "far-from-extreme"),
confirming the two signals are not near-perfectly (anti)correlated
restatements of one another.

**Sign-correctness verification, run before trusting any grid result (task
instruction, mirroring family 020's own required check, this time guarding
against the opposite mistake -- accidentally re-implementing family 020's
own high-proximity logic under a new name):** on SP500 development data,
using the primary config, confirm the mean buy multiplier on days in the
**top quartile of `prox_low_t`** (closest to the 52-week LOW) is
**strictly greater than** the mean buy multiplier on days in the **bottom
quartile of `prox_low_t`** (furthest above the 52-week LOW, i.e. closest to
the 52-week HIGH) -- i.e. near-LOW days get systematically LARGER buy
orders than far-above-the-low (near-high) days, the literal opposite
verification target from family 020's own check.

## Distinction from family 014 (drawdown-from-all-time-high reserve
deployment, REJECTED)

Required by task instruction, made explicit and mechanical:

1. **Different reference window length.** Family 014 anchors on the
   asset's **all-time** high (optionally capped at a long, multi-year
   rolling window per its own prereg.md) -- a reference that can go years
   without changing during a sustained drawdown. This family anchors on a
   strictly **trailing 52-week** (~1-year) LOW -- a reference that resets
   on a much shorter, rolling annual cadence and can never reflect a
   multi-year-old trough. A single asset can simultaneously read as "deep
   in drawdown from its all-time high" (family 014's `dd_t` large) while
   also reading as "well ABOVE its own 52-week low, in the middle of a
   grinding-up-from-the-bottom rally" (this family's `prox_low_t` small,
   the "otherwise"/small-buy tier) -- the two signals are not two
   parameterizations of the same statistic and routinely disagree on the
   same asset on the same day.
2. **Different reference point (HIGH vs. LOW) entirely, not merely a
   different window on the same extremum.** Family 014's `dd_t = 1 -
   close_t/ATH_t` measures distance below a running **maximum** (a high).
   This family's `prox_low_t = low52_t/close_t` measures proximity to a
   running **minimum** (a low). These are conceptually and mechanically
   different reference objects (a peak vs. a trough), not the same
   reference object read over a different lookback window -- unlike, say,
   testing "52-week high" vs. "26-week high" against the same underlying
   idea, which WOULD be a parameter re-test of the same reference. Swapping
   the reference from a maximum to a minimum is a materially different
   construction, matching this task's framing exactly ("different window
   length AND different functional form").
3. **Different functional form.** Family 014 uses a **discrete drawdown-
   depth ladder** with multiple named tiers stepping up as `dd_t` deepens
   through several explicit thresholds (per its own prereg.md's ladder
   table). This family's primary construction is likewise a discrete
   3-tier step ladder (matching this loop's established convention for
   proximity-based sizing, e.g. family 020's own 3-tier ladder) but keyed
   to `prox_low_t` (a ratio of the LOW to the current close, bounded in
   `(0, 1]`) rather than family 014's `dd_t` (a ratio of the shortfall
   below an all-time high, also bounded in `[0, 1)` but computed from the
   opposite extremum) -- the **grid's window-length parameter itself**
   (`window_def`, `trading252` vs. `calendar`) also has no analogue in
   family 014's all-time-anchored design, since family 014's reference does
   not reset annually at all.

Because family 014's own `dd_t` and this family's own `prox_low_t` are
literally computed from different price extrema (a maximum vs. a minimum)
over different window lengths, no numeric identity or near-identity check
is possible the way it is for family 020 above (where both `prox_t` and
`prox_low_t` are ratios of the SAME window-length class of extremum, just
opposite ends of the range) -- the distinction here is structural, not a
matter of the two signals merely disagreeing on some days.

## Win-rule interpretation

Assessed as a **single-asset family** (sec 4.1's "Single-asset" line),
across all 5 core assets, using the existing single-asset `engine.py`
unmodified -- this signal is entirely per-asset, using each asset's own
price history only, exactly like families 001/003/005/014/017/020/021/023/
026/028/030/031/033.

## Exact rules

Computed independently for each asset, using only that asset's own OHLC
close prices, causally (no lookahead):

1. **Trailing 52-week low, `low52_t`,** two window definitions (mirroring
   family 020's own two window definitions for its 52-week HIGH):
   - **`trading252`:** a rolling causal minimum over the trailing 252
     trading days (`min(close_{t-251}, ..., close_t)`, falling back to the
     expanding min while fewer than 252 observations exist).
   - **`calendar`:** a rolling causal minimum over the trailing 365
     calendar days on the asset's own trading-day index
     (`close.rolling("365D").min()`).
   Both are causal by construction (a rolling/expanding minimum computed
   only from `close_0..close_t`, verified by the no-lookahead check below).
2. **Proximity-to-low ratio:** `prox_low_t = low52_t / close_t`, always
   `<= 1` because `low52_t` is a running minimum that includes `close_t`
   itself (so `prox_low_t = 1.0` exactly on any day the asset closes at a
   new 52-week low).
3. **Ladder multiplier, `m_t`,** a discrete step function of `prox_low_t`
   with two breakpoints `(far_thresh, near_thresh)` and three tier
   multipliers `(mult_far, mult_mid, mult_near)`, **increasing in
   `prox_low_t`** (buy MORE the closer to the low, i.e. buy MORE the
   SMALLER `close_t` is relative to `low52_t`'s own scale):
   - `prox_low_t < far_thresh` (far ABOVE the 52-week low): `m_t =
     mult_far` (smallest buy -- required `mult_far < 1.0`, per family 033's
     lesson, so a cash reserve actually accumulates during the far-above-
     low "normal" state).
   - `far_thresh <= prox_low_t < near_thresh`: `m_t = mult_mid`.
   - `prox_low_t >= near_thresh` (AT/near the 52-week low): `m_t =
     mult_near` (largest buy -- the "buy MORE near the low" element of the
     family, required `mult_near > mult_mid > mult_far`, i.e.
     `mult_near > 1`).
4. **Order:** `buy_usd_t = min(weekly_deposit * m_t, weekly_deposit *
   max_lump_cap)`, never a sell. The engine's own cash cap (sec 3.2:
   `buy_usd <= cash`) enforces "cash-capped, no leverage" mechanically -- a
   below-1x week (`m_t < 1`, when price is far above its 52-week low, i.e.
   the normal/no-signal state) banks the unspent share of that week's
   deposit as cash (earning IRX), which becomes available to fund a later
   above-1x week once price falls back near a 52-week low -- the same
   implicit-reserve pattern already used and accepted for families 003,
   005, 014 and 020. `max_lump_cap` is a hard ceiling on how large a single
   week's buy can be relative to the plain $500 deposit, independent of how
   much banked cash is available.
5. **Decision cadence:** the multiplier is recomputed at every trading
   day's close (needed because `low52_t`/`prox_low_t` change daily), but
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
| `window_def` | 52-week-low window definition | `trading252`, `calendar` | `trading252` |
| `ladder` | Bundled `(far_thresh, near_thresh, mult_far, mult_mid)` preset (see below) -- one logical parameter selecting among named presets, same bundling convention families 014/020 used | `mild`, `moderate`, `aggressive`, `flat` | `moderate` |
| `mult_near` | Buy multiplier while `prox_low_t >= near_thresh` (the "buy MORE near the low" regime) | `1.5`, `2.0` | `1.5` |
| `max_lump_cap` | Ceiling on `buy_usd` as a multiple of the plain $500 deposit | `2.0`, `3.0` | `3.0` |

**Ladder presets** (bundling `far_thresh`, `near_thresh`, `mult_far`,
`mult_mid` into one selectable parameter, mirroring family 020's own
bundling exactly, with the tier lookup keyed to `prox_low_t` instead of
`prox_t` -- `mult_far < mult_mid < mult_near` throughout, buy size RISING
as the price approaches the LOW):

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
`prox_low_t` -- i.e. a real, independently-computed member of the signal-
computation code path (not a special bypass) that is expected, by
construction, to reduce to plain DCA once every tier multiplier is 1.0.

**Per family 033's lesson (task instruction, verified before running the
grid):** the primary configuration's "far above the low" (normal/no-signal)
tier multiplier is `mult_far = 0.50`, strictly below 1.0 -- a genuine cash
reserve accumulates during normal/far-from-low periods (unlike family 033's
`normal_buy_mult = 1.0`, which starved its own rare-trigger mechanism via
the engine's cash cap). This is verified pre-grid, in the run script,
before the grid is trusted: see "Pre-grid non-degeneracy and cash-reserve
sanity check" below.

## Grid

`window_def` (2) x `ladder` (4) x `mult_near` (2) x `max_lump_cap` (2) =
**32 configurations** (<= 36 cap, 4 tunable parameters <= 5).

## Primary configuration

`window_def=trading252` (the standard trading-day convention used
elsewhere in this loop, e.g. family 005's 252-day lookback and family 020's
own primary), `ladder=moderate` (a middle-of-the-road preset, not the most
aggressive), `mult_near=1.5` (a meaningful but not extreme tilt at the low,
chosen before seeing any results), `max_lump_cap=3.0` (generous enough not
to bind the primary ladder's own 1.5x ceiling, so the cap is a genuine tail
control rather than a routinely-binding constraint) -- all chosen before
any backtest is run on development data, and deliberately mirroring family
020's own primary-configuration choices numerically so that any difference
in outcome between the two families is attributable to the sign/reference-
point difference rather than to different tuning generosity.

## Expected sign of the effect

Positive: the strategy should beat plain DCA on both final wealth and
Sharpe, because it buys systematically more of each asset while price sits
near its own trailing 52-week low (per the contrarian short-horizon
reversal literature, anchoring-driven overreaction near a salient low
predicts a rebound) and systematically less while price sits far above
that recent low (avoiding disproportionate exposure once the cheap-relative-
to-recent-range window has closed), funded entirely by deposits the
strategy itself banked during far-above-low periods rather than by leverage
or externally sourced capital.

## Implementation checks to run (sec 3.2, before any results count) --
two-reference-point pattern (per families 014/020's precedent) plus an
explicit sign check guarding against the opposite mistake from family 020's

1. **Explicit bypass flag, matching plain DCA bit-for-bit.** A module-level
   `enabled=False` path that skips the proximity/ladder computation
   entirely and submits exactly `weekly_deposit` as the buy order every
   week, no sells -- checked against `v3chk.check_degenerate_equals_dca`.
2. **True zero-effect grid arm, verified independently against plain DCA.**
   The real grid configuration `ladder=flat` combined with `mult_near=1.0`
   (any `window_def`/`max_lump_cap`) is run through the *actual*
   proximity/ladder computation (`enabled=True`, not the bypass path) and
   its resulting units/cash path is checked bit-for-bit against an
   independently-run plain-DCA reference.
3. Cash and positions never negative, for both the DCA baseline and the
   primary config, and for the most aggressive grid corner (`calendar,
   aggressive, mult_near=2.0, max_lump_cap=3.0`).
4. **No-lookahead test, with particular attention to the 52-week-low
   tracker's causality** (task instruction): perturbing all of an asset's
   OHLC data strictly after day `t` must leave every order on/before day
   `t` unchanged. Because `low52_t` is computed from a strictly causal
   rolling/expanding minimum over `close_0..close_t` only (never
   `close_{t+1}` or later), this check specifically confirms no future low
   can leak backward into `low52_t` at any earlier `t`. Run at two spot-
   checks deep into the sample (`t=6000`, `t=20000`), per prior families'
   precedent.
5. Point-in-time macro data: not applicable -- price-only signal, no
   ALFRED-vintage macro series.
6. **Total capital deployed never exceeds cumulative deposits plus
   interest** (task instruction), verified via family 021's principled
   "never invest" ceiling-bound method: a reference run that never buys
   anything gives the true maximum interest ceiling any cash trajectory
   could have earned on the asset's own daily_rf path; cumulative buys
   minus cumulative deposits must never exceed that ceiling, for the
   primary config and the most aggressive grid corner.
7. **Pre-grid non-degeneracy AND cash-reserve sanity check** (established
   convention, task instruction, adapted for this family's ladder shape
   per family 020's own precedent, PLUS the family-033 cash-reserve
   verification the task specifically calls for): confirm each of the
   near-low, middle, and far-above-low tiers claims between 2% and 98% of
   development days on each of the 5 core assets; separately, and
   specifically per family 033's lesson, confirm that during the primary
   config's "far above the low" tier (`mult_far=0.50 < 1.0`), the strategy
   actually banks a positive average cash balance materially above the
   DCA baseline's own (near-zero) average cash balance, and that this
   banked reserve is drawn down (falls) during near-low-tier weeks --
   i.e. the reserve mechanism is verified to actually build up and then
   actually get spent, not merely assumed from `mult_far<1.0` alone.
8. **Sign-correctness check** (task instruction, required specifically for
   this family to guard against the opposite mistake from family 020 --
   i.e. accidentally re-implementing family 020's OWN high-proximity logic
   under a new name/window): on SP500 development data, using the primary
   config, confirm the mean buy multiplier on days in the top quartile of
   `prox_low_t` (closest to the 52-week LOW) is **strictly greater than**
   the mean buy multiplier on days in the bottom quartile of `prox_low_t`
   (furthest above the 52-week low, i.e. closest to the 52-week HIGH) --
   i.e. near-LOW days get systematically LARGER buy orders than
   near-HIGH days, verifying the ladder is not accidentally wired with
   family 020's logic instead.
9. **Signal-disagreement check vs. family 020** (task instruction, the
   concrete numeric check promised in the distinction section above): on
   SP500 development data, compute family 020's own tier (per its own
   `ladder=moderate` primary config) and this family's own tier for every
   development day, and report the fraction of days on which the two
   signals disagree about which "extreme" (high vs. low) the asset is
   closer to -- confirming the two are not near-perfectly (anti)correlated
   restatements of one another.

## Robustness adaptations (sec 4.3, only if sec 4.1 passes)

Directly following families 003/005/006/007/014/017/020's single-asset
precedent: rolling windows (3-year and 5-year for SP500/gold/silver/oil,
2-year for BTC, per sec 4.3's own text), block bootstrap (4-week blocks,
raw + detrended), and placebo (circular-shift the daily `prox_low_t`-
derived multiplier signal, since it is this family's timing signal in the
sec 4.3 sense). Bootstrap/placebo run counts scoped to **60 simulations
each** (established time-budget convention), declared here before any
backtest, actual count confirmed again in results.md. Sec 4.3 is only run
in full if sec 4.1 passes first, per prior families' precedent.
