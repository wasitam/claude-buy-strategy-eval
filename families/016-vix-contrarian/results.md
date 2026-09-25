# Family 016 results: VIX contrarian fear-gauge sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively:
it beats plain DCA on **0 of 5** core assets, on wealth AND Sharpe, at
either fee level. This is not a silent no-op -- the primary config's
per-asset results genuinely differ from DCA on every asset (underperforms
on wealth on all 5, confirming the mechanism actually fired throughout the
backtest, consistent with the pre-registered non-degeneracy check below).
Sec 4.4's grid diagnostic also fails completely: **0 of 24** configs reach
the combined wealth-AND-Sharpe majority bar. DSR is effectively zero.
Holdout was **not** opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family** (sec 4.1's Single-asset line),
across all 5 core assets, category **Sizing / valuation** (chosen over
"Volatility targeting" -- see prereg.md's category-justification section:
this is a discrete, threshold-triggered directional bet on mean reversion
after a shared cross-market fear spike, closer in spirit to family 004's
value averaging and family 008's CAPE sizing than to family 003's smooth,
direction-agnostic realized-variance targeting rule). Signal: the CBOE VIX
(`^VIX`, S&P 500 option-implied volatility -- a single shared,
cross-market signal, not any asset's own realized volatility) spiking into
an elevated trailing percentile (`elevated_pct`, over a trailing
`vix_lookback`-day window) marks a "fear" regime; deposits are sized UP
(`buy_multiplier * weekly_deposit`, cash-capped) during that regime,
funded by banking a small fraction (`1 - calm_fraction`) of every calm
week's deposit as cash. No sells, ever; no leverage; cash never goes
negative (engine's own cap, sec 3.2).

**Rigorous distinction from family 003 (required by this iteration's
task):** prereg.md documents six independent axes of difference -- signal
source (shared S&P-500-implied VIX vs. each asset's own realized vol),
volatility concept (implied/forward vs. realized/backward), functional
form (discrete threshold regime vs. continuous ratio), sign (buy MORE into
elevated risk vs. buy LESS), economic story (behavioral overshoot/reversion
bet vs. variance-targeting risk management), and trigger granularity
(one shared series for all 5 assets vs. a per-asset internal calculation).
No parameter setting of either family nests or reduces to the other.

**Pre-backtest non-degeneracy check (prereg.md, required by this
iteration's task instruction, following family 015's precedent):** before
any backtest, the primary config's elevated-fear regime frequency was
computed directly for all 5 core assets and found genuinely mixed on
every one (12.93% of VIX-available days for SP500, ~11.3-11.7% for
gold/silver/BTC/oil) -- ruling out a family-014-style silent no-op by
construction. The backtest results below confirm the mechanism fired
throughout: the primary config's per-asset wealth/Sharpe figures differ
meaningfully (not identically) from DCA on every asset, in the
underperforming direction.

## Judgment call: VIX's 1990 data start vs. each core asset's development period

`^VIX` is directly reachable via yfinance (confirmed during the gate
step: 9,253 daily rows, 1990-01-02 through today), routed through the
existing `data.fetch_yf_macro()` helper added for family 015. Comparing
VIX's 1990 start against each core asset's own `load_dev()` start date:
only **SP500** (dev history from 1927-12-30) has any development-period
history predating VIX -- about 68% of its 23,109 development trading days
(1927-1989) have no VIX signal available at all. GOLD/SILVER/OIL
(dev start 2000-08) and BTC (dev start 2014-09) are fully covered by VIX's
1990+ history. Per the established warm-up convention (families
001/011/015), the elevated-fear flag defaults to **False (calm)** whenever
the trailing percentile can't yet be computed -- both during the initial
`vix_lookback`-day warm-up on every asset, and for SP500's entire
pre-1990 stretch. This means SP500's mechanism can only ever fire its
"buy more" leg on the ~32% of its development days from 1990 onward,
which is flagged explicitly here (and in prereg.md) as a real, if modest,
asymmetry versus the other four assets rather than being silently absorbed
into the generic warm-up convention.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (aggressive corner: `vix_lookback=252, elevated_pct=80, buy_multiplier=3.0, calm_fraction=0.75` -- lowest threshold, highest multiplier, most aggressive banking) | PASS |
| Total capital deployed (cumulative buy_usd) never exceeds cumulative deposits + interest, within a 5% empirical bound (primary config) | PASS |
| Total capital deployed never exceeds cumulative deposits + interest (aggressive corner) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000` and `t=9500`) | PASS |
| Point-in-time macro data | N/A -- VIX is a daily market-price series (no publication lag / ALFRED vintage concern, same as family 015's DXY), documented explicitly rather than skipped |
| Primary-config regime non-degeneracy (pre-registered check, per-asset) | PASS -- 4.09%/11.06%/11.05%/9.83%/11.06% of ALL dev days (SP500/GOLD/SILVER/BTC/OIL); 12.93%/11.66%/11.65%/11.30%/11.66% of VIX-available dev days respectively |

## Primary configuration: `vix_lookback=252, elevated_pct=90, buy_multiplier=2.0, calm_fraction=0.9, max_buy_multiple=4.0`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 78.314 | 85.277 | 0.15616 | 0.15310 | NO (wealth fails) |
| GOLD | 2.205 | 2.231 | 0.50265 | 0.50492 | NO |
| SILVER | 1.666 | 1.687 | 0.31773 | 0.31968 | NO |
| BTC | 9.750 | 9.856 | 1.08240 | 1.06731 | NO (wealth fails) |
| OIL | 1.173 | 1.180 | 0.22710 | 0.22782 | NO |

**Sec 4.1: FAIL**, 0/5 core assets, at both fee levels (0.25% fee results
are qualitatively identical -- see `_primary_per_asset.csv`). The primary
config underperforms DCA on **wealth** on every single core asset; it
does beat DCA on Sharpe for SP500 and BTC (consistent with "leaning into
fear" producing a smoother, higher-Sharpe path on those two even while
lagging on absolute wealth), but sec 4.1 requires both metrics together,
so the combined bar is not cleared on any asset.

### Grid diagnostic (sec 4.4)

**0 of 24 configurations (0.0%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees. The grid's best individual
Sharpe-only showing is 3/5 (one config, `elevated_pct=80.0,
buy_multiplier=3.0, calm_fraction=0.9`), but no config anywhere in the
24-config grid pairs that with >=3/5 on wealth (see `grid_results.csv`
for the full per-config breakdown; the printed run log shows every
config's wealth/Sharpe/both counts, all 0/5 on the combined bar).

**Sec 4.4: FAIL** (need >=2/3 = 16/24; got 0/24).

CSCV probability of backtest overfitting (24-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.0** -- the
grid's corners are not "overfit" in the CSCV sense; they are
consistently, uniformly poor across resampled splits (the same signature
family 014 showed with its own PBO=0.0).

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series
  (strategy weekly NAV return minus DCA weekly NAV return, averaged across
  the 5 assets): **-0.0356** (weekly, i.e. **-0.256 annualized**) --
  negative, consistent with the primary config underperforming DCA on
  wealth on every asset.
- `N` (raw trial count, whole-loop pool): **523** (196 seeded + 303 from
  families 001-015 + 24 new from this family's grid; matches the sanity
  check 196+327=523, `state/trial_counter.json["new"]`=327 after this
  family).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **58** clusters
  (unchanged from family 015 -- this family's 24 grid configs did not add
  any new distinct cluster, i.e. its excess-return series correlate
  >=0.5 with an already-existing cluster).
- **DSR (N_eff-based): ~1.39e-38** -- effectively zero. A negative raw
  Sharpe cannot clear the DSR's positive SR0 threshold (SR0=0.151 at this
  N_eff) under any reasonable trial-count adjustment.
- DSR (raw-N, conservative reference): ~9.78e-47, also effectively zero.

**Sec 4.2: FAIL**, decisively -- the excess-return series' negative mean
Sharpe rules out a DSR pass regardless of the trial-count adjustment.

### Robustness (sec 4.3)

**Not run.** Per the established precedent (families 006/007/008/011/013/
014/015: sec 4.3 is only attempted if sec 4.1 passes first), and sec 4.1
fails outright (0/5, the same category of decisive failure as families
011's, 014's and 015's), the rolling-window / block-bootstrap / placebo
battery was skipped.

## Verdict

**REJECTED.** Sec 4.1 fails at both fee levels (0/5 core assets, driven
by wealth underperformance on every asset). Sec 4.4's grid diagnostic
fails completely (0/24, need >=16/24). DSR is effectively zero (negative
raw Sharpe). Holdout was **not** opened.

## Interpretation

The "buy more into elevated cross-market fear" mechanism, as tested, does
not improve on plain DCA's final wealth for any of the 5 core assets over
the development window, even though it does modestly improve Sharpe for 2
of 5 (SP500, BTC) -- a smoother path, not a wealthier one. A plausible
read, consistent with the negative pooled excess Sharpe and the grid's
uniformly poor wealth showing (no config anywhere in the 24-config grid
clears wealth on even a bare majority of assets): reallocating a small,
fixed slice of every calm week's deposit into cash (`1 - calm_fraction`)
to fund the elevated-week "lean in" buys creates a persistent, low-level
cash drag during the ~85-89 percent of weeks that are calm, and this drag
is not fully recovered by the elevated-week extra buying even when VIX
spikes are followed by genuine recoveries -- because VIX-elevated windows,
while short relative to family 015's multi-year DXY regimes, are still
often multi-week stretches (not single-day spikes), during which
`max_buy_multiple`'s cap and the finite banked-cash pool limit how much
the mechanism can actually lean in before cash runs out and it reverts to
`calm_fraction`-sized (i.e. still below-DCA) buying mid-panic. This is
consistent with, but does not confirm, a version of family 011's and
015's own diagnosed timescale mismatch: the banking mechanic's calm-week
drag accumulates continuously (every calm week, for years), while the
elevated-week payoff is concentrated in a comparatively small number of
episodes, so the aggregate arithmetic does not net out favorably over the
development window even when Sharpe (a risk-adjusted, not absolute,
measure) improves modestly on two of the five assets. This does not rule
out other VIX-based mechanisms (e.g. a same-magnitude but shorter-fuse
version, or one funded without any calm-week cash drag at all) but this
specific family, as pre-registered and tested, does not clear sec 4.1.

## Trial accounting

- Seed: 196 (unchanged).
- New before this family: 303 (families 001-015).
- New from this family's 24-config grid: 24.
- New total after this family: 303 + 24 = 327 (matches
  `state/trial_counter.json`).
- Raw N at assessment: 196 + 327 = **523** (matches `n_total_raw` in
  `_run_output.json`).
- N_eff at assessment: **58** (unchanged from family 015 -- no new
  distinct cluster).
- Families (new) count: 14 (was 13 before this family).

## Files

- `families/016-vix-contrarian/prereg.md` -- pre-registration (committed
  before any backtest).
- `families/016-vix-contrarian/grid_results.csv` -- full 24-config x
  5-asset x 2-fee grid.
- `families/016-vix-contrarian/_primary_per_asset.csv` -- primary config's
  per-asset summary.
- `families/016-vix-contrarian/_run_output.json` -- machine-readable
  summary of all checks above.
- `src/backtest/v3/strategies/vix_contrarian.py` -- implementation.
- `scripts/v3/run_016_vix_contrarian.py` -- end-to-end run script.
- `state/trials/new_016_*.csv` -- 24 new trial excess-return series.
