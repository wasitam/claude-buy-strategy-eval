# Family 019 results: OECD Composite Leading Indicator (CLI) regime switch

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively:
it beats plain DCA on final wealth AND Sharpe on **0 of 5** core assets at
either fee level (need >=3/5). Sec 4.4's grid diagnostic fails even more
starkly: **0 of 24** grid configurations (0.0%) reach the combined
majority bar (need >=16/24). DSR is effectively zero (in fact the pooled
excess-return series has a *negative* raw Sharpe). Holdout was **not**
opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family** (sec 4.1's Single-asset line),
across all 5 core assets, category **Regime switch (macro)**. Signal:
FRED `USALOLITONOSTSAM` (OECD's normalized US composite leading
indicator), point-in-time lagged 60 calendar days, normalized against its
own trailing window (`zscore` or `percentile`), triggering a **weak**
regime (bank cash, buy only `weak_tilt_fraction * weekly_deposit`) when
the normalized signal reads below a method-specific threshold, and a
**strong** regime (buy the week's deposit plus a capped catch-up lump
from banked cash) otherwise. No sells, ever; no leverage.

**Data reachability (task instruction, verified before writing
prereg.md):** `USALOLITONOSTSAM` is reachable via FRED (1955-01-01
through 2024-01-01, 829 monthly rows) — no substitution needed.

**The triple distinction (required by this iteration's task):** prereg.md
documents, with a summary table, that this family's data source (a
real-economy composite leading-activity index: new orders, permits,
confidence, minor spread/equity sub-components, OECD-normalized) is a
genuinely different construction and answers a genuinely different
question from both family 011 (BAA-AAA credit spread / NFCI — a
market-priced financial-conditions/credit-stress signal) and v2.1
Strategy D (Fed funds target, DGS2, T10Y2Y, DFII10, FEDTARMD — a
policy-rate/yield-curve stance signal). None of family 011's or Strategy
D's series appear as inputs to `USALOLITONOSTSAM`, and the three signal
families have historically diverged from one another at points cited in
prereg.md (e.g. early 2007-08: Fed easing while credit spreads widened;
liquidity-driven credit blowouts like 1998 LTCM or parts of 2011 with
little advance CLI deterioration).

**Data-handling judgment call, flagged before any backtest (task
instruction: "follow the point-in-time/publication-lag discipline...
check both" family 011's `fetch_fred_macro()` usage and v2's
`regimes.py` ALFRED-vintage pattern):** checked live against ALFRED's own
vintage-download list for `USALOLITONOSTSAM`
(`alfred.stlouisfed.org/series/downloaddata?seid=USALOLITONOSTSAM`) —
true point-in-time vintages only exist from **2018-07-17** onward (62
vintages total), covering almost none of this family's development
sample (each core asset's start of history through 2019-12-31). This is
the same kind of vintage-coverage wall `v2/regimes.py`'s own R4
(`FEDTARMD`, vintages only from 2015-12-16) documents for its own signal.
Resolution: a conservative fixed **60-calendar-day** publication lag
(more conservative than family 011's 45-day BAA/AAA lag, consistent with
the OECD's documented ~5-6-week release schedule plus a safety margin)
stands in for full vintage reconstruction, with the honestly-flagged
limitation that this protects against look-ahead in *availability
timing* but not fully against a later-revised (and therefore more
informative-looking) historical CLI value appearing in the pre-2018-07
portion of the sample. Recorded here regardless of verdict, as promised
in prereg.md.

## Pre-grid non-degeneracy sanity check (required by this iteration's
task, before any grid run)

The primary config's (`normalization_method=zscore, lookback_years=10,
threshold_level=1` i.e. `z < -0.5`) weak-regime condition was confirmed
to fire non-trivially — neither near-0% nor near-100% of development
days — against each asset's own trading-day index, before any grid
backtest was trusted:

| Asset | Dev days | Weak days | Frac. weak |
|---|---|---|---|
| SP500 | 23,109 | 4,421 | 19.13% |
| GOLD | 4,848 | 1,214 | 25.04% |
| SILVER | 4,850 | 1,215 | 25.05% |
| BTC | 1,932 | 275 | 14.23% |
| OIL | 4,857 | 1,214 | 24.99% |

All 5 assets land comfortably within the pre-registered (2%, 98%) sanity
band, with a plausible spread (14-25%) reflecting each asset's different
development-window overlap with historical US slowdown/recession
episodes — confirms the regime computation is implemented correctly (no
degenerate near-0%/near-100% trigger) before any backtest is trusted.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (cash never negative under the engine's cash-capped fill logic) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000` and `t=20000`) | PASS |
| Macro-specific: shortening the publication lag from the documented 60 days to 0 days changes 4.84% of historical regime readings (SP500) -- confirms the lag is doing real work, not a no-op, before trusting the documented-lag-only backtests below | PASS |
| Point-in-time macro data (documented 60-day fixed lag, ALFRED true-vintage coverage gap flagged above) | PASS |

## Primary configuration: `normalization_method=zscore, lookback_years=10, threshold_level=1 (z<-0.5), weak_tilt_fraction=0.0, max_lump_multiple=6`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 84.716 | 85.277 | 0.15264 | 0.15310 | NO (both fail) |
| GOLD | 2.058 | 2.231 | 0.43321 | 0.50492 | NO (both fail) |
| SILVER | 1.526 | 1.687 | 0.27238 | 0.31968 | NO (both fail) |
| BTC | 9.740 | 9.856 | 1.06382 | 1.06731 | NO (both fail) |
| OIL | 1.092 | 1.180 | 0.18214 | 0.22782 | NO (both fail) |

**Sec 4.1: FAIL**, 0/5 core assets at both fee levels (0.25% results are
qualitatively identical — see `_primary_per_asset.csv`). Unlike most
prior families in this loop, this is not a "Sharpe broadly wins, wealth
lags" pattern (families 003/005/006/007/017/018) — the primary config
loses on **both** final wealth **and** Sharpe on **every single core
asset**. The mechanism's "avoid depositing into a weakening economy, buy
back once it normalizes" hypothesis simply did not help on this
development sample at the primary threshold: banking cash during the
z<-0.5 window and redeploying it via capped catch-up lumps produced
worse risk-adjusted outcomes than steady DCA on all 5 assets.

### Grid diagnostic (sec 4.4)

**0 of 24 configurations (0.0%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees — the weakest grid result of
any family in this loop so far. Only 2 of the 24 configs (`cfg06`,
`cfg07`: `zscore, lookback_years=10, threshold_level=0` i.e. the
strictest `z < -1.0` threshold) reach even 1/5 assets; every other config
reaches 0/5. Both the `zscore` and `percentile` normalization methods
fail uniformly across every `lookback_years` and `threshold_level`
combination — this is not a case of one grid arm or one normalization
method carrying the family while another drags it down (contrast family
018's October-vs-November-start pattern); the CLI-based weak/strong
banking signal simply does not produce a favorable timing shift anywhere
in the pre-declared grid.

**Sec 4.4: FAIL** (need >=2/3 = 16/24; got 0/24 = 0.0%).

CSCV probability of backtest overfitting (24-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.186** — low to
moderate; consistent with the grid being genuinely, consistently weak
rather than a resampling artifact.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series
  (strategy weekly NAV return minus DCA weekly NAV return, averaged
  across the 5 assets): **-0.02568** (weekly, **-0.1852 annualized**) —
  **negative**, the first family in this loop whose primary config's raw
  excess Sharpe is meaningfully negative rather than merely small and
  positive.
- `N` (raw trial count, whole-loop pool): **587** (196 seeded + 367 from
  families 001-018 + 24 new from this family's grid; matches the sanity
  check 196+391=587, `state/trial_counter.json["new"]`=391 after this
  family).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **61**
  clusters (up from family 018's 60 — this family's 24-config grid
  contributes exactly 1 new distinct cluster; the other 23 correlate
  rho>=0.5 with an existing cluster, expected given they all share the
  same underlying CLI-regime banking mechanic at different
  normalization/threshold/tilt settings).
- **DSR (N_eff-based): ~1.83e-34** — effectively zero, and doubly so
  because the raw excess Sharpe is negative to begin with (a negative
  Sharpe can never clear a positive `SR0` threshold at any `N`). The
  excess series also has very heavy tails (skew -0.48, kurtosis 109.5,
  the second-highest kurtosis observed in this loop after family 018's
  709.25 — a handful of large historical slowdown/recovery episodes
  dominate the tilt-driven catch-up-lump weeks).
- DSR (raw-N, conservative reference): ~3.28e-40, also effectively zero.

**Sec 4.2: FAIL**, decisively — a negative raw excess Sharpe cannot clear
the trial-count-adjusted DSR bar at either `N` or `N_eff` under any
circumstance.

### Robustness (sec 4.3)

**Not run.** Per the established precedent (sec 4.3 is only attempted if
sec 4.1 passes first), and sec 4.1 fails (0/5, the weakest sec 4.1 result
of any family so far), the rolling-window / block-bootstrap / placebo
battery was skipped.

## Verdict

**REJECTED.** Sec 4.1 fails at both fee levels (0/5 core assets — the
strategy underperforms DCA on both wealth and Sharpe on every single
asset). Sec 4.4's grid diagnostic fails even more starkly (0/24, need
>=16/24). DSR is effectively zero, driven by a genuinely negative raw
excess Sharpe rather than merely an insufficiently large positive one.
Holdout was **not** opened.

## Interpretation

Unlike most prior "timing/banking" families in this loop (003/005/006/
007/010/011/017/018), which typically showed Sharpe improving broadly
while wealth lagged on a majority of assets (a real but modest
risk-smoothing effect that didn't translate to more final wealth), this
family shows **no positive effect of either kind** anywhere in its
pre-declared grid. A plausible reading, offered honestly and without
retuning (per sec 5.4/sec 4.4's rule that only the primary config is
eligible and grid patterns are diagnostic only): the OECD CLI, as a
6-9-month-leading real-economy indicator, tends to read "weak" well
*after* the sharpest part of a market drawdown has already occurred and
well *before* the market itself has fully priced in the recovery the CLI
is anticipating — so banking cash while the CLI is weak means banking
cash precisely during the market's own recovery phase (the CLI lags the
market's own forward-pricing of the same real-economy information it is
built to anticipate), the reverse of the credit-stress mechanism's
"avoid depositing into acute market distress" logic that showed a
(still ultimately rejected) modest positive tilt in family 011's sec 4.1
result. This is a plausible mechanism-level explanation for the
uniformly negative result, not a claim that has itself been tested here
— consistent with the loop's discipline of not chasing an ex-post
narrative into a new grid arm.

## Trial accounting

- Seed: 196 (unchanged).
- New before this family: 367 (families 001-018).
- New from this family's 24-config grid: 24.
- New total after this family: 367 + 24 = 391 (matches
  `state/trial_counter.json`).
- Raw N at assessment: 196 + 391 = **587** (matches `n_total_raw` in
  `_run_output.json`).
- N_eff at assessment: **61** (up from family 018's 60 — one new
  distinct cluster).
- Families (new) count: 17 (was 16 before this family).

## Files

- `families/019-oecd-cli-regime/prereg.md` — pre-registration (committed
  before any backtest).
- `families/019-oecd-cli-regime/grid_results.csv` — full 24-config x
  5-asset x 2-fee grid.
- `families/019-oecd-cli-regime/_primary_per_asset.csv` — primary
  config's per-asset summary.
- `families/019-oecd-cli-regime/_run_output.json` — machine-readable
  summary of all checks above.
- `src/backtest/v3/strategies/oecd_cli_regime.py` — implementation.
- `scripts/v3/run_019_oecd_cli_regime.py` — end-to-end run script.
- `state/trials/new_019_*.csv` — 24 new trial excess-return series.
