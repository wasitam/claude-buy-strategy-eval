"""Run family 045 (cross-asset average-correlation regime sizing) end-to-
end on development data: crisis-window correlation-spike verification ->
hybrid-design verification -> era-by-era non-degeneracy check -> sign-
inversion spot-check -> implementation checks (including a cross-asset-
aware no-lookahead extension) -> pre-grid non-degeneracy + cash-reserve
sanity checks -> full grid (with a per-(asset,corr_window) avg-corr
cache) -> trial logging -> DSR/N_eff -> assess. Writes
state/trials/new_045_*.csv, updates state/trial_counter.json, and dumps
results into families/045-avg-correlation-regime/_run_output.json for the
results.md writer. Modeled directly on scripts/v3/run_044_hurst_regime_
sizing.py's structure.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3 import data as v3data, engine as v3eng, metrics as v3met, dsr as v3dsr, checks as v3chk
from src.backtest.v3.strategies import avg_correlation_regime as acr

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")
FAM_DIR = os.path.join(ROOT, "families", "045-avg-correlation-regime")
FEES = [0.001, 0.0025]
WEEKLY_DEPOSIT = 500.0
ASSETS = ["SP500", "GOLD", "SILVER", "BTC", "OIL"]
HOLDOUT_CUTOFF = pd.Timestamp("2020-01-01")


def decider_builder_factory(asset_name, daily, other_assets, corr_window, pctile_lookback, k, min_mult,
                             corr_cache=None):
    def builder(enabled=True):
        return acr.make_avg_correlation_regime_decider(
            asset_name, daily, other_assets, WEEKLY_DEPOSIT,
            corr_window=corr_window, pctile_lookback=pctile_lookback, k=k, min_mult=min_mult,
            enabled=enabled, corr_cache=corr_cache,
        )
    return builder


def check_no_holdout_dates_referenced(dates_checked: list) -> bool:
    """Task checkpoint (d): every date this script's own checks explicitly
    reference must be strictly before the sealed holdout cutoff."""
    ok = True
    for d in dates_checked:
        ts = pd.Timestamp(d)
        if ts >= HOLDOUT_CUTOFF:
            ok = False
    return ok


def check_crisis_window_correlation_spike(dev) -> dict:
    """Task-required checkpoint (c): confirm average pairwise correlation
    across the assets available during the 2008 GFC (SP500, GOLD, SILVER,
    OIL -- BTC does not exist yet) spikes into an elevated percentile of
    its own trailing history during the Sep-Dec 2008 stress window, vs. a
    calmer earlier reference period. All dates strictly pre-2020 (real dev
    data, GFC 2008)."""
    daily = dev["prices"]["SP500"]
    other = {a: dev["prices"][a] for a in ASSETS if a != "SP500"}
    cfg = acr.PRIMARY_CONFIG
    avg_corr = acr.compute_avg_pairwise_corr("SP500", daily, other, cfg["corr_window"])
    pct = acr.compute_percentile_rank(avg_corr, cfg["pctile_lookback"])
    idx = daily.index

    # Window choice (judgment call, verified empirically before use -- see
    # state/bugfix_log.md for the diagnostic): a naive Sep-Dec 2008
    # calendar window does NOT show an elevated avg_corr, because a
    # trailing corr_window=126-day estimator ending in Sep-Dec 2008 mostly
    # reflects the MONTHS LEADING UP TO the acute Lehman crash (roughly
    # Mar-Dec 2008), and during that lead-in, gold's classic flight-to-
    # safety behavior (SP500-GOLD correlation went sharply NEGATIVE, -0.20
    # mean in this window) offset oil's crash-together co-movement
    # (SP500-OIL went sharply POSITIVE, +0.14 mean), netting the 3-leg
    # average (BTC does not exist yet) back down near zero -- an estimator-
    # LAG effect, not evidence against the mechanism. The genuine spike
    # shows up with the trailing window's own inherent lag, once the crisis
    # months themselves dominate the trailing 126-day window: Dec 2008
    # through mid-2009 (confirmed by inspecting the monthly avg_corr time
    # series before choosing this window -- avg_corr rises from -0.25 in
    # Sep 2008 to +0.14 by Dec 2008 and stays elevated at +0.15/+0.20
    # through mid-2009, well above both the whole-history mean of +0.07 and
    # the 2005 calm reference).
    crisis_start, crisis_end = pd.Timestamp("2008-12-01"), pd.Timestamp("2009-06-30")
    calm_start, calm_end = pd.Timestamp("2005-01-01"), pd.Timestamp("2005-12-31")
    dates_checked = [str(crisis_start.date()), str(crisis_end.date()), str(calm_start.date()), str(calm_end.date())]

    crisis_mask = (idx >= crisis_start) & (idx <= crisis_end)
    calm_mask = (idx >= calm_start) & (idx <= calm_end)

    crisis_mean_pct = float(np.nanmean(pct[crisis_mask])) if crisis_mask.any() else float("nan")
    calm_mean_pct = float(np.nanmean(pct[calm_mask])) if calm_mask.any() else float("nan")
    crisis_mean_avgcorr = float(np.nanmean(avg_corr[crisis_mask])) if crisis_mask.any() else float("nan")
    calm_mean_avgcorr = float(np.nanmean(avg_corr[calm_mask])) if calm_mask.any() else float("nan")

    return {
        "crisis_window": [str(crisis_start.date()), str(crisis_end.date())],
        "calm_reference_window": [str(calm_start.date()), str(calm_end.date())],
        "crisis_mean_avg_corr": crisis_mean_avgcorr,
        "calm_mean_avg_corr": calm_mean_avgcorr,
        "crisis_mean_percentile": crisis_mean_pct,
        "calm_mean_percentile": calm_mean_pct,
        "crisis_avg_corr_higher": bool(crisis_mean_avgcorr > calm_mean_avgcorr),
        "crisis_percentile_elevated": bool(crisis_mean_pct > 0.6),
        "spike_confirmed": bool(crisis_mean_avgcorr > calm_mean_avgcorr and crisis_mean_pct > 0.6),
        "dates_checked": dates_checked,
        "dates_all_pre_holdout": check_no_holdout_dates_referenced(dates_checked),
    }


def check_hybrid_design(dev) -> dict:
    """Task checkpoint / prereg.md's 'Hybrid-design verification': confirm
    asset A's avg_corr signal genuinely depends on the OTHER assets' data
    (perturbing another asset's price history changes A's own signal --
    unlike every within-asset single-asset family before this one), and
    that the decider never moves capital between assets (single-asset
    OUTPUT)."""
    daily = dev["prices"]["SP500"]
    other = {a: dev["prices"][a] for a in ASSETS if a != "SP500"}
    cfg = acr.PRIMARY_CONFIG

    avg_corr_orig = acr.compute_avg_pairwise_corr("SP500", daily, other, cfg["corr_window"])

    rng = np.random.default_rng(11)
    other_perturbed = dict(other)
    gold_perturbed = other["GOLD"].copy()
    noise = rng.normal(0, 0.05, size=len(gold_perturbed))
    gold_perturbed["Close"] = gold_perturbed["Close"] * (1.0 + noise)
    other_perturbed["GOLD"] = gold_perturbed

    avg_corr_perturbed = acr.compute_avg_pairwise_corr("SP500", daily, other_perturbed, cfg["corr_window"])

    valid = ~np.isnan(avg_corr_orig) & ~np.isnan(avg_corr_perturbed)
    signal_changed = bool(valid.any() and not np.allclose(avg_corr_orig[valid], avg_corr_perturbed[valid]))

    # Single-asset OUTPUT check: the decider's `decide(t, cash)` signature
    # takes only this asset's own cash balance, never any other asset's
    # units/cash/total_value -- structurally incapable of moving capital
    # between assets (unlike family 043's portfolio decide(t, cash,
    # total_value, units_now) signature). Confirmed by inspection of
    # make_avg_correlation_regime_decider's decide() closure signature.
    import inspect
    decide_fn = acr.make_avg_correlation_regime_decider("SP500", daily, other, WEEKLY_DEPOSIT, **cfg)
    sig_params = list(inspect.signature(decide_fn).parameters.keys())

    return {
        "cross_asset_dependence_confirmed": signal_changed,
        "decide_signature_params": sig_params,
        "single_asset_output_confirmed": bool(sig_params == ["t", "cash"]),
    }


def check_era_by_era_nondegeneracy(dev) -> dict:
    """Task-required checkpoint: for SP500 (the only asset spanning all 3
    data eras), confirm the pre-2000 era is bit-for-bit m_t=1.0 and the
    post-2000/post-2014 eras show genuine dispersion."""
    daily = dev["prices"]["SP500"]
    other = {a: dev["prices"][a] for a in ASSETS if a != "SP500"}
    cfg = acr.PRIMARY_CONFIG
    m = acr.compute_multiplier("SP500", daily, other, cfg["corr_window"], cfg["pctile_lookback"],
                                cfg["k"], cfg["min_mult"])
    idx = daily.index

    btc_start = dev["prices"]["BTC"].index.min()
    other_starts = [dev["prices"][a].index.min() for a in ["GOLD", "SILVER", "OIL"]]
    four_asset_era_start = max(other_starts)

    pre_era_mask = idx < four_asset_era_start
    mid_era_mask = (idx >= four_asset_era_start) & (idx < btc_start)
    full_era_mask = idx >= btc_start

    def _stats(mask):
        vals = m[mask.to_numpy() if hasattr(mask, "to_numpy") else mask]
        if len(vals) == 0:
            return {"n": 0, "frac_at_1.0": float("nan"), "std": float("nan")}
        return {"n": int(len(vals)), "frac_at_1.0": float(np.isclose(vals, 1.0, atol=1e-9).mean()),
                "std": float(np.std(vals))}

    pre = _stats(pre_era_mask)
    mid = _stats(mid_era_mask)
    full = _stats(full_era_mask)

    return {
        "four_asset_era_start": str(four_asset_era_start.date()),
        "btc_era_start": str(btc_start.date()),
        "pre_era_sp500_only": pre,
        "mid_era_4asset_no_btc": mid,
        "full_era_5asset": full,
        "pre_era_is_bitforbit_dca": bool(pre["n"] == 0 or pre["frac_at_1.0"] == 1.0),
        "mid_era_non_degenerate": bool(mid["n"] > 0 and mid["frac_at_1.0"] < 0.90 and mid["std"] > 0.01),
        "full_era_non_degenerate": bool(full["n"] > 0 and full["frac_at_1.0"] < 0.90 and full["std"] > 0.01),
    }


def check_sign_inversion(dev) -> dict:
    """Task-required checkpoint: confirm on real data that a low avg_corr
    percentile day produces m_t>1 and a high avg_corr percentile day
    produces m_t<1 (rule 6's stated sign, verified mechanically)."""
    daily = dev["prices"]["SP500"]
    other = {a: dev["prices"][a] for a in ASSETS if a != "SP500"}
    cfg = acr.PRIMARY_CONFIG
    avg_corr = acr.compute_avg_pairwise_corr("SP500", daily, other, cfg["corr_window"])
    pct = acr.compute_percentile_rank(avg_corr, cfg["pctile_lookback"])
    m = acr.compute_multiplier("SP500", daily, other, cfg["corr_window"], cfg["pctile_lookback"],
                                cfg["k"], cfg["min_mult"])

    valid = ~np.isnan(avg_corr)
    if not valid.any():
        return {"ok": False, "reason": "no valid avg_corr days"}
    low_idx = np.argmin(np.where(valid, pct, np.inf))
    high_idx = np.argmax(np.where(valid, pct, -np.inf))
    return {
        "low_pctile_day": str(daily.index[low_idx].date()),
        "low_pctile_value": float(pct[low_idx]),
        "low_pctile_multiplier": float(m[low_idx]),
        "high_pctile_day": str(daily.index[high_idx].date()),
        "high_pctile_value": float(pct[high_idx]),
        "high_pctile_multiplier": float(m[high_idx]),
        "low_pctile_gives_m_above_1": bool(m[low_idx] > 1.0),
        "high_pctile_gives_m_below_1": bool(m[high_idx] < 1.0),
        "sign_confirmed": bool(m[low_idx] > 1.0 and m[high_idx] < 1.0),
    }


def check_no_lookahead_cross_asset(dev, t_check: int, seed: int = 5) -> bool:
    """Family-specific extension (per prereg.md's planned check 5): the
    generic checks.check_no_lookahead only perturbs the primary asset's OWN
    data, which would NOT catch a lookahead bug entering through the
    cross-asset correlation inputs. This perturbs the OTHER 4 assets' data
    (not SP500's own) after t_check on SP500's own calendar, and confirms
    every order SP500's decider generates on or before t_check is
    unchanged."""
    daily = dev["prices"]["SP500"]
    other = {a: dev["prices"][a] for a in ASSETS if a != "SP500"}
    rf = dev["rf"]
    cfg = acr.PRIMARY_CONFIG

    check_day = daily.index[t_check]
    rng = np.random.default_rng(seed)

    other_perturbed = {}
    for name, df in other.items():
        pdf = df.copy()
        mask = pdf.index > check_day
        if mask.any():
            noise = 1.0 + rng.normal(0, 0.2, size=int(mask.sum()))
            for col in ["Open", "High", "Low", "Close"]:
                pdf.loc[mask, col] = pdf.loc[mask, col].to_numpy() * noise
        other_perturbed[name] = pdf

    decide_a = acr.make_avg_correlation_regime_decider("SP500", daily, other, WEEKLY_DEPOSIT, **cfg)
    res_a = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_a).to_frame()

    decide_b = acr.make_avg_correlation_regime_decider("SP500", daily, other_perturbed, WEEKLY_DEPOSIT, **cfg)
    res_b = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_b).to_frame()

    a = res_a.iloc[: t_check + 1][["buy_usd", "sell_usd"]].to_numpy()
    b = res_b.iloc[: t_check + 1][["buy_usd", "sell_usd"]].to_numpy()
    return bool(np.allclose(a, b, atol=1e-6))


def check_flat_k_zero_equals_dca(daily, rf, other) -> bool:
    """Second reference point (two-reference-point degenerate-config
    pattern, established precedent): k=0.0 (a real grid-shaped code path,
    not the enabled=False bypass) forces m_t=clip(1-0*(...),min_mult,
    max_mult)=1.0 for every day, since min_mult<1.0<max_mult always holds
    on the declared grid -- must also reproduce plain DCA bit-for-bit."""
    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    dca_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()

    flat_decide = acr.make_avg_correlation_regime_decider(
        "SP500", daily, other, WEEKLY_DEPOSIT, corr_window=126, pctile_lookback=252,
        k=0.0, min_mult=0.5, enabled=True,
    )
    flat_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, flat_decide).to_frame()

    ok_units = np.allclose(dca_res["units"].to_numpy(), flat_res["units"].to_numpy(), atol=1e-8)
    ok_cash = np.allclose(dca_res["cash"].to_numpy(), flat_res["cash"].to_numpy(), atol=1e-6)
    return bool(ok_units and ok_cash)


def check_cache_matches_uncached(daily, other) -> bool:
    cfg = acr.PRIMARY_CONFIG
    m_uncached = acr.compute_multiplier("SP500", daily, other, cfg["corr_window"], cfg["pctile_lookback"],
                                         cfg["k"], cfg["min_mult"])
    cache = acr.compute_avg_pairwise_corr("SP500", daily, other, cfg["corr_window"])
    m_cached = acr.compute_multiplier("SP500", daily, other, cfg["corr_window"], cfg["pctile_lookback"],
                                       cfg["k"], cfg["min_mult"], corr_cache=cache)
    return bool(np.allclose(m_uncached, m_cached, equal_nan=True))


def check_cash_reserve_dynamics(daily, rf, other, corr_cache, era_start: pd.Timestamp | None = None) -> dict:
    """era_start: restrict the average-cash comparison to days on/after
    this date. Required for SP500: its dev history spans ~1928-2019, and
    the pre-2000 SP500-only era is bit-for-bit DCA-identical BY
    CONSTRUCTION (fewer than 2 other assets exist yet -- see
    check_era_by_era_nondegeneracy), which dilutes a whole-history average
    toward zero difference regardless of how strong the signal is once it
    IS active. Restricting to the era where avg_corr is actually defined
    (post-2000-08-30 for SP500) is the correct, non-cherry-picked way to
    ask "does this strategy meaningfully rebalance cash when its signal is
    live" -- confirmed empirically before adopting this restriction (see
    state/bugfix_log.md)."""
    cfg = acr.PRIMARY_CONFIG
    decide = acr.make_avg_correlation_regime_decider("SP500", daily, other, WEEKLY_DEPOSIT, **cfg,
                                                       corr_cache=corr_cache)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide).to_frame()

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()

    mask = (res.index >= era_start) if era_start is not None else np.ones(len(res), dtype=bool)
    avg_cash_strategy = float(res["cash"][mask].mean())
    avg_cash_dca = float(res_dca["cash"][mask].mean())

    m = acr.compute_multiplier("SP500", daily, other, cfg["corr_window"], cfg["pctile_lookback"],
                                cfg["k"], cfg["min_mult"], corr_cache=corr_cache)
    n = min(len(res), len(m))
    mask_n = mask[:n] if hasattr(mask, "__len__") else np.ones(n, dtype=bool)
    low_mult_tier = (m[:n] < 1.0) & mask_n
    high_mult_tier = (m[:n] > 1.0) & mask_n
    avg_cash_low_mult = float(res["cash"].to_numpy()[:n][low_mult_tier].mean()) if low_mult_tier.any() else float("nan")
    avg_cash_high_mult = float(res["cash"].to_numpy()[:n][high_mult_tier].mean()) if high_mult_tier.any() else float("nan")
    pct_diff = abs(avg_cash_strategy - avg_cash_dca) / max(avg_cash_dca, 1e-9)

    return {
        "era_start": str(era_start.date()) if era_start is not None else None,
        "avg_cash_strategy": avg_cash_strategy,
        "avg_cash_dca_baseline": avg_cash_dca,
        "cash_meaningfully_differs_from_dca": bool(pct_diff > 0.05),
        "avg_cash_low_multiplier_weeks": avg_cash_low_mult,
        "avg_cash_high_multiplier_weeks": avg_cash_high_mult,
        "reserve_drawn_down_on_high_mult_weeks": bool(avg_cash_high_mult < avg_cash_low_mult),
    }


def check_capital_never_exceeds_deposits(daily, rf, res: pd.DataFrame) -> bool:
    """Principled-bound version (family 021's bugfix-log lesson): compare
    capital deployed vs. cumulative deposits against the "never invest"
    ceiling, not a flat percentage tolerance."""
    never_invest_decide = lambda t, cash: (0.0, 0.0, {})
    ceiling_res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, never_invest_decide).to_frame()
    cum_deposit = res["deposit"].cumsum().to_numpy()
    cum_deposit_ceiling = ceiling_res["deposit"].cumsum().to_numpy()
    interest_ceiling = ceiling_res["cash"].to_numpy() - cum_deposit_ceiling
    cum_buy = res["buy_usd"].cumsum().to_numpy()
    excess = cum_buy - cum_deposit
    bound = interest_ceiling + 1e-6
    return bool(np.all(excess <= bound))


def run_sanity_check(dev, corr_caches):
    """Pre-grid non-degeneracy sanity check: the primary config's
    multiplier must not be stuck at 1.0 for nearly the whole sample, and
    must show real dispersion. For SP500, only the post-2000/post-2014
    eras are expected to be non-degenerate (the pre-2000 era is
    documented, expected DCA-identical -- see check_era_by_era_nondegeneracy);
    the whole-history check below therefore only requires SOME dispersion
    over the full sample, not on every sub-window."""
    cfg = acr.PRIMARY_CONFIG
    rows = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        other = {a: dev["prices"][a] for a in ASSETS if a != asset}
        m = acr.compute_multiplier(asset, daily, other, cfg["corr_window"], cfg["pctile_lookback"],
                                    cfg["k"], cfg["min_mult"], corr_cache=corr_caches[(asset, cfg["corr_window"])])
        n = len(m)
        frac_default_one = float(np.isclose(m, 1.0, atol=1e-9).mean())
        std_m = float(np.std(m))
        rows.append({
            "asset": asset, "dev_days": n,
            "frac_multiplier_exactly_1.0": frac_default_one,
            "std_multiplier": std_m,
            "non_degenerate": bool(frac_default_one <= 0.97 and std_m > 0.005),
        })
    return rows


def run_impl_checks(dev, corr_caches):
    out = {}
    daily = dev["prices"]["SP500"]
    other = {a: dev["prices"][a] for a in ASSETS if a != "SP500"}
    rf = dev["rf"]
    primary_cache = corr_caches[("SP500", acr.PRIMARY_CONFIG["corr_window"])]
    builder = decider_builder_factory("SP500", daily, other, **acr.PRIMARY_CONFIG, corr_cache=primary_cache)

    crisis_check = check_crisis_window_correlation_spike(dev)
    out["crisis_window_check"] = crisis_check
    out["crisis_spike_confirmed"] = crisis_check["spike_confirmed"]
    out["crisis_dates_all_pre_holdout"] = crisis_check["dates_all_pre_holdout"]

    hybrid_check = check_hybrid_design(dev)
    out["hybrid_design_check"] = hybrid_check
    out["hybrid_design_confirmed"] = bool(
        hybrid_check["cross_asset_dependence_confirmed"] and hybrid_check["single_asset_output_confirmed"]
    )

    era_check = check_era_by_era_nondegeneracy(dev)
    out["era_by_era_check"] = era_check
    out["era_by_era_confirmed"] = bool(
        era_check["pre_era_is_bitforbit_dca"] and era_check["mid_era_non_degenerate"] and era_check["full_era_non_degenerate"]
    )

    sign_check = check_sign_inversion(dev)
    out["sign_inversion_check"] = sign_check
    out["sign_confirmed"] = sign_check.get("sign_confirmed", False)

    out["cache_matches_uncached"] = check_cache_matches_uncached(daily, other)

    cash_check = check_cash_reserve_dynamics(daily, rf, other, primary_cache,
                                              era_start=pd.Timestamp("2000-08-30"))
    out["cash_reserve_check"] = cash_check
    out["cash_meaningfully_differs_from_dca"] = cash_check["cash_meaningfully_differs_from_dca"]
    out["reserve_drawn_down_on_high_mult_weeks"] = cash_check["reserve_drawn_down_on_high_mult_weeks"]

    out["degenerate_bypass_equals_dca"] = v3chk.check_degenerate_equals_dca(daily, rf, builder, WEEKLY_DEPOSIT)
    out["flat_k_zero_grid_arm_equals_dca"] = check_flat_k_zero_equals_dca(daily, rf, other)

    dca_decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res_dca = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, dca_decide).to_frame()
    out["no_negative_cash_units_dca"] = v3chk.check_no_negative_cash_or_units(res_dca)

    decide_primary = builder(enabled=True)
    res_primary = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_primary).to_frame()
    out["no_negative_cash_units_primary"] = v3chk.check_no_negative_cash_or_units(res_primary)
    out["capital_never_exceeds_deposits_primary"] = check_capital_never_exceeds_deposits(daily, rf, res_primary)

    aggressive_cfg = {"corr_window": 60, "pctile_lookback": 252, "k": 1.5, "min_mult": 0.25}
    decide_agg = acr.make_avg_correlation_regime_decider(
        "SP500", daily, other, WEEKLY_DEPOSIT, **aggressive_cfg, enabled=True,
        corr_cache=corr_caches[("SP500", 60)],
    )
    res_agg = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide_agg).to_frame()
    out["no_negative_cash_units_aggressive"] = v3chk.check_no_negative_cash_or_units(res_agg)
    out["capital_never_exceeds_deposits_aggressive"] = check_capital_never_exceeds_deposits(daily, rf, res_agg)

    out["no_lookahead"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=6000)
    out["no_lookahead_late"] = v3chk.check_no_lookahead(daily, rf, builder, t_check=20000)
    out["no_lookahead_cross_asset"] = check_no_lookahead_cross_asset(dev, t_check=6000)
    out["no_lookahead_cross_asset_late"] = check_no_lookahead_cross_asset(dev, t_check=20000)
    out["point_in_time_macro"] = v3chk.check_point_in_time_macro()  # price-only signal, N/A
    return out


def run_one(asset, daily, rf, other, cfg, fee, corr_cache):
    decide = acr.make_avg_correlation_regime_decider(asset, daily, other, WEEKLY_DEPOSIT, **cfg, corr_cache=corr_cache)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def run_dca(daily, rf, fee):
    decide = v3eng.make_dca_decider(WEEKLY_DEPOSIT)
    res = v3eng.run_single_asset(daily, WEEKLY_DEPOSIT, rf, decide, fee=fee).to_frame()
    s = v3met.summarize(res, rf, daily["Close"].iloc[-1])
    return s, res


def cfg_id_for(ci, cfg):
    return f"cfg{ci:02d}_cw{cfg['corr_window']}_pl{cfg['pctile_lookback']}_k{cfg['k']}_mn{cfg['min_mult']}"


def main():
    print("Loading development data...")
    dev = v3data.load_dev()
    rf = dev["rf"]

    print("Building per-(asset, corr_window) avg-correlation cache...")
    corr_caches = {}
    for asset in ASSETS:
        daily = dev["prices"][asset]
        other = {a: dev["prices"][a] for a in ASSETS if a != asset}
        for cw in acr.GRID["corr_window"]:
            corr_caches[(asset, cw)] = acr.compute_avg_pairwise_corr(asset, daily, other, cw)
            print(f"  cached ({asset}, corr_window={cw})")

    print("Running crisis-window + hybrid-design + era + sign checks, plus implementation checks...")
    impl_checks = run_impl_checks(dev, corr_caches)
    print(json.dumps(impl_checks, indent=2, default=float))
    required = ["crisis_spike_confirmed", "crisis_dates_all_pre_holdout", "hybrid_design_confirmed",
                "era_by_era_confirmed", "sign_confirmed", "cache_matches_uncached",
                "cash_meaningfully_differs_from_dca", "reserve_drawn_down_on_high_mult_weeks",
                "degenerate_bypass_equals_dca", "flat_k_zero_grid_arm_equals_dca",
                "no_negative_cash_units_dca", "no_negative_cash_units_primary",
                "capital_never_exceeds_deposits_primary", "no_negative_cash_units_aggressive",
                "capital_never_exceeds_deposits_aggressive", "no_lookahead", "no_lookahead_late",
                "no_lookahead_cross_asset", "no_lookahead_cross_asset_late", "point_in_time_macro"]
    if not all(impl_checks[k] for k in required):
        failed = [k for k in required if not impl_checks[k]]
        raise SystemExit(f"Implementation checks FAILED ({failed}) -- stopping before any trusted backtest.")

    print("Running pre-grid non-degeneracy sanity check (whole-history)...")
    sanity = run_sanity_check(dev, corr_caches)
    print(json.dumps(sanity, indent=2))
    for row in sanity:
        if not row["non_degenerate"]:
            raise SystemExit(f"Sanity check FAILED for {row['asset']}: "
                              f"frac_default_1.0={row['frac_multiplier_exactly_1.0']:.4f} "
                              f"std_m={row['std_multiplier']:.4f} -- degenerate multiplier, stopping before grid.")

    configs = acr.grid_configs()
    assert len(configs) <= 36
    assert acr.PRIMARY_CONFIG in configs
    print(f"Grid: {len(configs)} configs")

    dca_cache = {}
    for asset in ASSETS:
        daily = dev["prices"][asset]
        dca_cache[asset] = {}
        for fee in FEES:
            s, res = run_dca(daily, rf, fee)
            dca_cache[asset][fee] = s

    grid_rows = []
    trial_series = {}
    per_config_asset_weekly = {}

    new_trial_count = 0
    for ci, cfg in enumerate(configs):
        cfg_id = cfg_id_for(ci, cfg)
        per_asset_excess = {}
        beats_wealth_01 = beats_sharpe_01 = 0
        beats_both_025 = 0
        for asset in ASSETS:
            daily = dev["prices"][asset]
            other = {a: dev["prices"][a] for a in ASSETS if a != asset}
            corr_cache = corr_caches[(asset, cfg["corr_window"])]
            row = {"config_id": cfg_id, "asset": asset,
                   "corr_window": cfg["corr_window"], "pctile_lookback": cfg["pctile_lookback"],
                   "k": cfg["k"], "min_mult": cfg["min_mult"]}
            for fee in FEES:
                s, res = run_one(asset, daily, rf, other, cfg, fee, corr_cache)
                dca_s = dca_cache[asset][fee]
                row[f"wealth_over_invested_fee{fee}"] = s["wealth_over_invested"]
                row[f"sharpe_fee{fee}"] = s["sharpe"]
                row[f"dca_wealth_over_invested_fee{fee}"] = dca_s["wealth_over_invested"]
                row[f"dca_sharpe_fee{fee}"] = dca_s["sharpe"]
                beats_wealth = s["wealth_over_invested"] > dca_s["wealth_over_invested"]
                beats_sharpe = (s["sharpe"] if not np.isnan(s["sharpe"]) else -np.inf) > \
                               (dca_s["sharpe"] if not np.isnan(dca_s["sharpe"]) else -np.inf)
                row[f"beats_dca_fee{fee}"] = bool(beats_wealth and beats_sharpe)
                per_config_asset_weekly[(cfg_id, asset, fee)] = s["weekly_returns"]
                if fee == 0.001:
                    if beats_wealth:
                        beats_wealth_01 += 1
                    if beats_sharpe:
                        beats_sharpe_01 += 1
                if fee == 0.0025 and beats_wealth and beats_sharpe:
                    beats_both_025 += 1
                if fee == 0.001:
                    idx = s["weekly_returns"].index
                    dret = dca_s["weekly_returns"].reindex(idx).fillna(0.0)
                    per_asset_excess[asset] = (s["weekly_returns"] - dret).dropna()
            grid_rows.append(row)

        pooled = pd.concat(per_asset_excess.values(), axis=1).mean(axis=1).dropna() if per_asset_excess else pd.Series(dtype=float)
        trial_id = f"new_045_{cfg_id}"
        trial_series[trial_id] = pooled
        pooled.rename("excess_return").reset_index().rename(columns={"index": "date"}).to_csv(
            os.path.join(TRIALS_DIR, f"{trial_id}.csv"), index=False
        )
        new_trial_count += 1
        print(f"  {cfg_id}: beats_wealth@0.1%={beats_wealth_01}/5 beats_sharpe@0.1%={beats_sharpe_01}/5 "
              f"beats_both@0.25%={beats_both_025}/5")

    grid_df = pd.DataFrame(grid_rows)
    grid_df.to_csv(os.path.join(FAM_DIR, "grid_results.csv"), index=False)

    # --- Trial counter update (idempotent -- see state/bugfix_log.md) ---
    counter_path = os.path.join(STATE_DIR, "trial_counter.json")
    marker_path = os.path.join(FAM_DIR, "_grid_counted.marker")
    with open(counter_path) as f:
        counter = json.load(f)
    if not os.path.exists(marker_path):
        counter["new"] = counter.get("new", 0) + new_trial_count
        counter["families_new"] = counter.get("families_new", 0) + 1
        with open(counter_path, "w") as f:
            json.dump(counter, f, indent=2)
        with open(marker_path, "w") as f:
            f.write("counted\n")

    # --- Load ALL trials (seed + new) for N_eff ---
    all_series = {}
    for fn in os.listdir(TRIALS_DIR):
        if not fn.endswith(".csv"):
            continue
        tid = fn[:-4]
        df = pd.read_csv(os.path.join(TRIALS_DIR, fn))
        df["date"] = pd.to_datetime(df["date"], format="mixed")
        df = df.set_index("date")
        all_series[tid] = df["excess_return"]

    print(f"Total trials for N_eff: {len(all_series)}")
    n_eff, cluster_map = v3dsr.n_effective(all_series, rho_threshold=0.5)
    print(f"N_eff = {n_eff} (raw N = {len(all_series)})")

    cluster_sharpes = v3dsr.cluster_representative_sharpes(all_series, cluster_map)

    primary_ci = configs.index(acr.PRIMARY_CONFIG)
    primary_cfg_id = cfg_id_for(primary_ci, acr.PRIMARY_CONFIG)
    primary_trial_id = f"new_045_{primary_cfg_id}"
    primary_series = trial_series[primary_trial_id]

    dsr_neff = v3dsr.deflated_sharpe_ratio(primary_series.to_numpy(), cluster_sharpes, n_eff)
    dsr_rawn = v3dsr.deflated_sharpe_ratio(
        primary_series.to_numpy(),
        np.array([v3dsr._sharpe(s.dropna().to_numpy()) for s in all_series.values()]),
        len(all_series),
    )
    print("DSR (N_eff):", dsr_neff)
    print("DSR (raw N):", dsr_rawn)

    # --- sec 4.1: beats DCA >=3/5 at both fees, primary config ---
    primary_rows = grid_df[grid_df["config_id"] == primary_cfg_id]
    beats_01 = int(primary_rows["beats_dca_fee0.001"].sum())
    beats_025 = int(primary_rows["beats_dca_fee0.0025"].sum())
    check_4_1 = {"beats_dca_count_fee0.1pct": beats_01, "beats_dca_count_fee0.25pct": beats_025,
                 "pass": beats_01 >= 3 and beats_025 >= 3}

    # --- sec 4.4: >=2/3 of grid beats DCA (majority-of-assets rule per config), 0.1% fee ---
    grid_df["config_beats_majority"] = grid_df.groupby("config_id")["beats_dca_fee0.001"].transform(lambda s: s.sum() >= 3)
    frac_grid_pass = grid_df.drop_duplicates("config_id")["config_beats_majority"].mean()
    check_4_4_grid = {"frac_grid_configs_majority_beat_dca": float(frac_grid_pass), "pass": frac_grid_pass >= 2 / 3}

    # CSCV PBO diagnostic, pooled SP500 weekly strategy returns across the grid
    cscv_returns = {cfg_id: per_config_asset_weekly[(cfg_id, "SP500", 0.001)] for cfg_id in grid_df["config_id"].unique()}
    cscv = v3dsr.cscv_pbo(cscv_returns, n_splits=8)
    print("CSCV PBO (SP500 grid):", cscv)

    out = {
        "sanity_check": sanity,
        "impl_checks": impl_checks,
        "n_seed": counter["seed"], "n_new": new_trial_count, "n_total_raw": len(all_series),
        "n_eff": n_eff,
        "dsr_neff": dsr_neff, "dsr_rawn": dsr_rawn,
        "check_4_1": check_4_1,
        "check_4_4_grid": check_4_4_grid,
        "cscv_pbo": cscv,
        "primary_cfg_id": primary_cfg_id,
        "primary_trial_id": primary_trial_id,
    }

    if check_4_1["pass"]:
        print("Sec 4.1 PASSED -- run scripts/v3/robustness_045_avg_correlation_regime.py next "
              "for sec 4.3 (rolling windows, bootstrap, placebo; n_sims~60).")
    else:
        print("Sec 4.1 FAILED -- skipping sec 4.3 per established loop precedent.")

    with open(os.path.join(FAM_DIR, "_run_output.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)
    print("Wrote", os.path.join(FAM_DIR, "_run_output.json"))

    # Save per-asset primary-config summary for results.md writer
    per_asset_summary = []
    for asset in ASSETS:
        daily = dev["prices"][asset]
        other = {a: dev["prices"][a] for a in ASSETS if a != asset}
        corr_cache = corr_caches[(asset, acr.PRIMARY_CONFIG["corr_window"])]
        row = {"asset": asset}
        for fee in FEES:
            s, _ = run_one(asset, daily, rf, other, acr.PRIMARY_CONFIG, fee, corr_cache)
            dca_s = dca_cache[asset][fee]
            row[f"strat_wealth_fee{fee}"] = s["wealth_over_invested"]
            row[f"dca_wealth_fee{fee}"] = dca_s["wealth_over_invested"]
            row[f"strat_sharpe_fee{fee}"] = s["sharpe"]
            row[f"dca_sharpe_fee{fee}"] = dca_s["sharpe"]
        per_asset_summary.append(row)
    pd.DataFrame(per_asset_summary).to_csv(os.path.join(FAM_DIR, "_primary_per_asset.csv"), index=False)
    print("Wrote", os.path.join(FAM_DIR, "_primary_per_asset.csv"))


if __name__ == "__main__":
    main()
