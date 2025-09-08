#!/usr/bin/env bash
# Sincroniza calendario horario (últimos 14 días) desde db_sistema_electrico → db_Ncore
set -euo pipefail
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SQL_FILE="${ROOT_DIR}/sql/sync_calendario_incremental.sql"

psql -U postgres -d db_Ncore -f "${SQL_FILE}"
echo "[OK] Calendario horario (14d) sincronizado en db_Ncore.core_calendario_horario"
