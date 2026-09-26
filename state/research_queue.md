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
| 38 | Range-based (Parkinson) realized-volatility sizing: increase buy size when an asset's own trailing Parkinson range-based volatility estimator (built from daily High/Low, `sqrt((1/(4*ln(2))) * mean((ln(High/Low))^2))` over a trailing window) is LOW relative to its own trailing percentile, decrease when elevated -- the same inverse-vol-sizing economic logic as family 003, but built from an entirely different statistic: family 003's realized variance uses only daily CLOSE-to-close returns (a single number per day), while Parkinson's estimator uses each day's intraday High/Low RANGE, a materially more efficient volatility estimator under continuous-price assumptions (Parkinson 1980) and one that can diverge sharply from close-to-close variance on days with large intraday swings that closed flat (a pattern close-to-close variance cannot see at all, and vice versa for a gap-driven day with a narrow intraday range). Price-only signal (daily High/Low/Close, already in the existing cached OHLC data, no Volume dependency), no external data dependency, testable identically on all 5 core assets. | Volatility targeting | Parkinson, M. (1980), "The Extreme Value Method for Estimating the Variance of the Rate of Return," *Journal of Business* 53(1), 61-65; Garman, M.B. and Klass, M.J. (1980), "On the Estimation of Security Price Volatilities from Historical Data," *Journal of Business* 53(1), 67-78 (the broader range-based-volatility-estimator literature Parkinson's estimator belongs to) |

When fewer than 5 ideas remain, the next iteration researches more and adds
them here, each with a source, mechanism and category (plan sec 8 step 2).
