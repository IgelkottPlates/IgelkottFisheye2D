# The test on the Mac: the same cases, the same maths and the same limits as verify_windows.py, which is read and run
# from here with two swaps, so the cases live in one place only:
#
#   - The OpenGL context: CGL (the Legacy profile, GLSL 1.20, which Live FX's Matchbox shaders are written for) instead
#     of WGL.
#   - PIXERA is skipped: the Mac's OpenGL has no GLSL 4.50. The PIXERA edition is tested only with verify_windows.py.
#
# Live FX translates the shader to Metal on the Mac; this test compiles it with Apple's GLSL 1.20 and so says nothing
# about the translation. That is seen in Live FX (docs/MAC-TEST.md).
#
#   python3 tools/verify_mac.py            (from the project root)
#   python3 tools/verify_mac.py . --canvas (the LED canvases at full size)
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
    """Replace the text from start to end; fail the test if verify_windows.py has changed so the markers are missing."""
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

src = swap(src, "import array, ctypes, ctypes.wintypes as wt, ", "import array, ctypes, ")
src = swap(src, "# MARK: - OpenGL via WGL", "# MARK: - OpenGL via CGL (verify_mac.py)")
src = cut(src, "user32, gdi32, kernel32 = ctypes.windll.user32", "GLuint, GLint, GLenum, GLsizei, GLfloat =", CGL)
src = cut(src, "def ext(name, restype, *args):", "\n\n\n", EXT)
src = cut(src, 'pixera = link("#version 450 compatibility', 'print("PIXERA: the effect compiles and links (GLSL 4.50).")',
          'pixera = None\nprint("PIXERA: not tested on the Mac (no GLSL 4.50); run verify_windows.py on Windows.")',
          keep_end=False)
# No PIXERA cases: every case counts as without PIXERA, and the chain with PIXERA's Equirectangular is skipped
src = swap(src, 'if not c["pixera"]:', 'if True:')
src = swap(src, 'if host == "pixera" and not c["pixera"]:', 'if host == "pixera":')
src = swap(src, "has_ref = os.path.exists(", "has_ref = False and os.path.exists(")
src = re.sub(r'print\("PIXERA \(texture coordinates up\), source %d x %d:" % \(n, n\)\)\n', "", src)

if sys.platform != "darwin":
    sys.exit("verify_mac: run this on a Mac; on Windows use tools/verify_windows.py")
sys.argv[0] = WINDOWS
exec(compile(src, WINDOWS + " (via verify_mac.py)", "exec"), {"__name__": "__main__", "__file__": WINDOWS})
