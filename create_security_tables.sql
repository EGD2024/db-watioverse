-- =====================================================
-- CREAR TABLAS DE SEGURIDAD Y VERSIONADO
-- Ejecutar en db_N1 para soporte de versionado
-- =====================================================

-- TABLA: CLIENT_VERSIONS - Versionado completo de datos de cliente
DROP TABLE IF EXISTS client_versions CASCADE;
CREATE TABLE client_versions (
    id SERIAL PRIMARY KEY,
    version_id VARCHAR(50) NOT NULL,
    client_hash VARCHAR(64) NOT NULL,
    source_priority INTEGER NOT NULL, -- 1=factura, 2=cuestionario, 3=enriquecimiento, 4=estimacion
    enrichment_timestamp TIMESTAMP,
    data_quality_score DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changes_summary JSONB,
    
    UNIQUE(version_id, client_hash)
);

-- TABLA: DATA_AUDIT_LOG - Auditoría de acceso a datos personales
DROP TABLE IF EXISTS data_audit_log CASCADE;
CREATE TABLE data_audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(50) NOT NULL,
    operation VARCHAR(20) NOT NULL, -- SELECT, INSERT, UPDATE, DELETE
    table_name VARCHAR(50) NOT NULL,
    client_hash VARCHAR(64),
    ip_address INET,
    user_agent TEXT,
    details JSONB
);

-- TABLA: HASH_REGISTRY - Registro de hashes para trazabilidad
DROP TABLE IF EXISTS hash_registry CASCADE;
CREATE TABLE hash_registry (
    id SERIAL PRIMARY KEY,
    hash_value VARCHAR(64) NOT NULL UNIQUE,
    hash_type VARCHAR(20) NOT NULL, -- client, direccion, cups
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 1
);

-- Crear índices para tablas de seguridad
CREATE INDEX IF NOT EXISTS idx_client_versions_hash ON client_versions(client_hash);
CREATE INDEX IF NOT EXISTS idx_client_versions_version ON client_versions(version_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON data_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_user ON data_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_client ON data_audit_log(client_hash);
CREATE INDEX IF NOT EXISTS idx_audit_table ON data_audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_hash_value ON hash_registry(hash_value);
CREATE INDEX IF NOT EXISTS idx_hash_type ON hash_registry(hash_type);

-- =====================================================
-- EJECUTAR EN db_enriquecimiento
-- =====================================================

-- Ya existe enrichment_queue, enrichment_cache, enrichment_sources
-- Agregar campos de TTL y auditoría

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

-- =====================================================
-- EJECUTAR EN TODAS LAS BASES TEMPORALES
-- =====================================================

-- Función para limpieza automática de TTL
CREATE OR REPLACE FUNCTION cleanup_expired_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    table_record RECORD;
BEGIN
    -- Limpiar tabla actual según TTL configurado
    -- Esta función se debe personalizar para cada BD
    
    CASE current_database()
        WHEN 'db_N0' THEN
            DELETE FROM documents WHERE created_at < NOW() - INTERVAL '30 days';
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            
        WHEN 'db_clima' THEN
            DELETE FROM weather_cache WHERE created_at < NOW() - INTERVAL '30 days';
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            
        WHEN 'db_enriquecimiento' THEN
            DELETE FROM enrichment_cache WHERE created_at < NOW() - INTERVAL '90 days';
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            
        WHEN 'db_encuesta' THEN
            DELETE FROM questionnaire_sessions WHERE created_at < NOW() - INTERVAL '365 days';
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            
        ELSE
            -- No hacer nada para otras BDs
            deleted_count := 0;
    END CASE;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Verificación final
SELECT 'Tablas de seguridad creadas' as status, 
       COUNT(*) as nuevas_tablas 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('client_versions', 'data_audit_log', 'hash_registry', 'enrichment_log');
