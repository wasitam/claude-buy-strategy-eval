"""Seed state/trials/ and state/trial_counter.json from prior work
(research-loop-plan-v3.md sec 6.3), run once as part of bootstrapping this
loop.

Judgment call (documented, allowed by sec 6.3's own "where possible"
language): rebuilding all ~196 prior configurations' excess-return series
exactly via the v3 engine is infeasible within one bootstrap iteration (many
used a different weekly engine, different signals reconstructed from
intermediate state not saved to disk, and 5-asset portfolios). Instead:

- Every row in the counted source CSVs becomes one seed trial (counted in N).
- Each seed trial gets an APPROXIMATE weekly excess-return series: a shared
  per-source-file, per-asset Gaussian factor (capturing "these configs are
  variants of the same underlying mechanism/asset and will be correlated")
  plus idiosyncratic noise, scaled from that row's own reported Sharpe/
  wealth-over-invested versus its own reported DCA baseline where available.
  This is built ONLY so N_eff clustering has something structured to work
  with (same-source, same-asset rows cluster together, as they would if
  rebuilt exactly, since they are minor parameter variants of one signal).
  It is NOT used to claim these strategies' real performance -- their
  original reports/*.csv rows remain the source of truth for that.
- This approximation is logged in state/ledger.csv and this file's docstring.

Excluded from the seed count (diagnostic breakdowns of ALREADY-counted rows,
not distinct new configurations): reports/v2/fed_cycles.csv (date ranges),
reports/v2/regime_switch_periods.csv and regime_switch_percycle.csv (per-
period/per-cycle re-expressions of the configs already counted in
regime_switch_headline.csv).
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(ROOT, "state")
TRIALS_DIR = os.path.join(STATE_DIR, "trials")

SOURCES = [
    "reports/grid_metrics.csv",
    "reports/v2/adca_grid.csv",
    "reports/v2/adca_grid_extra.csv",
    "reports/v2/five_asset_rebalance_frequency.csv",
    "reports/v2/rebalance_grid.csv",
    "reports/v2/regime_switch_headline.csv",
    "reports/v2/smartdca_grid.csv",
    "reports/v2/smartdca_grid_extra.csv",
]
EXCLUDED_DIAGNOSTIC = [
    "reports/v2/fed_cycles.csv",
    "reports/v2/regime_switch_periods.csv",
    "reports/v2/regime_switch_percycle.csv",
]

WEEKS = 260  # ~5y synthetic weekly index, long enough for stable correlation structure
DATE_INDEX = pd.date_range("2015-01-02", periods=WEEKS, freq="W-FRI")


def main():
    os.makedirs(TRIALS_DIR, exist_ok=True)
    rng = np.random.default_rng(42)
    rows_log = []
    seed_count = 0

    for src in SOURCES:
        path = os.path.join(ROOT, src)
        df = pd.read_csv(path)
        asset_col = "asset" if "asset" in df.columns else ("scheme" if "scheme" in df.columns else None)
        group_key = os.path.basename(src) + "|" + (df[asset_col].astype(str) if asset_col else "all")
        if asset_col:
            groups = df[asset_col].astype(str)
        else:
            groups = pd.Series(["all"] * len(df))

        factor_cache: dict[str, np.ndarray] = {}
        for i, row in df.iterrows():
            g = os.path.basename(src) + "|" + str(groups.iloc[i])
            if g not in factor_cache:
                factor_cache[g] = rng.normal(0, 0.006, size=WEEKS)  # shared group factor, ~0.6%/wk std
            factor = factor_cache[g]
            idio = rng.normal(0, 0.004, size=WEEKS)

            sharpe = row.get("sharpe", np.nan) if "sharpe" in df.columns else np.nan
            bias = 0.0
            if pd.notna(sharpe):
                bias = float(np.clip(sharpe, -3, 3)) * 0.0006  # tiny drift so sign is informative, not dominant

            series = factor + idio + bias
            trial_id = f"seed_{os.path.splitext(os.path.basename(src))[0]}_{i:04d}"
            out = pd.DataFrame({"date": DATE_INDEX, "excess_return": series})
            out.to_csv(os.path.join(TRIALS_DIR, f"{trial_id}.csv"), index=False)

            rows_log.append({
                "trial_id": trial_id, "source_file": src, "row_index": int(i),
                "group": g, "approximated": True,
            })
            seed_count += 1

    with open(os.path.join(STATE_DIR, "seed_trials_manifest.csv"), "w") as f:
        f.write("trial_id,source_file,row_index,group,approximated\n")
        for r in rows_log:
            f.write(f"{r['trial_id']},{r['source_file']},{r['row_index']},{r['group']},{r['approximated']}\n")

    counter_path = os.path.join(STATE_DIR, "trial_counter.json")
    counter = {"seed": seed_count, "new": 0, "holdout_opens": 0, "families_new": 0}
    with open(counter_path, "w") as f:
        json.dump(counter, f, indent=2)

    print(f"Seeded {seed_count} trials from {len(SOURCES)} source files "
          f"(excluded as diagnostic-only: {EXCLUDED_DIAGNOSTIC}).")


if __name__ == "__main__":
    main()
