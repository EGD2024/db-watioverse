-- =====================================================
-- RECREAR BD N1 CON ESTRUCTURA SEPARADA
-- Base de datos N1: Datos energéticos limpios + enriquecimiento
-- Arquitectura modular con separación clara de responsabilidades
-- =====================================================

-- Eliminar BD N1 existente si existe
DROP DATABASE IF EXISTS N1;

-- Crear BD N1
CREATE DATABASE N1
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'es_ES.UTF-8'
    LC_CTYPE = 'es_ES.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Conectar a BD N1
\c N1;

-- =====================================================
-- TABLA MAESTRA: DOCUMENTS
-- Control principal de documentos procesados
-- =====================================================
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) UNIQUE NOT NULL,
    cliente TEXT NOT NULL,
    direccion TEXT NOT NULL,
    nif VARCHAR(20),
    fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version_pipeline VARCHAR(10) DEFAULT '1.0',
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para tabla documents
CREATE INDEX idx_documents_cups ON documents(cups);
CREATE INDEX idx_documents_cliente ON documents(cliente);
CREATE INDEX idx_documents_fecha ON documents(fecha_procesamiento);

-- =====================================================
-- TABLA CONTROL: METADATA
-- Metadatos de procesamiento y trazabilidad
-- =====================================================
CREATE TABLE metadata (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    fecha_generacion TIMESTAMP NOT NULL,
    fuente_origen VARCHAR(50) DEFAULT 'N0_to_N1_pipeline',
    campos_totales INTEGER,
    enriquecimiento_aplicado BOOLEAN DEFAULT FALSE,
    version_pipeline VARCHAR(10) DEFAULT '1.0',
    hash_datos VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para tabla metadata
CREATE INDEX idx_metadata_cups ON metadata(cups);
CREATE INDEX idx_metadata_fecha ON metadata(fecha_generacion);

-- =====================================================
-- TABLAS BASE: DATOS LIMPIOS SIN METADATOS
-- =====================================================

-- Tabla CLIENT: Datos del cliente
CREATE TABLE client (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    cliente TEXT NOT NULL,
    nif VARCHAR(20),
    direccion TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_client_cups ON client(cups);

-- Tabla CONTRACT: Datos del contrato
CREATE TABLE contract (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo_facturacion VARCHAR(7), -- YYYY-MM
    fecha_inicio DATE,
    fecha_fin DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_contract_cups ON contract(cups);
CREATE INDEX idx_contract_periodo ON contract(periodo_facturacion);

-- Tabla INVOICE: Datos de facturación
CREATE TABLE invoice (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    fecha_emision DATE,
    consumo_facturado_kwh DECIMAL(10,3),
    importe_total DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_invoice_cups ON invoice(cups);
CREATE INDEX idx_invoice_fecha ON invoice(fecha_emision);

-- =====================================================
-- TABLAS CONSUMO POR PERÍODOS (P1-P6)
-- =====================================================

CREATE TABLE consumption_p1 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P1',
    consumo_kwh DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE consumption_p2 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P2',
    consumo_kwh DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE consumption_p3 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P3',
    consumo_kwh DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE consumption_p4 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P4',
    consumo_kwh DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE consumption_p5 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P5',
    consumo_kwh DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE consumption_p6 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P6',
    consumo_kwh DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para tablas consumption
CREATE INDEX idx_consumption_p1_cups ON consumption_p1(cups);
CREATE INDEX idx_consumption_p2_cups ON consumption_p2(cups);
CREATE INDEX idx_consumption_p3_cups ON consumption_p3(cups);
CREATE INDEX idx_consumption_p4_cups ON consumption_p4(cups);
CREATE INDEX idx_consumption_p5_cups ON consumption_p5(cups);
CREATE INDEX idx_consumption_p6_cups ON consumption_p6(cups);

-- =====================================================
-- TABLAS COSTE POR PERÍODOS (P1-P6)
-- =====================================================

CREATE TABLE cost_p1 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P1',
    coste_energia DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_p2 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P2',
    coste_energia DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_p3 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P3',
    coste_energia DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_p4 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P4',
    coste_energia DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_p5 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P5',
    coste_energia DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_p6 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P6',
    coste_energia DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para tablas cost
CREATE INDEX idx_cost_p1_cups ON cost_p1(cups);
CREATE INDEX idx_cost_p2_cups ON cost_p2(cups);
CREATE INDEX idx_cost_p3_cups ON cost_p3(cups);
CREATE INDEX idx_cost_p4_cups ON cost_p4(cups);
CREATE INDEX idx_cost_p5_cups ON cost_p5(cups);
CREATE INDEX idx_cost_p6_cups ON cost_p6(cups);

-- =====================================================
-- TABLAS POTENCIA POR PERÍODOS (P1-P6)
-- =====================================================

CREATE TABLE power_p1 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P1',
    potencia_contratada DECIMAL(8,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE power_p2 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P2',
    potencia_contratada DECIMAL(8,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE power_p3 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P3',
    potencia_contratada DECIMAL(8,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE power_p4 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P4',
    potencia_contratada DECIMAL(8,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE power_p5 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P5',
    potencia_contratada DECIMAL(8,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE power_p6 (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    periodo VARCHAR(2) DEFAULT 'P6',
    potencia_contratada DECIMAL(8,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para tablas power
CREATE INDEX idx_power_p1_cups ON power_p1(cups);
CREATE INDEX idx_power_p2_cups ON power_p2(cups);
CREATE INDEX idx_power_p3_cups ON power_p3(cups);
CREATE INDEX idx_power_p4_cups ON power_p4(cups);
CREATE INDEX idx_power_p5_cups ON power_p5(cups);
CREATE INDEX idx_power_p6_cups ON power_p6(cups);

-- =====================================================
-- TABLAS SOSTENIBILIDAD
-- =====================================================

-- Tabla SUSTAINABILITY_BASE: Datos directos de factura
CREATE TABLE sustainability_base (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    mix_energetico_renovable_pct DECIMAL(5,2),
    mix_energetico_cogeneracion_pct DECIMAL(5,2),
    mix_energetico_residuos_pct DECIMAL(5,2),
    emisiones_co2_kg_kwh DECIMAL(8,6),
    residuos_radiactivos_mg_kwh DECIMAL(8,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sustainability_base_cups ON sustainability_base(cups);

-- Tabla SUSTAINABILITY_METRICS: Datos calculados
CREATE TABLE sustainability_metrics (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    huella_carbono_kg DECIMAL(10,2),
    rating_sostenibilidad VARCHAR(1), -- A, B, C, D, E
    ahorro_potencial_eur DECIMAL(10,2),
    recomendacion_mejora TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sustainability_metrics_cups ON sustainability_metrics(cups);
CREATE INDEX idx_sustainability_metrics_rating ON sustainability_metrics(rating_sostenibilidad);

-- =====================================================
-- TABLA ANALYTICS: ENRIQUECIMIENTO Y KPIS
-- =====================================================

CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL REFERENCES documents(cups) ON DELETE CASCADE,
    -- Geolocalización
    latitud DECIMAL(10,8),
    longitud DECIMAL(11,8),
    -- Datos climáticos
    precipitacion_mm DECIMAL(6,2),
    temperatura_media_c DECIMAL(4,2),
    -- Precios OMIE
    precio_omie_kwh DECIMAL(8,6),
    precio_omie_mwh DECIMAL(8,3),
    -- KPIs calculados
    ratio_precio_mercado DECIMAL(6,4),
    eficiencia_energetica DECIMAL(8,2), -- kWh/día
    coste_kwh_promedio DECIMAL(8,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analytics_cups ON analytics(cups);
CREATE INDEX idx_analytics_geo ON analytics(latitud, longitud);
CREATE INDEX idx_analytics_precio ON analytics(precio_omie_kwh);

-- =====================================================
-- TRIGGERS PARA UPDATED_AT
-- =====================================================

-- Función para actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para tablas con updated_at
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_client_updated_at BEFORE UPDATE ON client FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_contract_updated_at BEFORE UPDATE ON contract FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_invoice_updated_at BEFORE UPDATE ON invoice FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sustainability_base_updated_at BEFORE UPDATE ON sustainability_base FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sustainability_metrics_updated_at BEFORE UPDATE ON sustainability_metrics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_analytics_updated_at BEFORE UPDATE ON analytics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- VISTAS ÚTILES PARA CONSULTAS
-- =====================================================

-- Vista completa de datos N1 por CUPS
CREATE VIEW v_n1_completo AS
SELECT 
    d.cups,
    d.cliente,
    d.direccion,
    d.nif,
    c.periodo_facturacion,
    c.fecha_inicio,
    c.fecha_fin,
    i.fecha_emision,
    i.consumo_facturado_kwh,
    i.importe_total,
    -- Consumos por períodos
    cp1.consumo_kwh as consumo_p1,
    cp2.consumo_kwh as consumo_p2,
    cp3.consumo_kwh as consumo_p3,
    -- Sostenibilidad
    sb.mix_energetico_renovable_pct,
    sb.emisiones_co2_kg_kwh,
    sm.rating_sostenibilidad,
    sm.huella_carbono_kg,
    -- Analytics
    a.latitud,
    a.longitud,
    a.precio_omie_kwh,
    a.coste_kwh_promedio,
    a.ratio_precio_mercado,
    -- Metadatos
    d.fecha_procesamiento,
    d.version_pipeline
FROM documents d
LEFT JOIN client cl ON d.cups = cl.cups
LEFT JOIN contract c ON d.cups = c.cups
LEFT JOIN invoice i ON d.cups = i.cups
LEFT JOIN consumption_p1 cp1 ON d.cups = cp1.cups
LEFT JOIN consumption_p2 cp2 ON d.cups = cp2.cups
LEFT JOIN consumption_p3 cp3 ON d.cups = cp3.cups
LEFT JOIN sustainability_base sb ON d.cups = sb.cups
LEFT JOIN sustainability_metrics sm ON d.cups = sm.cups
LEFT JOIN analytics a ON d.cups = a.cups
WHERE d.activo = TRUE;

-- Vista resumen por cliente
CREATE VIEW v_resumen_cliente AS
SELECT 
    cl.cliente,
    COUNT(d.cups) as total_cups,
    AVG(i.consumo_facturado_kwh) as consumo_promedio,
    AVG(i.importe_total) as importe_promedio,
    AVG(a.coste_kwh_promedio) as coste_kwh_promedio,
    AVG(sb.mix_energetico_renovable_pct) as renovable_promedio,
    COUNT(CASE WHEN sm.rating_sostenibilidad IN ('A','B') THEN 1 END) as cups_sostenibles
FROM documents d
JOIN client cl ON d.cups = cl.cups
LEFT JOIN invoice i ON d.cups = i.cups
LEFT JOIN sustainability_base sb ON d.cups = sb.cups
LEFT JOIN sustainability_metrics sm ON d.cups = sm.cups
LEFT JOIN analytics a ON d.cups = a.cups
WHERE d.activo = TRUE
GROUP BY cl.cliente;

-- =====================================================
-- PERMISOS Y CONFIGURACIÓN
-- =====================================================

-- Otorgar permisos al usuario postgres
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Configurar parámetros de BD
ALTER DATABASE N1 SET timezone TO 'Europe/Madrid';

-- =====================================================
-- COMENTARIOS EN TABLAS
-- =====================================================

COMMENT ON DATABASE N1 IS 'Base de datos N1: Datos energéticos limpios con enriquecimiento para eSCORE';

COMMENT ON TABLE documents IS 'Tabla maestra de documentos procesados en N1';
COMMENT ON TABLE metadata IS 'Metadatos de procesamiento y trazabilidad N0→N1';
COMMENT ON TABLE client IS 'Datos limpios del cliente sin metadatos de extracción';
COMMENT ON TABLE contract IS 'Datos del contrato energético';
COMMENT ON TABLE invoice IS 'Datos de facturación principal';
COMMENT ON TABLE sustainability_base IS 'Datos de sostenibilidad directos de factura';
COMMENT ON TABLE sustainability_metrics IS 'Métricas de sostenibilidad calculadas';
COMMENT ON TABLE analytics IS 'Datos de enriquecimiento: geolocalización, clima, OMIE, KPIs';

-- Comentarios en columnas clave
COMMENT ON COLUMN documents.cups IS 'Código Único de Punto de Suministro - clave primaria';
COMMENT ON COLUMN analytics.latitud IS 'Latitud obtenida por geocodificación de dirección';
COMMENT ON COLUMN analytics.precio_omie_kwh IS 'Precio OMIE €/kWh del período de facturación';
COMMENT ON COLUMN sustainability_metrics.rating_sostenibilidad IS 'Rating A-E basado en % energía renovable';

-- =====================================================
-- FINALIZACIÓN
-- =====================================================

-- Mostrar resumen de tablas creadas
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- Mostrar estadísticas finales
SELECT 
    'N1 RECREADA EXITOSAMENTE' as status,
    COUNT(*) as total_tablas
FROM pg_tables 
WHERE schemaname = 'public';

ANALYZE;
