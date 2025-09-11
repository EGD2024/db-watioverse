# Agregados Diarios y Eventos Sociales ESIOS

Sistema automático de procesamiento de datos ESIOS para generar agregados diarios y detectar eventos destacados para redes sociales.

## Componentes

### 1. Agregados Diarios (`esios_agregados_diarios.py`)
Procesa datos horarios para crear resúmenes diarios automáticos.

**Agregados generados:**
- **PVPC diario:** promedio, mínimo, máximo desde indicador 1001
- **Mix energético:** renovable/no renovable, porcentajes desde 1433/1434
- **Emisiones CO2:** promedio diario desde indicador 1739
- **Demanda:** máximo y promedio diario desde indicador 1293
- **Resumen consolidado:** todos los agregados para RRSS

**Uso:**
```bash
python esios_agregados_diarios.py <comando> [fecha_inicio] [fecha_fin]

# Comandos individuales
python esios_agregados_diarios.py pvpc              # Solo PVPC
python esios_agregados_diarios.py mix               # Solo mix energético
python esios_agregados_diarios.py emisiones         # Solo emisiones
python esios_agregados_diarios.py demanda           # Solo demanda
python esios_agregados_diarios.py resumen           # Solo resumen consolidado

# Comando completo
python esios_agregados_diarios.py completo          # Todos los agregados
python esios_agregados_diarios.py completo 2025-01-01 2025-01-07
```

### 2. Eventos Sociales (`esios_eventos_sociales.py`)
Detecta automáticamente eventos destacados para contenido de redes sociales.

**Tipos de eventos detectados:**
- **Récords PVPC:** máximos/mínimos históricos con contexto
- **Récords renovables:** porcentajes máximos de generación verde
- **Anomalías emisiones:** días muy limpios (P10) o muy sucios (P90)
- **Picos demanda:** demandas > 2 desviaciones estándar vs promedio

**Uso:**
```bash
python esios_eventos_sociales.py <comando> [dias_analisis]

# Comandos individuales
python esios_eventos_sociales.py records-pvpc 30        # Récords PVPC últimos 30 días
python esios_eventos_sociales.py records-renovables     # Récords renovables
python esios_eventos_sociales.py anomalias-emisiones    # Días muy limpios/sucios
python esios_eventos_sociales.py picos-demanda          # Picos demanda significativos

# Comando completo
python esios_eventos_sociales.py completo               # Todos los eventos
```

### 3. Pipeline Completo (`esios_pipeline_completo.py`)
Orquestador que ejecuta: Ingesta → Agregados → Eventos en secuencia.

**Modos disponibles:**
- **Prioritarios:** indicadores críticos PVPC (1001,1002,600,601,1900,1901)
- **Completo:** todos los indicadores activos del catálogo

**Uso:**
```bash
python esios_pipeline_completo.py <modo> [fecha_inicio] [fecha_fin]

# Pipeline prioritario (rápido)
python esios_pipeline_completo.py prioritarios

# Pipeline completo (lento)
python esios_pipeline_completo.py completo
python esios_pipeline_completo.py completo 2025-01-01 2025-01-07
```

## Ejemplos de Eventos Generados

### Récords PVPC
```
🔥 RÉCORD HISTÓRICO: PVPC alcanza 245.67 €/MWh, superando el anterior máximo de 198.45 €/MWh
📉 MÍNIMO HISTÓRICO: PVPC baja a 12.34 €/MWh, por debajo del anterior mínimo de 18.90 €/MWh
```

### Récords Renovables
```
🌱 RÉCORD VERDE: 78.5% de generación renovable, superando el anterior récord de 72.1%
```

### Anomalías Emisiones
```
🌿 DÍA MUY LIMPIO: Solo 89 gCO2/kWh (promedio: 156 gCO2/kWh)
⚠️ DÍA CON ALTAS EMISIONES: 287 gCO2/kWh (promedio: 156 gCO2/kWh)
```

### Picos Demanda
```
⚡ PICO DE DEMANDA: 42,150 MW (+15.2% vs promedio)
```

## Integración con Scheduler

### Horarios automáticos recomendados
```python
# En esios_scheduler.py - agregar estos jobs:

# Agregados diarios a las 07:00
schedule.every().day.at("07:00").do(lambda: os.system("python esios_agregados_diarios.py completo"))

# Eventos sociales a las 08:00 (después de agregados)
schedule.every().day.at("08:00").do(lambda: os.system("python esios_eventos_sociales.py completo"))

# Pipeline completo prioritarios a las 06:30
schedule.every().day.at("06:30").do(lambda: os.system("python esios_pipeline_completo.py prioritarios"))
```

## Consultas SQL Útiles

### Ver agregados recientes
```sql
-- Resumen últimos 7 días
SELECT * FROM core_esios_resumen_diario 
WHERE dia >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY dia DESC;

-- PVPC últimos 30 días con tendencia
SELECT dia, pvpc_medio_kwh,
       LAG(pvpc_medio_kwh) OVER (ORDER BY dia) as pvpc_anterior,
       pvpc_medio_kwh - LAG(pvpc_medio_kwh) OVER (ORDER BY dia) as variacion
FROM core_esios_pvpc_diario 
WHERE dia >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY dia DESC;
```

### Ver eventos sociales
```sql
-- Eventos últimos 30 días por tipo
SELECT tipo, COUNT(*) as cantidad, MIN(dia) as desde, MAX(dia) as hasta
FROM core_esios_evento_social 
WHERE dia >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY tipo
ORDER BY cantidad DESC;

-- Eventos destacados recientes
SELECT dia, tipo, descripcion, valor, unidad
FROM core_esios_evento_social 
WHERE dia >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY dia DESC, created_at DESC;
```

## Arquitectura de Datos

### Flujo completo
```
Datos horarios → Agregados diarios → Eventos sociales → Contenido RRSS
     ↓                    ↓                  ↓              ↓
core_esios_valor_horario → core_esios_*_diario → core_esios_evento_social → APIs/Webhooks
```

### Tablas de agregados
- `core_esios_pvpc_diario` - Agregados PVPC por día
- `core_esios_mix_diario` - Mix renovable/no renovable por día  
- `core_esios_emisiones_diario` - Emisiones CO2 promedio por día
- `core_esios_demanda_diario` - Demanda máxima/media por día
- `core_esios_resumen_diario` - Consolidado para RRSS

### Tabla de eventos
- `core_esios_evento_social` - Eventos destacados con metadatos JSON

## Próximos pasos

1. **Webhooks automáticos** para notificar eventos a Slack/Discord
2. **Templates de contenido** para diferentes redes sociales
3. **Dashboard Grafana** con métricas de agregados
4. **Alertas por email** para récords críticos
5. **API REST** para consultar eventos desde aplicaciones externas
