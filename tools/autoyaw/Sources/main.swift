// Auto Stabilize for IgelkottFisheye: fisheye clip in, Stab Yaw curve out. No tracker and no measurements.
// (Eric 2026-10-12: "this has to be automated, I can't be responsible for this" — FOV, image size and start point
// were typed in by hand and went wrong without warning.)
//
// With the lens pointing straight up, pan (yaw) is a rotation of the image around the lens centre. A band just above
// the horizon (sky and distant mountains; not the ground, which moves with the speed) is unwrapped to angle × radius,
// and the rotation between two frames is the shift along the angle that fits best. The sum is the pan; the shake =
// pan − road (Gaussian smoothing in both directions, like the tracking view in directionlock.swift) is written as
// Stab Yaw.
//
// What used to be typed in is taken from the clip: the frame rate, the number of frames and — from Darkroom's corner
// mark — the camera and the lens centre. FOV and start point are not part of this computation.
//
// The lens centre (2026-10-19, the handoffs from IgelkottMotion and IgelkottDarkroom: only Darkroom finds the image
// circle):
//  - a trusted corner mark (QR in the corners, IGK1|1|<camera>|…, read with IgelkottLensMark): the camera's model as is;
//  - otherwise the camera from --camera (default PYXIS 12K) and the centre from FisheyetoEqui's calibration for the clip,
//    or the model's own (FisheyeLens.forClip). No circle detector of its own — it measured the background in the
//    corners, where the mark now sits.
//
// Tested against the Offroad plate 2026-10-12 (1124 frames): against the cloud track through the lens model,
// correlation 0.9995, largest difference 0.035°; against the tracking view without its spikes 0.998. No spikes, where
// the tracker had nine.
//
//   autoyaw <clip.mov> [--camera pyxis12K|sonyVenice2] [--out <folder>] [--smooth 0.5] [--strength 1] [--invert] [--whole]
//   autoyaw --selftest          (made-up clip with a known pan; 0 when it matches)
// Build: tools/autoyaw/Package.swift.
import Foundation
import AVFoundation
import Accelerate
import IgelkottFisheyeLens
import IgelkottLensMark

func fail(_ s: String) -> Never { FileHandle.standardError.write((s + "\n").data(using: .utf8)!); exit(1) }

// The lens (FisheyeLens.pyxis12K), only for where the horizon lies in the image circle: radius / circle radius at an
// elevation
let K = (2068.8673345215607, -31.032060077989637, 0.1394366394877631, -0.00029359255648059773)
func lensRadius(_ th: Double) -> Double { let t2 = th * th; return th * (K.0 + t2 * (K.1 + t2 * (K.2 + t2 * K.3))) }
func circleFraction(elevation: Double) -> Double { lensRadius((90 - elevation) * .pi / 180) / lensRadius(125 * .pi / 180) }

/// The lens centre and the image circle's radius (125° from zenith) in a grey image S pixels wide.
struct Circle { var cx: Double; var cy: Double; var r: Double }

/// The circle from a camera's model (the centre may be moved by FisheyetoEqui's calibration), in an image S pixels wide.
func lensCircleOf(_ lens: FisheyeLens, size S: Int) -> Circle {
    let k = Double(S) / lens.reference
    return Circle(cx: lens.center.x * k, cy: lens.center.y * k, r: lens.radius(125 * .pi / 180) * k)
}

/// The rotation between frames in a band above the horizon.
struct PanEstimator {
    let S: Int
    let A = 3600, NR = 40, maxShift = 40                             // 0.1° per step; at most ±4° between two frames
    var sx: [Float], sy: [Float]
    var prev: [Float]? = nil

    init(size: Int, circle: Circle) {
        S = size
        sx = [Float](repeating: 0, count: A * NR); sy = sx
        for j in 0..<NR {
            // 3° … 28° above the horizon
            let rad = circle.r * circleFraction(elevation: 3 + 25 * Double(j) / Double(NR - 1))
            for a in 0..<A {
                let p = Double(a) * 2 * .pi / Double(A)
                sx[j * A + a] = Float(circle.cx + rad * sin(p)); sy[j * A + a] = Float(circle.cy + rad * cos(p))   // angle = sideways, 0 = forward (bottom edge of the image)
            }
        }
    }

    /// The band unwrapped from a grey image, each radius without its slow trend (6° moving average)
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

    /// Adds a frame; returns the rotation since the previous one (degrees, + = content moved right in the car's frame)
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
                    // prev[a] · cur[a + s] over the whole turn, in two straight pieces
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

/// Gaussian smoothing in both directions, edge repeated (same as directionlock.swift and the stabilizer page).
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

// MARK: - The test: a made-up clip with a known pan

func selftest() -> Never {
    let S = 768, n = 120
    var rng = SystemRandomNumberGenerator()
    // Structure that depends only on direction: sums of waves along the angle, different per radius
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
            let phi = atan2(dx, dy) - yaw * .pi / 180, q = r / circle.r                 // the content has moved +yaw along the angle
            var v = 128.0
            for w in waves { v += w.amp * sin(w.h * phi + w.ph + w.rr * q) }
            g[y * S + x] = UInt8(max(40, min(250, v)))
        } }
        return g
    }
    let first = frame(truth[0])
    let found = Circle(cx: circle.cx, cy: circle.cy, r: circle.r)
    // The Venice model in a 4096 image: the centre where FisheyeLens.sonyVenice2 has it
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

// MARK: - The clip

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

// The camera and the lens centre: a trusted corner mark first, otherwise --camera and FisheyetoEqui's calibration
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
