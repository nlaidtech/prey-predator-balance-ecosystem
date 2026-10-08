# PowerShell launcher for Predator-Prey Balance Ecosystem
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$pythonExe = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"

if (-not (Test-Path $pythonExe)) {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $pythonExe = "python"
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        $pythonExe = "py"
    } else {
        Write-Error "Python was not found. Please install Python 3.10+."
        exit 1
    }
}

Write-Host "Launching Predator-Prey Wildlife Ecosystem Simulation using: $pythonExe" -ForegroundColor Cyan
& $pythonExe main.py
