-- =====================================================
-- CREACIÓN DE BASE DE DATOS CORE - DATOS MAESTROS
-- Datos de referencia no-PII centralizados
-- Fecha: 2025-09-08
-- Base de datos: db_Ncore
-- =====================================================

-- =====================================================
-- 1. COMERCIALIZADORAS Y TARIFAS
-- =====================================================

CREATE TABLE IF NOT EXISTS core_comercializadoras (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    nif VARCHAR(20) NOT NULL,
    tipo_mercado VARCHAR(20) CHECK (tipo_mercado IN ('libre', 'regulado', 'ambos')),
    activa BOOLEAN DEFAULT TRUE,
    fecha_alta DATE,
    fecha_baja DATE,
    telefono_atencion VARCHAR(20),
    email_contacto VARCHAR(100),
    web VARCHAR(200),
    -- Metadata
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fuente VARCHAR(50) DEFAULT 'CNMC'
);

CREATE TABLE IF NOT EXISTS core_tarifas_comercializadoras (
    id SERIAL PRIMARY KEY,
    comercializadora_id INT REFERENCES core_comercializadoras(id),
    codigo_tarifa VARCHAR(20) NOT NULL,
    nombre_comercial VARCHAR(100),
    tipo_tarifa VARCHAR(50), -- 'indexada', 'fija', 'dual', 'pvpc'
    periodos INT DEFAULT 1,
    precio_base DECIMAL(10,6),
    margen_comercial DECIMAL(10,6),
    vigente_desde DATE NOT NULL,
    vigente_hasta DATE,
    condiciones_especiales TEXT,
    UNIQUE(comercializadora_id, codigo_tarifa, vigente_desde)
);

-- =====================================================
-- 2. DISTRIBUIDORAS Y ZONAS
-- =====================================================

CREATE TABLE IF NOT EXISTS core_distribuidoras (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    nif VARCHAR(20) NOT NULL,
    zona_distribucion VARCHAR(50),
    provincia VARCHAR(100),
    comunidad_autonoma VARCHAR(100),
    activa BOOLEAN DEFAULT TRUE,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 3. TARIFAS REGULADAS (PEAJES Y CARGOS)
-- =====================================================

CREATE TABLE IF NOT EXISTS core_peajes_acceso (
    id SERIAL PRIMARY KEY,
    codigo_tarifa VARCHAR(10) NOT NULL, -- '2.0TD', '3.0TD', '6.1TD', etc.
    descripcion VARCHAR(200),
    tension VARCHAR(20), -- 'BT', 'AT1', 'AT2', 'AT3', 'AT4'
    periodos INT NOT NULL,
    -- Precios por periodo
    precio_potencia_p1 DECIMAL(10,6),
    precio_potencia_p2 DECIMAL(10,6),
    precio_potencia_p3 DECIMAL(10,6),
    precio_potencia_p4 DECIMAL(10,6),
    precio_potencia_p5 DECIMAL(10,6),
    precio_potencia_p6 DECIMAL(10,6),
    precio_energia_p1 DECIMAL(10,6),
    precio_energia_p2 DECIMAL(10,6),
    precio_energia_p3 DECIMAL(10,6),
    precio_energia_p4 DECIMAL(10,6),
    precio_energia_p5 DECIMAL(10,6),
    precio_energia_p6 DECIMAL(10,6),
    -- Vigencia
    vigente_desde DATE NOT NULL,
    vigente_hasta DATE,
    normativa VARCHAR(100),
    fuente VARCHAR(50) DEFAULT 'BOE',
    UNIQUE(codigo_tarifa, vigente_desde)
);

-- =====================================================
-- 4. ZONAS CLIMÁTICAS Y GEOGRAFÍA
-- =====================================================

CREATE TABLE IF NOT EXISTS core_zonas_climaticas (
    id SERIAL PRIMARY KEY,
    codigo_postal VARCHAR(5) UNIQUE NOT NULL,
    municipio VARCHAR(100) NOT NULL,
    provincia VARCHAR(100) NOT NULL,
    comunidad_autonoma VARCHAR(100) NOT NULL,
    zona_climatica_cte VARCHAR(10) NOT NULL, -- 'A3', 'B4', 'C2', 'D3', 'E1'
    altitud INT,
    latitud DECIMAL(10,6),
    longitud DECIMAL(10,6),
    -- Datos climáticos de referencia
    hdd_anual_medio DECIMAL(10,2),
    cdd_anual_medio DECIMAL(10,2),
    temperatura_media_anual DECIMAL(5,2),
    radiacion_global_anual DECIMAL(10,2),
    -- Metadata
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fuente VARCHAR(50) DEFAULT 'CTE+AEMET'
);

-- =====================================================
-- 5. CALENDARIO Y FESTIVOS
-- =====================================================

CREATE TABLE IF NOT EXISTS core_calendario (
    fecha DATE PRIMARY KEY,
    año INT NOT NULL,
    mes INT NOT NULL,
    dia INT NOT NULL,
    dia_semana INT NOT NULL, -- 1=Lunes, 7=Domingo
    semana_año INT NOT NULL,
    trimestre INT NOT NULL,
    es_laborable BOOLEAN DEFAULT TRUE,
    es_festivo_nacional BOOLEAN DEFAULT FALSE,
    periodo_tarifario VARCHAR(2), -- 'P1', 'P2', 'P3', 'P4', 'P5', 'P6'
    estacion VARCHAR(10) -- 'invierno', 'primavera', 'verano', 'otoño'
);

CREATE TABLE IF NOT EXISTS core_festivos (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    tipo VARCHAR(20) NOT NULL, -- 'nacional', 'autonomico', 'local'
    ambito VARCHAR(100), -- NULL para nacional, CCAA o municipio
    descripcion VARCHAR(200),
    UNIQUE(fecha, tipo, ambito)
);

-- =====================================================
-- 6. PRECIOS MERCADO (OMIE)
-- =====================================================

CREATE TABLE IF NOT EXISTS core_precios_omie (
    timestamp_hora TIMESTAMP PRIMARY KEY,
    precio_spot DECIMAL(10,4) NOT NULL, -- €/MWh
    precio_ajuste DECIMAL(10,4),
    precio_final DECIMAL(10,4),
    demanda_prevista DECIMAL(10,2), -- MW
    demanda_real DECIMAL(10,2), -- MW
    -- Estadísticas del día
    precio_medio_dia DECIMAL(10,4),
    precio_max_dia DECIMAL(10,4),
    precio_min_dia DECIMAL(10,4),
    volatilidad_dia DECIMAL(10,4),
    -- Metadata
    fecha_publicacion TIMESTAMP,
    version INT DEFAULT 1
);

-- Índices para consultas rápidas
CREATE INDEX idx_precios_omie_fecha ON core_precios_omie(DATE(timestamp_hora));
CREATE INDEX idx_precios_omie_precio ON core_precios_omie(precio_final);

-- =====================================================
-- 7. FACTORES DE EMISIÓN CO2
-- =====================================================

CREATE TABLE IF NOT EXISTS core_factores_emision (
    id SERIAL PRIMARY KEY,
    tipo_energia VARCHAR(50) NOT NULL, -- 'red_electrica', 'gas_natural', 'gasoleo', etc.
    año INT NOT NULL,
    mes INT,
    factor_emision DECIMAL(10,6) NOT NULL, -- tCO2/MWh o tCO2/kWh
    unidad VARCHAR(20) NOT NULL, -- 'tCO2/MWh', 'kgCO2/kWh'
    ambito VARCHAR(50), -- 'peninsular', 'balear', 'canario'
    fuente VARCHAR(100), -- 'REE', 'MITECO', 'CNMC'
    fecha_publicacion DATE,
    UNIQUE(tipo_energia, año, mes, ambito)
);

-- =====================================================
-- 8. COEFICIENTES DE PASO
-- =====================================================

CREATE TABLE IF NOT EXISTS core_coeficientes_conversion (
    id SERIAL PRIMARY KEY,
    tipo_conversion VARCHAR(50) NOT NULL, -- 'PCS_PCI', 'kWh_termias', etc.
    origen_unidad VARCHAR(20) NOT NULL,
    destino_unidad VARCHAR(20) NOT NULL,
    coeficiente DECIMAL(15,10) NOT NULL,
    aplica_desde DATE NOT NULL,
    aplica_hasta DATE,
    normativa VARCHAR(200),
    notas TEXT,
    UNIQUE(tipo_conversion, aplica_desde)
);

-- =====================================================
-- 9. TABLAS DE CACHÉ Y OPTIMIZACIÓN
-- =====================================================

CREATE TABLE IF NOT EXISTS core_cache_consultas (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64) UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    resultado JSONB NOT NULL,
    fecha_cache TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ttl_segundos INT DEFAULT 3600,
    hits INT DEFAULT 0,
    ultima_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vista materializada para consultas frecuentes
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_tarifas_vigentes AS
SELECT 
    pa.codigo_tarifa,
    pa.descripcion,
    pa.tension,
    pa.periodos,
    pa.precio_potencia_p1,
    pa.precio_potencia_p2,
    pa.precio_potencia_p3,
    pa.precio_energia_p1,
    pa.precio_energia_p2,
    pa.precio_energia_p3,
    pa.vigente_desde,
    pa.vigente_hasta
FROM core_peajes_acceso pa
WHERE pa.vigente_hasta IS NULL 
   OR pa.vigente_hasta >= CURRENT_DATE
WITH DATA;

CREATE UNIQUE INDEX ON mv_tarifas_vigentes(codigo_tarifa);

-- =====================================================
-- ÍNDICES OPTIMIZADOS
-- =====================================================

-- Comercializadoras
CREATE INDEX idx_comercializadoras_activa ON core_comercializadoras(activa);
CREATE INDEX idx_comercializadoras_tipo ON core_comercializadoras(tipo_mercado);

-- Distribuidoras
CREATE INDEX idx_distribuidoras_zona ON core_distribuidoras(zona_distribucion);
CREATE INDEX idx_distribuidoras_provincia ON core_distribuidoras(provincia);

-- Zonas climáticas
CREATE INDEX idx_zonas_provincia ON core_zonas_climaticas(provincia);
CREATE INDEX idx_zonas_climatica ON core_zonas_climaticas(zona_climatica_cte);
CREATE INDEX idx_zonas_coords ON core_zonas_climaticas(latitud, longitud);

-- Calendario
CREATE INDEX idx_calendario_año_mes ON core_calendario(año, mes);
CREATE INDEX idx_calendario_laborable ON core_calendario(es_laborable);
CREATE INDEX idx_calendario_periodo ON core_calendario(periodo_tarifario);

-- Festivos
CREATE INDEX idx_festivos_fecha ON core_festivos(fecha);
CREATE INDEX idx_festivos_tipo ON core_festivos(tipo);

-- Factores emisión
CREATE INDEX idx_emision_tipo_año ON core_factores_emision(tipo_energia, año);

-- =====================================================
-- FUNCIONES ÚTILES
-- =====================================================

-- Función para obtener tarifa vigente
CREATE OR REPLACE FUNCTION get_tarifa_vigente(
    p_codigo_tarifa VARCHAR,
    p_fecha DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    codigo_tarifa VARCHAR,
    descripcion VARCHAR,
    precio_potencia_p1 DECIMAL,
    precio_energia_p1 DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pa.codigo_tarifa,
        pa.descripcion,
        pa.precio_potencia_p1,
        pa.precio_energia_p1
    FROM core_peajes_acceso pa
    WHERE pa.codigo_tarifa = p_codigo_tarifa
      AND pa.vigente_desde <= p_fecha
      AND (pa.vigente_hasta IS NULL OR pa.vigente_hasta >= p_fecha)
    ORDER BY pa.vigente_desde DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Función para obtener zona climática
CREATE OR REPLACE FUNCTION get_zona_climatica(
    p_codigo_postal VARCHAR
)
RETURNS VARCHAR AS $$
DECLARE
    v_zona VARCHAR;
BEGIN
    SELECT zona_climatica_cte 
    INTO v_zona
    FROM core_zonas_climaticas
    WHERE codigo_postal = p_codigo_postal;
    
    RETURN v_zona;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TRIGGERS DE ACTUALIZACIÓN
-- =====================================================

-- Trigger para actualizar fecha_actualizacion
CREATE OR REPLACE FUNCTION update_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_comercializadoras
    BEFORE UPDATE ON core_comercializadoras
    FOR EACH ROW
    EXECUTE FUNCTION update_fecha_actualizacion();

CREATE TRIGGER trigger_update_distribuidoras
    BEFORE UPDATE ON core_distribuidoras
    FOR EACH ROW
    EXECUTE FUNCTION update_fecha_actualizacion();

-- =====================================================
-- COMENTARIOS DE TABLAS
-- =====================================================

COMMENT ON TABLE core_comercializadoras IS 'Catálogo maestro de comercializadoras eléctricas';
COMMENT ON TABLE core_tarifas_comercializadoras IS 'Tarifas ofertadas por cada comercializadora';
COMMENT ON TABLE core_distribuidoras IS 'Catálogo de empresas distribuidoras por zona';
COMMENT ON TABLE core_peajes_acceso IS 'Peajes de acceso regulados por CNMC';
COMMENT ON TABLE core_zonas_climaticas IS 'Zonas climáticas CTE con datos de referencia';
COMMENT ON TABLE core_calendario IS 'Calendario con periodos tarifarios';
COMMENT ON TABLE core_festivos IS 'Festivos nacionales, autonómicos y locales';
COMMENT ON TABLE core_precios_omie IS 'Histórico de precios del mercado eléctrico';
COMMENT ON TABLE core_factores_emision IS 'Factores de emisión CO2 por tipo de energía';
COMMENT ON TABLE core_coeficientes_conversion IS 'Coeficientes de conversión entre unidades';
COMMENT ON TABLE core_cache_consultas IS 'Cache de consultas frecuentes para optimización';
