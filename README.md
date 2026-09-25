# BTC / Gold / Silver Rule-Based Accumulation Backtest

Backtests a percentile-of-own-distribution buy/sell rule (for cost & risk
management, not trading for profit) against DCA, buy-and-hold, a buy-only
variant, and a band-rebalancing benchmark — on BTC, Gold, and Silver — using
live daily data from Yahoo Finance (`yfinance`).

Full design spec: [`btc-gold-silver-backtest-spec.md`](btc-gold-silver-backtest-spec.md).

**Results: [`reports/report.md`](reports/report.md)** (headline metrics grid,
grid heatmaps, and — for a p=5 deep dive on every asset/signal — buy/sell
charts, account-value charts, drawdown charts, and all three robustness
tests: random-timing Monte Carlo, block bootstrap, rolling windows).

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run_all.py
```

Data is fetched from Yahoo Finance on first run and cached in `data/*.csv`
(delete those files to refresh). Output lands in `reports/` (`grid_metrics.csv`,
`report.md`, `deep_dive.json`, `figures/*.png`).

## Layout

- `src/backtest/data.py` — fetch/cache daily OHLC from Yahoo Finance.
- `src/backtest/resample.py` — daily → weekly candles, weekly risk-free rate from `^IRX`.
- `src/backtest/indicators.py` — generic indicator → percentile-of-trailing-distribution
  signal engine (Signal A: shock/ATR; Signal B: trend-stretch/Mayer-Multiple-style).
- `src/backtest/engine.py` — the core weekly backtest (buys, sells, fees, cash-earns-rf,
  synthetic NAV for drawdown).
- `src/backtest/benchmarks.py` — DCA, buy-and-hold, buy-only, band-rebalancing.
- `src/backtest/metrics.py` — wealth/invested, XIRR, drawdown, vol, Sharpe/Sortino/Calmar,
  cost basis, signal-quality forward returns.
- `src/backtest/robustness.py` — random-timing Monte Carlo, block bootstrap
  (raw + de-trended), rolling windows.
- `src/backtest/report.py` — chart generation.
- `run_all.py` / `write_report.py` — orchestration + markdown report assembly.

## Headline finding

Selling 30% of holdings into "spike" signals during a strongly trending
asset (BTC especially) tends to cut off upside faster than it protects
against drawdown-for-drawdown's-sake — consistent with the time-series
momentum literature cited in the spec. See `reports/report.md` for the full
grid, robustness tests, and per-asset nuance (the rule does meaningfully cut
drawdown, at the cost of raw upside).
