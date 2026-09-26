"""Documentation/inspection helper only: writes a CSV of the
reconstructed ISM Manufacturing PMI monthly series a reviewer can open
directly, without running Python. NOT used by
src/backtest/v3/strategies/ism_pmi_regime.py or by
scripts/v3/run_052_ism_pmi_regime.py -- the single source of truth for
the ANCHORS list and the interpolation method is
src.backtest.v3.strategies.ism_pmi_regime.fetch_raw_signal(). This script
just calls that function and writes its output next to
families/052-ism-pmi-regime/ (NOT under data/, since data/*.csv is
gitignored as a live-fetch cache directory in this repo, and this is
deliberately not a live fetch -- see ism_pmi_regime.py's module
docstring and prereg.md "Required step 1" for the full disclosure of why
this series is hard-coded rather than downloaded).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.backtest.v3.strategies import ism_pmi_regime as ism

OUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "families", "052-ism-pmi-regime", "ISM_PMI_reconstructed_for_review.csv",
)


def main():
    monthly = ism.fetch_raw_signal()
    out = monthly.reset_index()
    out.columns = ["observation_date", "ISM_PMI_reconstructed"]
    out.to_csv(OUT_PATH, index=False)
    print(f"Wrote {OUT_PATH}: {len(out)} monthly rows, "
          f"{out['observation_date'].min()} .. {out['observation_date'].max()}")


if __name__ == "__main__":
    main()
