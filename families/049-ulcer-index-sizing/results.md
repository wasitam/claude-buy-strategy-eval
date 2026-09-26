# Family 049 results: Ulcer Index (drawdown-severity-weighted) sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1: it beats
DCA on final wealth on **5/5** core assets (every margin razor-thin, 3rd-5th
significant digit), but the combined wealth-AND-Sharpe criterion only
clears on **2/5** assets (SP500, BTC) at both fee levels -- short of the
required 3/5. DSR is effectively zero. Sec 4.4's grid diagnostic also
fails: only **11/24 (45.8%)** configurations reach the combined majority
bar, short of the 2/3 requirement, with CSCV PBO=0.629 (elevated). Holdout
was **not** opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family** across all 5 core assets, category
**Sizing / valuation** (seed queue idea #50). Source: Martin & McCann
(1989), the original Ulcer Index paper. Signal: for each asset, a
**local** rolling running peak over a trailing `ui_window`-day window
(unlike families 014/037's expanding-or-multi-year all-time-high),
the RMS ("root-mean-square") of the daily percentage drawdown from that
local peak over the same window -- combining BOTH depth and persistence
of drawdowns into a single number. A causal percentile rank of this
statistic drives a CONTINUOUS sizing multiplier (never a discrete ladder).

## The required rigorous distinction from families 014 and 037

Full argument in prereg.md. Three independent, programmatically-verified
proofs (not hand-copied), run before the grid:

**Proof 1 (vs. family 014's magnitude-only snapshot):** two synthetic
126-day windows with an IDENTICAL current drawdown depth (15%, family
014's exact statistic) but durations of 10 vs. 100 days -- Ulcer Index
`4.23` vs. `13.36` (>3x), despite family 014 being unable to distinguish
them at all.

**Proof 2 (vs. family 037's duration-only count):** two synthetic 126-day
windows with an IDENTICAL duration (60 days, family 037's exact statistic)
but depths of 10% vs. 30% -- Ulcer Index `6.90` vs. `20.70` (3.0x, matching
the linear depth ratio the RMS formula predicts), despite family 037 being
unable to distinguish them at all.

**Proof 3 (real dev-period SP500 data, strictly pre-2020):** the same two
episodes family 037's own `results.md` established --

| Episode | Trough | Family 014's stat (max `dd`) | This family's stat (`UI_126`) |
|---|---|---|---|
| Deep-but-brief (2018-19) | 2018-12-24 | **19.78%** (larger) | **5.960** |
| Shallow-but-long (2015-16) | 2016-02-11 | **14.16%** (smaller) | **6.996** (larger) |

The shallower-but-longer episode scores a **higher** Ulcer Index despite a
**smaller** family-014 magnitude reading -- the rankings disagree, exactly
as the general argument predicts. `distinctiveness_from_family_014_proven:
true`, all dates confirmed pre-2020.

**Brief distinction from family 003** (ordinary return variance):
asymmetric (downside-only, from a running peak) vs. symmetric; requires a
running-peak reference vs. none at all -- a choppy uptrend has high
variance but near-zero Ulcer Index, a slow grinding decline has low daily
variance but a high Ulcer Index (conceptual argument, prereg.md).

## Ulcer Index formula spot-check (Q4 2018 SP500 crash, real data, pre-2020)

| Date | UI (`ui_window=126`) |
|---|---|
| 2018-01-15 (calm, before the selloff) | 0.59 |
| 2018-12-24 (trough) | 5.96 |
| 2019-11-01 (well past the recovery) | 2.82 |

UI spikes >3x through the trough and decays after the recovery, as
expected. (First-draft check dates, `2018-08-01`/`2019-06-01`, were
rejected pre-grid for overlapping the separate Feb 2018 and May 2019
volatility events -- see `state/bugfix_log.md`, no engine or strategy
logic was affected.)

## Pre-grid non-degeneracy sanity check

| Asset | Dev days | Frac. `m_t == 1.0` (primary) | Std(m_t) | Non-degenerate? |
|---|---|---|---|---|
| SP500 | 23,109 | 1.36% | 0.571 | PASS |
| GOLD | 4,848 | 5.49% | 0.575 | PASS |
| SILVER | 4,850 | 5.30% | 0.582 | PASS |
| BTC | 1,932 | 13.30% | 0.537 | PASS |
| OIL | 4,857 | 5.54% | 0.543 | PASS |

## Cash-reserve dynamics check (required this iteration)

Primary config (`min_mult=0.5 < 1.0`, chosen deliberately per families
014/037's own documented `near_high_mult=1.0` reserve-nullification
lesson): average cash (`$125.50`) meaningfully exceeds plain DCA's
baseline (`$103.88`, +21%) -- a genuine reserve is banked -- and average
cash during depressed-UI (high-multiplier) weeks (`$103.99`) is lower than
during elevated-UI (low-multiplier) weeks (`$147.40`) -- the reserve is
drawn down when the multiplier calls for it. Both checks **PASS**.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| UI formula spot-check (Q4 2018 SP500 crash) | PASS |
| Decoupling proof 1 vs. family 014 (depth fixed, duration varied) | PASS |
| Decoupling proof 2 vs. family 037 (duration fixed, depth varied) | PASS |
| Real-data divergence example vs. family 014 (two known pre-2020 episodes) | PASS |
| Cached vs. uncached `compute_multiplier` match | PASS |
| `enabled=False` bypass reproduces plain DCA bit-for-bit | PASS |
| `k=0.0` grid-shaped code path (real, not bypass) also reproduces plain DCA bit-for-bit | PASS |
| Cash-reserve check: avg cash, primary vs. DCA baseline | PASS (differs meaningfully) |
| Cash-reserve check: avg cash, low-mult (elevated UI) vs. high-mult (depressed UI) weeks | PASS |
| Cash and positions never negative (DCA, primary, aggressive corner) | PASS |
| Capital deployed never exceeds cumulative deposits + interest, principled "never invest" ceiling bound (primary, aggressive corner) | PASS |
| No-lookahead (spot-checked at `t=6000` and `t=20000`) | PASS |
| Point-in-time macro data | N/A -- price-only signal |
| `PRIMARY_CONFIG` is a member of `grid_configs()` (import-time assertion) | PASS |
| No dev-period check references a date on/after 2020-01-01 or an unseen ticker | PASS |

## Primary configuration: `ui_window=126, pctile_lookback=252, k=1.0, min_mult=0.5` (`max_mult=2.0, max_lump_multiple=3.0` fixed)

### Sec 4.1 result (vs. plain per-asset DCA)

| Asset | Strategy wealth/invested (0.1%) | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both, 0.1%)? |
|---|---|---|---|---|---|
| SP500 | 85.28080 | 85.27722 | 0.153134 | 0.153097 | **YES** |
| GOLD | 2.23128 | 2.23123 | 0.504764 | 0.504917 | NO (Sharpe loses) |
| SILVER | 1.68685 | 1.68666 | 0.319620 | 0.319677 | NO (Sharpe loses) |
| BTC | 9.85570 | 9.85568 | 1.067335 | 1.067309 | **YES** |
| OIL | 1.18035 | 1.17986 | 0.227785 | 0.227824 | NO (Sharpe loses) |

**Sec 4.1: FAIL.** `beats_dca_count = 2/5` at both 0.1% and 0.25% fees
(need >=3/5). Every asset beats DCA on raw wealth (5/5), but the Sharpe
comparison is lost on GOLD/SILVER/OIL by razor-thin margins (4th-5th
significant digit), the same "wealth wins, Sharpe loses on most assets by
a hair" pattern families 003/014/030/031/034/035/036/037/044 have all
produced with this loop's per-asset trailing-statistic sizing design on
this development sample.

### Sec 4.2 -- Deflated Sharpe Ratio >= 0.95

- Raw weekly Sharpe of the primary config's pooled excess-return series:
  **-0.00573/week** (annualized ~-4.13%) -- genuinely negative.
- `N` (raw trial count at this assessment): **1,491** (196 seed + 1,295
  new, matching `state/trial_counter.json`: 196+1295=1491, and consistent
  with the running `1467 + 24 (this family) = 1491` sanity check against
  family 048's own 1,467 raw-trial figure).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **134**
  clusters.
- **DSR (N_eff-based, used for the decision): 2.34e-22.** Skew -3.71,
  kurtosis 167.9 (heavily left-skewed, extremely fat-tailed).
- DSR (raw-N, conservative reference): 4.24e-22.

**Sec 4.2: FAIL**, decisively (effectively zero either way).

### Sec 4.3 -- not run

Per established precedent (families 001/006/019/021/023/024/037/044/046/
047/048), sec 4.3 is only run when sec 4.1 passes. Here sec 4.1 fails
outright (2/5, need 3/5), so sec 4.3's rolling-window, bootstrap and
placebo legs were skipped -- an explicit, logged gap rather than a
fabricated result, per this iteration's time-budget instruction.

### Sec 4.4 -- robust across parameters (grid diagnostic)

**11 of 24 configurations (45.8%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees -- short of the 2/3 (16/24)
requirement. The pattern is informative: every `ui_window=63,
pctile_lookback=504` and `ui_window=126, pctile_lookback=504` arm (12/12
configs at the 504-day percentile lookback) clears the majority bar
(mostly 3/5, occasionally 2/5), while `pctile_lookback=252` arms are far
weaker and inconsistent (0/5 to 5/5-wealth-only) -- a longer percentile
lookback (roughly 2 trading years) appears to produce a more stable
regime read than the shorter 1-year lookback the primary config uses, but
per sec 4.4 no grid arm can be substituted for the primary regardless of
this pattern.

**Sec 4.4: FAIL** (11/24 = 45.8% < 66.7% required).

CSCV probability of backtest overfitting (diagnostic, SP500 grid, 8
splits, 70 combinations): **PBO = 0.629** -- one of the more elevated
overfitting-risk values in this loop (behind families 047's 0.857 and
048's 0.714, ahead of 044's 0.486), consistent with the grid's mixed,
lookback-dependent pass pattern rather than a uniformly-losing or
uniformly-winning grid.

### Sec 4.5 -- distinctness

Not applicable; this family did not become a finalist.

## Verdict

**REJECTED.** Fails sec 4.1 (2/5 combined wealth-AND-Sharpe assets, need
3/5) despite winning on raw wealth for all 5 assets. DSR effectively zero
(sec 4.2 FAIL). Sec 4.3 not run (sec 4.1 fails, per established
precedent). Sec 4.4 FAIL (11/24 = 45.8% < 2/3), CSCV PBO=0.629 (elevated).
Holdout **not** opened (rejected, not a finalist, per sec 8 step 8).

## Interpretation

The Ulcer Index's own combined depth-and-persistence statistic is
genuinely, provably distinct from both family 014's magnitude-only
snapshot and family 037's duration-only count (three independent proofs,
including a real pre-2020 SP500 example where the two prior families'
rankings would disagree with each other and with this family's own), and
the cash-reserve mechanism genuinely funds and draws down a reserve as
designed (unlike family 037's own `near_high_mult=1.0` primary-config
trap, avoided here by choosing `min_mult=0.5<1.0` up front). But being a
mechanistically distinct and correctly-implemented statistic does not, by
itself, produce a result that clears sec 4.1's combined wealth-AND-Sharpe
bar: the primary config's wealth-side edge is real but small (5/5 assets,
razor-thin margins), and that small edge is not accompanied by a
consistent Sharpe-side edge (2/5 assets), the same general pattern this
loop's other continuous-percentile-driven single-asset sizing families
(003/014/030/031/034/035/036/037/044) have repeatedly produced on this
development sample. The grid's own diagnostic pattern -- a longer
1-year-vs-2-year percentile lookback materially changing the pass rate --
is a real, mechanistically sensible finding (a longer lookback gives the
percentile rank a more stable regime read) but cannot rescue the primary
config under sec 4.4's own rule against retroactively switching to a
better-looking grid arm.

## Judgment calls made in this iteration

1. **Chose the Ulcer Index's running peak and RMS-averaging window to be
   the SAME single window length (`ui_window`)**, per Martin & McCann's
   original definition, rather than adding a second, independent
   long-run all-time-high parameter (as families 014/037 use). This kept
   the family at 4 tunable parameters (well under the 5-parameter
   ceiling) while making the family's reference-point choice itself
   (a strictly LOCAL, resetting peak) a genuine additional point of
   distinction from families 014/037's expanding-or-multi-year `ATH_t`,
   beyond just the depth-and-duration-combining RMS formula.
2. **Chose `min_mult=0.5 < 1.0` in the PRIMARY configuration** (not just
   somewhere in the grid), directly applying family 014/037's own
   documented lesson that a `near_high_mult`/floor `>= 1.0` in the primary
   config silently nullifies any reserve funding under the engine's
   no-leverage cash cap. Verified pre-grid (per this iteration's explicit
   instruction) that the primary config's realized average cash balance
   does meaningfully differ from DCA's (+21%), avoiding the bit-for-bit-
   DCA outcome family 037's own primary config hit.
3. **Caught and fixed a real mistake in the formula-spot-check's own
   cited dates before the grid ran** (`2018-08-01`/`2019-06-01` each
   overlapped a separate real volatility event, given the family's LOCAL
   126-day window), logged in `state/bugfix_log.md` per the established
   convention -- no engine or strategy logic was affected, and no trial
   was counted before or after the fix.
4. **Constructed two independent synthetic decoupling proofs** (holding
   family 014's statistic fixed while varying duration, and holding
   family 037's statistic fixed while varying depth) in addition to the
   task's real-data-preferred example, since a single real-data pair can
   only ever demonstrate a two-way ranking disagreement with ONE prior
   family at a time (the two prior families' own statistics already
   disagree with each other on any given pair of episodes) -- the
   synthetic constructions let the "held-fixed" variable be chosen
   exactly, cleanly isolating the divergence from each prior family in
   turn.
5. **Sec 4.3 skipped entirely**, since sec 4.1 failed decisively for the
   primary config (2/5, well short of 3/5) and the failure pattern (thin,
   inconsistent Sharpe-side margins) matches this loop's now-repeated
   pattern for this general family shape -- consistent with established
   precedent (families 001/006/019/021/023/024/037/044/046/047/048) of
   reserving sec 4.3 for configurations that at least clear the sec 4.1
   bar, logged here as an explicit, reasoned gap per this iteration's
   time-budget instruction.
