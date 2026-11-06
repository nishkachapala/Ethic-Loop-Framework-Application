Set-Location $PSScriptRoot
Write-Host "========================================================" -ForegroundColor DarkGreen
Write-Host "Starting ETHIC-Loop Framework on http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor DarkGreen

Start-Process "http://127.0.0.1:5000"

if (Test-Path ".\.venv\Scripts\python.exe") {
    & ".\.venv\Scripts\python.exe" app.py
} else {
    python app.py
}
