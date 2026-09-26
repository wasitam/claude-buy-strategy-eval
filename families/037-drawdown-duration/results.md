# Family 037 results: Drawdown-DURATION (time-underwater) sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively:
it is **numerically identical to plain DCA on every one of the 5 core
assets** (0/5 beat DCA on wealth AND Sharpe, at both 0.1% and 0.25% fees),
for a mechanically-diagnosed reason explained below, not a bug. Sec 4.4's
grid diagnostic also fails completely: **0 of 32 configurations (0.0%)**
clear the >=3/5 combined wealth-AND-Sharpe majority bar (best achieved
anywhere on the grid was 2/5). DSR is exactly 0.0. Holdout was **not**
opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family** (sec 4.1's Single-asset line),
across all 5 core assets, category **Sizing / valuation** (the seed
queue's own categorization of idea #35). Source: seed queue item #35 plus
the practitioner "time-to-recovery" / underwater-duration literature
underlying the Calmar/Sterling/Ulcer-Index family of risk measures.
Signal: for each asset, a strictly causal running peak `ATH_t` (identical
definition to family 014's), and `dur_t`, the count of trading days since
the close last touched or exceeded `ATH_t` -- a pure elapsed-time counter
with **zero** dependence on how far below `ATH_t` today's close currently
sits. A 3-tier ladder multiplier sizes buys up the longer `dur_t` runs.

## The required rigorous distinction from family 014 -- real-data divergence example

Full argument in prereg.md. Summary: family 014's signal is the
**percentage-magnitude shortfall** `dd_t = max(0, 1 - close_t/ATH_t)`;
this family's signal is the **elapsed-trading-day count** since the last
peak, with no reference to price level at all once the peak date is
fixed. Verified programmatically (not hand-copied) on two real, entirely
pre-2020 SP500 episodes:

| Episode | Peak | Trough | New high | Max `dd` (family 014's stat) | `dur` to new high (this family's stat) |
|---|---|---|---|---|---|
| Deep-but-brief (2018-19) | 2018-09-20 (2930.75) | 2018-12-24 (2351.10) | 2019-04-23 | **19.78%** | **146 trading days** |
| Shallow-but-long (2015-16) | 2015-05-21 (2130.82) | 2016-02-11 (1829.08) | 2016-07-11 | **14.16%** | **286 trading days** |

The deeper drawdown (2018-19) resolved into a new high in **about half**
the trading days the shallower drawdown (2015-16) took -- the magnitude
ranking and the duration ranking of the two episodes **disagree**, exactly
as the general argument predicts. `distinctiveness_from_family_014_proven:
true`, all six referenced dates confirmed pre-2020.

## Pre-grid non-degeneracy sanity check

| Asset | Dev days | Frac. `m_t == 1.0` (primary) | Std(m_t) | Non-degenerate? |
|---|---|---|---|---|
| SP500 | 23,109 | 32.54% | 0.450 | PASS |
| GOLD | 4,848 | 34.47% | 0.437 | PASS |
| SILVER | 4,850 | 18.64% | 0.391 | PASS |
| BTC | 1,932 | 35.30% | 0.422 | PASS |
| OIL | 4,857 | 20.01% | 0.401 | PASS |

## Cash-reserve dynamics check (family 033's lesson)

Run on the grid's reserve-bearing arm (`near_high_mult=0.75`, `ladder=moderate`,
since the **primary config's own `near_high_mult=1.0` banks no reserve at
all** -- see below): average cash (`$112.30`) exceeds the plain-DCA
baseline (`$103.88`) -- a genuine reserve is banked -- and average cash
during long-duration (`m_t > 1`) weeks (`$104.05`) is lower than during
near-high (`m_t < 1`) weeks (`$129.41`) -- the banked reserve is drawn
down when the long-duration signal fires. Both checks **PASS**.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Real-data divergence example vs. family 014 (2 known episodes) | PASS (rankings disagree, both pre-2020) |
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| `ladder=flat, near_high_mult=1.0` grid-shaped code path (real, not the bypass) also reproduces plain DCA bit-for-bit | PASS |
| Cash-reserve check: avg cash, reserve arm vs. DCA baseline | PASS (reserve arm > DCA) |
| Cash-reserve check: avg cash, high-duration tier vs. low-duration tier | PASS (high-duration < low-duration) |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (aggressive grid corner: `al=10, ladder=aggressive, nhm=0.75, mlc=3.0`) | PASS |
| Capital deployed never exceeds cumulative deposits + interest, principled "never invest" ceiling bound (primary config) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (aggressive grid corner) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000` and `t=20000`) | PASS |
| Point-in-time macro data | N/A -- price-only signal, no macro dependency |
| `PRIMARY_CONFIG` is a member of `grid_configs()` (asserted at import time) | PASS |
| No dev-period check references a date on/after 2020-01-01 or an unseen ticker | PASS |

## Primary configuration: `ath_lookback_years=None, ladder=moderate, near_high_mult=1.0, max_lump_cap=3.0`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.27722 | 85.27722 | 0.15310 | 0.15310 | NO (identical) |
| GOLD | 2.23123 | 2.23123 | 0.50492 | 0.50492 | NO (identical) |
| SILVER | 1.68666 | 1.68666 | 0.31968 | 0.31968 | NO (identical) |
| BTC | 9.85568 | 9.85568 | 1.06731 | 1.06731 | NO (identical) |
| OIL | 1.17986 | 1.17986 | 0.22782 | 0.22782 | NO (identical) |

**Sec 4.1: FAIL** -- 0/5 core assets at both fee levels. Every value is
bit-for-bit identical to DCA (`buy_usd` max diff `0.0`, `units` max diff
`0.0`, verified directly), not merely "close."

**Why the primary config is bit-for-bit DCA -- a genuine design finding,
diagnosed after the run, not a bug.** The primary config's
`near_high_mult=1.0` means every week that is not in a long-duration tier
spends the *entire* weekly deposit, exactly like DCA -- so **no cash
reserve is ever banked** while `dur_t` is small. Then, on any week where
`dur_t` has run long enough to request `m_t > 1`, the only cash available
to fund that request is that same week's own $500 deposit (nothing was
banked in advance), so the engine's `buy_usd = min(requested, cash)` cap
(sec 3.2, no leverage) silently clips the request straight back down to
$500 -- identical to what DCA would have bought anyway. This is exactly
the same mechanical finding family 014's results.md already documented
for its own `near_high_mult=1.0` primary config (this family's primary
was deliberately chosen to mirror family 014's for direct
reference-point comparability, per prereg.md), reproduced here to the same
values to the decimal place, which is itself independent confirmation
that both the reference-point computation and the engine's cash-cap logic
behave identically and correctly across the two families. Confirmed
directly in the grid: **every `near_high_mult=1.0` configuration (16/32)
is exactly DCA-equivalent** (0/5 on both wealth and Sharpe, every fee
level), regardless of `ath_lookback_years`, `ladder` preset, or
`max_lump_cap`; **every `near_high_mult=0.75` configuration (16/32)**
does fund a real reserve and beats DCA on wealth AND Sharpe on at most
**2/5** assets (`mild`/`moderate`/`flat` ladders) or, despite a higher
raw wealth-only hit rate, only **1/5** on the combined wealth-AND-Sharpe
criterion for the `aggressive` ladder (its wealth gains and Sharpe gains
land on different assets) -- short of the 3/5 majority bar in every case.

### Grid diagnostic (sec 4.4)

**0 of 32 configurations (0.0%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees -- need >=2/3 (22/32). The best
any grid configuration achieved anywhere was 2/5 (the `near_high_mult=0.75`
arms of the `mild`, `moderate` and `flat` ladders, both `ath_lookback_years`
settings). CSCV PBO = 0.0 (uninformative here given sec 4.1's outright
failure, in the same way family 014's PBO=0.0 was uninformative: the
grid's only real axis of variation is the binary
funded-reserve-vs-no-reserve split produced by `near_high_mult`, which is
a very easy split for CSCV to rank consistently).

### Sec 4.2: Deflated Sharpe Ratio -- FAIL (reported for completeness; not required once sec 4.1 fails)

- `N_eff = 123` (raw `N = 1137`, seed 196 + new 941 across all families
  tested through this family: `196 + 909 (through family 036) + 32 (this
  family) = 1137`, sanity-checked against `state/trial_counter.json`'s own
  updated `new: 941`).
- DSR (N_eff-based): **0.0** exactly (the primary config's pooled
  excess-return series is identically zero every week, since it is
  bit-for-bit DCA).
- DSR (raw-N, conservative reference): **0.0**.

### Sec 4.3: not run in full

Sec 4.1 failed decisively, so sec 4.3's rolling-window, bootstrap and
placebo legs were skipped per established loop precedent (families
006/007/008/011/013/014/036 and others: sec 4.3 is reserved for
configurations that at least clear the sec 4.1 bar).

## Assessment summary

| Check | Result | Pass? |
|---|---|---|
| Sec 4.1 (beats DCA >=3/5, both fees) | 0/5 at both fees (bit-for-bit DCA) | FAIL |
| Sec 4.2 (DSR >= 0.95) | 0.0 (N_eff), 0.0 (raw N) | FAIL |
| Sec 4.3 (rolling/bootstrap/placebo) | not run (sec 4.1 gate not cleared) | N/A |
| Sec 4.4 (>=2/3 of grid beats DCA majority) | 0/32 (0.0%) | FAIL |

**Verdict: REJECTED.** Logged, not promoted to finalist or near-miss
(sec 4.1 itself fails outright). Holdout not opened, per sec 5.4.

## Judgment calls

1. **Primary config chosen to mirror family 014's exact
   `near_high_mult=1.0` and `ladder=moderate` choices**, for direct
   comparability of the reference-point/statistic swap (magnitude vs.
   duration) holding every other design choice fixed -- made before
   seeing any results, per prereg.md. This produced the same
   reserve-nullification finding family 014 already surfaced, now
   reproduced independently for a different underlying statistic,
   reinforcing that the finding is about the `near_high_mult=1.0` choice
   interacting with the engine's no-leverage cash cap, not specific to
   either family's particular signal.
2. **`near_high_mult=0.75` grid arms (which do fund a real reserve) still
   fall short of the 3/5 majority bar** on the combined wealth-AND-Sharpe
   criterion (max 2/5), and the `aggressive` ladder's reserve arm does
   *worse* on the combined criterion (1/5) than its own wealth-only hit
   rate (3/5) would suggest, because its wealth gains and Sharpe gains
   land on different assets -- consistent with the loop's broader pattern
   (families 003/014/030/031/034/035/036) that a per-asset
   trailing-statistic-driven sizing multiplier tends to produce thin,
   inconsistently-signed per-asset margins in this development sample.
   Per sec 4.4, no grid arm can be substituted for the primary regardless
   of this pattern.
3. This family adds a second independent data point (after family 014)
   confirming that an all-time-high reference point that never adapts
   downward, combined with a `near_high_mult=1.0` "no reduction near the
   high" choice, mechanically neutralizes a ladder-based reserve strategy
   under this engine's correct no-leverage cash-cap rule -- worth keeping
   in mind for any future family that reuses this reference-point
   convention: a genuinely reserve-funded design requires
   `near_high_mult < 1.0` in its *primary* configuration, not only
   somewhere in the grid.
