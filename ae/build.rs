// Builds the After Effects edition: the PiPL resource (pipl crate) and the kernel. The kernel is not ported again: it
// is the Resolve edition's DCTL text (resolve/IgelkottFisheye.fuse, made by tools/build_shaders.py from
// shader/core.dctl), compiled as C++ after tools/dctl_cpu.h, exactly as verify_windows.py tests it.
use pipl::*;
use std::{env, fs, path::PathBuf};

const PF_PLUG_IN_VERSION: u16 = 13;
const PF_PLUG_IN_SUBVERS: u16 = 28;

fn kernel() {
    let root = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap()).join("..");
    let fuse_path = root.join("resolve").join("IgelkottFisheye.fuse");
    let header_path = root.join("tools").join("dctl_cpu.h");
    println!("cargo:rerun-if-changed={}", fuse_path.display());
    println!("cargo:rerun-if-changed={}", header_path.display());
    let fuse = fs::read_to_string(&fuse_path).expect("resolve/IgelkottFisheye.fuse (run python tools/build_shaders.py)");
    let params = fuse.split("IgkParams = [[").nth(1).and_then(|s| s.split("]]").next()).expect("IgkParams in the Fuse");
    let kernel = fuse.split("[==[").nth(1).and_then(|s| s.split("]==]").next()).expect("the kernel in the Fuse");
    let header = fs::read_to_string(&header_path).unwrap();
    // On the CPU the per-frame work is taken out of the pixel loop (2026-11-25: ~205 ms per 4K frame on 28 threads
    // before): the pixel tag (20-40 bilinear reads per pixel) and the two rotation matrices (18 sin/cos per pixel) are
    // the same for every pixel of a frame, so igk_ae_render works them out once per call with the same functions and
    // the kernel reads the results. Same lines, same order of operations: the picture is bit for bit the same.
    let swap = |text: &str, from: &str, to: &str| -> String {
        assert!(text.contains(from), "build.rs: the kernel no longer has `{from}`; update ae/build.rs");
        text.replace(from, to)
    };
    let kernel = swap(kernel, "float tag = igkTag(src, 0.0f);", "float tag = igk_frame_tag;");
    let kernel = swap(&kernel, "IgkMat3 rLeft = igkRotation(params->view[0], params->view[1], params->view[2]);",
                      "IgkMat3 rLeft = igk_frame_left;");
    let kernel = swap(&kernel, "IgkMat3 rRight = igkRotation(params->viewR[0], params->viewR[1], params->viewR[2]);",
                      "IgkMat3 rRight = igk_frame_right;");
    let kernel = swap(&kernel, "__KERNEL__ void IgkKernel(",
                      "// Worked out once per call by igk_ae_render (see ae/build.rs)\n\
                       static thread_local float igk_frame_tag;\n\
                       static thread_local IgkMat3 igk_frame_left, igk_frame_right;\n\n\
                       __KERNEL__ void IgkKernel(");
    let text = format!(
        "{header}\ntypedef struct {{{params}}} IgkParams;\n{kernel}\n\
         // The kernel over the output rows y0..y1 (counted from the bottom, as the kernel does). Buffers are AE's own.\n\
         extern \"C\" void igk_ae_render(const void *src, int sw, int sh, long long srb, void *dst, int dw, int dh, long long drb,\n\
                                       int fmt, const IgkParams *p, int y0, int y1) {{\n\
             Tex s = {{src, nullptr, sw, sh, srb, fmt, 1}};\n\
             Tex d = {{nullptr, dst, dw, dh, drb, fmt, 1}};\n\
             igk_frame_tag = igkTag(&s, 0.0f);\n\
             igk_frame_left = igkRotation(p->view[0], p->view[1], p->view[2]);\n\
             igk_frame_right = igkRotation(p->viewR[0], p->viewR[1], p->viewR[2]);\n\
             for (igk_gy = y0; igk_gy < y1; igk_gy++) for (igk_gx = 0; igk_gx < dw; igk_gx++) IgkKernel(p, &s, &d);\n\
         }}\n");
    let out = PathBuf::from(env::var("OUT_DIR").unwrap()).join("igk_kernel.cpp");
    fs::write(&out, text).unwrap();
    cc::Build::new().cpp(true).std("c++14").opt_level(3).file(&out).warnings(false).compile("igkkernel");
}

#[rustfmt::skip]
fn main() {
    kernel();
    // The version from VERSION (0.23 -> 0, 23)
    let version = fs::read_to_string(PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap()).join("../VERSION")).unwrap();
    let mut parts = version.trim().split('.').map(|v| v.parse::<u32>().unwrap_or(0));
    let (major, minor) = (parts.next().unwrap_or(0), parts.next().unwrap_or(0));
    println!("cargo:rerun-if-changed=../VERSION");
    pipl::plugin_build(vec![
        Property::Kind(PIPLType::AEEffect),
        Property::Name("IgelkottFisheye"),
        Property::Category("Igelkott"),
        #[cfg(target_os = "windows")]
        Property::CodeWin64X86("EffectMain"),
        #[cfg(target_os = "macos")]
        Property::CodeMacIntel64("EffectMain"),
        #[cfg(target_os = "macos")]
        Property::CodeMacARM64("EffectMain"),
        Property::AE_PiPL_Version { major: 2, minor: 0 },
        Property::AE_Effect_Spec_Version { major: PF_PLUG_IN_VERSION, minor: PF_PLUG_IN_SUBVERS },
        Property::AE_Effect_Version { version: major, subversion: minor, bugversion: 0, stage: Stage::Release, build: 1 },
        Property::AE_Effect_Info_Flags(0),
        Property::AE_Effect_Global_OutFlags(OutFlags::DeepColorAware),
        Property::AE_Effect_Global_OutFlags_2(OutFlags2::FloatColorAware | OutFlags2::SupportsSmartRender | OutFlags2::SupportsThreadedRendering),
        Property::AE_Effect_Match_Name("Igelkott IgelkottFisheye"),
        Property::AE_Reserved_Info(0),
        Property::AE_Effect_Support_URL("https://igelkottplates.com"),
    ])
}
