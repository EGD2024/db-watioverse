-- =====================================================
-- ESQUEMA N1 - PARTE 2: TABLAS PRINCIPALES
-- =====================================================

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
