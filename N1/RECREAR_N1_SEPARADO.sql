-- ============================================================================
-- SCRIPT: RECREAR_N1_SEPARADO.sql
-- DESCRIPCIÓN: Recrear BD N1 con separación clara entre datos base y enriquecimiento
-- FECHA: 2025-01-06
-- ARQUITECTURA: Datos limpios de N0 + Enriquecimiento separado
-- ============================================================================

-- Eliminar tablas existentes en orden inverso de dependencias
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS analytics CASCADE;
DROP TABLE IF EXISTS sustainability_metrics CASCADE;
DROP TABLE IF EXISTS sustainability_base CASCADE;
DROP TABLE IF EXISTS invoice_summary CASCADE;
DROP TABLE IF EXISTS invoice CASCADE;
DROP TABLE IF EXISTS power_term CASCADE;
DROP TABLE IF EXISTS energy_consumption CASCADE;
DROP TABLE IF EXISTS metering CASCADE;
DROP TABLE IF EXISTS supply_point CASCADE;
DROP TABLE IF EXISTS supply_address CASCADE;
DROP TABLE IF EXISTS direccion_fiscal CASCADE;
DROP TABLE IF EXISTS contract CASCADE;
DROP TABLE IF EXISTS provider CASCADE;
DROP TABLE IF EXISTS client CASCADE;
DROP TABLE IF EXISTS metadata CASCADE;

-- ============================================================================
-- SECCIÓN 1: TABLAS BASE (DATOS LIMPIOS DE N0)
-- ============================================================================

-- Client table (datos limpios, sin metadatos de extracción)
CREATE TABLE client (
    id SERIAL PRIMARY KEY,
    nombre_cliente VARCHAR(255),
    nif_titular VARCHAR(20),
    tipo_cliente VARCHAR(50),
    segmento_consumo VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Provider table (datos del proveedor)
CREATE TABLE provider (
    id SERIAL PRIMARY KEY,
    nombre_comercializadora VARCHAR(255),
    nombre_distribuidora VARCHAR(255),
    cif_comercializadora VARCHAR(20),
    cif_distribuidora VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contract table (información contractual)
CREATE TABLE contract (
    id SERIAL PRIMARY KEY,
    numero_contrato VARCHAR(50),
    tarifa_acceso VARCHAR(50),
    tipo_tarifa VARCHAR(50),
    modalidad_contrato VARCHAR(50),
    fecha_inicio_contrato DATE,
    fecha_fin_contrato DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Direccion fiscal table
CREATE TABLE direccion_fiscal (
    id SERIAL PRIMARY KEY,
    direccion_completa TEXT,
    codigo_postal VARCHAR(10),
    poblacion VARCHAR(100),
    provincia VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supply address table
CREATE TABLE supply_address (
    id SERIAL PRIMARY KEY,
    direccion_suministro TEXT,
    codigo_postal_suministro VARCHAR(10),
    poblacion_suministro VARCHAR(100),
    provincia_suministro VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supply point table
CREATE TABLE supply_point (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(50) UNIQUE,
    numero_contador VARCHAR(50),
    tipo_contador VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Metering table (medición de contadores)
CREATE TABLE metering (
    id SERIAL PRIMARY KEY,
    lectura_anterior INTEGER,
    lectura_actual INTEGER,
    fecha_lectura_anterior DATE,
    fecha_lectura_actual DATE,
    consumo_total_kwh INTEGER,
    multiplicador_contador INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Energy consumption table (consumos energéticos base)
CREATE TABLE energy_consumption (
    id SERIAL PRIMARY KEY,
    periodo_facturacion_inicio DATE,
    periodo_facturacion_fin DATE,
    numero_dias_facturados INTEGER,
    -- Consumos por períodos (datos base de factura)
    consumo_kwh_p1 INTEGER,
    consumo_kwh_p2 INTEGER,
    consumo_kwh_p3 INTEGER,
    consumo_kwh_p4 INTEGER,
    consumo_kwh_p5 INTEGER,
    consumo_kwh_p6 INTEGER,
    consumo_total_kwh INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Power term table (términos de potencia base)
CREATE TABLE power_term (
    id SERIAL PRIMARY KEY,
    -- Potencias contratadas
    potencia_contratada_p1 DECIMAL(10,1),
    potencia_contratada_p2 DECIMAL(10,1),
    potencia_contratada_p3 DECIMAL(10,1),
    potencia_contratada_p4 DECIMAL(10,1),
    potencia_contratada_p5 DECIMAL(10,1),
    potencia_contratada_p6 DECIMAL(10,1),
    -- Potencias facturadas
    potencia_facturada_p1 DECIMAL(10,1),
    potencia_facturada_p2 DECIMAL(10,1),
    potencia_facturada_p3 DECIMAL(10,1),
    potencia_facturada_p4 DECIMAL(10,1),
    potencia_facturada_p5 DECIMAL(10,1),
    potencia_facturada_p6 DECIMAL(10,1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoice table (facturación base, datos limpios)
CREATE TABLE invoice (
    id SERIAL PRIMARY KEY,
    numero_factura VARCHAR(50),
    fecha_emision DATE,
    fecha_cargo DATE,
    importe_total DECIMAL(10,2),
    importe_antes_impuestos DECIMAL(10,2),
    tipo_iva INTEGER,
    importe_iva DECIMAL(10,2),
    porcentaje_impuesto_electricidad DECIMAL(10,4),
    importe_impuesto_electricidad DECIMAL(10,2),
    bono_social DECIMAL(10,2),
    coste_energia_total DECIMAL(10,2),
    coste_potencia_total DECIMAL(10,2),
    coste_otro_concepto DECIMAL(10,2),
    coste_otro_servicio DECIMAL(10,2),
    alquiler_contador DECIMAL(10,2),
    ajuste_mecanismo_iberico DECIMAL(10,2),
    -- Descuentos
    descuento_energia DECIMAL(10,2),
    descuento_potencia DECIMAL(10,2),
    descuento_servicio DECIMAL(10,2),
    descuento_otro_concepto DECIMAL(10,2),
    -- Precios por períodos
    precio_peaje_p1 DECIMAL(10,8),
    precio_peaje_p2 DECIMAL(10,8),
    precio_peaje_p3 DECIMAL(10,8),
    precio_peaje_p4 DECIMAL(10,8),
    precio_peaje_p5 DECIMAL(10,8),
    precio_peaje_p6 DECIMAL(10,8),
    precio_energia_p1 DECIMAL(10,7),
    precio_energia_p2 DECIMAL(10,7),
    precio_energia_p3 DECIMAL(10,7),
    precio_energia_p4 DECIMAL(10,7),
    precio_energia_p5 DECIMAL(10,7),
    precio_energia_p6 DECIMAL(10,7),
    precio_potencia_p1 DECIMAL(10,7),
    precio_potencia_p2 DECIMAL(10,7),
    precio_potencia_p3 DECIMAL(10,7),
    precio_potencia_p4 DECIMAL(10,7),
    precio_potencia_p5 DECIMAL(10,7),
    precio_potencia_p6 DECIMAL(10,7),
    -- Otros campos base
    autoconsumo VARCHAR(10),
    energia_reactiva DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoice summary table (resumen de importes)
CREATE TABLE invoice_summary (
    id SERIAL PRIMARY KEY,
    importe_total_periodo DECIMAL(10,2),
    importe_energia_periodo DECIMAL(10,2),
    importe_potencia_periodo DECIMAL(10,2),
    importe_otros_conceptos DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECCIÓN 2: TABLAS DE SOSTENIBILIDAD (MIXTO: BASE + ENRIQUECIMIENTO)
-- ============================================================================

-- Sustainability base (datos que vienen directamente de la factura)
CREATE TABLE sustainability_base (
    id SERIAL PRIMARY KEY,
    -- Mix energético (datos de factura)
    energia_origen_renovable DECIMAL(10,2),
    energia_origen_nuclear DECIMAL(10,2),
    energia_origen_cc_gas_natural DECIMAL(10,2),
    energia_origen_cogeneracion_alta_eficiencia DECIMAL(10,2),
    energia_origen_carbon DECIMAL(10,2),
    energia_origen_fuel_gas DECIMAL(10,2),
    energia_origen_otras_no_renovables DECIMAL(10,2),
    -- Emisiones (datos de factura)
    emisiones_co2_equivalente DECIMAL(10,2),
    letra_escala_medioambiental VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sustainability metrics (datos calculados/enriquecimiento)
CREATE TABLE sustainability_metrics (
    id SERIAL PRIMARY KEY,
    sustainability_base_id INTEGER REFERENCES sustainability_base(id),
    -- Métricas calculadas
    huella_carbono_kg_co2 DECIMAL(10,2),
    porcentaje_renovable DECIMAL(5,2),
    rating_sostenibilidad VARCHAR(10), -- A, B, C, D, E
    equivalencia_arboles_plantados INTEGER,
    -- Comparativas y benchmarks
    percentil_sostenibilidad_sector DECIMAL(5,2),
    mejora_vs_mes_anterior DECIMAL(5,2),
    -- Recomendaciones
    recomendaciones_sostenibilidad TEXT[],
    potencial_ahorro_co2_kg DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECCIÓN 3: TABLAS DE ENRIQUECIMIENTO PURO
-- ============================================================================

-- Analytics table (KPIs y métricas calculadas)
CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    document_id INTEGER,
    -- KPIs energéticos
    consumo_promedio_diario_kwh DECIMAL(15,12),
    coste_promedio_diario_eur DECIMAL(15,12),
    eficiencia_energetica_ratio DECIMAL(10,4),
    -- Ratios de costes
    ratio_coste_energia_potencia DECIMAL(10,4),
    ratio_peaje_energia DECIMAL(10,4),
    coste_kwh_medio DECIMAL(10,6),
    -- Comparativas temporales
    variacion_consumo_vs_mes_anterior DECIMAL(5,2),
    variacion_coste_vs_mes_anterior DECIMAL(5,2),
    -- Análisis de períodos
    periodo_mayor_consumo VARCHAR(10), -- P1, P2, etc.
    periodo_mayor_coste VARCHAR(10),
    concentracion_consumo_punta DECIMAL(5,2), -- % en P1-P2
    -- Alertas y recomendaciones
    alertas_consumo TEXT[],
    recomendaciones_ahorro TEXT[],
    potencial_ahorro_eur DECIMAL(10,2),
    -- Benchmarking
    percentil_consumo_sector DECIMAL(5,2),
    percentil_coste_sector DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECCIÓN 4: TABLA MAESTRA Y CONTROL
-- ============================================================================

-- Documents table (tabla maestra con referencias)
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    -- Referencias a tablas base
    client_id INTEGER REFERENCES client(id),
    provider_id INTEGER REFERENCES provider(id),
    contract_id INTEGER REFERENCES contract(id),
    direccion_fiscal_id INTEGER REFERENCES direccion_fiscal(id),
    supply_address_id INTEGER REFERENCES supply_address(id),
    supply_point_id INTEGER REFERENCES supply_point(id),
    metering_id INTEGER REFERENCES metering(id),
    energy_consumption_id INTEGER REFERENCES energy_consumption(id),
    power_term_id INTEGER REFERENCES power_term(id),
    invoice_id INTEGER REFERENCES invoice(id),
    invoice_summary_id INTEGER REFERENCES invoice_summary(id),
    -- Referencias a sostenibilidad
    sustainability_base_id INTEGER REFERENCES sustainability_base(id),
    sustainability_metrics_id INTEGER REFERENCES sustainability_metrics(id),
    -- Referencias a enriquecimiento
    analytics_id INTEGER REFERENCES analytics(id),
    -- Campos de control
    estado_procesamiento VARCHAR(20) DEFAULT 'procesado',
    origen_datos VARCHAR(20) DEFAULT 'N0',
    fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version_esquema VARCHAR(10) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Metadata table (control de traslado N0 → N1)
CREATE TABLE metadata (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECCIÓN 5: ÍNDICES DE OPTIMIZACIÓN
-- ============================================================================

-- Índices para tablas base
CREATE INDEX idx_client_nif ON client(nif_titular);
CREATE INDEX idx_supply_point_cups ON supply_point(cups);
CREATE INDEX idx_invoice_numero ON invoice(numero_factura);
CREATE INDEX idx_invoice_fecha_emision ON invoice(fecha_emision);
CREATE INDEX idx_energy_consumption_periodo ON energy_consumption(periodo_facturacion_inicio, periodo_facturacion_fin);

-- Índices para enriquecimiento
CREATE INDEX idx_analytics_document_id ON analytics(document_id);
CREATE INDEX idx_sustainability_metrics_base_id ON sustainability_metrics(sustainability_base_id);

-- Índices para tabla maestra
CREATE INDEX idx_documents_client_id ON documents(client_id);
CREATE INDEX idx_documents_fecha_procesamiento ON documents(fecha_procesamiento);
CREATE INDEX idx_documents_estado ON documents(estado_procesamiento);

-- ============================================================================
-- COMENTARIOS FINALES
-- ============================================================================

-- ARQUITECTURA IMPLEMENTADA:
-- 1. DATOS BASE: Tablas limpias que reciben datos directos de N0
-- 2. SOSTENIBILIDAD MIXTA: 
--    - sustainability_base: Datos de factura (mix energético, emisiones)
--    - sustainability_metrics: Cálculos y KPIs derivados
-- 3. ENRIQUECIMIENTO: analytics con KPIs, ratios y recomendaciones
-- 4. CONTROL: documents (maestra) + metadata (traslado)

-- FLUJO DE DATOS:
-- N0 → Tablas BASE + sustainability_base
-- Procesamiento → sustainability_metrics + analytics
-- Consultas → JOIN documents con tablas específicas según necesidad
