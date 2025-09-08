-- =====================================================
-- CREAR ESTRUCTURA OPTIMIZADA DE DIRECCIONES N0
-- N0 ya tiene estructura más limpia que N1
-- =====================================================

-- 1. CREAR TABLA client_address para N0
CREATE TABLE IF NOT EXISTS client_address (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    
    -- Campos de dirección descompuesta
    tipo_via VARCHAR(50),
    nombre_via VARCHAR(200),
    numero VARCHAR(20),
    planta VARCHAR(20),
    puerta VARCHAR(20),
    codigo_postal VARCHAR(10),
    poblacion VARCHAR(100),
    municipio VARCHAR(100),
    provincia VARCHAR(100),
    comunidad_autonoma VARCHAR(100),
    pais VARCHAR(50) DEFAULT 'España',
    
    -- Metadatos
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. CREAR TABLA provider_address para N0
CREATE TABLE IF NOT EXISTS provider_address (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    
    -- Campos de dirección descompuesta
    tipo_via VARCHAR(50),
    nombre_via VARCHAR(200),
    numero VARCHAR(20),
    planta VARCHAR(20),
    puerta VARCHAR(20),
    codigo_postal VARCHAR(10),
    poblacion VARCHAR(100),
    municipio VARCHAR(100),
    provincia VARCHAR(100),
    comunidad_autonoma VARCHAR(100),
    pais VARCHAR(50) DEFAULT 'España',
    
    -- Metadatos
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. supply_address N0 YA ESTÁ BIEN - Solo añadir campos que falten
ALTER TABLE supply_address 
ADD COLUMN IF NOT EXISTS document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS cups VARCHAR(22),
ADD COLUMN IF NOT EXISTS direccion_suministro TEXT,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 4. CREAR ÍNDICES para N0
CREATE INDEX IF NOT EXISTS idx_n0_client_address_cups ON client_address(cups);
CREATE INDEX IF NOT EXISTS idx_n0_client_address_cp ON client_address(codigo_postal);
CREATE INDEX IF NOT EXISTS idx_n0_provider_address_cups ON provider_address(cups);
CREATE INDEX IF NOT EXISTS idx_n0_provider_address_cp ON provider_address(codigo_postal);
CREATE INDEX IF NOT EXISTS idx_n0_supply_address_cups ON supply_address(cups);
CREATE INDEX IF NOT EXISTS idx_n0_supply_address_cp ON supply_address(codigo_postal);

-- 5. VERIFICAR ESTRUCTURA CREADA N0
SELECT 
    table_name,
    COUNT(*) as total_columns
FROM information_schema.columns 
WHERE table_name IN ('client_address', 'provider_address', 'supply_address')
    AND table_schema = 'public'
GROUP BY table_name
ORDER BY table_name;

-- =====================================================
-- RESULTADO N0:
-- - 3 tablas especializadas para direcciones
-- - Estructura consistente con N1 pero adaptada a N0
-- - Índices optimizados para consultas
-- =====================================================
