# Testing IgelkottFisheye in Live FX on a Mac

On Windows, Live FX runs the Matchbox shader in OpenGL. On a Mac, Live FX translates it to Metal first, so a shader
that works on Windows can still fail to compile or draw differently on a Mac. Versions 0.14 to 0.17 (the pixel tag,
Auto (tag), Offset after the projection, the new Equirect, Split in Equirect, Right Offset) have only been tested on
Windows. The Mac was last checked before 0.14 (row order seen 2026-10-05). This list checks the current version on a
Mac.

Write each result into `PROJECT.md` with the date, the Mac's name and the Live FX version. A screenshot helps for
every step that says **look**.

## Before you start

- [ ] A Mac with Assimilate Live FX 9.9 that has been started at least once.
- [ ] The test clips: the `Store` set (Sony Venice 2, ProRes 4444, 5760², ACEScct AP1, with the pixel tag), copied to
      the Mac. Use at least A013C004 (zenith, car) and A001C016 (nadir, drone). Use `.mov` files only.
- [ ] One `.mov` clip **without** a pixel tag, for example any fisheye clip made before 2026-11-19. Or take
      `pyxis_zenith_notag.png` from `python3 tools/make_testplates.py <folder>` and make it a `.mov`, for example
      `ffmpeg -loop 1 -i pyxis_zenith_notag.png -t 5 -c:v prores_ks notag.mov`. Live FX does not read PNG the right
      way up.
- [ ] For reference, the Windows screenshots of the same steps (in this session, or ask for them).

## 1. Install

- [ ] Quit Live FX.
- [ ] Copy `matchbox/IgelkottFisheye2D.glsl` and `matchbox/IgelkottFisheye2D.xml` (from the repository or the v0.17
      release) to `/Library/Application Support/Assimilator/Plugins/Matchbox/shaders`. Replace the old files.
- [ ] Start Live FX. It only reads shaders at start-up.

## 2. Does it compile?

- [ ] Make a project with A013C004. On the clip, open **Plug-ins.. → Matchbox → shaders → IgelkottFisheye2D →
      Apply On Node**.
- [ ] **Look:** a road with the car's bonnet at the bottom, not black, not red, not an error frame.
- [ ] Open **Log Files..** on Live FX's start page and search for `Matchbox`, `IgelkottFisheye`, `Metal`, `error`.
      Write down any shader error word for word.

If it does not compile, stop here and send the log lines. Nothing else on this list can be tested.

## 3. The panel

- [ ] **Look:** four columns.
      - **Plate:** Camera: Auto (tag), Pointing: Auto (tag), Offset X, Offset Y.
      - **View:** Yaw, Pitch, Roll, FOV, Mode: Wall.
      - **Split:** Split, Split Position.
      - **Right Wall:** Right Yaw, Right Pitch, Right Roll, Right FOV, Right Offset X, Right Offset Y.
- [ ] Hover over a control: the tooltip is in English.

## 4. Orientation (the most important Mac check)

Use Media → Image Format **HD 1080-24**, Mode Wall, Yaw 0, Pitch 0, FOV 90.

- [ ] **A013C004 (zenith, look):** the sky is at the top, the road and bonnet at the bottom, the horizon level.
      Signs and number plates read left to right, so the picture is not mirrored.
- [ ] **Yaw 90 (look):** the view turns right. Yaw −90 turns left.
- [ ] **Pitch 30 (look):** the view tilts up.
- [ ] **A001C016 (nadir, look):** water and land at the bottom, sky at the top. With Yaw 180 the drone's legs show at
      the top of the picture.

If the picture is upside down or mirrored, note which, with a screenshot. Live FX on the Mac reads rows in a different
order than on Windows, and the shader then needs a Mac-specific fix.

## 5. Camera and Pointing (the pixel tag)

- [ ] **The Venice clips with Auto / Auto:** there is no yellow warning sign in the top left corner.
- [ ] **Camera: PYXIS 12K on a Venice clip (look):** the picture changes, because it is the wrong lens. Set it back to
      Auto (tag).
- [ ] **Pointing: Zenith on A001C016 (look):** the picture is wrong, upside down or the wrong part. Set it back to
      Auto (tag).
- [ ] **The clip without a tag (look):** black, NOT AN IGELKOTT CLIP in yellow across the middle and a small yellow
      warning sign in the top left corner, with Auto and with Camera/Pointing chosen by hand (0.20).
- [ ] **Camera: Z-Cam E2 S6 on a Venice clip (look):** a picture (the Z-Cam's own lens model, 0.18), no warning sign.
- [ ] **FOV 90, Yaw 45 (look):** what was straight ahead at Yaw 0 is now at the left edge: FOV is horizontal (0.18).

## 6. Offset and Split (Mode Wall)

- [ ] **Offset X 200:** the picture moves right. **Offset Y 200:** the picture moves up. Set both back to 0.
- [ ] **Split on, Split Position 50, Right Yaw 90 (look):** two walls side by side with a sharp edge in the middle. The
      right wall looks to the right.
- [ ] **Offset X 200 with Split on:** only the left wall's picture moves, and the edge stays.
- [ ] **Right Offset Y 200:** only the right wall's picture moves up. Set everything back to 0 and turn Split off.

## 7. Mode Equirect

- [ ] **Format 2:1** (Custom 3840 × 1920), Mode Equirect, Yaw 0 **(look):** the whole sphere. Straight ahead is in the
      middle, the horizon is level.
- [ ] **Yaw 90:** the panorama scrolls sideways. Pitch tilts it, Roll turns it. Set them back to 0.
- [ ] **Format 32:9** (Custom 7680 × 2160) **(look):** 360° across the width and not stretched (houses and boats keep
      their shape), cropped at the top and bottom.
- [ ] **Split on, 50 %, Right Yaw 180 (look):** forward on the left half, backward on the right half, together the
      whole 360°. Compare with the Windows screenshot.
- [ ] **Format 16:9** (HD 1080-24), Mode Equirect, Split off: black bands at the top and bottom, past the poles.

## 8. Canvas sizes and playback

For each size, play the clip and write down whether it plays in real time.

- [ ] 4K UHD (3840 × 2160)
- [ ] 8K UHD (7680 × 4320)
- [ ] Custom 15360 × 2160

## 9. Saved projects

- [ ] Set a node to non-zero values (for example Offset X 50, Yaw 20, Mode Equirect, Split on, Right Offset Y 30) and
      leave with **Close Project**. Reopen the project: all the values are still there.
- [ ] If an older project with the node exists on the Mac, open it. Write down whether any value (Offset, Mode) loaded
      wrong. On Windows this happened after controls were added.

## 10. Colour (optional)

- [ ] Media → Data Format: Color ACEScg (AP1), EOTF ACEScct on the Store clips. Settings → Monitors → Interface:
      Rec709, Gamma 2.4. **Look:** normal contrast. (On Windows the Interface needs Scene Linear instead of Gamma 2.4,
      because Windows encodes the viewer itself; write down which one looks right on the Mac.)

## 11. Store in NotchLC: file weight and max fps (8K canvas)

The same test as on Windows (2026-11-22, `PROJECT.md`, "Store i NotchLC: storlek och tyngd"), but the Mac has a faster
disk and Live FX's **Free Run** plays as fast as it can instead of at the clip's rate, so the real maximum shows. On
Windows the fisheye with the node stopped at 25 fps only because that is the clip's rate, and the 16K equirect was
limited by the disk (1.3–1.5 GB/s).

The files: `Store/_NotchLC/`. The fisheye NotchLC files carry the wrong name `*_ProRes4444_1.mov` (plus
`A007C001_220127SK_fisheye_Gamma-ACEScct_AP1.mov`). The 16K equirects from FisheyetoEqui are named
`*_16K360_ProRes422HQ_1.mov` but are NotchLC. A fisheye needs 0.57–0.79 GB/s, an equirect 1.4–2.1 GB/s.

### 11a. The files (Terminal)

- [ ] `brew install ffmpeg` if `ffmpeg -decoders | grep notchlc` shows nothing.
- [ ] Measure all 18 files on the fast disk. Each file is copied there, measured and deleted, one at a time (an equirect
      is up to 193 GB):

      python3 tools/bench_notchlc.py --store "/Volumes/igelkottstore.com/2025/Free Demo 2025/Store" \
          --work "/Volumes/<fast disk>/IgelkottBench" --out ~/IgelkottBench/bench.jsonl

      It can be stopped and started again; finished files are skipped. Each line has the size, MB per frame, the read
      rate needed, the disk's read rate past the file cache, the max fps from the disk, and ffmpeg's CPU decode rate.
      Copying from the NAS takes most of the time (hours).

### 11b. Live FX, max fps with Free Run (look)

- [ ] Copy A007C001 to the fast disk in both forms (fisheye NotchLC and equirect NotchLC). Use `--only` and `--keep`
      with the script above, or copy them by hand.
- [ ] New project, 7680 × 2160, 25 fps, ACES on (ACEScct). Both clips: Media → Data Format Color ACEScg (AP1), EOTF
      ACEScct.
- [ ] Fisheye: the node with defaults (Auto/Auto, Wall, Yaw 0, FOV 90), 7680 × 2160 out.
- [ ] Equirect: **Plug-ins → Assimilate Inc → Effects VR → Eq->2D Transformer**, FOV **31.42** (Eq->2D's FOV is
      vertical; 31.42 on 7680 × 2160 is 90° horizontal, the same as the node), 7680 × 2160 out.
- [ ] Set playback to **Free Run**. Write down where the setting is in Live FX 9.9 on the Mac, because it is not yet in
      `PROJECT.md` and was not found in Assimilate's documentation.
- [ ] Play each clip for 10 seconds or more and write down:
      - fps: Live FX's own fps display, if it has one, or the frame counter over a timed stretch (frames ÷ seconds);
      - disk read: `iostat -d -w 1 <disk>` in Terminal, or Activity Monitor → Disk;
      - GPU and CPU: Activity Monitor → Window → GPU History, plus Live FX's CPU %.
- [ ] Do the same for the fisheye **without** the node, so the decode alone and the node's cost can be told apart.
- [ ] If there is time: the node at 15360 × 2160 out (Custom), Free Run.
- [ ] **Look:** the picture is right in Free Run too (no tears, no frames repeated on the canvas).

For comparison (Windows, Intel 660p, Radeon RX 9070 XT, not Free Run): the fisheye with the node played at 25 fps (real
time) at 784 MB/s, 3 % CPU and about 8 % GPU. The equirect with Eq->2D played at 10–11 fps at 984 MB/s and 42 % GPU
compute.

### 11c. The picture differences (optional)

`python3 tools/compare_eq2d.py <Store> <clip without .mov> <out folder>` measures the shift, sharpness, colour and
edge differences between the node and FisheyetoEqui → Eq->2D on the ProRes files (`Store/*.mov`, `Store/_Equi/`). It
compares the files, not Live FX, so it gives the same numbers on any machine. Run it on the Mac only to check that, or
for new clips. It needs `pip3 install numpy opencv-python`. Put the out folder outside the project.

## Afterwards

- Write the results into `PROJECT.md` under the version, with the date, the Mac and the Live FX version, plus anything
  that differed from Windows.
- If anything fails, open an issue with the log lines and screenshots.
- `python3 tools/verify_mac.py` runs the cases of `tools/verify_windows.py` on the Mac (Live FX version only; PIXERA needs
  GLSL 4.50 and is tested on Windows). It compiles the shader with Apple's GLSL 1.20, not through Live FX's Metal
  translation, so the steps above are still needed. `build-app.sh` runs it before it builds the
  Mac installer.
