# IgelkottFisheye in other players

The goal: play a square fisheye plate (PYXIS 12K or Sony Venice 2 with the Entaniya HAL 250, zenith or nadir) straight
onto LED walls in every major player, with the same numbers everywhere, and let the community add the players we do
not use ourselves. This page maps the players and how each one could run the effect.

Mapped 2026-11-20. Facts marked *unverified* come from general knowledge or a forum post, not from the vendor's own
documentation; check them before starting a port.

## What a host has to offer

The effect is one fragment (pixel) shader. `shader/core.glsl` needs the host to give it:

- **Random access to the source**: read the plate at any point, not only at the output pixel. The lens maps every wall
  pixel to an arbitrary point in the fisheye, and the pixel tag reads 80 cells in the corners.
- **The output pixel's position and the output size**, to build the wall's view (Yaw, Pitch, Roll, horizontal FOV over the wall's width).
- **Floats, `atan2`, fixed-length loops and 3 × 3 matrices.** No integer bit operations and no arrays, so the same
  text also compiles as GLSL 1.20.
- **Parameters**: popups (Plate, Camera, Pointing, Mode) and floats (Yaw, Pitch, Roll, FOV, Lens Offset, Split).

A host that can only apply a fixed LUT, a colour grade or an STMap-free "effect stack" cannot run it. A host that takes
an STMap or UV map could play a *baked* version (one map per camera, pointing and view), without the tag.

## The map

| Player | Used for | How it runs custom code | Language | Port | Status |
|---|---|---|---|---|---|
| **Assimilate Live FX** | ICVFX playback, grading | Matchbox node | GLSL 1.20 + XML | done | **0.14, tested in the GUI** (`matchbox/`) |
| **PIXERA** (AV Stumpfl) | Media server | GLSL effect file | GLSL 4.50 | done | **0.14, tested against PIXERA's own Equirectangular, not inside PIXERA** (`pixera/`) |
| **Autodesk Flame** (macOS, Linux) | Finishing | Matchbox (the format Live FX adopted) | GLSL 1.20 + XML | the Live FX files, or a build without the row flip | first look in Flame needed (below) |
| **Foundry Nuke Stage** | ICVFX playback on LED walls | Custom node: GLSL `main()`, input `src0()` / `absolute_src0(uv)`, output `dst0` ([docs](https://learn.foundry.com/nuke-stage/1.1v3/content/reference_guide/nodes/utility/custom_node.html)) | GLSL | new wrapper around `core.glsl` | first look in Nuke Stage needed (below) |
| **Foundry Nuke** | Compositing, plate prep | BlinkScript kernel, `eAccessRandom` source ([docs](https://learn.foundry.com/nuke/developers/16.0/BlinkUserGuide/BlinkKernelAPIReference/Images/RandomAccess.html)) | Blink (C++-like) | hand port of the core | not started |
| **Unreal Engine** (nDisplay) | Most LED volumes; also Pixotope, Zero Density, Aximmetry DE *(unverified)* | Material with a Custom (HLSL) node on a Media Plate; the material must have a `MediaTexture` parameter ([docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/the-media-plate-actor-in-unreal-engine)) | HLSL | HLSL core + material | not started |
| **disguise** | Media server, ICVFX | No custom shader layer found in its effect layers ([docs](https://help.disguise.one/designer/layers/layer-types/effect/effect-layers-overview)); likely route: a Notch block *(unverified)* or Unreal via RenderStream | via Notch or Unreal | depends on those | not started |
| **Notch** | Real-time graphics, runs inside disguise | Custom Shader post effect, `.fx` files ([docs](https://manual.notch.one/2026.2/en/docs/workflows/working-with-custom-shaders/)) | HLSL | HLSL core + `.fx` | not started |
| **Smode** | Media server, compositing | Shader generator ([docs](https://www.smode.io/doc/ref/compo/2d/generator/shader-generator.htm)); also loads ISF | GLSL | GLSL wrapper or ISF | not started |
| **TouchDesigner** | Interactive, media server | GLSL TOP *(unverified details)* | GLSL | GLSL wrapper | not started |
| **Ventuz** | Broadcast, media server | Custom Effect Shader layer ([docs](https://www.ventuz.com/support/help/V8_01/NodeLayerCustomEffectShader.html)) | HLSL | HLSL core | not started |
| **ISF hosts**: MadMapper, Millumin, VDMX, Modulo Player, Smode, CoGe, Synesthesia; After Effects via ISF4AE, Final Cut Pro and Motion via ISF for Motion ([list](https://docs.isf.video/using_isf)) | Projection mapping, VJ, editing | ISF: one GLSL file with a JSON header for the controls | GLSL | one ISF file reaches all of them | not started |
| **Adobe After Effects** | Compositing | Native effect plugin (SmartFX, 32 bpc); no custom shader layer in After Effects 27 | Rust ([after-effects](https://crates.io/crates/after-effects) crate) + the DCTL kernel compiled as C++ | `ae/`, same kernel as Resolve | done in 0.23: tested in After Effects 27.0 (Mac); Windows build not yet tested |
| **DaVinci Resolve / Fusion** | Grading, editing | Fusion Fuse with a DCTL GPU kernel (a Color page DCTL only sees the clip already scaled to the timeline) | DCTL (CUDA-like C) + Lua | `shader/core.dctl`, a hand port of the core | done in 0.23: `resolve/IgelkottFisheye.fuse`, tested in Resolve Studio 21.1 (Mac) |
| **Resolume** | VJ, media server | FFGL plug-ins; ISF reported to work in Resolume Wire *(unverified)* | C++ / GLSL | FFGL or Wire | not started |
| **vvvv gamma** | Creative coding, media server | Shader files | SDSL (HLSL-like) | HLSL core | not started |
| **Hippotizer** (Green Hippo), **Watchout** (Dataton), **Aximmetry**, **Brainstorm** | Media servers, virtual studio | No custom shader route found in this search | ? | ? | ask the vendors or their users |

## Suggested order

1. **Flame**: costs nothing (the Live FX files), only needs a test in Flame.
2. **Nuke Stage**: built for LED walls and takes GLSL, so `core.glsl` with a small wrapper.
3. **ISF**: one file reaches MadMapper, Millumin, Smode, VDMX, Modulo Player, After Effects and Final Cut Pro.
4. **Unreal Engine**: the largest share of LED volumes; needs an HLSL version of the core, which then also serves
   Notch (and so disguise), Ventuz and vvvv.
5. **Nuke (BlinkScript)**: plate prep and comp.
6. ~~**Resolve**~~: done (0.23, a Fusion Fuse).
7. The rest on request from people who use them.

## First look in Flame and Nuke Stage

Neither player's documentation settles the points that decide whether the wall comes out upright, so each port starts
with one test in the player itself. Use a `.mov` plate with the pixel tag (any clip from Fisheye to Equi 1.94 or later).

### Flame

Copy `matchbox/IgelkottFisheye2D.glsl` and `.xml` to Flame's Matchbox folder, put the node on the clip, leave everything
at the default (Plate Auto, Mode Wall, Yaw 0, FOV 90) and look at the wall:

- **Upright, no yellow warning sign**: Flame lays images out top row first like Live FX does for `.mov`. The Live FX files
  are the Flame files; nothing to build.
- **Turned 180°** (sky at the bottom) and the warning sign in the bottom left, upside down: Flame lays images out bottom
  row first, as Live FX does for PNG. Flame then needs its own build without the row flip (`q.y = h - q.y` and the
  source read turned the other way), a few lines in `tools/build_shaders.py`.
- **Black or a compile error**: send the error from Flame's shell or log.

Write down the Flame version and the platform (macOS or Linux).

### Nuke Stage

The Custom node's documentation shows the input as `src0()`, `offset_src0(vec2)`, `absolute_src0(vec2 uv)` and
`size_src0()`, and the output as `dst0`. It does not say whether `absolute_src0` takes fractions or pixels, how a node
finds the pixel it is drawing, where row 0 is, or how to give the node controls. Paste this into a Custom node on a
fisheye plate:

```glsl
void main() {
    vec2 s = size_src0();
    vec2 p = gl_FragCoord.xy;
    dst0 = p.x < 0.5 * s.x ? absolute_src0(p / s) : absolute_src0(p);
    if (p.y < 0.05 * s.y) dst0 = vec4(1.0, 0.0, 0.0, 1.0);
}
```

- **It compiles** → `gl_FragCoord` works, and the effect can find its pixel.
- **The left half shows the plate the right way round** → `absolute_src0` takes fractions; **the right half does** →
  it takes pixels.
- **The red stripe is at the top** → row 0 is the top; **at the bottom** → row 0 is the bottom. If the half that shows
  the plate shows it upside down, the source and the output count rows from different ends.
- Also note: can the Custom node have controls (Yaw, FOV …), or must they be numbers at the top of the source? Can its
  output be a different size from its input (a 16:9 wall from a square plate)?

With these answers the Nuke Stage version is `shader/core.glsl` with a small wrapper, and it is tested on a GPU here the
same way as Live FX and PIXERA before it goes to Nuke Stage.

## How a port is added

- The maths lives in one place: `shader/core.glsl` (lens model, nadir turn, pixel tag, warning sign). A new **GLSL** host
  gets a wrapper next to `shader/matchbox.glsl` and `shader/pixera.glsl`, and an output in `tools/build_shaders.py`.
- An **HLSL** host should get its core generated from `core.glsl` by `tools/build_shaders.py` (type names, `mul()`
  order for matrices, `fmod` versus `mod`), not a hand-kept copy, so the camera numbers keep one source.
- **C-like** hosts (BlinkScript, DCTL) need a hand port; the test must then compare it with the lens model.
- Every port is tested the same way: `tools/verify_windows.py` draws the effect on a real GPU and compares each pixel with
  the lens model (`FisheyeLens.point`), within 0.5 source pixels at 8040, and reads the pixel tag test vectors. A port is
  not done until it has been seen in the player itself, upright, on a `.mov` plate.
- Camera numbers come only from the IgelkottFisheyeLens package; the pixel tag rules only from its `PixelTag`.

## Before others can help

- The camera numbers are published in `shader/cameras.json`, copied from Igelkott's lens package by
  `tools/build_shaders.py`. A clone can rebuild and run `tools/verify_windows.py` without the package. The tag test
  vectors are inside the test itself.
- The PIXERA chain test needs PIXERA's own `Equirectangular` effect, which is not ours to publish. Without it, that test
  is skipped.
- Licence: the IgelkottFisheye Licence (`LICENSE`): use, also commercially, only to play back Igelkott plates.
