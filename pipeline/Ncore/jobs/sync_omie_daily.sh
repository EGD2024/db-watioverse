#!/usr/bin/env bash
# Sincroniza precios OMIE diarios desde db_sistema_electrico → db_Ncore
# Requisitos: FDW configurado, f_omie_precios creada, psql en PATH y .pgpass/credenciales válidas
set -euo pipefail
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SQL_FILE="${ROOT_DIR}/sql/sync_omie_daily.sql"

psql -U postgres -d db_Ncore -f "${SQL_FILE}"
echo "[OK] OMIE diario sincronizado en db_Ncore.core_precios_omie_diario"
