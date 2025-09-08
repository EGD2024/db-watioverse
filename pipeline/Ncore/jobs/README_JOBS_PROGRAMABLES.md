# Jobs Programables - Pipeline Ncore

## Scripts para Programación Periódica (Cron)

### 1. **sync_all_to_ncore.py** - DIARIO
**Frecuencia recomendada**: Diario a las 06:00 AM  
**Comando cron**: `0 6 * * * cd /path/to/db_watioverse && source venv/bin/activate && python pipeline/Ncore/jobs/sync_all_to_ncore.py`  
**Función**: Sincronización completa incremental de todos los datos

### 2. **update_pvpc_simple.py** - DIARIO  
**Frecuencia recomendada**: Diario a las 05:30 AM (antes del sync general)  
**Comando cron**: `30 5 * * * cd /path/to/db_watioverse && source venv/bin/activate && python pipeline/Ncore/jobs/update_pvpc_simple.py`  
**Función**: Actualiza precios_horarios_pvpc en db_sistema_electrico desde OMIE

### 3. **fetch_ree_mix_co2.py** - HORARIO
**Frecuencia recomendada**: Cada hora a los 20 minutos  
**Comando cron**: `20 * * * * cd /path/to/db_watioverse && source venv/bin/activate && python pipeline/Ncore/jobs/fetch_ree_mix_co2.py`  
**Función**: Descarga mix de generación y emisiones CO2 desde REE

### 4. **backfill_pvpc_to_ncore.py** - HORARIO (Incremental)
**Frecuencia recomendada**: Cada 30 minutos  
**Comando cron**: `*/30 * * * * cd /path/to/db_watioverse && source venv/bin/activate && python pipeline/Ncore/jobs/backfill_pvpc_to_ncore.py --start $(date -d "2 days ago" +\%Y-\%m-\%d) --step-days 2`  
**Función**: Mantiene core_precios_omie al día con últimos 2 días

### 5. **sync_boe_to_ncore.py** - SEMANAL
**Frecuencia recomendada**: Domingos a las 03:00 AM  
**Comando cron**: `0 3 * * 0 cd /path/to/db_watioverse && source venv/bin/activate && python pipeline/Ncore/jobs/sync_boe_to_ncore.py`  
**Función**: Sincroniza cambios en precios regulados BOE

## Scripts de Backfill (Ejecución Manual o Mensual)

### backfill_pvpc_to_ncore.py --full
**Uso**: Recuperación de histórico completo  
**Comando**: `python backfill_pvpc_to_ncore.py --start 2020-01-01 --step-days 30`

### sync_all_to_ncore.py --full  
**Uso**: Sincronización completa de todo el histórico  
**Comando**: `python sync_all_to_ncore.py --full`

## Archivo Crontab Ejemplo

```bash
# Pipeline Ncore - Sincronización de datos energéticos
# ======================================================

# Variables de entorno
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
DB_PATH=/Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse

# Actualización PVPC en sistema_electrico (5:30 AM diario)
30 5 * * * cd $DB_PATH && source venv/bin/activate && python pipeline/Ncore/jobs/update_pvpc_simple.py >> logs/pvpc_update.log 2>&1

# Sincronización completa sistema_electrico → Ncore (6:00 AM diario)
0 6 * * * cd $DB_PATH && source venv/bin/activate && python pipeline/Ncore/jobs/sync_all_to_ncore.py >> logs/sync_all.log 2>&1

# REE Mix/CO2 (cada hora a los 20 minutos)
20 * * * * cd $DB_PATH && source venv/bin/activate && python pipeline/Ncore/jobs/fetch_ree_mix_co2.py >> logs/ree_mix.log 2>&1

# PVPC incremental rápido (cada 30 minutos)
*/30 * * * * cd $DB_PATH && source venv/bin/activate && python pipeline/Ncore/jobs/backfill_pvpc_to_ncore.py --start $(date -d "2 days ago" +\%Y-\%m-\%d) --step-days 2 >> logs/pvpc_incremental.log 2>&1

# BOE regulado (domingos 3:00 AM)
0 3 * * 0 cd $DB_PATH && source venv/bin/activate && python pipeline/Ncore/jobs/sync_boe_to_ncore.py >> logs/boe_sync.log 2>&1

# Limpieza de logs (primer día del mes)
0 0 1 * * find $DB_PATH/logs -name "*.log" -mtime +30 -delete
```

## Instalación del Crontab

1. Crear directorio de logs:
```bash
mkdir -p /Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/logs
```

2. Editar crontab del usuario:
```bash
crontab -e
```

3. Pegar el contenido del archivo crontab ejemplo

4. Verificar que está instalado:
```bash
crontab -l
```

## Monitoreo

Para verificar el estado de las sincronizaciones:
```bash
# Ver últimas ejecuciones
tail -f logs/sync_all.log

# Verificar sincronización en BD
psql -d db_Ncore -c "SELECT tabla, MAX(fecha) FROM (
  SELECT 'core_precios_omie' as tabla, MAX(timestamp_hora)::date as fecha FROM core_precios_omie
  UNION ALL
  SELECT 'core_precios_omie_diario', MAX(fecha) FROM core_precios_omie_diario
  UNION ALL  
  SELECT 'core_precio_regulado_boe', MAX(fecha_inicio) FROM core_precio_regulado_boe
) t GROUP BY tabla;"
```

## Notas Importantes

1. **update_pvpc_simple.py** debe ejecutarse ANTES que el sync general para que los datos estén disponibles
2. **fetch_ree_mix_co2.py** puede ejecutarse cada hora ya que REE actualiza datos horarios
3. **backfill_pvpc_to_ncore.py** con ventana de 2 días garantiza que no se pierdan datos por retrasos
4. Los logs deben limpiarse periódicamente para evitar llenar el disco
5. Ajustar rutas según tu instalación real
