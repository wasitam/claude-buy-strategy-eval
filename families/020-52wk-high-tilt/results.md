# Family 020 results: 52-week-high proximity momentum tilt

**Verdict: NEAR-MISS.** The primary configuration passes sec 4.1 narrowly
(beats DCA on final wealth AND Sharpe on **exactly 3 of 5** core assets, at
both fee levels -- the minimum passing count). It fails sec 4.2 (DSR
effectively zero, driven by a negative raw pooled excess-return Sharpe),
sec 4.4 (only 50% of the grid reaches the majority bar, need >=2/3), and
sec 4.3's placebo leg decisively (real result lands at the 13th/37th
percentile of 60 circular-shifted placebo runs on wealth/Sharpe, need
>=95th) even though its rolling-window and bootstrap legs pass. Holdout
was **not** opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family** (sec 4.1's Single-asset line), across
all 5 core assets, category **Trend / time-series momentum exit**.
Signal: `prox_t = close_t / high52_t` where `high52_t` is a strictly
causal trailing 52-week-high (two window definitions in the grid:
`trading252` rolling max over 252 trading days, or `calendar` rolling max
over 365 calendar days). A 3-tier ladder multiplier `m_t` **increases**
buy size as `prox_t` rises (closer to the 52-week high -> bigger buy),
the opposite ordering of family 014's ladder (which increases buy size as
drawdown from the **all-time** high deepens). No sells, ever; no leverage.

**The required triple distinction (task instruction, especially the
family-014 sign point):** prereg.md documents in full why this family is
not a re-test of family 001 (binary MA trend exit vs. this family's
continuous, always-invested proximity ratio), family 005 (sign-only
trailing 12-month return vs. this family's continuous distance-from-a-
specific-price-level signal), and, most importantly, family 014 (whose
ladder multiplier rises with drawdown depth from the **all-time** high --
buy MORE far below, a value/mean-reversion logic -- vs. this family's
ladder multiplier rising with proximity to the **52-week** high -- buy
MORE near the high, a momentum/continuation logic; the literal sign
inverse, on a materially shorter reference window).

## Sign-correctness verification (required by this iteration's task,
before trusting any backtest)

On SP500 development data, using the primary config, the mean buy
multiplier on days in the **top quartile** of `prox_t` (closest to the
52-week high) was **1.500** vs. **0.6233** on days in the **bottom
quartile** (furthest below the 52-week high) -- confirming near-high days
get systematically LARGER buy orders than far-below-high days, the
intended sign, and ruling out an accidentally-inverted ladder that would
have silently reproduced family 014's logic instead.

## Pre-grid non-degeneracy sanity check (adapted for this family's ladder
shape -- see judgment call below)

The primary config's 3-tier ladder has no tier equal to exactly 1.0x
(`mult_far=0.50`, `mult_mid=0.75`, `mult_near=1.5`), so `m_t != 1.0` on
~100% of days trivially -- not a meaningful non-degeneracy signal for this
family. The substantive check instead confirms price is not stuck in a
single tier for nearly the whole sample: each tier must claim between 2%
and 98% of development days.

| Asset | Dev days | Frac. near-high tier | Frac. mid tier | Frac. far tier | Non-degenerate? |
|---|---|---|---|---|---|
| SP500 | 23,109 | 54.03% | 33.29% | 12.67% | PASS |
| GOLD | 4,848 | 43.36% | 51.40% | 5.24% | PASS |
| SILVER | 4,850 | 17.40% | 53.53% | 29.07% | PASS |
| BTC | 1,932 | 16.67% | 26.14% | 57.19% | PASS |
| OIL | 4,857 | 23.02% | 44.82% | 32.16% | PASS |

All 5 assets clear the (2%, 98%) band on every tier, with a plausible
spread across assets (SP500 spends over half its development history near
its own 52-week high, consistent with its long secular uptrend; BTC spends
the majority far from its 52-week high, consistent with its sharper
boom-bust cycles over its shorter dev window) -- confirms the proximity/
ladder computation is implemented correctly (no degenerate single-tier
trigger) before any backtest is trusted.

**Judgment call (documented per task instruction):** the original
frac-non-1.0x formulation copied from prior families' sanity-check
convention (e.g. family 019's binary weak/strong flag) does not transfer
to a 3-tier ladder whose primary config has no 1.0x tier -- it would
trivially report 100% "non-degenerate" days regardless of implementation
correctness. Adapted to the tier-frequency check above before running the
grid (recorded in prereg.md and `scripts/v3/run_020_high52wk_tilt.py`),
which is the meaningful analogue for a multi-tier ladder.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Sign check: mean multiplier, top quartile `prox_t` vs. bottom quartile | 1.500 vs 0.6233 -- PASS (near-high buys strictly larger) |
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Real `ladder=flat, mult_near=1.0` grid-arm code path (not the bypass) also reproduces plain DCA bit-for-bit | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (most aggressive grid corner: `calendar, aggressive, mult_near=2.0, max_lump_cap=3.0`) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (primary config) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (most aggressive grid corner) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000` and `t=20000`, specifically exercising the 52-week-high tracker's causal rolling/expanding maximum) | PASS |
| Point-in-time macro data | N/A -- price-only signal, no macro dependency |

## Primary configuration: `window_def=trading252, ladder=moderate, mult_near=1.5, max_lump_cap=3.0`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.2711 | 85.2772 | 0.153097 | 0.153097 | NO (wealth loses by a hair; Sharpe an effective tie) |
| GOLD | 2.23137 | 2.23123 | 0.504972 | 0.504917 | YES |
| SILVER | 1.68696 | 1.68666 | 0.319821 | 0.319677 | YES |
| BTC | 9.83953 | 9.85568 | 1.063295 | 1.067309 | NO (both lose) |
| OIL | 1.18052 | 1.17986 | 0.227999 | 0.227824 | YES |

**Sec 4.1: PASS** -- 3/5 core assets (GOLD, SILVER, OIL) at both 0.1% and
0.25% fees (0.25% results qualitatively identical, see
`_primary_per_asset.csv`), exactly the minimum passing count. Every
passing margin is small in absolute terms (a few basis points of terminal
wealth, a few thousandths of Sharpe) -- the strategy is not decisively
beating DCA on any asset, it is narrowly ahead on 3 and narrowly (SP500)
or clearly (BTC) behind on the other 2.

### Grid diagnostic (sec 4.4)

**16 of 32 configurations (50.0%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees -- need >=2/3 (21.3/32). The
pattern is clean and interpretable: every `ladder=mild` and
`ladder=moderate` configuration (16/16, both window definitions, both
`mult_near` values, both `max_lump_cap` values) reaches the majority bar
at 3/5 or 4/5 assets on Sharpe, but every `ladder=aggressive` config drops
to 1-2/5 (the far-below-high floor of `mult_far=0.30` combined with the
wider `far_thresh=0.70` band bites too hard, especially on BTC and SP500's
long drawdowns), and every `ladder=flat` config (the true zero-effect arm)
reproduces DCA exactly, 0/5 by construction. `window_def` (trading252 vs.
calendar) makes essentially no difference within a given ladder/mult_near/
max_lump_cap combination -- the two window definitions produce nearly
identical grid rows.

**Sec 4.4: FAIL** (need >=21.3/32; got 16/32 = 50.0%).

CSCV probability of backtest overfitting (32-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.486** -- close
to a coin flip, the highest (most concerning) PBO of any family in this
loop so far, consistent with the grid's clean but narrow-margin,
ladder-severity-dependent pattern being at meaningful risk of being a
resampling/overfitting artifact rather than a robust effect.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series
  (strategy weekly NAV return minus DCA weekly NAV return, averaged across
  the 5 assets): **-0.02638** (weekly, **-0.1902 annualized**) --
  **negative**, despite the primary config passing sec 4.1's per-asset
  majority count. This is the same pattern family 019 showed at the
  extreme (0/5, uniformly negative) but here it coexists with a 3/5
  sec-4.1 pass: SP500 and BTC's losses (BTC's especially, given its
  outsized weekly volatility) dominate the equal-weighted pooled average
  even though GOLD/SILVER/OIL individually pass.
- `N` (raw trial count, whole-loop pool): **619** (196 seeded + 391 from
  families 001-019 + 32 new from this family's grid; matches the sanity
  check 196+423=619, `state/trial_counter.json["new"]`=423 after this
  family).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **69**
  clusters (up from family 019's 61 -- this family's 32-config grid
  contributes 8 new distinct clusters, more than most prior families'
  grids, consistent with the `ladder` severity levels and `window_def`
  choice producing meaningfully different excess-return paths rather than
  all correlating >=0.5 with one existing cluster).
- **DSR (N_eff-based): ~2.52e-69** -- effectively zero, and, as with
  family 019, doubly so because the raw excess Sharpe is negative to begin
  with (a negative Sharpe can never clear a positive `SR0` threshold at
  any `N`). The excess series is extremely heavy-tailed (skew -28.66,
  kurtosis 1322.9 -- the highest kurtosis of any family in this loop by a
  wide margin, driven by the `max_lump_cap`-bounded but still large
  catch-up-lump weeks concentrated around 52-week-high crossings).
- DSR (raw-N, conservative reference): ~2.34e-81, also effectively zero.

**Sec 4.2: FAIL**, decisively -- a negative raw pooled excess Sharpe cannot
clear the trial-count-adjusted DSR bar at either `N` or `N_eff`.

### Robustness (sec 4.3, run in full since sec 4.1 passed)

Per prereg.md's declared time-budget (n_sims=60 for bootstrap/placebo,
consistent with the task's stated convention), run on the primary config.

**Rolling windows** (3y/5y for SP500/GOLD/SILVER/OIL, 2y for BTC, stepping
20 trading days, 3,439 total windows): **67.5% beat DCA on wealth, 63.2%
beat DCA on Sharpe**, both **above the 60% bar -- PASS**. Every asset/
window combination individually clears 60% except BTC_2y (36.1% wealth,
30.6% Sharpe -- BTC alone would fail this leg), but the pooled/overall
figure the sec 4.3 rule is stated against passes.

**Block bootstrap** (500-history budget reduced to the established n_sims=60
convention, 4-week blocks, SP500 only as the representative asset per
families 003/005's precedent): raw-path beats DCA on wealth in **53.3%**
of histories (bare majority) and Sharpe in **68.3%**; detrended beats DCA
on wealth in **70.0%** and Sharpe in **65.0%** -- both legs clear a
majority -- **PASS**.

**Placebo** (circular-shift the primary config's own `prox_t`-derived
multiplier sequence 60 times, SP500): the real result lands at the
**13.3th percentile on wealth** and the **36.7th percentile on Sharpe** of
the placebo distribution -- need **>=95th** -- **FAIL**, decisively. The
real (correctly time-aligned) signal performs *worse* than the median
randomly-shifted version of its own multiplier sequence on wealth, and
only middling on Sharpe -- strong evidence that the specific temporal
alignment of the 52-week-high proximity signal is not doing real
forecasting work; the sec 4.1 pass is much more consistent with a
narrow-margin, mechanism-agnostic effect of *some* time-varying buy-size
multiplier (any one, correctly aligned or not) mildly smoothing the return
path, than with George & Hwang's specific continuation mechanism actually
being captured on this development sample.

**Sec 4.3: FAIL overall** (rolling and bootstrap legs pass; the placebo
leg -- the check most directly diagnostic of whether the *signal itself*
is doing the work, rather than just "some correlated sizing tilt" -- fails
decisively). Per the AND logic of sec 4.3 ("must beat DCA in... on wealth
and on Sharpe separately" for each sub-check), the family does not clear
sec 4.3 as a whole.

## Verdict

**NEAR-MISS.** Sec 4.1 passes narrowly (exactly 3/5 core assets, small
margins). Sec 4.2 fails decisively (DSR ~0, negative raw pooled excess
Sharpe). Sec 4.4 fails (50.0% of grid reaches the majority bar, need
66.7%) with the highest CSCV PBO (0.486) of any family in this loop so
far. Sec 4.3 fails overall on its placebo leg despite passing its rolling-
window and bootstrap legs. Holdout was **not** opened (sec 4.2/4.3/4.4 all
fail, matching this loop's holdout-eligibility precedent of requiring all
of sec 4.1-4.4 to pass before considering a finalist).

## Interpretation

The result pattern here is unusually informative for a "near-miss": every
individual diagnostic that isolates *whether the George & Hwang mechanism
specifically* is responsible for the sec-4.1 pass says no. The placebo
test is the sharpest of these -- a randomly time-shifted version of the
same multiplier sequence typically does *better* on wealth than the real,
correctly-aligned signal, which is close to the opposite of what a real
continuation effect should produce. Combined with the CSCV PBO of 0.486
(the highest/most concerning of any family so far) and the grid's clean
`ladder`-severity-dependent split (mild/moderate pass, aggressive fails --
i.e. the effect only survives at the gentlest tilts, where the strategy is
closest to plain DCA to begin with), the most plausible reading is that
the primary config's narrow sec-4.1 win reflects the same "any gentle,
roughly-DCA-shaped sizing tilt mildly smooths the pooled return path"
pattern several prior mechanism-agnostic families in this loop have shown
(003/005/006/007/017/018), not George & Hwang's specific 52-week-high
anchoring/continuation mechanism. This is offered as an honest post-hoc
interpretation of the diagnostic pattern, not a claim that has itself been
independently tested, consistent with this loop's discipline against
chasing an ex-post narrative into a new grid arm.

## Trial accounting

- Seed: 196 (unchanged).
- New before this family: 391 (families 001-019).
- New from this family's 32-config grid: 32.
- New total after this family: 391 + 32 = **423** (matches
  `state/trial_counter.json`).
- Raw N at assessment: 196 + 423 = **619** (matches `n_total_raw` in
  `_run_output.json`).
- N_eff at assessment: **69** (up from family 019's 61 -- 8 new distinct
  clusters from this family's grid).
- Families (new) count: 18 (was 17 before this family).

## Files

- `families/020-52wk-high-tilt/prereg.md` -- pre-registration (committed
  before any backtest).
- `families/020-52wk-high-tilt/grid_results.csv` -- full 32-config x
  5-asset x 2-fee grid.
- `families/020-52wk-high-tilt/_primary_per_asset.csv` -- primary config's
  per-asset summary.
- `families/020-52wk-high-tilt/_run_output.json` -- machine-readable
  summary of the grid/DSR/CSCV checks above.
- `families/020-52wk-high-tilt/_robustness_output.json` -- machine-readable
  rolling-window/bootstrap/placebo results.
- `src/backtest/v3/strategies/high52wk_tilt.py` -- implementation.
- `scripts/v3/run_020_high52wk_tilt.py` -- end-to-end grid run script.
- `scripts/v3/robustness_020_high52wk_tilt.py` -- sec 4.3 robustness script.
- `state/trials/new_020_*.csv` -- 32 new trial excess-return series.
