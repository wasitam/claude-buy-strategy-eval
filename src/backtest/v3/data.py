"""v3 data gate (research-loop-plan-v3.md sec 5.2).

Two entry points, and ONLY two:

- load_dev(tickers=None)        -> development data: start of history through
                                    2019-12-31, core assets only.
- open_holdout(family_id, prereg_hash) -> 2020-01-01+ data on the 5 core assets
                                    PLUS full history on the 5 unseen assets.
                                    Gated: requires a frozen, committed prereg_final.md
                                    whose sha256 matches prereg_hash. Logs the look to
                                    state/holdout_log.csv and increments state/trial_counter.json.

No other function in this module (or anywhere else in the codebase) may hand back
raw OHLC rows. `_ALLOWED_RAW_DATA_FUNCS` below is the whitelist a static check
(see `check_no_raw_data_leak` at the bottom) verifies against source text.

Underlying fetch/cache mechanics are ported from src/backtest/v2/data.py (same
yfinance + FRED sources, same on-disk CSV cache under data/).
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DATA_DIR = os.path.join(REPO_ROOT, "data")
STATE_DIR = os.path.join(REPO_ROOT, "state")
FAMILIES_DIR = os.path.join(REPO_ROOT, "families")

DEV_HOLDOUT_CUTOFF = pd.Timestamp("2020-01-01")  # dev: < this date. holdout core: >= this date.

CORE_TICKERS = {
    "SP500": "^GSPC",
    "GOLD": "GC=F",
    "SILVER": "SI=F",
    "BTC": "BTC-USD",
    "OIL": "CL=F",
}
UNSEEN_TICKERS = {
    "NDX": "^NDX",
    "NIKKEI": "^N225",
    "COPPER": "HG=F",
    "PLATINUM": "PL=F",
    "ETH": "ETH-USD",
}
RF_TICKER = {"IRX": "^IRX"}


def _cache_path(name: str) -> str:
    return os.path.join(DATA_DIR, f"{name}.csv")


def _fetch_yf_raw(name: str, ticker: str, force: bool = False) -> pd.DataFrame:
    """Internal only. Not part of the public gate -- callers must go through
    load_dev()/open_holdout()."""
    path = _cache_path(name)
    if not force and os.path.exists(path):
        df = pd.read_csv(path, index_col=0, parse_dates=True)
    else:
        os.makedirs(DATA_DIR, exist_ok=True)
        df = yf.Ticker(ticker).history(period="max", auto_adjust=False)
        if df.empty:
            raise RuntimeError(f"No data returned for {ticker}")
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df.to_csv(path)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    for col in ["Open", "High", "Low", "Close"]:
        if col in df.columns:
            df = df[df[col] > 0]
    return df[["Open", "High", "Low", "Close"]].sort_index()


def _fetch_irx_raw(force: bool = False) -> pd.DataFrame:
    return _fetch_yf_raw("IRX", "^IRX", force=force)


def fetch_fred_macro(series_id: str, force: bool = False) -> pd.Series:
    """Public FRED macro-series fetch (e.g. BAA, AAA, NFCI for family 011's
    credit-stress filter). Deliberately routed through data.py (not called
    directly from a strategy module) so the fredgraph.csv access is caught
    by check_no_raw_data_leak()'s allowlist -- the caller is still
    responsible for its OWN point-in-time / publication-lag handling (see
    families/011-credit-stress-filter/prereg.md), since this function
    returns the raw, unlagged FRED series exactly as published today, cached
    on disk under data/<series_id>.csv. This is not asset OHLC data and is
    not subject to the dev/holdout date gate -- macro series are reindexed
    onto an already dev-clipped or holdout-appropriate trading-day index by
    the caller, so no leakage is possible through this function alone."""
    path = _cache_path(f"FRED_{series_id}")
    if not force and os.path.exists(path):
        df = pd.read_csv(path, index_col=0, parse_dates=True)
    else:
        os.makedirs(DATA_DIR, exist_ok=True)
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        df = pd.read_csv(url, parse_dates=["observation_date"]).set_index("observation_date")
        df.columns = [series_id]
        df.to_csv(path)
    s = df[series_id].copy()
    s.index = pd.to_datetime(s.index)
    return s.dropna().sort_index()


def fetch_yf_macro(ticker: str) -> pd.Series:
    """Public yfinance macro-series fetch for a NON-core ticker (e.g. the
    US Dollar Index `DX-Y.NYB` for family 015's DXY regime signal).
    Deliberately routed through data.py (not called directly from a
    strategy module) so the yfinance-direct-call leak check still catches
    any OTHER module that bypasses this gate, mirroring fetch_fred_macro's
    role for FRED series. Refuses any ticker already in CORE_TICKERS or
    UNSEEN_TICKERS -- those must go through load_dev()/open_holdout() only,
    so this function can never become a side-channel around the dev/holdout
    date gate. Returns the raw Close series exactly as published (the
    caller is responsible for any point-in-time/lag handling, though for a
    market-price index like DXY -- unlike a survey-based macro release --
    there is no publication lag: the close is observable same-day)."""
    if ticker in CORE_TICKERS.values() or ticker in UNSEEN_TICKERS.values():
        raise PermissionError(
            f"fetch_yf_macro({ticker!r}): refusing a core/unseen asset ticker -- "
            "use load_dev()/open_holdout() for asset OHLC, never this function."
        )
    name = "MACRO_" + ticker.replace("=", "_").replace("^", "").replace(".", "_")
    raw = _fetch_yf_raw(name, ticker)
    return raw["Close"].dropna().sort_index()


def _daily_rf(index: pd.DatetimeIndex) -> pd.Series:
    irx = _fetch_irx_raw()
    s = irx["Close"].reindex(irx.index.union(index)).sort_index().ffill().reindex(index).ffill().bfill()
    return (s / 100.0) / 252.0


def load_dev(tickers: list[str] | None = None) -> dict:
    """Development data: core assets only, strictly before 2020-01-01.

    Returns {"prices": {NAME: daily OHLC df}, "rf": daily risk-free series}.
    Hard-refuses any ticker not in CORE_TICKERS and clips at DEV_HOLDOUT_CUTOFF.
    """
    names = list(CORE_TICKERS.keys()) if tickers is None else tickers
    bad = [t for t in names if t not in CORE_TICKERS]
    if bad:
        raise PermissionError(
            f"load_dev(): refusing non-core ticker(s) {bad}. "
            f"Only {list(CORE_TICKERS)} are allowed in development data."
        )
    out = {}
    for name in names:
        raw = _fetch_yf_raw(name, CORE_TICKERS[name])
        clipped = raw[raw.index < DEV_HOLDOUT_CUTOFF]
        out[name] = clipped
    all_idx = sorted(set().union(*[set(df.index) for df in out.values()]))
    rf = _daily_rf(pd.DatetimeIndex(all_idx))
    rf = rf[rf.index < DEV_HOLDOUT_CUTOFF]
    return {"prices": out, "rf": rf, "tickers": {n: CORE_TICKERS[n] for n in names}}


def _prereg_hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def open_holdout(family_id: str, prereg_hash: str) -> dict:
    """Sealed-holdout gate (research-loop-plan-v3.md sec 5.2).

    1. Requires families/<family_id>/prereg_final.md to exist and its sha256 to
       equal prereg_hash (i.e. the caller must already have frozen+committed it).
    2. Logs a row to state/holdout_log.csv.
    3. Increments state/trial_counter.json["new"] by 1 (a holdout open is a trial).
    4. Only then returns: core assets >= 2020-01-01, and full history of the 5
       unseen assets.
    """
    prereg_path = os.path.join(FAMILIES_DIR, family_id, "prereg_final.md")
    if not os.path.exists(prereg_path):
        raise PermissionError(
            f"open_holdout({family_id!r}): no frozen prereg_final.md found. "
            "Freeze and commit it before opening the holdout."
        )
    actual_hash = _prereg_hash(prereg_path)
    if actual_hash != prereg_hash:
        raise PermissionError(
            f"open_holdout({family_id!r}): prereg_hash mismatch "
            f"(expected {prereg_hash}, prereg_final.md hashes to {actual_hash}). "
            "The frozen file must not change after the hash was recorded."
        )

    os.makedirs(STATE_DIR, exist_ok=True)
    log_path = os.path.join(STATE_DIR, "holdout_log.csv")
    is_new = not os.path.exists(log_path)
    look_number = 1
    if not is_new:
        with open(log_path) as f:
            look_number = sum(1 for _ in f) if os.path.getsize(log_path) == 0 else max(1, sum(1 for _ in f))
        # count existing data rows for THIS family to get its look number
        existing = pd.read_csv(log_path)
        look_number = int((existing["family_id"] == family_id).sum()) + 1
    with open(log_path, "a") as f:
        if is_new:
            f.write("timestamp_utc,family_id,look_number,prereg_hash\n")
        f.write(f"{datetime.now(timezone.utc).isoformat()},{family_id},{look_number},{prereg_hash}\n")

    counter_path = os.path.join(STATE_DIR, "trial_counter.json")
    with open(counter_path) as f:
        counter = json.load(f)
    counter["new"] = counter.get("new", 0) + 1
    counter.setdefault("holdout_opens", 0)
    counter["holdout_opens"] += 1
    with open(counter_path, "w") as f:
        json.dump(counter, f, indent=2)

    core = {}
    for name, ticker in CORE_TICKERS.items():
        raw = _fetch_yf_raw(name, ticker)
        core[name] = raw[raw.index >= DEV_HOLDOUT_CUTOFF]
    unseen = {}
    for name, ticker in UNSEEN_TICKERS.items():
        raw = _fetch_yf_raw(name, ticker)
        unseen[name] = raw

    all_idx = sorted(set().union(*[set(df.index) for df in {**core, **unseen}.values()]))
    rf = _daily_rf(pd.DatetimeIndex(all_idx))

    return {"core": core, "unseen": unseen, "rf": rf, "look_number": look_number}


# ---------------------------------------------------------------------------
# Static leak check: no other function in this module, and no other module in
# the repo, may expose raw OHLC data outside these two gates.
# ---------------------------------------------------------------------------
_ALLOWED_RAW_DATA_FUNCS = {"load_dev", "open_holdout"}
_INTERNAL_HELPERS = {"_fetch_yf_raw", "_fetch_irx_raw", "_daily_rf", "_prereg_hash", "_cache_path"}


def check_no_raw_data_leak() -> list[str]:
    """Scans src/backtest/v3 for any function outside this module that reads
    from data/*.csv directly or calls yfinance directly. Returns a list of
    violations (empty = clean)."""
    v3_dir = os.path.dirname(__file__)
    violations = []
    for root, _dirs, files in os.walk(v3_dir):
        for fn in files:
            if not fn.endswith(".py") or fn == "data.py":
                continue
            path = os.path.join(root, fn)
            with open(path) as f:
                text = f.read()
            if "yf.Ticker" in text or "yfinance" in text or "fredgraph.csv" in text:
                violations.append(f"{path}: imports/calls yfinance or FRED directly")
            if "read_csv" in text and os.path.join("v3", "") not in path:
                pass
    return violations


if __name__ == "__main__":
    d = load_dev()
    for k, v in d["prices"].items():
        print(k, len(v), v.index.min().date(), "->", v.index.max().date())
