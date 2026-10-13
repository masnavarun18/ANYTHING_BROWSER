"""
ANYTHING BROWSER - Windows Installer Generator
Generates an automated Windows Setup Installer script and uninstaller.
"""

import os
import sys


def generate_installer_scripts():
    installer_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(installer_dir)
    dist_app_dir = os.path.join(root_dir, "dist", "AnythingBrowser")

    # 1. PowerShell Install Script (install.ps1)
    install_ps1_content = """# ANYTHING BROWSER Windows Installer Script
param(
    [string]$InstallDir = "$env:LOCALAPPDATA\\Programs\\AnythingBrowser"
)

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Installing ANYTHING BROWSER... " -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan

# Source files directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceDir = Join-Path (Split-Path -Parent $ScriptDir) "dist\\AnythingBrowser"

if (-not (Test-Path $SourceDir)) {
    Write-Error "Build output not found at $SourceDir. Please run build.py first."
    exit 1
}

# Create Target Directory
Write-Host "Installing application to $InstallDir ..." -ForegroundColor Yellow
if (Test-Path $InstallDir) {
    Remove-Item -Path $InstallDir -Recurse -Force
}
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

# Copy Files
Copy-Item -Path "$SourceDir\\*" -Destination $InstallDir -Recurse -Force

$ExePath = Join-Path $InstallDir "AnythingBrowser.exe"

# Unblock Exe for Smart App Control / Defender
Unblock-File -Path $ExePath -ErrorAction SilentlyContinue

# Locate Python Executable for trusted execution
$PythonwPath = "C:\\Users\\masna\\AppData\\Local\\Programs\\Python\\Python312\\pythonw.exe"
$MainPyPath = "C:\\ANYTHING\\src\\main.py"
$IconPath = "C:\\ANYTHING\\assets\\logo.ico"

# Create Desktop Shortcut
$WScriptShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath("Desktop")
$DesktopShortcut = $WScriptShell.CreateShortcut("$DesktopPath\\ANYTHING BROWSER.lnk")

if (Test-Path $PythonwPath) {
    $DesktopShortcut.TargetPath = $PythonwPath
    $DesktopShortcut.Arguments = "`"$MainPyPath`""
    $DesktopShortcut.WorkingDirectory = "C:\\ANYTHING"
} else {
    $DesktopShortcut.TargetPath = $ExePath
    $DesktopShortcut.WorkingDirectory = $InstallDir
}

if (Test-Path $IconPath) {
    $DesktopShortcut.IconLocation = "$IconPath,0"
}

$DesktopShortcut.Description = "ANYTHING BROWSER Desktop Web Browser"
$DesktopShortcut.Save()

# Create Start Menu Shortcut
$StartMenuPath = [System.Environment]::GetFolderPath("StartMenu")
$ProgramGroup = Join-Path $StartMenuPath "Programs\\ANYTHING BROWSER"
New-Item -ItemType Directory -Path $ProgramGroup -Force | Out-Null
$StartShortcut = $WScriptShell.CreateShortcut("$ProgramGroup\\ANYTHING BROWSER.lnk")

if (Test-Path $PythonwPath) {
    $StartShortcut.TargetPath = $PythonwPath
    $StartShortcut.Arguments = "`"$MainPyPath`""
    $StartShortcut.WorkingDirectory = "C:\\ANYTHING"
} else {
    $StartShortcut.TargetPath = $ExePath
    $StartShortcut.WorkingDirectory = $InstallDir
}

if (Test-Path $IconPath) {
    $StartShortcut.IconLocation = "$IconPath,0"
}

$StartShortcut.Description = "ANYTHING BROWSER Desktop Web Browser"
$StartShortcut.Save()

# Create Uninstaller Script
$UninstallPs1 = Join-Path $InstallDir "uninstall.ps1"
$UninstallScriptContent = @"
`$InstallDir = "$InstallDir"
`$DesktopPath = [System.Environment]::GetFolderPath("Desktop")
`$StartMenuPath = [System.Environment]::GetFolderPath("StartMenu")

Write-Host "Uninstalling ANYTHING BROWSER..." -ForegroundColor Yellow

# Remove Shortcuts
Remove-Item -Path "`$DesktopPath\\ANYTHING BROWSER.lnk" -ErrorAction SilentlyContinue
Remove-Item -Path "`$StartMenuPath\\Programs\\ANYTHING BROWSER" -Recurse -ErrorAction SilentlyContinue

# Remove Files
if (Test-Path `$InstallDir) {
    Remove-Item -Path `$InstallDir -Recurse -Force
}

Write-Host "ANYTHING BROWSER uninstalled successfully." -ForegroundColor Green
"@
Set-Content -Path $UninstallPs1 -Value $UninstallScriptContent

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " ANYTHING BROWSER Installed Successfully! " -ForegroundColor Green
Write-Host " Shortcuts created on Desktop and Start Menu. " -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Cyan
"""

    install_ps1_path = os.path.join(installer_dir, "install.ps1")
    with open(install_ps1_path, "w", encoding="utf-8") as f:
        f.write(install_ps1_content)

    # 2. Batch Wrapper (Setup_AnythingBrowser.bat)
    setup_bat_content = """@echo off
title Installing ANYTHING BROWSER...
powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"
pause
"""
    setup_bat_path = os.path.join(installer_dir, "Setup_AnythingBrowser.bat")
    with open(setup_bat_path, "w", encoding="utf-8") as f:
        f.write(setup_bat_content)

    print("==================================================")
    print("Windows Installer Package Scripts Generated:")
    print(f"1. PowerShell Setup Script: {install_ps1_path}")
    print(f"2. Windows Batch Installer: {setup_bat_path}")
    print("==================================================")


if __name__ == "__main__":
    generate_installer_scripts()
