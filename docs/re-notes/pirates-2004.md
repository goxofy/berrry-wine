# Sid Meier's Pirates! (2004)

`test/binaries/candidates/pirates-2004/digital/app/Pirates!.exe`, registry id
`pirates_2004` (`d3d9Programmable`, `bigMemory`). Direct3D 9, statically linked
(`d3d9.dll` import), with msvcr71/msvcp71, Bink, Miles (mss32 plus its
`win32/*.asi`, `*.m3d`, `*.flt` providers) and oleaut32 from the game directory.

## Route to the main menu (CLI, software D3D9 arm)

```sh
node test/run.js --app=pirates_2004 --d3d9-renderer=software --batch-size=100000 \
  --max-batches=1000000 --max-seconds=180 --stuck-after=1000000 --no-close --png=menu.png
```

The D3D9 main menu (Play Sid Meier's Pirates!, Load A Game, Change Your System
Options, Visit The Firaxis Website, Visit The Hall Of Champions, View Credits,
Quit, over the Caribbean map) is up by batch ~1000 at `--batch-size=100000`.
Assets load from `assets\pak*.fpk` one byte per `ReadFile`, which is slow but
correct. Evidence: `scratch/runs/20261006T033534Z-pirates_2004-dxinit`.

## Startup, as reverse engineered (2026-10-06)

- `0x4d2950` is graphics init. It calls `0x500080` (device setup); a nonzero
  result goes to an error path that first asks the DxDiag provider for the
  DirectX version (`0x4ad050`, through the game's `dxdiagn.dll` COM server)
  **only to choose the message**: below 9.0c (`0x90003`) it shows the
  "requires DirectX 9.0c" text at `0x70e234`, otherwise "Unable to initialize
  DirectX." So that message never means the DirectX version check failed.
- Device setup creates a HAL device with software vertex processing
  (BehaviorFlags `0x24`), reads the render target, depth surface and
  `GetDeviceCaps`, and at `0x5c0963` requires `MaxTextureBlendStages >= 2` and
  `MaxSimultaneousTextures >= 2`. Its caps record is at `this+0x644`; it also
  reads MaxVertexBlendMatrices (`+0xa8`), MaxStreams, and the vertex/pixel
  shader versions (`+0xc4`/`+0xcc`; the helper at `0x5002f0` returns them as
  major*10+minor to about twenty callers).
- Miles' A3D provider `win32\mssa3d.m3d` asks `CoCreateInstance` for
  Aureal's class (`a3dapi.dll`), which no machine without an A3D card has.

## Fixed

| commit | what |
|---|---|
| `ba161dfb` | D3D9 caps advertise `MaxTextureBlendStages = 6` (was 0) |
| `12408feb` | a `CoCreateInstance` whose in-proc DLL is missing resumes the caller (the yield pump left EIP on the thunk and re-ran it on the caller stack) and clears `*ppv` |
| `d7f5a429` | `test/run.js` honours `bigMemory` (2048 MB); at 512 MB the asset load runs out of guest heap |

## Not yet looked at

Gameplay (`Play Sid Meier's Pirates!`), audio, the WebGL arm at this build.
`ole32.dll` is absent from this box's `test/binaries/dlls`, so the Miles
providers' ole32 imports fall to WAT stubs.

## TG77 cooperative thread attach (2026-10-14, unresolved)

Safari reported `DllMain did not complete` for module `0x9f1000`, reason 2,
with restored caller EIP `0x9fc4bb`. Chrome cooperative evidence supplied by
the runtime investigator (`scratch/runs/20261014-pirates-browser-cooperative`)
places the actual msvcr71.dll callback at `0x7503fc0`, yield 9 / halt 4:
a critical-section wait. The section owner remains to be captured.

Source inspection and the cheap `node tools/pirates-attach-gap.js` witness
confirm that the synchronous callback runner restores the caller and releases
the callback gate on this wait; retrying the notification repeats previously
completed DLL callbacks. This mock reproduction is not real-PE acceptance.
See [continuation interface and regression plan](../pirates-attach-continuation-plan-20261014.txt)
for the required owning-thread scheduler integration, cleanup contracts and
unexecuted real-PE/browser gates. No production fix is included.

## Cooperative thread-attach regression (2026-10-14, TG77)

The Safari report on module SHA256
`e6ac188dd8c7b16d04eaa4b74446ab2c4ab211422738709e33cffda5db444e7e`
reports `DllMain did not complete: module=0x9f1000 reason=2`.
Reproduced with the existing pinned corpus acquisition on temporary
`bx_tgbme2h7`, Chrome, isolated page, `?debug&no-threads&app=pirates_2004`.
Source was `43f04c7c4ac8914c385c37a7be96c7e1b9f61623`, same module hash.
No guest patch, capability override, or DllMain completion bypass was used.

The loader identifies `0x9f1000` as **msvcr71.dll**, preferred base
`0x7c340000`, entry `0x9f329f`. Several prior callbacks complete normally.
The failing callback stops at `EIP=0x7503fc0 yield=9 halt=4`: a critical-section
wait, not the callback budget limit. The later crash report's `0x9fc5ec`
(Safari reported `0x9fc4bb`) is the restored caller state, not that wait thunk.
Increasing budgets or marking the unfinished attach complete would hide the
scheduling problem.

Next capture the contended section and its owner, then implement resumable
thread-attach scheduling with a real contended-lock regression. Preserve the
callback frame, loader serialization, and exactly-once notifications while
allowing the owner to run. `pumpThreadsOnce` deliberately refuses entry while
already running a cooperative worker, so it is not a drop-in fix here.
The owner and precise lock have not yet been established. Worker-mode and
Safari retests remain separate; no fix or gameplay acceptance is claimed.

Evidence: `scratch/runs/20261014-pirates-browser-cooperative/` contains the
90-second probe, six captures/state snapshots, browser log and process receipt.
The final fatal-error screenshot was reviewed. The original user report is in
`scratch/runs/20261014-pirates-user-crash/report.txt`.

## Cooperative continuation candidate (2026-10-14, runtime verified)

Task branch `task/pirates-attach-fix` now retains the notification generator,
module cursor, snapshot pins and loader gate through ordinary scheduler turns.
Candidate production source `16961623b` freshly built to WASM SHA256
`70c6d329d51eee5db553715f53ffc47f3e6e2491b54ae5327f1b8b012427d655` passes
the real-PE contended-section regression and existing main/Worker DllMain
completion, load-context and callback-serialization tests.

The original cooperative Chrome startup now reaches the visible Main Menu.
The actual msvcr71 callback still parks at `0x7503fc0`, yield9; captured section
guest `0xa3c190` (WASM `0x64e190`) is owned by **thread1/main**, recursion1.
First recorded tid6 park retains its actual frame and loader gate `[6,1]`;
5.415ms later its callback returns, followed by sequence completion and gate
release `[0,0]`. Four such waits complete during the 90-second run. Thus this
route's owner can run and release the section with ordinary scheduling.

Evidence `scratch/runs/20261014-pirates-attach-candidate/` includes raw traces,
test/build receipts and reviewed final menu capture. The baseline module is
older, so the screenshots alone are not a controlled version A/B. No gameplay
input, affected Safari validation, merge or deployment is claimed. Blocking
nested initialization and synchronous exit-detach remain existing boundaries;
see `docs/pirates-attach-candidate-20261014.txt` for exact test scope.


## Original browser main menu (2026-10-31)

The registered original `pirates_2004` reached an inspected Main Menu in
Chrome 151 using the WebGL selection and retained module
`573e235db16e351668289f49e2f279ff48bcad56e7ca533167cb94cd6f4ec3fc`.
This was a retained-module run; its full source identity was not reconstructed,
so it is not a fresh current-main build or a controlled comparison with the
October 14 callback candidate. Original assets and host sources were unchanged.

The title splash preceded the menu. Escape, Enter and one canvas click were
recorded as trusted input; keys and buttons were released. The UI slice changed
from Auto (logged as 100000) to 5000, then 50000. The menu capture shows Play,
Load, Options, credits and Quit over the original Caribbean map. Its late
metadata records a visible 800×600 game window at GPU sequence 3. Subsequent
Play-selection/control requests failed or stopped completing while browser
target discovery still responded. There is no verified Play consumption,
character creation, sailing or gameplay result, and no established cause for
the control failure. Resource lookup 404s occurred; no fatal API trap was
observed. No production fix is claimed.

Evidence: `scratch/runs/20261031T0200Z-pirates-original-browser/`, especially
`loading-3min.png`, `loading-3min.json`, `actions.jsonl`, `verification.json`
and `recovery.txt`. Verification covers 1374 original input pins, 266 served
responses and 141 unique host paths. The controller exited 0 after explicit
quit; its browser, profile and three ports were closed. No Boat was used.
The next runtime check should start with a small UI slice and test original
menu selection; this capture establishes rendering only.

## Original new game reaches sailing (2026-10-31)

A second local Chrome 151 run started with UI slice **5000** before Launch,
cooperative execution and the same retained `573e235d…` module. Native mouse
and keyboard input advanced Play → Crew Signups → tavern → English captain
welcome → crew decision → **cast off at Port Royale**. The inspected sailing
view shows the ship, ocean, port, 600 gold and 41 crew. Subsequent paired
Right and Up key inputs were delivered; the ship becomes visible and the
coast/port position changes across the captures. This establishes progression
beyond the menu and an updating original sailing scene; the small sample does
not isolate each key's effect or qualify a voyage, combat or objective.

Rendering remains visibly defective: the mountains are white, and the console
records 270 “specular lighting is not implemented” errors. Their causal
relationship is unproven. No source fix, complete graphics acceptance, audio
acceptance or persistent save is claimed. This retained module's full source
identity remains unknown; it is not a newly built main revision.

Evidence: `scratch/runs/20261031T0215Z-pirates-small-slice/`. Personally inspected
`play-enter.png`, `crew-confirm.png`, `captains.png`, `captain-continue.png`,
`captain-next.png`, `cast-off.png`, `sailing-turn.png` and `sailing-sails.png`
show the route. `actions.jsonl` and screenshot metadata retain timing and
25 trusted input events, with all keys/buttons released. Verification matches
1374 original input pins, 465 served responses and 141 unique host paths;
179 artifact hashes preserve the run. Explicit quit closed the browser,
controller (exit 0), three ports and profile; no Boat was used.
`recovery.txt` records the exact native route. A next graphics investigation
should first reproduce the white terrain with a source-identified build and
compare a matched scene, rather than infer a cause from the specular warning.

## Current-main build identity check (2026-10-31)

A locked canonical `tools/build.sh` passed at main `90c0c0c48`. Tracked
source hashes remained unchanged across compilation. Its 1,896,705-byte module
has SHA-256 `573e235db16e351668289f49e2f279ff48bcad56e7ca533167cb94cd6f4ec3fc`,
exactly matching the retained module used for the successful sailing run above.
This supplies a reproducible current-main source identity for those module
bytes; it does not turn the earlier execution into a fresh runtime replay.

The new browser run rendered Main Menu, but its browser PID disappeared and
CDP refused connections before the new-game route completed. The cause is
unknown. No new sailing or terrain comparison is claimed. Evidence is in
`scratch/runs/20261031T0220Z-pirates-main-sailing/`: `build.log`,
`source-before.json`, `build-identity.json`, inspected `captains.png`, and
`verification.json`. Explicit controller quit completed; its browser, profile
and three ports were closed. No Boat was used. The next graphics task still
needs a matched sailing scene and a measured rendering contract before
attributing the white terrain to the unsupported specular path.

## WebGL fixed-function specular lighting (2026-10-31)

`lib/d3d9-fixed.js` now computes the fixed vertex stage's specular RGB using
material specular times the sum of each light's specular color, half-vector
power, attenuation and spotlight factor. It follows Microsoft's
[D3D9 specular equation](https://learn.microsoft.com/en-us/windows/win32/direct3d9/specular-lighting),
including the finite camera-to-vertex viewer vector and the infinite viewer's
`(0,0,1)` vector. Material/COLOR1/COLOR2 selection uses the existing fallback
and COLORVERTEX rules; normals use the inverse-transpose world-view transform
and optional normalization. Back-facing lights and degenerate vectors produce
no highlight. Power zero avoids GLSL's undefined `pow(0,0)` case.

The specular sum is clamped per vertex, interpolated separately, and added
after the texture cascade without changing its alpha. Mixed programmable pixel
shader post-specular and software-backend specular remain unsupported and
guarded. This rendering implementation does not establish the cause of the
white terrain in Pirates.

Focused `test/test-d3d9-specular-web.js` passes **86 actual WebGL1/2 pixel
checks** against an independent scalar vertex-lighting/interpolation reference:
directional, point and spot lights; attenuation/range/cones; material sources
and missing-color fallbacks; COLORVERTEX; powers 0/1/2/4/20; finite/infinite
viewer and translation; inverse-transpose normals and normalization; zero
vectors/backfaces; accumulation/clamping; texture replacement and alpha.
The mixed-stage and software-backend regressions pass. The unmodified existing
lighting WebGL suite fails with `invalid light attenuation` on its known
“all-zero attenuation reads as 1” fixture. A diagnostic run excluding only that
case passes the remaining 76 pixel checks; the full suite is not a pass.
Locked `flock /tmp/wine-build.lock bash tools/build.sh` passes and reproduces
the canonical `573e235d…` module. Evidence is retained in
`scratch/runs/20261031T0221Z-pirates-specular/`, including test/build logs,
renderer source patch/hash and original-asset verification.

The bounded original-asset retest **reached sailing with the new renderer**.
The successful attempt is under `final/`: UI slice 5000, cooperative execution,
Chrome 151 / ANGLE SwiftShader, canonical `573e235d…` module, and served
`d3d9-fixed.js` SHA-256 `13c8e353e63ecc11f544259aee8891f9f2ecf8a9aa0f99d0d96e2805da8791a6`.
Native Play → Crew Signups → tavern → English captain reached **St. Kitts**,
with 600 gold and 41 crew. Escape briefly opened System Options; returning
showed the sailing scene, then the ship entered town. Native Sail away →
“No matter, cast off!” returned to sea. Right and Up inputs followed; inspected
`cast-off.png`, `castoff-turn.png` and `castoff-sails.png` show changing ship
orientation and coast position. Their individual control effects are not
isolated, and no combat, voyage objective, audio or persistent save is qualified.

White terrain **persists**. The successful run has zero specular rejection
messages and no page exceptions; its console errors are 28 HTTP 404s. Thus
specular support does not resolve this visible defect. This is a different
starting port from the earlier Port Royale capture, not a frame-matched terrain
comparison, and the terrain's cause remains unproven.

The first attempt captured the title, then timed out on premature menu input
and returned to the launcher; the reload's cause is unknown. A retry correctly
refused a canonical-module/generated-map mismatch after another worker changed
the shared map. The successful run therefore serves the **first** captured host
source versions from this run, including the new renderer and canonical
`54a33f1054df7c3f` map, with a retained URL-to-hash mapping. It does not pair
the old module with the concurrently edited mirror. All 1374 original input
pins match the prior canonical run; the successful route retains 466 served
responses and 34 trusted input events, with no held keys/buttons. Own browsers,
controllers, servers and profiles were closed; no Boat/test box was used.
`recovery.txt` and `verification.json` retain the exact route and limits.
Next: investigate the actual terrain texture/material draws with a matched
scene; do not treat removing the specular rejection as a terrain fix.

## White-coast draw boundary investigation (2026-10-31)

The white coast is reproduced using the previous run's **matched** `573e235d…`
module, `54a33f1054df7c3f` map and specular renderer `13c8e353…`. There is no
terrain repair in this change: the measured renderer behavior agrees with the
submitted state, and the upstream reason for that state remains unresolved.
Evidence and a self-contained source/module recovery recipe are in
`scratch/runs/20261031T0240Z-pirates-terrain/recovery.txt`.

A bounded original sailing trace identifies a **4,936-triangle coastal draw**
that writes the pale pixels. It has stride 32, FVF `0x112` (position, normal,
one UV), no vertex colors, **no bound textures**, and null vertex/pixel shaders.
Stage 0 selects DIFFUSE; diffuse/ambient material is `(0.5,0.5,0.5,1)`, with
lighting enabled and specular disabled. The directional light's diffuse RGB is
`1.78559768`. This is not a texture decoder producing white texels: this draw
has no texture to decode. A subsequent 700-call sea trace retains neighboring
texture pixels and finds the same untextured terrain, no draw errors and no
offscreen color attachment in the bounded scene. Neither trace establishes
that all terrain draws or all frames use this path.

Read-only guest/WAT draw-state snapshots confirm null texture pointers before
the JavaScript bridge copies the draw. Original game renderer inspection finds
`NiD3DDefaultShader`, equal to the renderer's default at `+0x898`; the observed
mesh has zero property-state and shader-extra pointers at `+0xc0`/`+0xc8`.
Disassembly around `0x5c4270` shows the shader-extra lookup and default fallback;
the draw reaches `DrawIndexedPrimitive` at `0x5c43b7`. Shader counters report
12 creations and **zero refusals**, with zero declaration rejects. These facts
locate the investigation before backend pixel shading; they do not prove
whether initialization, capability handling, state emulation or original game
logic caused the absent terrain attachment. No missing-asset or lighting-root-
cause claim is made.

The retained real geometry/state is replayed through actual WebGL 1 and 2 with
an independent scalar lighting, projection, depth selection and interpolation
calculation. Both sampled points match **exactly in both versions**:
`[225,220,249,255]` and `[191,186,216,255]`. `replay-frozen.cjs` uses the exact
retained renderer sources; its four pixel assertions pass. Changing shared
lighting or substituting a texture would mask this evidence without addressing
the demonstrated default-shader/material selection. The existing all-zero
attenuation fixture failure predates this investigation; its suite was not
rerun or claimed to pass. A fresh locked `tools/build.sh` passes, but produces
a different module/map and was deliberately not substituted into this replay.

Native St. Kitts **Sail away → No matter, cast off!** returns to sea with
600 gold and 41 crew. Inspected `castoff-settled.png`,
`native-turn-after-trace.png`, `native-sails-after-trace.png` and
`sailaway-final.png` show movement past Nevis to a Port Freedom landing prompt;
Enter on “No, sail away” returns to the sailing HUD. White coast persists.
Simulation continued during diagnostics, so individual key effects are not
isolated; this does not qualify combat, voyage objectives, audio or saves.
All 50 recorded inputs are trusted and released. All 1,374 original pins and
472 served responses match; zero specular rejects/page exceptions, 28 HTTP
404s. Own browsers/controllers/ports/profile are closed; no Boat/testbox used.

Next: instrument original terrain construction near `0x4e6bc2` and the
`0x4ee360`/`0x4ec000` binding path, capturing capability results and the mesh
property/shader attachment lifecycle. `TerrainShader` is enabled at runtime;
its capability bypass flag is zero. The blocker is the unexplained absence of
terrain texturing/shader attachment before draw submission, with a recoverable
original sailing route and measured backend behavior, not a tested terrain fix.
