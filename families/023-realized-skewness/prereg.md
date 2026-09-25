# Family 023: Realized-skewness sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Neuberger, A. (2012), "Realized Skewness," *Review of Financial Studies*
25(11), 3423-3455; Amaya, D., Christoffersen, P., Jacobs, K. and Vasquez,
A. (2015), "Does Realized Skewness Predict the Cross-Section of Equity
Returns?," *Journal of Financial Economics* 118(1), 135-167. Amaya et al.
compute a realized skewness statistic from an asset's own recent (in their
case, intraday) return series and find it **negatively** predicts the
asset's near-term forward return: stocks with more negatively skewed
recent realized returns earn higher subsequent returns than stocks with
more positively skewed recent realized returns. Seed queue idea #23
(research-loop-plan-v3.md sec 7.3 addendum).

## Mechanism ("why would this work, and who is on the other side?")

Realized skewness is the third standardized moment of an asset's recent
return distribution: negative realized skewness means the recent return
history is dominated by a **few large down days among many small up
days** (a "grinds up, drops hard" shape); positive realized skewness means
the opposite (a "grinds down, spikes up" shape, or occasional sharp rallies
amid otherwise flat/negative drift). The literature's explanation for why
negative skewness predicts *higher* forward returns is a **crash-risk /
negative-skewness-aversion premium**: investors dislike holding assets
whose left tail has recently been demonstrated to be fat (a recent large
down move is salient evidence that another one is possible), so they
demand extra expected compensation to hold or continue holding such an
asset, bidding its price down (and its forward expected return up)
relative to an asset with a similarly volatile but more symmetric or
positively skewed recent history. Lottery-preference literature (e.g.
Bali, Cakici & Whitelaw's MAX effect) documents the mirror image:
investors *overpay* for assets with positively skewed recent
returns (a few big up days) for their lottery-like upside, which
depresses those assets' forward expected returns. A fixed-dollar DCA
buyer invests the same $500 every week regardless of the recent shape of
the return distribution, so this family re-times the SAME total deposit
stream: it buys more, funded from cash banked during positively-skewed
weeks, specifically while the asset's trailing realized skewness is
negative (elevated crash-risk-premium regime), and buys a reduced share
while trailing skewness is positive (a crowded, lottery-priced regime) --
no leverage, no borrowing, average capital committed over time unchanged.
The "other side" of this trade is the lottery-seeking / lottery-averse
investors identified in that literature: this family systematically buys
into the discount left by investors who have just sold off a recently
scary (negatively skewed) asset, and buys less of an asset that lottery-
preference investors have just bid up after a recent run of sharp upside
days.

## Category

**Sizing / valuation.**

## Exact rules

1. Daily return: `r_t = Close_t / Close_{t-1} - 1`.
2. Trailing realized skewness (causal, `skew_window` trading days,
   including day `t`), using the literature's standard **realized
   skewness** formula (Neuberger 2012; Amaya et al. 2015's daily-return
   adaptation of the intraday formula -- an un-demeaned, scale-invariant
   third-moment statistic, not the textbook demeaned sample-skewness
   formula):

   `RSkew_t = sqrt(skew_window) * sum(r_i^3, i in window) /
              (sum(r_i^2, i in window))^1.5`

   Undefined (treated as neutral / "not triggered") until `skew_window`
   trading days of return history exist, and on the negligible-probability
   case `sum(r_i^2) == 0` (all-zero returns in the window).
3. **Regime** on day `t` (three-way, evaluated only on each week's last
   trading day, matching families 003/005/016/017/021's weekly-decision
   cadence):
   - **Negative-skew regime**: `RSkew_t < neg_threshold` (`neg_threshold`
     is negative). Buy `min(cash, buy_multiplier * weekly_deposit,
     max_buy_multiple * weekly_deposit)`.
   - **Positive-skew regime**: `RSkew_t > pos_threshold` (`pos_threshold`
     is positive). Buy `reduce_fraction * weekly_deposit`, banking the
     `(1 - reduce_fraction)` remainder as cash (earning IRX) to fund later
     negative-skew-regime buying.
   - **Neutral** (`neg_threshold <= RSkew_t <= pos_threshold`): buy exactly
     `weekly_deposit` (plain DCA for that week -- no boost, no banking).
   - Never a sell. No leverage, no borrowing -- `buy_usd` is always
     cash-capped by the engine itself (sec 3.2), so a negative-skew week
     with insufficient banked cash simply buys what's available.

Thresholds are **fixed values directly on the `RSkew_t` statistic**
(the "fixed sign-based threshold" option named in this iteration's task
instruction), not a further trailing percentile rank of `RSkew_t` itself
-- chosen because `RSkew_t`'s formula is already scale-invariant in
return magnitude (normalized by `sum(r_i^2)^1.5`) and depends on
`skew_window` only through the `sqrt(skew_window)` sampling-noise
correction, so a fixed threshold is meaningful across the two window
choices in the grid without needing an extra ranking lookback (which
would have pushed this family over the 5-parameter cap). The pre-grid
non-degeneracy sanity check below is the concrete test that this choice
does not produce a degenerate (near-0% or near-100%) trigger rate on any
asset; if it did, the fixed-threshold design would need to be revisited
before trusting the grid.

## Parameters (5, all tunable; `max_buy_multiple` fixed, not grid-varied, same convention as family 021)

| Param | Meaning | Grid values |
|---|---|---|
| `skew_window` | Trailing window (trading days) for `RSkew_t` | 60, 90 |
| `neg_threshold` | `RSkew_t` cutoff below which the negative-skew (boost) regime triggers | -0.5, -0.25 |
| `pos_threshold` | `RSkew_t` cutoff above which the positive-skew (reduce) regime triggers | 0.25, 0.5 |
| `buy_multiplier` | Multiple of `weekly_deposit` bought on a negative-skew week-end (cash-capped) | 1.5, 2.0 |
| `reduce_fraction` | Fraction of `weekly_deposit` bought on a positive-skew week-end (remainder banked) | 0.85, 0.95 |
| `max_buy_multiple` (fixed) | Hard ceiling on any single week's buy relative to `weekly_deposit` | 4.0 |

Grid: 2 x 2 x 2 x 2 x 2 = **32 configurations** (<=36 cap; 5 tunable
parameters, at the sec 3.4 ceiling).

## Primary configuration

`skew_window=90, neg_threshold=-0.5, pos_threshold=0.5, buy_multiplier=2.0,
reduce_fraction=0.85` (`max_buy_multiple=4.0` fixed). The wider, more
conservative thresholds (0.5 rather than 0.25) are chosen as primary to
target genuinely elevated/depressed skewness episodes rather than routine
noise, consistent with the literature's own use of extreme-decile sorts
rather than near-median splits.

## Expected sign of the effect

Beats DCA on final wealth AND Sharpe: buying more during negative-realized-
skewness episodes (funded from a reserve banked during positive-skewness
episodes) is expected to capture, on average, the crash-risk /
negative-skewness-aversion premium Amaya et al. (2015) document, the same
total deposit stream re-timed rather than increased.

## Required triple distinction from families 003, 016 and 017 (this iteration's task instruction)

All four families size buys using a statistic derived from an asset's own
(or a shared) recent return/price behavior, so the distinction must be
made explicit and precise, exactly as the task requires:

- **Family 003 (vol-managed sizing):** sizes inversely to each asset's own
  trailing **realized VARIANCE** -- the **second** standardized moment of
  returns, a pure measure of dispersion with no directional/asymmetry
  information at all (a return series and its exact sign-flipped mirror
  image have identical realized variance). This family (023) uses
  **realized SKEWNESS** -- the **third** standardized moment, which
  measures asymmetry specifically: a series and its sign-flipped mirror
  have equal-magnitude but opposite-signed skewness. These are
  fundamentally different statistics computed from the same raw return
  series but capturing unrelated properties of its shape (spread vs.
  asymmetry), and family 003's direction-agnostic "buy more when calm"
  rule is not even directionally comparable to this family's "buy more
  specifically when the recent shape has been left-skewed" rule.
- **Family 016 (VIX contrarian):** sizes using a single, **forward-
  looking, option-IMPLIED volatility LEVEL** from one shared market-wide
  index (`^VIX`), applied identically to all 5 assets regardless of each
  asset's own trading history -- a cross-sectional, options-market input
  with no per-asset computation at all. This family (023) is strictly
  **backward-looking**: `RSkew_t` is computed entirely from each asset's
  **own trailing daily-return series**, with no options data, no implied
  expectations, and no shared cross-asset input whatsoever. The two
  differ on every one of: data source (options-implied vs. realized
  price-history), asset scope (one shared index vs. per-asset
  computation), and statistical moment (a volatility *level*, not even
  a standardized moment, vs. a third standardized moment).
- **Family 017 (RSI2 mean-reversion):** a bounded **0-100 oscillator**
  computed from the short-horizon **ratio of average gains to average
  losses in price LEVELS** (a relative-strength construction, not a
  moment of a return distribution at all) over a short window (2-day
  lookback, by construction of RSI-2). This family (023) computes an
  **unbounded statistical moment (skewness) of RETURNS**, not price
  levels, over a materially longer window (60-90 trading days vs. RSI-2's
  2-day span). The economic story also differs completely: RSI-2 is a
  short-term, mechanical price-level mean-reversion signal (an
  overbought/oversold oscillator with no risk-premium interpretation),
  while this family is a risk-premium-for-crash-risk story with an
  explicit asset-pricing citation (Amaya et al. 2015) tied to the third
  moment specifically, not to price-level extremes.

In short: 003 is a **2nd-moment, direction-agnostic dispersion signal**;
016 is a **shared, forward-looking, options-derived volatility level**;
017 is a **bounded, short-horizon price-level oscillator with no moment
interpretation**; 023 is an **asset-own, backward-looking, unbounded 3rd-
moment (asymmetry) signal on returns**, the only one of the four that
uses skewness, or any measure of return asymmetry, at all. Not a re-test
of sec 7.2's closed list either (v1's ATR-shock Signal A and trend-
stretch Signal B are both price-level constructions with no
distribution-shape/moment computation).

## Data prerequisite

Price-only (Close), already cached for all 5 core assets in `data/*.csv`
-- no new data source, no Volume, no macro/FRED dependency. Feasibility is
not a novel question for this family (unlike families 008/009/012/021).

## Design scope: single-asset family across all 5 core assets

Following the standard precedent (families 001/003/005/014/017/020/021):
an asset-agnostic, per-asset internal signal, assessed under sec 4.1's
standard >=3/5-core-assets rule.

## Pre-grid non-degeneracy sanity check (to be run before the full grid, per the established convention)

Before trusting the grid, confirm the primary config's negative-skew and
positive-skew triggers each fire non-trivially (not near-0%, not
near-100%) on every asset -- the concrete test for whether the
fixed-threshold design (rather than a trailing percentile rank) produces
a degenerate signal on any asset. Requires each asset's fraction of
week-end decision days flagged "negative-skew regime" to fall strictly
between 2% and 60%, and likewise for "positive-skew regime" (independently
-- the two regimes are mutually exclusive by construction of the
thresholds, so their sum is also implicitly bounded below 100%, with the
remainder neutral).

## Implementation checks to run (sec 3.2, before any grid result is trusted)

1. `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash).
2. Cash and positions never negative, for the DCA baseline, the primary
   config, and the grid's most aggressive corner (`skew_window=60,
   neg_threshold=-0.25, pos_threshold=0.25, buy_multiplier=2.0,
   reduce_fraction=0.85` -- the narrowest thresholds combined with the
   shortest window and largest multiplier/banking, expected to trigger the
   negative-skew boost most often and drain the reserve hardest).
3. Capital deployed never exceeds cumulative deposits + interest, for the
   primary config and the aggressive corner, using family 021's
   principled-bound method (a "never invest" reference run on the same
   `daily_rf` path gives the maximum interest any cash trajectory could
   have earned; capital deployed minus cumulative deposits must never
   exceed that ceiling), not a flat percentage tolerance.
4. No-lookahead: perturbing all data after day `t` leaves every order
   on/before `t` unchanged, spot-checked at two points deep into
   development history -- this must specifically exercise the `RSkew_t`
   computation's strict causality (it must use only `r_i` for `i <= t`,
   never any future return).
5. Point-in-time macro: N/A -- price-only signal, no macro/FRED
   dependency.

## Files (to be produced by the implementation/run step)

- `src/backtest/v3/strategies/realized_skewness.py`
- `scripts/v3/run_023_realized_skewness.py`
- `families/023-realized-skewness/grid_results.csv`,
  `_primary_per_asset.csv`, `_run_output.json`
- `state/trials/new_023_*.csv`
