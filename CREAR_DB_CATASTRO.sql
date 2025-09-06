-- =====================================================
-- CREAR ESTRUCTURA db_catastro
-- Base de datos de información catastral
-- Ejecutar conectado a db_catastro
-- =====================================================

-- TABLA 1: CADASTRAL_DATA - Datos catastrales por referencia
DROP TABLE IF EXISTS cadastral_data CASCADE;
CREATE TABLE cadastral_data (
    id SERIAL PRIMARY KEY,
    referencia_catastral VARCHAR(20) NOT NULL UNIQUE,
    cups VARCHAR(22),
    direccion TEXT,
    codigo_postal VARCHAR(10),
    municipio VARCHAR(100),
    provincia VARCHAR(100),
    
    -- Datos del inmueble
    uso_principal VARCHAR(50),
    superficie_construida DECIMAL(10,2),
    superficie_parcela DECIMAL(10,2),
    ano_construccion INTEGER,
    tipo_via VARCHAR(50),
    nombre_via VARCHAR(200),
    numero VARCHAR(10),
    
    -- Coordenadas
    latitud DECIMAL(10,6),
    longitud DECIMAL(10,6),
    
    -- Metadatos
    fecha_consulta DATE,
    fuente VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 2: BUILDING_CHARACTERISTICS - Características edificios
DROP TABLE IF EXISTS building_characteristics CASCADE;
CREATE TABLE building_characteristics (
    id SERIAL PRIMARY KEY,
    referencia_catastral VARCHAR(20) REFERENCES cadastral_data(referencia_catastral),
    
    -- Características constructivas
    numero_plantas INTEGER,
    numero_viviendas INTEGER,
    tipo_construccion VARCHAR(50), -- unifamiliar, plurifamiliar, industrial
    calidad_construccion VARCHAR(20), -- alta, media, baja
    estado_conservacion VARCHAR(20), -- bueno, regular, malo
    
    -- Instalaciones
    tiene_ascensor BOOLEAN,
    tiene_garaje BOOLEAN,
    tiene_trastero BOOLEAN,
    tiene_piscina BOOLEAN,
    tiene_calefaccion BOOLEAN,
    tiene_aire_acondicionado BOOLEAN,
    
    -- Reforma y mejoras
    ano_ultima_reforma INTEGER,
    tipo_reforma VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 3: ENERGY_CERTIFICATES - Certificados energéticos
DROP TABLE IF EXISTS energy_certificates CASCADE;
CREATE TABLE energy_certificates (
    id SERIAL PRIMARY KEY,
    referencia_catastral VARCHAR(20) REFERENCES cadastral_data(referencia_catastral),
    cups VARCHAR(22),
    
    -- Calificación energética
    calificacion_energetica VARCHAR(1), -- A, B, C, D, E, F, G
    consumo_energia_primaria DECIMAL(10,2), -- kWh/m²año
    emisiones_co2 DECIMAL(10,2), -- kgCO2/m²año
    
    -- Detalles certificado
    fecha_certificado DATE,
    fecha_validez DATE,
    numero_registro VARCHAR(50),
    tecnico_certificador VARCHAR(200),
    
    -- Recomendaciones mejora
    mejoras_propuestas TEXT,
    ahorro_estimado_porcentaje DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 4: CADASTRAL_CACHE - Cache de consultas
DROP TABLE IF EXISTS cadastral_cache CASCADE;
CREATE TABLE cadastral_cache (
    id SERIAL PRIMARY KEY,
    query_key VARCHAR(100) NOT NULL UNIQUE,
    query_type VARCHAR(50), -- referencia, direccion, cups
    response_data JSONB,
    
    -- Control cache
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimización
CREATE INDEX idx_cadastral_data_ref ON cadastral_data(referencia_catastral);
CREATE INDEX idx_cadastral_data_cups ON cadastral_data(cups);
CREATE INDEX idx_cadastral_data_cp ON cadastral_data(codigo_postal);
CREATE INDEX idx_building_char_ref ON building_characteristics(referencia_catastral);
CREATE INDEX idx_energy_cert_ref ON energy_certificates(referencia_catastral);
CREATE INDEX idx_energy_cert_cups ON energy_certificates(cups);
CREATE INDEX idx_cadastral_cache_key ON cadastral_cache(query_key);
CREATE INDEX idx_cadastral_cache_expires ON cadastral_cache(expires_at);

-- Verificación final
SELECT 'db_catastro creada' as status, COUNT(*) as total_tablas 
FROM information_schema.tables 
WHERE table_schema = 'public';
