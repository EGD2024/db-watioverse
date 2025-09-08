#!/bin/bash
# Script de instalación de jobs programados para Pipeline Ncore
# Ejecutar con: bash install_cron.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Obtener ruta absoluta del proyecto
DB_PATH="$(cd "$(dirname "$0")/../../.." && pwd)"

echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   INSTALADOR DE JOBS PROGRAMADOS - PIPELINE NCORE${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Ruta del proyecto:${NC} $DB_PATH"
echo ""

# Verificar que existe el venv
if [ ! -d "$DB_PATH/venv" ]; then
    echo -e "${RED}❌ No se encuentra el entorno virtual en $DB_PATH/venv${NC}"
    echo "   Créalo con: python3 -m venv $DB_PATH/venv"
    exit 1
fi

# Crear directorio de logs si no existe
mkdir -p "$DB_PATH/logs"
echo -e "${GREEN}✅ Directorio de logs creado/verificado${NC}"

# Crear archivo temporal con las tareas cron
CRON_FILE="/tmp/ncore_cron_$$"
cat > "$CRON_FILE" << EOF
# Pipeline Ncore - Sincronización de datos energéticos
# Instalado: $(date)
# ======================================================

# Variables de entorno
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
DB_PATH=$DB_PATH

# ====== JOBS CRÍTICOS DIARIOS ======

# 1. Actualización PVPC en sistema_electrico (5:30 AM diario)
# Actualiza precios horarios desde OMIE
30 5 * * * cd \$DB_PATH && source venv/bin/activate && python pipeline/Ncore/jobs/update_pvpc_simple.py >> logs/pvpc_update.log 2>&1

# 2. Sincronización completa sistema_electrico → Ncore (6:00 AM diario)
# Sincroniza todos los datos entre bases
0 6 * * * cd \$DB_PATH && source venv/bin/activate && python pipeline/Ncore/jobs/sync_all_to_ncore.py >> logs/sync_all.log 2>&1

# ====== JOBS DE ACTUALIZACIÓN FRECUENTE ======

# 3. REE Mix generación y CO2 (cada hora a los 20 minutos)
# Descarga mix de generación y emisiones CO2 desde REE
20 * * * * cd \$DB_PATH && source venv/bin/activate && python pipeline/Ncore/jobs/fetch_ree_mix_co2.py >> logs/ree_mix.log 2>&1

# 4. PVPC incremental rápido (cada 30 minutos)
# Mantiene core_precios_omie actualizado con últimos 2 días
*/30 * * * * cd \$DB_PATH && source venv/bin/activate && python pipeline/Ncore/jobs/backfill_pvpc_to_ncore.py --start \$(date -d "2 days ago" +\%Y-\%m-\%d) --step-days 2 >> logs/pvpc_incremental.log 2>&1 2>/dev/null

# ====== JOBS SEMANALES ======

# 5. BOE regulado (domingos 3:00 AM)
# Sincroniza cambios en precios regulados BOE
0 3 * * 0 cd \$DB_PATH && source venv/bin/activate && python pipeline/Ncore/jobs/sync_boe_to_ncore.py >> logs/boe_sync.log 2>&1

# ====== MANTENIMIENTO ======

# 6. Limpieza de logs antiguos (primer día del mes a medianoche)
# Elimina logs de más de 30 días
0 0 1 * * find \$DB_PATH/logs -name "*.log" -mtime +30 -delete

# 7. Verificación de salud del sistema (diario 7:00 AM)
# Envía resumen de sincronización por email o log
0 7 * * * cd \$DB_PATH && source venv/bin/activate && python -c "
import psycopg2
conn = psycopg2.connect(host='localhost', dbname='db_Ncore', user='postgres', password='admin')
cur = conn.cursor()
cur.execute('''
    SELECT 
        'core_precios_omie' as tabla, MAX(timestamp_hora)::text as ultima_fecha
    FROM core_precios_omie
    UNION ALL
    SELECT 'core_precios_omie_diario', MAX(fecha)::text FROM core_precios_omie_diario
    UNION ALL
    SELECT 'core_precio_regulado_boe', MAX(fecha_inicio)::text FROM core_precio_regulado_boe
''')
for row in cur.fetchall():
    print(f'{row[0]}: {row[1]}')
conn.close()
" >> logs/health_check.log 2>&1
EOF

echo -e "${YELLOW}Jobs a instalar:${NC}"
echo "  1. update_pvpc_simple.py      - Diario 5:30 AM"
echo "  2. sync_all_to_ncore.py       - Diario 6:00 AM"
echo "  3. fetch_ree_mix_co2.py       - Cada hora"
echo "  4. backfill_pvpc_to_ncore.py  - Cada 30 minutos"
echo "  5. sync_boe_to_ncore.py       - Semanal (domingos)"
echo "  6. Limpieza logs              - Mensual"
echo "  7. Health check               - Diario 7:00 AM"
echo ""

# Preguntar confirmación
read -p "¿Deseas instalar estos jobs en el crontab? (s/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ss]$ ]]; then
    # Backup del crontab actual
    crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
    echo -e "${GREEN}✅ Backup del crontab actual guardado${NC}"
    
    # Obtener crontab actual sin los jobs de Ncore
    crontab -l 2>/dev/null | grep -v "Pipeline Ncore" | grep -v "DB_PATH=$DB_PATH" > /tmp/current_cron || true
    
    # Añadir nuevos jobs
    cat /tmp/current_cron "$CRON_FILE" | crontab -
    
    echo -e "${GREEN}✅ Jobs instalados correctamente${NC}"
    echo ""
    echo -e "${YELLOW}Verificación:${NC}"
    echo "Para ver los jobs instalados: crontab -l | grep -A20 'Pipeline Ncore'"
    echo "Para ver los logs: tail -f $DB_PATH/logs/*.log"
    echo ""
    echo -e "${GREEN}✅ INSTALACIÓN COMPLETA${NC}"
else
    echo -e "${RED}Instalación cancelada${NC}"
fi

# Limpiar
rm -f "$CRON_FILE"
