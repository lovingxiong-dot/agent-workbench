# Stop old process, clean build artifacts, rebuild exe + desktop shortcut
$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "[0/5] Activating venv..." -ForegroundColor Cyan
& "$projectRoot\venv\Scripts\Activate.ps1"

Write-Host "[1/5] Stopping AgentWorkbench..." -ForegroundColor Cyan
Stop-Process -Name "AgentWorkbench" -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500

Write-Host "[2/5] Cleaning dist / build..." -ForegroundColor Cyan
Remove-Item -Recurse -Force -Path "$projectRoot\dist", "$projectRoot\build" -ErrorAction SilentlyContinue

Write-Host "[3/5] Running PyInstaller in venv..." -ForegroundColor Cyan
Set-Location $projectRoot
python -m PyInstaller AgentWorkbenchV5.spec --noconfirm

if ($LASTEXITCODE -eq 0) {
    Write-Host "[4/5] Build OK: $projectRoot\dist\AgentWorkbench\AgentWorkbench.exe" -ForegroundColor Green

    Write-Host "[5/5] Refreshing desktop shortcut..." -ForegroundColor Cyan
    $reg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
    $desktop = (Get-ItemProperty -Path $reg -Name "Desktop").Desktop
    $linkPath = Join-Path $desktop "AI Agent Workbench.lnk"
    $exePath = Join-Path $projectRoot "dist\AgentWorkbench\AgentWorkbench.exe"
    $icoPath = Join-Path $projectRoot "assets\app.ico"
    $workDir = Join-Path $projectRoot "dist\AgentWorkbench"

    $WScriptShell = New-Object -ComObject WScript.Shell
    $shortcut = $WScriptShell.CreateShortcut($linkPath)
    $shortcut.TargetPath = $exePath
    $shortcut.WorkingDirectory = $workDir
    $shortcut.IconLocation = "$icoPath,0"
    $shortcut.Description = "AI Agent Workbench"
    $shortcut.Save()

    Write-Host "       Desktop: $linkPath" -ForegroundColor Green
    Write-Host "[5/5] Done." -ForegroundColor Green
} else {
    Write-Host "[4/5] Build failed." -ForegroundColor Red
}
