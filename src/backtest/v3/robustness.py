"""Rolling windows, block bootstrap, and placebo circular-shift (plan sec 4.3),
adapted from src/backtest/v2/robustness.py for the v3 daily engine + weekly
metrics convention.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import engine as eng
from . import metrics as met


def rolling_windows(
    daily: pd.DataFrame, daily_rf: pd.Series, weekly_deposit: float,
    strategy_decide_builder, benchmark_decide_builder,
    window_years: int, step_days: int = 20, fee: float = 0.001,
) -> pd.DataFrame:
    window_days = int(window_years * 252)
    n = len(daily)
    rows = []
    for start in range(0, max(n - window_days, 0), step_days):
        w = daily.iloc[start: start + window_days]
        if len(w) < window_days * 0.9:
            continue
        rf = daily_rf.reindex(w.index).ffill().fillna(0.0)
        s_decide = strategy_decide_builder(w)
        b_decide = benchmark_decide_builder(w)
        s_res = eng.run_single_asset(w, weekly_deposit, rf, s_decide, fee=fee).to_frame()
        b_res = eng.run_single_asset(w, weekly_deposit, rf, b_decide, fee=fee).to_frame()
        s = met.summarize(s_res, rf, w["Close"].iloc[-1])
        b = met.summarize(b_res, rf, w["Close"].iloc[-1])
        rows.append({
            "window_start": w.index[0], "window_end": w.index[-1],
            "strat_wealth_over_invested": s["wealth_over_invested"],
            "bench_wealth_over_invested": b["wealth_over_invested"],
            "strat_sharpe": s["sharpe"], "bench_sharpe": b["sharpe"],
            "beats_wealth": s["wealth_over_invested"] > b["wealth_over_invested"],
            "beats_sharpe": (s["sharpe"] if not np.isnan(s["sharpe"]) else -np.inf)
                            > (b["sharpe"] if not np.isnan(b["sharpe"]) else -np.inf),
        })
    return pd.DataFrame(rows)


def _synthetic_daily_from_returns(daily: pd.DataFrame, log_returns: np.ndarray) -> pd.DataFrame:
    start_price = float(daily["Close"].iloc[0])
    closes = start_price * np.exp(np.cumsum(log_returns))
    closes = np.concatenate([[start_price], closes])
    opens = np.concatenate([[start_price], closes[:-1]])
    body = np.abs(closes - opens)
    real_range = (daily["High"] - daily["Low"]).to_numpy()
    real_body = (daily["Close"] - daily["Open"]).abs().to_numpy()
    ratio = np.nanmedian(real_range[real_body > 1e-9] / real_body[real_body > 1e-9]) if np.any(real_body > 1e-9) else 1.5
    pad = body * max(ratio - 1.0, 0.1) / 2.0
    highs = np.maximum(opens, closes) + pad
    lows = np.maximum(np.minimum(opens, closes) - pad, 1e-6)
    idx = daily.index[: len(closes)]
    return pd.DataFrame({"Open": opens, "High": highs, "Low": lows, "Close": closes}, index=idx)


def block_bootstrap(
    daily: pd.DataFrame, daily_rf: pd.Series, weekly_deposit: float,
    strategy_decide_builder, benchmark_decide_builder,
    n_sims: int = 500, block_weeks: int = 4, detrend: bool = False, seed: int = 11, fee: float = 0.001,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    block_days = block_weeks * 5
    log_ret = np.log(daily["Close"]).diff().dropna().to_numpy()
    n = len(log_ret)
    mean_ret = log_ret.mean()
    n_blocks_needed = int(np.ceil(n / block_days))
    starts_pool = np.arange(0, max(n - block_days + 1, 1))
    rows = []
    for _ in range(n_sims):
        starts = rng.choice(starts_pool, size=n_blocks_needed, replace=True)
        blocks = [log_ret[s: s + block_days] for s in starts]
        path = np.concatenate(blocks)[:n]
        if detrend:
            path = path - mean_ret
        synth = _synthetic_daily_from_returns(daily, path)
        rf = daily_rf.reindex(synth.index).ffill().fillna(0.0)
        s_decide = strategy_decide_builder(synth)
        b_decide = benchmark_decide_builder(synth)
        s_res = eng.run_single_asset(synth, weekly_deposit, rf, s_decide, fee=fee).to_frame()
        b_res = eng.run_single_asset(synth, weekly_deposit, rf, b_decide, fee=fee).to_frame()
        s = met.summarize(s_res, rf, synth["Close"].iloc[-1])
        b = met.summarize(b_res, rf, synth["Close"].iloc[-1])
        rows.append({
            "strat_wealth_over_invested": s["wealth_over_invested"],
            "bench_wealth_over_invested": b["wealth_over_invested"],
            "strat_sharpe": s["sharpe"], "bench_sharpe": b["sharpe"],
        })
    return pd.DataFrame(rows)


def placebo_circular_shift(
    daily: pd.DataFrame, daily_rf: pd.Series, weekly_deposit: float,
    signal_raw: np.ndarray, strategy_decide_from_signal, benchmark_decide,
    real_wealth_over_invested: float, real_sharpe: float,
    n_sims: int = 500, seed: int = 5, fee: float = 0.001,
) -> tuple[pd.DataFrame, float, float]:
    """Circular-shift a strategy's raw timing signal (e.g. price-vs-SMA distance)
    n_sims times and rerun. strategy_decide_from_signal(shifted_signal) -> decide fn."""
    rng = np.random.default_rng(seed)
    n = len(signal_raw)
    rows = []
    for _ in range(n_sims):
        shift = int(rng.integers(1, n - 1))
        shifted = np.roll(signal_raw, shift)
        decide = strategy_decide_from_signal(shifted)
        res = eng.run_single_asset(daily, weekly_deposit, daily_rf, decide, fee=fee).to_frame()
        s = met.summarize(res, daily_rf, daily["Close"].iloc[-1])
        rows.append({"wealth_over_invested": s["wealth_over_invested"], "sharpe": s["sharpe"]})
    df = pd.DataFrame(rows)
    pctile_wealth = float(100.0 * (df["wealth_over_invested"] <= real_wealth_over_invested).mean())
    pctile_sharpe = float(100.0 * (df["sharpe"].dropna() <= real_sharpe).mean())
    return df, pctile_wealth, pctile_sharpe
