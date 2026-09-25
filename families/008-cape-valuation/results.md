# Family 008 results: CAPE / earnings-yield valuation sizing (S&P 500)

**Verdict: REJECTED -- structural.** This family cannot become a finalist
under sec 4.1's standard >=3/5-core-assets win rule regardless of its
SP500 result, because CAPE/earnings-yield is only definable for equities
among the 5 core assets (see prereg.md's scoping decision). It is scored
here on SP500 alone as a **documented single-asset diagnostic**, and its
own numbers -- reported honestly below -- do not clear the bar even on
that one asset. Holdout was **not** opened (task instruction step 7;
holdout is reserved for finalists, and this family cannot be one by
construction).

## Scoping decision (recap; full reasoning in prereg.md)

Unlike families 006/007 (turn-of-month, day-of-week), where the mechanism
itself is asset-agnostic even though the motivating literature was
asset-specific, CAPE/earnings-yield's **mechanism** requires an earnings
series that only exists for S&P 500 among the 5 core assets (gold,
silver, oil and BTC have no earnings). Rather than invent unrelated
per-asset proxy mechanisms (gold real-price-vs-trend, BTC NVT, etc.) under
this one family's pre-registration -- which would conflate several
different mechanisms and literatures under a single declared category,
defeating the point of sec 3.4's one-page/one-mechanism complexity ceiling
-- this family follows **option (b)**: SP500-only, explicitly not
eligible for sec 4.1's pass, logged as structurally out of scope rather
than scored with an invented workaround. **This is a real gap between
sec 4.1's win rule and any fundamentals-based signal that is legitimately
single-asset by construction, flagged explicitly for the owner** -- see
prereg.md's "Single-asset scoping decision" section for the full
reasoning, and the note at the end of this file for why it also applies
to seed-queue ideas #9 (BTC on-chain valuation) and #12 (commodity
term-structure carry).

## Data reachability and earnings-series substitution (recap)

Shiller's own CAPE source (`econ.yale.edu`) returned a direct 403, and
every third-party mirror tried (multpl.com, data.nasdaq.com/quandl,
quandl.com, stooq.com, datahub.io, img1.wsimg.com) was rejected by this
environment's egress-proxy allowlist. FRED's `CP` (Corporate Profits
After Tax, quarterly) and `CPIAUCSL` (CPI-U, monthly) **are** reachable
and were used to build a Shiller-shaped P/E10 valuation ratio (real SP500
price / trailing-10-year average real corporate profits) with the same
BEA/BLS publication-lag discipline `v2/data.py`'s existing macro-fetch
convention already uses (6-month lag for `CP`, 2-month lag for `CPIAUCSL`,
the latter identical to the codebase's existing `weekly_fred_lagged`).
This is a documented substitution of the earnings input, not a change of
mechanism -- the sizing signal only ever uses this ratio's own **trailing,
point-in-time percentile rank**, never its absolute level, so the
substitution does not change what the signal measures. See prereg.md for
the full construction and its one flagged limitation (FRED's `CP` series
is used at its current, single-vintage values with a fixed release-lag
offset, not full ALFRED point-in-time vintage-diffing -- the same
precedent already accepted in this codebase for `UNRATE`/`TCU`).

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| Degenerate config (`enabled=False`, forces same-week-end-day full-deposit buy every week, bypassing the valuation/percentile computation) reproduces plain DCA exactly (bit-for-bit on units and cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary CAPE-sizing config) | PASS |
| No-lookahead: perturbing all data after day t leaves every order on/before t unchanged (primary config, standard interior spot-check) | PASS |
| No-lookahead, targeted at the rolling-percentile construction, at the first trading day of 1990 (early in the signal's usable era) | PASS |
| No-lookahead, targeted at the rolling-percentile construction, at the last trading day of 2018 (late in development) | PASS |
| Point-in-time macro data (CP/CPIAUCSL release-lag rules + strictly-trailing rolling percentile rank, never a full-sample percentile) | PASS (verified structurally; see prereg.md) |
| Total capital deployed never exceeds the SAME $500/week deposit stream's own cumulative value (deposits + interest earned while un-invested), path-wise | PASS |

## Primary configuration: `pctile_window_years=20, low_pctile=20, high_pctile=80, max_mult=2.0, min_mult=0.5`

(20-year trailing percentile window; bottom/top-quintile thresholds, a
literature-standard split per Asness et al.-style valuation-quintile
tilts; a full 4x sizing range between the cheapest and richest bands,
symmetric in log-space around 1.0 -- none tuned on this loop's own data.)

### SP500 result (diagnostic -- see scoping decision above; sec 4.1's >=3/5 rule is not scored)

At 0.1% fees:

| | Strategy | DCA |
|---|---|---|
| Wealth / invested | 85.210x | 85.277x |
| Sharpe (weekly NAV returns) | 0.15450 | 0.15457 |
| CAGR | 5.821% | 5.822% |
| Max drawdown | -85.96% | -85.96% |
| Avg. cash share | 0.31% | -- |

**Beats DCA (both wealth AND Sharpe): NO** -- fails on both metrics, by a
very small margin, at 0.1% fees.

At 0.25% fees, the pattern is identical (85.082x vs 85.149x wealth;
0.15374 vs 0.15381 Sharpe) -- **fails on both metrics at both fee
levels.**

The average cash share held by the primary configuration is tiny
(0.31%), which is the main mechanical reason the result sits so close to
DCA in both directions: at `low_pctile=20`/`high_pctile=80` (a fairly
wide "neutral" middle band covering 60 percentile points, where the
multiplier only partially tilts) combined with `max_mult=2.0`/
`min_mult=0.5`, the strategy spends almost all its banked cash back down
again relatively quickly rather than holding a persistently large cash
buffer through any one multi-year regime, so the net wealth effect ends
up being a wash rather than a decisive win or loss in either direction --
unlike families 006/007's BTC results, where full-banking
(`mild_tilt_fraction=0.0`) produced a much larger, more decisive
opportunity-cost drag.

### Deflated Sharpe Ratio (diagnostic; N_eff/DSR computed on SP500's own excess series, not a 5-asset pooled series -- deviation flagged below)

- Raw weekly Sharpe of the primary config's excess-return series (vs.
  DCA, SP500 only): **-0.0149/week** (annualized ~-10.7%) -- negative on
  average, consistent with the primary config's small net underperformance
  above. Skew is close to zero (0.014) but kurtosis is high (42.4),
  reflecting the occasional large multiplier-driven purchase relative to
  DCA's smooth weekly buys.
- `N` (raw trial count at this assessment): **384** (196 seeded + 156
  from families 001-007 + 32 new from this family's grid).
- `N_eff` (average-linkage clustering, distance sqrt(0.5(1-rho)),
  rho >= 0.5 threshold): **38** clusters (unchanged from family 007's
  count -- this family's own 32 grid configs cluster among themselves and
  with prior BTC/SP500-heavy clusters rather than adding new distinct
  clusters, consistent with how correlated multiplier-timing variants of
  the same underlying signal tend to be).
- **DSR (N_eff-based): 6.80e-31** -- essentially zero.
- DSR (raw-N, conservative reference): 7.39e-42.

**Deviation from the standard pooled-excess-series DSR convention,
flagged explicitly (per the task's instruction):** every other family in
this loop pools the equal-weight average of 5 per-asset excess series
before computing DSR (sec 3.3). Since this family only has one asset,
`N_eff`/DSR here are computed directly on **SP500's own excess-return
series**, not a pooled average. This makes the DSR here more exposed to
SP500's own idiosyncratic sample-path risk than a genuinely pooled
5-asset DSR would be -- there is no averaging-across-assets
noise-reduction at all. Read this family's DSR as "the deflated
probability that SP500 alone has a real edge," not as directly comparable
in construction to families 001-007's pooled-5-asset DSR figures, even
though the DSR/N_eff formula itself is applied identically.

### Grid diagnostic (sec 4.4-shaped, not scored pass/fail -- see scoping decision)

**3 of 32 configurations (9.4%) beat DCA on wealth AND Sharpe at both fee
levels** -- far below the 2/3 bar sec 4.4 would apply if this family were
eligible to be scored against it. All 3 passing configs share
`pctile_window_years=15` and `high_pctile=70` (tighter/shorter-window
variants); every `pctile_window_years=20` config in the grid -- including
the primary -- fails. This 15-vs-20-year split is a useful diagnostic on
its own: it suggests whatever small edge exists in this development
sample is sensitive to the percentile window's length, which is not a
robust sign, though the grid is too small (32 configs, single asset) to
draw a strong conclusion either way -- reported honestly as a mixed,
inconclusive grid result rather than evidence for or against the
mechanism.

CSCV probability of backtest overfitting (diagnostic, full 32-config
grid, 8 splits, 70 combinations, SP500 weekly strategy returns at 0.1%
fee): **PBO = 0.243** -- moderate, worse than family 006/007's SP500
grids (PBO=0.0 each) but well short of a coin flip; consistent with a
grid that has a real but narrow and window-length-sensitive edge in a
small minority of its configurations, exactly the pattern the 9.4% pass
rate above already shows.

### Rolling windows / bootstrap / placebo (sec 4.3) -- not run

Following the precedent set by families 006 and 007 (sec 4.3 is only
attempted "if sec 4.1 passes"), and given that this family's primary
config fails outright on the one asset available to it (SP500, both
metrics, both fee levels) and its DSR is effectively zero, sec 4.3 was
not run. This also kept the iteration within its time budget. Separately
and independently, this family could never pass sec 4.1 as literally
written regardless of any sec 4.3 result, since it only has 1 of the
required 5 core assets available -- so running sec 4.3 in full would not
have changed the verdict.

## Verdict

**REJECTED -- structural.** Per the task's explicit instruction: even
though SP500's own primary-config result is weak on its own merits (fails
wealth and Sharpe at both fee levels, DSR effectively zero, only 9.4% of
the grid beats DCA), the verdict is recorded as **rejected for a
structural reason** (this family cannot satisfy sec 4.1's >=3/5-core-
assets rule with only one eligible asset), not silently worked around or
scored as if it had a defined single-asset pass path that the charter
does not provide. Holdout was **not** opened.

## Flag for the owner: a real ambiguity in how sec 4.1's win rule applies to single-asset fundamentals signals

This is the first family in the loop where the *mechanism itself* (not
merely its motivating literature) is single-asset by construction. The
charter's sec 4.1 win rule (">=3 of 5 core assets") implicitly assumes
every mechanism can be meaningfully tested on all 5 core assets, which
holds for every purely price/calendar-based mechanism tested so far
(001-007) but does not hold for a fundamentals-based valuation signal
like CAPE, which requires an earnings series that literally does not
exist for gold, silver, oil or BTC. **Two other queued ideas have the
exact same structural issue and will hit this same wall when their turn
comes:**

- **Idea #9 (BTC on-chain valuation: MVRV, realized price)** -- an
  on-chain valuation signal is BTC/crypto-specific by construction (no
  other core asset has an on-chain ledger to compute MVRV/realized price
  from).
- **Idea #12 (commodity term-structure carry)** -- requires a tradable
  futures curve, which does not exist for BTC-USD (spot only) or ^GSPC as
  tested in this loop, restricting it in the other direction (to
  gold/silver/oil only, still fewer than 5, and possibly to a subset of
  those 3 depending on curve data availability).

**No change is made to the charter or to sec 4.1 here** -- this family
followed the charter exactly as written, including accepting that a
structurally single-asset mechanism cannot pass. But the owner may want
to consider, before idea #9 or #12 comes up in the queue, whether sec 4.1
should define an explicit (and presumably higher, to stay conservative)
single-asset pass bar for mechanisms that are legitimately single-asset
by construction, rather than every such idea being capped at "diagnostic
only, cannot pass" regardless of how strong its one-asset result turns
out to be. This iteration's own SP500 result happens to be weak anyway
(so the practical stakes of this ambiguity were low this time), but a
future single-asset idea could plausibly produce a strong one-asset
result that the charter, as currently written, has no path to ever
recognize as a finalist.
