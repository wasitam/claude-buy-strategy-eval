# Family 047 results: CBOE SKEW Index tail-risk-pricing regime sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1
decisively (1/5 core assets, need >=3/5) and sec 4.4 decisively (0/36
grid configs clear the majority bar). Sec 4.2's DSR is effectively zero
with a strongly negative raw pooled excess Sharpe. Sec 4.3 was not run,
per established loop precedent (sec 4.1 already fails, so no remaining
check can change the verdict). Holdout was **not** opened (not a
finalist).

## Data feasibility

`^SKEW` (CBOE SKEW Index) is reachable via yfinance: 9,177 daily rows,
starting **1990-01-02** -- essentially identical dev-period history
length to `^VIX` itself (~30.0 years through 2019-12-31), the longest
history of any volatility-derived signal used in this loop so far (2.3x
`^VVIX`'s ~13.0 years, family 046). No substitute idea was needed.

## Sign decision

Adopted the risk-off/defensive-bank sign, the same as families
011/019/027/032/041/046 (not family 016's contrarian-buy-into-realized-
fear sign): SKEW is a forward-pricing signal about tail-crash
probability that has not yet materialized in the underlying asset's own
price action, so banking cash ahead of it is the more principled
response. Elevated SKEW percentile -> buy LESS; depressed -> buy MORE
(up to a capped catch-up lump).

## Required distinction from families 016 (VIX level), 025 (VIX-vs-realized
spread), 041 (VIX3M/VIX term structure) and 046 (VVIX vol-of-vol)

Verified concretely on real 1990-2019 SP500 development data (7,559
overlapping trading days):

- Raw SKEW-vs-VIX level correlation: only **-0.235** (weak, and of the
  opposite sign from a naive "both just measure fear" prior).
- Flag-agreement with family 016's elevated-VIX flag: 45.3%.
- Flag-agreement with family 025's elevated-VRP flag: 48.7%.
- Flag-agreement with family 041's non-backwardation flag: 52.8%.
- Flag-agreement with family 046's elevated-VVIX flag: 52.2%.

All four agreement rates sit strictly between 0% and 100%, confirming
SKEW's signal is not a relabeling of any prior volatility-derived
family's signal. Concrete divergence example: **2019-12-19**, VIX
closed at 12.50 (an unusually calm 8.3rd trailing percentile) while
SKEW closed at 150.14, its own all-time-record **100th** trailing
percentile through that date -- the textbook "complacent VIX, but the
tails are getting pricier" episode. Concrete inverse-divergence
example: **1991-01-14** (Gulf War onset), VIX at 36.20 (elevated, ~99.6th
percentile) while SKEW sat at only its 13.5th percentile -- an acute,
already-realized macro shock with no accompanying rise in tail-pricing
asymmetry, the mirror image of the December 2019 case (414 pre-2020 days
meet the joint "VIX>90th pctile, SKEW<30th pctile" condition, confirming
this is not a one-off artifact). Concrete comovement/contrast example:
2008-10-20 to 2008-11-24 (the GFC), VIX pinned near its own all-time
highs throughout while SKEW's own percentile fluctuated in a much wider
band (0.59-1.00) -- the two series can coincide during a shared crisis,
but do not move in lockstep even then.

## Implementation checks (all passed)

Degenerate bypass reproduces DCA bit-for-bit; the `k=0` second reference
point also reproduces DCA bit-for-bit; no negative cash/units on DCA,
the primary config, and the grid's most-aggressive corner; capital never
exceeds cumulative deposits+interest via the principled ceiling-bound
method; no-lookahead perturbation test at t=6000 and t=20000; pre-grid
non-degeneracy check passed on all 5 assets (multiplier std ranges
0.293-0.502, all well above the 0.01 floor); primary config's realized
cash-reserve dynamics differ meaningfully from DCA's in the correct
direction (avg cash $110.47 vs. DCA's $103.88; $144.24 avg cash during
elevated-SKEW/low-multiplier weeks vs. $105.27 during depressed-SKEW/
high-multiplier weeks).

## Sec 4.1 (single-asset, >=3/5, both fees): FAIL

Primary config (`skew_lookback=252, k=1.0, min_mult=0.5, max_mult=2.0`)
beats DCA on wealth AND Sharpe on only **1/5 core assets** (SILVER only,
and razor-thin: strategy wealth 1.68694x vs. DCA's 1.68666x, Sharpe
0.31971 vs. 0.31968) at both 0.1% and 0.25% fees. SP500, GOLD and BTC
lose on both wealth and Sharpe; OIL wins wealth (1.18004x vs. 1.17986x)
but loses Sharpe (0.22770 vs. 0.22782). Decisive FAIL (need >=3/5).

## Sec 4.2 (DSR >= 0.95): FAIL

DSR (N_eff-based) = 1.54e-55 (N_eff=134, raw N=1449). The raw pooled
excess-return Sharpe is genuinely **negative** (-0.0241/week, -17.4%/yr
annualized), with extreme kurtosis (1299.9) and strongly negative skew
(-29.5) -- unlike family 046 (VVIX), where the raw Sharpe was positive
before the DSR penalty erased it, this family's primary config simply
does not beat DCA in a naive sense either, on the pooled excess series.

## Sec 4.3 (robustness): NOT RUN

Sec 4.1 already fails decisively (1/5, need >=3/5) and sec 4.4 fails at
0% (need >=2/3), so no remaining sec 4.3 check (rolling windows, block
bootstrap, placebo) could change the verdict -- a family must clear
every sec 4.1-4.4 check to become a finalist. Per the established
time-budget discipline this loop uses elsewhere (e.g. family 046's own
sec 4.3 partial-completion note), the robustness suite was not run at
all this iteration, and this is logged here as an explicit, honest gap
rather than a fabricated result.

## Sec 4.4 (grid, >=2/3 beats DCA): FAIL

**0/36 (0%)** of the grid clears the majority-of-assets bar at 0.1%
fee -- the weakest sec 4.4 grid result of any family tested in this loop
so far (previously the weakest was family 021's 8.3%). CSCV PBO = 0.857,
the highest (most overfitting-prone) diagnostic value of any family so
far, though moot given the grid's outright 0% pass rate.

## Interpretation

SKEW's data feasibility, sign reasoning and distinction from every
prior VIX-derivative family in this loop were all confirmed cleanly and
concretely -- this is a genuinely different signal, not a relabeling.
But the identically-shaped functional form (continuous percentile-
scaled inverted multiplier, same grid shape, same risk-off sign) that
produced family 046's (VVIX) strongest-yet sec 4.1/4.4 result before
failing on DSR and rolling windows, produced almost no edge at all when
applied to SKEW: the primary config loses to DCA on 4/5 core assets, and
literally none of the 36 grid configurations clear even the basic
majority-of-assets bar. This is a useful negative result: a template
that works reasonably well (on the raw win-rate checks, before the DSR/
robustness gauntlet) for one option-derived volatility signal does not
automatically transfer to every signal with a plausible risk-off sign
and a similar construction -- SKEW's own economic content (crash-tail
pricing asymmetry at a single tenor) appears not to carry the kind of
exploitable, DCA-beating signal this loop is looking for, at least in
this functional form. Not a finalist.

## Trial accounting

`state/trial_counter.json`: seed=196, new=1253 (1217 prior + 36 this
grid), families_new=45, holdout_opens=0. Sanity check: 196+1253=1449,
matching `_run_output.json`'s `n_total_raw`. N_eff=134.
