"""Fetch and cache daily OHLC data from Yahoo Finance via yfinance."""
from __future__ import annotations

import os
import pandas as pd
import yfinance as yf

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

TICKERS = {
    "BTC": "BTC-USD",
    "GOLD": "GC=F",
    "SILVER": "SI=F",
    "IRX": "^IRX",
}


def _cache_path(name: str) -> str:
    return os.path.join(DATA_DIR, f"{name}.csv")


def fetch_ticker(name: str, ticker: str, force: bool = False) -> pd.DataFrame:
    path = _cache_path(name)
    if not force and os.path.exists(path):
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        return df
    os.makedirs(DATA_DIR, exist_ok=True)
    df = yf.Ticker(ticker).history(period="max", auto_adjust=False)
    if df.empty:
        raise RuntimeError(f"No data returned for {ticker}")
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.to_csv(path)
    return df


def fetch_all(force: bool = False) -> dict[str, pd.DataFrame]:
    out = {}
    for name, ticker in TICKERS.items():
        out[name] = fetch_ticker(name, ticker, force=force)
        print(f"{name} ({ticker}): {len(out[name])} rows, "
              f"{out[name].index.min().date()} -> {out[name].index.max().date()}")
    return out


if __name__ == "__main__":
    fetch_all(force=True)
