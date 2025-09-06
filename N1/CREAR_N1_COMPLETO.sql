-- =====================================================
-- ESQUEMA N1 - BASE DE DATOS ENERGÉTICA DEL CLIENTE
-- Basado en N0 pero sin metadatos de extracción
-- Incluye campos de enriquecimiento y análisis
-- =====================================================

-- Tabla client (sin metadatos de extracción)
CREATE TABLE client (
    id SERIAL PRIMARY KEY,
    nombre_cliente VARCHAR(255),
    nif_titular VARCHAR(50),
    -- Campos de enriquecimiento
    tipo_cliente VARCHAR(20), -- 'residencial', 'comercial', 'industrial'
    segmento_consumo VARCHAR(20), -- 'bajo', 'medio', 'alto'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla provider (completa de N0)
CREATE TABLE provider (
    id SERIAL PRIMARY KEY,
    email_proveedor VARCHAR(255),
    web_proveedor VARCHAR(255),
    entidad_bancaria VARCHAR(255),
    datos_bancarios_iban VARCHAR(50),
    -- Campos de enriquecimiento
    rating_proveedor DECIMAL(3,2), -- Rating del proveedor
    tipo_energia VARCHAR(50), -- 'renovable', 'mixta', 'convencional'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla direccion_fiscal (completa de N0)
CREATE TABLE direccion_fiscal (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES provider(id),
    codigo_postal VARCHAR(10),
    comunidad_autonoma VARCHAR(100),
    municipio VARCHAR(100),
    nombre_via VARCHAR(255),
    numero VARCHAR(100),
    pais VARCHAR(10),
    planta VARCHAR(50),
    poblacion VARCHAR(100),
    provincia VARCHAR(100),
    puerta VARCHAR(20),
    tipo_via VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supply point table (completa de N0)
CREATE TABLE supply_point (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22),
    -- Campos de enriquecimiento
    zona_climatica VARCHAR(10), -- A, B, C, D, E
    tipo_suministro VARCHAR(20), -- 'residencial', 'comercial', 'industrial'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supply address table (completa de N0)
CREATE TABLE supply_address (
    id SERIAL PRIMARY KEY,
    supply_point_id INTEGER REFERENCES supply_point(id),
    codigo_postal VARCHAR(10),
    comunidad_autonoma VARCHAR(100),
    municipio VARCHAR(100),
    nombre_via VARCHAR(255),
    numero VARCHAR(100),
    pais VARCHAR(10),
    planta VARCHAR(50),
    poblacion VARCHAR(100),
    provincia VARCHAR(100),
    puerta VARCHAR(20),
    tipo_via VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla contract (completa de N0 + enriquecimiento)
CREATE TABLE contract (
    id SERIAL PRIMARY KEY,
    comercializadora VARCHAR(255),
    numero_contrato_comercializadora VARCHAR(50),
    fecha_inicio_contrato DATE,
    fecha_fin_contrato DATE,
    distribuidora VARCHAR(255),
    numero_contrato_distribuidora VARCHAR(50),
    cups_electricidad VARCHAR(22),
    nombre_producto VARCHAR(50),
    mercado VARCHAR(10),
    potencia_contratada_p1 INTEGER,
    potencia_contratada_p2 INTEGER,
    potencia_contratada_p3 INTEGER,
    potencia_contratada_p4 INTEGER,
    potencia_contratada_p5 INTEGER,
    potencia_contratada_p6 INTEGER,
    precio_unitario_potencia_p1 DECIMAL(10,7),
    precio_unitario_potencia_p2 DECIMAL(10,7),
    precio_unitario_potencia_p3 DECIMAL(10,7),
    precio_unitario_potencia_p4 DECIMAL(10,7),
    precio_unitario_potencia_p5 DECIMAL(10,7),
    precio_unitario_potencia_p6 DECIMAL(10,7),
    -- Campos de enriquecimiento
    tarifa_acceso VARCHAR(10), -- 2.0TD, 3.0TD, etc.
    potencia_total_contratada DECIMAL(10,2), -- Suma de todos los períodos
    tipo_tarifa VARCHAR(20), -- 'fija', 'indexada', 'discriminacion_horaria'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Metering table (completa de N0)
CREATE TABLE metering (
    id SERIAL PRIMARY KEY,
    numero_contador VARCHAR(50),
    fecha_lectura_inicio_contador DATE,
    fecha_lectura_fin_contador DATE,
    tipo_lectura_contador VARCHAR(20),
    lectura_actual_contador_p1 INTEGER,
    lectura_anterior_contador_p1 INTEGER,
    lectura_actual_contador_p2 INTEGER,
    lectura_anterior_contador_p2 INTEGER,
    lectura_actual_contador_p3 INTEGER,
    lectura_anterior_contador_p3 INTEGER,
    lectura_actual_contador_p4 INTEGER,
    lectura_anterior_contador_p4 INTEGER,
    lectura_actual_contador_p5 INTEGER,
    lectura_anterior_contador_p5 INTEGER,
    lectura_actual_contador_p6 INTEGER,
    lectura_anterior_contador_p6 INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Energy consumption table (completa de N0 + enriquecimiento)
CREATE TABLE energy_consumption (
    id SERIAL PRIMARY KEY,
    inicio_periodo DATE,
    fin_periodo DATE,
    consumo_facturado_mes INTEGER,
    precio_peaje_eur_kwh DECIMAL(10,8),
    precio_energia_eur_kwh DECIMAL(10,8),
    precio_cargos_eur_kwh DECIMAL(10,7),
    margen_comercializadora_eur_kwh DECIMAL(10,8),
    precio_total_energia_eur_kwh DECIMAL(10,8),
    coste_peaje_eur DECIMAL(10,2),
    coste_energia_eur DECIMAL(10,2),
    coste_cargos_eur DECIMAL(10,2),
    coste_margen_comercializadora_eur DECIMAL(10,2),
    coste_total_energia_eur DECIMAL(10,2),
    -- Campos de enriquecimiento
    consumo_promedio_diario DECIMAL(10,2),
    eficiencia_energetica VARCHAR(10), -- A, B, C, D, E, F, G
    variacion_vs_mes_anterior DECIMAL(5,2), -- Porcentaje
    benchmark_consumo_similar DECIMAL(10,2), -- Comparativa
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Power term table (completa de N0 + enriquecimiento)
CREATE TABLE power_term (
    id SERIAL PRIMARY KEY,
    periodo VARCHAR(10),
    potencia_contratada_kw INTEGER,
    dias_facturacion INTEGER,
    precio_peaje_potencia_eur_kw_dia DECIMAL(10,7),
    precio_potencia_eur_kw_dia DECIMAL(10,7),
    precio_cargos_potencia_eur_kw_dia DECIMAL(10,7),
    margen_comercializadora_potencia_eur_kw_dia DECIMAL(10,7),
    precio_total_potencia_eur_kw_dia DECIMAL(10,7),
    coste_peaje_potencia_eur DECIMAL(10,2),
    coste_potencia_eur DECIMAL(10,2),
    coste_cargos_potencia_eur DECIMAL(10,2),
    coste_margen_comercializadora_potencia_eur DECIMAL(10,2),
    coste_total_potencia_eur DECIMAL(10,2),
    -- Campos de enriquecimiento
    utilizacion_potencia DECIMAL(5,2), -- Porcentaje de uso real vs contratada
    recomendacion_potencia VARCHAR(50), -- 'reducir', 'mantener', 'aumentar'
    ahorro_potencial_eur DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CONTINÚA EN SIGUIENTE ARCHIVO...
