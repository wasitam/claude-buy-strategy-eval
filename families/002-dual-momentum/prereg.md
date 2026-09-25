# Family 002: Dual momentum rotation across the 5 core assets + T-bills

**Status:** pre-registered. Committed before any backtest is run on development
data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Antonacci, G. (2014), *Dual Momentum Investing: An Innovative Strategy for
Higher Returns with Lower Risk*. The "dual momentum" / "Global Equities
Momentum" rule: combine **absolute momentum** (a time-series filter — only
hold an asset if its own trailing total return beats the risk-free rate,
i.e. it has positive momentum against cash) with **relative momentum** (a
cross-sectional filter — among the assets that pass the absolute filter,
rank by trailing return and hold only the strongest). Seed queue item #2
(research-loop-plan-v3.md sec 7.3).

## Mechanism ("why would this work, and who is on the other side?")

Two premia, combined: (a) time-series (absolute) momentum earns a premium by
sitting out of an asset during sustained drawdowns — the same
autocorrelated-drawdown logic as family 001's trend filter, but applied
identically across a 5-asset universe as an admission gate rather than a
per-asset override; (b) cross-sectional (relative) momentum earns a premium
by concentrating capital in the assets currently exhibiting the strongest
trend, on the theory that information diffuses slowly into prices
(underreaction) and that trend-following flows (CTAs, momentum funds) provide
positive feedback for months after a trend is established. The "other side"
of the trade is investors who rebalance mechanically back to fixed weights
(selling recent winners, buying recent losers) or who hold through a
systemic drawdown in an asset that has already broken down across the whole
5-asset universe — both groups are, on average, taking the other side of the
capital reallocation this strategy performs. The cost paid is concentration
risk (holding 1-2 of 5 assets, not all 5) and whipsaw around momentum
turning points, plus materially higher turnover/fees than a buy-and-hold
benchmark.

## Category

**Cross-asset rotation / relative strength** (research-loop-plan-v3.md sec
4.5). This is a **portfolio** strategy: the win rule applied is sec 4.1's
"Portfolio" line (see "Win-rule interpretation" below).

## Relationship to closed families (sec 7.2)

None of the v1/v2/v2.1 closed families used cross-sectional relative-strength
ranking to dynamically reallocate the deposit stream across a subset of
assets. v2's rebalanced portfolios (C1, C2, C3) used **fixed target weights**
with periodic rebalancing back to those same fixed weights — a static-weight
discipline, not signal-driven asset selection. Family 001 (this loop, not
closed, REJECTED) used a per-asset price-vs-own-SMA trend signal in
isolation, with no cross-asset comparison and no reallocation of capital
between assets — a fundamentally different mechanism from ranking assets
against each other and moving capital between them. This family is a
different mechanism (cross-sectional ranking + capital reallocation) and is
not a re-test of any closed family or of family 001.

## Win-rule interpretation (a real ambiguity in the charter, resolved here)

Sec 4.1 gives two lines: "Single-asset: ... at least 3 of 5 core assets" and
"Portfolio: beats fixed-weight 5-asset DCA." Dual momentum's mechanism
*requires* comparing assets against each other to rank them — it has no
meaningful decomposition into 5 independent single-asset "in this asset or
cash" decisions without destroying the relative-momentum half of the
mechanism (relative ranking is only definable across the universe, not per
asset). Sec 4.5 also lists "Cross-asset rotation / relative strength" as its
own mechanism category, distinct from "Trend / time-series momentum exit,"
which further signals that rotation strategies are meant to be assessed as
portfolios, the same way v2's C1/C2/C3 rebalanced portfolios were. **This
family is therefore assessed under sec 4.1's "Portfolio" line**: one NAV
series (pooled $2,500/week deposit across the 5-asset universe, dynamically
allocated) compared against fixed-weight 5-asset DCA ($500/week into each of
the 5 assets, never rebalanced), on final wealth AND Sharpe, at both fee
levels. The holdout pass rule (sec 5.3 "Portfolio" line — core 5-asset
2020+, and unseen 5-asset full history) and sec 4.3's robustness checks are
adapted to the portfolio NAV the same way (see "Robustness adaptations"
below).

## Exact rules

**Shared calendar:** per research-loop-plan-v3.md sec 3.2 ("For the
portfolio calendar, use NYSE trading days"), the portfolio's decision
calendar is `^GSPC`'s own daily trading-day index, clipped to start once
every one of the 5 core assets has data (i.e. BTC's first available date,
since BTC has the shortest history). Each other asset's daily OHLC is
forward-filled onto this shared calendar (handles small exchange-specific
holiday mismatches between NYSE, COMEX/NYMEX futures and BTC's
every-calendar-day trading). This is a judgment call, documented here and in
results.md.

**Signal, computed at each shared-calendar day `t`'s close, using only data
through `t` (no lookahead):**
- For each asset `a`, absolute momentum `AM_a,t = close_a,t / close_a,t-lookback_days - 1`
  (simple trailing total return over the lookback window; while fewer than
  `lookback_days` observations exist for an asset, it is excluded from
  ranking that day — treated as not qualifying).
- T-bill hurdle over the same window: `RF_t = prod(1 + daily_rf) - 1` compounded
  over the trailing `lookback_days`.
- Asset `a` **qualifies** on day `t` if `AM_a,t > RF_t + abs_mom_buffer_bps/10000`.
- Among qualifying assets, rank by `AM_a,t` descending (relative momentum) and
  select the top `top_n`. If fewer than `top_n` qualify, hold only the
  qualifying ones. If zero qualify, target is 100% cash (T-bills).
- Selected assets get **equal target weight** (`1/min(top_n, n_qualifying)`
  each); everything else (including cash) gets the residual weight.

**Rebalance cadence:** the target weight vector is recomputed and the
portfolio is rebalanced toward it **weekly**, on the shared calendar's last
trading day of each ISO week — the same day the $2,500 deposit
($500/asset-equivalent, pooled into one cash account) is credited. This is a
judgment call: it matches the deposit cadence exactly (so the strategy can
be read as "each week, decide where this week's money — and a rebalance of
existing money — goes," a natural retail-investor cadence), keeps the grid's
backtest cost bounded (daily full-portfolio rebalancing over ~90 years of
SP500 history x 12 grid configs x robustness sims was judged too expensive
for this iteration's budget), and is within the "at most daily" complexity
ceiling (sec 3.4) since it trades strictly less often than daily. Antonacci's
original is monthly; weekly is a defensible, slightly more responsive
variant given weekly funding, and is declared here before any backtest runs.

**Orders:** on a rebalance day, for each asset the target dollar value is
`target_weight_a x total_portfolio_value` (cash + sum of all positions,
valued at that day's close, including that day's deposit). The order for
asset `a` is `target_dollar_a - current_dollar_value_a` (positive = buy,
negative = sell). All orders fill at the **next** trading day's open — sells
across all 5 assets first, then buys, buys capped by available pooled cash
(engine sec 3.2). On non-rebalance days, no orders are placed (existing
positions are held).

**Degenerate case (`enabled=False`, implementation check only, not a grid
arm):** bypasses momentum entirely and, each week, submits a buy order for
exactly that asset's own $500 share of the deposit and nothing else (no
selling, no reallocation of existing holdings) — this reproduces the
fixed-weight 5-asset DCA benchmark exactly, bit-for-bit, the same pattern
family 001 used for its degenerate check.

## Data inputs

Daily OHLC close of all 5 core assets, and the daily risk-free rate (IRX),
all sourced via `src.backtest.v3.data.load_dev()` only. No macro or
alternative data.

## Parameters (3 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `lookback_days` | 126, 189, 252 (~6, ~9, ~12 trading months) | 252 |
| `top_n` | 1, 2 | 1 |
| `abs_mom_buffer_bps` | 0, 50 | 0 |

(Rebalance cadence is fixed at weekly, not a tunable grid parameter, per the
judgment call above.)

## Grid

3 x 2 x 2 = **12 configurations** (<= 36 cap).

## Primary configuration

`lookback_days=252, top_n=1, abs_mom_buffer_bps=0` — the literal Antonacci
12-month-lookback, single-best-asset, no-whipsaw-buffer "Global Equities
Momentum"-style rule, generalized from 2 risky assets to the 5-asset core
universe.

## Expected sign

Positive: higher final wealth and higher Sharpe than fixed-weight 5-asset
DCA. The absolute-momentum filter should reduce exposure during periods when
most/all of the 5 assets are simultaneously drawing down (keeping more of
the deposit stream in T-bills during those windows than a passive 5-asset
DCA ever does), and the relative-momentum ranking should concentrate capital
into whichever of the 5 assets is currently trending hardest, capturing the
cross-sectional momentum premium documented in the source literature. The
cost is concentration risk (foregoing the other 4 assets' diversification)
and higher turnover/fees, which is why the strategy must still pass at
0.25% fees (sec 4.1).

## Robustness adaptations (sec 4.3, portfolio-level)

- **Rolling windows:** 3-year and 5-year windows on the **portfolio NAV**
  (strategy vs. fixed-weight 5-asset DCA), stepped every 4 weeks, over the
  shared calendar's dev-period span (BTC's first date through 2019-12-31).
  No separate per-asset or 2-year-BTC window, since there is only one NAV
  series for a portfolio family.
- **Block bootstrap:** 4-week blocks, the **same block start indices reused
  across all 5 assets' log-return series** (sec 4.3's explicit rule for
  portfolios), both as-is and detrended, rerun through the portfolio engine.
- **Placebo:** circular-shift the weekly target-weight-selection sequence
  (which asset(s) were selected each rebalance week) and rerun.
- **Run counts:** per the plan's own scoped-down precedent (family 001,
  `state/bugfix_log.md` judgment call #3, and `src/backtest/v2/robustness.py`'s
  own docstring), bootstrap and placebo use **60 simulations** each rather
  than the plan's default 500 — half of family 001's already-reduced 120 —
  because each portfolio-level simulation reruns the full 5-asset engine
  (~5x the cost of family 001's single-asset sims). This is declared here,
  before any backtest, as a cost-scoping judgment call consistent with prior
  iterations, and will be documented again in results.md with the actual
  run count used.
