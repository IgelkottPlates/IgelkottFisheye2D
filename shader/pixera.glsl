//@implements: sampler2D
struct IgelkottFisheye {
	sampler2D sampler;
	//@ label: "Camera", editor: enum, enum_default: 0, values: "Auto_(tag), PYXIS_12K, Sony_Venice_2, Z-Cam_E2_S6"
	int camera;
	//@ label: "Pointing", editor: enum, enum_default: 0, values: "Auto_(tag), Zenith, Nadir"
	int pointing;
	//@ label: "Offset X (% of height)", editor: range, min: -200, max: 200, range_min: -200, range_max: 200, range_default: 0
	float offsetX;
	//@ label: "Offset Y (% of height)", editor: range, min: -200, max: 200, range_min: -200, range_max: 200, range_default: 0
	float offsetY;
	//@ label: "Mode", editor: enum, enum_default: 0, values: "Wall, Equirect"
	int mode;
	//@ label: "Yaw", editor: range, min: -360, max: 360, range_min: -360, range_max: 360, range_default: 0
	float yaw;
	//@ label: "Pitch", editor: range, min: -90, max: 90, range_min: -90, range_max: 90, range_default: 0
	float pitch;
	//@ label: "Roll", editor: range, min: -180, max: 180, range_min: -180, range_max: 180, range_default: 0
	float roll;
	//@ label: "FOV (horizontal)", editor: range, min: 1, max: 179, range_min: 1, range_max: 179, range_default: 90
	float fov;
	//@ label: "Aspect (width / height)", editor: range, min: 0.1, max: 10, range_min: 0.1, range_max: 10, range_default: 1.7778
	float aspect;
	//@ label: "Split", editor: bool, bool_default: false
	bool split;
	//@ label: "Split Position %", editor: range, min: 0, max: 100, range_min: 0, range_max: 100, range_default: 50
	float splitPos;
	//@ label: "Right Yaw", editor: range, min: -360, max: 360, range_min: -360, range_max: 360, range_default: 0
	float yawR;
	//@ label: "Right Pitch", editor: range, min: -90, max: 90, range_min: -90, range_max: 90, range_default: 0
	float pitchR;
	//@ label: "Right Roll", editor: range, min: -180, max: 180, range_min: -180, range_max: 180, range_default: 0
	float rollR;
	//@ label: "Right FOV (horizontal)", editor: range, min: 1, max: 179, range_min: 1, range_max: 179, range_default: 90
	float fovR;
	//@ label: "Right Offset X (% of height)", editor: range, min: -200, max: 200, range_min: -200, range_max: 200, range_default: 0
	float offsetXR;
	//@ label: "Right Offset Y (% of height)", editor: range, min: -200, max: 200, range_min: -200, range_max: 200, range_default: 0
	float offsetYR;
};

// tex_coords run 0..1 with y up, as in PIXERA's Equirectangular effect; the wall is `aspect` heights wide.
// Offset X/Y move the finished picture (after the projection), in % of the height: PIXERA gives the effect no pixel size.
// With Split on, Offset X/Y are the left wall's and Right Offset X/Y the right wall's.
vec4 texture(IgelkottFisheye s, vec2 tex_coords) {
	// The output pixel's size in tex_coords, from the screen derivatives (PIXERA gives the effect no pixel size): the same
	// 2 x 2 samples over the pixel as Live FX. With one sample the wall came out sharper than the model and aliased
	// (MTF50 0.513 against 0.420, 2026-11-23). Taken first, outside any branch.
	vec2 ddx = dFdx(tex_coords);
	vec2 ddy = dFdy(tex_coords);
	float tag = igkTag(s.sampler, 0.0);         // always: a plate without the tag is refused (Eric 2026-11-23)
	vec3 pl = igkPlate(tag, s.camera, s.pointing);
	int cam = int(pl.x + 0.5);
	vec3 sum = vec3(0.0);
	if (pl.z < 0.5) {
		float w = max(s.aspect, 0.01);
		float splitX = s.split ? clamp(s.splitPos, 0.0, 100.0) * 0.01 * w : w;
		mat3 rLeft = igkRotation(s.yaw, s.pitch, s.roll);
		mat3 rRight = igkRotation(s.yawR, s.pitchR, s.rollR);
		for (int j = 0; j < 2; j++) {
			for (int i = 0; i < 2; i++) {
				vec2 t = tex_coords + ddx * (float(i) * 0.5 - 0.25) + ddy * (float(j) * 0.5 - 0.25);
				vec2 q = vec2(t.x * w, t.y);
				bool right = q.x >= splitX;                                // Split on, the right wall
				vec2 o = q - (right ? vec2(s.offsetXR, s.offsetYR) : vec2(s.offsetX, s.offsetY)) * 0.01;
				vec2 c = o - vec2(right ? 0.5 * (splitX + w) : 0.5 * splitX, 0.5);   // from the wall's middle, in heights
				vec3 d;
				if (s.mode == 1) {
					vec4 e = igkEquirectDirection(c, w, right ? rRight : rLeft);
					if (e.w < 0.5) continue;                               // past a pole: black
					d = e.xyz;
				} else {
					d = igkWallDirection(c, right ? w - splitX : splitX, right ? rRight : rLeft, right ? s.fovR : s.fov);
				}
				vec2 p = igkLensPoint(d, cam, pl.y > 0.5);
				if (igkInside(p)) sum += igkFetch(s.sampler, p).rgb;
			}
		}
	}
	vec3 color = sum * 0.25;
	float aw = max(s.aspect, 0.01);
	if (pl.z > 1.5 && igkMessage(vec2(tex_coords.x * aw, 1.0 - tex_coords.y), vec2(aw, 1.0)) > 0.5) color = IGK_WARNING_YELLOW;
	if (pl.z > 0.5) {
		float mark = igkWarning(vec2(tex_coords.x * max(s.aspect, 0.01), 1.0 - tex_coords.y), 0.05);
		if (mark > 1.5) color = vec3(0.0);
		else if (mark > 0.5) color = IGK_WARNING_YELLOW;
	}
	return vec4(color, 1.0);
}
