# IgelkottFisheye for Assimilate Live FX on Windows: installs (or removes) the Matchbox node IgelkottFisheye2D.
#
# Live FX on Windows reads Matchbox shaders from %ProgramData%\Assimilator\plugin64\Matchbox\shaders at start
# (read off Live FX 9.9 build 1214, 2026-10-28) and registers them in Settings\JunxionX64.xml.
# The .glsl and .xml are taken from this script's folder (the zip) or from ..\matchbox (the project folder).
#
#   Install IgelkottFisheye.cmd                  double-click
#   powershell -File Install-IgelkottFisheye.ps1 [-Uninstall] [-Quiet] [-Target <folder>]
param([switch]$Uninstall, [switch]$Quiet, [string]$Target)

$ErrorActionPreference = 'Stop'
$Title = 'IgelkottFisheye for Live FX'
$Files = @('IgelkottFisheye2D.glsl', 'IgelkottFisheye2D.xml')

function Say([string]$Text, [string]$Icon = 'Information') {
    if ($Quiet) { Write-Output $Text; return }
    Add-Type -AssemblyName System.Windows.Forms
    [void][System.Windows.Forms.MessageBox]::Show($Text, $Title, 'OK', $Icon)
}

$Assimilator = Join-Path $env:ProgramData 'Assimilator'
if (-not $Target) {
    if (-not (Test-Path $Assimilator)) {
        Say "Live FX was not found ($Assimilator).`n`nInstall Assimilate Live FX and start it once, then run this again." 'Error'
        exit 1
    }
    $Target = Join-Path $Assimilator 'plugin64\Matchbox\shaders'
}

# The node files: next to this script in the zip, or in ..\matchbox in the project folder
$Source = $PSScriptRoot
if (-not (Test-Path (Join-Path $Source $Files[0]))) { $Source = Join-Path (Split-Path $PSScriptRoot -Parent) 'matchbox' }
if (-not $Uninstall) {
    foreach ($f in $Files) {
        if (-not (Test-Path (Join-Path $Source $f))) {
            Say "$f is missing next to this installer. Unpack the whole zip and run it again." 'Error'
            exit 1
        }
    }
}

$Running = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(Assimilator|Assimilate|LiveFX|Scratch)' })

function Copy-Or-Remove {
    if ($Uninstall) {
        foreach ($f in $Files) { Remove-Item -LiteralPath (Join-Path $Target $f) -Force -ErrorAction SilentlyContinue }
        foreach ($f in $Files) { if (Test-Path (Join-Path $Target $f)) { throw "could not remove $f" } }
    } else {
        New-Item -ItemType Directory -Force -Path $Target | Out-Null
        foreach ($f in $Files) { Copy-Item -LiteralPath (Join-Path $Source $f) -Destination $Target -Force }
    }
}

# Same files already there: nothing to do
$Changed = $true
if (-not $Uninstall) {
    $Changed = $false
    foreach ($f in $Files) {
        $dst = Join-Path $Target $f
        if (-not (Test-Path $dst) -or (Get-FileHash (Join-Path $Source $f)).Hash -ne (Get-FileHash $dst).Hash) { $Changed = $true }
    }
}

if ($Changed) {
    try {
        Copy-Or-Remove
    } catch {
        # The Matchbox folder is not writable for this account: ask for administrator rights once
        if ($env:IGELKOTT_ELEVATED) { Say "Could not write to $Target.`n`n$($_.Exception.Message)" 'Error'; exit 1 }
        $psArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-Target', "`"$Target`"")
        if ($Uninstall) { $psArgs += '-Uninstall' }
        if ($Quiet) { $psArgs += '-Quiet' }
        $env:IGELKOTT_ELEVATED = '1'
        try {
            $p = Start-Process powershell -Verb RunAs -ArgumentList $psArgs -Wait -PassThru
            exit $p.ExitCode
        } catch {
            Say "Administrator rights are needed to write to $Target, and they were not given." 'Error'
            exit 1
        }
    }
}

$Version = ''
$verFile = Join-Path (Split-Path $PSScriptRoot -Parent) 'VERSION'
if (Test-Path (Join-Path $PSScriptRoot 'VERSION')) { $verFile = Join-Path $PSScriptRoot 'VERSION' }
if (Test-Path $verFile) { $Version = ' ' + (Get-Content $verFile -TotalCount 1).Trim() }

$Restart = if ($Running.Count -gt 0) { "`n`nLive FX is running: quit it and start it again." } else { "`n`nStart Live FX." }
if ($Uninstall) {
    Say "IgelkottFisheye was removed from`n$Target$Restart"
} elseif ($Changed) {
    Say "IgelkottFisheye$Version is installed in`n$Target$Restart`n`nThe node is under Plug-ins.. > Matchbox > shaders > IgelkottFisheye2D."
} else {
    Say "IgelkottFisheye$Version is already installed in`n$Target`n`nNothing to do."
}
exit 0
