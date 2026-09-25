# Family 011: Credit-stress risk-off filter

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Gilchrist, S. and Zakrajšek, E. (2012), *Credit Spreads and Business Cycle
Fluctuations*, American Economic Review — shows that a corporate-bond
credit spread built from secondary-market bond prices (the "excess bond
premium" component in particular) is a powerful leading indicator of
economic activity and financial conditions, above and beyond what
default-risk-adjusted spreads alone would predict; spread widening
anticipates tightening financial conditions and weaker forward economic
and asset-market outcomes. Practitioner analogue: the Chicago Fed's
**National Financial Conditions Index (NFCI)**, itself constructed from
~100 measures of risk, credit and leverage across money, debt and equity
markets, explicitly designed as a real-time financial-stress gauge in the
same spirit. Seed queue item #11 (research-loop-plan-v3.md sec 7.3):
"Credit-stress risk-off filter (BAA−AAA spread, NFCI)."

## Mechanism ("why would this work, and who is on the other side?")

Widening corporate credit spreads (BAA minus AAA yields) and a rising NFCI
both signal that financial intermediaries and bond investors are pricing
in elevated default and liquidity risk, tightening the supply of credit to
the real economy before that stress fully shows up in equity prices or
other asset markets — credit markets have historically led equity/risk-
asset markets at major stress turning points (2000-02, 2007-09, 2015-16
energy-credit stress, 2020 COVID, 2022 rate-shock/regional-bank stress).
The mechanism this family tests is **not** "sell risk assets when credit
is stressed" (that would require shorting, which the plan forbids) —
it is the same banking/cash-cap deposit-timing mechanic already used by
families 004/006/007/010: **when the credit/financial-conditions signal
is in its own stressed percentile range, bank that week's deposit as cash
(earning IRX) instead of buying; when the signal is calm, deploy the
current week's deposit plus a capped catch-up lump from banked cash.**
This is a bet that periods of elevated credit stress are, on average,
followed by more attractive entry prices across risk assets once the
episode resolves (spreads mean-revert, and forced/liquidity-driven selling
during acute credit stress tends to overshoot fair value) — the same
"buy after distress resolves rather than during it" logic behind trend-
exit and turn-of-month strategies, but keyed to a credit-market rather
than a price-trend or calendar signal. The "other side" of this trade is
whoever supplies liquidity to sellers during acute credit-stress episodes
(distressed-debt funds, value investors, market-makers) and is compensated
for absorbing the elevated risk and uncertainty at exactly the moments
this family's investor is instead sitting in cash — this family never
claims to time the *bottom*, only to avoid dollar-costing new deposits
directly into the most acute, highest-uncertainty phase of a credit-stress
episode, redeploying once conditions normalize.

## Category

**Regime switch (macro / credit / sentiment)** (research-loop-plan-v3.md
sec 4.5's category list, matching sec 7.3's own label for seed-queue item
#11 exactly).

## Why this is NOT a re-test of v2.1 Strategy D (sec 7.2 closed list)

v2.1 Strategy D's rate-regime signals (R1–R4, Combo, Control — see
`src/backtest/v2/regimes.py`) are built **entirely from interest-rate
data**: the Fed funds target midpoint (`DFEDTAR`/`DFEDTARU`/`DFEDTARL`),
the 2-year Treasury yield (`DGS2`) relative to its own trailing mean, the
10y-2y curve slope (`T10Y2Y`), 10-year TIPS real yields (`DFII10`), and the
FOMC dot plot median projection (`FEDTARMD`, an ALFRED-vintaged series).
Every one of R1–R4 answers a version of the question "is monetary policy
tight or loose, and in which direction is it moving?" — a **policy-stance**
regime, not a market-stress regime. This family's signal — the BAA−AAA
corporate credit spread and/or the NFCI — answers a categorically
different question: "how much compensation are corporate-bond investors
demanding for default/liquidity risk right now, and how tight are
financial conditions across money, credit, leverage and equity markets
broadly?" These are genuinely different data series (none of BAA, AAA or
NFCI appear anywhere in `src/backtest/v2/regimes.py`) and a genuinely
different economic mechanism: the Fed can hold rates flat or even cut
while credit spreads are actively blowing out (e.g. 2007-08's early phase,
where the Fed funds rate was already falling while credit spreads widened
sharply — R1/R2a would have read "easing/loose", not "tight", at exactly
the point this family's signal reads "stressed"). Historically the two
signal families frequently diverge, which is itself the clearest evidence
they are not proxies for one another. A reviewer could reasonably ask
whether *any* macro regime-switch family risks re-treading v2.1 Strategy
D's ground; this family's answer is that the closed list's exact rule
(sec 7.2's own text: "R1, R2a, R2b, R2b-inv, R2c, R3, R4, Combo and
Control") lists specific, named, rate-based signal constructions, none of
which this family's credit-spread/NFCI signal is a restatement,
relabeling, or minor variant of.

## Single-asset vs. multi-asset scoping (judgment call, stated explicitly)

The credit-stress signal is **macro and asset-agnostic** — like families
006/007's calendar signal, it does not depend on which of the 5 core
assets it is applied to. Following the precedent explicitly set in
families 006 and 007 (a signal whose motivating literature/construction is
not asset-specific gets tested on all 5 core assets under sec 4.1's
standard single-asset >=3/5 rule, rather than narrowed to one asset), this
family is assessed as a **single-asset family across all 5 core assets**,
independently per asset, using the existing single-asset `engine.py`. This
is the harder-to-pass, conservative choice (it does not pre-judge which
assets the effect, if real, would show up on) and avoids family 008/010's
structural-scoping question entirely, since — unlike CAPE (equities-only
by construction, no earnings for commodities/BTC) or the gold/silver ratio
(only meaningful as a 2-asset relative-value pair) — a credit-stress
regime signal has no structural reason to be undefined for gold, silver,
oil or BTC; it is a market-wide financial-conditions gauge, not a
per-asset fundamental.

## Exact rules

Computed at each week-end decision day `t` (same weekly cadence as every
other v3 family), using only the point-in-time credit/financial-conditions
signal available as of `t`'s close (see "Point-in-time / publication-lag
discipline" below) and the asset's own trading-day calendar/price for
fills — the credit signal itself never depends on the asset being traded.

1. **Signal series** (`signal_choice`):
   - `"credit_spread"`: BAA − AAA (Moody's Seasoned Baa/Aaa Corporate Bond
     Yield, FRED series `BAA`/`AAA`, monthly).
   - `"nfci"`: the Chicago Fed National Financial Conditions Index (FRED
     series `NFCI`, weekly).
2. **Point-in-time construction.** The raw FRED series is shifted forward
   by a fixed publication lag (see below) before being forward-filled onto
   the asset's daily trading-day index, so that the value "seen" on trading
   day `t` is only ever a value that had actually been published by `t`'s
   close, never today's true (possibly-still-unpublished-as-of-`t`) value.
3. **Regime.** At each week-end day `t`, compute the point-in-time signal's
   percentile rank within its own trailing `lookback_years` window (a
   purely backward-looking, expanding-until-full rolling percentile,
   `MIN_PERIODS` = the window length). If the percentile rank is
   `>= stress_pctile`, the regime is **stressed**; otherwise **calm**.
   Before enough history exists to fill the window, the regime defaults to
   **calm** (behaves like plain DCA until the signal is usable — the same
   convention family 005 uses for its momentum signal's warm-up period).
4. **Weekly decision (week-end days only), no sells ever** (matching
   families 003/005/006/007's precedent — a pure timing/banking rule,
   never a rule that liquidates existing units, so it stays within the
   plan's no-leverage/no-shorting constraint by construction):
   - **Stressed:** buy `stress_tilt_fraction * weekly_deposit`. The
     remainder is banked as cash (earning IRX, sec 3.2) until the regime
     next reads calm.
   - **Calm:** buy `min(cash, max_lump_multiple * weekly_deposit)` — this
     both makes the current week's normal deposit and, if there is banked
     cash from a prior stressed stretch, deploys a capped catch-up lump,
     cash-capped so this can never become leverage.
5. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the signal/regime computation entirely and buys
   100% of that week's cash on every week-end day (0 otherwise) —
   reproduces plain DCA bit-for-bit, same pattern as every prior v3
   family's disable path.

## Point-in-time / publication-lag discipline (sec 3.2 bullet 4)

Following the pattern established in `src/backtest/v2/regimes.py` (Strategy
D's rate-regime signals: fetch the raw FRED series, then apply an explicit,
documented lag/vintage rule before the value is usable in any decision) —
reused here, adapted to this family's two series, neither of which is an
ALFRED-vintaged (revised) series, so a fixed conservative publication lag
is used in place of true ALFRED vintage lookups (both BAA/AAA and NFCI are
constructed from market prices / already-public data at their observation
date, not later-revised survey aggregates, so vintage revision is not a
concern the way it is for GDP or the FOMC dot plot — only *release timing*
is):
- **`BAA`/`AAA`** (monthly, observation date = first of the month,
  representing that month's average corporate bond yield): FRED publishes
  these with the full month's data only after the month closes. A
  **45-calendar-day** lag is applied from each observation date before the
  value is usable — deliberately conservative (FRED's own typical release
  is within the first half of the following month) to guarantee no
  look-ahead even under a slow-release scenario.
- **`NFCI`** (weekly, observation date = the Friday the index-week ends):
  the Chicago Fed's actual publication schedule releases each week's NFCI
  value the following Friday (about a 7-calendar-day lag). An **8-calendar-
  day** lag is applied, one day more conservative than the documented
  schedule.
- Both lagged series are then forward-filled onto the asset's daily trading
  index (`.reindex(daily_index, method="ffill")` after the lag shift),
  exactly mirroring `regimes.py`'s `target_mid_w`/`dgs2_w` construction
  pattern (fetch raw -> reindex onto a daily date range -> ffill -> reindex
  onto the weekly/trading index).
- This is verified by the no-lookahead implementation check (below),
  applied with extra care per the task's instruction: the perturbation
  test perturbs asset **price** data only (as in every prior family), so a
  second, macro-specific check is added: recomputing the regime with the
  lag shortened to 0 days must, on at least some historical dates, produce
  a *different* regime reading than the documented lag — proving the lag
  is actually doing something, not a no-op — while the documented-lag
  version is the one used in all real backtests.

## Data inputs

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only,
  same as every prior family).
- `BAA`, `AAA` and `NFCI` from FRED, via the new
  `src.backtest.v3.data.fetch_fred_macro(series_id)` helper (added in this
  family's implementation, routed through `data.py` so the raw-data-leak
  static check's `fredgraph.csv` scan — which currently only allowlists
  `data.py` itself — stays accurate; no other v3 module calls FRED or
  yfinance directly).

## Parameters (4 of the allowed 5)

| Parameter | Grid values | Primary |
|---|---|---|
| `signal_choice` | `credit_spread`, `nfci` | `credit_spread` |
| `lookback_years` | 5, 10 | 10 |
| `stress_pctile` | 70, 80, 90 | 80 |
| `stress_tilt_fraction` | 0.0, 0.25 | 0.0 |

`max_lump_multiple` is fixed at **6** for every grid config and the primary
(not varied in the grid) — the same value family 006/007 used as their
"headroom essentially never binds" setting, so the grid's 4 varied
dimensions isolate the credit-stress signal's construction and threshold
rather than the catch-up cap. This keeps the family at 4 *tunable* (grid-
varied) parameters plus 1 fixed constant, i.e. **effectively 4 tunable
parameters, comfortably under the plan's <=5 ceiling** (and even counting
`max_lump_multiple` as a 5th declared-but-fixed parameter stays at the
ceiling, not over it).

`signal_choice=credit_spread` is primary because BAA−AAA is the seed
queue's first-listed signal and the most direct empirical proxy for
Gilchrist & Zakrajšek's credit-spread mechanism, with a much longer
history (BAA/AAA both go back to 1919 on FRED) than NFCI (starts 1971,
usable window is materially shorter for `lookback_years=10` in the early
development period) — a no-look choice based on data coverage and
directness to the cited paper, not on any development-data result.
`lookback_years=10` is primary as a business-cycle-length window (long
enough to span at least one full credit cycle, avoiding a short window
that would make "stressed" mean merely "somewhat above last year", per
the same reasoning family 008 and 010 used for their own percentile-window
primaries). `stress_pctile=80` matches the 20/80 dead-zone convention
families 008 and 010 already established in this loop (top quintile of
the trailing-window signal = stressed). `stress_tilt_fraction=0.0` (full
banking during stress) is primary as the "purest" test of the timing-shift
hypothesis, matching family 006/007's own primary choice for the
analogous parameter, and consistent with the mechanism description above.

## Grid

2 (`signal_choice`) x 2 (`lookback_years`) x 3 (`stress_pctile`) x 2
(`stress_tilt_fraction`) = **24 configurations** (<=36 cap).

## Primary configuration

`signal_choice=credit_spread, lookback_years=10, stress_pctile=80,
stress_tilt_fraction=0.0` (`max_lump_multiple=6` fixed for all configs).

## Expected sign

**Positive on both wealth and Sharpe, if the credit-stress mechanism is
real and its "buy after distress resolves" logic survives this loop's
fee/robustness bar** — stated honestly as the family's central hypothesis,
not a certainty. A genuine risk flagged before any backtest, informed by
families 003/005/006/007/010's now-consistent pattern in this loop: like
those families, this mechanism only reallocates *timing* of a fixed
deposit stream (never total capital deployed, no leverage), so even a real
effect may show a small absolute wealth/Sharpe margin over DCA, and — per
family 010's now-documented "degenerate-config trap" and its DSR/placebo
failure pattern — a strong sec 4.1 pass driven by a small number of large
historical credit-stress episodes (2000-02, 2007-09, 2015-16, 2020, 2022)
is exactly the kind of few-dominant-episode result that DSR and the
placebo circular-shift test are designed to catch; this family's own
results should be read with that precedent in mind before drawing
conclusions from sec 4.1 alone.

## Grid-counted marker note

Following family 010's documented degenerate-config trap: `enabled=False`
is the **only** true degenerate case here too. A grid config with
`stress_tilt_fraction=0` and the signal `enabled=True` is **not**
equivalent to DCA even during a period with zero stressed weeks in the
lookback window, because the regime computation and percentile logic still
run and could, in principle, mark historical weeks stressed even at
`stress_pctile` thresholds — only `enabled=False`, which bypasses the
regime/signal computation entirely, is checked against the DCA baseline.
This is flagged here, before implementation, specifically so the same
mistake family 010 caught only after an initial wrong assumption does not
recur.
