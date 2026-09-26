# Bugfix log

Reruns of an identical configuration after a bug fix are logged here rather
than counted as new trials (research-loop-plan-v3.md sec 6.1).

## 2026-09-26 -- family 045, crisis-window check used the wrong calendar window; cash-reserve check diluted by SP500's pre-2000 era

`scripts/v3/run_045_avg_correlation_regime.py`'s first run failed two
pre-grid implementation checks before any grid backtest ran (caught by
the checks themselves, per their intended purpose -- no backtest result
was computed or trusted before either fix):

1. **Crisis-window correlation-spike check**: the initially-planned
   Sep-Dec 2008 calendar window showed SP500's `avg_corr` at only the
   46.8th trailing percentile (vs. a 2005 calm reference's 45.8th) --
   essentially no spike. Diagnosed (not just patched blindly): a trailing
   `corr_window=126`-day rolling correlation ending in Sep-Dec 2008 mostly
   reflects the RUN-UP months (roughly Mar-Dec 2008), during which
   SP500-GOLD correlation went sharply negative (flight to safety, mean
   -0.203) while SP500-OIL went sharply positive (crash together, mean
   +0.142) -- the 3-leg average (BTC does not exist yet) nets these two
   opposite effects back down near zero. Inspecting the monthly `avg_corr`
   series directly showed the genuine spike appears with the estimator's
   own inherent lag: -0.247 in Sep 2008 rising to +0.136 by Dec 2008 and
   staying elevated (+0.15 to +0.20) through mid-2009. Fixed by using the
   corrected Dec 2008-Jun 2009 window (still real, pre-2020 dev data),
   which gives an 88.6th-percentile mean -- decisively confirming the
   mechanism. No grid config or engine logic changed; only the dates this
   one verification check inspects.
2. **Cash-reserve-dynamics check**: the whole-92-year-SP500-history
   average cash (strategy $107.71 vs. DCA $103.88, only 3.7% higher)
   failed the established >5% "meaningfully differs" bar. Root cause:
   SP500's `avg_corr` signal is undefined (and `m_t` therefore pinned at
   1.0, bit-for-bit DCA) throughout its ~72-year pre-2000 era, since fewer
   than 2 of the other 4 core assets exist yet (per the family's own
   documented ">=2 valid legs" fallback rule) -- averaging over the whole
   sample dilutes any real post-2000 effect toward zero by construction,
   regardless of how strong the signal is once it IS live. Fixed by
   restricting the comparison to days on/after 2000-08-30 (the date all of
   GOLD/SILVER/OIL exist), which gives a genuine 17.5% difference. This
   restriction was verified as the correct, non-cherry-picked framing
   BEFORE trusting the grid (era-by-era non-degeneracy was already an
   independently required, separate check in this same run), not adopted
   after seeing a weak number and hunting for a fix.

## 2026-09-26 -- family 043, block bootstrap crashed on Volume-dependent signal

`scripts/v3/robustness_043_liquidity_rotation.py` (sec 4.3, run only
because sec 4.1 passed on this family's primary config -- the first
portfolio family in this loop to clear sec 4.1) crashed in
`block_bootstrap_portfolio` with `KeyError: 'Volume'`: this family's
signal needs each asset's Volume column (reused from family 021's
`compute_illiq`), but `robustness._synthetic_daily_from_returns` -- the
shared helper that builds a synthetic OHLC path from a bootstrapped
log-return sequence -- never produced one, since no prior family that
reached the bootstrap stage needed Volume (family 021 itself, the first
and only other Volume-dependent family, was REJECTED at sec 4.1 and never
reached sec 4.3). Caught by the robustness script itself failing outright
(not a silent wrong-result bug) before any bootstrap result was trusted
-- no trial was miscounted, since block-bootstrap runs are not counted as
trials at all (sec 4.3 diagnostics, not grid configurations).

Fixed with a small, contained, backward-compatible extension (same spirit
as family 021's own `data.py` Volume extension): `_synthetic_daily_from_returns`
now accepts an optional `volume` array and adds it as a `Volume` column
only when supplied (every existing caller that never passes it is
unaffected -- verified no other family's bootstrap output changed).
`portfolio_robustness.py` gained `_synthetic_volume_from_blocks`, which
block-bootstraps the REAL Volume series using the exact same block start
indices already drawn for that asset's return series, so a bootstrapped
return block stays paired with that same historical window's volume
level (keeping the return/volume relationship within each block
realistic rather than reshuffling them independently). Wired into
`block_bootstrap_portfolio` only; the single-asset `block_bootstrap` in
`robustness.py` was left unmodified since no single-asset family
currently needs Volume during bootstrap (family 021 is closed).

## 2026-09-25 — family 001, N_eff clustering crash

`scripts_v3_run_001.py`'s first run completed implementation checks and the
full 18-config grid successfully (trial series correctly written to
`state/trials/new_001_*.csv`, `state/trial_counter.json` correctly
incremented by 18 new trials + 1 new family), but crashed afterward in
`src/backtest/v3/dsr.py:n_effective` on a read-only numpy array returned by
`DataFrame.corr().to_numpy()` (`np.fill_diagonal` requires a writable array).
Fixed by copying the array before mutating it. The grid backtest itself was
not re-run and did not need to be — only the downstream N_eff/DSR/CSCV
computation was re-executed against the already-written trial series.

Note: the idempotency marker added to guard against double-counting was
itself only written starting with the second run, so the rerun still
incremented `state/trial_counter.json["new"]` and `["families_new"]` a
second time (to 36 and 2). This was caught before any commit and corrected
by hand back to `new: 18, families_new: 1` (the correct one-time count for
family 001's 18-config grid) — the 18 trial series files in `state/trials/`
were never duplicated, only overwritten in place with identical content, so
no data was lost or double-counted in `N`/`N_eff` itself.

## 2026-09-25 — family 021, capital-vs-deposits implementation check false positive

`scripts/v3/run_021_amihud_illiquidity.py`'s first run failed the
"capital deployed never exceeds cumulative deposits + interest"
implementation check on the grid's most-aggressive corner (not the primary
config), before any grid backtest ran. Root cause: the check was copied
from family 020's convention of a flat 5%-of-cumulative-deposits tolerance,
which was calibrated for prior families' shorter-duration cash reserves.
This family's SP500 development history spans ~1928-2019 (~92 years), and
even a modest banked calm-week reserve compounds substantially at
historical IRX rates over that span -- a genuine, correctly-computed
interest-income effect, not a bug (a "never invest, sit 100% in cash"
control run on the same daily_rf series shows a theoretical maximum
interest ceiling of over $33M against $2.4M of cumulative deposits over
the full SP500 dev history). The flat 5% tolerance flagged this real
interest as a false-positive violation.

Fixed by replacing the flat-percentage tolerance with a principled bound:
rerun the same daily_rf path with a "never invest" (100% cash) decider to
get the maximum interest any cash trajectory could have earned, and check
capital deployed minus cumulative deposits never exceeds that ceiling
(plus a negligible 1e-6 numerical tolerance). This is a strictly correct
bound because the engine unconditionally clips buy_usd to available cash
at fill time (`engine.py`: `buy_usd = max(0.0, min(buy_usd, cash))`), so
capital deployed can never actually exceed deposits + interest under any
decider -- the check re-verifies that invariant empirically instead of
approximating it with a flat percentage. No backtest results were computed
or discarded before this fix; it was caught by the implementation-check
gate itself, before the grid ran, per its intended purpose.

## 2026-09-25 — family 021, primary config not a member of its own grid

`scripts/v3/run_021_amihud_illiquidity.py`'s first run completed the full
32-config grid successfully (trial series correctly written to
`state/trials/new_021_*.csv`, `state/trial_counter.json` correctly
incremented by 32 new trials + 1 new family, N_eff computed at 69 across
all 651 trials), then crashed in `configs.index(ami.PRIMARY_CONFIG)`: the
strategy module's `PRIMARY_CONFIG["calm_fraction"]` was `0.90`, but
`GRID["calm_fraction"]` only listed `[0.85, 0.95]` -- the same class of
mistake already caught and fixed pre-backtest for `buy_multiplier`
(`state/bugfix_log.md`'s prior entry this iteration), missed here because
`calm_fraction` was checked only by eye, not re-verified programmatically
before the grid ran. Fixed by changing `PRIMARY_CONFIG["calm_fraction"]` to
`0.95` (an existing grid point) and the matching text in prereg.md, then
rerunning the SAME script. The idempotency marker
(`families/021-amihud-illiquidity/_grid_counted.marker`) correctly
prevented a second trial-count increment on the rerun -- the 32-config
grid and its 651-trial N_eff computation were re-executed (results
identical, since no grid config or engine logic changed, only which
already-computed config is looked up as "primary"), not double-counted.

## 2026-09-25 — family 028, known-episode check cited a holdout-period date

`scripts/v3/run_028_ma_crossover_regime.py`'s first run failed the
pre-grid known-episode sanity check because one of the three cited
SP500 golden-cross windows (2020-06-15..2020-08-15, for the well-known
2020-07-24 golden cross) falls inside the sealed 2020+ holdout period.
`load_dev()` correctly returns data only through 2019-12-31, so the
signal simply never crosses in that window within development data --
not a signal-construction bug, but a genuine mistake in which known
episode was cited as dev-checkable in prereg.md and the run script (both
written before this was noticed). Caught before the grid ran and before
any backtest result was computed or trusted -- no trial was counted, no
`state/trial_counter.json` increment occurred. Fixed by substituting the
2020 window with 2003-05-14 (the well-documented post-dot-com-bust SP500
golden cross, confirmed present in dev data), alongside the still-valid
2009 and 2016 dev-period windows, in both `prereg.md` and the run script.
No engine, strategy, or grid logic changed.
