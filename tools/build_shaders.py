# Builds the node's files from one source (Stage 1's handoff 2026-11-19: "one shared source for Matchbox and Pixera"):
#
#   shader/core.glsl            the lens, the nadir flip, the pixel tag, the warning (GLSL both 1.20 and 4.50 read)
#   shader/matchbox.glsl        the Live FX wrapper       -> matchbox/IgelkottFisheye2D.glsl
#   shader/IgelkottFisheye2D.xml  the panel (@VERSION@)   -> matchbox/IgelkottFisheye2D.xml
#   shader/pixera.glsl          the PIXERA wrapper        -> pixera/IgelkottFisheye.glsl
#   shader/core.dctl            the core by hand in DCTL (Resolve's GPU language), kept line for line with core.glsl
#   shader/resolve.dctl + resolve.fuse  the Resolve kernel and Fuse  -> resolve/IgelkottFisheye.fuse
#
# The camera numbers (PYXIS 12K, Sony Venice 2, Z-Cam E2 S6) are read as text from
# _shared/IgelkottFisheyeLens/…/FisheyeLens.swift, so the shaders have exactly the same digits, and are copied to
# shader/cameras.json. That copy is in the GitHub repo, so someone who clones without _shared can build; if _shared is
# there it is the source and --check fails a stale copy. The version comes from VERSION.
#
#   python tools/build_shaders.py           (from the project root; writes the files)
#   python tools/build_shaders.py --check   (0 when the files are already up to date, otherwise 1)
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPY = ("shader", "cameras.json")
TOKENS_COPY = ("shader", "tokens.json")
TOKENS = os.path.join(os.path.dirname(ROOT), "IgelkottDesign", "tokens", "tokens.json")
LENS = os.path.join(os.path.dirname(ROOT), "_shared", "IgelkottFisheyeLens", "Sources", "IgelkottFisheyeLens", "FisheyeLens.swift")


def read(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as fh:
        return fh.read()


def flt(v):
    """A number as a GLSL float: 1936 -> 1936.0 (the Z-Cam centre is written as an integer in Swift)."""
    v = v.strip()
    return v if re.search(r"[.eE]", v) else v + ".0"


def camera(swift, name):
    """reference, center (2) and k (4) as text, from `static let <name> = FisheyeLens(...)`."""
    m = re.search(r"static let %s = FisheyeLens\(reference: ([0-9.]+),\s*center: SIMD2\(([^)]*)\),\s*k: SIMD4\(([^)]*)\)" % name, swift)
    if not m:
        sys.exit("build_shaders: %s not found in %s" % (name, LENS))
    ref = m.group(1) if "." in m.group(1) else m.group(1) + ".0"
    return ref, [flt(v) for v in m.group(2).split(",")], [flt(v) for v in m.group(3).split(",")]


CAMERAS = (("PYXIS", "pyxis12K", "PYXIS 12K"), ("VENICE", "sonyVenice2", "Sony Venice 2"),
           ("ZCAM", "zcamE2S6", "Z-Cam E2 S6"))


def cameras():
    """{swift_name: {reference, center, k}} as text: from _shared if it is there, else from the copy shader/cameras.json."""
    if os.path.exists(LENS):
        with open(LENS, encoding="utf-8") as fh:
            swift = fh.read()
        out = {}
        for _, name, _ in CAMERAS:
            ref, c, k = camera(swift, name)
            out[name] = {"reference": ref, "center": c, "k": k}
        return out
    return json.loads(read(*COPY))["cameras"]


def tokens():
    """IgelkottDesign's colours the shader uses (atlas rule 17): warning, text and accent, as "#RRGGBB". From the design
    project if it is there, else from the copy shader/tokens.json (a clone without the rest of Igelkott Appar)."""
    if os.path.exists(TOKENS):
        with open(TOKENS, encoding="utf-8") as fh:
            c = json.load(fh)["color"]
        return {"warning": c["warning"]["value"], "text": c["text"]["value"], "accent": c["accent"]["value"]}
    return json.loads(read(*TOKENS_COPY))["color"]


def tokens_text(tok):
    return json.dumps({"note": "Copied from IgelkottDesign/tokens/tokens.json by tools/build_shaders.py. Do not edit by hand.",
                       "color": tok}, indent=2) + "\n"


def colours(tok):
    def vec(hexv):
        return "vec3(%s)" % ", ".join("%.6f" % (int(hexv[i:i + 2], 16) / 255.0) for i in (1, 3, 5))
    return ("// Colours from IgelkottDesign's tokens (color.warning %s, color.text %s, color.accent %s)\n"
            "const vec3 IGK_WARNING_YELLOW = %s;\nconst vec3 IGK_BRAND_TEXT = %s;\nconst vec3 IGK_BRAND_ACCENT = %s;\n"
            % (tok["warning"], tok["text"], tok["accent"], vec(tok["warning"]), vec(tok["text"]), vec(tok["accent"])))


def copy_text(cams):
    return json.dumps({"note": "Copied from _shared/IgelkottFisheyeLens (FisheyeLens.swift) by tools/build_shaders.py. "
                               "Reference width, lens centre and r(theta) = k1*t + k2*t^3 + k3*t^5 + k4*t^7, in source pixels. "
                               "Do not edit by hand.", "cameras": cams}, indent=2) + "\n"


def numbers(cams):
    lines = []
    for glsl, swift_name, human in CAMERAS:
        cam = cams[swift_name]
        ref, c, k = cam["reference"], cam["center"], cam["k"]
        lines += ["// %s (FisheyeLens.%s): reference width, lens centre, r(theta) in source pixels" % (human, swift_name),
                  "const float IGK_%s_REF = %s;" % (glsl, ref),
                  "const vec2 IGK_%s_CENTER = vec2(%s);" % (glsl, ", ".join(c)),
                  "const vec4 IGK_%s_K = vec4(%s);" % (glsl, ", ".join(k))]
    return "\n".join(lines) + "\n"


def dctl_numbers(cams, tok):
    """The camera numbers and colours as #defines for the DCTL kernel (Metal needs the f on every float)."""
    f = lambda v: "(%sf)" % flt(v)
    lines = []
    for glsl, swift_name, human in CAMERAS:
        cam = cams[swift_name]
        lines += ["// %s (FisheyeLens.%s)" % (human, swift_name),
                  "#define IGK_%s_REF %s" % (glsl, f(cam["reference"])),
                  "#define IGK_%s_CENTER_X %s" % (glsl, f(cam["center"][0])),
                  "#define IGK_%s_CENTER_Y %s" % (glsl, f(cam["center"][1]))]
        lines += ["#define IGK_%s_K%d %s" % (glsl, i + 1, f(v)) for i, v in enumerate(cam["k"])]
    def vec(hexv):
        return "to_float3(%s)" % ", ".join("%.6ff" % (int(hexv[i:i + 2], 16) / 255.0) for i in (1, 3, 5))
    lines += ["// Colours from IgelkottDesign's tokens (color.warning %s, color.text %s, color.accent %s)"
              % (tok["warning"], tok["text"], tok["accent"]),
              "#define IGK_WARNING_YELLOW %s" % vec(tok["warning"]), "#define IGK_BRAND_TEXT %s" % vec(tok["text"]),
              "#define IGK_BRAND_ACCENT %s" % vec(tok["accent"])]
    return "\n".join(lines) + "\n"


def resolve_fuse(cams, tok, version):
    swap = lambda t: t.replace("FETCH(", "igkFetch(src, ").replace("SRC_PARAM ", "__TEXTURE2D__ src, ").replace("SRC_ARG ", "src, ")
    kernel = ("// IgelkottFisheye %s for DaVinci Resolve - Igelkott Film AB (generated by tools/build_shaders.py)\n" % version
              + dctl_numbers(cams, tok) + "\n"
              "// The source, fractions of the picture with the top row first (Fusion's texture coordinates run up)\n"
              "__DEVICE__ float4 igkFetch(__TEXTURE2D__ t, float2 p) { return _tex2DVec4(t, p.x, 1.0f - p.y); }\n\n"
              + swap(read("shader", "core.dctl")) + "\n" + swap(read("shader", "resolve.dctl")))
    if "]==]" in kernel:
        sys.exit("build_shaders: the kernel must not contain ]==] (the Lua string's end)")
    return read("shader", "resolve.fuse").replace("@VERSION@", version).replace("@KERNEL@", kernel.rstrip("\n"))


def core(fetch, src_param, src_arg):
    text = read("shader", "core.glsl")
    return text.replace("FETCH(", fetch).replace("SRC_PARAM ", src_param).replace("SRC_ARG ", src_arg)


def generated(version):
    cams = cameras()
    tok = tokens()
    note = ("// GENERATED by tools/build_shaders.py from shader/ (version %s): edit shader/core.glsl and the wrapper, then run\n"
            "// python tools/build_shaders.py. The camera numbers come from _shared/IgelkottFisheyeLens.\n" % version)
    # The wrapper declares the sampler; the core reads it, so the declaration goes first.
    sampler = "uniform sampler2D front;\n"
    wrapper = read("shader", "matchbox.glsl").replace(sampler, "", 1).replace("FETCH(", "texture2D(front, ")
    matchbox = ("#version 120\n\n// IgelkottFisheye2D for Assimilate Live FX - Igelkott Film AB\n" + note + "\n" + sampler + "\n"
                + numbers(cams) + colours(tok) + "\n" + core("texture2D(front, ", "", "") + "\n" + wrapper)
    pixera = ("#if defined(GPUPAD)\n#version 450\n"
              "vec4 texture_(sampler2D s, vec2 tc) { return texture(s, tc); }\n"
              "vec4 texture_(sampler3D s, vec3 tc) { return texture(s, tc); }\n"
              "#define texture texture_\n#endif\n\n"
              "// IgelkottFisheye for PIXERA - Igelkott Film AB\n" + note + "\n" + numbers(cams) + colours(tok) + "\n"
              "// The source, fractions of the picture with the top row first (PIXERA's texture coordinates run up)\n"
              "vec4 igkFetch(sampler2D t, vec2 p) { return texture(t, vec2(p.x, 1.0 - p.y)); }\n\n"
              + core("igkFetch(igkSrc, ", "sampler2D igkSrc, ", "igkSrc, ") + "\n" + read("shader", "pixera.glsl"))
    xml = read("shader", "IgelkottFisheye2D.xml").replace("@VERSION@", version)
    return {("matchbox", "IgelkottFisheye2D.glsl"): matchbox, ("matchbox", "IgelkottFisheye2D.xml"): xml,
            ("pixera", "IgelkottFisheye.glsl"): pixera, ("resolve", "IgelkottFisheye.fuse"): resolve_fuse(cams, tok, version),
            COPY: copy_text(cams),
            TOKENS_COPY: tokens_text(tok)}


def main():
    version = read("VERSION").strip()
    stale = []
    for path, text in generated(version).items():
        full = os.path.join(ROOT, *path)
        try:
            with open(full, encoding="utf-8", newline="") as fh:
                current = fh.read()
        except OSError:
            current = None
        if current == text:
            continue
        stale.append("/".join(path))
        if "--check" not in sys.argv:
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
    if "--check" in sys.argv:
        print("build_shaders: " + ("stale: " + ", ".join(stale) if stale else "up to date"))
        sys.exit(1 if stale else 0)
    print("build_shaders: " + ("wrote " + ", ".join(stale) if stale else "nothing to do"))


if __name__ == "__main__":
    main()
