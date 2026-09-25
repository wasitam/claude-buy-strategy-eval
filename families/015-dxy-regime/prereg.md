# Family 015: DXY (US Dollar Index) regime rotation

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Jen, S. (2001), the "dollar smile" framework -- the US dollar tends to
strengthen at BOTH extremes of the global growth/risk cycle (flight-to-
safety USD demand during global risk-off episodes, AND USD strength driven
by relative US growth/yield outperformance during strong-US-growth
episodes), with the dollar typically weakest in the "middle" of the smile
(synchronized global growth, risk-on, non-US assets outperforming). Also:
the classic inverse-relationship literature between the trade-weighted
dollar and USD-denominated commodity prices (dollar-denominated commodities
mechanically cost more to non-US buyers when the dollar strengthens, and
producer/EM USD-debt-service costs rise), e.g. Chen, Y.-C., Rogoff, K. and
Rossi, B. (2010), "Can Exchange Rates Forecast Commodity Prices?",
*Quarterly Journal of Economics* 125(3), and the long-standing practitioner
observation of a persistent negative gold/DXY and oil/DXY correlation.
Seed queue item #15 (research-loop-plan-v3.md sec 7.3 / this iteration's
task): "US Dollar Index (DXY) regime rotation."

## Mechanism ("why would this work, and who is on the other side?")

A confirmed, sustained US Dollar Index uptrend signals tightening global
USD liquidity (higher relative US real rates and/or safe-haven USD demand)
which mechanically raises the effective price of USD-denominated
commodities to non-US buyers and raises the cost of servicing USD-
denominated debt for commodity producers and EM borrowers -- both channels
that have historically coincided with headwinds for gold, oil, silver and
(more loosely, via risk-sentiment spillover) other risk assets including
BTC and, to a lesser and more theoretically ambiguous degree, SP500 (see
"Sign and scoping" below). This family applies the same banking/cash-cap
deposit-timing mechanic already used by families 004/006/007/010/011:
**when the DXY signal reads a confirmed dollar-strength regime, bank that
week's deposit as cash (earning IRX) instead of buying; when the regime
reads calm/not-confirmed, deploy the current week's deposit plus a capped
catch-up lump from banked cash.** This never sells existing holdings, never
shorts and never leverages, staying within the plan's constraints by
construction. The "other side" of this trade is whoever supplies liquidity
to sellers and buys the (real or perceived) dip during dollar-strength
episodes -- commodity producers hedging forward, value/contrarian buyers,
and market-makers -- compensated for taking on the risk that the dollar-
strength regime persists or that this investor's read of the correlation
is wrong for that particular episode; this family's investor is betting
that the historical inverse USD/commodity relationship holds up often
enough, net of costs, to beat simply dollar-cost-averaging through dollar
cycles indiscriminately.

## Sign and scoping across the 5 core assets (judgment call, stated explicitly per the task's instruction)

The literature's inverse-USD relationship is strongest and most direct for
**gold, silver and oil** (classic dollar-denominated-commodity channel).
**BTC**'s relationship to the dollar is looser and regime-dependent -- BTC
has behaved at times like a risk asset (correlated with equities, weak
during broad USD-strength/risk-off) and at times like digital gold
(inversely correlated with the dollar on its own monetary-debasement
narrative) -- but on balance the practitioner and academic literature more
often documents BTC's dollar-strength periods as headwinds (both the
"risk-off/flight-to-USD" and "tightening-USD-liquidity" channels tend to
coincide with weaker BTC), so the same "bank away during dollar strength"
direction is used, with lower conviction, flagged here. **SP500**'s
relationship is the most theoretically ambiguous of the five, exactly per
Jen (2001)'s "dollar smile": USD strength can reflect *either* global
risk-off (bad for SP500) *or* relative US growth outperformance (which can
be neutral-to-good for SP500, even as it hurts multinational earnings via
the translation channel) -- these two channels can offset, and the
empirical USD/SP500 correlation has flipped sign across different
multi-year regimes (e.g. broadly negative in 2002-2008, close to zero or
mildly positive in parts of 2014-2019). Despite this ambiguity, the family
is scoped and tested with a **single, uniform mechanism and sign applied
identically across all 5 core assets** -- bank away from every asset during
confirmed dollar strength -- for two reasons: (1) this matches the
established precedent in families 006/007/011 (a macro/price signal
applied identically per-asset, not asset-tailored signs baked in before
seeing any data, which sec 7.1's "ideas found by looking at the data are
not allowed" rule would make suspect if done post hoc); and (2) applying a
uniform mechanism, rather than hand-picking signs per asset, is the more
conservative test of the underlying "dollar smile" hypothesis -- if the
mechanism is only real for the strongest-case assets (gold/silver/oil) and
not SP500, the honest way to find that out is to test it uniformly and
report the per-asset pattern in results.md, not to declare SP500 exempt in
advance and risk being accused of tuning the win-scope to the answer. This
is flagged as a real risk to sec 4.1's >=3/5 majority bar going in: if the
SP500 leg drags in the wrong direction, that alone would not doom the
family (only 3 of 5 assets need to pass), but it is the leg most likely to
be the one that fails, and the report says so honestly regardless of the
eventual outcome.

## Category

**Regime switch (macro / credit / sentiment)**, chosen over "Cross-asset
rotation / relative strength" (sec 4.5's category list). Justification:
"Cross-asset rotation / relative strength" (as used by families 002's dual
momentum and 010's gold/silver ratio) describes mechanisms that move
capital *between* two or more of the 5 core assets based on their
*relative* performance to one another. This family does no such thing --
it uses a single external macro signal (the DXY, entirely independent of
any of the 5 core assets' own prices) to decide, independently for each
asset, whether that week's deposit into *that one asset* is banked as cash
or deployed -- structurally identical in mechanism shape to family 011's
credit-stress filter (external macro signal -> per-asset banking/deploy
decision), which was itself categorized "Regime switch." No capital ever
rotates between assets in this family; a dollar-strength regime causes
every asset's deposit to be banked simultaneously and independently, not
reallocated toward one asset and away from another. "Regime switch" is
therefore the better-fitting category.

## Why this is NOT a re-test of v2.1 Strategy D (sec 7.2 closed list) or family 011 (sec 7.2-adjacent discipline)

v2.1 Strategy D's rate-regime signals (R1-R4, Combo, Control) are built
entirely from **interest-rate data**: the Fed funds target, 2-year
Treasury yield, the 10y-2y curve slope, 10-year TIPS real yields, and the
FOMC dot plot -- every one answering "is US monetary policy tight or loose,
and in which direction is it moving?" Family 011's credit-stress signal
(BAA-AAA spread / NFCI) answers "how much default/liquidity risk premium
are corporate-bond investors demanding, and how tight are financial
conditions broadly?" This family's signal -- the trade-weighted US Dollar
Index's own price trend -- answers a third, distinct question: "is the
dollar itself, as a currency, in a sustained appreciation trend against
its trading partners?" The DXY is a currency-market price series, not a
policy-rate series or a credit-spread/financial-conditions composite; it
can and historically has diverged sharply from both (e.g. the dollar
strengthened through much of 2014-2015 even as Fed policy stayed at the
zero lower bound -- R1/R2a would have read "loose" while this family's
signal read "dollar-strength regime"; and credit spreads can stay calm
during periods of sharp dollar appreciation or vice versa, as in parts of
2018). No prior family (001-014) or the sec 7.2 closed list uses an FX
signal of any kind -- this is the first family in the loop to do so.

## Data inputs and reachability (gate step, verified before this file was written)

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only,
  same as every prior family).
- **DXY**: `DX-Y.NYB` (ICE US Dollar Index) via yfinance, confirmed
  reachable in this environment (14,151 daily rows, 1971-01-04 through
  today, verified by a direct fetch during this family's gate step). This
  is a daily market-price series, so unlike family 011's macro-release
  series, there is no publication lag to model -- the close is observable
  same-day, same as any of the 5 core assets' own OHLC. Routed through a
  new public helper, `src.backtest.v3.data.fetch_yf_macro(ticker)`, added
  in this family's implementation and structurally parallel to
  `fetch_fred_macro()`: it refuses any ticker already in `CORE_TICKERS` or
  `UNSEEN_TICKERS` (so it can never become a side-channel around the
  dev/holdout date gate) and is the only place in the codebase, besides
  `data.py` itself, allowed to call yfinance directly, keeping the
  raw-data-leak static check's coverage intact.
- **FRED substitute considered and not needed**: `DTWEXBGS` (Fed Board
  trade-weighted USD index vs. broad currency partners, weekly) was also
  confirmed reachable via FRED as a fallback (following family 008's
  FRED-substitution precedent), but is not used, since `DX-Y.NYB` is
  directly reachable, matches the seed queue item's own named ticker
  exactly, has daily (not weekly) resolution, and has a much longer
  history (1971 vs. `DTWEXBGS`'s 2006 start) -- all strictly better for
  this family's trend-confirmation signal, so the primary ticker choice
  needed no substitution.

## Single-asset vs. portfolio scoping (judgment call, stated explicitly per the task's instruction)

Assessed as a **single-asset family across all 5 core assets** under sec
4.1's standard >=3/5 rule, the macro signal applied identically and
independently per asset -- directly following the precedent set by
families 006, 007 and 011 (an asset-agnostic macro/calendar signal, tested
on every core asset via the existing single-asset `engine.py`, rather than
narrowed to a subset or recast as a portfolio-rotation family). This is
the conservative, harder-to-pass choice (any one asset's result cannot be
propped up by another's, unlike family 010's 2-asset portfolio framing)
and sidesteps family 008/010's structural single-asset-only trap
entirely, since a currency-market macro signal has no structural reason to
be undefined for any of the 5 core assets.

## Exact rules

Computed at each trading day's close `t`, using only data available by
that close (the DXY series' own close on day `t`, and each asset's own
price history through `t` -- the DXY leg never depends on which asset is
being traded).

1. **DXY series**: daily close of `DX-Y.NYB` (`data.fetch_yf_macro`),
   reindexed onto the asset's own trading-day calendar with a
   forward-fill (the DXY trades on its own calendar, e.g. it is closed on
   some days an asset like BTC trades) -- causal only, never filling
   backward.
2. **Trailing trend reference**: `SMA_t` = simple moving average of the
   DXY close over the trailing `dxy_lookback` trading days (of the
   aligned, forward-filled series), `min_periods = dxy_lookback` (NaN,
   i.e. no signal, before enough history exists).
3. **Raw dollar-strength flag**: `raw_strong_t = (DXY_close_t > SMA_t * (1
   + threshold_pct / 100))`. Before `SMA_t` exists, `raw_strong_t =
   False` (defaults to the calm/DCA-like state during signal warm-up,
   matching family 001/011's convention).
4. **Confirmation** (a "confirmed" trend, per the idea's own wording, not
   a same-day flip): `confirmed_t` uses the same discrete state-machine
   pattern as family 001's `compute_signal` (`trend_exit.py`) --
   `raw_strong` must hold continuously for `confirm_days` consecutive
   trading days before `confirmed_t` actually flips state; a single day's
   flicker is ignored. `confirmed_t` starts `False` (calm) at the series'
   start.
5. **Weekly decision (week-end days only, no sells ever)** -- same
   banking/lump-sum pattern as families 004/006/007/010/011:
   - **Confirmed dollar-strength regime:** buy `bank_fraction *
     weekly_deposit`. The remainder is banked as cash (earning IRX) until
     the regime next reads calm.
   - **Calm (not confirmed):** buy `min(cash, max_lump_multiple *
     weekly_deposit)` -- both the current week's normal deposit and, if
     cash was banked during a prior dollar-strength stretch, a capped
     catch-up lump, cash-capped so this can never become leverage.
6. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the DXY/SMA/confirmation computation entirely and
   buys 100% of that week's cash on every week-end day (0 otherwise) --
   reproduces plain DCA bit-for-bit, same pattern as every prior v3
   family's disable path.

## Parameters (4 tunable + 1 fixed, <=5 total, same pattern as family 011)

| Parameter | Grid values | Primary |
|---|---|---|
| `dxy_lookback` (SMA window, trading days) | 100, 200 | 200 |
| `confirm_days` | 5, 10 | 10 |
| `threshold_pct` (SMA buffer, %) | 0.0, 1.0 | 0.0 |
| `bank_fraction` (fraction of deposit still bought while regime confirmed) | 0.0, 0.25 | 0.0 |

`max_lump_multiple` is fixed at **6.0** for every grid config and the
primary (not grid-varied) -- the same value families 006/007/011 used as
their "headroom essentially never binds" setting, keeping this family at 4
tunable (grid-varied) parameters plus 1 fixed constant, comfortably at/under
the plan's <=5 ceiling.

`dxy_lookback=200` is primary as a full-cycle trend window (matching
family 001's own 210-day primary choice for its SMA trend signal, a
no-look choice based on convention/comparability, not any development-data
result on this signal). `confirm_days=10` is primary specifically because
the idea (and this file's own mechanism section) is framed around a
*confirmed* dollar-strength trend, not a same-day SMA cross -- 10 trading
days (2 calendar weeks) requires the regime to persist past a brief
whipsaw before it is treated as real, the more conservative of the two
grid values. `threshold_pct=0.0` (a plain SMA cross, no extra buffer) is
primary as the simplest, most literal reading of "above its trailing
trend," with `threshold_pct=1.0` in the grid as a stricter diagnostic
variant. `bank_fraction=0.0` (full banking during confirmed dollar
strength) is primary as the "purest" test of the timing-shift hypothesis,
matching family 006/007/011's own primary choice for the analogous
parameter.

**Primary-config non-degeneracy check (pre-registration design
verification, run before backtest, per the task's explicit instruction to
avoid a repeat of family 014's oversight):** the primary configuration's
`confirmed_t` regime was computed directly against development-window DXY
data (SP500's trading calendar, pre-2020) to confirm it produces a
genuinely mixed regime, not a degenerate always-on or always-off signal --
this is a check on the *signal's own frequency*, not a look at any
strategy backtest result, so it does not violate sec 7.1's "ideas found by
looking at the data are not allowed" rule (the mechanism and its
parameters were already fixed by the reasoning above; this only verifies
the primary config isn't a silent no-op the way family 014's
`near_high_mult=1.0` was). Result: the primary config
(`dxy_lookback=200, confirm_days=10, threshold_pct=0.0`) reads a confirmed
dollar-strength regime on **26.0%** of development-window trading days
(SP500 calendar) -- a genuinely mixed, non-degenerate regime, so the
"confirmed dollar strength -> bank" leg of the mechanism will actually
fire during backtesting, and with `bank_fraction=0.0` the primary
config's results are expected to differ meaningfully from plain DCA (as
opposed to family 014's `near_high_mult=1.0`, where the engine's own cash
cap silently clipped every "buy more" request back to the plain deposit --
that specific failure mode does not apply here, since this family's
"stressed" leg *reduces* the buy request below the deposit rather than
requesting *more* than is available, so there is no cash-cap collision to
silently nullify it).

## Grid

2 (`dxy_lookback`) x 2 (`confirm_days`) x 2 (`threshold_pct`) x 2
(`bank_fraction`) = **16 configurations** (<=36 cap).

## Primary configuration

`dxy_lookback=200, confirm_days=10, threshold_pct=0.0, bank_fraction=0.0`
(`max_lump_multiple=6.0` fixed for all configs).

## Expected sign

**Positive on both wealth and Sharpe for gold, silver and oil** (the
strongest-case assets per the mechanism, expected a priori to be the ones
most likely to drive a >=3/5 pass if the effect is real), with **lower
conviction for BTC** and **the most genuine uncertainty for SP500** (per
the "dollar smile" ambiguity discussed above) -- stated honestly as the
family's central, asset-differentiated hypothesis, even though the tested
mechanism itself is applied uniformly across all 5 assets (see "Sign and
scoping" above for why). As with every prior timing/banking-mechanic
family in this loop (004/006/007/010/011), this only reallocates the
*timing* of a fixed deposit stream, never total capital deployed and never
leverage, so even a real effect may show a modest absolute wealth/Sharpe
margin over DCA; and per family 010's documented "degenerate-config trap"
and family 011's own flagged risk, a sec 4.1 pass driven by a small number
of large historical dollar-cycle episodes (the 1980-85 and 2014-16 dollar
super-cycles both predate this family's core-asset development windows
for several assets; BTC's short development history in particular may
contain very few or zero full DXY cycles) is exactly the kind of
few-dominant-episode result the DSR and placebo circular-shift test are
designed to catch -- this family's own results should be read with that
precedent in mind before drawing conclusions from sec 4.1 alone.

## Implementation-check plan (sec 3.2, to be run in the implementation step)

1. `enabled=False` bypass reproduces plain DCA bit-for-bit (units and cash).
2. Cash and positions never negative, for the DCA baseline, the primary
   config, and the grid's most aggressive corner
   (`dxy_lookback=100, confirm_days=5, threshold_pct=1.0, bank_fraction=0.0`
   -- the config expected to spend the least time confirmed-strong, i.e.
   least banking, as a check on the opposite tail from the primary).
3. Total capital deployed never exceeds cumulative deposits + interest
   (primary config and the aggressive corner).
4. No-lookahead: perturbing all data after day `t` leaves every order
   on/before `t` unchanged, checked at two spot-check points deep into the
   sample (following family 011's precedent of checking more than one
   `t`), with particular attention to the DXY-alignment/ffill step's
   strict causality (only the DXY series' OWN past values, reindexed
   causally onto the asset calendar, ever enter `SMA_t`).
5. Point-in-time macro: N/A in the ALFRED-vintage sense (a daily market
   price series has no revision/publication-lag concern, as explained in
   "Data inputs" above) -- documented explicitly as such rather than
   silently skipped, matching the precedent set by every prior
   price-only-signal family's "N/A" entry for this check.
