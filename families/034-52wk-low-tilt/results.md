# Family 034 results: 52-week-low proximity contrarian tilt

**Verdict: NEAR-MISS.** The primary configuration passes sec 4.1 narrowly
(beats DCA on final wealth AND Sharpe on **exactly 3 of 5** core assets, at
both fee levels -- the minimum passing count, and the identical count and
near-identical margins to family 020's own near-miss). It fails sec 4.2
(DSR effectively zero, driven by a negative raw pooled excess-return
Sharpe), sec 4.4 (only 50% of the grid reaches the majority bar, need
>=2/3), and sec 4.3's bootstrap and placebo legs decisively (placebo: real
result lands at the 3rd/2nd percentile of 60 circular-shifted runs on
wealth/Sharpe -- need >=95th -- the *opposite* extreme from a pass) even
though its rolling-window leg passes. Holdout was **not** opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family** (sec 4.1's Single-asset line), across
all 5 core assets, category **Sizing / valuation** (the seed queue's own
categorization of idea #34, and the category the signal's economic content
-- "how cheap is this asset relative to its own recent trading range" --
actually matches, as opposed to a continuation/momentum framing). Signal:
`prox_low_t = low52_t / close_t` where `low52_t` is a strictly causal
trailing 52-week-low (two window definitions in the grid: `trading252`
rolling min over 252 trading days, or `calendar` rolling min over 365
calendar days). A 3-tier ladder multiplier `m_t` **increases** buy size as
`prox_low_t` rises (closer to the 52-week low -> bigger buy).

**The required distinctions (full reasoning in prereg.md):**

- **vs. family 020** (52-week-HIGH proximity momentum tilt, NEAR-MISS):
  opposite reference extremum (a running minimum vs. family 020's running
  maximum) and opposite economic story (contrarian/overreaction-reversal,
  De Bondt & Thaler 1985 / Lehmann 1990 / Jegadeesh 1990, vs. family 020's
  momentum/continuation, George & Hwang 2004) -- two independently
  literature-supported, competing hypotheses, not the same construction
  re-signed. Confirmed empirically on real SP500 development data (see
  "Signal-disagreement check" below): the two signals' tier assignments
  disagree on 72.8% of development days and their proximity ratios
  correlate at only -0.32, ruling out a near-perfect (anti)correlated
  restatement.
- **vs. family 014** (drawdown-from-all-time-high reserve deployment,
  REJECTED): different reference extremum entirely (a running minimum,
  this family, vs. family 014's running maximum), a materially shorter
  window (52-week vs. all-time), and a different functional-form parameter
  set (this family's `window_def` grid parameter has no all-time-anchored
  analogue at all).

## Sign-correctness verification (required by this iteration's task, before
trusting any backtest)

On SP500 development data, using the primary config, the mean buy
multiplier on days in the **top quartile** of `prox_low_t` (closest to the
52-week low) was **1.500** vs. **0.6233** on days in the **bottom quartile**
(furthest above the 52-week low, i.e. closest to the 52-week high) --
confirming near-low days get systematically LARGER buy orders than
near-high days, the intended sign, and ruling out an accidental
re-implementation of family 020's own high-proximity logic.

## Cash-reserve dynamics check (family 033's lesson, required this
iteration)

With the primary config's "far above the low" (normal) tier multiplier
fixed at `mult_far = 0.50 < 1.0`, the strategy's average cash balance over
the SP500 development sample is **materially higher than the plain-DCA
baseline's** (a genuine reserve is banked, not merely assumed from
`mult_far<1.0` alone), and the average cash balance during near-low-tier
weeks is **lower than** during far-above-low-tier weeks (the banked reserve
is actually drawn down when the near-low signal fires) -- both checks
**PASS**, confirming this family avoided family 033's cash-cap no-op trap.

## Signal-disagreement check vs. family 020 (concrete numeric check promised
in prereg.md)

On SP500 development data: family 020's own tier (its `moderate` primary
ladder, keyed to `prox_t = close_t/high52_t`) and this family's own tier
(keyed to `prox_low_t = low52_t/close_t`) **disagree about which extreme
the asset is closer to on 72.8% of development days**, and
`corr(prox_t, prox_low_t) = -0.322` -- far from a near-perfect
(anti)correlation of +/-1, confirming the two signals are genuinely
different constructions, not the same statistic read with an inverted
sign.

## Pre-grid non-degeneracy sanity check

| Asset | Dev days | Frac. near-low tier | Frac. mid tier | Frac. far-above-low tier | Non-degenerate? |
|---|---|---|---|---|---|
| SP500 | 23,109 | 12.80% | 56.49% | 30.70% | PASS |
| GOLD | 4,848 | 16.13% | 54.13% | 29.74% | PASS |
| SILVER | 4,850 | 18.31% | 42.00% | 39.69% | PASS |
| BTC | 1,932 | 3.93% | 17.75% | 78.31% | PASS |
| OIL | 4,857 | 7.82% | 32.61% | 59.56% | PASS |

All 5 assets clear the (2%, 98%) band on every tier. BTC spends the large
majority of its short development window far above its own 52-week low
(consistent with its strong overall uptrend over 2014-2019), the mirror
pattern of what family 020 found for BTC's proximity to its own 52-week
high (BTC spent the majority of days FAR from its high in that same
family's check) -- a plausible, internally consistent pair of findings
given BTC's historically choppy but net-upward development-period path.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Sign check: mean multiplier, top quartile `prox_low_t` vs. bottom quartile | 1.500 vs 0.6233 -- PASS (near-low buys strictly larger) |
| Cash-reserve check: avg cash, strategy vs. DCA baseline | strategy > DCA baseline -- PASS (reserve builds up) |
| Cash-reserve check: avg cash, near-low tier vs. far-above-low tier | near-low < far-above-low -- PASS (reserve drawn down) |
| Signal-disagreement vs. family 020: fraction of days the two tier readings disagree | 72.8% (>5% threshold) -- PASS (not a restatement) |
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Real `ladder=flat, mult_near=1.0` grid-arm code path (not the bypass) also reproduces plain DCA bit-for-bit | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (most aggressive grid corner: `calendar, aggressive, mult_near=2.0, max_lump_cap=3.0`) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (primary config) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (most aggressive grid corner) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000` and `t=20000`, specifically exercising the 52-week-low tracker's causal rolling/expanding minimum) | PASS |
| Point-in-time macro data | N/A -- price-only signal, no macro dependency |

## Primary configuration: `window_def=trading252, ladder=moderate, mult_near=1.5, max_lump_cap=3.0`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.26230 | 85.27722 | 0.152990 | 0.153097 | NO (both lose by a hair) |
| GOLD | 2.23136 | 2.23123 | 0.504981 | 0.504917 | YES |
| SILVER | 1.68692 | 1.68666 | 0.319783 | 0.319677 | YES |
| BTC | 9.83632 | 9.85568 | 1.065485 | 1.067309 | NO (both lose) |
| OIL | 1.18035 | 1.17986 | 0.227842 | 0.227824 | YES |

**Sec 4.1: PASS** -- 3/5 core assets (GOLD, SILVER, OIL) at both 0.1% and
0.25% fees (0.25% results qualitatively identical, see
`_primary_per_asset.csv`), exactly the minimum passing count. As with
family 020, every passing margin is small in absolute terms -- the
strategy is not decisively beating DCA on any asset, it is narrowly ahead
on 3 and narrowly (SP500) or clearly (BTC) behind on the other 2.

### Grid diagnostic (sec 4.4)

**16 of 32 configurations (50.0%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees -- need >=2/3 (21.3/32), the
identical pass rate to family 020's own grid. The pattern is clean and
interpretable, and a close structural mirror of family 020's own grid
pattern: every `ladder=mild` and `ladder=moderate` configuration (16/16,
both window definitions, both `mult_near` values, both `max_lump_cap`
values) reaches 3/5 assets on the combined bar, but every `ladder=
aggressive` config drops to 2/5 (the far-above-low floor of `mult_far=0.30`
combined with the wider `far_thresh=0.70` band bites too hard on the
Sharpe leg specifically -- wealth alone still reaches 3/5 on every
aggressive config), and every `ladder=flat` config (the true zero-effect
arm) reproduces DCA exactly, 0/5 by construction. `window_def`
(`trading252` vs. `calendar`) makes essentially no difference within a
given ladder/mult_near/max_lump_cap combination.

**Sec 4.4: FAIL** (need >=21.3/32; got 16/32 = 50.0%).

CSCV probability of backtest overfitting (32-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.814** -- the
highest (most concerning) PBO of any family tested in this loop so far
(higher even than family 020's own 0.486), consistent with the grid's
narrow-margin, ladder-severity-dependent pattern being at high risk of
being a resampling/overfitting artifact rather than a robust effect.

## Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series
  (strategy weekly NAV return minus DCA weekly NAV return, averaged across
  the 5 assets): **-0.02208** (weekly, **-15.92% annualized**) --
  **negative**, despite the primary config passing sec 4.1's per-asset
  majority count (the same GOLD/SILVER/OIL-pass-but-SP500/BTC-dominate-the-
  pooled-average pattern family 020 showed).
- `N` (raw trial count, whole-loop pool): **1,033** (196 seeded + 805 from
  families 001-033 + 32 new from this family's grid; matches the sanity
  check 196+837=1033, `state/trial_counter.json["new"]`=837 after this
  family).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **105**
  clusters (up from family 033's 97).
- **DSR (N_eff-based): ~9.74e-41** -- effectively zero, doubly so because
  the raw excess Sharpe is negative to begin with. The excess series is
  extremely heavy-tailed (skew -18.92, kurtosis 785.6 -- driven by the
  `max_lump_cap`-bounded but still large catch-up-lump weeks concentrated
  around 52-week-low crossings, the mirror pattern of family 020's own
  extreme kurtosis around 52-week-high crossings).
- DSR (raw-N, conservative reference): ~1.05e-44, also effectively zero.

**Sec 4.2: FAIL**, decisively -- a negative raw pooled excess Sharpe cannot
clear the trial-count-adjusted DSR bar at either `N` or `N_eff`.

## Sec 4.3 (run in full since sec 4.1 passed)

Per prereg.md's declared time-budget (n_sims=60 for bootstrap/placebo).

**Rolling windows** (3y/5y for SP500/GOLD/SILVER/OIL, 2y for BTC, stepping
20 trading days, 3,439 total windows -- the identical window count to
family 020's own check): **62.8% beat DCA on wealth, 64.0% beat DCA on
Sharpe**, both **above the 60% bar -- PASS**. GOLD and OIL are the
strongest performers (76-82% on both metrics at both window lengths);
SILVER and SP500 pass more narrowly; **BTC_2y fails badly** (9.7% wealth,
25.0% Sharpe -- BTC alone would fail this leg decisively), consistent with
sec 12's caveat that BTC-dependent results should be read with caution
and with family 020's own BTC-2y weakness on its own (opposite-signed)
signal.

**Block bootstrap** (60-sim budget, 4-week blocks, SP500 only as the
representative asset per families 003/005/020's precedent): the **raw
path** beats DCA on wealth in only **45.0%** of histories (below a
majority) despite beating on Sharpe in 55.0% -- **FAIL** (both legs must
clear a majority); the **detrended path** beats on wealth in **71.7%** but
on Sharpe in only **45.0%** -- **FAIL** on the Sharpe leg. Both bootstrap
legs fail, on opposite metrics -- unlike family 020, whose bootstrap
legs both passed.

**Placebo** (circular-shift the primary config's own `prox_low_t`-derived
multiplier sequence 60 times, SP500): the real result lands at the
**3.3rd percentile on wealth** and the **1.7th percentile on Sharpe** of
the placebo distribution -- need **>=95th** -- **FAIL**, even more
decisively than family 020's own placebo failure (13.3rd/36.7th
percentile). The real (correctly time-aligned) 52-week-low signal performs
*worse* than nearly every one of the 60 randomly-shifted versions of its
own multiplier sequence, on both wealth and Sharpe -- strong evidence that
whatever thin edge the primary config shows on 3/5 assets at sec 4.1 is not
attributable to the specific temporal alignment of the 52-week-low
proximity signal, and is more likely explained by the same interest-
banking/catch-up-lump timing mechanics this loop has repeatedly found
across its ladder-sizing families (003/005/014/020/033) than by any
genuine contrarian-rebound effect near 52-week lows.

**Sec 4.3: mixed** -- rolling windows PASS, but both bootstrap legs and the
placebo leg FAIL, the placebo leg decisively so.

## Verdict

**NEAR-MISS.** Sec 4.1 passes narrowly (3/5 core assets, both fee levels),
but sec 4.2's DSR is effectively zero (negative raw pooled excess Sharpe),
sec 4.4's grid diagnostic reaches only 50% (need >=2/3, the highest CSCV
PBO of any family in this loop so far at 0.814), and sec 4.3's bootstrap
and placebo legs fail (the placebo leg decisively, landing in the bottom
few percent of 60 randomly-shifted-signal runs rather than the required
top 5%). Not promoted to finalist. Holdout was **not** opened.

## Interpretation

This family's result is, in essence, family 020's near-miss mirrored: an
almost identical sec 4.1 pass count and margin structure (3/5, tiny
wealth/Sharpe deltas, GOLD/SILVER/OIL passing and SP500/BTC failing),
an equally weak sec 4.4 grid (50% both families), and a decisive sec 4.3
placebo failure in both directions -- evidence that a 3-tier proximity-to-
a-52-week-extremum ladder, in EITHER direction (buy more near the high, or
buy more near the low), produces a thin, not-robustly-timed effect in this
development sample that is better explained by the shared interest-
banking/catch-up-lump mechanics this loop has now observed repeatedly
across its ladder-sizing families than by either the momentum-continuation
or contrarian-reversal story motivating the two signs. This is itself a
useful negative finding for the final report: neither of the two
"distance from a salient 52-week price level" hypotheses this loop has now
tested (family 020's high-proximity momentum tilt and this family's
low-proximity contrarian tilt) survives sec 4.2-4.4's trial-adjusted and
robustness bars, despite both resting on real, separately-motivated
literature.

## Judgment calls made this iteration

1. **Category:** filed as Sizing / valuation (per the seed queue's own
   framing and the signal's cheapness-relative-to-range economic content),
   not Trend / time-series momentum exit (the category family 020's
   opposite-signed signal correctly uses, given its continuation-based
   economic story) -- documented in full in prereg.md.
2. **Two extra checks beyond the standard convention**, both required by
   this iteration's task and both run pre-grid: the family-033-style
   cash-reserve build-up/drawdown check (confirming `mult_far=0.50<1.0`
   genuinely banks and later spends a reserve, not merely assumed from the
   parameter value alone), and a concrete signal-disagreement check against
   family 020's own tier assignments (72.8% disagreement, corr=-0.32) to
   substantiate the "not a re-test" claim with real development-data
   numbers rather than argument alone.
3. **Primary configuration deliberately mirrors family 020's own numeric
   choices** (same breakpoints, same `mult_near`/`max_lump_cap` values),
   documented in prereg.md as an intentional design choice so that any
   difference in outcome between the two families is attributable to the
   sign/reference-point difference rather than to different tuning
   generosity -- this makes the close similarity of the two families'
   final results a meaningful comparison rather than a coincidence.
