# Win32 multimedia timer retained return ownership

Base: exact integrated main `d550de85ae9b46d23314d164a932d66478894999`.
Task branch: `task/mm-timer-owner-recovered-oct21`. Independent acceptance is
pending; this task does not merge main or enable nonlocal jump APIs.

## Reproduction and correction

`MM_OWNER_REF=d550de85ae9b46d23314d164a932d66478894999 node
test/test-mm-timer-ownership.js --baseline` compiles the actual producer,
save/restore functions, token allocator and CACA000A return arm. After timer
entry, it enters an unrelated child invocation and executes the return arm.
The baseline accepts that wrong owner, clears the callback guard and restores
the interrupted caller. This is executed source evidence, not a census label.

CACA000A now retains the allocated child identity, root and expected return
ESP in emulator-owned records. Admission precedes producer stack, timer-slot,
wait and guard mutations. `fire_mm_timer` admits before due polling because
polling itself can consume and signal event timers. A poll without a function
callback cancels its provisional child; it still spends one monotonic identity.
Exhaustion traps without wrapping or consuming a timer. Production loaders
must already have established the invocation root; admission does not lazily
reattach an uninitialized or retired instance.

The 32 KiB appended region contains 64 records for each of 16 thread slots.
Its allocation leaves every existing region in place. Per-instance root/depth
and the shared invocation validator reject retired roots. Expected ESP rejects
a malformed return before restoration. The outer dispatcher checks CACA000A
before resource scopes, thunk hooks or other dispatcher bookkeeping; the return
helper checks again before popping the child. A rejected owner is not unwound.

## Producer / return matrix

| Producer | Continuation and retained state | Qualification |
| --- | --- | --- |
| `fire_mm_timer` | CACA000A; expected ESP = interrupted ESP − 40 | Admission before due poll/consumption; one-shot, periodic, no-due and event routes exercised |
| DispatchMessageA MM_TIMER arm in `09a5-handlers-window.wat` | CACA000A; expected ESP = API-entry ESP − 32, accounting for completed RET 4 frame | Admits before the handler changes ESP/EIP; message-carried callback/id/user survive already-retired one-shot slot |
| `fire_audio_callback_bound`, through wave/MIDI wrappers | CACA000A; expected ESP = interrupted ESP − 40; record marks audio ownership | Existing immutable registration, wait and saved-carry behavior preserved; no audio lifecycle redesign |
| `mm_timer_thread_step` | CACA003B; existing pinned loop ESP | Root validation and refusal to discard any live CACA000A record added, also at dispatcher entry. This does **not** claim retained child ownership for the dedicated thread's own CACA003B callback lifetime |

Nested DispatchMessage timers have separate records. Their returns restore the
prior active guard/resume reason and cannot restore an outer audio wait. Only
the record that admitted audio calls `wave_callback_restore_wait`. Audio may
interrupt a dedicated timer-thread callback, finish CACA000A, then allow that
thread to continue through CACA003B. Neither continuation can consume the
other's live save frame in the tested routes.

## Validation

- `node test/test-mm-timer-ownership.js --controls`: 55 production-slice cases.
  All four CACA000A producers return normally; mismatched child, same-depth
  child reuse, stale root/epoch/thread, duplicate return and malformed ESP
  reject. Depth, record and serial exhaustion plus uninitialized/retired
  admission preserve copied whole-memory and exported-global snapshots.
  Nested timer/audio, dispatcher preflight and cross-continuation cases pass.
  Removing the retained-identity check (including substituting the current
  child at leave) compiles and fails the wrong-child behavioral assertion.
- `node test/test-audio-saved-carry.js --mutations`: 29 compiled cases plus six
  detected corruption controls. Its extraction now includes real ownership
  helpers/allocator, while retaining the original carry/flags/stack assertions.
- Existing invocation-token, wave owner, queue and scheduler regressions pass.
- Census gate: 407 boundaries, all still labeled `pending`; nonlocal API lock
  remains enforced. Census mutation tests also cover unreviewed timer owner
  and depth resets. Only changed producers/helpers received renewed seals.
- Region declarations and generated mirror agree (268 regions); tier gate
  passes (2078 tests). The new regression is in the default unit tier.
- `git diff --check` passes. Shared root TODOS/STATUS/index/config hashes remain
  unchanged; laptop worktrees were not accessed.

The tests use real production WAT slices with identity guest translation and
modeled stdcall RET 20, not an x86 interpreter. The DispatchMessage test extracts
its exact MM_TIMER arm; admission snapshots start at that producer boundary,
not at the outer ordinary-API dispatcher bookkeeping. Return tests execute the
actual early dispatcher preflight and actual continuation arm separately, not
the entire dispatcher. Host queue/scheduler tests use their existing modeled
transport environment. Full-build/browser/game/Windows behavior, CACA003B's
independent retained lifetime, other deferred families and nonlocal jumps
remain unqualified. The two existing full-module timer tests were adjusted to
establish harness roots/owned frames but were **not run** under the no-full-build
constraint. The full-module wave-wait test was also not run.

## Evidence and recovery

Shared evidence: `scratch/runs/20261021-mm-timer-owner-recovered/`, including
admission, baseline/final logs, `result.json` and `publication.json`. The
read-only `git-source-overlay.cjs` supplies missing tracked files from exact
HEAD for canonical scanners on this sparse checkout; actual edited files take
precedence. It does not rewrite source or suppress a gate. Re-run on a complete
checkout without that preload, or use `NODE_OPTIONS=--require=<overlay>` for
the census test's child scanner.

The checkout uses a local Git object alternate to the verified source
repository. The published task branch, based on the stated main commit, is
the remote recovery source; no ignored binary or full build is required for
these source-slice tests. No boxes were assigned, started, resumed, stopped or
deleted; runtime lifecycle remains coordinator-owned.
