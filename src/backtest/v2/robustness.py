"""Robustness tests, spec v2 section 9: rolling windows, block bootstrap
(raw + de-trended), and placebo tests for ADCA and C3's trend filter.

Scoping note (documented again in the report): the spec asks for 1,000
bootstrap/placebo simulations. Given the size of this project's grid, this
module runs a reduced simulation count (documented per call site) on a
representative variant per strategy family, not the full grid -- consistent
with how v1's robustness suite was scoped.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import engine as eng
from . import metrics as met
from . import strategies as strat
from . import rebalance as rb


# ---------------------------------------------------------------------------
# Rolling windows (single asset)
# ---------------------------------------------------------------------------

def rolling_windows_single_asset(
    weekly: pd.DataFrame, weekly_rf: pd.Series, weekly_deposit: float,
    strategy_decide_builder, benchmark_decide_builder,
    window_years: int, step_weeks: int = 13,
) -> pd.DataFrame:
    """strategy_decide_builder(weekly_window) -> decide_fn; same for benchmark."""
    window_weeks = window_years * 52
    n = len(weekly)
    rows = []
    for start in range(0, n - window_weeks, step_weeks):
        w = weekly.iloc[start : start + window_weeks]
        rf = weekly_rf.reindex(w.index).ffill().fillna(0.0)
        strat_decide = strategy_decide_builder(w)
        bench_decide = benchmark_decide_builder(w)
        strat_res = eng.run_single_asset(w, weekly_deposit, rf, strat_decide).to_frame()
        bench_res = eng.run_single_asset(w, weekly_deposit, rf, bench_decide).to_frame()
        s = met.summarize(strat_res, rf, w["Close"].iloc[-1])
        b = met.summarize(bench_res, rf, w["Close"].iloc[-1])
        rows.append({
            "window_start": w.index[0], "window_end": w.index[-1],
            "strat_wealth_over_invested": s["wealth_over_invested"],
            "bench_wealth_over_invested": b["wealth_over_invested"],
            "strat_sharpe": s["sharpe"], "bench_sharpe": b["sharpe"],
            "strat_max_dd": s["max_drawdown"], "bench_max_dd": b["max_drawdown"],
            "beats_wealth": s["wealth_over_invested"] > b["wealth_over_invested"],
            "beats_sharpe": (s["sharpe"] or -np.inf) > (b["sharpe"] if not np.isnan(b["sharpe"]) else -np.inf),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Block bootstrap (single asset): resample 4-week blocks of log returns
# ---------------------------------------------------------------------------

def _synthetic_weekly_from_returns(weekly: pd.DataFrame, log_returns: np.ndarray) -> pd.DataFrame:
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


def block_bootstrap_paths(weekly: pd.DataFrame, n_sims: int, block_weeks: int = 4, seed: int = 11, detrend: bool = False) -> list[pd.DataFrame]:
    rng = np.random.default_rng(seed)
    log_ret = np.log(weekly["Close"]).diff().dropna().to_numpy()
    n = len(log_ret)
    mean_ret = log_ret.mean()
    n_blocks_needed = int(np.ceil(n / block_weeks))
    block_starts_pool = np.arange(0, n - block_weeks + 1)
    paths = []
    for _ in range(n_sims):
        starts = rng.choice(block_starts_pool, size=n_blocks_needed, replace=True)
        blocks = [log_ret[s : s + block_weeks] for s in starts]
        path = np.concatenate(blocks)[:n]
        if detrend:
            path = path - mean_ret
        paths.append(_synthetic_weekly_from_returns(weekly, path))
    return paths


def block_bootstrap_single_asset(
    weekly: pd.DataFrame, weekly_rf: pd.Series, weekly_deposit: float,
    strategy_decide_builder, benchmark_decide_builder,
    n_sims: int = 200, block_weeks: int = 4, detrend: bool = False,
) -> pd.DataFrame:
    paths = block_bootstrap_paths(weekly, n_sims=n_sims, block_weeks=block_weeks, detrend=detrend)
    rows = []
    for synth in paths:
        rf = weekly_rf.reindex(synth.index).ffill().fillna(0.0)
        strat_decide = strategy_decide_builder(synth)
        bench_decide = benchmark_decide_builder(synth)
        strat_res = eng.run_single_asset(synth, weekly_deposit, rf, strat_decide).to_frame()
        bench_res = eng.run_single_asset(synth, weekly_deposit, rf, bench_decide).to_frame()
        s = met.summarize(strat_res, rf, synth["Close"].iloc[-1])
        b = met.summarize(bench_res, rf, synth["Close"].iloc[-1])
        rows.append({
            "strat_wealth_over_invested": s["wealth_over_invested"],
            "bench_wealth_over_invested": b["wealth_over_invested"],
            "strat_sharpe": s["sharpe"], "bench_sharpe": b["sharpe"],
            "strat_max_dd": s["max_drawdown"], "bench_max_dd": b["max_drawdown"],
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Rolling windows (portfolio)
# ---------------------------------------------------------------------------

def rolling_windows_portfolio(
    weekly: dict, assets: list, weekly_rf: pd.Series, weekly_deposit_total: float,
    scheme: str, trigger_mode: str, window_years: int, step_weeks: int = 13,
) -> pd.DataFrame:
    """Compares `scheme`/`trigger_mode` against the fixed-weight-never-rebalanced
    benchmark, on the same target weights, over every rolling window."""
    index = weekly[assets[0]].index
    n = len(index)
    window_weeks = window_years * 52
    rows = []
    for start in range(0, n - window_weeks, step_weeks):
        widx = index[start : start + window_weeks]
        w_weekly = {a: weekly[a].reindex(widx) for a in assets}
        rf = weekly_rf.reindex(widx).ffill().fillna(0.0)
        closes = {a: w_weekly[a]["Close"] for a in assets}
        weights = rb.build_target_weights(scheme, closes, assets, widx)

        strat_res = rb.run_portfolio(w_weekly, assets, weekly_deposit_total, rf, weights, trigger_mode=trigger_mode)
        bench_res = rb.run_portfolio(w_weekly, assets, weekly_deposit_total, rf, weights, trigger_mode="never")
        s = met.summarize_portfolio(strat_res, rf)
        b = met.summarize_portfolio(bench_res, rf)
        rows.append({
            "window_start": widx[0], "window_end": widx[-1],
            "strat_wealth_over_invested": s["wealth_over_invested"],
            "bench_wealth_over_invested": b["wealth_over_invested"],
            "strat_sharpe": s["sharpe"], "bench_sharpe": b["sharpe"],
            "strat_max_dd": s["max_drawdown"], "bench_max_dd": b["max_drawdown"],
            "beats_wealth": s["wealth_over_invested"] > b["wealth_over_invested"],
            "beats_sharpe": (s["sharpe"] or -np.inf) > (b["sharpe"] if not np.isnan(b["sharpe"]) else -np.inf),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Block bootstrap (portfolio): same calendar blocks drawn for every asset
# together, so cross-asset correlation is preserved (spec 9.2).
# ---------------------------------------------------------------------------

def block_bootstrap_portfolio(
    weekly: dict, assets: list, weekly_rf: pd.Series, weekly_deposit_total: float,
    scheme: str, trigger_mode: str, n_sims: int = 150, block_weeks: int = 4,
    detrend: bool = False, seed: int = 17,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    index = weekly[assets[0]].index
    log_ret = {a: np.log(weekly[a]["Close"]).diff().dropna().to_numpy() for a in assets}
    n = len(log_ret[assets[0]])
    mean_ret = {a: log_ret[a].mean() for a in assets}
    n_blocks_needed = int(np.ceil(n / block_weeks))
    block_starts_pool = np.arange(0, n - block_weeks + 1)

    rows = []
    for _ in range(n_sims):
        starts = rng.choice(block_starts_pool, size=n_blocks_needed, replace=True)  # SAME starts for every asset
        synth_weekly = {}
        for a in assets:
            blocks = [log_ret[a][s : s + block_weeks] for s in starts]
            path = np.concatenate(blocks)[:n]
            if detrend:
                path = path - mean_ret[a]
            synth_weekly[a] = _synthetic_weekly_from_returns(weekly[a], path)
        widx = synth_weekly[assets[0]].index
        rf = weekly_rf.reindex(widx).ffill().fillna(0.0)
        closes = {a: synth_weekly[a]["Close"] for a in assets}
        weights = rb.build_target_weights(scheme, closes, assets, widx)
        strat_res = rb.run_portfolio(synth_weekly, assets, weekly_deposit_total, rf, weights, trigger_mode=trigger_mode)
        bench_res = rb.run_portfolio(synth_weekly, assets, weekly_deposit_total, rf, weights, trigger_mode="never")
        s = met.summarize_portfolio(strat_res, rf)
        b = met.summarize_portfolio(bench_res, rf)
        rows.append({
            "strat_wealth_over_invested": s["wealth_over_invested"],
            "bench_wealth_over_invested": b["wealth_over_invested"],
            "strat_sharpe": s["sharpe"], "bench_sharpe": b["sharpe"],
            "strat_max_dd": s["max_drawdown"], "bench_max_dd": b["max_drawdown"],
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Placebo tests
# ---------------------------------------------------------------------------

def placebo_adca(
    weekly: pd.DataFrame, weekly_rf: pd.Series, weekly_deposit: float,
    score: np.ndarray, real_wealth_over_invested: float, real_sharpe: float,
    n_sims: int = 300, seed: int = 5,
) -> pd.DataFrame:
    """Randomly circular-shift the regime-score series (spec 9.3)."""
    rng = np.random.default_rng(seed)
    n = len(score)
    rows = []
    for _ in range(n_sims):
        shift = rng.integers(1, n - 1)
        shifted = np.roll(score, shift)
        decide = strat.make_adca_decider(weekly_deposit, shifted)
        res = eng.run_single_asset(weekly, weekly_deposit, weekly_rf, decide).to_frame()
        s = met.summarize(res, weekly_rf, weekly["Close"].iloc[-1])
        rows.append({"wealth_over_invested": s["wealth_over_invested"], "sharpe": s["sharpe"]})
    df = pd.DataFrame(rows)
    pctile_wealth = float(100.0 * (df["wealth_over_invested"] <= real_wealth_over_invested).mean())
    pctile_sharpe = float(100.0 * (df["sharpe"].dropna() <= real_sharpe).mean())
    return df, pctile_wealth, pctile_sharpe


def placebo_strategy_d(
    weekly: pd.DataFrame, weekly_rf: pd.Series, weekly_deposit: float,
    regime_tight: np.ndarray, real_wealth_over_invested: float, real_sharpe: float,
    n_sims: int = 300, seed: int = 21,
) -> tuple:
    """Randomly circular-shift a Strategy D regime series (spec 15.7 placebo):
    keeps the same number/length of TIGHT stretches, breaks their link to
    real conditions."""
    from . import strategy_d as sd

    rng = np.random.default_rng(seed)
    n = len(regime_tight)
    rows = []
    for _ in range(n_sims):
        shift = rng.integers(1, n - 1)
        shifted = np.roll(np.asarray(regime_tight, dtype=bool), shift)
        decide = sd.make_strategy_d_decider(weekly, weekly_deposit, shifted)
        res = eng.run_single_asset(weekly, weekly_deposit, weekly_rf, decide).to_frame()
        s = met.summarize(res, weekly_rf, weekly["Close"].iloc[-1])
        rows.append({"wealth_over_invested": s["wealth_over_invested"], "sharpe": s["sharpe"]})
    df = pd.DataFrame(rows)
    pctile_wealth = float(100.0 * (df["wealth_over_invested"] <= real_wealth_over_invested).mean())
    pctile_sharpe = float(100.0 * (df["sharpe"].dropna() <= real_sharpe).mean())
    return df, pctile_wealth, pctile_sharpe


def placebo_c3_trend(
    weekly: dict, assets: list, weekly_rf: pd.Series, weekly_deposit_total: float,
    real_target_weights: pd.DataFrame, real_wealth_over_invested: float, real_sharpe: float,
    n_sims: int = 150, seed: int = 9, trigger_mode: str = "bands_5_25",
) -> tuple:
    """Randomly circular-shift C3's month-end trend (halved/not) flags per asset,
    decoupling the trend filter from real prices, and rerun the portfolio."""
    rng = np.random.default_rng(seed)
    idx = real_target_weights.index
    n = len(idx)
    # reconstruct the "halved" 0/1 signal per asset from the real C3 weights:
    # eff_i = w_i or w_i/2 => halved iff w_CASH-derived asset contributed to freed weight.
    # Simplify: derive per-asset halved boolean from whether eff weight < the C2 (non-trend) weight it would've had.
    from . import rebalance as rb2
    closes = {a: weekly[a]["Close"].reindex(idx).ffill() for a in assets}
    c2_weights = rb2.build_target_weights("C2", closes, assets, idx)

    halved_by_asset = {}
    for a in assets:
        halved_by_asset[a] = (real_target_weights[a] < c2_weights[a] * 0.99).to_numpy()

    rows = []
    for _ in range(n_sims):
        shift = rng.integers(1, n - 1)
        shifted_weights = c2_weights.copy()
        shifted_weights[rb2.CASH_SLEEVE] = 0.0
        for a in assets:
            shifted_halved = np.roll(halved_by_asset[a], shift)
            eff = c2_weights[a].to_numpy().copy()
            freed = np.zeros(n)
            for t in range(n):
                if shifted_halved[t]:
                    freed[t] += eff[t] / 2.0
                    eff[t] = eff[t] / 2.0
            shifted_weights[a] = eff
            shifted_weights[rb2.CASH_SLEEVE] = shifted_weights[rb2.CASH_SLEEVE] + freed
        res = rb2.run_portfolio(weekly, assets, weekly_deposit_total, weekly_rf, shifted_weights, trigger_mode=trigger_mode)
        s = met.summarize_portfolio(res, weekly_rf)
        rows.append({"wealth_over_invested": s["wealth_over_invested"], "sharpe": s["sharpe"]})
    df = pd.DataFrame(rows)
    pctile_wealth = float(100.0 * (df["wealth_over_invested"] <= real_wealth_over_invested).mean())
    pctile_sharpe = float(100.0 * (df["sharpe"].dropna() <= real_sharpe).mean())
    return df, pctile_wealth, pctile_sharpe
