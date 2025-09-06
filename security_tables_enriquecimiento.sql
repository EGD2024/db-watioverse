-- =====================================================
-- ACTUALIZAR TABLAS DE SEGURIDAD EN db_enriquecimiento
-- Ejecutar conectado a db_enriquecimiento
-- =====================================================

-- Actualizar enrichment_queue para usar hashes
ALTER TABLE enrichment_queue 
ADD COLUMN IF NOT EXISTS cups_hash VARCHAR(64),
ADD COLUMN IF NOT EXISTS direccion_hash VARCHAR(64);

-- Actualizar enrichment_cache para TTL automático
ALTER TABLE enrichment_cache 
ADD COLUMN IF NOT EXISTS direccion_hash VARCHAR(64),
ADD COLUMN IF NOT EXISTS cups_hash VARCHAR(64);

-- TABLA: ENRICHMENT_LOG - Log de operaciones de enriquecimiento
DROP TABLE IF EXISTS enrichment_log CASCADE;
CREATE TABLE enrichment_log (
    id SERIAL PRIMARY KEY,
    operation_id UUID DEFAULT gen_random_uuid(),
    direccion_hash VARCHAR(64) NOT NULL,
    api_source VARCHAR(50) NOT NULL,
    request_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_timestamp TIMESTAMP,
    success BOOLEAN DEFAULT FALSE,
    response_size INTEGER,
    api_rate_limit_remaining INTEGER,
    error_message TEXT
);

-- Crear índices para enrichment_log
CREATE INDEX IF NOT EXISTS idx_enrichment_hash ON enrichment_log(direccion_hash);
CREATE INDEX IF NOT EXISTS idx_enrichment_api ON enrichment_log(api_source);
CREATE INDEX IF NOT EXISTS idx_enrichment_timestamp ON enrichment_log(request_timestamp);

-- Función para limpieza TTL en db_enriquecimiento
CREATE OR REPLACE FUNCTION cleanup_expired_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Limpiar cache expirado (90 días)
    DELETE FROM enrichment_cache WHERE created_at < NOW() - INTERVAL '90 days';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Limpiar cola completada (30 días)
    DELETE FROM enrichment_queue 
    WHERE status = 'completed' AND completed_at < NOW() - INTERVAL '30 days';
    
    -- Limpiar logs antiguos (180 días)
    DELETE FROM enrichment_log WHERE request_timestamp < NOW() - INTERVAL '180 days';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Verificación final
SELECT 'Tablas de seguridad actualizadas en db_enriquecimiento' as status,
       COUNT(*) as tablas_existentes
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('enrichment_queue', 'enrichment_cache', 'enrichment_sources', 'enrichment_log');
