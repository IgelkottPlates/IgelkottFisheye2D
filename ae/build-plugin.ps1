# Builds IgelkottFisheye.aex for After Effects on Windows from ae/ (Rust, the after-effects crate) and the kernel in
# resolve/IgelkottFisheye.fuse (see ae/build.rs). Needs Rust (https://rustup.rs, the MSVC toolchain) and the Visual
# Studio Build Tools with "Desktop development with C++" (the C++ compiler for the kernel and rc.exe for the PiPL
# resource). The build goes to %LOCALAPPDATA% (no build output in the project folder).
#
#   powershell -ExecutionPolicy Bypass -File ae\build-plugin.ps1            -> <cache>\IgelkottFisheye.aex
#   powershell -ExecutionPolicy Bypass -File ae\build-plugin.ps1 -Install   -> also copies it to MediaCore (asks for admin)
param([switch]$Install)

$ErrorActionPreference = 'Stop'
$Here = $PSScriptRoot
$Root = Split-Path $Here -Parent
$env:CARGO_TARGET_DIR = Join-Path $env:LOCALAPPDATA 'Igelkott\IgelkottLiveFXFisheye\ae-target'

python (Join-Path $Root 'tools\build_shaders.py') --check
if ($LASTEXITCODE -ne 0) { throw 'Run python tools\build_shaders.py first' }
if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) { throw 'cargo is missing: install Rust from https://rustup.rs' }

Push-Location $Here
try { cargo build --release; if ($LASTEXITCODE -ne 0) { throw 'cargo build failed' } } finally { Pop-Location }

$Dll = Join-Path $env:CARGO_TARGET_DIR 'release\igelkottfisheye.dll'
$Aex = Join-Path $env:CARGO_TARGET_DIR 'release\IgelkottFisheye.aex'
Copy-Item -Force $Dll $Aex
Write-Output "Built $Aex"

if ($Install) {
    $Dest = 'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore'
    Start-Process powershell -Verb RunAs -Wait -ArgumentList "-NoProfile -Command Copy-Item -Force '$Aex' '$Dest\IgelkottFisheye.aex'"
    Write-Output "Installed in ${Dest}: restart After Effects"
}
