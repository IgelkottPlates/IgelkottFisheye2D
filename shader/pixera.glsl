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
	//@ label: "FOV (vertical)", editor: range, min: 1, max: 179, range_min: 1, range_max: 179, range_default: 90
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
	//@ label: "Right FOV (vertical)", editor: range, min: 1, max: 179, range_min: 1, range_max: 179, range_default: 90
	float fovR;
};

// tex_coords run 0..1 with y up, as in PIXERA's Equirectangular effect; the wall is `aspect` heights wide.
// Offset X/Y move the finished picture (after the projection), in % of the height: PIXERA gives the effect no pixel size.
vec4 texture(IgelkottFisheye s, vec2 tex_coords) {
	vec3 pl = igkPlate(igkTag(s.sampler, 0.0), s.camera, s.pointing);
	int cam = int(pl.x + 0.5);
	vec3 color = vec3(0.0);
	if (igkHasModel(cam)) {
		float w = max(s.aspect, 0.01);
		vec2 q = vec2(tex_coords.x * w, tex_coords.y);
		vec2 o = q - vec2(s.offsetX, s.offsetY) * 0.01;
		float splitX = s.split ? clamp(s.splitPos, 0.0, 100.0) * 0.01 * w : w;
		vec3 d;
		if (s.mode == 1) {
			d = igkEquirectDirection(vec2(o.x / w, o.y));
		} else if (q.x < splitX) {
			d = igkWallDirection(o - vec2(0.5 * splitX, 0.5), 1.0, s.yaw, s.pitch, s.roll, s.fov);
		} else {
			d = igkWallDirection(o - vec2(0.5 * (splitX + w), 0.5), 1.0, s.yawR, s.pitchR, s.rollR, s.fovR);
		}
		vec2 p = igkLensPoint(d, cam, pl.y > 0.5);
		if (igkInside(p)) color = igkFetch(s.sampler, p).rgb;
	}
	if (pl.z > 0.5) {
		float mark = igkWarning(vec2(tex_coords.x * max(s.aspect, 0.01), 1.0 - tex_coords.y), 0.05);
		if (mark > 1.5) color = vec3(0.0);
		else if (mark > 0.5) color = IGK_WARNING_YELLOW;
	}
	return vec4(color, 1.0);
}
