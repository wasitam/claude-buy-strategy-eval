# Family 047 pre-registration: CBOE SKEW Index tail-risk-pricing regime sizing

**Idea source:** research queue #48. Literature: CBOE SKEW Index white
paper (CBOE, 2010/2019 methodology updates) (SKEW is derived from the
slope/curvature of the S&P 500 30-day option-implied volatility SMILE --
specifically the price of out-of-the-money puts relative to at-the-money
options -- and is constructed so that `SKEW = 100` means the market prices
S&P 500 returns as approximately log-normal, i.e. no extra tail-crash
premium, while `SKEW > 100` means the market is pricing a fatter left
tail than log-normal, with the CBOE's own stated mapping translating the
index level into an implied probability of a >-2-standard-deviation move
over the next 30 days); Bali & Murray (2013), "Does risk-neutral skewness
predict the cross-section of equity option portfolio returns?", *Journal
of Financial and Economic Analysis* (S&P 500 option-implied skewness
carries incremental, priced information about crash risk beyond the VIX
level); Xing, Zhang & Zhao (2010), "What does individual option
volatility smirk tell us about future equity returns?", *Journal of
Financial and Quantitative Economics* (volatility smirk steepness --
the same underlying construct SKEW standardizes -- predicts subsequent
underperformance, distinct from at-the-money implied volatility level).

## Mechanism ("why would this work, and who is on the other side?")

`^SKEW` is a standardized measure of the SHAPE of the S&P 500 option
implied-volatility smile at a single (30-day) tenor: specifically, how
much more expensive far-out-of-the-money puts are, relative to
at-the-money options, than a log-normal returns model would imply. This
is a fundamentally different quantity from every prior volatility-family
signal in this loop:

- `^VIX` (family 016) measures the LEVEL of at-the-money 30-day implied
  volatility -- "how much movement is priced in," with no reference to
  asymmetry.
- Family 025's VIX-minus-realized-vol spread measures a LEVEL gap
  between implied and trailing-realized volatility.
- `^VIX3M`/`^VIX` (family 041) measures the TERM-STRUCTURE SLOPE across
  TWO DIFFERENT TENORS (30-day vs. 3-month) of the SAME at-the-money
  volatility level.
- `^VVIX` (family 046) measures the LEVEL of implied volatility OF THE
  VIX INDEX ITSELF -- a second-order "vol-of-vol" quantity about how much
  VIX will move, still built from at-the-money-style options (on VIX),
  with no smile-shape/asymmetry component.

`^SKEW`, by contrast, holds the tenor fixed (30 days) and the underlying
fixed (S&P 500 options) and instead measures the ASYMMETRY of the smile
at that one tenor: it can rise even while VIX, VIX3M/VIX and VVIX are
all unremarkable, whenever dealers/market-makers bid up crash insurance
(deep OTM puts) specifically, without a broader rise in at-the-money
implied volatility, vol-of-vol, or the term structure. This is the
textbook "complacent index level, but the tails are getting pricier"
regime the literature above associates with elevated informed hedging
demand ahead of a left-tail event that has not yet repriced the
at-the-money volatility level.

**Sign decision:** this family adopts the same risk-off/defensive-bank
sign as families 011/019/027/032/041/046 (not family 016's contrarian-
buy-into-realized-fear sign). SKEW, like VVIX and the VIX3M/VIX term
structure, is a LEADING/forward-pricing signal about a risk that has not
yet fully materialized in the underlying asset's own realized price
action -- by construction it is a derivative-market pricing signal about
tail-crash PROBABILITY, not a statement that a crash has already
happened and a rebound is available to buy (family 016's regime).
Elevated SKEW percentile -> buy LESS (bank a reserve). Depressed SKEW
percentile -> buy MORE (deploy normally, and once enough reserve has
banked, at up to a capped catch-up lump multiple) -- the same continuous,
percentile-scaled sizing multiplier form as families 041/045/046 (per
task instruction: a continuous multiplier, never a discrete ladder, to
avoid the cash-cap-nullification bug documented in `state/bugfix_log.md`
and this family's own `min_mult<1.0` import-time assertion below).

**Who is on the other side?** A DCA investor mechanically buying every
week is, by construction, indifferent to whether the market's own option
dealers are currently paying up specifically for deep-tail crash
protection. If SKEW's tail-pricing signal has genuine predictive content
for subsequent drawdowns (as Bali & Murray 2013 and Xing/Zhang/Zhao 2010
argue for the closely related smirk-steepness construct), a DCA investor
who buys straight through an elevated-SKEW regime is buying into a period
the options market itself is pricing as unusually crash-prone, without
extracting any compensating discount, exactly the gap this family's
signal targets.

## Data feasibility (checked first, per task instruction)

`yf.Ticker('^SKEW').history(period='max', auto_adjust=False)` returns
**9,177 daily rows**, from **1990-01-02** through the present (checked
2026-09-26; reachable via yfinance, routed through
`v3data.fetch_yf_macro('^SKEW')` exactly like families 015/041/046).

Comparison of development-period (pre-2020-01-01) history across this
loop's volatility-derived signals:

| Series | Start | Dev-period length (to 2019-12-31) | Used by |
|---|---|---|---|
| `^SKEW` | 1990-01-02 | ~30.0 years | this family |
| `^VIX` | 1990-01-02 | ~30.0 years | families 016, 025 |
| `^VIX3M` | 2006-07-17 | ~13.4 years | family 041 |
| `^VVIX` | 2007-01-03 | ~13.0 years | family 046 |

`^SKEW`'s dev-period history is **essentially identical to `^VIX`'s own
~30-year history** (both start 1990-01-02) -- the longest history of any
volatility-derived signal used in this loop so far, and roughly 2.3x
`^VVIX`'s history (which family 046 already judged adequate for a full
36-configuration grid). SKEW is therefore judged clearly **feasible**, on
an even stronger basis than family 046. No substitute idea from the
queue is needed.

## Required distinction from families 016, 025, 041 and 046 (verified concretely on real dev data, not just asserted)

Raw level correlation, `^SKEW` vs. `^VIX`, full pre-2020 overlap
(1990-01-02 through 2019-12-31, 7,525 trading days): **-0.235**. This is
weak and, notably, of the OPPOSITE sign from a naive "both just measure
fear" prior -- SKEW and VIX are not a relabeling of each other, and can
even move in opposite directions.

**Concrete divergence example ("complacent VIX, but the tails are
getting pricier"):** December 2019 (all dates strictly pre-2020-01-01,
dev data). On 2019-12-19, `^VIX` closed at **12.50** (83rd trailing
percentile from the BOTTOM -- i.e. VIX's own 252-day percentile rank was
only 0.083, an unusually calm reading) while `^SKEW` closed at **150.14**,
its trailing 252-day percentile rank at **1.000** -- the single highest
SKEW reading in the entire pre-2020 SKEW history at that point, and a
widely-documented real event (SKEW hit contemporary record highs in
December 2019). This is the textbook divergence this family's signal is
built to capture: an at-the-money volatility level near multi-year lows,
simultaneously with the options market pricing the fattest left tail on
record. (This episode also, with hindsight, preceded the 2020 selloff --
but that selloff itself falls inside the sealed 2020+ holdout and is
**not** used to design or motivate this family; the divergence is
established purely from the December 2019 dev-period SKEW/VIX levels
themselves, which is a standalone, verifiable fact independent of what
happened afterward.)

**Concrete comovement/contrast example:** the 2008 GFC (Oct-Nov 2008),
where `^VIX` reached all-time highs (percentile rank ~0.94-1.00
throughout) while `^SKEW`'s own percentile rank fluctuated in a much
wider, less consistently-elevated band (0.59-1.00, frequently dipping
into the 0.6-0.9 range even as VIX stayed pinned near 1.00) -- confirming
the two series don't move in lockstep even during a shared crisis, only
that they CAN coincide.

**Concrete inverse-divergence example (elevated VIX, depressed SKEW):**
January 1991 (Gulf War onset), `^VIX` percentile rank 0.92-1.00 (VIX
spiked to the low-to-mid 30s) while `^SKEW`'s percentile rank fell to
0.13-0.29 (SKEW in the low 110s, well below its typical range) -- a
period of acute, already-realized macro shock (an ATM-vol event) with
NO accompanying rise in tail-pricing asymmetry, the mirror image of the
December 2019 case. 414 pre-2020 trading days meet the
`vix_pctile>0.9 and skew_pctile<0.3` joint condition, confirming this
inverse pattern is not a one-off artifact.

These three episodes, plus the weak/negative raw correlation, jointly
establish that `^SKEW` is measuring a genuinely different dimension
(smile SHAPE/asymmetry at one tenor) than `^VIX`'s LEVEL (family 016),
family 025's level-spread, `^VIX3M/^VIX`'s cross-tenor SLOPE (family
041), or `^VVIX`'s vol-of-vol LEVEL (family 046). The run script computes
the same flag-agreement cross-tabs family 046 used (elevated-SKEW flag
vs. each prior family's own elevated flag) live against real dev data
before trusting any grid result, exactly as those families did.

## Category

**Volatility targeting** (per the task's category assignment for this
idea; consistent with families 041 and 046's own category, since all
three are variations on sizing buys off a volatility-derivatives-implied
signal, while remaining materially different SIGNALS as required by
sec 7.2/distinctness).

## Rules

1. Compute `^SKEW`'s daily close, forward-filled causally onto each
   asset's own trading-day index (never filled backward), via
   `v3data.fetch_yf_macro('^SKEW')` -- identical alignment method to
   families 015/041/046's own helpers.
2. Compute a causal, point-in-time rolling percentile rank `pctile_t` of
   `skew_t` within its own trailing `skew_lookback` window of past SKEW
   values ending at `t` (inclusive). Defaults to 0.5 (neutral) until
   `skew_lookback` days of valid SKEW history exist (this is a non-issue
   here since SKEW's ~30-year history covers all of GOLD/SILVER/OIL's
   dev history from inception and all of BTC's; only SP500's own
   pre-1990 era, if any were included, would see the neutral default --
   SP500's dev history in this loop's engine in fact starts well before
   1990, so the neutral default DOES apply there until 1990).
3. Sizing multiplier (continuous, inverted/risk-off sign, never a
   discrete ladder):
   `m_t = clip(1 - k * (2 * pctile_t - 1), min_mult, max_mult)`
   Elevated SKEW percentile -> buy LESS (bank a reserve). Depressed SKEW
   percentile -> buy MORE (deploy normally / capped catch-up lump).
4. Each week's buy = `min(weekly_deposit * m_t, max_lump_multiple *
   weekly_deposit)`, capped by the engine's own unconditional cash cap
   (`buy_usd <= cash`, `engine.py` sec 3.2) -- no leverage, ever. A
   shortfall on an elevated-SKEW (low-multiplier) week simply banks as
   cash (earning IRX) until a later depressed-SKEW (high-multiplier)
   week spends it.
5. Never a sell. At most one order per asset per trading day (a single
   buy).

## Data inputs

- Each core/unseen asset's own OHLC (via `data.py`'s existing gate).
- `^SKEW` daily close, via `v3data.fetch_yf_macro('^SKEW')` (a market
  price index with no publication lag, same-day observable, matching
  family 046's own note about VVIX/VIX/VIX3M/DXY).
- IRX for cash interest (existing engine plumbing).

## Parameters (4 tunable + 1 fixed, <=5)

- `skew_lookback` (tunable): trailing window (trading days) for the
  SKEW percentile-rank calculation.
- `k` (tunable): sizing sensitivity to the percentile deviation from 0.5.
- `min_mult` (tunable): floor on the multiplier (must be `< 1.0`, or the
  engine's no-leverage cash cap silently nullifies the reserve-banking
  arm -- families 014/033/037/039/040/041/046's now-7x-confirmed lesson,
  enforced by an import-time assertion).
- `max_mult` (tunable): ceiling on the multiplier.
- `max_lump_multiple` (fixed at 3.0, not grid-varied): hard ceiling on
  any single week's buy relative to `weekly_deposit`, identical to
  family 046's own fixed value.

## Grid (36 configurations, at the sec 3.4 cap)

`skew_lookback x k x min_mult x max_mult = 3 x 3 x 2 x 2 = 36`

- `skew_lookback`: [126, 252, 504]
- `k`: [0.5, 1.0, 1.5]
- `min_mult`: [0.25, 0.5]
- `max_mult`: [1.5, 2.0]

## Primary configuration

`skew_lookback=252, k=1.0, min_mult=0.5, max_mult=2.0` (identical grid
position and identical values to family 046's own primary config, which
is itself the natural "1-year lookback, unit sensitivity, moderate
band" default point in this loop's now-established VIX-derivative-signal
sizing template -- not chosen by looking at any result).

## Expected sign of the effect

Beats DCA on final wealth AND Sharpe on at least 3 of 5 core assets
(sec 4.1), by banking cash ahead of periods the options market itself is
pricing as unusually crash-prone (elevated SKEW), then deploying that
reserve (plus a capped catch-up lump) once the tail-pricing signal
normalizes -- reducing the strategy's exposure to the worst drawdowns
relative to plain DCA, at the cost of some upside capture during calm
periods misclassified as risk-off. Given SKEW's weak/negative raw
correlation with VIX and family 046's own finding that a superficially
strong sec 4.1/4.4 result can still fail sec 4.2's DSR check on extreme-
kurtosis grounds, no strong prior is placed on this family clearing
sec 4.2-4.4; the grid and robustness suite will determine that.

## Implementation-check plan (pre-registered, before any backtest)

1. Degenerate bypass (`enabled=False`) reproduces DCA bit-for-bit.
2. Second reference point: `k=0.0` (a real grid-shaped code path, not the
   bypass) also reproduces DCA bit-for-bit.
3. No negative cash/units, on DCA, the primary config, and the grid's
   most-aggressive corner.
4. Capital deployed never exceeds cumulative deposits + interest, via the
   principled "never invest" ceiling-bound method (family 021's fix).
5. No-lookahead perturbation test at two different `t` checkpoints.
6. Point-in-time macro check (existing shared check).
7. Pre-grid non-degeneracy sanity check on all 5 core assets (multiplier
   is not trivially 1.0 for >90% of days, and has nonzero standard
   deviation).
8. Cash-reserve-dynamics check: primary config's average cash differs
   meaningfully from DCA's, and cash is higher during elevated-SKEW
   (low-multiplier) weeks than depressed-SKEW (high-multiplier) weeks.
9. `PRIMARY_CONFIG` verified a genuine member of `grid_configs()` via an
   import-time assertion (family 021's lesson).
10. Every grid cell's `min_mult < 1.0` verified via an import-time
    assertion (families 014/033/037/039/040/041/046's lesson).
