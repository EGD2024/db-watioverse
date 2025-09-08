-- =====================================================
-- CORRECCIÓN DE LONGITUD DEL CAMPO direccion_hash
-- =====================================================
-- Fecha: 2025-01-07
-- Propósito: Corregir la longitud del campo direccion_hash
-- Base de datos: db_enriquecimiento

-- OPCIÓN 1: Eliminar y recrear la tabla (CUIDADO: borra datos existentes)
DROP TABLE IF EXISTS enriched_data CASCADE;

-- OPCIÓN 2: Modificar la tabla existente (RECOMENDADO si hay datos)
-- ALTER TABLE enriched_data ALTER COLUMN direccion_hash TYPE VARCHAR(40);

-- Recrear la tabla con la longitud correcta
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

-- Recrear índices
CREATE INDEX IF NOT EXISTS idx_enriched_data_lookup 
ON enriched_data(direccion_hash, codigo_postal, periodo, source_type);

CREATE INDEX IF NOT EXISTS idx_enriched_data_expires 
ON enriched_data(expires_at) WHERE expires_at IS NOT NULL;

-- Verificar la estructura
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'enriched_data' 
AND column_name = 'direccion_hash';
