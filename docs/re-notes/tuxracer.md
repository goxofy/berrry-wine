# Tux Racer original Win32 progression

The original 0.61a game is registered as `tuxracer_original_061a`. Preserve
its canonical local manifest. The
retained payload and static closure recipe are described in
`tuxracer-original-recovery-oct28.md`.

The 2026-10-30 SDL investigation retained at
`scratch/runs/20261030T200605Z-tuxracer-sdl-owner/` established that ordinary
Enter reaches MainMenu, and ordinary P reaches an unimplemented
`glTexCoord2d` (API 4414), guest EIP `0x00421c56`, return `0x00421c66`.
The inspected frames were MainMenu; that run did not establish Practice or
race gameplay. Sampler relocation repair `cbcfb806f` changes observation only.

The scalar API takes two doubles in four x86 argument words. Its implementation
reads the guest stack at ESP+4 through the checked `glTexCoord2dv` path and
consumes the return address plus 16 argument bytes only after success. Both
forms demote each double once at the existing float encoder boundary and use
opcode 28 (`glTexCoord2f`), preserving unit-zero `(s,t,0,1)`, other vertex
attributes, and display-list value capture/replay. No command opcode was added.
The dispatch generator also includes the scalar native API in dynamic WGL
lookup availability.

Focused validation is in `test/test-gl-texcoord2dv-dispatch.js`: scalar and
vector calls inside/outside Begin, non-affine page crossings, signed zero,
rounding, nonfinite coordinates, stack bytes and GPRs, list compilation and
replay, allocation/translation/wrap failures, and five deliberately broken
route/ABI/encoder variants. `test/test-gl-color4dv-dispatch.js` retains its
color/vertex checks and no longer expects the scalar texture API to trap.
Logs and the bounded original-game retest belong in
`scratch/runs/20261030T2016Z-tuxracer-gl2d/`.

The single bounded canonical original-game retest used the final shared-tree
Wasm and current runner, software GL and cooperative threads. Enter down/up
reached the inspected MainMenu; P keydown was acknowledged and dispatched.
The next trap is **`glColor3dv` (API 4222)**, guest EIP `0x00416427`, return
`0x00416436`, vector argument `0x086027e8`. The process exited after 4.99 s.
Both inspected captures (`poll.png`, `mainmenu.png`) are MainMenu, taken before
P; Practice/race remains unverified. Do not label the menu's Practice button
as a rendered Practice screen. The source/runner/module hashes, canonical
157-file mount validation, input acknowledgements, crash and 25 SHA-verified
remote artifacts are retained in the run above.

Task-owned finite-TTL Boat `bx_yb3nay5w` was snapshot-verified at
2026-10-30T20:23:46.181Z and verified STOPPED at 20:23:46.230Z, before its
original expiry 20:41:54.584Z. Closeout found no surviving task watchdog.
Its stopped snapshot retains `/home/user/tuxracer-render`,
including the original fixture and `capture-gl2d-oct30`. Fork a new finite-TTL
test box for the next API repair; the local run archive also preserves this
retest's captures and control scripts. No public deployment was performed.

The `glRectf` repair on 2026-10-30 is code commit `5cd674228` on main.
It appends opcode 142 without changing earlier command IDs, captures four
float words as one display-list command, and executes the rectangle through
native GL_QUADS vertices `(x1,y1),(x2,y1),(x2,y2),(x1,y2)` at z=0/w=1.
Existing vertex attributes and quad triangulation are reused. Direct calls,
compilation and replay inside Begin/End report GL_INVALID_OPERATION without
ending or changing the caller's primitive. WGL lookup exposes the real API.
Focused rectangle/ABI/list/packed-replay/mutation, color/texture, full-module
WGL, existing display-list/stream/encoder suites and locked build all passed.

The single original 157-file invocation in
`scratch/runs/20261030T2040Z-tuxracer-glrectf/` ran the exact module
`4e62aa1563afe438ab39011b90910d4d311c05d4809241e4e8f6f00b710412b2`
and runner `c82398cf64e381ef2a729696280e4eab858eb51b7deb956f2b150281691b5748`.
Ordinary Enter down/up, then P down/up reached the personally inspected
**Practice “Select a race” / Frozen River screen**. An additional native
Enter down/up in that same invocation reached **“Loading, Please Wait…”**;
both subsequent frames still showed loading. The controller quit normally
at 27.953 seconds (20:41:55.062–20:42:23.015 UTC), exit 0, no new API trap.
Practice selection is verified; race gameplay is not. The next useful step
is a longer bounded observation after race Enter, rather than claiming the
loading frames demonstrate gameplay. Initial read-only mount preflight
inherited the supervisor's small child limit and failed to start Node;
restoring the supervisor's normal child limits verified all 157 files and
the exact hashes after launch, without a second game invocation.

Task-owned fork `bx_msqscjw8`, from stopped parent `bx_na7bzcfg`, has a
verified completed snapshot at 20:43:09.436Z and was verified STOPPED at
20:43:33.964Z, before its original 21:08:03.788Z expiry. The explicit shutdown
delegation is fulfilled. Fork this retained snapshot with a finite TTL;
`/home/user/tuxracer-render` retains the original assets/current runtime and
`capture-glrectf-oct30` control/evidence. All 40 remote artifacts were copied
using Boat exec and SHA-verified locally; no SSH/scp or public deployment.
