// IgelkottFisheye core: the lens, the nadir turn, the pixel tag and the warning sign. One source for Live FX (Matchbox,
// GLSL 1.20) and PIXERA (GLSL 4.50): tools/build_shaders.py puts the camera numbers in front of this text and one of the
// wrappers (matchbox.glsl, pixera.glsl) after it. Keep to what both read: no integer bit operations, no arrays, no
// `texture2D`. In shader/core.glsl the source is read with a placeholder the script swaps for each host (uv in fractions
// of the picture, top row first); functions that read it take the sampler as a first parameter in PIXERA only.
//
// Directions: y up, z straight ahead (yaw 0 = the middle of the equirect FisheyetoEqui makes), x right.
// The lens points straight up: theta from the zenith, r(theta) = k1*t + k2*t^3 + k3*t^5 + k4*t^7,
// point = centre + (d.x, d.z) * r(theta) / sin(theta) (FisheyeLens.point in _shared/IgelkottFisheyeLens).
// Nadir (lens pointing down, flying plate): the direction is read as (x, -y, -z), 180 degrees about X, as Stage 1 and Motion.

const float IGK_PI = 3.14159265358979;
// Degrees to radians without the built-in radians(): PIXERA's own effects define a radians() of their own
// (Ref-Eric/Equirectangular.glsl.txt), which would clash in a stricter compiler.
const float IGK_DEG = 0.017453292519943295;

// Cameras: the pixel tag's codes. 1 PYXIS 12K, 2 Sony Venice 2, 3 Z-Cam E2 S6 (no lens model yet), 0 and 4-7 none.
bool igkHasModel(int cam) {
    return cam == 1 || cam == 2;
}

vec2 igkLensCenter(int cam) {
    return cam == 2 ? IGK_VENICE_CENTER / IGK_VENICE_REF : IGK_PYXIS_CENTER / IGK_PYXIS_REF;
}

vec4 igkLensK(int cam) {
    return cam == 2 ? IGK_VENICE_K / IGK_VENICE_REF : IGK_PYXIS_K / IGK_PYXIS_REF;
}

// The direction's point in the source, fractions of the picture, top row first
vec2 igkLensPoint(vec3 d, int cam, bool nadir) {
    if (nadir) d = vec3(d.x, -d.y, -d.z);
    vec4 k = igkLensK(cam);
    float rho = length(d.xz);
    float th = atan(rho, d.y);
    float t2 = th * th;
    float poly = k.x + t2 * (k.y + t2 * (k.z + t2 * k.w));
    float f = rho > 1e-9 ? poly * th / rho : poly;
    return igkLensCenter(cam) + d.xz * f;
}

bool igkInside(vec2 p) {
    return p.x >= 0.0 && p.x <= 1.0 && p.y >= 0.0 && p.y <= 1.0;
}

// R = Ry(yaw) * Rx(-pitch) * Rz(roll), as IgelkottStage (CameraCost.rotation) and Eq->2D
mat3 igkRotation(float y, float p, float r) {
    y *= IGK_DEG; p *= -IGK_DEG; r *= IGK_DEG;
    mat3 ry = mat3(cos(y), 0.0, -sin(y),   0.0, 1.0, 0.0,   sin(y), 0.0, cos(y));
    mat3 rx = mat3(1.0, 0.0, 0.0,   0.0, cos(p), sin(p),   0.0, -sin(p), cos(p));
    mat3 rz = mat3(cos(r), sin(r), 0.0,   -sin(r), cos(r), 0.0,   0.0, 0.0, 1.0);
    return ry * rx * rz;
}

// A flat wall: c = the point relative to the wall's middle (y up), h = the height c is measured in, fov = vertical angle
vec3 igkWallDirection(vec2 c, float h, float yaw, float pitch, float roll, float fov) {
    float f = 0.5 * h / tan(clamp(fov, 1.0, 179.0) * IGK_DEG * 0.5);
    return igkRotation(yaw, pitch, roll) * normalize(vec3(c.x / f, c.y / f, 1.0));
}

// The whole sphere, 2:1: uv in fractions, y up; u = lon / 2pi + 0.5, the middle is yaw 0 (FisheyetoEqui's equirect)
// Mode Equirect on any canvas (Eric 2026-11-20, "crop to 360 wide"): 360 degrees over the width, the same degrees per
// pixel up and down, centred on the horizon. 2:1 is the whole sphere; wider canvases are cropped top and bottom (32:9:
// 101 degrees); narrower ones reach past the poles, and that part is black (igkEquirectUV gives v outside 0..1).
vec2 igkEquirectUV(vec2 s, float w, float h) {
    return vec2(s.x / w, 0.5 + (s.y - 0.5 * h) * 2.0 / w);
}

vec3 igkEquirectDirection(vec2 uv) {
    float lon = (uv.x - 0.5) * 2.0 * IGK_PI;
    float lat = (uv.y - 0.5) * IGK_PI;
    return vec3(cos(lat) * sin(lon), sin(lat), cos(lat) * cos(lon));
}

// MARK: The pixel tag (PixelTag in _shared/IgelkottFisheyeLens, IgelkottLensMark; the rules live there)
// Two rows of ten cells, 0.011 of the side, along the top edge next to the QR code: x 0.116-0.226, y 0.010-0.032, in all
// four corners mirrored as the QR codes. Cell 0 white, cell 1 black (a cell is 1 above the middle between them), then
// version (2 bits, 1), camera (3), nadir, adjusted, horizon burnt in, 4 free, CRC-6 (0x27, start 0x3F, top bit first).
// The fisheye is square, so fractions of the side are fractions of the picture.

const float IGK_TAG_CELL = 0.011;
const float IGK_TAG_X = 0.116;
const float IGK_TAG_Y = 0.010;
const float IGK_TAG_MIN_CONTRAST = 0.1;

// The middle of cell i in corner k (0 top left, 1 top right, 2 bottom left, 3 bottom right), top row first
vec2 igkTagCell(int k, int i) {
    float fi = float(i);
    float row = floor(fi / 10.0);
    vec2 p = vec2(IGK_TAG_X + (fi - 10.0 * row + 0.5) * IGK_TAG_CELL, IGK_TAG_Y + (row + 0.5) * IGK_TAG_CELL);
    if (k == 1 || k == 3) p.x = 1.0 - p.x;
    if (k >= 2) p.y = 1.0 - p.y;
    return p;
}

float igkLuma(vec3 c) {
    return dot(c, vec3(0.2126, 0.7152, 0.0722));
}

// a XOR b for 0..63
float igkXor6(float a, float b) {
    float r = 0.0;
    float p = 1.0;
    for (int i = 0; i < 6; i++) {
        r += p * abs(mod(floor(a / p), 2.0) - mod(floor(b / p), 2.0));
        p *= 2.0;
    }
    return r;
}

// One bit into the CRC-6 (polynomial 0x27 = 39)
float igkCrcStep(float crc, float bit) {
    float top = crc >= 32.0 ? 1.0 : 0.0;
    crc = mod(crc * 2.0, 64.0);
    return top != bit ? igkXor6(crc, 39.0) : crc;
}

// The tag in corner k: camera * 2 + nadir, or -1 (no contrast, wrong version or wrong CRC)
float igkTagCorner(SRC_PARAM int k) {
    float white = igkLuma(FETCH(igkTagCell(k, 0)).rgb);
    float black = igkLuma(FETCH(igkTagCell(k, 1)).rgb);
    if (white - black < IGK_TAG_MIN_CONTRAST) return -1.0;
    float mid = 0.5 * (white + black);
    float data = 0.0;
    float crc = 63.0;
    float check = 0.0;
    for (int i = 2; i < 20; i++) {
        float bit = igkLuma(FETCH(igkTagCell(k, i)).rgb) > mid ? 1.0 : 0.0;
        if (i < 14) {
            data = data * 2.0 + bit;
            crc = igkCrcStep(crc, bit);
        } else {
            check = check * 2.0 + bit;
        }
    }
    if (check != crc || floor(data / 1024.0) != 1.0) return -1.0;
    return mod(floor(data / 128.0), 8.0) * 2.0 + mod(floor(data / 64.0), 2.0);
}

float igkVotes(float t, float a, float b, float c, float d) {
    return t < 0.0 ? 0.0 : (a == t ? 1.0 : 0.0) + (b == t ? 1.0 : 0.0) + (c == t ? 1.0 : 0.0) + (d == t ? 1.0 : 0.0);
}

// The tag most corners agree on (camera * 2 + nadir), or -1 when no corner reads
float igkTag(SRC_PARAM float unused) {
    float a = igkTagCorner(SRC_ARG 0);
    float b = igkTagCorner(SRC_ARG 1);
    float c = igkTagCorner(SRC_ARG 2);
    float d = igkTagCorner(SRC_ARG 3);
    float best = a;
    float n = igkVotes(a, a, b, c, d);
    float m = igkVotes(b, a, b, c, d);
    if (m > n) { best = b; n = m; }
    m = igkVotes(c, a, b, c, d);
    if (m > n) { best = c; n = m; }
    m = igkVotes(d, a, b, c, d);
    if (m > n) { best = d; n = m; }
    return best;
}

// The plate: vec3(camera, nadir 0/1, warning 0/1). Eric 2026-11-20: Auto is a choice in each list, no Plate control.
// Camera: 0 Auto (the tag's camera), 1 PYXIS 12K, 2 Sony Venice 2, 3 Z-Cam E2 S6. Pointing: 0 Auto, 1 Zenith, 2 Nadir.
// A list on Auto with no valid tag: PYXIS 12K / Zenith and the warning. A camera without a lens model (Z-Cam E2 S6 today,
// chosen or from the tag): black and the warning, never another camera's model.
vec3 igkPlate(float tag, int camera, int pointing) {
    bool hasTag = tag >= 0.0;
    int cam = camera;
    if (camera == 0) cam = hasTag ? int(floor(tag / 2.0 + 0.25)) : 1;
    float nadir = pointing == 2 ? 1.0 : 0.0;
    if (pointing == 0 && hasTag) nadir = mod(tag, 2.0);
    bool missing = !hasTag && (camera == 0 || pointing == 0);
    float warn = (missing || !igkHasModel(cam)) ? 1.0 : 0.0;
    return vec3(float(cam), nadir, warn);
}

// The warning sign: a small yellow triangle with a black "!" in the top left corner of the output, no text.
// q = the point in the output from its top left corner, size = the triangle's side, in the same units.
// 0 = not on the sign, 1 = yellow, 2 = black.
float igkWarning(vec2 q, float size) {
    vec2 p = (q - vec2(0.5 * size)) / size;          // 0..1 over the sign's box, y down
    if (p.x < 0.0 || p.x > 1.0 || p.y < 0.0 || p.y > 0.9) return 0.0;
    if (abs(p.x - 0.5) > 0.5 * p.y / 0.9) return 0.0;
    if (abs(p.x - 0.5) < 0.06 && ((p.y > 0.3 && p.y < 0.62) || (p.y > 0.7 && p.y < 0.8))) return 2.0;
    return 1.0;
}

const vec3 IGK_WARNING_YELLOW = vec3(1.0, 0.78, 0.0);
