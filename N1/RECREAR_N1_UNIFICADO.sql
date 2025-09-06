-- =====================================================
-- SCRIPT UNIFICADO COMPLETO PARA RECREAR BD N1 
-- Incluye DROP IF EXISTS + CREATE de TODAS las tablas
-- =====================================================

-- Eliminar tablas existentes en orden inverso de dependencias
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS analytics CASCADE;
DROP TABLE IF EXISTS sustainability CASCADE;
DROP TABLE IF EXISTS invoice_summary CASCADE;
DROP TABLE IF EXISTS invoice CASCADE;
DROP TABLE IF EXISTS power_term CASCADE;
DROP TABLE IF EXISTS energy_consumption CASCADE;
DROP TABLE IF EXISTS metering CASCADE;
DROP TABLE IF EXISTS contract CASCADE;
DROP TABLE IF EXISTS supply_address CASCADE;
DROP TABLE IF EXISTS supply_point CASCADE;
DROP TABLE IF EXISTS direccion_fiscal CASCADE;
DROP TABLE IF EXISTS provider CASCADE;
DROP TABLE IF EXISTS client CASCADE;

-- Eliminar índices si existen
DROP INDEX IF EXISTS idx_documents_cups;
DROP INDEX IF EXISTS idx_documents_client;
DROP INDEX IF EXISTS idx_invoice_fecha;
DROP INDEX IF EXISTS idx_analytics_document;
DROP INDEX IF EXISTS idx_energy_consumption_periodo;

-- =====================================================
-- CREAR TABLAS N1 - BASE DE DATOS ENERGÉTICA DEL CLIENTE
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

-- Invoice table (completa de N0 + enriquecimiento)
CREATE TABLE invoice (
    id SERIAL PRIMARY KEY,
    numero_factura VARCHAR(50),
    año INTEGER,
    fecha_inicio_periodo DATE,
    fecha_fin_periodo DATE,
    dias_periodo_facturado INTEGER,
    numero_factura_rectificada VARCHAR(50),
    fecha_cargo DATE,
    total_a_pagar DECIMAL(10,2),
    tipo_iva INTEGER,
    importe_iva DECIMAL(10,2),
    porcentaje_impuesto_electricidad DECIMAL(10,4),
    importe_impuesto_electricidad DECIMAL(10,2),
    bono_social DECIMAL(10,2),
    coste_energia_total DECIMAL(10,2),
    coste_potencia_total DECIMAL(10,2),
    coste_otro_concepto DECIMAL(10,2),
    coste_otro_servicio DECIMAL(10,2),
    coste_promedio_diario_eur DECIMAL(15,12),
    alquiler_contador DECIMAL(10,2),
    ajuste_mecanismo_iberico DECIMAL(10,2),
    descuento_energia DECIMAL(10,2),
    descuento_potencia DECIMAL(10,2),
    descuento_servicio DECIMAL(10,2),
    descuento_otro_concepto DECIMAL(10,2),
    -- Consumos por períodos
    consumo_kwh_p1 INTEGER,
    consumo_kwh_p2 INTEGER,
    consumo_kwh_p3 INTEGER,
    consumo_kwh_p4 INTEGER,
    consumo_kwh_p5 INTEGER,
    consumo_kwh_p6 INTEGER,
    -- Precios peaje por períodos
    precio_peaje_p1 DECIMAL(10,8),
    precio_peaje_p2 DECIMAL(10,8),
    precio_peaje_p3 DECIMAL(10,8),
    precio_peaje_p4 DECIMAL(10,8),
    precio_peaje_p5 DECIMAL(10,8),
    precio_peaje_p6 DECIMAL(10,8),
    -- Precios energía por períodos
    precio_energia_p1 DECIMAL(10,8),
    precio_energia_p2 DECIMAL(10,8),
    precio_energia_p3 DECIMAL(10,8),
    precio_energia_p4 DECIMAL(10,8),
    precio_energia_p5 DECIMAL(10,8),
    precio_energia_p6 DECIMAL(10,8),
    -- Precios cargos por períodos
    precio_cargos_energia_p1 DECIMAL(10,8),
    precio_cargos_energia_p2 DECIMAL(10,8),
    precio_cargos_energia_p3 DECIMAL(10,7),
    precio_cargos_energia_p4 DECIMAL(10,8),
    precio_cargos_energia_p5 DECIMAL(10,8),
    precio_cargos_energia_p6 DECIMAL(10,8),
    -- Margen comercializadora por períodos
    margen_comercializadora_p1 DECIMAL(10,8),
    margen_comercializadora_p2 DECIMAL(10,2),
    margen_comercializadora_p3 DECIMAL(10,2),
    margen_comercializadora_p4 DECIMAL(10,2),
    margen_comercializadora_p5 DECIMAL(10,2),
    margen_comercializadora_p6 DECIMAL(10,2),
    -- Precio total energía por períodos
    precio_total_energia_p1 DECIMAL(10,8),
    precio_total_energia_p2 DECIMAL(10,8),
    precio_total_energia_p3 DECIMAL(10,8),
    precio_total_energia_p4 DECIMAL(10,8),
    precio_total_energia_p5 DECIMAL(10,8),
    precio_total_energia_p6 DECIMAL(10,8),
    -- Costes peaje por períodos
    coste_peaje_p1 DECIMAL(10,2),
    coste_peaje_p2 DECIMAL(10,2),
    coste_peaje_p3 DECIMAL(10,2),
    coste_peaje_p4 DECIMAL(10,2),
    coste_peaje_p5 DECIMAL(10,2),
    coste_peaje_p6 DECIMAL(10,2),
    -- Costes energía por períodos
    coste_energia_p1 DECIMAL(10,2),
    coste_energia_p2 DECIMAL(10,2),
    coste_energia_p3 DECIMAL(10,2),
    coste_energia_p4 DECIMAL(10,2),
    coste_energia_p5 DECIMAL(10,2),
    coste_energia_p6 DECIMAL(10,2),
    -- Costes cargos por períodos
    coste_cargos_energia_p1 DECIMAL(10,2),
    coste_cargos_energia_p2 DECIMAL(10,2),
    coste_cargos_energia_p3 DECIMAL(10,2),
    coste_cargos_energia_p4 DECIMAL(10,2),
    coste_cargos_energia_p5 DECIMAL(10,2),
    coste_cargos_energia_p6 DECIMAL(10,2),
    -- Costes margen comercializadora por períodos
    coste_margen_comercializadora_p1 DECIMAL(10,2),
    coste_margen_comercializadora_p2 DECIMAL(10,2),
    coste_margen_comercializadora_p3 DECIMAL(10,2),
    coste_margen_comercializadora_p4 DECIMAL(10,2),
    coste_margen_comercializadora_p5 DECIMAL(10,2),
    coste_margen_comercializadora_p6 DECIMAL(10,2),
    -- Costes totales por períodos
    coste_total_energia_p1 DECIMAL(10,2),
    coste_total_energia_p2 DECIMAL(10,2),
    coste_total_energia_p3 DECIMAL(10,2),
    coste_total_energia_p4 DECIMAL(10,2),
    coste_total_energia_p5 DECIMAL(10,2),
    coste_total_energia_p6 DECIMAL(10,2),
    -- Precios potencia por períodos
    precio_peaje_potencia_p1 DECIMAL(10,2),
    precio_peaje_potencia_p2 DECIMAL(10,2),
    precio_peaje_potencia_p3 DECIMAL(10,2),
    precio_peaje_potencia_p4 DECIMAL(10,2),
    precio_peaje_potencia_p5 DECIMAL(10,2),
    precio_peaje_potencia_p6 DECIMAL(10,2),
    precio_potencia_p1 DECIMAL(10,7),
    precio_potencia_p2 DECIMAL(10,7),
    precio_potencia_p3 DECIMAL(10,7),
    precio_potencia_p4 DECIMAL(10,7),
    precio_potencia_p5 DECIMAL(10,7),
    precio_potencia_p6 DECIMAL(10,7),
    -- Otros campos de potencia y consumo
    consumo_promedio_diario_kwh DECIMAL(15,12),
    potencia_facturada_p1 DECIMAL(10,1),
    potencia_facturada_p2 DECIMAL(10,1),
    potencia_facturada_p3 DECIMAL(10,1),
    potencia_facturada_p4 DECIMAL(10,1),
    potencia_facturada_p5 DECIMAL(10,1),
    potencia_facturada_p6 DECIMAL(10,1),
    -- Potencias máximas demandadas
    potencia_maxima_demandada_año_kw_p1 DECIMAL(10,2),
    potencia_maxima_demandada_año_kw_p2 DECIMAL(10,2),
    potencia_maxima_demandada_año_kw_p3 DECIMAL(10,2),
    potencia_maxima_demandada_año_kw_p4 DECIMAL(10,2),
    potencia_maxima_demandada_año_kw_p5 DECIMAL(10,2),
    potencia_maxima_demandada_año_kw_p6 DECIMAL(10,2),
    -- Excesos de potencia
    coste_exceso_potencia_p1 DECIMAL(10,2),
    coste_exceso_potencia_p2 DECIMAL(10,2),
    coste_exceso_potencia_p3 DECIMAL(10,2),
    coste_exceso_potencia_p4 DECIMAL(10,2),
    coste_exceso_potencia_p5 DECIMAL(10,2),
    coste_exceso_potencia_p6 DECIMAL(10,2),
    -- Autoconsumo y energía reactiva
    autoconsumo VARCHAR(10),
    energia_vertida_kwh DECIMAL(10,2),
    importe_compensacion_excedentes DECIMAL(10,2),
    -- Energía reactiva por períodos
    consumo_reactiva_p1 DECIMAL(10,2),
    consumo_reactiva_p2 DECIMAL(10,2),
    consumo_reactiva_p3 DECIMAL(10,2),
    consumo_reactiva_p4 DECIMAL(10,2),
    consumo_reactiva_p5 DECIMAL(10,2),
    consumo_reactiva_p6 DECIMAL(10,2),
    -- Penalizaciones reactiva
    penalizacion_reactiva_p1 DECIMAL(10,2),
    penalizacion_reactiva_p2 DECIMAL(10,2),
    penalizacion_reactiva_p3 DECIMAL(10,2),
    penalizacion_reactiva_p4 DECIMAL(10,2),
    penalizacion_reactiva_p5 DECIMAL(10,2),
    penalizacion_reactiva_p6 DECIMAL(10,2),
    -- Totales reactiva
    coste_excesos_energia_reactiva DECIMAL(10,2),
    consumo_reactiva_total DECIMAL(10,2),
    energia_reactiva_facturar_total DECIMAL(10,2),
    -- Otros
    url_qr_comparador_cnmc TEXT,
    -- Campos de enriquecimiento
    variacion_importe_vs_anterior DECIMAL(5,2), -- Porcentaje
    categoria_consumidor VARCHAR(20), -- 'eficiente', 'promedio', 'alto_consumo'
    alertas_consumo TEXT[], -- Array de alertas
    recomendaciones TEXT[], -- Array de recomendaciones
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoice summary table (completa de N0 + enriquecimiento)
CREATE TABLE invoice_summary (
    id SERIAL PRIMARY KEY,
    importe_total_potencia DECIMAL(10,2),
    importe_total_energia DECIMAL(10,2),
    importe_total_reactiva DECIMAL(10,2),
    importe_total_excesos_potencia DECIMAL(10,2),
    importe_total_autoconsumo DECIMAL(10,2),
    importe_impuesto_electrico DECIMAL(10,2),
    importe_alquiler_equipos DECIMAL(10,2),
    importe_otros_conceptos DECIMAL(10,2),
    subtotal_factura DECIMAL(10,2),
    importe_total_iva DECIMAL(10,2),
    total_factura DECIMAL(10,2),
    -- Campos de enriquecimiento
    desglose_porcentual JSONB, -- Porcentajes de cada concepto
    comparativa_mercado DECIMAL(5,2), -- vs precio medio mercado
    indice_eficiencia_coste DECIMAL(5,2), -- KPI de eficiencia
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sustainability table (completa de N0 + enriquecimiento)
CREATE TABLE sustainability (
    id SERIAL PRIMARY KEY,
    energia_origen_renovable DECIMAL(10,2),
    energia_origen_nuclear DECIMAL(10,2),
    energia_origen_cc_gas_natural DECIMAL(10,2),
    energia_origen_cogeneracion_alta_eficiencia DECIMAL(10,2),
    energia_origen_carbon DECIMAL(10,2),
    energia_origen_fuel_gas DECIMAL(10,2),
    energia_origen_otras_no_renovables DECIMAL(10,2),
    emisiones_co2_equivalente DECIMAL(10,2),
    letra_escala_medioambiental VARCHAR(10),
    -- Campos de enriquecimiento
    huella_carbono_kg_co2 DECIMAL(10,2),
    porcentaje_renovable DECIMAL(5,2),
    rating_sostenibilidad VARCHAR(10), -- A, B, C, D, E
    equivalencia_arboles_plantados INTEGER,
    recomendaciones_sostenibilidad TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA NUEVA: Analytics y KPIs
CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    document_id INTEGER,
    -- KPIs de consumo
    consumo_total_kwh DECIMAL(10,2),
    consumo_promedio_mensual DECIMAL(10,2),
    tendencia_consumo VARCHAR(20), -- 'creciente', 'estable', 'decreciente'
    estacionalidad_consumo JSONB, -- Patrones estacionales
    -- KPIs económicos
    coste_kwh_promedio DECIMAL(10,6),
    coste_total_anual_estimado DECIMAL(10,2),
    ahorro_potencial_anual DECIMAL(10,2),
    -- KPIs de eficiencia
    factor_carga DECIMAL(5,4), -- Eficiencia uso potencia
    factor_potencia DECIMAL(5,4), -- Calidad energética
    indice_eficiencia_global DECIMAL(5,2),
    -- Comparativas
    percentil_consumo_similar INTEGER, -- vs consumidores similares
    ranking_eficiencia INTEGER,
    -- Alertas y recomendaciones
    alertas_activas JSONB,
    recomendaciones_activas JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Main documents table (sin metadatos de extracción)
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    id_cups VARCHAR(22),
    id_cups_pais VARCHAR(10),
    client_id INTEGER REFERENCES client(id),
    provider_id INTEGER REFERENCES provider(id),
    supply_point_id INTEGER REFERENCES supply_point(id),
    contract_id INTEGER REFERENCES contract(id),
    metering_id INTEGER REFERENCES metering(id),
    energy_consumption_id INTEGER REFERENCES energy_consumption(id),
    power_term_id INTEGER REFERENCES power_term(id),
    invoice_id INTEGER REFERENCES invoice(id),
    invoice_summary_id INTEGER REFERENCES invoice_summary(id),
    sustainability_id INTEGER REFERENCES sustainability(id),
    analytics_id INTEGER REFERENCES analytics(id),
    -- Campos de enriquecimiento
    estado_procesamiento VARCHAR(20) DEFAULT 'procesado',
    fecha_ultimo_enriquecimiento TIMESTAMP,
    version_enriquecimiento INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimización
CREATE INDEX idx_documents_cups ON documents(id_cups);
CREATE INDEX idx_documents_client ON documents(client_id);
CREATE INDEX idx_invoice_fecha ON invoice(fecha_inicio_periodo, fecha_fin_periodo);
CREATE INDEX idx_analytics_document ON analytics(document_id);
CREATE INDEX idx_energy_consumption_periodo ON energy_consumption(inicio_periodo, fin_periodo);

-- Mensaje final
SELECT 'BD N1 completa creada exitosamente - 13 tablas + 5 índices' as status;
