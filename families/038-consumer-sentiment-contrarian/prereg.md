# Family 038: Consumer-sentiment contrarian regime

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Scoping decision: idea #37 (overnight/intraday return-split sizing) was
**not** taken this iteration -- full reasoning (required by this
iteration's task brief)

This iteration's task brief named idea #37 (seed research queue, "overnight/
intraday return-split sizing": increase buy size when an asset's own
trailing overnight, close-to-open, return component has been running
positive and elevated RELATIVE TO its trailing intraday, open-to-close,
return component -- a relative "overnight-driven vs intraday-driven"
regime -- decrease or hold normal otherwise) as the queue's next item, but
explicitly flagged it as very closely related to family 026
(`families/026-intraday-overnight/`, "Intraday/overnight return
decomposition sizing," already tested -- REJECTED) and required a careful,
honest comparison before proceeding.

**Family 026's exact construction** (`families/026-intraday-overnight/prereg.md`):
1. Daily overnight leg `overnight_t = Open_t/Close_{t-1} - 1` and intraday
   leg `intraday_t = Close_t/Open_t - 1`, both lagged (day `t`'s own legs
   excluded from its own signal).
2. Trailing cumulative sums of each leg over a `lookback_days` window of
   complete prior days.
3. `spread_t = cum_overnight_t - cum_intraday_t` -- the RELATIVE measure
   of how much of the asset's recent cumulative return has come from the
   overnight leg versus the intraday leg.
4. `spread_t` is ranked in its OWN trailing percentile (`pctile_lookback`
   days). `elevated_t` (spread in the top decile, i.e. overnight
   dominating intraday by an unusually wide margin, relative to the
   asset's own history) triggers a buy-MORE tilt; `compressed_t` (spread
   in the bottom decile, intraday dominating or overnight negative)
   triggers a buy-LESS tilt; otherwise a calm/normal fraction is bought.

**Idea #37 as stated in this iteration's task brief:** "increase buy size
when an asset's own trailing overnight ... return component has been
running positive and elevated RELATIVE TO its trailing intraday ... return
component (a relative overnight-driven vs intraday-driven regime),
decrease or hold normal otherwise."

**Side-by-side comparison, term by term:**

| Element | Family 026 | Idea #37 (task brief) |
|---|---|---|
| Return decomposition | Open/Close split into overnight and intraday legs | Identical: overnight (close-to-open) vs. intraday (open-to-close) legs |
| Comparison | Overnight leg **relative to** intraday leg (a spread) | Overnight **relative to** intraday leg -- the brief's own wording, "RELATIVE TO," capitalized for emphasis |
| Trigger direction | Overnight dominating intraday (elevated spread) -> buy more; intraday dominating (compressed/negative spread) -> buy less | Overnight "running positive and elevated" relative to intraday -> buy more; otherwise -> decrease/hold normal |
| Aggregation | Trailing cumulative sum over each leg, then a spread, then a trailing-percentile rank of the spread | Not specified beyond "trailing," but no ratio, different window, different asset scope, or different sign convention is named anywhere in the brief |
| Sizing shape | 3-tier (elevated buy-more / compressed buy-less / normal) | 2-3 tier, same qualitative shape ("increase ... decrease or hold normal") |

**Conclusion (honest, applying sec 7.2's "materially different: a
different signal definition or a different mechanism" standard to this
loop's own family 026, per this iteration's explicit instruction):** idea
#37, exactly as stated in the task brief, is **not materially different**
from family 026. Both use the identical Open/Close decomposition into
overnight and intraday legs, both size buys on the SAME relative
comparison (overnight performance relative to intraday performance, not a
standalone level of either leg), and both use the same qualitative
elevated-buy-more / otherwise-buy-less-or-normal shape. The task brief's
own suggested paths to a genuine distinction -- a ratio instead of a
spread, a different aggregation window, a different asset scope, or a
different sign convention -- are not actually present in how idea #37 is
stated; the brief names them as *hypothetical* ways a distinction *could*
be constructed, not as features already built into idea #37 as written.
Manufacturing one of those variants now (e.g. quietly redefining #37 as "a
ratio, not a spread") after already knowing family 026's exact
construction and result would be exactly the kind of look-then-relabel
maneuver sec 5.4's holdout-discipline spirit (and sec 7.2's closed-family
discipline, applied here by analogy to this loop's own prior family)
warns against -- the loop must not retune or reframe a family after
effectively having "seen" a closely related one's full construction, and
here the closely-related family 026 was tested and documented in an
earlier iteration of this very loop, with its exact spread/percentile/
elevated-compressed construction fully known before this decision is made.

**Decision: idea #37 is skipped entirely, per this iteration's explicit
task-brief instruction (option (b)).** It is removed from the active queue
below without being tested, with this reasoning recorded. A materially
different overnight/intraday-decomposition idea (e.g. a genuine ratio-based
or single-leg-level construction, explicitly NOT the relative-spread
construction already tested by family 026) could still be proposed as a
fresh, distinctly-defined idea in a future iteration, but idea #37 as
currently worded in the queue is not that idea.

**Substitute idea chosen: #39 (consumer-sentiment contrarian regime).**
Of the three alternatives offered (#39 consumer-sentiment contrarian
regime, #40 realized-kurtosis sizing, #41 rolling Sortino-ratio sizing),
#39 is chosen as the "most clearly distinct and interesting" substitute:
it is a **regime switch (macro/sentiment)** family built from a genuinely
new data source (a household-survey sentiment index, UMCSENT) with no
overlap at all with any prior price-only trailing-statistic family (#40
and #41 are both single-asset, price-only, higher-moment/risk-adjusted-
return sizing rules -- a category and data type this loop has already
tested repeatedly: families 003, 005, 023, 030, 031, 034, 035, 036, 037 --
whereas #39 is only this loop's 5th macro/sentiment regime family and its
1st built from a survey-based measure of household sentiment about the
economy, rather than a market-priced, credit, real-activity, or
monetary-quantity series). #39 is taken as this iteration's actual family,
below, per this iteration's explicit instruction.

## Source

Lemmon, M. and Portniaguina, E. (2006), "Consumer Confidence and Asset
Prices: Some Empirical Evidence," *Review of Financial Studies* 19(4),
1499-1529, and Baker, M. and Wurgler, J. (2006), "Investor Sentiment and
the Cross-Section of Stock Returns," *Journal of Finance* 61(4),
1645-1680 -- the sentiment-and-forward-returns literature's classic
finding that periods of unusually elevated investor/consumer optimism
tend to precede weaker-than-average forward returns (a "smart contrarian"
signal: euphoria is priced in and leaves little room for further upside
surprise, while excessive pessimism historically preceded stronger forward
returns as expectations reset too low). Seed research queue idea #39
(research-loop-plan-v3.md sec 7.3 replenishment; taken as this iteration's
substitute idea per the scoping decision above): "Consumer-sentiment
contrarian regime."

## Mechanism ("why would this work, and who is on the other side?")

The University of Michigan Consumer Sentiment Index (`UMCSENT`) is a
monthly household survey of consumers' own assessment of their personal
finances and the broader economy. The contrarian-sentiment story: when
`UMCSENT` reads unusually elevated relative to its own trailing history,
consumer (and by extension, marginal-investor) expectations are running
euphoric -- a state historically associated with asset prices that have
already run up to reflect that optimism, leaving comparatively little
room for further positive surprise and more room for disappointment. When
`UMCSENT` reads unusually depressed relative to its own trailing history,
sentiment has become excessively pessimistic, historically associated
with asset prices that have overshot to the downside and subsequently
mean-revert as sentiment normalizes. This family bets that banking new
deposits (rather than investing them immediately) during a euphoric-
sentiment window, and deploying with a capped catch-up lump once
sentiment is no longer euphoric, produces on average more favorable entry
prices than investing steadily through a euphoric-sentiment window -- the
same banking/cash-cap deposit-timing mechanic already used by families
004/006/007/011/015/019/027/032 (bank now, catch-up lump later,
cash-capped, never leverage), applied here to a household-survey
sentiment signal instead of a calendar, price, credit-spread,
real-activity, policy-rate, curve-shape, or monetary-quantity signal. The
"other side" of this trade is whoever continues to invest at a steady
pace through a euphoric-sentiment window and is compensated (in
expectation) for bearing that risk -- either an investor with no access
to or no belief in the sentiment signal, or one who believes that
consumer survey sentiment is too noisy, too lagged, or too disconnected
from asset-price fundamentals to be worth timing around.

## Category

**Regime switch (macro / credit / sentiment)** (research-loop-plan-v3.md
sec 4.5's category list; matches families 011/016/019/027/032's category
label -- a regime signal driving a banking/timing decision, no leverage or
shorting).

## The fivefold macro/sentiment-signal distinction (this loop now has 5
regime-switch families of this general shape, plus 1 market-priced
volatility-sentiment family; each must be shown to test something
genuinely separate)

| | v2.1 Strategy D | Family 011 | Family 016 | Family 019 | Family 027 | Family 032 | Family 038 (this) |
|---|---|---|---|---|---|---|---|
| Question | Is policy tight/loose? | Is credit/financial stress elevated? | Is options-market fear elevated? | Is real-economy leading activity below trend? | Does the curve shape signal future easing/recession? | Is the quantity of money growing faster/slower than trend? | Is household consumer sentiment euphoric or despondent relative to its own trend? |
| Data type | Policy rates, yield curve level | Market-priced credit spreads, financial-conditions index | Market-priced, options-implied volatility (`^VIX`) | Real-economy composite leading-activity index | Treasury yield-curve shape (2s10s) | Monetary aggregate (quantity of money) | **Household survey** of consumer sentiment (`UMCSENT`) |
| FRED/data series | DFEDTAR(U/L), DGS2, T10Y2Y, DFII10, FEDTARMD | BAA, AAA, NFCI | `^VIX` (yfinance) | USALOLITONOSTSAM | DGS2, DGS10 / T10Y2Y | M2SL | UMCSENT |
| Transmission channel | Price of money (policy rate) | Market pricing of default/liquidity risk | Options-market-implied near-term fear | Real-economy activity cycle | Bond-market policy expectations | Quantity-of-money / liquidity channel | Household expectations about personal finances and the broader economy |

`UMCSENT` is a **survey-based** measure of household sentiment,
constructed from consumer telephone interviews (University of Michigan
Surveys of Consumers), with **no direct link** to option prices,
realized/implied market volatility, credit spreads, policy rates, the
yield curve, or the money supply. It shares no input series with any of
the other 6 regime-type families above and is not derived from any of
them. Concretely, the two can and do diverge sharply: `UMCSENT` fell to
some of its lowest readings on record in 2022 on inflation and gas-price
concerns even as the equity market (and `^VIX`, family 016's own signal)
was comparatively calmer than the survey's despondency implied for parts
of that window; conversely, consumer sentiment stayed relatively muted
through much of the 2009-2015 equity bull market recovery even as the
market itself (and, per family 019, the real-economy CLI) recovered much
faster -- direct evidence that survey-based household sentiment is not a
simple proxy for market-priced fear, real-activity, credit, monetary, or
policy signals. (Both example episodes are stated for narrative context
only; the family's own required pre-2020 known-episode check below stays
strictly within development dates.)

## Single-asset scoping (judgment call, stated explicitly)

Following the precedent set by families 006/007/011/015/016/019/027/032
(a macro/sentiment signal that does not depend on which of the 5 core
assets it is applied to gets tested on all 5 core assets under sec 4.1's
standard single-asset >=3/5 rule, using the existing single-asset
`engine.py`, rather than narrowed to one asset), this family is assessed
as a **single-asset family across all 5 core assets**, independently per
asset. `UMCSENT` is a US household-sentiment signal, not specific to any
one of gold/silver/oil/BTC/SP500 -- the same "macro/sentiment signal is
asset-agnostic" reasoning already used for families 006/007/011/015/016/
019/027/032.

## Exact rules

Computed at each week-end decision day `t` (same weekly cadence as every
other v3 family), using only the point-in-time sentiment signal available
as of `t`'s close (see "Point-in-time / publication-lag discipline"
below) and the asset's own trading-day calendar/price for fills -- the
sentiment signal itself never depends on the asset being traded.

1. **Point-in-time construction.** The raw FRED `UMCSENT` series (monthly,
   observation date = the 1st of the reference month) is shifted forward
   by a fixed conservative publication lag (see below) before any
   normalization is computed, so every derived value "seen" on trading
   day `t` is built only from `UMCSENT` levels that had actually been
   published (in at least preliminary form) by `t`'s close.
2. **Trend-relative normalization.** At each (lagged) `UMCSENT`
   observation, compute its own trailing-window statistic against its
   own trailing `lookback_years`-year window of prior observations, using
   one of two methods selected by `normalization_method`:
   - `zscore`: `z_i = (UMCSENT_i - trailing_mean) / trailing_std`.
   - `percentile`: `pct_i` = the percentage of the trailing window's
     observations that are `<= UMCSENT_i`.
3. **Threshold level** (`threshold_level`, an integer 0/1/2 selecting a
   threshold, matching families 019/032's convention): for `zscore`,
   thresholds by level `{0: 0.5, 1: 1.0, 2: 1.5}` standard deviations
   ABOVE the trailing mean; for `percentile`, thresholds by level
   `{0: 80.0, 1: 90.0, 2: 95.0}`. **Direction, stated plainly:** this is
   the mirror image of families 019/032's "below threshold = weak/bank"
   direction -- here, sentiment reading ABOVE its own trailing threshold
   is the "euphoric" (buy-less/bank) trigger, the contrarian sign this
   family's mechanism requires.
4. **Regime.** **Euphoric** if the normalized statistic is `>=` its
   threshold; otherwise **normal/depressed** (this family does not
   distinguish "normal" from "depressed" with a separate third state --
   both non-euphoric readings get the same full-deploy-plus-catch-up
   treatment, matching families 019/032's own 2-state, not 3-state,
   structure). Before enough history exists to fill both the signal's own
   warm-up and the `lookback_years` normalization window, the regime
   defaults to **normal** (behaves like plain DCA during signal warm-up,
   the same convention families 011/019/032 use).
5. **Weekly decision (week-end days only), no sells ever** (matching
   families 003/005/006/007/011/016/019/027/032's precedent -- a pure
   timing/banking rule that never liquidates existing units, staying
   within the plan's no-leverage/no-shorting constraint by construction):
   - **Euphoric:** buy `euphoric_tilt_fraction * weekly_deposit`. The
     remainder is banked as cash (earning IRX, sec 3.2) until the regime
     next reads normal.
   - **Normal/depressed:** buy `min(cash, max_lump_multiple *
     weekly_deposit)` -- this both makes the current week's normal
     deposit and, if there is banked cash from a prior euphoric stretch,
     deploys a capped catch-up lump, cash-capped so this can never become
     leverage.
6. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the signal/regime computation entirely and buys
   100% of that week's cash on every week-end day (0 otherwise) --
   reproduces plain DCA bit-for-bit, same pattern as every prior v3
   family's disable path. As families 010/011/019/032 flagged explicitly:
   a grid config with `euphoric_tilt_fraction=0` and `enabled=True` is
   **NOT** equivalent to DCA -- the regime computation still runs. Only
   `enabled=False` is checked against the DCA baseline. (This family has
   no ladder-style "otherwise multiplier" at all -- its non-euphoric arm
   is a full-deploy-plus-catch-up-lump rule, structurally the SAME shape
   as families 019/032's own already-validated "accelerating/normal" arm,
   not a continuous ladder multiplier -- so the near_high_mult-style
   cash-cap-nullification failure mode families 014/033/037 hit does not
   apply to this family's design: the "otherwise" arm is deliberately the
   MOST aggressive arm, not a passive near-1.0x arm.)

## Point-in-time / publication-lag discipline (sec 3.2 bullet 4)

**Data reachability, verified live before writing this pre-registration:**
`UMCSENT` is reachable via FRED's `fredgraph.csv` endpoint (the same
mechanism `fetch_fred_macro()` already uses for families 011/019/027/032) --
confirmed live: 676 monthly observations, 1952-11-01 through the present.
Ample coverage for every core asset's development period, including BTC's
short 2014-2019 window.

**Revision character and publication lag.** The University of Michigan
Surveys of Consumers publishes each reference month's reading in two
releases WITHIN that same reference month: a preliminary reading (roughly
mid-month) and a final reading (roughly the last business day of the
month). Unlike GDP, M2, or the OECD CLI, `UMCSENT`'s within-month
preliminary-to-final revision is small and the index itself is not
subject to later, multi-year benchmark-style revisions once the final
reading for a month is published. To stay conservative and consistent
with every prior macro family in this loop (011/019/027/032 all used a
fixed lag standing in for full vintage reconstruction rather than
attempting it), a **35-calendar-day** lag is applied from each
observation date (the 1st of the reference month) before the value
becomes usable -- comfortably past even the final, end-of-month release
for that same reference month, and shorter than family 032's 45-day M2
lag only because `UMCSENT`'s own release calendar is faster (both
readings land within the reference month itself, unlike M2's ~3-5-week-
after-month-end H.6 release).
- **Known, honestly-flagged limitation** (same category families 019/032's
  prereg.md already flagged for their own series): a fixed publication
  lag protects against look-ahead in *availability timing* but does not
  fully protect against a look-ahead risk in the *value itself* if a
  preliminary reading were ever materially revised at the final release --
  this risk is smaller for `UMCSENT` than for the survey/composite series
  prior families used (family 019's OECD CLI), but is not zero, and is
  flagged here before any backtest is run, to be repeated in results.md
  regardless of verdict.

## Pre-grid sanity checks (run before the grid, per established loop
convention for macro/regime families)

1. **Non-degeneracy:** the primary configuration's `euphoric` condition
   must fire non-trivially (not near-0%, not near-100% of dev days) on
   every core asset.
2. **Known-episode check, strictly within dev dates (pre-2020):** the
   primary configuration's normalized `UMCSENT` reading during the
   well-documented dot-com-era consumer-confidence peak (`UMCSENT` peaked
   near an all-time high of 112.0 in January 2000, a widely cited episode
   of historically extreme consumer optimism just before the dot-com
   crash) must read as **euphoric** for a clear majority of the
   1999-06-01 through 2000-05-31 window (allowing for at most a small
   minority of isolated non-euphoric monthly prints given the signal's
   monthly granularity) -- confirming the signal construction correctly
   identifies a real, well-known sentiment-euphoria episode before any
   grid result is trusted. This spot-check stays strictly within
   development dates (1999-2000 is two decades before the 2020-01-01
   holdout cutoff) and is checked, never the reverse: the loop does not
   search for whichever episode happens to look best, it confirms the
   single well-documented episode named in this prereg.md.

## Data inputs

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only,
  same as every prior family).
- `UMCSENT` from FRED, via `src.backtest.v3.data.fetch_fred_macro("UMCSENT")`
  (the same helper families 011/019/027/032 already use -- no new
  data-access code needed, keeping the `fredgraph.csv` raw-data-leak
  check's allowlist unchanged).

## Parameters (4 tunable + 1 fixed, all <=5 total)

| Parameter | Grid values | Primary |
|---|---|---|
| `normalization_method` | "zscore", "percentile" | "zscore" |
| `lookback_years` | 5, 10 | 10 |
| `threshold_level` | 0, 1, 2 | 1 |
| `euphoric_tilt_fraction` | 0.0, 0.25 | 0.0 |

Fixed (not grid-varied, does not count against the <=5 tunable-parameter
ceiling): `max_lump_multiple = 6.0` -- the same "headroom essentially
never binds" constant families 011/019/032 used for the analogous
parameter.

`normalization_method="zscore"` is primary as the more standard, more
interpretable choice, matching families 019/032's own primary choice for
the analogous parameter. `lookback_years=10` is primary as a
business-cycle-length window (long enough to span at least one full
sentiment cycle), matching families 011/019/032's own primary reasoning.
`threshold_level=1` (`z >= 1.0`, i.e. sentiment one standard deviation
above its own trailing mean) is primary as the middle of the three grid
levels, matching family 019/032's own primary choice for the analogous
parameter. `euphoric_tilt_fraction=0.0` (full banking while euphoric) is
primary as the "purest" test of the timing-shift hypothesis, matching
families 006/007/011/019/032's own primary choice for the analogous
parameter.

## Grid

2 (`normalization_method`) x 2 (`lookback_years`) x 3 (`threshold_level`)
x 2 (`euphoric_tilt_fraction`) = **24 configurations** (<=36 cap).

## Primary configuration

`normalization_method="zscore", lookback_years=10, threshold_level=1,
euphoric_tilt_fraction=0.0` (`max_lump_multiple=6.0` fixed for all
configs).

## Expected sign

**Positive on both wealth and Sharpe, if the contrarian-sentiment
mechanism is real and its "buy after euphoria resolves" logic survives
this loop's fee/robustness bar** -- stated honestly as the family's
central hypothesis, not a certainty. A genuine risk flagged before any
backtest, informed by families 003/005/006/007/010/011/019/027/032's now-
consistent pattern in this loop: like those families, this mechanism only
reallocates *timing* of a fixed deposit stream (never total capital
deployed, no leverage), so even a real effect may show a small absolute
wealth/Sharpe margin over DCA. A further risk specific to this family, per
family 027/032's own honestly-flagged caution about "rare, clustered"
macro/sentiment regime signals: genuinely euphoric `UMCSENT` readings
(1 standard deviation or more above trend) may be relatively rare and
temporally clustered in the pre-2020 development sample (concentrated
around a handful of historical booms, e.g. the mid-1960s, mid-1980s, and
late-1990s), so even a real effect risks being a small-sample,
few-dominant-episode result -- exactly the class of result sec 4.2's DSR
and sec 4.3's placebo test are designed to catch, and exactly the failure
mode families 011/019/027/032/031/034 have each already hit in this loop.

## Complexity ceiling check (sec 3.4)

- Rules fit on one page, computed from end-of-day OHLC + a single monthly
  FRED series. PASS.
- At most one order per asset per trading day (one weekly buy). PASS.
- 4 tunable parameters (<=5). PASS.
- Data: `UMCSENT` via the already-established `fetch_fred_macro()` helper,
  confirmed reachable live. PASS.
- Grid: 24 configurations (<=36), one primary configuration declared above
  before any testing. PASS.

## Not a re-test of sec 7.2's closed list or any prior v3 family

No family in sec 7.2's closed list (v1 buy-the-dip/trim-the-spike, v2
SmartDCA, v2 ADCA B1/B2, v2 C1-C3 rebalancing, v2.1 Strategy D) used a
household-survey consumer-sentiment series -- Strategy D used policy-rate
and yield-curve data exclusively. No prior v3 family (001-037) used
`UMCSENT` or any consumer-confidence survey either; the closest prior
families (011 credit spreads, 016 VIX, 019 OECD CLI, 027 yield curve, 032
M2) are each distinguished above by data type and transmission channel.
This is confirmed a new signal, not a re-parameterization.

## Implementation-check plan (sec 3.2, to be run in the implementation
step)

1. `enabled=False` bypass reproduces plain DCA bit-for-bit (units and
   cash).
2. Cash and positions never negative, for the DCA baseline and the
   primary config.
3. Total capital deployed never exceeds cumulative deposits + interest
   (primary config), via family 021's principled "never invest"
   ceiling-bound method.
4. **No-lookahead**: perturbing all OHLC data strictly after day
   `t_check` must leave every order generated on or before `t_check`
   unchanged. Checked at two spot-check points deep into the sample
   (`t=6000`, `t=20000`).
5. **Point-in-time macro**: the documented 35-day lag must actually
   matter -- shortening it to 0 days must change SOME historical regime
   readings vs. the documented lag (proving the lag is not a no-op),
   while every real backtest uses the documented lag only.
6. **Pre-grid non-degeneracy check** (before the grid runs): compute the
   primary config's `euphoric` regime frequency directly on development
   data for all 5 core assets (must be non-trivial: not near-0%, not
   near-100%) -- confirming the trigger fires non-trivially on all 5
   assets before any backtest result is trusted.
7. **Known-episode check** (before the grid runs, strictly pre-2020): the
   January 2000 dot-com-era `UMCSENT` peak must read as euphoric for a
   clear majority of the 1999-06 through 2000-05 window.

## Files (to be created in the implementation/run step)

- `src/backtest/v3/strategies/consumer_sentiment_regime.py`
- `scripts/v3/run_038_consumer_sentiment.py`
- `families/038-consumer-sentiment-contrarian/results.md`,
  `grid_results.csv`, `_primary_per_asset.csv`, `_run_output.json`
- `state/trials/new_038_*.csv` (24 files)
