# Family 024: SAD (Seasonal Affective Disorder) / daylight-length deposit timing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Kamstra, M.J., Kramer, L.A. and Levi, M.D. (2003), *Winter Blues: A SAD
Stock Market Cycle*, American Economic Review 93(1), 324-343. Using data
from stock exchanges across many countries (including both hemispheres) and
controlling for known calendar seasonals (turn-of-month, day-of-week,
Halloween/Sell-in-May, tax-loss selling), the paper finds that aggregate
equity returns are significantly related to the length of the day through
fall and winter, and interprets this as a "SAD effect": seasonal affective
disorder -- a well-documented clinical condition in which the shortening of
daylight hours in fall and winter causes depression in a meaningful share
of the population -- raises investors' aggregate risk aversion as days
shorten, and that risk aversion recedes as days lengthen again after the
winter solstice. Corroborating channel evidence they cite: aggregate
mutual-fund flow data show a shift toward safe (money-market/bond) funds in
autumn and back toward risky (equity) funds in spring, consistent with a
seasonal risk-aversion cycle rather than a pure pricing artifact. Follow-up
work (Kamstra, Kramer & Levi, *Losing Sleep at the Market: The Daylight
Saving Anomaly*, AER 2000, on the related but distinct daylight-saving
time-change effect; Kramer & Weber, *Political Orientation and Risk
Aversion...*/SAD-and-risk-aversion follow-ups) is consistent with the
original finding's behavioral premise, not independently re-verified here.
Research queue idea #24 (`state/research_queue.md`): "SAD (Seasonal
Affective Disorder) / daylight-length deposit timing."

## Mechanism ("why would this work, and who is on the other side?")

Kamstra, Kramer & Levi's (2003) proposed causal chain: (1) SAD is clinically
documented to elevate depression symptoms as the photoperiod shortens
through fall toward the winter solstice, and depression is experimentally
linked (in the psychology and behavioral-economics literature they cite) to
heightened risk aversion; (2) a meaningful share of market participants
experience this seasonal mood shift, even if only a minority are clinically
diagnosed, because the effect is a population-average tilt, not a
unanimous one; (3) as aggregate risk aversion rises through fall (in step
with shortening days, i.e. the northern-hemisphere interval from roughly
the autumnal equinox to the winter solstice), investors shed risky
holdings, depressing risky-asset prices/returns over that stretch; (4)
once the winter solstice passes and days begin lengthening again, the
population's SAD symptoms recede, risk aversion falls back, previously
shunned risky assets are rebought, and returns rebound through winter into
spring. The "other side" of the trade is, as with families 006/007/018,
whoever supplies liquidity against this recurring, largely
non-informational mood-driven selling pressure in the fall and buying
pressure in the winter/spring -- market-makers and other liquidity
providers compensated (on average, historically) for absorbing it, while
carrying the risk that the pattern fails to repeat, is arbitraged away, or
reverses in any given year.

### Sign interpretation (read carefully; stated explicitly per this
iteration's task, since getting this wrong invalidates the whole family)

Kamstra, Kramer & Levi's headline empirical result, and the summary used
by essentially every secondary source and follow-up paper (Kramer & Weber;
the Croatian-market replication in Novak & Petr (2021), Kubinschi (2021),
and others; and the paper's own abstract) is: **stock returns are
relatively low in fall (as days shorten toward the winter solstice) and
relatively high in winter and spring (as days lengthen from the winter
solstice back toward the summer)**, i.e. lower demand for risky stock in
fall, higher demand for risky stock in spring. This is the interpretation
this family uses.

This is a DIFFERENT claim from a naive "returns compensate for anticipated
risk in advance" reading (elevated returns going INTO the shortening-
daylight period, as compensation priced in ahead of time) -- that reading
would predict HIGH returns in fall and a post-solstice give-back, the
opposite sign. The task description explicitly flags this as the subtle,
easy-to-get-backwards part of the literature, and it is resolved here by
the paper's own realized-return finding, not by the ex-ante-compensation
argument: KKL's regression finds a SIGNIFICANT NEGATIVE relationship
between the SAD variable (which is HIGHEST when nights are longest, i.e.
near/at the winter solstice) and REALIZED returns over the fall-into-
winter stretch, and the fund-flow evidence (safe funds in autumn, risky
funds in spring) points the same direction: investors are net SELLERS of
risk through fall, net BUYERS through winter/spring. The economic logic
for why realized (not just expected) returns move this way: if required
returns rise through fall as risk aversion is actually increasing (not
merely anticipated once and priced in), discount rates rise through the
whole fall interval, which mechanically implies FALLING prices (negative
realized returns) throughout that interval, not just on the first day risk
aversion starts to rise. The reversal after the solstice works the same
way in reverse: falling risk aversion -> falling discount rates -> rising
prices -> positive realized returns through winter/spring.

**This family's explicit interpretation: buy LESS (bank cash) as daylight
shortens toward the winter solstice, and buy MORE (deploy banked cash) as
daylight lengthens away from the winter solstice.** The continuous signal
used (below) is built directly from daylight length and is, by
construction, MAXIMAL for the "buy less/bank" tilt exactly at the winter
solstice (the day of minimum daylight, where the fall's cumulative
risk-aversion build-up is at its documented peak per KKL) and MINIMAL
(i.e. maximal "buy more" tilt) at the summer solstice (maximum daylight,
risk aversion at its documented trough). This is a deliberate,
symmetric-around-the-solstice simplification of KKL's own fall-specific,
piecewise-asymmetric SAD regressor (their variable is defined to be
nonzero only during the astronomically-defined "fall" trading days, and a
separate, differently-signed "onset" term captures the anticipation
effect within fall itself) -- this family instead uses ONE smooth,
continuous, year-round function of daylight length (required by the
task's design spec, and a materially different functional form from
family 018's discrete window, see below), which trades a small amount of
fidelity to KKL's exact within-fall asymmetry for a strictly simpler,
lower-parameter-count, always-defined signal. This simplification is
flagged explicitly as a judgment call, not hidden.

## Category

**Seasonality / execution timing** (research-loop-plan-v3.md sec 4.5's
category list; same category as families 006, 007, 018, 022 -- a
calendar-driven execution-timing tilt within the fixed $500/week deposit
schedule, never a change to how much total capital gets deployed over the
long run).

## Why this is NOT a re-test of family 018, or sec 7.2's closed list

- **Not a re-test of sec 7.2's closed list:** no family in that list uses
  any calendar-based signal at all.
- **Explicit, load-bearing distinction from family 018 (Halloween/Sell-in-
  May), since both are "Seasonality / execution timing" and both concern
  autumn-through-spring seasonality:**
  1. **Functional form: continuous vs. discrete.** Family 018's signal is a
     BINARY step function of calendar month: `is_strong_season(t) in
     {True, False}`, switching abruptly at two fixed month boundaries
     (default Nov 1 / May 1). This family's signal is a CONTINUOUS,
     smoothly-varying function of the actual astronomical daylight length
     on day `t`, computed from a solstice-based formula -- there is no
     discrete on/off boundary anywhere in the year; the buy multiplier
     changes by a small amount every single trading day, tracking the
     day-to-day change in daylight hours, and is symmetric and smooth
     around both solstices (see "Exact rules" below). A degenerate
     collapse of this family's continuous signal to family 018's discrete
     step function is not reachable within this family's parameter grid
     (no parameter turns the continuous daylight function into a step
     function).
  2. **Behavioral channel: institutional flow/vacation vs. mood/risk-
     aversion.** Family 018's cited mechanism (Bouman & Jacobsen 2002) is
     explicitly institutional/logistical: thinner trading desks, lower
     risk appetite for NEW positions during the northern-hemisphere summer
     vacation period, and mid-year mandate-review cycles -- a
     calendar-scheduling story about when institutions are staffed and
     reviewing risk budgets, unrelated to any individual's mood. This
     family's cited mechanism (Kamstra, Kramer & Levi 2003) is
     explicitly a clinical/psychological story: seasonal affective
     disorder altering individual investors' mood and, through documented
     mood-risk-aversion links, their portfolio risk tolerance, driven
     continuously by the photoperiod itself (hence naturally continuous,
     not naturally discrete the way an institutional calendar deadline
     is).
  3. **Anchor literature and cited evidence differ, and the two papers'
     authors treat each other's effect as a control, not a restatement.**
     KKL (2003) explicitly controls for calendar seasonals including the
     Halloween-type effect in their regressions, and find the SAD effect
     survives as a statistically distinct additional predictor -- i.e. the
     original SAD paper itself treats these as two separate,
     simultaneously-estimable effects, not two names for the same thing.
  4. **Timing/shape differ in practice even though both "favor" a
     Nov-through-spring stretch loosely.** Family 018's strong season is a
     flat, equal-weighted 6-month window (every November day treated
     identically to every February day). This family's signal peaks
     exactly at the winter solstice (Dec 21) and is at its weakest exactly
     at the summer solstice (Jun 21) -- November and February are NOT
     treated identically (November, further from the solstice, gets a
     smaller "buy less" tilt than late December).
  This mirrors sec 7.2's own re-test standard ("a different signal
  definition or a different mechanism") and the precedent already
  established between families 006/007/018 themselves (distinct calendar
  granularities, distinct anchor literature, distinct mechanisms).

## Single-asset vs. multi-asset scoping

Following the established precedent from families 006, 007, 018 and 022
(all asset-agnostic calendar mechanisms tested across all 5 core assets
under sec 4.1's standard >=3/5 rule, even though each one's anchor
literature is equity- or region-specific): **this family is tested on all
5 core assets.** KKL's own paper tests SAD across many countries and
hemispheres (finding the effect flips sign appropriately in the Southern
Hemisphere), which if anything argues the structural claim (a photoperiod-
driven mood/risk-aversion cycle affecting market participants generally)
is not logically restricted to equities -- commodity and crypto market
participants are human beings subject to the same daylight cycle. No
reason was found to depart from the uniform-application precedent set by
006/007/018/022.

## Reference latitude (fixed, not tunable -- documented judgment call)

None of the 5 core assets (S&P 500, gold, silver, BTC, WTI oil) has an
unambiguous single "home market latitude" the way a single-country equity
index would. **Decision: use a fixed reference latitude of 40 degrees
North** for the daylight-length calculation, applied identically to every
asset. Rationale: 40N is a defensible, literature-adjacent choice --
it is within the latitude band of KKL's own primary US evidence (NYSE,
roughly 40.7N) and of most of the other major exchanges in their
international panel (London ~51.5N, Tokyo ~35.7N, etc. straddle it), and
is a commonly-used "mid-latitude Northern Hemisphere" reference point in
follow-up SAD literature when a single representative latitude is needed.
It is held FIXED across the whole grid (not a tunable parameter, to keep
the tunable-parameter count low per sec 3.4's <=5 ceiling) so that the
grid explores how strongly to act on the signal, not where in the world
the signal is computed for -- varying latitude would not meaningfully
change the signal's timing (solstice dates are latitude-independent) but
only its amplitude, which the `tilt_strength` parameter already controls
directly and more transparently.

## Exact rules

Computed at each trading day `t` using only calendar information (the
asset's own trading-day index and each day's calendar date) -- like family
018, no price or macro dependence in the signal at all, so no-lookahead is
automatically satisfied for the signal itself (the calendar, and hence the
astronomical daylight length on any future date, is known exactly in
advance).

1. **Daylight length `D(t)`** (hours), via the standard solstice-based
   astronomical approximation at the fixed reference latitude `phi =
   40 deg N`:
   - Solar declination (degrees): `delta(t) = -23.44 * cos(360/365 *
     (doy(t) + 10))`, where `doy(t)` is the day-of-year (1-366).
   - Hour angle (radians): `H(t) = arccos(clip(-tan(phi) * tan(delta(t)),
     -1, 1))`.
   - Daylight hours: `D(t) = 24 * H(t) / pi`.
   - This is the same family of formula used in standard solar-geometry
     references; it is not exact to the minute (omits the equation of
     time and atmospheric refraction) but is smooth, correctly signed, and
     accurate to within a few minutes of the true daylight length at this
     latitude -- more than sufficient for a smooth continuous timing
     signal. Spot-checked before any backtest (see implementation checks
     below): Dec 21 gives ~9.16h (true ~9h20m), Jun 21 gives ~14.84h (true
     ~14h49m), both equinoxes give ~11.90h (true ~12h00m).
2. **Normalized SAD signal `S(t) in [-1, +1]`:** `S(t) = (D_mid - D(t)) /
   ((D_max - D_min) / 2)`, where `D_max`, `D_min`, `D_mid =
   (D_max+D_min)/2` are `D(t)` evaluated at the (latitude-fixed) summer and
   winter solstices. `S(t) = +1` exactly at the winter solstice (shortest
   day, maximal "buy less/bank" signal) and `S(t) = -1` exactly at the
   summer solstice (longest day, maximal "buy more" signal), continuous
   and smooth in between, symmetric around both solstices.
3. **Shaped signal:** `S_shaped(t) = sign(S(t)) * |S(t)|^power` (`power`
   is a tunable steepness parameter; `power=1` is the unshaped linear
   signal, `power>1` concentrates the tilt more tightly around the two
   solstices and flattens it near the equinoxes).
4. **Buy multiplier:** `mult(t) = 1 - tilt_strength * S_shaped(t)`, which
   ranges continuously from `1 - tilt_strength` (at the winter solstice)
   to `1 + tilt_strength` (at the summer solstice). `tilt_strength in
   (0, 1)` keeps `mult(t)` strictly positive.
5. **Weekly execution (identical banking mechanic to family 018, so
   capital neutrality is structurally guaranteed the same way):** on each
   week's decision day, `target_buy_usd = min(cash, max_lump_multiple *
   weekly_deposit, mult(t) * weekly_deposit)`. When `mult(t) < 1`, less
   than the week's $500 deposit is spent and the remainder is banked as
   cash (earning IRX, engine sec 3.2); when `mult(t) > 1`, previously
   banked cash is drawn down to buy more than $500 that week, capped by
   `max_lump_multiple * weekly_deposit` and by available cash. Never
   sells, never leverages (buys are always cash-capped by the engine at
   fill time).

## Parameters (3, well under the sec 3.4 cap of 5)

1. `tilt_strength` -- how strongly the multiplier responds to the SAD
   signal.
2. `power` -- steepness/shape exponent on the normalized signal.
3. `max_lump_multiple` -- ceiling on burst buying when banked cash is
   deployed.

(`reference_latitude_deg=40.0` is fixed, not a grid parameter -- see
above.)

## Grid (18 configurations, under the sec 3.4 cap of 36)

| Parameter | Values |
|---|---|
| `tilt_strength` | 0.3, 0.5, 0.7 |
| `power` | 1.0, 2.0 |
| `max_lump_multiple` | 4, 8, 12 |

3 x 2 x 3 = 18 configurations.

## Primary configuration

`tilt_strength=0.5, power=1.0, max_lump_multiple=8`

(Verified programmatically, at module import time, to be a member of the
declared grid above -- per family 021's lesson.)

## Expected sign

Per the sign interpretation above: strategy final wealth AND Sharpe should
exceed plain DCA's, on the theory that systematically banking cash while
daylight shortens toward the winter solstice (when KKL find realized
returns are relatively low/falling) and deploying it while daylight
lengthens away from the winter solstice (when KKL find realized returns
are relatively high/rising) buys more units, on average, at relatively
depressed prices and fewer units at relatively elevated prices, versus a
flat weekly schedule that is indifferent to the calendar.

## Implementation-check plan (sec 3.2, to run before any grid result is
trusted)

1. `enabled=False` bypass reproduces plain DCA exactly (bit-for-bit units
   and cash), same pattern as families 018/021/022/023.
2. Cash and positions never negative, for the DCA baseline, the primary
   config, and the grid's most-aggressive corner (`tilt_strength=0.7,
   power=2.0, max_lump_multiple=12`).
3. Capital deployed never exceeds cumulative deposits + interest, via
   family 021's principled "never invest" ceiling-bound method (not a flat
   percentage tolerance).
4. No-lookahead perturbation test (trivial in principle, since the signal
   is a deterministic calendar function with no price dependence at all --
   still run and verified explicitly, spot-checked at two points in the
   series, per the task's instruction).
5. **Astronomical sanity spot-check (before any backtest is trusted):**
   `D(t)` reproduces the expected solstice/equinox values above (Dec 21
   shortest, Jun 21 longest, both equinoxes near 12h) at the fixed 40N
   latitude, confirmed against several separate years to rule out a
   day-of-year indexing bug (leap years included).
6. **Pre-grid non-degeneracy sanity check:** confirm `mult(t)` is neither
   constant nor pinned at its bounds across a full year of trading days
   for every core asset (i.e. the signal is genuinely continuous and
   varying, not accidentally degenerate to a constant or a step function).
