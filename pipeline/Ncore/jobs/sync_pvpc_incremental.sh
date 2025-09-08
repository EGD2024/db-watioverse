#!/usr/bin/env bash
# Sincroniza PVPC horario (últimos 30 días) desde db_sistema_electrico → db_Ncore
set -euo pipefail
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SQL_FILE="${ROOT_DIR}/sql/sync_pvpc_incremental.sql"

psql -U postgres -d db_Ncore -f "${SQL_FILE}"
echo "[OK] PVPC horario (30d) sincronizado en db_Ncore.core_precios_omie"
