# Builds the Mac package for Live FX: ../_releases/IgelkottFisheye/IgelkottFisheye-Mac.zip (Eric 2026-11-23: "a simple
# Mac zip in the Release, no app"). A folder IgelkottFisheye-<version>-Mac with the node, README.txt (mac/README.txt),
# VERSION, LICENSE.txt, Resolve/ (the Fuse and resolve/README.txt, since 0.23) and AfterEffects/ (IgelkottFisheye.plugin
# as ae/build-plugin.sh built it in ~/Library/Caches, signed, universal, and ae/README.txt; since 0.23). Runs on a Mac only
# now: the plugin is built there. Refuses if the plugin is missing, unsigned or of another version. No build output in the project folder (atlas rules 1-3). Runs on Mac and Windows; refuses if
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
         ("mac/README.txt", "README.txt"), ("VERSION", "VERSION"), ("LICENSE", "LICENSE.txt"),
         ("resolve/IgelkottFisheye.fuse", "Resolve/IgelkottFisheye.fuse"), ("resolve/README.txt", "Resolve/README.txt"),
         ("ae/README.txt", "AfterEffects/README.txt"))
PLUGIN = os.path.expanduser(os.environ.get("IGELKOTT_AE_TARGET", "~/Library/Caches/Igelkott/IgelkottLiveFXFisheye/ae-target")
                            + "/release/IgelkottFisheye.plugin")
if not os.path.isdir(PLUGIN):
    sys.exit("build_mac_package: %s is missing: run ae/build-plugin.sh first" % PLUGIN)
plist = subprocess.run(["/usr/libexec/PlistBuddy", "-c", "Print :CFBundleShortVersionString", PLUGIN + "/Contents/Info.plist"],
                       capture_output=True, text=True).stdout.strip()
if plist != version:
    sys.exit("build_mac_package: the plugin is %s, VERSION is %s: run ae/build-plugin.sh" % (plist, version))
if subprocess.run(["codesign", "--verify", "--strict", PLUGIN]).returncode:
    sys.exit("build_mac_package: the plugin's signature does not verify")
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
    # The plugin bundle byte for byte (its signature covers the files); the executable keeps its x bit
    for base, dirs, names in os.walk(PLUGIN):
        dirs.sort()
        for n in sorted(names):
            full = os.path.join(base, n)
            rel = os.path.relpath(full, os.path.dirname(PLUGIN))
            info = zipfile.ZipInfo("%s/AfterEffects/%s" % (name, rel), date_time=time.localtime()[:6])
            info.external_attr = (0o755 if os.access(full, os.X_OK) else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(full, "rb") as fh:
                z.writestr(info, fh.read())
os.replace(out + ".tmp", out)
print("Built " + out)
