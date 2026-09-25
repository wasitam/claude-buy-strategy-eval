"""Resample daily OHLC to weekly candles, and build a weekly risk-free rate series."""
from __future__ import annotations

import pandas as pd


def to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Standard weekly resample: open=first, high=max, low=min, close=last.

    Weeks are anchored on Sunday close (W-SUN -> label is the Sunday ending the week),
    which keeps week boundaries stable regardless of which weekday the series starts on.
    """
    o = df["Open"].resample("W-SUN").first()
    h = df["High"].resample("W-SUN").max()
    l = df["Low"].resample("W-SUN").min()
    c = df["Close"].resample("W-SUN").last()
    v = df["Volume"].resample("W-SUN").sum() if "Volume" in df.columns else None
    out = pd.DataFrame({"Open": o, "High": h, "Low": l, "Close": c})
    if v is not None:
        out["Volume"] = v
    out = out.dropna(subset=["Open", "High", "Low", "Close"])
    return out


def weekly_risk_free_rate(irx_daily: pd.DataFrame) -> pd.Series:
    """^IRX is quoted as an annualized discount-style yield in percent (e.g. 5.0 = 5%).

    Convert to a simple weekly compounding rate: weekly_rate = (1 + annual/100) ** (1/52) - 1.
    Returns a weekly series aligned the same way as to_weekly() (W-SUN close).
    """
    annual_pct = irx_daily["Close"].resample("W-SUN").last().ffill()
    weekly_rate = (1.0 + annual_pct / 100.0) ** (1.0 / 52.0) - 1.0
    weekly_rate.name = "weekly_rf"
    return weekly_rate
