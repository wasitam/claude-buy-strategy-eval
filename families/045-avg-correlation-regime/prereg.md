# Family 045: Cross-asset average-correlation regime sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Longin, F. and Solnik, B. (2001), "Extreme Correlation of International
Equity Markets," *Journal of Finance* 56(2), 649-676 (correlations across
markets rise sharply during downturns -- the "correlation breakdown"/
tail-dependence literature, the same source family 034's queue entry #34
already cited for a *rotation* mechanism); Ang, A. and Bekaert, G. (2002),
"International Asset Allocation With Regime Shifts," *Review of Financial
Studies* 15(4), 1137-1187 (a high-correlation "bear"/systemic-stress
regime that recurs across asset classes, with reduced cross-sectional
diversification benefit precisely when it matters most). Research queue
idea #46 (research-loop-plan-v3.md sec 7.3 addendum).

## Mechanism ("why would this work, and who is on the other side?")

Longin & Solnik and Ang & Bekaert document that pairwise correlations
across markets are not stable: they rise, often sharply, during systemic
stress/crisis episodes ("correlations go to 1" in a crash) and fall in
calm periods when each asset's price action is driven more by its own
idiosyncratic factors. A period of LOW average cross-asset correlation is
therefore a regime where the 5-core-asset universe (S&P 500, gold,
silver, BTC, oil) is behaving as 5 largely independent, idiosyncratic-
risk-dominated markets -- a genuine diversification-rich environment in
which a marginal dollar into any one of them is not simply riding the
same systemic factor as the other four. A period of HIGH average
cross-asset correlation is a systemic-stress regime in which all 5 assets
are moving together, and the diversification a multi-asset DCA plan is
implicitly counting on is temporarily much weaker than usual.

This family sizes EACH asset's OWN weekly buy up when that asset's own
trailing average pairwise return correlation against the OTHER 4 core
assets sits LOW in its own trailing history (buy more into a
diversification-rich regime, while it is genuinely available), and sizes
it down when that average correlation sits HIGH (bank a reserve during a
systemic co-movement/stress regime, deploying it later once
diversification has reasserted itself). A plain fixed-$500/week DCA
investor buys the same dollar amount into every asset every week
regardless of how correlated the universe currently is -- on this
hypothesis, it buys "blind" through exactly the stress episodes when the
5-asset portfolio is least diversified and (per the same literature) most
exposed to a common shock, and under-buys during the calm, genuinely
diversified periods when a marginal dollar's idiosyncratic-risk exposure
is most attractive.

**Who is on the other side:** systematic fixed-weight/fixed-schedule
buyers (plain DCA, and any other periodic contributor who does not
condition size on realized co-movement structure) -- on this hypothesis
they contribute the same-sized dollar into every regime, including the
systemic-stress episodes this family explicitly avoids over-weighting.
**Explicit tension flagged and owned:** buying MORE when correlations are
low and LESS when they are high is a bet that low realized
cross-sectional correlation is not itself predictive of near-term returns
(it is treated purely as a diversification-quality/systemic-risk proxy,
not a directional return signal) -- if elevated correlation regimes
happen to coincide with a market bottom (a classic contrarian buying
opportunity, and the opposite prescription), this mechanism would be
banking cash exactly when a contrarian buyer would want to lean in. This
is a real, opposite-direction possibility and is not resolved by
argument; it is exactly what sec 4.1's backtest checks.

## Category

**Regime switch (macro / credit / sentiment).** Chosen per the research
queue's own filing of idea #46 (not "Cross-asset rotation / relative
strength" or "Volatility targeting") because the mechanism is a
systemic-co-movement REGIME classification -- structurally the same shape
as the loop's other regime-switch families (011 credit-stress,
016/025/041/047 VIX-family, 019 OECD CLI, 027 yield-curve, 032 M2 growth,
038 consumer sentiment, all of which classify the CURRENT market/macro
environment into a calm-vs-stressed state and size accordingly) rather
than a rotation (redirecting capital ACROSS assets, family 043's shape)
or a pure volatility-of-returns statistic (family 003's shape). The
signal here differs from every other regime-switch family in this loop
only in its INPUT: it is derived purely from the 5 core assets' own
realized co-movement, with no external macro/credit/sentiment data series
at all -- documented explicitly below as the required distinction from
that whole family of priors.

## Required distinction 1: hybrid design vs. family 043 (cross-asset INPUT vs. cross-asset OUTPUT)

Family 043 (Amihud-illiquidity cross-asset rotation, NEAR-MISS) is a
**portfolio** family: its OUTPUT is a reallocation of the SAME pooled
$2,500/week deposit ACROSS the 5 assets (a target-weight table, assessed
against fixed-weight 5-asset DCA per sec 4.1's Portfolio line). Capital
literally moves between assets every week.

Family 045 (this family) is a **single-asset** family, assessed under sec
4.1's Single-asset >=3/5-core-assets line, exactly like families
001/003/005/etc. Each of the 5 core assets keeps its OWN independent
$500/week deposit stream and its OWN independent decider; no dollar ever
moves from one asset's ledger to another's. **What makes this family
genuinely new relative to every single-asset family before it (001-042,
044) is that each asset's decider input is not a statistic of that
asset's OWN price series alone** -- it is a statistic (the average of 4
pairwise correlations) that is mathematically undefined without looking
at the OTHER 4 assets' return series too. This is a deliberate hybrid:
**cross-asset INPUT, single-asset OUTPUT** -- the mirror image of family
043's cross-asset OUTPUT, single-signal-per-asset INPUT (043's own
per-asset Amihud percentile, reused unmodified from family 021, is a
purely within-asset statistic; only the cross-sectional RANKING and the
rebalancing action are cross-asset in 043). Concretely:

| | Family 043 (Amihud rotation) | Family 045 (this family) |
|---|---|---|
| Signal computed from | Each asset's OWN Amihud ratio history alone (within-asset statistic, reused verbatim from family 021) | ALL 5 assets' return histories jointly (asset A's signal is mathematically undefined given only A's own price series) |
| Action taken | Reallocates the POOLED deposit's WEIGHT across the 5 assets (capital moves between assets) | Sizes EACH asset's OWN, separate weekly buy up/down (capital never moves between assets) |
| Assessed against | Fixed-weight 5-asset DCA (Portfolio line, sec 4.1) | Per-asset DCA, >=3/5-core-assets rule (Single-asset line, sec 4.1) |
| Cross-asset dependency location | OUTPUT (the rebalancing decision) | INPUT (the sizing signal) |

This distinction is verified concretely, not just asserted, in the
pre-grid checks below (see "Hybrid-design verification").

## Required distinction 2: price-only vs. every macro/credit/sentiment regime family (011/016/019/025/027/032/038/041/042/047)

Every VIX-family (016 level, 025 VIX-minus-realized spread, 041
VIX3M/VIX term structure, 047 VVIX vol-of-vol), credit/macro family (011
BAA-AAA/NFCI, 019 OECD CLI, 027 T10Y2Y, 032 M2 growth, 038 consumer
sentiment) in this loop derives its regime signal from an **externally
published series** -- an options market (CBOE), a bond market spread, a
government statistical release, or a survey. This family's signal is
computed **purely from the 5 core assets' own already-loaded OHLC price
data** (the exact same Close series `load_dev()` already returns for
every prior price-only family, e.g. 001/005/020/028/030/031/036/039/040/
044) -- no new external data source, no new reachability risk, no
publication lag, no ALFRED/point-in-time vintage handling required at
all. Concretely: family 042 (realized-volatility term structure) is the
closest PRICE-ONLY prior with a "market-wide regime" flavor, but its
statistic is a single asset's own short-vs-long realized-vol RATIO
(within-asset, no cross-asset dependency whatsoever) -- not comparable to
this family's genuinely cross-asset average-correlation statistic. This
is documented as a real structural distinction: this is the loop's first
regime-switch family whose signal has zero data-reachability risk and
needs no publication-lag/point-in-time handling of any kind, because it
never leaves the already-gated `load_dev()` price data.

## Exact rules

For each core asset `a` in {SP500, GOLD, SILVER, BTC, OIL}, using ONLY
`load_dev()`'s Close data for all 5 core assets (no macro/external data):

1. Daily log return `r_t^b = log(Close_t^b) - log(Close_{t-1}^b)` for
   every asset `b` (including `a` itself), `r_0^b := 0`.
2. For each of the OTHER 4 assets `b != a`: causally align `b`'s Close
   series onto asset `a`'s own trading-day calendar via a forward-fill-
   only reindex (never backward-filled -- identical technique to families
   016/025/041's `_aligned_close` for `^VIX`, applied here to another
   core asset's own price series instead of an external macro series).
   `b`'s log return on `a`'s calendar is computed from this aligned,
   forward-filled Close, and is explicitly marked undefined (NaN) on
   every day before `b`'s own first real observation (never fabricated
   by filling backward from `b`'s eventual start).
3. `corr_t^{a,b}` = the trailing Pearson correlation of `r^a` and `b`'s
   aligned-and-log-returned series, over the last `corr_window` trading
   days of asset `a`'s own calendar ending at `t` (inclusive; rolling,
   `min_periods=corr_window`) -- undefined (NaN) if the window contains
   any day before `b`'s own history starts, since `b`'s return is NaN
   there and NaN propagates through the correlation window.
4. `avg_corr_t^a` = the simple mean of the (up to 4) `corr_t^{a,b}`
   values that are defined that day, **provided at least 2 of the 4 are
   defined**; otherwise `avg_corr_t^a` is undefined (NaN) that day. This
   is the asset-agnostic, causal, cross-asset systemic-co-movement proxy.
5. `pctile_t^a` in [0, 1]: a causal, point-in-time rolling percentile rank
   of `avg_corr_t^a` within its own trailing `pctile_lookback`-day window
   of past `avg_corr` values (identical rolling-percentile construction to
   families 025/031/035/036/039/040/041/042/044). Defaults to 0.5
   (neutral) wherever `avg_corr_t^a` itself is undefined (NaN) -- either
   during warm-up, or (see "BTC's shorter history" below) during any
   stretch where fewer than 2 of the other 4 core assets have started
   trading yet.
6. Continuous sizing multiplier (never a discrete ladder, per the
   established cash-cap-nullification lesson):
   `m_t^a = clip(1 - k * (2 * pctile_t^a - 1), min_mult, max_mult)`.
   **Sign, stated explicitly**: this is the sign-INVERSE of every prior
   continuous-percentile family in this loop (001/025/031/035/036/039/
   040/041/044 all use `m_t = 1 + k*(2*pctile_t-1)`, elevated signal ->
   buy MORE). Here, a LOW `avg_corr` percentile (diversification-rich) ->
   `m_t` above 1 -> buy MORE; a HIGH `avg_corr` percentile (systemic-
   stress, correlations elevated toward each other) -> `m_t` below 1 ->
   buy LESS/bank a reserve. The inversion is a direct, necessary
   consequence of the mechanism's stated sign (buy more in the
   diversification-rich regime) and is verified mechanically, not just
   asserted, in the pre-grid checks below.
7. Order: `target_buy_usd = weekly_deposit * m_t^a`, capped at
   `max_lump_multiple * weekly_deposit` and then at available cash (the
   engine's own no-leverage cap, sec 3.2) -- never a sell, never
   leverage, never borrowing. A below-1.0-multiplier day banks the
   shortfall as cash (earning IRX), available to fund a later
   above-1.0-multiplier day -- the same reserve mechanism every prior
   continuous-sizing family in this loop uses.

### BTC's shorter history and the 3 data eras (judgment call, documented per this iteration's explicit instruction)

`load_dev()`'s actual per-asset dev-period start dates are SP500
1927-12-30, GOLD/SILVER/OIL ~2000-08-23/30, BTC 2014-09-17 (all end
2019-12-31). This creates three eras for, e.g., SP500's own `avg_corr`
signal:

- **1927-12-30 to ~2000-08-23** (SP500-only era): none of the other 4
  core assets exist yet. Zero of the 4 pairwise correlations are
  defined -> `avg_corr` is NaN throughout -> `pctile` defaults to 0.5 ->
  `m_t=1.0` -> **this family is bit-for-bit identical to plain DCA for
  SP500's entire pre-2000 history**, a genuine, documented consequence of
  rule 4's ">=2 valid legs" requirement, not a bug.
- **~2000-08-23 to 2014-09-17** (4-asset era, no BTC): GOLD, SILVER and
  OIL are all available (3 of the 4 possible legs; SP500's signal in this
  era averages up to 3 legs, other assets among GOLD/SILVER/OIL average
  up to 2 legs from the other two plus SP500). This satisfies the ">=2"
  threshold, so a genuine (non-degenerate) signal begins here.
- **2014-09-17 to 2019-12-31** (full 5-asset era): all 4 possible legs
  are available for every asset's own `avg_corr`.

This is the **documented 4-asset (and, before 2000, fewer-than-4-asset)
fallback** the task brief anticipated, arising naturally from
`load_dev()`'s own real per-asset start dates rather than an arbitrarily
chosen cutoff: **no shared 5-asset calendar is imposed** (unlike family
043's portfolio calendar, which had to start at BTC's own start date
since a portfolio must hold every asset simultaneously) -- each asset
keeps its own full dev-period length, and the correlation signal itself
gracefully degrades to "neutral, no tilt" via rule 4's threshold whenever
too few other assets exist to define a meaningful average, rather than
truncating SP500's ~72 years of pre-2000 history or GOLD/SILVER/OIL's
~14 years of pre-BTC history down to BTC's own short 2014-2019 window.
Verified concretely in the pre-grid checks below (era-by-era non-NaN
fraction and multiplier dispersion, per asset).

## Complexity ceiling (sec 3.4, checked)

- Rules fit on one page (above); computable end-of-day from Close only
  (already-cached, already-reachable data for all 5 core assets -- no new
  data source).
- At most one order per asset per trading day (a single buy order,
  sized by `m_t^a`, no sells -- identical order shape to every prior
  continuous-sizing single-asset family).
- **4 tunable parameters** (<=5): `corr_window`, `pctile_lookback`, `k`,
  `min_mult`.
- Grid: `corr_window` (3) x `pctile_lookback` (2) x `k` (3) x `min_mult`
  (2) = **36 configurations** (at the sec 3.4 cap), one primary
  configuration declared below, before any backtest.

## Parameters and grid

| Parameter | Grid values | Primary |
|---|---|---|
| `corr_window` | 60, 90, 126 | 126 |
| `pctile_lookback` | 252, 504 | 252 |
| `k` | 0.5, 1.0, 1.5 | 1.0 |
| `min_mult` | 0.25, 0.5 | 0.5 |

Fixed constants (not grid-varied, matching every prior continuous-sizing
family's convention): `max_mult=2.0`, `max_lump_multiple=3.0`.

**Primary configuration:** `corr_window=126, pctile_lookback=252, k=1.0,
min_mult=0.5` (`corr_window=126` trading days is roughly 6 months --
long enough, per the task brief's own guidance, for a reasonably stable
pairwise-correlation estimate, while still being responsive within a
single calendar year; the other three parameter values mirror the
primary-configuration convention every prior continuous-percentile family
in this loop (025/031/035/036/039/040/041/044) has used).

## Expected sign of the effect

Positive: the primary configuration is expected to beat plain DCA on
final wealth AND Sharpe on at least 3 of the 5 core assets, by avoiding
over-weighting systemic-stress/high-co-movement episodes (when the
universe's effective diversification is weakest) and over-weighting
genuinely idiosyncratic, low-co-movement episodes instead -- per the
Longin & Solnik / Ang & Bekaert regime-shift literature cited above. This
is a modest-magnitude sizing tilt (max multiplier range 0.5x-2.0x, same
order of magnitude as every prior continuous-sizing family in this loop),
so a small, possibly economically negligible effect on any single asset
is an anticipated, not surprising, outcome regardless of sign.

## Planned pre-grid verification (executed in the run script, before any grid result is trusted)

1. **Hybrid-design verification**: confirm concretely that asset A's
   `avg_corr` signal changes when another asset's price history is
   perturbed (proving genuine cross-asset dependence, unlike every
   within-asset single-asset family before it) and that the per-asset
   deciders never move capital between assets (proving the single-asset
   OUTPUT claim), completing the family 043 distinction above with code,
   not just prose.
2. **Crisis-window correlation-spike verification**: using only real
   development data (strictly pre-2020, no unseen tickers), confirm that
   average pairwise correlation across the assets available during the
   2008 global financial crisis (SP500, GOLD, SILVER, OIL -- BTC does not
   exist yet) spikes into an elevated percentile of its own trailing
   history during the Sep-Dec 2008 stress window, versus a calmer
   reference period earlier in the same asset's development history --
   confirming the statistic behaves as the mechanism requires before any
   grid is trusted.
3. **Era-by-era non-degeneracy check**: for SP500 specifically (the only
   asset spanning all 3 data eras), confirm the pre-2000 era is
   bit-for-bit `m_t=1.0` (per the documented fallback above) and that the
   post-2000 and post-2014 eras show genuine, non-degenerate multiplier
   dispersion.
4. **Sign-inversion spot-check**: confirm on real data that a low
   `avg_corr` percentile day produces `m_t>1` and a high `avg_corr`
   percentile day produces `m_t<1` (the necessary consequence of rule 6's
   stated sign, verified mechanically rather than only asserted).
5. **No-lookahead perturbation test extended to the cross-asset inputs**:
   perturb data for the OTHER 4 assets (not just asset A's own data)
   after a checkpoint day `t`, and confirm every order asset A's decider
   generates on or before `t` is unchanged -- the standard single-asset
   no-lookahead check (`checks.check_no_lookahead`) only perturbs the
   primary asset's own data and would NOT catch a lookahead bug that
   enters through the cross-asset correlation inputs, so a family-
   specific extension is required and is written directly into the run
   script (following the precedent of family-specific check extensions
   documented in `state/bugfix_log.md`).
6. **Pre-grid non-degeneracy and cash-reserve-dynamics checks** (per
   established convention): the primary config's multiplier must not be
   stuck at 1.0 for nearly the whole sample on any asset with a
   meaningful post-fallback history, and average cash must meaningfully
   differ from the plain-DCA baseline.
7. **`PRIMARY_CONFIG` membership in the declared grid**, verified via an
   import-time assertion in the strategy module (family 021's lesson).
