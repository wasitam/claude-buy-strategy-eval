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

| # | Idea | Category | Key source |
|---|---|---|---|
| 29 | Threshold/band-triggered rebalancing for the 5-asset portfolio: rebalance a position back toward its 20% target weight only when it drifts beyond a fixed band (e.g. +/-5 or +/-10 percentage points) from target, rather than on a fixed calendar interval. A **Rebalancing / allocation** family -- the category was previously only tested via v2's closed C1-C3 sweep (sec 7.2), which varied the fixed CALENDAR interval (weekly/monthly/quarterly/annual) a portfolio rebalances on; this family instead varies a drift-BAND trigger, never rebalancing on a schedule at all -- must state this distinction explicitly in prereg.md, same discipline family 020 used for its own distinction from 001/005/014. Portfolio family (uses `src/backtest/v3/portfolio_engine.py`/`portfolio_robustness.py`), assessed vs. fixed-weight 5-asset DCA per sec 4.1's Portfolio line, not the single-asset >=3/5 rule. | Rebalancing / allocation | Donohue, C. and Yip, K. (2003), "Optimal Portfolio Rebalancing with Transaction Costs," *Journal of Portfolio Management* 29(4), 49-63; Masters, S.J. (2003), "Rebalancing," *Journal of Portfolio Management* |

When fewer than 5 ideas remain, the next iteration researches more and adds
them here, each with a source, mechanism and category (plan sec 8 step 2).
