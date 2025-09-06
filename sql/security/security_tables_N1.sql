-- =====================================================
-- CREAR TABLAS DE SEGURIDAD EN db_N1
-- Ejecutar conectado a db_N1
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

-- Crear índices para optimización
CREATE INDEX IF NOT EXISTS idx_client_versions_hash ON client_versions(client_hash);
CREATE INDEX IF NOT EXISTS idx_client_versions_version ON client_versions(version_id);
CREATE INDEX IF NOT EXISTS idx_client_versions_created ON client_versions(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON data_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_user ON data_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_client ON data_audit_log(client_hash);
CREATE INDEX IF NOT EXISTS idx_audit_table ON data_audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_hash_value ON hash_registry(hash_value);
CREATE INDEX IF NOT EXISTS idx_hash_type ON hash_registry(hash_type);

-- Función para limpieza TTL en db_N1 (mantiene datos permanentes, solo limpia logs)
CREATE OR REPLACE FUNCTION cleanup_audit_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Limpiar logs de auditoría antiguos (mantener 2 años)
    DELETE FROM data_audit_log WHERE timestamp < NOW() - INTERVAL '2 years';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Verificación final
SELECT 'Tablas de seguridad creadas en db_N1' as status, 
       COUNT(*) as nuevas_tablas 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('client_versions', 'data_audit_log', 'hash_registry');
