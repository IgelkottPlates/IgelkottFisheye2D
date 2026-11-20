# Times the Live FX shader on the graphics card (Windows): verify_windows.py's OpenGL setup and helpers are read and run
# from here, then the shader is drawn 20 times at LED canvas sizes, with the pixel tag in all four corners and without a
# tag, as built and with the tag read taken out (what Camera and Pointing chosen by hand cost).
#
#   python tools/bench_windows.py            (from the project root)
import os, sys, time

root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
src = open(os.path.join(root, "tools", "verify_windows.py"), encoding="utf-8").read()
src = src[:src.index("\ncases = [")]
sys.argv = [sys.argv[0], root]
g = {"__file__": os.path.join(root, "tools", "verify_windows.py"), "__name__": "bench"}
exec(compile(src, "verify_windows.py", "exec"), g)
ctypes, gl, GLuint, GLfloat = g["ctypes"], g["gl"], g["GLuint"], g["GLfloat"]
VERT = "#version 120\nvoid main() { gl_Position = gl_Vertex; }\n"
base = g["matchbox_src"]
progs = [("as built", g["link"](VERT, base)),
         ("no tag read", g["link"](VERT, base.replace("tag = igkTag(0.0);", "tag = 2.0;", 1)))]
N = 1024
tags = {"tag in 4 corners": g["every"](g["tag_cells"](2, 1)), "no tag": None}
sizes = [("4K UHD 3840x2160", 3840, 2160), ("8K UHD 7680x4320", 7680, 4320), ("15360x2160", 15360, 2160)]
GL_TEXTURE_2D, GL_FRAMEBUFFER, GL_RGBA16F = g["GL_TEXTURE_2D"], g["GL_FRAMEBUFFER"], 0x881A


def draw():
    gl.glBegin(g["GL_QUADS"])
    for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        gl.glVertex2f(GLfloat(x), GLfloat(y))
    gl.glEnd()


print("The Live FX shader, ms per frame (Camera and Pointing on Auto, Mode Wall):")
for tagname, tag in tags.items():
    g["upload"](N, tag, True)
    for sname, w, h in sizes:
        out, fbo = GLuint(0), GLuint(0)
        gl.glGenTextures(1, ctypes.byref(out)); gl.glBindTexture(GL_TEXTURE_2D, out)
        gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA16F, w, h, 0, g["GL_RGBA"], g["GL_FLOAT"], None)
        g["glGenFramebuffers"](1, ctypes.byref(fbo)); g["glBindFramebuffer"](GL_FRAMEBUFFER, fbo)
        g["glFramebufferTexture2D"](GL_FRAMEBUFFER, g["GL_COLOR_ATTACHMENT0"], GL_TEXTURE_2D, out, 0)
        gl.glBindTexture(GL_TEXTURE_2D, g["src_tex"]); gl.glViewport(0, 0, w, h)
        row = []
        for pname, prog in progs:
            g["glUseProgram"](prog)
            g["setup_matchbox"](prog, g["case"]("bench", w, h, cam=0, pointing=0, yaw=20.0, pitch=5.0))
            for _ in range(3):
                draw()
            gl.glFinish()
            t = time.perf_counter()
            for _ in range(20):
                draw()
            gl.glFinish()
            row.append("%s %.2f" % (pname, (time.perf_counter() - t) / 20 * 1000))
        print("  %-17s %-18s %s" % (tagname, sname, "   ".join(row)))
        g["glDeleteFramebuffers"](1, ctypes.byref(fbo)); gl.glDeleteTextures(1, ctypes.byref(out))
