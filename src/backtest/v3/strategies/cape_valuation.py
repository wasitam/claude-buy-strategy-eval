"""Family 008: CAPE / earnings-yield valuation sizing (Shiller; Campbell &
Shiller 1998; Asness et al.), SP500 only.

families/008-cape-valuation/prereg.md has the full mechanism, rationale,
data-reachability writeup and the SP500-only scoping decision (structural:
CAPE/earnings-yield is only defined for equities among the 5 core assets).

Mechanism: buy more SP500 when it is CHEAP relative to its own trailing
smoothed real earnings (low valuation-ratio percentile -> higher expected
forward returns, per Shiller/Campbell-Shiller/Asness et al.), buy less when
EXPENSIVE. Never sells, never leverages -- purely a bounded buy-size
multiplier applied to the existing $500/week deposit schedule, cash-capped
by the engine so cash never goes negative.

Earnings-yield proxy: Shiller's own CAPE data source (econ.yale.edu) and
every third-party mirror tried (multpl.com, data.nasdaq.com/quandl,
stooq.com, datahub.io, img1.wsimg.com) is unreachable in this environment
(direct 403 or egress-proxy policy denial -- see prereg.md "Data
reachability" for the full list). This family instead builds a
Shiller-shaped P/E10 valuation ratio from FRED's public, point-in-time
-available series (same fetch/cache mechanism v2/regimes.py already uses
for other macro data):
  - `CP` (Corporate Profits After Tax, NIPA, quarterly, nominal, 1947+) as
    the earnings-proxy input, in place of Shiller's own bottom-up S&P 500
    reported EPS series.
  - `CPIAUCSL` (CPI-U, monthly, 1947+) to convert both profits and price to
    real terms, exactly as Shiller's own CAPE construction does.
This is a documented SUBSTITUTION of the earnings series, not a change of
mechanism -- see prereg.md for the full reasoning and the point-in-time
publication-lag rules (BEA ~6mo lag for CP, BLS ~2mo lag for CPI, matching
and exceeding v2/data.py's existing weekly_fred_lagged convention).

The sizing signal only ever uses this ratio's OWN trailing point-in-time
PERCENTILE RANK (never a full-sample percentile, never Shiller's own
absolute CAPE units) -- invariant to the ratio's absolute scale, so the
earnings-series substitution above does not change what the signal
measures (a valuation LEVEL relative to the asset's own recent history).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import engine as eng
from ...v2 import data as v2data

CATEGORY = "Sizing / valuation"

CP_RELEASE_LAG_MONTHS = 6   # conservative: ~3mo after quarter-end (BEA corporate-profits lag)
CPI_RELEASE_LAG_MONTHS = 2  # matches v2/data.py's weekly_fred_lagged convention exactly
TRAILING_EARNINGS_QUARTERS = 40  # 10 years, Shiller's own CAPE smoothing window


def _lagged_daily(series: pd.Series, lag_months: int, daily_index: pd.DatetimeIndex) -> pd.Series:
    """Point-in-time: an observation dated d is usable from the first day of
    the month `lag_months` after d, forward-filled onto daily_index. Mirrors
    v2/data.py's weekly_fred_lagged exactly, generalized to any lag and any
    daily target index (not just weekly Fridays)."""
    s = series.copy()
    s.index = pd.to_datetime(s.index)
    s = s[~s.index.duplicated(keep="last")].sort_index()
    available_from = (s.index + pd.DateOffset(months=lag_months)).map(lambda d: d.replace(day=1))
    avail = pd.Series(s.to_numpy(), index=available_from)
    avail = avail[~avail.index.duplicated(keep="last")].sort_index()
    full_daily_idx = pd.date_range(avail.index.min(), daily_index.max(), freq="D")
    daily = avail.reindex(full_daily_idx).ffill()
    return daily.reindex(daily_index, method="ffill")


def build_pit_valuation_ratio(daily_close: pd.Series) -> pd.Series:
    """Real SP500 price / trailing-10-year average REAL corporate profits,
    both using only data available point-in-time as of each day (prereg.md
    "Point-in-time discipline"). NOT Shiller's literal CAPE units (different
    earnings series) -- a P/E10-shaped valuation LEVEL whose only use here
    is its own point-in-time PERCENTILE RANK (build_pit_percentile below)."""
    cp = v2data.fetch_fred("CP")["CP"].copy()
    cpi = v2data.fetch_fred("CPIAUCSL")["CPIAUCSL"].copy()
    cp.index = pd.to_datetime(cp.index)
    cpi.index = pd.to_datetime(cpi.index)
    cp = cp[~cp.index.duplicated(keep="last")].sort_index()
    cpi = cpi[~cpi.index.duplicated(keep="last")].sort_index()

    idx = daily_close.index

    # CPI "as of day t" (point-in-time, 2-month release lag) -- deflates
    # today's price to real terms.
    cpi_pit_daily = _lagged_daily(cpi, CPI_RELEASE_LAG_MONTHS, idx)

    # Real quarterly corporate profits, deflated by EACH quarter's OWN
    # contemporaneous CPI. CPI's 2-month lag always clears well before CP's
    # own 6-month lag, so by the time a quarter's CP figure is usable at
    # all, that quarter's CPI is already known -- no extra gating needed.
    cpi_quarterly = cpi.resample("QS").mean()
    cpi_q = cpi_quarterly.reindex(cp.index, method="nearest")
    real_cp_q = cp / cpi_q  # real corporate profits, constant "1 CPI-index-point" units

    # Trailing 10-year (40-quarter) average of real profits, computed on the
    # quarterly series itself, then release-lagged as a whole (keyed off its
    # own date index, i.e. the quarter each rolling-average row ends on).
    real_cp_10y_avg_q = real_cp_q.rolling(TRAILING_EARNINGS_QUARTERS, min_periods=TRAILING_EARNINGS_QUARTERS).mean()
    real_cp_10y_avg_pit_daily = _lagged_daily(real_cp_10y_avg_q.dropna(), CP_RELEASE_LAG_MONTHS, idx)

    real_price_daily = daily_close / cpi_pit_daily

    ratio = real_price_daily / real_cp_10y_avg_pit_daily
    return ratio


def build_pit_percentile(ratio: pd.Series, window_years: int) -> pd.Series:
    """Trailing (never centered/forward-looking) point-in-time percentile
    rank of `ratio` within a `window_years`-long window ending at each day
    (inclusive). pandas' rolling().rank() only ever looks backward from each
    row, which is exactly the point-in-time property this family's signal
    requires (prereg.md "Point-in-time discipline")."""
    window_days = int(round(window_years * 252))
    min_periods = max(504, window_days // 4)  # need >=2 years of ratio history before any signal
    pct = ratio.rolling(window_days, min_periods=min_periods).rank(pct=True) * 100.0
    return pct


def _mult_for(p: float, low_pctile: float, high_pctile: float, max_mult: float, min_mult: float) -> float:
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return 1.0  # signal not yet computable -> behave exactly like plain DCA (pre-registered fallback)
    if p <= low_pctile:
        return max_mult
    if p >= high_pctile:
        return min_mult
    frac = (p - low_pctile) / (high_pctile - low_pctile)
    return max_mult + frac * (min_mult - max_mult)


def make_cape_decider(
    daily: pd.DataFrame, weekly_deposit: float, pctile: pd.Series | None,
    low_pctile: float = 20.0, high_pctile: float = 80.0,
    max_mult: float = 2.0, min_mult: float = 0.5,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: bypasses the valuation/percentile/multiplier
    computation entirely and buys the full week's cash every week-end day
    (0 otherwise), bit-for-bit plain DCA."""
    is_week_end = eng.week_end_flags(daily.index)
    pct_arr = pctile.reindex(daily.index).to_numpy() if (enabled and pctile is not None) else None

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        p = pct_arr[t] if pct_arr is not None else None
        m = _mult_for(p, low_pctile, high_pctile, max_mult, min_mult)
        target_buy_usd = min(cash, m * weekly_deposit)
        return target_buy_usd, 0.0, {"pctile": None if p is None or np.isnan(p) else float(p), "mult": m}

    return decide


CATEGORY = "Sizing / valuation"

# Grid: pctile_window_years x low_pctile x high_pctile x max_mult x min_mult
# = 2x2x2x2x2 = 32 (<=36 cap; 5 params <=5, at the parameter cap).
GRID = {
    "pctile_window_years": [15, 20],
    "low_pctile": [20, 30],
    "high_pctile": [70, 80],
    "max_mult": [1.5, 2.0],
    "min_mult": [0.3, 0.5],
}
PRIMARY_CONFIG = {
    "pctile_window_years": 20, "low_pctile": 20, "high_pctile": 80,
    "max_mult": 2.0, "min_mult": 0.5,
}


def grid_configs() -> list[dict]:
    out = []
    for wy in GRID["pctile_window_years"]:
        for lo in GRID["low_pctile"]:
            for hi in GRID["high_pctile"]:
                for mx in GRID["max_mult"]:
                    for mn in GRID["min_mult"]:
                        out.append({
                            "pctile_window_years": wy, "low_pctile": lo, "high_pctile": hi,
                            "max_mult": mx, "min_mult": mn,
                        })
    return out
