// The test for stabilizer/index.html: the script block "core" runs in Node.
// The page computes from a track tracked in the node's Mode Tracking view (fixed scale in degrees per pixel), so the
// test makes a track with a known pan and checks that the page gives it back, and that the scale is the same as the
// Swift tool's TRACK_SCALE (the node has had no Tracking view since 0.14).
// The road/shake split is tested against the same reference as tools/directionlock.swift (tools/fixtures/vy).
//
//   node tools/test-stabilizer.mjs          (from the project root; 0 when it matches)
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";

const html = readFileSync("stabilizer/index.html", "utf8");
const core = html.match(/<script id="core">([\s\S]*?)<\/script>/)[1];
const module = { exports: {} };
new Function("module", "require", core)(module, createRequire(import.meta.url));
const { DEG_PER_PIXEL, parseCurves, readTrack, anglesOf, trackingAngles, split, spikes, fixSlips, curveCSV } = module.exports;

let good = true;
const check = (ok, text) => { good = good && ok; console.log(`  ${ok ? "PASS" : "FAIL"} ${text}`); };

// The scale: the page and the Swift tool must have the same number
const swift = +readFileSync("tools/directionlock.swift", "utf8").match(/let TRACK_SCALE = ([0-9.]+)/)[1];
check(DEG_PER_PIXEL === swift, `the page and the Swift tool agree on ${DEG_PER_PIXEL} degrees per pixel`);

// A track with a known pan and nod, written as Live FX exports it: Offset = minus the movement, Y up, and not 0 on
// the first key. The view's size and the point's position appear nowhere — they must not be needed.
const n = 600, pan = [], nod = [];
for (let i = 0; i < n; i++) { pan.push(18 * Math.sin(i / 170) + 1.2 * Math.sin(i / 4) - 0.4 * Math.sin(i / 1.7)); nod.push(0.3 * Math.sin(i / 5)); }
const curve = (name, v) => `#ANIM Matchbox.Clip\\Framing\\${name}\n#COND CC\n` + v.map((x, i) => `${i}.000000,${x.toFixed(6)}`).join("\n") + "\n";
const ox = pan.map(p => -434.2 - (p - pan[0]) / DEG_PER_PIXEL), oy = nod.map(p => 29.8 - (p - nod[0]) / DEG_PER_PIXEL);
const t = readTrack([{ name: "export.csv", text: curve("Offset X", ox) + curve("Offset Y", oy) }]);
const a = anglesOf(t, DEG_PER_PIXEL);
const worst = (got, want) => Math.max(...got.map((v, i) => Math.abs(v - (want[i] - want[0]))));
check(worst(a.yaw, pan) < 1e-6, `a known pan comes back: largest error ${worst(a.yaw, pan).toExponential(1)} deg (one file, offsets not starting at 0)`);
check(worst(a.pitch, nod) < 1e-6, `a known nod comes back: largest error ${worst(a.pitch, nod).toExponential(1)} deg`);
const two = readTrack([{ name: "a Offset X.csv", text: curve("Offset X", ox) }, { name: "a Offset Y.csv", text: curve("Offset Y", oy) }]);
check(two.kind === "pixels" && two.a.length === n && two.b[7] === t.b[7], "two files give the same as one");

// Any 360 (Eric 2026-10-13: "so generic it can take keys from any 360 at all"):
// degrees from Pan 360 are used as they are, and pixels from an equirect image are computed with 360° / image width.
const deg = (name, v) => `#ANIM Clip\\Pan 360\\${name}\n#COND CC\n` + v.map((x, i) => `${i}.000000,${x.toFixed(6)}`).join("\n") + "\n";
const p360 = readTrack([{ name: "pan.csv", text: deg("Yaw", pan.map(v => v + 7)) + deg("Pitch", nod) + deg("Roll", nod.map(v => 2 * v)) }]);
const a360 = anglesOf(p360, DEG_PER_PIXEL);
check(p360.kind === "degrees" && worst(a360.yaw, pan) < 1e-5 && worst(a360.pitch, nod) < 1e-5 && Math.abs(a360.roll[40] - 2 * (nod[40] - nod[0])) < 1e-5,
      "Pan 360 Yaw / Pitch / Roll in degrees are used as they are");
const eqW = 7680, eq = readTrack([{ name: "eq.csv", text: curve("Offset X", pan.map(p => -(p - pan[0]) * eqW / 360)) }]);
check(eq.kind === "pixels" && eq.b === null && worst(anglesOf(eq, 360 / eqW).yaw, pan) < 1e-4, "pixels from a 7680 wide equirect picture, Offset X alone");

// Road/shake: the same Gaussian as the Swift tool, against its reference (angles from tracking view FOV 60, as the
// reference was made with)
const dir = "tools/fixtures/vy/";
const values = name => parseCurves(readFileSync(dir + name, "utf8"))[0].keys.map(k => k[1]);
const vx = values("Track vy Offset X.csv"), f = 1080 / Math.tan(30 * Math.PI / 180);
const wall = vx.map(o => Math.atan2(-754 - o, f) * 180 / Math.PI).map((v, _, all) => v - all[0]);
const shake = split(wall, 12).shake, want = values("Vy Stab Yaw (skak).csv");
const d = Math.max(...want.map((w, i) => Math.abs(w - shake[i])));
check(d < 2e-6, `road and shake: largest difference from the reference ${d.toFixed(7)} deg over ${want.length} keys`);
const back = parseCurves(curveCSV("Stab Yaw", t.frames, a.yaw))[0];
check(back.name === "Stab\\Stab Yaw" && back.keys.every((k, i) => Math.abs(k[1] - a.yaw[i]) < 1e-6), "the saved file reads back");

// Spikes: the tracker slipping onto something else in the image (Eric 2026-10-12: "the tracker got stuck on something
// else in the image and then follows another part of the mountain"). A clean track gets three faults — a short spike,
// a 20-frame plateau and a jump that never comes back (another part of the mountain) — and must be repaired back to
// the clean shake.
const calm = []; for (let i = 0; i < n; i++) calm.push(18 * Math.sin(i / 170) + 0.8 * Math.sin(i / 9) - 0.3 * Math.sin(i / 4.5));
const clean = split(calm, 12).shake;
const broken = [...calm];
broken[150] += 1.8; broken[151] += 1.1;
for (let i = 300; i < 320; i++) broken[i] -= 2.5;
for (let i = 450; i < n; i++) broken[i] += 3;
const fix = fixSlips(broken, true, []);
const repaired = split(fix.pan, 12).shake;
const diff = v => Math.max(...v.map((x, i) => Math.abs(x - clean[i])));
check(fix.fixed.length >= 3 && diff(repaired) < 0.3, `slips are found and fixed (${JSON.stringify(fix.fixed)}); largest difference from the clean shake ${diff(repaired).toFixed(2)} deg, was ${diff(split(broken, 12).shake).toFixed(2)}`);
check(spikes(repaired).length === 0, "no spike keys left after the fix");
const untouched = fixSlips(calm, true, []);
check(untouched.fixed.length === 0 && untouched.pan.every((v, i) => v === calm[i]), "a clean track is left alone");
const hand = fixSlips(broken, false, [[149, 152]]);
check(hand.fixed.length === 1 && Math.abs(hand.pan[150] - calm[150]) < 0.3 && hand.pan[300] === broken[300], "a stretch marked by hand is bridged, the rest is not touched");

// Pitch: the stretches fixed in the pan are bridged in the pitch too (the tracker slips both ways at once)
const nodBroken = nod.map((v, i) => v + (i >= 300 && i < 320 ? 0.9 : 0));
const nodFixed = fixSlips(trackingAngles(t.a, nodBroken.map(p => -(p - nodBroken[0]) / DEG_PER_PIXEL)).pitch, false, [[300, 319]]);
check(Math.max(...nodFixed.pan.slice(295, 325).map((v, i) => Math.abs(v - (nod[295 + i] - nod[0])))) < 0.4, "pitch: a stretch fixed in the pan is bridged in the pitch too");

// The real track from Mode Wall (Track vy, nine spikes): after the fix it must be close to the pan measured in the clip
const truth = parseCurves(readFileSync("tools/fixtures/auto/Offroad 130-175s Stab Yaw.csv", "utf8"))[0].keys.map(k => k[1]);
const real = split(fixSlips(wall, true, []).pan, 12).shake;
const worstReal = v => Math.max(...v.map((x, i) => Math.abs(x - truth[i])));
check(worstReal(real) < 0.5 && spikes(real).length === 0, `the real Offroad track: largest difference from the pan measured in the clip ${worstReal(real).toFixed(2)} deg after the fix, was ${worstReal(shake).toFixed(2)}`);

// The error messages say what the user should do
const message = files => { try { readTrack(files); return ""; } catch (e) { return e.message; } };
check(/Offset X too/.test(message([{ name: "y.csv", text: curve("Offset Y", oy) }])), "only Offset Y → asks for Offset X");
check(/no Yaw curve/.test(message([{ name: "p.csv", text: deg("Pitch", nod) }])), "Pan 360 Pitch alone → asks for Yaw");
check(/not tracker keys/.test(message([{ name: "g.csv", text: "#ANIM Clip\\Primary\\Gain\n#COND CC\n0,1\n1,1\n" }])), "another kind of curve → says so");
check(/no keys/.test(message([{ name: "empty.csv", text: "hello" }])), "empty file → says so");

// The page has no fields to type numbers in (the image width for an equirect is picked from a list)
check(!/type="number"/.test(html), "the page has no number fields");

console.log(good ? "The stabilizer page gives back a known pan." : "The stabilizer page is wrong.");
process.exit(good ? 0 : 1);
