"""Deflated Sharpe Ratio (Bailey & Lopez de Prado, 2014) and N_eff via
average-linkage hierarchical clustering (plan sec 6.2), plus CSCV
probability of backtest overfitting (Bailey et al., 2017) as a diagnostic
(plan sec 4.4).
"""
from __future__ import annotations

import itertools
import numpy as np
import pandas as pd
from scipy.stats import norm, skew, kurtosis
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform


def _sharpe(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 2 or x.std(ddof=1) == 0:
        return 0.0
    return float(x.mean() / x.std(ddof=1))


def expected_max_sharpe(sr_estimates: np.ndarray, n_trials: int) -> float:
    """E[max SR] under the null across n_trials independent trials, using the
    Bailey & Lopez de Prado (2014) approximation from the variance of SR
    estimates across (clustered) trials, per unit period."""
    if n_trials <= 1:
        return float(np.nanmean(sr_estimates)) if len(sr_estimates) else 0.0
    var_sr = float(np.nanvar(sr_estimates, ddof=1)) if len(sr_estimates) > 1 else 0.0
    if var_sr <= 0:
        return float(np.nanmean(sr_estimates)) if len(sr_estimates) else 0.0
    euler_gamma = 0.5772156649
    e_max = np.sqrt(var_sr) * (
        (1 - euler_gamma) * norm.ppf(1 - 1.0 / n_trials)
        + euler_gamma * norm.ppf(1 - 1.0 / (n_trials * np.e))
    )
    return float(e_max)


def deflated_sharpe_ratio(
    returns: np.ndarray, cluster_sharpes: np.ndarray, n_eff: int, periods_per_year: float = 52.0
) -> dict:
    """DSR = Prob(true SR > 0 | observed SR, deflated for n_eff trials and the
    return series' skew/kurtosis). returns: the candidate's own weekly excess
    return series (non-annualized). cluster_sharpes: per-period Sharpe of every
    cluster representative (incl. the candidate), used to estimate SR0 (the
    expected max under the null) and its variance."""
    r = np.asarray(returns, dtype=float)
    r = r[~np.isnan(r)]
    n = len(r)
    if n < 3:
        return {"dsr": float("nan"), "sr": float("nan"), "sr0": float("nan"), "n": n, "n_eff": n_eff}
    sr_hat = _sharpe(r)
    sr0 = expected_max_sharpe(cluster_sharpes, max(n_eff, 1))
    g3 = float(skew(r, bias=False)) if n > 2 else 0.0
    g4 = float(kurtosis(r, fisher=False, bias=False)) if n > 3 else 3.0
    denom = np.sqrt(max(1e-12, 1 - g3 * sr_hat + (g4 - 1) / 4.0 * sr_hat**2))
    z = (sr_hat - sr0) * np.sqrt(n - 1) / denom
    dsr = float(norm.cdf(z))
    return {
        "dsr": dsr, "sr": sr_hat, "sr_annualized": sr_hat * np.sqrt(periods_per_year),
        "sr0": sr0, "n": n, "n_eff": n_eff, "skew": g3, "kurtosis": g4,
    }


def n_effective(trial_series: dict[str, pd.Series], rho_threshold: float = 0.5) -> tuple[int, dict]:
    """trial_series: {trial_id: weekly excess-return series}. Aligns on the
    common index, computes pairwise correlation, clusters by average linkage on
    distance sqrt(0.5*(1-rho)), cuts the tree so members joined at rho>=0.5
    (distance <= sqrt(0.25)=0.5) land in one cluster. Returns (n_eff, {trial_id: cluster_id})."""
    ids = list(trial_series.keys())
    if len(ids) <= 1:
        return len(ids), {i: 0 for i in ids}
    df = pd.DataFrame({i: trial_series[i] for i in ids}).dropna(how="all")
    df = df.fillna(0.0)
    corr = np.array(df.corr().fillna(0.0).to_numpy(), copy=True)
    np.fill_diagonal(corr, 1.0)
    dist = np.array(np.sqrt(np.clip(0.5 * (1 - corr), 0, None)), copy=True)
    np.fill_diagonal(dist, 0.0)
    condensed = squareform(dist, checks=False)
    Z = linkage(condensed, method="average")
    dist_cutoff = np.sqrt(0.5 * (1 - rho_threshold))
    labels = fcluster(Z, t=dist_cutoff, criterion="distance")
    n_eff = int(len(set(labels)))
    mapping = {ids[i]: int(labels[i]) for i in range(len(ids))}
    return n_eff, mapping


def cluster_representative_sharpes(trial_series: dict[str, pd.Series], cluster_map: dict) -> np.ndarray:
    clusters = {}
    for tid, cid in cluster_map.items():
        clusters.setdefault(cid, []).append(tid)
    reps = []
    for cid, members in clusters.items():
        best = max(members, key=lambda m: _sharpe(trial_series[m].dropna().to_numpy()))
        reps.append(_sharpe(trial_series[best].dropna().to_numpy()))
    return np.array(reps)


def cscv_pbo(grid_returns: dict[str, pd.Series], n_splits: int = 8) -> dict:
    """Combinatorially Symmetric Cross-Validation probability of backtest
    overfitting (Bailey, Borwein, Lopez de Prado, Zhu, 2017), diagnostic only
    (plan sec 4.4). grid_returns: {config_id: weekly return series (strategy,
    not excess)} for one family's full pre-declared grid.

    n_splits must be even; data is cut into n_splits contiguous blocks, and
    every way of choosing half of them as the "in-sample" set (vs the
    complementary "out-of-sample" set) is evaluated.
    """
    ids = list(grid_returns.keys())
    if len(ids) < 2:
        return {"pbo": float("nan"), "n_combos": 0}
    df = pd.DataFrame({i: grid_returns[i] for i in ids}).dropna(how="all").fillna(0.0)
    n = len(df)
    if n < n_splits * 2:
        n_splits = max(2, n // 4 - (n // 4) % 2 or 2)
    if n_splits < 2:
        return {"pbo": float("nan"), "n_combos": 0}
    block_edges = np.linspace(0, n, n_splits + 1).astype(int)
    blocks = [df.iloc[block_edges[i]:block_edges[i + 1]] for i in range(n_splits)]
    half = n_splits // 2
    combos = list(itertools.combinations(range(n_splits), half))
    logits = []
    for combo in combos:
        is_blocks = [blocks[i] for i in combo]
        oos_blocks = [blocks[i] for i in range(n_splits) if i not in combo]
        is_df = pd.concat(is_blocks)
        oos_df = pd.concat(oos_blocks)
        is_sr = is_df.apply(lambda c: _sharpe(c.to_numpy()))
        best_id = is_sr.idxmax()
        oos_sr = oos_df.apply(lambda c: _sharpe(c.to_numpy()))
        rank = oos_sr.rank(pct=True)[best_id]  # relative rank of the IS-best config, OOS
        # avoid 0/1 exactly
        rank = min(max(rank, 1e-6), 1 - 1e-6)
        logit = np.log(rank / (1 - rank))
        logits.append(logit)
    pbo = float(np.mean(np.array(logits) < 0))
    return {"pbo": pbo, "n_combos": len(combos), "n_splits": n_splits}
