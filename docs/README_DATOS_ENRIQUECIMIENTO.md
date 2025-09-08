# Datos para Enriquecimiento de Información Energética

## Resumen Ejecutivo

Este documento identifica los campos obligatorios y opcionales necesarios para utilizar las herramientas de enriquecimiento de datos disponibles en el ecosistema:

- **OMIE**: Precios del mercado eléctrico español
- **Nominatim (OSM)**: Geocodificación y datos geográficos  
- **Open‑Meteo (AEMET equivalente)**: Datos meteorológicos históricos
- **PVPC (BOE)**: Precio regulado (peajes/cargos)
- **REE**: Mix eléctrico y factores de emisión CO2

## 1. API OMIE (Precios de Electricidad)

### Propósito
Obtener precios históricos del mercado eléctrico español para análisis de costes energéticos.

### Campos Obligatorios
| Campo | Tipo | Descripción | Origen en JSON N0 |
|-------|------|-------------|-------------------|
| `fecha_inicio_periodo` | DATE | Fecha de inicio del período de facturación | `invoice_2x3.fecha_inicio_periodo` |
| `fecha_fin_periodo` | DATE | Fecha de fin del período de facturación | `invoice_2x3.fecha_fin_periodo` |

### Campos Opcionales
| Campo | Tipo | Descripción | Valor por Defecto |
|-------|------|-------------|-------------------|
| `zona_mercado` | STRING | Zona del mercado (ES, PT) | "ES" |
| `tipo_precio` | STRING | Tipo de precio (spot, futures) | "spot" |

### Datos Enriquecidos Generados
- `precio_medio_kwh`: Precio medio del período (€/kWh)
- `precios_horarios`: Array de precios por hora
- `precio_maximo`: Precio máximo del período
- `precio_minimo`: Precio mínimo del período
- `volatilidad`: Desviación estándar de precios

### Ejemplo de Uso
```python
# Datos de entrada desde JSON N0
fecha_inicio = "2025-04-08"
fecha_fin = "2025-05-07"

# Llamada a OMIE
precio_data = omie_api.obtener_precio_medio(datetime.strptime(fecha_inicio, "%Y-%m-%d"))
```

## 2. Nominatim (OSM) – Geolocalización

### Propósito
Enriquecer direcciones con coordenadas geográficas, información administrativa y datos de ubicación (sin API key).

### Campos Obligatorios
| Campo | Tipo | Descripción | Origen en JSON N0 |
|-------|------|-------------|-------------------|
| `direccion_completa` | STRING | Dirección completa para geocodificar | Concatenación de campos de `supply_point.datos_suministro.direccion_suministro` |
| `codigo_postal` | STRING | Código postal (5 dígitos) | `supply_point.datos_suministro.direccion_suministro.codigo_postal` |

### Composición de Dirección Completa
```
{tipo_via} {nombre_via} {numero}, {planta} {puerta}
{codigo_postal} {poblacion}, {provincia}
{pais}
```

### Ejemplo de Dirección desde JSON N0
```
DO CAMIÑO DE FERRO 6, 6 A
36003 Pontevedra, Pontevedra
España
```

### Campos Opcionales
| Campo | Tipo | Descripción | Valor por Defecto |
|-------|------|-------------|-------------------|
| `pais` | STRING | País de la dirección | "España" |
| `idioma` | STRING | Idioma de respuesta | "es" |

### Datos Enriquecidos Generados
- `latitud`: Coordenada latitud (decimal)
- `longitud`: Coordenada longitud (decimal)
- `direccion_normalizada`: Display name OSM
- `osm_class` / `osm_type` / `importance`
- `tipo_ubicacion`: Inferido de OSM
- `zona_climatica`: Zona climática CTE (por coordenadas)
- `altitud_msnm`: Altitud sobre el nivel del mar (si disponible)

### Ejemplo de Uso
```python
# Datos de entrada desde JSON N0
direccion = f"{supply_point['datos_suministro']['direccion_suministro']['tipo_via']} {supply_point['datos_suministro']['direccion_suministro']['nombre_via']} {supply_point['datos_suministro']['direccion_suministro']['numero']}"
cp = supply_point['datos_suministro']['direccion_suministro']['codigo_postal']

# Llamada a Nominatim
geo_data = nominatim_api.search(direccion, cp)
```

## 3. AEMET API (Datos Meteorológicos)

### Propósito
Obtener datos meteorológicos históricos para análisis de eficiencia energética y patrones de consumo.

### Campos Obligatorios
| Campo | Tipo | Descripción | Origen en JSON N0 |
|-------|------|-------------|-------------------|
| `codigo_postal` | STRING | Código postal (5 dígitos) | `supply_point.datos_suministro.direccion_suministro.codigo_postal` |
| `fecha_inicio_periodo` | DATE | Fecha de inicio del período | `invoice_2x3.fecha_inicio_periodo` |
| `fecha_fin_periodo` | DATE | Fecha de fin del período | `invoice_2x3.fecha_fin_periodo` |

### Campos Opcionales
| Campo | Tipo | Descripción | Valor por Defecto |
|-------|------|-------------|-------------------|
| `tipo_datos` | STRING | Tipo de datos (diarios, mensuales) | "mensuales" |
| `estacion_preferida` | STRING | Código de estación meteorológica | Auto-detectar por proximidad |

### Datos Enriquecidos Generados
- `temperatura_media`: Temperatura media del período (°C)
- `temperatura_maxima`: Temperatura máxima (°C)
- `temperatura_minima`: Temperatura mínima (°C)
- `precipitacion_total`: Precipitación acumulada (mm)
- `humedad_relativa_media`: Humedad relativa media (%)
- `radiacion_solar_media`: Radiación solar media (kWh/m²)
- `grados_dia_calefaccion`: Grados día de calefacción (base 15°C)
- `grados_dia_refrigeracion`: Grados día de refrigeración (base 25°C)

### Ejemplo de Uso
```python
# Datos de entrada desde JSON N0
cp = "36003"
fecha_inicio = "2025-04-08"
fecha_fin = "2025-05-07"

# Llamada a AEMET
weather_data = aemet_api.get_weather_data(cp, fecha_inicio, fecha_fin)
```

## 4. Mapeo de Campos desde JSON N0

### Campos Disponibles en JSON N0
```json
{
  "supply_point": {
    "datos_suministro": {
      "direccion_suministro": {
        "codigo_postal": "36003",           // ✅ OBLIGATORIO para todas las APIs
        "comunidad_autonoma": "Galicia",    // ℹ️ Informativo
        "municipio": "Pontevedra",          // ℹ️ Informativo  
        "nombre_via": "CAMIÑO DE FERRO",    // ✅ OBLIGATORIO para Google
        "numero": "6",                      // ✅ OBLIGATORIO para Google
        "pais": "España",                   // ✅ OBLIGATORIO para Google
        "planta": "6 A",                    // 🔶 OPCIONAL para Google
        "poblacion": "Pontevedra",          // ✅ OBLIGATORIO para Google
        "provincia": "Pontevedra",          // ✅ OBLIGATORIO para Google
        "puerta": "",                       // 🔶 OPCIONAL para Google
        "tipo_via": "DO"                    // ✅ OBLIGATORIO para Google
      }
    }
  },
  "invoice_2x3": {
    "fecha_inicio_periodo": "2025-04-08",  // ✅ OBLIGATORIO para OMIE y AEMET
    "fecha_fin_periodo": "2025-05-07"      // ✅ OBLIGATORIO para OMIE y AEMET
  }
}
```

## 5. Configuración de Base de Datos

### Tabla: enrichment_sources
Configuración de las APIs externas:

```sql
CREATE TABLE IF NOT EXISTS enrichment_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) UNIQUE NOT NULL,
    source_type VARCHAR(20) NOT NULL, -- 'weather', 'geocoding', 'market_price'
    base_url VARCHAR(255) NOT NULL,
    api_key_required BOOLEAN DEFAULT false,
    rate_limit_per_minute INTEGER DEFAULT 60,
    rate_limit_per_hour INTEGER DEFAULT 1000,
    max_failures INTEGER DEFAULT 5,
    timeout_seconds INTEGER DEFAULT 30,
    config JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_success TIMESTAMP,
    last_failure TIMESTAMP,
    consecutive_failures INTEGER DEFAULT 0
);
```

### Tabla: enriched_data
Almacenamiento de datos enriquecidos:

```sql
CREATE TABLE IF NOT EXISTS enriched_data (
    id SERIAL PRIMARY KEY,
    direccion_hash VARCHAR(64) NOT NULL, -- SHA-256 de la dirección
    codigo_postal VARCHAR(5) NOT NULL,
    periodo VARCHAR(7) NOT NULL, -- YYYY-MM
    source_type VARCHAR(20) NOT NULL,
    enriched_fields JSONB NOT NULL,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(direccion_hash, codigo_postal, periodo, source_type)
);
```

## 6. Validación de Datos

### Campos Obligatorios Mínimos
Para que el sistema de enriquecimiento funcione, se requieren **obligatoriamente**:

1. **Código Postal** (5 dígitos): `36003`
2. **Fecha de Período**: `2025-04-08` a `2025-05-07`
3. **Dirección Básica**: `tipo_via + nombre_via + numero`

### Validaciones Automáticas
- Código postal: Formato español (5 dígitos)
- Fechas: Formato ISO (YYYY-MM-DD)
- Dirección: Mínimo tipo_via + nombre_via + numero

### Manejo de Errores
- **Datos faltantes**: Log de advertencia, continúa sin enriquecimiento
- **API no disponible**: Reintento con backoff exponencial
- **Rate limit**: Espera automática hasta reset
- **Datos inválidos**: Validación previa, rechazo de llamada

## 7. Ejemplo de Implementación

### Función de Enriquecimiento Completo
```python
def enriquecer_datos_factura(json_n0):
    """
    Enriquece una factura N0 con datos externos.
    
    Args:
        json_n0: Diccionario con datos de factura N0
        
    Returns:
        dict: Datos enriquecidos por fuente
    """
    # Extraer campos obligatorios
    cp = json_n0['supply_point']['datos_suministro']['direccion_suministro']['codigo_postal']
    fecha_inicio = json_n0['invoice_2x3']['fecha_inicio_periodo']
    fecha_fin = json_n0['invoice_2x3']['fecha_fin_periodo']
    
    # Construir dirección completa
    dir_data = json_n0['supply_point']['datos_suministro']['direccion_suministro']
    direccion = f"{dir_data['tipo_via']} {dir_data['nombre_via']} {dir_data['numero']}"
    
    resultados = {}
    
    # 1. Enriquecimiento OMIE
    try:
        omie_data = omie_api.obtener_precio_medio(datetime.strptime(fecha_inicio, "%Y-%m-%d"))
        if omie_data:
            resultados['omie'] = omie_data
    except Exception as e:
        logger.error(f"Error OMIE: {e}")
    
    # 2. Enriquecimiento Google Maps
    try:
        geo_data = google_api.geocode(direccion, cp)
        if geo_data:
            resultados['geocoding'] = geo_data
    except Exception as e:
        logger.error(f"Error Google: {e}")
    
    # 3. Enriquecimiento AEMET
    try:
        weather_data = aemet_api.get_weather_data(cp, fecha_inicio, fecha_fin)
        if weather_data:
            resultados['weather'] = weather_data
    except Exception as e:
        logger.error(f"Error AEMET: {e}")
    
    return resultados
```

## 8. Métricas y Monitorización

### KPIs de Enriquecimiento
- **Tasa de éxito por API**: % de llamadas exitosas
- **Tiempo de respuesta medio**: Latencia por API
- **Cobertura de datos**: % de facturas enriquecidas
- **Calidad de datos**: Score de confianza promedio

### Alertas Automáticas
- Rate limit alcanzado (>90% del límite)
- Fallos consecutivos (>3 fallos)
- Tiempo de respuesta alto (>10 segundos)
- APIs inactivas por >1 hora

---

**Fecha de creación**: 2025-01-07  
**Versión**: 1.0  
**Autor**: Sistema de Enriquecimiento db_watioverse
