#!/usr/bin/env bash
# Monitoriza OMIE day-ahead: verifica 24h en origen y agregado en Ncore
set -euo pipefail
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

/usr/bin/env python3 "${SCRIPT_DIR}/monitor_omie_dayahead.py"
