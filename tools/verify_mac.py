# Provet på Mac: samma fall, samma räkning och samma gränser som verify_windows.py, som läses och körs härifrån med två
# byten, så att fallen bara finns på ett ställe:
#
#   - OpenGL-kontexten: CGL (Legacy-profilen, GLSL 1.20, som Live FX:s Matchbox-shaders skrivs för) i stället för WGL.
#   - PIXERA hoppas över: Macens OpenGL har inte GLSL 4.50. PIXERA-utgåvan provas bara med verify_windows.py.
#
# Live FX översätter shadern till Metal på Mac; det här provet kompilerar den med Apples GLSL 1.20 och säger alltså inget
# om översättningen. Den ses i Live FX (docs/MAC-TEST.md).
#
#   python3 tools/verify_mac.py            (från projektroten)
#   python3 tools/verify_mac.py . --canvas (LED-dukarna i full storlek)
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WINDOWS = os.path.join(HERE, "verify_windows.py")

CGL = '''opengl32 = ctypes.CDLL("/System/Library/Frameworks/OpenGL.framework/OpenGL")
_pix, _npix, _ctx = ctypes.c_void_p(), ctypes.c_int(), ctypes.c_void_p()
_attrs = (ctypes.c_int * 3)(99, 0x1000, 0)            # kCGLPFAOpenGLProfile = kCGLOGLPVersion_Legacy (GLSL 1.20)
opengl32.CGLChoosePixelFormat.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_int)]
opengl32.CGLCreateContext.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
opengl32.CGLSetCurrentContext.argtypes = [ctypes.c_void_p]
if opengl32.CGLChoosePixelFormat(_attrs, ctypes.byref(_pix), ctypes.byref(_npix)) or not _pix:
    fail("no pixel format")
if opengl32.CGLCreateContext(_pix, None, ctypes.byref(_ctx)) or opengl32.CGLSetCurrentContext(_ctx):
    fail("no context")
opengl32.glGetString.restype = ctypes.c_char_p
GL_RENDERER, GL_SHADING_LANGUAGE_VERSION, GL_VERSION = 0x1F01, 0x8B8C, 0x1F02
print("OpenGL: %s | %s | GLSL %s" % (opengl32.glGetString(GL_RENDERER).decode(), opengl32.glGetString(GL_VERSION).decode(),
                                       opengl32.glGetString(GL_SHADING_LANGUAGE_VERSION).decode()))

'''

EXT = '''def ext(name, restype, *args):
    f = getattr(opengl32, name, None)
    if f is None:
        fail("missing OpenGL function " + name)
    f.restype = restype; f.argtypes = list(args)
    return f
'''


def cut(s, start, end, new, keep_end=True):
    """Byt texten från start till end; fäll provet om verify_windows.py har ändrats så att markeringarna saknas."""
    a = s.find(start)
    b = s.find(end, a)
    if a < 0 or b < 0:
        sys.exit("verify_mac: verify_windows.py has changed (%r ... %r not found); update tools/verify_mac.py"
                 % (start[:40], end[:40]))
    return s[:a] + new + s[b if keep_end else b + len(end):]


def swap(s, old, new):
    if old not in s:
        sys.exit("verify_mac: verify_windows.py has changed (%r not found); update tools/verify_mac.py" % old[:60])
    return s.replace(old, new)


with open(WINDOWS, encoding="utf-8") as fh:
    src = fh.read()

src = swap(src, "import array, ctypes, ctypes.wintypes as wt, math", "import array, ctypes, math")
src = swap(src, "# MARK: - OpenGL via WGL", "# MARK: - OpenGL via CGL (verify_mac.py)")
src = cut(src, "user32, gdi32, kernel32 = ctypes.windll.user32", "GLuint, GLint, GLenum, GLsizei, GLfloat =", CGL)
src = cut(src, "def ext(name, restype, *args):", "\n\n\n", EXT)
src = cut(src, 'pixera = link("#version 450 compatibility', 'print("PIXERA: the effect compiles and links (GLSL 4.50).")',
          'pixera = None\nprint("PIXERA: not tested on the Mac (no GLSL 4.50); run verify_windows.py on Windows.")',
          keep_end=False)
# Inga PIXERA-fall: varje fall räknas som utan PIXERA, och kedjan med PIXERA:s Equirectangular hoppas över
src = swap(src, 'if not c["pixera"]:', 'if True:')
src = swap(src, 'if host == "pixera" and not c["pixera"]:', 'if host == "pixera":')
src = swap(src, "has_ref = os.path.exists(", "has_ref = False and os.path.exists(")
src = re.sub(r'print\("PIXERA \(texture coordinates up\), source %d x %d:" % \(n, n\)\)\n', "", src)

if sys.platform != "darwin":
    sys.exit("verify_mac: run this on a Mac; on Windows use tools/verify_windows.py")
sys.argv[0] = WINDOWS
exec(compile(src, WINDOWS + " (via verify_mac.py)", "exec"), {"__name__": "__main__", "__file__": WINDOWS})
