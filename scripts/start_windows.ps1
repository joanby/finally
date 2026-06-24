# Inicia FinAlly en Docker (Windows PowerShell). Idempotente.
# Uso: .\scripts\start_windows.ps1 [-Build]
param([switch]$Build)
$ErrorActionPreference = "Stop"

$Image = "finally"
$Container = "finally"
$Port = 8000

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

# Construye la imagen si no existe o si se pide -Build.
docker image inspect $Image > $null 2>&1
if ($Build -or $LASTEXITCODE -ne 0) {
    Write-Host "Construyendo imagen '$Image'..."
    docker build -t $Image .
}

# Elimina contenedor previo si existe (re-ejecución segura).
$existing = docker ps -aq -f "name=^$Container$"
if ($existing) {
    Write-Host "Eliminando contenedor previo '$Container'..."
    docker rm -f $Container | Out-Null
}

New-Item -ItemType Directory -Force -Path (Join-Path $Root "db") | Out-Null

$envArgs = @()
if (Test-Path (Join-Path $Root ".env")) {
    $envArgs = @("--env-file", (Join-Path $Root ".env"))
}

Write-Host "Arrancando contenedor '$Container'..."
docker run -d `
    --name $Container `
    -p "${Port}:8000" `
    -v "${Root}/db:/app/db" `
    @envArgs `
    $Image | Out-Null

Write-Host "FinAlly disponible en http://localhost:$Port"
