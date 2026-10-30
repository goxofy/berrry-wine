# DX SDK Direct3D Retained Mode samples (globe, viewer, flip3dtl)

## October 30: Globe motion verified on both repaired-build routes

Runs `20261030T2330Z-dx-globe-webgl` and
`20261030T2330Z-dx-globe-software` each contain two personally inspected
captures of the original SDK Globe executable. The shaded, textured sphere
changes orientation on both routes. This closes the earlier unverified WebGL
motion finding after GPU Execute extent repair `de2e338c4`; it does not resolve
the historical texture-band correctness question or establish pixel parity.

Both Chrome 151/ANGLE SwiftShader runs loaded retained canonical module
`d83e413fbc38ca5aa5447a7be62d10010783fd5490c98ec07c076553897950e5`.
WebGL had the owning host's `d3dimGpu` and GPU selection enabled; software
had neither. Guest threads were disabled in both. Each run verified 38 original
SDK input hashes and all 182 served-response hashes. Its `investigation.json` records
frames, build/backend evidence and cleanup: browser absent, three ports closed,
private profile removed, no Boat. The different orientations and sphere sizes
are not a same-frame comparison; FPS, full scene correctness and completion of
the historical 27-app corpus remain unqualified.

## October 30: original Tunnel WebGL motion verified after extents fix

Run `20261030T2325Z-dx-tunnel-gpu-extents` retested original `dx_tunnel`
with the canonical module retained from the passing build for GPU Execute
extent repair `de2e338c4`. Two personally inspected browser captures show
changed tunnel orientation and texture position. A bounded trace of 284
copy/present events contains 94 distinct scene-region hashes on both primary
surface and render target, excluding the text overlay.

Chrome 151/ANGLE SwiftShader loaded module
`d83e413fbc38ca5aa5447a7be62d10010783fd5490c98ec07c076553897950e5`.
All served-response hashes match their local inputs. The run's `result.json`
records module identity, captures and verified cleanup: browser exited, three
ports closed, private profile removed, no Boat. This closes the earlier
unverified WebGL motion finding for Tunnel; pixel parity, full scene correctness,
performance and completion of the 27-app corpus remain unqualified.

## October 30: Twist WebGL animation repaired

The original `dx_twist` browser run `20261030T2320Z-dx-twist-gpu-extents`
now visibly deforms and rotates its textured sphere. Three captured frames
were personally inspected. The bounded copy trace contains 101 distinct
scene-region hashes on both the primary surface and render target; changing
copy rectangles cover the sphere. Before the fix, run
`20261030T2316Z-dx-twist-copy-trace` copied only the FPS text rectangle after
the initial frame, leaving the primary scene unchanged despite target updates.

The GPU executor omitted ExecuteBuffer status extents that D3DRM consumes to
choose its windowed copy rectangle. Accepted draws now report conservative,
clipped coverage while Execute still owns that status, independently of later
batch submission or readback. Wrong-target, inactive and empty reports are
ignored. Triangles, lines, points, clipping and deferred submission have focused
coverage, including the actual compiled WASM export.

The locked canonical build and five focused D3DIM tests pass. The original
Chrome 151/ANGLE SwiftShader run loaded retained module
`d83e413fbc38ca5aa5447a7be62d10010783fd5490c98ec07c076553897950e5`;
served-response integrity and browser/port/profile cleanup are recorded in
its `result.json`. No Boat was used. This establishes visible animation for
this sample; pixel parity, complete scene correctness, performance and the
historical 27-app corpus goal remain unqualified. Earlier stationary-frame
findings below describe the previous build.

## October 30: Twist motion boundary narrowed; no repair yet

Two original WebGL diagnostic runs, `20261030T2305Z-dx-twist-motion-probe`
and `20261030T2307Z-dx-twist-frame-boundary`, used the same verified canonical
module `7e8d3194…` from source `8cfa97b0d`. Runtime-only wrappers sampled
120 distinct submitted vertex hashes and 120 distinct full readback/DIB hashes.
That establishes progressing geometry submission and readback, not visible
animation: whole-frame hashes can change with the guest FPS overlay.

Four later samples excluded the overlay and measured the same scene-region
hash, `3605449039`, while draw count advanced from 14,092 to 14,125. Three
closely spaced screenshots were personally inspected and show the same sphere
orientation. This narrows the unresolved animation gap without identifying its
cause or establishing scene correctness. No production source was changed.
Each run retains its diagnostic logs and `investigation.json`; both browsers
exited, all six ports closed, private profiles were removed, and no Boat was used.

## October 30: paired original Twist renders; motion differs

Runs `20261030T2304Z-dx-twist-browser` and
`20261030T2304Z-dx-twist-software` contain inspected original `dx_twist`
initial/final frames. Both render a dark textured object with a yellow/black
radiation symbol. Software shape and orientation change; WebGL frames appear
stationary. WebGL animation is unverified, and the cause remains undiagnosed.
This is a concrete follow-up gap rather than a scene-correctness pass.

Both loaded module `7e8d3194…` from the passing canonical build of
`8cfa97b0d`, with unchanged source hashes recorded in the copied build
manifest. Chrome 151/ANGLE SwiftShader observed guest threads enabled;
WebGL used `D3DIMGpu`, while software selected DX2–7 WAT without it.
Each run verified 39 input hashes and 38 served SDK responses. Its
`investigation.json` references captures, route/build evidence and cleanup.
Both own browsers exited, six ports closed and private profiles were removed;
no Boat was used. FPS overlays are not benchmarks. Pixel parity, complete scene
correctness and the historical 27-app goal remain unqualified.


## October 30: Tunnel renders from a verified canonical build

Runs `20261030T2317Z-dx-tunnel-browser` and
`20261030T2317Z-dx-tunnel-software` contain inspected initial/final captures
of original `dx_tunnel`: gray textured tunnel walls with yellow/black edges.
Software frames show changed orientation; WebGL animation is not established.
Chrome 151/ANGLE SwiftShader used `D3DIMGpu` on WebGL and the DX2–7 WAT
software rasterizer without `D3DIMGpu` on software. Guest threads were enabled.

The locked canonical build passed on source `8cfa97b0d`; all 1,148 tracked
build-source file hashes stayed unchanged across compilation, with no tracked
source patch. It produced module `7e8d3194…`, matching each loaded module.
This newly verified build reproduces the earlier retained module hash; it does
not retroactively establish the earlier runs' complete host/source identity.
Each run verified 39 inputs and 38 served SDK responses. Build logs, source
manifest, captures, route observations and cleanup are in its `investigation.json`.
Both browsers exited, six ports closed, and private profiles were removed.
No Boat was used. The guest FPS overlay is not a benchmark; these captures do
not establish pixel parity, full scene correctness, or completion of the 27-app corpus.


## October 30: paired original Flip3DTL browser animation

Runs `20261030T2311Z-dx-flip3dtl-browser` and
`20261030T2311Z-dx-flip3dtl-software` each contain inspected initial/final
captures of original `dx_flip3dtl`: a Windows 95 textured cube changes
orientation on both routes. The window identifies itself as Flip3D DISPLAY
HAL. The guest FPS overlay is not an independently measured benchmark.

Chrome 151/ANGLE SwiftShader used WebGL with `D3DIMGpu` in the first run;
the second selected the DX2–7 WAT software rasterizer and had no `D3DIMGpu`.
Guest threads were observed enabled in both. Both loaded retained module
`7e8d3194…`, compiled source revision unknown, and verified all 39 input
hashes and 38 served SDK response hashes. Each run's `investigation.json`
records evidence and cleanup: browser gone, three ports closed, private
profile removed, no Boat. These observations establish animated textured
output on both routes, not pixel parity, full scene correctness, performance,
or completion of the historical 27-app corpus.


## October 30: Viewer original-mesh startup failure

`20261030T2308Z-dx-viewer-browser/investigation.json` records a fresh
original `viewer.exe` browser attempt with WebGL selected. The normal registry
replaces `camera.x`, `mslogo.x`, and `sphere2.x` with tetra/cube test fixtures.
For this run only, the launch manifest instead used the original SDK files
from `dx_globe`, retaining the original Viewer executable. No fixture mesh was
fetched; 39 input hashes and 38 served SDK responses passed verification.

The inspected startup dialog says **Failed to load camera.x —
D3DRMERR_NOTFOUND**. A trusted click on OK left no Viewer windows or running
app. This does not establish a rendered original scene; prior fixture-based
Open/menu checks do not close this gap. Original `camera.x` uses binary
`xof 0303bin` ProgressiveMesh/InlineData representation; the failure's cause
remains unknown. Chrome 151/ANGLE SwiftShader loaded retained module
`7e8d3194…`, compiled source revision unknown. The browser, three listening
ports, and private profile were cleaned up; no Boat was used.

## October 30: paired original Globe browser renders

Runs `20261030T2302Z-dx-globe-browser` and
`20261030T2305Z-dx-globe-software` add inspected initial/final captures of
original `dx_globe`. Both show the titled Direct3DRM sample with a dark shaded
sphere and yellow/black textured band. Software captures show a change in
orientation; WebGL animation is not established. Their different apparent
sizes and orientations are not a pixel-parity comparison or correctness verdict.

Chrome 151 used ANGLE SwiftShader with guest threads observed enabled.
The WebGL UI/console and `D3DIMGpu` identify that route; the software UI/console
identify the DX2–7 WAT rasterizer, with no `D3DIMGpu`. The queried host
`backend` property was unavailable, and OpenGL `gl_sw_enabled()` does not
identify the D3DIM route. Both loaded retained module `7e8d3194…` (full hash
in each `loaded-module.json`), compiled source revision unknown. Each run
verified 39 input hashes and 38 fetched SDK responses. Browser processes and
servers are gone and temporary profiles removed. Evidence and limits are in
each run's `investigation.json`; no FPS, full scene correctness, current-main
build, or complete historical 27-app claim follows from these captures.

## October 30: original Boids browser animation

`scratch/runs/20261030T2255Z-dx-boids-browser/investigation.json` records a
fresh original `dx_boids` run. Both inspected frames show colored flock
triangles and cyan boundary lines, with positions changing between captures.
This registered sample uses immediate mode, separate from the retained-mode
samples discussed below.

Chrome 151 ran with ANGLE SwiftShader, WebGL selected, and guest threads
observed enabled. The host reported backend `webgl` and a `D3DIMGpu` object.
The loaded module was `7e8d3194fd189a8e0089b41ee5972b08b67fd5650d6dfbe2a2fbb9d3c323a327`;
its compiled source revision is unknown. All 39 input hashes and served SDK
asset hashes were verified. Repeated readback-shadow performance warnings
remain in the console log. This establishes animated output, not complete
scene correctness, pixel parity, FPS, or historical corpus membership.
The browser and servers were closed and its temporary profile removed.

The paired `20261030T2258Z-dx-boids-software` run uses the same retained
module and SDK inputs. Its initial/final captures were also inspected: colored
flock triangles and cyan boundaries move on the software path. The host reports
`software`, no `D3DIMGpu`, and the UI identifies the DX2–7 WAT software rasterizer.
All 39 input and 38 served SDK response hashes pass. The OpenGL
`gl_sw_enabled()` value of zero does not describe the D3DIM backend.
The captures are from different animation times, so this establishes output
on both routes without pixel parity or FPS claims. This browser and its servers
were also closed, and its profile removed.

`--app=dx_globe`, `--app=dx_viewer`, `--app=dx_flip3dtl`. The binaries are the
DirectX 5 SDK samples in `binaries/dx-sdk/bin/`, and their assets (`sphere3.x`,
`mslogo.x`, the `.ppm` textures) sit beside the exe and are mounted by the
registry entry — `node tools/gfx-app-census.js --apps=dx_globe --list` names
the families each one reaches.

They matter out of proportion to their size: they are the smallest programs in
the corpus that drive the D3DRM path end to end, so they fail faster and more
legibly than the games that share it. `tools/gfx-app-census.js` counts 10 apps
reaching d3drm and 9 reaching d3dim, including the seven `scr_*` screensavers,
which all name an identical family set and move together.

## "Failed to load sphere3.x" was never about the file (fixed 2026-09-22)

The symptom was a message box reading `Failed to load sphere3.x.
D3DRMERR_BADFILE`, which names an asset and a file-format error and is about
neither. Everything that looks guilty is innocent, in this order:

- The file is mounted. `--trace-fs` shows
  `CreateFile("sphere3.x", ...) → 0x70000001`: the open succeeds.
- The `.x` parser never runs. The failure is upstream of it, in
  `DirectXFileCreate`.
- `--trace-api` puts it exactly: `HeapAlloc(hHeap=0, dwFlags=8, dwBytes=8)`
  returns `0x00000000`. A **null heap handle**, which real Windows also fails.

The null handle is the tell. d3dxof keeps its heap in a global that its own
`DllMain` fills in, and that `DllMain` never got that far:

```
[LoadLibrary] d3dxof.dll loaded at 0x816000, dllMain=0x821040
WARNING: DllMain did not return cleanly, EIP=0x81ac0e yield=0 halt=3
```

`0x81ac0e` is the return address of the `SetEvent` in d3dxof's one-time init,
so the initializer was abandoned mid-frame — after it had taken its critical
section, before it had stored its heap. d3drm.dll aborted the same way at
`0x519720`.

**The cause was in the host, not the guest.** `lib/dll-loader.js`'s
`callDllMain` ran the initializer and, on any halt that was not a cooperative
`Sleep`, restored the caller's EIP and ESP and returned — which is precisely
what the comment above that loop says must never happen. Halt 1 (block budget
spent) and halt 3 (the host asked for control) are scheduling signals, not
completion. Fixed by resuming the initializer for both, bounded at 64 resumes.

After the fix all three DllMains report `DllMain returned, EAX=0x1`, the
message box is gone, and dx_globe runs 346804 API calls in 20000 batches
against 911 before, drawing a lit, textured sphere.

**The general lesson, which is why this is written down:** a half-initialized
DLL fails arbitrarily far from `DllMain` and never mentions it. The error it
produces is whatever the first unwritten global happens to break — here, a
file-format error for a file that had already opened. `halt=` in that warning
is the fact that separates "wanted one more slice" from "genuinely stuck", and
it is printed for that reason.

## Where they stand now

Measured 2026-09-22 at 8000 batches, one capture each, on the fix above:

| app | API calls | distinct colours | reading |
|---|---|---|---|
| `dx_globe` | 346804 @20000 | 320 | **draws** — lit textured sphere, some texture corruption in one band |
| `dx_flip3dtl` | 31726 | 77 | draws something; April's note recorded 628 colours, so check a longer budget before calling it a regression |
| `dx_viewer` | 181247 | 5 | runs the loop, near-blank |
| `scr_geometry` | 25506 | 1 | runs the loop, blank |

So the loader fix cleared the entry blocker for the whole cluster without
finishing any of them except globe. The remaining work is scene output, not
initialization — and note that a colour count is a weak instrument: it cannot
tell a black background that is correct from one that is a failure, which is
what made "black output" a single diagnosis for four different bugs in the
older notes.

`mcm` (Motocross Madness) now reaches a modal instead: *"has detected a change
in your game, video hardware or driver installation. We must now test your
video memory..."*. That is a dialog to answer, not a render bug — see
`tools/startup-modal-sweep.js`.

## Globe blank after masked Execute branches (2026-09-22)

The masked BRANCHFORWARD implementation exposed a missing PROCESSVERTICES
side effect, independently of the loader issue above. Globe sets driver status
to 0x01fff000, transforms 56 vertices, then conditionally exits the buffer if
any common standard clip-plane bit (mask 0x0003f000) remains. Vertex processing
never updated those bits, so every triangle was skipped. Trace and guest record
dumps established the sequence; a temporary control restoring only the old
assumed-zero branch comparison recovered rendering and passed the Render-menu
test (222 / 2982 / 31713 point / wire / solid lit pixels).

The main-tree fix accumulates standard homogeneous clip union/intersection
status during transformation, keeping the masked branch comparison. See
[Execute review](../d3dim-execute-data-sparse-review.md) for scope and remaining
status/extent limitations. Viewer Open/menu browser coverage passed in both
scheduling modes before this fix, but does not prove its scene is rendered.

After the fix, the full build and Globe Render-menu test pass with the same
222 / 2982 / 31713 pixel counts as the control. Viewer also passes its CLI
mesh-selection / Change Color test. These are scoped regression results, not
certification of texture quality or the whole D3DRM/screensaver cluster.

## Original SDK source now located (2026-09-22)

The Microsoft DX5 SDK archive also contains the actual samples and English Word
reference manuals. Provenance and document hashes are recorded in the
[Execute review](../d3dim-execute-data-sparse-review.md). Temporary extracted
sources are at `/private/tmp/wa-dx5-docs.59DpEl/sdk-source/cdrom/sdk/samples/`;
they are not committed. In particular, `uvis/uvis.cpp` provides a direct example
of using ExecuteData extents to drive retained-mode ForceUpdate, despite its
PROCESSVERTICES record omitting UPDATEEXTENTS. This is a useful small source
reference for replacing our viewport-sized extent approximation. The geometry
and update rectangle paths both need testing; getting nonblank pixels alone
does not verify this interaction.

## Execute extents replace viewport substitution (2026-09-22)

SETSTATUS now installs its actual rectangle; flagged PROCESSVERTICES and
clipped raster coverage expand it across executions. See the
[Execute review](../d3dim-execute-data-sparse-review.md#execute-extent-accumulation-2026-09-22)
for regression coverage and explicit native-rounding/rejection limitations.

After rebuilding, Globe's Render-menu test passes twice (all 11 items), with
point/wire/solid counts 224 / 3642 / 13535. Those are changed, not pixel-identical
to the old viewport approximation. A 150-batch capture still shows the sphere
with the previously observed texture-band defect. Viewer passes mesh selection
and Change Color on CLI, and Open/Renderer-menu browser coverage in cooperative
and threaded modes. None of these assertions is a native rendering oracle.

An isolated old-code control reproduces 222 / 2982 / 31713. SDK `globe.c` moves
the camera on each callback, so fixed block-budget screenshots need not show
the same scene after extent-driven work changes. That is an explanation to
test with frame-aligned captures, not an established pixel-equivalence result.

Uvis is present as original SDK source, but neither local SDK binary directory
contains `uvis.exe`; its ForceUpdate route remains to be built or sourced and
tested. Do not treat source inspection as an end-to-end Uvis pass.

## Frame-aligned extent comparison (2026-09-22)

Globe's camera callback is `0x4016ec`; its static animation time is the float
at `0x40b104` (xref to the 0.08 constant identifies it). Comparing the old
viewport substitution against the new extent implementation at completed
callback counts 10, 50 and 100 yields **zero differing pixels** in all 640x480
primary captures, with identical animation times. Thus the earlier fixed-budget
image difference is absent at these aligned scene checkpoints. See the
[Execute review](../d3dim-execute-data-sparse-review.md#frame-aligned-globe-ab-2026-09-22)
for artifact hashes, control procedure and limitations. The texture defect is
present in both arms; this comparison does not fix or validate it.
