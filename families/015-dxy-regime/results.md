# Family 015 results: DXY (US Dollar Index) regime rotation

**Verdict: REJECTED.** The primary configuration fails sec 4.1 decisively:
it beats plain DCA on **0 of 5** core assets, on wealth AND Sharpe, at
either fee level. Unlike family 014's `near_high_mult=1.0` trap, this is
**not** a silent no-op -- the primary config's results genuinely differ
from DCA on every asset (it underperforms DCA on every asset, not
duplicates it), confirming the mechanism actually fired throughout the
backtest. Sec 4.4's grid diagnostic also fails completely (0/16 configs
reach the majority bar). DSR is effectively zero. Holdout was **not**
opened.

## Scoping recap (full reasoning in prereg.md)

Assessed as a **single-asset family** (sec 4.1's Single-asset line),
across all 5 core assets, category **Regime switch (macro / credit /
sentiment)** (chosen over "Cross-asset rotation / relative strength" --
see prereg.md's category-justification section: no capital ever rotates
between assets in this family, only a per-asset banking/deploy decision
driven by an external macro signal, structurally like family 011's
credit-stress filter). Signal: a confirmed US Dollar Index (`DX-Y.NYB`)
uptrend (close above its trailing SMA, held for `confirm_days` consecutive
trading days) marks a "dollar-strength" regime; deposits are banked as
cash during that regime and deployed with a capped catch-up lump
otherwise. The mechanism was applied with a **uniform sign and rule across
all 5 assets** despite the literature's ambiguity for SP500 (Jen 2001's
"dollar smile") -- a scoping decision made explicitly before backtesting,
per prereg.md, precisely so the eventual per-asset pattern could be read
honestly rather than tuned in advance.

**Pre-backtest non-degeneracy check (prereg.md, required by this
iteration's task instruction after family 014's oversight):** before any
backtest, the primary config's confirmed-regime frequency was computed
directly and found to be 26.0% of development-window trading days -- a
genuinely mixed, non-degenerate regime, ruling out a family-014-style
silent no-op by construction. The backtest results below confirm this:
the primary config's per-asset wealth and Sharpe figures are close to but
never numerically identical to DCA's (e.g. SP500 wealth/invested 85.193 vs
DCA's 85.277) -- the mechanism fired throughout, it simply underperformed.

## Implementation checks (sec 3.2, all passed)

| Check | Result |
|---|---|
| `enabled=False` bypass reproduces plain DCA bit-for-bit (units, cash) | PASS |
| Cash and positions never negative (DCA baseline) | PASS |
| Cash and positions never negative (primary config) | PASS |
| Cash and positions never negative (aggressive corner: `dxy_lookback=100, confirm_days=5, threshold_pct=1.0, bank_fraction=0.0` -- least time confirmed-strong) | PASS |
| Total capital deployed (cumulative buy_usd) never exceeds cumulative deposits + interest, within a 5% empirical bound (primary config) | PASS |
| Total capital deployed never exceeds cumulative deposits + interest (aggressive corner) | PASS |
| No-lookahead: perturbing all data after day `t` leaves every order on/before `t` unchanged (spot-checked at `t=6000` and `t=9500`) | PASS |
| Point-in-time macro data | N/A -- DXY is a daily market-price series (no publication lag / ALFRED vintage concern, unlike family 011's monthly/weekly macro releases); documented explicitly rather than skipped |
| Primary-config regime non-degeneracy (pre-registered check) | PASS -- 25.98% of dev-window days confirmed dollar-strength |

## Primary configuration: `dxy_lookback=200, confirm_days=10, threshold_pct=0.0, bank_fraction=0.0, max_lump_multiple=6.0`

### Sec 4.1 result (vs. plain per-asset DCA), 0.1% fee

| Asset | Strategy wealth/invested | DCA wealth/invested | Strategy Sharpe | DCA Sharpe | Beats DCA (both)? |
|---|---|---|---|---|---|
| SP500 | 85.193 | 85.277 | 0.15303 | 0.15310 | NO |
| GOLD | 2.158 | 2.231 | 0.48925 | 0.50492 | NO |
| SILVER | 1.616 | 1.687 | 0.30604 | 0.31968 | NO |
| BTC | 9.230 | 9.856 | 1.05525 | 1.06731 | NO |
| OIL | 1.169 | 1.180 | 0.21464 | 0.22782 | NO |

**Sec 4.1: FAIL**, 0/5 core assets, at both fee levels (0.25% fee results
are qualitatively identical -- see `_primary_per_asset.csv`). The primary
config underperforms DCA on both wealth AND Sharpe on every single core
asset, including the two assets (gold, oil) where the mechanism's
underlying "dollar strength hurts USD-denominated commodities" hypothesis
was expected to be strongest a priori.

### Grid diagnostic (sec 4.4)

**0 of 16 configurations (0.0%) reach the combined wealth-AND-Sharpe
majority bar** (>=3/5 assets) at 0.1% fees. The best-looking individual
metric anywhere in the grid is `beats_sharpe@0.1%=3/5` (reached by 4 of the
16 configs, all `threshold_pct=1.0` arms -- the stricter SMA-buffer
setting), but even those configs only reach `beats_wealth@0.1%=2/5`, so no
config anywhere in the grid clears the combined 3/5-on-both bar (see
`grid_results.csv` for the full per-config breakdown; the printed run log
above shows every config's wealth/Sharpe/both counts).

**Sec 4.4: FAIL** (need >=2/3 = 11/16; got 0/16).

CSCV probability of backtest overfitting (16-config grid, 8 splits, 70
combinations, SP500 weekly returns at 0.1% fee): **PBO = 0.557** -- notably
higher than family 014's PBO=0.0 or family 011's (both much lower); this
is consistent with sec 4.1's outright failure being genuinely noisy/close
to a coin-flip across the grid's variations (unlike family 014's clean
mechanical near_high_mult=1.0/0.75 split), rather than a single dominant
mechanism effect either confirming or refuting cleanly.

### Deflated Sharpe Ratio (sec 4.2)

- Raw weekly Sharpe of the primary config's pooled excess-return series
  (strategy weekly NAV return minus DCA weekly NAV return, averaged across
  the 5 assets): **-0.0445** (weekly, i.e. **-0.321 annualized**) --
  negative, consistent with the primary config underperforming DCA on
  every asset.
- `N` (raw trial count, whole-loop pool): **499** (196 seeded + 287 from
  families 001-014 + 16 new from this family's grid).
- `N_eff` (average-linkage clustering, rho>=0.5 threshold): **58** clusters
  (up from family 014's 56 -- this family's 16 grid configs add 2 new
  distinct clusters).
- **DSR (N_eff-based): ~1.4e-44** -- effectively zero. A negative raw
  Sharpe cannot clear the DSR's positive SR0 threshold (SR0=0.151 at this
  N_eff) under any reasonable trial-count adjustment.
- DSR (raw-N, conservative reference): ~9.7e-54, also effectively zero.

**Sec 4.2: FAIL**, decisively -- the excess-return series' negative mean
Sharpe rules out a DSR pass regardless of the trial-count adjustment.

### Robustness (sec 4.3)

**Not run.** Per the established precedent (families 006/007/008/011/013/
014: sec 4.3 is only attempted if sec 4.1 passes first), and sec 4.1 fails
outright (0/5, the same category of decisive failure as families 011's
and 014's), the rolling-window / block-bootstrap / placebo battery was
skipped.

## Verdict

**REJECTED.** Sec 4.1 fails at both fee levels (0/5 core assets). Sec
4.4's grid diagnostic fails completely (0/16, need >=11/16). DSR is
effectively zero (negative raw Sharpe). Holdout was **not** opened.

## Interpretation

The confirmed-DXY-uptrend banking mechanism, as tested, does not improve
on plain DCA for any of the 5 core assets over the development window --
including gold and oil, the two assets where the "dollar strength hurts
USD-denominated commodities" mechanism was expected a priori to be
strongest. A plausible read, consistent with the negative pooled excess
Sharpe and the grid's uniformly poor showing (no config anywhere in the
16-config grid clears the combined bar): banking deposits during a
confirmed, sustained DXY uptrend systematically misses some of the best
entry points during those very episodes -- dollar "super-cycles" like the
mid-1990s-2001 and 2014-2016 uptrends coincided with extended, low-
volatility periods for several of these assets (not exclusively acute
stress episodes the way family 011's credit-spread signal was designed to
target), so redirecting deposits away from those weeks removed
opportunistic buying rather than avoiding genuinely bad prices, and the
capped catch-up lump on the "calm" side did not make up the difference net
of the weeks skipped. This is consistent with, but does not confirm, the
prereg's own flagged risk that DXY trend regimes (multi-year currency
cycles) may be poorly matched in timescale/frequency to a weekly banking
mechanic tuned by families 006/007/011's much shorter-horizon calendar/
credit-spread signals. This does not rule out other DXY-based
constructions (a mean-reversion rather than trend-following DXY signal, a
shorter-horizon FX-momentum signal, or restricting the mechanism to only
gold/oil/silver rather than all 5 core assets) -- but those would be
materially different mechanisms requiring their own pre-registration, and
per sec 5.4/7.2's discipline this specific family (this exact rule and
grid) is now closed.

## Data reachability

No issues. `DX-Y.NYB` (ICE US Dollar Index) was confirmed directly
reachable via yfinance before this family's implementation step (14,151
daily rows, 1971-01-04 through the present), so the FRED substitute
(`DTWEXBGS`) considered in prereg.md was not needed. A new public helper,
`src.backtest.v3.data.fetch_yf_macro(ticker)`, was added to route this
fetch through `data.py`'s gate (refusing any core/unseen asset ticker),
keeping the raw-data-leak static check's coverage intact.
