# Family 027: Yield-curve slope (2s10s) inversion regime filter

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Estrella, A. and Mishkin, F.S. (1998), *Predicting U.S. Recessions:
Financial Variables as Leading Indicators*, Review of Economics and
Statistics 80(1), 45-61 — the classic finding that the spread between the
10-year and (originally 3-month, later extended in the literature to
2-year) Treasury yields is one of the most reliable single leading
indicators of U.S. recessions, with a lead time historically in the range
of roughly 12-18 months from inversion to recession onset (subsequent
literature, e.g. Federal Reserve Bank of San Francisco Economic Letters on
the 2s10s spread specifically, and Estrella & Trubin (2006), extends and
updates the result). Seed queue item #27 (idea list this iteration):
"Yield-curve slope (2s10s) inversion regime filter."

## Mechanism ("why would this work, and who is on the other side?")

An inverted 2-year/10-year Treasury yield spread (short rates above long
rates) has historically signaled that bond-market participants expect the
Fed to cut short rates in the future, typically because they expect
weaker growth or an outright recession — the term premium compresses or
turns negative when the market prices in future easing. Because the
lag from inversion to recession has historically run 12-18 months, and
recessions are typically associated with equity/risk-asset drawdowns
(sometimes accompanied by commodity or crypto sell-offs too, though the
transmission is weaker and noisier for gold, silver, oil and BTC than for
equities), a deposit-timing rule that banks new cash while the curve is
inverted or has recently been inverted — rather than fully investing that
cash immediately — is a bet that (a) inversion is genuine advance warning
of future risk-asset weakness, and (b) capital preserved as cash ahead of
that weakness can be redeployed at more attractive prices once the curve
re-steepens and/or the episode resolves. This is the same banking/
cash-cap deposit-timing mechanic already used by families 004/006/007/010/
011 (bank now, catch-up lump later, cash-capped, no leverage) applied to a
different macro signal. The "other side" of this trade is whoever
continues to buy risk assets and hold duration through an inversion
episode and is compensated (in expectation) for bearing the pre-recession
uncertainty this family's investor instead avoids by banking new deposits
— term-premium and duration-risk-bearing investors, and dip-buyers who
correctly judge that any given inversion's lag/severity will be milder
than history's average. A known risk to the mechanism, stated honestly
before any backtest: inversions are rare, clustered events (only a
handful in the full available Treasury-yield history), so even a real
effect risks being a small-sample, few-dominant-episode result — exactly
the class of result sec 4.2's DSR and sec 4.3's placebo test are designed
to catch (the same caution family 011's own prereg.md flagged for its
credit-stress signal, and the same failure mode family 019's OECD CLI
regime family hit in practice).

## Category

**Regime switch (macro / credit / sentiment)** (research-loop-plan-v3.md
sec 4.5's category list; matches family 011's and 019's category label for
the same reason — a macro leading-indicator regime signal driving a
banking/timing decision).

## Rigorous distinction from family 011 (credit-stress filter)

Family 011's signal is the BAA-AAA corporate bond credit spread and/or
the Chicago Fed NFCI — both are **market-priced financial-conditions /
credit-stress** signals: they measure how much compensation bond
investors currently demand for default and liquidity risk, and how tight
financial conditions are *right now* across money, credit, leverage and
equity markets. This family's signal, the Treasury 2s10s slope
(`T10Y2Y`), is **not** a credit-stress or financial-conditions signal at
all — it contains no default-risk or liquidity-premium information; it is
built entirely from two default-risk-free Treasury yields and reflects
the market's expectation of the *future path of the risk-free short rate*
relative to the current long rate (a monetary-policy-expectations /
term-structure signal). The two series are constructed from entirely
different markets (corporate bonds and a systemic financial-stress index,
vs. two points on the risk-free Treasury curve) and have historically
diverged: the curve can invert years before credit spreads show any
stress at all (2005-06's inversion preceded 2007-08's credit-spread
blowout by well over a year — during 2005-06, BAA-AAA spreads were
historically *tight*, not stressed, while T10Y2Y was already negative),
which is direct empirical evidence the two are not proxies for one
another. Family 011's `regimes.py`-style rate-based cousins in v2.1
(discussed next) are the closer overlap; family 011 itself is a clean,
independent signal family from this one.

## Rigorous distinction from v2.1 Strategy D (sec 7.2 closed list) — the closest prior family

This is the **closest** prior family, because `T10Y2Y` is literally one of
Strategy D's named signal inputs (`src/backtest/v2/regimes.py`'s `R2b`,
"curve slope below its own trailing-26w mean" (flattening), `R2b-inv`,
"curve slope below zero" (inversion), and `R2c`, "R2a AND R2b" — see
`regimes.py:133-164`). Per sec 7.2's own text, "a new family may build on
one of these only if materially different: a different signal definition
or a different mechanism." The underlying data series here is literally
the same (`T10Y2Y` from FRED). This section argues the **mechanism** is
materially different, on its own terms, not by redefining the signal:

1. **What the signal controls.** v2.1 Strategy D's `R2b-inv`/`R2b`/`R2c`
   are inputs to an **8-signal ensemble vote** (`build_all_signals`
   returns `R1, R2a, R2b, R2b-inv, R2c, R3, R4, Combo`) whose *output* is a
   binary vote on **which of two pre-existing, already-defined strategies
   to run** — SmartDCA (v2's own rho x m_max sizing rule) or plain DCA —
   for that period, across a 5-asset universe (gold/silver/BTC/oil/
   SP500). Family 027's yield-curve signal is used **alone**, not as one
   vote among eight, and its output is **not** a choice between two other
   pre-existing strategies. It is a **direct deposit-banking decision**:
   bank this week's cash vs. deploy it (plus a capped catch-up lump),
   exactly the same primitive family 011's credit-stress filter, family
   006's turn-of-month timing, and family 004's banking mechanic already
   use in this loop. Strategy D never itself decides "bank cash vs. buy
   now" — it decides "run SmartDCA this period, or run plain DCA this
   period," and SmartDCA is itself a valuation-anchored sizing rule with
   its own internal buy-size logic, not a cash-banking rule. These are
   different **classes** of mechanism: **meta-strategy-selection** (choose
   which of two existing rule-systems governs sizing) vs. **direct
   timing/banking** (this family's own simple threshold-and-hold rule
   governs sizing, with no reference to or dependency on SmartDCA or any
   other pre-existing strategy at all).
2. **Signal construction is also not identical**, even though both use
   `T10Y2Y`. `R2b-inv` is a simple `slope < 0` snapshot test with a
   2-week whipsaw-confirmation filter (`anti_whipsaw`, `confirm_weeks=2`)
   applied uniformly across all of Strategy D's signals. This family adds
   two mechanism-specific features `R2b-inv` does not have: (a) an
   explicit **persistence** requirement (`persistence_days` consecutive
   trading days below threshold, tunable, not fixed at a shared 2-week
   whipsaw filter shared across 8 unrelated signals) motivated by
   Estrella & Mishkin's own point that a single-day inversion is noisy
   and unreliable, and (b) an explicit **post-inversion banking-window
   extension** (`banking_window_days`, tunable up to 2 years) that keeps
   banking cash for a period *after* the curve un-inverts, motivated
   directly by the 12-18-month historically-documented lag between
   inversion and recession — a feature with no analogue anywhere in
   `regimes.py` (Strategy D's signals are all point-in-time snapshot
   reads with a shared short whipsaw filter, never an extended
   forward-looking banking window keyed to a economically-motivated lag).
3. **Re-test question, answered explicitly and honestly.** Is this a
   re-test of Strategy D's "yield-curve flattening/inversion" signal
   specifically? **Partially yes in data source, no in mechanism and
   rule.** The data series is unambiguously the same. But sec 7.2's test
   is explicitly disjunctive ("a different signal definition **or** a
   different mechanism" — either suffices), and this family satisfies
   both prongs: a different mechanism (direct banking vs.
   meta-strategy-selection-by-ensemble-vote, argued above), **and** a
   different signal definition (persistence-confirmation + post-inversion
   banking-window extension, vs. Strategy D's shared 2-week whipsaw
   filter with no lag/extension feature). Because Strategy D's `R2b-inv`
   was only ever tested as one of eight votes feeding a strategy-selection
   ensemble, its *standalone* explanatory power as a direct deposit-timing
   signal was never itself isolated or tested in v2.1 — that isolated
   question is what this family answers, and the result of this family's
   isolated test cannot be inferred from Strategy D's ensemble-level
   result (which pooled inversion together with rate-level, dot-plot and
   TIPS-real-yield signals across 5 unrelated assets and never reported
   `R2b-inv`'s standalone contribution). This is judged, on balance, a
   materially different family under sec 7.2's own stated rule, not a
   re-test — but it is flagged here as the family in this loop's closest
   proximity to a closed prior result, and any positive result from this
   family should be read by the owner with that proximity explicitly in
   mind (this is exactly the kind of judgment call the task asked to be
   argued rigorously rather than asserted).

## Single-asset vs. multi-asset scoping

The yield-curve signal is macro and asset-agnostic (it says nothing about
any one of the 5 core assets specifically), matching the precedent set by
families 006/007/011/015/019 (an asset-agnostic macro/calendar signal
gets tested on all 5 core assets under sec 4.1's standard >=3/5 rule,
rather than narrowed to one asset). This is the harder-to-pass, more
conservative choice, and is assessed as a **single-asset family across
all 5 core assets**, independently per asset, using `engine.py`.

## Exact rules

Computed at each week-end decision day `t` (same weekly cadence as every
other v3 family), using only the point-in-time `T10Y2Y` value available
as of `t`'s close, and the asset's own trading-day calendar/price for
fills — the yield-curve signal never depends on which asset is being
traded.

1. **Signal series.** `T10Y2Y` (10-Year Treasury Constant Maturity Minus
   2-Year Treasury Constant Maturity, FRED series `T10Y2Y`, daily, back to
   1976-06-01), fetched via `src.backtest.v3.data.fetch_fred_macro`.
2. **Point-in-time construction.** `T10Y2Y` is a market-observable daily
   rate computed from same-day Treasury auction/secondary-market yields;
   FRED's actual publication practice posts each business day's value the
   next business day. A conservative **2-calendar-day** publication lag is
   applied (one calendar day more than the documented 1-business-day
   practice, matching family 015's DXY-style "market price, minimal but
   nonzero lag" convention rather than assuming same-day availability),
   then forward-filled onto the asset's daily trading index.
3. **Confirmed inversion.** At each trading day `t`, `inverted_raw_t =
   (point-in-time T10Y2Y_t < invert_threshold)`. `confirmed_inverted_t =
   True` only if `inverted_raw` has been continuously `True` for the
   trailing `persistence_days` trading days ending at `t` (a rolling
   all-True window) — this is the persistence/confirmation filter
   Estrella & Mishkin's own lag caveat motivates (a single noisy day
   crossing zero should not itself flip the regime).
4. **Banking regime (with lag extension).** `banking_t = True` if
   `confirmed_inverted` has been `True` at any point within the trailing
   `banking_window_days` calendar days ending at `t` (inclusive of `t`
   itself) — i.e., a rolling "any confirmed inversion within this window"
   test. `banking_window_days=0` means banking tracks the confirmed
   inversion exactly, with no extension; larger values extend banking
   into the normal-slope period following de-inversion, modeling the
   12-18-month historically-documented lag between inversion and
   recession risk (`banking_window_days` up to 504 trading days, ~2
   years, deliberately spans and exceeds the upper end of the cited lag
   range rather than under-covering it).
5. **Weekly decision (week-end days only), no sells ever** (matching
   families 003/005/006/007/010/011's precedent — a pure timing/banking
   rule, never a rule that liquidates existing units, staying within the
   plan's no-leverage/no-shorting constraint by construction):
   - **Banking regime active:** buy `stress_tilt_fraction * weekly_deposit`.
     The remainder is banked as cash (earning IRX, sec 3.2) until the
     regime next reads normal.
   - **Normal regime:** buy `min(cash, max_lump_multiple * weekly_deposit)`
     — this week's normal deposit, plus a capped catch-up lump from any
     banked cash, cash-capped so this can never become leverage.
6. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the signal/regime computation entirely and buys
   100% of that week's cash on every week-end day (0 otherwise) —
   reproduces plain DCA bit-for-bit, same pattern as every prior v3
   family's disable path. Per family 010/011's documented degenerate-
   config trap: a grid config with `stress_tilt_fraction=0` and
   `enabled=True` is **not** equivalent to DCA, because the regime
   computation still runs and could mark historical weeks as banking even
   at conservative thresholds — only `enabled=False` is checked against
   the DCA baseline.

## Pre-grid data-reachability and known-episode sanity check (done before
registering the grid; not a backtest result)

`T10Y2Y` was fetched via `fetch_fred_macro("T10Y2Y")` (already cached from
v2.1's Strategy D usage, confirming reachability in v3's `data.py` gate
too): 1976-06-01 through the present, 12,577 daily observations. Spot-
checked against the three known development-period inversion episodes
named in the task: **1989** (curve negative 66% of trading days that
year, min spread -0.45), **2000** (negative 90% of days, min -0.52), and
**2006-07** (negative 65% of days in 2006, min -0.19; tapering to 29% of
days in 2007 as the curve re-steepened mid-year, consistent with the
documented history of that inversion episode ending around mid-2007).
This confirms the raw signal correctly and non-trivially registers all
three known historical episodes before any backtest result is trusted, per
the task's explicit instruction. The full persistence + banking-window
confirmation logic is re-verified as a non-degeneracy sanity check on the
primary config specifically, before the grid runs (see the run script).

## Data inputs

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only,
  same as every prior family).
- `T10Y2Y` from FRED, via `src.backtest.v3.data.fetch_fred_macro("T10Y2Y")`
  (same gate family 011 added for `BAA`/`AAA`/`NFCI`; no new data-access
  code path is needed).

## Parameters (4 tunable + 1 fixed, <=5 total)

| Parameter | Grid values | Primary |
|---|---|---|
| `invert_threshold` | 0.0, -0.10 | 0.0 |
| `persistence_days` | 5, 20 | 5 |
| `banking_window_days` | 0, 252, 504 | 252 |
| `stress_tilt_fraction` | 0.0, 0.25 | 0.0 |

`max_lump_multiple` is fixed at **6** for every grid config and the
primary (not varied in the grid), matching family 011's own convention
("headroom essentially never binds"). This keeps the family at 4
*tunable* (grid-varied) parameters, comfortably under the plan's <=5
ceiling.

`invert_threshold=0.0` is primary because it is Estrella & Mishkin's own
textbook definition (curve inverted = short rate above long rate, spread
below zero) and the standard, most-cited threshold in the subsequent
practitioner and Fed-research literature on 2s10s inversion specifically
— a no-look choice based on the cited literature's own convention, not on
any development-data result. `persistence_days=5` (one trading week) is
primary as a minimal noise filter consistent with the mechanism's own
caution against single-day snapshot reads, without being so long a
requirement that it risks missing shorter historical inversion episodes
(the shortest of the three known episodes checked above, 2007, still had
inverted readings during large multi-week stretches, comfortably longer
than a 5-day confirmation window). `banking_window_days=252` (~1 trading
year) is primary as the low end of the cited 12-18-month lag range,
translated to trading days — a conservative middle choice that extends
banking meaningfully past de-inversion without assuming the full 18-month
upper bound, matching the reasoning families 008/010/011 used for their
own primary window-length choices. `stress_tilt_fraction=0.0` (full
banking while the regime is active) is primary as the "purest" test of
the timing-shift hypothesis, matching family 011's own primary choice for
the analogous parameter.

## Grid

2 (`invert_threshold`) x 2 (`persistence_days`) x 3 (`banking_window_days`)
x 2 (`stress_tilt_fraction`) = **24 configurations** (<=36 cap).

## Primary configuration

`invert_threshold=0.0, persistence_days=5, banking_window_days=252,
stress_tilt_fraction=0.0` (`max_lump_multiple=6` fixed for all configs).

## Expected sign

**Positive on both wealth and Sharpe, if the yield-curve-inversion
leading-indicator mechanism is real and its "bank ahead of, and catch up
after, the historically-signaled risk window" logic survives this loop's
fee/robustness bar** — stated honestly as the family's central hypothesis,
not a certainty. Genuine risks flagged before any backtest, informed by
this loop's now-consistent pattern across every prior macro-regime
family (006/007/011/015/019): (1) like those families, this mechanism
only reallocates *timing* of a fixed deposit stream (never total capital
deployed, no leverage), so even a real effect may show a small absolute
wealth/Sharpe margin over DCA; (2) inversions are rare and clustered
(effectively 3-4 distinct historical episodes in the available Treasury
history, per the sanity check above), so this family is at meaningful risk
of the "few-dominant-episode" pattern family 011's own prereg flagged and
family 019 hit in practice — a strong sec 4.1 pass on such a thin event
count should be read with real skepticism by sec 4.2 (DSR) and sec 4.3
(placebo) before being trusted, and this family's own results should be
read with that precedent explicitly in mind rather than taking a sec 4.1
pass at face value.

## Grid-counted marker note

Following families 010/011's documented degenerate-config trap:
`enabled=False` is the **only** true degenerate case here too. A grid
config with `stress_tilt_fraction=0` and `enabled=True` is **not**
equivalent to DCA even during a period with zero confirmed-inverted weeks
in the relevant window, because the regime computation and persistence/
banking-window logic still run. Only `enabled=False`, which bypasses the
regime/signal computation entirely, is checked against the DCA baseline.
