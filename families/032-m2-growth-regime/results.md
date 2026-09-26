# Family 032 results: M2 money-supply growth regime switch

**Verdict: REJECTED.** The primary configuration fails sec 4.1
decisively: only **1 of 5** core assets beat DCA on final wealth AND
Sharpe at either fee level. Sec 4.4's grid diagnostic also fails hard
(0/24 configs clear the majority bar). Sec 4.2/4.3 (DSR and the rolling-
window/bootstrap/placebo battery) are reported/skipped respectively per
the loop's established time-budget convention (§4.3 run in full only if
§4.1 passes; §4.2's DSR is always computed and reported). Holdout was
**not** opened (not a finalist).

## Category and the fourfold macro-signal distinction

Filed as **Regime switch (macro)** (research-loop-plan-v3.md sec 4.5's
category list). This loop now has four macro regime-switch families, and
this iteration's task required an explicit fourfold distinction, given in
full in `prereg.md` and summarized here:

| | v2.1 Strategy D | Family 011 | Family 019 | Family 027 | Family 032 (this) |
|---|---|---|---|---|---|
| Question | Policy tight/loose? | Credit/financial stress elevated? | Real-economy leading activity below trend? | Curve shape signals future easing/recession? | Is the quantity of money growing faster/slower than trend? |
| Data | DFEDTAR(U/L), DGS2, T10Y2Y, DFII10, FEDTARMD | BAA, AAA, NFCI | USALOLITONOSTSAM | DGS2, DGS10 / T10Y2Y | M2SL |
| Channel | Price of money (policy rate) | Market pricing of default/liquidity risk | Real-economy activity cycle | Bond-market policy expectations | Quantity-of-money / liquidity channel |

M2SL contains none of the other three families' input series and is not
derived from them. The clearest concrete historical divergence cited in
`prereg.md`: 2020-21 saw M2 growth **accelerate** sharply (pandemic fiscal
transfers + QE-driven deposit creation) at the same time the OECD CLI
(family 019) **collapsed** in the COVID shock — the two signals moved in
opposite directions during the same window, direct evidence they are not
proxies for one another.

## Data reachability and revision character

`M2SL` is reachable via FRED's `fredgraph.csv` endpoint (the same
`fetch_fred_macro()` helper families 011/019/027 already use): 812 monthly
observations, 1959-01-01 through the present. ALFRED's own metadata page
reports **"First Vintage: 1980-02-08"** for `M2SL` — real vintage coverage
starts earlier than family 019's OECD CLI series (2018-07), though still
leaving the pre-1980 portion of this family's dev sample without true
vintage-by-vintage reconstruction. Following families 011/019/027's own
precedent, a fixed conservative **45-calendar-day** publication lag stands
in for full vintage reconstruction (matching family 011's own monthly
BAA/AAA lag), rather than attempting partial true-vintage backtesting —
the same time-budget tradeoff those three families made.

## Pre-grid sanity checks (per prereg.md and this iteration's task brief)

1. **Non-degeneracy** (primary config, all 5 core assets):

| Asset | Dev days | Decelerating days | Frac. decelerating |
|---|---|---|---|
| SP500 | 23,109 | 5,330 | 23.06% |
| GOLD | 4,848 | 1,360 | 28.05% |
| SILVER | 4,850 | 1,361 | 28.06% |
| BTC | 1,932 | 699 | 36.18% |
| OIL | 4,857 | 1,364 | 28.08% |

All comfortably inside the (2%, 98%) sanity band — the decelerating
regime is not degenerate on any asset.

2. **Known-episode check (2008-09 QE-era acceleration, strictly within
   dev dates):** the primary config's growth-rate/z-score reading over
   2008-09-01 through 2009-12-31 (16 monthly observations, the well-
   documented post-Lehman Fed balance-sheet expansion) reads only
   **6.2%** decelerating (a single isolated noisy monthly print, the
   2008-09-15 observation), with the YoY growth rate rising from **5.6%**
   at the window's start to **6.1%** at its end, peaking above **10.3%**
   in between — correctly identifying this well-known M2 acceleration
   episode as accelerating (not decelerating) before the grid was
   trusted. **PASS.**

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (cash never negative under the engine's cash-capped fill logic, family 021's principled bound) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000` and `t=20000`, deep in the pre-2020 dev sample) | PASS |
| Macro-specific: shortening the publication lag from the documented 45 days to 0 days changes 4.62% of historical regime readings (SP500) -- confirms the lag is doing real work, not a no-op | PASS |
| Point-in-time macro data (documented 45-day fixed lag, ALFRED partial-vintage-coverage gap flagged above) | PASS |

## Primary-config-in-grid verification

Verified programmatically via a module-level assertion in
`m2_growth_regime.py` (`assert PRIMARY_CONFIG in grid_configs()`, executed
automatically on import) and re-confirmed in the run script before any
grid backtest: `PRIMARY_CONFIG = {yoy_window_months=12, lookback_years=10,
threshold_level=1, decel_tilt_fraction=0.0}` (`max_lump_multiple=6.0`
fixed) is a genuine member of the 24-config grid (`cfg20_yw12_lb10_tl1_tf0.0`).
No mismatch found.

## Sec 4.1 result (vs. plain per-asset DCA), development windows

| Asset | Strategy wealth/invested (0.1%) | DCA wealth/invested (0.1%) | Strategy Sharpe (0.1%) | DCA Sharpe (0.1%) | Beats DCA (both, 0.1%)? |
|---|---|---|---|---|---|
| SP500 | 84.8678x | 85.2772x | 0.15278 | 0.15310 | NO |
| GOLD | 2.1566x | 2.2312x | 0.49421 | 0.50492 | NO |
| SILVER | 1.6031x | 1.6867x | 0.30539 | 0.31968 | NO |
| BTC | 9.7600x | 9.8557x | 1.06762 | 1.06731 | NO (loses on wealth) |
| OIL | 1.1889x | 1.1799x | 0.22802 | 0.22782 | **YES** |

At 0.1% fees: **1/5** assets beat DCA on both wealth AND Sharpe (OIL
alone). At 0.25% fees: also **1/5**, same pattern. **Sec 4.1: FAIL**
decisively (need >=3/5). BTC narrowly wins on Sharpe but loses on wealth,
so it does not count; every loser but SP500/GOLD/SILVER trails by a small
but consistent margin, and OIL's win is itself narrow.

## Grid diagnostic (sec 4.4)

**0 of 24 configurations (0.0%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets, 0.1% fee) — a uniform failure across the
whole 24-config parameter space (need >=16/24 = 2/3). The best individual
corners (`cfg00`/`cfg01`, `yoy_window_months=6, lookback_years=5,
threshold_level=0`, and the primary's own `cfg20`/`cfg21` corner) reach at
most 2/5 assets on Sharpe alone or 1/5 on the combined wealth-AND-Sharpe
count — no config anywhere in the grid reaches a 3-asset majority.
**Sec 4.4: FAIL** (need >=16/24; got 0/24).

CSCV probability of backtest overfitting (24-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.714** — high,
meaning the grid's in-sample ranking of configurations is poorly
reproduced out-of-sample, consistent with a mostly-noise parameter space
rather than a genuine, tunable effect.

## Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series
  (equal-weight average of the 5 per-asset excess series, strategy weekly
  NAV return minus DCA weekly NAV return): **-0.03606/week** (annualized
  **-26.0%**) — negative, with negative skew (-0.845) and elevated
  kurtosis (141.5).
- `N` (raw trial count, whole-loop pool): **965** (196 seeded + 745 from
  families 001-031 + 24 new from this family's grid).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **79**
  clusters (up from 74 at family 031 — this family's 24 grid configs
  opened at least one new cluster distinct from the existing 74).
- **DSR (N_eff-based): 2.98e-36** — essentially zero, against an SR0
  threshold of 0.146/week at this loop's N_eff=79.
- DSR (raw-N, conservative reference): 7.54e-37.

**Sec 4.2: FAIL**, decisively — a negative raw pooled excess-return
Sharpe cannot clear any positive trial-adjusted bar.

## Sec 4.3

**Not run in full**, per the plan's own time-budget convention (rolling
windows / block bootstrap / placebo are only run in full when sec 4.1
passes) — sec 4.1 already fails decisively (1/5 assets), so the
n_sims=60 robustness battery would not change the verdict.

## Verdict

**REJECTED.** Sec 4.1 fails decisively (1/5 assets, both fee levels), sec
4.4's grid diagnostic fails uniformly across the whole 24-config grid
(0/24), and sec 4.2's DSR is essentially zero on a negative raw excess
Sharpe. Sec 4.3 was not run per the established time-budget convention.
Holdout was **not** opened.

## Interpretation

The quantity-of-money/liquidity-channel hypothesis — that M2 growth
deceleration relative to its own trend flags a tightening-liquidity window
worth banking cash through — does not show a usable edge in this
development sample. A likely contributing factor, flagged honestly in
`prereg.md` before any backtest ran: genuine M2 growth-deceleration
episodes are rare in the pre-2020 dev sample, and the single most dramatic
historical deceleration episode — 2022-23's outright M2 contraction, the
event that motivated renewed public and practitioner attention to this
signal in the first place — falls entirely inside the sealed 2020+ holdout
and was never available to this family's development-data assessment. The
pre-2020 decelerating-regime windows this family could learn from (mostly
milder growth slowdowns, e.g. the mid-2000s and various shorter dips) were
evidently not decisive enough, on their own, to produce a robust
wealth-and-Sharpe edge over plain DCA — consistent with the general
pattern this loop has now observed across all four of its macro
regime-switch families (v2.1 Strategy D, family 011, family 019, and now
family 032): each identifies a real, well-documented macro phenomenon, but
translating "bank cash during a rare, historically significant stress/
tightening window" into a systematically exploitable, fee-and-trial-
adjusted edge over steady dollar-cost-averaging has not worked for any of
them in this development sample.
