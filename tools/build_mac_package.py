# Builds the Mac package for Live FX: ../_releases/IgelkottFisheye/IgelkottFisheye-Mac.zip (Eric 2026-11-23: "a simple
# Mac zip in the Release, no app"). A folder IgelkottFisheye-<version>-Mac with the node, README.txt (mac/README.txt),
# VERSION and LICENSE.txt. No build output in the project folder (atlas rules 1-3). Runs on Mac and Windows; refuses if
# matchbox/ does not match shader/ (build_shaders.py --check). The test (verify_windows.py / verify_mac.py) runs first.
#
#   python tools/build_mac_package.py
import os, subprocess, sys, time, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
version = open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()
if subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_shaders.py"), "--check"]).returncode:
    sys.exit("build_mac_package: matchbox/ is stale, run tools/build_shaders.py first")

name = "IgelkottFisheye-%s-Mac" % version
files = (("matchbox/IgelkottFisheye2D.glsl", "IgelkottFisheye2D.glsl"),
         ("matchbox/IgelkottFisheye2D.xml", "IgelkottFisheye2D.xml"),
         ("mac/README.txt", "README.txt"), ("VERSION", "VERSION"), ("LICENSE", "LICENSE.txt"))
dist = os.path.join(os.path.dirname(ROOT), "_releases", "IgelkottFisheye")
os.makedirs(dist, exist_ok=True)
out = os.path.join(dist, "IgelkottFisheye-Mac.zip")
with zipfile.ZipFile(out + ".tmp", "w", zipfile.ZIP_DEFLATED) as z:
    for src, dst in files:
        with open(os.path.join(ROOT, src), "rb") as fh:
            data = fh.read().replace(b"\r\n", b"\n")           # Mac line endings
        info = zipfile.ZipInfo("%s/%s" % (name, dst), date_time=time.localtime()[:6])
        info.external_attr = 0o644 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, data)
os.replace(out + ".tmp", out)
print("Built " + out)
