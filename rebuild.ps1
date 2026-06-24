# Stop old process, clean build artifacts, and rebuild exe
Write-Host "[0/4] Activating venv..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

Write-Host "[1/4] Stopping AgentWorkbench..." -ForegroundColor Cyan
Stop-Process -Name "AgentWorkbench" -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500

Write-Host "[2/4] Cleaning dist / build..." -ForegroundColor Cyan
Remove-Item -Recurse -Force -Path "dist", "build" -ErrorAction SilentlyContinue

Write-Host "[3/4] Running PyInstaller in venv..." -ForegroundColor Cyan
python -m PyInstaller AgentWorkbench.spec --noconfirm

if ($LASTEXITCODE -eq 0) {
    Write-Host "[4/4] Build OK: .\dist\AgentWorkbench\AgentWorkbench.exe" -ForegroundColor Green
} else {
    Write-Host "[4/4] Build failed." -ForegroundColor Red
}
