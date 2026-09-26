# Research queue (research-loop-plan-v3.md sec 7.3)

Idea #1 (10-month/200-day trend exit) has been taken from the queue and used
for family `001-trend-exit`; see `families/001-trend-exit/` (REJECTED).
Idea #2 (dual momentum rotation) has been taken from the queue and used for
family `002-dual-momentum`; see `families/002-dual-momentum/` (NEAR-MISS).
Idea #3 (volatility-managed sizing) has been taken from the queue and used
for family `003-vol-managed-sizing`; see `families/003-vol-managed-sizing/`
(REJECTED).
Idea #4 (value averaging) has been taken from the queue and used for family
`004-value-averaging`; see `families/004-value-averaging/` (NEAR-MISS).
Idea #5 (time-series momentum sizing) has been taken from the queue and used
for family `005-tsmom-sizing`; see `families/005-tsmom-sizing/` (NEAR-MISS).
Idea #6 (turn-of-month deposit timing) has been taken from the queue and
used for family `006-turn-of-month`; see `families/006-turn-of-month/`
(REJECTED).
Idea #7 (day-of-week deposit timing) has been taken from the queue and
used for family `007-day-of-week`; see `families/007-day-of-week/`
(REJECTED).
Idea #8 (CAPE / earnings-yield valuation sizing) has been taken from the
queue and used for family `008-cape-valuation`; see
`families/008-cape-valuation/` (REJECTED -- structural: the mechanism is
only definable for S&P 500 among the 5 core assets, so sec 4.1's
>=3/5-core-assets rule cannot be satisfied by construction; run as a
documented SP500-only diagnostic instead, whose own result was also weak.
See families/008-cape-valuation/results.md "Flag for the owner" -- ideas
#9 and #12 below have the same structural issue and should be read with
that in mind when their turn comes).

**Owner decision (2026-09-25), on the structural gap flagged in family 008's
results.md:** ideas #9 (BTC on-chain valuation) and #12 (commodity
term-structure carry) have the same problem as #8 -- their mechanism is only
definable for one asset among the 5 core assets (BTC on-chain metrics don't
exist for gold/silver/oil/SP500; term-structure carry data isn't available
for all 5 either), so sec 4.1's >=3/5-core-assets rule can never be
satisfied by construction, no matter the single-asset result. The owner's
call: **skip these entirely rather than run them as diagnostics or relax
the win rule.** Removed from the queue below without being tested. This
does not change sec 4.1 itself -- it's a per-idea scoping call, documented
here for the final report's "what didn't get tested and why" section.

Idea #10 (gold/silver ratio rotation) has been taken from the queue and
used for family `010-gold-silver-ratio`; see
`families/010-gold-silver-ratio/` (NEAR-MISS). Assessed as a **2-asset
portfolio family** (gold+silver only, vs. fixed-weight 2-asset DCA) rather
than under either of sec 4.1's literal single-asset or 5-asset-portfolio
lines -- a real interpretive gap for a mechanism scoped to a strict subset
of the 5 core assets, distinct from family 008's structurally single-asset
gap. See `families/010-gold-silver-ratio/prereg.md`'s "2-asset
assessment-scoping decision" section for the full reasoning. Sec 4.1 passed
very decisively (27/27 grid configs beat DCA at both fees, the strongest
margin of any family so far), but DSR (computed on this family's own
2-asset excess series) was effectively zero and the placebo test's wealth
leg missed its bar -- see results.md.

Idea #11 (credit-stress risk-off filter) has been taken from the queue and
used for family `011-credit-stress-filter`; see
`families/011-credit-stress-filter/` for the verdict.

Idea #13 (momentum-tilted rebalancing) has been taken from the queue and
used for family `013-momentum-rebalance`; see
`families/013-momentum-rebalance/` (REJECTED). Assessed as a **5-asset
portfolio family** (sec 4.1 Portfolio line) vs fixed-weight 5-asset DCA,
directly following families 002's and 010's precedent. Explicitly
documented in prereg.md as NOT a re-test of sec 7.2's closed C1/C2/C3
(fixed vs momentum-dependent/time-varying targets) or of family 002 (dual
momentum's binary in/out rotation vs this family's continuous
always-fully-invested weight tilt -- different mechanism categories,
"Cross-asset rotation / relative strength" vs "Rebalancing / allocation").
Sec 4.1: primary config beats DCA on Sharpe but not wealth (fails the
combined bar). Only the grid's most aggressive tilt_strength=2.0 arm
(2/16 configs) passed both bars -- can't be promoted per sec 4.4's own
rule. DSR effectively zero.

Idea #14 (drawdown-from-high reserve deployment) has been taken from the
queue and used for family `014-drawdown-reserve`; see
`families/014-drawdown-reserve/` (REJECTED). Assessed as a **single-asset
family** (sec 4.1 Single-asset line) across all 5 core assets, category
Sizing/valuation. Included the rigorous SmartDCA-distinction argument
required by sec 7.2 (all-time-high ratchet vs. SmartDCA's trailing moving
average -- see prereg.md). Sec 4.1: primary config (`near_high_mult=1.0`)
beats DCA on 0/5 core assets -- its results are numerically identical to
plain DCA on every asset, because `near_high_mult=1.0` means no cash
reserve is ever banked near the high, so the engine's own no-leverage cash
cap silently clips every in-drawdown "buy more" request back down to that
week's own deposit. Two independent implementation-check reference points
(an `enabled=False` bypass flag, and the real `ladder=flat,
near_high_mult=1.0` grid arm run through the actual signal computation)
both confirmed the strategy code itself is correct -- the DCA-identical
result is a genuine finding about the primary parameter choice, not a bug.
Grid: 0/32 configs (0.0%) reach the majority bar; DSR exactly 0.

This was the **last idea from the original sec 7.3 seed queue** (#1-14,
minus #9/#12 skipped by owner decision). The queue below (#15-18, added
last iteration) now carries the loop forward; per sec 8 step 2, the next
iteration checks whether >=5 ideas remain and researches more if not (4
remain, one below the threshold -- the next iteration's first task).

**Queue replenishment (2026-09-25, prior iteration, plan sec 8 step 2):** the
queue was down to 2 remaining ideas (#13, #14) after #11 was taken, below
the sec 8 step-2 threshold of 5. 4 new ideas were added below after a
literature search (SSRN/arXiv q-fin/practitioner sources), each chosen to
(a) be testable on a multi-asset subset of the 5 core assets via free data
already reachable in this environment (yfinance `^VIX`, `DX-Y.NYB`, or the
assets' own OHLC -- confirmed reachable, see this iteration's session log),
(b) not re-tread families 001-010's exact mechanisms or the sec 7.2 closed
list, and (c) avoid the single-asset-only structural trap flagged in
family 008's results.md (unlike #9/#12, skipped by owner decision) -- each
signal below is asset-agnostic (like 006/007/011's precedent) or explicitly
a relative-value pair, never structurally definable for only one core
asset.

| # | Idea | Category | Key source |
|---|---|---|---|
| 13 | Momentum-tilted rebalancing (rebalance toward trend winners) | Rebalancing | Asness, Moskowitz & Pedersen (2013) |
| 14 | Drawdown-from-high reserve deployment (a different reference point than SmartDCA's moving average) | Sizing | Practitioner literature; must justify why it isn't a re-test |
| 16 | VIX-level contrarian fear-gauge sizing: buy size scales up when the CBOE VIX (`^VIX`, confirmed reachable) sits in an elevated trailing percentile (a market-wide fear/overreaction signal), tilts down when VIX is complacent -- a *contrarian*, short-horizon mean-reversion bet, mechanistically distinct from family 003 (inverse-*realized*-variance sizing, no view on direction) and family 005 (trend-following sign of trailing return). Applied identically across all 5 core assets as a market-wide sentiment gauge, same precedent as 006/007/011. | Volatility targeting / Sizing | Whaley (2000), "The Investor Fear Gauge"; practitioner "buy the VIX spike" literature |
| 18 | "Halloween effect" / Sell-in-May seasonal deposit timing: bank a larger share of May-October deposits, deploy a catch-up lump-sum tilt into November-April, on a fixed annual calendar window (distinct time horizon and window shape from families 006's turn-of-month weekly window and 007's day-of-week window -- an annual seasonal cycle, not a monthly or weekly one). Calendar-only signal, testable identically on all 5 core assets per the 006/007 scoping precedent. | Seasonality / execution timing | Bouman & Jacobsen (2002), *The Halloween Indicator, "Sell in May and Go Away": Another Puzzle*, American Economic Review |

Idea #15 (DXY / US Dollar Index regime rotation) has been taken from the
queue and used for family `015-dxy-regime`; see `families/015-dxy-regime/`
for the verdict.

Idea #16 (VIX contrarian fear-gauge sizing) has been taken from the queue
and used for family `016-vix-contrarian`; see
`families/016-vix-contrarian/` (REJECTED). Assessed as a single-asset
family across all 5 core assets, category **Sizing / valuation** (chosen
over "Volatility targeting" specifically to keep the family-003 distinction
unambiguous -- see prereg.md's full mechanism/signal/sign/functional-form
distinction table). Sec 4.1: primary config beats DCA on wealth AND Sharpe
on 0/5 core assets (wealth underperforms on every asset; Sharpe alone
beats DCA on 2/5). Grid: 0/24 configs reach the majority bar. DSR
effectively zero.

**Queue replenishment (2026-09-25, this iteration, plan sec 8 step 2):**
after #15 was taken, 3 ideas remained (#16-18), below the sec 8 step-2
threshold of 5. 3 new ideas were added below after a literature search,
each chosen to (a) be testable on the 5 core assets (or explicitly flagged
if a data-availability caveat applies, to be resolved at that family's own
gate step), (b) not re-tread families 001-015's exact mechanisms or the
sec 7.2 closed list, and (c) avoid the single-asset-only structural trap
flagged in family 008's results.md.

| # | Idea | Category | Key source |
|---|---|---|---|
| 19 | OECD Composite Leading Indicator (CLI) regime switch: bank deposits when the US CLI (FRED `USALOLITONOSTSAM`, monthly, ALFRED-revisable) reads below its own trailing-normalized threshold (signaling below-trend / weakening economic momentum), deploy normally or with catch-up when the CLI is at/above it. Asset-agnostic macro regime signal, applied per-asset like 006/007/011. Distinct from family 011 (a credit/financial-conditions spread, not a composite leading-activity index) and from v2.1 Strategy D (policy-rate stance, not real-economy activity) -- must state this distinction explicitly in prereg.md, same discipline family 011 used for its own v2.1 distinction. | Regime switch (macro) | OECD (2026), Composite Leading Indicators; series construction background in Conference Board/OECD leading-indicator literature |
| 20 | 52-week-high proximity momentum tilt: buy size scales up as an asset's own trailing close approaches (or sits at/near) its trailing 52-week high, scales down the further below it the price sits -- a price-anchoring momentum signal, price-only (no external data dependency), testable identically on all 5 core assets. Mechanistically distinct from family 001 (binary moving-average trend exit) and family 005 (sign-only 12-month time-series momentum): this is a continuous, anchor-based signal on distance-from-52-week-high itself, which George & Hwang (2004) show has separate, additive forecasting power beyond a plain trailing-return momentum signal. | Trend / time-series momentum exit | George, T.J. and Hwang, C.-Y. (2004), "The 52-Week High and Momentum Investing," *Journal of Finance* 59(5), 2145-2176 |
| 21 | Amihud illiquidity-shock sizing: buy larger on/after days where an asset's own Amihud illiquidity ratio (|daily return| / dollar volume) spikes into an elevated trailing percentile (a proxy for a forced-selling / liquidity-shock episode where price impact is unusually large per dollar traded), on the hypothesis that such shocks are disproportionately compensated and tend to mean-revert. Price-and-volume-only signal, no macro dependency, testable per-asset. **Data caveat, to be resolved at this idea's own sec 8 step-3 gate:** `src/backtest/v3/data.py`'s cached OHLC currently drops the `Volume` column (Open/High/Low/Close only) -- adding it back for all 5 core assets (yfinance provides Volume for all of them, including futures/BTC) is expected to be a small, contained change to `_fetch_yf_raw`, but must be verified (and, if BTC/futures volume proves unreliable pre-a certain date, flagged) before this family's implementation step, not assumed. | Sizing / valuation | Amihud, Y. (2002), "Illiquidity and Stock Returns: Cross-Section and Time-Series Effects," *Journal of Financial Markets* 5(1), 31-56 |

Idea #17 (RSI2 short-horizon mean-reversion sizing) has been taken from the
queue and used for family `017-rsi2-reversion`; see
`families/017-rsi2-reversion/` (REJECTED). Assessed as a single-asset
family across all 5 core assets, category **Sizing / valuation**. Sec 4.1:
primary config beats DCA on wealth AND Sharpe on 2/5 core assets (SP500,
SILVER) -- short of the 3/5 majority, though it does beat DCA on Sharpe
alone on 5/5 assets. Grid: 2/24 (8.3%) configs reach the combined majority
bar. DSR effectively zero. Included the rigorous triple-distinction
argument required by this iteration's task (vs. family 016's shared VIX
signal, family 003's realized-variance sizing, and families 001/005's
long-horizon trend-following signals -- see prereg.md).

4 ideas remain (#18-21), below the sec 8 step-2 threshold of 5 -- the next
iteration's first task is to research and add more before taking #18.

**Queue replenishment (2026-09-25, this iteration, plan sec 8 step 2):**
before taking #18, 4 ideas remained (#18-21) at the sec-8-step-2 threshold
of 5, below it once #18 is taken. 3 new ideas were added below after a
literature search (WebSearch), each chosen to (a) be testable on the 5
core assets, (b) not re-tread families 001-018's exact mechanisms or the
sec 7.2 closed list -- in particular distinct from family 018 itself
(taken this same iteration; see below) despite two of the three sharing
its "Seasonality / execution timing" category -- and (c) avoid the
single-asset-only structural trap flagged in family 008's results.md.

| # | Idea | Category | Key source |
|---|---|---|---|
| 22 | Presidential election cycle timing: bank a larger share of deposits during years 1-2 of the US presidential term (historically weaker, per Hirsch's Stock Trader's Almanac and Santa-Clara & Valkanov's "Presidential Puzzle"), deploy a catch-up lump-sum tilt during years 3-4 (historically strongest, especially year 3). A **quadrennial** seasonal cycle -- a full order of magnitude longer period than family 018's annual Nov-Apr/May-Oct window, 006's monthly turn-of-month window, or 007's weekly day-of-week window -- and a different economic story (political business-cycle / policy-manipulation and investor-sentiment literature specific to the US election calendar, vs. institutional flow cycles or crypto liquidity composition). Calendar-only signal (US presidential term year, publicly known in advance), testable identically on all 5 core assets per the 006/007/018 scoping precedent -- though, like 006/007, the anchor literature is US-equity-specific, a caveat to be stated explicitly in that family's own prereg.md. | Seasonality / execution timing | Santa-Clara, P. and Valkanov, R. (2003), "The Presidential Puzzle: Political Cycles and the Stock Market," *Journal of Finance* 58(5), 1841-1872; Hirsch, Y. (1967-), *Stock Trader's Almanac* |
| 24 | Seasonal Affective Disorder (SAD) / daylight-length deposit timing: size deposits by a **continuous** function of Northern Hemisphere day length (shortest around the winter solstice, longest around the summer solstice) rather than a discrete calendar window, banking more as daylight shortens through fall (proxying rising risk aversion per the SAD literature's depression-and-risk-aversion channel) and deploying a catch-up tilt as daylight lengthens through winter/spring. Explicitly distinct from family 018 despite the shared "Seasonality" category and both being annual-periodicity: 018's mechanism is a fixed, discrete 6-month institutional-flow window (in or out), while this family's signal is a smooth, continuously-varying function of calendar day peaking/troughing at the solstices, motivated by an investor-psychology/risk-aversion channel rather than institutional payment or rebalancing cycles -- this distinction must be made explicit in that family's own prereg.md when its turn comes, mirroring the discipline 018's own prereg.md uses to distinguish itself from 006/007. Calendar-only signal, testable identically on all 5 core assets. | Seasonality / execution timing | Kamstra, M.J., Kramer, L.A. and Levi, M.D. (2003), "Winter Blues: A SAD Stock Market Cycle," *American Economic Review* 93(1), 324-343 |

Idea #18 ("Halloween effect" / Sell-in-May seasonal deposit timing) has
been taken from the queue and used for family `018-halloween-seasonal`;
see `families/018-halloween-seasonal/` for the verdict.

Idea #19 (OECD Composite Leading Indicator regime switch) has been taken
from the queue and used for family `019-oecd-cli-regime`; see
`families/019-oecd-cli-regime/` (REJECTED). Assessed as a single-asset
family across all 5 core assets, category **Regime switch (macro)**.
Verified live FRED reachability for `USALOLITONOSTSAM` before
pre-registering (no substitution needed) and documented the required
triple distinction from family 011 (credit-stress/financial-conditions
spread) and v2.1 Strategy D (policy-rate/yield-curve stance) in
prereg.md, plus the ALFRED true-vintage coverage gap (only from
2018-07) that forced a conservative fixed 60-day publication lag in
place of full point-in-time vintage reconstruction over most of the
development period. Sec 4.1: primary config beats DCA on wealth AND
Sharpe on 0/5 core assets -- the strategy underperforms DCA on BOTH
metrics on every single asset, unlike most prior timing/banking
families' "Sharpe wins, wealth lags" pattern. Grid: 0/24 configs (0.0%)
reach the majority bar, the weakest grid result of any family so far.
DSR effectively zero, driven by a genuinely negative raw pooled excess
Sharpe.

Idea #20 (52-week-high proximity momentum tilt) has been taken from the
queue and used for family `020-52wk-high-tilt`; see
`families/020-52wk-high-tilt/` (NEAR-MISS). Assessed as a single-asset
family across all 5 core assets, category **Trend / time-series momentum
exit**. Sec 4.1: primary config beats DCA on wealth AND Sharpe on exactly
3/5 core assets (GOLD, SILVER, OIL), the minimum passing count, with small
margins. Grid: 16/32 (50.0%) configs reach the majority bar -- sec 4.4
FAIL. DSR effectively zero (negative raw pooled excess Sharpe) -- sec 4.2
FAIL. Sec 4.3 run in full (sec 4.1 passed): rolling windows and bootstrap
both PASS, but the placebo circular-shift test FAILS decisively (real
result at the 13th/37th percentile, need >=95th) -- the strongest single
piece of evidence that the George & Hwang mechanism itself, not just some
generic time-varying sizing tilt, is not what's producing the narrow sec
4.1 pass. Also the highest CSCV PBO (0.486) of any family so far.
Documented the required triple distinction from families 001, 005 and,
critically, 014 (this family's ladder is the deliberate sign-inverse of
family 014's: buy MORE near a 52-WEEK high vs family 014's buy MORE far
below an ALL-TIME high) and explicitly verified the sign was implemented
correctly (mean multiplier 1.500 near-high vs 0.6233 far-below on SP500)
before trusting any backtest, per this iteration's task instruction.

4 ideas remain (#21-24), below the sec 8 step-2 threshold of 5 -- the next
iteration's first task is to research and add at least one more idea
before taking #21.

**Queue replenishment (2026-09-25, this iteration, plan sec 8 step 2):**
before taking #21, 4 ideas remained (#21-24), below the sec-8-step-2
threshold of 5. 3 new ideas were added below after a literature search
(WebSearch), each chosen to (a) be testable on the 5 core assets with data
already reachable in this environment (yfinance `^VIX`, the assets' own
Open/Close, or FRED `T10Y2Y`, all previously confirmed reachable by
families 003/016/011), (b) not re-tread families 001-021's exact
mechanisms or the sec 7.2 closed list, and (c) avoid the single-asset-only
structural trap flagged in family 008's results.md. One candidate found
during this search -- the pre-FOMC announcement drift (Lucca & Moench
2013/2015) -- was considered and explicitly **not added**: the source
literature itself finds the effect is specific to US equities and
documents its *absence* in Treasuries, currencies and commodities, so it
would fail the multi-asset-definable-data requirement before any
backtest, the same structural problem as ideas #9/#12 (which the owner
decided to skip outright rather than run as single-asset diagnostics) --
noted here for the final report's "what didn't get tested and why"
section, per that same owner decision's precedent.

| # | Idea | Category | Key source |
|---|---|---|---|
| 25 | Variance risk premium (VRP) sizing: buy size scales up when the spread between the CBOE VIX (`^VIX`, option-*implied* forward-looking vol, confirmed reachable per family 016) and an asset's own trailing *realized* volatility is elevated in a trailing percentile (i.e. implied vol is running unusually rich relative to what has actually been realized -- the classic variance-risk-premium signal), scales down when the spread is compressed or negative. Explicitly a **spread of two moments** (implied minus realized), mechanistically distinct from family 003 (realized volatility alone, no implied-vol comparison, direction-agnostic) and family 016 (the raw VIX *level* alone, no realized-vol comparison at all) -- must state this distinction explicitly in prereg.md, same discipline family 021 used for its own triple distinction from 003/016/017. Applied identically across all 5 core assets (VIX as the shared implied-vol input, each asset's own realized vol as the asset-specific input), same cross-asset-signal precedent as 006/007/011/016. | Volatility targeting | Bekaert, G. and Hoerova, M. (2014), "The VIX, the Variance Premium and Stock Market Volatility," *Journal of Econometrics* 183(2), 181-192; Carr, P. and Wu, L. (2009), "Variance Risk Premiums," *Review of Financial Studies* 22(3), 1311-1341 |
| 26 | Intraday/overnight return decomposition sizing: buy size scales with the recent realized share of an asset's total return that has accrued **overnight** (prior Close to next Open) versus **intraday** (Open to Close) over a trailing window -- a decomposition of the SAME daily return series into two components neither of which any prior family in this loop has isolated (family 001/005/020 use only Close-to-Close trailing returns or levels; no prior family splits a day's return into its open-close and close-open halves). Testable identically on all 5 core assets from the existing cached OHLC (no new data source), price-only. | Sizing / valuation | Lou, D., Polk, C. and Skouras, S. (2019), "A Tug of War: Overnight versus Intraday Expected Returns," *Journal of Financial Economics* 134(1), 192-213 |
| 27 | Yield-curve slope (2s10s) inversion regime filter: bank deposits when the US Treasury 10-year minus 2-year yield spread (FRED `T10Y2Y`, already cached in `data/T10Y2Y.csv` from a prior iteration's reachability check) is negative or compressed in a trailing percentile (a classic recession-risk signal), deploy normally or with a catch-up tilt when the curve is normally sloped. A **term-structure-of-interest-rates** signal, explicitly distinct from family 011 (a credit-risk spread, BAA-AAA/NFCI, not a Treasury term-structure measure) and from v2.1 Strategy D (the level/stance of the policy rate itself, not the shape of the yield curve) -- must state this distinction explicitly in prereg.md, same discipline family 019 used for its own distinction from 011 and v2.1 D. Asset-agnostic macro regime signal, applied per-asset like 006/007/011/019. | Regime switch (macro / credit / sentiment) | Estrella, A. and Mishkin, F. S. (1998), "Predicting U.S. Recessions: Financial Variables as Leading Indicators," *Review of Economics and Statistics* 80(1), 45-61 |

Idea #21 (Amihud illiquidity-shock sizing) has been taken from the queue
and used for family `021-amihud-illiquidity`; see
`families/021-amihud-illiquidity/` (REJECTED). Volume-data feasibility was
confirmed for all 5 core assets (see prereg.md/results.md -- SILVER is the
noisiest but still workable; no asset required exclusion). Assessed as a
single-asset family across all 5 core assets, category **Sizing /
valuation**. Sec 4.1: primary config beats DCA on wealth AND Sharpe on
**0/5** core assets -- underperforms DCA on wealth on every asset (most
assets show a small Sharpe improvement alongside a small wealth loss, the
same "Sharpe wins, wealth lags" pattern several mechanism-agnostic sizing
families in this loop have shown). Grid: 0/32 configs (0.0%) reach the
majority bar, tied with family 019 for the weakest grid result so far. DSR
effectively zero (negative raw pooled excess Sharpe). Sec 4.3 not run
(only run when sec 4.1 passes).

3 ideas remain (#22-24) plus the 3 just added (#25-27) = 6 ideas, above the
sec 8 step-2 threshold of 5 -- no further replenishment needed before the
next iteration takes #22.

Idea #22 (Presidential election cycle timing) has been taken from the
queue and used for family `022-election-cycle`; see
`families/022-election-cycle/` (REJECTED). Assessed as a single-asset
family across all 5 core assets, category **Seasonality / execution
timing**, following the 006/007/018 precedent (asset-agnostic calendar
mechanism, US-equity-specific motivating literature -- not the CAPE/
family-008 structural-exclusion case, since the signal needs no
asset-specific fundamentals data). Sec 4.1: primary config beats DCA on
wealth AND Sharpe on 2/5 core assets (SP500, BTC) -- short of the 3/5
majority. Grid: 0/24 (0.0%) configs reach the combined majority bar; best
any config manages is 3/5. CSCV PBO=0.614 (notably high, consistent with
a genuinely noisy signal given only ~5 complete 4-year cycles in most
assets' development history). DSR effectively zero. Documented the
required distinction from families 006 (monthly), 007 (weekly) and 018
(annual) in prereg.md: this is a QUADRENNIAL cycle keyed to the actual US
presidential election calendar (year mod 4), not a modular function of
month/weekday. By-hand cross-checked `cycle_year()` against 16 known
election/non-election years before any backtest, and verified
`PRIMARY_CONFIG` membership in `GRID` programmatically per family 021's
lesson (no mismatch found this time). Flagged the 2008/2000 crisis-year
confound risk in prereg.md before backtesting.

2 ideas remain (#23-24) plus the 3 from the prior replenishment (#25-27) =
5 ideas, at the sec 8 step-2 threshold -- no further replenishment needed
before the next iteration takes #23, though it is worth researching one
more idea early next iteration to stay comfortably above the threshold.

Idea #23 (Realized-skewness sizing) has been taken from the queue and used
for family `023-realized-skewness`; see `families/023-realized-skewness/`
(REJECTED). Assessed as a single-asset family across all 5 core assets,
category **Sizing / valuation**. Sec 4.1: primary config beats DCA on
wealth AND Sharpe on **2/5** core assets (SP500, BTC) -- short of the 3/5
majority; GOLD/SILVER/OIL all lose on both metrics. Grid: 1/32 (3.1%)
configs reach the combined majority bar (need >=22/32), and the one that
does (`skew_window=60`) is not the primary -- every `skew_window=90`
config manages only 2/5 assets, the longer window uniformly weaker than
the shorter one across the whole grid. CSCV PBO=0.0, the lowest of any
family so far (a consistently, stably weak grid rather than a noisy one).
DSR effectively zero (negative raw pooled excess Sharpe). Pre-grid
non-degeneracy sanity check confirmed the fixed-threshold `RSkew_t`
design fires non-trivially (14.9%-32.7%) on every asset for both the
negative-skew and positive-skew regimes. Verified `PRIMARY_CONFIG`
membership in `GRID` programmatically (assertion at import time), per
family 021's lesson -- no mismatch. Documented the required triple
distinction from families 003 (2nd-moment realized variance, direction-
agnostic), 016 (shared forward-looking implied-vol level) and 017
(bounded price-level oscillator, no moment interpretation) in prereg.md,
per this iteration's explicit task instruction. Sec 4.3 not run (only run
when sec 4.1 passes). Holdout not opened (not a finalist).

1 idea remains (#24) plus the 3 from the prior replenishment (#25-27) = 4
ideas, below the sec 8 step-2 threshold of 5 -- one more idea is added now
to restore the threshold before the next iteration takes #24.

| # | Idea | Category | Key source |
|---|---|---|---|
| 28 | 50-day/200-day moving-average crossover ("golden cross" / "death cross") regime tilt: scale buy size up while the 50-day SMA sits above the 200-day SMA (a classic bull-regime signal), scale down (banking a reserve) while it sits below. Explicitly distinct from family 001 (price level vs. a SINGLE 10-month/200-day moving average, with a binary invest/park-in-cash exit-to-T-bills rule) and from family 005 (sign of the raw 12-month return, no moving average at all): this family compares TWO moving averages of different lengths to each other, never compares price to a single average, and tilts buy size continuously between two multipliers rather than exiting to cash entirely -- must state this distinction explicitly in prereg.md, same discipline family 020 used to distinguish itself from families 001/005/014. Price-only signal (daily Close), no external data dependency, testable identically on all 5 core assets. | Trend / time-series momentum exit | Brock, W., Lakonishok, J. and LeBaron, B. (1992), "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns," *Journal of Finance* 47(5), 1731-1764 |

When fewer than 5 ideas remain, the next iteration researches more and adds
them here, each with a source, mechanism and category (plan sec 8 step 2).

Idea #24 (SAD daylight-length deposit timing) has been taken from the
queue and used for family `024-sad-daylight`; see
`families/024-sad-daylight/` (REJECTED). Assessed as a single-asset
family across all 5 core assets, category **Seasonality / execution
timing**. Sign interpretation (Kamstra, Kramer & Levi 2003, cited and
explained in prereg.md): buy less/bank as daylight shortens toward the
winter solstice (realized returns relatively low through fall per KKL),
buy more as daylight lengthens away from it (returns relatively high in
winter/spring). Sec 4.1: primary config beats DCA on wealth AND Sharpe on
**0/5** core assets -- decisive fail (need >=3/5); the strategy beats DCA
on Sharpe alone on 4/5 assets but loses on WEALTH on all 5/5, so the
combined requirement is never met. Grid: 0/18 (0.0%) configs reach the
combined majority bar, and the 0/5-wealth pattern is uniform across the
ENTIRE grid (every `tilt_strength`/`power`/`max_lump_multiple`
combination) -- not an unlucky primary-config draw. CSCV PBO=0.0
(consistently weak, not overfit). DSR effectively zero (negative raw
pooled excess Sharpe). Astronomical sanity spot-check (solstice/equinox
daylight values, 4 separate years) and pre-grid non-degeneracy check
(multiplier spans its full designed range on every asset) both confirmed
correct before any backtest was trusted. Verified `PRIMARY_CONFIG`
membership in `GRID` programmatically at module import time, per family
021's lesson. Rigorous distinction from family 018 (continuous
solstice-symmetric daylight function vs. discrete binary 6-month window;
mood/risk-aversion channel vs. institutional-flow/vacation channel)
documented in prereg.md, per this iteration's explicit task instruction.
Sec 4.3 not run (only run when sec 4.1 passes). Holdout not opened (not a
finalist).

4 ideas remain (#25-28), below the sec 8 step-2 threshold of 5 -- one more
idea is added now to restore the threshold before the next iteration
takes #25, following family 023's precedent (adding exactly 1 replacement
idea).

Idea #29 (threshold/band-triggered rebalancing) was taken from the queue
and, per this iteration's explicit task guidance, **refined** before
pre-registration into a **risk-parity/inverse-volatility** target-weight
mechanism instead of the literal drift-band-trigger framing above: on
inspection, a pure drift-band trigger (rebalance only when a position
wanders beyond a fixed +/-N percentage-point band from a FIXED target)
looked too close in spirit to v2's closed C1-C3 sweep (which already
varies the rebalancing SCHEDULE against fixed targets; a band trigger is
just another way of choosing WHEN to rebalance toward the same kind of
fixed target, not a different kind of target), whereas risk-parity
weighting changes WHAT the target itself is (volatility-based, not fixed)
-- a more clearly distinct mechanism, and the one explicitly endorsed by
the task's default guidance. See `families/029-risk-parity-rebalance/`
(**REJECTED**). Assessed as a 5-asset portfolio family, category
**Rebalancing / allocation**: each week, target weights are set inversely
proportional to each asset's own trailing realized volatility (bounded,
renormalized, optionally EMA-smoothed), rebalanced weekly. Rigorously
distinguished in prereg.md from sec 7.2's closed C1-C3 (fixed target
weights vs. this family's volatility-dependent, time-varying targets) and
from family 013 (momentum-tilted rebalancing, this loop, REJECTED: family
013's target is driven by trailing RETURN, this family's by trailing
VOLATILITY -- the two mechanisms make opposite allocation calls for BTC,
this universe's asset with both the highest trailing return and the
highest volatility over the dev window). Pre-grid non-degeneracy check
confirmed BTC's average risk-parity weight (0.070) is materially below
both gold's (0.310) and the 0.20 equal-weight baseline. Sec 4.1: primary
config (`vol_lookback_days=126, min_weight=0.05, max_weight=0.40,
smoothing_halflife_days=10`) loses to fixed-weight 5-asset DCA on BOTH
wealth and Sharpe at both fees (0.1%: 1.447x/0.789 vs DCA's 2.937x/0.802)
-- FAIL, decisively, and uniformly across the whole 12-config grid (0/12
pass the combined bar, need >=8/12). DSR effectively zero (raw pooled
excess Sharpe strongly negative, -69.0%/yr annualized). CSCV PBO=0.386.
Interpretation: BTC dominates this dev window's total 5-asset compounding
so heavily that any mechanism structurally underweighting it -- whether
family 013's momentum-driven or this family's volatility-driven
rebalancing -- gives up more wealth than it recovers in risk-adjusted
terms; a second instance of this same BTC-dominance failure mode in the
"Rebalancing / allocation" category. Holdout not opened (not a finalist).

4 ideas remain (#30-33), below the sec 8 step-2 threshold of 5 -- one more
idea is added now to restore the threshold before the next iteration
takes #30, following families 023/024/025/026/027/028's precedent (adding
exactly 1 replacement idea).

| # | Idea | Category | Key source |
|---|---|---|---|
| 34 | Cross-asset tail-risk/drawdown-correlation rotation: each week, rank the 5 core assets by their trailing correlation to a rolling "risk-off" composite (e.g. the equal-weight average trailing return of the other 4 assets during that composite's worst trailing-decile days), and tilt allocation toward assets that have historically shown the LOWEST co-drawdown behavior with the rest of the universe (a diversification-quality signal), rather than toward assets with the lowest standalone volatility (this loop's own family 029, risk parity) or the strongest trailing momentum (family 013). A **Cross-asset rotation / relative strength** family (allocation driven by CROSS-asset co-movement structure during stress, not any one asset's own price level, return, or volatility in isolation) -- genuinely distinct from family 002 (binary absolute+relative momentum admission gate, no correlation/co-movement measure at all), family 010 (gold/silver ratio, a two-asset relative-value spread, not a 5-asset correlation structure), and family 013/029 (both single-asset trailing statistics -- return or volatility -- with no cross-asset dependence structure at all). Price-only signal (daily Close of all 5 core assets), no external data dependency. | Cross-asset rotation / relative strength | Longin, F. and Solnik, B. (2001), "Extreme Correlation of International Equity Markets," *Journal of Finance* 56(2), 649-676 (correlations rise in market downturns -- the "correlation breakdown" / tail-dependence literature); Ang, A. and Chen, J. (2002), "Asymmetric Correlations of Equity Portfolios," *Journal of Financial Economics* 63(3), 443-494 |

When fewer than 5 ideas remain, the next iteration researches more and adds
them here, each with a source, mechanism and category (plan sec 8 step 2).

Idea #25 (Variance risk premium (VRP) sizing) has been taken from the
queue and used for family `025-vrp-sizing`; see `families/025-vrp-sizing/`
(REJECTED). Assessed as a single-asset family across all 5 core assets,
category **Volatility targeting**. Signal: `VRP_t = IV_t - RV_t` (VIX
minus each asset's own trailing realized vol -- the SPREAD, not either
leg alone), ranked in its own trailing percentile: elevated spread (top
decile) -> buy more; compressed spread (bottom decile) -> buy less. Sec
4.1: primary config beats DCA on wealth AND Sharpe on **0/5** core assets
-- decisive fail (need >=3/5); SP500 and BTC beat DCA on Sharpe alone via
the banking/smoothing mechanic but lose on WEALTH on all 5/5 assets. Grid:
0/36 (0.0%) configs reach the combined majority bar, uniform failure
across the entire 36-point parameter space. CSCV PBO=0.471, notably
higher than most REJECTED families (a diffuse, noise-dominated grid
rather than a reliably-wrong one) -- a secondary diagnostic only, does not
change the decisive 0/36 wealth-failure verdict. DSR effectively zero
(negative raw pooled excess Sharpe). Rigorous triple distinction from
family 003 (realized vol alone, inverse sign) and family 016 (VIX level
alone, no realized-vol comparison) documented in prereg.md with a worked
numeric contrast, and VERIFIED MECHANICALLY on real development data (not
just by prereg-text argument): cross-tabulating this family's elevated
flag against family 016's own primary-config elevated-VIX flag showed
substantial disagreement on every asset (flag agreement 78.4%-95.9%
across the 5 assets, well below 100%), confirming the spread logic is
genuinely implemented, not an accidental collapse onto either
predecessor's signal. Pre-grid non-degeneracy check confirmed
elevated/compressed regime frequencies non-trivial on all 5 assets.
Verified `PRIMARY_CONFIG` membership in `GRID` programmatically at module
import time, per family 021's lesson. VIX's 1990+ data start handled with
the same warm-up convention and cross-asset-proxy acknowledgment as
family 016. Sec 4.3 not run (only run when sec 4.1 passes). Holdout not
opened (not a finalist).

4 ideas remain (#26-29), below the sec 8 step-2 threshold of 5 -- one more
idea is added now to restore the threshold before the next iteration
takes #26, following family 023/024's precedent (adding exactly 1
replacement idea).

| # | Idea | Category | Key source |
|---|---|---|---|
| 30 | Short-term reversal / losing-streak contrarian sizing: increase buy size after a run of `N` or more consecutive DOWN daily closes (a short-term oversold/mean-reversion signal), reduce buy size after a run of consecutive UP closes, normal size otherwise. Price-only signal (daily Close, consecutive-close-direction counting), no external data dependency, testable identically on all 5 core assets. Explicitly distinct from family 001 (a single long-horizon 10-month/200-day trend-following EXIT to cash, opposite sign and horizon), family 005 (sign of the trailing 12-month return, no streak-counting, opposite sign for the momentum leg), family 016 (VIX-based cross-market fear spike, not a price-level streak on the asset's own closes) and family 025 (implied-vs-realized vol spread, not a directional price-streak count at all) -- must state this distinction explicitly in prereg.md, same discipline prior families used. | Sizing / valuation | Jegadeesh, N. (1990), "Evidence of Predictable Behavior of Security Returns," *Journal of Finance* 45(3), 881-898; Lehmann, B.N. (1990), "Fads, Martingales, and Market Efficiency," *Quarterly Journal of Economics* 105(1), 1-28 (short-horizon return reversal literature) |

Idea #26 (Intraday/overnight return decomposition sizing) has been taken
from the queue and used for family `026-intraday-overnight`; see
`families/026-intraday-overnight/` (REJECTED). Assessed as a single-asset
family across all 5 core assets, category **Sizing / valuation**. First
family in this loop to use the intraday (Open-to-Close) / overnight
(Close-to-Open) return decomposition as a data dimension, documented
explicitly in prereg.md as new (no prior v3 family or sec 7.2 closed
family split a day's own return this way). Signal: `spread_t =` trailing
LAGGED cumulative overnight return minus trailing LAGGED cumulative
intraday return (both sums computed on the leg series shifted forward one
day before rolling, so day t's own O/C split never enters its own signal
-- a deliberately conservative no-lookahead design per this iteration's
explicit caution, adapting Lou, Polk & Skouras (2019)'s finding that the
overnight leg shows continuation while the intraday leg is noisier and
reversal-prone), ranked in its own trailing percentile: elevated spread
(overnight dominating) -> buy more; compressed spread (intraday
dominating) -> buy less. Sec 4.1: primary config beats DCA on wealth AND
Sharpe on **0/5** core assets -- decisive fail (need >=3/5); SP500 beats
DCA on Sharpe alone by a hair via the banking/smoothing mechanic but loses
on wealth, and GOLD/SILVER/BTC/OIL lose on BOTH metrics outright, a
weaker result than most prior REJECTED sizing families. Grid: 0/36 (0.0%)
configs reach the combined majority bar, uniform failure across the
entire 36-point parameter space. CSCV PBO=0.0 (the lowest possible
reading -- a reliably weak grid, not a noisy one). DSR effectively zero
(negative raw pooled excess Sharpe, -0.04785/week). Hand-checked the O/C
decomposition arithmetic on 5 real SP500 days (1928-2007) before trusting
the grid: the exact multiplicative identity
`(1+overnight_t)*(1+intraday_t)-1` reproduced the actual Close-to-Close
return to floating-point precision on all 5 days. Pre-grid non-degeneracy
check confirmed elevated/compressed regime frequencies non-trivial and
close to their nominal ~10% decile rate on all 5 assets. Verified
`PRIMARY_CONFIG` membership in `GRID` programmatically at module import
time, per family 021's lesson. Flagged explicitly in prereg.md before
backtesting that LPS's mechanism (equity-market trading-hours structure)
has no clean analogue for BTC (24/7 trading) and only a partial one for
the commodity futures, weakening the economic story for 4/5 core assets
even before results came in. Sec 4.3 not run (only run when sec 4.1
passes). Holdout not opened (not a finalist).

4 ideas remain (#27-30), below the sec 8 step-2 threshold of 5 -- one more
idea is added now to restore the threshold before the next iteration
takes #27, following families 023/024/025's precedent (adding exactly 1
replacement idea).

| # | Idea | Category | Key source |
|---|---|---|---|
| 31 | Kelly-fraction-style trailing-Sharpe sizing: scale buy size up when an asset's own trailing mean-return-over-volatility ratio (a rolling realized Sharpe/Kelly-fraction proxy, `mean(daily log return) / variance(daily log return)` over a trailing window) is elevated in its own trailing percentile, scale down when it is depressed or negative -- a signal that combines BOTH the mean and the variance of trailing returns into a single ratio, mechanistically distinct from family 003 (variance alone, no mean/return component at all, direction-agnostic) and family 005 (the sign of the trailing return alone, no variance normalization) since neither predecessor's signal can be recovered from this one (or vice versa) without the missing moment. Price-only signal (daily Close), no external data dependency, testable identically on all 5 core assets. | Sizing / valuation | Kelly, J.L. (1956), "A New Interpretation of Information Rate," *Bell System Technical Journal*; MacLean, L.C., Thorp, E.O. and Ziemba, W.T., eds. (2011), *The Kelly Capital Growth Investment Criterion: Theory and Practice* |

Idea #27 (Yield-curve slope (2s10s) inversion regime filter) has been
taken from the queue and used for family `027-yield-curve-regime`; see
`families/027-yield-curve-regime/` (REJECTED). Assessed as a single-asset
family across all 5 core assets, category **Regime switch (macro /
credit / sentiment)**. Signal: T10Y2Y (FRED, already cached from v2.1's
Strategy D usage) with a persistence-confirmation filter and a
lag-motivated post-inversion banking-window extension (up to 2 years,
modeling the 12-18-month documented inversion-to-recession lag), banking
deposits during/after a confirmed inversion, deployed with a capped
catch-up lump when normal. Rigorously distinguished in prereg.md from
family 011 (credit-stress: a categorically different, market-priced
financial-conditions signal, not a Treasury-curve-shape signal) and, in
particular, from v2.1 Strategy D -- the closest prior family, since
T10Y2Y is literally one of Strategy D's 8 ensemble-vote signals (R2b-inv)
-- on both of sec 7.2's disjunctive grounds: mechanism (this family uses
the signal ALONE as a direct banking/timing decision, vs. Strategy D's
use of it as one of 8 votes choosing between two other pre-existing
strategies, SmartDCA vs. plain DCA) and signal construction (persistence
confirmation + lag-extension window, vs. Strategy D's shared 2-week
whipsaw filter with no lag-extension feature). Sec 4.1: primary config
(invert_threshold=0.0, persistence_days=5, banking_window_days=252,
stress_tilt_fraction=0.0) beats DCA on wealth AND Sharpe on **2/5** core
assets (need >=3/5) -- SP500 by a razor-thin margin, OIL genuinely; GOLD
loses both, SILVER loses wealth, BTC is IDENTICAL to DCA because its
short 2014-2019 dev window contains only one 3-day near-inversion that
never reaches the persistence threshold (an honest data-limitation
finding flagged before backtesting, not a bug). Grid: 11/24 (45.8%)
configs reach the majority bar (need >=16/24) -- a genuinely MIXED
result, unlike families 025/026's uniform failures: the grid's strongest
corner (tighter -0.10 threshold, NO lag extension) reaches 4/5 assets,
but the primary config's honest, literature-faithful parameter choices
land in a weaker region, which sec 4.4's diagnostic-only rule correctly
prevents the loop from chasing after the fact. CSCV PBO=0.057 (low, a
genuinely differentiated grid). DSR effectively zero despite a small
POSITIVE raw pooled excess Sharpe (+0.0592/yr annualized, unlike
families 025/026's negative results) -- far below the SR0=0.1466
threshold this loop's 821-trial/71-cluster count now demands. Pre-grid
known-episode check confirmed the raw T10Y2Y signal correctly registers
the 1989/2000/2006-07 inversions before any backtest was trusted.
Verified PRIMARY_CONFIG membership in GRID both programmatically and via
an explicit module-import-time assertion. Sec 4.3 not run (only run when
sec 4.1 passes). Holdout not opened (not a finalist).

4 ideas remain (#28-31), below the sec 8 step-2 threshold of 5 -- one more
idea is added now to restore the threshold before the next iteration
takes #28, following families 023/024/025/026's precedent (adding exactly
1 replacement idea).

| # | Idea | Category | Key source |
|---|---|---|---|
| 32 | M2 money-supply growth regime: bank deposits when trailing year-over-year M2 money-supply growth (FRED series `M2SL`) is depressed/contracting in its own trailing percentile (tight-liquidity conditions), deploy normally or with a capped catch-up lump when M2 growth is elevated (loose-liquidity conditions) -- a monetarist "don't fight the Fed / don't fight the flow of liquidity" mechanism (excess money-supply growth has historically flowed disproportionately into financial and real asset prices, e.g. the 2020-22 M2 surge and subsequent risk-asset rally, followed by 2022's sharp M2 growth deceleration alongside a broad risk-asset drawdown). Genuinely distinct signal source from every prior macro-regime family in this loop (011's credit spread/NFCI, 015's DXY, 019's OECD CLI, 027's T10Y2Y) -- a money-supply AGGREGATE growth rate, not a price, spread, or composite index -- though the eventual prereg.md must argue this carefully against v2.1 Strategy D's rate-level signals (R1: Fed funds target; R2a: DGS2 vs. its own trailing mean) since "loose monetary policy" is part of the economic story for both, even though M2 growth and the policy rate level are not the same thing and have diverged historically (e.g. 2008-09's near-zero rates arrived well after M2 growth had already troughed). | Regime switch (macro / credit / sentiment) | Friedman, M. and Schwartz, A.J. (1963), *A Monetary History of the United States*; more recent practitioner literature on M2 growth and asset-price inflation (e.g. Fed/BIS working papers on the 2020-22 liquidity surge) |

Idea #28 (50/200-day moving-average crossover "golden cross"/"death cross"
regime tilt) has been taken from the queue and used for family
`028-ma-crossover-regime`; see `families/028-ma-crossover-regime/`
(**NEAR-MISS**). Assessed as a single-asset family across all 5 core
assets, category **Trend / time-series momentum exit**. Signal: SMA_50 vs.
SMA_200 (or an alternate pair from the 3-pair grid), with a
persistence-confirmation filter (whipsaw reduction), tilting buy size
between `bull_mult`/`bear_mult` (never a binary exit, never a sell) with
the shortfall/surplus banked as cash and cash-capped, the same reserve
mechanic family 005's TSMOM sizing uses. Rigorously distinguished in
prereg.md from family 001 (single MA vs. price level, binary in/out) and
family 005 (sign of trailing total return, no moving average at all) and
from v1's closed-list Signal B (price-vs-single-MA distance percentile) --
this family compares two moving averages of price to each other, a
construction none of those three share. Pre-grid known-episode check
confirmed the raw 50/200 crossover registers SP500's well-documented
2003/2009/2016 golden crosses (2020's crossing falls in the sealed
holdout period and was correctly excluded from the dev-only check, see
`state/bugfix_log.md`). Sec 4.1: primary config (`fast_days=50,
slow_days=200, persistence_days=5, bull_mult=1.5, bear_mult=0.5`) beats
DCA on wealth AND Sharpe on **3/5** core assets (SP500, GOLD, BTC) at
both fees -- PASS (SP500's win is razor-thin on both metrics over its
92-year dev history; SILVER and OIL both lose narrowly on Sharpe only,
winning wealth). Grid: 28/36 (77.8%) configs reach the combined majority
bar (need >=24/36) -- PASS, the best sec 4.4 grid result of any family in
this loop so far. CSCV PBO=0.171 (moderate). DSR effectively zero (raw
pooled excess Sharpe is slightly NEGATIVE, -0.038/yr annualized, despite
the 3/5-asset sec 4.1 pass -- driven by SILVER/OIL's Sharpe losses
pulling the pooled series down) -- far below the SR0=0.146 threshold this
loop's 857-trial/72-cluster count now demands: DSR FAIL. Sec 4.3 (run in
full since sec 4.1 passed, n_sims=60 time-budget): rolling windows PASS
(67.6% wealth / 67.8% Sharpe pooled across 9 asset/window combinations,
>60% required) but block bootstrap and placebo both FAIL -- raw-path
bootstrap only 46.7%/45.0% (need majority), detrended 73.3%/51.7%
(borderline), and the placebo circular-shift result lands at only the
76.7th wealth / 41.7th Sharpe percentile (need >=95th) -- the specific
temporal alignment of the crossover signal is not doing enough work
beyond its raw regime frequency. **Verdict: NEAR-MISS** (passes sec 4.1
and sec 4.4, fails sec 4.2 DSR and sec 4.3 bootstrap/placebo). Verified
`PRIMARY_CONFIG` membership in `GRID` both programmatically and via an
explicit module-import-time assertion in the strategy module itself.
Holdout not opened (not a finalist).

4 ideas remain (#29-32), below the sec 8 step-2 threshold of 5 -- one more
idea is added now to restore the threshold before the next iteration
takes #29, following families 023/024/025/026/027's precedent (adding
exactly 1 replacement idea).

| # | Idea | Category | Key source |
|---|---|---|---|
| 33 | Post-earnings-announcement-drift-style volume-confirmed breakout sizing: increase buy size when price closes above its own trailing `N`-day high AND that day's volume exceeds its own trailing volume average by a threshold multiple (a volume-confirmed breakout, distinct from family 020's pure price-level 52-week-high tilt, which uses no volume condition at all), scale down/normal otherwise. A genuinely different signal class from every prior trend/momentum family in this loop because it requires BOTH a price condition and an independent volume-surge condition to jointly hold before tilting -- neither family 001 (single MA vs. price), 005 (sign of trailing return), 020 (52-week-high percentile, no volume) nor the new family 028 (dual-MA crossover) reference trading volume at all. Price+volume signal (daily Close/Volume, both already present in the existing yfinance OHLCV fetch), no new external data dependency, testable identically on all 5 core assets (BTC/gold/silver/oil futures/SP500 all carry a Volume field in the existing cached data). | Trend / time-series momentum exit | Karpoff, J.M. (1987), "The Relation Between Price Changes and Trading Volume: A Survey," *Journal of Financial and Quantitative Economics* 22(1), 109-126; Lee, C.M.C. and Swaminathan, B. (2000), "Price Momentum and Trading Volume," *Journal of Finance* 55(5), 2017-2069 |

When fewer than 5 ideas remain, the next iteration researches more and adds
them here, each with a source, mechanism and category (plan sec 8 step 2).

Idea #30 (short-term reversal / losing-streak contrarian sizing) has been
taken from the queue and used for family `030-losing-streak-reversal`; see
`families/030-losing-streak-reversal/`. Assessed as a single-asset family
across all 5 core assets, category **Sizing / valuation**. Signal: a
DISCRETE, magnitude-blind count of consecutive same-direction daily closes
(a streak LENGTH), not a smoothed gain/loss ratio -- rigorously
distinguished in prereg.md from family 017 (RSI2's continuous, bounded,
magnitude-weighted oscillator, plus family 030's added decay/duration
state-machine element that RSI2 has no analogue for), family 023
(realized skewness, a magnitude-weighted, order-independent statistical
moment) and family 003 (realized variance, direction-agnostic dispersion).
3 ideas (#31-33) remained after taking #30, below the sec 8 step-2
threshold of 5 -- 2 replacement ideas are added now to restore the
threshold before the next iteration takes #31.

| # | Idea | Category | Key source |
|---|---|---|---|
| 34 | 52-week-low contrarian value tilt: increase buy size the closer an asset's current close sits to its own trailing 52-week LOW (a long-horizon value/contrarian anchor), reduce or hold normal size otherwise. The mirror-image reference point of family 020's 52-week-HIGH tilt, but an opposite economic bet: family 020 is trend-following (buy more near a fresh high, betting the trend continues); this family is long-horizon mean-reversion (buy more near a trailing-year low, betting the price has overshot to the downside and will partially recover over a multi-month-to-year horizon, not the few-day horizon family 030's streak signal targets). Must state this distinction explicitly in prereg.md, plus the distinction from family 014 (drawdown-from-ALL-TIME-high reserve deployment, a different and typically much longer reference window than a rolling 52-week low, and family 014's reference point never resets to a new low the way a rolling 52-week low continuously does). Price-only signal (daily Close, trailing rolling minimum), no external data dependency, testable identically on all 5 core assets. | Sizing / valuation | De Bondt, W.F.M. and Thaler, R. (1985), "Does the Stock Market Overreact?," *Journal of Finance* 40(3), 793-808 (long-horizon overreaction/reversal); George, T.J. and Hwang, C.-Y. (2004), "The 52-Week High and Momentum Investing," *Journal of Finance* 59(5), 2145-2176 (documents the 52-week-high anchor's role in trend continuation, the reference point this family mirrors from the low side) |
| 35 | Drawdown-DURATION (time-underwater) sizing: increase buy size the longer an asset has gone, in trading days, since its last all-time (or trailing-N-year) high close -- a signal built on the LENGTH of time spent below a prior peak, not the MAGNITUDE of the shortfall from that peak. Explicitly distinct from family 014 (drawdown-from-high reserve deployment, whose signal is the percentage-magnitude shortfall from the reference high, reacting identically to a deep-but-brief drawdown and a shallow-but-long one) since a duration-only signal and a magnitude-only signal are mechanically independent statistics of the same underlying price path (a V-shaped crash-and-instant-recovery has near-zero duration despite large magnitude; a slow multi-year grind sideways below a peak has large duration despite modest magnitude) -- neither can be recovered from the other. Price-only signal (daily Close, running peak and days-since-peak counter), no external data dependency, testable identically on all 5 core assets. | Sizing / valuation | Practitioner "time-to-recovery" / underwater-duration literature underlying the Calmar and Sterling ratio families (which use max-drawdown MAGNITUDE, not duration); Ibbotson Associates and related work on the psychological and portfolio-rebalancing effects of extended underwater periods distinct from drawdown depth alone |

Idea #31 (Kelly-fraction-style trailing-Sharpe sizing) has been taken from
the queue and used for family `031-kelly-sharpe-sizing`; see
`families/031-kelly-sharpe-sizing/` (NEAR-MISS). Assessed as a
single-asset family across all 5 core assets, category **Sizing /
valuation** (a judgment call over "Volatility targeting," justified in
prereg.md: the return/edge numerator drives the reading as much as the
risk denominator, unlike family 003's pure risk-targeting design).
Signal: a trailing Sharpe ratio (mean/vol of daily log returns), turned
into a continuous (not discrete-threshold) buy multiplier via a causal
percentile rank -- rigorously distinguished in prereg.md, with a concrete
real-data numeric contrast (BTC 2018-01-22 vs SP500 1993-12-20, Sharpe
~1.068 on both despite ~17x different return/vol magnitudes), from family
003 (volatility alone), family 005 (sign of return alone), family 025 (a
volatility-vs-volatility spread) and family 020 (price-level proximity).
Passed sec 4.1 (4/5 assets) and sec 4.4 (83.3% of grid, this loop's best
sec 4.4 result so far) but failed sec 4.2 (DSR ~2e-22) and sec 4.3
(rolling windows 56-58%, bootstrap fails both legs, placebo lands at only
the 33rd Sharpe percentile). 4 ideas (#32-35) remained after taking #31,
below the sec 8 step-2 threshold of 5 -- 1 replacement idea is added now
to restore the threshold before the next iteration takes #32.

| # | Idea | Category | Key source |
|---|---|---|---|
| 36 | Return-autocorrelation regime sizing: increase buy size when an asset's own trailing daily-return autocorrelation (lag-1, over a rolling window) is positive and elevated in its own trailing percentile (a "trending/persistent" regime, where price changes are serially reinforcing), decrease buy size when that autocorrelation is negative (a "choppy/mean-reverting" regime, where price changes tend to reverse day-to-day). A genuinely new statistic for this loop: unlike family 005's sign-of-trailing-RETURN, family 003's realized VARIANCE, family 030's discrete consecutive-day STREAK COUNT, or family 031's return-to-vol SHARPE RATIO, the lag-1 autocorrelation coefficient measures neither the level nor the dispersion of returns but their **serial dependence structure** -- two assets with identical trailing mean and variance of returns can have wildly different autocorrelation (e.g. a smoothly trending path vs. a choppy zig-zag path of the same net return and volatility), and none of families 003/005/020/030/031's signals can distinguish those two cases at all. Price-only signal (daily Close, trailing lag-1 sample autocorrelation of log returns), no external data dependency, testable identically on all 5 core assets. | Trend / time-series momentum exit | Lo, A.W. and MacKinlay, A.C. (1988), "Stock Market Prices Do Not Follow Random Walks: Evidence from a Simple Specification Test," *Review of Financial Studies* 1(1), 41-66 (documents significant positive short-horizon return autocorrelation, i.e. rejection of the random walk, in broad equity indices) |

When fewer than 5 ideas remain, the next iteration researches more and adds
them here, each with a source, mechanism and category (plan sec 8 step 2).

Idea #32 (M2 money-supply growth regime) has been taken from the queue and
used for family `032-m2-growth-regime`; see
`families/032-m2-growth-regime/` (REJECTED). Assessed as a single-asset
family across all 5 core assets, category **Regime switch (macro)**.
Signal: FRED M2SL's trailing 12-month YoY growth rate, trend-normalized
via its own trailing z-score, banking deposits when growth decelerates
below its own trend and deploying with a capped catch-up lump once it
reaccelerates -- rigorously distinguished in prereg.md (a fourfold
distinction, since this loop now has 4 macro-regime families) from v2.1
Strategy D (policy rates/yield-curve level), family 011 (market-priced
credit spreads/NFCI) and family 019 (OECD real-activity composite): M2SL
is a monetary-aggregate quantity-of-money signal, structurally and
historically independent of all three (e.g. 2020-21's M2 acceleration
coincided with the OECD CLI's sharp COVID-era collapse, the clearest
evidence the two are not proxies). Failed sec 4.1 decisively (only 1/5
core assets beat DCA on both wealth AND Sharpe at either fee level) and
sec 4.4 (0/24 grid configs cleared the majority bar) -- sec 4.2/4.3 were
not run in full per the plan's own "only if sec 4.1 passes" time-budget
rule. Implementation checks and both pre-grid sanity checks (non-
degeneracy; the 2008-09 QE-era acceleration correctly reads as
accelerating) passed. 4 ideas (#33-36) remained after taking #32, below
the sec 8 step-2 threshold of 5 -- 1 replacement idea is added now to
restore the threshold before the next iteration takes #33.

| # | Idea | Category | Key source |
|---|---|---|---|
| 37 | Overnight/intraday return-split sizing: increase buy size when an asset's own trailing overnight (prior close -> today's open) return component has been running positive and elevated relative to its trailing intraday (open -> close) return component (an "overnight-driven" regime), decrease or hold normal otherwise. A genuinely new statistic for this loop: unlike every prior family's signal (built from close-to-close returns, price levels, or volume), this splits each trading day's total return into its close-to-open and open-to-close halves and compares their trailing relative contribution -- two assets with identical trailing close-to-close returns can have wildly different overnight/intraday splits (e.g. SP500's long-run excess return has been documented as concentrated in the overnight session, with the intraday session roughly flat or negative on average), a decomposition none of families 001/003/005/020/030/031/036's signals can see at all, since each collapses to a single daily close-to-close number. Price-only signal (daily Open and Close, both already in the existing cached OHLCV data), no external data dependency, testable identically on all 5 core assets (note: BTC trades continuously with no single "open"; this family's prereg.md must state explicitly how the overnight/intraday split is defined for a 24-hour asset, e.g. a fixed daily UTC cutoff as its own "close"/"open" proxy, or must narrow sec 4.1's scope if no principled definition exists). | Seasonality / execution timing | Cliff, M., Cooper, M. and Gulen, H. (2008), "Return Differences between Trading and Non-Trading Hours: Like Night and Day," working paper; Lou, D., Polk, C. and Skouras, S. (2019), "A Tug of War: Overnight versus Intraday Expected Returns," *Journal of Financial Economics* 134(1), 192-213 (documents the persistent overnight-return/intraday-return decomposition and its differing risk/return character) |

When fewer than 5 ideas remain, the next iteration researches more and adds
them here, each with a source, mechanism and category (plan sec 8 step 2).

Idea #33 (volume-confirmed breakout sizing) has been taken from the queue
and used for family `033-volume-breakout`; see
`families/033-volume-breakout/` (REJECTED). Assessed as a single-asset
family across all 5 core assets, category **Trend / time-series momentum
exit**. Signal: a joint AND of (a) a new trailing-N-day price high
(20-60 trading days, materially shorter than family 020's ~1-year 52-week-
high window) and (b) that day's own volume exceeding a multiple of its own
trailing average volume -- the first family in this loop to use trading
volume as a trend-confirmation input, rigorously distinguished in
prereg.md from families 001/005/020/028 (none of which reference volume
at all). Reused family 021's existing Volume-data feasibility finding
rather than re-deriving it; no new Volume quirk found. Failed sec 4.1 as
decisively as a strategy can fail: the primary configuration's
`normal_buy_mult=1.0` meant the engine's own cash cap starved the rare
joint trigger of any funding, making the primary's realized trading
literally bit-for-bit identical to plain DCA on all 5 assets at both fee
levels (0/5, DSR exactly 0) -- confirmed a genuine cash-cap mechanics
effect, not a code bug, via the implementation checks and by contrast with
the grid's `normal_buy_mult=0.75` arm (which behaves differently, though
still fails sec 4.1/4.4). Grid: 0/36 configs cleared the majority bar --
sec 4.4 FAIL; the grid's win pattern tracked `normal_buy_mult` alone,
with `window`/`volume_surge_multiple`/`breakout_buy_mult` showing no
visible effect, suggesting an interest-banking/timing effect (echoing
family 021) rather than the volume-price signal itself is whatever weak
differentiator exists. Design lesson recorded for future queue ideas: a
primary configuration's "otherwise" multiplier for a rare/joint signal
should be set below 1.0, not exactly 1.0, so a cash reserve actually
exists to fund the signal. 4 ideas (#34-37) remained after taking #33,
below the sec 8 step-2 threshold of 5 -- 1 replacement idea is added now
to restore the threshold before the next iteration takes #34.

| # | Idea | Category | Key source |
|---|---|---|---|
Idea #38 (range-based Parkinson realized-volatility sizing) has been taken
from the queue and used for family `035-parkinson-vol-sizing`; see
`families/035-parkinson-vol-sizing/` (NEAR-MISS -- passes sec 4.1 narrowly
at exactly 3/5 core assets at both fee levels; fails sec 4.2 decisively
(DSR effectively zero, `dsr~3.2e-25`, driven by a slightly negative raw
pooled excess-return Sharpe of -0.0048), and fails sec 4.3's rolling-window
leg (pooled 51.7%/51.0% wealth/Sharpe, need >60%; SP500's own 3y/5y windows
and BTC's 2y window are all well under 50%) and its placebo leg (real
result at the 78th/58th percentile of 60 circular-shifted runs, need
>=95th) -- only the grid diagnostic (sec 4.4, 100% of the 36-config grid
clears the majority bar) and the bootstrap's detrended-wealth leg (65%)
pass. Rigorously distinguished in prereg.md from family 003
(vol-managed-sizing, also Volatility targeting): family 003's realized-vol
estimator is close-to-close sample variance (Close-only input); this
family's is the Parkinson (1980) high-low-range estimator (High/Low-only
input, Close never used in the vol calculation) -- a different raw input,
not a re-parameterization, backed by a concrete numeric example (SILVER
2011-09-26: a 14.67% log high-low range against an essentially flat -0.41%
close-to-close move gives a Parkinson single-day annualized-vol
contribution of 139.8% vs. a close-to-close contribution of only 6.6%, a
~21x divergence). Holdout not opened.

| # | Idea | Category | Key source |
|---|---|---|---|

Idea #34 (52-week-low proximity contrarian tilt) has been taken from the
queue and used for family `034-52wk-low-tilt`; see
`families/034-52wk-low-tilt/` (NEAR-MISS -- passes sec 4.1 narrowly at
exactly 3/5 core assets, the identical count and near-identical margins to
family 020's own near-miss on the opposite-signed 52-week-high tilt; fails
sec 4.2's DSR (effectively zero, negative raw pooled excess Sharpe), sec
4.4's grid diagnostic (50%, need >=2/3, CSCV PBO=0.814 -- the highest of any
family tested so far), and sec 4.3's bootstrap and placebo legs (placebo
decisively so: the real result lands at the 3rd/2nd percentile of 60
circular-shifted runs, need >=95th). Rigorously distinguished in prereg.md
from family 020 (opposite reference extremum -- a running 52-week MINIMUM,
not MAXIMUM -- and opposite economic story: contrarian/overreaction-reversal
vs. momentum/continuation, confirmed empirically via a 72.8%-of-days signal-
disagreement check and a -0.32 correlation between the two proximity
ratios) and from family 014 (all-time-high drawdown ladder vs. this
family's 52-week-low proximity ladder -- different extremum, different
window length, different functional-form parameters). Holdout not opened.
4 ideas (#35-38) remained after taking #34, below the sec 8 step-2
threshold of 5 -- 1 replacement idea is added now to restore the threshold
before the next iteration takes #35.

| # | Idea | Category | Key source |
|---|---|---|---|
| 39 | Consumer-sentiment contrarian regime: bank deposits when the University of Michigan Consumer Sentiment Index (FRED `UMCSENT`, monthly, ALFRED-revisable, confirmed reachable via the same fredgraph.csv path families 011/019/027/032 already use) reads elevated/euphoric in its own trailing percentile (a classic "excess optimism precedes weak forward returns" contrarian-sentiment signal), deploy normally or with a capped catch-up lump when sentiment is depressed/pessimistic. A genuinely different signal source from every prior sentiment/regime family in this loop: family 016's VIX is a market-*priced*, option-implied fear gauge (a forward-looking risk-neutral measure), while UMCSENT is a *survey-based* measure of household sentiment about the real economy and personal finances, constructed from consumer interviews with no direct link to option prices or realized market volatility at all -- the two can and do diverge (e.g. consumer sentiment can stay depressed on labor-market/inflation concerns even while the VIX signals market calm, and vice versa during a sharp-but-brief market selloff that doesn't yet show up in a monthly survey). Also distinct from family 032 (M2 money-supply growth, a quantity-of-money aggregate with no sentiment or survey component) and from v2.1 Strategy D / family 027 (policy-rate and yield-curve signals, not survey sentiment). Must state this distinction explicitly in prereg.md, same discipline prior macro/sentiment families used. Asset-agnostic macro sentiment signal, applied per-asset like 006/007/011/019/027/032. | Regime switch (macro / credit / sentiment) | Lemmon, M. and Portniaguina, E. (2006), "Consumer Confidence and Asset Prices: Some Empirical Evidence," *Review of Financial Studies* 19(4), 1499-1529; Baker, M. and Wurgler, J. (2006), "Investor Sentiment and the Cross-Section of Stock Returns," *Journal of Finance* 61(4), 1645-1680 |

Idea #36 (return-autocorrelation regime sizing) has been taken from the
queue and used for family `036-autocorr-regime-sizing`; see
`families/036-autocorr-regime-sizing/` (REJECTED -- primary config beats
DCA on wealth AND Sharpe on only 2/5 core assets (SILVER, OIL) at both fee
levels, short of the required 3/5; SP500 and GOLD lose on both metrics,
BTC is mixed. Since sec 4.1 itself fails, this is a straight REJECTED, not
a near-miss. Sec 4.4's grid diagnostic also fails decisively (only 6/36,
16.7%, clear the majority bar; need >=2/3), CSCV PBO=0.414. DSR effectively
zero (raw pooled excess-return Sharpe -0.00884/week); sec 4.3 not run in
full since sec 4.1 failed. Rigorously distinguished in prereg.md from
family 003 (realized variance -- dispersion), family 005 (sign of trailing
return -- level), family 030 (discrete streak count -- magnitude-blind)
and family 031 (return-to-vol Sharpe ratio) via a constructed toy 8-day
example: two return paths that are permutations of the identical multiset
of four +1% and four -1% daily returns give IDENTICAL mean, sample
variance, family-005 sign, family-031 Sharpe and family-030 max-streak
across both paths, yet lag-1 autocorrelation of -0.750 (choppy) vs. +0.167
(trending/paired-run) -- none of the four prior families' signals can
distinguish the two paths, while this family's signal does. Holdout not
opened.) 4 ideas (#35, #37, #39, #40) remained after taking #36, below the
sec 8 step-2 threshold of 5 -- 1 replacement idea is added now to restore
the threshold before the next iteration takes #35.

| # | Idea | Category | Key source |
|---|---|---|---|
| 41 | Rolling Sortino-ratio sizing: scale buy size up when an asset's own trailing mean daily log return divided by its trailing DOWNSIDE deviation (the semi-deviation computed only from negative daily returns, zero contribution from positive days) is elevated in its own trailing percentile, scale down when depressed -- an asymmetric risk-adjusted-return signal, mechanistically distinct from family 031 (Kelly-Sharpe sizing, `mean/std` using the FULL, symmetric variance of both up and down days) and family 003 (realized variance alone, also symmetric, no mean/return component): a Sortino-style downside deviation can differ substantially from a Sharpe-style full standard deviation even holding the trailing mean fixed, whenever the trailing window's upside and downside volatility are not equal (e.g. a period with several large up-day outliers but small, consistent down-day moves has high full variance but low downside deviation, giving a much higher Sortino ratio than Sharpe ratio for the identical return series) -- must state and verify this distinction explicitly and concretely in prereg.md, same discipline family 031 used to distinguish itself from families 003/005. Price-only signal (daily Close), no external data dependency, testable identically on all 5 core assets. | Sizing / valuation | Sortino, F.A. and van der Meer, R. (1991), "Downside Risk," *Journal of Portfolio Management* 17(4), 27-31; Sortino, F.A. and Price, L.N. (1994), "Performance Measurement in a Downside Risk Framework," *Journal of Investing* 3(3), 59-64 |

Idea #35 (drawdown-duration / time-underwater sizing) has been taken from
the queue and used for family `037-drawdown-duration`; see
`families/037-drawdown-duration/` (REJECTED -- primary config
(`ath_lookback_years=None, ladder=moderate, near_high_mult=1.0,
max_lump_cap=3.0`) is numerically IDENTICAL to plain DCA on all 5 core
assets at both fee levels, 0/5, the same reserve-nullification mechanism
family 014 and family 033 already documented: with `near_high_mult=1.0`
no cash reserve is ever banked while the days-since-peak counter is
short, so the engine's own no-leverage cash cap clips every
above-1x-multiplier request straight back down to that week's own $500
deposit. Sec 4.1 FAIL decisively. Grid: 0/32 (0.0%) configs reach the
combined majority bar -- splits cleanly by `near_high_mult` alone (all 16
`near_high_mult=1.0` configs are exactly DCA-equivalent; all 16
`near_high_mult=0.75` configs, which do fund a real reserve, reach at
most 2/5 on the combined criterion). CSCV PBO=0.0 (uninformative given
sec 4.1's outright failure). DSR exactly 0. Sec 4.3 not run (sec 4.1
already decisive fail). Rigorously distinguished in prereg.md from family
014 (percentage-magnitude drawdown-from-high, this family's closest
prior) via a real, programmatically-verified SP500 dev-period divergence
example: the Sept 2018-Apr 2019 correction (deep, 19.78% max drawdown,
resolved in 146 trading days) versus the May 2015-Jul 2016 sideways grind
(shallower, 14.16% max drawdown, took 286 trading days to a new high) --
the magnitude ranking and the duration ranking of the two real episodes
disagree, exactly as the general mechanically-independent-statistics
argument predicts. Design lesson reinforced for the queue (now confirmed
independently across families 014/033/037): a ladder-based sizing
family's PRIMARY configuration itself, not only some grid arm, must set
its "otherwise"/near-high multiplier below 1.0, or the engine's correct
no-leverage cash cap silently nullifies the entire mechanism. Holdout not
opened.) 4 ideas (#37, #39, #40, #41) remained after taking #35, below
the sec 8 step-2 threshold of 5 -- 1 replacement idea is added now to
restore the threshold before the next iteration takes #37.

| # | Idea | Category | Key source |
|---|---|---|---|
| 42 | VIX futures term-structure carry (contango/backwardation) regime: bank deposits (or hold normal size) when the VIX term structure is inverted into backwardation (near-term implied vol, `^VIX`, trading ABOVE 3-month implied vol, `^VIX3M` -- a "fear spike" signal historically associated with continued near-term stress), deploy normally or with a capped catch-up lump when the curve is in its normal contango state (`VIX3M/VIX` ratio elevated in its own trailing percentile -- the typical calm-market state in which the volatility risk premium has historically been most reliably harvested by staying invested). A genuinely different signal from every prior VIX-based family in this loop: family 016's `vix_contrarian` uses the LEVEL of spot VIX alone (a single point on the curve, no term-structure/slope component at all), while this family uses the SLOPE/ratio between two points on the VIX futures-implied curve (a term-structure carry signal, the same economic object as bond-market term-structure carry, applied to the volatility market) -- an asset can have an elevated spot VIX level yet still sit in mild contango, or a middling spot VIX level yet sit in outright backwardation, so the two statistics are not interchangeable. Also distinct from family 025's `vrp_sizing` (realized-vs-implied volatility SPREAD at a single tenor, a cross-measure gap, not a curve-slope-between-two-implied-tenors signal at all). Applied as a shared macro/regime signal identically across all 5 core assets' own per-asset decisions, the same convention families 006/007/011/019/027/032 already use for a single shared external signal. Data: `^VIX` and `^VIX3M` daily closes, both free and already reachable via the same data path family 016/025 use (CBOE-sourced, no publication lag since both are same-day closing index levels, not survey/reported economic data). | Carry / term structure | Simon, D.P. and Campasano, J. (2014), "The VIX Futures Basis: Evidence and Trading Strategies," *Journal of Derivatives* 21(3); Cheng, I.-H. (2019), "The VIX Premium," *Review of Financial Studies* 32(1), 180-227 (documents the VIX futures term-structure's historical tendency toward contango and the return premium associated with it, and its inversion into backwardation during market stress) |

**Idea #37 (overnight/intraday return-split sizing) was reviewed against
family 026 and SKIPPED, not tested.** Full side-by-side reasoning in
`families/038-consumer-sentiment-contrarian/prereg.md`'s "Scoping decision"
section. Summary: idea #37 as worded ("increase buy size when an asset's
own trailing overnight return component has been running positive and
elevated RELATIVE TO its trailing intraday return component ... decrease
or hold normal otherwise") is mechanically the same construction family
026 already tested and rejected (`families/026-intraday-overnight/`): the
identical Open/Close overnight-vs-intraday decomposition, the identical
relative comparison (a spread between the two legs, not a standalone level
of either leg), and the identical elevated-buy-more / otherwise-buy-less-
or-normal sizing shape. None of the potential distinctions the task brief
suggested as hypothetically available (a ratio instead of a spread, a
different aggregation window, a different asset scope, a different sign
convention) are actually present in how idea #37 is stated -- they were
offered as ways a distinction *could* be built, not features already in
#37's own wording, and building one in now (after already knowing family
026's exact construction and result) would be exactly the kind of
after-the-fact relabeling the loop's holdout/closed-family discipline
warns against, applied here by analogy to this loop's own family 026.
**Decision: idea #37 removed from the active queue without being tested.**
A genuinely distinct future overnight/intraday idea (e.g. a true ratio or
single-leg-level construction, explicitly not the relative-spread
construction) could still be proposed fresh in a later iteration under a
new idea number, but not as a re-labeling of #37 as currently worded.

Idea #39 (consumer-sentiment contrarian regime) was taken as this
iteration's substitute family (per the task brief's option (b)) and used
for family `038-consumer-sentiment-contrarian`; see
`families/038-consumer-sentiment-contrarian/`. 3 ideas (#40, #41, #42)
remained after taking #37 (skipped) and #39, below the sec 8 step-2
threshold of 5 -- 2 replacement ideas are added below to restore the
threshold before the next iteration.

Idea #40 (realized-kurtosis fat-tail sizing) has been taken from the queue
and used for family `039-realized-kurtosis-sizing`; see
`families/039-realized-kurtosis-sizing/` (REJECTED -- primary config beats
DCA on only 2/5 core assets, need >=3/5). 4 ideas (#41, #42, #43, #44)
remained after taking #40, below the sec 8 step-2 threshold of 5 -- 1
replacement idea (#45, Hurst-exponent regime sizing) is added below to
restore the threshold before the next iteration.

Idea #41 (rolling Sortino-ratio sizing) has been taken from the queue and
used for family `040-sortino-sizing`; see `families/040-sortino-sizing/`
(NEAR-MISS -- passes sec 4.1 4/5 core assets and sec 4.4 83.3% grid, but
fails sec 4.2 DSR and sec 4.3 rolling/bootstrap/placebo; an almost exact
numeric match to family 031's own near-miss result on every check). 4
ideas (#42, #43, #44, #45) remained after taking #41, below the sec 8
step-2 threshold of 5 -- 1 replacement idea (#46, cross-asset correlation
regime sizing) is added below to restore the threshold before the next
iteration.

| # | Idea | Category | Key source |
|---|---|---|---|
| 43 | Realized-volatility term-structure (short-vs-long trailing-window ratio) sizing: buy more when an asset's own SHORT trailing realized-volatility window (e.g. 10-20 trading days) is unusually LOW relative to its own LONGER trailing window (e.g. 100-252 days) -- a "calm now relative to its own recent-past normal" regime, buy less/hold normal when short-window vol is elevated relative to the long-window reference. Genuinely different from family 003 (a single absolute realized-variance level, no term-structure/ratio-of-two-windows component at all) and from family 035 (Parkinson high-low range estimator vs. this family's close-to-close estimator, and also a single-window level, not a short-vs-long ratio); the economic story here (a vol-term-structure/calm-relative-to-own-longer-run-normal signal) is closer to the equity vol-of-vol and VIX-term-structure carry literature (already tested via VIX itself in families 016/042) but applied to the asset's OWN realized volatility rather than to an options-market-implied series -- must state and verify this distinction concretely (e.g. a toy or real-data example where the short/long ratio and the single-window level disagree) in prereg.md. Price-only signal (daily Close), no external data dependency, testable identically on all 5 core assets. | Volatility targeting | Christensen, B.J. and Prabhala, N.R. (1998), "The relation between implied and realized volatility," *Journal of Financial Economics* 50(2), 125-150 (vol term-structure/realized-vol-ratio framing); Bollerslev, T. et al. (2018), "Risk Everywhere: Modeling and Managing Volatility," *Review of Financial Studies* 31(7), 2729-2773 |
| 44 | Amihud-illiquidity-regime rotation across the 5 core assets: instead of family 021's already-tested single-asset Amihud illiquidity SIZING rule (buy more of the SAME asset when its own trailing Amihud ratio is elevated), this family ROTATES the marginal weekly deposit toward whichever of the 5 core assets currently has the LOWEST trailing Amihud illiquidity ratio (i.e. currently the most liquid, cheapest to trade, per-dollar-of-volume least price-impactful asset among the 5) rather than sizing any one asset's own buys. A genuinely different mechanism category (cross-asset rotation, not single-asset sizing) built from the SAME underlying Amihud statistic family 021 already validated the computation of, applied here as a cross-sectional RANKING across assets rather than a within-asset trailing-percentile SIZING rule -- must state and verify this distinction (family 021 never compares one asset's Amihud ratio to another's; this family never sizes a single asset's OWN buy based on its own history alone). Requires each of the 5 core assets' daily Volume (already confirmed reachable and used by family 021/033). | Cross-asset rotation / relative strength | Amihud, Y. (2002), "Illiquidity and stock returns: cross-section and time-series effects," *Journal of Financial Markets* 5(1), 31-56 (the same source family 021 used, applied here to its cross-sectional ranking application rather than its single-asset time-series application) |
| 45 | Hurst-exponent (fractal trend-persistence) regime sizing: estimate an asset's own trailing Hurst exponent `H` via rescaled-range (R/S) analysis over a trailing window, a multi-scale measure of whether the return series behaves as trending/persistent (`H>0.5`), mean-reverting/anti-persistent (`H<0.5`), or a random walk (`H~=0.5`) across SEVERAL sub-window scales simultaneously, not just a single lag. Scale buy size up while `H` sits high in its own trailing percentile (a persistent/trending regime, consistent with staying invested through a trend), scale down/bank while `H` sits low (a mean-reverting/choppy regime). Must be rigorously distinguished from family 036 (lag-1 sample autocorrelation): rho_1 measures serial dependence between ADJACENT daily returns only, at a single lag, while the Hurst exponent is estimated from the scaling behavior of the range statistic across MULTIPLE aggregation scales simultaneously (a fractal/self-similarity measure) and is well known in the literature to pick up long-range dependence that a single-lag autocorrelation coefficient can miss entirely (e.g. a series with rho_1 near zero can still have H significantly above or below 0.5 if the dependence operates at longer lags/scales) -- must construct a concrete toy or real-data example showing the two disagree. Price-only signal (daily Close), no external data dependency, testable identically on all 5 core assets. | Trend / time-series momentum exit | Mandelbrot, B.B. and Van Ness, J.W. (1968), "Fractional Brownian Motions, Fractional Noises and Applications," *SIAM Review* 10(4), 422-437; Peters, E.E. (1994), *Fractal Market Analysis: Applying Chaos Theory to Investment and Economics*, Wiley (R/S Hurst-exponent regime framework applied to financial time series) |
Idea #46 (cross-asset average-correlation regime sizing) has been taken
from the queue and used for family `045-avg-correlation-regime`; see
`families/045-avg-correlation-regime/` (REJECTED -- primary config beats
DCA on wealth AND Sharpe on only 2/5 core assets, need >=3/5; sec 4.4 grid
only 11.1% clears the majority bar; DSR effectively zero (1.77e-42).
Verified in code, not just prose, the required distinction from family
043 (this family's signal is undefined from any one asset's own price
history alone -- perturbing GOLD's price changes SP500's own signal --
yet the decider's signature is the single-asset (t, cash) form, never
moving capital between assets, unlike 043's portfolio decider) and from
the external-data macro-regime families (purely price-derived, no
external series). See results.md for full detail.

| # | Idea | Category | Key source |
|---|---|---|---|
| 51 | Skewness-of-skewness (meta-skew) regime timing: track the trailing rolling STANDARD DEVIATION of family 023's own realized-skewness series (i.e. how much the skewness statistic itself has been fluctuating recently, a second-order "instability of asymmetry" measure), bank deposits when this meta-skew volatility sits high in its own trailing percentile (an unstable, hard-to-characterize distributional regime), deploy normally when low (a stable distributional regime). Genuinely different from family 023 (which sizes directly off the LEVEL of skewness) and from every realized-moment family in this loop (003/023/039), since this is a second-order statistic OF a moment, not the moment itself -- must construct a concrete example (real dev-period data) where the skewness level and its own trailing volatility diverge (e.g. a period with mild but wildly oscillating skewness vs. a period with strong but stable skewness) to prove the two statistics are not redundant. Price-only signal (daily Close), no external data dependency, testable identically on all 5 core assets. | Volatility targeting | Extension of the co-moment instability literature underlying Kraus & Litzenberger (1976) and the realized-moment estimation framework of Neuberger (2012) / Amaya et al. (2015), applied to second-order stability of the skewness estimator itself rather than its level |

When fewer than 5 ideas remain, the next iteration researches more and adds
them here, each with a source, mechanism and category (plan sec 8 step 2).

Idea #42 (VIX futures term-structure carry) was taken from the queue and
used for family `041-vix-term-structure-carry`; see
`families/041-vix-term-structure-carry/` (**NEAR-MISS**). Data-feasibility
check confirmed `^VIX3M` reachable via yfinance (`period="max"`, 5,081
rows, 2006-07-17+) -- a genuine term-structure counterpart to spot `^VIX`,
not a re-test of families 016/025; no substitute idea was needed.
Assessed as a single-asset family across all 5 core assets, category
**Carry / term structure** (first family in this loop to use it). Signal:
`ratio_t = VIX3M_t/VIX_t`, causal percentile-ranked, continuous multiplier
(not a discrete ladder, per the established cash-cap-nullification
lesson). Rigorously distinguished from family 016 (VIX level alone) and
family 025 (VIX-minus-realized-vol spread), verified mechanically on real
overlapping 2006-2019 data (backwardation flag vs. family 016's elevated
flag agree only 92.4% of days; raw ratio-vs-VIX-level correlation -0.667).
Sec 4.1: primary config beats DCA on wealth AND Sharpe on 4/5 core assets
(SP500, SILVER, BTC, OIL; GOLD loses both, razor-thin) at both fees --
PASS. Grid: 20/36 (55.6%) configs reach the majority bar -- sec 4.4 FAIL
(need >=24/36). DSR effectively zero (1.09e-20). Sec 4.3 (run in full):
rolling windows FAIL decisively (23.4%/23.8% pooled, need >60%, the
weakest rolling-window result of any near-miss family so far); bootstrap
FAILS (raw 48.3%/50.0%, detrended 53.3%/48.3%); placebo lands at the
50.0th/46.7th percentile (need >=95th) -- almost exactly the median of 60
shifts, one of the most decisive placebo failures in this loop. Holdout
not opened (near-miss, not a finalist).

4 ideas remain (#43-46), below the sec 8 step-2 threshold of 5 -- 1
replacement idea is added now to restore the threshold before the next
iteration takes #43.

| # | Idea | Category | Key source |
|---|---|---|---|
Idea #47 (VVIX vol-of-vol regime sizing) has been taken from the queue
and used for family `046-vvix-regime-sizing`; see
`families/046-vvix-regime-sizing/` (NEAR-MISS -- the strongest sec
4.1/sec 4.4 single-asset result of any family in this loop: 4/5 core
assets beat DCA at both fee levels, 100% of the grid clears the majority
bar. But DSR is effectively zero (3.30e-23) despite a positive raw
Sharpe, driven by extreme kurtosis (1444.6) -- the edge is concentrated
in a handful of extreme weeks. Rolling windows pooled across 3,439
windows fail decisively (24.9%/25.9%, need >60%). Block bootstrap and
placebo were not completed within the iteration's time budget, since the
verdict was already settled by the DSR and rolling-window failures --
logged as an explicit gap in results.md, not a fabricated result.
Distinction from families 016/025/041 verified concretely: raw
VVIX-vs-VIX correlation only +0.264, flag-agreement 56.1%/55.2%/45.8%.
See results.md for full detail.)

| # | Idea | Category | Key source |
|---|---|---|---|
| 52 | Turn-of-quarter deposit timing (quarterly, not monthly): bank a larger share of mid-quarter-month deposits, deploy a catch-up lump-sum tilt into the first and last few trading days surrounding each calendar-quarter boundary (Mar/Jun/Sep/Dec), on the hypothesis that institutional quarter-end/quarter-start portfolio rebalancing and window-dressing flows concentrate returns at quarter boundaries -- a genuinely different periodicity from family 006 (monthly turn-of-month) and family 018 (semiannual Nov-Apr/May-Oct): a quarterly cycle sits at a third, intermediate time scale between those two, and the motivating flow (institutional quarter-end rebalancing) is distinct from either family's own literature (monthly settlement-cycle flows for 006, seasonal vacation/risk-aversion flows for 018). Must state and verify this distinction (a materially different periodicity and a materially different institutional-flow story) concretely in prereg.md. Calendar-only signal, testable identically on all 5 core assets. | Seasonality / execution timing | Maxwell, W.F. (1998), "The January Effect in the Corporate Bond Market: A Systematic Examination," *Financial Management* 27(2), 18-30 (quarterly institutional flow/rebalancing literature); Musto, D.K. (1997), "Portfolio Disclosures and Year-End Price Shifts," *Journal of Finance* 52(4), 1563-1588 (window-dressing at reporting-period boundaries) |

When fewer than 5 ideas remain, the next iteration researches more and adds
them here, each with a source, mechanism and category (plan sec 8 step 2).

Idea #43 (realized-volatility term-structure, short-vs-long ratio sizing)
was taken from the queue and used for family `042-realvol-term-structure`;
see `families/042-realvol-term-structure/` (**REJECTED**). **Important
correction, documented in prereg.md/results.md**: this queue entry's own
characterization of family 003 as "a single absolute realized-variance
level, no ratio-of-two-windows component" does not match family 003's
actual implemented rule (`m_t=clip(sigma_ref/sigma_recent,min_mult,
max_mult)`), which already computes a short-vs-long realized-vol ratio --
stated plainly rather than silently asserted around. The family's real,
verified distinction from family 003 is instead in the functional form (a
further percentile-normalization of the ratio within its own trailing
history, vs. family 003's direct clip of the raw ratio against fixed
absolute bounds) plus a shorter short-window grid (10-20d vs. 003's
20-60d), confirmed via a concrete rank-reversal example on real GOLD dev
data (2001-12-11: ratio=1.974, this family's own percentile=0.500 ->
multiplier=1.0; 2003-12-23: ratio=1.534 (lower), percentile=1.000 ->
multiplier=2.0 -- a full rank reversal vs. the family-003-style raw-ratio
multiplier ordering). Assessed as a single-asset family across all 5 core
assets, category **Volatility targeting**. Sec 4.1: primary config beats
DCA on wealth AND Sharpe on only **2/5** core assets (GOLD, OIL) at both
fees -- FAIL (need >=3/5; SP500 and BTC lose both, SILVER wins wealth but
loses Sharpe). Grid: 5/36 (13.9%) configs reach the majority bar -- sec
4.4 FAIL, decisively (second-weakest grid result in this loop). CSCV
PBO=0.571, the highest (most overfitting-prone) of any family so far.
Raw pooled excess-return Sharpe is negative (-0.01101/week) -- DSR
effectively zero, sec 4.2 FAIL. Sec 4.3 not run (sec 4.1 already fails
decisively, per established precedent). Holdout not opened (rejected, not
a finalist).

4 ideas remain (#44-47), below the sec 8 step-2 threshold of 5 -- 1
replacement idea is added now to restore the threshold before the next
iteration takes #44.

| # | Idea | Category | Key source |
|---|---|---|---|
Idea #44 (Amihud-illiquidity cross-asset rotation) was taken from the queue
and used for family `043-liquidity-rotation`; see
`families/043-liquidity-rotation/` (**NEAR-MISS**). Assessed as a
5-asset portfolio family (sec 4.1 Portfolio line) vs. fixed-weight
5-asset DCA, category **Cross-asset rotation / relative strength**.
Reused family 021's exact per-asset Amihud-ratio/causal-percentile
computation unmodified, then ranked the 5 assets' own-history percentiles
AGAINST EACH OTHER each week-end (cross-sectional, not within-asset) and
rebalanced the pooled $2,500/week deposit toward the `top_n`
currently-most-liquid assets at equal weight. Rigorous distinction from
family 021 verified concretely (max pairwise cross-asset percentile
correlation only 0.241, per-asset selection frequency 7.6%-57.8% with
none frozen at 0%/100%, turnover 36.2%, and `top_n=5` collapses to an
always-invested equal-weight portfolio with no parameter setting
recovering 021's within-asset rule -- the two are not nested). Primary
config (`illiq_lookback=252, top_n=1, signal_smooth_days=10`) beats
fixed-weight DCA on wealth AND Sharpe at both fee levels -- **sec 4.1
PASS**, the second family in this loop (after 002) to clear it -- but
DSR=0.423 (sec 4.2 FAIL), block bootstrap and placebo both fail
decisively while rolling windows pass (sec 4.3 FAIL overall), and only
1/12 (8.3%) of the grid clears the bar (sec 4.4 FAIL, decisively). BTC's
57.8% selection frequency during its 2014-2019 bull run is flagged as the
likely dominant driver, the same BTC-concentration pattern family 002
showed. Holdout not opened (near-miss, not a finalist). This iteration
also extended `robustness.py`/`portfolio_robustness.py` with an optional
synthetic-Volume path for block bootstrap (the first Volume-dependent
signal to reach sec 4.3; logged in `state/bugfix_log.md`).

4 ideas remain (#45-48), below the sec 8 step-2 threshold of 5 -- 1
replacement idea is added now to restore the threshold before the next
iteration takes #45.

Idea #48 (CBOE SKEW Index tail-risk-pricing regime sizing) has been taken
from the queue and used for family `047-skew-index-sizing`; see
`families/047-skew-index-sizing/` (**REJECTED**). Single-asset family
across all 5 core assets, category **Volatility targeting**. Data
feasibility confirmed first: `^SKEW` is reachable via yfinance with
~30.0 years of dev-period history (1990-01-02 on), the longest of any
volatility-derived signal used in this loop (2.3x `^VVIX`'s history),
so no substitute idea was needed. Distinction from families 016 (VIX
level)/025 (VIX-vs-realized spread)/041 (VIX3M/VIX term structure)/046
(VVIX vol-of-vol) verified concretely on real dev data: raw SKEW-vs-VIX
level correlation only -0.235 (weak, opposite-signed from a naive "both
just measure fear" prior), flag-agreement 45.3%/48.7%/52.8%/52.2%
against those four families' own elevated flags (all strictly between
0% and 100%), a December 2019 "complacent VIX (12.50, 8.3rd trailing
percentile), expensive tails (SKEW=150.14, its own all-time-record
100th trailing percentile)" divergence episode, a January 1991 Gulf War
inverse-divergence episode (VIX elevated, SKEW depressed), and a 2008
GFC comovement/contrast episode. Primary config (`skew_lookback=252,
k=1.0, min_mult=0.5, max_mult=2.0`) beats DCA on wealth AND Sharpe on
only **1/5** core assets (SILVER only, razor-thin; SP500/GOLD/BTC lose
both, OIL wins wealth but loses Sharpe) at both fee levels -- **sec 4.1
FAIL** (need >=3/5), decisively. Grid: **0/36 (0%)** of configs clear
the majority-of-assets bar -- sec 4.4 FAIL, the weakest grid result of
any family in this loop so far. CSCV PBO=0.857, the highest (most
overfitting-prone) of any family so far. Raw pooled excess-return Sharpe
is strongly negative (-0.0241/week, -17.4%/yr annualized) with extreme
kurtosis (1299.9) -- DSR effectively zero (1.54e-55), sec 4.2 FAIL. Sec
4.3 not run (sec 4.1 already fails decisively, per established
precedent). Holdout not opened (rejected, not a finalist). Unlike
family 046 (VVIX), whose sign and functional form produced the loop's
strongest sec 4.1/4.4 result before failing on DSR/rolling-windows,
SKEW's identically-shaped signal (same risk-off sign, same continuous
percentile-multiplier form, same grid shape) failed even the basic
sec 4.1/4.4 win-rate checks -- a useful negative data point that the
functional-form template that worked well for VVIX's signal does not
transfer to every volatility-derivative signal with a plausible
risk-off sign.

4 ideas remain (#49-52), below the sec 8 step-2 threshold of 5 -- 1
replacement idea is added now to restore the threshold before the next
iteration takes #49.

Idea #49 (tolerance-band drift-triggered rebalancing of the 5-asset
portfolio) has been taken from the queue and used for family
`048-drift-band-rebalance`; see `families/048-drift-band-rebalance/`
(**REJECTED**). Assessed as a 5-asset portfolio family (sec 4.1 Portfolio
line) vs. fixed-weight 5-asset DCA, category **Rebalancing / allocation**.
Target weights are FIXED equal weight (20% each, never tilted by any
signal, unlike families 013/029) and a rebalance to that fixed target
fires only when some asset's weight drifts more than `band_pct` outside
20% (checked at each week-end) with a `min_days_between_rebalances`
cooldown; between triggers the strategy behaves exactly like plain DCA.
Required concrete distinction check (real dev data, primary config)
passed both legs before the grid was trusted: inter-rebalance gap
coefficient of variation 1.159 (far from the 0 a fixed calendar cadence
would show) and dispersion-vs-rebalance point-biserial correlation +0.452
(rebalance week-ends have materially higher cross-asset dispersion) --
confirms the trigger genuinely responds to realized price divergence
rather than being a disguised calendar rule, the distinction v2's closed
C1/C2/C3 and families 002/013/029/043 all required. Sec 4.1: primary
config (`band_pct=0.05, min_days_between_rebalances=5`) beats DCA on
Sharpe (1.060 vs 0.802) but loses on wealth (2.013x vs 2.937x invested at
0.1% fees) -- FAIL (need both), and this Sharpe-wins/wealth-loses pattern
holds uniformly across the ENTIRE 18-config grid (0/18, 0% clear the bar)
-- sec 4.4 FAIL, tied with family 047 for the weakest possible grid
outcome. DSR effectively zero (raw pooled excess Sharpe -0.0791/week,
skew -1.30, kurtosis 14.51). CSCV PBO=0.714 (elevated). Sec 4.3 not run
(sec 4.1 fails decisively across the whole grid, per established
precedent). Turnover/fee comparison (this family's own hypothesized
channel, per the task's transaction-cost framing): primary config's
turnover (3.51x invested) exceeds DCA's structural zero-sell floor
(1.00x) but falls monotonically as `band_pct` widens (5.08x at
`band_pct=0.02` down to 2.04x at `band_pct=0.15`) -- the band mechanism
suppresses turnover exactly as designed relative to an always-rebalance
rule, it just cannot outrun a benchmark that never sells, and the wealth
shortfall is driven by the FIXED TARGET's bounded BTC exposure (the same
root cause families 013's zero-tilt corner and 029's risk-parity target
hit), not by fee drag. Caught and fixed a real `PRIMARY_CONFIG`-grid
mismatch before any backtest ran (import-time assertion, family 021's
lesson): the first-draft grid did not contain the intended primary value
0.05; corrected before running, documented in results.md. Zero
external-data dependency (price-only signal), the only family in this
loop with no data-reachability risk by construction. Holdout not opened
(rejected, not a finalist).

2 ideas remain (#50, #53), below the sec 8 step-2 threshold of 5 -- 3
replacement ideas are added now to restore the threshold comfortably
above it before the next iteration takes #50.

| # | Idea | Category | Key source |
|---|---|---|---|
| 54 | Pre-FOMC announcement drift deposit timing (SP500): bank a larger share of deposits on an ordinary week, deploy a catch-up tilt into the 1-2 trading days immediately preceding each scheduled FOMC rate-decision announcement (a fixed, publicly known macro-event calendar, not a moving average, momentum sign, or a periodic weekday/month-of-year cycle). Genuinely different calendar structure from every prior seasonality family in this loop: families 006 (turn-of-month) and 007 (day-of-week) are both fixed MODULAR calendar cycles (day-of-month or day-of-week, repeating identically every period); family 018 (Halloween) and family 024 (SAD daylight) are both fixed ANNUAL calendar windows keyed to the calendar year itself; family 022 (election cycle) is a fixed QUADRENNIAL cycle keyed to year mod 4. This family's calendar is keyed to the FOMC's own scheduled meeting dates (8 per year, irregularly spaced within the year, published well in advance by the Federal Reserve, not derivable from any simple modular date function) -- a genuinely different, externally-determined event calendar, not a period of any of the above cycles' own repeating pattern. Must construct and verify this concretely in prereg.md (e.g., confirm FOMC meeting dates do not fall in a fixed weekday/month/quadrennial-year pattern that would make this family redundant with 006/007/018/022/024). Applicable to SP500 primarily (the motivating literature is US-equity-specific); must address whether/how to apply the same calendar to the other 4 core assets (a macro rate-policy event, plausibly relevant to all dollar-denominated assets, unlike family 008's CAPE which has no cross-asset analog at all) per family 022's own precedent for a US-specific event applied to all 5 core assets. | Seasonality / execution timing | Lucca, D.O. and Moench, E. (2015), "The Pre-FOMC Announcement Drift," *Journal of Finance* 70(1), 329-371 |
| 55 | ISM Manufacturing PMI regime deposit sizing: bank deposits (or trim buy size) when the ISM Manufacturing PMI (a single business-survey diffusion index, `<=50` conventionally read as contraction) sits low/falling in its own trailing percentile, deploy a catch-up tilt when it sits high/rising. Genuinely different macro signal from every prior regime family in this loop: family 019 (OECD CLI) is a COMPOSITE leading indicator averaging many underlying series across multiple economies with a built-in smoothing/detrending methodology; family 011 (credit-stress filter) and family 032 (M2 growth) are neither a business survey nor a leading-indicator diffusion index at all (a credit spread and a monetary aggregate respectively); family 027 (yield-curve slope) is a market-priced term-structure signal, not a survey. ISM PMI is a single-country, single-survey-based diffusion index (a monthly non-market business-condition survey, FRED/ISM published, with a known reporting lag that must be respected per plan sec 3.2 point-in-time rules) -- must construct a concrete real dev-period divergence example against family 019's OECD CLI in prereg.md (the two leading-indicator families should NOT move in lockstep at all times, given the methodological differences) before any design work, plus confirm the series' publication-lag/point-in-time properties and feasible history length via FRED. | Regime switch (macro / credit / sentiment) | Institute for Supply Management PMI methodology; Koenig, E.F. (2002), "Using the Purchasing Managers' Index to Assess the Economy's Strength and the Likely Direction of Monetary Policy," Federal Reserve Bank of Dallas Economic and Financial Policy Review |
| 56 | Momentum acceleration ("velocity of momentum") sizing: buy more when an asset's trailing momentum is itself INCREASING (the trend is accelerating), buy less when trailing momentum is decreasing even if still positive (the trend is decelerating) -- a second-derivative-of-price signal, not a level or sign-of-return signal. Genuinely different statistic from every prior momentum/trend family in this loop: family 005 (TSMOM sizing) scales by the SIGN of the trailing 12-month return only (a first-derivative, binary-direction signal, blind to whether that return is itself rising or falling); family 013 (momentum-tilted rebalancing) uses the LEVEL of cross-sectional relative momentum to set portfolio weights, not its own rate of change; family 002 (dual momentum) uses momentum LEVEL as a binary admission/ranking filter. This family instead compares momentum at two different points in time (e.g., today's trailing N-month return vs. that same trailing N-month return M months ago) and sizes buys by the sign/magnitude of that difference -- a genuinely distinct, higher-order statistic ("is the trend itself gaining or losing steam"), not a relabeling of any prior family's own signal. Must construct a concrete toy or real-data example in prereg.md showing a case where trailing momentum LEVEL and momentum ACCELERATION disagree in sign (e.g., a still-positive but decelerating trend) to prove the two are not interchangeable, following family 044's own Hurst-vs-autocorrelation divergence-example precedent. Price-only signal (daily Close), no external data dependency, testable identically on all 5 core assets. | Trend / time-series momentum exit | Novy-Marx, R. (2012), "Is Momentum Really Momentum?," *Journal of Financial Economics* 103(3), 429-453 (momentum of momentum / "intermediate horizon" persistence); Gao, L., Han, Y., Li, S.Z. and Zhou, G. (2018), "Market Intraday Momentum," *Journal of Financial Economics* (momentum-of-momentum / acceleration framing) |

| # | Idea | Category | Key source |
|---|---|---|---|
Idea #53 (Money-market funding-stress regime sizing) has been taken from
the queue and used for family `050-ted-funding-stress`; see
`families/050-ted-funding-stress/` (**REJECTED**). Single-asset family
across all 5 core assets, category **Regime switch (macro / credit /
sentiment)**. `TEDRATE` confirmed live reachable via FRED (1986-01-02
through 2022-01-21, discontinued but comfortably covering the full dev
period) -- no substitute construction was needed. Required concrete real
dev-period divergence from family 011 verified on live FRED data before
design work: Aug-Sep 2007 TED spike (z=+2.98/+3.93) while the BAA-AAA
corporate spread stayed flat (z=-0.10/-0.17) -- the interbank funding
market froze months before corporate credit widened; mirror-image
Dec2001-Feb2002 divergence (corporate spread z=+4.48..+4.55 near record
highs while TED z=-1.51..-1.76, depressed); full-history monthly z-score
correlation only +0.286. Brief distinctions from family 032 (M2, a
monetary-quantity aggregate, not a spread) and family 019 (OECD CLI, a
composite multi-series index, not a market-quoted spread) also
documented. Known-episode check (Aug 2007-Mar 2008, strictly pre-2020)
confirmed the primary config reads 95.1% stressed in the TED spread's own
textbook onset window before any grid result was trusted. Sec 4.1:
primary config (`lookback_years=10, stress_pctile=80,
stress_tilt_fraction=0.0, persistence_days=1`) beats DCA on wealth AND
Sharpe on only 2/5 core assets (SP500, BTC, both razor-thin) -- short of
the 3/5 majority, though a genuinely closer, mixed-margin result than
family 011's uniform 0/5 failure. Grid: 4/24 (16.7%) configs reach the
majority bar (the entire `lookback_years=5, stress_pctile=80` block) --
sec 4.4 FAIL, though the grid is directionally sensitive to
`stress_pctile` (the 90th-percentile block fails almost completely)
rather than uniformly flat. CSCV PBO=0.186 (notably lower than most
rejected families, consistent with a genuinely differentiated grid). DSR
effectively zero (raw pooled excess Sharpe -0.01344/week, genuinely
negative). Partially supports but does not confirm the prereg's
hypothesis that TED's faster mean-reversion (vs. family 011's slower
corporate-credit spread) would let this mechanism clear the sec 4.1 bar.
Holdout not opened (rejected, not a finalist).

3 ideas remain (#54-56), below the sec 8 step-2 threshold of 5 -- 1
replacement idea is added now to restore ground before the next
iteration takes #54, following families 023/024/025/026/027's precedent
(adding exactly 1 replacement idea).

| # | Idea | Category | Key source |
|---|---|---|---|
| 58 | Baltic Dry Index (BDI) shipping-freight-rate regime sizing: bank deposits when the Baltic Dry Index (a global dry-bulk shipping freight-rate index, a real-time market price for physical goods transport capacity, historically used as a leading indicator of global trade volume and industrial demand) sits low/falling in its own trailing percentile, deploy a catch-up tilt when high/rising. Genuinely different data type from every macro/regime family in this loop so far: families 011/050 are financial-market interbank/credit spreads, family 019 is a composite survey-based leading-activity index, family 027 is a Treasury yield-curve shape, and family 032 is a monetary aggregate -- none is a market-priced good-transport (freight) rate, a physical-trade-volume proxy with no financial-intermediation content at all. Must confirm free daily/weekly BDI data reachability (e.g. via a public index provider or a reachable proxy) before any design work, per this loop's standing data-feasibility discipline -- flagged explicitly as the first task at this idea's own gate step, since BDI is less commonly available as a free public series than the FRED-hosted signals used by 011/019/027/032/050. | Regime switch (macro / credit / sentiment) | Baltic Exchange (index methodology); Kilian, L. (2009), "Not All Oil Price Shocks Are Alike: Disentangling Demand and Supply Shocks in the Crude Oil Market," *American Economic Review* 99(3), 1053-1069 (uses a shipping-cost-based measure as a global real-activity proxy) |

Idea #45 (Hurst-exponent fractal trend-persistence regime sizing) has
been taken from the queue and used for family `044-hurst-regime-sizing`;
see `families/044-hurst-regime-sizing/` (**REJECTED**). Single-asset
family across all 5 core assets, category **Trend / time-series momentum
exit**. Trailing Hurst exponent `H_t` via classical rescaled-range (R/S)
analysis across a denser-than-usual multi-scale ladder (`hurst_window`
divided by `1,2,3,4,6,8,12,16`), causal percentile-ranked and converted to
a CONTINUOUS buy multiplier (elevated H/trending -> buy more; depressed
H/mean-reverting -> buy less). Rigorously distinguished from family 036
(lag-1 autocorrelation, the closest prior family): a constructed synthetic
series (slow sinusoidal drift + dominant i.i.d. noise, seed=7, n=252) has
lag-1 autocorrelation +0.0034 (near zero -- family 036 reads pure noise)
but H=0.692 (materially above 0.5 -- correctly detected as persistent),
proving the two statistics are not interchangeable; an AR(1) control
confirmed both statistics move together on genuine short-range
persistence, so the divergence is specifically a long-range-only-
dependence property. Primary config (`hurst_window=126,
pctile_lookback=252, k=1.0, min_mult=0.5`) beats DCA on wealth AND Sharpe
on only 2/5 core assets (SILVER, OIL, both razor-thin) at both fee levels
-- **sec 4.1 FAIL** (need >=3/5; every asset's gap vs. DCA is extremely
small in either direction). DSR effectively zero (1.30e-22, raw pooled
excess Sharpe genuinely negative, -0.00878/week) -- sec 4.2 FAIL. Grid:
only 6/36 (16.7%) configs beat DCA -- sec 4.4 FAIL (CSCV PBO=0.486,
elevated). Sec 4.3 not run per established precedent (sec 4.1 already
fails). Holdout not opened (rejected, not a finalist).

Idea #50 (Ulcer Index drawdown-severity-weighted volatility sizing) has
been taken from the queue and used for family `049-ulcer-index-sizing`;
see `families/049-ulcer-index-sizing/` (**REJECTED**). Single-asset family
across all 5 core assets, category **Sizing / valuation**. Local-window
Ulcer Index (`UI_t`, RMS of daily percentage drawdown from a trailing
rolling peak, the SAME window serving as both the peak reference and the
RMS-averaging window), causal percentile-ranked and converted to a
CONTINUOUS buy multiplier (elevated UI -> buy less/bank; depressed UI ->
buy more/normal). Rigorously distinguished from family 014 (magnitude-only
snapshot) and family 037 (duration-only count) via three programmatically-
verified proofs: two synthetic (family 014's stat held fixed at 15%
depth while duration varies 10 vs. 100 days -> UI 4.23 vs. 13.36; family
037's stat held fixed at 60 days while depth varies 10% vs. 30% -> UI 6.90
vs. 20.70) and one real dev-period SP500 example (deep-but-brief 2018-19
vs. shallow-but-long 2015-16 -- family 014 ranks 2018-19 worse by depth,
this family's UI ranks 2015-16 worse, 6.996 vs. 5.960 -- rankings
disagree, as predicted). Primary config (`ui_window=126,
pctile_lookback=252, k=1.0, min_mult=0.5`) beats DCA on final wealth on
5/5 core assets (all razor-thin) but the combined wealth-AND-Sharpe
criterion clears on only 2/5 (SP500, BTC) at both fee levels -- **sec 4.1
FAIL** (need >=3/5). DSR effectively zero (2.34e-22, raw pooled excess
Sharpe genuinely negative, -0.00573/week) -- sec 4.2 FAIL. Grid: 11/24
(45.8%) configs reach the combined majority bar -- sec 4.4 FAIL (need
>=2/3; CSCV PBO=0.629, elevated). Sec 4.3 not run per established
precedent (sec 4.1 already fails). Holdout not opened (rejected, not a
finalist).

**Idea #49 closed as duplicate, no new family created (this iteration,
2026-09-26).** This iteration was assigned idea #49 (tolerance-band
drift-triggered rebalancing of the 5-asset portfolio to a FIXED
equal-weight target) with an explicit instruction to first re-read family
`048-drift-band-rebalance/` in full, since its name sounded similar, and
to check whether it already covers exactly this mechanism before doing
any further work. It does. `families/048-drift-band-rebalance/prereg.md`
cites this exact queue item by number ("Seed queue item #49 ...") and
implements precisely the mechanism idea #49 describes: FIXED equal 20%
target weights for every asset (no momentum or risk-parity tilt), with a
rebalance triggered only when `max_a |w_a,t - 0.2| > band_pct`, checked at
each week-end decision day, plus a `min_days_between_rebalances` cooldown
-- word-for-word the same trigger condition and target structure this
queue entry specifies. `families/048-drift-band-rebalance/results.md`
already ran and rejected it: primary config (`band_pct=0.05,
min_days_between_rebalances=5`) beats fixed-weight 5-asset DCA on Sharpe
(1.060 vs 0.802) but loses on wealth (2.013x vs 2.937x invested at 0.1%
fees) -- sec 4.1 FAIL, and the same Sharpe-wins/wealth-loses pattern holds
across the entire 18-config grid (0/18 pass) -- sec 4.4 FAIL. DSR
effectively zero. The family's own required distinction checks (rebalance
gaps have coefficient of variation 1.159, far from a fixed calendar's
CV=0; dispersion-vs-rebalance point-biserial correlation +0.452) already
confirm the mechanism genuinely is a path-dependent drift trigger against
a fixed target, not a relabeled v2 C1/C2/C3 calendar rule -- i.e. this is
not a case where family 048 tested something superficially similar but
mechanistically different under a confusing name; it is the literal same
family + queue item, already fully assessed and REJECTED, logged in
`state/ledger.csv` (row `048-drift-band-rebalance`) and in this file's own
earlier entry ("Idea #49 ... has been taken from the queue and used for
family `048-drift-band-rebalance` ... REJECTED"). The row for idea #49
that remained in the "currently pending" table below that point (listing
"#49, #53" together) was a bookkeeping leftover from a later
replenishment step that mistakenly re-listed an already-resolved item
instead of only the genuinely-still-open one (#53) -- it has been removed
above. No new backtest, prereg, or strategy code was run for idea #49 in
this iteration, per this task's explicit instruction for the duplicate
case. Idea #49 is now closed for good: **closed as duplicate of family
048, no new family created.**

Removing the stale #49 row drops the pending list to 4 items (#53-56),
below the sec 8 step-2 threshold of 5 -- 1 replacement idea is added now
to restore the threshold.

| # | Idea | Category | Key source |
|---|---|---|---|
| 57 | Short-end T-bill curve roll-down ("cash carry") deposit-timing: when the short end of the risk-free curve is upward-sloped (FRED `DGS6MO` / `DGS1` yield above the 3-month T-bill yield already used for this engine's own cash interest, `IRX`/FRED `DGS3MO`, both standard constant-maturity series, same reachability class as `T10Y2Y` already confirmed for family 027's queue entry), holding a deposit in cash a little longer before deploying it earns roll-down/carry on the bill itself as it "rolls down" the curve toward maturity, so bank a small, capped share of the week's deposit and release it with a short lag; when the short end is flat or inverted, there is no roll-down benefit to holding cash longer, so deploy the full deposit immediately (behaves like plain DCA). Genuinely different axis from family 027 (queued, 2s10s `T10Y2Y`): 027 uses the LONG-end slope (10y minus 2y) as a business-cycle/recession-prediction regime signal wholly unconnected to any instrument this engine actually holds; this idea uses the SHORT end of the curve (3-month vs 6-month/1-year) as a literal roll-down/carry measure of the exact asset class (T-bills) the engine's own idle cash already earns interest in -- the classic money-market "carry" mechanism (hold the higher-yielding, longer-maturity bill and let it roll down to a lower yield/higher price as time passes) rather than a macro-regime forecast, so it is placed in the Carry/term-structure category (currently the loop's thinnest category, only family 041's VIX term structure sits there) rather than Regime switch. Also distinct from the commodity-futures term-structure carry idea (#12, seed queue, explicitly skipped by the owner for data infeasibility -- no free front/second-month futures curve was reachable): this idea needs no futures curve at all, only constant-maturity Treasury yields already known reachable via FRED. Asset-agnostic macro/rates signal, applied identically to deposit timing across all 5 core assets, same cross-asset-signal precedent as 006/007/011/019/027. Must confirm `DGS6MO`/`DGS1`/`DGS3MO` publication-lag and point-in-time properties via FRED (ALFRED vintages if revised) before any design work, per plan sec 3.2. | Carry / term structure | Fama, E.F. and Bliss, R.R. (1987), "The Information in Long-Maturity Forward Rates," *American Economic Review* 77(4), 680-692 (short-rate forward/roll-down predictability); Campbell, J.Y. and Shiller, R.J. (1991), "Yield Spreads and Interest Rate Movements: A Bird's Eye View," *Review of Economic Studies* 58(3), 495-514 (short-end curve carry/roll-down as a return driver distinct from long-end recession signaling) |

Idea #54 (Pre-FOMC announcement drift deposit timing) has been taken from
the queue and used for family `051-pre-fomc-drift`; see
`families/051-pre-fomc-drift/` (**REJECTED**). Single-asset family across
all 5 core assets, category **Seasonality / execution timing**. FOMC
meeting-calendar data reachability: `federalreserve.gov`,
`en.wikipedia.org` and `www.r-bloggers.com` were all confirmed
`EGRESS_BLOCKED` in this session (no live-reachable structured source),
so the 208 scheduled FOMC decision dates (1994-02-04..2019-12-11, 8/year)
were hard-coded from this session's own knowledge of the well-documented
public historical FOMC record, per the task's explicit allowance for this
contingency (unscheduled/emergency actions deliberately excluded).
Required concrete redundancy check against families 006/007/018/022/024
verified on the real 208-date list (not asserted): weekday distribution
spread across 4 weekdays (never a single fixed day, unlike 007);
day-of-month overlap with family 006's own turn-of-month window measured
at 1.09x the pure-chance-expected rate (43 actual vs. 39.6 expected --
"no disproportionate concentration," the correct test, not "zero
overlap" which no 8-meetings/year calendar could achieve); month-of-year
dates shift by days-to-weeks year over year (unlike 018/024's fixed
repeating annual template); year-mod-4 counts near-uniform (48/48/56/56,
unlike 022's quadrennial dependence); inter-meeting gaps irregular
(34-58 calendar days, not a fixed modulus). Cross-asset scoping: applied
to all 5 core assets per family 022's own precedent for a US-specific
macro event (FOMC decisions plausibly relevant to all USD-denominated
assets). Sec 4.1: primary config (`window_days=2, mild_tilt_fraction=0.0,
max_lump_multiple=6, banking_window_weeks=8`) beats DCA on wealth AND
Sharpe on only **1/5** core assets (OIL only) at both fee levels -- FAIL
(need >=3/5), decisively. Structural Sharpe-wins/wealth-loses pattern
(the primary wins Sharpe on 4/5 assets but wealth on only 1/5; SP500 --
the literature's own anchor asset -- loses wealth despite winning
Sharpe). Grid: 0/16 (0%) configs reach the majority bar -- sec 4.4 FAIL,
tied with families 047/048 for the weakest possible grid outcome, with
the same Sharpe/wealth split holding structurally across the whole grid.
CSCV PBO=0.0 (lowest of any family so far -- no genuine overfitting-to-
noise signal, every config shares the same consistent SP500 wealth-loss
ranking). DSR effectively zero (3.77e-30 N_eff-based; raw pooled excess
Sharpe -0.0311/week, genuinely negative, moderate skew/kurtosis). Sec 4.3
not run per established precedent (sec 4.1 already fails decisively).
Caught and fixed a redundancy-gate bug before any backtest ran (first
draft used an arbitrary hard overlap threshold instead of the correct
chance-expected baseline; logged in `state/bugfix_log.md`, no trial
affected). Holdout not opened (rejected, not a finalist).

5 ideas remain (#55-58 plus this note leaves #55-58; +#54 just
resolved), below the sec 8 step-2 threshold's comfortable margin -- 2
replacement ideas are added now to restore the queue comfortably above
the threshold of 5 before the next iteration.

| # | Idea | Category | Key source |
|---|---|---|---|
| 59 | 10-year TIPS real-yield (FRED `DFII10`) opportunity-cost regime sizing: bank deposits when the 10-year Treasury Inflation-Protected Securities real yield sits high/rising in its own trailing percentile (holding non-yielding or low-yielding assets is expensive when a safe, inflation-protected alternative pays a high real return), deploy a catch-up tilt when real yields sit low/falling (the opportunity cost of holding gold, silver, BTC or even equities relative to a safe real return is low). `DFII10` is explicitly named as a reachable FRED series in prereg.md's own alternatives-considered lists for families 019 and 032, but has never itself been used as any family's primary signal -- confirmed via a repo-wide search before adding this entry. Genuinely different mechanism from every prior family: family 027 (`T10Y2Y`) is the SLOPE between two nominal Treasury maturities (a business-cycle/recession-prediction signal), not a real (inflation-adjusted) LEVEL; family 032 (M2) is a monetary-quantity aggregate, not a market-priced yield; families 011/050 are credit spreads, not a Treasury real yield. The real-yield-as-opportunity-cost-of-non-yielding-assets channel is a distinct, well-established valuation mechanism (most directly relevant to gold, which pays no yield at all) that has not yet been tested in this loop. Applicable cross-asset (gold/silver most directly per the classic "gold vs. real rates" relationship; SP500/oil/BTC less directly but testable under this loop's established asset-agnostic-mechanism-vs-asset-specific-literature precedent, e.g. families 006/007/018/022). Must confirm `DFII10`'s point-in-time/publication-lag properties and full history length via FRED (coverage begins 2003-01-02) before any design work, per plan sec 3.2. | Sizing / valuation | Barsky, R.B. and Summers, L.H. (1988), "Gibson's Paradox and the Gold Standard," *Journal of Political Economy* 96(3), 528-550 (real interest rates as the fundamental driver of gold's relative value); Erb, C.B. and Harvey, C.R. (2013), "The Golden Dilemma," *Financial Analysts Journal* 69(4), 10-42 (real-yield-vs-gold-price empirical relationship) |
| 60 | Economic Policy Uncertainty (EPU) Index regime deposit timing: bank deposits when the Baker-Bloom-Davis News-Based Economic Policy Uncertainty Index (FRED `USEPUINDXD`, a daily, text-mining-derived count of newspaper articles discussing policy-related economic uncertainty) sits high/rising in its own trailing percentile, deploy a catch-up tilt when it sits low/falling. Genuinely different DATA TYPE from every prior regime/sentiment family in this loop: family 038 (consumer sentiment) is a household-survey-response index; families 011/050 are market-priced credit spreads; family 019 is a composite multi-series leading-activity index; family 027 is a Treasury yield-curve shape; family 032 is a monetary aggregate; idea #58 (queued, Baltic Dry) is a physical-goods freight-rate market price. EPU is none of these -- it is a purely TEXT-BASED, news-volume-derived uncertainty measure with no market price, no survey response, and no economic-quantity content at all, capturing a genuinely distinct "how much is the media/policy discourse itself signaling uncertainty" channel (Baker, Bloom & Davis's own headline finding: elevated EPU precedes reduced investment and equity-market volatility spikes). Must confirm `USEPUINDXD`'s FRED reachability and point-in-time properties (it is published with essentially no lag, being derived from same-day news text, but confirm exact vintage/revision behavior) and full history length before any design work, per plan sec 3.2 -- flagged explicitly since this loop has not yet tested a text-derived signal of any kind. | Regime switch (macro / credit / sentiment) | Baker, S.R., Bloom, N. and Davis, S.J. (2016), "Measuring Economic Policy Uncertainty," *Quarterly Journal of Economics* 131(4), 1593-1636 |
