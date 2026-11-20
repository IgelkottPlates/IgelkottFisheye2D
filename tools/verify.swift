// Provet för IgelkottFisheye2D: shadern ritas på riktigt (OpenGL på Macen, samma GLSL som Live FX läser) och varje
// utpixel jämförs med IgelkottStages räkning (FisheyeLens.point och CameraCost.rotation, avskrivna här i dubbel
// precision). Källan är en gradient (R = x, G = y uppifrån, normerade), så utpixelns färg är källpunkten shadern läste.
//
// Varje fall körs i båda radordningarna: Live FX (standard, Flip Vertical av) lägger källan och utbilden uppifrån i
// minnet — här efterliknat genom att gradienten laddas upp översta raden först och utbilden läses med rad 0 överst —
// och OpenGL/Flame (Flip Vertical på), nerifrån.
//
//   swift tools/verify.swift            (från projektroten)
//
// Stabiliseringen (Stab Yaw, Pitch, Roll) prövas två gånger: i fallen (förväntat d = S · R · stråle) och i ett eget
// prov där Back, Side, Sky och Ref TV ritas med och utan samma S; källpunkterna räknas tillbaka till riktningar, och
// varje pixel i varje vy ska ha vridits med just S — sfären rör sig som en kropp.
//
// Ger 0 när alla fall håller (största felet i källpixlar vid 8040 under gränsen), annars 1.
import Foundation
import OpenGL.GL
import OpenGL.GL3
import simd

// MARK: - IgelkottStages räkning (StageKit/FisheyeLens.swift, StageProtocol/CameraCost.swift)

let REF = 8040.0
let CENTER = SIMD2(4019.9389914282037, 4019.9389463189077)
let K = SIMD4(2068.8673345215607, -31.032060077989637, 0.1394366394877631, -0.00029359255648059773)

func rotation(yaw: Double, pitch: Double, roll: Double) -> simd_double3x3 {
    let y = yaw * .pi / 180, p = -pitch * .pi / 180, r = roll * .pi / 180
    let ry = simd_double3x3(columns: (SIMD3(cos(y), 0, -sin(y)), SIMD3(0, 1, 0), SIMD3(sin(y), 0, cos(y))))
    let rx = simd_double3x3(columns: (SIMD3(1, 0, 0), SIMD3(0, cos(p), sin(p)), SIMD3(0, -sin(p), cos(p))))
    let rz = simd_double3x3(columns: (SIMD3(cos(r), sin(r), 0), SIMD3(-sin(r), cos(r), 0), SIMD3(0, 0, 1)))
    return ry * rx * rz
}

// Sony Venice 2 (_shared/IgelkottFisheyeLens, FisheyeLens.sonyVenice2): egen referens, mitt och kurva. Kontrolleras
// mot den delade filen nedan, så att shadern, provet och resten av husen inte glider isär.
let VREF = 5760.0
let VCENTER = SIMD2(2848.031459694644, 2854.3896750742356)
let VK = SIMD4(1440.3464186123263, -21.606695057429874, 0.09789618777410111, -0.0002943394610105899)

/// Kamerans modell i andelar av bildens bredd: (mitten, kurvan). camera 0 = PYXIS skalad (Sensor Height, Lens Scale),
/// 1 = PYXIS 12K som den är, 2 = Sony Venice 2.
func lens(camera: Int32, scale: Double) -> (center: SIMD2<Double>, k: SIMD4<Double>) {
    camera == 2 ? (VCENTER / VREF, VK / VREF) : (CENTER / REF, K / REF * (camera == 1 ? 1 : scale))
}

/// Källpunkten i pixlar vid 8040 (origo uppe till vänster), som FisheyeLens.point.
func point(_ d: SIMD3<Double>, offset: SIMD2<Double>, scale: Double = 1, camera: Int32 = 0) -> SIMD2<Double> {
    let l = lens(camera: camera, scale: scale)
    let rho = (d.x * d.x + d.z * d.z).squareRoot()
    let th = atan2(rho, d.y), t2 = th * th
    let poly = l.k.x + t2 * (l.k.y + t2 * (l.k.z + t2 * l.k.w))
    let f = rho > 1e-9 ? poly * th / rho : poly
    return (l.center + SIMD2(d.x, d.z) * f) * REF + offset
}

/// Väggens riktning genom lagerpunkten (x, y uppifrån, pixelmitt = heltal + 0,5), som CameraCost.Projection.direction med
/// Eq->2D:s brännvidd ur den lodräta FOV:en.
func wallDirection(_ x: Double, _ yTop: Double, w: Double, h: Double, fov: Double, R: simd_double3x3) -> SIMD3<Double> {
    let f = (h / 2) / tan(fov * .pi / 360)
    return R * simd_normalize(SIMD3((x - w / 2) / f, (h / 2 - yTop) / f, 1))
}

/// Tracking view: fast skala i grader per pixel (TRACK_SCALE i shadern), sidled och höjd raka i bilden; R = bara yaw.
let TRACK_SCALE = 0.02
func trackDirection(_ x: Double, _ yTop: Double, w: Double, h: Double, R: simd_double3x3) -> SIMD3<Double> {
    let lon = (x - w / 2) * TRACK_SCALE * .pi / 180, lat = (h / 2 - yTop) * TRACK_SCALE * .pi / 180
    return R * SIMD3(cos(lat) * sin(lon), sin(lat), cos(lat) * cos(lon))
}

/// Equirect: dirToSrc baklänges.
func equiDirection(_ x: Double, _ yTop: Double, w: Double, h: Double, R: simd_double3x3) -> SIMD3<Double> {
    let lon = (x / w - 0.5) * 2 * .pi, lat = (0.5 - yTop / h) * .pi
    return R * SIMD3(cos(lat) * sin(lon), sin(lat), cos(lat) * cos(lon))
}

/// Källpunkten (pixlar vid 8040) tillbaka till riktningen: r(θ) löst med Newton.
func unproject(_ p: SIMD2<Double>, offset: SIMD2<Double>, scale: Double = 1, camera: Int32 = 0) -> SIMD3<Double> {
    let l = lens(camera: camera, scale: scale), k = l.k
    let v = (p - offset) / REF - l.center, len = simd_length(v), r = len
    var th = r / k.x
    for _ in 0..<20 {
        let t2 = th * th
        let g = th * (k.x + t2 * (k.y + t2 * (k.z + t2 * k.w))) - r
        let dg = k.x + t2 * (3 * k.y + t2 * (5 * k.z + t2 * 7 * k.w))
        th -= g / dg
    }
    let s = len > 1e-9 ? sin(th) / len : 0
    return SIMD3(v.x * s, cos(th), v.y * s)
}

// MARK: - OpenGL

func fail(_ s: String) -> Never { FileHandle.standardError.write((s + "\n").data(using: .utf8)!); exit(1) }

var attrs: [CGLPixelFormatAttribute] = [kCGLPFAAccelerated, kCGLPFAAllowOfflineRenderers, CGLPixelFormatAttribute(0)]
var pf: CGLPixelFormatObj?
var npix: GLint = 0
guard CGLChoosePixelFormat(&attrs, &pf, &npix) == kCGLNoError, let pf else { fail("no pixel format") }
var ctx: CGLContextObj?
guard CGLCreateContext(pf, nil, &ctx) == kCGLNoError, let ctx else { fail("no context") }
CGLSetCurrentContext(ctx)
print("OpenGL: \(String(cString: glGetString(GLenum(GL_RENDERER)))) · GLSL \(String(cString: glGetString(GLenum(GL_SHADING_LANGUAGE_VERSION))))")

let root = URL(fileURLWithPath: CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : FileManager.default.currentDirectoryPath)
let source = try String(contentsOf: root.appendingPathComponent("matchbox/IgelkottFisheye2D.glsl"), encoding: .utf8)

func compile(_ type: GLenum, _ text: String) -> GLuint {
    let s = glCreateShader(type)
    text.withCString { p in var ptr: UnsafePointer<GLchar>? = p; glShaderSource(s, 1, &ptr, nil) }
    glCompileShader(s)
    var ok: GLint = 0; glGetShaderiv(s, GLenum(GL_COMPILE_STATUS), &ok)
    if ok == 0 {
        var log = [GLchar](repeating: 0, count: 4096); glGetShaderInfoLog(s, 4096, nil, &log)
        fail("shader compile failed:\n\(String(cString: log))")
    }
    return s
}
let vs = compile(GLenum(GL_VERTEX_SHADER), "#version 120\nvoid main() { gl_Position = gl_Vertex; }\n")
let fs = compile(GLenum(GL_FRAGMENT_SHADER), source)
let prog = glCreateProgram()
glAttachShader(prog, vs); glAttachShader(prog, fs); glLinkProgram(prog)
var linked: GLint = 0; glGetProgramiv(prog, GLenum(GL_LINK_STATUS), &linked)
if linked == 0 { fail("link failed") }
glUseProgram(prog)
print("The shader compiles and links (GLSL 1.20).")

// Källan: N × N gradient, R = x / N och G = y uppifrån / N i texelns mitt. Uppladdad rad 0 = bildens översta (Live FX)
// eller nedersta (OpenGL/Flame).
var N = 1024
func gradient(topRowFirst: Bool) -> [Float] {
    var tex: [Float] = []
    tex.reserveCapacity(N * N * 4)
    for row in 0..<N {
        let yTop = Double(topRowFirst ? row : N - 1 - row)
        for x in 0..<N { tex += [Float((Double(x) + 0.5) / Double(N)), Float((yTop + 0.5) / Double(N)), 0, 1] }
    }
    return tex
}
var srcTex: GLuint = 0
glGenTextures(1, &srcTex); glActiveTexture(GLenum(GL_TEXTURE0)); glBindTexture(GLenum(GL_TEXTURE_2D), srcTex)
glTexParameteri(GLenum(GL_TEXTURE_2D), GLenum(GL_TEXTURE_MIN_FILTER), GL_LINEAR)
glTexParameteri(GLenum(GL_TEXTURE_2D), GLenum(GL_TEXTURE_MAG_FILTER), GL_LINEAR)
glTexParameteri(GLenum(GL_TEXTURE_2D), GLenum(GL_TEXTURE_WRAP_S), GL_CLAMP_TO_EDGE)
glTexParameteri(GLenum(GL_TEXTURE_2D), GLenum(GL_TEXTURE_WRAP_T), GL_CLAMP_TO_EDGE)
glUniform1i(glGetUniformLocation(prog, "front"), 0)

struct Case { var name: String; var w: Int; var h: Int; var yaw, pitch, roll, fov: Double; var offset: SIMD2<Double>; var quality: Int32; var mode: Int32
              var stab = SIMD3<Double>(0, 0, 0)                         // Stab Yaw, Pitch, Roll
              var scale = 1.0                                           // Lens Scale
              var sensorHeight = 23.32                                  // Sensor Height mm (23,32 = PYXIS 12K)
              var camera: Int32 = 0 }                                   // 0 Custom, 1 PYXIS 12K, 2 Sony Venice 2
let cases = [
    Case(name: "Back 3840x2160 (scaled 384x216), pitch 15, FOV 58.5", w: 384, h: 216, yaw: 0, pitch: 15, roll: 0, fov: 58.5, offset: .zero, quality: 1, mode: 0),
    Case(name: "Side, yaw 90, FOV 90, square", w: 256, h: 256, yaw: 90, pitch: 0, roll: 0, fov: 90, offset: .zero, quality: 1, mode: 0),
    Case(name: "Sky, pitch 70, roll 12", w: 256, h: 256, yaw: -35, pitch: 70, roll: 12, fov: 100, offset: .zero, quality: 1, mode: 0),
    Case(name: "LED 960x540 (scaled 192x108), yaw 81.8, FOV 10", w: 192, h: 108, yaw: 81.8, pitch: -4, roll: 0, fov: 10, offset: .zero, quality: 1, mode: 0),
    Case(name: "Ref TV, yaw 180, plate offset (+12.5, -7.25)", w: 192, h: 108, yaw: 180, pitch: 2, roll: -3, fov: 20, offset: SIMD2(12.5, -7.25), quality: 1, mode: 0),
    Case(name: "Back, quality 3 x 3", w: 384, h: 216, yaw: 10, pitch: 15, roll: 0, fov: 58.5, offset: .zero, quality: 3, mode: 0),
    Case(name: "Equirect 512x256", w: 512, h: 256, yaw: 0, pitch: 0, roll: 0, fov: 90, offset: .zero, quality: 1, mode: 1),
    Case(name: "Back, Stab Pitch +1.3", w: 384, h: 216, yaw: 0, pitch: 15, roll: 0, fov: 58.5, offset: .zero, quality: 1, mode: 0, stab: SIMD3(0, 1.3, 0)),
    Case(name: "Side, yaw 90, Stab Yaw 4, Pitch -3, Roll 2.5", w: 256, h: 256, yaw: 90, pitch: 0, roll: 0, fov: 90, offset: .zero, quality: 1, mode: 0, stab: SIMD3(4, -3, 2.5)),
    Case(name: "Sky, Stab Yaw -20, Pitch 6, Roll -8, quality 2 x 2", w: 256, h: 256, yaw: -35, pitch: 70, roll: 12, fov: 100, offset: .zero, quality: 2, mode: 0, stab: SIMD3(-20, 6, -8)),
    Case(name: "Ref TV, yaw 180, plate offset, Stab Pitch -0.6, Roll 1", w: 192, h: 108, yaw: 180, pitch: 2, roll: -3, fov: 20, offset: SIMD2(12.5, -7.25), quality: 1, mode: 0, stab: SIMD3(0, -0.6, 1)),
    Case(name: "Side, yaw 90, Lens Scale 0.9715 (another camera)", w: 256, h: 256, yaw: 90, pitch: 0, roll: 0, fov: 90, offset: .zero, quality: 1, mode: 0, scale: 0.9715),
    Case(name: "Back, Lens Scale 1.2, plate offset, Stab Pitch 1", w: 384, h: 216, yaw: 0, pitch: 15, roll: 0, fov: 58.5, offset: SIMD2(-20, 9), quality: 2, mode: 0, stab: SIMD3(0, 1, 0), scale: 1.2),
    Case(name: "Side, yaw 90, Sensor Height 24 mm", w: 256, h: 256, yaw: 90, pitch: 0, roll: 0, fov: 90, offset: .zero, quality: 1, mode: 0, sensorHeight: 24),
    Case(name: "Back, Sensor Height 18 mm, Lens Scale 1.01", w: 384, h: 216, yaw: 0, pitch: 15, roll: 0, fov: 58.5, offset: .zero, quality: 1, mode: 0, scale: 1.01, sensorHeight: 18),
    Case(name: "Fisheye (stabilize), Stab 0: the same image out", w: 256, h: 256, yaw: 0, pitch: 0, roll: 0, fov: 90, offset: .zero, quality: 1, mode: 2),
    Case(name: "Fisheye (stabilize), Stab Yaw 2, Pitch -1.3, Roll 0.7, Sensor Height 23.9, plate offset", w: 256, h: 256, yaw: 40, pitch: 9, roll: 3, fov: 90, offset: SIMD2(12.5, -7.25), quality: 2, mode: 2, stab: SIMD3(2, -1.3, 0.7), sensorHeight: 23.9),
    Case(name: "Tracking view 384x216, yaw 25 (pitch, roll and FOV not used)", w: 384, h: 216, yaw: 25, pitch: 40, roll: 17, fov: 33, offset: .zero, quality: 1, mode: 3, sensorHeight: 23.9),
    Case(name: "Tracking view 256x256, yaw -140, Stab Yaw 1.5, quality 2 x 2", w: 256, h: 256, yaw: -140, pitch: 0, roll: 0, fov: 90, offset: SIMD2(-24, -39), quality: 2, mode: 3, stab: SIMD3(1.5, 0, 0), sensorHeight: 23.9),
    Case(name: "Camera Sony Venice 2, Back (Sensor Height and Lens Scale not used)", w: 384, h: 216, yaw: 0, pitch: 15, roll: 0, fov: 58.5, offset: .zero, quality: 1, mode: 0, scale: 1.3, sensorHeight: 30, camera: 2),
    Case(name: "Camera Sony Venice 2, Ref TV yaw 180 with Lens Offset", w: 192, h: 108, yaw: 180, pitch: 2, roll: -3, fov: 20, offset: SIMD2(12.5, -7.25), quality: 1, mode: 0, camera: 2),
    Case(name: "Camera Sony Venice 2, Fisheye (stabilize) Stab 1.5 / -0.8", w: 256, h: 256, yaw: 0, pitch: 0, roll: 0, fov: 90, offset: .zero, quality: 1, mode: 2, stab: SIMD3(1.5, -0.8, 0), camera: 2),
    Case(name: "Camera Sony Venice 2, Tracking view yaw 30", w: 384, h: 216, yaw: 30, pitch: 0, roll: 0, fov: 90, offset: .zero, quality: 1, mode: 3, camera: 2),
    Case(name: "Camera PYXIS 12K (Sensor Height 18 not used)", w: 256, h: 256, yaw: 90, pitch: 0, roll: 0, fov: 90, offset: .zero, quality: 1, mode: 0, sensorHeight: 18, camera: 1),
    Case(name: "Equirect, Stab Yaw 30, Pitch 10, Roll -5", w: 512, h: 256, yaw: 0, pitch: 0, roll: 0, fov: 90, offset: .zero, quality: 1, mode: 1, stab: SIMD3(30, 10, -5)),
]

/// Ritar ett fall och ger utbilden (RGBA, glReadPixels ordning).
func render(_ c: Case, liveFX: Bool) -> [Float] {
    var fbo: GLuint = 0, out: GLuint = 0
    glGenTextures(1, &out); glBindTexture(GLenum(GL_TEXTURE_2D), out)
    glTexImage2D(GLenum(GL_TEXTURE_2D), 0, GL_RGBA32F_ARB, GLsizei(c.w), GLsizei(c.h), 0, GLenum(GL_RGBA), GLenum(GL_FLOAT), nil)
    glGenFramebuffersEXT(1, &fbo); glBindFramebufferEXT(GLenum(GL_FRAMEBUFFER_EXT), fbo)
    glFramebufferTexture2DEXT(GLenum(GL_FRAMEBUFFER_EXT), GLenum(GL_COLOR_ATTACHMENT0_EXT), GLenum(GL_TEXTURE_2D), out, 0)
    guard glCheckFramebufferStatusEXT(GLenum(GL_FRAMEBUFFER_EXT)) == GLenum(GL_FRAMEBUFFER_COMPLETE_EXT) else { fail("incomplete framebuffer") }
    glBindTexture(GLenum(GL_TEXTURE_2D), srcTex)
    glViewport(0, 0, GLsizei(c.w), GLsizei(c.h))
    func set(_ n: String, _ v: Float) { glUniform1f(glGetUniformLocation(prog, n), v) }
    set("adsk_result_w", Float(c.w)); set("adsk_result_h", Float(c.h))
    set("yaw", Float(c.yaw)); set("pitch", Float(c.pitch)); set("roll", Float(c.roll)); set("fov", Float(c.fov))
    set("stab_yaw", Float(c.stab.x)); set("stab_pitch", Float(c.stab.y)); set("stab_roll", Float(c.stab.z))
    set("offset_x", Float(c.offset.x)); set("offset_y", Float(c.offset.y)); set("lens_scale", Float(c.scale))
    set("sensor_height", Float(c.sensorHeight))
    glUniform1i(glGetUniformLocation(prog, "camera"), c.camera)
    glUniform1i(glGetUniformLocation(prog, "quality"), c.quality)
    glUniform1i(glGetUniformLocation(prog, "mode"), c.mode)
    glUniform1i(glGetUniformLocation(prog, "flip_v"), liveFX ? 0 : 1)
    glClear(GLbitfield(GL_COLOR_BUFFER_BIT))
    glBegin(GLenum(GL_QUADS)); glVertex2f(-1, -1); glVertex2f(1, -1); glVertex2f(1, 1); glVertex2f(-1, 1); glEnd()
    var px = [Float](repeating: 0, count: c.w * c.h * 4)
    glReadPixels(0, 0, GLsizei(c.w), GLsizei(c.h), GLenum(GL_RGBA), GLenum(GL_FLOAT), &px)
    glDeleteFramebuffersEXT(1, &fbo); glDeleteTextures(1, &out)
    return px
}

var allGood = true
// Källans storlek ska inte spela någon roll: noden räknar i andelar av bilden. Andra varvet har en källa på 1008 × 1008
// (4032 / 4, inte en tvåpotens) — PYXIS-mastrarna är 4032² sedan 2026-11-04 (IgelkottDarkroom), samma bild som 8040²
// nedskalad.
for texN in [1024, 1008] {
N = texN
for liveFX in (texN == 1024 ? [true, false] : [true]) {
print((liveFX ? "Live FX row order (top row first, Flip Vertical off)" : "OpenGL/Flame row order (bottom row first, Flip Vertical on)") +
      (texN == 1024 ? ":" : ", source 1008 × 1008 (4032 / 4):"))
glBindTexture(GLenum(GL_TEXTURE_2D), srcTex)
glTexImage2D(GLenum(GL_TEXTURE_2D), 0, GL_RGBA32F_ARB, GLsizei(N), GLsizei(N), 0, GLenum(GL_RGBA), GLenum(GL_FLOAT),
             gradient(topRowFirst: liveFX))
for c in cases {
    let px = render(c, liveFX: liveFX)

    let S = rotation(yaw: c.stab.x, pitch: c.stab.y, roll: c.stab.z)
    let R = S * rotation(yaw: c.yaw, pitch: c.pitch, roll: c.roll)
    let lensScale = c.scale * 23.32 / c.sensorHeight
    let n = Int(c.quality)
    var worst = 0.0, checked = 0, black = 0, wrongBlack = 0
    for row in 0..<c.h {
        let yTopPix = liveFX ? row : c.h - 1 - row                    // glReadPixels rad 0 = översta i Live FX:s ordning
        for x in 0..<c.w {
            // Förväntat: medlet av källpunkterna i provens lägen (normerade), svart utanför bildramen
            var sum = SIMD2<Double>.zero, inside = 0
            for j in 0..<n {
                for i in 0..<n {
                    let sx = Double(x) + (Double(i) + 0.5) / Double(n)
                    // Provets läge uppifrån: (j + 0,5) / n från gl_FragCoord-radens början, som räknas uppifrån i
                    // Live FX:s ordning och nerifrån i OpenGL:s
                    let sy = liveFX ? Double(yTopPix) + (Double(j) + 0.5) / Double(n)
                                    : Double(yTopPix) + 1 - (Double(j) + 0.5) / Double(n)
                    let d = c.mode == 3 ? trackDirection(sx, sy, w: Double(c.w), h: Double(c.h), R: S * rotation(yaw: c.yaw, pitch: 0, roll: 0))
                          : c.mode == 2 ? S * unproject(SIMD2(sx / Double(c.w), sy / Double(c.h)) * REF, offset: c.offset, scale: lensScale, camera: c.camera)
                          : c.mode == 1 ? equiDirection(sx, sy, w: Double(c.w), h: Double(c.h), R: R)
                                        : wallDirection(sx, sy, w: Double(c.w), h: Double(c.h), fov: c.fov, R: R)
                    let p = point(d, offset: c.offset, scale: lensScale, camera: c.camera) / REF
                    if p.x >= 0, p.x <= 1, p.y >= 0, p.y <= 1 {
                        // Gradientens bilinjära värde: rakt inom texelmitterna, klämt vid kanten
                        let lo = 0.5 / Double(N), hi = 1 - lo
                        sum += SIMD2(min(max(p.x, lo), hi), min(max(p.y, lo), hi)); inside += 1
                    }
                }
            }
            let k = (row * c.w + x) * 4
            let got = SIMD2(Double(px[k]), Double(px[k + 1]))
            if inside == 0 {
                black += 1
                if got.x != 0 || got.y != 0 { wrongBlack += 1 }
                continue
            }
            guard inside == n * n else { continue }                   // pixlar på bildramens kant: blandade, hoppas över
            let want = sum / Double(n * n)
            worst = max(worst, simd_length(got - want) * REF)
            checked += 1
        }
    }
    let ok = worst < 0.5 && wrongBlack == 0 && checked > 0
    allGood = allGood && ok
    print(String(format: "  %@ %@: largest error %.3f source px at 8040 (%d px checked, %d black outside the frame%@)",
                 ok ? "PASS" : "FAIL", c.name, worst, checked, black, wrongBlack > 0 ? ", \(wrongBlack) NOT black" : ""))
}

// Sfären som en kropp: samma S på fyra vyer, varje pixels riktning ska ha vridits med S (vinkeln i källpixlar vid 8040
// mitt i bilden, K.x pixlar per radian)
let stab = SIMD3(1.5, 1.3, -0.8)
let S = rotation(yaw: stab.x, pitch: stab.y, roll: stab.z)
print("  The sphere as one body, Stab Yaw \(stab.x), Pitch \(stab.y), Roll \(stab.z) on every view:")
for c0 in [cases[0], cases[1], cases[2], cases[4]] {
    var c1 = c0; c1.stab = stab
    let a = render(c0, liveFX: liveFX), b = render(c1, liveFX: liveFX)
    var worst = 0.0, checked = 0
    let lo = 1.0 / Double(N), hi = 1 - lo                             // inte i gradientens klämda kant
    for k in stride(from: 0, to: a.count, by: 4) {
        let p0 = SIMD2(Double(a[k]), Double(a[k + 1])), p1 = SIMD2(Double(b[k]), Double(b[k + 1]))
        guard p0.x > lo, p0.x < hi, p0.y > lo, p0.y < hi, p1.x > lo, p1.x < hi, p1.y > lo, p1.y < hi else { continue }
        let d0 = unproject(p0 * REF, offset: c0.offset), d1 = unproject(p1 * REF, offset: c0.offset)
        let e = S * d0
        worst = max(worst, atan2(simd_length(simd_cross(e, d1)), simd_dot(e, d1)) * K.x)
        checked += 1
    }
    let ok = worst < 0.5 && checked > 0
    allGood = allGood && ok
    print(String(format: "  %@ %@: largest deviation from S %.3f source px at 8040 (%d px checked)",
                 ok ? "PASS" : "FAIL", c0.name, worst, checked))
}
}
}

// Tecknet, för PROJECT.md: var hamnar väggen rakt fram och den rakt bak med Stab Pitch +5?
for (name, yaw) in [("yaw 0", 0.0), ("yaw 180", 180.0)] {
    let d = rotation(yaw: 0, pitch: 5, roll: 0) * rotation(yaw: yaw, pitch: 0, roll: 0) * SIMD3(0, 0, 1)
    print(String(format: "Stab Pitch +5: the centre of the wall at %@ fetches the source at elevation %+.2f deg", name, asin(d.y) * 180 / .pi))
}
// Kamerornas tal ska vara desamma som i _shared/IgelkottFisheyeLens (shadern kontrolleras mot provets tal ovan)
let sharedURL = root.deletingLastPathComponent().appendingPathComponent("_shared/IgelkottFisheyeLens/Sources/IgelkottFisheyeLens/FisheyeLens.swift")
if let shared = try? String(contentsOf: sharedURL, encoding: .utf8) {
    let shaderText = source
    var same = true
    for (name, nums) in [("pyxis12K", [CENTER.x, CENTER.y, K.x, K.y, K.z, K.w]), ("sonyVenice2", [VCENTER.x, VCENTER.y, VK.x, VK.y, VK.z, VK.w])] {
        guard let r = shared.range(of: "static let \(name)") else { same = false; continue }
        let block = String(shared[r.lowerBound...].prefix(600))
        for v in nums where !block.contains("\(v)") || !shaderText.contains("\(v)") { same = false; print("  differs: \(name) \(v)") }
    }
    allGood = allGood && same
    print("  \(same ? "PASS" : "FAIL") PYXIS 12K and Sony Venice 2: the shader and this test use the numbers in _shared/IgelkottFisheyeLens")
} else {
    print("  (could not read \(sharedURL.path); the camera numbers were not compared)")
}
print(allGood ? "All cases match IgelkottStage." : "Some cases differ from IgelkottStage.")
exit(allGood ? 0 : 1)
