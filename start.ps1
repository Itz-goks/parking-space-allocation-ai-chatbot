$ErrorActionPreference = "Stop"

Write-Host "=== Parking Space Allocation AI Chatbot ===" -ForegroundColor Cyan

# Use the Python launcher if available; otherwise use python.
$pythonCmd = Get-Command py -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $python = "py"
    $pythonArgs = @("-3")
} else {
    $python = "python"
    $pythonArgs = @()
}

# Create a local virtual environment.
if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    & $python @pythonArgs -m venv venv
}

$venvPython = (Resolve-Path ".\venv\Scripts\python.exe").Path

Write-Host "Installing/updating required packages..." -ForegroundColor Yellow
& $venvPython -m pip install -r requirements.txt

Write-Host "Starting Streamlit..." -ForegroundColor Green
& $venvPython -m streamlit run app.py
