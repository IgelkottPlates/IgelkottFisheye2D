# Playback test on the Threadripper PC (Windows, 6 GB/s)

The NotchLC playback test (`docs/MAC-TEST.md` section 11) on the Threadripper rig, Windows 10, Radeon RX 9070 XT. It
moved there on 2026-11-23 (Eric) because the test disk must read at 6 GB/s:

- The first Windows PC (ASUS PRIME Z390-A, i9-9900KS) has PCIe 3.0 only. Its NVMe slot runs the Corsair MP600 PRO NH
  at Gen 3 x4, so its ceiling is about 3.5 GB/s.
- Windows has no APFS driver of its own. Paragon's (macOS File Systems for Windows 18.30) reads APFS through Dokan
  and topped out at 1.1 GB/s on that disk, with 1 to 16 readers.

Write each result into `PROJECT.md` with the date, the machine and the Live FX version.

## Before you start

- [x] **The disk is NTFS (64 KB clusters), formatted on Windows** (Eric 2026-11-23, Threadripper: "keep NTFS").
      NTFS is Windows' own file system and costs nothing when reading. The Mac can read NTFS but not write it. To use
      the disk read-write on the Mac as well, format it exFAT instead; erase it only after copying everything off
      (6.3 TB on 2026-11-23). The exFAT recipe, in an administrator command prompt, `diskpart`:

      list disk
      select disk <N>          (the 8 TB Corsair MP600 PRO NH, about 7452 GB; check it twice)
      clean
      convert gpt
      create partition primary
      format fs=exfat unit=1M quick label=8TB
      assign letter=E

      Then copy `_NotchLC` onto it. The Mac reads and writes exFAT with its own driver; only the formatting is done on
      Windows. Neither file system is proven at 6 GB/s on this disk yet: 11a measures it.
- [ ] The disk sits in an M.2 or PCIe slot that runs at **Gen 4 x4 or faster**. Check in PowerShell:

      Get-PnpDevice -Class SCSIAdapter -PresentOnly | Where-Object FriendlyName -match 'NVM' | ForEach-Object {
          Get-PnpDeviceProperty -InstanceId $_.InstanceId -KeyName DEVPKEY_PciDevice_CurrentLinkSpeed,DEVPKEY_PciDevice_CurrentLinkWidth }

      The disk's controller should show link speed 4 (or 5) and width 4. Speed 3 means Gen 3, about 3.5 GB/s at most.
- [ ] Live FX 9.9 with a valid licence. The first PC's licence had expired on 2026-11-23.
- [ ] IgelkottFisheye installed: `windows/Install IgelkottFisheye.cmd`, or copy `matchbox/IgelkottFisheye2D.glsl` and
      `.xml` to `C:\ProgramData\Assimilator\plugin64\Matchbox\shaders`. Start Live FX afterwards.
- [ ] Python 3 and an ffmpeg with the NotchLC decoder (Topaz Video AI's `ffmpeg.exe` has it).

## 11a. The files

Measure all 18 files where they lie on the disk (no copy). Replace `E:` with the disk's letter:

    python tools\bench_notchlc.py --store E:\ --in-place --out %USERPROFILE%\IgelkottBench\bench-threadripper.jsonl ^
        --ffmpeg "C:\Program Files\Topaz Labs LLC\Topaz Video AI\ffmpeg.exe" ^
        --ffprobe "C:\Program Files\Topaz Labs LLC\Topaz Video AI\ffprobe.exe"

Each line has the size, MB per frame, the read rate needed (fisheye 0.57–0.79 GB/s, 16K equirect 1.4–2.1 GB/s), the
disk's read rate past the file cache, the max fps from the disk, and ffmpeg's CPU decode rate.

## 11b. Live FX, max fps with Free Run

The same steps as `docs/MAC-TEST.md` 11b:

- Project 7680 × 2160, 25 fps, ACES (ACEScct).
- A007C001 as fisheye with the node (Auto/Auto, Wall, FOV 90), and as equirect with Eq->2D at FOV 31.42.
- Free Run.
- Write down fps, disk read and GPU/CPU. On Windows, read them with the `\GPU Engine(pid_<Live FX>*)\Utilization
  Percentage` counter, plus the process's CPU time and read transfer count. The Process and PhysicalDisk counters fail
  on a Swedish Windows.
- The fisheye without the node too, then the node at 15360 × 2160.

Since 0.20 the node refuses a plate without the pixel tag: black, NOT AN IGELKOTT CLIP. All 18 Store files carry the
tag. A black wall with the message means the file was not read the way the node expects.

## Earlier results to compare with

- First Windows PC, Intel 660p, 2026-11-22: fisheye with the node at 25 fps (real time, 784 MB/s). The equirect with
  Eq->2D played at 10–11 fps, limited by the disk.
- Same PC, Paragon APFS, 2026-11-23: 1.1 GB/s from the 8 TB disk (Dokan).
