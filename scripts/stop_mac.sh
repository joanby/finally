#!/usr/bin/env bash
# Detiene y elimina el contenedor FinAlly (macOS/Linux). NO borra el volumen db/.
set -euo pipefail

CONTAINER="finally"

if docker ps -aq -f name="^${CONTAINER}$" | grep -q .; then
  echo "Deteniendo y eliminando '$CONTAINER'..."
  docker rm -f "$CONTAINER" >/dev/null
  echo "Hecho. Los datos en db/ se conservan."
else
  echo "No hay contenedor '$CONTAINER' en ejecución."
fi
