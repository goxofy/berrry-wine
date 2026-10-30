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
