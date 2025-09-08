-- =====================================================
-- INSERCIÓN DE DATOS DE EJEMPLO PARA ENRIQUECIMIENTO
-- =====================================================
-- Fecha: 2025-01-07
-- Propósito: Insertar datos de ejemplo basados en JSON N0 real
-- Base de datos: db_enriquecimiento

-- =====================================================
-- DATOS EXTRAÍDOS DEL JSON N0 REAL
-- =====================================================
-- Archivo: N0_ES0022000008433586LW0F_20250512_191543.json
-- Cliente: ALEJANDRO DÍAZ GONZÁLEZ
-- Dirección: DO CAMIÑO DE FERRO 6, 6 A, 36003 Pontevedra
-- Período: 2025-04-08 a 2025-05-07

-- Hash corto de la dirección (36 caracteres)
-- Representa: "DO CAMIÑO DE FERRO 6, 6 A, 36003 Pontevedra, Pontevedra, España"
-- Hash válido: a1b2c3d4e5f6789012345678901234567890

-- =====================================================
-- 1. DATOS DE ENRIQUECIMIENTO METEOROLÓGICO (AEMET)
-- =====================================================

INSERT INTO enriched_data (
    direccion_hash,
    codigo_postal,
    periodo,
    source_type,
    enriched_fields,
    confidence_score,
    expires_at
) VALUES (
    'a1b2c3d4e5f6789012345678901234567890',
    '36003', -- Pontevedra
    '2025-04', -- Abril 2025
    'weather',
    '{
        "codigo_postal": "36003",
        "temperatura_media": 15.8,
        "temperatura_maxima": 21.4,
        "temperatura_minima": 10.2,
        "precipitacion_total": 52.7,
        "humedad_relativa_media": 75,
        "radiacion_solar_media": 4.8,
        "grados_dia_calefaccion": 135,
        "grados_dia_refrigeracion": 2,
        "estacion_meteorologica": "1495 - Pontevedra",
        "fuente": "AEMET",
        "timestamp": "2025-01-07T19:32:00Z",
        "datos_periodo": {
            "fecha_inicio": "2025-04-08",
            "fecha_fin": "2025-05-07",
            "dias_periodo": 30
        }
    }'::jsonb,
    0.94,
    CURRENT_TIMESTAMP + INTERVAL '30 days'
) ON CONFLICT (direccion_hash, codigo_postal, periodo, source_type) 
DO UPDATE SET
    enriched_fields = EXCLUDED.enriched_fields,
    confidence_score = EXCLUDED.confidence_score,
    expires_at = EXCLUDED.expires_at;

-- =====================================================
-- 2. DATOS DE GEOLOCALIZACIÓN (GOOGLE MAPS)
-- =====================================================

INSERT INTO enriched_data (
    direccion_hash,
    codigo_postal,
    periodo,
    source_type,
    enriched_fields,
    confidence_score,
    expires_at
) VALUES (
    'a1b2c3d4e5f6789012345678901234567890',
    '36003',
    '2025-04',
    'geocoding',
    '{
        "direccion_original": "DO CAMIÑO DE FERRO 6, 6 A",
        "direccion_normalizada": "Camiño de Ferro, 6, 36003 Pontevedra, España",
        "codigo_postal": "36003",
        "latitud": 42.4296,
        "longitud": -8.6448,
        "precision_geocoding": "ROOFTOP",
        "tipo_ubicacion": "residential",
        "zona_climatica": "C1",
        "altitud_estimada": 25,
        "componentes_direccion": {
            "tipo_via": "DO",
            "nombre_via": "CAMIÑO DE FERRO",
            "numero": "6",
            "planta": "6 A",
            "codigo_postal": "36003",
            "poblacion": "Pontevedra",
            "provincia": "Pontevedra",
            "comunidad_autonoma": "Galicia",
            "pais": "España"
        },
        "informacion_geografica": {
            "zona_horaria": "Europe/Madrid",
            "zona_utm": "29T",
            "coordenadas_utm": {
                "x": 539821,
                "y": 4698543
            }
        },
        "fuente": "Google Maps API",
        "timestamp": "2025-01-07T19:32:00Z"
    }'::jsonb,
    0.97,
    CURRENT_TIMESTAMP + INTERVAL '90 days' -- Los datos geográficos cambian poco
) ON CONFLICT (direccion_hash, codigo_postal, periodo, source_type) 
DO UPDATE SET
    enriched_fields = EXCLUDED.enriched_fields,
    confidence_score = EXCLUDED.confidence_score,
    expires_at = EXCLUDED.expires_at;

-- =====================================================
-- 3. DATOS DE PRECIOS DE MERCADO (OMIE)
-- =====================================================

INSERT INTO enriched_data (
    direccion_hash,
    codigo_postal,
    periodo,
    source_type,
    enriched_fields,
    confidence_score,
    expires_at
) VALUES (
    'a1b2c3d4e5f6789012345678901234567890',
    '36003',
    '2025-04',
    'market_price',
    '{
        "fecha_inicio": "2025-04-08",
        "fecha_fin": "2025-05-07",
        "zona_mercado": "ES",
        "precio_medio_kwh": 0.11234,
        "precio_maximo": 0.16789,
        "precio_minimo": 0.07456,
        "volatilidad": 0.02145,
        "precios_horarios_muestra": [
            {"hora": "00:00", "precio": 0.08234},
            {"hora": "06:00", "precio": 0.09123},
            {"hora": "12:00", "precio": 0.14567},
            {"hora": "18:00", "precio": 0.16234},
            {"hora": "22:00", "precio": 0.12345}
        ],
        "estadisticas_periodo": {
            "dias_analizados": 30,
            "horas_con_datos": 720,
            "precio_p25": 0.09456,
            "precio_p50": 0.11234,
            "precio_p75": 0.13789,
            "precio_p95": 0.15678
        },
        "comparacion_historica": {
            "precio_mismo_mes_año_anterior": 0.13456,
            "variacion_interanual": -16.5,
            "tendencia": "bajista"
        },
        "fuente": "OMIE",
        "timestamp": "2025-01-07T19:32:00Z"
    }'::jsonb,
    0.91,
    CURRENT_TIMESTAMP + INTERVAL '7 days' -- Los precios cambian frecuentemente
) ON CONFLICT (direccion_hash, codigo_postal, periodo, source_type) 
DO UPDATE SET
    enriched_fields = EXCLUDED.enriched_fields,
    confidence_score = EXCLUDED.confidence_score,
    expires_at = EXCLUDED.expires_at;

-- =====================================================
-- 4. DATOS ADICIONALES PARA OTROS CASOS
-- =====================================================

-- Caso Madrid (código postal 28001)
INSERT INTO enriched_data (
    direccion_hash,
    codigo_postal,
    periodo,
    source_type,
    enriched_fields,
    confidence_score,
    expires_at
) VALUES (
    'madrid_hash_1234567890abcdef12345678',
    '28001',
    '2025-04',
    'weather',
    '{
        "codigo_postal": "28001",
        "temperatura_media": 18.2,
        "temperatura_maxima": 24.8,
        "temperatura_minima": 11.6,
        "precipitacion_total": 32.4,
        "humedad_relativa_media": 58,
        "radiacion_solar_media": 5.6,
        "grados_dia_calefaccion": 98,
        "grados_dia_refrigeracion": 12,
        "estacion_meteorologica": "3195 - Madrid-Retiro",
        "fuente": "AEMET"
    }'::jsonb,
    0.96,
    CURRENT_TIMESTAMP + INTERVAL '30 days'
) ON CONFLICT (direccion_hash, codigo_postal, periodo, source_type) DO NOTHING;

-- Caso Barcelona (código postal 08001)
INSERT INTO enriched_data (
    direccion_hash,
    codigo_postal,
    periodo,
    source_type,
    enriched_fields,
    confidence_score,
    expires_at
) VALUES (
    'barcelona_hash_abcdef1234567890abcdef',
    '08001',
    '2025-04',
    'weather',
    '{
        "codigo_postal": "08001",
        "temperatura_media": 17.5,
        "temperatura_maxima": 22.1,
        "temperatura_minima": 13.2,
        "precipitacion_total": 28.9,
        "humedad_relativa_media": 68,
        "radiacion_solar_media": 5.2,
        "grados_dia_calefaccion": 85,
        "grados_dia_refrigeracion": 8,
        "estacion_meteorologica": "0076 - Barcelona",
        "fuente": "AEMET"
    }'::jsonb,
    0.95,
    CURRENT_TIMESTAMP + INTERVAL '30 days'
) ON CONFLICT (direccion_hash, codigo_postal, periodo, source_type) DO NOTHING;

-- =====================================================
-- 5. VERIFICACIÓN DE DATOS INSERTADOS
-- =====================================================

-- Mostrar resumen de datos insertados
SELECT 
    'Datos de enriquecimiento insertados:' as mensaje,
    source_type as "Tipo de Fuente",
    COUNT(*) as "Registros",
    MIN(created_at) as "Primer Registro",
    MAX(created_at) as "Último Registro"
FROM enriched_data 
GROUP BY source_type
ORDER BY source_type;

-- Mostrar datos específicos del ejemplo principal
SELECT 
    'Datos para Pontevedra (36003):' as mensaje,
    source_type as "Fuente",
    confidence_score as "Confianza",
    expires_at as "Expira",
    jsonb_pretty(enriched_fields) as "Datos Enriquecidos"
FROM enriched_data 
WHERE codigo_postal = '36003' 
AND periodo = '2025-04'
ORDER BY source_type;

-- Estadísticas generales
SELECT 
    'Estadísticas generales:' as mensaje,
    COUNT(*) as "Total Registros",
    COUNT(DISTINCT codigo_postal) as "Códigos Postales",
    COUNT(DISTINCT source_type) as "Tipos de Fuente",
    ROUND(AVG(confidence_score), 3) as "Confianza Media"
FROM enriched_data;
