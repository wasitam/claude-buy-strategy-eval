# Family 022 results: Presidential election-cycle deposit timing

**Verdict: REJECTED.** The primary configuration fails sec 4.1: it beats
plain DCA on wealth AND Sharpe on only **2 of 5** core assets (need >=3),
at both 0.1% and 0.25% fees. Sec 4.4's grid diagnostic also fails
completely: **0 of 24** configs (0.0%) reach the combined wealth-AND-
Sharpe majority bar (>=3/5 assets) -- the best any single config manages
is exactly 3/5 (two grid arms, neither the primary). Sec 4.3
(rolling windows / bootstrap / placebo) was **not** run, per this loop's
established precedent of running it only when sec 4.1 passes. Holdout was
**not** opened.

## By-hand cycle-year cross-check (required before any backtest)

`cycle_year()` was verified against 16 known calendar years before the
sanity check or any backtest ran: 2000/2004/2008/2012/2016/2020/2024 all
map to 4 (election years); 2001/2005/2021 to 1 (post-election);
2002/2006/2022 to 2 (midterm); 2003/2007/2023 to 3 (pre-election). All 16
matched by hand. In particular **2008 = year 4 of the 2004-2008 term
(election year, "strong" under the primary config)** and **2000 = year 4
of the 1996-2000 term (also "strong")** were confirmed, exactly the two
crisis-year cases flagged as a risk in `prereg.md` before any grid ran.

## Primary-config-in-grid verification (per family 021's lesson)

Checked programmatically, before the grid ran: every value in
`PRIMARY_CONFIG` (`n_weak_years=2, include_election_year_in_strong=True,
bank_fraction=0.5, max_lump_multiple=8`) is a member of its `GRID[...]`
list, and `PRIMARY_CONFIG in grid_configs()` -- both asserted at module
import time in `election_cycle.py` and re-checked explicitly in the run
script before any backtest. Both passed; no mismatch was found (unlike
family 021's two pre/post-grid bugs).

## Pre-grid non-degeneracy sanity check (per prereg.md, run before the grid)

| Asset | n days | Frac. days in strong-year regime | Non-degenerate? |
|---|---|---|---|
| SP500 | 23,109 | 50.01% | PASS |
| GOLD | 4,848 | 48.35% | PASS |
| SILVER | 4,850 | 48.33% | PASS |
| BTC | 1,932 | 56.73% | PASS |
| OIL | 4,857 | 48.36% | PASS |

All 5 assets land within a few points of the expected ~50% (a 2-year/
2-year split of the 4-year cycle), well inside the pre-declared (35%,
65%) band. BTC's 56.73% is the furthest from 50%, consistent with its
short (2014-2019) development window not spanning full 4-year cycles
symmetrically -- flagged in `prereg.md` as the least informative of the
5 assets for this signal, confirmed here quantitatively. Confirms the
cycle-year/strong-weak computation is implemented correctly before any
backtest is trusted.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000`) | PASS |
| Point-in-time macro data | N/A -- calendar-only signal, no macro dependence |
| Capital deployed never exceeds cumulative deposits + interest (primary config, family 021's principled-bound method) | PASS |

No implementation-check failures or bugfixes were needed for this family
(no entry added to `state/bugfix_log.md`).

## Primary configuration: `n_weak_years=2, include_election_year_in_strong=True, bank_fraction=0.5, max_lump_multiple=8`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.5770 | 85.2772 | 0.162617 | 0.153097 | YES |
| GOLD | 2.14557 | 2.23123 | 0.477590 | 0.504917 | NO (both lose) |
| SILVER | 1.63668 | 1.68666 | 0.310370 | 0.319677 | NO (both lose) |
| BTC | 9.98428 | 9.85568 | 1.129493 | 1.067309 | YES |
| OIL | 1.18186 | 1.17986 | 0.217893 | 0.227824 | NO (wealth wins, Sharpe loses) |

**Sec 4.1: FAIL** -- 2/5 core assets beat DCA on wealth AND Sharpe (need
>=3), at both 0.1% and 0.25% fees (0.25% results qualitatively
identical: still 2/5). SP500 and BTC clear the bar; GOLD and SILVER lose
on both metrics; OIL wins on wealth alone (Sharpe loses narrowly).

### Grid diagnostic (sec 4.4)

**0 of 24 configurations (0.0%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees -- need >=2/3 (16/24). The
best any single config manages is exactly 3/5 assets beating DCA on both
metrics, reached by `cfg01` (`n_weak_years=2,
include_election_year_in_strong=True, bank_fraction=0.3,
max_lump_multiple=8`) and `cfg03` (the primary's own `bank_fraction=0.5`
variant) at 0.1% fee only -- neither reaches 3/5 at 0.25% fee, and
neither is the declared primary. The `include_election_year_in_strong=
False` arms (moving the election year itself out of the strong bucket)
generally do slightly worse on the wealth+Sharpe combined bar than the
matching `True` arms, the opposite of what the risk section in
`prereg.md` speculated might happen if 2008/2000 were driving a
spurious result via the crisis-year confound -- some evidence the
result is not simply "sensitive to whether 2008/2000 are in or out,"
though sec 4.1's failure makes this a secondary observation, not a
tested claim (sec 4.3's placebo, which would test this more rigorously,
was not run).

**Sec 4.4: FAIL** (need >=16/24; got 0/24 = 0.0%).

CSCV probability of backtest overfitting (24-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.614** --
notably higher than family 021's 0.10 and most other REJECTED families
in this loop's ledger, meaning the grid's *ranking* of configs by
in-sample performance does not reliably predict which configs perform
well out-of-sample within the grid's own resamples. This is consistent
with a genuinely weak, noisy signal (a handful of long, low-frequency
4-year cycles gives the grid comparatively few independent
"observations" to rank configs by, unlike families 006/007/018's much
higher-frequency calendar signals) rather than with any single config
being robustly good or robustly bad.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  **-0.008742** (weekly, **-0.06304 annualized**) -- **negative**.
- `N` (raw trial count, whole-loop pool): **675** (196 seeded + 479 new,
  matching `state/trial_counter.json["new"]` = 479 after this family and
  `n_total_raw` in `_run_output.json`).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **69**
  clusters (unchanged from families 020/021 -- this family's 24-config
  grid did not add any new distinct clusters at the rho>=0.5 threshold).
- **DSR (N_eff-based): ~1.63e-27** -- effectively zero (a negative raw
  Sharpe can never clear a positive `SR0` threshold at any `N`).
- DSR (raw-N, conservative reference): ~2.75e-31, also effectively zero.

**Sec 4.2: FAIL**, decisively.

## Verdict

**REJECTED.** Sec 4.1 fails (2/5 core assets, need >=3). Sec 4.4 fails
(0/24 grid configs reach the majority bar; need >=16/24). Sec 4.2 fails
decisively (DSR ~0, negative raw pooled excess Sharpe). Sec 4.3 was not
run (only run when sec 4.1 passes, per this loop's established
precedent). Holdout was **not** opened.

## Interpretation

SP500 and BTC individually clear the wealth-AND-Sharpe bar under the
literature's literal "second half of term" primary split, consistent
with Santa-Clara & Valkanov's own equity-market result showing up on the
one equity asset in this loop's universe -- but GOLD and SILVER lose on
both metrics, and OIL only half-clears (wealth without Sharpe), so the
pooled, cross-asset picture the >=3/5 rule requires is not met. The
grid's high CSCV PBO (0.614) and the fact that no config manages more
than 3/5 even before accounting for fee stress is consistent with the
risk flagged in `prereg.md`: with only ~5 complete 4-year cycles in most
assets' development history (fewer for BTC), this family has far fewer
independent repetitions of its underlying signal than families
006/007/018, so a modest, asset-mixed result like this one is hard to
distinguish from noise on development data alone -- exactly the caution
the prereg's "expected sign" section called for in advance. The
2008/2000 crisis-year confound flagged before backtesting does not
appear to be straightforwardly inflating the result (the
`include_election_year_in_strong=False` grid arms, which pull those two
years out of the strong bucket, do not perform better), but sec 4.1's
outright failure makes this an observation from the grid diagnostic, not
a claim independently tested via sec 4.3's placebo test (not run,
consistent with this loop's discipline against spending the bootstrap/
placebo time-budget on families that don't clear the sec 4.1 gate).

## Trial accounting

- Seed: 196 (unchanged).
- New before this family: 455 (families 001-021).
- New from this family's 24-config grid: 24.
- New total after this family: 455 + 24 = **479** (matches
  `state/trial_counter.json`).
- Raw N at assessment: 196 + 479 = **675** (matches `n_total_raw` in
  `_run_output.json`).
- N_eff at assessment: **69** (unchanged from families 020/021).
- Families (new) count: 20 (was 19 before this family).

## Files

- `families/022-election-cycle/prereg.md` -- pre-registration (committed
  before any backtest).
- `families/022-election-cycle/grid_results.csv` -- full 24-config x
  5-asset x 2-fee grid.
- `families/022-election-cycle/_primary_per_asset.csv` -- primary
  config's per-asset summary.
- `families/022-election-cycle/_run_output.json` -- machine-readable
  summary of the grid/DSR/CSCV checks above.
- `src/backtest/v3/strategies/election_cycle.py` -- implementation
  (includes an import-time assertion that `PRIMARY_CONFIG` values all
  appear in `GRID` and that `PRIMARY_CONFIG` is a member of
  `grid_configs()`, per family 021's lesson).
- `scripts/v3/run_022_election_cycle.py` -- end-to-end grid run script
  (by-hand `cycle_year()` cross-check -> primary-in-grid verification ->
  pre-backtest sanity check -> implementation checks -> grid -> DSR/N_eff
  -> assessment).
- `state/trials/new_022_*.csv` -- 24 new trial excess-return series.
