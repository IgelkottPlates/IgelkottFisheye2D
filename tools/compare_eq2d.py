"""Compare IgelkottFisheye (the wall straight from the fisheye) with FisheyetoEqui's 16K equirect played through
Eq->2D, on an 8K canvas (7680 x 2160). Measures shift, sharpness, colour and the pixels only one of them shows.
Compares the files, not Live FX, so the numbers are the same on Mac and Windows. Needs numpy and opencv-python.

    python3 tools/compare_eq2d.py "/Volumes/igelkottstore.com/2025/Free Demo 2025/Store" A013C004_220516BG_fisheye_Gamma-ACEScct_AP1 ~/IgelkottCompare

Ours: core.glsl/matchbox.glsl in numpy (2 x 2 bilinear samples per pixel, lens model from shader/cameras.json, tag ->
camera/nadir). Eq->2D: the atlas formula (eq2d-fov-framing.md): f = (h/2)/tan(FOVv/2), yaw/pitch/roll as ours, one
bilinear sample in the 15360 x 7680 equirect (u = lon/2pi + 0.5, top row = up). The FOV is set so both are the same
horizontal angle. Windows results 2026-11-22: PROJECT.md, "Equirect + Eq->2D mot noden".
"""
import json, math, subprocess, sys, os
import numpy as np, cv2

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
FFPROBE = os.environ.get("FFPROBE", "ffprobe")
STORE = sys.argv[1]
CAM = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shader", "cameras.json")))["cameras"]
CAMS = {1: "pyxis12K", 2: "sonyVenice2", 3: "zcamE2S6"}
W, H = 7680, 2160
VIEWS = [  # name, yaw, pitch, roll, horizontal FOV
    ("yaw0", 0, 0, 0, 90), ("yaw90", 90, 0, 0, 90), ("yaw180", 180, 0, 0, 90), ("yaw270", 270, 0, 0, 90),
    ("pitch30", 0, 30, 0, 90), ("pitch-20", 45, -20, 0, 90), ("wide150", 0, 0, 0, 150), ("tele30", 0, 0, 0, 30),
]
OUT = sys.argv[3] if len(sys.argv) > 3 else "out"


def frame(path, n, fps, w, h):
    cmd = [FFMPEG, "-v", "error", "-ss", "%.6f" % ((n + 0.25) / fps), "-i", path, "-frames:v", "1",
           "-vf", "scale=in_color_matrix=bt709:in_range=limited:out_range=full:flags=accurate_rnd+full_chroma_int",
           "-f", "rawvideo", "-pix_fmt", "rgb48le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return (np.frombuffer(raw, np.uint16).reshape(h, w, 3).astype(np.float32) / 65535.0)


def luma(a):
    return a @ np.array([0.2126, 0.7152, 0.0722], np.float32)


# --- the pixel tag (core.glsl igkTagCorner) ---
def crc_step(crc, bit):
    top = 1 if crc >= 32 else 0
    crc = (crc * 2) % 64
    return crc ^ 39 if top != bit else crc


def tag(img):
    s = img.shape[0]
    votes = []
    for k in range(4):
        def cell(i):
            row = i // 10
            x = 0.116 + (i - 10 * row + 0.5) * 0.011
            y = 0.010 + (row + 0.5) * 0.011
            if k in (1, 3): x = 1 - x
            if k >= 2: y = 1 - y
            return float(luma(img[int(y * s), int(x * s)]))
        wv, bv = cell(0), cell(1)
        if wv - bv < 0.1: votes.append(-1); continue
        mid = (wv + bv) / 2; data = 0; crc = 63; chk = 0
        for i in range(2, 20):
            bit = 1 if cell(i) > mid else 0
            if i < 14: data = data * 2 + bit; crc = crc_step(crc, bit)
            else: chk = chk * 2 + bit
        votes.append(-1 if chk != crc or data // 1024 != 1 else ((data // 128) % 8) * 2 + (data // 64) % 2)
    good = [v for v in votes if v >= 0]
    return max(set(good), key=good.count) if good else -1, votes


def rot(y, p, r):
    y, p, r = math.radians(y), -math.radians(p), math.radians(r)
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rx = np.array([[1, 0, 0], [0, math.cos(p), -math.sin(p)], [0, math.sin(p), math.cos(p)]])
    rz = np.array([[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]])
    return ry @ rx @ rz  # GLSL mat3 columns -> these rows are the same matrices written row-major


def dirs(view, ox=0.5, oy=0.5):
    _, yaw, pitch, roll, fov = view
    xs = np.arange(W, dtype=np.float64) + ox
    ys = np.arange(H, dtype=np.float64) + oy
    cx = xs[None, :] - W / 2
    cy = H / 2 - ys[:, None]
    f = 0.5 * W / math.tan(math.radians(fov) / 2)
    v = np.stack(np.broadcast_arrays(cx / f, cy / f, np.ones((H, W))), -1)
    v /= np.linalg.norm(v, axis=-1, keepdims=True)
    return v @ rot(yaw, pitch, roll).T


def ours(img, view, cam, nadir):
    c = CAM[CAMS[cam]]; ref = float(c["reference"]); s = img.shape[0]
    k = [float(x) / ref for x in c["k"]]; ctr = [float(x) / ref for x in c["center"]]
    acc = np.zeros((H, W, 3), np.float32)
    for j in range(2):
        for i in range(2):
            d = dirs(view, (i + 0.5) * 0.5, (j + 0.5) * 0.5)
            if nadir: d = d * np.array([1, -1, -1])
            rho = np.hypot(d[..., 0], d[..., 2]); th = np.arctan2(rho, d[..., 1]); t2 = th * th
            poly = k[0] + t2 * (k[1] + t2 * (k[2] + t2 * k[3]))
            fct = np.where(rho > 1e-9, poly * th / np.maximum(rho, 1e-12), poly)
            px = ctr[0] + d[..., 0] * fct; py = ctr[1] + d[..., 2] * fct
            inside = (px >= 0) & (px <= 1) & (py >= 0) & (py <= 1)
            smp = cv2.remap(img, (px * s - 0.5).astype(np.float32), (py * s - 0.5).astype(np.float32),
                            cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            acc += np.where(inside[..., None], smp, 0)
    return acc * 0.25


def eq2d(eq, view):
    d = dirs(view)
    lon = np.arctan2(d[..., 0], d[..., 2]); lat = np.arcsin(np.clip(d[..., 1], -1, 1))
    eh, ew = eq.shape[:2]
    u = (lon / (2 * math.pi) + 0.5) * ew - 0.5; v = (0.5 - lat / math.pi) * eh - 0.5
    return cv2.remap(eq, u.astype(np.float32), v.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


def measure(a, b, fov):
    """a = ours, b = Eq->2D. Shifts are b relative to a (output pixels and degrees)."""
    degpx = fov / W
    la, lb = luma(a), luma(b)
    valid = (la > 0.004) & (lb > 0.004)
    T = 256; win = cv2.createHanningWindow((T, T), cv2.CV_32F)
    shifts, sharp, hf = [], [], []
    for y in range(0, H - T + 1, T):
        for x in range(0, W - T + 1, T // 1):
            if not valid[y:y + T, x:x + T].all(): continue
            ta, tb = la[y:y + T, x:x + T], lb[y:y + T, x:x + T]
            if ta.std() < 0.01: continue
            (dx, dy), resp = cv2.phaseCorrelate(ta.astype(np.float64), tb.astype(np.float64), win.astype(np.float64))
            if resp > 0.15: shifts.append((x + T / 2, y + T / 2, dx, dy, resp))
            ga = cv2.Laplacian(ta, cv2.CV_32F).var(); gb = cv2.Laplacian(tb, cv2.CV_32F).var()
            sharp.append(gb / max(ga, 1e-12))
            fa = np.abs(np.fft.fft2(ta * win)) ** 2; fb = np.abs(np.fft.fft2(tb * win)) ** 2
            fr = np.hypot(*np.meshgrid(np.fft.fftfreq(T), np.fft.fftfreq(T)))
            bands = [(0.05, 0.15), (0.15, 0.3), (0.3, 0.5)]
            hf.append([math.sqrt(fb[(fr >= lo) & (fr < hi)].sum() / max(fa[(fr >= lo) & (fr < hi)].sum(), 1e-20)) for lo, hi in bands])
    sh = np.array(shifts) if shifts else np.zeros((0, 5))
    mag = np.hypot(sh[:, 2], sh[:, 3]) if len(sh) else np.zeros(0)
    # colour: low-passed so geometry and sharpness do not count
    ba, bb = cv2.GaussianBlur(a, (0, 0), 12), cv2.GaussianBlur(b, (0, 0), 12)
    m = valid & (cv2.erode(valid.astype(np.uint8), np.ones((51, 51))) > 0)
    big = np.abs(luma(bb - ba)) > 40 / 1023.0          # burnt-in watermark and other content that is not in both
    wm = int((big & m).sum())
    diff = (bb - ba)[m & ~big]  # in 0..1 of the ACEScct code range
    only_a = int(((la > 0.004) & (lb <= 0.004)).sum()); only_b = int(((lb > 0.004) & (la <= 0.004)).sum())
    return {
        "tiles": len(sh),
        "shift_px_median": round(float(np.median(mag)), 3) if len(mag) else None,
        "shift_px_p95": round(float(np.percentile(mag, 95)), 3) if len(mag) else None,
        "shift_px_max": round(float(mag.max()), 3) if len(mag) else None,
        "shift_mean_dx_dy": [round(float(sh[:, 2].mean()), 3), round(float(sh[:, 3].mean()), 3)] if len(sh) else None,
        "shift_deg_median": round(float(np.median(mag)) * degpx, 4) if len(mag) else None,
        "shift_deg_max": round(float(mag.max()) * degpx, 4) if len(mag) else None,
        "laplacian_var_ratio_eq2d_over_ours": round(float(np.median(sharp)), 3) if sharp else None,
        "amplitude_ratio_bands_low_mid_high": [round(float(x), 3) for x in np.median(np.array(hf), 0)] if hf else None,
        "colour_mean_diff_rgb_10bit": [round(float(x) * 1023, 2) for x in diff.mean(0)] if len(diff) else None,
        "colour_p99_absdiff_luma_10bit": round(float(np.percentile(np.abs(luma(diff)), 99)) * 1023, 2) if len(diff) else None,
        "pixels_content_differs": wm,
        "pixels_only_ours": only_a, "pixels_only_eq2d": only_b,
        "worst_tiles": [[round(float(v), 2) for v in r[:4]] for r in sh[np.argsort(-np.hypot(sh[:, 2], sh[:, 3]))[:3]]] if len(sh) else [],
    }


def equimap(f, e, cam, nadir):
    """FisheyetoEqui's equirect against our lens model, tile by tile around the sphere (equirect pixels)."""
    c = CAM[CAMS[cam]]; ref = float(c["reference"]); s = f.shape[0]
    k = [float(x) / ref for x in c["k"]]; ctr = [float(x) / ref for x in c["center"]]
    eh, ew = e.shape[:2]; T = 256; win = cv2.createHanningWindow((T, T), cv2.CV_64F); rows = []
    for lat0 in range(80, -81, -10):
        for lon0 in range(-180, 180, 30):
            y0 = int((0.5 - lat0 / 180) * eh) - T // 2; x0 = int((lon0 / 360 + 0.5) * ew) - T // 2
            if y0 < 0 or y0 + T > eh: continue
            x0 %= ew
            xs = (np.arange(x0, x0 + T) + 0.5) / ew; ys = (np.arange(y0, y0 + T) + 0.5) / eh
            lon = (xs - 0.5) * 2 * math.pi; lat = (0.5 - ys) * math.pi
            LON, LAT = np.meshgrid(lon, lat)
            d = np.stack([np.cos(LAT) * np.sin(LON), np.sin(LAT), np.cos(LAT) * np.cos(LON)], -1)
            if nadir: d = d * np.array([1, -1, -1])
            rho = np.hypot(d[..., 0], d[..., 2]); th = np.arctan2(rho, d[..., 1]); t2 = th * th
            poly = k[0] + t2 * (k[1] + t2 * (k[2] + t2 * k[3]))
            fct = np.where(rho > 1e-9, poly * th / np.maximum(rho, 1e-12), poly)
            px = ctr[0] + d[..., 0] * fct; py = ctr[1] + d[..., 2] * fct
            if px.min() < 0 or px.max() > 1 or py.min() < 0 or py.max() > 1: continue
            a = luma(cv2.remap(f, (px * s - 0.5).astype(np.float32), (py * s - 0.5).astype(np.float32), cv2.INTER_LINEAR))
            b = luma(np.take(e, np.arange(x0, x0 + T) % ew, axis=1)[y0:y0 + T])
            if a.std() < 0.01 or b.max() < 0.004: continue
            (dx, dy), r = cv2.phaseCorrelate(a.astype(np.float64), b.astype(np.float64), win)
            if r > 0.15: rows.append([lat0, lon0, round(dx, 3), round(dy, 3), round(r, 2)])
    return rows


def main():
    clip = sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    fish = os.path.join(STORE, clip + ".mov")
    equi = os.path.join(STORE, "_Equi", clip + "_16K360_ProRes422HQ.mov")
    st = json.loads(subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=nb_frames,r_frame_rate", "-of", "json", fish],
                                   capture_output=True, text=True, check=True).stdout)["streams"][0]
    num, den = st["r_frame_rate"].split("/"); fps = float(num) / float(den); nfr = int(st["nb_frames"])
    res = {"clip": clip, "frames": []}
    for n in [nfr // 4, nfr // 2, 3 * nfr // 4]:
        f = frame(fish, n, fps, 5760, 5760)
        t, votes = tag(f)
        cam, nadir = (t // 2, t % 2) if t >= 0 else (2, 0)
        e = frame(equi, n, fps, 15360, 7680)
        fr = {"frame": n, "tag": t, "votes": votes, "camera": CAMS.get(cam), "nadir": nadir, "views": {}}
        if n == nfr // 2:
            fr["equimap_lat_lon_dx_dy_resp"] = equimap(f, e, cam, nadir)
            print(clip[:8], "equimap", fr["equimap_lat_lon_dx_dy_resp"], flush=True)
        for view in VIEWS:
            a = ours(f, view, cam, nadir); b = eq2d(e, view)
            fr["views"][view[0]] = measure(a, b, view[4])
            if n == nfr // 2 and view[0] in ("yaw0", "pitch30"):
                cy, cx = H // 2, W // 2
                crop = np.concatenate([a[cy - 270:cy + 270, cx - 480:cx + 480], b[cy - 270:cy + 270, cx - 480:cx + 480]], 1)
                cv2.imwrite(os.path.join(OUT, f"{clip[:8]}_{view[0]}_ours_vs_eq2d.png"),
                            (np.clip(crop[..., ::-1], 0, 1) * 65535).astype(np.uint16))
            print(clip[:8], n, view[0], json.dumps(fr["views"][view[0]]), flush=True)
            del a, b
        del f, e
        res["frames"].append(fr)
    json.dump(res, open(os.path.join(OUT, clip[:8] + ".json"), "w"), indent=1)


if __name__ == "__main__":
    main()
