#!/usr/bin/env bash
# Inicia FinAlly en Docker (macOS/Linux). Idempotente.
set -euo pipefail

IMAGE="finally"
CONTAINER="finally"
PORT="8000"

# Raíz del repo (un nivel por encima de scripts/).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BUILD=false
[[ "${1:-}" == "--build" ]] && BUILD=true

# Construye la imagen si no existe o si se pide --build.
if $BUILD || ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "Construyendo imagen '$IMAGE'..."
  docker build -t "$IMAGE" .
fi

# Si ya hay un contenedor con ese nombre, lo elimina (re-ejecución segura).
if docker ps -aq -f name="^${CONTAINER}$" | grep -q .; then
  echo "Eliminando contenedor previo '$CONTAINER'..."
  docker rm -f "$CONTAINER" >/dev/null
fi

mkdir -p "$ROOT/db"

ENV_ARGS=()
[[ -f "$ROOT/.env" ]] && ENV_ARGS+=(--env-file "$ROOT/.env")

echo "Arrancando contenedor '$CONTAINER'..."
docker run -d \
  --name "$CONTAINER" \
  -p "${PORT}:8000" \
  -v "$ROOT/db:/app/db" \
  "${ENV_ARGS[@]}" \
  "$IMAGE" >/dev/null

echo "FinAlly disponible en http://localhost:${PORT}"
