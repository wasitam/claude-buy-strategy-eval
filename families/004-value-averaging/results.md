# Family 004 results: value averaging (Edleson 1991)

**Verdict: NEAR-MISS** (passes sec 4.1 and, unusually, sec 4.3; fails sec 4.2
and sec 4.4; holdout not opened per sec 8 step 8, "finalists only" -- this
family never reached finalist status, since sec 4 requires every check to
pass, not a majority of them).

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`, buy_usd=cash every day) reproduces plain DCA exactly (bit-for-bit on units and cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary VA config) | PASS |
| **Capital-neutrality**: cumulative net capital deployed (buys - sell proceeds) never exceeds what the SAME $500/week deposit stream would be worth compounding at IRX alone (i.e. VA's own accumulated deposits + the interest they earned while un-invested -- no external capital ever enters) | PASS |
| No-lookahead: perturbing all data after day t leaves every order on/before t unchanged | PASS |
| Point-in-time macro data | N/A (price-only strategy; vacuously satisfied) |

## Primary configuration: `annual_growth_rate=0.10, max_multiple_of_deposit=4, allow_sells=True`

### sec 4.1 -- beats DCA on wealth AND Sharpe, >= 3 of 5 core assets, both fee levels

At 0.1% fees:

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both) |
|---|---|---|---|---|---|
| SP500 | 85.433 | 85.277 | 0.15572 | 0.15310 | **YES** |
| GOLD | 2.0503 | 2.2312 | 0.53232 | 0.50492 | no (wealth lower) |
| SILVER | 1.8136 | 1.6867 | 0.35445 | 0.31968 | **YES** |
| BTC | 4.2042 | 9.8557 | 0.93197 | 1.06731 | no (both worse, large gap) |
| OIL | 1.2701 | 1.1799 | 0.23191 | 0.22782 | **YES** |

At 0.25% fees the pattern is identical: SP500, SILVER, OIL beat DCA on both
metrics; GOLD and BTC do not. **3/5 at both fee levels -- sec 4.1: PASS**
(first single-asset family in this loop to clear sec 4.1; family 002 also
passed sec 4.1 but as a portfolio family).

BTC's shortfall is large and directionally exactly as flagged in
`prereg.md`'s "Expected sign" section: BTC's short (~5-year) development
window is dominated by a strong secular uptrend, and VA's target-path rule
mechanically under-buys (and, with `allow_sells=True`, actively sells) once
the account races ahead of the assumed 10%/year target -- which happens
early and often during a sustained bull run -- so it misses a large share of
the compounding. GOLD's shortfall is smaller and driven by a similar but
milder effect.

### sec 4.2 -- Deflated Sharpe Ratio >= 0.95

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  **-0.0351/week** (annualized ~-0.253) -- negative on average, dragged down
  by BTC's large negative excess pulling down the equal-weight pooled
  average even though 3 of 5 assets individually show a positive edge.
- `N` (raw trial count at this assessment): **280** (196 seeded + 66 from
  families 001-003 + 18 new from this family's grid).
- `N_eff` (average-linkage clustering, distance sqrt(0.5(1-rho)), rho>=0.5
  threshold): **34** clusters.
- **DSR (N_eff-based, used for the decision): 1.17e-37** -- essentially
  zero. The pooled excess series is heavily left-skewed and fat-tailed
  (skew -1.21, kurtosis 53.2), consistent with BTC's large, occasional
  negative-excess weeks (missed rally weeks under `allow_sells=True`)
  dominating the distribution's shape.
- DSR (raw-N, conservative reference): 1.88e-58.

**sec 4.2: FAIL**, overwhelmingly so -- the pooled (equal-weight across all
5 assets, including BTC) excess series is negative on average despite 3 of 5
individual assets beating DCA, because BTC's shortfall is large enough in
dollar/Sharpe terms to swamp the other four assets' smaller gains in the
pooled average that sec 3.3 mandates for the DSR test.

### sec 4.4 -- robust across parameters (grid diagnostic)

**8 of 18 configurations (44.4%) reach the majority-of-assets bar** (>=3/5
core assets beating DCA on both wealth and Sharpe at 0.1% fees). The pattern
is monotonic in the intended direction on two of three parameters: higher
`max_multiple_of_deposit` (less capped, closer to the "natural" VA rule) and
higher `annual_growth_rate` (a steeper assumed path, which keeps the account
"behind" and buying more, for longer, before BTC's/GOLD's trend outruns it)
both increase the pass rate; `allow_sells` has a smaller, mixed effect.
**sec 4.4: FAIL** (need >= 2/3 = 12/18; only 8/18 pass).

CSCV probability of backtest overfitting (diagnostic, SP500 grid, 8 splits,
70 combinations): **PBO = 0.10**. The lowest of the four v3 families so far
(001: 0.0, 002: 0.443, 003: 0.286) -- consistent with a grid that isn't
overfit so much as genuinely and consistently informative about SP500 in
particular (SP500 is the asset least affected by the BTC-style trend-outrun
failure mode), even though the *pooled, cross-asset* result fails sec 4.2
and the *majority-of-assets* rule fails sec 4.4.

### sec 4.3 -- robust across time and resamples (run to completion)

Per the task's instruction and the family 002 precedent (this family passes
sec 4.1, so the full suite was run rather than stopped early), at the same
reduced simulation count as family 002 (n_sims=60 per bootstrap/placebo
variant, `scripts/v3/robustness_004_value_averaging.py`):

- **Rolling windows** (3y/5y for SP500, GOLD, SILVER, OIL; 2y for BTC,
  stepping 20 trading days): **72.3% beat DCA on wealth, 87.7% on Sharpe**
  overall (3,439 windows across 9 asset/window combinations) -- both above
  the 60% bar. Per-asset detail: SP500 (74-76% wealth, 84-86% Sharpe), GOLD
  (41-70% wealth, 91% Sharpe), SILVER (69-74% wealth, 87-92% Sharpe), OIL
  (81-82% wealth, 95-99% Sharpe), BTC (26% wealth, 81% Sharpe) -- BTC and
  GOLD's 5y window are the only sub-60%-on-wealth cells, consistent with
  sec 4.1's asset-level pattern. **PASS overall.**
- **Block bootstrap** (500-target scoped to 60 sims/variant per the
  running precedent, 4-week blocks, SP500): raw-path beats DCA 78.3% of
  sims on wealth, 76.7% on Sharpe; detrended beats DCA 95.0% on wealth,
  78.3% on Sharpe. Both variants clear "majority" (>50%) on both metrics.
  **PASS.**
- **Placebo** (circular-shift of VA's real per-day net-order series --
  buy_usd minus sell_usd, nonzero only on week-end decision days --
  replayed as an open-loop daily order schedule still capped by real cash
  on hand each simulated day, so no leverage is possible even in the
  shuffled placebo; 60 shifts, SP500): the real result lands at the
  **96.7th percentile on wealth and 95.0th on Sharpe** among the shuffled
  placebos -- both at or above the required 95th percentile. **PASS.**

**sec 4.3 overall: PASS** (all three sub-checks pass, on SP500 specifically
and, for rolling windows, in aggregate across the full asset/window set).
This is notable: unlike families 001-003, this family clears the
time/resample-robustness bar cleanly. It still cannot become a finalist,
because sec 4 requires *every* check (4.1-4.4) to pass, and this family
fails 4.2 and 4.4.

## Verdict

**NEAR-MISS.** The primary configuration passes sec 4.1 (3/5 core assets
beat DCA on wealth AND Sharpe, at both 0.1% and 0.25% fees) and, unusually
for this loop so far, sec 4.3 in full (rolling windows, block bootstrap raw
and detrended, and placebo circular-shift all clear their bars on SP500).
But it fails sec 4.2 (DSR 1.17e-37, far below 0.95 -- the *pooled*,
equal-weight-across-5-assets excess series used for the DSR test is dragged
negative by BTC's large shortfall even though 3 of 5 assets individually
beat DCA) and sec 4.4 (only 8/18 = 44.4% of the grid clears the
majority-of-assets bar, need >= 2/3 = 12/18). Per sec 8 step 8, holdout data
was **not** opened -- holdout access is reserved for finalists only, and
sec 4 requires every check to pass, not a majority of them.

## Why the mechanism didn't clear every bar (interpretation, not part of the formal verdict)

The result is a clean illustration of exactly the tension Hayley's critique
predicts, once capital-neutrality is enforced: value averaging's contrarian
"buy more below the assumed path, sell above it" rule works well on assets
whose prices oscillate around a trend close to the assumed 10%/year growth
rate (SP500, SILVER, OIL all pass cleanly, and pass the full sec 4.3
robustness battery) but is a structural headwind on an asset with a strong,
sustained trend well above that assumed rate over the development sample
(BTC, whose ~5-year development CAGR far exceeds 10%/year) -- the rule
repeatedly sells into, and pauses buying during, BTC's own bull run, exactly
the failure mode the prereg's "Expected sign" section flagged before any
backtest was run. Because the plan's DSR test (sec 3.3, sec 4.2) uses the
**pooled, equal-weight-across-5-assets** excess series rather than a
per-asset or majority-vote statistic, one asset's large, systematic
shortfall (BTC) is enough to swamp three other assets' smaller, genuine
gains in the aggregate series the DSR is computed on -- the same mechanical
gap between "passes sec 4.1 (majority of assets)" and "passes sec 4.2
(pooled excess series)" that also produced family 002's near-miss verdict,
though the specific asset driving it differs (BTC's own trend for 002 was a
tailwind concentrated in one direction that inflated a rotation strategy's
apparent edge; here BTC's trend is a headwind that suppresses VA's pooled
edge). A version of this family that excluded BTC, or used a per-asset
adaptive assumed growth rate rather than one fixed 10%/year rate across all
5 very different assets, might plausibly do better on sec 4.2/4.4 -- but
that would be retuning on the very development data just examined, which
sec 5.4's holdout-discipline spirit (never feed results back into a new
family's design) extends by analogy to grid/parameter choices within an
already-assessed family: this configuration's verdict stands, and any such
variant would need to be its own newly pre-registered family per sec 7.1,
citing only literature and *general* reasoning, not this specific result.

## Judgment calls made in this iteration

1. **Target path formula and shape fixed by design, not a grid parameter.**
   Declared in `prereg.md` before any backtest: the target-value path uses
   the canonical future-value-of-an-annuity formula with a constant assumed
   per-week growth rate (`V_target(w) = weekly_deposit x ((1+r)^w - 1) / r`),
   matching Edleson's own constant-assumed-return framing. Only the rate
   itself (`annual_growth_rate`) is tunable, keeping the parameter count at
   3 (of the allowed 5) while still letting the grid test sensitivity to how
   aggressive the assumed path is.
2. **Capital-neutrality / Hayley's-critique resolution**, the central
   judgment call for this family (fully documented in `prereg.md`'s "How
   this family addresses Hayley's critique" section before any backtest):
   VA and DCA share the exact same $500/week deposit schedule (never
   different), VA's buys are funded only from the account's own accumulated
   cash (capped by real cash on hand every week -- no leverage, no external
   capital, enforced by the same engine cash-cap invariant every other v3
   family relies on), and an additional magnitude cap
   (`max_multiple_of_deposit` x $500) bounds any single week's action to
   keep VA's cash flow in the same order of magnitude as DCA's constant
   $500/week rather than occasionally acting like a lump-sum investor. The
   family is scored on final wealth (sec 4.1), not IRR, precisely because
   IRR would still reward VA's early-and-larger draws in a way final wealth
   under this capital-neutral construction does not -- this is the specific
   design choice the task instructed be made explicit given Hayley's
   critique is "specifically about this kind of design choice mattering a
   lot," and an added implementation check (see table above) verifies the
   invariant holds path-wise, not just on average, across the full ~96-year
   SP500 development history.
3. **Shadow position tracking inside the decider.** The single-asset
   engine's `decide(t, cash)` interface passes only cash, not current units,
   to the decider (unlike the portfolio engine used by family 002, whose
   `decide` signature does pass `units_now`). Since VA fundamentally needs
   the account's current *value* (units x price) to compute the gap against
   the target path, `value_averaging.py`'s decider maintains its own causal
   shadow simulation of its past fills, using the identical next-day-open /
   sells-before-buys / fee mechanics as the real engine. Because every buy
   this decider ever submits is already capped by the real `cash` value the
   engine hands it each call (so the engine's own downstream cash-cap never
   has to clip it further), the shadow stays exactly in sync with the
   engine's true state at every step -- verified by the capital-neutrality
   and no-negative-cash/units implementation checks passing exactly.
4. **Placebo signal choice.** Rather than circular-shifting a pure
   price-based signal (as family 001 did with price-minus-SMA), this
   family's placebo (`scripts/v3/robustness_004_value_averaging.py`)
   circular-shifts VA's real per-day net-order series (buy_usd minus
   sell_usd from the actual primary-config run) and replays it as an
   open-loop daily order schedule against the same price history, still
   capped by real cash each simulated day. This was chosen because VA's
   true signal (the gap between account value and target) is inherently
   self-referential -- it depends on the account's own trading history, not
   just the raw price series -- so shifting a derived, already-realized
   order-size series (analogous to family 003's own multiplier-time-series
   approach, though family 003 did not run its placebo to completion) tests
   the same underlying question (does the *specific timing* of VA's extra
   buys/sells carry the edge, versus the same order sizes landing on
   arbitrary days) without the recursive-consistency problems a shifted raw
   gap signal would create.
5. **Reduced sec 4.3 simulation counts** (n_sims=60 per bootstrap/placebo
   variant, same as family 002), run to completion in this iteration
   because the primary configuration passes sec 4.1 -- per the task's own
   instruction ("if this family looks promising ... run sec 4.3 to
   completion since that's when it matters most") and the family 002
   precedent. This is the first family since 002 where sec 4.3 was run to
   completion rather than stopped early after 4.1/4.2/4.4 already
   conclusively failed.
