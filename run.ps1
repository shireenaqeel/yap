# Yap launcher — hamesha project ke .venv Python se chalata hai,
# taake plotly/Streamlit sahi environment se import ho (global Python313 nahi).

$ErrorActionPreference = "Stop"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: .venv nahi mila ($venvPython)." -ForegroundColor Red
    Write-Host "Pehle banayein:  python -m venv .venv ; .venv\Scripts\python.exe -m pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Port 8502 matches the local Google OAuth redirect_uri in secrets.toml. This
# lives here (not in config.toml) so the committed config stays default-port,
# which is what Hugging Face Spaces expects when it serves the app.
& $venvPython -m streamlit run (Join-Path $PSScriptRoot "app.py") --server.port 8502 @args
