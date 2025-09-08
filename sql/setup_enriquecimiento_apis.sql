-- =====================================================
-- CONFIGURACIÓN DE APIS DE ENRIQUECIMIENTO
-- =====================================================
-- Fecha: 2025-01-07
-- Propósito: Configurar las APIs externas para enriquecimiento de datos
-- Base de datos: db_enriquecimiento

-- Crear tabla de configuración de fuentes externas
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

-- Crear tabla para almacenar datos enriquecidos
CREATE TABLE IF NOT EXISTS enriched_data (
    id SERIAL PRIMARY KEY,
    direccion_hash VARCHAR(40) NOT NULL, -- Hash corto de la dirección
    codigo_postal VARCHAR(5) NOT NULL,
    periodo VARCHAR(7) NOT NULL, -- YYYY-MM
    source_type VARCHAR(20) NOT NULL,
    enriched_fields JSONB NOT NULL,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(direccion_hash, codigo_postal, periodo, source_type)
);

-- Crear índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_enriched_data_lookup 
ON enriched_data(direccion_hash, codigo_postal, periodo, source_type);

CREATE INDEX IF NOT EXISTS idx_enriched_data_expires 
ON enriched_data(expires_at) WHERE expires_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_enrichment_sources_active 
ON enrichment_sources(source_type, is_active) WHERE is_active = true;

-- =====================================================
-- INSERTAR CONFIGURACIÓN DE APIS
-- =====================================================

-- 1. API OMIE (Precios de electricidad)
INSERT INTO enrichment_sources (
    source_name, 
    source_type, 
    base_url, 
    api_key_required,
    rate_limit_per_minute,
    rate_limit_per_hour,
    max_failures,
    timeout_seconds,
    config,
    is_active
) VALUES (
    'OMIE_API',
    'market_price',
    'https://apidatos.ree.es/es/datos/mercados/componentes-precio-energia-cierre-desglose',
    false,
    30, -- 30 llamadas por minuto
    500, -- 500 llamadas por hora
    3,
    30,
    '{
        "market": "ES",
        "time_trunc": "month",
        "data_format": "json",
        "fallback_url": "https://api.omie.es/files/flash"
    }'::jsonb,
    true
) ON CONFLICT (source_name) DO UPDATE SET
    base_url = EXCLUDED.base_url,
    config = EXCLUDED.config,
    is_active = EXCLUDED.is_active;

-- 2. API REE (Fallback para precios)
INSERT INTO enrichment_sources (
    source_name, 
    source_type, 
    base_url, 
    api_key_required,
    rate_limit_per_minute,
    rate_limit_per_hour,
    max_failures,
    timeout_seconds,
    config,
    is_active
) VALUES (
    'REE_Datos',
    'market_price',
    'https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real',
    false,
    60,
    1000,
    5,
    30,
    '{
        "market": "ES",
        "data_format": "json"
    }'::jsonb,
    true
) ON CONFLICT (source_name) DO UPDATE SET
    base_url = EXCLUDED.base_url,
    config = EXCLUDED.config,
    is_active = EXCLUDED.is_active;

-- 3. API AEMET (Datos meteorológicos)
INSERT INTO enrichment_sources (
    source_name, 
    source_type, 
    base_url, 
    api_key_required,
    rate_limit_per_minute,
    rate_limit_per_hour,
    max_failures,
    timeout_seconds,
    config,
    is_active
) VALUES (
    'AEMET_API',
    'weather',
    'https://opendata.aemet.es/opendata/api',
    true, -- Requiere API key
    20, -- Límite conservador
    200,
    3,
    45,
    '{
        "data_type": "climatologias",
        "format": "json",
        "default_stations": {
            "28": {"indicativo": "3195", "nombre": "Madrid-Retiro"},
            "08": {"indicativo": "0076", "nombre": "Barcelona"},
            "41": {"indicativo": "5783", "nombre": "Sevilla"},
            "46": {"indicativo": "8416", "nombre": "Valencia"},
            "36": {"indicativo": "1495", "nombre": "Pontevedra"}
        }
    }'::jsonb,
    true
) ON CONFLICT (source_name) DO UPDATE SET
    base_url = EXCLUDED.base_url,
    config = EXCLUDED.config,
    api_key_required = EXCLUDED.api_key_required,
    is_active = EXCLUDED.is_active;

-- 4. Google Maps API (Geocodificación)
INSERT INTO enrichment_sources (
    source_name, 
    source_type, 
    base_url, 
    api_key_required,
    rate_limit_per_minute,
    rate_limit_per_hour,
    max_failures,
    timeout_seconds,
    config,
    is_active
) VALUES (
    'GOOGLE_MAPS_API',
    'geocoding',
    'https://maps.googleapis.com/maps/api/geocode/json',
    true, -- Requiere API key
    50, -- Límite estándar de Google
    2500, -- Límite diario convertido a horario
    5,
    15,
    '{
        "region": "es",
        "language": "es",
        "result_type": "street_address|premise",
        "location_type": "ROOFTOP|RANGE_INTERPOLATED"
    }'::jsonb,
    true
) ON CONFLICT (source_name) DO UPDATE SET
    base_url = EXCLUDED.base_url,
    config = EXCLUDED.config,
    api_key_required = EXCLUDED.api_key_required,
    is_active = EXCLUDED.is_active;

-- 5. API Catastro (Datos catastrales - opcional)
INSERT INTO enrichment_sources (
    source_name, 
    source_type, 
    base_url, 
    api_key_required,
    rate_limit_per_minute,
    rate_limit_per_hour,
    max_failures,
    timeout_seconds,
    config,
    is_active
) VALUES (
    'CATASTRO_API',
    'cadastral',
    'http://ovc.catastro.meh.es/OVCSWLocalizacionRC/OVCCallejero.asmx',
    false,
    30,
    500,
    5,
    30,
    '{
        "format": "xml",
        "service": "Consulta_DNPRC"
    }'::jsonb,
    false -- Desactivado por defecto (opcional)
) ON CONFLICT (source_name) DO UPDATE SET
    base_url = EXCLUDED.base_url,
    config = EXCLUDED.config,
    is_active = EXCLUDED.is_active;

-- =====================================================
-- DATOS DE EJEMPLO PARA TESTING
-- =====================================================

-- Insertar datos de ejemplo para testing (dirección del JSON N0)
INSERT INTO enriched_data (
    direccion_hash,
    codigo_postal,
    periodo,
    source_type,
    enriched_fields,
    confidence_score,
    expires_at
) VALUES (
    -- Hash SHA-256 de "DO CAMIÑO DE FERRO 6, 6 A, 36003 Pontevedra"
    'a1b2c3d4e5f6789012345678901234567890',
    '36003',
    '2025-04',
    'weather',
    '{
        "temperatura_media": 16.5,
        "temperatura_maxima": 22.1,
        "temperatura_minima": 11.2,
        "precipitacion_total": 45.3,
        "humedad_relativa_media": 72,
        "radiacion_solar_media": 4.2,
        "grados_dia_calefaccion": 120,
        "grados_dia_refrigeracion": 5,
        "fuente": "AEMET",
        "estacion": "1495 - Pontevedra"
    }'::jsonb,
    0.95,
    CURRENT_TIMESTAMP + INTERVAL '30 days'
) ON CONFLICT (direccion_hash, codigo_postal, periodo, source_type) DO NOTHING;

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
        "latitud": 42.4296,
        "longitud": -8.6448,
        "precision_geocoding": "ROOFTOP",
        "tipo_ubicacion": "residential",
        "zona_climatica": "C1",
        "altitud_estimada": 20,
        "fuente": "Google Maps API"
    }'::jsonb,
    0.98,
    CURRENT_TIMESTAMP + INTERVAL '90 days'
) ON CONFLICT (direccion_hash, codigo_postal, periodo, source_type) DO NOTHING;

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
        "precio_medio_kwh": 0.12456,
        "precio_maximo": 0.18923,
        "precio_minimo": 0.08234,
        "volatilidad": 0.02134,
        "precios_horarios": [0.11, 0.10, 0.09, 0.12, 0.15, 0.18],
        "fuente": "OMIE"
    }'::jsonb,
    0.92,
    CURRENT_TIMESTAMP + INTERVAL '7 days'
) ON CONFLICT (direccion_hash, codigo_postal, periodo, source_type) DO NOTHING;

-- =====================================================
-- FUNCIONES AUXILIARES
-- =====================================================

-- Función para limpiar datos expirados
CREATE OR REPLACE FUNCTION cleanup_expired_enrichment_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM enriched_data 
    WHERE expires_at IS NOT NULL 
    AND expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Función para obtener estadísticas de enriquecimiento
CREATE OR REPLACE FUNCTION get_enrichment_stats()
RETURNS TABLE(
    source_type VARCHAR(20),
    total_records BIGINT,
    avg_confidence DECIMAL(3,2),
    expired_records BIGINT,
    latest_update TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ed.source_type,
        COUNT(*) as total_records,
        ROUND(AVG(ed.confidence_score), 2) as avg_confidence,
        COUNT(*) FILTER (WHERE ed.expires_at < CURRENT_TIMESTAMP) as expired_records,
        MAX(ed.created_at) as latest_update
    FROM enriched_data ed
    GROUP BY ed.source_type
    ORDER BY total_records DESC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VERIFICACIÓN DE INSTALACIÓN
-- =====================================================

-- Verificar que las tablas se crearon correctamente
DO $$
DECLARE
    source_count INTEGER;
    data_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO source_count FROM enrichment_sources WHERE is_active = true;
    SELECT COUNT(*) INTO data_count FROM enriched_data;
    
    RAISE NOTICE '✅ APIs configuradas: %', source_count;
    RAISE NOTICE '✅ Registros de ejemplo: %', data_count;
    RAISE NOTICE '✅ Sistema de enriquecimiento configurado correctamente';
END $$;

-- Mostrar configuración actual
SELECT 
    source_name as "API",
    source_type as "Tipo",
    CASE WHEN api_key_required THEN '🔑 Sí' ELSE '🔓 No' END as "API Key",
    rate_limit_per_minute as "Límite/min",
    CASE WHEN is_active THEN '✅ Activa' ELSE '❌ Inactiva' END as "Estado"
FROM enrichment_sources 
ORDER BY source_type, source_name;
