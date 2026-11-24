"""Builds the tutorial film: one uninterrupted walk through the program, with an animated mouse pointer and every
click highlighted. The whole program window is on screen all the time; the caption has its own band below it.
Narration, a short dissolve between steps, a title card first and an outro card last
(style: _atlas/knowledge/video/instruktionsfilm.md).

    python3 build_video.py [voice]          # ONLY=id1,id2 renders just those steps, for a preview

Narration: a recorded take vo/<step id>.wav (or .aif/.aiff/.m4a/.mp3) is used when it exists; otherwise macOS say
with the given voice (default Daniel). A step lasts as long as its narration plus the pauses.

A step may zoom (z, cx, cy in screenshot pixels) to see something better; the zoom always starts from the whole
picture. Everything is drawn frame by frame in Pillow at sub-pixel precision (ffmpeg's zoompan rounds to whole
pixels and shakes).

Needs ffmpeg/ffprobe and Pillow. Screenshots: images/ (the Live FX window, 2560 x 1440). Film: 2560 x 1440.
Intermediate files go to ~/Library/Caches/Igelkott/IgelkottLiveFXFisheye/tutorial; the film to
~/Movies/IgelkottFisheye Tutorial/.
"""
import json, math, os, shutil, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

S = Path(__file__).resolve().parent
OUT = Path.home() / "Library/Caches/Igelkott/IgelkottLiveFXFisheye/tutorial"
FILM = Path.home() / "Movies/IgelkottFisheye Tutorial"
OUT.mkdir(parents=True, exist_ok=True); FILM.mkdir(parents=True, exist_ok=True)
VOICE, RATE, FPS = (sys.argv[1] if len(sys.argv) > 1 else "Daniel"), "178", 30
W, H = 2560, 1440                      # the film
SW, SH = 2560, 1440                    # the screenshots (Live FX full screen at 2560 x 1440)
IW, IH = 2304, 1296                    # the program window on screen: whole, at the top, 0.9 x
IX, IY = (W - IW) // 2, 0
SC = IW / SW
BAND = H - IH                          # caption band below the window
FF = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
FP = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
HN = "/System/Library/Fonts/HelveticaNeue.ttc"
# IgelkottDesign tokens (shader/tokens.json is a copy): accent cyan, text white; dark surface as the HUB film
TOK = json.loads((S.parent / "shader/tokens.json").read_text())["color"]
ACCENT, TEXT = TOK["accent"], TOK["text"]
ACC = tuple(int(ACCENT[i:i + 2], 16) for i in (1, 3, 5))
SURFACE = (11, 14, 18)
VO = S / "vo"
DISSOLVE, EDGE = 0.4, 0.5              # dissolve between steps; fade from/to black at the film's start and end
scenes = json.loads((S / "scenes.json").read_text())
ONLY = [x for x in os.environ.get("ONLY", "").split(",") if x]
if ONLY:
    scenes = [s for s in scenes if s["id"] in ONLY]


def font(size, idx):
    return ImageFont.truetype(HN, size, index=idx)


def run(*a):
    subprocess.run(a, check=True)


def dur(p):
    return float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True, check=True).stdout)


def ease(t):
    return (1 - math.cos(math.pi * min(max(t, 0), 1))) / 2


# ---------- pictures ----------

def background():
    """Dark surface with a soft teal glow in the middle, like the HUB cards."""
    img = Image.new("RGB", (W, H), SURFACE)
    glow = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(glow)
    for r in range(930, 0, -12):
        d.ellipse((W / 2 - r * 1.3, H / 2 - r, W / 2 + r * 1.3, H / 2 + r), fill=int(60 * (1 - r / 930) ** 1.5))
    return Image.composite(Image.new("RGB", (W, H), (0, 70, 82)), img, glow)


def centred(d, y, text, f, fill):
    d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


def card(title, sub):
    img = background(); d = ImageDraw.Draw(img)
    centred(d, 560, title, font(122, 1), TEXT)
    centred(d, 728, sub, font(61, 2), ACCENT)
    return img


def caption(text):
    """The caption in its own band below the program window, so it never covers the program."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if text:
        d = ImageDraw.Draw(img); f = font(56, 1)
        w = d.textlength(text, font=f)
        d.text(((W - w) / 2, IH + (BAND - 66) / 2), text, font=f, fill=TEXT)
    return img


def cursor_sprite(scale=2.0):
    """A macOS-style arrow, white with a black edge, drawn 4x and scaled down for smooth edges."""
    k = 4; pts = [(0, 0), (0, 25), (6, 19), (10.5, 28.5), (14, 27), (9.8, 17.8), (18, 17.8)]
    size = (int(24 * k * scale), int(34 * k * scale))
    im = Image.new("RGBA", size, (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    poly = [(2 * k + x * k * scale, 2 * k + y * k * scale) for x, y in pts]
    d.line(poly + [poly[0]], fill=(0, 0, 0, 255), width=int(5 * k * scale))
    d.polygon(poly, fill=(255, 255, 255, 255))
    d.line(poly + [poly[0]], fill=(0, 0, 0, 255), width=int(1.6 * k * scale))
    return im.resize((size[0] // k, size[1] // k), Image.LANCZOS)


CURSOR = cursor_sprite()
CURSOR_DOWN = CURSOR.resize((int(CURSOR.width * 0.88), int(CURSOR.height * 0.88)), Image.LANCZOS)


# ---------- narration ----------

def narration(i, sc):
    """The step's sound, exactly n frames long: 0.4 s silence, the take (recorded or say), then a pause."""
    take = next((VO / f"{sc['id']}{e}" for e in (".wav", ".aif", ".aiff", ".m4a", ".mp3")
                 if (VO / f"{sc['id']}{e}").exists()), None)
    if take is None:
        take = OUT / f"{i:02d}.aiff"
        run("say", "-v", VOICE, "-r", RATE, "-o", str(take), sc["say"])
    raw = OUT / f"{i:02d}_raw.wav"
    run(FF, "-loglevel", "error", "-y", "-i", str(take), "-af", "apad=pad_dur=0.9,adelay=400|400",
        "-ar", "48000", "-ac", "2", str(raw))
    n = int(round(dur(raw) * FPS))
    wav = OUT / f"{i:02d}.wav"
    run(FF, "-loglevel", "error", "-y", "-i", str(raw), "-af", "apad", "-t", f"{n / FPS:.6f}",
        "-ar", "48000", "-ac", "2", str(wav))
    return wav, n


# ---------- the walk ----------

def centre(c):
    x0, y0, x1, y1 = c["box"]
    return ((x0 + x1) / 2, (y0 + y1) / 2)


def arrivals(clicks, d):
    """When the pointer reaches each target: spread over the step, leaving time to read."""
    if not clicks:
        return []
    t0, t1 = 0.9, max(1.2, d - 0.9)
    seg = (t1 - t0) / len(clicks)
    return [t0 + seg * (j + 0.6) for j in range(len(clicks))]


def view(zz, cx, cy):
    """The part of the screenshot on screen at zoom zz around (cx, cy), screenshot pixels."""
    w, h = SW / zz, SH / zz
    return min(max(cx - w / 2, 0), SW - w), min(max(cy - h / 2, 0), SH - h), w, h


def step(sc, n, base, cap, ptr0, show_ptr):
    """Yield the step's frames: the whole window (zooming in from the whole picture only if the step asks for it),
    highlights, the pointer starting where it last was (ptr0, screen pixels), and the caption."""
    d = n / FPS
    z, cx, cy = sc.get("z", 1.0), sc.get("cx", SW / 2), sc.get("cy", SH / 2)
    clicks = sc.get("clicks", []); arr = arrivals(clicks, d)
    whole = base.resize((IW, IH), Image.LANCZOS)
    canvas = Image.new("RGBA", (W, H), SURFACE + (255,))
    for k in range(n):
        t = k / FPS; e = ease(k / max(n - 1, 1)) if z > 1 else 0
        zz = 1 + (z - 1) * e
        x0, y0, w, h = view(zz, SW / 2 + (cx - SW / 2) * e, SH / 2 + (cy - SH / 2) * e)
        s = SC * zz
        tf = lambda x, y: (IX + (x - x0) * s, IY + (y - y0) * s)
        fr = canvas.copy()
        pic = whole if zz == 1 else base.resize((IW, IH), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))
        fr.paste(pic, (IX, IY))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
        # highlights: in 0.35 s before the pointer arrives, dimmer once the next target is reached
        for j, c in enumerate(clicks):
            a = min(max((t - (arr[j] - 0.35)) / 0.3, 0), 1)
            if a <= 0:
                continue
            if j + 1 < len(clicks) and t > arr[j + 1]:
                a *= 0.45
            bx0, by0 = tf(c["box"][0], c["box"][1]); bx1, by1 = tf(c["box"][2], c["box"][3])
            dr.rounded_rectangle((bx0 - 8, by0 - 8, bx1 + 8, by1 + 8), radius=12,
                                 fill=ACC + (int(46 * a),), outline=ACC + (int(255 * a),), width=5)
        # pointer: eases to each target in the 0.75 s before it is reached
        pos, pressed = ptr0, False
        for j, c in enumerate(clicks):
            prev = tf(*centre(clicks[j - 1])) if j else ptr0
            tgt = tf(*centre(c))
            if t < arr[j] - 0.75:
                pos = prev; break
            if t < arr[j]:
                q = ease((t - (arr[j] - 0.75)) / 0.75)
                pos = (prev[0] + (tgt[0] - prev[0]) * q, prev[1] + (tgt[1] - prev[1]) * q)
                pressed = c["kind"] == "drop" and j > 0 and clicks[j - 1]["kind"] == "drag"
                break
            pos, pressed = tgt, c["kind"] == "drag"
        for j, c in enumerate(clicks):
            if c["kind"] == "drag":
                continue
            for off in ((0, 0.18) if c["kind"] == "double" else (0,)):
                u = (t - arr[j] - off) / 0.45
                if 0 <= u <= 1:
                    px, py = tf(*centre(c)); r = 13 + 45 * u
                    dr.ellipse((px - r, py - r, px + r, py + r), outline=ACC + (int(255 * (1 - u)),), width=5)
        if show_ptr:
            down = pressed or any(0 <= t - a_ <= 0.14 for a_ in arr)
            cur = CURSOR_DOWN if down else CURSOR
            lay.alpha_composite(cur, (int(min(max(pos[0] - 4, 0), W - 1)), int(min(max(pos[1] - 4, 0), H - 1))))
        fr.alpha_composite(lay)
        a = min(max((t - 0.5) / 0.4, 0), 1)                 # caption fades in
        if a > 0:
            c_ = cap.copy(); c_.putalpha(c_.getchannel("A").point(lambda v: int(v * a)))
            fr.alpha_composite(c_)
        yield fr.convert("RGB")


def end_pointer(sc, ptr0):
    clicks = sc.get("clicks", [])
    if not clicks:
        return ptr0
    z, cx, cy = sc.get("z", 1.0), sc.get("cx", SW / 2), sc.get("cy", SH / 2)
    x0, y0, _, _ = view(z, cx, cy)
    px, py = centre(clicks[-1])
    return (IX + (px - x0) * SC * z, IY + (py - y0) * SC * z)


# 1. narration for every step, then one sound track
plan = []
for i, sc in enumerate(scenes):
    wav, n = narration(i, sc)
    plan.append((sc, wav, n)); print(f"{sc['id']}: {n / FPS:.1f} s", flush=True)
(OUT / "audio.txt").write_text("".join(f"file '{w}'\n" for _, w, _ in plan))
track = OUT / "narration.wav"
run(FF, "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(OUT / "audio.txt"), "-c", "copy", str(track))
total = sum(n for _, _, n in plan)

# 2. the pictures, one continuous stream
final = FILM / ("IgelkottFisheye-LiveFX-wall-setup.mp4" if not ONLY else "preview.mp4")
enc = subprocess.Popen([FF, "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                        "-r", str(FPS), "-i", "-", "-i", str(track), "-map", "0:v", "-map", "1:a",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(final)], stdin=subprocess.PIPE)
black = Image.new("RGB", (W, H), (0, 0, 0))
ptr, last, done = (IX + IW * 0.66, IY + IH * 0.70), None, 0
for sc, _, n in plan:
    if "card" in sc:
        frames = (card(*sc["card"]) for _ in range(n))
    else:
        base = Image.open(S / "images" / f"{sc['img']}.png").convert("RGB")
        if base.size != (SW, SH):
            base = base.resize((SW, SH), Image.LANCZOS)
        frames = step(sc, n, base, caption(sc.get("cap", "")), ptr, True)
    keep = None
    for k, fr in enumerate(frames):
        if last is not None and k < DISSOLVE * FPS:          # dissolve from the previous step's last frame
            fr = Image.blend(last, fr, ease(k / (DISSOLVE * FPS)))
        g = done + k
        f = min(g / (EDGE * FPS), (total - 1 - g) / (EDGE * FPS), 1)
        enc.stdin.write((fr if f >= 1 else Image.blend(black, fr, max(f, 0))).tobytes())
        keep = fr
    last = keep; done += n
    if "card" not in sc:
        ptr = end_pointer(sc, ptr)
enc.stdin.close()
if enc.wait():
    sys.exit("ffmpeg failed")
print(final, f"{dur(final):.1f} s")
