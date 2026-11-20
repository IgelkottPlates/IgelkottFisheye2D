# Builds the Windows install package: ..\_releases\IgelkottFisheye\IgelkottFisheye-Windows.zip (no build output in
# the project folder, atlas rules 1-3; the version is the VERSION file inside the zip and the name of its folder)
# (the node, the installer, the PIXERA effect and README.txt, all in one folder inside the zip;
# no Stabilizer page since 0.14: the node has no Tracking view or Stab controls).
# Runs tools\verify_windows.py first and refuses to build if the shader does not match IgelkottStage.
#
#   powershell -ExecutionPolicy Bypass -File windows\build-package.ps1 [-SkipVerify]
param([switch]$SkipVerify)

$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
$Version = (Get-Content (Join-Path $Root 'VERSION') -TotalCount 1).Trim()
$Name = "IgelkottFisheye-$Version-Windows"

if (-not $SkipVerify) {
    python (Join-Path $Root 'tools\verify_windows.py')
    if ($LASTEXITCODE -ne 0) { throw 'verify_windows.py failed: no package built' }
}

$Stage = Join-Path ([IO.Path]::GetTempPath()) "igelkott-package\$Name"
if (Test-Path $Stage) { Remove-Item -Recurse -Force $Stage }
New-Item -ItemType Directory -Force -Path $Stage | Out-Null

$Files = [ordered]@{
    'windows\Install IgelkottFisheye.cmd'   = 'Install IgelkottFisheye.cmd'
    'windows\Uninstall IgelkottFisheye.cmd' = 'Uninstall IgelkottFisheye.cmd'
    'windows\Install-IgelkottFisheye.ps1'   = 'Install-IgelkottFisheye.ps1'
    'windows\README.txt'                    = 'README.txt'
    'matchbox\IgelkottFisheye2D.glsl'       = 'IgelkottFisheye2D.glsl'
    'matchbox\IgelkottFisheye2D.xml'        = 'IgelkottFisheye2D.xml'
    'VERSION'                               = 'VERSION'
    'LICENSE'                               = 'LICENSE.txt'
    'pixera\IgelkottFisheye.glsl'           = 'PIXERA\IgelkottFisheye.glsl'
    'pixera\README.txt'                     = 'PIXERA\README.txt'
}
New-Item -ItemType Directory -Force -Path (Join-Path $Stage 'PIXERA') | Out-Null
foreach ($src in $Files.Keys) { Copy-Item -LiteralPath (Join-Path $Root $src) -Destination (Join-Path $Stage $Files[$src]) }

# Notepad-friendly line endings for the text the user opens
$readme = Join-Path $Stage 'README.txt'
[IO.File]::WriteAllText($readme, ((Get-Content -Raw $readme) -replace "`r?`n", "`r`n"))

$Dist = Join-Path (Split-Path $Root -Parent) '_releases\IgelkottFisheye'
New-Item -ItemType Directory -Force -Path $Dist | Out-Null
$Zip = Join-Path $Dist 'IgelkottFisheye-Windows.zip'
if (Test-Path $Zip) { Remove-Item -Force $Zip }
Compress-Archive -Path $Stage -DestinationPath $Zip
Remove-Item -Recurse -Force (Split-Path $Stage -Parent)

Write-Output "Built $Zip"
