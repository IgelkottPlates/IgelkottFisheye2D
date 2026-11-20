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
# provvektorer. Fallen täcker Plate Manual och Auto (tagg i alla hörn, i ett hörn, efter en LUT, trasig CRC, Z-Cam,
# majoritet, för svag kontrast, ingen tagg), PYXIS 12K och Sony Venice 2, zenit och nadir, Wall, Split och Equirect,
# och varningstecknet pixel för pixel. Gränsen är 0,5 källpixlar vid 8040.
#
# Ger 0 när alla fall håller, annars 1.
import array, ctypes, ctypes.wintypes as wt, math, os, subprocess, sys

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
CAMS = {1: (REF, CENTER, K), 2: (VREF, VCENTER, VK)}
YELLOW = (1.0, 0.78, 0.0)


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


def wall_direction(cx, cy, h, R, fov):
    f = (h / 2) / math.tan(fov * math.pi / 360)
    v = (cx / f, cy / f, 1.0)
    l = math.sqrt(v[0] ** 2 + v[1] ** 2 + 1)
    return apply(R, (v[0] / l, v[1] / l, v[2] / l))


def equi_direction(u, v_up):
    lon = (u - 0.5) * 2 * math.pi; lat = (v_up - 0.5) * math.pi
    return (math.cos(lat) * math.sin(lon), math.sin(lat), math.cos(lat) * math.cos(lon))


def direction(c, qx, qy_up, w, h, ox=0.0, oy=0.0):
    """Riktningen genom punkten (qx, qy_up) i en utbild w × h (y upp), som nodens Wall/Split/Equirect. (ox, oy) är
    Offset X/Y i samma enheter: bilden flyttas efter projektionen, Split-gränsen står kvar."""
    sx, sy = qx - ox, qy_up - oy
    if c["mode"] == 1:
        return equi_direction(sx / w, sy / h)
    split_x = c["pos"] / 100 * w if c["split"] else w
    if qx < split_x:
        return wall_direction(sx - split_x / 2, sy - h / 2, h, c["R"], c["fov"])
    return wall_direction(sx - (split_x + w) / 2, sy - h / 2, h, c["RR"], c["right"][3])


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
    seti(p, "mode", c["mode"])
    setf(p, "yaw", c["yaw"]); setf(p, "pitch", c["pitch"]); setf(p, "roll", c["roll"]); setf(p, "fov", c["fov"])
    setf(p, "aspect", c["w"] / c["h"]); seti(p, "split", c["split"]); setf(p, "splitPos", c["pos"])
    for n, v in zip(("yawR", "pitchR", "rollR", "fovR"), c["right"]):
        setf(p, n, v)


glUniform2f = ext("glUniform2f", None, GLint, GLfloat, GLfloat)


def case(name, w, h, cam=1, pointing=1, offset=(0.0, 0.0), mode=0, yaw=0.0, pitch=0.0, roll=0.0, fov=90.0,
         split=False, pos=50.0, right=(0.0, 0.0, 0.0, 90.0), tag=None, expect=None, pixera=False, step=1):
    """cam: 0 Auto, 1 PYXIS, 2 Venice, 3 Z-Cam; pointing: 0 Auto, 1 Zenith, 2 Nadir (panelens värden).
    offset: Offset X/Y i utbildens pixlar. expect = (kamera, nadir, varning) som noden ska välja; utan = handvalet."""
    c = dict(name=name, w=w, h=h, cam=cam, pointing=pointing, offset=offset, mode=mode, yaw=yaw, pitch=pitch,
             roll=roll, fov=fov, split=split, pos=pos, right=right, tag=tag, pixera=pixera, step=step,
             expect=expect or (cam, pointing == 2, cam not in CAMS))
    c["R"] = rotation(yaw, pitch, roll); c["RR"] = rotation(*right[:3])
    return c


def every(cells, white=1.0, black=0.0):
    return [(cells, white, black)] * 4


PYXIS_UP, PYXIS_DOWN = tag_cells(1, False), tag_cells(1, True)
VENICE_UP, VENICE_DOWN = tag_cells(2, False), tag_cells(2, True)
broken = list(VENICE_DOWN); broken[7] = not broken[7]                    # ruta 7 (nadir) vänd: fel CRC
O = (12.5, -7.25)
cases = [
    case("PYXIS, Back 384x216, pitch 15, FOV 58.5", 384, 216, pitch=15, fov=58.5, pixera=True),
    case("PYXIS, Side yaw 90, square", 256, 256, yaw=90),
    case("PYXIS, Sky yaw -35, pitch 70, roll 12, FOV 100", 256, 256, yaw=-35, pitch=70, roll=12, fov=100),
    case("PYXIS, LED 192x108, yaw 81.8, FOV 10", 192, 108, yaw=81.8, pitch=-4, fov=10),
    case("PYXIS, Ref TV yaw 180, Offset (12.5, -7.25) px", 192, 108, yaw=180, pitch=2, roll=-3, fov=20, offset=O,
         pixera=True),
    case("PYXIS, Equirect 512x256", 512, 256, mode=1, pixera=True),
    case("PYXIS, Equirect, Offset (40, 10) px", 512, 256, mode=1, offset=(40.0, 10.0)),
    case("Sony Venice 2, Back", 384, 216, cam=2, pitch=15, fov=58.5),
    case("Sony Venice 2, Ref TV yaw 180, Offset", 192, 108, cam=2, yaw=180, pitch=2, roll=-3, fov=20, offset=O),
    case("PYXIS Nadir, yaw 30, pitch -20", 384, 216, pointing=2, yaw=30, pitch=-20, fov=70, pixera=True),
    case("Sony Venice 2 Nadir, Equirect", 512, 256, cam=2, pointing=2, mode=1),
    case("Split 50 %: left yaw 0 FOV 60, right yaw 90 pitch 5 roll 3 FOV 40", 384, 216, fov=60, split=True,
         right=(90, 5, 3, 40), pixera=True),
    case("Split 30 %, Venice: left roll 10, right yaw -120 FOV 70", 384, 216, cam=2, roll=10, fov=50, split=True, pos=30,
         right=(-120, 0, 0, 70), pixera=True),
    case("Split 40 % with Offset (-30, 20) px: the edge stays, both pictures move", 384, 216, fov=60, split=True,
         pos=40, right=(90, 0, 0, 60), offset=(-30.0, 20.0), pixera=True),
    case("Split off: the right wall's values are not used", 256, 144, yaw=40, fov=60, right=(90, 10, 5, 30)),
    case("Z-Cam E2 S6: no lens model, black and the warning", 192, 108, cam=3, pixera=True),
    case("Auto, PYXIS zenith tag in every corner", 384, 216, cam=0, pointing=0,
         pitch=10, fov=60, tag=every(PYXIS_UP), expect=(1, False, False), pixera=True),
    case("Auto, Venice nadir tag in the bottom right corner only", 384, 216, cam=0, pointing=0, yaw=20, pitch=-15,
         fov=60, tag=[None, None, None, (VENICE_DOWN, 1.0, 0.0)], expect=(2, True, False), pixera=True),
    case("Auto, Venice tag after a LUT (white 0.62, black 0.38)", 256, 144, cam=0, pointing=0, yaw=-60,
         tag=every(VENICE_UP, 0.62, 0.38), expect=(2, False, False)),
    case("Auto, no tag: PYXIS zenith and the warning", 256, 144, cam=0, pointing=0, yaw=60, expect=(1, False, True),
         pixera=True),
    case("Auto, broken CRC in every corner: PYXIS zenith and the warning", 256, 144, cam=0, pointing=0, yaw=10,
         tag=every(broken), expect=(1, False, True)),
    case("Auto, Z-Cam tag: never another camera's model, black and the warning", 256, 144, cam=0, pointing=0,
         tag=every(tag_cells(3, False)), expect=(3, False, True)),
    case("Auto, three corners PYXIS nadir, one Venice zenith: the majority", 256, 144, cam=0, pointing=0, pitch=-30,
         tag=[(PYXIS_DOWN, 1.0, 0.0)] * 3 + [(VENICE_UP, 1.0, 0.0)], expect=(1, True, False)),
    case("Auto, contrast 0.05 (under 0.1): PYXIS zenith and the warning", 256, 144, cam=0, pointing=0,
         tag=every(PYXIS_DOWN, 0.55, 0.5), expect=(1, False, True)),
    case("Auto, Venice nadir in the top corners, Equirect", 512, 256, cam=0, pointing=0, mode=1,
         tag=[(VENICE_DOWN, 1.0, 0.0), (VENICE_DOWN, 1.0, 0.0), None, None], expect=(2, True, False), pixera=True),
    case("Camera Venice chosen, Pointing Auto, PYXIS nadir tag: Venice nadir", 256, 144, cam=2, pointing=0,
         pitch=-20, tag=every(PYXIS_DOWN), expect=(2, True, False), pixera=True),
    case("Camera Auto, Pointing Zenith chosen, Venice nadir tag: Venice zenith", 256, 144, cam=0, pointing=1,
         pitch=20, tag=every(VENICE_DOWN), expect=(2, False, False)),
    case("Camera PYXIS chosen, Pointing Auto, no tag: PYXIS zenith and the warning", 256, 144, cam=1, pointing=0,
         expect=(1, False, True)),
    case("Both chosen, no tag: no warning", 256, 144, cam=2, pointing=2, pitch=-10, expect=(2, True, False)),
]


def check(c, px, n, host):
    """Jämför utbilden med räkningen. Live FX: 2 × 2 prov, raden räknas uppifrån; PIXERA: ett prov, y uppåt."""
    w, h = c["w"], c["h"]
    cam, nadir, warn = c["expect"]
    lo, hi = 0.5 / n, 1 - 0.5 / n
    samples = ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)) if host == "livefx" else ((0.5, 0.5),)
    worst, checked, black, bad, sign_px = 0.0, 0, 0, 0, 0
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
            if warn and (mk(-0.01) != mark or mk(0.01) != mark):
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
                    d = direction(c, qx, qy_up, w, h, *c["offset"])
                else:
                    d = direction(c, qx, qy_up, w / h, 1.0, c["offset"][0] / h, c["offset"][1] / h)
                if cam not in CAMS:
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
    ok = worst < 0.5 and bad == 0 and (checked > 0 or cam not in CAMS) and (sign_px > 0) == warn
    print("  %s %s: largest error %.3f source px at 8040 (%d px checked, %d black%s%s)"
          % ("PASS" if ok else "FAIL", c["name"], worst, checked, black,
             ", warning sign %d px" % sign_px if sign_px else "", ", %d px WRONG" % bad if bad else ""))
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
                     tag=every(tag_cells(2, True)), expect=(2, True, False), step=st),
                case("%s, Auto, no tag: PYXIS zenith and the warning sign" % label, W, H, cam=0, pointing=0, yaw=50,
                     expect=(1, False, True), pixera=True, step=st)]
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
        if n == 1008 and not c["tag"] and c["cam"] == 1 and c["pointing"] != 0 and c["name"] != cases[0]["name"]:
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
    upload(1024, None, False)
    EW, EH = 4096, 2048
    ce = case("chain", EW, EH, cam=cam, pointing=2 if nadir else 1, mode=1)
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
for name, nums in (("pyxis12K", CENTER + K), ("sonyVenice2", VCENTER + VK)):
    at = shared.find("static let " + name) if source.startswith("_shared") else shared.find('"%s"' % name)
    block = shared[at:at + 600] if at >= 0 else ""
    for v in nums:
        if repr(v) not in block or repr(v) not in matchbox_src or repr(v) not in pixera_src:
            same = False; print("  differs: %s %r" % (name, v))
all_good &= same
print("  %s PYXIS 12K and Sony Venice 2: both shaders and this test use the numbers in %s"
      % ("PASS" if same else "FAIL", source))

print("All cases match IgelkottStage." if all_good else "Some cases differ from IgelkottStage.")
sys.exit(0 if all_good else 1)
