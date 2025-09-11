# Jobs de Ingesta ESIOS

Sistema de ingesta automática para indicadores ESIOS con versionado y paralelización.

## Componentes

### 1. Job Individual (`esios_ingesta_job.py`)
Ingesta un indicador específico con versionado completo.

**Uso:**
```bash
python esios_ingesta_job.py <indicator_id> [geo_id] [fecha_inicio] [fecha_fin]

# Ejemplos
python esios_ingesta_job.py 1001                    # PVPC últimos 7 días
python esios_ingesta_job.py 1001 8741 2025-01-01 2025-01-07  # Rango específico
```

**Funcionalidades:**
- Registro automático en `core_esios_ingesta_ejecucion`
- UPSERT con `ON CONFLICT` (idempotente)
- Manejo de errores con rollback
- Actualización `ultima_actualizacion` en catálogo
- Normalización temporal UTC

### 2. Job Batch (`esios_batch_ingesta.py`)
Ingesta paralela de múltiples indicadores.

**Uso:**
```bash
python esios_batch_ingesta.py <modo> [fecha_inicio] [fecha_fin]

# Modos
python esios_batch_ingesta.py prioritarios          # Solo críticos PVPC
python esios_batch_ingesta.py completo              # Todos los activos
python esios_batch_ingesta.py completo 2025-01-01 2025-01-07
```

**Indicadores prioritarios:**
- 1001 (PVPC 2.0TD) ★
- 1002 (PVPC 3.0TD)
- 600 (Mercado diario)
- 601 (Intradiario)
- 1900 (Peajes transporte)
- 1901 (Cargos sistema)

### 3. Scheduler Automático (`esios_scheduler.py`)
Ejecución automática con horarios configurables.

**Horarios por defecto:**
- **PVPC (1001):** cada 4 horas (crítico)
- **Prioritarios:** diario 06:00
- **Completo:** domingos 02:00

**Uso:**
```bash
# Ejecutar scheduler
python esios_scheduler.py

# Tests manuales
python esios_scheduler.py test-pvpc
python esios_scheduler.py test-prioritarios
python esios_scheduler.py test-completo
```

## Configuración

### Variables de entorno requeridas
```bash
# API ESIOS
ESIOS_API_TOKEN=tu_token_aqui
ESIOS_BASE_URL=https://api.esios.ree.es/

# Base de datos
DATABASE_URL_NCORE=postgresql://user:pass@host:5432/db_Ncore

# Configuración jobs (opcional)
MAX_CONCURRENT_INDICATORS=3
BATCH_SIZE_HOURS=168
RETRY_ATTEMPTS=3
TIMEOUT_SECONDS=300
```

### Instalación dependencias
```bash
pip install -r requirements_esios.txt
```

## Monitoreo y Logs

### Consultar ejecuciones
```sql
-- Últimas ejecuciones por indicador
SELECT 
    i.indicator_id, i.nombre,
    e.ts_inicio, e.ts_fin, e.estado, e.filas_afectadas, e.mensaje
FROM core_esios_ingesta_ejecucion e
JOIN core_esios_indicador i ON e.indicator_id = i.indicator_id
ORDER BY e.ts_inicio DESC
LIMIT 20;

-- Indicadores con errores recientes
SELECT indicator_id, COUNT(*) as errores
FROM core_esios_ingesta_ejecucion 
WHERE estado = 'error' AND ts_inicio > NOW() - INTERVAL '24 hours'
GROUP BY indicator_id
ORDER BY errores DESC;
```

### Logs del scheduler
- Archivo: `esios_scheduler.log`
- Reportes JSON: `esios_reporte_*.json`

## Arquitectura de Datos

### Flujo de ingesta
```
ESIOS API → esios_ingesta_job → core_esios_valor_horario → vistas v_esios_ind_{ID}
```

### Versionado y trazabilidad
- `core_esios_ingesta_ejecucion`: registro completo de cada job
- `version_fuente`: metadatos de respuesta ESIOS
- `ultima_actualizacion`: timestamp en catálogo de indicadores

### Política sin fallbacks
- Si indicador no está `activo=true` → excepción
- Si falta dato con peso > 0 en eSCORE → excepción (alineado con ESC público)

## Integración con Sistema Eléctrico

### Conexión con db_sistema_electrico
```sql
-- Ejemplo: actualizar PVPC desde ESIOS
INSERT INTO db_sistema_electrico.precios_horarios_pvpc 
SELECT 
    DATE(fecha_hora AT TIME ZONE 'Europe/Madrid') as fecha,
    EXTRACT(HOUR FROM fecha_hora AT TIME ZONE 'Europe/Madrid')::time as hora,
    valor as precio_energia
FROM db_Ncore.v_esios_pvpc_horario
WHERE fecha_hora >= '2025-01-01';
```

### Vistas críticas para simulación
- `v_esios_pvpc_horario` (1001) ★
- `v_esios_mercado_diario` (600)
- `v_esios_peajes_transporte` (1900)
- `v_esios_cargos_sistema` (1901)

## Próximos pasos

1. **Agregados diarios automáticos**
2. **Generador eventos sociales**
3. **Alertas por Slack/email**
4. **Dashboard Grafana**
5. **Backup incremental**
