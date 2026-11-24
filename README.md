# IgelkottFisheye

Play a square fisheye driving plate straight onto LED walls, through the lens model, with one resampling.

IgelkottFisheye takes the fisheye clip (PYXIS 12K or Sony Venice 2 with the Entaniya HAL 250, lens pointing up or down,
any size) and draws a flat wall view from it: Yaw, Pitch, Roll and FOV, like an equirect-to-2D transform, but without
going through an equirect first. It is the same maths IgelkottStage uses, written once in GLSL and built for each player.

| Player | Status | Files |
|---|---|---|
| Assimilate Live FX (Windows, Mac) | Works, tested on real plates | `matchbox/IgelkottFisheye2D.glsl` + `.xml` |
| PIXERA (AV Stumpfl) | Built and tested on a graphics card; not yet seen inside PIXERA | `pixera/IgelkottFisheye.glsl` |
| Nuke, Nuke Stage, Flame, Unreal, Notch, Smode, disguise, ISF hosts… | Not yet: see [docs/PLAYERS.md](docs/PLAYERS.md) | |

What it does on the wall, with numbers: [IgelkottFisheye on the Wall](https://igelkottplates.github.io/IgelkottFisheye2D/).

Help with the other players is welcome: see [CONTRIBUTING.md](CONTRIBUTING.md).

## Install

### Live FX on Windows

Download `IgelkottFisheye-Windows.zip` from [Releases](../../releases), unpack it and double-click
`Install IgelkottFisheye.cmd`. Restart Live FX. The node is under **Plug-ins → Matchbox → shaders → IgelkottFisheye2D**.

By hand: copy `matchbox/IgelkottFisheye2D.glsl` and `matchbox/IgelkottFisheye2D.xml` to
`C:\ProgramData\Assimilator\plugin64\Matchbox\shaders` and restart Live FX.

### Live FX on Mac

Download `IgelkottFisheye-Mac.zip` from [Releases](../../releases), unpack it and copy `IgelkottFisheye2D.glsl` and
`IgelkottFisheye2D.xml` to `/Library/Application Support/Assimilator/Plugins/Matchbox/shaders` (Finder: Go → Go to
Folder…). Restart Live FX. The zip's `README.txt` has the steps and a one-line Terminal command.

### PIXERA

See [pixera/README.txt](pixera/README.txt).

## Using it

Put one node on the fisheye clip for each wall.

- **Camera** and **Pointing**: on **Auto (tag)**, the default, the camera and whether the lens pointed up (zenith) or
  down (nadir) are read from a small black and white pixel tag in the plate's corners (written by IgelkottDarkroom and
  Fisheye to Equi). Or choose them by hand. A plate without the tag is not played: the output is black with NOT AN IGELKOTT CLIP / IGELKOTTPLATES.COM and a yellow warning sign.
- **Offset X / Y** move the finished picture, in output pixels (PIXERA: % of the height); with Split on, the left
  wall's picture, and **Right Offset X / Y** the right wall's. The plate must be centred.
- **Yaw, Pitch, Roll, FOV**: the wall's view. FOV is the horizontal angle, from the wall's left edge to its right edge (with Split on, each wall's own width).
- **Mode**: Wall (a flat view) or Equirect: 360° over the whole width with square degrees, aimed with Yaw, Pitch and
  Roll, so the whole sphere at 2:1 and cropped top and bottom on wider canvases such as 32:9.
- **Split**: two walls side by side from one plate, with a sharp edge at Split Position; the right wall has its own
  Right Yaw / Pitch / Roll / FOV and Right Offset. In Equirect each wall is a window at the same scale, centred on its
  own Yaw / Pitch / Roll (Split 50 % with Right Yaw 180 gives the whole 360° side by side).

Use `.mov` clips in Live FX. PNG sequences are not supported: Live FX reads them upside down.

After updating the node, check its values in saved projects: Live FX has been seen loading wrong values (Offset, Mode)
into existing nodes when a version adds controls, and Reset does not fix Offset. Since 0.17, Mode Equirect is aimed with
Yaw, Pitch and Roll, so a node with leftover wall angles shows a rotated sphere.

## How it is built

The shader source is in `shader/`: `core.glsl` (the lens, the pixel tag, the warning sign), one thin wrapper per player
and the Live FX panel `IgelkottFisheye2D.xml`. The files in `matchbox/` and `pixera/` are generated from it:

```
python tools/build_shaders.py           # writes matchbox/ and pixera/
python tools/build_shaders.py --check   # 0 when they are up to date
python tools/verify_windows.py          # Windows: draws both on the graphics card, compares every pixel with the lens model
python3 tools/verify_mac.py             # Mac: the same cases for the Live FX version
```

Only Python 3 is needed, with no packages. The camera numbers are in `shader/cameras.json`. Don't edit them by hand,
because they come from Igelkott's lens package. `tools/verify_windows.py` fails if any output pixel lands more than half
a source pixel from where the lens model puts it, at 8040 px.

## Licence

The IgelkottFisheye Licence, see [LICENSE](LICENSE). You may use and change IgelkottFisheye, also for commercial work,
but only to play back plates from Igelkott Film AB ([igelkottplates.com](https://igelkottplates.com)). Using it with
other footage, or selling or redistributing it, is not allowed. Changes are shared by contributing them here.
