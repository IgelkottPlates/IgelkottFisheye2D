@echo off
rem Double-click to remove the IgelkottFisheye node from Assimilate Live FX (Windows).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-IgelkottFisheye.ps1" -Uninstall %*
