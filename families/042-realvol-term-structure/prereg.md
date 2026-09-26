# Family 042: Realized-volatility term-structure (short-vs-long trailing-window ratio) sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Christensen, B.J. and Prabhala, N.R. (1998), "The relation between implied
and realized volatility," *Journal of Financial Economics* 50(2), 125-150
(the vol-term-structure / realized-vol-ratio framing this family adapts).
Bollerslev, T., Patton, A.J. and Quaedvlieg, R. (2018)/Bollerslev et al.
(2018), "Risk Everywhere: Modeling and Managing Volatility," *Review of
Financial Studies* 31(7), 2729-2773 (short-vs-long realized-vol-ratio
signals as a risk-regime indicator). Seed queue idea #43
(`state/research_queue.md`), category **Volatility targeting**.

## Mechanism ("why would this work, and who is on the other side?")

Realized volatility is strongly persistent (clusters) at every horizon,
but a SHORT trailing window (e.g. 10-20 trading days) and a LONGER trailing
window (e.g. 252 trading days) of the SAME underlying realized-vol series
respond to regime changes at different speeds: the short window reacts
almost immediately to a genuine calming (or heating-up) of the asset's own
recent trading, while the long window is a slow-moving anchor for what
"normal" has looked like over roughly the past year. The RATIO of the two
-- long-window vol divided by short-window vol -- is therefore a genuine
term-structure statistic of the asset's OWN realized-volatility series (the
same slope-of-a-curve idea the vol-term-structure/carry literature applies
to *options-implied* volatility curves, e.g. Simon & Campasano 2014's
VIX3M/VIX slope already tested in family 041, but applied here to realized
volatility instead): when the ratio is elevated, the asset's recent trading
has calmed MORE than its own longer-run baseline would suggest is "just
noise" -- a "calm now relative to its own recent-past normal" regime, in
which a fixed-dollar DCA buyer is under-weighting a comparatively favorable
entry window. When the ratio is depressed (short-window vol elevated
relative to the long-run reference), the asset is heating up relative to
its own recent history, and a fixed-dollar buyer is about to commit a
disproportionate share of the deposit stream into exactly the kind of
regime transition that historically precedes further turbulence (volatility
clustering runs in the other direction too). As in every prior sizing
family in this loop, this re-times the SAME total deposit stream -- it
under-invests (relative to DCA) when the ratio is depressed, banking the
shortfall as interest-earning cash, and over-invests (again relative to
DCA, capped, funded only from banked cash -- no leverage) when the ratio is
elevated. The "other side" of this trade is constant-dollar DCA buyers and
other constant-mix investors who do not condition buy size on the asset's
own vol-term-structure at all. The risk paid is the same as every other
realized-vol sizing family in this loop: a calm-relative-to-own-history
reading does not guarantee the calm persists, and capping the multiplier
means the strategy cannot avoid a genuinely fast regime flip it has not yet
seen.

## Category

**Volatility targeting** (research-loop-plan-v3.md sec 4.5).

## Rigorous distinction from family 003 (required by this iteration's brief)

**This distinction requires an important correction to how `state/research_
queue.md`'s idea #43 entry (and this iteration's own task brief) initially
characterized family 003.** Family 003's actual pre-registered and
implemented rule (`families/003-vol-managed-sizing/prereg.md`,
`src/backtest/v3/strategies/vol_managed_sizing.py`) is **not** "a single
absolute realized-variance level" -- it already computes a ratio of a short
(`vol_lookback_days`, grid 20/40/60) and a long (`ref_lookback_days`, grid
126/252) trailing realized-vol window: `m_t = clip(sigma_ref_t /
sigma_recent_t, min_mult, max_mult)`. On inspection, that IS a short-vs-long
realized-vol-ratio construction, in the same spirit as this family's own
core idea. This is stated here explicitly and honestly, rather than
silently asserting a false distinction the code does not support -- the
loop's own discipline (sec 7.2/7.1) requires a family's pre-registration to
give the REAL reason it is not a re-test, not a reason that happens to sound
right.

**The genuine, verifiable distinction is in the FUNCTIONAL FORM applied to
that ratio, not in whether a ratio is computed at all:**

- **Family 003:** clips the RAW ratio value directly against FIXED,
  absolute multiplier bounds: `m_t = clip(sigma_ref_t/sigma_recent_t,
  min_mult, max_mult)`. A given raw ratio value (e.g. 1.8) is treated
  identically regardless of what range of ratio values that specific asset
  has historically produced -- the same fixed clip bounds (0.5-2.0 in the
  primary config) apply whether the asset's ratio typically swings 0.4-3.0
  (e.g. BTC) or sits in a tight 0.8-1.3 band (e.g. most of GOLD's history).
- **This family (042):** takes a further, causal, point-in-time PERCENTILE
  RANK of the ratio within its OWN trailing `ts_lookback` history FIRST,
  and maps THAT percentile to the multiplier via the continuous
  percentile-to-multiplier construction already established by families
  030/031/036/039/040/041: `m_t = clip(1 + k*(2*pctile_t - 1), min_mult,
  max_mult)`. The SAME raw ratio value can map to a very different
  multiplier on two different dates, or two different assets, depending on
  what range of ratio values had recently prevailed -- "unusually calm" is
  calibrated to each asset's own recent regime, not to a fixed absolute
  threshold.

**Concrete numeric rank-reversal, real dev-period data (GOLD, `GC=F`,
`short_window=20`, `long_window=252`, `ts_lookback=252`), confirming the
two constructions are not merely re-parameterizations of each other:**

| Date | Raw ratio (`sigma_long/sigma_short`) | This family's own trailing-252-day percentile rank | Family-003-style multiplier (`clip(ratio, 0.5, 2.0)`) | This family's multiplier (`k=1.0, min_mult=0.5, max_mult=2.0`) |
|---|---|---|---|---|
| 2001-12-11 | **1.974** (higher raw ratio) | 0.500 (exact median of its own trailing year) | **1.974** (near the max) | **1.000** (exactly plain DCA -- no signal at all) |
| 2003-12-23 | **1.534** (lower raw ratio) | 1.000 (the single most extreme "calm" reading in its own trailing year) | **1.534** (moderate) | **2.000** (the maximum buy multiplier) |

The two constructions produce **exactly opposite rankings** of these two
dates: the raw-ratio-clip family-003-style rule sizes 2001-12-11 above
2003-12-23; this family's own percentile-normalized construction sizes
2003-12-23 (its own multiplier ceiling) above 2001-12-11 (its own neutral
DCA-equivalent floor) -- a full rank reversal, computed live in
`scripts/v3/run_042_realvol_term_structure.py::check_rank_reversal_vs_003`
against real data, not hand-picked from a synthetic example, so a data
refresh cannot silently invalidate this section.

This family's short-window grid (10/15/20 trading days) is also
deliberately shorter than family 003's own short-window grid (20/40/60),
per the seed queue idea's own explicit brief ("SHORT trailing
realized-volatility window (e.g. 10-20 trading days)"), giving this family
a materially different effective parameterization in addition to the
functional-form difference above.

## Rigorous distinction from family 035 (Parkinson range estimator)

Family 035 uses the Parkinson (1980) high-low RANGE estimator (`p_t =
(ln(High_t/Low_t))^2 / (4*ln(2))`, reading each day's High/Low only, never
Close) as a SINGLE-window realized-vol level fed into the SAME
family-003-style raw-ratio-clip construction family 003 itself uses
(`m_t = clip(sigma_ref/sigma_recent, min_mult, max_mult)`, both legs
Parkinson-estimated). This family instead (a) uses the plain close-to-close
log-return estimator (never reads High/Low at all -- an entirely disjoint
raw input from family 035's estimator, the same distinction family 035's
own prereg.md draws against family 003) AND (b) applies the percentile-
normalization layer described above, which family 035 does not (family 035
clips its own raw ratio directly, exactly as family 003 does). Two
independent axes of difference from family 035: the estimator (close-to-
close vs. Parkinson range) and the functional form (percentile-normalized
vs. raw-ratio-clipped).

## Distinction from families 016/025/041 (VIX-based term-structure/spread families)

Briefly, per this iteration's task brief: families 016 (VIX level), 025
(VIX-minus-realized-vol spread) and 041 (VIX3M/VIX implied-vol
term-structure ratio) all use `^VIX`/`^VIX3M` -- an OPTIONS-MARKET-IMPLIED
volatility series, external to the asset itself, shared identically across
all 5 core assets. This family never touches implied volatility or any
external data source at all: its signal is built entirely from each
asset's OWN historical Close prices (`load_dev()` only), and is therefore
asset-specific (each of the 5 core assets gets its own independently-
computed ratio and percentile, unlike the shared VIX-based signal 016/025/
041 apply identically to all 5). This is the same "own realized series vs.
options-market-implied series" distinction the seed queue's idea #43 entry
itself draws.

## Concrete example: the short/long ratio vs. a single-window absolute level (required by this iteration's brief)

**GOLD (`GC=F`), 2009-02-23** (real dev-period data, `short_window=20`):

| Statistic | Value | Own trailing-252-day percentile |
|---|---|---|
| `sigma_short` (20-day trailing realized vol, annualized) | **27.6%** | **93rd percentile** of its own trailing year -- a SINGLE-window absolute-level rule reading this in isolation would flag the day as unusually VOLATILE (elevated), not calm, and would size DOWN. |
| `sigma_long` (252-day trailing realized vol, annualized) | 31.8% | (the tail of the 2008 GFC crisis still baked into the trailing year) |
| `ratio_t = sigma_long/sigma_short` | 1.153 | **100th percentile** (`pctile_t = 1.0`) of its own trailing year -- the single most extreme "calm-now-relative-to-own-recent-past" reading in that entire window, because the reference itself was still worse. |

A single-window absolute-vol-level sizing rule (buy more when `sigma_short`
sits LOW in its own percentile) would size DOWN aggressively on 2009-02-23
(93rd percentile = elevated). This family's short-vs-long RATIO signal sizes
UP maximally (`pctile_t = 1.0`, `m_t` at its ceiling) on the exact same day
-- the ratio and the level rank the identical episode in opposite
directions, because the ratio asks "calmer than what THIS asset's own
recent past has been," not "calm in some fixed absolute sense." Computed
live in `scripts/v3/run_042_realvol_term_structure.py::check_ratio_vs_level_divergence`
against real data.

## Single-asset scoping

Assessed as a **single-asset family across all 5 core assets** under sec
4.1's standard >=3/5 rule, following families 001/003/005/014/017/020/021/
023/026/028/030/031/033/034/035/036/037/039/040/041's precedent for a
per-asset internal (price-only) signal computed independently on each
asset -- no capital ever moves between assets.

## Data inputs

Daily Close price of the asset itself only (one of the 5 core assets,
tested independently -- single-asset family). No macro, external, or
alternative data; no High/Low (unlike family 035). Sourced via
`src.backtest.v3.data.load_dev()` only.

## Exact rules

Computed causally at each trading day `t`'s close, using only data through
`t` (no lookahead):

1. **Realized-vol estimator** (identical to family 003's close-to-close
   estimator): `sigma_window_t = std(diff(log(Close)), ddof=1, over the
   trailing `window` trading days) * sqrt(252)`, for `window in
   {short_window, long_window}`.
2. **Short-vs-long ratio**: `ratio_t = sigma_long_t / sigma_short_t`, with
   `long_window` FIXED at 252 (one trading year, not grid-varied -- the
   standard trailing-year reference, matching family 003's own primary
   `ref_lookback_days=252` and family 041's `ts_lookback=252` for
   comparability). `ratio_t > 1`: short-window vol sits BELOW the asset's
   own longer-run reference (calm-now-relative-to-own-normal). `ratio_t <
   1`: short-window vol is elevated relative to the reference. NaN until
   both windows are full.
3. **Trailing percentile rank**: `pctile_t` = the causal, point-in-time
   rolling percentile rank of `ratio_t` within the trailing `ts_lookback`
   window of past `ratio` values ending at `t` (inclusive) -- identical
   construction to families 036/039/040/041's `compute_percentile_rank`.
   Defaults to `0.5` (neutral) until `ts_lookback` days of valid `ratio`
   history exist.
4. **Continuous sizing multiplier** (deliberately continuous, not a
   discrete tier ladder -- per this iteration's explicit instruction and
   the confirmed cash-cap-nullification bug in families 014/033/037):
   `m_t = clip(1 + k * (2 * pctile_t - 1), min_mult, max_mult)`. Elevated
   `pctile_t` (calm-now-relative-to-own-normal) -> `m_t > 1` (buy more).
   Depressed `pctile_t` (short-vol elevated relative to own normal) ->
   `m_t < 1` (buy less, bank a reserve). `max_mult` is FIXED at 2.0 (not
   grid-varied, matching family 041's own fixed upper bound) to keep the
   family at 4 tunable parameters.
5. **Weekly decision (every trading day, no sells ever, no leverage)**:
   `target_buy_usd = min(weekly_deposit * m_t, max_lump_multiple *
   weekly_deposit)`, `max_lump_multiple` FIXED at 3.0. The engine's own
   unconditional cash cap (`buy_usd <= cash`, `engine.py` sec 3.2) enforces
   that a shortfall on a low-multiplier week simply banks as cash (earning
   IRX) until a later high-multiplier week can spend it -- never leverage,
   never borrowing.
6. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the ratio/percentile computation entirely and buys
   100% of that week's cash deposit -- reproduces plain DCA bit-for-bit,
   same pattern as every prior v3 family's disable path.

## Functional form: continuous percentile-scaled multiplier, NOT a discrete ladder

Per this iteration's explicit instruction ("strongly prefer a continuous
percentile-scaled sizing multiplier over a discrete ladder to avoid the
confirmed cash-cap-nullification bug"): this family uses the SAME
`m_t = clip(1 + k*(2*pctile-1), min_mult, max_mult)` construction families
030/031/036/039/040/041 already use. Every grid cell's `min_mult` is
asserted `< 1.0` at module-import time (the families 014/033/037/039/040/
041 lesson), and `short_window < long_window` is also asserted at
import-time (the ratio's sign convention is only meaningful when the short
window really is shorter than the reference window).

## Parameters (4 tunable + 2 fixed, <=5 tunable, per sec 3.4)

| Parameter | Grid values | Primary |
|---|---|---|
| `short_window` (trailing window, trading days, for the SHORT-horizon realized vol) | 10, 15, 20 | 20 |
| `ts_lookback` (trailing window, trading days, for the ratio's own percentile rank) | 126, 252 | 252 |
| `k` (sensitivity of the multiplier to the percentile) | 0.5, 1.0, 1.5 | 1.0 |
| `min_mult` (floor on the multiplier, elevated-short-vol weeks) | 0.25, 0.5 | 0.5 |

`long_window` is fixed at **252** (not grid-varied) and `max_mult` is fixed
at **2.0** (not grid-varied) -- both chosen for comparability with families
003/041's own primary configurations, a no-look convention choice, not a
development-data result on THIS signal. `max_lump_multiple` is fixed at
**3.0**, identical to families 030/031/036/039/040/041's own fixed ceiling.
This keeps the family at 4 tunable (grid-varied) parameters plus 3 fixed
numeric constants, at/under the plan's <=5 tunable-parameter ceiling.

`short_window=20` is primary as the upper (most stable) end of the seed
queue idea's own suggested 10-20-day range, for the same "less estimation
noise" reasoning family 003 used in choosing its own primary
`vol_lookback_days=60` (the longest of its own short-window grid).
`ts_lookback=252`, `k=1.0`, `min_mult=0.5` are primary as the identical
middle-of-grid choices families 030/036/039/040/041 already used for their
own primary configurations of this same functional form, again for
comparability rather than picked to maximize any observed effect -- fixed
before any backtest was run.

## Grid

3 (`short_window`) x 2 (`ts_lookback`) x 3 (`k`) x 2 (`min_mult`) =
**36 configurations** (at the sec 3.4 cap).

## Primary configuration

`short_window=20, ts_lookback=252, k=1.0, min_mult=0.5` (`long_window=252`,
`max_mult=2.0`, `max_lump_multiple=3.0` fixed for all configs).

## Expected sign

**Positive, primarily on Sharpe**, for the same mechanistic reason as
families 003/035 (avoiding a disproportionate dollar-weighted share of the
deposit stream during weeks where the asset's own realized volatility is
elevated relative to its recent normal, and shifting that capital into
calmer relative-regime weeks). The wealth effect is expected to be smaller
and could go either way, since total capital committed is approximately
unchanged (only its timing shifts) -- identical framing to family 003's own
"expected sign" section. Because this signal's percentile-normalization
step is asset-adaptive (unlike family 003's fixed absolute clip bounds),
it is plausible, though not the criterion that gates the family's verdict,
that this construction reacts more consistently across the 5 very
differently-scaled core assets (gold and BTC have very different typical
realized-vol ranges) than a fixed-clip rule would.

## Implementation-check plan (sec 3.2, to be run in the implementation step)

1. `enabled=False` bypass reproduces plain DCA bit-for-bit (units and cash).
2. A second reference point: a real `k=0.0` grid-shaped code path (going
   through the actual ratio/percentile computation) also reproduces plain
   DCA bit-for-bit (families 020/033/034/035/039/040/041's two-reference-
   point pattern).
3. Cash and positions never negative, for the DCA baseline, the primary
   config, and the grid's most aggressive corner (`short_window=10, k=1.5,
   min_mult=0.25, ts_lookback=126`).
4. Total capital deployed never exceeds cumulative deposits + interest, via
   the principled "never invest" ceiling bound (family 021's fix) -- primary
   config and the aggressive corner.
5. No-lookahead: perturbing all data after day `t` leaves every order on/
   before `t` unchanged, checked at two spot-check points deep into the
   sample (`t=6000`, `t=20000`).
6. Point-in-time macro: N/A -- price-only signal, no macro/ALFRED series at
   all (a stronger case than families 015/016/025/041's own "N/A"
   documentation, since this family has no external data dependency
   whatsoever).
7. **Rank-reversal-vs.-family-003 check (required by this family's rigorous-
   distinction burden)**: on real dev-period data (GOLD), confirm the
   concrete rank-reversal example in "Rigorous distinction from family 003"
   above, computed live, not hand-copied.
8. **Ratio-vs.-single-window-level divergence check (required by this
   iteration's brief)**: on real dev-period data (GOLD, 2009-02-23),
   confirm the concrete divergence example above, computed live.
9. Pre-grid non-degeneracy sanity check (primary config's multiplier shows
   real dispersion, not stuck at 1.0, on all 5 core assets) before trusting
   any grid result.
10. Pre-grid cash-reserve-dynamics check (primary config's realized average
    cash balance meaningfully differs from DCA's -- families 039/040/041's
    verification pattern) before trusting any grid result.
11. `PRIMARY_CONFIG` membership in the declared grid verified
    programmatically via an explicit module-import-time assertion (per
    family 021's lesson), alongside assertions that every grid cell's
    `min_mult < 1.0` and every `short_window < long_window`.
