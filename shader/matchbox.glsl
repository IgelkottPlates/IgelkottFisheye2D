// Live FX (Matchbox). For movie files Live FX lays the source and the output out top row first (seen on Mac 2026-10-05
// and on Windows 2026-10-28): texture row 0 is the top of the picture and gl_FragCoord.y counts from the top. PNG clips
// are laid out bottom row first (Windows 2026-11-19): there the wall comes out turned 180 degrees.

uniform sampler2D front;
uniform float adsk_result_w, adsk_result_h;

uniform int plate;
uniform int camera;
uniform int pointing;
uniform float offset_x;
uniform float offset_y;
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
    vec3 pl = igkPlate(igkTag(0.0), plate, camera, pointing);
    int cam = int(pl.x + 0.5);
    bool nadir = pl.y > 0.5;
    vec2 offset = vec2(offset_x, offset_y);
    float w = adsk_result_w;
    float h = adsk_result_h;
    float splitX = split ? clamp(split_pos, 0.0, 100.0) * 0.01 * w : w;
    vec3 sum = vec3(0.0);
    if (igkHasModel(cam)) {
        // 2 x 2 samples over the pixel
        for (int j = 0; j < 2; j++) {
            for (int i = 0; i < 2; i++) {
                vec2 q = gl_FragCoord.xy + (vec2(float(i), float(j)) + 0.5) * 0.5 - 0.5;
                q.y = h - q.y;                                                  // y up from the bottom
                vec3 d;
                if (mode == 1) {
                    d = igkEquirectDirection(q / vec2(w, h));
                } else if (q.x < splitX) {
                    d = igkWallDirection(q - vec2(0.5 * splitX, 0.5 * h), h, yaw, pitch, roll, fov);
                } else {
                    d = igkWallDirection(q - vec2(0.5 * (splitX + w), 0.5 * h), h, yaw_r, pitch_r, roll_r, fov_r);
                }
                vec2 p = igkLensPoint(d, cam, nadir, offset);
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
