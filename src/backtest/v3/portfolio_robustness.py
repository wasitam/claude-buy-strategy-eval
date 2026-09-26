"""Rolling windows, block bootstrap, and placebo circular-shift (plan sec
4.3), adapted for the PORTFOLIO engine (family 002 and later portfolio
families). Reuses `_synthetic_daily_from_returns` from robustness.py (the
single-asset version) unmodified -- it only needs one asset's OHLC shape to
infer a realistic high/low padding ratio, applied independently per asset.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import portfolio_engine as peng
from . import metrics as met
from .robustness import _synthetic_daily_from_returns


def _synthetic_volume_from_blocks(daily: pd.DataFrame, starts: np.ndarray, block_days: int, target_len: int):
    """Block-bootstraps the real Volume series using the SAME block start
    indices as the paired return series (families 021/043's Amihud-ratio
    signal needs a Volume column; see robustness._synthetic_daily_from_returns).
    Returns None if `daily` has no Volume column (backward compatible for
    every Volume-free family)."""
    if "Volume" not in daily.columns:
        return None
    vol = daily["Volume"].to_numpy()
    blocks = [vol[s: s + block_days] for s in starts]
    path = np.concatenate(blocks) if blocks else np.array([])
    if len(path) < target_len:
        pad_val = path[-1] if len(path) else (vol[-1] if len(vol) else np.nan)
        path = np.concatenate([path, np.full(target_len - len(path), pad_val)])
    return path[:target_len]


def rolling_windows_portfolio(
    aligned: dict, daily_rf: pd.Series, weekly_deposit_per_asset: float,
    strategy_decide_builder, benchmark_decide_builder,
    window_years: float, step_days: int = 20, fee: float = 0.001,
) -> pd.DataFrame:
    """strategy_decide_builder(aligned_window, idx_window) -> decide fn."""
    idx = next(iter(aligned.values())).index
    n = len(idx)
    window_days = int(window_years * 252)
    rows = []
    for start in range(0, max(n - window_days, 0), step_days):
        w_idx = idx[start: start + window_days]
        if len(w_idx) < window_days * 0.9:
            continue
        w_assets = {a: df.loc[w_idx] for a, df in aligned.items()}
        rf = daily_rf.reindex(w_idx).ffill().fillna(0.0)
        s_decide = strategy_decide_builder(w_assets, w_idx)
        b_decide = benchmark_decide_builder(w_assets, w_idx)
        closes = {a: w_assets[a]["Close"].to_numpy() for a in w_assets}
        s_res = peng.run_portfolio(w_assets, weekly_deposit_per_asset, rf, s_decide, fee=fee)
        b_res = peng.run_portfolio(w_assets, weekly_deposit_per_asset, rf, b_decide, fee=fee)
        s_fw = float(s_res.cash[-1] + sum(s_res.units[a][-1] * closes[a][-1] for a in w_assets))
        b_fw = float(b_res.cash[-1] + sum(b_res.units[a][-1] * closes[a][-1] for a in w_assets))
        s = met.summarize_portfolio(s_res.to_frame(), rf, s_fw)
        b = met.summarize_portfolio(b_res.to_frame(), rf, b_fw)
        rows.append({
            "window_start": w_idx[0], "window_end": w_idx[-1],
            "strat_wealth_over_invested": s["wealth_over_invested"],
            "bench_wealth_over_invested": b["wealth_over_invested"],
            "strat_sharpe": s["sharpe"], "bench_sharpe": b["sharpe"],
            "beats_wealth": s["wealth_over_invested"] > b["wealth_over_invested"],
            "beats_sharpe": (s["sharpe"] if not np.isnan(s["sharpe"]) else -np.inf)
                            > (b["sharpe"] if not np.isnan(b["sharpe"]) else -np.inf),
        })
    return pd.DataFrame(rows)


def block_bootstrap_portfolio(
    aligned: dict, daily_rf: pd.Series, weekly_deposit_per_asset: float,
    strategy_decide_builder, benchmark_decide_builder,
    n_sims: int = 60, block_weeks: int = 4, detrend: bool = False, seed: int = 11, fee: float = 0.001,
) -> pd.DataFrame:
    """strategy_decide_builder(synthetic_aligned, idx) -> decide fn. The SAME
    block start indices are reused across all assets each sim (plan sec 4.3:
    "For portfolios, all assets share the same blocks")."""
    names = list(aligned.keys())
    idx = next(iter(aligned.values())).index
    rng = np.random.default_rng(seed)
    block_days = block_weeks * 5
    log_rets = {a: np.log(aligned[a]["Close"]).diff().dropna().to_numpy() for a in names}
    n = min(len(v) for v in log_rets.values())
    mean_rets = {a: log_rets[a][:n].mean() for a in names}
    n_blocks_needed = int(np.ceil(n / block_days))
    starts_pool = np.arange(0, max(n - block_days + 1, 1))
    rows = []
    for _ in range(n_sims):
        starts = rng.choice(starts_pool, size=n_blocks_needed, replace=True)
        synth = {}
        for a in names:
            blocks = [log_rets[a][s: s + block_days] for s in starts]
            path = np.concatenate(blocks)[:n]
            if detrend:
                path = path - mean_rets[a]
            vol_synth = _synthetic_volume_from_blocks(aligned[a], starts, block_days, target_len=len(path) + 1)
            synth[a] = _synthetic_daily_from_returns(aligned[a], path, volume=vol_synth)
        # align all assets to the shortest synthetic index (same length by construction)
        common_idx = synth[names[0]].index
        synth = {a: df.reindex(common_idx) for a, df in synth.items()}
        rf = daily_rf.reindex(common_idx).ffill().fillna(0.0)
        s_decide = strategy_decide_builder(synth, common_idx)
        b_decide = benchmark_decide_builder(synth, common_idx)
        closes = {a: synth[a]["Close"].to_numpy() for a in names}
        s_res = peng.run_portfolio(synth, weekly_deposit_per_asset, rf, s_decide, fee=fee)
        b_res = peng.run_portfolio(synth, weekly_deposit_per_asset, rf, b_decide, fee=fee)
        s_fw = float(s_res.cash[-1] + sum(s_res.units[a][-1] * closes[a][-1] for a in names))
        b_fw = float(b_res.cash[-1] + sum(b_res.units[a][-1] * closes[a][-1] for a in names))
        s = met.summarize_portfolio(s_res.to_frame(), rf, s_fw)
        b = met.summarize_portfolio(b_res.to_frame(), rf, b_fw)
        rows.append({
            "strat_wealth_over_invested": s["wealth_over_invested"],
            "bench_wealth_over_invested": b["wealth_over_invested"],
            "strat_sharpe": s["sharpe"], "bench_sharpe": b["sharpe"],
        })
    return pd.DataFrame(rows)


def placebo_circular_shift_portfolio(
    aligned: dict, daily_rf: pd.Series, weekly_deposit_per_asset: float,
    weekend_weights: pd.DataFrame, is_week_end: np.ndarray, asset_names: list,
    strategy_decide_from_weekend_weights, benchmark_decide,
    real_wealth_over_invested: float, real_sharpe: float,
    n_sims: int = 60, seed: int = 5, fee: float = 0.001,
) -> tuple:
    """Circular-shift the primary config's week-end target-weight sequence
    (the rotation signal, sampled only on decision days) among the week-end
    days themselves, then rerun with the shifted weight sequence mapped back
    onto the real price path. strategy_decide_from_weekend_weights(shifted_weekend_weights) -> decide fn."""
    idx = next(iter(aligned.values())).index
    rng = np.random.default_rng(seed)
    n_weekends = len(weekend_weights)
    rows = []
    for _ in range(n_sims):
        shift = int(rng.integers(1, n_weekends - 1))
        shifted = pd.DataFrame(
            np.roll(weekend_weights.to_numpy(), shift, axis=0),
            index=weekend_weights.index, columns=weekend_weights.columns,
        )
        decide = strategy_decide_from_weekend_weights(shifted)
        res = peng.run_portfolio(aligned, weekly_deposit_per_asset, daily_rf, decide, fee=fee)
        closes = {a: aligned[a]["Close"].to_numpy() for a in asset_names}
        fw = float(res.cash[-1] + sum(res.units[a][-1] * closes[a][-1] for a in asset_names))
        s = met.summarize_portfolio(res.to_frame(), daily_rf, fw)
        rows.append({"wealth_over_invested": s["wealth_over_invested"], "sharpe": s["sharpe"]})
    df = pd.DataFrame(rows)
    pctile_wealth = float(100.0 * (df["wealth_over_invested"] <= real_wealth_over_invested).mean())
    pctile_sharpe = float(100.0 * (df["sharpe"].dropna() <= real_sharpe).mean())
    return df, pctile_wealth, pctile_sharpe
