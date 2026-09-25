"""Generic indicator -> percentile-of-own-trailing-distribution signal engine.

Design goal (per spec section 3.2): build ONE generic engine that turns any
causal indicator series into buy/sell dates by ranking each value against its
own trailing history, so new indicators can be plugged in without touching
the backtest engine.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRAILING_WINDOW = 104  # ~2 years of weekly candles


def atr(weekly: pd.DataFrame, n: int = 14) -> pd.Series:
    """Causal weekly Average True Range (simple rolling mean of True Range)."""
    high, low, close = weekly["High"], weekly["Low"], weekly["Close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(n, min_periods=n).mean()


def moving_average(close: pd.Series, n: int = 40) -> pd.Series:
    return close.rolling(n, min_periods=n).mean()


def trailing_percentile_rank(values: pd.Series, window: int = TRAILING_WINDOW) -> pd.Series:
    """For each t, rank values[t] against the trailing `window` (expanding until
    that much history exists), as a percentile in [0, 100]. Purely causal: the
    window at t is values[t-window+1 : t+1] (never future data).

    Uses the 'weak' definition: percentile = 100 * (# of values in window <= value[t]) / n_window,
    so a genuinely lowest value in a full window gets 100/window (never exactly 0),
    and the highest gets 100.

    Vectorized: the expanding warm-up phase (t < window-1) uses a small python
    loop; once the window is full it uses a sliding_window_view + broadcasted
    comparison, which is O(n*window) but done in C rather than pure Python --
    this matters because the robustness tests call this thousands of times.
    """
    arr = values.to_numpy(dtype=float)
    n = len(arr)
    out = np.full(n, np.nan)

    warmup_end = min(window - 1, n)
    for t in range(warmup_end):
        if np.isnan(arr[t]):
            continue
        win = arr[: t + 1]
        win = win[~np.isnan(win)]
        if len(win) == 0:
            continue
        out[t] = 100.0 * np.sum(win <= arr[t]) / len(win)

    if n >= window:
        windows = np.lib.stride_tricks.sliding_window_view(arr, window)  # (n-window+1, window)
        last = windows[:, -1]
        with np.errstate(invalid="ignore"):
            counts = np.sum(windows <= last[:, None], axis=1)
        out[window - 1 :] = 100.0 * counts / window
        out[window - 1 :][np.isnan(last)] = np.nan

    return pd.Series(out, index=values.index, name=f"{values.name}_pctile")


def signal_a_shock(weekly: pd.DataFrame, atr_n: int = 14, window: int = TRAILING_WINDOW) -> pd.Series:
    """Normalized weekly move: (close[t] - close[t-1]) / ATR_14w[t-1].

    Uses the PREVIOUS week's ATR so the crash candle itself can't inflate the
    threshold that is supposed to catch it (spec section 3.2, Signal A).
    """
    close = weekly["Close"]
    atr_series = atr(weekly, atr_n)
    normalized_move = (close - close.shift(1)) / atr_series.shift(1)
    normalized_move.name = "signal_a"
    return normalized_move


def signal_b_trend_stretch(weekly: pd.DataFrame, ma_n: int = 40, atr_n: int = 14) -> pd.Series:
    """Distance from the ~200-day (40-week) moving average, in ATR units.

    (close[t] - MA_40w[t]) / ATR_14w[t]  (spec section 3.2, Signal B).
    """
    close = weekly["Close"]
    ma = moving_average(close, ma_n)
    atr_series = atr(weekly, atr_n)
    distance = (close - ma) / atr_series
    distance.name = "signal_b"
    return distance


def percentile_signal_to_trades(
    indicator: pd.Series, p: float, window: int = TRAILING_WINDOW
) -> tuple[pd.Series, pd.Series]:
    """Generic engine: indicator series in -> (buy_bool, sell_bool) out.

    Buy when indicator ranks in the bottom p% of its trailing distribution.
    Sell when indicator ranks in the top p%.
    Both series are boolean, indexed the same as `indicator`.
    """
    pctile = trailing_percentile_rank(indicator, window=window)
    buy = pctile <= p
    sell = pctile >= (100.0 - p)
    buy = buy.fillna(False)
    sell = sell.fillna(False)
    return buy, sell
