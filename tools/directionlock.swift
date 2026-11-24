// Direction Lock for IgelkottFisheye: a tracked curve from Live FX (CSV from the Curve Editor) → Eric's formula →
// curves for Stab Yaw and Stab Pitch (CSV that the Curve Editor imports on the node).
//
// The formula (Eric 2025, read from "Tracked mountain Yaw.csv" → "… Yaw_DL.csv"):
//     ut[0] = t[0]
//     ut[n] = (t[n] − t[n−1]) + k · ut[n−1]          DL: k = 1/2, DL1.3: k = 1/1.3
// The shake (fast change) is corrected, but the correction decays, so slow turns in the road follow the car.
// A shader has no memory between frames, so this is computed here and not in the node.
//
//   swift tools/directionlock.swift <tracker.csv> … [--k 0.5] [--pixels <FOV> <height>] [--yaw-sign 1] [--pitch-sign -1]
//                                                   [--strength 1] [--out <folder>]
//   swift tools/directionlock.swift "… Offset X.csv" "… Offset Y.csv" --fisheye 4096 [--sensor-height 23.9] [--start x y]
//                                                   [--yaw-only]
//   swift tools/directionlock.swift "… Offset X.csv" "… Offset Y.csv" --view 60 3840 2160 --smooth 0.5 [--start x y]
//   swift tools/directionlock.swift --test tools/fixtures       (the test against the 2025 files; 0 when it matches)
//
// --pixels: the tracker gives pixels in a wall's output image (not degrees). The angle is counted from the first key:
// atan((p − p[0]) / f), f = (height / 2) / tan(FOV / 2), the wall's FOV and height as in the node.
// --fisheye <width>: the tracker has followed a point in the fisheye clip itself (Framing → Stabilize → Track 1 Point,
// Apply To Framing, exported as Framing\Offset X and Offset Y). The point stays in frame the whole clip, also when the
// car turns. Read 2026-10-11 against the Offroad clip (frames from the clip at frame 0, 480 and 900): Offset is MINUS
// the point's movement, in source pixels, with Y up — point = start + (−Offset X, +Offset Y) in image pixels (y down).
// The point goes through the lens model (the same r(θ) as the shader, --sensor-height) to a direction; Stab Yaw is
// the sideways change (azimuth) and Stab Pitch the change in height, both through DL. The start position is not
// needed: when the car turns the point moves in a circle around the lens centre, and the circle is fitted to the
// track (--start x y if the clip does not turn).
// A point behind the car gives reversed Stab Pitch (accounted for), a point straight to the side shows roll, not
// pitch (warned). Several tracks in the same folder are kept apart by file name ("Track bak Offset X/Y" →
// "Track bak Stab Yaw").
// --yaw-only (Eric 2026-10-11: "it's only pan we're trying to stabilize"): only Stab Yaw is written, and an older
// Stab Pitch file for the same track is removed from the output folder so it is not imported by mistake.
//
// --view <FOV> <width> <height> + --smooth <seconds>: THE MAIN PATH (SPL26 2026-10-12, Eric: "it looks like it works").
// Tracked in a tracking view — an IgelkottFisheye node in Mode Wall on the raw clip, aimed straight ahead at the
// horizon — so the tracker works in a rectilinear image. Offset X/Y are pixels in the view (minus the point's
// movement, Y up). The angles: f = (height / 2) / tan(FOV / 2), sideways = atan(x / f), height = atan(y / hypot(x, f)),
// relative to the first key, with the point's start position --start <x> <y> (view pixels, origin top left; without
// the flag: the image centre).
// --smooth splits the angle into road (Gaussian smoothing in both directions, sigma = seconds · --fps frames, rounded
// down) and shake = angle − road; the shake is written as Stab Yaw / Stab Pitch. DL (k = 0.5) decays over 2–3 frames
// and lets the 1–3 Hz rocking through; on a recorded plate, smoothing in both directions is the right filter. Without
// --smooth, DL is used. Same computation as SPL26's prototype vy_stab.py (removed in 0.9; the test compares against
// its curves in fixtures/vy).
//
// --tracking: tracked in the node's Mode Tracking view (fixed scale 0.02° per pixel, TRACK_SCALE in the shader). The
// angle is the offset times the scale; neither FOV, image size nor start point is needed. Used with --smooth, like
// --view.
//
// The signs: Stab Yaw + = fetch further to the right, Stab Pitch + = fetch higher up (the internal project notes,
// stabilisation). A point the tracker sees further down (y grows downward) is corrected with Stab Pitch −, hence
// --pitch-sign −1 as the default for pixels.
import Foundation

struct Channel { var name: String; var keys: [(frame: Double, value: Double)] }

/// Live FX's curve CSV: blocks that start with "#ANIM <name>", then "#COND …" and one key per line. Two columns
/// (frame, value) or six (left tangent, key, right tangent); "," or ";"; Numbers writes minus as "−".
func parse(_ text: String) -> [Channel] {
    var out: [Channel] = []
    for raw in text.components(separatedBy: .newlines) {
        let line = raw.trimmingCharacters(in: .whitespaces).replacingOccurrences(of: "−", with: "-")
        if line.isEmpty { continue }
        if line.hasPrefix("#ANIM") {
            let name = line.dropFirst(5).trimmingCharacters(in: CharacterSet(charactersIn: " ,;\t"))
            out.append(Channel(name: name, keys: []))
            continue
        }
        if line.hasPrefix("#") { continue }
        let f = line.split(whereSeparator: { $0 == "," || $0 == ";" }).compactMap { Double($0.trimmingCharacters(in: .whitespaces)) }
        guard f.count >= 2 else { continue }
        if out.isEmpty { out.append(Channel(name: "", keys: [])) }
        out[out.count - 1].keys.append(f.count >= 4 ? (f[2], f[3]) : (f[0], f[1]))
    }
    return out
}

func directionLock(_ t: [Double], k: Double) -> [Double] {
    var out: [Double] = []
    for n in t.indices { out.append(n == 0 ? t[0] : (t[n] - t[n - 1]) + k * out[n - 1]) }
    return out
}

/// Six columns, as Live FX itself exports a Matchbox parameter (imported on Stab Pitch 2026-10-11).
func write(_ name: String, _ keys: [(frame: Double, value: Double)]) -> String {
    var s = "#ANIM Stab\\\(name)\n#COND CC\n"
    for k in keys {
        let p = String(format: "%.6f,%.6f", k.frame, k.value)
        s += "\(p),\(p),\(p)\n"
    }
    return s
}

func isPitch(_ name: String) -> Bool {
    let n = name.lowercased()
    return n.contains("pitch") || n.hasSuffix("y") || n.contains("tilt")
}

// The lens, as in matchbox/IgelkottFisheye2D.glsl (FisheyeLens.pyxis12K): r(θ) in pixels at 8040
let K = (2068.8673345215607, -31.032060077989637, 0.1394366394877631, -0.00029359255648059773)
func lensRadius(_ th: Double) -> Double { let t2 = th * th; return th * (K.0 + t2 * (K.1 + t2 * (K.2 + t2 * K.3))) }
func lensAngle(_ r: Double) -> Double {
    var th = r / K.0
    for _ in 0..<30 {
        let t2 = th * th
        th -= (lensRadius(th) - r) / (K.0 + t2 * (3 * K.1 + t2 * (5 * K.2 + t2 * 7 * K.3)))
    }
    return th
}

/// The circle that best fits the points (least squares, algebraic): centre and radius.
func fitCircle(_ pts: [(x: Double, y: Double)]) -> (cx: Double, cy: Double, r: Double)? {
    var m = [[Double]](repeating: [Double](repeating: 0, count: 4), count: 3)
    for p in pts {
        let row = [2 * p.x, 2 * p.y, 1, p.x * p.x + p.y * p.y]
        for i in 0..<3 { for j in 0..<4 { m[i][j] += row[i] * row[j] } }
    }
    for i in 0..<3 {
        let piv = (i..<3).max { abs(m[$0][i]) < abs(m[$1][i]) }!
        m.swapAt(i, piv)
        if abs(m[i][i]) < 1e-12 { return nil }
        for r in 0..<3 where r != i { let f = m[r][i] / m[i][i]; for j in 0..<4 { m[r][j] -= f * m[i][j] } }
    }
    var cx = m[0][3] / m[0][0], cy = m[1][3] / m[1][1]
    let c = m[2][3] / m[2][2], r2 = c + cx * cx + cy * cy
    guard r2 > 0 else { return nil }
    var r = r2.squareRoot()
    // The algebraic fit gives too small a radius on a short noisy arc; refine on the distances (Gauss–Newton)
    for _ in 0..<50 {
        var a = [[Double]](repeating: [Double](repeating: 0, count: 4), count: 3)
        for p in pts {
            let dx = p.x - cx, dy = p.y - cy, d = max(hypot(dx, dy), 1e-9)
            let row = [-dx / d, -dy / d, -1, -(d - r)]                // d(resid)/d(cx, cy, r) and −resid
            for i in 0..<3 { for j in 0..<4 { a[i][j] += row[i] * row[j] } }
        }
        var singular = false
        for i in 0..<3 {
            let piv = (i..<3).max { abs(a[$0][i]) < abs(a[$1][i]) }!
            a.swapAt(i, piv)
            if abs(a[i][i]) < 1e-12 { singular = true; break }
            for q in 0..<3 where q != i { let f = a[q][i] / a[i][i]; for j in 0..<4 { a[q][j] -= f * a[i][j] } }
        }
        if singular { break }
        let step = (a[0][3] / a[0][0], a[1][3] / a[1][1], a[2][3] / a[2][2])
        cx += step.0; cy += step.1; r += step.2
        if abs(step.0) + abs(step.1) + abs(step.2) < 1e-9 { break }
    }
    return r > 0 ? (cx, cy, r) : nil
}

struct FisheyeTrack { var yaw: [Double]; var pitch: [Double]; var report: String }

/// Offset X/Y from Framing (source pixels) → the point's angles relative to the first key: sideways (azimuth, + = right)
/// and height. `center` = the lens centre in source pixels; needed only with `start`.
func fisheyeTrack(ox: [Double], oy: [Double], width: Double, sensorHeight: Double, start: (x: Double, y: Double)?,
                  center: (x: Double, y: Double)) -> FisheyeTrack? {
    // The point's movement in image pixels (y down), from the start. The first key is not always 0 (Track bak: −17.5)
    let move = zip(ox, oy).map { (x: -($0 - ox[0]), y: $1 - oy[0]) }
    var v0: (x: Double, y: Double), note: String
    if let s = start {
        v0 = (s.x - center.x, s.y - center.y); note = "start given"
    } else {
        guard let c = fitCircle(move) else { return nil }
        let dev = (move.map { pow(hypot($0.x - c.cx, $0.y - c.cy) - c.r, 2) }.reduce(0, +) / Double(move.count)).squareRoot()
        let a = move.map { atan2($0.y - c.cy, $0.x - c.cx) }
        var span = 0.0, run = 0.0, lo = 0.0, hi = 0.0
        for i in 1..<a.count {
            var d = a[i] - a[i - 1]; if d > .pi { d -= 2 * .pi }; if d < -.pi { d += 2 * .pi }
            run += d; lo = min(lo, run); hi = max(hi, run)
        }
        span = (hi - lo) * 180 / .pi
        // Short arc or poor fit: the circle's centre is not determined, so the start position must be given
        guard span > 8, dev < 0.05 * c.r else { return nil }
        v0 = (-c.cx, -c.cy)
        note = String(format: "circle fitted to the track: radius %.1f px, deviation %.1f px, arc %.1f deg; start %.0f, %.0f px from the lens centre",
                      c.r, dev, span, v0.x, v0.y)
    }
    let scale = 23.32 / sensorHeight * width / 8040                   // source pixels per model pixel
    var az: [Double] = [], el: [Double] = []
    for m in move {
        let x = v0.x + m.x, y = v0.y + m.y
        az.append(atan2(x, y) * 180 / .pi)                            // image x = right, y down = forward
        el.append(90 - lensAngle(hypot(x, y) / scale) * 180 / .pi)
    }
    var yaw = [0.0], pitch = [0.0], unwrapped = 0.0
    for i in 1..<az.count {
        var d = az[i] - az[i - 1]; if d > 180 { d -= 360 }; if d < -180 { d += 360 }
        unwrapped += d
        yaw.append(unwrapped)
        // Stab Pitch + raises what is in front and lowers what is behind: a point behind the car counts reversed
        pitch.append(pitch[i - 1] + (el[i] - el[i - 1]) * (cos(az[i] * .pi / 180) >= 0 ? 1 : -1))
    }
    let side = az.filter { abs(cos($0 * .pi / 180)) < 0.5 }.count
    note += String(format: "; point at azimuth %.1f … %.1f deg, elevation %.1f … %.1f deg", az.min()!, az.max()!, el.min()!, el.max()!)
    if side > 0 { note += "; WARNING: \(side) keys with the point more than 60 deg to the side — its height there shows roll, not pitch" }
    return FisheyeTrack(yaw: yaw, pitch: pitch, report: note)
}

/// Offset X/Y from Framing in a tracking view (Mode Wall) → the point's angles relative to the first key, as the
/// prototype. `start` = the point's position in view pixels relative to the image centre, x to the right, y up.
func viewTrack(ox: [Double], oy: [Double], fov: Double, height: Double, start: (x: Double, y: Double)) -> FisheyeTrack {
    let f = (height / 2) / tan(fov * .pi / 360)
    var yaw: [Double] = [], pitch: [Double] = []
    for (a, b) in zip(ox, oy) {
        let x = start.x - (a - ox[0]), y = start.y - (b - oy[0])        // Offset = minus the movement, Y up; first key not always 0
        yaw.append(atan2(x, f) * 180 / .pi)
        pitch.append(atan2(y, hypot(x, f)) * 180 / .pi)
    }
    let y0 = yaw[0], p0 = pitch[0]
    let note = String(format: "tracking view, f = %.1f px, point starts %.0f px right of and %.0f px above the centre; whole pan %.2f … %.2f deg",
                      f, start.x, start.y, yaw.map { $0 - y0 }.min()!, yaw.map { $0 - y0 }.max()!)
    return FisheyeTrack(yaw: yaw.map { $0 - y0 }, pitch: pitch.map { $0 - p0 }, report: note)
}

/// Gaussian smoothing in both directions, edge repeated, as the prototype.
func gauss(_ v: [Double], sigma: Double) -> [Double] {
    let r = Int(3 * sigma), n = v.count
    let w = (-r...r).map { exp(-0.5 * pow(Double($0) / sigma, 2)) }
    return (0..<n).map { i in
        var acc = 0.0, sum = 0.0
        for (j, k) in w.enumerated() { acc += v[min(max(i + j - r, 0), n - 1)] * k; sum += k }
        return acc / sum
    }
}

func fail(_ s: String) -> Never { FileHandle.standardError.write((s + "\n").data(using: .utf8)!); exit(1) }

var args = Array(CommandLine.arguments.dropFirst())
var k = 0.5, strength = 1.0, yawSign = 1.0, pitchSign: Double? = nil
var pixels: (fov: Double, height: Double)? = nil
var outDir: String? = nil, testDir: String? = nil
var fisheyeWidth: Double? = nil, sensorHeight = 23.32
var start: (x: Double, y: Double)? = nil, lensOffset = (x: 0.0, y: 0.0)
var yawOnly = false
var view: (fov: Double, width: Double, height: Double)? = nil
var tracking = false
let TRACK_SCALE = 0.02                                               // degrees per pixel, as the shader
var smooth: Double? = nil, fps = 25.0
var files: [String] = []
func number(_ flag: String) -> Double {
    guard !args.isEmpty, let v = Double(args.removeFirst().replacingOccurrences(of: ",", with: ".")) else { fail("\(flag) needs a number") }
    return v
}
while !args.isEmpty {
    let a = args.removeFirst()
    switch a {
    case "--k": k = number(a)
    case "--strength": strength = number(a)
    case "--yaw-sign": yawSign = number(a)
    case "--pitch-sign": pitchSign = number(a)
    case "--pixels": let f = number(a); pixels = (f, number(a))
    case "--yaw-only": yawOnly = true
    case "--view": let f = number(a), w = number(a); view = (f, w, number(a))
    case "--tracking": tracking = true
    case "--smooth": smooth = number(a)
    case "--fps": fps = number(a)
    case "--fisheye": fisheyeWidth = number(a)
    case "--sensor-height": sensorHeight = number(a)
    case "--start": let x = number(a); start = (x, number(a))
    case "--lens-offset": let x = number(a); lensOffset = (x, number(a))        // as the node's Lens Offset, pixels at 8040
    case "--out": guard !args.isEmpty else { fail("--out needs a folder") }; outDir = args.removeFirst()
    case "--test": guard !args.isEmpty else { fail("--test needs a folder") }; testDir = args.removeFirst()
    default: files.append(a)
    }
}

if let dir = testDir {
    // The test: the 2025 files. k = 1/2 must give _DL, k = 1/1.3 must give _DL1.3, to six decimals.
    var good = true
    for (axis, suffix, kk) in [("Yaw", "_DL", 0.5), ("Yaw", "_DL1.3", 1 / 1.3), ("Pitch", "_DL", 0.5), ("Pitch", "_DL1.3", 1 / 1.3)] {
        func load(_ n: String) -> [(frame: Double, value: Double)] {
            guard let s = try? String(contentsOfFile: "\(dir)/\(n)", encoding: .utf8), let c = parse(s).first else { fail("cannot read \(dir)/\(n)") }
            return c.keys
        }
        let t = load("Tracked mountain \(axis).csv"), want = load("Tracked mountain \(axis)\(suffix).csv")
        let got = directionLock(t.map(\.value), k: kk)
        var worst = 0.0
        for (i, w) in want.enumerated() where i < got.count { worst = max(worst, abs(got[i] - w.value)) }
        let ok = want.count > 1000 && got.count >= want.count && worst < 2.5e-6
        good = good && ok
        print(String(format: "  %@ Tracked mountain %@ → %@ (k = %.4f): largest difference %.7f over %d keys",
                     ok ? "PASS" : "FAIL", axis, suffix, kk, worst, want.count))
    }
    // Fisheye mode: a point 20° above the horizon straight ahead, the car turns 40° and nods; the track is made as Live FX
    // writes it (Offset = −movement, Y up, source pixels) and must give back the turn and the nod.
    do {
        let w = 4096.0, sh = 23.9, scale = 23.32 / sh * w / 8040
        var ox: [Double] = [], oy: [Double] = [], wantYaw: [Double] = [], wantPitch: [Double] = []
        var first = (x: 0.0, y: 0.0)
        for n in 0..<600 {
            let yaw = 40 * sin(Double(n) / 190), nod = 0.6 * sin(Double(n) / 7) + 0.3 * sin(Double(n) / 2.3)
            let az = (5 + yaw) * .pi / 180, r = lensRadius((90 - 20 - nod) * .pi / 180) * scale
            let p = (x: r * sin(az), y: r * cos(az))
            if n == 0 { first = p }
            ox.append(-(p.x - first.x)); oy.append(p.y - first.y)
            wantYaw.append(yaw - 40 * sin(0)); wantPitch.append(nod - (0.6 * sin(0) + 0.3 * sin(0)))
        }
        var worst = 1e9
        if let t = fisheyeTrack(ox: ox, oy: oy, width: w, sensorHeight: sh, start: nil, center: (w / 2, w / 2)) {
            // What is used is DL of the angles (the shake); the circle's centre is only roughly set by a short arc
            let gy = directionLock(t.yaw, k: 0.5), wy = directionLock(wantYaw, k: 0.5)
            let gp = directionLock(t.pitch, k: 0.5), wp = directionLock(wantPitch, k: 0.5)
            worst = 0
            for i in 0..<600 { worst = max(worst, abs(gy[i] - wy[i]), abs(gp[i] - wp[i])) }
            var raw = 0.0
            for i in 0..<600 { raw = max(raw, abs(t.yaw[i] - wantYaw[i]), abs(t.pitch[i] - wantPitch[i])) }
            print(String(format: "    (angles before DL: largest error %.3f deg; %@)", raw, t.report))
        }
        let ok = worst < 0.03
        good = good && ok
        print(String(format: "  %@ Fisheye track (synthetic turn and nod, start from the fitted circle): largest error after DL %.4f deg", ok ? "PASS" : "FAIL", worst))
    }
    // The tracking view: the Offroad track (Track vy) must give SPL26's curves from the prototype (FOV 60, 3840 × 2160,
    // start 754 px left of and 287 px above the centre, sigma 12 frames)
    do {
        func load(_ n: String) -> [Double] {
            guard let s = try? String(contentsOfFile: "\(dir)/vy/\(n)", encoding: .utf8), let c = parse(s).first else { fail("cannot read \(dir)/vy/\(n)") }
            return c.keys.map(\.value)
        }
        let t = viewTrack(ox: load("Track vy Offset X.csv"), oy: load("Track vy Offset Y.csv"), fov: 60, height: 2160, start: (-754, 287))
        for (name, angles, file) in [("Stab Yaw", t.yaw, "Vy Stab Yaw (skak).csv"), ("Stab Pitch", t.pitch, "Vy Stab Pitch (skak).csv")] {
            let want = load(file), road = gauss(angles, sigma: (0.5 * 25).rounded(.down))
            let got = zip(angles, road).map { $0 - $1 }
            var worst = 0.0
            for (i, w) in want.enumerated() where i < got.count { worst = max(worst, abs(got[i] - w)) }
            let ok = want.count == got.count && want.count > 1000 && worst < 2e-6
            good = good && ok
            print(String(format: "  %@ Tracking view → %@ (smooth 0.5 s): largest difference %.7f deg over %d keys, %.2f … %.2f deg",
                         ok ? "PASS" : "FAIL", name, worst, want.count, got.min() ?? 0, got.max() ?? 0))
        }
    }
    print(good ? "Direction Lock matches the 2025 files." : "Direction Lock differs from the 2025 files.")
    exit(good ? 0 : 1)
}

/// The shake from an angle curve: angle − road with --smooth, otherwise Eric's DL.
func shake(_ t: [Double]) -> [Double] {
    guard let s = smooth else { return directionLock(t, k: k) }
    let road = gauss(t, sigma: max(1, (s * fps).rounded(.down)))
    return zip(t, road).map { $0 - $1 }
}

func save(_ target: String, _ base: String, _ dir: String, _ frames: [Double], _ values: [Double], from: String) {
    let out = "\(dir)/\(base) \(target).csv"
    do { try write(target, zip(frames, values).map { ($0, $1) }).write(toFile: out, atomically: true, encoding: .utf8) }
    catch { fail("cannot write \(out)") }
    print(String(format: "%@: %d keys, %.3f … %.3f deg (%@)", (out as NSString).lastPathComponent, values.count,
                 values.min() ?? 0, values.max() ?? 0, from))
}

if fisheyeWidth != nil || view != nil || tracking {
    let width = fisheyeWidth ?? 0
    // The curves are paired on the file name without " Offset X" / " Offset Y": one track per name
    var tracks: [String: (x: Channel?, y: Channel?, url: URL)] = [:], order: [String] = []
    for path in files {
        guard let text = try? String(contentsOfFile: path, encoding: .utf8) else { fail("cannot read \(path)") }
        let url = URL(fileURLWithPath: path)
        var base = url.deletingPathExtension().lastPathComponent
        for tail in [" Offset X", " Offset Y", " X", " Y"] where base.hasSuffix(tail) { base = String(base.dropLast(tail.count)); break }
        for c in parse(text) where !c.keys.isEmpty {
            let n = c.name.lowercased()
            guard n.hasSuffix("x") || n.hasSuffix("y") else { continue }
            if tracks[base] == nil { tracks[base] = (nil, nil, url); order.append(base) }
            if n.hasSuffix("x") { tracks[base]!.x = c } else { tracks[base]!.y = c }
        }
    }
    let dir = outDir ?? (files.first.map { URL(fileURLWithPath: $0).deletingLastPathComponent().path } ?? ".")
    try? FileManager.default.createDirectory(atPath: dir, withIntermediateDirectories: true)
    let center = (x: (4019.9389914282037 + lensOffset.x) * width / 8040, y: (4019.9389463189077 + lensOffset.y) * width / 8040)
    var done = 0, problems: [String] = []
    for base in order {
        guard let cx = tracks[base]!.x, let cy = tracks[base]!.y else { problems.append("\(base): needs both Offset X and Offset Y"); continue }
        let n = min(cx.keys.count, cy.keys.count)
        let ox = cx.keys.prefix(n).map(\.value), oy = cy.keys.prefix(n).map(\.value)
        var track: FisheyeTrack? = nil
        if tracking {
            // Offset = minus the movement (Y up), times the fixed scale
            track = FisheyeTrack(yaw: ox.map { -($0 - ox[0]) * TRACK_SCALE }, pitch: oy.map { -($0 - oy[0]) * TRACK_SCALE },
                                 report: String(format: "tracking view, %.2f deg per pixel", TRACK_SCALE))
        } else if let v = view {
            // --start in view pixels (origin top left) → relative to the centre, y up
            track = viewTrack(ox: ox, oy: oy, fov: v.fov, height: v.height,
                              start: start.map { ($0.x - v.width / 2, v.height / 2 - $0.y) } ?? (0, 0))
        } else {
            track = fisheyeTrack(ox: ox, oy: oy, width: width, sensorHeight: sensorHeight, start: start, center: center)
        }
        guard let t = track else {
            problems.append("\(base): the track does not turn enough to find the lens centre from it — give the point's start position with --start <x> <y> (source pixels, origin top left)")
            continue
        }
        print("\(base): \(t.report)")
        let frames = cx.keys.prefix(n).map(\.frame)
        save("Stab Yaw", base, dir, frames, shake(t.yaw).map { $0 * yawSign * strength }, from: view != nil || tracking ? "tracking view, sideways" : "fisheye track, sideways")
        if yawOnly {
            try? FileManager.default.removeItem(atPath: "\(dir)/\(base) Stab Pitch.csv")
        } else {
            save("Stab Pitch", base, dir, frames, shake(t.pitch).map { $0 * (pitchSign ?? 1) * strength }, from: view != nil || tracking ? "tracking view, height" : "fisheye track, height")
        }
        done += 1
    }
    if done == 0 && problems.isEmpty { fail("needs the tracker's Offset X and Offset Y curves") }
    if !problems.isEmpty { fail(problems.joined(separator: "\n")) }
    exit(0)
}

guard !files.isEmpty else { fail("usage: directionlock <tracker.csv> … [--k 0.5] [--pixels <FOV> <height>] [--yaw-sign 1] [--pitch-sign -1] [--strength 1] [--out <folder>]") }
for path in files {
    guard let text = try? String(contentsOfFile: path, encoding: .utf8) else { fail("cannot read \(path)") }
    let channels = parse(text).filter { !$0.keys.isEmpty }
    if channels.isEmpty { fail("no keys in \(path)") }
    let url = URL(fileURLWithPath: path)
    let dir = outDir ?? url.deletingLastPathComponent().path
    try? FileManager.default.createDirectory(atPath: dir, withIntermediateDirectories: true)
    for c in channels {
        let pitch = isPitch(c.name)
        var t = c.keys.map(\.value)
        var sign = pitch ? (pitchSign ?? 1) : yawSign
        if let p = pixels {
            let f = (p.height / 2) / tan(p.fov * .pi / 360), first = t[0]
            t = t.map { atan(($0 - first) / f) * 180 / .pi }
            if pitch { sign = pitchSign ?? -1 }
        }
        let u = directionLock(t, k: k).map { $0 * sign * strength }
        let target = pitch ? "Stab Pitch" : "Stab Yaw"
        if pitch && yawOnly { continue }
        let out = "\(dir)/\(url.deletingPathExtension().lastPathComponent) \(target).csv"
        do { try write(target, zip(c.keys, u).map { ($0.0.frame, $0.1) }).write(toFile: out, atomically: true, encoding: .utf8) }
        catch { fail("cannot write \(out)") }
        print(String(format: "%@ → %@: %d keys, %.3f … %.3f deg (from \"%@\")", url.lastPathComponent,
                     (out as NSString).lastPathComponent, u.count, u.min() ?? 0, u.max() ?? 0, c.name))
    }
}
