# Family 041: VIX futures term-structure carry (contango/backwardation)

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Data-feasibility check (done FIRST, per this iteration's task instruction)

Confirmed live in this environment before any design work: `^VIX3M` (CBOE
3-Month Volatility Index, the genuine term-structure counterpart to spot
`^VIX`) is reachable via yfinance with substantial history:

| Ticker | Rows | Start | End |
|---|---|---|---|
| `^VIX` | 9,253 | 1990-01-02 | today |
| `^VIX3M` | 5,081 | **2006-07-17** | today |

(`^VIX9D` and `^VIX6M` are also reachable, from 2011-01-03 and 2008-01-02
respectively, but are not used here -- see "Parameters" below for why the
`^VIX`/`^VIX3M` pair was chosen over these alternates.) A first probe using
`yf.download()`'s default window returned only ~22 rows for all three
tickers; `yf.Ticker(...).history(period="max")` (the same call
`data._fetch_yf_raw` already uses for every other ticker in this codebase)
returns the full history shown above -- confirmed genuine, not a
default-window artifact, before trusting the reachability finding.

**This is a genuine term-structure proxy, not spot VIX reused**: `^VIX3M`
is CBOE's own published 3-month-implied-volatility index (the second point
on the same options-implied volatility curve as `^VIX`'s 1-month-implied
point), not a re-parameterization or resampling of `^VIX` itself. The
ratio/spread between the two is a genuine curve-slope statistic, not a
level. **Verdict: feasible.** Idea #42 (VIX futures term-structure carry)
proceeds as this iteration's family, no substitute needed.

`^VIX3M`'s 2006-07-17 start means: SP500's 1927-2019 development window is
mostly pre-`^VIX3M` (as it is mostly pre-`^VIX` too, see family 016);
GOLD/SILVER/OIL's ~2000-2019 development windows are roughly one-third
pre-`^VIX3M`; BTC's entire 2014-2019 development window falls after
`^VIX3M`'s start, so the signal is available for all of BTC's (short)
development period. This is the same shape of caveat family 016 already
documented for `^VIX`'s 1990 start, one step further into the sample --
stated explicitly here, not silently absorbed into the warm-up convention
(see "Data inputs and reachability" below for exact day counts).

## Source

Simon, D.P. and Campasano, J. (2014), "The VIX Futures Basis: Evidence and
Trading Strategies," *Journal of Derivatives* 21(3) -- documents that the
VIX futures basis (a term-structure-of-implied-volatility measure) predicts
forward S&P 500 returns and VIX changes. Cheng, I.-H. (2019), "The VIX
Premium," *Review of Financial Studies* 32(1), 180-227 -- documents the VIX
futures term structure's historical tendency toward contango (a return
premium associated with staying invested / short volatility during normal,
upward-sloping-curve periods) and its inversion into backwardation during
market stress (near-term implied vol spiking above longer-term implied
vol). Seed queue idea #42 (research-loop-plan-v3.md sec 7.3 addendum /
`state/research_queue.md`).

## Mechanism ("why would this work, and who is on the other side?")

The VIX options/futures-implied volatility curve normally slopes upward
(contango): near-term implied volatility (`^VIX`, ~1-month) trades below
longer-term implied volatility (`^VIX3M`, ~3-month), reflecting a normal
term premium for bearing near-term uncertainty and the tendency of acute
volatility spikes to be short-lived and mean-reverting. During acute market
stress, the curve inverts into backwardation: near-term fear (`^VIX`) spikes
above the longer-term reading (`^VIX3M`), signaling that the market expects
elevated volatility to persist or worsen in the near term specifically, not
merely a brief, already-priced-in blip. This family's mechanism (the
literature-faithful, non-contrarian reading; see "Sign" below) is a
**risk-management carry story**: contango periods are calm, term-premium-
harvesting periods in which staying fully (or extra) invested is
historically well compensated (Cheng 2019's VIX premium); backwardation
periods are acute-stress episodes in which banking a cash reserve rather
than buying into an actively deteriorating near-term outlook is the more
conservative, literature-faithful reading of what an inverted curve is
telling the market. The "other side" of this trade is whoever is forced to
sell (or is simply willing to buy) during genuine backwardation-flagged
stress without regard to the curve's own signal -- e.g. mechanical DCA
buyers, or investors who read a VIX spike as an immediate buying
opportunity (family 016's own contrarian bet) rather than a signal to wait;
this family's investor is betting that the term-structure's own slope,
not the VIX *level* alone, is informative about whether the near-term
outlook has already stabilized (contango resuming) or not (backwardation
persisting).

## Sign (deliberately literature-faithful, not contrarian)

Per the task brief's explicit framing: "contango = calm markets = deploy
normally; backwardation = stress = bank" is the **base, literature-faithful
carry-premium reading** (Cheng 2019: the VIX premium is earned during
contango; it collapses or reverses during backwardation) -- **this is the
version implemented and pre-registered as this family's primary mechanism**,
not the contrarian "buy MORE into backwardation" alternative the task brief
also mentions has been tested elsewhere in this loop (family 016's VIX
*level* contrarian bet, REJECTED). Choosing the carry-premium sign here
(rather than a second contrarian variant) is itself part of what keeps this
family mechanistically distinct from family 016: family 016 bets on
mean-reversion-after-panic (buy the spike); this family bets on the
term-structure's own information content about persistence vs. resumption
of a calm curve shape (bank during backwardation, ride the normal-contango
carry premium otherwise) -- a different economic claim, not merely the
sign-flip of family 016's claim on a different statistic.

## Rigorous distinction from family 016 (vix_contrarian) and family 025 (vrp_sizing)

| | Family 016 (VIX contrarian) | Family 025 (VRP sizing) | Family 041 (this family) |
|---|---|---|---|
| **Signal source** | `^VIX` **level** alone -- a single point on the implied-vol curve (the ~1-month tenor), no comparison to any other measure. | `^VIX` (implied, 1-month) **minus** each asset's own trailing **realized** volatility -- a cross-*measure* spread (implied vs. realized), both legs at the SAME (near-term) tenor. | `^VIX3M` **divided by** `^VIX` -- a ratio of two **implied**-volatility measures at two DIFFERENT tenors (1-month vs. 3-month) on the SAME curve. Never touches realized volatility at all. |
| **What moves the signal** | Any change in the market's near-term option-implied vol level, regardless of the curve's shape at other tenors. | Any divergence between what options markets expect (implied) and what has actually happened (realized) on a GIVEN asset, regardless of the implied curve's own shape. | The **slope/shape of the implied-vol curve itself** -- can move even when `^VIX`'s own level is unchanged (e.g. `^VIX` flat but `^VIX3M` falling = curve flattening toward backwardation with no change in the near-term level alone), and is entirely insensitive to any one asset's own realized volatility (gold, silver, BTC, oil contribute nothing to this signal, same as families 016/025's own VIX-level input). |
| **Economic story** | Behavioral overshoot/panic-and-recovery (Whaley 2000): buy MORE into an elevated fear level, betting on mean reversion. | Variance-risk-premium harvesting (Bekaert & Hoerova 2014; Carr & Wu 2009): size by how rich implied vol is running relative to what has actually realized, on THIS asset. | Term-structure-of-volatility carry (Simon & Campasano 2014; Cheng 2019): bank during a curve INVERSION (near > far), ride the normal, upward-sloping-curve carry premium otherwise. The economic object is the curve's SLOPE across two implied-vol tenors, the volatility-market analogue of a bond-market term-structure carry trade -- neither family 016 nor family 025 constructs or references a second implied-vol tenor at all. |
| **Sign / direction** | Elevated level -> buy MORE (contrarian, risk-seeking). | Elevated implied-minus-realized spread -> buy MORE (risk-seeking). | Elevated (i.e. deep-contango, high `^VIX3M`/`^VIX` ratio) -> buy MORE; depressed/inverted (backwardation) -> buy LESS/bank (risk-averse during a signaled stress persistence, not risk-seeking into it). |
| **Can one signal be recovered from the other?** | No: `^VIX` level alone cannot reconstruct `^VIX3M`/`^VIX`, and vice versa -- an asset can have an elevated `^VIX` level yet still sit in mild contango (both `^VIX` and `^VIX3M` elevated together), or a middling `^VIX` level yet sit in outright backwardation (a curve inversion at moderate absolute levels). | No: the VRP spread (implied minus realized, single tenor) and this family's curve-slope ratio (implied vs. implied, two tenors) are algebraically independent quantities; neither term of one appears in the other. | -- |

Concrete numeric divergence check (real data, computed live before trusting
the grid; see "Implementation checks" below): the trailing daily
correlation between family 016's own elevated-VIX-level flag and this
family's own backwardation flag, and the raw `^VIX3M`/`^VIX` ratio's
correlation with the raw `^VIX` level itself, both computed on real
overlapping (2006-07-17 through 2019-12-31) development data before any
grid backtest is trusted.

## Category

**Carry / term structure** (sec 4.5's list) -- the first family in this
loop to use this category (the plan's own gate note explicitly flags this
category as not yet tested). Unambiguous: this signal is a slope between
two points on the SAME implied-volatility curve, precisely the structure
sec 4.5 names "carry / term structure" for.

## Single-asset vs. portfolio scoping (judgment call, stated explicitly)

Assessed as a **single-asset family across all 5 core assets** under sec
4.1's standard >=3/5 rule, following families 006/007/011/015/016/019/025/
027/032/038's precedent for a single shared external, asset-agnostic
market signal applied independently per asset via the existing
single-asset `engine.py` -- no capital ever moves between the 5 assets;
each asset's own weekly deposit is resized up or down independently based
on the shared VIX-term-structure regime.

## Data inputs and reachability

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only,
  same as every prior family).
- **`^VIX`** and **`^VIX3M`**: both routed through the existing
  `src.backtest.v3.data.fetch_yf_macro(ticker)` helper (added for family
  015, reused unchanged by families 016/025/038's VIX/DXY/UMCSENT usage) --
  refuses any ticker already in `CORE_TICKERS`/`UNSEEN_TICKERS`, so neither
  can become a side-channel around the dev/holdout date gate. Neither
  ticker is in `CORE_TICKERS` or `UNSEEN_TICKERS`, so both are accepted.
  Both are daily market-price closes with no publication lag (same-day
  observable, unlike a survey/reported macro series), confirmed reachable
  with the row counts and start dates in the "Data-feasibility check"
  section above.
- **Availability vs. each core asset's own development window**:

| Asset | Dev start | `^VIX3M`-available dev days | Frac. of dev days with `^VIX3M` |
|---|---|---|---|
| SP500 | 1927-12-30 | 3,373 / 23,109 | 14.6% |
| GOLD | 2000-08-23 | 3,373 / 4,848 | 69.6% |
| SILVER | 2000-08-30 | 3,373 / 4,850 | 69.5% |
| BTC | 2014-09-17 | 1,932 / 1,932 | **100%** |
| OIL | 2000-08-24 | 3,373 / 4,857 | 69.4% |

  (Exact figures computed and cross-checked against `^VIX3M`'s real
  2006-07-17 start against each asset's own real `load_dev()` start date
  during the implementation step, before the grid is trusted -- see
  "Implementation checks.") Before `^VIX3M` history exists (SP500's
  pre-2006 stretch, and every asset's initial `ts_lookback` warm-up
  window), the multiplier defaults to **1.0 (neutral)**, i.e. behaves as
  plain DCA -- same warm-up convention as every continuous-percentile
  family in this loop (families 030/031/036/039/040), NOT the discrete
  `calm_fraction`-style default some earlier ladder families used
  (deliberately: see "Functional form" below for why a continuous
  multiplier is used here at all).

## Exact rules

Computed at each trading day's close `t`, using only data available by
that close.

1. **Term-structure ratio**: `ratio_t = VIX3M_t / VIX_t`, where both series
   are the raw daily closes of `^VIX3M` and `^VIX`, each forward-filled
   causally (never backward) onto the asset's own trading-day index
   (identical alignment method to families 016/025's `_aligned_vix_close`).
   `ratio_t > 1` = contango (the normal state); `ratio_t < 1` = backwardation
   (the stress state). `ratio_t` is `NaN` wherever either leg is
   unavailable (pre-2006-07-17, or a warm-up gap in either series).
2. **Trailing percentile rank**: `pctile_t` = the causal, point-in-time
   rolling percentile rank of `ratio_t` within the trailing `ts_lookback`
   window of past `ratio` values ending at `t` (inclusive) -- identical
   construction to families 036/039/040's `compute_percentile_rank`.
   Defaults to `0.5` (neutral) until `ts_lookback` days of valid `ratio`
   history exist.
3. **Continuous sizing multiplier** (deliberately continuous, not a
   discrete tier ladder -- see "Functional form" below):
   `m_t = clip(1 + k * (2 * pctile_t - 1), min_mult, max_mult)`.
   Elevated `pctile_t` (deep contango, ratio high relative to its own
   trailing history) -> `m_t > 1` (buy more, riding the carry premium).
   Depressed `pctile_t` (backwardation or shallow contango relative to its
   own trailing history) -> `m_t < 1` (buy less, banking a reserve).
   Identical functional form to families 030/031/036/039/040's own
   percentile-to-multiplier construction (family 040's exact formula,
   sign NOT inverted since elevated contango percentile is the "calm,
   deploy more" state).
4. **Weekly decision (week-end days only, no sells ever, no leverage)**:
   `target_buy_usd = min(weekly_deposit * m_t, max_lump_multiple *
   weekly_deposit)`. The engine's own unconditional cash cap
   (`buy_usd <= cash`, `engine.py` sec 3.2) enforces that a shortfall on a
   low-multiplier (backwardation-percentile) week simply banks as cash
   (earning IRX) until a later high-multiplier (deep-contango-percentile)
   week can spend it -- never leverage, never borrowing, exactly the
   families 030/031/036/039/040 reserve-banking mechanic.
5. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the ratio/percentile computation entirely and buys
   100% of that week's cash on every week-end day (0 otherwise) --
   reproduces plain DCA bit-for-bit, same pattern as every prior v3
   family's disable path.

## Functional form: continuous percentile-scaled multiplier, NOT a discrete ladder

Per this iteration's explicit instruction ("prefer a continuous
percentile-scaled sizing multiplier over a discrete ladder to avoid the
confirmed cash-cap-nullification bug"): this family uses the SAME
continuous `m_t = clip(1 + k*(2*pctile-1), min_mult, max_mult)` construction
families 030/031/036/039/040 already use, specifically to avoid the
failure mode families 014/020(-adjacent)/033/037 documented repeatedly --
a discrete ladder whose PRIMARY configuration's "otherwise" multiplier sits
at exactly 1.0 lets the engine's own no-leverage cash cap silently
nullify the reserve-banking arm, making the primary numerically identical
to plain DCA. Every grid cell's `min_mult` is asserted `< 1.0` at
module-import time (the families 014/033/037/039/040 lesson), and this is
verified directly via a cash-reserve-dynamics check (see "Implementation
checks") rather than merely asserted.

## Parameters (4 tunable + 2 fixed, <=5 tunable, per sec 3.4)

| Parameter | Grid values | Primary |
|---|---|---|
| `ts_lookback` (trailing window, trading days, for the ratio's own percentile rank) | 126, 252, 504 | 252 |
| `k` (sensitivity of the multiplier to the percentile) | 0.5, 1.0, 1.5 | 1.0 |
| `min_mult` (floor on the multiplier, backwardation/depressed-contango weeks) | 0.25, 0.5 | 0.5 |
| `max_mult` (ceiling on the multiplier, deep-contango weeks) | 1.5, 2.0 | 2.0 |

`max_lump_multiple` is fixed at **3.0** (not grid-varied) -- the same
absolute ceiling on any single week's buy relative to the normal weekly
deposit families 030/031/036/039/040 use, regardless of banked cash.
`^VIX`/`^VIX3M` (rather than `^VIX9D`/`^VIX6M` or some other tenor pair)
are fixed, not grid-varied -- chosen as the single most standard,
most-cited VIX term-structure pair in the cited literature (Simon &
Campasano 2014; Cheng 2019 both center their analysis on the 1-month vs.
3-month segment of the curve), and because `^VIX3M`'s 2006 start gives
meaningfully more development history than `^VIX6M`'s 2008 start or
`^VIX9D`'s 2011 start would. This keeps the family at 4 tunable
(grid-varied) parameters plus 1 fixed numeric constant (`max_lump_multiple`)
and 1 fixed tenor-pair choice, at/under the plan's <=5 tunable-parameter
ceiling.

`ts_lookback=252` (one trading year) is primary as the standard "trailing
year" reference window, matching family 016's own `vix_lookback=252` and
family 025's own `vrp_lookback=252` choices -- a no-look
convention/comparability choice, not a development-data result on THIS
signal. `k=1.0` and `min_mult=0.5`/`max_mult=2.0` are primary as the
identical middle-of-grid choices families 030/036/039/040 already used for
their own primary configurations of this same functional form, again for
comparability rather than picked to maximize any observed effect -- fixed
before any backtest was run.

## Grid

3 (`ts_lookback`) x 3 (`k`) x 2 (`min_mult`) x 2 (`max_mult`) =
**36 configurations** (at the sec 3.4 cap).

## Primary configuration

`ts_lookback=252, k=1.0, min_mult=0.5, max_mult=2.0` (`max_lump_multiple=3.0`
fixed for all configs).

## Expected sign

**Positive on both wealth and Sharpe**, if the historical
contango-carry-premium / backwardation-stress-persistence pattern holds up
net of the mechanism's own costs: this family bets that riding the normal
contango state (buying at or above the normal weekly rate) while banking a
reserve specifically during backwardation-flagged episodes captures the
literature-documented VIX term-structure premium, net of what it forgoes by
under-buying during backwardation, across all 5 core assets. As with every
prior timing/banking-mechanic family in this loop, this only reallocates
the *timing* of a fixed deposit stream, never total capital deployed and
never leverage, so even a real effect may show a modest absolute
wealth/Sharpe margin over DCA. `^VIX3M`'s relatively short history (2006+)
means fewer distinct backwardation episodes are available in development
data than family 016's `^VIX`-level signal saw (2006-2019 development
episodes: 2008-09 GFC, 2010 flash crash, 2011 debt-ceiling/Eurozone, 2015-16
China deval/oil crash, 2018-Q4) -- flagged here honestly as a smaller
effective sample of backwardation regimes than several prior VIX-based
families had, before any grid result is seen.

## Implementation-check plan (sec 3.2, to be run in the implementation step)

1. `enabled=False` bypass reproduces plain DCA bit-for-bit (units and cash).
2. A second reference point: a real `k=0.0` grid-shaped code path (going
   through the actual ratio/percentile computation) also reproduces plain
   DCA bit-for-bit (families 020/033/034/035/039/040's two-reference-point
   pattern).
3. Cash and positions never negative, for the DCA baseline, the primary
   config, and the grid's most aggressive corner (`ts_lookback=126, k=1.5,
   min_mult=0.25, max_mult=2.0`).
4. Total capital deployed never exceeds cumulative deposits + interest,
   via the principled "never invest" ceiling bound (family 021's fix) --
   primary config and the aggressive corner.
5. No-lookahead: perturbing all data after day `t` leaves every order
   on/before `t` unchanged, checked at two spot-check points deep into the
   sample (`t=6000`, `t=20000`), with particular attention to the
   `^VIX`/`^VIX3M` alignment/ffill step's strict causality.
6. Point-in-time macro: N/A in the ALFRED-vintage sense (`^VIX`/`^VIX3M`
   are daily market-price series with no revision/publication-lag concern,
   same as families 015/016/025's own "N/A" documentation).
7. **Distinction-verification check (required by this family's rigorous-
   distinction burden)**: on real overlapping development data
   (2006-07-17 through 2019-12-31), cross-tabulate this family's
   backwardation flag (`ratio_t < 1`) against family 016's own primary-
   config elevated-VIX-level flag, and separately compute the raw
   correlation between the `^VIX3M`/`^VIX` ratio and the raw `^VIX` level
   -- confirming genuine, non-trivial disagreement (family 025's
   verification pattern, applied here to families 016/041 instead of
   016/025).
8. Pre-grid non-degeneracy sanity check (primary config's multiplier shows
   real dispersion, not stuck at 1.0, on all 5 core assets) before
   trusting any grid result.
9. `PRIMARY_CONFIG` membership in the declared grid verified
   programmatically via an explicit module-import-time assertion (per
   family 021's lesson), alongside an assertion that every grid cell's
   `min_mult < 1.0`.
