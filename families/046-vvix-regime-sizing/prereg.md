# Family 046 pre-registration: VVIX vol-of-vol regime sizing

**Idea source:** research queue #47. Literature: Huang, Schlag, Shaliastovich
& Thornton (2019), "Volatility-of-Volatility Risk," *Journal of Financial
and Quantitative Economics* (VVIX as a priced, second-order risk factor
distinct from VIX-level exposure); CBOE VVIX Index white paper (CBOE,
2012) (methodology: VVIX is the VIX-methodology-style 30-day
implied-volatility index computed from OUT-OF-THE-MONEY OPTIONS ON VIX
FUTURES/VIX itself, i.e. it measures the market's expectation of how
volatile the VIX INDEX will be over the next 30 days -- a genuinely
different underlying quantity than VIX, which measures the market's
expectation of how volatile the S&P 500 will be); Park (2015), "Variance
disparity and market volatility," and related vol-of-vol literature
associating VVIX spikes with elevated systemic tail-risk pricing and
subsequent equity-market instability.

## Mechanism ("why would this work, and who is on the other side?")

VVIX is the CBOE's implied-volatility index computed from options ON VIX
(or VIX futures), not on the S&P 500 directly. It measures the market's
priced expectation of how much the VIX INDEX ITSELF will move over the
next 30 days -- a second-order ("vol-of-vol") uncertainty measure, distinct
from VIX's own level (first-order: expected S&P 500 volatility). A
trader can hold a strong view on where volatility is heading (low VIX,
calm equity market) while simultaneously facing large uncertainty about
HOW STABLE that calm regime itself is -- i.e. VIX can be moderate while
VVIX is elevated, which the literature (Huang et al. 2019; CBOE 2012)
reads as the market pricing in an elevated probability of a near-term
volatility SHOCK (a jump in VIX itself), even though the current
volatility level has not yet moved. This is fundamentally a forward-
looking, second-derivative signal about market fragility, not a
statement about the currently-realized or currently-implied level of
equity volatility.

**Sign decision (task instruction: "test the sign carefully"):** two
candidate framings exist in this loop's own precedent:

1. **Contrarian-buy-into-fear** (family 016's VIX-level framing): the
   volatility event has ALREADY happened (VIX is elevated NOW), so buying
   more captures a mean-reversion/rebound opportunity in the underlying
   asset once the acute fear passes.
2. **Risk-off/defensive-bank** (families 011/019/027/032's credit- and
   macro-stress framing): the signal is a LEADING indicator of upcoming
   instability that has not yet fully materialized in the asset's own
   price action, so banking cash ahead of it is the more principled
   response.

VVIX fits framing 2, not framing 1. Unlike VIX itself (which IS the
market's currently-priced fear level -- by the time VIX is elevated, the
equity selloff that family 016 exploits is typically already underway),
VVIX prices uncertainty ABOUT THE FUTURE PATH OF VIX. Empirically and by
construction, VVIX often leads or coincides with the ONSET of vol
instability rather than its peak (see the concrete divergence example
below: Dec 2014, VVIX spiked to its 97.8th trailing percentile while VIX
sat at a moderate 18.5, well before the Jan-Feb 2015 spike in realized
market stress; VVIX in that episode functioned as an early-warning signal
of fragility, not a signal that a rebound opportunity had already
arrived). This family therefore adopts the **risk-off/defensive-bank
sign**: elevated VVIX percentile -> buy LESS (bank a reserve, waiting for
the uncertainty to resolve); depressed VVIX percentile -> buy MORE
(deploy normally/aggressively in a genuinely calm, low-meta-uncertainty
regime). This is the same inverted-continuous-percentile functional form
family 045 already uses (for an unrelated cross-asset-correlation
signal), applied here to a different, single-external-series input.

**Who is on the other side?** Investors who treat VIX itself as the only
volatility signal worth watching are, by construction, blind to a
regime where the currently-quoted volatility level is calm but the
market's own uncertainty about how long that calm will last is
elevated -- exactly the gap this family's signal targets. If VVIX-implied
fragility genuinely precedes VIX spikes (rather than being pure noise),
a DCA investor who mechanically buys through that lead time is buying
into an unpriced-yet risk that this strategy defers instead.

## Data feasibility (checked first, per task instruction)

`yf.Ticker('^VVIX').history(period='max', auto_adjust=False)` returns
**4,955 daily rows**, from **2007-01-03** through the present (checked
2026-09-26; reachable via yfinance, routed through
`v3data.fetch_yf_macro('^VVIX')` exactly like family 041's `^VIX3M`).

Comparison of development-period (pre-2020-01-01) history across this
loop's volatility-index signals:

| Series | Start | Dev-period length (to 2019-12-31) | Used by |
|---|---|---|---|
| `^VIX` | 1990-01-02 | ~30.0 years | families 016, 025 |
| `^VIX3M` | 2006-07-17 | ~13.4 years | family 041 |
| `^VVIX` | 2007-01-03 | ~13.0 years | this family |

VVIX's dev-period history (~13.0 years, 3,270 trading days through
2019-12-31) is essentially IDENTICAL in length to `^VIX3M`'s (~13.4
years), which family 041 already found adequate for a full-grid,
36-configuration family (finishing near-miss, not infeasible). VVIX is
therefore judged **feasible**, on the same basis. This is materially
shorter than plain VIX's own ~30-year history, so — like family 041 — the
signal is undefined (falls back to neutral, `m_t=1.0`, bit-for-bit DCA)
for any day before 2007-01-03, on every core asset (this affects only
SP500, whose own dev history goes back to 1927; GOLD/SILVER/OIL start in
2000, BTC in 2014, all already after VVIX's own start).

## Required distinction from families 016, 025 and 041 (concrete, not just asserted)

All four signals ultimately derive from CBOE VIX-family option-implied
data, so the burden here is unusually high. Each of the three prior
families measures a genuinely different quantity than VVIX:

- **Family 016** (VIX contrarian): uses `VIX_t` itself — the
  FIRST-order level of implied S&P-500 volatility.
- **Family 025** (VRP sizing): uses `VIX_t - RV_t`, a SPREAD between
  implied and each asset's own realized volatility — still first-order
  (both legs are volatility LEVELS of the underlying asset, not
  volatility of an index).
- **Family 041** (VIX term-structure carry): uses `VIX3M_t / VIX_t`, a
  RATIO between two different TENORS of implied vol on the SAME
  underlying (the S&P 500) — a curve-slope/term-structure statistic,
  still first-order.
- **This family (046)**: uses `VVIX_t` — the market's implied volatility
  of VIX ITSELF, a genuinely SECOND-order quantity. It answers "how much
  will expected-S&P-500-volatility move around?", not "how high is
  expected S&P-500-volatility right now?" or "what is its term
  structure?". VVIX can be high while VIX is moderate (elevated
  uncertainty about a still-calm regime) or VVIX can be low while VIX is
  high (a volatility spike that the market is confident will persist or
  fade in a predictable, low-vol-of-vol way) — a decoupling none of
  016/025/041's own statistics can produce, since all three are
  functions of VIX/VIX3M/realized-vol LEVELS alone.

**Concrete real-data divergence example (dev-period, pre-2020, verified
live before any design work; not a hand-picked date from unseen data):**

Using `^VIX` and `^VVIX` daily closes over 2007-01-03..2019-12-31
(3,270 overlapping days), the raw correlation between the two series'
LEVELS is only **+0.264** — a weak positive relationship confirming they
carry substantially different information, not a relabeling of the same
quantity.

- **VIX moderate, VVIX elevated (the decoupling case):** on **2014-12-10**,
  `VIX=18.53` (a moderate level -- not remotely "elevated fear" by family
  016's own percentile-based flag) while `VVIX=117.32` sits at the
  **97.8th percentile** of its own trailing history through that date --
  a genuinely elevated vol-of-vol reading during an otherwise unremarkable
  equity-volatility regime (this window coincides with the Nov-Dec 2014
  oil-price collapse and mounting uncertainty about its knock-on effects,
  which materialized in equity markets only later, in the Aug 2015 and
  Jan-Feb 2016 selloffs). Family 016's elevated-VIX flag reads "calm" on
  this exact day; this family's signal reads "elevated vol-of-vol
  uncertainty."
- **Both move together (the confirming/contrast case):** during the peak
  of the 2008 GFC (**2008-10-20 to 2008-11-24**), VIX and VVIX both sit at
  or near their own all-time trailing-percentile highs simultaneously
  (VIX 96.5th-100th percentile, VVIX 93.7th-99.8th percentile) — the
  textbook case where a genuine, realized volatility crisis is
  ACCOMPANIED by elevated uncertainty about future volatility, unlike the
  Dec 2014 divergence case above where uncertainty about future
  volatility rose well ahead of any realized equity-volatility spike.

This confirms VVIX is not a relabeled or highly-correlated proxy for
VIX's own level (weak +0.264 dev-period correlation, and a documented
real divergence episode), while also showing the two statistics validly
co-move during a genuine, fully-developed volatility crisis — exactly the
behavior the mechanism section predicts for a second-order,
leading-indicator-style signal.

## Category

**Volatility targeting** (matching the research queue's own filing;
also considered "Regime switch," but the signal is a volatility
statistic computed from options data, the same categorization basis as
family 025's VRP sizing, so Volatility targeting is the better fit).

## Rules

For each core asset independently (single-asset family, §4.1's standard
rule, shared cross-market signal per family 016/025/041's precedent):

1. `vvix_t` = CBOE VVIX daily close, causally forward-filled onto the
   asset's own trading-day index (identical alignment method to
   `_aligned_vix_close()` in families 016/025/041).
2. `pctile_t` = causal, point-in-time rolling percentile rank of
   `vvix_t` within its own trailing `vvix_lookback` window of past VVIX
   values (through and including day `t`). Defaults to 0.5 (neutral)
   before `vvix_lookback` days of VVIX history exist, or before
   `^VVIX`'s own 2007-01-03 start (falls back to plain DCA, `m_t=1.0`,
   for any day before then).
3. Continuous, INVERTED sizing multiplier (elevated VVIX percentile ->
   buy LESS; depressed -> buy MORE; risk-off sign, per the mechanism
   section above):

   `m_t = clip(1 - k * (2 * pctile_t - 1), min_mult, max_mult)`

4. `buy_usd_t = min(weekly_deposit * m_t, max_lump_multiple *
   weekly_deposit)`, further capped by the engine's own unconditional
   cash cap (`buy_usd <= cash`, `engine.py` §3.2). No sells, ever; no
   leverage; cash never goes negative.

## Parameters (4 tunable, ≤5)

- `vvix_lookback` — trailing window (trading days) for VVIX's own
  percentile-rank calculation: `{126, 252, 504}`
- `k` — multiplier steepness: `{0.5, 1.0, 1.5}`
- `min_mult` — floor on the buy multiplier (must be `< 1.0`, per the
  families 014/033/037/039/040/041 lesson against cash-cap
  nullification): `{0.25, 0.5}`
- `max_mult` — ceiling on the buy multiplier: `{1.5, 2.0}`

Fixed (not grid-varied): `max_lump_multiple = 3.0` (matching family
041's fixed value).

**Grid: 3 × 3 × 2 × 2 = 36 configurations** (at the §3.4 cap).

**Primary configuration:** `vvix_lookback=252, k=1.0, min_mult=0.5,
max_mult=2.0` (the same "middle-of-the-grid" choice this loop has used
as its default primary config across essentially every prior continuous-
percentile family, declared before any grid result is seen).

## Expected sign of the effect

Elevated VVIX-percentile weeks should show a reduced buy multiplier
(bank cash); depressed VVIX-percentile weeks should show an increased
buy multiplier (deploy more). If VVIX-implied fragility genuinely
precedes bouts of realized market stress, this reserve should be
available (and deployable at lower average entry prices) shortly after
the regime turns — the same qualitative logic as families 011/019/027/032,
applied to a distinct, options-implied vol-of-vol input rather than a
credit-spread or survey-based macro input.

## Complexity ceiling (§3.4) — self-check

- Rules fit on one page, computed end-of-day. PASS.
- At most one order per asset per trading day (buy-only, no sells).
  PASS.
- 4 tunable parameters (≤5). PASS.
- Data: `^VVIX` via yfinance, already confirmed free and reachable.
  PASS.
- Grid: 36 configurations (≤36 cap), one declared primary config. PASS.

## Closed-family check (§7.2)

Not a re-test of any v1/v2/v2.1 closed family (none of those used any
VIX-family option-implied series at all).

## Pre-grid checks planned (before trusting any grid result)

1. `PRIMARY_CONFIG` is a member of `grid_configs()` — import-time
   assertion.
2. Every grid cell's `min_mult < 1.0` — import-time assertion.
3. VVIX availability vs. each asset's own dev window (computed live).
4. Distinction-verification cross-tabs vs. families 016, 025 AND 041
   (flag-agreement fractions and level correlations, on real overlapping
   SP500 dev data).
5. Pre-grid non-degeneracy sanity check (multiplier not stuck at 1.0;
   dispersion) on all 5 core assets.
6. Cash-reserve-dynamics check (average cash vs. DCA; drawn down on
   low-multiplier/elevated-VVIX weeks vs. banked on high-multiplier/
   depressed-VVIX weeks).
7. No dev-period check or spot-check ever reads a date on/after
   2020-01-01, or any unseen ticker (all divergence-example dates above
   are 2008/2014, strictly pre-2020, and `^VVIX` reachability was
   checked via `period="max"`/row-count/start-date only, never by
   inspecting any specific 2020+ value).

## Implementation checks (§3.2, standard)

Degenerate (`enabled=False`) reproduces DCA bit-for-bit; a second,
real `k=0.0` grid-shaped code path also reproduces DCA bit-for-bit
(two-reference-point pattern); cash/units never negative (DCA, primary,
aggressive grid corner); capital never exceeds cumulative deposits +
interest via the principled never-invest-ceiling bound; no-lookahead
perturbation test at `t=6000` and `t=20000`; point-in-time macro N/A
(VVIX is a market-price index, observable same-day, no publication lag,
same precedent as VIX/VIX3M/DXY in families 015/016/025/041).
