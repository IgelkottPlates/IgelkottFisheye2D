// Runs the Resolve edition's DCTL kernel (resolve/IgelkottFisheye.fuse) on the CPU: the vector types, the math
// functions and the texture reads the kernel uses, as the Fusion Fuse SDK describes them (bilinear, normalised
// coordinates from the bottom left, clamped edges, as the Fuse's sampler). Two users:
//   - the tests (verify_windows.py): float RGBA rows from the bottom, as Fusion holds them;
//   - the After Effects edition (ae/): AE's own buffers, ARGB in 8, 16 (0-32768) or 32 bits, rows from the top, read
//     and written in place, several threads at once (the kernel's x and y are per thread).
// Says nothing about Resolve's own GPU compiler: that is seen in Resolve.
#include <cmath>

struct float2 { float x, y; };
struct float3 { float x, y, z; };
struct float4 { float x, y, z, w; };

static inline float2 to_float2(float a, float b) { return {a, b}; }
static inline float3 to_float3(float a, float b, float c) { return {a, b, c}; }
static inline float4 to_float4(float a, float b, float c, float d) { return {a, b, c, d}; }

#define IGK_OPS(T, APPLY)                                                                                  \
    static inline T operator+(T a, T b) { return APPLY(+, a, b); }                                         \
    static inline T operator-(T a, T b) { return APPLY(-, a, b); }                                         \
    static inline T operator*(T a, T b) { return APPLY(*, a, b); }                                         \
    static inline T operator/(T a, T b) { return APPLY(/, a, b); }                                         \
    static inline T operator+(T a, float s) { return a + splat_##T(s); }                                   \
    static inline T operator-(T a, float s) { return a - splat_##T(s); }                                   \
    static inline T operator*(T a, float s) { return a * splat_##T(s); }                                   \
    static inline T operator/(T a, float s) { return a / splat_##T(s); }                                   \
    static inline T operator*(float s, T a) { return splat_##T(s) * a; }                                   \
    static inline T &operator+=(T &a, T b) { a = a + b; return a; }                                        \
    static inline T &operator*=(T &a, T b) { a = a * b; return a; }

static inline float2 splat_float2(float s) { return {s, s}; }
static inline float3 splat_float3(float s) { return {s, s, s}; }
static inline float4 splat_float4(float s) { return {s, s, s, s}; }
#define IGK_A2(op, a, b) float2{a.x op b.x, a.y op b.y}
#define IGK_A3(op, a, b) float3{a.x op b.x, a.y op b.y, a.z op b.z}
#define IGK_A4(op, a, b) float4{a.x op b.x, a.y op b.y, a.z op b.z, a.w op b.w}
IGK_OPS(float2, IGK_A2)
IGK_OPS(float3, IGK_A3)
IGK_OPS(float4, IGK_A4)

static inline float _sqrtf(float x) { return std::sqrt(x); }
static inline float _atan2f(float y, float x) { return std::atan2(y, x); }
static inline float _floorf(float x) { return std::floor(x); }
static inline float _fabs(float x) { return std::fabs(x); }
static inline float _cosf(float x) { return std::cos(x); }
static inline float _sinf(float x) { return std::sin(x); }
static inline float _tanf(float x) { return std::tan(x); }
static inline float _fmaxf(float a, float b) { return std::fmax(a, b); }
static inline float _fminf(float a, float b) { return std::fmin(a, b); }
static inline float _clampf(float x, float a, float b) { return std::fmin(std::fmax(x, a), b); }

// A texture. fmt 0: RGBA float; 1: AE ARGB 8 bits; 2: AE ARGB 16 bits (0-32768); 3: AE ARGB float. top_first: the
// buffer's first row is the picture's top (AE); the kernel's y counts from the bottom (Fusion) either way.
// rowbytes is 64 bits: long is 32 bits on Windows, and a large plate's buffer passes 2 GB
struct Tex { const void *px; void *out; int w, h; long long rowbytes; int fmt; int top_first; };

static inline unsigned char *igkRow(const Tex *t, const void *base, int y) {
    long long row = t->top_first ? (long long)(t->h - 1 - y) : (long long)y;
    return (unsigned char *)base + row * t->rowbytes;
}

static inline float4 igkTexel(const Tex *t, int x, int y) {
    x = x < 0 ? 0 : (x >= t->w ? t->w - 1 : x);
    y = y < 0 ? 0 : (y >= t->h ? t->h - 1 : y);
    unsigned char *r = igkRow(t, t->px, y);
    switch (t->fmt) {
    case 1: { const unsigned char *p = r + 4 * x; return {p[1] / 255.0f, p[2] / 255.0f, p[3] / 255.0f, p[0] / 255.0f}; }
    case 2: { const unsigned short *p = (const unsigned short *)r + 4 * x;
              return {p[1] / 32768.0f, p[2] / 32768.0f, p[3] / 32768.0f, p[0] / 32768.0f}; }
    case 3: { const float *p = (const float *)r + 4 * x; return {p[1], p[2], p[3], p[0]}; }
    default: { const float *p = (const float *)r + 4 * x; return {p[0], p[1], p[2], p[3]}; }
    }
}

// Bilinear, normalised coordinates (0 and 1 are the picture's outer edges), clamped
static inline float4 _tex2DVec4(const Tex *t, float u, float v) {
    float fx = u * t->w - 0.5f, fy = v * t->h - 0.5f;
    int x0 = (int)std::floor(fx), y0 = (int)std::floor(fy);
    float ax = fx - x0, ay = fy - y0;
    float4 a = igkTexel(t, x0, y0), b = igkTexel(t, x0 + 1, y0), c = igkTexel(t, x0, y0 + 1), d = igkTexel(t, x0 + 1, y0 + 1);
    return (a * (1 - ax) + b * ax) * (1 - ay) + (c * (1 - ax) + d * ax) * ay;
}

static inline float igkClamp01(float v) { return v < 0.0f ? 0.0f : (v > 1.0f ? 1.0f : v); }

static inline void _tex2DVec4Write(Tex *t, int x, int y, float4 c) {
    unsigned char *r = igkRow(t, t->out, y);
    switch (t->fmt) {
    case 1: { unsigned char *p = r + 4 * x;
              p[0] = (unsigned char)(igkClamp01(c.w) * 255.0f + 0.5f); p[1] = (unsigned char)(igkClamp01(c.x) * 255.0f + 0.5f);
              p[2] = (unsigned char)(igkClamp01(c.y) * 255.0f + 0.5f); p[3] = (unsigned char)(igkClamp01(c.z) * 255.0f + 0.5f); break; }
    case 2: { unsigned short *p = (unsigned short *)r + 4 * x;
              p[0] = (unsigned short)(igkClamp01(c.w) * 32768.0f + 0.5f); p[1] = (unsigned short)(igkClamp01(c.x) * 32768.0f + 0.5f);
              p[2] = (unsigned short)(igkClamp01(c.y) * 32768.0f + 0.5f); p[3] = (unsigned short)(igkClamp01(c.z) * 32768.0f + 0.5f); break; }
    case 3: { float *p = (float *)r + 4 * x; p[0] = c.w; p[1] = c.x; p[2] = c.y; p[3] = c.z; break; }
    default: { float *p = (float *)r + 4 * x; p[0] = c.x; p[1] = c.y; p[2] = c.z; p[3] = c.w; }
    }
}

static thread_local int igk_gx, igk_gy;
#define __DEVICE__ static inline
#define __KERNEL__
#define __CONSTANTREF__ const
#define __TEXTURE2D__ const Tex *
#define __TEXTURE2D_WRITE__ Tex *
#define DEFINE_KERNEL_ITERATORS_XY(a, b) int a = igk_gx, b = igk_gy;
