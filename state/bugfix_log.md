# Bugfix log

Reruns of an identical configuration after a bug fix are logged here rather
than counted as new trials (research-loop-plan-v3.md sec 6.1).

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
