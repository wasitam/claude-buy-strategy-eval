# Family 014: Drawdown-from-high reserve deployment

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Practitioner "buy the dip harder" / cash-reserve DCA literature (widely
discussed under names like "value cost averaging against the peak" and
"drawdown-triggered lump-sum deployment" in retail-investing practitioner
writing; economically related to the professional tactical-asset-allocation
practice of holding a dry-powder reserve and deploying it in proportion to
drawdown depth, e.g. as described in Faber's tactical allocation writing and
in momentum-crash/drawdown-timing discussions -- distinct from, though
adjacent to, the academic moving-average trend-exit literature already
closed under this loop's family 001 and this loop's own SmartDCA precedent,
see the required distinction section below). Seed queue item #14
(research-loop-plan-v3.md sec 7.3): "track each asset's own trailing
all-time-high price; buy size scales up as price falls further below that
high ... banking unused deposit into cash reserve during normal/near-high
periods, deploying the reserve (cash-capped, no leverage) as drawdown
deepens."

## Mechanism ("why would this work, and who is on the other side?")

The economic case rests on two standard, well-documented effects, combined
here into a single mechanical rule:

1. **Long-run mean reversion after large drawdowns.** Across all 5 core
   asset classes, historically the largest forward returns have clustered in
   the periods following the deepest drawdowns from a prior peak (the
   "buy when there's blood in the streets" empirical regularity that
   underlies value investing and contrarian tactical allocation more
   broadly). A rule that mechanically shifts more capital into an asset the
   further it sits below its own historical peak is a disciplined,
   emotion-free way to harvest this regularity without requiring any
   forecast of when the bottom will occur.
2. **Reserve-funded averaging reduces regret-driven behavioral errors.**
   Retail investors are well documented (behavioral finance literature on
   DCA vs. lump-sum, and on panic-selling/stopping contributions during
   drawdowns) to react to drawdowns by *reducing* or halting contributions
   at the worst possible time. A rule that instead pre-commits to banking
   unused deposits near the highs and spending them back in during
   drawdowns forces the opposite, historically better-rewarded, behavior --
   with no leverage and no new money, only a reallocation of the investor's
   own already-scheduled deposits across time.

**Who is on the other side?** Investors who keep contributing a flat amount
regardless of price level (this family's own DCA benchmark) forgo this
timing tilt entirely. Investors who instead reduce or stop contributions
during drawdowns (a well-documented behavioral pattern) are the ones this
mechanism is designed to out-perform by construction, and are plausibly
"funding" the effect if drawdown-period forward returns are elevated partly
*because* of exactly this kind of flow behavior (some other investors
capitulating and selling into the drawdown while this strategy is buying
into it). The mechanism can fail if a drawdown is structural rather than
cyclical (the asset never recovers to a new high within the horizon that
matters, so "buying more the further underwater" simply loses more money
faster) -- a real risk this pre-registration flags before any backtest is
run, consistent with the honest-reporting spirit of sec 12's risk list.

## Category

**Sizing / valuation** (research-loop-plan-v3.md sec 4.5) -- matches the
seed queue's own categorization of idea #14.

## Why this is NOT a re-test of SmartDCA (sec 7.2 closed list) -- required justification

Sec 7.2 explicitly closes "v2 SmartDCA (rho x m_max x sweep grid)" and the
task instructions single out this exact family as needing a rigorous,
explicit justification for why it is not a re-test. That justification, in
full:

**SmartDCA's reference point is a trailing moving average -- a smoothed,
backward-looking statistic that is recomputed every period from a rolling
window of recent prices, and therefore itself moves (up AND down) with
recent price action.** SmartDCA's buy multiplier is driven by
`rho`-scaled distance of price *below* a (typically 52-week) simple/
exponential moving average. Two mechanical consequences follow from that
choice of reference: (a) the reference itself declines during a sustained
drawdown (a falling moving average), which continuously narrows the gap
the signal is measuring even while the price keeps falling, so the signal
is partly measuring *short-run deviation from a locally-adapting trend*,
not distance from any fixed historical level; and (b) once price has been
below the average long enough for the average itself to fall below the
old pre-drawdown level, a price that is still deeply underwater relative
to its own history can register as only mildly "below average," because
the average has already adapted downward with it.

**This family's reference point is the asset's own trailing all-time-high
price -- a ratchet that only ever moves up (when a new high is set) or
stays exactly fixed (during every day that is not a new high), and never
declines, no matter how long or how deep the drawdown runs**, except when
the lookback-cap parameter (below) causes an old peak to roll out of the
window, which happens on a horizon of years, not weeks. Two consequences
follow from *this* choice of reference, and they are the mirror image of
SmartDCA's: (a) the reference never adapts downward during a drawdown, so
the signal keeps measuring the full, undiminished distance from the actual
historical peak for as long as the drawdown persists -- a multi-year bear
market registers as "just as far underwater" on day 500 as it did on day
50, whereas a 52-week moving average would have fallen substantially by
day 500 and would show a much smaller gap; and (b) the reference is a
single point estimate (one past price), not a smoothed statistic over a
rolling window of many prices, so it carries no information at all about
*recent* price action or trend direction/velocity -- it is purely "how far
below the best-ever level are we," with zero regard for whether the price
is currently rising or falling, accelerating or decelerating. SmartDCA's
signal, by contrast, is inherently trend-sensitive (a moving average is a
smoothed trend estimate; distance-from-it partially encodes recent trend
strength, not just absolute drawdown depth).

**Concretely, the two signals diverge sharply and often in this loop's own
development data.** Take a slow, grinding decline that stays below its
2-year-old all-time high for three straight years without ever setting a
new high (a real feature of, e.g., gold's and oil's history in the
development window): a 52-week moving average tracks that decline down
within about a year and then re-flattens near the new (lower) price level,
so SmartDCA's signal returns close to "neutral" for the remaining two years
even though the asset is still, say, 40% below its true multi-year peak.
This family's signal stays pinned at "~40% below all-time-high" (subject
only to the lookback-cap parameter below) for the full three years,
continuing to scale buys up long after SmartDCA's signal has gone quiet.
Conversely, a sharp V-shaped one-month crash-and-recovery that never even
dents the moving average much (because a 52-week average barely moves in
four weeks) can still register a large drawdown-from-high reading on this
family's signal for the weeks the price sits below its recent peak, even
though SmartDCA's signal barely fires at all over that short a window.
These are not two parameterizations of the same underlying statistic --
"distance below a rolling average" and "distance below the highest price
ever recorded" are different functions of the price path with different
persistence properties, different half-lives of signal decay, and a
different economic story (buying more the longer and deeper you are
underwater from ANY past peak, a value/contrarian story with no reference
to recent trend, vs. buying more when short-run price sits below its own
recent smoothed trend, a mean-reversion-around-a-moving-trend story). No
non-degenerate configuration of this family's grid (below) reduces to any
SmartDCA `(rho, m_max)` configuration, and no SmartDCA configuration
reduces to any configuration of this family. This is a materially
different mechanism, not a re-test.

**Also not a re-test of family 001 (10-month/200-day trend exit, this
loop, REJECTED).** Family 001 is a binary in/out switch relative to a
trailing moving average (fully invested above it, fully parked in cash
below it) -- the same "moving, backward-looking reference" category as
SmartDCA, just a step function instead of a continuous multiplier, and
again never uses the all-time-high. This family is always invested (never
exits to 100% cash by rule; see "exact rules" below) and its multiplier is
a continuous/ladder function of a fixed-ratchet reference, not a binary
switch on a moving one. Different reference object and different rule
shape from family 001 as well.

## Win-rule interpretation

Assessed as a **single-asset family** (sec 4.1's "Single-asset" line, as
instructed): beats DCA on final wealth AND Sharpe on at least 3 of the 5
core assets, at both fee levels, using the existing single-asset
`engine.py` unmodified (no portfolio engine needed -- this signal is
entirely per-asset, using each asset's own price history only, exactly
like families 003/004/005/006/007/008).

## Exact rules

Computed independently for each asset, using only that asset's own OHLC
close prices, causally (no lookahead):

1. **Trailing all-time-high, `ATH_t`:**
   - **Unbounded** (`ath_lookback_years = None`): `ATH_t = max(close_0, ..., close_t)`,
     the running maximum of the close price over the asset's full history up
     to and including day `t` (an expanding-window causal maximum).
   - **Lookback-capped** (`ath_lookback_years = L`): `ATH_t = max(close_{t-W+1}, ..., close_t)`
     where `W = round(252 * L)` trading days, a trailing rolling-window
     causal maximum (falls back to the expanding max while fewer than `W`
     observations exist). This exists specifically to prevent one very old,
     possibly never-to-be-revisited peak (e.g. a speculative spike decades
     ago) from permanently pinning the signal at "always deeply
     underwater" for a long-lived asset, per the task's own stated
     motivation.
2. **Drawdown depth:** `dd_t = max(0, 1 - close_t / ATH_t)` (0 exactly on
   any day that closes at or above the trailing high; strictly positive
   below it).
3. **Ladder multiplier, `m_t`,** a discrete step function of `dd_t` with two
   breakpoints `(tier1_dd, tier2_dd)` and three tier multipliers
   `(near_high_mult, mult_tier1, mult_tier2)`:
   - `dd_t < tier1_dd`: `m_t = near_high_mult` (normal-or-reduced buying near
     the high -- the "bank the reserve" regime).
   - `tier1_dd <= dd_t < tier2_dd`: `m_t = mult_tier1`.
   - `dd_t >= tier2_dd`: `m_t = mult_tier2` (deepest-drawdown regime -- the
     "deploy the reserve" regime).
4. **Order:** `buy_usd_t = min(weekly_deposit * m_t, weekly_deposit * max_lump_cap)`,
   never a sell. The engine's own cash cap (sec 3.2: `buy_usd <= cash`)
   enforces the "cash-capped, no leverage" requirement mechanically -- a
   below-1x week (`m_t < 1`, i.e. `near_high_mult < 1`) banks the unspent
   share of that week's deposit as cash (earning IRX), which becomes
   available precisely to fund a later above-1x week once drawdown deepens,
   exactly the reserve-banking/reserve-deployment mechanism the task
   describes, with no separate reserve-accounting parameter needed (this is
   the same implicit-reserve pattern already used and accepted for families
   003 and 005). `max_lump_cap` is a hard ceiling on how large a single
   week's buy can be relative to the plain $500 deposit, independent of how
   much banked cash is actually available, so a very large accumulated
   reserve cannot be dumped into a single week's order even if the cash
   exists to cover it (an explicit anti-concentration control, matching the
   spirit of family 013's per-asset weight bounds).
5. **Decision cadence:** the multiplier is recomputed at every trading day's
   close (needed because `ATH_t`/`dd_t` change daily), but since deposits
   only arrive on each week's last trading day, `buy_usd_t` is only
   non-zero on week-end decision days -- identical cadence to every other
   single-asset family in this loop (weekly $500 deposit, single order/week,
   satisfying sec 3.4's "at most one order per asset per trading day").

## Data inputs

Daily OHLC close of each of the 5 core assets, individually, plus the
daily risk-free rate (IRX) for cash interest -- all sourced via
`src.backtest.v3.data.load_dev()` only. No macro or alternative data.

## Parameters (4 of the allowed 5)

| Parameter | Meaning | Grid values | Primary |
|---|---|---|---|
| `ath_lookback_years` | Cap on how far back the running high is tracked | `None` (unbounded), `10` | `None` |
| `ladder` | Bundled `(tier1_dd, tier2_dd, mult_tier1, mult_tier2)` preset (see below) -- one logical parameter selecting among named presets, same bundling convention family 013 used for its weight-bound pair | `mild`, `moderate`, `aggressive`, `flat` | `moderate` |
| `near_high_mult` | Buy multiplier while `dd_t < tier1_dd` (the "bank the reserve" regime) | `0.75`, `1.0` | `1.0` |
| `max_lump_cap` | Ceiling on `buy_usd` as a multiple of the plain $500 deposit | `2.0`, `3.0` | `3.0` |

**Ladder presets** (bundling `tier1_dd`, `tier2_dd`, `mult_tier1`,
`mult_tier2` into one selectable parameter, to stay within the 5-parameter
ceiling while still letting the grid explore both the breakpoints and the
tier multipliers):

| Preset | `tier1_dd` | `tier2_dd` | `mult_tier1` | `mult_tier2` |
|---|---|---|---|---|
| `mild` | 0.10 | 0.25 | 1.25 | 1.75 |
| `moderate` (primary, and the task's own illustrative example) | 0.10 | 0.25 | 1.5 | 2.0 |
| `aggressive` | 0.15 | 0.35 | 2.0 | 3.0 |
| `flat` | 0.10 | 0.25 | 1.0 | 1.0 |

`flat` is the family's **true zero-effect grid arm** (see "Implementation
checks" below): with `mult_tier1 = mult_tier2 = 1.0`, every tier's
multiplier is identical to the near-high regime's baseline, so *when also
paired with* `near_high_mult = 1.0`, `m_t = 1.0` for every day regardless
of `dd_t` -- i.e. this is a real, independently-computed member of the
pre-declared grid (not a special bypass code path) that is expected, by
construction of the rule itself, to reduce to plain DCA.

## Grid

`ath_lookback_years` (2) x `ladder` (4) x `near_high_mult` (2) x
`max_lump_cap` (2) = **32 configurations** (<= 36 cap, 4 tunable
parameters <= 5).

## Primary configuration

`ath_lookback_years=None` (unbounded -- the literal, simplest reading of
"all-time-high"), `ladder=moderate` (the task's own illustrative
1x/1.5x/2x example), `near_high_mult=1.0` (no reduction below the plain
deposit near the high -- the reserve only ever grows from *banked* cash the
strategy never actually needs to spend at par, keeping the primary
configuration close to plain DCA's risk profile except in drawdowns, a
conservative choice made before seeing any results), `max_lump_cap=3.0`
(generous enough not to bind the primary ladder's own 2.0x ceiling, so the
cap is a genuine tail control rather than a routinely-binding constraint at
the chosen primary settings) -- all chosen before any backtest is run on
development data.

## Expected sign of the effect

Positive: the strategy should beat plain DCA on both final wealth and
Sharpe, because it buys systematically more of each asset during periods
that (per the mean-reversion mechanism above) have historically been
followed by above-average forward returns, funded entirely by deposits the
strategy itself banked during calmer periods rather than by leverage or
externally sourced capital, and because holding a larger position built at
lower average cost during drawdowns should mechanically raise both
terminal wealth and the volatility-adjusted return relative to a flat
deposit schedule that buys the same total dollar amount irrespective of
price level.

## Implementation checks to run (sec 3.2, before any results count) -- two-reference-point pattern

Per the established convention (families 010/013's degenerate-config-trap
lesson, and the task's explicit instruction that this family needs *two*
reference points since it is "always active" in the sense that a buy order
fires every week regardless of drawdown level):

1. **Explicit bypass flag, matching plain DCA bit-for-bit.** A module-level
   `enabled=False` path that skips the drawdown/ladder computation entirely
   and submits exactly `weekly_deposit` as the buy order every week, no
   sells -- checked against `v3chk.check_degenerate_equals_dca` the same
   way every prior family's bypass flag was checked. This satisfies sec
   3.2 check 1's literal wording.
2. **True zero-effect grid arm, verified independently against plain DCA.**
   The real grid configuration `ladder=flat, near_high_mult=1.0` (any
   `ath_lookback_years`/`max_lump_cap`, since neither affects the result
   once every tier's multiplier is 1.0) is run through the *actual*
   drawdown/ladder computation (`enabled=True`, not the bypass path) and
   its resulting units/cash path is checked bit-for-bit against an
   independently-run plain-DCA reference on the same asset -- confirming
   the ladder-based signal path itself, not just the bypass flag, collapses
   to DCA when every tier multiplier is set to 1.0. This is the second,
   independent reference point the task requires: it exercises the
   `ATH_t`/`dd_t` computation and the ladder lookup for real (unlike check
   1, which never touches that code path at all), so it catches bugs check
   1 cannot.
3. Cash and positions never negative, for both the DCA baseline and the
   primary config.
4. **No-lookahead test, with particular attention to the all-time-high
   tracker's causality** (the task flags this as important): perturbing
   all of an asset's OHLC data strictly after day `t` must leave every
   order on/before day `t` unchanged. Because `ATH_t` and `dd_t` are each
   computed from a (running or rolling) maximum that by construction only
   ever looks at `close_0..close_t`, this check specifically confirms that
   no future high can leak backward into `ATH_t` at any earlier `t` -- run
   at a spot-check deep into the sample, per families 001-013's precedent.
5. Point-in-time macro data: not applicable -- this family uses only each
   asset's own price data, no ALFRED-vintage macro series.
6. **Total capital deployed never exceeds cumulative deposits plus interest**
   (explicit check for this family, since the ladder can request up to
   `max_lump_cap x $500` in a single week): confirmed by construction, since
   `buy_usd_t = min(..., cash)` inside the engine (sec 3.2) already forbids
   spending more than is on hand, and cash itself is only ever credited by
   deposits and IRX interest -- verified empirically by asserting
   `cumulative buy_usd <= cumulative deposit + cumulative interest credited`
   across the full backtest for the primary config and for the most
   aggressive grid corner (`ladder=aggressive, near_high_mult=0.75,
   max_lump_cap=3.0`).

## Robustness adaptations (sec 4.3, only if sec 4.1 passes)

Directly following families 003/005/006/007/008's single-asset precedent:
rolling windows (3-year and 5-year for SP500/gold/silver/oil, 2-year for
BTC, per sec 4.3's own text), block bootstrap (4-week blocks, raw +
detrended), and placebo (circular-shift the daily `dd_t` drawdown-depth
signal, since it is this family's timing/regime signal in the sec 4.3
sense). Bootstrap/placebo run counts scoped to **60 simulations each**
(established time-budget convention per the task instructions and prior
families' precedent), declared here before any backtest, actual count
confirmed again in results.md. Sec 4.3 is only run in full if sec 4.1
passes first, per families 006/007/008/011/013's precedent.
