# BTC / Gold / Silver Accumulation Backtests

Two generations of a research backtest on whether any rule-based variant on
weekly accumulation beats plain DCA for a long-term BTC/gold/silver investor,
using live data from Yahoo Finance (`yfinance`) and FRED.

## v2 — SmartDCA / ADCA / rebalanced portfolio (current)

Tests three strategies that stay fully invested and change *how much* or
*where* to buy, instead of *whether* to be in the market:

- **SmartDCA** — buy more when price is below its 52-week trend, less when above.
- **ADCA** — buy more in "expansion" market/macro regimes, less in "contraction."
- **Rebalanced BTC/gold/silver portfolio** — direct new money to the most
  underweight asset; rebalance on drift bands.

Spec: [`btc-gold-silver-backtest-spec-v2.md`](btc-gold-silver-backtest-spec-v2.md).
**Results: [`reports/v2/report.md`](reports/v2/report.md)** (full parameter
grids, implementation checks, and — per strategy family — account-value
charts, drawdown charts, rolling windows, block bootstrap, and placebo tests).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run_v2.py
```

Layout: `src/backtest/v2/data.py` (Yahoo + FRED fetch/cache, FRED publication-lag
handling), `engine.py` (single-asset weekly event loop: deposits, interest,
next-open fills, fees), `strategies.py` (SmartDCA, ADCA), `rebalance.py`
(multi-asset portfolio engine + C1/C2/C3 target weights), `metrics.py` (NAV
series, headline + diagnostic metrics), `robustness.py` (rolling windows,
block bootstrap, placebo shuffles), `checks.py` (spec §11 sanity checks),
`report.py` (charts). `run_v2.py` / `write_report_v2.py` orchestrate + write
the markdown report.

**Extra-asset check:** BTC's ~100x decade-long rise makes it an outlier for
SmartDCA/ADCA (a strategy that trims buys above trend loses out when the
trend basically never stops). [`reports/v2/report_extra_assets.md`](reports/v2/report_extra_assets.md)
reruns the identical SmartDCA/ADCA code on WTI crude oil (`CL=F`) and an
energy-sector ETF (`XLE`) — both range-bound, non-100x assets — via
`python run_v2_extra_assets.py`. There, unlike on BTC/gold/silver, SmartDCA
*does* beat plain DCA in most of the grid (~92% of combos on oil, ~67% on
the energy ETF), supporting the idea that the strategy's failure on v2's
three original assets was driven by their persistent uptrends, not a flaw
in the method itself.

## v1 — buy-the-dip / trim-the-spike (superseded)

Tested a percentile-ranked ATR-shock and trend-stretch buy/sell rule against
DCA, buy-and-hold, a buy-only variant, and a band-rebalancing benchmark.
Found it **underperformed plain DCA** on raw return (selling into strength
during a trending asset like BTC cuts off upside), while meaningfully cutting
drawdown — the diagnosis that motivated v2.

Spec: [`btc-gold-silver-backtest-spec.md`](btc-gold-silver-backtest-spec.md).
Results: [`reports/report.md`](reports/report.md). Run with `python run_all.py`.
