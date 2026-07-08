$projectRoot = Split-Path -Parent $PSScriptRoot
$envRoot = Split-Path -Parent $projectRoot

Write-Host "[0/5] Activating venv..." -ForegroundColor Cyan
& "$projectRoot\venv\Scripts\Activate.ps1"

Write-Host "[1/5] Stopping AgentWorkbench..." -ForegroundColor Cyan
Stop-Process -Name "AgentWorkbenchV6" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "AgentWorkbench" -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500

Write-Host "[2/5] Cleaning .dist / .dist/build..." -ForegroundColor Cyan
Remove-Item -Recurse -Force -Path "$envRoot\.dist\AgentWorkbenchV6", "$envRoot\.dist\build" -ErrorAction SilentlyContinue

Write-Host "[3/5] Running PyInstaller in venv..." -ForegroundColor Cyan
Set-Location $projectRoot
python -m PyInstaller agent_workbench.spec --noconfirm --distpath "$envRoot\.dist" --workpath "$envRoot\.dist\build"

if ($LASTEXITCODE -eq 0) {
    $exeSingle = "$envRoot\.dist\AgentWorkbenchV6.exe"
    $exeDir = "$envRoot\.dist\AgentWorkbenchV6\AgentWorkbenchV6.exe"
    if (Test-Path $exeSingle) {
        $exePath = $exeSingle
        $workDir = "$envRoot\.dist"
    } elseif (Test-Path $exeDir) {
        $exePath = $exeDir
        $workDir = "$envRoot\.dist\AgentWorkbenchV6"
    } else {
        Write-Host "[4/5] Build OK, but could not locate executable." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "[4/5] Build OK: $exePath" -ForegroundColor Green

    Write-Host "[5/5] Refreshing desktop shortcut..." -ForegroundColor Cyan
    $reg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
    $desktop = (Get-ItemProperty -Path $reg -Name "Desktop").Desktop
    $linkPath = Join-Path $desktop "AI Agent Workbench V6.lnk"
    $icoPath = Join-Path $projectRoot "assets\app.ico"

    $WScriptShell = New-Object -ComObject WScript.Shell
    $shortcut = $WScriptShell.CreateShortcut($linkPath)
    $shortcut.TargetPath = $exePath
    $shortcut.WorkingDirectory = $workDir
    $shortcut.IconLocation = "$icoPath,0"
    $shortcut.Description = "AI Agent Workbench V6"
    $shortcut.Save()

    Write-Host "       Desktop: $linkPath" -ForegroundColor Green
    Write-Host "[5/5] Done." -ForegroundColor Green
} else {
    Write-Host "[4/5] Build failed." -ForegroundColor Red
}
