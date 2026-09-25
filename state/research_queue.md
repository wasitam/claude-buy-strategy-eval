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

Remaining queue (3 ideas -- below the plan sec 8 step 2 threshold of 5; the
*next* iteration should research and add more before or as part of its own
run, since this iteration's scope was specifically idea #10 end-to-end,
not a full queue replenishment):

| # | Idea | Category | Key source |
|---|---|---|---|
| 11 | Credit-stress risk-off filter (BAA−AAA spread, NFCI) | Regime | Gilchrist & Zakrajšek (2012) |
| 13 | Momentum-tilted rebalancing (rebalance toward trend winners) | Rebalancing | Asness, Moskowitz & Pedersen (2013) |
| 14 | Drawdown-from-high reserve deployment (a different reference point than SmartDCA's moving average) | Sizing | Practitioner literature; must justify why it isn't a re-test |

When fewer than 5 ideas remain, the next iteration researches more and adds
them here, each with a source, mechanism and category (plan sec 8 step 2).
