# Provplåtar för att se noden i Live FX eller PIXERA utan riktiga taggade filer: en påhittad värld fotograferad genom
# linsmodellen, med eller utan pixeltaggen (PixelTag i _shared/IgelkottFisheyeLens). Bara Python 3, inga paket.
#
#   python tools/make_testplates.py <mapp> [storlek]      (standard 1536)
#
# Världen: rakt fram (yaw 0) röd, höger grön, bak blå, vänster gul; himlen ljus, marken mörk, horisonten vit; ett mörkt
# rutnät var 15:e grad. Fram till höger (yaw 0–45) är ljusare än fram till vänster, så en spegelvänd bild syns.
# Med Plate Auto, Yaw 0 och FOV 90 ska alla taggade plåtar ge samma vägg: röd i mitten, grön kant till höger.
#
#   pyxis_zenith_tag.png    PYXIS 12K, objektivet uppåt, tagg (kamera 1)
#   venice_nadir_tag.png    Sony Venice 2, objektivet nedåt, tagg (kamera 2, nadir)
#   pyxis_zenith_notag.png  utan tagg: noden ska visa varningen i Auto
import math, os, struct, sys, zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CAMS = {1: (8040.0, (4019.9389914282037, 4019.9389463189077),
            (2068.8673345215607, -31.032060077989637, 0.1394366394877631, -0.00029359255648059773)),
        2: (5760.0, (2848.031459694644, 2854.3896750742356),
            (1440.3464186123263, -21.606695057429874, 0.09789618777410111, -0.0002943394610105899))}


def crc6(bits):
    crc = 0x3F
    for b in bits:
        top = (crc >> 5) & 1 == 1
        crc = (crc << 1) & 0x3F
        if top != b:
            crc ^= 0x27
    return crc


def bits(value, n):
    return [(value >> i) & 1 == 1 for i in reversed(range(n))]


def tag_cells(cam, nadir, adjusted=True, oriented=False):
    data = bits(1, 2) + bits(cam & 7, 3) + [nadir, adjusted, oriented] + bits(0, 4)
    return [True, False] + data + bits(crc6(data), 6)


def tag_rect(i, corner, n):
    rnd = lambda v: math.floor(v + 0.5)
    u0 = 0.116 + (i % 10) * 0.011; v0 = 0.010 + (i // 10) * 0.011
    x0, x1 = rnd(u0 * n), rnd((u0 + 0.011) * n)
    y0, y1 = rnd(v0 * n), rnd((v0 + 0.011) * n)
    if corner % 2 == 1:
        x0, x1 = n - x1, n - x0
    if corner >= 2:
        y0, y1 = n - y1, n - y0
    return x0, y0, x1, y1


def world(d):
    lon = math.degrees(math.atan2(d[0], d[2])); lat = math.degrees(math.asin(max(-1.0, min(1.0, d[1]))))
    if abs(lat) < 0.6:
        return (1.0, 1.0, 1.0)
    if -45 <= lon < 45:
        c = (0.85, 0.15, 0.12) if lon < 0 else (1.0, 0.35, 0.3)
    elif 45 <= lon < 135:
        c = (0.15, 0.75, 0.2)
    elif -135 <= lon < -45:
        c = (0.9, 0.8, 0.1)
    else:
        c = (0.15, 0.3, 0.9)
    k = 0.9 if lat > 0 else 0.4
    c = tuple(v * k for v in c)
    if min(lon % 15, 15 - lon % 15) < 0.35 or min(lat % 15, 15 - lat % 15) < 0.35:
        c = tuple(v * 0.3 for v in c)
    return c


def unproject(px, py, n, cam):
    ref, c, k = CAMS[cam]
    qx = px * ref / n - c[0]; qy = py * ref / n - c[1]
    rho = math.hypot(qx, qy)
    if rho < 1e-9:
        return (0.0, 1.0, 0.0)
    th = rho / k[0]
    for _ in range(12):
        t2 = th * th
        g = th * (k[0] + t2 * (k[1] + t2 * (k[2] + t2 * k[3]))) - rho
        dg = k[0] + t2 * (3 * k[1] + t2 * (5 * k[2] + t2 * 7 * k[3]))
        th -= g / dg
    if th > 2.2 or th < 0:
        return None
    s = math.sin(th) / rho
    return (qx * s, math.cos(th), qy * s)


def plate(n, cam, nadir, tag):
    rows = []
    for y in range(n):
        row = bytearray(b"\0")                                   # PNG: filter 0
        for x in range(n):
            d = unproject(x + 0.5, y + 0.5, n, cam)
            if d is None:
                row += b"\0\0\0"; continue
            if nadir:                                            # objektivet nedåt: linsens riktning (x, −y, −z) i världen
                d = (d[0], -d[1], -d[2])
            row += bytes(int(round(v * 255)) for v in world(d))
        rows.append(row)
    if tag:
        cells = tag_cells(cam, nadir)
        for corner in range(4):
            for i, on in enumerate(cells):
                x0, y0, x1, y1 = tag_rect(i, corner, n)
                v = 255 if on else 0
                for y in range(y0, y1):
                    rows[y][1 + 3 * x0:1 + 3 * x1] = bytes([v]) * (3 * (x1 - x0))
    return rows


def png(path, rows, n):
    def chunk(t, data):
        return struct.pack(">I", len(data)) + t + data + struct.pack(">I", zlib.crc32(t + data) & 0xFFFFFFFF)
    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0))
                 + chunk(b"IDAT", zlib.compress(b"".join(rows), 6)) + chunk(b"IEND", b""))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python tools/make_testplates.py <folder> [size]")
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 1536
    os.makedirs(out, exist_ok=True)
    for name, cam, nadir, tag in (("pyxis_zenith_tag", 1, False, True), ("venice_nadir_tag", 2, True, True),
                                  ("pyxis_zenith_notag", 1, False, False)):
        path = os.path.join(out, name + ".png")
        png(path, plate(n, cam, nadir, tag), n)
        print("wrote", path)
