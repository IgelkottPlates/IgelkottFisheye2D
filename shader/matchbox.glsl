// Live FX (Matchbox). For movie files Live FX lays the source and the output out top row first (seen on Mac 2026-10-05
// and on Windows 2026-10-28): texture row 0 is the top of the picture and gl_FragCoord.y counts from the top. PNG clips
// are laid out bottom row first (Windows 2026-11-19): there the wall comes out turned 180 degrees.

uniform sampler2D front;
uniform float adsk_result_w, adsk_result_h;

uniform int camera;
uniform int pointing;
uniform float offset_x;
uniform float offset_y;
uniform float offset_xr;
uniform float offset_yr;
uniform int mode;
uniform float yaw;
uniform float pitch;
uniform float roll;
uniform float fov;
uniform bool split;
uniform float split_pos;
uniform float yaw_r;
uniform float pitch_r;
uniform float roll_r;
uniform float fov_r;

void main() {
    float tag = -1.0;                                                   // both chosen by hand: the tag is not used
    if (camera == 0 || pointing == 0) tag = igkTag(0.0);
    vec3 pl = igkPlate(tag, camera, pointing);
    int cam = int(pl.x + 0.5);
    bool nadir = pl.y > 0.5;
    // Offset X/Y move the finished picture, after the projection (Eric 2026-11-20): output pixels, +X right, +Y up; the
    // left wall's with Split on, and Right Offset X/Y the right wall's. The Split edge stays where Split Position puts it.
    float w = adsk_result_w;
    float h = adsk_result_h;
    float splitX = split ? clamp(split_pos, 0.0, 100.0) * 0.01 * w : w;
    mat3 rLeft = igkRotation(yaw, pitch, roll);
    mat3 rRight = igkRotation(yaw_r, pitch_r, roll_r);
    vec3 sum = vec3(0.0);
    if (igkHasModel(cam)) {
        // 2 x 2 samples over the pixel
        for (int j = 0; j < 2; j++) {
            for (int i = 0; i < 2; i++) {
                vec2 q = gl_FragCoord.xy + (vec2(float(i), float(j)) + 0.5) * 0.5 - 0.5;
                q.y = h - q.y;                                                  // y up from the bottom
                bool right = q.x >= splitX;                                     // Split on, the right wall
                vec2 s = q - (right ? vec2(offset_xr, offset_yr) : vec2(offset_x, offset_y));
                vec2 c = s - vec2(right ? 0.5 * (splitX + w) : 0.5 * splitX, 0.5 * h);   // from the wall's middle
                vec3 d;
                if (mode == 1) {
                    vec4 e = igkEquirectDirection(c, w, right ? rRight : rLeft);
                    if (e.w < 0.5) continue;                                    // past a pole: black
                    d = e.xyz;
                } else {
                    d = igkWallDirection(c, right ? w - splitX : splitX, right ? rRight : rLeft, right ? fov_r : fov);
                }
                vec2 p = igkLensPoint(d, cam, nadir);
                if (igkInside(p)) sum += FETCH(p).rgb;
            }
        }
    }
    vec3 color = sum * 0.25;
    if (pl.z > 0.5) {
        float mark = igkWarning(gl_FragCoord.xy, max(16.0, 0.05 * h));
        if (mark > 1.5) color = vec3(0.0);
        else if (mark > 0.5) color = IGK_WARNING_YELLOW;
    }
    gl_FragColor = vec4(color, 1.0);
}
