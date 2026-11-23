# Provet för IgelkottFisheye på Windows: båda utgåvorna ritas på riktigt med datorns grafikkort (en OpenGL-kontext ur
# WGL) och varje utpixel jämförs i dubbel precision med IgelkottStages räkning. Live FX på Windows kör OpenGL själv
# (loggen: "OpenGL 4.6.0 Compatibility Profile"), så Matchbox-shadern (GLSL 1.20) kompileras här av samma drivrutin som
# Live FX använder; PIXERA-effekten (GLSL 4.50) ritas med GPUpad-mallens omskrivning av texture(). Inga paket, bara
# Python 3 (ctypes), inget som kräver AMD eller NVIDIA.
#
#   python tools/verify_windows.py            (från projektroten)
#
# Källan är en gradient (R = x, G = y uppifrån, normerade), så utpixelns färg är källpunkten shadern läste. Pixeltaggen
# (PixelTag i _shared/IgelkottFisheyeLens) ritas i hörnen som Darkroom ritar den; dess bitar kontrolleras mot Swift-testets
# provvektorer. Fallen täcker Plate Manual och Auto (tagg i alla hörn, i ett hörn, efter en LUT, trasig CRC, Z-Cam, kod 4 utan modell,
# majoritet, för svag kontrast, ingen tagg), PYXIS 12K och Sony Venice 2, zenit och nadir, Wall, Split och Equirect,
# och varningstecknet pixel för pixel. Gränsen är 0,5 källpixlar vid 8040.
#
# Ger 0 när alla fall håller, annars 1.
import array, ctypes, ctypes.wintypes as wt, json, math, os, subprocess, sys

root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

# Filerna ska vara gjorda ur shader/ (tools/build_shaders.py)
if subprocess.call([sys.executable, os.path.join(root, "tools", "build_shaders.py"), "--check"]) != 0:
    sys.stderr.write("Run python tools/build_shaders.py first.\n"); sys.exit(1)

# MARK: - IgelkottStages räkning (StageKit/FisheyeLens.swift, StageProtocol/CameraCost.swift)

REF = 8040.0
CENTER = (4019.9389914282037, 4019.9389463189077)
K = (2068.8673345215607, -31.032060077989637, 0.1394366394877631, -0.00029359255648059773)
VREF = 5760.0
VCENTER = (2848.031459694644, 2854.3896750742356)
VK = (1440.3464186123263, -21.606695057429874, 0.09789618777410111, -0.0002943394610105899)
ZREF = 3872.0
ZCENTER = (1936.0, 1936.0)
ZK = (965.3796533166083, -9.478101051830038, 0.2498244786039206, -0.5051113655662752)
CAMS = {1: (REF, CENTER, K), 2: (VREF, VCENTER, VK), 3: (ZREF, ZCENTER, ZK)}
# Färgerna ur IgelkottDesigns tokens, som build_shaders.py skriver av till shader/tokens.json (atlas regel 17)
with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shader", "tokens.json"),
          encoding="utf-8") as _fh:
    _tok = json.load(_fh)["color"]
YELLOW, WHITE, CYAN = (tuple(int(_tok[k][i:i + 2], 16) / 255.0 for i in (1, 3, 5)) for k in ("warning", "text", "accent"))


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def apply(m, v):
    return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2])


def rotation(yaw, pitch, roll):
    # Rader här, kolumner i GLSL/simd: R = Ry(yaw) · Rx(−pitch) · Rz(roll)
    y, p, r = math.radians(yaw), math.radians(-pitch), math.radians(roll)
    ry = [[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]]
    rx = [[1, 0, 0], [0, math.cos(p), -math.sin(p)], [0, math.sin(p), math.cos(p)]]
    rz = [[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]]
    return mul(mul(ry, rx), rz)


def point(d, cam, nadir):
    """FisheyeLens.point / referensen, nadir som (x, −y, −z): källpunkten i andelar, uppifrån."""
    if nadir:
        d = (d[0], -d[1], -d[2])
    ref, c, k = CAMS[cam]
    rho = math.hypot(d[0], d[2])
    th = math.atan2(rho, d[1]); t2 = th * th
    poly = (k[0] + t2 * (k[1] + t2 * (k[2] + t2 * k[3]))) / ref
    f = poly * th / rho if rho > 1e-9 else poly
    return (c[0] / ref + d[0] * f, c[1] / ref + d[2] * f)


def wall_direction(cx, cy, ww, R, fov):
    """FOV vågrätt över väggens bredd ww (Eric 2026-11-20; till och med 0.17 lodrätt över höjden)."""
    f = (ww / 2) / math.tan(fov * math.pi / 360)
    v = (cx / f, cy / f, 1.0)
    l = math.sqrt(v[0] ** 2 + v[1] ** 2 + 1)
    return apply(R, (v[0] / l, v[1] / l, v[2] / l))


def equi_direction(cx, cy, w, R):
    """Mode Equirect: 360 grader över hela bredden w, samma grader per pixel på höjden, (cx, cy) från väggens mitt,
    riktad med väggens R; None förbi en pol."""
    k = 2 * math.pi / w
    lat, lon = cy * k, cx * k
    if abs(lat) > math.pi / 2:
        return None
    return apply(R, (math.cos(lat) * math.sin(lon), math.sin(lat), math.cos(lat) * math.cos(lon)))


def direction(c, qx, qy_up, w, h, scale=1.0):
    """Riktningen genom punkten (qx, qy_up) i en utbild w × h (y upp), som nodens Wall/Split/Equirect. Offset X/Y (vänstra
    väggen) och Right Offset X/Y (högra) flyttar bilden efter projektionen, gånger scale; Split-gränsen står kvar."""
    split_x = c["pos"] / 100 * w if c["split"] else w
    right = qx >= split_x
    ox, oy = c["roffset"] if right else c["offset"]
    sx, sy = qx - ox * scale, qy_up - oy * scale
    cx = sx - ((split_x + w) / 2 if right else split_x / 2)
    cy = sy - h / 2
    R = c["RR"] if right else c["R"]
    if c["mode"] == 1:
        return equi_direction(cx, cy, w, R)
    return wall_direction(cx, cy, w - split_x if right else split_x, R, c["right"][3] if right else c["fov"])


def warning(qx, qy_top, size):
    """Varningstecknet (igkWarning): 0 inget, 1 gult, 2 svart."""
    px, py = (qx - 0.5 * size) / size, (qy_top - 0.5 * size) / size
    if px < 0 or px > 1 or py < 0 or py > 0.9:
        return 0
    if abs(px - 0.5) > 0.5 * py / 0.9:
        return 0
    if abs(px - 0.5) < 0.06 and (0.3 < py < 0.62 or 0.7 < py < 0.8):
        return 2
    return 1


GLYPHS = {0: (583347, 17969), 5: (583347, 17969), 1: (476721, 17966), 12: (476721, 17966), 2: (1020036, 4228),
          13: (1020036, 4228), 14: (1020036, 4228), 4: (476735, 17969), 7: (462980, 4238), 18: (462980, 4238),
          8: (476695, 17967), 9: (1032734, 16927), 10: (541200, 16927), 17: (541200, 16927), 11: (576152, 21073),
          16: (476688, 16942), 19: (1001022, 16912), 20: (462980, 4238), 21: (476695, 17967), 22: (1032734, 16927),
          23: (541200, 16927), 24: (576152, 21073), 25: (476721, 17966), 26: (1020036, 4228), 27: (1020036, 4228),
          28: (1001022, 16912), 29: (541200, 16927), 30: (476735, 17969), 31: (1020036, 4228), 32: (1032734, 16927),
          33: (508430, 1086), 34: (0, 396), 35: (476688, 16942), 36: (476721, 17966), 37: (585397, 17969)}
FONT = {"N": "10001 11001 10101 10011 10001 10001 10001", "O": "01110 10001 10001 10001 10001 10001 01110",
        "T": "11111 00100 00100 00100 00100 00100 00100", "A": "01110 10001 10001 11111 10001 10001 10001",
        "I": "01110 00100 00100 00100 00100 00100 01110", "G": "01110 10001 10000 10111 10001 10001 01111",
        "E": "11111 10000 10000 11110 10000 10000 11111", "L": "10000 10000 10000 10000 10000 10000 11111",
        "K": "10001 10010 10100 11000 10100 10010 10001", "C": "01110 10001 10000 10000 10000 10001 01110",
        "P": "11110 10001 10001 11110 10000 10000 10000", "S": "01111 10000 10000 01110 00001 00001 11110",
        "M": "10001 11011 10101 10101 10001 10001 10001", ".": "00000 00000 00000 00000 00000 01100 01100"}
for i, ch in enumerate("NOT AN IGELKOTT CLIP" + "IGELKOTTPLATES.COM"):   # shaderns tal ska vara just dessa bokstäver
    r = [int(x, 2) for x in FONT[ch].split()] if ch != " " else [0] * 7
    want = (((r[0] * 32 + r[1]) * 32 + r[2]) * 32 + r[3], (r[4] * 32 + r[5]) * 32 + r[6])
    if GLYPHS.get(i, (0, 0)) != want:
        sys.stderr.write("igkMessageGlyph(%d) is not %r\n" % (i, ch)); sys.exit(1)


def message(qx, qy_top, sw, sh):
    """Meddelandet (igkMessage): 1 på en punkt i NOT AN IGELKOTT CLIP, 2 i IGELKOTTPLATES, 3 i .COM, annars 0."""
    unit = min(0.7 * sw / 119.0, 0.15 * sh / 7.0)
    px, py = (qx - 0.5 * sw) / unit + 59.5, (qy_top - 0.5 * sh) / unit + 9.0
    if px < 0 or px >= 119 or py < 0 or py >= 18:
        return 0
    letter = math.floor(px / 6); col = math.floor(px - 6 * letter)
    if col > 4.5:
        return 0
    row = math.floor(py)
    if row > 6:                                       # andra raden: rad 11-17, bokstav 1-18
        if row < 11 or letter < 1 or letter > 18:
            return 0
        row -= 11; letter += 19
    line = (3 if letter > 33 else 2) if letter > 19 else 1          # .COM är bokstav 34-37
    g = GLYPHS.get(letter, (0, 0))
    bits = (g[0] >> (5 * (3 - row))) & 31 if row < 4 else (g[1] >> (5 * (6 - row))) & 31
    return line * ((bits >> (4 - col)) & 1)


# MARK: - Pixeltaggen (PixelTag.swift: reglerna står där)

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
    """PixelTag.rect: rutan i pixlar (y nedåt), kanterna avrundade som Swifts .rounded()."""
    rnd = lambda v: math.floor(v + 0.5)
    u0 = 0.116 + (i % 10) * 0.011; v0 = 0.010 + (i // 10) * 0.011
    x0, x1 = rnd(u0 * n), rnd((u0 + 0.011) * n)
    y0, y1 = rnd(v0 * n), rnd((v0 + 0.011) * n)
    if corner % 2 == 1:
        x0, x1 = n - x1, n - x0
    if corner >= 2:
        y0, y1 = n - y1, n - y0
    return x0, y0, x1, y1


def in_tag_zone(p):
    u = min(p[0], 1 - p[0]); v = min(p[1], 1 - p[1])
    return 0.112 < u < 0.230 and v < 0.036


# Swift-testets provvektorer (PixelTagTests: cellerna som text)
vectors = {(1, False, True, False): "10010010100000000011", (2, True, True, True): "10010101110000110100",
           (3, False, False, False): "10010110000000001011", (0, False, False, False): "10010000000000101001"}
for (cam, nadir, adj, ori), want in vectors.items():
    got = "".join("1" if b else "0" for b in tag_cells(cam, nadir, adj, ori))
    if got != want:
        sys.stderr.write("The tag here differs from PixelTag: %s gives %s, not %s\n" % ((cam, nadir, adj, ori), got, want))
        sys.exit(1)
print("The pixel tag's bits match PixelTag's test vectors.")

# MARK: - OpenGL via WGL (ett dolt fönster, en vanlig kontext; Compatibility Profile ger GLSL 1.20 och glBegin)

def fail(s):
    sys.stderr.write(s + "\n"); sys.exit(1)


user32, gdi32, kernel32 = ctypes.windll.user32, ctypes.windll.gdi32, ctypes.windll.kernel32
opengl32 = ctypes.windll.opengl32


class PIXELFORMATDESCRIPTOR(ctypes.Structure):
    _fields_ = [("nSize", wt.WORD), ("nVersion", wt.WORD), ("dwFlags", wt.DWORD), ("iPixelType", ctypes.c_ubyte),
                ("cColorBits", ctypes.c_ubyte), ("cRedBits", ctypes.c_ubyte), ("cRedShift", ctypes.c_ubyte),
                ("cGreenBits", ctypes.c_ubyte), ("cGreenShift", ctypes.c_ubyte), ("cBlueBits", ctypes.c_ubyte),
                ("cBlueShift", ctypes.c_ubyte), ("cAlphaBits", ctypes.c_ubyte), ("cAlphaShift", ctypes.c_ubyte),
                ("cAccumBits", ctypes.c_ubyte), ("cAccumRedBits", ctypes.c_ubyte), ("cAccumGreenBits", ctypes.c_ubyte),
                ("cAccumBlueBits", ctypes.c_ubyte), ("cAccumAlphaBits", ctypes.c_ubyte), ("cDepthBits", ctypes.c_ubyte),
                ("cStencilBits", ctypes.c_ubyte), ("cAuxBuffers", ctypes.c_ubyte), ("iLayerType", ctypes.c_ubyte),
                ("bReserved", ctypes.c_ubyte), ("dwLayerMask", wt.DWORD), ("dwVisibleMask", wt.DWORD),
                ("dwDamageMask", wt.DWORD)]


user32.CreateWindowExW.restype = wt.HWND
user32.CreateWindowExW.argtypes = [wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID]
user32.GetDC.restype = wt.HDC
user32.GetDC.argtypes = [wt.HWND]
gdi32.ChoosePixelFormat.argtypes = [wt.HDC, ctypes.POINTER(PIXELFORMATDESCRIPTOR)]
gdi32.SetPixelFormat.argtypes = [wt.HDC, ctypes.c_int, ctypes.POINTER(PIXELFORMATDESCRIPTOR)]
opengl32.wglCreateContext.restype = wt.HANDLE
opengl32.wglCreateContext.argtypes = [wt.HDC]
opengl32.wglMakeCurrent.argtypes = [wt.HDC, wt.HANDLE]
opengl32.wglGetProcAddress.restype = ctypes.c_void_p
opengl32.wglGetProcAddress.argtypes = [ctypes.c_char_p]
opengl32.glGetString.restype = ctypes.c_char_p

# Fönsterklassen "STATIC" finns alltid; fönstret visas aldrig
hwnd = user32.CreateWindowExW(0, "STATIC", "verify", 0, 0, 0, 16, 16, None, None, None, None)
hdc = user32.GetDC(hwnd)
pfd = PIXELFORMATDESCRIPTOR()
pfd.nSize = ctypes.sizeof(PIXELFORMATDESCRIPTOR); pfd.nVersion = 1
pfd.dwFlags = 0x4 | 0x20 | 0x1                                       # DRAW_TO_WINDOW | SUPPORT_OPENGL | DOUBLEBUFFER
pfd.cColorBits = 32
fmt = gdi32.ChoosePixelFormat(hdc, ctypes.byref(pfd))
if not fmt or not gdi32.SetPixelFormat(hdc, fmt, ctypes.byref(pfd)):
    fail("no pixel format")
hglrc = opengl32.wglCreateContext(hdc)
if not hglrc or not opengl32.wglMakeCurrent(hdc, hglrc):
    fail("no context")

GL_RENDERER, GL_SHADING_LANGUAGE_VERSION, GL_VERSION = 0x1F01, 0x8B8C, 0x1F02
print("OpenGL: %s | %s | GLSL %s" % (opengl32.glGetString(GL_RENDERER).decode(), opengl32.glGetString(GL_VERSION).decode(),
                                       opengl32.glGetString(GL_SHADING_LANGUAGE_VERSION).decode()))

GLuint, GLint, GLenum, GLsizei, GLfloat = ctypes.c_uint, ctypes.c_int, ctypes.c_uint, ctypes.c_int, ctypes.c_float


def ext(name, restype, *args):
    addr = opengl32.wglGetProcAddress(name.encode())
    if not addr:
        fail("missing OpenGL function " + name)
    return ctypes.WINFUNCTYPE(restype, *args)(addr)


glCreateShader = ext("glCreateShader", GLuint, GLenum)
glShaderSource = ext("glShaderSource", None, GLuint, GLsizei, ctypes.POINTER(ctypes.c_char_p), ctypes.c_void_p)
glCompileShader = ext("glCompileShader", None, GLuint)
glGetShaderiv = ext("glGetShaderiv", None, GLuint, GLenum, ctypes.POINTER(GLint))
glGetShaderInfoLog = ext("glGetShaderInfoLog", None, GLuint, GLsizei, ctypes.c_void_p, ctypes.c_char_p)
glCreateProgram = ext("glCreateProgram", GLuint)
glAttachShader = ext("glAttachShader", None, GLuint, GLuint)
glLinkProgram = ext("glLinkProgram", None, GLuint)
glGetProgramiv = ext("glGetProgramiv", None, GLuint, GLenum, ctypes.POINTER(GLint))
glGetProgramInfoLog = ext("glGetProgramInfoLog", None, GLuint, GLsizei, ctypes.c_void_p, ctypes.c_char_p)
glUseProgram = ext("glUseProgram", None, GLuint)
glGetUniformLocation = ext("glGetUniformLocation", GLint, GLuint, ctypes.c_char_p)
glUniform1f = ext("glUniform1f", None, GLint, GLfloat)
glUniform1i = ext("glUniform1i", None, GLint, GLint)
glActiveTexture = ext("glActiveTexture", None, GLenum)
glGenFramebuffers = ext("glGenFramebuffers", None, GLsizei, ctypes.POINTER(GLuint))
glBindFramebuffer = ext("glBindFramebuffer", None, GLenum, GLuint)
glFramebufferTexture2D = ext("glFramebufferTexture2D", None, GLenum, GLenum, GLenum, GLuint, GLint)
glCheckFramebufferStatus = ext("glCheckFramebufferStatus", GLenum, GLenum)
glDeleteFramebuffers = ext("glDeleteFramebuffers", None, GLsizei, ctypes.POINTER(GLuint))

GL_FRAGMENT_SHADER, GL_VERTEX_SHADER, GL_COMPILE_STATUS, GL_LINK_STATUS = 0x8B30, 0x8B31, 0x8B81, 0x8B82
GL_TEXTURE_2D, GL_TEXTURE0, GL_RGBA, GL_FLOAT, GL_RGBA32F = 0x0DE1, 0x84C0, 0x1908, 0x1406, 0x8814
GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER, GL_LINEAR = 0x2801, 0x2800, 0x2601
GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE = 0x2802, 0x2803, 0x812F
GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_FRAMEBUFFER_COMPLETE = 0x8D40, 0x8CE0, 0x8CD5
GL_COLOR_BUFFER_BIT, GL_QUADS, GL_PACK_ALIGNMENT, GL_UNPACK_ALIGNMENT = 0x4000, 0x0007, 0x0D05, 0x0CF5
gl = opengl32


def compile_shader(kind, text):
    s = glCreateShader(kind)
    buf = ctypes.c_char_p(text.encode("utf-8"))
    glShaderSource(s, 1, ctypes.byref(buf), None)
    glCompileShader(s)
    ok = GLint(0); glGetShaderiv(s, GL_COMPILE_STATUS, ctypes.byref(ok))
    log = ctypes.create_string_buffer(8192); glGetShaderInfoLog(s, 8192, None, log)
    if not ok.value:
        fail("shader compile failed:\n" + log.value.decode(errors="replace"))
    if log.value.strip():
        print("Compiler notes:\n" + log.value.decode(errors="replace").strip())
    return s


def link(vertex, fragment):
    p = glCreateProgram()
    glAttachShader(p, compile_shader(GL_VERTEX_SHADER, vertex)); glAttachShader(p, compile_shader(GL_FRAGMENT_SHADER, fragment))
    glLinkProgram(p)
    linked = GLint(0); glGetProgramiv(p, GL_LINK_STATUS, ctypes.byref(linked))
    if not linked.value:
        log = ctypes.create_string_buffer(8192); glGetProgramInfoLog(p, 8192, None, log)
        fail("link failed:\n" + log.value.decode(errors="replace"))
    return p


def read_file(*p):
    with open(os.path.join(root, *p), encoding="utf-8") as fh:
        return fh.read()


matchbox_src = read_file("matchbox", "IgelkottFisheye2D.glsl")
pixera_src = read_file("pixera", "IgelkottFisheye.glsl")
matchbox = link("#version 120\nvoid main() { gl_Position = gl_Vertex; }\n", matchbox_src)
print("Live FX (Matchbox): the shader compiles and links (GLSL 1.20).")
# PIXERA: GPUpad-mallens block byts mot samma omskrivning, sedan en main som anropar effektens texture()
body = pixera_src[pixera_src.index("#endif") + len("#endif"):]
pixera = link("#version 450 compatibility\nvoid main() { gl_Position = gl_Vertex; }\n",
              "#version 450\n"
              "vec4 texture_(sampler2D s, vec2 tc) { return texture(s, tc); }\n"
              "vec4 texture_(sampler3D s, vec3 tc) { return texture(s, tc); }\n"
              "#define texture texture_\n" + body +
              "\nuniform IgelkottFisheye u;\nuniform vec2 u_size;\nout vec4 fragColor;\n"
              "void main() { fragColor = texture(u, gl_FragCoord.xy / u_size); }\n")
print("PIXERA: the effect compiles and links (GLSL 4.50).")

src_tex = GLuint(0)
gl.glGenTextures(1, ctypes.byref(src_tex)); glActiveTexture(GL_TEXTURE0); gl.glBindTexture(GL_TEXTURE_2D, src_tex)
for pname, val in ((GL_TEXTURE_MIN_FILTER, GL_LINEAR), (GL_TEXTURE_MAG_FILTER, GL_LINEAR),
                   (GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE), (GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)):
    gl.glTexParameteri(GL_TEXTURE_2D, pname, val)
gl.glPixelStorei(GL_PACK_ALIGNMENT, 1); gl.glPixelStorei(GL_UNPACK_ALIGNMENT, 1)


def upload(n, tag, top_row_first):
    """Gradienten n × n (R = x, G = y uppifrån) med taggen ritad: tag = fyra hörn, vart och ett None eller (celler, vit, svart)."""
    img = array.array("f", bytes(4 * 4 * n * n))
    for y in range(n):
        g = (y + 0.5) / n
        base = y * n * 4
        for x in range(n):
            k = base + x * 4
            img[k] = (x + 0.5) / n; img[k + 1] = g; img[k + 3] = 1.0
    for corner, spec in enumerate(tag or ()):
        if spec is None:
            continue
        cells, white, black = spec
        for i, on in enumerate(cells):
            x0, y0, x1, y1 = tag_rect(i, corner, n)
            v = white if on else black
            for y in range(y0, y1):
                for x in range(x0, x1):
                    k = (y * n + x) * 4
                    img[k] = img[k + 1] = img[k + 2] = v
    if not top_row_first:
        rows = [img[r * n * 4:(r + 1) * n * 4] for r in range(n)]
        img = array.array("f")
        for r in reversed(rows):
            img.extend(r)
    buf = (GLfloat * len(img)).from_buffer(img)
    gl.glBindTexture(GL_TEXTURE_2D, src_tex)
    gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, n, n, 0, GL_RGBA, GL_FLOAT, buf)


def render(prog, c, setup):
    w, h = c["w"], c["h"]
    out, fbo = GLuint(0), GLuint(0)
    gl.glGenTextures(1, ctypes.byref(out)); gl.glBindTexture(GL_TEXTURE_2D, out)
    gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, w, h, 0, GL_RGBA, GL_FLOAT, None)
    glGenFramebuffers(1, ctypes.byref(fbo)); glBindFramebuffer(GL_FRAMEBUFFER, fbo)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, out, 0)
    if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
        fail("incomplete framebuffer")
    gl.glBindTexture(GL_TEXTURE_2D, src_tex)
    gl.glViewport(0, 0, w, h)
    glUseProgram(prog)
    setup(prog, c)
    gl.glClearColor(GLfloat(0), GLfloat(0), GLfloat(0), GLfloat(0)); gl.glClear(GL_COLOR_BUFFER_BIT)
    gl.glBegin(GL_QUADS)
    for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        gl.glVertex2f(GLfloat(x), GLfloat(y))
    gl.glEnd()
    step = c.get("step", 1)
    if step == 1:
        px = (GLfloat * (w * h * 4))()
        gl.glReadPixels(0, 0, w, h, GL_RGBA, GL_FLOAT, px)
    else:
        # Stora dukar: bara var step:e rad läses tillbaka (raden på sin plats, resten nollor som check() hoppar över)
        px = {}
        line = (GLfloat * (w * 4))()
        for row in range(step // 2, h, step):
            gl.glReadPixels(0, row, w, 1, GL_RGBA, GL_FLOAT, line)
            px[row] = list(line)
    glDeleteFramebuffers(1, ctypes.byref(fbo)); gl.glDeleteTextures(1, ctypes.byref(out))
    return px


def uniforms(prefix):
    def setf(p, n, v): glUniform1f(glGetUniformLocation(p, (prefix + n).encode()), GLfloat(v))

    def seti(p, n, v): glUniform1i(glGetUniformLocation(p, (prefix + n).encode()), int(v))
    return setf, seti


def setup_matchbox(p, c):
    setf, seti = uniforms("")
    seti(p, "front", 0)
    setf(p, "adsk_result_w", c["w"]); setf(p, "adsk_result_h", c["h"])
    seti(p, "camera", c["cam"]); seti(p, "pointing", c["pointing"])
    setf(p, "offset_x", c["offset"][0]); setf(p, "offset_y", c["offset"][1]); seti(p, "mode", c["mode"])
    setf(p, "offset_xr", c["roffset"][0]); setf(p, "offset_yr", c["roffset"][1])
    setf(p, "yaw", c["yaw"]); setf(p, "pitch", c["pitch"]); setf(p, "roll", c["roll"]); setf(p, "fov", c["fov"])
    seti(p, "split", c["split"]); setf(p, "split_pos", c["pos"])
    for n, v in zip(("yaw_r", "pitch_r", "roll_r", "fov_r"), c["right"]):
        setf(p, n, v)


def setup_pixera(p, c):
    setf, seti = uniforms("u.")
    seti(p, "sampler", 0)
    glUniform2f(glGetUniformLocation(p, b"u_size"), GLfloat(c["w"]), GLfloat(c["h"]))
    seti(p, "camera", c["cam"]); seti(p, "pointing", c["pointing"])
    # PIXERA: Offset X/Y i % av höjden; fallet anger pixlar i utbilden
    setf(p, "offsetX", c["offset"][0] / c["h"] * 100); setf(p, "offsetY", c["offset"][1] / c["h"] * 100)
    setf(p, "offsetXR", c["roffset"][0] / c["h"] * 100); setf(p, "offsetYR", c["roffset"][1] / c["h"] * 100)
    seti(p, "mode", c["mode"])
    setf(p, "yaw", c["yaw"]); setf(p, "pitch", c["pitch"]); setf(p, "roll", c["roll"]); setf(p, "fov", c["fov"])
    setf(p, "aspect", c["w"] / c["h"]); seti(p, "split", c["split"]); setf(p, "splitPos", c["pos"])
    for n, v in zip(("yawR", "pitchR", "rollR", "fovR"), c["right"]):
        setf(p, n, v)


glUniform2f = ext("glUniform2f", None, GLint, GLfloat, GLfloat)


def case(name, w, h, cam=1, pointing=1, offset=(0.0, 0.0), roffset=(0.0, 0.0), mode=0, yaw=0.0, pitch=0.0, roll=0.0, fov=90.0,
         split=False, pos=50.0, right=(0.0, 0.0, 0.0, 90.0), tag="auto", expect=None, pixera=False, step=1):
    """cam: 0 Auto, 1 PYXIS, 2 Venice, 3 Z-Cam; pointing: 0 Auto, 1 Zenith, 2 Nadir (panelens värden).
    offset: Offset X/Y i utbildens pixlar. expect = (kamera, nadir, läge) som noden ska välja; utan = handvalet.
    Läge 0 spelar, 1 svart med varningstecknet (kamera utan linsmodell), 2 vägrar (ingen tagg: svart, NOT AN IGELKOTT
    CLIP och varningstecknet, Eric 2026-11-23). tag "auto" = handvalets egen tagg i alla hörn (en plåt utan tagg spelas
    aldrig sedan 0.20), None = ingen tagg."""
    auto = tag == "auto"
    if auto:
        tag = every(tag_cells(cam if cam in (1, 2, 3) else 1, pointing == 2))
    c = dict(name=name, w=w, h=h, cam=cam, pointing=pointing, offset=offset, roffset=roffset, mode=mode, yaw=yaw, pitch=pitch,
             roll=roll, fov=fov, split=split, pos=pos, right=right, tag=tag, autotag=auto, pixera=pixera, step=step,
             expect=expect or (cam, pointing == 2, 0 if cam in CAMS else 1))
    c["R"] = rotation(yaw, pitch, roll); c["RR"] = rotation(*right[:3])
    return c


def every(cells, white=1.0, black=0.0):
    return [(cells, white, black)] * 4


PYXIS_UP, PYXIS_DOWN = tag_cells(1, False), tag_cells(1, True)
VENICE_UP, VENICE_DOWN = tag_cells(2, False), tag_cells(2, True)
broken = list(VENICE_DOWN); broken[7] = not broken[7]                    # ruta 7 (nadir) vänd: fel CRC
O = (12.5, -7.25)
REFUSED = (0, False, 2)
cases = [
    case("PYXIS, Back 384x216, pitch 15, FOV 58.5", 384, 216, pitch=15, fov=58.5, pixera=True),
    case("PYXIS, Side yaw 90, square", 256, 256, yaw=90),
    case("PYXIS, Sky yaw -35, pitch 70, roll 12, FOV 100", 256, 256, yaw=-35, pitch=70, roll=12, fov=100),
    case("PYXIS, LED 192x108, yaw 81.8, FOV 10", 192, 108, yaw=81.8, pitch=-4, fov=10),
    case("PYXIS, Ref TV yaw 180, Offset (12.5, -7.25) px", 192, 108, yaw=180, pitch=2, roll=-3, fov=20, offset=O,
         pixera=True),
    case("PYXIS, Equirect 512x256", 512, 256, mode=1, pixera=True),
    case("PYXIS, Equirect, Offset (40, 10) px", 512, 256, mode=1, offset=(40.0, 10.0)),
    case("PYXIS, Equirect 32:9 768x216: 360 wide, cropped top and bottom", 768, 216, mode=1, pixera=True),
    case("Venice nadir, Equirect 16:9 384x216: past the poles black", 384, 216, cam=2, pointing=2, mode=1, pixera=True),
    case("Sony Venice 2, Back", 384, 216, cam=2, pitch=15, fov=58.5),
    case("Sony Venice 2, Ref TV yaw 180, Offset", 192, 108, cam=2, yaw=180, pitch=2, roll=-3, fov=20, offset=O),
    case("PYXIS Nadir, yaw 30, pitch -20", 384, 216, pointing=2, yaw=30, pitch=-20, fov=70, pixera=True),
    case("Sony Venice 2 Nadir, Equirect", 512, 256, cam=2, pointing=2, mode=1),
    case("Split 50 %: left yaw 0 FOV 60, right yaw 90 pitch 5 roll 3 FOV 40", 384, 216, fov=60, split=True,
         right=(90, 5, 3, 40), pixera=True),
    case("Split 30 %, Venice: left roll 10, right yaw -120 FOV 70", 384, 216, cam=2, roll=10, fov=50, split=True, pos=30,
         right=(-120, 0, 0, 70), pixera=True),
    case("Split 40 % with Offset (-30, 20) and Right Offset (25, -15) px: the edge stays, each picture moves", 384,
         216, fov=60, split=True, pos=40, right=(90, 0, 0, 60), offset=(-30.0, 20.0), roffset=(25.0, -15.0), pixera=True),
    case("Split off: Right Offset is not used", 256, 144, yaw=20, fov=60, roffset=(40.0, 30.0), pixera=True),
    case("Equirect aimed: yaw 40, pitch 10, roll 5", 512, 256, mode=1, yaw=40, pitch=10, roll=5, pixera=True),
    case("Equirect 32:9 Split 50 %: left yaw 0, right yaw 180 pitch 5", 768, 216, mode=1, split=True,
         right=(180, 5, 0, 90), pixera=True),
    case("Equirect Split 35 %, Venice nadir, Right Offset (20, 10) px", 768, 216, cam=2, pointing=2, mode=1,
         split=True, pos=35, yaw=-30, right=(120, -8, 3, 90), offset=(-10.0, 5.0), roffset=(20.0, 10.0), pixera=True),
    case("Split off: the right wall's values are not used", 256, 144, yaw=40, fov=60, right=(90, 10, 5, 30)),
    case("Z-Cam E2 S6, Back", 192, 108, cam=3, pitch=15, fov=58.5, pixera=True),
    case("Z-Cam E2 S6 nadir, Equirect", 512, 256, cam=3, pointing=2, mode=1, pixera=True),
    case("Auto, PYXIS zenith tag in every corner", 384, 216, cam=0, pointing=0,
         pitch=10, fov=60, tag=every(PYXIS_UP), expect=(1, False, 0), pixera=True),
    case("Auto, Venice nadir tag in the bottom right corner only", 384, 216, cam=0, pointing=0, yaw=20, pitch=-15,
         fov=60, tag=[None, None, None, (VENICE_DOWN, 1.0, 0.0)], expect=(2, True, 0), pixera=True),
    case("Auto, Venice tag after a LUT (white 0.62, black 0.38)", 256, 144, cam=0, pointing=0, yaw=-60,
         tag=every(VENICE_UP, 0.62, 0.38), expect=(2, False, 0)),
    case("Auto, no tag: refused, NOT AN IGELKOTT CLIP and the warning", 256, 144, cam=0, pointing=0, yaw=60, tag=None,
         expect=REFUSED, pixera=True),
    case("Auto, broken CRC in every corner: refused", 256, 144, cam=0, pointing=0, yaw=10,
         tag=every(broken), expect=REFUSED),
    case("Auto, Z-Cam zenith tag: its own model, no warning", 256, 144, cam=0, pointing=0, yaw=30,
         tag=every(tag_cells(3, False)), expect=(3, False, 0), pixera=True),
    case("Auto, tag code 4 (no lens model): never another camera's model, black and the warning", 256, 144, cam=0,
         pointing=0, tag=every(tag_cells(4, False)), expect=(4, False, 1)),
    case("Auto, three corners PYXIS nadir, one Venice zenith: the majority", 256, 144, cam=0, pointing=0, pitch=-30,
         tag=[(PYXIS_DOWN, 1.0, 0.0)] * 3 + [(VENICE_UP, 1.0, 0.0)], expect=(1, True, 0)),
    case("Auto, contrast 0.05 (under 0.1): refused", 256, 144, cam=0, pointing=0,
         tag=every(PYXIS_DOWN, 0.55, 0.5), expect=REFUSED),
    case("Auto, Venice nadir in the top corners, Equirect", 512, 256, cam=0, pointing=0, mode=1,
         tag=[(VENICE_DOWN, 1.0, 0.0), (VENICE_DOWN, 1.0, 0.0), None, None], expect=(2, True, 0), pixera=True),
    case("Camera Venice chosen, Pointing Auto, PYXIS nadir tag: Venice nadir", 256, 144, cam=2, pointing=0,
         pitch=-20, tag=every(PYXIS_DOWN), expect=(2, True, 0), pixera=True),
    case("Camera Auto, Pointing Zenith chosen, Venice nadir tag: Venice zenith", 256, 144, cam=0, pointing=1,
         pitch=20, tag=every(VENICE_DOWN), expect=(2, False, 0)),
    case("Camera PYXIS chosen, Pointing Auto, no tag: refused", 256, 144, cam=1, pointing=0, tag=None, expect=REFUSED),
    case("Both chosen, no tag: refused too", 256, 144, cam=2, pointing=2, pitch=-10, tag=None, expect=REFUSED,
         pixera=True),
    case("Both chosen, a 1920 x 1080 output: the message fits", 1920, 1080, cam=1, pointing=1, tag=None, expect=REFUSED,
         step=3, pixera=True),
]


def check(c, px, n, host):
    """Jämför utbilden med räkningen. 2 × 2 prov per pixel i båda (PIXERA sedan 0.21); Live FX räknar raden uppifrån, PIXERA y uppåt."""
    w, h = c["w"], c["h"]
    cam, nadir, state = c["expect"]
    warn = state > 0
    lo, hi = 0.5 / n, 1 - 0.5 / n
    samples = ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75))
    worst, checked, black, bad, sign_px, msg_px = 0.0, 0, 0, 0, 0, 0
    step = c.get("step", 1)
    for row in range(step // 2 if step > 1 else 0, h, step):
        line = px[row] if step > 1 else None
        for x in range(step // 2 if step > 1 else 0, w, step):
            if line is None:
                k = (row * w + x) * 4
                got = (px[k], px[k + 1], px[k + 2])
            else:
                got = (line[4 * x], line[4 * x + 1], line[4 * x + 2])
            if host == "livefx":
                mk = lambda e: warning(x + 0.5 + e, row + 0.5 + e, max(16.0, 0.05 * h))
            else:
                mk = lambda e: warning((x + 0.5 + e) / h, 1 - (row + 0.5 + e) / h, 0.05)
            mark = mk(0.0) if warn else 0
            if state == 2 and not mark and mk(-0.05) == 0 and mk(0.05) == 0:   # vägrad: svart, meddelandet i gult
                if host == "livefx":
                    mm = lambda e: message(x + 0.5 + e, row + 0.5 + e, w, h)
                else:
                    mm = lambda e: message((x + 0.5 + e) / h, 1 - (row + 0.5 + e) / h, w / h, 1.0)
                m = mm(0.0)
                if mm(-0.01) != m or mm(0.01) != m:
                    continue
                if m:
                    msg_px += 1
                want = {0: (0.0, 0.0, 0.0), 1: YELLOW, 2: WHITE, 3: CYAN}[m]
                if max(abs(a - b) for a, b in zip(got, want)) > 1e-3:
                    bad += 1
                    if os.environ.get("IGK_DEBUG"):
                        print("    refused px x %d row %d: message %d got %r" % (x, row, m, got))
                black += 0 if m else 1
                continue
            if warn and (mk(-0.05) != mark or mk(0.05) != mark):
                continue                    # exakt på tecknets kant: grafikkortets float kan hamna på andra sidan
            if mark:
                sign_px += 1
                want = YELLOW if mark == 1 else (0.0, 0.0, 0.0)
                if max(abs(a - b) for a, b in zip(got, want)) > 1e-3:
                    bad += 1
                    if os.environ.get("IGK_DEBUG"):
                        print("    sign px x %d row %d: mark %d got %r" % (x, row, mark, got))
                continue
            sx = sy = 0.0; inside = 0; skip = False
            for ox, oy in samples:
                if host == "livefx":
                    qx, qy_up = x + ox, h - (row + oy)
                else:
                    qx, qy_up = (x + ox) / h, (row + oy) / h                   # PIXERA: höjden = 1
                if host == "livefx":
                    d = direction(c, qx, qy_up, w, h)
                else:
                    d = direction(c, qx, qy_up, w / h, 1.0, 1.0 / h)
                if cam not in CAMS or d is None:
                    continue
                p = point(d, cam, nadir)
                if min(abs(p[0]), abs(p[0] - 1), abs(p[1]), abs(p[1] - 1)) < 1e-4:
                    skip = True                             # exakt på källbildens kant: float kan hamna på andra sidan
                if 0 <= p[0] <= 1 and 0 <= p[1] <= 1:
                    if c["tag"] and in_tag_zone(p):
                        skip = True
                    sx += min(max(p[0], lo), hi); sy += min(max(p[1], lo), hi); inside += 1
            if inside == 0 and skip:
                continue
            if inside == 0:
                black += 1
                if got[0] != 0 or got[1] != 0:
                    bad += 1
                    if os.environ.get("IGK_DEBUG"):
                        print("    black px x %d row %d: got %r" % (x, row, got))
                continue
            if skip or inside != len(samples):
                continue                                                    # bildramens kant, eller taggen
            worst = max(worst, math.hypot(got[0] - sx / inside, got[1] - sy / inside) * REF)
            checked += 1
    ok = (worst < 0.5 and bad == 0 and (checked > 0 or cam not in CAMS or state == 2) and (sign_px > 0) == warn
          and (msg_px > 0) == (state == 2))
    print("  %s %s: largest error %.3f source px at 8040 (%d px checked, %d black%s%s%s)"
          % ("PASS" if ok else "FAIL", c["name"], worst, checked, black,
             ", warning sign %d px" % sign_px if sign_px else "", ", message %d px" % msg_px if msg_px else "",
             ", %d px WRONG" % bad if bad else ""))
    return ok


all_good = True

# --canvas: LED-dukarnas storlekar (Eric 2026-11-20: "4k kanvas och 8k och 16kx2160"), ritade i full storlek, var
# step:e pixel kontrollerad. Källan är 2048 × 2048 (felet räknas ändå i källpixlar vid 8040).
if "--canvas" in sys.argv:
    mx = GLint(0); gl.glGetIntegerv(0x0D33, ctypes.byref(mx))                                  # GL_MAX_TEXTURE_SIZE
    vp = (GLint * 2)(); gl.glGetIntegerv(0x0D3A, vp)                                          # GL_MAX_VIEWPORT_DIMS
    print("Graphics card: largest texture %d px, largest viewport %d x %d" % (mx.value, vp[0], vp[1]))
    big = []
    for W, H, st, label in ((3840, 2160, 7, "4K UHD"), (4096, 2160, 7, "DCI 4K"), (7680, 4320, 13, "8K UHD"),
                            (15360, 2160, 13, "16K x 2160"), (16384, 2160, 13, "16384 x 2160")):
        if W > min(mx.value, vp[0]) or H > min(mx.value, vp[1]):
            print("  SKIP %s %d x %d: larger than this graphics card allows" % (label, W, H)); continue
        big += [case("%s %dx%d, PYXIS, yaw 30 pitch 10 FOV 60" % (label, W, H), W, H, yaw=30, pitch=10, fov=60,
                     pixera=True, step=st),
                case("%s, Venice nadir, Offset (%d, %d) px, roll 5, FOV 40" % (label, W // 40, -H // 30), W, H, cam=2,
                     pointing=2, yaw=-70, pitch=-12, roll=5, fov=40, offset=(float(W // 40), float(-H // 30)), pixera=True,
                     step=st),
                case("%s, Split 37.5 %%: left yaw -45 FOV 50, right yaw 60 FOV 35" % label, W, H, yaw=-45, fov=50,
                     split=True, pos=37.5, right=(60, 4, 0, 35), pixera=True, step=st),
                case("%s, Equirect" % label, W, H, mode=1, pixera=True, step=st),
                case("%s, Auto, Venice nadir tag: warning-free" % label, W, H, cam=0, pointing=0, yaw=15, pitch=-20,
                     tag=every(tag_cells(2, True)), expect=(2, True, 0), step=st),
                case("%s, no tag: refused, NOT AN IGELKOTT CLIP" % label, W, H, cam=0, pointing=0, yaw=50, tag=None,
                     expect=REFUSED, pixera=True, step=st)]
    for host, prog, setup, top in (("livefx", None, setup_matchbox, True), ("pixera", None, setup_pixera, False)):
        print(("Live FX" if host == "livefx" else "PIXERA") + ", source 2048 x 2048:")
        last = "unset"
        for c in big:
            if host == "pixera" and not c["pixera"]:
                continue
            if last != repr(c["tag"]):
                upload(2048, c["tag"], top); last = repr(c["tag"])
            all_good &= check(c, render(matchbox if host == "livefx" else pixera, c, setup), 2048, host)
    print("All canvases match IgelkottStage." if all_good else "Some canvases differ from IgelkottStage.")
    sys.exit(0 if all_good else 1)

# Källans storlek ska inte spela någon roll: andra varvet har en källa på 1008 × 1008 (4032 / 4, inte en tvåpotens).
for n in (1024, 1008):
    print("Live FX (top row first), source %d x %d:" % (n, n))
    last = "unset"
    for c in cases:
        if n == 1008 and c["autotag"] and c["cam"] == 1 and c["pointing"] != 0 and c["name"] != cases[0]["name"]:
            continue
        if last != repr(c["tag"]):
            upload(n, c["tag"], True); last = repr(c["tag"])
        all_good &= check(c, render(matchbox, c, setup_matchbox), n, "livefx")
    print("PIXERA (texture coordinates up), source %d x %d:" % (n, n))
    last = "unset"
    for c in cases:
        if not c["pixera"]:
            continue
        if last != repr(c["tag"]):
            upload(n, c["tag"], False); last = repr(c["tag"])
        all_good &= check(c, render(pixera, c, setup_pixera), n, "pixera")

# PIXERA-kedjan: vår effekt i Mode Equirect ger en equirect, PIXERA:s egen Equirectangular (Ref-Eric) läser den genom en
# Screen Pixel Position-karta (en plan skärm framför ögat). Varje pixel ska hamna på källpunkten för den riktning PIXERA:s
# effekt räknar fram; deras mitt är +X i världen, FisheyetoEquis är d.z: d = (n.z, n.y, n.x).
# Ref-Eric ligger inte i GitHub-repot (PIXERA:s fil, inte vår att lägga ut): utan den hoppas kedjan över.
has_ref = os.path.exists(os.path.join(root, "Ref-Eric", "Equirectangular.glsl.txt"))
ref_src = read_file("Ref-Eric", "Equirectangular.glsl.txt") if has_ref else "#endif"
ref_body = ref_src[ref_src.index("#endif") + len("#endif"):].replace("radians(", "radiansEq(")   # deras egen radians()
equirect_ref = None if not has_ref else link("#version 450 compatibility\nvoid main() { gl_Position = gl_Vertex; }\n",
                    "#version 450\n"
                    "vec4 texture_(sampler2D s, vec2 tc) { return texture(s, tc); }\n"
                    "vec4 texture_(sampler3D s, vec3 tc) { return texture(s, tc); }\n"
                    "#define texture texture_\nuniform int u_render_target_id;\n" + ref_body +
                    "\nuniform Equirectangular u;\nuniform vec2 u_size;\nout vec4 fragColor;\n"
                    "void main() { fragColor = texture(u, gl_FragCoord.xy / u_size); }\n")


def render_texture(prog, w, h, setup):
    """Ritar till en RGBA32F-textur och lämnar den kvar (texturens id)."""
    out, fbo = GLuint(0), GLuint(0)
    gl.glGenTextures(1, ctypes.byref(out)); gl.glBindTexture(GL_TEXTURE_2D, out)
    for pname, val in ((GL_TEXTURE_MIN_FILTER, GL_LINEAR), (GL_TEXTURE_MAG_FILTER, GL_LINEAR),
                       (GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE), (GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)):
        gl.glTexParameteri(GL_TEXTURE_2D, pname, val)
    gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, w, h, 0, GL_RGBA, GL_FLOAT, None)
    glGenFramebuffers(1, ctypes.byref(fbo)); glBindFramebuffer(GL_FRAMEBUFFER, fbo)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, out, 0)
    gl.glViewport(0, 0, w, h)
    glUseProgram(prog); setup(prog)
    gl.glBegin(GL_QUADS)
    for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        gl.glVertex2f(GLfloat(x), GLfloat(y))
    gl.glEnd()
    px = (GLfloat * (w * h * 4))()
    gl.glReadPixels(0, 0, w, h, GL_RGBA, GL_FLOAT, px)
    glDeleteFramebuffers(1, ctypes.byref(fbo))
    return out, px


print("PIXERA chain: IgelkottFisheye Mode Equirect -> PIXERA's own Equirectangular (Ref-Eric), source 1024 x 1024:"
      if has_ref else "PIXERA chain: SKIPPED, Ref-Eric/Equirectangular.glsl.txt (PIXERA's own effect) is not here")
for cam, nadir, label in ((1, False, "PYXIS 12K zenith"), (2, True, "Sony Venice 2 nadir")) if has_ref else ():
    EW, EH = 4096, 2048
    ce = case("chain", EW, EH, cam=cam, pointing=2 if nadir else 1, mode=1)
    upload(1024, ce["tag"], False)                                      # med taggen: utan den vägrar noden (0.20)
    equi_tex, _ = render_texture(pixera, EW, EH, lambda p: (glActiveTexture(GL_TEXTURE0), gl.glBindTexture(GL_TEXTURE_2D, src_tex),
                                                         setup_pixera(p, ce)))
    # Skärmkartan: M × M texlar, världspunkten i texelns mitt; en plan skärm 10 enheter fram (+X), 12 × 12 stor
    M = 128
    def world(u, v):
        return (10.0, (v - 0.5) * 12.0, (u - 0.5) * 12.0)
    vals = array.array("f")
    for j in range(M):
        for i in range(M):
            vals.extend(world((i + 0.5) / M, (j + 0.5) / M) + (1.0,))
    map_tex = GLuint(0)
    gl.glGenTextures(1, ctypes.byref(map_tex)); gl.glBindTexture(GL_TEXTURE_2D, map_tex)
    for pname, val in ((GL_TEXTURE_MIN_FILTER, GL_LINEAR), (GL_TEXTURE_MAG_FILTER, GL_LINEAR),
                       (GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE), (GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)):
        gl.glTexParameteri(GL_TEXTURE_2D, pname, val)
    gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, M, M, 0, GL_RGBA, GL_FLOAT, (GLfloat * len(vals)).from_buffer(vals))
    W = H = 128

    def setup_ref(p):
        glActiveTexture(GL_TEXTURE0); gl.glBindTexture(GL_TEXTURE_2D, equi_tex)
        glActiveTexture(GL_TEXTURE0 + 1); gl.glBindTexture(GL_TEXTURE_2D, map_tex); glActiveTexture(GL_TEXTURE0)
        setf, seti = uniforms("u.")
        seti(p, "sampler", 0); seti(p, "samplerScreenPxlPos", 1)
        for n in ("posX", "posY", "posZ", "rotX", "rotY", "rotZ"):
            setf(p, n, 0.0)
        glUniform1i(glGetUniformLocation(p, b"u_render_target_id"), 0)
        glUniform2f(glGetUniformLocation(p, b"u_size"), GLfloat(W), GLfloat(H))
    out_tex, px = render_texture(equirect_ref, W, H, setup_ref)
    scale = (M - 2.0) / M
    worst, checked = 0.0, 0
    for row in range(H):
        for x in range(W):
            tx, ty = (x + 0.5) / W, (row + 0.5) / H
            # deras shiftedTexCoords (ct = 1, index 0), sedan kartan: världspunkten är affin i texelkoordinaterna
            su = (tx - 0.5) * scale + 0.5
            sv = ((1.0 - ty) - 0.5) * scale + 0.5
            n = world(su, sv)
            l = math.sqrt(sum(c * c for c in n)); n = tuple(c / l for c in n)
            p = point((n[2], n[1], n[0]), cam, nadir)
            if not (0.01 < p[0] < 0.99 and 0.01 < p[1] < 0.99):
                continue
            k = (row * W + x) * 4
            worst = max(worst, math.hypot(px[k] - p[0], px[k + 1] - p[1]) * REF); checked += 1
    ok = worst < 1.0 and checked > 0
    all_good &= ok
    print("  %s %s, a flat screen 10 units ahead: largest error %.3f source px at 8040 (%d px checked; two resamplings)"
          % ("PASS" if ok else "FAIL", label, worst, checked))
    gl.glDeleteTextures(1, ctypes.byref(equi_tex)); gl.glDeleteTextures(1, ctypes.byref(map_tex))
    gl.glDeleteTextures(1, ctypes.byref(out_tex))

# MARK: - MTF50 (Eric 2026-11-23: "lägg in det här i provet det windows kör också")
# Nodens skärpa vid FOV 90 på 4K-duken (3840 × 2160), Venice 2 (5760²) zenit. En sned kant (5° från lodrät = vågrät
# upplösning H, 85° = lodrät V) ritas analytiskt i fisheyen (8 × 8 delprov i pixlarna kanten går genom, sensorns
# lådapertur), shadern ritar väggen på grafikkortet och kanten mäts som ISO 12233 (kantlinjen passad rad för rad, ESF i
# ¼ px, Hamming, derivatan rättad). Gränsen är numpy-modellen av nodens räkning (~/IgelkottCompare/mtf/mtf50.py,
# PROJECT.md "MTF50") ± 0,02, åt båda hållen: skarpare är också en ändring (färre prov per pixel viker bilden); Live FX
# och PIXERA ska ge samma tal. På Mac 2026-11-23 gav grafikkortet modellens tal på tredje decimalen. Eq->2D (FisheyetoEquis 16K-equi, samma vy,
# 2026-11-23) skrivs ut som jämförelse. Prov på metoden: en kant med Gauss 1 px ger 0,187 (teorin 0,187).
MTF_W, MTF_H, MTF_T = 3840, 2160, 200
MTF_CASES = (  # namn, yaw, pitch, riktning, kantens vinkel, modellen, Eq->2D
    ("horizon (yaw 0)", 0, 0, "H", 5.0, 0.355, 0.299), ("horizon (yaw 0)", 0, 0, "V", 85.0, 0.236, 0.220),
    ("pitch +30", 0, 30, "H", 5.0, 0.296, 0.260), ("pitch +30", 0, 30, "V", 85.0, 0.245, 0.225),
    ("yaw 45 pitch -20", 45, -20, "H", 5.0, 0.420, 0.308), ("yaw 45 pitch -20", 45, -20, "V", 85.0, 0.223, 0.207))


def mtf_theta(r, k):
    """Linsmodellens r(θ) baklänges (Newton): vinkeln från axeln för r källpixlar från mitten."""
    th = r / k[0]
    for _ in range(6):
        t2 = th * th
        f = th * (k[0] + t2 * (k[1] + t2 * (k[2] + t2 * k[3]))) - r
        df = k[0] + t2 * (3 * k[1] + t2 * (5 * k[2] + t2 * 7 * k[3]))
        th -= f / df
    return th


def mtf_patch(yaw, pitch, angle, half=220, lo=0.25, hi=0.75, ss=8):
    """Fisheyens ruta kring vyns mitt med kanten: (x0, y0, storlek, värden uppifrån)."""
    ref, c, k = CAMS[2]
    R = rotation(yaw, pitch, 0.0)
    a = math.radians(angle)
    nrm = apply(R, (math.cos(a), math.sin(a), 0.0))
    p = point(apply(R, (0.0, 0.0, 1.0)), 2, False)
    x0, y0, s = int(p[0] * ref) - half, int(p[1] * ref) - half, 2 * half

    def side(x, y):
        dx, dy = x - c[0], y - c[1]
        r = math.hypot(dx, dy); th = mtf_theta(r, k); q = math.sin(th) / max(r, 1e-12)
        return nrm[0] * dx * q + nrm[1] * math.cos(th) + nrm[2] * dy * q > 0
    corner = [[side(x0 + i, y0 + j) for i in range(s + 1)] for j in range(s + 1)]
    vals = []
    for j in range(s):
        for i in range(s):
            cs = (corner[j][i], corner[j][i + 1], corner[j + 1][i], corner[j + 1][i + 1])
            if all(cs) or not any(cs):
                f = 1.0 if cs[0] else 0.0
            else:
                f = sum(side(x0 + i + (u + 0.5) / ss, y0 + j + (v + 0.5) / ss) for v in range(ss) for u in range(ss)) / ss ** 2
            vals.append(lo + (hi - lo) * f)
    return x0, y0, s, vals


def mtf_upload(patch, top_row_first, lo=0.25):
    """Venice-källan 5760² i grått lo, kantens ruta och Venice-zenittaggen ovanpå."""
    n = int(VREF)
    gl.glBindTexture(GL_TEXTURE_2D, src_tex)
    gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, n, n, 0, GL_RGBA, GL_FLOAT, None)
    fbo = GLuint(0); glGenFramebuffers(1, ctypes.byref(fbo)); glBindFramebuffer(GL_FRAMEBUFFER, fbo)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, src_tex, 0)
    gl.glViewport(0, 0, n, n)
    gl.glClearColor(GLfloat(lo), GLfloat(lo), GLfloat(lo), GLfloat(1)); gl.glClear(GL_COLOR_BUFFER_BIT)
    glBindFramebuffer(GL_FRAMEBUFFER, 0); glDeleteFramebuffers(1, ctypes.byref(fbo))
    gl.glBindTexture(GL_TEXTURE_2D, src_tex)

    def put(x0, y0, w, h, rows):            # rows uppifrån, w × h värden
        if not top_row_first:
            y0 = n - y0 - h; rows = rows[::-1]
        buf = array.array("f")
        for row in rows:
            for v in row:
                buf.extend((v, v, v, 1.0))
        gl.glTexSubImage2D(GL_TEXTURE_2D, 0, x0, y0, w, h, GL_RGBA, GL_FLOAT, (GLfloat * len(buf)).from_buffer(buf))
    x0, y0, s, vals = patch
    put(x0, y0, s, s, [vals[j * s:(j + 1) * s] for j in range(s)])
    for corner, (cells, white, black) in enumerate(every(tag_cells(2, False))):
        for i, on in enumerate(cells):
            a0, b0, a1, b1 = tag_rect(i, corner, n)
            put(a0, b0, a1 - a0, b1 - b0, [[white if on else black] * (a1 - a0)] * (b1 - b0))


def mtf_render(prog, c, setup):
    """Väggen 3840 × 2160 på grafikkortet; bara rutan MTF_T² i mitten läses tillbaka (rad 0 nederst)."""
    w, h = c["w"], c["h"]
    out, fbo = GLuint(0), GLuint(0)
    gl.glGenTextures(1, ctypes.byref(out)); gl.glBindTexture(GL_TEXTURE_2D, out)
    gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, w, h, 0, GL_RGBA, GL_FLOAT, None)
    glGenFramebuffers(1, ctypes.byref(fbo)); glBindFramebuffer(GL_FRAMEBUFFER, fbo)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, out, 0)
    gl.glBindTexture(GL_TEXTURE_2D, src_tex)
    gl.glViewport(0, 0, w, h)
    glUseProgram(prog); setup(prog, c)
    gl.glClearColor(GLfloat(0), GLfloat(0), GLfloat(0), GLfloat(0)); gl.glClear(GL_COLOR_BUFFER_BIT)
    gl.glBegin(GL_QUADS)
    for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        gl.glVertex2f(GLfloat(x), GLfloat(y))
    gl.glEnd()
    px = (GLfloat * (MTF_T * MTF_T * 4))()
    gl.glReadPixels((w - MTF_T) // 2, (h - MTF_T) // 2, MTF_T, MTF_T, GL_RGBA, GL_FLOAT, px)
    glDeleteFramebuffers(1, ctypes.byref(fbo)); gl.glDeleteTextures(1, ctypes.byref(out))
    return [[px[(r * MTF_T + x) * 4] for x in range(MTF_T)] for r in range(MTF_T)]


def mtf50(tile, vertical_edge):
    """ISO 12233 sned kant: MTF50 i cykler per utpixel, och MTF vid 0,1/0,2/0,3 (för utskriften)."""
    t = tile if vertical_edge else [list(col) for col in zip(*tile)]       # kanten nästan lodrät i t
    h, w = len(t), len(t[0])
    ys, cs = [], []
    for r, row in enumerate(t):
        g = [abs(row[x + 1] - row[x]) for x in range(w - 1)]
        sg = sum(g)
        if sg > 1e-9:
            ys.append(r + 0.5); cs.append(sum(gi * (x + 1.0) for x, gi in enumerate(g)) / sg)
    my, mc = sum(ys) / len(ys), sum(cs) / len(cs)
    p1 = sum((y - my) * (cc - mc) for y, cc in zip(ys, cs)) / sum((y - my) ** 2 for y in ys)
    p0 = mc - p1 * my
    cosa = 1 / math.sqrt(1 + p1 * p1)
    nb = 320; tot = [0.0] * nb; cnt = [0] * nb
    for r, row in enumerate(t):
        edge = p0 + p1 * (r + 0.5)
        for x, v in enumerate(row):
            b = math.floor((x + 0.5 - edge) * cosa * 4) + nb // 2
            if 0 <= b < nb:
                tot[b] += v; cnt[b] += 1
    have = [i for i in range(nb) if cnt[i]]
    esf = []
    for i in range(nb):
        if cnt[i]:
            esf.append(tot[i] / cnt[i]); continue
        lo_i = max([j for j in have if j < i], default=None); hi_i = min([j for j in have if j > i], default=None)
        if lo_i is None or hi_i is None:
            esf.append(tot[(lo_i if hi_i is None else hi_i)] / cnt[(lo_i if hi_i is None else hi_i)])
        else:
            u = (i - lo_i) / (hi_i - lo_i)
            esf.append((1 - u) * tot[lo_i] / cnt[lo_i] + u * tot[hi_i] / cnt[hi_i])
    lsf = [(esf[min(i + 1, nb - 1)] - esf[max(i - 1, 0)]) / (2 if 0 < i < nb - 1 else 1) for i in range(nb)]
    lsf = [v * (0.54 - 0.46 * math.cos(2 * math.pi * i / (nb - 1))) for i, v in enumerate(lsf)]

    def mtf(kk):
        re = sum(v * math.cos(2 * math.pi * kk * i / nb) for i, v in enumerate(lsf))
        im = sum(v * math.sin(2 * math.pi * kk * i / nb) for i, v in enumerate(lsf))
        f = kk / (nb * 0.25); x = 2 * f * 0.25
        corr = math.sin(math.pi * x) / (math.pi * x) if x else 1.0
        return math.hypot(re, im) / corr
    m0 = mtf(0)
    curve = [(kk / (nb * 0.25), mtf(kk) / m0) for kk in range(0, nb // 2)]
    m50 = None
    for (fa, ma), (fb, mb) in zip(curve, curve[1:]):
        if ma >= 0.5 > mb:
            m50 = fa + (0.5 - ma) * (fb - fa) / (mb - ma); break
    at = lambda f: next(m for ff, m in curve if ff >= f - 1e-9)
    return m50, (at(0.1), at(0.2), at(0.3))


print("MTF50 at FOV 90 on the 4K canvas %d x %d, Sony Venice 2 source %d x %d (cycles per output pixel; Eq->2D for "
      "comparison):" % (MTF_W, MTF_H, int(VREF), int(VREF)))
mtf_hosts = [("Live FX", matchbox, setup_matchbox, True)] + ([("PIXERA", pixera, setup_pixera, False)] if pixera else [])
for name, yaw, pitch, d, ang, model, eq2d in MTF_CASES:
    patch = mtf_patch(yaw, pitch, ang)
    cm = case("MTF", MTF_W, MTF_H, cam=2, pointing=1, yaw=yaw, pitch=pitch, fov=90.0, tag=None)
    got = []
    for host, prog, setup, top in mtf_hosts:
        mtf_upload(patch, top)
        m50, pts = mtf50(mtf_render(prog, cm, setup), d == "H")
        got.append(m50)
        ok = m50 is not None and abs(m50 - model) <= 0.02
        all_good &= ok
        print("  %s %s %s %s: MTF50 %.3f (model %.3f, Eq->2D %.3f), MTF %.2f / %.2f / %.2f at 0.1 / 0.2 / 0.3"
              % ("PASS" if ok else "FAIL", host, name, d, m50 or float("nan"), model, eq2d, *pts))
    if len(got) == 2:
        same = None not in got and abs(got[0] - got[1]) < 0.005
        all_good &= same
        print("  %s Live FX and PIXERA give the same MTF50 (%s %s, difference %.4f)"
              % ("PASS" if same else "FAIL", name, d, abs(got[0] - got[1]) if None not in got else float("nan")))

# Kamerornas tal ska vara desamma som i _shared/IgelkottFisheyeLens
shared_path = os.path.join(os.path.dirname(os.path.abspath(root)), "_shared", "IgelkottFisheyeLens", "Sources",
                           "IgelkottFisheyeLens", "FisheyeLens.swift")
# Utan _shared (en klon av GitHub-repot): kopian shader/cameras.json, som build_shaders skriver ur _shared
if os.path.exists(shared_path):
    with open(shared_path, encoding="utf-8") as fh:
        shared = fh.read()
    source = "_shared/IgelkottFisheyeLens"
else:
    with open(os.path.join(root, "shader", "cameras.json"), encoding="utf-8") as fh:
        shared = fh.read()
    source = "shader/cameras.json (no _shared here)"
same = True
for name, nums in (("pyxis12K", CENTER + K), ("sonyVenice2", VCENTER + VK), ("zcamE2S6", ZCENTER + ZK)):
    at = shared.find("static let " + name) if source.startswith("_shared") else shared.find('"%s"' % name)
    block = shared[at:at + 600] if at >= 0 else ""
    for v in nums:
        in_block = repr(v) in block or (repr(v).endswith(".0") and repr(v)[:-2] in block)   # Swift: 1936
        if not in_block or repr(v) not in matchbox_src or repr(v) not in pixera_src:
            same = False; print("  differs: %s %r" % (name, v))
all_good &= same
print("  %s PYXIS 12K, Sony Venice 2 and Z-Cam E2 S6: both shaders and this test use the numbers in %s"
      % ("PASS" if same else "FAIL", source))

print("All cases match IgelkottStage." if all_good else "Some cases differ from IgelkottStage.")
sys.exit(0 if all_good else 1)
