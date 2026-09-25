# Family 014 results: Drawdown-from-high reserve deployment

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively:
it beats plain DCA on **0 of 5** core assets, at either fee level. In fact
the primary config's results are numerically identical to DCA's to several
decimal places on every asset -- a real, diagnosable design finding, not a
bug, explained below. DSR is exactly zero. Grid pass rate is 0%. Holdout
was **not** opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family** (sec 4.1's Single-asset line), using
the existing single-asset `engine.py` on each of the 5 core assets
independently, vs. plain per-asset DCA. Category: **Sizing / valuation**.

**Required SmartDCA distinction (sec 7.2), summarized (full argument in
prereg.md):** SmartDCA's reference point is a trailing moving average -- a
smoothed statistic that itself falls during a sustained drawdown and
encodes recent trend. This family's reference point is the asset's own
trailing all-time-high -- a ratchet that only rises or stays fixed, never
adapts downward, and carries zero information about recent trend
direction/velocity. The two signals diverge sharply on both slow grinding
declines (this family stays "pinned" at the true drawdown depth for years;
SmartDCA's moving average re-flattens and goes quiet) and sharp V-shaped
recoveries (this family reacts briefly; a 52-week average barely moves).
Not a re-test.

## Implementation checks (sec 3.2, all passed) -- two-reference-point pattern

| Check | Result |
|---|---|
| **Reference point 1**: `enabled=False` bypass flag (skips the drawdown/ladder computation entirely, buys exactly the $500 deposit every week) reproduces plain DCA exactly, bit-for-bit on units and cash | PASS |
| **Reference point 2 (family-specific)**: the REAL grid arm `ladder='flat', near_high_mult=1.0`, run through the actual `ATH_t`/`dd_t`/ladder-lookup computation (`enabled=True`, not the bypass path), independently reproduces plain DCA bit-for-bit on units and cash -- confirming the ladder code path itself, not just the bypass flag, collapses correctly when every tier multiplier is 1.0 | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (most aggressive grid corner: `ladder=aggressive, near_high_mult=0.75, max_lump_cap=3.0`) | PASS |
| Total capital deployed never exceeds cumulative deposits + interest (primary config) | PASS |
| Total capital deployed never exceeds cumulative deposits + interest (aggressive corner) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-check `t=6000`, deep into the sample) -- particular attention to the all-time-high tracker's strict causality (`ATH_t` uses only `close_0..close_t`, expanding-max or trailing-rolling-max) | PASS |
| Point-in-time macro data | N/A -- price-only signal (each asset's own OHLC), no macro/ALFRED series |

## Primary configuration: `ath_lookback_years=None (unbounded), ladder=moderate, near_high_mult=1.0, max_lump_cap=3.0`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.277 | 85.277 | 0.15310 | 0.15310 | NO (identical) |
| GOLD | 2.231 | 2.231 | 0.50492 | 0.50492 | NO (identical) |
| SILVER | 1.687 | 1.687 | 0.31968 | 0.31968 | NO (identical) |
| BTC | 9.856 | 9.856 | 1.06731 | 1.06731 | NO (identical) |
| OIL | 1.180 | 1.180 | 0.22782 | 0.22782 | NO (identical) |

**Sec 4.1: FAIL** at both fee levels, 0/5 core assets. The result at 0.25%
fees is identical for the same reason.

**Why the primary config is bit-for-bit DCA -- a genuine design finding,
diagnosed after the run, not a bug:** the primary configuration's
`near_high_mult=1.0` means the strategy spends the *entire* weekly deposit
every week that is not in a tier-1/tier-2 drawdown (exactly like DCA), so
**no cash reserve is ever banked** during normal/near-high periods. Then,
on any week that IS deep enough into a drawdown to request a multiplier
above 1.0, the only cash available to fund that request is that same
week's own $500 deposit (nothing was banked in advance) -- so the engine's
`buy_usd = min(requested, cash)` cap silently clips the request straight
back down to $500, identical to what DCA would have bought that week
anyway. With `near_high_mult=1.0`, the "deploy the reserve" leg of the
mechanism can never fire, because there is never a reserve to deploy: the
strategy is DCA in every week regardless of the ladder tier multipliers,
which is exactly what the primary-config results show. This is confirmed
directly in the grid: every `near_high_mult=1.0` configuration in the
32-config grid (16 of 32) is 0/5 on both wealth and Sharpe, identically to
DCA, regardless of `ath_lookback_years`, `ladder` preset, or
`max_lump_cap` -- while every `near_high_mult=0.75` configuration (which
DOES bank a real reserve near the highs) produces a materially different,
non-DCA result. The prereg's own primary-selection reasoning ("no
reduction below the plain deposit near the high ... keeps the primary
configuration close to plain DCA's risk profile except in drawdowns") was
wrong on the mechanics: at `near_high_mult=1.0` the strategy isn't merely
*close* to DCA outside drawdowns, it is DCA in every state, including
during drawdowns, because the reserve the ladder's higher tiers are
supposed to spend is never funded. This is an honest, pre-registration-
consistent negative result about the primary configuration as chosen, not
an implementation bug -- the two independent implementation checks above
(bypass flag and the real `flat` grid arm) both confirm the engine/ladder
code is working exactly as specified; the primary config simply picked a
parameter combination that, by the rule's own arithmetic, nullifies the
mechanism.

### Grid diagnostic (sec 4.4)

**0 of 32 configurations (0.0%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees. The clean pattern: every
`near_high_mult=1.0` config (16/32) is exactly DCA-equivalent (0/5, for the
mechanical reason above); every `near_high_mult=0.75` config (16/32) beats
DCA on wealth AND Sharpe on exactly 2/5 assets at 0.1% fees (short of the
3/5 majority bar) and on 1-2/5 at 0.25% fees. Not one grid configuration
clears the majority bar at either fee level.

**Sec 4.4: FAIL** (need >=2/3 = 22/32; got 0/32).

CSCV probability of backtest overfitting (32-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.0** -- the
lowest (best) of any family so far, but uninformative here given sec 4.1's
outright failure: a PBO of 0 says the grid's best-looking configuration on
one data split reliably ranks well on another, which is unsurprising when
the grid's only real axis of variation (`near_high_mult`) produces a
consistent, mechanically-explained split between "identical to DCA" and
"a modest, still-short-of-the-bar improvement."

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series
  (strategy weekly NAV return minus DCA weekly NAV return, averaged across
  the 5 assets): **0.0** exactly, consistent with the primary config being
  bit-for-bit DCA on every asset (zero excess return every week).
- `N` (raw trial count, whole-loop pool): **483** (196 seeded + 255 from
  families 001-013 + 32 new from this family's grid).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **56** clusters
  (up from family 013's 40 -- this family's 32 grid configs add 16 new
  distinct clusters, one per `near_high_mult=0.75` configuration; the 16
  `near_high_mult=1.0` configs all cluster with the existing zero-excess
  DCA-equivalent trials already in the pool).
- **DSR (N_eff-based): 0.0** -- exactly zero (a zero raw Sharpe cannot
  clear any positive SR0 threshold).
- DSR (raw-N, conservative reference): 0.0.

**Sec 4.2: FAIL**, trivially, since the excess-return series is
identically zero.

### Robustness (sec 4.3)

**Not run.** Per the established precedent (families 006/007/008/011/013:
sec 4.3 is only attempted if sec 4.1 passes first), and sec 4.1 fails
outright (0/5, the same category of decisive failure as families 011's
0/5), the rolling-window / block-bootstrap / placebo battery was skipped.

## Verdict

**REJECTED.** Sec 4.1 fails at both fee levels (0/5 core assets -- the
primary configuration is numerically identical to plain DCA on every
asset). Sec 4.4's grid diagnostic fails completely (0/32, need >=22/32).
DSR is exactly zero. Holdout was **not** opened.

## Interpretation and judgment call flagged for the record

The mechanism as designed is economically sound in principle (buy more
the further underwater from an all-time-high, funded by cash banked
during calmer periods), but **the primary configuration's choice of
`near_high_mult=1.0` accidentally disables the funding half of the
mechanism entirely**: without banking below the full deposit near the
high, there is no reserve for the drawdown tiers to spend, and the
engine's own no-leverage cash cap (correctly, per sec 3.2) then silently
reduces every "buy more" request back down to whatever that week's own
deposit provides -- which is exactly DCA. This is a real, useful negative
finding about *this specific* choice of primary configuration, made
honestly visible only by pre-registering the config before seeing results
and then reporting what actually happened, rather than quietly swapping to
a better-looking grid arm (sec 4.4 forbids that regardless). The grid's
`near_high_mult=0.75` configurations, which DO fund a real reserve, show
the mechanism can at least move the needle (2/5 assets beating DCA on both
wealth and Sharpe, vs. 0/5 for the no-reserve configs) -- but even those
configurations fall well short of the 3/5 majority bar and the 2/3 grid
threshold, so this is not simply a case of "the wrong primary was chosen
and a working config was sitting in the grid the whole time" (sec 4.4's
own rule would forbid promoting it even if it had passed). This reads as a
genuine mechanism weakness for this development window and asset mix: an
all-time-high ratchet, by never adapting downward, keeps the ladder
"maxed out" for however long a drawdown persists, but in a development
window dominated by a handful of very long secular bull runs (BTC, SP500)
interrupted by comparatively brief, sharp drawdowns rather than prolonged
multi-year bear markets, the reserve-funded extra buying during those
brief windows is not large enough, relative to the total deposit stream,
to meaningfully improve on simply dollar-cost-averaging through the whole
period. This does not rule out other drawdown-ladder constructions (a
continuous rather than discrete multiplier, tier breakpoints tuned to each
asset's own historical drawdown distribution rather than one shared
ladder, or explicit reserve caps sized as a fraction of cumulative
deposits) -- but those would be materially different mechanisms requiring
their own pre-registration, and per sec 5.4/7.2's discipline this specific
family (this exact rule and grid) is now closed.

## Data reachability

No issues. All 5 core assets' own OHLC and IRX are already-cached core-
asset series reachable via `src.backtest.v3.data.load_dev()`. No external
macro/alternative data was needed for this family's price-only signal.
