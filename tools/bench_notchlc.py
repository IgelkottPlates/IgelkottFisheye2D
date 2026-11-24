"""How heavy the Store clips in NotchLC are to play: file size, MB per frame, the read rate they need, how many frames
per second the local disk can read, and ffmpeg's CPU decode rate (only a measure of weight; Live FX decodes NotchLC
on the GPU). Runs on Mac and Windows.

    python3 tools/bench_notchlc.py --store "/Volumes/igelkottstore.com/2025/Free Demo 2025/Store" \
        --work ~/IgelkottBench --out ~/IgelkottBench/bench.jsonl

Each file is copied to --work, measured and deleted again (--keep keeps it); --in-place measures the files where they
lie (already on the disk to test; nothing is copied or deleted). Files already in --out are skipped, so
the run can be stopped and started again. --only fisheye|equi measures one kind. --ffmpeg/--ffprobe default to the
ones on PATH (Homebrew ffmpeg has the NotchLC decoder). The disk is read past the system's file cache
(F_NOCACHE on the Mac, FILE_FLAG_NO_BUFFERING on Windows), 4 readers x 32 MB like a player reading ahead.

Windows results 2026-11-22: the internal project notes (PROJECT.md), NotchLC storage.
"""
import argparse, glob, json, os, shutil, subprocess, sys, threading, time

CHUNK = 32 << 20


def files(store, only):
    n = os.path.join(store, "_NotchLC")
    out = []
    if only in (None, "fisheye"):
        # the fisheye NotchLC files carry the ProRes name (Media Encoder on M3Ultra); A007C001 was renamed 2026-11-21
        # since 2026-11-23 the equirects are ProRes 4444 too, so the fisheye pattern needs "_fisheye_"
        fish = sorted(f for f in glob.glob(os.path.join(n, "*_fisheye_*ProRes4444*.mov")) if "_16K360_" not in f)
        a7 = os.path.join(n, "A007C001_220127SK_fisheye_Gamma-ACEScct_AP1.mov")
        out += [(f, "fisheye NotchLC") for f in fish + ([a7] if os.path.exists(a7) else [])]
    if only in (None, "equi"):
        out += [(f, "equi NotchLC") for f in sorted(glob.glob(os.path.join(n, "*_16K360_ProRes4*.mov")))]
    return out


def probe(ffprobe, f):
    r = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=codec_name,codec_tag_string,width,height,r_frame_rate,nb_frames,pix_fmt",
                        "-of", "json", f], capture_output=True, text=True, check=True)
    s = json.loads(r.stdout)["streams"][0]
    a, b = s["r_frame_rate"].split("/")
    return s, float(a) / float(b), int(s.get("nb_frames", 0))


def _reader_windows(f):
    import ctypes
    from ctypes import wintypes
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateFileW.restype = wintypes.HANDLE
    k.VirtualAlloc.restype = ctypes.c_void_p
    k.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD]
    k.ReadFile.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
    k.SetFilePointerEx.argtypes = [wintypes.HANDLE, ctypes.c_longlong, ctypes.c_void_p, wintypes.DWORD]

    def open_():
        h = k.CreateFileW(f, 0x80000000, 1, None, 3, 0x20000000 | 0x08000000, None)  # NO_BUFFERING | SEQUENTIAL
        return h, k.VirtualAlloc(None, CHUNK, 0x3000, 0x04)

    def read(state, off):
        h, buf = state; r = wintypes.DWORD()
        k.SetFilePointerEx(h, off, None, 0)
        k.ReadFile(h, buf, CHUNK, ctypes.byref(r), None)
        return r.value

    return open_, read, lambda state: k.CloseHandle(state[0])


def _reader_posix(f):
    def open_():
        fd = os.open(f, os.O_RDONLY)
        if sys.platform == "darwin":
            import fcntl
            fcntl.fcntl(fd, 48, 1)  # F_NOCACHE: past the unified buffer cache
        return fd

    return open_, lambda fd, off: len(os.pread(fd, CHUNK, off)), os.close


def read_speed(f, gb=12, threads=4, start_frac=0.5):
    """GB/s, 4 readers of 32 MB from the middle of the file, past the file cache."""
    open_, read, close = (_reader_windows if os.name == "nt" else _reader_posix)(f)
    size = os.path.getsize(f)
    base = (int(size * start_frac) // CHUNK) * CHUNK
    n = min((gb << 30) // CHUNK, (size - base) // CHUNK)
    lock = threading.Lock(); nxt = [0]; got = [0]

    def worker():
        st = open_()
        while True:
            with lock:
                i = nxt[0]; nxt[0] += 1
            if i >= n: break
            r = read(st, base + i * CHUNK)
            with lock: got[0] += r
        close(st)

    t = time.perf_counter(); ts = [threading.Thread(target=worker) for _ in range(threads)]
    [x.start() for x in ts]; [x.join() for x in ts]
    return got[0] / (time.perf_counter() - t) / 1e9


def decode_fps(ffmpeg, f, frames, start):
    t = time.perf_counter()
    r = subprocess.run([ffmpeg, "-v", "error", "-threads", "0", "-ss", str(start), "-i", f, "-frames:v", str(frames),
                        "-an", "-f", "null", "-"], capture_output=True, text=True)
    return frames / (time.perf_counter() - t), r.returncode, r.stderr[-300:]


def copy(src, work):
    dst = os.path.join(work, os.path.basename(src))
    t = time.perf_counter()
    if os.name == "nt":
        subprocess.run(["robocopy", os.path.dirname(src), work, os.path.basename(src), "/J", "/NP", "/NJH", "/NJS",
                        "/R:1", "/W:1"], capture_output=True)
    else:
        shutil.copyfile(src, dst)
    return dst, time.perf_counter() - t


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--store", required=True, help="the Store folder (with _NotchLC inside)")
    ap.add_argument("--work", help="folder on the disk to test (outside the project folder)")
    ap.add_argument("--in-place", action="store_true", help="measure the files where they lie, no copy")
    ap.add_argument("--out", required=True, help="results, one JSON line per file")
    ap.add_argument("--only", choices=["fisheye", "equi"])
    ap.add_argument("--keep", action="store_true", help="keep the copies in --work")
    ap.add_argument("--ffmpeg", default="ffmpeg"); ap.add_argument("--ffprobe", default="ffprobe")
    a = ap.parse_args()
    if not a.in_place and not a.work:
        ap.error("--work is needed unless --in-place")
    if not a.in_place:
        os.makedirs(a.work, exist_ok=True)
    done = set()
    if os.path.exists(a.out):
        done = {json.loads(l)["key"] for l in open(a.out, encoding="utf-8") if l.strip()}
    for src, kind in files(a.store, a.only):
        key = os.path.basename(src) + "|" + kind
        if key in done: continue
        size = os.path.getsize(src)
        if a.in_place:
            local, copy_s = src, None
        elif shutil.disk_usage(a.work).free < size + (20 << 30):
            print("skip (no room)", key, flush=True); continue
        else:
            local, copy_s = copy(src, a.work)
        s, fps, nfr = probe(a.ffprobe, local)
        mbf = size / max(nfr, 1) / 1e6
        rs = read_speed(local)
        dfps, rc, err = decode_fps(a.ffmpeg, local, 48, start=nfr / fps * 0.3)
        rec = {"key": key, "kind": kind, "file": os.path.basename(src), "codec": s.get("codec_name"),
               "pix_fmt": s.get("pix_fmt"), "size": [s.get("width"), s.get("height")], "fps": fps, "frames": nfr,
               "seconds": round(nfr / fps, 1), "GB": round(size / 1e9, 2), "MB_per_frame": round(mbf, 2),
               "MBps_needed": round(mbf * fps, 1), "Mbitps": round(mbf * fps * 8, 0), "disk_read_GBps": round(rs, 2),
               "max_fps_from_disk": round(rs * 1000 / mbf, 1), "cpu_decode_fps_ffmpeg": round(dfps, 2),
               "decode_rc": rc, "decode_err": err if rc else "", "copy_MBps": round(size / copy_s / 1e6, 0) if copy_s else None,
               "platform": sys.platform}
        print(json.dumps(rec), flush=True)
        with open(a.out, "a", encoding="utf-8") as h: h.write(json.dumps(rec) + "\n")
        if not a.keep and not a.in_place: os.remove(local)


if __name__ == "__main__":
    main()
