# Family 016: VIX contrarian fear-gauge sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Whaley, R. E. (2000), "The Investor Fear Gauge," *Journal of Portfolio
Management* 26(3) -- the paper that coined "fear gauge" for the CBOE
Volatility Index (VIX) and documented that VIX spikes cluster around market
stress episodes. Also the broader mean-reversion-after-panic literature:
VIX spikes into the top decile of its trailing distribution have
historically been followed, on average, by above-average forward equity
(and, more loosely, broad risk-asset) returns as the panic/overshoot
unwinds -- e.g. the "buy when VIX is high" practitioner heuristic
formalized in various sell-side/academic studies of VIX-conditioned
forward returns (see also Whaley (2009), "Understanding VIX," for VIX's
behavior as a coincident/leading stress indicator rather than a forecast of
future realized vol itself). Seed queue idea #16 (research-loop-plan-v3.md
sec 7.3 addendum / this iteration's task): "VIX contrarian fear-gauge
sizing."

## Mechanism ("why would this work, and who is on the other side?")

The VIX is the market's own real-time, forward-looking price of S&P 500
option-implied volatility -- a cross-market gauge of aggregate investor
fear/uncertainty, not a property of any single one of the 5 core assets.
When VIX spikes into an elevated percentile of its own trailing
distribution, it typically coincides with acute, often indiscriminate
selling pressure across risk assets (forced deleveraging, margin calls,
liquidity withdrawal) that tends to overshoot fundamentals. The historical
pattern this family bets on is that such panic-driven selloffs are, on
average, followed by mean-reverting recoveries -- so **increasing** buy
size specifically during those elevated-fear episodes (buying into the
panic, not away from it) should, if the historical pattern holds, capture
better average entry prices than buying a constant amount every week
regardless of sentiment. The "other side" of this trade is whoever is
forced to sell during the panic (margin-called leveraged holders,
risk-limit-driven institutional deleveraging, panicking retail sellers) and
is compensated for providing that liquidity by accepting a worse average
price than a patient, contrarian buyer who has cash on hand specifically
earmarked for those episodes; this family's investor is betting that this
historical overshoot-and-recover pattern persists often enough, net of
costs, to beat indiscriminate constant-size DCA.

## Rigorous distinction from family 003 (vol_managed_sizing) -- required by this iteration's task, since a reviewer would ask

Family 003 and family 016 both scale weekly buy size using a measure of
volatility, so the distinction must be explicit and load-bearing, not
cosmetic:

| | Family 003 (vol-managed sizing) | Family 016 (VIX contrarian) |
|---|---|---|
| **Signal source** | Each asset's **own realized volatility**, computed purely from that asset's own daily returns (`vol_lookback_days` trailing stdev of log returns). A different, asset-specific number for every one of the 5 core assets. | The **CBOE VIX**, a single shared, cross-market signal derived entirely from **S&P 500 option prices** -- structurally identical across all 5 assets; gold, silver, BTC and oil have zero input into their own VIX-based signal. This is the same "one external macro/market signal applied per-asset" shape as families 006 (calendar), 007 (calendar), 011 (credit spread) and 015 (DXY) -- not the same shape as family 003's per-asset internal signal. |
| **Volatility concept** | **Realized** (backward-looking, historical) volatility of the asset's own price path. | **Implied** (forward-looking) volatility, priced in today by S&P 500 options -- a market expectation, not a historical statistic, and not computed from any of the 5 core assets' own price histories at all (SP500's own realized vol is not the input; the VIX index level is). |
| **Functional form** | A smooth, continuous ratio `sigma_ref / sigma_recent`, clipped to `[min_mult, max_mult]` -- the multiplier moves gradually and can take any value in a continuous range on every single day. | A **discrete, threshold-triggered regime switch**: `buy_multiplier` (a single fixed step-up) applies only above a fixed trailing percentile threshold (`elevated_pct`); below it, buys are a fixed `calm_fraction`. Two discrete states, not a continuously varying dial. |
| **Sign / relationship to buy size** | **Inverse**: high (recent, own) vol => buy LESS (`m_t<1`); low vol => buy MORE. A smooth risk-parity-style de-risking rule -- it reduces exposure precisely when the asset itself is choppy, regardless of the outcome for expected returns. | **Direct / contrarian**: elevated (cross-market, SP500-implied) fear => buy MORE. The opposite sign relationship to family 003, and applied identically to every asset (including gold/silver/BTC/oil, none of which contribute to the VIX signal that triggers their own extra buying). |
| **Economic story** | A risk-management / variance-targeting story (Moreira & Muir 2017): keep risk exposure roughly constant over time by leaning against an asset's own fluctuating variance, independent of any view on mean reversion or over/undershooting. | A behavioral-finance overshoot/panic-selling story (Whaley 2000): a *specific*, testable hypothesis that a shared fear spike is followed by *recovery*, i.e. this family takes a directional bet on mean reversion after cross-market panic that family 003 never makes (family 003 is agnostic to direction; it only manages variance). |
| **Trigger granularity** | Recomputed continuously every trading day from a rolling ratio of two windows on the SAME asset. | A single shared VIX percentile series computed once (same for all 5 assets, no asset-specific volatility calculation at all) and thresholded into a binary elevated/calm state, aligned onto each asset's own trading calendar. |

In short: family 003 asks "is *this asset* currently choppy relative to its
own recent history, and if so let's de-risk (buy less)?" -- a purely
statistical, per-asset, continuous, risk-reduction rule. Family 016 asks
"is the *whole market* currently panicking (per SP500 options, regardless
of what any individual asset's own price is doing), and if so let's lean
in and buy more, betting the panic overshoots?" -- a shared, discrete,
behavioral, risk-*seeking* rule with the opposite sign. These are different
signals (implied SP500-options vol vs. each asset's own realized vol),
different functional forms (discrete regime vs. continuous ratio),
opposite economic mechanisms (behavioral overshoot/reversion bet vs.
variance-targeting risk management) and opposite directional
relationships to buy size (buy more into elevated risk vs. buy less into
elevated risk). No rule or parameter of family 016 nests or reduces to
family 003's rule under any parameter setting, and vice versa -- so this is
not a re-test of family 003 by any reasonable reading of sec 7.2's
"materially different" bar (which family 003 predates and is not on the
sec 7.2 closed list itself, but the same "materially different" standard
is applied here anyway, per the task's explicit instruction to make this
rigorous).

## Category

Between **"Sizing / valuation"** and **"Volatility targeting"** (sec
4.5's list; the task instructs picking the better fit and documenting
why). **Chosen: "Sizing / valuation."** Justification: "Volatility
targeting" (per family 003's own use of that label) describes a smooth,
continuous risk-parity-style scheme whose purpose is to hold *exposure*,
not *expected-return conviction*, roughly constant by leaning against an
asset's own variance -- it is agnostic about whether higher volatility
means better or worse expected forward returns. Family 016 is not that: it
is a discrete, threshold-triggered *directional bet* -- "when the market's
fear gauge spikes, conviction in a forward mean-reversion opportunity goes
up, so buy more" -- structurally the same kind of "increase the buy
because a signal suggests this is a favorable entry point" logic as family
004's value averaging (target-based sizing) and family 008's CAPE
valuation sizing (buy more when valuation/signal says price is
relatively favorable), both filed under "Sizing / valuation." Labeling
family 016 "Volatility targeting" would risk exactly the confusion this
section is required to rule out -- a reader skimming category labels could
mistake it for a second instance of family 003's mechanism. "Sizing /
valuation" is the more accurate and more clearly distinguishing label.

## Single-asset vs. portfolio scoping (judgment call, stated explicitly per the task's instruction)

Assessed as a **single-asset family across all 5 core assets** under sec
4.1's standard >=3/5 rule, the VIX signal applied identically and
independently per asset -- directly following the precedent set by
families 006, 007, 011 and 015 (a single external, asset-agnostic
market/macro signal, tested per-asset via the existing single-asset
`engine.py`, not recast as a portfolio-rotation family, since no capital
ever moves between the 5 assets -- each asset's own weekly deposit is
simply resized up or down independently based on the shared VIX regime).
This is the conservative, harder-to-pass choice (no asset's result can
prop up another's, unlike family 010's 2-asset portfolio framing) and
mirrors family 015's own scoping reasoning exactly.

## Data inputs and reachability (gate step, verified before this file was written)

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only,
  same as every prior family).
- **VIX**: `^VIX` (CBOE Volatility Index) via yfinance, confirmed reachable
  in this environment during this family's gate step: 9,253 daily rows,
  **1990-01-02 through today**. Routed through the existing
  `src.backtest.v3.data.fetch_yf_macro(ticker)` helper (added for family
  015, reused here unchanged) -- refuses any ticker already in
  `CORE_TICKERS`/`UNSEEN_TICKERS`, so it cannot become a side-channel
  around the dev/holdout date gate, and keeps the raw-data-leak static
  check's coverage intact. `^VIX` is not in `CORE_TICKERS` or
  `UNSEEN_TICKERS`, so it is accepted.
- **VIX's 1990 start vs. each core asset's own development-period start**
  (explicit judgment call, per the task's instruction): comparing VIX's
  1990-01-02 start against each core asset's own `load_dev()` start date --
  SP500 (1927-12-30), GOLD/SILVER/OIL (2000-08-23/30), BTC (2014-09-17) --
  only **SP500** has any development-period history predating VIX
  (1927-1989, about 68% of SP500's 23,109 development trading days). Gold,
  silver, oil and BTC's development periods all start well after 1990, so
  VIX is available for their entire development windows. For SP500's
  pre-1990 stretch (and for the initial `vix_lookback` window's warm-up
  period on every asset, until enough trailing VIX history exists to
  compute a percentile at all), the elevated/calm signal **defaults to
  calm (`False`, i.e. behaves as plain DCA at `calm_fraction`)** --
  identical to family 001/011/015's own documented warm-up convention.
  This is a substantively large caveat for SP500 specifically (only the
  post-1990, VIX-available 7,308 of its 23,109 development days can ever
  register the "elevated" leg of the mechanism) and is flagged here
  explicitly, not silently absorbed into the warm-up convention.

## Pre-backtest non-degeneracy check (per the task's explicit instruction, following family 015's precedent after family 014's oversight)

Before any backtest, the primary configuration's elevated-VIX-percentile
regime frequency was computed directly against development-window data for
all 5 core assets (causal, trailing `vix_lookback=252`-day percentile rank,
`elevated_pct=90`):

| Asset | VIX-available dev days | Elevated days (>=90th pct) | Frac. of VIX-available days | Frac. of ALL dev days |
|---|---|---|---|---|
| SP500 | 7,308 / 23,109 | 945 | 12.93% | 4.09% |
| GOLD | 4,597 / 4,848 | 536 | 11.66% | 11.06% |
| SILVER | 4,599 / 4,850 | 536 | 11.65% | 11.05% |
| BTC | 1,681 / 1,932 | 190 | 11.30% | 9.83% |
| OIL | 4,606 / 4,857 | 537 | 11.66% | 11.06% |

Every asset's elevated-regime frequency is comfortably non-degenerate
(neither near-0% nor near-100%, both among VIX-available days and as a
share of all development days) -- close to, but not identically, the
nominal 10% implied by a 90th-percentile threshold (a trailing rolling
percentile rank is not exactly stationary at its nominal rate, since the
window itself shifts as new extremes enter/leave it), consistent with a
genuinely mixed, non-degenerate signal rather than a family-014-style
silent no-op. SP500's lower "frac. of ALL dev days" figure (4.09% vs.
~11% for the other four) is expected and explained entirely by its long
pre-1990 VIX-unavailable stretch (documented above), not by the signal
itself being degenerate within its available window.

## Exact rules

Computed at each trading day's close `t`, using only data available by
that close.

1. **VIX series**: daily close of `^VIX` (`data.fetch_yf_macro`),
   reindexed onto the asset's own trading-day calendar with a
   forward-fill (VIX trades on its own calendar, e.g. closed some days BTC
   trades) -- causal only, never filling backward, same pattern as family
   015's DXY alignment.
2. **Trailing percentile rank**: `percentile_t` = the percentage of the
   trailing `vix_lookback` daily VIX closes (through and including day
   `t`, on the aligned/forward-filled series) that are `<=` the VIX close
   on day `t`. `min_periods = vix_lookback` (no signal, i.e. `NaN`, before
   enough history exists).
3. **Elevated-fear flag**: `elevated_t = percentile_t >= elevated_pct`.
   Before `percentile_t` exists (warm-up, or pre-1990 for SP500),
   `elevated_t = False` (defaults to the calm/DCA-like state, matching
   family 001/011/015's convention). No multi-day confirmation is used
   (unlike family 015's `confirm_days`) -- VIX spikes are, by their own
   nature as acute panic episodes, expected to be sharp and short-lived,
   not sustained multi-year trends like a currency regime, so requiring a
   persistence filter would work against the mechanism's own premise and
   was excluded to keep the parameter count at <=5 without diluting the
   signal's intended immediacy.
4. **Weekly decision (week-end days only, no sells ever, no leverage)**:
   - **Elevated fear (`elevated_t = True`):** buy
     `min(cash, buy_multiplier * weekly_deposit, max_buy_multiple *
     weekly_deposit)` -- lean in and buy more, cash-capped by whatever has
     been banked from prior calm weeks plus this week's own deposit, and
     separately capped by the fixed `max_buy_multiple` ceiling so a long
     run of banked cash can never turn into an unbounded lump (mirrors
     family 015's `max_lump_multiple` role).
   - **Calm (`elevated_t = False`):** buy `calm_fraction * weekly_deposit`.
     The remainder, `(1 - calm_fraction) * weekly_deposit`, is banked as
     cash (earning IRX) specifically to fund a future elevated-fear week's
     extra buying -- this is what makes the elevated leg's "buy more" a
     genuine reallocation of the SAME total deposit stream over time, not
     leverage: cash never goes negative (engine's own cap, sec 3.2) and no
     new capital beyond deposits + interest is ever spent.
5. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the VIX/percentile computation entirely and buys
   100% of that week's cash on every week-end day (0 otherwise) --
   reproduces plain DCA bit-for-bit, same pattern as every prior v3
   family's disable path.

## Parameters (4 tunable + 1 fixed, <=5 total, same "4+1" pattern as family 015)

| Parameter | Grid values | Primary |
|---|---|---|
| `vix_lookback` (trailing window, trading days, for the percentile calc) | 252, 504 | 252 |
| `elevated_pct` (percentile threshold for the elevated-fear flag) | 80, 90 | 90 |
| `buy_multiplier` (multiple of the normal weekly deposit bought when elevated) | 1.5, 2.0, 3.0 | 2.0 |
| `calm_fraction` (fraction of deposit bought in calm weeks; remainder banked) | 0.75, 0.9 | 0.9 |

`max_buy_multiple` is fixed at **4.0** for every grid config and the
primary (not grid-varied) -- the ceiling on how large a single elevated
week's buy can ever be relative to the normal weekly deposit, regardless
of how much cash has been banked. Keeps this family at 4 tunable
(grid-varied) parameters plus 1 fixed constant, at/under the plan's <=5
ceiling.

`vix_lookback=252` (one trading year) is primary as the standard "trailing
year" reference window (matching family 003's own `ref_lookback_days=252`
choice for its longer reference window, a no-look convention/comparability
choice, not a development-data result on THIS signal). `elevated_pct=90`
is primary because Whaley's own "fear gauge" framing and the broader
practitioner "VIX spike" literature emphasize genuinely extreme readings
(top decile), not merely above-median vol, as the episodes associated with
overshoot/recovery -- the more literal, higher-conviction reading of the
mechanism, with `elevated_pct=80` in the grid as a looser diagnostic
variant. `buy_multiplier=2.0` (double the normal deposit) is primary as a
clean, easily-explained "buy twice as much" rule -- the middle value of the
3-point grid, not the most aggressive (`3.0`) or the most conservative
(`1.5`) end, chosen for comparability rather than picked to maximize any
observed effect (no development-data result informed this choice; it was
fixed before any backtest was run). `calm_fraction=0.9` is primary as a
light banking rate (90% of every calm week's deposit is still invested
immediately, only 10% diverted to fund future elevated-week buying) --
this keeps the strategy close to ordinary DCA during the ~85-89% of
weeks that are calm, so any measured effect is attributable mainly to the
elevated-week reallocation itself rather than to a large, constant cash
drag from aggressive banking; `calm_fraction=0.75` is the grid's more
aggressive-banking diagnostic variant.

## Grid

2 (`vix_lookback`) x 2 (`elevated_pct`) x 3 (`buy_multiplier`) x 2
(`calm_fraction`) = **24 configurations** (<=36 cap).

## Primary configuration

`vix_lookback=252, elevated_pct=90, buy_multiplier=2.0, calm_fraction=0.9`
(`max_buy_multiple=4.0` fixed for all configs).

## Expected sign

**Positive on both wealth and Sharpe**, if the historical VIX-spike
overshoot/recovery pattern holds up net of the mechanism's own costs: this
family bets that buying extra into elevated cross-market fear captures
better-than-average entry prices often enough to beat constant-size DCA,
across all 5 core assets (the VIX is a broad cross-market fear signal, not
an SP500-specific one, so the directional hypothesis is applied uniformly,
with the least direct literature support for BTC and, to a lesser degree,
industrial-use commodities like oil, silver and gold whose short-run price
action is not purely driven by the same equity-risk-sentiment channel that
prices SP500 options -- flagged here honestly, matching the pattern
families 011/015 used for their own weaker-conviction legs). As with every
prior timing/banking-mechanic family in this loop (004/006/007/010/011/
015), this only reallocates the *timing* of a fixed deposit stream, never
total capital deployed and never leverage, so even a real effect may show
a modest absolute wealth/Sharpe margin over DCA. Per family 010/011/015's
documented precedent, a sec 4.1 pass driven by a small number of dominant
historical panic episodes (e.g. 2008, 2020 -- though 2020 falls mostly in
the holdout for most assets, so only earlier episodes like 1998, 2001-02,
2008-09, 2011, 2015-16, 2018-Q4 are available in development data) is
exactly the kind of few-dominant-episode result the DSR and placebo
circular-shift test (sec 4.3) are designed to catch, and this family's own
results should be read with that precedent in mind before drawing
conclusions from sec 4.1 alone.

## Implementation-check plan (sec 3.2, to be run in the implementation step)

1. `enabled=False` bypass reproduces plain DCA bit-for-bit (units and cash).
2. Cash and positions never negative, for the DCA baseline, the primary
   config, and the grid's most aggressive corner
   (`vix_lookback=252, elevated_pct=80, buy_multiplier=3.0,
   calm_fraction=0.75` -- lowest threshold (most days flagged elevated),
   highest multiplier, most aggressive banking, i.e. the config expected
   to spend cash fastest/hardest).
3. Total capital deployed never exceeds cumulative deposits + interest
   (primary config and the aggressive corner).
4. No-lookahead: perturbing all data after day `t` leaves every order
   on/before `t` unchanged, checked at two spot-check points deep into the
   sample (following family 011/015's precedent of checking more than one
   `t`), with particular attention to the VIX-alignment/ffill step's
   strict causality (only the VIX series' OWN past values, reindexed
   causally onto the asset calendar, ever enter `percentile_t`).
5. Point-in-time macro: N/A in the ALFRED-vintage sense (VIX, like family
   015's DXY, is a daily market-price series with no revision/publication-
   lag concern -- the closing index level is observable same-day) --
   documented explicitly as such rather than silently skipped, matching
   the precedent set by every prior price-only-signal family's "N/A"
   entry for this check.
