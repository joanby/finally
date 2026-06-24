# Detiene y elimina el contenedor FinAlly (Windows PowerShell). NO borra el volumen db/.
$ErrorActionPreference = "Stop"

$Container = "finally"

$existing = docker ps -aq -f "name=^$Container$"
if ($existing) {
    Write-Host "Deteniendo y eliminando '$Container'..."
    docker rm -f $Container | Out-Null
    Write-Host "Hecho. Los datos en db/ se conservan."
} else {
    Write-Host "No hay contenedor '$Container' en ejecución."
}
