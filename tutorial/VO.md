# Voice-over script: IgelkottFisheye in Live FX

One take per line. Save each take as `vo/<file>.wav` in this folder (WAV, 48 kHz, mono or stereo). Cut the silence at
the start and end of each take; the build adds 0.4 s before and 0.9 s after. A step lasts as long as its take, so
the pace is yours. A step without a recorded take keeps the synthetic voice. Then run `python3 build_video.py`.

| # | File | Line | On screen |
|---|---|---|---|
| 1 | `title.wav` | IgelkottFisheye in Assimilate Live FX. In a few minutes you will set up a project that plays an Igelkott fisheye plate straight on an LED wall, with the right colour, at 4K, at 8K, or at 15360 by 2160, from one machine. | IgelkottFisheye in Live FX / Set up a wall: 4K, 8K and 15360 × 2160 |
| 2 | `project.wav` | Create a new project. Set the format to the size of your wall, here 3840 by 2160, and the frame rate to the plate's, here 24. Turn Color Management on, with ACES 1.1 and ACEScct. | Format = wall size · Framerate = plate · Color Management On, ACES 1.1, ACEScct |
| 3 | `filler.wav` | In the Construct, choose Filler, then Black, and drop it in the first slot. This black shot is the base of the wall, and it always has the timeline's size. | Filler › Black in the first slot: the base of the wall |
| 4 | `import.wav` | Import the plate with Import Clips. | Import Clips › the plate |
| 5 | `loadno.wav` | Live FX asks whether to change the timeline to the plate's size. Answer No. The plate is square, the wall is not. | Answer No: the timeline keeps the wall's size |
| 6 | `pale.wav` | Live FX reads the plate as Rec 709, gamma 2.4. That looks flat and grey. | Default Rec709 / Gamma 2.4: flat and grey |
| 7 | `color.wav` | In Media, set Color to ACEScg, AP1, | Media › Color: ACEScg (AP1) |
| 8 | `eotf.wav` | and the EOTF to ACEScct. | EOTF: ACEScct |
| 9 | `right.wav` | Now the plate has its real contrast and colour. | Plate: ACEScg (AP1) / ACEScct |
| 10 | `length.wav` | Go back to the black shot. Click the Live FX title above the panel buttons, and set Shot Length Out to the plate's length minus one, here 2179. | Live FX menu › Shot Length Out = plate length − 1 |
| 11 | `plugins.wav` | With the black shot selected, open Plug-ins, Matchbox, and choose IgelkottFisheye2D. Click Apply On Layer. | Plug-ins › Matchbox › IgelkottFisheye2D › Apply On Layer |
| 12 | `fetch.wav` | The node starts with the black shot as its input. Click Fetch. In the Construct, drag the plate down into the input called Fisheye, and click. | Fetch… › drag the plate into the Fisheye input |
| 13 | `tag.wav` | The node reads the pixel tag in the plate, so the camera and the pointing are set for you. | Camera and Pointing: Auto (tag) |
| 14 | `inlen.wav` | In Inputs, check that Length is the plate's length, so the whole plate plays. | Inputs › Length = plate length |
| 15 | `blackpale.wav` | One more step. The black shot is sRGB, gamma 2.2, so the wall looks pale. | Black is sRGB / Gamma 2.2: the wall looks pale |
| 16 | `blackright.wav` | Set the black shot's Media to ACEScg and ACEScct, the same as the plate. | Black › Media: ACEScg (AP1) / ACEScct |
| 17 | `wall4k.wav` | That is a 4K wall, one 4K output. Yaw, Pitch, Roll and FOV aim it. FOV is the angle from the wall's left edge to its right edge. | 4K wall, 3840 × 2160: one 4K output |
| 18 | `three.wav` | For a bigger wall, give the same size to three things: the timeline, the black shot and the node. For 8K, that is 7680 by 4320, two by two 4K outputs. | Same size in three places: timeline, Black, node |
| 19 | `wall8k.wav` | The node fills the whole 8K wall. | 8K wall, 7680 × 4320: 2 × 2 4K outputs |
| 20 | `mode16.wav` | The widest wall is 15360 by 2160, four 4K outputs in a row. Give that size to the timeline, the black shot and the node, and in the node choose Mode, Equirect. | 15360 × 2160 · Mode › Equirect |
| 21 | `wall16.wav` | Now the whole sphere, 360 degrees, runs across all four outputs, from one node. Yaw turns it. | 15360 × 2160: 360° equirect across four 4K outputs |
| 22 | `monitors.wav` | Last, the viewer. On a Mac, the interface is sRGB, gamma 2.2. On Windows, choose Scene Linear. Set each output to what your LED processor expects: SDR, PQ or HLG. | Mac: sRGB / Gamma 2.2 · Windows: Scene Linear · outputs: SDR, PQ or HLG |
| 23 | `outro.wav` | That's it. The node and free demo plates are at igelkott plates dot com. | Play Igelkott plates on your wall / igelkottplates.com |
