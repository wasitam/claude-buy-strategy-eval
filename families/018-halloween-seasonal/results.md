# Family 018 results: "Halloween effect" / Sell-in-May seasonal deposit timing

**Verdict: REJECTED.** The primary configuration fails sec 4.1: it beats
plain DCA on final wealth AND Sharpe on only **2 of 5** core assets at
both fee levels, short of the required 3/5 majority. Sec 4.4's grid
diagnostic also fails: only **6 of 16** configurations (37.5%) reach the
combined majority bar (need >=11/16). DSR is effectively zero. Holdout
was **not** opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family** (sec 4.1's Single-asset line),
across all 5 core assets, category **Seasonality / execution timing**.
Signal: a purely calendar-based annual window -- a "strong season"
(default November-April) in which banked cash from the "weak season"
(default May-October) is deployed up to a lump-multiple cap each week, and
a weak season in which only `mild_tilt_fraction * weekly_deposit` is
bought on schedule, banking the rest. No sells, ever; no leverage.

**Explicit distinction from families 006 and 007 (required by this
iteration's task):** prereg.md documents that the three "Seasonality /
execution timing" families operate at three different, non-nested
calendar granularities, each roughly an order of magnitude apart --
family 006 is a **monthly** cycle (`f(day-of-month)`, ~4-trading-day
window recurring every ~21 trading days, institutional payroll/rebalancing
flow story), family 007 is a **weekly** cycle (`f(day-of-week)`, a single
weekday recurring every ~5-7 calendar days, crypto weekday/weekend
liquidity-composition story), and this family is an **annual** cycle
(`f(month-of-year)`, a ~6-calendar-month window recurring once a year,
summer vacation/risk-aversion story from a 37-country equity panel). Each
cites independent literature with an independent mechanism.

## Pre-backtest non-degeneracy sanity check (required by this iteration's
task, before any grid run)

Because the signal is a fixed calendar split (not a data-derived
threshold like families 011/014/015/016/017's signals), the primary
config's (`strong_season_start_month=11, weak_season_start_month=5`)
strong-season condition was confirmed to fire on close to 50% of trading
days for every asset, directly against each asset's own trading-day index,
before any backtest was trusted:

| Asset | Dev days | Strong-season days | Frac. strong |
|---|---|---|---|
| SP500 | 23,109 | 11,336 | 49.05% |
| GOLD | 4,848 | 2,371 | 48.91% |
| SILVER | 4,850 | 2,371 | 48.89% |
| BTC | 1,932 | 967 | 50.05% |
| OIL | 4,857 | 2,374 | 48.88% |

All 5 assets land within the pre-registered (40%, 60%) sanity band and are
tightly clustered near 50%, as expected for a ~6-month/6-month calendar
split -- confirms the seasonal-window computation is implemented
correctly (no off-by-one month-boundary bug) before any backtest is
trusted.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000`) -- trivial by construction since the signal is a pure function of calendar date with no price dependence, but still run explicitly per the task's instruction, not assumed | PASS |
| Point-in-time macro data | N/A -- calendar-only signal, no macro/external data at all |
| Total capital deployed never exceeds cumulative deposits + interest | PASS |

## Primary configuration: `strong_season_start_month=11, weak_season_start_month=5, mild_tilt_fraction=0.0, max_lump_multiple=6`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.789 | 85.277 | 0.15788 | 0.15310 | YES |
| GOLD | 2.202 | 2.231 | 0.51886 | 0.50492 | NO (wealth fails) |
| SILVER | 1.678 | 1.687 | 0.33225 | 0.31968 | NO (wealth fails) |
| BTC | 8.833 | 9.856 | 1.07880 | 1.06731 | NO (wealth fails) |
| OIL | 1.226 | 1.180 | 0.25049 | 0.22782 | YES |

**Sec 4.1: FAIL**, 2/5 core assets (SP500, OIL) at both fee levels (0.25%
results are qualitatively identical -- see `_primary_per_asset.csv`),
short of the required 3/5 majority. As with families 003/005/006/007/017,
the primary config's Sharpe beats DCA on **all 5** assets (the mechanism
smooths the return path everywhere -- concentrating buys into the
historically-favorable half of the year reduces realized volatility) but
wealth only beats DCA on 2 of 5 (GOLD, SILVER, BTC lag on final wealth
despite the Sharpe improvement), so the combined bar fails on 3 of the 5
assets.

### Grid diagnostic (sec 4.4)

**6 of 16 configurations (37.5%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees. Sharpe alone is essentially
guaranteed to beat DCA everywhere (15 of 16 configs hit 5/5 on Sharpe);
wealth is again the binding constraint. Notably, all 6 passing
configurations use `strong_season_start_month=10` (the October-start
shifted window, not the primary's literal November Bouman & Jacobsen
start), and 4 of those 6 also use `weak_season_start_month=4` -- the
shifted `(Oct, Apr)` window arm outperforms the primary `(Nov, May)` arm on
this metric across the grid (8/8 October-start configs beat 2-3/5 assets
each, vs. only 0/8 November-start configs reaching 3/5; the best
November-start showing, including the primary itself, tops out at 2/5).
This is a genuine, pre-registered grid arm (not chosen after seeing
results) but the loop's own rule (sec 4.4) is explicit that **only the
primary configuration can become a finalist** -- this grid pattern is
diagnostic only and does not change the primary's own verdict.

**Sec 4.4: FAIL** (need >=2/3 = 10.67 -> 11/16; got 6/16 = 37.5%).

CSCV probability of backtest overfitting (16-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.029** -- very
low; the grid's pattern (October-start configs outperform November-start
configs consistently) is not an overfitting artifact of resampling, it
holds up across split combinations.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series
  (strategy weekly NAV return minus DCA weekly NAV return, averaged
  across the 5 assets): **+0.00255** (weekly, **+0.0184 annualized**) --
  barely positive, essentially indistinguishable from zero at this scale.
- `N` (raw trial count, whole-loop pool): **563** (196 seeded + 351 from
  families 001-017 + 16 new from this family's grid; matches the sanity
  check 196+367=563, `state/trial_counter.json["new"]`=367 after this
  family).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **60**
  clusters (unchanged from family 017 -- this family's grid did not
  contribute any new distinct clusters, all 16 configs' pooled
  excess-return series correlate at rho>=0.5 with an existing cluster).
- **DSR (N_eff-based): ~1.33e-24** -- effectively zero. The raw excess
  Sharpe (0.00255/week) is far below the SR0=0.151 threshold implied at
  this N_eff, and the series' high excess kurtosis (709.25, from a
  handful of dominant seasonal episodes concentrated into large,
  infrequent lump-sum purchases -- the highest kurtosis observed in this
  loop so far, consistent with `mild_tilt_fraction=0.0` producing very
  lumpy, seasonally-concentrated buys) further penalizes the DSR
  calculation.
- DSR (raw-N, conservative reference): ~5.50e-30, also effectively zero.

**Sec 4.2: FAIL**, decisively -- a barely-positive raw excess Sharpe
cannot clear the trial-count-adjusted DSR bar at either N or N_eff.

### Robustness (sec 4.3)

**Not run.** Per the established precedent (sec 4.3 is only attempted if
sec 4.1 passes first), and sec 4.1 fails (2/5, short of the 3/5
majority), the rolling-window / block-bootstrap / placebo battery was
skipped (the run script is wired to print an explicit skip notice on a
sec-4.1 fail, and correctly skipped it here).

## Verdict

**REJECTED.** Sec 4.1 fails at both fee levels (2/5 core assets, short
of the 3/5 majority -- driven by Sharpe improving broadly while wealth
lags on 3 of 5 assets, the same qualitative pattern already seen in
families 003, 005, 006, 007 and 017). Sec 4.4's grid diagnostic fails
(6/16, need >=11/16). DSR is effectively zero (barely-positive raw
Sharpe, swamped by the trial-count penalty and very high excess
kurtosis). Holdout was **not** opened.

## Interpretation

The Halloween/Sell-in-May mechanism, at its canonical Bouman & Jacobsen
(2002) November-April window, produces the same qualitative pattern as
every prior "execution-timing-within-a-fixed-schedule" family in this
loop (003, 005, 006, 007, 017): a real, broad improvement in
risk-adjusted return (Sharpe beats DCA on 5/5 assets) that does not
translate into more final wealth on a majority of assets. Unlike family
006's SP500-specific pass or family 007's expected BTC-specific
asymmetry, this family's broader (37-country, not single-asset) literature
grounding did not produce a broader pass -- if anything the pattern is
close to the reverse of what family 006 and 007's own asymmetric priors
would have predicted: SP500 (the most literature-relevant asset) does
pass, but so does OIL (not obviously predicted), while GOLD, SILVER and
BTC -- three quite different asset types -- all fail on wealth despite
uniformly better Sharpe. The grid's own diagnostic is notable and
recorded honestly: every one of the 6 grid arms that reaches the 3/5
majority bar uses the one-month-earlier `(Oct, Apr)` shifted window rather
than the primary's literal `(Nov, May)` Bouman & Jacobsen window --
consistent with, but not proof of, a plausible boundary-drift explanation
(if the true seasonal turning point in this development sample sits
somewhat earlier than the literature's original 1970s-1998 international
panel would suggest, a one-month-early window would capture more of the
favorable early-autumn recovery and less of the weakest late-summer
weeks). Per sec 4.4, this cannot promote the family: only the
pre-registered primary configuration is eligible to become a finalist,
and the primary config itself is a clean, pre-registered fail. This does
not rule out a differently-windowed seasonal mechanism, but this specific
family, as pre-registered and tested, does not clear sec 4.1.

## Trial accounting

- Seed: 196 (unchanged).
- New before this family: 351 (families 001-017).
- New from this family's 16-config grid: 16.
- New total after this family: 351 + 16 = 367 (matches
  `state/trial_counter.json`).
- Raw N at assessment: 196 + 367 = **563** (matches `n_total_raw` in
  `_run_output.json`).
- N_eff at assessment: **60** (unchanged from family 017 -- no new
  distinct clusters).
- Families (new) count: 16 (was 15 before this family).

## Files

- `families/018-halloween-seasonal/prereg.md` -- pre-registration
  (committed before any backtest).
- `families/018-halloween-seasonal/grid_results.csv` -- full 16-config x
  5-asset x 2-fee grid.
- `families/018-halloween-seasonal/_primary_per_asset.csv` -- primary
  config's per-asset summary.
- `families/018-halloween-seasonal/_run_output.json` -- machine-readable
  summary of all checks above.
- `src/backtest/v3/strategies/halloween_seasonal.py` -- implementation.
- `scripts/v3/run_018_halloween_seasonal.py` -- end-to-end run script.
- `state/trials/new_018_*.csv` -- 16 new trial excess-return series.
