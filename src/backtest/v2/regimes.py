"""Rate-regime signals for Strategy D (spec v2.1 section 15).

Data note on R4 (dot plot): ALFRED's vintage list for FEDTARMD only goes
back to 2015-12-16 in practice (checked live against the ALFRED download
page's actual vintage dropdown), not to Jan 2012 as the spec's data table
assumed. R4's usable sample is therefore ~2016+, not 2012+. This is a real
data-availability constraint, not a design choice -- documented again in
the report.
"""
from __future__ import annotations

import os
import re
import time

import numpy as np
import pandas as pd
import requests

from . import data as d2

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")


# ---------------------------------------------------------------------------
# Data fetch
# ---------------------------------------------------------------------------

def fetch_fed_target_midpoint(force: bool = False) -> pd.Series:
    """Daily Fed funds target midpoint: DFEDTAR until 2008-12-15, then the
    midpoint of DFEDTARU/DFEDTARL (spec 15.2)."""
    tar = d2.fetch_fred("DFEDTAR", force=force)["DFEDTAR"]
    upper = d2.fetch_fred("DFEDTARU", force=force)["DFEDTARU"]
    lower = d2.fetch_fred("DFEDTARL", force=force)["DFEDTARL"]
    tar.index = pd.to_datetime(tar.index)
    upper.index = pd.to_datetime(upper.index)
    lower.index = pd.to_datetime(lower.index)
    midpoint_range = (upper + lower) / 2.0
    switch_date = pd.Timestamp("2008-12-16")
    combined = pd.concat([tar[tar.index < switch_date], midpoint_range[midpoint_range.index >= switch_date]])
    return combined.sort_index().dropna()


def fetch_alfred_vintage_dates(force: bool = False) -> list[str]:
    path = os.path.join(DATA_DIR, "FEDTARMD_vintage_dates.txt")
    if not force and os.path.exists(path):
        return [l.strip() for l in open(path) if l.strip()]
    resp = requests.get("https://alfred.stlouisfed.org/series/downloaddata?seid=FEDTARMD", timeout=30)
    dates = sorted(set(re.findall(r'option value="(20\d\d-\d\d-\d\d)"', resp.text)))
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(dates))
    return dates


def fetch_alfred_vintage(vintage_date: str, force: bool = False) -> pd.Series | None:
    """One dot-plot vintage: index = projection year-end (Jan 1), values = median."""
    path = os.path.join(DATA_DIR, f"FEDTARMD_vintage_{vintage_date}.csv")
    if not force and os.path.exists(path):
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        return df.iloc[:, 0] if len(df) else None
    url = f"https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=FEDTARMD&vintage_date={vintage_date}"
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        return None
    from io import StringIO
    df = pd.read_csv(StringIO(resp.text), parse_dates=["observation_date"]).set_index("observation_date")
    df.to_csv(path)
    return df.iloc[:, 0] if len(df) else None


def build_dotplot_pointintime_series(index: pd.DatetimeIndex, force: bool = False) -> pd.Series:
    """For each week t, the median projection for the NEXT calendar year-end,
    from the latest vintage released strictly before week t's Friday close
    (spec: 'usable from the trading day after its release')."""
    vintage_dates = fetch_alfred_vintage_dates(force=force)
    vintages = []
    for vd in vintage_dates:
        s = fetch_alfred_vintage(vd, force=force)
        if s is not None:
            vintages.append((pd.Timestamp(vd), s))
    vintages.sort(key=lambda x: x[0])

    out = pd.Series(np.nan, index=index)
    for t in index:
        usable = [(rd, s) for rd, s in vintages if rd < t]
        if not usable:
            continue
        release_date, s = usable[-1]  # latest usable vintage
        target_year_end = pd.Timestamp(year=t.year + 1, month=1, day=1)
        if target_year_end in s.index:
            out[t] = s[target_year_end]
    return out.ffill()


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

def anti_whipsaw(raw_bool: pd.Series, confirm_weeks: int = 2) -> pd.Series:
    """Only flip state after `confirm_weeks` consecutive weeks of the new
    reading (spec 15.3)."""
    raw = raw_bool.to_numpy()
    n = len(raw)
    out = np.zeros(n, dtype=bool)
    state = raw[0] if n else False
    run_val = raw[0] if n else False
    run_len = 1
    out[0] = state
    for t in range(1, n):
        if raw[t] == run_val:
            run_len += 1
        else:
            run_val = raw[t]
            run_len = 1
        if run_val != state and run_len >= confirm_weeks:
            state = run_val
        out[t] = state
    return pd.Series(out, index=raw_bool.index)


def build_all_signals(index: pd.DatetimeIndex, raw: dict, confirm_weeks: int = 2) -> dict[str, pd.Series]:
    """Builds R1, R2a, R2b, R2b-inv, R2c, R3, R4, Combo -- each forward-filled
    onto `index`, anti-whipsaw smoothed, and boolean (True = TIGHT)."""
    target_mid = fetch_fed_target_midpoint().reindex(
        pd.date_range(index.min() - pd.Timedelta(weeks=30), index.max(), freq="D")
    ).ffill()
    target_mid_w = target_mid.reindex(index, method="ffill")

    dgs2 = raw["DGS2"]["DGS2"].reindex(pd.date_range(index.min() - pd.Timedelta(weeks=30), index.max(), freq="D")).ffill()
    dgs2_w = dgs2.reindex(index, method="ffill")

    slope = raw["T10Y2Y"]["T10Y2Y"].reindex(pd.date_range(index.min() - pd.Timedelta(weeks=30), index.max(), freq="D")).ffill()
    slope_w = slope.reindex(index, method="ffill")

    dfii10 = raw["DFII10"]["DFII10"].reindex(pd.date_range(index.min() - pd.Timedelta(weeks=30), index.max(), freq="D")).ffill()
    dfii10_w = dfii10.reindex(index, method="ffill")

    # R1: target midpoint at t > target midpoint 26 weeks earlier
    r1_raw = target_mid_w > target_mid_w.shift(26)
    # R2a: 2yr yield above its own trailing-26w mean
    r2a_raw = dgs2_w > dgs2_w.rolling(26, min_periods=26).mean()
    # R2b: curve slope below its own trailing-26w mean (flattening)
    r2b_raw = slope_w < slope_w.rolling(26, min_periods=26).mean()
    # R2b-inv: inverted curve
    r2binv_raw = slope_w < 0
    # R2c: bear flattening = R2a AND R2b (on the RAW pre-whipsaw readings, per spec's literal AND)
    r2c_raw = r2a_raw & r2b_raw
    # R3: real yield above its own trailing-26w mean
    r3_raw = dfii10_w > dfii10_w.rolling(26, min_periods=26).mean()

    r1 = anti_whipsaw(r1_raw.fillna(False), confirm_weeks)
    r2a = anti_whipsaw(r2a_raw.fillna(False), confirm_weeks)
    r2b = anti_whipsaw(r2b_raw.fillna(False), confirm_weeks)
    r2binv = anti_whipsaw(r2binv_raw.fillna(False), confirm_weeks)
    r2c = anti_whipsaw(r2c_raw.fillna(False), confirm_weeks)
    r3 = anti_whipsaw(r3_raw.fillna(False), confirm_weeks)

    combo_raw = (r1_raw.fillna(False).astype(int) + r2a_raw.fillna(False).astype(int)
                 + r2b_raw.fillna(False).astype(int) + r3_raw.fillna(False).astype(int)) >= 3
    combo = anti_whipsaw(combo_raw, confirm_weeks)

    out = {
        "R1": r1, "R2a": r2a, "R2b": r2b, "R2b-inv": r2binv, "R2c": r2c,
        "R3": r3, "Combo": combo,
    }

    dot = build_dotplot_pointintime_series(index)
    r4_raw = (dot > target_mid_w).reindex(index).fillna(False)
    r4_valid_from = dot.first_valid_index()
    r4 = anti_whipsaw(r4_raw, confirm_weeks)
    out["R4"] = r4
    out["R4_valid_from"] = r4_valid_from

    return out


def control_signal(weekly_close: pd.Series, confirm_weeks: int = 2) -> pd.Series:
    """Control: asset's own 26-week log return < 0 (spec 15.3)."""
    log_ret_26w = np.log(weekly_close) - np.log(weekly_close.shift(26))
    raw = (log_ret_26w < 0).fillna(False)
    return anti_whipsaw(raw, confirm_weeks)


# ---------------------------------------------------------------------------
# Fed cycle detection (spec 15.7)
# ---------------------------------------------------------------------------

def detect_fed_cycles(target_mid_weekly: pd.Series, hold_threshold_weeks: int = 26) -> pd.DataFrame:
    """Heuristic cycle detection from the Fed funds target midpoint series:
    group consecutive weekly moves of the same sign into hike/ease cycles;
    a flat stretch longer than `hold_threshold_weeks` between moves becomes
    its own 'hold' cycle. This is a simplification of 'derive from data,
    don't hard-code' -- documented in the report."""
    delta = target_mid_weekly.diff().fillna(0.0)
    moves = delta[delta.abs() > 1e-9]  # weeks where the target actually changed
    if len(moves) == 0:
        return pd.DataFrame(columns=["type", "start", "end"])

    rows = []
    cur_type = "hike" if moves.iloc[0] > 0 else "ease"
    cur_start = moves.index[0]
    last_move_date = moves.index[0]
    for date, d in moves.iloc[1:].items():
        this_type = "hike" if d > 0 else "ease"
        gap_weeks = (date - last_move_date).days / 7.0
        if this_type != cur_type or gap_weeks > hold_threshold_weeks:
            rows.append({"type": cur_type, "start": cur_start, "end": last_move_date})
            if gap_weeks > hold_threshold_weeks:
                rows.append({"type": "hold", "start": last_move_date, "end": date})
            cur_type = this_type
            cur_start = date
        last_move_date = date
    rows.append({"type": cur_type, "start": cur_start, "end": last_move_date})

    df = pd.DataFrame(rows)
    # extend each cycle's end to just before the next cycle's start (so cycles tile the timeline)
    df["end"] = df["start"].shift(-1).fillna(target_mid_weekly.index.max())
    return df
