-- =====================================================
-- CREAR ESTRUCTURA OPTIMIZADA DE DIRECCIONES N1
-- Implementa direcciones especializadas por tipo de entidad
-- =====================================================

-- 1. CREAR TABLA client_address (Dirección fiscal del cliente)
CREATE TABLE client_address (
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

-- 2. CREAR TABLA provider_address (Dirección fiscal del proveedor/comercializadora)
CREATE TABLE provider_address (
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

-- 3. EXPANDIR supply_address existente (mantener datos actuales)
-- Añadir campos que faltan para completar estructura
ALTER TABLE supply_address 
ADD COLUMN IF NOT EXISTS tipo_via VARCHAR(50),
ADD COLUMN IF NOT EXISTS nombre_via VARCHAR(200),
ADD COLUMN IF NOT EXISTS numero VARCHAR(20),
ADD COLUMN IF NOT EXISTS planta VARCHAR(20),
ADD COLUMN IF NOT EXISTS puerta VARCHAR(20),
ADD COLUMN IF NOT EXISTS municipio VARCHAR(100),
ADD COLUMN IF NOT EXISTS comunidad_autonoma VARCHAR(100),
ADD COLUMN IF NOT EXISTS pais VARCHAR(50) DEFAULT 'España',
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 4. CREAR ÍNDICES para todas las tablas de direcciones
CREATE INDEX IF NOT EXISTS idx_client_address_cups ON client_address(cups);
CREATE INDEX IF NOT EXISTS idx_client_address_cp ON client_address(codigo_postal);
CREATE INDEX IF NOT EXISTS idx_client_address_municipio ON client_address(municipio);
CREATE INDEX IF NOT EXISTS idx_client_address_provincia ON client_address(provincia);

CREATE INDEX IF NOT EXISTS idx_provider_address_cups ON provider_address(cups);
CREATE INDEX IF NOT EXISTS idx_provider_address_cp ON provider_address(codigo_postal);
CREATE INDEX IF NOT EXISTS idx_provider_address_municipio ON provider_address(municipio);
CREATE INDEX IF NOT EXISTS idx_provider_address_provincia ON provider_address(provincia);

CREATE INDEX IF NOT EXISTS idx_supply_address_cups ON supply_address(cups);
CREATE INDEX IF NOT EXISTS idx_supply_address_cp ON supply_address(codigo_postal);
CREATE INDEX IF NOT EXISTS idx_supply_address_municipio ON supply_address(municipio);
CREATE INDEX IF NOT EXISTS idx_supply_address_provincia ON supply_address(provincia);

-- 5. CREAR VISTA UNIFICADA para consultas cross-direcciones
CREATE OR REPLACE VIEW direcciones_completas AS
SELECT 
    'client' as tipo_direccion,
    cups,
    codigo_postal,
    municipio,
    provincia,
    comunidad_autonoma,
    CONCAT(tipo_via, ' ', nombre_via, ' ', numero) as direccion_completa
FROM client_address
UNION ALL
SELECT 
    'provider' as tipo_direccion,
    cups,
    codigo_postal,
    municipio,
    provincia,
    comunidad_autonoma,
    CONCAT(tipo_via, ' ', nombre_via, ' ', numero) as direccion_completa
FROM provider_address
UNION ALL
SELECT 
    'supply' as tipo_direccion,
    cups,
    codigo_postal,
    municipio,
    provincia,
    comunidad_autonoma,
    CONCAT(tipo_via, ' ', nombre_via, ' ', numero) as direccion_completa
FROM supply_address;

-- 6. VERIFICAR ESTRUCTURA CREADA
SELECT 
    table_name,
    COUNT(*) as total_columns
FROM information_schema.columns 
WHERE table_name IN ('client_address', 'provider_address', 'supply_address')
    AND table_schema = 'public'
GROUP BY table_name
ORDER BY table_name;

-- =====================================================
-- RESULTADO:
-- - 3 tablas especializadas para direcciones
-- - Estructura completa con 10+ campos descompuestos
-- - Índices optimizados para consultas geográficas
-- - Vista unificada para análisis cross-direcciones
-- =====================================================
