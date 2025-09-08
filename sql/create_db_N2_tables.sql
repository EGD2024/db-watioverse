-- =============================================================================
-- CREACIÓN DE TABLAS PARA db_N2 - DATOS ENRIQUECIDOS DEL CLIENTE
-- =============================================================================
-- Base de datos: db_N2
-- Propósito: Almacenar datos de N1 enriquecidos con información geográfica,
--           climática y KPIs calculados antes del scoring en N3
-- Fecha: 2025-01-07
-- =============================================================================

-- Crear base de datos si no existe (ejecutar manualmente si es necesario)
-- CREATE DATABASE db_N2;

-- NOTA: Este script debe ejecutarse estando ya conectado a db_N2
-- Comando: psql -h localhost -U postgres -d db_N2 -f create_db_N2_tables.sql

-- =============================================================================
-- TABLA PRINCIPAL: facturas_electricidad_enriquecidas
-- =============================================================================
-- Almacena facturas de electricidad con datos enriquecidos
CREATE TABLE IF NOT EXISTS facturas_electricidad_enriquecidas (
    -- Identificadores únicos
    id SERIAL PRIMARY KEY,
    cups_electricidad VARCHAR(22) NOT NULL,
    fecha_procesamiento TIMESTAMP NOT NULL,
    
    -- Datos geográficos enriquecidos
    latitud DECIMAL(10,8),
    longitud DECIMAL(11,8),
    direccion_normalizada TEXT,
    municipio VARCHAR(100),
    provincia VARCHAR(50),
    codigo_postal VARCHAR(10),
    zona_climatica VARCHAR(10),
    altitud_msnm INTEGER,
    tipo_zona VARCHAR(20), -- urbana, rural, industrial
    
    -- Datos climáticos del período
    temperatura_media_mes_anterior DECIMAL(5,2),
    precipitacion_total_mes_anterior DECIMAL(7,2),
    grados_dia_calefaccion DECIMAL(7,2),
    grados_dia_refrigeracion DECIMAL(7,2),
    humedad_relativa_media DECIMAL(5,2),
    horas_sol_total DECIMAL(6,2),
    
    -- Datos de mercado energético
    precio_medio_omie_mes_anterior DECIMAL(8,4),
    
    -- KPIs de eficiencia calculados (JSON)
    kpis_eficiencia JSONB,
    
    -- Metadatos del proceso de enriquecimiento
    metadata_enriquecimiento JSONB,
    
    -- Campos de auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Índice único se creará por separado
    CONSTRAINT unique_cups_fecha UNIQUE(cups_electricidad, fecha_procesamiento)
);

-- =============================================================================
-- TABLA AUXILIAR: coordenadas_geograficas
-- =============================================================================
-- Cache de coordenadas geográficas por CUPS para optimizar consultas
CREATE TABLE IF NOT EXISTS coordenadas_geograficas (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL UNIQUE,
    latitud DECIMAL(10,8) NOT NULL,
    longitud DECIMAL(11,8) NOT NULL,
    direccion_normalizada TEXT,
    municipio VARCHAR(100),
    provincia VARCHAR(50),
    codigo_postal VARCHAR(10),
    zona_climatica VARCHAR(10),
    altitud_msnm INTEGER,
    tipo_zona VARCHAR(20),
    
    -- Metadatos de la geocodificación
    fuente_geocodificacion VARCHAR(50), -- google_maps, catastro, manual
    precision_geocodificacion VARCHAR(20), -- exact, approximate, interpolated
    fecha_geocodificacion TIMESTAMP,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- TABLA AUXILIAR: datos_climaticos_mensuales
-- =============================================================================
-- Datos climáticos históricos por coordenadas y mes
CREATE TABLE IF NOT EXISTS datos_climaticos_mensuales (
    id SERIAL PRIMARY KEY,
    latitud DECIMAL(10,8) NOT NULL,
    longitud DECIMAL(11,8) NOT NULL,
    año INTEGER NOT NULL,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    
    -- Datos climáticos
    temperatura_media_celsius DECIMAL(5,2),
    temperatura_maxima_celsius DECIMAL(5,2),
    temperatura_minima_celsius DECIMAL(5,2),
    precipitacion_total_mm DECIMAL(7,2),
    grados_dia_calefaccion DECIMAL(7,2),
    grados_dia_refrigeracion DECIMAL(7,2),
    humedad_relativa_media DECIMAL(5,2),
    horas_sol_total DECIMAL(6,2),
    velocidad_viento_media DECIMAL(5,2),
    
    -- Metadatos
    fuente_datos VARCHAR(50), -- aemet, visual_crossing, etc.
    calidad_datos VARCHAR(20), -- high, medium, low, estimated
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Índice único por ubicación y período
    UNIQUE(latitud, longitud, año, mes)
);

-- =============================================================================
-- TABLA AUXILIAR: enrichment_cache
-- =============================================================================
-- Cache general de enriquecimiento por CUPS
CREATE TABLE IF NOT EXISTS enrichment_cache (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL,
    
    -- Datos JSON por categoría
    datos_clima JSONB,
    datos_sostenibilidad JSONB,
    datos_territorio JSONB,
    datos_mercado JSONB,
    
    -- Estado del cache
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- TABLA AUXILIAR: enrichment_queue
-- =============================================================================
-- Cola de procesamiento asíncrono para enriquecimiento
CREATE TABLE IF NOT EXISTS enrichment_queue (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL,
    fecha_factura DATE NOT NULL,
    
    -- Control de procesamiento
    priority VARCHAR(10) DEFAULT 'normal', -- high, normal, low
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    
    -- Resultados del procesamiento
    result_data JSONB,
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    next_retry_at TIMESTAMP,
    
    -- Índice único por CUPS y fecha
    UNIQUE(cups, fecha_factura)
);

-- =============================================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =============================================================================

-- Índices principales para facturas_electricidad_enriquecidas
CREATE INDEX IF NOT EXISTS idx_facturas_enriq_cups ON facturas_electricidad_enriquecidas(cups_electricidad);
CREATE INDEX IF NOT EXISTS idx_facturas_enriq_fecha ON facturas_electricidad_enriquecidas(fecha_procesamiento);
CREATE INDEX IF NOT EXISTS idx_facturas_enriq_provincia ON facturas_electricidad_enriquecidas(provincia);
CREATE INDEX IF NOT EXISTS idx_facturas_enriq_zona_climatica ON facturas_electricidad_enriquecidas(zona_climatica);

-- Índices para coordenadas_geograficas
CREATE INDEX IF NOT EXISTS idx_coord_geo_latlon ON coordenadas_geograficas(latitud, longitud);
CREATE INDEX IF NOT EXISTS idx_coord_geo_municipio ON coordenadas_geograficas(municipio);
CREATE INDEX IF NOT EXISTS idx_coord_geo_provincia ON coordenadas_geograficas(provincia);

-- Índices para datos_climaticos_mensuales
CREATE INDEX IF NOT EXISTS idx_clima_latlon ON datos_climaticos_mensuales(latitud, longitud);
CREATE INDEX IF NOT EXISTS idx_clima_fecha ON datos_climaticos_mensuales(año, mes);
CREATE INDEX IF NOT EXISTS idx_clima_latlon_fecha ON datos_climaticos_mensuales(latitud, longitud, año, mes);

-- Índices para enrichment_cache
CREATE INDEX IF NOT EXISTS idx_enrichment_cache_cups_active ON enrichment_cache(cups, is_active);

-- Índices para enrichment_queue
CREATE INDEX IF NOT EXISTS idx_enrich_queue_status ON enrichment_queue(status);
CREATE INDEX IF NOT EXISTS idx_enrich_queue_priority ON enrichment_queue(priority, created_at);
CREATE INDEX IF NOT EXISTS idx_enrich_queue_retry ON enrichment_queue(next_retry_at) WHERE status = 'failed';

-- =============================================================================
-- TRIGGERS PARA AUDITORÍA
-- =============================================================================

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para updated_at
CREATE TRIGGER update_facturas_enriq_updated_at 
    BEFORE UPDATE ON facturas_electricidad_enriquecidas 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_coord_geo_updated_at 
    BEFORE UPDATE ON coordenadas_geograficas 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clima_updated_at 
    BEFORE UPDATE ON datos_climaticos_mensuales 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_enrich_cache_updated_at 
    BEFORE UPDATE ON enrichment_cache 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- COMENTARIOS EN TABLAS
-- =============================================================================

COMMENT ON TABLE facturas_electricidad_enriquecidas IS 'Tabla principal con facturas de electricidad enriquecidas con datos geográficos, climáticos y KPIs';
COMMENT ON TABLE coordenadas_geograficas IS 'Cache de coordenadas geográficas por CUPS para optimizar geocodificación';
COMMENT ON TABLE datos_climaticos_mensuales IS 'Datos climáticos históricos mensuales por coordenadas geográficas';
COMMENT ON TABLE enrichment_cache IS 'Cache general de datos de enriquecimiento por CUPS';
COMMENT ON TABLE enrichment_queue IS 'Cola de procesamiento asíncrono para enriquecimiento de datos';

-- =============================================================================
-- PERMISOS Y SEGURIDAD
-- =============================================================================

-- Crear usuario específico para N2 si no existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'n2_user') THEN
        CREATE ROLE n2_user WITH LOGIN PASSWORD 'n2_secure_password_2025';
    END IF;
END
$$;

-- Otorgar permisos
GRANT CONNECT ON DATABASE db_N2 TO n2_user;
GRANT USAGE ON SCHEMA public TO n2_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO n2_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO n2_user;

-- =============================================================================
-- ESTADÍSTICAS Y MANTENIMIENTO
-- =============================================================================

-- Actualizar estadísticas
ANALYZE facturas_electricidad_enriquecidas;
ANALYZE coordenadas_geograficas;
ANALYZE datos_climaticos_mensuales;
ANALYZE enrichment_cache;
ANALYZE enrichment_queue;

-- =============================================================================
-- FIN DEL SCRIPT
-- =============================================================================

-- Base de datos db_N2 creada exitosamente con todas las tablas de datos enriquecidos
-- Tablas creadas:
--   - facturas_electricidad_enriquecidas (tabla principal)
--   - coordenadas_geograficas (cache geográfico)
--   - datos_climaticos_mensuales (datos climáticos)
--   - enrichment_cache (cache general)
--   - enrichment_queue (cola procesamiento)
-- Sistema listo para almacenar datos enriquecidos N1 → N2
