"""Robustness tests (spec section 7): random-timing Monte Carlo, block-bootstrap
shuffled histories, and rolling windows. This is the heart of the project --
it answers 'is the rule adding value, or just riding the market's overall rise?'
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .engine import run_backtest
from .benchmarks import dca
from .metrics import summarize, max_drawdown


def random_timing_mc(
    weekly: pd.DataFrame,
    n_buys: int,
    n_sells: int,
    weekly_rf: pd.Series,
    n_sims: int = 500,
    seed: int = 42,
    fee: float = 0.001,
    buy_amount: float = 500.0,
    sell_frac: float = 0.30,
) -> pd.DataFrame:
    """Same number of buys/sells as the real strategy, placed on randomly chosen
    weeks, repeated n_sims times. Real prices are kept unchanged."""
    rng = np.random.default_rng(seed)
    n = len(weekly)
    eligible = np.arange(0, n - 1)  # signal at t needs a fill at t+1
    rows = []
    for _ in range(n_sims):
        buy_idx = rng.choice(eligible, size=min(n_buys, len(eligible)), replace=False) if n_buys > 0 else np.array([], dtype=int)
        sell_idx = rng.choice(eligible, size=min(n_sells, len(eligible)), replace=False) if n_sells > 0 else np.array([], dtype=int)
        buy_signal = pd.Series(False, index=weekly.index)
        sell_signal = pd.Series(False, index=weekly.index)
        if len(buy_idx):
            buy_signal.iloc[buy_idx] = True
        if len(sell_idx):
            sell_signal.iloc[sell_idx] = True
        result = run_backtest(weekly, buy_signal, sell_signal, weekly_rf, fee=fee, buy_amount=buy_amount, sell_frac=sell_frac)
        s = summarize(result, weekly, weekly_rf, buy_amount=buy_amount)
        rows.append(s)
    return pd.DataFrame(rows)


def percentile_of_real(distribution: pd.Series, real_value: float) -> float:
    """What percentile the real strategy's stat falls at within the random
    distribution (0-100; higher = better if higher is better for that stat)."""
    vals = distribution.dropna().to_numpy()
    if len(vals) == 0 or real_value is None or np.isnan(real_value):
        return float("nan")
    return float(100.0 * np.sum(vals <= real_value) / len(vals))


def _synthetic_weekly_from_returns(weekly: pd.DataFrame, log_returns: np.ndarray) -> pd.DataFrame:
    """Rebuild a synthetic weekly OHLC frame from a log-return path, starting at
    the real series' starting close. Intraweek range is approximated as
    Open == previous Close (no gap), High/Low bracket Open/Close using the
    same average weekly range-to-body ratio as the real series (documented
    simplification -- block bootstrap only needs a directionally faithful
    price path, not real intraweek ranges)."""
    start_price = float(weekly["Close"].iloc[0])
    closes = start_price * np.exp(np.cumsum(log_returns))
    closes = np.concatenate([[start_price], closes])
    opens = np.concatenate([[start_price], closes[:-1]])
    body = np.abs(closes - opens)
    real_range = (weekly["High"] - weekly["Low"]).to_numpy()
    real_body = (weekly["Close"] - weekly["Open"]).abs().to_numpy()
    ratio = np.nanmedian(real_range[real_body > 1e-9] / real_body[real_body > 1e-9]) if np.any(real_body > 1e-9) else 1.5
    pad = body * max(ratio - 1.0, 0.1) / 2.0
    highs = np.maximum(opens, closes) + pad
    lows = np.maximum(np.minimum(opens, closes) - pad, 1e-6)
    idx = weekly.index[: len(closes)]
    return pd.DataFrame({"Open": opens, "High": highs, "Low": lows, "Close": closes}, index=idx)


def block_bootstrap_paths(
    weekly: pd.DataFrame, n_sims: int = 500, block_weeks: int = 4, seed: int = 7, detrend: bool = False
) -> list[pd.DataFrame]:
    """Resample block_weeks-long chunks of weekly log returns WITH replacement
    to build n_sims alternate price histories of the same length. Order
    within a block is preserved; blocks are drawn with replacement so some
    months can repeat or vanish (spec's corrected implementation note --
    shuffling order alone doesn't work since compounded return is order-
    independent)."""
    rng = np.random.default_rng(seed)
    log_ret = np.log(weekly["Close"]).diff().dropna().to_numpy()
    n = len(log_ret)
    mean_ret = log_ret.mean()
    n_blocks_needed = int(np.ceil(n / block_weeks))
    block_starts_pool = np.arange(0, n - block_weeks + 1)

    paths = []
    for _ in range(n_sims):
        chosen_starts = rng.choice(block_starts_pool, size=n_blocks_needed, replace=True)
        blocks = [log_ret[s : s + block_weeks] for s in chosen_starts]
        path = np.concatenate(blocks)[:n]
        if detrend:
            path = path - mean_ret
        paths.append(_synthetic_weekly_from_returns(weekly, path))
    return paths


def block_bootstrap_test(
    weekly: pd.DataFrame,
    signal_fn,
    p: float,
    weekly_rf: pd.Series,
    n_sims: int = 300,
    block_weeks: int = 4,
    detrend: bool = False,
    fee: float = 0.001,
    buy_amount: float = 500.0,
    sell_frac: float = 0.30,
) -> pd.DataFrame:
    """Run the strategy vs DCA on each bootstrapped alternate history and
    report which one wins on return / drawdown / Sharpe."""
    from .indicators import percentile_signal_to_trades

    paths = block_bootstrap_paths(weekly, n_sims=n_sims, block_weeks=block_weeks, seed=123, detrend=detrend)
    rows = []
    for synth in paths:
        rf = weekly_rf.reindex(synth.index).ffill().fillna(0.0)
        indicator = signal_fn(synth)
        buy, sell = percentile_signal_to_trades(indicator, p)
        strat = run_backtest(synth, buy, sell, rf, fee=fee, buy_amount=buy_amount, sell_frac=sell_frac)
        s = summarize(strat, synth, rf, buy_amount=buy_amount)
        d = dca(synth, s["total_invested"], rf)
        d_wealth = float(d["total_value"].iloc[-1])
        d_nav_dd, _ = max_drawdown(d["nav"])
        d_sharpe = float(
            (d["nav"].pct_change().dropna() - rf.reindex(d["nav"].pct_change().dropna().index).fillna(0)).mean()
            / (d["nav"].pct_change().dropna().std() or np.nan) * np.sqrt(52)
        )
        rows.append({
            "strat_wealth_over_invested": s["wealth_over_invested"],
            "dca_wealth_over_invested": d_wealth / s["total_invested"] if s["total_invested"] else np.nan,
            "strat_max_dd": s["max_drawdown"],
            "dca_max_dd": d_nav_dd,
            "strat_sharpe": s["sharpe"],
            "dca_sharpe": d_sharpe,
        })
    return pd.DataFrame(rows)


def rolling_windows_test(
    weekly: pd.DataFrame,
    signal_fn,
    p: float,
    weekly_rf: pd.Series,
    window_years: int,
    step_weeks: int = 13,
    min_signal_count: int = 5,
    fee: float = 0.001,
    buy_amount: float = 500.0,
    sell_frac: float = 0.30,
) -> pd.DataFrame:
    """Run the strategy vs DCA on every rolling window_years-long window,
    stepping step_weeks at a time."""
    from .indicators import percentile_signal_to_trades

    window_weeks = window_years * 52
    n = len(weekly)
    rows = []
    for start in range(0, n - window_weeks, step_weeks):
        end = start + window_weeks
        w = weekly.iloc[start:end]
        rf = weekly_rf.reindex(w.index).ffill().fillna(0.0)
        indicator = signal_fn(w)
        buy, sell = percentile_signal_to_trades(indicator, p)
        n_signals = int(buy.sum() + sell.sum())
        strat = run_backtest(w, buy, sell, rf, fee=fee, buy_amount=buy_amount, sell_frac=sell_frac)
        s = summarize(strat, w, rf, buy_amount=buy_amount)
        if s["total_invested"] <= 0:
            continue
        d = dca(w, s["total_invested"], rf)
        d_wealth = float(d["total_value"].iloc[-1])
        d_dd, _ = max_drawdown(d["nav"])
        d_ret = d["nav"].pct_change().dropna()
        d_rf = rf.reindex(d_ret.index).fillna(0.0)
        d_sharpe = float((d_ret - d_rf).mean() / (d_ret.std() or np.nan) * np.sqrt(52))
        rows.append({
            "window_start": w.index[0],
            "window_end": w.index[-1],
            "n_signals": n_signals,
            "low_signal_count": n_signals < min_signal_count,
            "strat_wealth_over_invested": s["wealth_over_invested"],
            "dca_wealth_over_invested": d_wealth / s["total_invested"],
            "strat_max_dd": s["max_drawdown"],
            "dca_max_dd": d_dd,
            "strat_sharpe": s["sharpe"],
            "dca_sharpe": d_sharpe,
            "strat_beats_dca_return": s["wealth_over_invested"] > (d_wealth / s["total_invested"]),
            "strat_beats_dca_dd": s["max_drawdown"] > d_dd,  # less negative = better
            "strat_beats_dca_sharpe": (s["sharpe"] or -np.inf) > (d_sharpe if not np.isnan(d_sharpe) else -np.inf),
        })
    return pd.DataFrame(rows)
