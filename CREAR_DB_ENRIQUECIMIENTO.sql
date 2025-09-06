-- =====================================================
-- CREAR ESTRUCTURA db_enriquecimiento
-- Base de datos de cache y enriquecimiento externo
-- Ejecutar conectado a db_enriquecimiento
-- =====================================================

-- TABLA 1: ENRICHMENT_CACHE - Cache multi-dimensional
CREATE TABLE enrichment_cache (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL,
    direccion_hash VARCHAR(64) NOT NULL,
    provincia VARCHAR(100),
    codigo_postal VARCHAR(10),
    tarifa VARCHAR(50),
    periodo_mes VARCHAR(7), -- YYYY-MM
    
    -- Datos enriquecidos
    datos_clima JSONB,
    datos_sostenibilidad JSONB,
    datos_mercado JSONB,
    datos_territorio JSONB,
    datos_catastro JSONB,
    
    -- Control temporal
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    
    -- Índice único compuesto
    UNIQUE(cups, direccion_hash, tarifa, periodo_mes)
);

-- TABLA 2: ENRICHMENT_QUEUE - Cola de trabajos asíncronos
CREATE TABLE enrichment_queue (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL,
    direccion_hash VARCHAR(64) NOT NULL,
    provincia VARCHAR(100),
    codigo_postal VARCHAR(10),
    tarifa VARCHAR(50),
    periodo_mes VARCHAR(7),
    
    -- Control de procesamiento
    priority VARCHAR(20) DEFAULT 'medium', -- high, medium, low
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    
    -- Timestamps
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    next_retry_at TIMESTAMP
);

-- TABLA 3: ENRICHMENT_SOURCES - Control de APIs externas
CREATE TABLE enrichment_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL, -- api, database, file
    base_url VARCHAR(255),
    api_key_required BOOLEAN DEFAULT false,
    
    -- Control de estado
    is_active BOOLEAN DEFAULT true,
    last_success TIMESTAMP,
    last_failure TIMESTAMP,
    consecutive_failures INTEGER DEFAULT 0,
    max_failures INTEGER DEFAULT 5,
    
    -- Rate limiting
    rate_limit_per_minute INTEGER DEFAULT 60,
    rate_limit_per_hour INTEGER DEFAULT 1000,
    current_minute_calls INTEGER DEFAULT 0,
    current_hour_calls INTEGER DEFAULT 0,
    rate_reset_minute TIMESTAMP,
    rate_reset_hour TIMESTAMP,
    
    -- Configuración
    timeout_seconds INTEGER DEFAULT 30,
    retry_delay_seconds INTEGER DEFAULT 60,
    config JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimización
CREATE INDEX idx_enrichment_cache_cups ON enrichment_cache(cups);
CREATE INDEX idx_enrichment_cache_hash ON enrichment_cache(direccion_hash);
CREATE INDEX idx_enrichment_cache_expires ON enrichment_cache(expires_at);
CREATE INDEX idx_enrichment_queue_status ON enrichment_queue(status);
CREATE INDEX idx_enrichment_queue_priority ON enrichment_queue(priority, requested_at);
CREATE INDEX idx_enrichment_sources_active ON enrichment_sources(is_active);

-- Poblar fuentes de enriquecimiento iniciales
INSERT INTO enrichment_sources (source_name, source_type, base_url, api_key_required, rate_limit_per_minute, rate_limit_per_hour, config) VALUES
('AEMET_API', 'api', 'https://opendata.aemet.es/opendata/api', true, 60, 1000, '{"description": "API meteorológica oficial de España"}'),
('CATASTRO_API', 'api', 'https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC', false, 100, 2000, '{"description": "Sede Electrónica del Catastro"}'),
('OMIE_API', 'api', 'https://www.omie.es/sites/default/files/dados', false, 100, 2000, '{"description": "Operador del Mercado Ibérico de Energía"}'),
('CNMC_Tarifas', 'api', 'https://www.cnmc.es/api', false, 30, 500, '{"description": "Comisión Nacional de Mercados y Competencia"}'),
('REE_Datos', 'api', 'https://apidatos.ree.es', false, 100, 2000, '{"description": "Red Eléctrica de España - datos del sistema"}'),
('INE_Territorio', 'api', 'https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA', false, 50, 1000, '{"description": "Instituto Nacional de Estadística"}'),
('MITECO_Sostenibilidad', 'api', 'https://www.miteco.gob.es/api', false, 20, 200, '{"description": "Ministerio para la Transición Ecológica"}');

-- Verificación final
SELECT 'db_enriquecimiento creada' as status, COUNT(*) as total_tablas 
FROM information_schema.tables 
WHERE table_schema = 'public';
