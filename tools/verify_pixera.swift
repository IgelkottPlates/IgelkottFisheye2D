// Provet för PIXERA-effekten (pixera/IgelkottFisheye.glsl): effekten ritas på riktigt i en OpenGL 4.1-kontext på Macen
// (modern GLSL som PIXERA:s, med GPUpad-mallens omskrivning av texture()), och varje utpixel jämförs i dubbel precision.
// Källan är en gradient (R = x, G = y uppifrån, normerade), så utpixelns färg är källpunkten effekten läste.
//
//  1. 3D_Screens: en Screen Pixel Position-karta (en lutande skärmyta runt ögat), ögats läge och vridning, Stab och
//     de tre kamerorna, mot räkningen här (samma linsmodell som verify.swift och _shared/IgelkottFisheyeLens).
//  2. Wall: som Live FX-noden (vertikal FOV, Yaw, Pitch, Roll).
//  3. Mot PIXERA:s egen Equirectangular-effekt (Ref-Eric/Equirectangular.glsl.txt): den får en equirect gjord som
//     FisheyetoEqui gör den ur samma fisheye, IgelkottFisheye får fisheyen direkt — samma skärmkarta och öga ska ge
//     samma källpunkt. Det prövar att riktningarna i PIXERA:s värld är rätt översatta.
//
//   swift tools/verify_pixera.swift            (från projektroten; 0 när det stämmer)
import Foundation
import OpenGL.GL3
import simd

func fail(_ s: String) -> Never { FileHandle.standardError.write((s + "\n").data(using: .utf8)!); exit(1) }

// MARK: - Räkningen

let REF = 8040.0
let CENTER = SIMD2(4019.9389914282037, 4019.9389463189077)
let K = SIMD4(2068.8673345215607, -31.032060077989637, 0.1394366394877631, -0.00029359255648059773)
let VREF = 5760.0
let VCENTER = SIMD2(2848.031459694644, 2854.3896750742356)
let VK = SIMD4(1440.3464186123263, -21.606695057429874, 0.09789618777410111, -0.0002943394610105899)

struct Lens { var camera: Int32 = 1; var sensorHeight = 23.32; var lensScale = 1.0; var offset = SIMD2<Double>.zero }

/// Källpunkten i andelar av bilden (uppifrån) för riktningen d (y upp, z rakt fram).
func point(_ d: SIMD3<Double>, _ l: Lens) -> SIMD2<Double> {
    let (c, k): (SIMD2<Double>, SIMD4<Double>) = l.camera == 2 ? (VCENTER / VREF, VK / VREF)
        : (CENTER / REF, K / REF * (l.camera == 1 ? 1 : l.lensScale * 23.32 / l.sensorHeight))
    let rho = (d.x * d.x + d.z * d.z).squareRoot(), th = atan2(rho, d.y), t2 = th * th
    let poly = k.x + t2 * (k.y + t2 * (k.z + t2 * k.w))
    let f = rho > 1e-9 ? poly * th / rho : poly
    return c + l.offset / REF + SIMD2(d.x, d.z) * f
}

func rotation(yaw: Double, pitch: Double, roll: Double) -> simd_double3x3 {
    let y = yaw * .pi / 180, p = -pitch * .pi / 180, r = roll * .pi / 180
    let ry = simd_double3x3(columns: (SIMD3(cos(y), 0, -sin(y)), SIMD3(0, 1, 0), SIMD3(sin(y), 0, cos(y))))
    let rx = simd_double3x3(columns: (SIMD3(1, 0, 0), SIMD3(0, cos(p), sin(p)), SIMD3(0, -sin(p), cos(p))))
    let rz = simd_double3x3(columns: (SIMD3(cos(r), sin(r), 0), SIMD3(-sin(r), cos(r), 0), SIMD3(0, 0, 1)))
    return ry * rx * rz
}

/// PIXERA:s ögonvridning (Equirectangular-effektens getRotationMatrix3x3; GLSL m[i][j] = kolumn i, rad j).
func eyeRotation(_ deg: SIMD3<Double>) -> simd_double3x3 {
    let r = deg * .pi / 180
    let c1 = cos(-r.x), c2 = cos(-r.y), c3 = cos(-r.z), s1 = sin(-r.x), s2 = sin(-r.y), s3 = sin(-r.z)
    return simd_double3x3(columns: (SIMD3(c2 * c3, -c1 * s3 + s1 * s2 * c3, s1 * s3 + c1 * s2 * c3),
                                    SIMD3(c2 * s3, c1 * c3 + s1 * s2 * s3, -s1 * c3 + c1 * s2 * s3),
                                    SIMD3(-s2, s1 * c2, c1 * c2)))
}

// MARK: - OpenGL 4.1

var attrs: [CGLPixelFormatAttribute] = [kCGLPFAOpenGLProfile, CGLPixelFormatAttribute(UInt32(kCGLOGLPVersion_3_2_Core.rawValue)),
                                        kCGLPFAAccelerated, kCGLPFAAllowOfflineRenderers, CGLPixelFormatAttribute(0)]
var pf: CGLPixelFormatObj?
var npix: GLint = 0
guard CGLChoosePixelFormat(&attrs, &pf, &npix) == kCGLNoError, let pf else { fail("no core pixel format") }
var ctx: CGLContextObj?
guard CGLCreateContext(pf, nil, &ctx) == kCGLNoError, let ctx else { fail("no context") }
CGLSetCurrentContext(ctx)
print("OpenGL: \(String(cString: glGetString(GLenum(GL_RENDERER)))) · \(String(cString: glGetString(GLenum(GL_VERSION))))")

let root = URL(fileURLWithPath: CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : FileManager.default.currentDirectoryPath)
func load(_ rel: String) -> String {
    guard let s = try? String(contentsOf: root.appendingPathComponent(rel), encoding: .utf8) else { fail("cannot read \(rel)") }
    // GPUpad-blocket (#version 450 …) byts mot provets eget huvud
    guard let a = s.range(of: "#if defined(GPUPAD)"), let b = s.range(of: "#endif", range: a.upperBound..<s.endIndex) else { return s }
    return String(s[..<a.lowerBound]) + String(s[b.upperBound...])
}
let prelude = """
#version 410 core
vec4 texture_(sampler2D s, vec2 tc) { return texture(s, tc); }
#define texture texture_
uniform int u_render_target_id;

"""

func compile(_ type: GLenum, _ text: String, _ what: String) -> GLuint {
    let s = glCreateShader(type)
    text.withCString { p in var ptr: UnsafePointer<GLchar>? = p; glShaderSource(s, 1, &ptr, nil) }
    glCompileShader(s)
    var ok: GLint = 0; glGetShaderiv(s, GLenum(GL_COMPILE_STATUS), &ok)
    if ok == 0 {
        var log = [GLchar](repeating: 0, count: 8192); glGetShaderInfoLog(s, 8192, nil, &log)
        fail("\(what) does not compile:\n\(String(cString: log))")
    }
    return s
}
let vs = compile(GLenum(GL_VERTEX_SHADER), """
#version 410 core
out vec2 vUV;
void main() { vec2 p = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2); vUV = p; gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0); }
""", "vertex shader")
func program(_ body: String, _ type: String, _ what: String) -> GLuint {
    let fs = compile(GLenum(GL_FRAGMENT_SHADER), prelude + body + "\nin vec2 vUV;\nout vec4 fragColor;\nuniform \(type) uS;\nvoid main() { fragColor = texture(uS, vUV); }\n", what)
    let p = glCreateProgram(); glAttachShader(p, vs); glAttachShader(p, fs); glLinkProgram(p)
    var ok: GLint = 0; glGetProgramiv(p, GLenum(GL_LINK_STATUS), &ok)
    if ok == 0 { fail("\(what) does not link") }
    return p
}
let ours = program(load("pixera/IgelkottFisheye.glsl"), "IgelkottFisheye", "pixera/IgelkottFisheye.glsl")
print("pixera/IgelkottFisheye.glsl compiles and links (GLSL 4.10, PIXERA's texture() form).")
// PIXERA:s egen effekt definierar om radians(); i provet får den ett eget namn
let refText = "#define radians radians_ref\n" + load("Ref-Eric/Equirectangular.glsl.txt")
let theirs = program(refText, "Equirectangular", "Ref-Eric/Equirectangular.glsl.txt")
print("PIXERA's Equirectangular effect compiles and links as the reference.")
var vao: GLuint = 0; glGenVertexArrays(1, &vao); glBindVertexArray(vao)

func makeTexture(_ w: Int, _ h: Int, _ data: [Float]) -> GLuint {
    var t: GLuint = 0
    glGenTextures(1, &t); glBindTexture(GLenum(GL_TEXTURE_2D), t)
    glTexImage2D(GLenum(GL_TEXTURE_2D), 0, GL_RGBA32F, GLsizei(w), GLsizei(h), 0, GLenum(GL_RGBA), GLenum(GL_FLOAT), data)
    for (p, v) in [(GL_TEXTURE_MIN_FILTER, GL_LINEAR), (GL_TEXTURE_MAG_FILTER, GL_LINEAR), (GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE), (GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)] {
        glTexParameteri(GLenum(GL_TEXTURE_2D), GLenum(p), v)
    }
    return t
}

// Fisheyen: N × N, rad 0 = nederst (OpenGL), R = x, G = y uppifrån (texelns mitt)
let N = 1024
var grad: [Float] = []
for row in 0..<N { for x in 0..<N { grad += [Float((Double(x) + 0.5) / Double(N)), Float(1 - (Double(row) + 0.5) / Double(N)), 0, 1] } }
let fishTex = makeTexture(N, N, grad)

// Screen Pixel Position: en skärmyta, linjär i texturkoordinaten (så den bilinjära läsningen är exakt): ögat + M · (15,
// 30·(v − 0,5), 40·(u − 0,5)), M en vridning — riktningar upp till ±50° från ögats +X.
let eye = SIMD3(1.5, -0.7, 10.0)
let M = rotation(yaw: 25, pitch: 8, roll: -6)
func screenPos(_ u: Double, _ v: Double) -> SIMD3<Double> { eye + M * SIMD3(15, 30 * (v - 0.5), 40 * (u - 0.5)) }
let PW = 256
var posData: [Float] = []
for j in 0..<PW { for i in 0..<PW {
    let p = screenPos((Double(i) + 0.5) / Double(PW), (Double(j) + 0.5) / Double(PW))
    posData += [Float(p.x), Float(p.y), Float(p.z), 1]
} }
let posTex = makeTexture(PW, PW, posData)

/// Direction n (PIXERA:s värld, efter ögats vridning) för utpixelns texturkoordinat, som Equirectangular-effekten räknar den.
func screenDirection(_ tu: Double, _ tv: Double, eyeRot: SIMD3<Double>) -> SIMD3<Double> {
    let scale = (Double(PW) - 2) / Double(PW)
    let sx = (tu - 0.5) * scale + 0.5, sy = ((1 - tv) - 0.5) * scale + 0.5
    return eyeRotation(eyeRot) * simd_normalize(screenPos(sx, sy) - eye)
}

struct Params {
    var mode: Int32 = 0; var lens = Lens(); var eyeRot = SIMD3<Double>(0, 0, 0)
    var yaw = 0.0, pitch = 0.0, roll = 0.0, fov = 90.0, aspect = 1.7778
    var stab = SIMD3<Double>(0, 0, 0); var flipV = false
}

func render(_ prog: GLuint, _ src: GLuint, w: Int, h: Int, _ p: Params) -> [Float] {
    var fbo: GLuint = 0, out: GLuint = 0
    glGenTextures(1, &out); glBindTexture(GLenum(GL_TEXTURE_2D), out)
    glTexImage2D(GLenum(GL_TEXTURE_2D), 0, GL_RGBA32F, GLsizei(w), GLsizei(h), 0, GLenum(GL_RGBA), GLenum(GL_FLOAT), nil)
    glGenFramebuffers(1, &fbo); glBindFramebuffer(GLenum(GL_FRAMEBUFFER), fbo)
    glFramebufferTexture2D(GLenum(GL_FRAMEBUFFER), GLenum(GL_COLOR_ATTACHMENT0), GLenum(GL_TEXTURE_2D), out, 0)
    glUseProgram(prog)
    glActiveTexture(GLenum(GL_TEXTURE0)); glBindTexture(GLenum(GL_TEXTURE_2D), src)
    glActiveTexture(GLenum(GL_TEXTURE1)); glBindTexture(GLenum(GL_TEXTURE_2D), posTex)
    func loc(_ n: String) -> GLint { glGetUniformLocation(prog, "uS." + n) }
    func f(_ n: String, _ v: Double) { glUniform1f(loc(n), Float(v)) }
    func i(_ n: String, _ v: Int32) { glUniform1i(loc(n), v) }
    i("sampler", 0); i("samplerScreenPxlPos", 1); glUniform1i(glGetUniformLocation(prog, "u_render_target_id"), 0)
    f("posX", eye.x); f("posY", eye.y); f("posZ", eye.z); f("rotX", p.eyeRot.x); f("rotY", p.eyeRot.y); f("rotZ", p.eyeRot.z)
    i("mode", p.mode); i("camera", p.lens.camera); f("sensorHeight", p.lens.sensorHeight); f("lensScale", p.lens.lensScale)
    f("offsetX", p.lens.offset.x); f("offsetY", p.lens.offset.y)
    f("yaw", p.yaw); f("pitch", p.pitch); f("roll", p.roll); f("fov", p.fov); f("aspect", p.aspect)
    f("stabYaw", p.stab.x); f("stabPitch", p.stab.y); f("stabRoll", p.stab.z); i("flipV", p.flipV ? 1 : 0)
    glViewport(0, 0, GLsizei(w), GLsizei(h))
    glClear(GLbitfield(GL_COLOR_BUFFER_BIT))
    glDrawArrays(GLenum(GL_TRIANGLES), 0, 3)
    var px = [Float](repeating: 0, count: w * h * 4)
    glReadPixels(0, 0, GLsizei(w), GLsizei(h), GLenum(GL_RGBA), GLenum(GL_FLOAT), &px)
    glDeleteFramebuffers(1, &fbo); glDeleteTextures(1, &out)
    return px
}

/// Jämför en utbild med förväntade källpunkter (nil = svart utanför bildramen). Fel i källpixlar vid 8040.
var allGood = true
func check(_ name: String, _ px: [Float], w: Int, h: Int, limit: Double = 0.5, expect: (Double, Double) -> SIMD2<Double>?) {
    var worst = 0.0, checked = 0, black = 0, wrongBlack = 0
    let lo = 0.5 / Double(N), hi = 1 - lo
    for row in 0..<h { for x in 0..<w {
        let tu = (Double(x) + 0.5) / Double(w), tv = (Double(row) + 0.5) / Double(h)
        let k = (row * w + x) * 4, got = SIMD2(Double(px[k]), Double(px[k + 1]))
        guard let p = expect(tu, tv), p.x >= 0, p.x <= 1, p.y >= 0, p.y <= 1 else {
            black += 1; if got.x != 0 || got.y != 0 { wrongBlack += 1 }; continue
        }
        let want = SIMD2(min(max(p.x, lo), hi), min(max(p.y, lo), hi))
        worst = max(worst, simd_length(got - want) * REF); checked += 1
    } }
    let ok = worst < limit && wrongBlack == 0 && checked > 0
    allGood = allGood && ok
    print(String(format: "  %@ %@: largest error %.3f source px at 8040 (%d px checked, %d black%@)", ok ? "PASS" : "FAIL", name, worst,
                 checked, black, wrongBlack > 0 ? ", \(wrongBlack) NOT black" : ""))
}

print("3D_Screens (Screen Pixel Position, Eye):")
for (name, p) in [
    ("PYXIS 12K, eye not turned", Params(lens: Lens(camera: 1))),
    ("PYXIS 12K, eye turned 20 / -35 / 8", Params(lens: Lens(camera: 1), eyeRot: SIMD3(20, -35, 8))),
    ("Sony Venice 2, eye turned, Stab 1.5 / -0.8 / 0.4", Params(lens: Lens(camera: 2), eyeRot: SIMD3(-10, 60, 0), stab: SIMD3(1.5, -0.8, 0.4))),
    ("Custom, Sensor Height 23.9, Lens Offset (-24, -39)", Params(lens: Lens(camera: 0, sensorHeight: 23.9, offset: SIMD2(-24, -39)), eyeRot: SIMD3(0, 90, 0))),
] {
    let S = rotation(yaw: p.stab.x, pitch: p.stab.y, roll: p.stab.z)
    check(name, render(ours, fishTex, w: 192, h: 128, p), w: 192, h: 128) { tu, tv in
        let n = screenDirection(tu, tv, eyeRot: p.eyeRot)
        return point(S * SIMD3(n.z, n.y, n.x), p.lens)
    }
}

print("Wall (like the Live FX node):")
for (name, p) in [
    ("yaw 0, FOV 90, 16:9", Params(mode: 1, lens: Lens(camera: 1))),
    ("yaw 140, pitch 12, roll -5, FOV 58.5, Venice", Params(mode: 1, lens: Lens(camera: 2), yaw: 140, pitch: 12, roll: -5, fov: 58.5)),
    ("Sky, pitch 70, FOV 100, square, Stab 3 / 2 / 0", Params(mode: 1, lens: Lens(camera: 1), yaw: -35, pitch: 70, fov: 100, aspect: 1, stab: SIMD3(3, 2, 0))),
] {
    let w = p.aspect > 1.5 ? 192 : 128, h = 108 * (p.aspect > 1.5 ? 1 : 0) + (p.aspect > 1.5 ? 0 : 128)
    let R = rotation(yaw: p.stab.x, pitch: p.stab.y, roll: p.stab.z) * rotation(yaw: p.yaw, pitch: p.pitch, roll: p.roll)
    let t = tan(p.fov * .pi / 360)
    check(name, render(ours, fishTex, w: w, h: h, p), w: w, h: h) { tu, tv in
        point(R * simd_normalize(SIMD3((tu - 0.5) * 2 * t * p.aspect, (tv - 0.5) * 2 * t, 1)), p.lens)
    }
}

// PIXERA:s Equirectangular med en equirect gjord som FisheyetoEqui gör den (lon = atan2(d.x, d.z), lat = asin(d.y), rad 0
// uppe i bilden) ur samma gradient-fisheye, mot IgelkottFisheye på fisheyen.
print("Against PIXERA's Equirectangular effect (equirect made like FisheyetoEqui makes it):")
let EW = 4096, EH = 2048
var equi: [Float] = []
for row in 0..<EH { for x in 0..<EW {
    let lon = ((Double(x) + 0.5) / Double(EW) - 0.5) * 2 * .pi, lat = (0.5 - (1 - (Double(row) + 0.5) / Double(EH))) * .pi
    let p = point(SIMD3(cos(lat) * sin(lon), sin(lat), cos(lat) * cos(lon)), Lens(camera: 1))
    equi += [Float(p.x), Float(p.y), 0, 1]
} }
let equiTex = makeTexture(EW, EH, equi)
for (name, rot) in [("eye not turned", SIMD3(0.0, 0, 0)), ("eye turned 15 / 40 / -10", SIMD3(15.0, 40, -10))] {
    let p = Params(lens: Lens(camera: 1), eyeRot: rot)
    let a = render(ours, fishTex, w: 192, h: 128, p), b = render(theirs, equiTex, w: 192, h: 128, p)
    var worst = 0.0, checked = 0
    for k in stride(from: 0, to: a.count, by: 4) where a[k] > 0.02 && a[k] < 0.98 && a[k + 1] > 0.02 && a[k + 1] < 0.98 {
        worst = max(worst, simd_length(SIMD2(Double(a[k] - b[k]), Double(a[k + 1] - b[k + 1]))) * REF); checked += 1
    }
    let ok = worst < 1.5 && checked > 1000
    allGood = allGood && ok
    print(String(format: "  %@ %@: largest difference %.3f source px at 8040 (%d px; the equirect is %d x %d)", ok ? "PASS" : "FAIL",
                 name, worst, checked, EW, EH))
}

print(allGood ? "The PIXERA effect matches." : "The PIXERA effect differs.")
exit(allGood ? 0 : 1)
