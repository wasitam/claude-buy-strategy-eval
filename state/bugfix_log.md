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
