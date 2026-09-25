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
| 15 | US Dollar Index (DXY) regime rotation: tilt deposits away from dollar-sensitive assets (gold, oil, BTC, and to a lesser extent SP500 via multinational earnings) during confirmed broad-dollar-strength trend regimes, deploy normally/with catch-up otherwise. Asset-agnostic macro signal (`DX-Y.NYB`, confirmed reachable via yfinance), applied per-asset like families 006/007/011. Distinct from every prior family: no prior family uses an FX signal. | Cross-asset rotation / regime switch | "Dollar smile" macro-driver literature (Jen, 2001); classic inverse USD-commodity price literature |
| 16 | VIX-level contrarian fear-gauge sizing: buy size scales up when the CBOE VIX (`^VIX`, confirmed reachable) sits in an elevated trailing percentile (a market-wide fear/overreaction signal), tilts down when VIX is complacent -- a *contrarian*, short-horizon mean-reversion bet, mechanistically distinct from family 003 (inverse-*realized*-variance sizing, no view on direction) and family 005 (trend-following sign of trailing return). Applied identically across all 5 core assets as a market-wide sentiment gauge, same precedent as 006/007/011. | Volatility targeting / Sizing | Whaley (2000), "The Investor Fear Gauge"; practitioner "buy the VIX spike" literature |
| 17 | Short-horizon RSI2-style mean-reversion sizing: buy larger when an asset's own short-term (2-3 day) RSI reads oversold, smaller when overbought -- each asset's own price-derived signal (no external data dependency, unlike #15/#16), testable identically on all 5 core assets. Distinct mechanism from every prior family: short-horizon (days, not months/quarters) mean reversion, not trend, valuation, calendar or macro-regime. | Sizing / valuation | Connors & Alvarez (2009), *Short Term Trading Strategies That Work*; Lehmann (1990) and Jegadeesh (1990) short-term reversal literature |
| 18 | "Halloween effect" / Sell-in-May seasonal deposit timing: bank a larger share of May-October deposits, deploy a catch-up lump-sum tilt into November-April, on a fixed annual calendar window (distinct time horizon and window shape from families 006's turn-of-month weekly window and 007's day-of-week window -- an annual seasonal cycle, not a monthly or weekly one). Calendar-only signal, testable identically on all 5 core assets per the 006/007 scoping precedent. | Seasonality / execution timing | Bouman & Jacobsen (2002), *The Halloween Indicator, "Sell in May and Go Away": Another Puzzle*, American Economic Review |

When fewer than 5 ideas remain, the next iteration researches more and adds
them here, each with a source, mechanism and category (plan sec 8 step 2).
