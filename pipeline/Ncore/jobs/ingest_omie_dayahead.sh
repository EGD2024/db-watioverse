#!/usr/bin/env bash
# Ingesta diaria de precios OMIE para el día siguiente (day-ahead) en db_sistema_electrico
# Publicación estimada: ~16:30. Este job se programa a las 16:35.
# Requiere: entorno virtual creado en .venv_omie con 'requests' instalado.
set -euo pipefail
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_BIN="${ROOT_DIR}/jobs/.venv_omie/bin/python"
BACKFILL_PY="${ROOT_DIR}/jobs/backfill_omie_from_ree.py"

# Obtener la fecha de mañana (macOS/BSD date). Para Linux, ajustar a: date -d "tomorrow" +%F
TOMORROW=$(date -v+1d +%F)

"${VENV_BIN}" "${BACKFILL_PY}" --start "${TOMORROW}" --end "${TOMORROW}"

echo "[OK] Ingerido OMIE day-ahead para ${TOMORROW} en db_sistema_electrico.omie_precios"
