# Family 043: Amihud-illiquidity cross-asset rotation

**Status:** pre-registered. Committed before any backtest is run on
development data, per research-loop-plan-v3.md sec 7.1(4) and sec 8 step 4.

## Source

Amihud, Y. (2002), "Illiquidity and Stock Returns: Cross-Section and
Time-Series Effects," *Journal of Financial Markets* 5(1), 31-56 -- the
same source family 021 used, applied here to its cross-sectional
application rather than its time-series application. Also: Longstaff,
F.A. (2004), "The Flight-to-Liquidity Premium in U.S. Treasury Bond
Prices," *Journal of Business* 77(3), 511-526; Vayanos, D. (2004),
"Flight to Quality, Flight to Liquidity, and the Pricing of Risk,"
NBER Working Paper 10327 (flight-to-liquidity/quality literature: capital
flees the currently-least-liquid instrument toward the currently-most-
liquid one during stress, rather than being compensated for holding the
illiquid one). Research queue idea #44 (research-loop-plan-v3.md sec 7.3
addendum).

## Mechanism ("why would this work, and who is on the other side?")

Amihud's ILLIQ ratio, `|r_t| / dollar_volume_t`, proxies how much an
asset's price moves per dollar traded -- a rising ILLIQ signals thinning
order books, widening effective spreads, and price impact from
forced/urgent trading (margin calls, deleveraging, acute uncertainty).
Family 021 tested Amihud's own *time-series* implication for a single
asset in isolation: buy MORE of an asset when its OWN ratio is elevated,
betting the resulting price-impact discount mean-reverts (that
family was REJECTED -- 0/5 assets).

This family tests a **different, cross-sectional** implication instead.
At any given time, an illiquidity shock in ONE of the 5 core assets
(BTC, gold, silver, oil, S&P 500) is not necessarily informative about
the *other* four -- these are five economically distinct, largely
segmented markets (a crypto-exchange liquidity crunch says little about
NYSE-cleared S&P 500 liquidity that week). The flight-to-liquidity/
flight-to-quality literature (Longstaff 2004; Vayanos 2004) documents
that when one market's liquidity deteriorates, capital disproportionately
flows toward whatever alternative is currently the *most* liquid, and
that the deteriorating market's own prices are disproportionately
affected by exactly the kind of forced, impact-driven trading Amihud's
ratio detects. A fixed-dollar, fixed-weight DCA investor buys the SAME
$500 into each of the 5 assets every week regardless of which one (if
any) happens to be in a liquidity-stress episode that week -- mechanically
buying into whichever asset's price is currently most distorted by
transitory impact costs, in proportion exactly as often as into the calm
ones. This family redirects the SAME pooled $2,500/week deposit (no
leverage, no extra capital) toward whichever of the 5 assets is
*currently, cross-sectionally, the most liquid* (lowest trailing Amihud
percentile, relative to ITS OWN history) and away from whichever is
currently least liquid, hypothesizing that this avoids paying into
transitory, impact-driven price dislocation in the currently-stressed
asset and instead directs capital to the asset currently trading most
"cleanly."

**Who is on the other side:** systematic fixed-weight buyers (plain DCA)
and anyone else contributing new capital on a fixed schedule regardless of
which asset is currently under liquidity stress -- on this hypothesis they
are, on average, buying disproportionately into whichever of the 5
assets is currently paying the largest temporary price-impact cost, while
this strategy's marginal dollar waits it out in the currently-cleaner
market. **Explicit tension flagged and owned:** this runs in the
*opposite* direction from Amihud's own cross-sectional illiquidity-premium
result (which would say tilt TOWARD illiquid assets to harvest a
compensating return premium, not away from them). This family is not
claiming to harvest that premium; it is a stress-avoidance/flight-to-
liquidity timing mechanism, a different literature and a different sign,
and is documented as such rather than silently assumed compatible with
Amihud's premium story.

## Category

**Cross-asset rotation / relative strength.**

## Rigorous distinction from family 021 (primary burden, per task instruction)

| | Family 021 (Amihud sizing, REJECTED) | Family 043 (this family) |
|---|---|---|
| Statistic | Same: `illiq_t = \|r_t\| / (Close_t * Volume_t)`, causal trailing percentile rank, per asset | Same underlying statistic and percentile computation (reused directly from `amihud_illiquidity.py`) |
| Comparison made | **Within one asset, across time**: asset A's `illiq_t` percentile vs. asset A's OWN trailing history only. Never looks at any other asset. | **Across the 5 assets, at one point in time**: each asset's own-history percentile is computed independently, then the 5 percentiles are RANKED against EACH OTHER cross-sectionally to find "currently most liquid of the 5." Never triggers a decision from a single asset's history alone -- the decision is undefined without at least 2 assets to compare. |
| Action | Sizes asset A's OWN weekly buy up/down based on asset A's OWN regime (elevated -> buy MORE of A, funded by banking cash from A's own calm weeks) | Reallocates the SAME pooled deposit's target WEIGHT across all 5 assets (rebalance-to-target-weight, family 002's precedent); never banks cash, never changes any single asset's buy in isolation |
| Direction | Buys MORE of an asset when ITS OWN ratio is elevated (bets on mean-reversion of a shock) | Buys MORE (higher target weight) of whichever asset is CURRENTLY LEAST illiquid relative to the other 4 (avoids the currently-most-stressed asset) -- opposite economic bet from 021, not merely a relabeling |
| Category | Sizing / valuation | Cross-asset rotation / relative strength |
| Can family 021's rule be recovered as a special/degenerate case of this one? | No. Setting `top_n=5` here collapses to an always-fully-invested EQUAL-WEIGHT rebalanced portfolio (never sizes any single asset up on its own shock); there is no parameter setting of this family that reproduces "buy more of asset A specifically when A's own ratio is elevated." | -- |

Concretely verified (not just asserted) before trusting any grid result,
in the pre-grid non-degeneracy check below: the 5 assets' own-history
Amihud percentiles on any given week-end day are **not** perfectly
correlated with each other (if they were, "currently most liquid of the
5" would degenerate to a fixed, time-invariant ranking and this would be
indistinguishable in effect from picking one favored asset forever --
checked explicitly).

## Brief distinction from families 002 and 010 (secondary, per task instruction)

- **Family 002 (dual momentum, NEAR-MISS):** ranks the 5 assets by
  trailing **total return** (relative momentum) with an absolute-return
  T-bill filter; can exit entirely to cash. This family ranks by a
  **liquidity/price-impact statistic** (Amihud ratio percentile), never
  by return, and is always fully invested across the 5 assets (no cash
  leg) -- structurally different signal, and structurally different
  "opt out" behavior (002 can go 100% cash; this family redistributes
  among the 5 assets themselves).
- **Family 010 (gold/silver ratio, REJECTED):** a **fixed 2-asset**
  relative-value tilt driven by the **price ratio** of gold to silver
  (a valuation/mean-reversion signal on the pair's relative price level).
  This family spans **all 5** core assets, and its signal has nothing to
  do with the price level or ratio of any pair -- it is a volume/impact
  (liquidity) metric, computed independently per asset from that asset's
  own returns and trading volume, with zero shared mechanism to 010's
  price-ratio construction.

Both prior rotation families (002 by return, 010 by a 2-asset price
ratio) are return/price-based; this is the first rotation family in this
loop keyed on a volume-derived liquidity/impact statistic, which is
expected to have low correlation with both (verified empirically after
the grid runs, per plan sec 4.5, if this family becomes a finalist).

## Complexity ceiling (sec 3.4, checked)

- Rules fit on one page (below); computable end-of-day from Close +
  Volume only.
- At most one order per asset per trading day (portfolio rebalance-to-
  target-weight, one buy-or-sell order per asset per week-end day, same
  mechanics as families 002/013/029).
- **3 tunable parameters** (<=5).
- Data: Close + Volume for the 5 core assets, already confirmed reachable
  and reliably present on development data by family 021's feasibility
  finding (reused verbatim here; no new data-reachability risk).
- Grid: **12 configurations** (<=36), one primary configuration declared
  below, before any backtest.

## Exact rules

For each core asset `a` in {SP500, GOLD, SILVER, BTC, OIL}:

1. Daily return `r_t^a`, dollar volume `dv_t^a = Close_t^a * Volume_t^a`,
   Amihud ratio `illiq_t^a = |r_t^a| / dv_t^a` (undefined/NaN wherever
   `Volume_t^a` is zero, missing, or `dv_t^a <= 0` -- identical handling
   rule to family 021, reusing its `compute_illiq` unmodified).
2. Trailing causal percentile rank of `illiq_t^a` among the last
   `illiq_lookback` trading days' DEFINED values only (identical
   computation to family 021's `_trailing_pctile_rank_ignoring_nan`,
   including its 20-valid-observation warm-up floor), giving
   `pctile_t^a` in [0, 100] or NaN before warm-up/on undefined days.
3. Optional smoothing: `smoothed_t^a` = the trailing simple mean of
   `pctile^a` over the last `signal_smooth_days` days (NaN-tolerant,
   `min_periods=1`) -- reduces single-day-noise-driven rotation flips,
   the continuous-smoothing analogue of the "avoid a discrete ladder"
   lesson (here applied to signal noise rather than sizing steps).
4. **Cross-sectional ranking**, evaluated only on each week's last
   trading day (matching families 002/013/029's weekly rebalance
   cadence, the same day the pooled $2,500 deposit lands): among the
   assets with a DEFINED `smoothed_t^a` that day, rank ascending (lowest
   percentile = currently most liquid relative to its own history =
   most favored); select the `top_n` lowest. Ties broken by a fixed
   asset order (stable sort) for determinism.
5. **Target weights:** the selected `top_n` assets each get weight
   `1/top_n` (or `1/k` if fewer than `top_n` assets have a defined
   signal that week, `k` = however many do); the rest get **0%**. If
   ZERO assets have a defined signal (full warm-up only), target weight
   falls back to **equal-weight across all 5** -- this fallback is the
   only role the "otherwise" bucket plays, and it is deliberately never
   zero-for-everyone (the queue's own flagged risk: an "otherwise" weight
   collapsing to 0% and starving the mechanism cannot happen here because
   the non-selected assets are SUPPOSED to be at 0% by design -- the risk
   being guarded against is instead "does the selection ever become
   degenerate/frozen on one fixed asset," checked below).
6. **Rebalance to target weight** every week-end day: `buy_usd^a =
   max(0, target_value^a - current_value^a)`, `sell_usd^a = max(0,
   current_value^a - target_value^a)`, using the portfolio engine's
   existing sells-then-buys, cash-capped fill mechanics (sec 3.2) --
   identical mechanics to family 002's `make_dual_momentum_decider`, no
   new engine logic beyond a differently-computed weight table. Always
   fully invested (weights sum to 1 every week; no dedicated cash leg
   beyond engine mechanics), no leverage, no shorting.

## Parameters (3, all tunable, <=5)

| Param | Meaning | Grid values |
|---|---|---|
| `illiq_lookback` | Trailing window (trading days) for each asset's own causal Amihud-percentile rank | 126, 252 |
| `top_n` | Number of currently-most-liquid assets held at equal weight | 1, 2, 3 |
| `signal_smooth_days` | Trailing smoothing window (days) on each asset's percentile series before cross-sectional ranking (1 = no smoothing) | 1, 10 |

Grid size: 2 x 3 x 2 = **12 configurations** (<=36).

## Primary configuration

`illiq_lookback=252, top_n=1, signal_smooth_days=10` -- a full one-year
own-history reference (matching family 021's own primary lookback and
family 002's default), the strongest/most concentrated expression of the
rotation signal (`top_n=1`), with light smoothing to avoid single-day
noise whipsawing the weekly pick.

## Expected sign

Primarily hypothesized to **improve Sharpe** (avoiding weeks where the
marginal deposit buys into an acutely stressed/illiquid asset's impact-
distorted price) rather than to mechanically raise total wealth --
similar in spirit to several other timing/reallocation families in this
loop where the total capital deployed is unchanged and only its
allocation across time/assets differs. Effect on **wealth** is
directionally uncertain a priori (redirecting deposits away from a
currently-illiquid asset also means missing that asset's OWN subsequent
recovery if the shock reverses quickly, especially for `top_n=1`'s full
concentration) and will be read from the backtest, not assumed.

## Pre-grid checks to run before trusting any grid result (per task instruction)

1. Verify `PRIMARY_CONFIG` is a member of the declared `GRID` via an
   import-time assertion in `liquidity_rotation.py`.
2. Verify the liquidity ranking is non-degenerate: confirm the 5 assets
   do NOT always rank in the same fixed order (i.e., which asset is
   "currently most liquid" genuinely rotates over time, not frozen on one
   asset by a computation bug), and report each asset's selection
   frequency at the primary config.
3. Confirm no sanity check or spot-check anywhere in this iteration
   touches 2020-01-01+ dates or any unseen ticker.
4. Verify realistic weight dynamics: confirm every one of the 5 assets is
   selected a non-trivial fraction of week-end days (no asset is
   permanently starved at exactly 0% for the entire development window,
   which would indicate a ranking bug rather than a genuinely rotating
   signal) and that turnover (fraction of week-ends where the selected
   set changes) is neither ~0% (frozen) nor ~100% (pure noise).

## Implementation checks planned (sec 3.2)

- Degenerate config (`enabled=False`) reproduces fixed-weight 5-asset DCA
  bit-for-bit (units and pooled cash), same convention as families
  002/013/029.
- **Second reference point** (per families 013/029's two-reference-point
  precedent): a `top_n=5` grid-shaped configuration (all 5 assets always
  selected, so target weight collapses to 1/5 each every week) must
  reproduce an independently-built equal-weight-weekly-rebalance reference
  portfolio (the v2 Strategy-C1-equivalent construction family 013 used),
  bit-for-bit, AND that result must differ from plain fixed-weight DCA
  (confirming "degenerate" here means C1-equivalent, not DCA-equivalent --
  the same distinction family 013 had to make explicit).
- Cash and positions never negative (DCA baseline, primary config, most
  concentrated grid corner `top_n=1`).
- No-lookahead: perturbing all 5 assets' data after day `t` leaves every
  order on/before `t` unchanged.
- Point-in-time macro data: N/A (price + volume only, no macro/ALFRED
  series).

## Assessment plan

Portfolio family, assessed against fixed-weight 5-asset DCA per sec 4.1's
Portfolio line, at $2,500/week combined deposit (families 002/013/029
convention). Sec 4.2 (DSR >= 0.95 via N_eff on this family's own pooled
excess series), sec 4.3 (rolling windows / block bootstrap / placebo,
time-boxed to ~60 sims each, run ONLY if sec 4.1 passes, per this loop's
established precedent), sec 4.4 (>=2/3 of the 12-config grid beats DCA;
CSCV PBO as a diagnostic). Holdout opened only if this family becomes a
finalist (sec 5.2/5.3).
