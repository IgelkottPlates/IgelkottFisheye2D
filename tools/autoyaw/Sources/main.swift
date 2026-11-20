// Auto Stabilize för IgelkottFisheye: fisheyeklippet in, Stab Yaw-kurvan ut. Ingen tracker och inga mått.
// (Eric 2026-10-12: "detta måste automatiseras, kan inte va ansvarig för detta" — FOV, bildstorlek och startpunkt
// skrevs in för hand och blev fel utan varning.)
//
// Med objektivet rakt upp är pan (yaw) en vridning av bilden kring objektivets mitt. Ett band strax över horisonten
// (himmel och avlägsna berg; inte marken, som rör sig med farten) vecklas ut till vinkel × radie, och vridningen mellan
// två bildrutor är den förskjutning längs vinkeln som passar bäst. Summan är panen; skaket = pan − väg (Gauss-utjämning
// åt båda hållen, som trackingvyn i directionlock.swift) skrivs som Stab Yaw.
//
// Det som förr skrevs in hämtas ur klippet: bildtakten, antalet bildrutor och — ur Darkroms hörnmärke — kameran och
// objektivets mitt. FOV och startpunkt finns inte i den här räkningen.
//
// Objektivets mitt (2026-10-19, handoffarna från IgelkottMotion och IgelkottDarkroom: bara Darkroom hittar bildcirkeln):
//  - ett litat hörnmärke (QR i hörnen, IGK1|1|<kamera>|…, läst med IgelkottLensMark): kamerans modell som den är;
//  - annars kameran ur --camera (standard PYXIS 12K) och mitten ur FisheyetoEquis kalibrering för klippet, eller modellens
//    egen (FisheyeLens.forClip). Ingen egen cirkeldetektor — den mätte bakgrunden i hörnen, där märket nu står.
//
// Provat mot Offroad-plåten 2026-10-12 (1124 bildrutor): mot molnspåret genom objektivets modell korrelation 0,9995,
// största skillnad 0,035°; mot trackingvyn utan dess spikar 0,998. Inga spikar, där trackern hade nio.
//
//   autoyaw <klipp.mov> [--camera pyxis12K|sonyVenice2] [--out <mapp>] [--smooth 0.5] [--strength 1] [--invert] [--whole]
//   autoyaw --selftest          (påhittat klipp med känd pan; 0 när det stämmer)
// Bygg: tools/autoyaw/Package.swift.
import Foundation
import AVFoundation
import Accelerate
import IgelkottFisheyeLens
import IgelkottLensMark

func fail(_ s: String) -> Never { FileHandle.standardError.write((s + "\n").data(using: .utf8)!); exit(1) }

// Objektivet (FisheyeLens.pyxis12K), bara för var horisonten ligger i bildcirkeln: radie / cirkelns radie vid en höjd
let K = (2068.8673345215607, -31.032060077989637, 0.1394366394877631, -0.00029359255648059773)
func lensRadius(_ th: Double) -> Double { let t2 = th * th; return th * (K.0 + t2 * (K.1 + t2 * (K.2 + t2 * K.3))) }
func circleFraction(elevation: Double) -> Double { lensRadius((90 - elevation) * .pi / 180) / lensRadius(125 * .pi / 180) }

/// Objektivets mitt och bildcirkelns radie (125° från zenit) i en gråbild S pixlar bred.
struct Circle { var cx: Double; var cy: Double; var r: Double }

/// Cirkeln ur en kameras modell (mitten kan vara flyttad av FisheyetoEquis kalibrering), i en bild S pixlar bred.
func lensCircleOf(_ lens: FisheyeLens, size S: Int) -> Circle {
    let k = Double(S) / lens.reference
    return Circle(cx: lens.center.x * k, cy: lens.center.y * k, r: lens.radius(125 * .pi / 180) * k)
}

/// Vridningen mellan bildrutor i ett band över horisonten.
struct PanEstimator {
    let S: Int
    let A = 3600, NR = 40, maxShift = 40                             // 0,1° per steg; högst ±4° mellan två bildrutor
    var sx: [Float], sy: [Float]
    var prev: [Float]? = nil

    init(size: Int, circle: Circle) {
        S = size
        sx = [Float](repeating: 0, count: A * NR); sy = sx
        for j in 0..<NR {
            // 3° … 28° över horisonten
            let rad = circle.r * circleFraction(elevation: 3 + 25 * Double(j) / Double(NR - 1))
            for a in 0..<A {
                let p = Double(a) * 2 * .pi / Double(A)
                sx[j * A + a] = Float(circle.cx + rad * sin(p)); sy[j * A + a] = Float(circle.cy + rad * cos(p))   // vinkeln = sidled, 0 = framåt (bildens nederkant)
            }
        }
    }

    /// Bandet utvecklat ur en gråbild, varje radie utan sitt långsamma förlopp (6° glidande medel)
    func unwrap(_ g: [UInt8]) -> [Float] {
        var out = [Float](repeating: 0, count: A * NR)
        var valid = [Bool](repeating: false, count: A * NR)
        g.withUnsafeBufferPointer { b in
            for i in 0..<(A * NR) {
                let x = sx[i], y = sy[i]
                let x0 = Int(x.rounded(.down)), y0 = Int(y.rounded(.down))
                guard x0 >= 0, y0 >= 0, x0 < S - 1, y0 < S - 1 else { continue }
                let fx = x - Float(x0), fy = y - Float(y0), o = y0 * S + x0
                out[i] = (Float(b[o]) * (1 - fx) + Float(b[o + 1]) * fx) * (1 - fy) + (Float(b[o + S]) * (1 - fx) + Float(b[o + S + 1]) * fx) * fy
                valid[i] = true
            }
        }
        var hp = [Float](repeating: 0, count: A * NR)
        let win = 60
        var pre = [Double](repeating: 0, count: 3 * A + 1)
        for j in 0..<NR {
            for a in 0..<(3 * A) { pre[a + 1] = pre[a] + Double(out[j * A + a % A]) }
            for a in 0..<A where valid[j * A + a] {
                let mean = (pre[A + a + win + 1] - pre[A + a - win]) / Double(2 * win + 1)
                hp[j * A + a] = out[j * A + a] - Float(mean)
            }
        }
        return hp
    }

    /// Lägger till en bildruta; ger vridningen sedan förra (grader, + = innehållet har gått åt höger i bilens ram)
    mutating func add(_ g: [UInt8]) -> Double {
        let cur = unwrap(g)
        defer { prev = cur }
        guard let p = prev else { return 0 }
        var score = [Double](repeating: 0, count: 2 * maxShift + 1)
        p.withUnsafeBufferPointer { pb in cur.withUnsafeBufferPointer { cb in
            for s in -maxShift...maxShift {
                var acc: Float = 0
                for j in 0..<NR {
                    let o = j * A
                    // prev[a] · cur[a + s] över hela varvet, i två raka stycken
                    let k = (s + A) % A
                    var d1: Float = 0, d2: Float = 0
                    vDSP_dotpr(pb.baseAddress! + o, 1, cb.baseAddress! + o + k, 1, &d1, vDSP_Length(A - k))
                    if k > 0 { vDSP_dotpr(pb.baseAddress! + o + A - k, 1, cb.baseAddress! + o, 1, &d2, vDSP_Length(k)) }
                    acc += d1 + d2
                }
                score[s + maxShift] = Double(acc)
            }
        } }
        let b = score.indices.max { score[$0] < score[$1] }!
        var sub = 0.0
        if b > 0, b < score.count - 1 {
            let l = score[b - 1], c = score[b], r = score[b + 1], d = l - 2 * c + r
            if d < 0 { sub = 0.5 * (l - r) / d }
        }
        return (Double(b - maxShift) + sub) * 360 / Double(A)
    }
}

/// Gauss-utjämning åt båda hållen, kanten upprepad (samma som directionlock.swift och stabilizer-sidan).
func gauss(_ v: [Double], sigma: Double) -> [Double] {
    let r = Int(3 * sigma), n = v.count
    let w = (-r...r).map { exp(-0.5 * pow(Double($0) / sigma, 2)) }
    return (0..<n).map { i in
        var acc = 0.0, sum = 0.0
        for (j, k) in w.enumerated() { acc += v[min(max(i + j - r, 0), n - 1)] * k; sum += k }
        return acc / sum
    }
}

func curveCSV(_ name: String, _ values: [Double]) -> String {
    var s = "#ANIM Stab\\\(name)\n#COND CC\n"
    for (i, v) in values.enumerated() { let p = String(format: "%d.000000,%.6f", i, v); s += "\(p),\(p),\(p)\n" }
    return s
}

// MARK: - Provet: ett påhittat klipp med känd pan

func selftest() -> Never {
    let S = 768, n = 120
    var rng = SystemRandomNumberGenerator()
    // Struktur som bara beror på riktningen: summor av vågor längs vinkeln, olika per radie
    let waves = (0..<60).map { _ in (h: Double(Int.random(in: 3...220, using: &rng)), ph: Double.random(in: 0...(2 * .pi), using: &rng),
                                     amp: Double.random(in: 4...16, using: &rng), rr: Double.random(in: 0...6, using: &rng)) }
    let circle = (cx: 0.497 * Double(S), cy: 0.492 * Double(S), r: 0.509 * Double(S))
    var truth = [0.0]
    for i in 1..<n { truth.append(14 * sin(Double(i) / 45) + 1.1 * sin(Double(i) / 3.1) + 0.5 * sin(Double(i) / 1.3)) }
    func frame(_ yaw: Double) -> [UInt8] {
        var g = [UInt8](repeating: 18, count: S * S)
        for y in 0..<S { for x in 0..<S {
            let dx = Double(x) + 0.5 - circle.cx, dy = Double(y) + 0.5 - circle.cy, r = hypot(dx, dy)
            guard r < circle.r else { continue }
            let phi = atan2(dx, dy) - yaw * .pi / 180, q = r / circle.r                 // innehållet har gått +yaw längs vinkeln
            var v = 128.0
            for w in waves { v += w.amp * sin(w.h * phi + w.ph + w.rr * q) }
            g[y * S + x] = UInt8(max(40, min(250, v)))
        } }
        return g
    }
    let first = frame(truth[0])
    let found = Circle(cx: circle.cx, cy: circle.cy, r: circle.r)
    // Venice-modellen i en 4096-bild: mitten där FisheyeLens.sonyVenice2 har den
    let v = lensCircleOf(.sonyVenice2, size: 4096)
    var good = abs(v.cx - 2848.031459694644 * 4096 / 5760) < 1e-9 && abs(v.r - FisheyeLens.sonyVenice2.radius(125 * .pi / 180) * 4096 / 5760) < 1e-9
    print(String(format: "  %@ image circle from the camera's lens model (Sony Venice 2 at 4096: centre %.1f, %.1f, radius %.1f)", good ? "PASS" : "FAIL", v.cx, v.cy, v.r))
    var est = PanEstimator(size: S, circle: found), pan = [0.0]
    _ = est.add(first)
    for i in 1..<n { pan.append(pan[i - 1] + est.add(frame(truth[i]))) }
    var worst = 0.0
    for i in 1..<n { worst = max(worst, abs((pan[i] - pan[i - 1]) - (truth[i] - truth[i - 1]))) }
    let ok = worst < 0.05
    good = good && ok
    print(String(format: "  %@ pan between frames: largest error %.4f deg over %d frames (pan %.1f … %.1f deg)", ok ? "PASS" : "FAIL", worst, n, truth.min()!, truth.max()!))
    print(good ? "Auto Stabilize finds a known pan." : "Auto Stabilize differs from the known pan.")
    exit(good ? 0 : 1)
}

// MARK: - Klippet

var args = Array(CommandLine.arguments.dropFirst())
var path: String? = nil, outDir: String? = nil, smooth = 0.5, strength = 1.0, invert = false, whole = false
var cameraFlag: String? = nil
while !args.isEmpty {
    let a = args.removeFirst()
    func number() -> Double { guard !args.isEmpty, let v = Double(args.removeFirst().replacingOccurrences(of: ",", with: ".")) else { fail("\(a) needs a number") }; return v }
    switch a {
    case "--selftest": selftest()
    case "--out": guard !args.isEmpty else { fail("--out needs a folder") }; outDir = args.removeFirst()
    case "--camera": guard !args.isEmpty else { fail("--camera needs pyxis12K or sonyVenice2") }; cameraFlag = args.removeFirst()
    case "--smooth": smooth = number()
    case "--strength": strength = number()
    case "--invert": invert = true
    case "--whole": whole = true
    default: path = a
    }
}
guard let path else { fail("usage: autoyaw <clip.mov> [--camera pyxis12K|sonyVenice2] [--out <folder>] [--smooth 0.5] [--strength 1] [--invert] [--whole]") }
let url = URL(fileURLWithPath: path)
let asset = AVURLAsset(url: url)
guard let track = asset.tracks(withMediaType: .video).first else { fail("Cannot read a video track in \(url.lastPathComponent). Use a QuickTime movie (ProRes, H.264 or HEVC).") }
let size = track.naturalSize
guard abs(size.width - size.height) <= 0.02 * size.width else {
    fail(String(format: "%@ is %.0f × %.0f. Auto Stabilize needs the square fisheye clip.", url.lastPathComponent, size.width, size.height))
}
let fps = Double(track.nominalFrameRate) > 1 ? Double(track.nominalFrameRate) : 25
let W = Int(size.width), S = min(1536, W)

// Kameran och objektivets mitt: ett litat hörnmärke först, annars --camera och FisheyetoEquis kalibrering
var lensModel: FisheyeLens, lensNote: String
let reading = await LensMark.read(movie: url)
if let r = reading, r.trusted, let cam = r.mark.camera {
    lensModel = cam
    lensNote = "\(cam.cameraName) from the corner mark (IgelkottDarkroom, \(r.corners.count) corners), no offset"
} else {
    if let p = cameraFlag, FisheyeLens.camera(profile: p) == nil { fail("Unknown camera \(p). Use pyxis12K or sonyVenice2.") }
    let cam = cameraFlag.flatMap { FisheyeLens.camera(profile: $0) } ?? FisheyeLens.defaultCamera
    lensModel = FisheyeLens.forClip(url.path, camera: cam)
    let centre = lensModel.centerSource == "lens" ? "the lens model's own centre" : "centre from \(lensModel.centerSource)"
    lensNote = "\(cam.cameraName) (\(cameraFlag == nil ? "default, no corner mark" : "--camera")), \(centre)" +
               (reading != nil ? " — a corner mark was found but is not trusted (\(reading!.corners.count) corners, in place: \(reading!.inPlace))" : "")
}
guard let reader = try? AVAssetReader(asset: asset) else { fail("Cannot open \(url.lastPathComponent).") }
let output = AVAssetReaderTrackOutput(track: track, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_420YpCbCr8BiPlanarFullRange])
output.alwaysCopiesSampleData = false
reader.add(output)
guard reader.startReading() else { fail("Cannot decode \(url.lastPathComponent): \(reader.error?.localizedDescription ?? "unknown error")") }

var gray = [UInt8](repeating: 0, count: S * S)
var estimator: PanEstimator? = nil
let lensCircle = lensCircleOf(lensModel, size: S)
var pan: [Double] = []
while let sample = output.copyNextSampleBuffer() {
    guard let pb = CMSampleBufferGetImageBuffer(sample) else { continue }
    CVPixelBufferLockBaseAddress(pb, .readOnly)
    var src = vImage_Buffer(data: CVPixelBufferGetBaseAddressOfPlane(pb, 0), height: vImagePixelCount(CVPixelBufferGetHeightOfPlane(pb, 0)),
                            width: vImagePixelCount(CVPixelBufferGetWidthOfPlane(pb, 0)), rowBytes: CVPixelBufferGetBytesPerRowOfPlane(pb, 0))
    gray.withUnsafeMutableBytes { raw in
        var dst = vImage_Buffer(data: raw.baseAddress, height: vImagePixelCount(S), width: vImagePixelCount(S), rowBytes: S)
        vImageScale_Planar8(&src, &dst, nil, vImage_Flags(kvImageHighQualityResampling))
    }
    CVPixelBufferUnlockBaseAddress(pb, .readOnly)
    if estimator == nil {
        estimator = PanEstimator(size: S, circle: lensCircle)
    }
    let step = estimator!.add(gray)
    pan.append((pan.last ?? 0) + step)
    if pan.count % 100 == 0 { FileHandle.standardError.write("\(pan.count) frames\n".data(using: .utf8)!) }
}
guard reader.status == .completed, pan.count >= 10 else { fail("Could not read the whole clip (\(pan.count) frames): \(reader.error?.localizedDescription ?? "too few frames")") }

let gain = strength * (invert ? -1 : 1)
let road = gauss(pan, sigma: max(1, (smooth * fps).rounded(.down)))
let shake = zip(pan, road).map { ($0 - $1) * gain }
let dir = outDir ?? url.deletingLastPathComponent().path
try? FileManager.default.createDirectory(atPath: dir, withIntermediateDirectories: true)
let base = url.deletingPathExtension().lastPathComponent
let out = "\(dir)/\(base) Stab Yaw.csv"
do {
    try curveCSV("Stab Yaw", shake).write(toFile: out, atomically: true, encoding: .utf8)
    if whole { try curveCSV("Stab Yaw", pan.map { $0 * gain }).write(toFile: "\(dir)/\(base) Stab Yaw (whole pan).csv", atomically: true, encoding: .utf8) }
} catch { fail("Cannot write \(out).") }
let k = Double(W) / Double(S)
print(String(format: "%d frames at %.3f fps, %d × %d", pan.count, fps, W, Int(size.height)))
print("Camera: \(lensNote)")
print(String(format: "Lens centre %.0f, %.0f px", lensCircle.cx * k, lensCircle.cy * k))
print(String(format: "Whole pan %.1f … %.1f deg (the road). Shake %.2f … %.2f deg.", pan.min()!, pan.max()!, shake.min()!, shake.max()!))
print(out)
