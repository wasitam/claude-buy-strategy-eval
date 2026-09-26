# Family 046 results: VVIX vol-of-vol regime sizing

**Verdict: NEAR-MISS.** The primary configuration passes sec 4.1 (4/5
core assets beat DCA on wealth AND Sharpe, at both fee levels) and sec
4.4 (100% of the grid clears the majority bar, the strongest grid result
of any family in this loop) but fails sec 4.2 (DSR effectively zero
despite a positive raw Sharpe, driven by extreme kurtosis) and sec 4.3
(rolling windows fail decisively; bootstrap/placebo not completed within
the iteration's time budget once the verdict was already settled by
sec 4.2's failure). Holdout was **not** opened (not a finalist).

## Data feasibility

`^VVIX` (CBOE VVIX Index) is reachable via yfinance:
4,955 rows, starting 2007-01-03. Dev-period history (~13.0 years through
2019-12-31) is comparable to `^VIX3M`'s ~13.4 years already used
successfully by family 041. No substitute idea was needed.

## Sign decision

Adopted the risk-off/defensive-bank sign (elevated VVIX percentile -> buy
LESS; depressed -> buy MORE), not family 016's contrarian-buy-into-fear
sign: VVIX is a leading-fragility indicator (uncertainty about VIX's own
future path), not a signal that an already-underway selloff is a rebound
opportunity, so the economically motivated sign is defensive, not
contrarian.

## Required distinction from families 016 (VIX level), 025 (VIX-vs-realized-vol
spread) and 041 (VIX3M/VIX term-structure ratio)

Verified concretely on real 2007-2019 SP500 data, not just asserted:
- Raw VVIX-vs-VIX level correlation: only +0.264.
- Flag-agreement with family 016's elevated-VIX flag: 56.1%.
- Flag-agreement with family 025's elevated-VRP flag: 55.2%.
- Flag-agreement with family 041's non-backwardation flag: 45.8%.

All four agreement rates sit meaningfully between 0% and 100%, confirming
VVIX's signal is not a relabeling of any prior VIX-derived family's
signal. Concrete divergence example: 2014-12-10, VIX moderate (18.53) but
VVIX at its own 97.8th trailing percentile -- a case where the market's
current fear level is unremarkable but uncertainty about future
volatility is near a 13-year extreme. Contrast/comovement example:
2008-10-20 to 2008-11-24 (the GFC), both VIX and VVIX simultaneously near
their own historical highs -- confirming the two series don't always
diverge, only that they can.

## Implementation checks (all passed)

Degenerate bypass reproduces DCA bit-for-bit; the `k=0` second reference
point also reproduces DCA; no negative cash/units; capital never exceeds
cumulative deposits+interest via the principled ceiling-bound method;
no-lookahead perturbation test at t=6000 and t=20000; pre-grid
non-degeneracy check passed on all 5 assets; primary config's realized
cash-reserve dynamics differ meaningfully from DCA's in the correct
direction.

## Sec 4.1 (single-asset, >=3/5, both fees): PASS

Primary config (`vvix_lookback=252, k=1.0, min_mult=0.5, max_mult=2.0`)
beats DCA on wealth AND Sharpe on **4/5 core assets** (SP500 razor-thin,
GOLD, SILVER, OIL win; BTC loses on wealth but wins on Sharpe) at both
0.1% and 0.25% fees.

## Sec 4.2 (DSR >= 0.95): FAIL

DSR (N_eff-based) = 3.30e-23 (N_eff=133, raw N=1413). The raw pooled
excess-return Sharpe is genuinely positive (+0.0127/week, +9.16%/yr
annualized) -- this family's edge is real in a naive sense -- but the
excess-return series is extremely fat-tailed (skew=27.7, kurtosis=1444.6),
driving the required SR0 hurdle (0.132/week) far above the realized
Sharpe. This is the sharpest illustration in this loop yet of exactly
what the DSR check is designed to catch: an apparently-positive edge that
is entirely explainable by a handful of extreme outlier weeks rather than
a stable, repeatable pattern.

## Sec 4.3 (robustness): FAIL

**Rolling windows** (pooled across 3,439 windows, matching family 020's
window count): 24.9% beat DCA on wealth, 25.9% on Sharpe (need >60%) --
decisive FAIL. Per-asset: SP500 3y/5y both fail badly (8.05%/9.12% and
9.42%/11.25%); GOLD/SILVER/OIL's 5-year windows individually clear 60%+
but their 3-year windows do not; BTC's 2-year windows fail badly
(15.28%/22.22%).

**Block bootstrap and placebo circular-shift**: not completed within this
iteration's time budget. Once sec 4.2's DSR failure and sec 4.3's
rolling-window failure were both already decisive, running the remaining
n_sims~60 legs to completion would not change the verdict (a family must
clear every sec 4.1-4.4 check to become a finalist, not a majority of
them), so the run was stopped rather than continuing to consume compute
on a settled outcome -- the same time-budget discipline the plan uses
elsewhere (e.g. skipping sec 4.3 entirely when sec 4.1 fails). This is
logged here as an explicit, honest gap rather than a fabricated result.

## Sec 4.4 (grid, >=2/3 beats DCA): PASS

**36/36 (100%)** of the grid clears the majority-of-assets bar at 0.1%
fee -- the strongest sec 4.4 result of any family tested in this loop.
CSCV PBO = 0.371 (moderate).

## Interpretation

VVIX-regime sizing is the strongest single-asset result this loop has
produced on the raw win-rate checks (sec 4.1 and sec 4.4 both pass
cleanly), which makes it a particularly clean illustration of why this
loop runs sec 4.2-4.4 rather than stopping at sec 4.1: the apparent edge
is concentrated in a small number of extreme weeks (kurtosis 1444.6) and
does not survive being tested on rolling sub-windows of the same
development period. Not a finalist.

## Trial accounting

`state/trial_counter.json`: seed=196, new=1217 (1181 prior + 36 this
grid), families_new=44, holdout_opens=0. Sanity check: 196+1217=1413,
matching `_run_output.json`'s `n_total_raw`. N_eff=133.
