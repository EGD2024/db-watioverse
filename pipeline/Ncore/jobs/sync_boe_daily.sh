#!/usr/bin/env bash
# Upsert BOE y recálculo de precios por periodo (P1..P6) en db_Ncore
set -euo pipefail
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SQL_UPSERT="${ROOT_DIR}/sql/sync_boe_upsert.sql"
SQL_RECALC="${ROOT_DIR}/sql/recalc_peajes_periodos.sql"

psql -U postgres -d db_Ncore -f "${SQL_UPSERT}"
psql -U postgres -d db_Ncore -f "${SQL_RECALC}"
echo "[OK] BOE upsert y recálculo P1..P6 completados; mv_tarifas_vigentes refrescada"
