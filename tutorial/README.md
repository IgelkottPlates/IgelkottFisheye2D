# Tutorial film: IgelkottFisheye in Live FX, a wall at 4K, 8K and 15360 × 2160

The film (2560 × 1440, 30 fps, about 3:35, one uninterrupted walk through Live FX with an animated pointer and every click highlighted, English narration and captions) shows a new user how to:

- set up the project with ACES / ACEScct;
- use Filler → Black as the base of the wall;
- bring in the plate (No to the size question, ACEScg (AP1) / ACEScct) and set Shot Length;
- put IgelkottFisheye2D on Black with Apply On Layer, and connect the plate with Fetch.. → the Fisheye input;
- set Inputs Length and Black's colour;
- use the wall sizes 3840 × 2160, 7680 × 4320 (2 × 2) and 15360 × 2160 (four 4K outputs in a row, Mode: Equirect);
- set up the viewer.

The screenshots in `images/` were taken on 2026-11-24 in Assimilate Live FX 9.9 on a Mac at 2560 × 1440, with plate A013C004 from
the free demo plates. They show only the Live FX window.

The screenshots and the recorded narration (`vo/`) are not in the Git repository (35 MB); a clone cannot build the film without them.

## Build

1. Edit text or zoom in `scenes.json`. The fields are:
   - `say`: narration;
   - `cap`: caption;
   - `cx`/`cy`/`z`: zoom target in image pixels;
   - `card`: title or outro card;
   - `clicks`: what is clicked, as boxes in image pixels (`kind`: click, double, drag, drop);
   - `cap_top`: puts the caption at the top, for a scene whose subject sits at the bottom edge.
2. Recorded narration: one take per step in `vo/<step>.wav`, see `VO.md`.
3. Run `python3 build_video.py [voice]` (default voice Daniel; `ONLY=id1,id2` for a preview). It needs ffmpeg, ffprobe and Pillow.
   - Intermediate files go to `~/Library/Caches/Igelkott/IgelkottLiveFXFisheye/tutorial`.
   - The film goes to `~/Movies/IgelkottFisheye Tutorial/`.
