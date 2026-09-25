# Research Loop v3: Find 2 Long-Term DCA Strategies That Actually Beat DCA

**Status:** Charter for an autonomous research loop. The goals, methods and rules below were settled in a Q&A with the owner. The loop runs them as written. Where the loop has to use judgment, this document says so. Everything else is fixed.

**Why this exists:** v1, v2, v2.1 and their extensions tested about 230 configurations across about 12 strategy families. None beat plain DCA on both wealth and Sharpe in a way that survived robustness checks. That much searching on the same data raises the risk of false positives. This loop keeps looking for new ideas, but keeps an honest count of how many times it has looked at the data, and raises the bar to match.

---

## 1. Objective and stopping rule

Find **2 strategies** that beat ordinary weekly DCA on **both final wealth and Sharpe**, by the rules in §4. The two must use **different mechanisms**, and their excess returns must have a **correlation below 0.5** (§4.5). Each must be simple enough to run from end-of-day data without a trading bot (§3).

**The loop stops when either of these happens:**

1. 2 confirmed winners are found (§5.3), **or**
2. **60 new strategy families** have been tested (§6.1).

Either way, it writes the final deliverables (§10). A negative result is a valid outcome and gets reported the same way.

---

## 2. Decisions (settled with the owner)

| Topic | Decision |
|---|---|
| Win metric | Beat DCA on **final wealth AND Sharpe**, using identical deposits |
| Win scope | Single-asset strategies: win on **≥3 of 5** core assets. Portfolio strategies: beat **fixed-weight 5-asset DCA** |
| Overfitting guard | **Sealed holdout + trial-count penalty** (Deflated Sharpe) |
| Allowed actions | Vary buy size / hold cash; sell or trim; rotate between assets. **No leverage, no shorting.** |
| Complexity ceiling | End-of-day decisions, at most **daily** trading, **≤5 tunable parameters**, any **free public** data |
| Stop rule | 2 winners, or **60 new families** |
| Owner involvement | **Fully autonomous.** Notifications on milestones only (§9.3) |
| Funding | Same as v2: **$500/week per asset from zero**, idle cash earns T-bills, no borrowing |
| Holdout | **Time holdout (2020 onward) on the 5 core assets + full history of 5 unseen assets** |
| Confidence | **Deflated Sharpe probability ≥ 0.95**, plus holdout, rolling-window and bootstrap checks |
| Distinctness | **Different mechanism category AND excess-return correlation < 0.5** |
| Costs | **0.1% per trade** as base. The strategy must **still win at 0.25%**. Taxes ignored |
| Runtime | **This long-running Claude Code session**, via `/loop`. All state lives in the repo |
| Idea sources | **Literature first.** The agent's own ideas are allowed if pre-registered with a mechanism |
| Prior work | **Counted as trials. Exact prior rules are closed** (§7.2) |
| Holdout opening cap | **No cap, but every opening counts as a trial** and is logged (§5.4) |
| Holdout pass (single-asset) | **Pooled 6 of 10**: 5 core assets over 2020+ plus 5 unseen assets |
| Deliverable | **Report + code + an execution playbook for each winner** |

---

## 3. Shared setup

### 3.1 Universe

- **Core assets (development and time holdout):** `^GSPC` (S&P 500), `GC=F` (gold), `SI=F` (silver), `BTC-USD`, `CL=F` (WTI oil).
- **Unseen assets (holdout only; never loaded during development):** `^NDX` (Nasdaq-100), `^N225` (Nikkei 225), `HG=F` (copper), `PL=F` (platinum), `ETH-USD`.

### 3.2 Engine (v3, daily resolution)

- Daily OHLC bars. For the portfolio calendar, use NYSE trading days. BTC and ETH use their own daily closes on those days.
- **Deposits:** $500 per asset (single-asset tests) or $2,500 (portfolio tests, $500 × 5), credited at the **last trading day's close each week**.
- **Decisions:** computed at each trading day's close, using only data available by that close.
- **Fills:** at the **next trading day's open**. Sells are processed first, then buys. Buys are capped by available cash, so cash never goes negative. No positions can go negative.
- **Cash interest:** `cash × (IRX/100) / 252` per trading day.
- **Fees:** 0.1% of notional per trade (base case) and 0.25% (stress case). The winner must pass both.
- **DCA benchmark:** each week's deposit is fully invested at the next open. The portfolio benchmark is **fixed-weight 5-asset DCA** ($500 into each asset every week, never rebalanced).
- **Implementation checks** (must pass before any results count; these carry over from v2 §11):
  1. The degenerate parameters of every strategy must reproduce DCA exactly.
  2. Cash never goes negative, and no position goes negative.
  3. **No-lookahead test:** randomly perturb all data after day `t`. Every order generated on or before day `t` must be unchanged.
  4. Macro and alternative data follow point-in-time rules: publication lags, and ALFRED vintages for any series that gets revised.

### 3.3 Metrics (per v2 §8)

- Build the **NAV series** exactly as in v2 §8.1, so deposits don't distort returns.
- **Final wealth** on identical deposits, **Sharpe** of weekly NAV returns (risk-free rate = IRX), Sortino, max drawdown, longest time underwater, CAGR, Calmar, average cash share, turnover and total fees.
- **Excess-return series:** strategy weekly NAV return minus DCA weekly NAV return. For single-asset strategies, take the equal-weight average of the 5 per-asset excess series (the **pooled excess series**). This is the series the Deflated Sharpe test runs on.

### 3.4 Complexity ceiling (a hard gate before any backtest)

A family is eligible only if all of these hold:
- Its rules fit on one page and can be computed from end-of-day data.
- It places at most one order per asset per trading day.
- It has at most 5 tunable parameters.
- All its data comes from free public sources the environment can reach.
- Its parameter grid has at most **36 configurations**, with one **primary configuration** declared before any testing.

---

## 4. Win rules (development data)

A family becomes a **finalist** only if **its primary configuration** meets every check below on development data.

### 4.1 Beats DCA
- **Single-asset:** beats DCA on final wealth AND Sharpe on **at least 3 of 5** core assets.
- **Portfolio:** beats fixed-weight 5-asset DCA on final wealth AND Sharpe.
- This must hold at **both 0.1% and 0.25%** fees.

### 4.2 Adjusted for number of trials
- **Deflated Sharpe Ratio** (Bailey & López de Prado, 2014) on the excess-return series must be **≥ 0.95**.
- `N` in the formula is the **effective number of trials so far**, as defined in §6.2.
- This probability is the loop's reported **"chance the result is real."** It is recomputed after every iteration, and it can only fall as `N` grows.

### 4.3 Robust across time and resamples
- **Rolling windows** (inside the development period, stepping 4 weeks): 3-year and 5-year windows for the S&P 500, gold, silver and oil, and 2-year windows for BTC. The strategy must beat DCA in **more than 60% of windows**, on wealth and on Sharpe separately.
- **Block bootstrap:** 500 histories built from 4-week blocks, both as-is and detrended. For portfolios, all assets share the same blocks. The strategy must beat DCA in **the majority of histories**, on wealth and on Sharpe.
- **Placebo** (for any strategy with a timing or regime signal): circular-shift the signal 500 times. The real result must be at or above the **95th percentile**.

### 4.4 Robust across parameters
- At least **2/3 of the family's pre-declared grid** must beat DCA on wealth and Sharpe (using the pooled excess series or the portfolio). This stops a single lucky setting from carrying the family.
- The grid is diagnostic only. **Only the primary configuration** can become a finalist. The loop never switches to a better-looking configuration after seeing results.
- Report the **probability of backtest overfitting** (Bailey et al., 2017, CSCV method) on the grid as a diagnostic.

### 4.5 Distinctness (between the 2 winners)
- **Mechanism categories** (each family declares exactly one):
  - Sizing / valuation
  - Trend / time-series momentum exit
  - Cross-asset rotation / relative strength
  - Rebalancing / allocation
  - Volatility targeting
  - Regime switch (macro / credit / sentiment)
  - Seasonality / execution timing
  - Carry / term structure
- The 2 winners must come from **different categories**, and the correlation of their weekly excess-return series must be **below 0.5**.

---

## 5. The holdout

### 5.1 What's sealed
- **Time holdout:** 2020-01-01 to the latest date, on the 5 core assets.
- **Asset holdout:** the full history of the 5 unseen assets (§3.1).
- **Development data:** each core asset's first date through 2019-12-31. BTC's development period (2014-09 to 2019-12) is short. That's a known weakness, and the report will call it out.

### 5.2 Enforced in code, not by good behavior
- `src/backtest/v3/data.py` exposes `load_dev()`. It refuses any date on or after 2020-01-01 and refuses every unseen ticker.
- Holdout data is reachable **only** through `open_holdout(family_id, prereg_hash)`. That function:
  1. Checks that a frozen pre-registration exists for the family and matches the hash.
  2. Adds a row to `state/holdout_log.csv` (timestamp, family, look number).
  3. Increments the trial counter.
  4. Returns the data.
- A code check makes the loop fail loudly if any other module reads holdout dates or tickers.

### 5.3 Holdout pass rule (the finalist becomes a winner)
- **Before opening:** freeze the finalist's exact rules and primary parameters in `families/<id>/prereg_final.md`. Commit it, and record its hash.
- **Single-asset:** beat DCA on wealth AND Sharpe in **at least 6 of 10** holdout tests (5 core assets over 2020+, plus 5 unseen assets, full history), at 0.1% fees. The strategy must also stay ahead of DCA on the pooled holdout result at 0.25%.
- **Portfolio:** beat fixed-weight DCA on wealth AND Sharpe on **both** of these: the core 5-asset portfolio over 2020+, and an unseen 5-asset portfolio (^NDX, ^N225, HG=F, PL=F, ETH-USD) over the full common history.
- **After passing:** recompute the Deflated Sharpe probability on development + holdout combined, using the updated `N`. It must still be ≥ 0.95.

### 5.4 Holdout discipline (important, since openings are unlimited and there are no approvals)
- A family that fails the holdout is **closed permanently**. The loop may not retune it, tweak it, or bring it back under a new name.
- Holdout results must **never** feed back into designing a new family. A new family's pre-registration must cite only literature and development results.
- Every opening increments `N`, and the holdout log is included in every report.

### 5.5 Final re-check
When the loop stops, recompute every winner's Deflated Sharpe probability at the **final** `N`. Report two numbers for each winner: the probability when it was found and the probability at the final `N`. If a winner falls below 0.95 at the final `N`, the report flags it as **"downgraded by later searching."**

---

## 6. Trial accounting

This is how the loop "adjusts the chance of success for how many times it has looked at the data."

### 6.1 What counts
- **One trial** = one distinct configuration (rule + parameters) evaluated on a data split. A grid of 36 configurations is 36 trials.
- **Holdout openings** count as trials too.
- Rerunning an identical configuration after a bug fix is **not** a new trial. Log it in `state/bugfix_log.md`.
- A **family** = one idea + its pre-declared grid. The 60-family budget counts **new** families only.

### 6.2 Effective `N` for the Deflated Sharpe calculation
- Keep every trial's weekly excess-return series in `state/trials/`.
- `N_eff` = the number of clusters when all trial excess-return series are grouped by average-linkage hierarchical clustering on the distance `sqrt(0.5 × (1 − ρ))`. Configurations with **ρ ≥ 0.5** land in the same cluster. This follows López de Prado's method for estimating the effective number of trials.
- `V[SR]` = the variance of Sharpe ratios across cluster representatives.
- Report both the **N_eff-based** probability (used for decisions) and a **raw-N** probability (a conservative reference).

### 6.3 Seeding from prior work
- On its first run, the loop **seeds** the trial store from every configuration already logged in `reports/grid_metrics.csv` and `reports/v2/*.csv`. That's about 230 rows; the exact count is computed at seed time. Where possible it rebuilds their excess-return series using the v3 engine on development data.
- It records the seed count in `state/trial_counter.json` as `"seed"`, separate from `"new"`.

---

## 7. Where ideas come from

### 7.1 Process
1. Search the literature first: SSRN, arXiv q-fin, journals and reputable practitioner research. Use WebSearch/WebFetch.
2. The agent may propose its own ideas. Each needs a written **economic mechanism** ("why would this work, and who is on the other side?") and must be pre-registered before any backtest.
3. Ideas found by looking at the data are **not allowed**.
4. Every family gets `families/<id>/prereg.md`, **committed before its first backtest**. It records: source, mechanism, category, exact rules, data inputs, parameters (≤5), grid (≤36), the primary configuration, and the expected sign of the effect.

### 7.2 Closed families (tested in v1–v2.1; exact rules may not be re-tested)
- v1 buy-the-dip / trim-the-spike: Signal A (ATR shock) and Signal B (trend stretch), with the percentile grid.
- v2 SmartDCA (rho × m_max × sweep grid).
- v2 ADCA B1 (macro) and ADCA B2 (asset-native).
- v2 rebalanced portfolios C1, C2 and C3, including the 5-asset rebalancing-frequency sweep.
- v2.1 Strategy D rate-regime switch: R1, R2a, R2b, R2b-inv, R2c, R3, R4, Combo and Control.

A new family may build on one of these only if it is **materially different**: a different signal definition or a different mechanism. Its pre-registration must say why it isn't a re-test.

### 7.3 Seed research queue (the loop adds more as it goes)
| # | Idea | Category | Key source |
|---|---|---|---|
| 1 | 10-month / 200-day moving-average exit to T-bills; buy DCA while above the average, park deposits in cash while below | Trend exit | Faber (2007) |
| 2 | Dual momentum rotation across the 5 assets + T-bills | Rotation | Antonacci (2014) |
| 3 | Volatility-managed sizing (buy size ∝ 1/realized variance) | Vol targeting | Moreira & Muir (2017); Harvey et al. (2018) |
| 4 | Value averaging (target-path contributions), scored on wealth, not IRR | Sizing | Edleson (1991); Hayley's critique |
| 5 | Time-series momentum sizing: scale buys by the sign of the 12-month return | Trend | Moskowitz, Ooi & Pedersen (2012) |
| 6 | Turn-of-month deposit timing (S&P 500) | Seasonality | Ariel (1987); Lakonishok & Smidt (1988) |
| 7 | Day-of-week deposit timing (BTC weekend effect) | Seasonality | Crypto calendar-effect literature |
| 8 | CAPE / earnings-yield valuation sizing (S&P 500) | Sizing / valuation | Shiller; Asness et al. |
| 9 | BTC on-chain valuation sizing (MVRV, realized price) | Sizing / valuation | Glassnode / CoinMetrics research |
| 10 | Gold/silver ratio rotation | Rotation | Relative-value commodity literature |
| 11 | Credit-stress risk-off filter (BAA−AAA spread, NFCI) | Regime | Gilchrist & Zakrajšek (2012) |
| 12 | Commodity term-structure carry (backwardation tilt), if free curve data exists | Carry | Koijen et al. (2018) |
| 13 | Momentum-tilted rebalancing (rebalance toward trend winners) | Rebalancing | Asness, Moskowitz & Pedersen (2013) |
| 14 | Drawdown-from-high reserve deployment (a different reference point than SmartDCA's moving average) | Sizing | Practitioner literature; must justify why it isn't a re-test |

---

## 8. The loop (one iteration = one family)

1. **Load state:** `state/ledger.csv`, `state/trial_counter.json`, `state/holdout_log.csv`, `state/research_queue.md`, `state/winners.json`. Check the stop conditions.
2. **Research:** take the next idea from the queue. If fewer than 5 ideas remain, research more and add them, each with a source, mechanism and category.
3. **Gate:** check the complexity ceiling (§3.4), the closed-family rule (§7.2), and data reachability. If a data source is blocked, notify (§9.3) and move to the next idea.
4. **Pre-register:** write `families/<id>/prereg.md` and commit it **before** any backtest.
5. **Implement:** code in `src/backtest/v3/strategies/<id>.py`, then run the §3.2 implementation checks.
6. **Develop:** run the full grid on development data only. Log every configuration's trial series. Update `N` and `N_eff`.
7. **Assess:** run every §4 check on the primary configuration. The verdict is one of **rejected**, **near-miss** (passes §4.1 but not §4.2–§4.4; logged but not promoted), or **finalist**.
8. **Holdout (finalists only):** freeze and commit `prereg_final.md`, open the holdout (§5.2), apply §5.3, and log the look. The result is **winner** or **closed**.
9. **Record:** add a ledger row, write `families/<id>/results.md`, commit, and **push** (so a container reset loses nothing).
10. **Notify:** only if the iteration hit a milestone (§9.3).
11. **Loop:** schedule the next iteration.

---

## 9. Runtime

### 9.1 Where it runs
- In **this Claude Code session**, using `/loop` in dynamic (self-paced) mode, one family per tick. Kick-off command:
  `/loop Run one iteration of research-loop-plan-v3.md §8, then schedule the next`
- Every iteration is self-contained and reads all its state from the repo. If the conversation context is compacted, or the container resets and the session resumes, nothing is lost.

### 9.2 Repo layout
```
research-loop-plan-v3.md          this charter
state/                            ledger.csv, trial_counter.json, holdout_log.csv,
                                  research_queue.md, winners.json, bugfix_log.md, trials/
families/<id>/                    prereg.md, prereg_final.md (finalists), results.md, figures/
src/backtest/v3/                  data.py (dev/holdout gate), engine.py (daily),
                                  metrics.py, dsr.py (Deflated Sharpe + N_eff), robustness.py,
                                  strategies/<id>.py
reports/v3/                       final_report.md, playbook_<winner>.md, figures/
```

### 9.3 Milestone notifications (the only times the loop contacts the owner)
Delivered as a chat message and a push notification:
- A family becomes a **finalist**, and the holdout is about to be opened.
- The **holdout result** for a finalist.
- A **winner is confirmed** (with its Deflated Sharpe probability at the current `N`).
- **Stopped**: 2 winners found, or the 60-family budget is used up.
- **Blocked**: a data source is unreachable, an implementation check fails and can't be fixed within the iteration, or the environment breaks.

---

## 10. Deliverables (written when the loop stops)

1. **`reports/v3/final_report.md`**, containing:
   - The full ledger of every family with its verdict.
   - Trial accounting: seed, new, holdout looks, `N_eff`, and how the bar changed over time.
   - The holdout log.
   - For each winner: results, robustness, and the Deflated Sharpe probability both when found and at the final `N`.
   - Near-misses, and an honest summary of what didn't work.
2. **Reusable code** under `src/backtest/v3/` that reruns everything on fresh data.
3. **`reports/v3/playbook_<winner>.md`** for each winner (one page):
   - The exact rules.
   - Which data to check, and where to get it.
   - When to act (day and time) and what order to place.
   - A worked example week.
   - What would invalidate the strategy (a kill-switch condition).
   - The expected behavior in drawdowns.

---

## 11. Defaults the loop sets itself (change any of these before kick-off)

- The unseen-asset list: ^NDX, ^N225, HG=F, PL=F, ETH-USD. ETH's history only starts in 2017.
- Development/holdout cutoff: **2019-12-31**.
- Grid cap: **36 configurations per family**. Bootstrap and placebo: **500 runs each**.
- The `N_eff` clustering threshold: **ρ ≥ 0.5**.
- Portfolio deposits: **$2,500/week**. Portfolio benchmark: **equal $500/asset fixed-weight DCA**.
- Prior families count toward `N`, but **not** toward the 60-new-family budget.

## 12. Risks and expectations

- **The bar starts high.** About 230 prior configurations are already in the trial count, and plain DCA has been hard to beat on both wealth and Sharpe. **Finding 0 or 1 winners is a realistic outcome**, and the loop is designed to report that honestly rather than loosen the rules.
- **BTC's development period is short** (about 5 years). Any BTC-dependent result should be read with caution.
- **Unlimited holdout openings with no approvals** is the weakest part of this design. It's protected by the code gate, the permanent-closure rule, trial counting, and the final re-check at the final `N`. The holdout log in every report makes any overuse visible.
- **Network access:** new data sources (on-chain, credit spreads, research sites) may be blocked by the environment's allowlist. The loop notifies the owner rather than silently dropping the idea.
- **A long-running session can end.** Pushing to git after every iteration keeps the loop resumable.
