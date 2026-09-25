"""Family 024: SAD (Seasonal Affective Disorder) / daylight-length deposit
timing (Kamstra, Kramer & Levi 2003, "Winter Blues: A SAD Stock Market
Cycle").

families/024-sad-daylight/prereg.md has the full mechanism, sign
interpretation and rules. Summary: a purely calendar-based execution-timing
shift within a fixed $500/week deposit schedule, driven by a CONTINUOUS
solstice-based astronomical daylight-length function (fixed reference
latitude 40N) -- distinct from family 018's DISCRETE binary Nov-Apr/May-Oct
window. The signal peaks (maximal "buy less/bank" tilt) exactly at the
winter solstice and troughs (maximal "buy more" tilt) exactly at the summer
solstice, per KKL's finding that realized returns are relatively low in
fall (as days shorten toward the winter solstice) and relatively high in
winter/spring (as days lengthen away from it).

  buy_usd(t) = min(cash, max_lump_multiple * weekly_deposit,
                    mult(t) * weekly_deposit)

Never sells. No price or macro data used in the signal -- only the asset's
own trading-day calendar (calendar date), known in advance like any real
calendar.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import engine as eng

REFERENCE_LATITUDE_DEG = 40.0  # fixed, not tunable -- see prereg.md


def daylight_hours(index: pd.DatetimeIndex, latitude_deg: float = REFERENCE_LATITUDE_DEG) -> np.ndarray:
    """Hours of daylight at `latitude_deg` on each date in `index`, via the
    standard solstice-based astronomical approximation (solar declination
    + sunrise-hour-angle formula). Not exact to the minute (omits the
    equation of time and atmospheric refraction) but smooth, correctly
    signed, and accurate to within a few minutes of true daylight length --
    sufficient for a continuous timing signal. See prereg.md's spot-check
    values (Dec 21 ~9.16h, Jun 21 ~14.84h, equinoxes ~11.90h at 40N)."""
    doy = pd.DatetimeIndex(index).dayofyear.to_numpy().astype(float)
    decl_deg = -23.44 * np.cos(np.radians(360.0 / 365.0 * (doy + 10.0)))
    lat = np.radians(latitude_deg)
    decl = np.radians(decl_deg)
    cos_h = -np.tan(lat) * np.tan(decl)
    cos_h = np.clip(cos_h, -1.0, 1.0)
    H = np.arccos(cos_h)  # radians, half-day hour angle
    return 24.0 * H / np.pi


def _solstice_daylight_bounds(latitude_deg: float = REFERENCE_LATITUDE_DEG) -> tuple[float, float]:
    """D_min (winter solstice, Dec 21) and D_max (summer solstice, Jun 21)
    at the given latitude, from the same formula -- used to normalize the
    signal. Latitude-independent choice of solstice dates (Dec 21 = doy
    355, Jun 21 = doy 172); a leap-year-agnostic reference year is used
    since the formula only depends on day-of-year."""
    ref_dates = pd.to_datetime(["2001-06-21", "2001-12-21"])
    d_summer, d_winter = daylight_hours(ref_dates, latitude_deg)
    return float(d_winter), float(d_summer)  # (D_min, D_max)


def compute_sad_multiplier(
    daily: pd.DataFrame, tilt_strength: float, power: float,
    latitude_deg: float = REFERENCE_LATITUDE_DEG,
) -> np.ndarray:
    """mult(t) = 1 - tilt_strength * sign(S(t)) * |S(t)|^power, where
    S(t) in [-1, +1] is the normalized daylight signal: S=+1 exactly at the
    winter solstice (shortest day -> maximal buy-less/bank tilt), S=-1
    exactly at the summer solstice (longest day -> maximal buy-more
    tilt)."""
    D = daylight_hours(daily.index, latitude_deg)
    D_min, D_max = _solstice_daylight_bounds(latitude_deg)
    D_mid = (D_max + D_min) / 2.0
    half_range = (D_max - D_min) / 2.0
    S = (D_mid - D) / half_range
    S = np.clip(S, -1.0, 1.0)
    S_shaped = np.sign(S) * np.abs(S) ** power
    mult = 1.0 - tilt_strength * S_shaped
    return mult


def make_sad_daylight_decider(
    daily: pd.DataFrame, weekly_deposit: float,
    tilt_strength: float = 0.5, power: float = 1.0, max_lump_multiple: float = 8.0,
    latitude_deg: float = REFERENCE_LATITUDE_DEG,
    enabled: bool = True,
):
    """enabled=False is the degenerate/disable path used ONLY by the
    implementation check: it bypasses the daylight computation entirely
    and buys the full week's cash every week-end day (0 otherwise), which
    is bit-for-bit plain DCA (used to prove the strategy nests DCA
    exactly)."""
    is_week_end = eng.week_end_flags(daily.index)
    mult = compute_sad_multiplier(daily, tilt_strength, power, latitude_deg) if enabled else None

    def decide(t, cash):
        if not enabled:
            if is_week_end[t]:
                return cash, 0.0, {}
            return 0.0, 0.0, {}
        if not is_week_end[t]:
            return 0.0, 0.0, {}
        target_buy_usd = min(cash, max_lump_multiple * weekly_deposit, mult[t] * weekly_deposit)
        target_buy_usd = max(0.0, target_buy_usd)
        return target_buy_usd, 0.0, {"mult": float(mult[t])}

    return decide


CATEGORY = "Seasonality / execution timing"

# Grid: tilt_strength x power x max_lump_multiple = 3x2x3 = 18 (<=36 cap,
# 3 tunable params <=5; reference_latitude_deg fixed, not a grid param).
GRID = {
    "tilt_strength": [0.3, 0.5, 0.7],
    "power": [1.0, 2.0],
    "max_lump_multiple": [4, 8, 12],
}
PRIMARY_CONFIG = {
    "tilt_strength": 0.5, "power": 1.0, "max_lump_multiple": 8,
}


def grid_configs() -> list[dict]:
    out = []
    for ts in GRID["tilt_strength"]:
        for p in GRID["power"]:
            for ml in GRID["max_lump_multiple"]:
                out.append({"tilt_strength": ts, "power": p, "max_lump_multiple": ml})
    return out


# Verified at module import time, per family 021's lesson: PRIMARY_CONFIG
# must be an actual member of the declared grid.
_CONFIGS = grid_configs()
assert PRIMARY_CONFIG in _CONFIGS, (
    f"PRIMARY_CONFIG {PRIMARY_CONFIG} is not a member of GRID's "
    f"{len(_CONFIGS)} configurations -- fix PRIMARY_CONFIG or GRID."
)
