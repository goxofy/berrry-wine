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

## Independent source acceptance — 2026-10-22

**Scoped SOURCE ACCEPTANCE** of exact candidate
`ce4ce4f95eacaedff1b3e386f3ce3ae5d85bd16c` against
`d550de85ae9b46d23314d164a932d66478894999`. No concrete source defect found
within this review. This is not permission to merge or runtime qualification.
Remote candidate matched; remote main
`bf99a428500d47ecacd3de2e86cc47cb0dfaacef` differs from the base only in
`ops/COORDINATOR.md`, `ops/README.md`, and `ops/TELEGRAM.md`. Those audit/policy
documents were reconciled read-only; no candidate source was replaced by main.

Reviewed the actual changed WAT and all CACA000A producers, including
DispatchMessageA and the outer dispatcher. The private record retains child,
root, expected ESP, prior guard/resume and audio ownership; invocation_leave
returns to the retained child's parent stack entry. Root/epoch/slot validation
precedes record access. Explicit loader/thread initialization establishes roots;
fresh slot reuse retires the old instance. Frame indexing is
`(tid-1)*2048 + depth*32` within 32768 bytes for 16 slots. The invocation stack
permits 63 live children (root consumes its first entry), tighter than the
64-record allocation. No guest-provided record pointer is trusted.

Admission precedes producer stack, timer consumption/event signaling and audio
wait changes. DispatchMessage admission is at its MM_TIMER arm, not before all
ordinary API dispatcher bookkeeping; the latter is not claimed transactional.
The separate CACA000A return preflight is before dispatcher effects and the
finish helper revalidates before popping/restoring. No-due/event polls release
their provisional child. One-shot and periodic consumption remain unchanged.
Nested DispatchMessage records restore outer guard/resume without restoring an
outer audio wait. CACA003B refuses a live CACA000A owner before its pinned-stack
reset; its independent callback lifetime is still outside this acceptance.

Validation on Node v24.18.1:

- Requested ownership replay: 55 cases and the wrong-child mutation detected.
- Requested saved-carry replay: 29 cases and all six mutations detected.
  Snapshot implementations copy memory (`Buffer.from` / `slice`), rather than
  retaining a live view; mutation checks require behavioral assertion failures.
- `node test/test-mm-timer-release-review.js`: seven independent cases. Four
  producer routes execute the exact production RET20, run-loop thunk routing,
  whole outer dispatcher and inner prefix through the continuation. Wrong-child
  outer dispatch rejects before prefix effects. Additional cases exercise actual
  shared-memory thread-slot reuse, thread 16 with 63 nested callbacks and region
  canaries, and observable event signaling after rejected/exhausted admission.
- Generated region mirror is current (268 regions). The appended allocation
  leaves old region placements unchanged. Census/mutation validation uses exact
  Git fallback for missing sparse files; raw sparse runs correctly rejected the
  absent `host.js` seal, and their failed logs are retained. No gate is suppressed.
- All 14 candidate source hashes and all 12 prior log seals match result.json.
  Unrelated token/host-owner/queue/scheduler, region-declaration and tier evidence
  is reused at that exact revision. Census changes retain `ownership: pending`,
  whole-function seals and the nonlocal API lock. No API jump unlock or broad
  SEH change occurred.

The independent fixture stubs resource cleanup, host services, thunk membership
and branch/cache dispatch; identity guest translation remains. It closes the
specific modeled-RET/separate-dispatch gap for these routes, **not** the complete
interpreter integration gap. Canonical/full-module timer and wave-wait tests,
full build, real guest translation/fault handling, browser/game/runtime tests,
and CACA003B's own retained lifetime remain outstanding. Coordinator owns that
qualification decision and any eventual integration; **NO MAIN MERGE** here.

Review branch: `task/mm-timer-owner-release-review-oct22`.
Evidence: `scratch/runs/20261022-mm-timer-owner-release-review/`, including
admission, seal verification, successful and failed gate logs, result and
publication receipts. Exact non-cone manifest projection was 36,551,511 bytes
plus 16,777,216 reserved bytes, below the 64 MiB total allowance; fresh admission
was 8,321,327,104 bytes against 2,982,150,144 required. No 16 MiB checkout limit
was applied. No workers, boxes, build, browser, dependency installation, fleet,
deployment or laptop actions; no assigned box/expiry, lifecycle stays with the
coordinator. Candidate and root WIP/index/config/TODOS/STATUS were not edited.
