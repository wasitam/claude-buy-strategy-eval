# BTC / Gold / Silver Accumulation Backtests

Three generations of a research backtest on whether any rule-based variant on
weekly accumulation beats plain DCA for a long-term BTC/gold/silver investor,
using live data from Yahoo Finance (`yfinance`) and FRED.

## v3 — autonomous research loop (planned)

[`research-loop-plan-v3.md`](research-loop-plan-v3.md) is the charter for an
autonomous loop. It researches, pre-registers and tests new long-term DCA
strategy families until it finds 2 that beat DCA on both wealth and Sharpe,
or until it has tested 60 families. It keeps an honest count of every look at
the data (a Deflated Sharpe penalty over roughly 230 prior configurations,
plus every new one) and uses a code-enforced sealed holdout: 2020+ data and 5
assets never used in development.

## v2.1 — Strategy D: rate-regime switch

Tests whether **switching to SmartDCA during monetary tightening, and plain
DCA otherwise**, beats either strategy alone — motivated directly by v2's
finding that SmartDCA only wins on gold/silver once the trend is stripped
out (detrended bootstrap: 64–70%), and specifically loses through the recent
gold/silver rally. 8 rate-regime signals (Fed-funds direction, 2-year yield
trend, yield-curve flattening/inversion, real-yield trend, Fed dot plot) plus
a combined vote and a price-only control, tested on gold, silver, BTC, oil,
and the S&P 500.

Spec: [`btc-gold-silver-backtest-spec-v2.1.md`](btc-gold-silver-backtest-spec-v2.1.md).
**Results: [`reports/v2/report_regime_switch.md`](reports/v2/report_regime_switch.md)**.
Run with `python run_v2_regime_switch.py`.

**Result: a clean negative.** On the spec's own primary gold+silver
2001–2023 sample, every single signal lands within rounding of plain DCA —
none pass the spec's 4-part win condition, none clear the placebo test even
before the multiple-testing correction, and the regime-timeline chart shows
why: gold rallied hard right through the whole 2022–2026 "tightening" window,
exactly the failure mode the spec's own risk section flagged in advance
(gold's post-2022 link to real rates weakening, widely attributed to central
bank buying). New: `src/backtest/v2/regimes.py` (point-in-time signal
construction, including real ALFRED dot-plot vintages) and `strategy_d.py`
(the switching logic).

## v2 — SmartDCA / ADCA / rebalanced portfolio

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
reruns the identical SmartDCA/ADCA code on WTI crude oil (`CL=F`), an
energy-sector ETF (`XLE`), and the S&P 500 (`^GSPC`) — via
`python run_v2_extra_assets.py`. There's a clean gradient: SmartDCA beats
plain DCA in ~92% of the grid on oil (no persistent trend), ~67% on the
energy ETF, exactly 50% on the S&P 500 (a real but much milder uptrend than
BTC), and 0% on BTC/gold/silver — supporting the idea that the strategy's
failure on v2's three original assets tracks how strong/persistent each
asset's trend is, not a flaw in the method itself.

**How often to rebalance:** [`reports/v2/report_five_asset_rebalance.md`](reports/v2/report_five_asset_rebalance.md)
extends Strategy C's portfolio engine from 3 to 5 assets (S&P 500, gold,
silver, BTC, oil) and sweeps 9 rebalancing schedules — from tight 2pp/10%
drift bands to a full year between rebalances — via
`python run_v2_five_asset_rebalance.py`. Headline: rebalancing at all beats
never rebalancing by a wide margin on Sharpe (~1.2 vs ~0.86) and drawdown
(~-33% vs ~-60%), but frequency barely matters *within* a sensible range —
**quarterly-to-semiannual (or, equivalently, medium-width 10/50 bands) sits
at the sweet spot**: monthly rebalancing or tight bands roughly double the
number of trades and triple the fee drag for no better (sometimes worse)
risk-adjusted return, while annual rebalancing starts to let drawdowns creep
back up as weights drift too far between corrections.

## v1 — buy-the-dip / trim-the-spike (superseded)

Tested a percentile-ranked ATR-shock and trend-stretch buy/sell rule against
DCA, buy-and-hold, a buy-only variant, and a band-rebalancing benchmark.
Found it **underperformed plain DCA** on raw return (selling into strength
during a trending asset like BTC cuts off upside), while meaningfully cutting
drawdown — the diagnosis that motivated v2.

Spec: [`btc-gold-silver-backtest-spec.md`](btc-gold-silver-backtest-spec.md).
Results: [`reports/report.md`](reports/report.md). Run with `python run_all.py`.
