# Family 025: Variance risk premium (VRP) sizing

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Bekaert, G. & Hoerova, M. (2014), "The VIX, the Variance Premium and Stock
Market Volatility," *Journal of Econometrics* 183(2) -- decomposes the VIX
into an expected-variance component and a variance-risk-premium component,
and shows the VRP (elevated vs. compressed) carries forward information
about equity risk-adjusted returns distinct from the VIX level itself.
Carr, P. & Wu, L. (2009), "Variance Risk Premia," *Review of Financial
Studies* 22(3) -- the foundational formalization of the variance risk
premium as the spread/ratio between risk-neutral (implied) and
physical-measure (realized) variance, and its predictive content for
forward equity index returns. Seed research queue idea #25
(research-loop-plan-v3.md sec 7.3 addendum, this iteration's task):
"Variance risk premium (VRP) sizing."

## Mechanism ("why would this work, and who is on the other side?")

The VRP is the compensation investors demand, embedded in options prices,
for bearing variance risk -- the spread between the market's forward-looking,
option-implied volatility (VIX) and the volatility that actually realizes
subsequently (or, as implemented causally here, the volatility that has
*just* realized, trailing). A positive, elevated VRP means implied vol is
running well above trailing realized vol: option sellers/variance-swap
sellers are being paid an unusually rich premium relative to what recent
turbulence alone would justify. In the VRP literature this elevated spread
has historically been associated with *better* subsequent risk-adjusted
returns for risk-bearing capital generally (Bekaert & Hoerova 2014; Carr &
Wu 2009) -- richer insurance pricing tends to coincide with periods where
taking on risk is comparatively well compensated, whether because
uncertainty aversion is temporarily overpriced relative to realized
outcomes, or because dealers/option writers have bid up the price of
crash protection beyond what trailing realized turbulence alone would
justify. Buying more into an elevated VRP is a bet on capturing that
compensation. The "other side" is the demand for portfolio insurance
itself -- institutions and levered players who are structurally willing to
overpay (in variance-swap/options terms) for downside protection
regardless of trailing realized outcomes, especially after a scare, and
whose persistent hedging demand is the standard explanation (in this
literature) for why the VRP is usually positive on average and often
richest precisely when realized turbulence has not (yet) caught up to
implied fear. This family's investor is being compensated, on average
and net of costs, for stepping in on the other side of that structural
hedging demand specifically when it is priced richest relative to recent
realized experience -- not simply whenever implied vol alone is elevated
(that is family 016's bet) and not whenever realized vol alone is elevated
or depressed (that is family 003's bet).

## Category

**Volatility targeting** (sec 4.5's list). Unlike family 016 (filed under
"Sizing / valuation" specifically because a single discrete fear-level
threshold on VIX alone, divorced from any realized-vol reference, was
judged closer to a valuation/mean-reversion bet than a variance-management
rule -- see family 016's prereg.md category-justification section), this
family's signal is explicitly the **relationship between two volatility
measures** (implied vs. realized) -- the defining shape of a volatility-
targeting/variance-premium rule in the literature (Bekaert & Hoerova 2014;
Carr & Wu 2009 both frame the VRP as a variance-management/risk-premium
quantity, not a standalone valuation signal), even though, like family
016, its trigger is a discrete threshold rather than a continuous dial.
"Volatility targeting" is the correct fit specifically because the
comparison itself (a spread of two vol measures) is the mechanism, not
merely a threshold on one number.

## Rigorous distinction from families 003 and 016 (required by this iteration's task)

Three families now use some notion of "volatility" to size buys. The
distinction must be explicit, load-bearing and numerically demonstrated,
not cosmetic.

| | Family 003 (vol-managed sizing) | Family 016 (VIX contrarian) | Family 025 (VRP sizing, this family) |
|---|---|---|---|
| **Signal** | Each asset's own **realized** vol alone (`sigma_ref/sigma_recent` ratio, both realized, both from the asset's own price history). No implied-vol component at all. | The **VIX level** alone, in its own trailing percentile. No realized-vol comparison at all -- a single number, not a spread. | The **spread** `VRP_t = IV_t - RV_t` (VIX minus the asset's own trailing realized vol), in the SPREAD's own trailing percentile. Neither implied nor realized vol alone -- their difference. |
| **Inputs used** | 1 quantity (realized vol, 2 windows of it). | 1 quantity (VIX). | 2 quantities compared against each other (VIX **and** the asset's own realized vol) -- a genuinely different, higher-order construction than either predecessor. |
| **Sign** | Inverse: high (own) realized vol => buy LESS. | Direct: high VIX (own percentile) => buy MORE. | Direct on the SPREAD: high VRP (implied running well above realized) => buy MORE; compressed/negative VRP => buy LESS/normal -- but this is a distinct trigger condition from family 016's, demonstrated numerically below. |
| **Nests either predecessor?** | N/A (baseline). | N/A (baseline). | No. `VRP_t` cannot be recovered from `RV_t` alone (family 003's input) or from `IV_t` alone (family 016's input) without the other term -- neither family's signal is a special case of this family's, nor vice versa, under any parameter setting. |

### The required numeric contrast: VIX-elevated does NOT imply VRP-elevated

Family 016 flags "buy more" whenever VIX alone is in an elevated trailing
percentile, regardless of what realized vol is doing. This family flags
"buy more" only when the *spread* IV−RV is in an elevated trailing
percentile. These diverge whenever realized vol moves in the same
direction as implied vol -- exactly the scenario this section is required
to make concrete:

- **Scenario A -- a live crisis where realized vol has caught up to implied
  (a "VIX elevated, VRP compressed" week):** suppose VIX = 25 (comfortably
  in its own top decile for a given period) and trailing realized vol on
  an asset has also risen sharply to 24 (a genuinely choppy, whipsawing
  realized tape, not a calm one). `VRP_t = 25 - 24 = 1` vol point --
  compressed relative to a "normal" VRP of roughly 4-6 points typically
  seen in calmer regimes (a standard stylized fact: VIX usually runs a
  few points above trailing realized vol on average). Family 016 reads
  this week as **"elevated fear -> buy more."** This family reads the
  *same* week as **"VRP compressed -> buy less/normal"** (realized
  turbulence has essentially caught up with implied fear, so there is no
  longer an unusually rich premium being paid relative to what recent
  experience justifies). Opposite sizing decisions from the same VIX
  print.
- **Scenario B -- a deceptively calm week with an unusually rich spread (a
  "VIX not elevated, VRP elevated" week):** suppose VIX = 15 (not in its
  own top percentile -- family 016 reads this as calm, normal-size buy)
  but trailing realized vol has been unusually quiet, at 6 (well below its
  own typical level). `VRP_t = 15 - 6 = 9` vol points -- well above the
  "normal" 4-6 range, likely landing in ITS OWN elevated trailing
  percentile even though the VIX print itself is unremarkable. This
  family reads this week as **"VRP elevated -> buy more,"** while family
  016 would size this week as an ordinary calm-fraction week. Again,
  opposite (or at least differing) sizing decisions from the same VIX
  print, this time driven entirely by the realized-vol leg that family
  016 never looks at.

Both scenarios are structurally possible under this family's rules (§
"Exact rules" below) precisely because `elevated_t`/`compressed_t` are
computed on the **spread's own trailing percentile distribution**, not on
VIX's trailing percentile distribution (family 016's signal) or on
realized vol's trailing ratio-to-reference (family 003's signal). The
implementation step's pre-grid sanity check (below) additionally verifies
empirically, on real development data, that this family's elevated/
compressed flags do NOT coincide with family 016's elevated-VIX flag on
every date (a mechanical, disconfirmable check that the spread logic, not
an accidental collapse to VIX-alone, is what is actually implemented).

## Single-asset vs. portfolio scoping

Assessed as a **single-asset family across all 5 core assets** under sec
4.1's standard >=3/5 rule, directly following family 016's own scoping
precedent (a shared external implied-vol signal, VIX, compared against
each asset's OWN realized vol -- so unlike family 016's signal, this one
is not fully shared across assets: the realized-vol leg is asset-specific,
even though the implied-vol leg is the shared SP500-derived VIX). No
capital ever moves between the 5 assets; each asset's own weekly deposit
is resized independently based on that asset's own VRP state.

## Data inputs and reachability (gate step)

- Each asset's own daily OHLC (`src.backtest.v3.data.load_dev()` only).
- **VIX** (`^VIX`) via `src.backtest.v3.data.fetch_yf_macro()`, the same
  helper and same reachability already confirmed for family 016: 9,253
  daily rows, 1990-01-02 through today. Re-verified reachable at this
  family's gate step (unchanged helper, no new network dependency).
- **Realized volatility**: computed directly from each asset's own OHLC
  close, using the SAME rolling-log-return-stdev calculation already
  implemented and tested in family 003's `compute_multiplier()`
  (`src/backtest/v3/strategies/vol_managed_sizing.py`) -- reused/adapted
  here (annualized `%` units to match VIX's own quoting convention,
  `sigma * 100` instead of family 003's raw decimal ratio), not
  reimplemented from scratch, per the task's explicit instruction to
  check family 003's file for reuse.
- **Cross-asset proxy acknowledgment (same choice family 016 already made
  and justified):** VIX is SP500-option-implied volatility specifically.
  Using it as the implied-vol leg of `VRP_t` for gold, silver, BTC and oil
  is a cross-asset proxy -- there is no free, point-in-time-reachable
  implied-vol index for those 4 assets individually in this environment
  (no free GVZ/OVX-equivalent history was located with the reachability
  this loop requires; if one becomes available in a future iteration it
  would be a materially different family, not a retune of this one). This
  mirrors family 016's own explicit acknowledgment of the identical
  limitation and is accepted on the same grounds: VIX is nonetheless the
  best free, reliable, long-history proxy for "aggregate market-implied
  fear" available, and the resulting spread is at minimum an economically
  interpretable comparison of a cross-market implied-vol level against
  each asset's own realized turbulence, if not a literally asset-native
  VRP.

### VIX's 1990 start vs. each core asset's development period (same limitation as family 016, same handling)

Identical to family 016's own documented judgment call: only **SP500**
(dev history from 1927-12-30) has development history predating VIX's
1990-01-02 start (about 68% of its 23,109 development trading days).
GOLD/SILVER/OIL (dev start 2000-08) and BTC (dev start 2014-09) are fully
covered by VIX's 1990+ history. Per the established warm-up convention
(families 001/011/015/016), `elevated_t` and `compressed_t` both default
to **False** (i.e., the normal/calm-fraction leg) whenever `VRP_t`'s
trailing percentile can't yet be computed -- both during the initial
`vrp_lookback`-day warm-up on every asset, and for SP500's entire
pre-1990 stretch (compounded here by also needing `rv_lookback` days of
the asset's own realized-vol warm-up, so the earliest possible signal date
is `max(VIX availability, rv_lookback warm-up, vrp_lookback warm-up)` on
each asset's own calendar). This is flagged explicitly, exactly as family
016 flagged it, rather than silently absorbed into the generic warm-up
convention.

## Exact rules

Computed at each trading day's close `t`, using only data available by
that close.

1. **Implied-vol leg**: `IV_t` = daily close of `^VIX`
   (`data.fetch_yf_macro`), reindexed onto the asset's own trading-day
   calendar with a causal forward-fill only (never backward) -- identical
   alignment method to family 016's `_aligned_vix_close()`.
2. **Realized-vol leg**: `RV_t` = trailing `rv_lookback`-day rolling
   standard deviation of the asset's own daily log returns, annualized
   (`* sqrt(252) * 100`, expressed in the same "vol points" units as
   VIX), `min_periods = rv_lookback` -- the identical rolling-stdev
   calculation used in family 003's `compute_multiplier()`, re-expressed
   in percentage-point units for direct comparability with `IV_t`.
3. **VRP**: `VRP_t = IV_t - RV_t` (a spread in vol points; can be
   negative if trailing realized vol has run above the VIX print).
4. **Trailing percentile rank of the SPREAD itself** (NOT of `IV_t` alone
   and NOT of `RV_t` alone): `percentile_t` = the percentage of the
   trailing `vrp_lookback` daily `VRP` values (through and including day
   `t`) that are `<=` `VRP_t`. `min_periods = vrp_lookback`.
5. **Regime flags**:
   - `elevated_t = percentile_t >= elevated_pct` (VRP unusually wide --
     implied running well above realized -- buy MORE).
   - `compressed_t = percentile_t <= compressed_pct` (VRP unusually thin
     or negative -- realized has caught up with or exceeded implied --
     buy LESS).
   - Otherwise, `normal_t` (neither elevated nor compressed).
   - Before `percentile_t` exists (warm-up, or pre-1990 for SP500):
     defaults to `normal_t` (calm-fraction leg), matching the established
     convention.
6. **Weekly decision (week-end days only, no sells ever, no leverage)**:
   - **Elevated (`elevated_t`):** buy `min(cash, buy_multiplier *
     weekly_deposit, max_buy_multiple * weekly_deposit)`.
   - **Compressed (`compressed_t`):** buy `compressed_fraction *
     weekly_deposit` (fixed at 0.5 -- buy noticeably less, not zero, to
     stay a reallocation-of-timing rule and avoid an implicit "always
     skip compressed weeks entirely" degenerate shape). The remainder,
     `(1 - compressed_fraction) * weekly_deposit`, is banked as cash
     (earning IRX).
   - **Normal (neither):** buy `calm_fraction * weekly_deposit` (fixed at
     0.9, matching family 016's calm-week banking rate). The remainder is
     banked as cash.
   - This is a genuine reallocation of the SAME total deposit stream over
     time, never leverage: cash never goes negative (engine's own cap,
     sec 3.2) and no capital beyond deposits + interest is ever spent.
7. **Degenerate case** (`enabled=False`, implementation check only, not a
   grid arm): bypasses the VRP/percentile computation entirely and buys
   100% of that week's cash on every week-end day (0 otherwise) --
   reproduces plain DCA bit-for-bit.

## Parameters (4 tunable + 3 fixed, <=5 tunable)

| Parameter | Grid values | Primary |
|---|---|---|
| `rv_lookback` (trailing window, trading days, for the realized-vol leg) | 20, 60, 120 | 60 |
| `elevated_pct` (percentile threshold on the VRP spread for "elevated") | 80, 90 | 90 |
| `compressed_pct` (percentile threshold on the VRP spread for "compressed") | 10, 20 | 10 |
| `buy_multiplier` (multiple of weekly deposit bought when elevated) | 1.5, 2.0, 3.0 | 2.0 |

Fixed (not grid-varied, do not count against the <=5 tunable-parameter
ceiling): `vrp_lookback = 252` (one trading year, the trailing window over
which the VRP spread's own percentile is ranked -- matches family 016's
`vix_lookback=252` primary as a no-look "trailing year" convention, chosen
before any backtest, not fit to this signal), `max_buy_multiple = 4.0`
(hard ceiling on any elevated week's buy relative to the normal deposit,
identical role to family 016's fixed constant), `compressed_fraction =
0.5` and `calm_fraction = 0.9` (fixed banking rates for the compressed and
normal legs respectively, chosen before any backtest for the same
comparability reasons family 016 gave for its own fixed `calm_fraction`).

`rv_lookback=60` is primary, matching family 003's own primary
`vol_lookback_days=60` choice (a no-look comparability convention, not a
development-data result on THIS signal) -- the middle value of the
3-point grid. `elevated_pct=90` / `compressed_pct=10` are primary as the
symmetric, literal top-decile/bottom-decile reading of "genuinely elevated"
vs. "genuinely compressed" VRP, mirroring family 016's `elevated_pct=90`
choice and its stated rationale (extreme readings, not merely
above/below-median, are what the literature associates with a real
premium effect) applied symmetrically to both tails of the spread.
`buy_multiplier=2.0` is primary for the same reason it was primary in
family 016: a clean, easily explained "buy twice as much," the middle of
the 3-point grid, not the most aggressive or most conservative end, fixed
before any backtest was run.

## Grid

3 (`rv_lookback`) x 2 (`elevated_pct`) x 2 (`compressed_pct`) x 3
(`buy_multiplier`) = **36 configurations** (at the <=36 cap).

## Primary configuration

`rv_lookback=60, elevated_pct=90, compressed_pct=10, buy_multiplier=2.0`
(`vrp_lookback=252`, `max_buy_multiple=4.0`, `compressed_fraction=0.5`,
`calm_fraction=0.9` fixed for all configs).

## Expected sign

**Positive on both wealth and Sharpe**, if the VRP literature's forward-
return association holds up net of the mechanism's own costs: buying more
specifically when the spread between implied and realized vol is
unusually rich (not merely when implied vol alone is high, and not merely
when realized vol alone is low) should capture a genuine risk-premium
effect that neither family 003 nor family 016 isolates on its own. As with
every prior timing/banking-mechanic family in this loop, this only
reallocates the *timing* of a fixed deposit stream, never total capital
deployed and never leverage. Weakest expected conviction for BTC and, to a
lesser degree, the non-financial commodities (silver, oil), whose
short-run realized vol is not driven by the same SP500-option-priced fear
channel that the VRP literature was built on -- flagged honestly, per the
pattern families 011/015/016 already used for their own weaker-conviction
legs. Per family 016's own documented precedent, a sec 4.1 pass driven by
a small number of dominant historical episodes is exactly what sec 4.3's
placebo circular-shift and bootstrap tests are designed to catch, and this
family's results should be read with that precedent in mind before drawing
conclusions from sec 4.1 alone.

## Implementation-check plan (sec 3.2, to be run in the implementation step)

1. `enabled=False` bypass reproduces plain DCA bit-for-bit (units and cash).
2. Cash and positions never negative, for the DCA baseline, the primary
   config, and the grid's most aggressive corner (`rv_lookback=20,
   elevated_pct=80, compressed_pct=20, buy_multiplier=3.0` -- shortest
   realized-vol window (noisiest, most trigger-happy spread), loosest
   elevated/compressed thresholds (most days flagged into a non-normal
   regime), highest multiplier -- the config expected to spend cash
   fastest/hardest).
3. Total capital deployed never exceeds cumulative deposits + interest
   (primary config and the aggressive corner), via family 021's
   principled "never invest" ceiling-bound method.
4. No-lookahead: perturbing all data after day `t` leaves every order
   on/before `t` unchanged, checked at two spot-check points deep into
   the sample, with particular attention to BOTH the VIX-alignment/ffill
   step's strict causality AND the realized-vol rolling-window's strict
   causality (neither leg may use any data beyond day `t`).
5. Point-in-time macro: N/A in the ALFRED-vintage sense (VIX is a daily
   market-price series with no revision/publication-lag concern, same as
   family 016's documented "N/A" for its own VIX dependency) -- documented
   explicitly, not silently skipped.
6. **Pre-grid non-degeneracy AND distinctness-from-016 sanity check**
   (required by this iteration's task, before the full grid runs): compute
   the primary config's `elevated_t`/`compressed_t` regime frequencies
   directly on development data for all 5 core assets (must be
   non-trivial: not near-0%, not near-100%), AND cross-tabulate this
   family's `elevated_t` flag against family 016's own primary-config
   `elevated_t` flag (recomputed on the same dates) to confirm they do
   NOT coincide on every date -- i.e., that this family's spread logic is
   mechanically distinct from family 016's VIX-alone logic on real data,
   not merely by prereg-text argument.

## Files (to be created in the implementation/run step)

- `src/backtest/v3/strategies/vrp_sizing.py`
- `scripts/v3/run_025_vrp_sizing.py`
- `families/025-vrp-sizing/results.md`, `grid_results.csv`,
  `_primary_per_asset.csv`, `_run_output.json`
- `state/trials/new_025_*.csv` (36 files)
