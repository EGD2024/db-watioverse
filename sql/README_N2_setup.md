# Configuración de Base de Datos N2 - Datos Enriquecidos

## Descripción

La base de datos **db_N2** almacena los datos enriquecidos del cliente que provienen de N1 más información adicional calculada:

- **Datos geográficos**: coordenadas, municipio, provincia, zona climática
- **Datos climáticos**: temperatura, precipitación, grados día
- **Datos de mercado**: precios OMIE del período
- **KPIs calculados**: eficiencia energética, correlaciones
- **Metadatos**: completitud del enriquecimiento, fuentes de datos

## Flujo de Datos

```
N1 (datos base) → N2 (datos enriquecidos) → N3 (scores calculados)
```

## Tablas Principales

### 1. `facturas_electricidad_enriquecidas`
Tabla principal con facturas enriquecidas con datos geográficos, climáticos y KPIs.

### 2. `coordenadas_geograficas`
Cache de coordenadas geográficas por CUPS para optimizar geocodificación.

### 3. `datos_climaticos_mensuales`
Datos climáticos históricos mensuales por coordenadas geográficas.

### 4. `enrichment_cache`
Cache general de datos de enriquecimiento por CUPS.

### 5. `enrichment_queue`
Cola de procesamiento asíncrono para enriquecimiento de datos.

## Instalación

### Prerrequisitos

1. PostgreSQL 12+ instalado y ejecutándose
2. Usuario con permisos para crear bases de datos
3. Variables de entorno configuradas (ver `.env.example`)

### Paso 1: Configurar Variables de Entorno

Asegúrate de que tu archivo `.env` incluye:

```bash
# Base de datos N2
DB_N2_HOST=localhost
DB_N2_PORT=5432
DB_N2_NAME=db_N2
DB_N2_USER=postgres
DB_N2_PASSWORD=tu_password_aqui
```

### Paso 2: Crear Base de Datos

Primero crear la base de datos db_N2:

```bash
# Crear la base de datos
createdb -h localhost -U postgres db_N2
```

O usando psql:

```bash
psql -h localhost -U postgres -c "CREATE DATABASE db_N2;"
```

### Paso 3: Ejecutar Script de Creación de Tablas

```bash
# Desde el directorio motores/db_watioverse/sql/
psql -h localhost -U postgres -d db_N2 -f create_db_N2_tables.sql
```

O si prefieres ejecutar paso a paso:

```bash
# Conectar directamente a la base de datos N2
psql -h localhost -U postgres -d db_N2

# Ejecutar el script
\i create_db_N2_tables.sql
```

### Paso 4: Verificar Instalación

```sql
-- Conectar a la base de datos N2
\c db_N2

-- Listar tablas creadas
\dt

-- Verificar estructura de tabla principal
\d facturas_electricidad_enriquecidas

-- Verificar índices
\di
```

## Estructura de Datos

### Ejemplo de Registro en `facturas_electricidad_enriquecidas`

```json
{
  "cups_electricidad": "ES0022000008433586LW0F",
  "fecha_procesamiento": "2025-01-07T20:11:50",
  "latitud": 42.2328,
  "longitud": -8.7226,
  "direccion_normalizada": "Rúa Real, 15, 36001 Pontevedra",
  "municipio": "Pontevedra",
  "provincia": "Pontevedra",
  "zona_climatica": "C1",
  "temperatura_media_mes_anterior": 12.5,
  "precipitacion_total_mes_anterior": 145.2,
  "precio_medio_omie_mes_anterior": 85.45,
  "kpis_eficiencia": {
    "eficiencia_energetica_kwh_m2": 45.2,
    "factor_climatico": "alto_consumo_frio",
    "ratio_precio_mercado": 1.25
  },
  "metadata_enriquecimiento": {
    "completitud": true,
    "campos_faltantes": [],
    "fuentes_datos": {
      "geograficos": "google_maps_api",
      "climaticos": "visual_crossing_api",
      "precios_energia": "db_sistema_electrico"
    }
  }
}
```

## Mantenimiento

### Limpieza de Datos Antiguos

```sql
-- Eliminar datos de enriquecimiento antiguos (más de 1 año)
DELETE FROM facturas_electricidad_enriquecidas 
WHERE created_at < NOW() - INTERVAL '1 year';

-- Limpiar cache expirado
DELETE FROM enrichment_cache 
WHERE expires_at < NOW();

-- Limpiar cola de procesamiento completada (más de 30 días)
DELETE FROM enrichment_queue 
WHERE status = 'completed' 
AND completed_at < NOW() - INTERVAL '30 days';
```

### Actualizar Estadísticas

```sql
-- Actualizar estadísticas para optimización
ANALYZE facturas_electricidad_enriquecidas;
ANALYZE coordenadas_geograficas;
ANALYZE datos_climaticos_mensuales;
```

### Monitoreo del Sistema

```sql
-- Verificar estado de la cola de enriquecimiento
SELECT status, COUNT(*) as cantidad
FROM enrichment_queue 
GROUP BY status;

-- Verificar completitud de enriquecimiento
SELECT 
    COUNT(*) as total_facturas,
    COUNT(*) FILTER (WHERE latitud IS NOT NULL) as con_coordenadas,
    COUNT(*) FILTER (WHERE temperatura_media_mes_anterior IS NOT NULL) as con_clima,
    COUNT(*) FILTER (WHERE precio_medio_omie_mes_anterior IS NOT NULL) as con_precios
FROM facturas_electricidad_enriquecidas;
```

## Solución de Problemas

### Error: "database does not exist"
```bash
# Crear la base de datos manualmente
createdb -h localhost -U postgres db_N2
```

### Error: "permission denied"
```bash
# Otorgar permisos al usuario
psql -h localhost -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE db_N2 TO tu_usuario;"
```

### Error: "connection refused"
```bash
# Verificar que PostgreSQL está ejecutándose
sudo systemctl status postgresql
# o en macOS
brew services list | grep postgresql
```

## Integración con Código

El motor de enriquecimiento (`enrichment_engine.py`) usa estas tablas automáticamente:

```python
from motores.motor_mejora.src.enrichment_engine import enrich_single_invoice

# Enriquecer una factura (se guarda automáticamente en N2)
resultado = enrich_single_invoice(
    cups="ES0022000008433586LW0F", 
    fecha_factura="2024-05-12"
)
```

## Seguridad

- Las tablas incluyen triggers automáticos para `updated_at`
- Usuario específico `n2_user` con permisos limitados
- Índices optimizados para consultas frecuentes
- Campos JSONB para flexibilidad en metadatos

## Contacto

Para problemas con la configuración de N2, revisar logs del sistema o consultar la documentación del motor de enriquecimiento.
