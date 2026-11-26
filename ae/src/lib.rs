// IgelkottFisheye for Adobe After Effects - Igelkott Film AB, https://igelkottplates.com
//
// A SmartFX effect put straight on the fisheye plate layer (Eric 2026-11-25: "On the plate, Wall Width/Height"). It
// reads the whole plate at its own size and writes a Wall Width x Wall Height picture centred on the layer, so in a comp
// of the wall's size with the plate centred, the wall fills the comp. 8, 16 and 32 bits per channel.
//
// The maths is not here: the kernel is the Resolve edition's DCTL text, compiled as C++ by build.rs (see there), so
// After Effects, Resolve and the tests run the same lines. This file only does After Effects: the controls, the output
// rectangle, the buffers and the threads.
use after_effects as ae;
use std::ffi::{c_int, c_longlong, c_void};

#[derive(Eq, PartialEq, Hash, Clone, Copy, Debug)]
enum Params {
    Camera,
    Pointing,
    Mode,
    Yaw,
    Pitch,
    Roll,
    Fov,
    OffsetX,
    OffsetY,
    Split,
    SplitPosition,
    RightYaw,
    RightPitch,
    RightRoll,
    RightFov,
    RightOffsetX,
    RightOffsetY,
    WallWidth,
    WallHeight,
}

// The kernel's parameter block (IgkParams in shader/resolve.fuse)
#[repr(C)]
struct IgkParams {
    camera: c_int,
    pointing: c_int,
    mode: c_int,
    split: c_int,
    offset: [f32; 4],
    view: [f32; 4],
    view_r: [f32; 4],
    split_pos: f32,
    dstsize: [c_int; 2],
}

unsafe extern "C" {
    fn igk_ae_render(src: *const c_void, sw: c_int, sh: c_int, srb: c_longlong, dst: *mut c_void, dw: c_int, dh: c_int,
                     drb: c_longlong, fmt: c_int, p: *const IgkParams, y0: c_int, y1: c_int);
}

#[derive(Default)]
struct Plugin {}

ae::define_effect!(Plugin, (), Params);

fn float(params: &mut ae::Parameters<Params>, id: Params, name: &str, lo: f32, hi: f32, soft_lo: f32, soft_hi: f32,
         default: f64, precision: i16) -> Result<(), ae::Error> {
    params.add(id, name, ae::FloatSliderDef::setup(|f| {
        f.set_valid_min(lo);
        f.set_valid_max(hi);
        f.set_slider_min(soft_lo);
        f.set_slider_max(soft_hi);
        f.set_default(default);
        f.set_precision(precision);
        f.set_value(f.default());
    }))
}

fn popup(params: &mut ae::Parameters<Params>, id: Params, name: &str, options: &[&str]) -> Result<(), ae::Error> {
    params.add(id, name, ae::PopupDef::setup(|f| {
        f.set_options(options);
        f.set_default(1);
        f.set_value(f.default());
    }))
}

// The pointer to row 0 of an AE world (rowbytes can be negative)
fn row0(layer: &ae::Layer) -> *const u8 {
    let p = layer.buffer().as_ptr();
    if layer.row_bytes() < 0 { unsafe { p.offset(-layer.row_bytes() * (layer.height() as isize - 1)) } } else { p }
}

impl AdobePluginGlobal for Plugin {
    fn params_setup(&self, params: &mut ae::Parameters<Params>, _: InData, _: OutData) -> Result<(), Error> {
        // The same controls as the Live FX node (Eric 2026-11-20), plus Wall Width/Height as in Resolve (2026-11-25)
        popup(params, Params::Camera, "Camera", &["Auto (tag)", "PYXIS 12K", "Sony Venice 2", "Z-Cam E2 S6"])?;
        popup(params, Params::Pointing, "Pointing", &["Auto (tag)", "Zenith", "Nadir"])?;
        popup(params, Params::Mode, "Mode", &["Wall", "Equirect"])?;
        float(params, Params::Yaw, "Yaw", -360.0, 360.0, -180.0, 180.0, 0.0, 2)?;
        float(params, Params::Pitch, "Pitch", -90.0, 90.0, -90.0, 90.0, 0.0, 2)?;
        float(params, Params::Roll, "Roll", -180.0, 180.0, -180.0, 180.0, 0.0, 2)?;
        float(params, Params::Fov, "FOV", 1.0, 179.0, 1.0, 179.0, 90.0, 2)?;
        float(params, Params::OffsetX, "Offset X", -8000.0, 8000.0, -500.0, 500.0, 0.0, 1)?;
        float(params, Params::OffsetY, "Offset Y", -8000.0, 8000.0, -500.0, 500.0, 0.0, 1)?;
        params.add(Params::Split, "Split", ae::CheckBoxDef::setup(|f| {
            f.set_default(false);
            f.set_label("Two walls side by side");
            f.set_value(f.default());
        }))?;
        float(params, Params::SplitPosition, "Split Position", 0.0, 100.0, 0.0, 100.0, 50.0, 1)?;
        float(params, Params::RightYaw, "Right Yaw", -360.0, 360.0, -180.0, 180.0, 0.0, 2)?;
        float(params, Params::RightPitch, "Right Pitch", -90.0, 90.0, -90.0, 90.0, 0.0, 2)?;
        float(params, Params::RightRoll, "Right Roll", -180.0, 180.0, -180.0, 180.0, 0.0, 2)?;
        float(params, Params::RightFov, "Right FOV", 1.0, 179.0, 1.0, 179.0, 90.0, 2)?;
        float(params, Params::RightOffsetX, "Right Offset X", -8000.0, 8000.0, -500.0, 500.0, 0.0, 1)?;
        float(params, Params::RightOffsetY, "Right Offset Y", -8000.0, 8000.0, -500.0, 500.0, 0.0, 1)?;
        float(params, Params::WallWidth, "Wall Width", 16.0, 30000.0, 16.0, 16384.0, 3840.0, 0)?;
        float(params, Params::WallHeight, "Wall Height", 16.0, 30000.0, 16.0, 8640.0, 2160.0, 0)?;
        Ok(())
    }

    fn handle_command(&mut self, cmd: ae::Command, in_data: InData, _out_data: OutData, params: &mut ae::Parameters<Params>)
        -> Result<(), ae::Error> {
        match cmd {
            ae::Command::About => {
                let mut out = _out_data;
                out.set_return_msg(&format!(
                    "IgelkottFisheye {} by Igelkott Film AB, igelkottplates.com\r\rIgelkott fisheye plates straight onto \
                     a wall, through the lens model, as IgelkottStage plays them. A plate without the Igelkott pixel tag \
                     is not played.", env!("CARGO_PKG_VERSION")));
            }
            ae::Command::SmartPreRender { mut extra } => {
                let ds_x = f32::from(in_data.downsample_x());
                let ds_y = f32::from(in_data.downsample_y());
                let wall_w = (params.get(Params::WallWidth)?.as_float_slider()?.value() as f32 * ds_x).round().max(1.0) as i32;
                let wall_h = (params.get(Params::WallHeight)?.as_float_slider()?.value() as f32 * ds_y).round().max(1.0) as i32;
                let cb = extra.callbacks();
                // The whole plate: its size first (an empty request), then all of it, whatever part of the wall is asked for
                let mut req = extra.output_request();
                req.rect = ae::sys::PF_LRect { left: 0, top: 0, right: 0, bottom: 0 };
                let info = cb.checkout_layer(0, 1, &req, in_data.current_time(), in_data.time_step(), in_data.time_scale())?;
                let full = info.max_result_rect;
                req.rect = full;
                cb.checkout_layer(0, 0, &req, in_data.current_time(), in_data.time_step(), in_data.time_scale())?;
                // The wall, centred on the plate, in the layer's coordinates
                let cx = (full.left + full.right) / 2;
                let cy = (full.top + full.bottom) / 2;
                let wall = ae::Rect { left: cx - wall_w / 2, top: cy - wall_h / 2, right: cx - wall_w / 2 + wall_w,
                                      bottom: cy - wall_h / 2 + wall_h };
                extra.set_result_rect(wall);
                extra.set_max_result_rect(wall);
                extra.set_returns_extra_pixels(true);
            }
            ae::Command::SmartRender { extra } => {
                let cb = extra.callbacks();
                let Some(src) = cb.checkout_layer_pixels(0)? else { return Ok(()); };
                let Some(mut dst) = cb.checkout_output()? else { return Ok(()); };
                let fmt = match dst.bit_depth() { 8 => 1, 16 => 2, _ => 3 };
                let ds_x = f32::from(in_data.downsample_x());
                let ds_y = f32::from(in_data.downsample_y());
                let f = |p: &mut ae::Parameters<Params>, id| -> Result<f32, ae::Error> { Ok(p.get(id)?.as_float_slider()?.value() as f32) };
                let k = IgkParams {
                    camera: params.get(Params::Camera)?.as_popup()?.value() - 1,
                    pointing: params.get(Params::Pointing)?.as_popup()?.value() - 1,
                    mode: params.get(Params::Mode)?.as_popup()?.value() - 1,
                    split: params.get(Params::Split)?.as_checkbox()?.value() as c_int,
                    // Offsets are full-size output pixels; at a lower preview resolution they shrink with the picture
                    offset: [f(params, Params::OffsetX)? * ds_x, f(params, Params::OffsetY)? * ds_y,
                             f(params, Params::RightOffsetX)? * ds_x, f(params, Params::RightOffsetY)? * ds_y],
                    view: [f(params, Params::Yaw)?, f(params, Params::Pitch)?, f(params, Params::Roll)?, f(params, Params::Fov)?],
                    view_r: [f(params, Params::RightYaw)?, f(params, Params::RightPitch)?, f(params, Params::RightRoll)?,
                             f(params, Params::RightFov)?],
                    split_pos: f(params, Params::SplitPosition)?,
                    dstsize: [dst.width() as c_int, dst.height() as c_int],
                };
                let (sw, sh, srb) = (src.width() as c_int, src.height() as c_int, src.row_bytes() as c_longlong);
                let (dw, dh, drb) = (dst.width() as c_int, dst.height() as c_int, dst.row_bytes() as c_longlong);
                let sp = row0(&src) as usize;
                let dp = row0(&dst) as usize;
                let _ = dst.buffer_mut();
                // Blocks of 8 rows from a shared counter, one thread per core: the performance and efficiency cores
                // finish together (2026-11-25, M3 Ultra 20 + 8 cores: 71 -> 64 ms per 3840 x 2160 frame against one
                // equal band per thread; bit for bit the same picture)
                const ROWS: c_int = 8;
                let n = std::thread::available_parallelism().map(|n| n.get()).unwrap_or(8).min(64);
                let next = std::sync::atomic::AtomicI32::new(0);
                let kp = &k as *const IgkParams as usize;
                std::thread::scope(|s| {
                    for _ in 0..n {
                        let next = &next;
                        s.spawn(move || loop {
                            let y0 = next.fetch_add(ROWS, std::sync::atomic::Ordering::Relaxed);
                            if y0 >= dh { break; }
                            unsafe {
                                igk_ae_render(sp as *const c_void, sw, sh, srb, dp as *mut c_void, dw, dh, drb, fmt,
                                              kp as *const IgkParams, y0, (y0 + ROWS).min(dh));
                            }
                        });
                    }
                });
                cb.checkin_layer_pixels(0)?;
            }
            _ => {}
        }
        Ok(())
    }
}
