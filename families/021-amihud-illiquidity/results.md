# Family 021 results: Amihud illiquidity-shock sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively:
it beats plain DCA on **0 of 5** core assets, on wealth AND Sharpe, at
either fee level -- it underperforms DCA on final wealth on every single
asset. Sec 4.4's grid diagnostic also fails completely: **0 of 32**
configs (0.0%) reach the combined wealth-AND-Sharpe majority bar. DSR is
effectively zero, driven by a genuinely negative raw pooled excess Sharpe.
Sec 4.3 (rolling windows / bootstrap / placebo) was **not** run, per this
loop's established precedent of running it only when sec 4.1 passes.
Holdout was **not** opened.

## Data-feasibility finding (this iteration's required gate, full detail in prereg.md)

Volume is reliably available for all 5 core assets on development data:
SP500 (76.2% nonzero, but all zero days are 1927-1949 -- zero after
2010), GOLD (91.5% nonzero, scattered gaps, 28 after 2015), SILVER (86.4%
nonzero, the noisiest, 108 zero days after 2015), BTC (100% nonzero), OIL
(99.9% nonzero, all gaps pre-2001). No asset needed exclusion (option (a)
in the task's data-feasibility gate was not triggered; the family
proceeded across all 5 core assets with an explicit rule treating
zero/missing-volume days as "Amihud ratio undefined, excluded from
ranking" rather than fabricating a signal on a bad print). `data.py` was
extended in a small, contained way to expose `Volume` (already present in
the underlying cached CSVs; `_fetch_yf_raw` just wasn't selecting it) --
`load_dev()`/`open_holdout()`'s dev/holdout cutoff and
`check_no_raw_data_leak()` were re-verified to still pass after the
change.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family** (sec 4.1's Single-asset line),
across all 5 core assets, category **Sizing / valuation**. Signal:
`illiq_t = |return_t| / (Close_t * Volume_t)` (Amihud 2002), a trailing
causal percentile rank of `illiq_t` marks a shock day when it crosses
`elevated_pct`; the elevated regime then persists for `decay_days`
trading days after its last trigger. Deposits are sized UP
(`buy_multiplier * weekly_deposit`, cash-capped) on a week-end decision
day inside an elevated regime, funded by banking `(1 - calm_fraction)` of
every calm week's deposit -- the same weekly-decision, calm-fraction-
banking pattern family 016 uses. No sells, ever; no leverage.

**Required distinction from families 003/016/017 (this iteration's task
instruction):** prereg.md documents that 003 is a direction-agnostic,
volume-free realized-variance (2nd moment) signal; 016 is a shared,
cross-market, options-derived implied-volatility *level* with no volume
component; 017 is a bounded, volume-free, pure-price relative-strength
oscillator; this family (021) is the only one of the four that uses
volume at all, and is specifically a price-impact-per-dollar-traded
(liquidity) ratio, not a volatility, sentiment, or oscillator signal.

## Pre-grid non-degeneracy sanity check (per prereg.md, run before the grid)

| Asset | n week-end days | Frac. week-end days in elevated regime | Non-degenerate? |
|---|---|---|---|
| SP500 | 4,801 | 13.2% | PASS |
| GOLD | 1,010 | 17.1% | PASS |
| SILVER | 1,010 | 18.0% | PASS |
| BTC | 277 | 9.7% | PASS |
| OIL | 1,011 | 18.6% | PASS |

All 5 assets fire the elevated-illiquidity trigger non-trivially (roughly
10-19% of week-end decision days), well inside the pre-declared (2%, 60%)
band and far from either a near-0% dead signal or a near-100% degenerate
one -- no evidence of a futures-roll artifact driving a spurious trigger
rate on GOLD/SILVER/OIL (the risk flagged in prereg.md). Confirms the
Amihud/percentile/decay computation is implemented correctly before any
backtest is trusted.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (most aggressive grid corner: `illiq_lookback=126, elevated_pct=90, decay_days=10, buy_multiplier=2.0, calm_fraction=0.85`) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (primary config) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (aggressive corner) | PASS -- see judgment call below |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000` and `t=20000`) | PASS |
| Point-in-time macro data | N/A -- price-and-volume-only signal, no macro dependency |

**Judgment call (documented per task instruction):** the "capital never
exceeds deposits" check, copied from family 020's flat 5%-of-deposits
tolerance convention, initially FAILED on the aggressive grid corner. Root
cause: SP500's development history spans ~1928-2019 (~92 years), and this
family's calm-week cash reserve, even at a modest banking rate, compounds
substantially over that span at historical IRX rates -- a genuine interest-
income effect, not a bug (a "never invest, sit 100% in cash" control run
on the same `daily_rf` path shows a theoretical maximum interest ceiling
of over $33M against $2.4M of cumulative deposits over the full SP500 dev
history). Fixed by replacing the flat-percentage tolerance with a
principled bound derived from that same control run (capital deployed
minus cumulative deposits must never exceed the "never invest" cash
trajectory's own accumulated interest) -- logged in
`state/bugfix_log.md`. This is mathematically guaranteed by the engine's
own cash-cap invariant (`buy_usd = max(0.0, min(buy_usd, cash))` in
`engine.py`) regardless of strategy; the check re-verifies it empirically.

A second bugfix (also logged in `state/bugfix_log.md`): the initial
`PRIMARY_CONFIG["calm_fraction"]` (0.90) was not itself a declared grid
value (`[0.85, 0.95]`), the same class of mistake as the `buy_multiplier`
fix made pre-backtest. This one was caught only after the 32-config grid
had already run (at `configs.index(PRIMARY_CONFIG)`), so the grid and its
trial series were correct but the primary-config lookup crashed. Fixed to
`calm_fraction=0.95` (an existing grid point) and the script rerun; the
idempotency marker prevented double-counting the trial total on rerun
(`state/trial_counter.json["new"]` stayed at 423 + 32 = 455, not 487).

## Primary configuration: `illiq_lookback=252, elevated_pct=95, decay_days=5, buy_multiplier=2.0, calm_fraction=0.95`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 84.5011 | 85.2772 | 0.157083 | 0.153097 | NO (wealth loses) |
| GOLD | 2.22860 | 2.23123 | 0.505087 | 0.504917 | NO (wealth loses) |
| SILVER | 1.68557 | 1.68666 | 0.319857 | 0.319677 | NO (wealth loses) |
| BTC | 9.51260 | 9.85568 | 1.059761 | 1.067309 | NO (both lose) |
| OIL | 1.17865 | 1.17986 | 0.227818 | 0.227824 | NO (both lose, effectively tied) |

**Sec 4.1: FAIL** -- 0/5 core assets beat DCA on wealth AND Sharpe, at
either 0.1% or 0.25% fees (0.25% results qualitatively identical). Every
asset except BTC shows a small Sharpe *improvement* alongside a small
wealth *loss* -- the same "Sharpe wins, wealth lags" pattern several
mechanism-agnostic sizing families in this loop have shown (e.g. families
006/007/017) -- but the combined wealth-AND-Sharpe bar sec 4.1 requires is
not met on a single asset.

### Grid diagnostic (sec 4.4)

**0 of 32 configurations (0.0%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees -- need >=2/3 (21.3/32), the
weakest grid result of any family so far alongside family 019's 0/24. The
best any single config manages is 2/5 assets beating DCA on both metrics
(`cfg07`, the most aggressive `illiq_lookback=126` corner: lowest
threshold, longest decay, highest multiplier, most aggressive banking).
Every config shows the same pattern as the primary: most assets show a
Sharpe improvement without a wealth improvement, so the combined bar is
essentially never cleared.

**Sec 4.4: FAIL** (need >=21.3/32; got 0/32 = 0.0%).

CSCV probability of backtest overfitting (32-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.10** -- low,
i.e. the grid's *pattern itself* (Sharpe-only, mechanism-agnostic
smoothing with no wealth edge) generalizes consistently across
resamples. This is a case where a low PBO is not reassuring: the grid is
consistently and robustly *bad* at the wealth-AND-Sharpe bar, not
inconsistently good.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  **-0.02540** (weekly, **-0.1832 annualized**) -- **negative**.
- `N` (raw trial count, whole-loop pool): **651** (196 seeded + 455 new,
  matching `state/trial_counter.json["new"]` = 455 after this family and
  `n_total_raw` in `_run_output.json`).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **69**
  clusters (unchanged from family 020 -- this family's 32-config grid did
  not add any new distinct clusters at the rho>=0.5 threshold, consistent
  with the grid's uniform "mild Sharpe-only smoothing, no wealth edge"
  pattern across all 32 configs correlating highly with existing
  clusters).
- **DSR (N_eff-based): ~1.65e-33** -- effectively zero (a negative raw
  Sharpe can never clear a positive `SR0` threshold at any `N`).
- DSR (raw-N, conservative reference): ~2.24e-38, also effectively zero.

**Sec 4.2: FAIL**, decisively.

## Verdict

**REJECTED.** Sec 4.1 fails completely (0/5 core assets). Sec 4.4 fails
completely (0/32 grid configs reach the majority bar, the weakest grid
result alongside family 019). Sec 4.2 fails decisively (DSR ~0, negative
raw pooled excess Sharpe). Sec 4.3 was not run (only run when sec 4.1
passes, per this loop's established precedent). Holdout was **not**
opened.

## Interpretation

The illiquidity-shock trigger fires at a plausible, non-degenerate rate
(roughly 10-19% of week-end decisions per asset) and the implementation
checks all pass, so this is a genuine finding about the Amihud
time-series illiquidity-premium mechanism on this development sample, not
an implementation artifact: buying more into an asset's own recent
price-impact spikes did not capture a compensating mean-reversion return
on any of the 5 core assets over their respective development histories.
The consistent "small Sharpe improvement, small wealth loss" pattern
across nearly the entire 32-config grid (the same pattern seen in several
prior REJECTED/NEAR-MISS mechanism-agnostic sizing families) is more
consistent with "banking cash into a reserve and redeploying it later
mildly smooths the return path regardless of the specific trigger used"
than with Amihud's illiquidity-premium mechanism specifically working on
these 5 assets' realized shock episodes. Because sec 4.1 fails outright,
this interpretation is offered as context, not as a claim independently
tested via sec 4.3's placebo (which was not run, consistent with this
loop's discipline against spending the bootstrap/placebo time-budget on
families that don't clear the sec 4.1 gate).

## Trial accounting

- Seed: 196 (unchanged).
- New before this family: 423 (families 001-020).
- New from this family's 32-config grid: 32.
- New total after this family: 423 + 32 = **455** (matches
  `state/trial_counter.json`).
- Raw N at assessment: 196 + 455 = **651** (matches `n_total_raw` in
  `_run_output.json`).
- N_eff at assessment: **69** (unchanged from family 020).
- Families (new) count: 19 (was 18 before this family).

## Files

- `families/021-amihud-illiquidity/prereg.md` -- pre-registration
  (committed before any backtest), including the Volume-data feasibility
  finding.
- `families/021-amihud-illiquidity/grid_results.csv` -- full 32-config x
  5-asset x 2-fee grid.
- `families/021-amihud-illiquidity/_primary_per_asset.csv` -- primary
  config's per-asset summary.
- `families/021-amihud-illiquidity/_run_output.json` -- machine-readable
  summary of the grid/DSR/CSCV checks above.
- `src/backtest/v3/strategies/amihud_illiquidity.py` -- implementation.
- `src/backtest/v3/data.py` -- extended to expose `Volume`.
- `scripts/v3/run_021_amihud_illiquidity.py` -- end-to-end grid run
  script.
- `scripts/v3/robustness_021_amihud_illiquidity.py` -- sec 4.3 robustness
  script, written but **not run** (sec 4.1 failed).
- `state/trials/new_021_*.csv` -- 32 new trial excess-return series.
- `state/bugfix_log.md` -- two pre/post-grid bugfixes (capital-check
  tolerance, `calm_fraction` grid mismatch), neither affecting the grid's
  trial results.
