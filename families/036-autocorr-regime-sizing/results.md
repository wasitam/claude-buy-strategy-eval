# Family 036 results: Return-autocorrelation regime sizing

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively
(beats DCA on final wealth AND Sharpe on only **2 of 5** core assets at
both 0.1% and 0.25% fees, short of the required 3/5). Since sec 4.1 is the
gating check, sec 4.2/4.3 are not run in full, per established loop
precedent (families where sec 4.1 fails go straight to REJECTED). Sec
4.4's grid diagnostic also fails decisively (only 16.7% of the 36-config
grid clears the majority-of-assets bar, need >=2/3), and the CSCV PBO
(0.414, diagnostic only) is high. Holdout was **not** opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family** (sec 4.1's Single-asset line), across
all 5 core assets, category **Trend / time-series momentum exit** (the
seed queue's own categorization of idea #36). Source: Lo, A.W. and
MacKinlay, A.C. (1988), *Stock Market Prices Do Not Follow Random Walks*,
Review of Financial Studies. Signal: each day's trailing lag-1 sample
autocorrelation of daily log returns, `rho_1_t = corr(r_i, r_{i-1})` over a
trailing `ac_window`-day window, converted to a causal, point-in-time
percentile rank `pctile_t` within its own trailing `pctile_lookback`
window, then a continuous sizing multiplier
`m_t = clip(1 + k*(2*pctile_t - 1), min_mult, max_mult)` -- identical
functional form to family 031's percentile-driven Kelly-Sharpe sizing,
applied to a different underlying statistic (serial dependence rather than
a mean/variance ratio).

## The required fourfold rigorous distinction from families 003, 005, 030
and 031 (full reasoning in prereg.md)

**(a) What each statistic measures:** family 003's realized variance is
the **dispersion** (second moment) of returns; family 005's TSMOM signal
is the **sign of the trailing return level** (first moment / running sum);
family 030's streak count is a **discrete, magnitude-blind count** of
consecutive same-direction days; family 031's Kelly-Sharpe ratio is
**mean/std**, a ratio of the first two moments. This family's `rho_1` is
`Cov(r_t, r_{t-1}) / Var(r)` -- the **serial dependence structure** of
consecutive returns, invariant to any reordering of a fixed multiset of
daily returns that leaves all four other statistics unchanged.

**(b) Concrete constructed numeric example (verified programmatically at
run time against the module's own `compute_autocorr_signal`, not
hand-copied -- see
`scripts/v3/run_036_autocorr_regime_sizing.py::check_toy_distinctiveness_example`):**
two 8-day toy return paths, permutations of the identical multiset of four
`+1%` and four `-1%` daily returns:

- Path A (choppy, day-to-day reversal): `[+1,-1,-1,+1,-1,+1,-1,+1]` (%)
- Path B (trending, paired-run persistence): `[-1,-1,+1,+1,-1,-1,+1,+1]` (%)

| Statistic | Path A | Path B | Identical? |
|---|---|---|---|
| Mean return (family 005's level) | `0.000000` | `0.000000` | YES |
| Sample variance (family 003's statistic) | `0.00011429` | `0.00011429` | YES |
| `sign(sum of returns)` (family 005's exact statistic) | `0` | `0` | YES |
| `mean/std` "Sharpe" (family 031's statistic) | `0.000000` | `0.000000` | YES |
| Max consecutive-same-direction streak (family 030's statistic) | `2` | `2` | YES |
| **Lag-1 autocorrelation `rho_1` (this family's statistic)** | **`-0.750000`** | **`+0.166667`** | **NO** |

All four prior families' statistics are exactly identical on these two
paths -- a strategy sized off any of families 003/005/030/031 alone would
treat Path A and Path B as indistinguishable. This family's `rho_1`
correctly registers the decisive difference (`-0.75` vs. `+0.167`), proof
by direct construction that lag-1 autocorrelation carries information the
other four statistics cannot see at all.

## Formula spot-check (task-required check (b))

Independently re-derived the lag-1 autocorrelation formula by hand
(`np.corrcoef` on raw log-return arrays) and cross-checked against the
module's own vectorized rolling-correlation implementation on two real,
known SP500 dev-period windows:

| Window | Description | Hand `rho_1` | Module `rho_1` | Match |
|---|---|---|---|---|
| 2013-01-02..2013-12-31 | Grinding low-vol uptrend | -0.09542 | -0.09542 | PASS |
| 2011-08-01..2011-09-30 | US credit-downgrade whipsaw | -0.21094 | -0.21094 | PASS |

Both windows match the module's computation to floating-point precision.
The trending window's `rho_1` (`-0.095`) is materially less negative than
the choppy whipsaw window's (`-0.211`) -- directionally sensible (a
smoother trend shows weaker day-to-day reversal tendency than a violent
whipsaw), though neither real window happens to show strongly *positive*
autocorrelation in this dev sample (daily-return lag-1 autocorrelation for
real assets is typically small and often slightly negative, consistent
with the literature's own finding that the effect, while statistically
detectable, is economically modest at the single-day frequency) -- the toy
example above, not this real-data spot-check, is the primary proof of
distinctiveness from families 003/005/030/031, exactly as prereg.md
specifies. All dates referenced are confirmed pre-2020 (`dates_all_pre_holdout: true`).

## Pre-grid non-degeneracy sanity check

| Asset | Dev days | Frac. `m_t == 1.0` (default) | Std(m_t) | Non-degenerate? |
|---|---|---|---|---|
| SP500 | 23,109 | 1.67% | 0.511 | PASS |
| GOLD | 4,848 | 6.23% | 0.491 | PASS |
| SILVER | 4,850 | 6.35% | 0.503 | PASS |
| BTC | 1,932 | 15.32% | 0.493 | PASS |
| OIL | 4,857 | 6.34% | 0.501 | PASS |

## Cash-reserve dynamics check (family 033's lesson, generalized to this
family's continuous multiplier per the task brief's checkpoint (e))

With `min_mult=0.5 < 1.0`, the primary config's average cash balance
(`$123.53`) is materially higher than the plain-DCA baseline's (`$103.88`)
-- a genuine reserve is banked -- and average cash during high-multiplier
(elevated-`rho_1`-percentile, `m_t > 1`) weeks (`$105.71`) is lower than
during low-multiplier (depressed-`rho_1`-percentile, `m_t < 1`) weeks
(`$141.53`) -- the banked reserve is drawn down when the elevated-percentile
signal fires. Both checks **PASS**.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Autocorrelation formula spot-check (2 known real windows, hand vs. module) | PASS (both match, directionally sensible) |
| Toy numeric-distinctiveness check vs. families 003/005/030/031 | PASS (all 4 prior statistics identical, `rho_1` decisively different) |
| Cash-reserve check: avg cash, strategy vs. DCA baseline | PASS (strategy > DCA) |
| Cash-reserve check: avg cash, high-mult tier vs. low-mult tier | PASS (high-mult < low-mult) |
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| `k=0.0` grid-shaped code path (real, not the bypass) also reproduces plain DCA bit-for-bit | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (aggressive grid corner: `aw=20, pl=252, k=1.5, min=0.25`) | PASS |
| Capital deployed never exceeds cumulative deposits + interest, principled "never invest" ceiling bound (primary config) | PASS |
| Capital deployed never exceeds cumulative deposits + interest (aggressive grid corner) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000` and `t=20000`) | PASS |
| Point-in-time macro data | N/A -- price-only signal, no macro dependency |
| No dev-period check references a date on/after 2020-01-01 or an unseen ticker | PASS (all dates checked pre-2020, `load_dev()`'s own gate enforces the rest) |

## Primary configuration: `ac_window=40, pctile_lookback=252, k=1.0, min_mult=0.5`

(`max_mult=2.0`, `max_lump_multiple=3.0` fixed, per family 031's precedent.)

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.26740 | 85.27722 | 0.153007 | 0.153097 | NO (both lose) |
| GOLD | 2.23118 | 2.23123 | 0.504894 | 0.504917 | NO (both lose) |
| SILVER | 1.68693 | 1.68666 | 0.319710 | 0.319677 | YES |
| BTC | 9.85508 | 9.85568 | 1.067378 | 1.067309 | NO (wealth loses, Sharpe wins) |
| OIL | 1.18045 | 1.17986 | 0.227870 | 0.227824 | YES |

**Sec 4.1: FAIL** -- only 2/5 core assets (SILVER, OIL) beat DCA on both
wealth and Sharpe at 0.1% fee (need >=3), and the same 2/5 at 0.25% fee.
Every margin, winning or losing, is razor-thin in absolute terms (as with
every prior family in this loop), and here the pattern tips the wrong way
on the majority of assets: SP500 and GOLD lose on both metrics, and BTC
shows a mixed result (Sharpe wins narrowly, wealth loses narrowly).

### Grid diagnostic (sec 4.4)

**Only 6 of 36 configurations (16.7%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees -- need >=2/3 (24/36). The
passing configs cluster at `pctile_lookback=504` with `k=1.0` (moderate
sensitivity) and shorter `ac_window` (20), or `ac_window in {40,60}` with
the smallest `k=0.5`; higher-`k` (more aggressive) arms and the primary
config's own `pctile_lookback=252` at `k=1.0` fall short. CSCV PBO = 0.414
(moderate-to-high, consistent with a grid that is not robustly beating DCA
across most of its declared parameter space).

### Sec 4.2: Deflated Sharpe Ratio -- FAIL (reported for completeness; not
required once sec 4.1 fails)

- `N_eff = 107` (raw `N = 1105`, seed 196 + new 909 across all families
  tested through family 036: `196 + 873 (prior) + 36 (this family) = 1105`,
  sanity-checked against family 035's own confirmed `1069` raw-trial count).
- DSR (N_eff-based): **1.38e-23** (need >= 0.95).
- DSR (raw-N, conservative reference): **4.92e-25**.
- Both driven by the primary config's pooled excess-return series having a
  negative raw weekly Sharpe (`-0.00884`, annualized `-0.0637`).

### Sec 4.3: not run in full

Sec 4.1 failed, so sec 4.3's rolling-window, bootstrap and placebo legs
were skipped per established loop precedent (they are reserved for
configs that at least clear the sec 4.1 bar, to avoid spending the
time-budget on a config that cannot become a finalist regardless).

## Assessment summary

| Check | Result | Pass? |
|---|---|---|
| Sec 4.1 (beats DCA >=3/5, both fees) | 2/5 at both fees | FAIL |
| Sec 4.2 (DSR >= 0.95) | 1.38e-23 (N_eff), 4.92e-25 (raw N) | FAIL |
| Sec 4.3 (rolling/bootstrap/placebo) | not run (sec 4.1 gate not cleared) | N/A |
| Sec 4.4 (>=2/3 of grid beats DCA majority) | 6/36 (16.7%) | FAIL |

**Verdict: REJECTED.** Logged, not promoted to finalist or near-miss (sec
4.1 itself fails, distinct from a near-miss which clears sec 4.1 but fails
sec 4.2-4.4). Holdout not opened, per sec 5.4 (holdout is reserved for
finalists only).

## Judgment calls

1. **`pctile_lookback` grid set to `{252, 504}`** rather than family 031's
   own `{504, 756}` -- a deliberate departure, since the underlying
   autocorrelation signal (bounded, typically small-magnitude for daily
   returns) plausibly has a shorter useful memory than a Sharpe-ratio
   signal built from the same return series; this is a genuine grid-design
   choice unique to this family's own statistic, not a copy of a prior
   family's exact grid (unlike family 035's deliberate mirroring of family
   003's grid for a different reason -- isolating an estimator swap). Noted
   here since it means this family's grid diagnostic (sec 4.4) is not
   directly comparable in absolute magnitude to family 031's, though both
   still fail their own respective 2/3 bars.
2. **Real-data formula spot-check did not turn up a strongly positive
   `rho_1` window** in the dev sample searched (both the trending and
   choppy real SP500 windows checked showed negative `rho_1`, just of
   different magnitudes) -- consistent with the literature's own finding
   that daily-return serial correlation for broad indices, while
   statistically significant in large samples, is small and can be
   negative on average at the single-day frequency (short-horizon
   reversal/bid-ask-bounce effects can dominate positive-feedback effects
   at very short horizons). This does not weaken the required distinctness
   proof, which rests on the toy numeric example (task checkpoint (c)), not
   on the real-data spot-check (task checkpoint (b), whose only
   requirement was that the sign/magnitude "make sense" directionally,
   which they do -- the whipsaw window is more negative than the smooth
   uptrend window).
3. Consistent with the loop's broader emerging pattern (families
   003/030/031/034/035 and others): a per-asset trailing-statistic-driven
   continuous sizing multiplier, in this development sample, tends to
   produce razor-thin, inconsistently-signed per-asset margins that do not
   reliably clear the 3/5 sec 4.1 bar, let alone survive sec 4.2's
   trial-count adjustment. This family adds one further data point to that
   pattern (2/5 rather than the borderline 3/5 several prior families
   showed), rather than a reversal of it.
