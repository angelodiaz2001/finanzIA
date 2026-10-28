# Inicia los tres servicios simulados, el backend principal y el frontend,
# cada uno en su propia ventana de PowerShell. Ejecutar desde cualquier carpeta:
#   powershell -ExecutionPolicy Bypass -File scripts\start_all.ps1

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "No existe .venv. Crea el entorno primero (ver README, sección Instalación)."
    exit 1
}
if (-not (Test-Path (Join-Path $root "frontend\node_modules"))) {
    Write-Warning "frontend\node_modules no existe: ejecuta 'npm install' dentro de frontend antes de usar la interfaz."
}

$services = @(
    @{ Name = "API Bancaria (8001)";       Cmd = "& '$python' -m uvicorn services.bank_api.main:app --port 8001 --reload" },
    @{ Name = "Billetera Digital (8002)";  Cmd = "& '$python' -m uvicorn services.wallet_api.main:app --port 8002 --reload" },
    @{ Name = "Notificaciones (8003)";     Cmd = "& '$python' -m uvicorn services.notifications_api.main:app --port 8003 --reload" },
    @{ Name = "Backend FinanzIA (8000)";   Cmd = "& '$python' -m uvicorn backend.app.main:app --port 8000 --reload" },
    @{ Name = "Frontend (5173)";           Cmd = "Set-Location '$root\frontend'; npm run dev" }
)

foreach ($s in $services) {
    $command = "`$Host.UI.RawUI.WindowTitle = '$($s.Name)'; Set-Location '$root'; $($s.Cmd)"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $command
    Start-Sleep -Milliseconds 400
}

Write-Host ""
Write-Host "Servicios iniciados en ventanas separadas."
Write-Host "  Frontend:          http://localhost:5173"
Write-Host "  Backend (Swagger): http://localhost:8000/docs"
Write-Host "  Banco:             http://localhost:8001/docs"
Write-Host "  Billetera:         http://localhost:8002/docs"
Write-Host "  Notificaciones:    http://localhost:8003/docs"
