"""Fetch and cache data for v2: BTC/gold/silver/IRX/VIX from Yahoo Finance,
UNRATE/TCU from FRED, and resample everything to W-FRI weekly candles.
"""
from __future__ import annotations

import os
import pandas as pd
import numpy as np
import yfinance as yf

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")

YF_TICKERS = {
    "BTC": "BTC-USD",
    "GOLD": "GC=F",
    "SILVER": "SI=F",
    "IRX": "^IRX",
    "VIX": "^VIX",
}
FRED_SERIES = ["UNRATE", "TCU"]


def _cache_path(name: str) -> str:
    return os.path.join(DATA_DIR, f"{name}.csv")


def fetch_yf(name: str, ticker: str, force: bool = False) -> pd.DataFrame:
    path = _cache_path(name)
    if not force and os.path.exists(path):
        return pd.read_csv(path, index_col=0, parse_dates=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    df = yf.Ticker(ticker).history(period="max", auto_adjust=False)
    if df.empty:
        raise RuntimeError(f"No data returned for {ticker}")
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.to_csv(path)
    return df


def fetch_fred(series_id: str, force: bool = False) -> pd.DataFrame:
    path = _cache_path(series_id)
    if not force and os.path.exists(path):
        return pd.read_csv(path, index_col=0, parse_dates=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(url, parse_dates=["observation_date"]).set_index("observation_date")
    df.columns = [series_id]
    df.to_csv(path)
    return df


def fetch_all(force: bool = False) -> dict[str, pd.DataFrame]:
    out = {}
    for name, ticker in YF_TICKERS.items():
        out[name] = fetch_yf(name, ticker, force=force)
        print(f"{name} ({ticker}): {len(out[name])} rows, "
              f"{out[name].index.min().date()} -> {out[name].index.max().date()}")
    for series_id in FRED_SERIES:
        df = fetch_fred(series_id, force=force)
        df = df[df[series_id].notna()]
        out[series_id] = df
        print(f"{series_id} (FRED): {len(df)} rows, {df.index.min().date()} -> {df.index.max().date()}")
    return out


def clean_ohlc(df: pd.DataFrame, max_weekly_move: float | None = None) -> pd.DataFrame:
    """Drop non-positive prices (data hygiene, spec 3)."""
    df = df.copy()
    for col in ["Open", "High", "Low", "Close"]:
        if col in df.columns:
            df = df[df[col] > 0]
    return df


def to_weekly_wfri(df: pd.DataFrame) -> pd.DataFrame:
    """Resample daily OHLC to W-FRI weekly candles (spec 2.3): open=first, high=max,
    low=min, close=last. BTC weekend bars fall into the following week's Friday-ending
    bucket, which is fine as long as every series uses the same rule."""
    o = df["Open"].resample("W-FRI").first()
    h = df["High"].resample("W-FRI").max()
    l = df["Low"].resample("W-FRI").min()
    c = df["Close"].resample("W-FRI").last()
    out = pd.DataFrame({"Open": o, "High": h, "Low": l, "Close": c}).dropna()
    return out


def flag_bad_ticks(weekly: pd.DataFrame, threshold: float = 0.50) -> pd.Series:
    """Flag weeks with a >threshold close-to-close move for manual inspection
    (spec 3, data hygiene -- Yahoo futures data occasionally has bad ticks)."""
    move = weekly["Close"].pct_change().abs()
    return move > threshold


def weekly_rf_rate(irx_daily: pd.DataFrame, index: pd.DatetimeIndex) -> pd.Series:
    """rf_weekly = IRX/100/52 (spec 8.2), using the latest ^IRX close, forward-filled."""
    irx_weekly = irx_daily["Close"].resample("W-FRI").last()
    irx_aligned = irx_weekly.reindex(index).ffill().bfill()
    return (irx_aligned / 100.0) / 52.0


def weekly_vix(vix_daily: pd.DataFrame, index: pd.DatetimeIndex) -> pd.Series:
    v = vix_daily["Close"].resample("W-FRI").last()
    return v.reindex(index).ffill()


def weekly_fred_lagged(fred_df: pd.DataFrame, series_id: str, index: pd.DatetimeIndex) -> pd.Series:
    """FRED publication lag (no lookahead, spec 3): a monthly value for month M is
    treated as available from the first day of month M+2, then forward-filled to
    weekly."""
    s = fred_df[series_id].copy()
    s.index = pd.to_datetime(s.index)
    available_from = s.index + pd.DateOffset(months=2)
    available_from = available_from.map(lambda d: d.replace(day=1))
    avail_series = pd.Series(s.values, index=available_from).sort_index()
    # reindex onto a daily grid first so ffill onto arbitrary weekly Fridays is correct
    daily_index = pd.date_range(avail_series.index.min(), index.max(), freq="D")
    daily = avail_series.reindex(daily_index).ffill()
    return daily.reindex(index, method="ffill")


if __name__ == "__main__":
    fetch_all(force=True)
