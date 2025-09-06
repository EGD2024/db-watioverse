-- =====================================================
-- CREAR TABLAS EN db_N1 CON CUESTIONARIOS DINÁMICOS
-- Base de datos db_N1: Datos energéticos limpios + enriquecimiento + cuestionarios
-- Ejecutar este script conectado a la BD db_N1
-- =====================================================

-- Eliminar tablas existentes si existen (en orden inverso por dependencias)
DROP TABLE IF EXISTS questionnaire_analytics CASCADE;
DROP TABLE IF EXISTS questionnaire_responses CASCADE;
DROP TABLE IF EXISTS questionnaire_sessions CASCADE;
DROP TABLE IF EXISTS questionnaire_conditions CASCADE;
DROP TABLE IF EXISTS questionnaire_questions CASCADE;
DROP TABLE IF EXISTS analytics CASCADE;
DROP TABLE IF EXISTS sustainability_metrics CASCADE;
DROP TABLE IF EXISTS sustainability_base CASCADE;
DROP TABLE IF EXISTS power_p6 CASCADE;
DROP TABLE IF EXISTS power_p5 CASCADE;
DROP TABLE IF EXISTS power_p4 CASCADE;
DROP TABLE IF EXISTS power_p3 CASCADE;
DROP TABLE IF EXISTS power_p2 CASCADE;
DROP TABLE IF EXISTS power_p1 CASCADE;
DROP TABLE IF EXISTS cost_p6 CASCADE;
DROP TABLE IF EXISTS cost_p5 CASCADE;
DROP TABLE IF EXISTS cost_p4 CASCADE;
DROP TABLE IF EXISTS cost_p3 CASCADE;
DROP TABLE IF EXISTS cost_p2 CASCADE;
DROP TABLE IF EXISTS cost_p1 CASCADE;
DROP TABLE IF EXISTS consumption_p6 CASCADE;
DROP TABLE IF EXISTS consumption_p5 CASCADE;
DROP TABLE IF EXISTS consumption_p4 CASCADE;
DROP TABLE IF EXISTS consumption_p3 CASCADE;
DROP TABLE IF EXISTS consumption_p2 CASCADE;
DROP TABLE IF EXISTS consumption_p1 CASCADE;
DROP TABLE IF EXISTS billing_base CASCADE;
DROP TABLE IF EXISTS billing_period CASCADE;
DROP TABLE IF EXISTS provider_base CASCADE;
DROP TABLE IF EXISTS contract_base CASCADE;
DROP TABLE IF EXISTS client_base CASCADE;
DROP TABLE IF EXISTS metadata CASCADE;
DROP TABLE IF EXISTS documents CASCADE;

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

-- =====================================================
-- TABLA CONTROL: METADATA
-- Metadatos de procesamiento y trazabilidad
-- =====================================================
CREATE TABLE metadata (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    archivo_origen VARCHAR(255) NOT NULL,
    fecha_extraccion TIMESTAMP,
    version_extractor VARCHAR(20),
    hash_archivo VARCHAR(64),
    tamano_archivo_bytes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLAS DE DATOS BASE (LIMPIOS)
-- =====================================================

-- Información del cliente
CREATE TABLE client_base (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    nombre VARCHAR(255),
    nif VARCHAR(20),
    direccion TEXT,
    codigo_postal VARCHAR(10),
    municipio VARCHAR(100),
    provincia VARCHAR(100),
    telefono VARCHAR(20),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Información del contrato
CREATE TABLE contract_base (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22),
    tarifa_acceso VARCHAR(20),
    potencia_contratada DECIMAL(10,3),
    tipo_contador VARCHAR(50),
    peaje_acceso VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Información del proveedor
CREATE TABLE provider_base (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    nombre_comercializadora VARCHAR(255),
    cif_comercializadora VARCHAR(20),
    nombre_distribuidora VARCHAR(255),
    cif_distribuidora VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Período de facturación
CREATE TABLE billing_period (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    fecha_inicio DATE,
    fecha_fin DATE,
    dias_facturados INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Facturación base
CREATE TABLE billing_base (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    numero_factura VARCHAR(50),
    fecha_emision DATE,
    fecha_vencimiento DATE,
    importe_total DECIMAL(10,2),
    iva DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLAS DE CONSUMO POR PERÍODOS
-- =====================================================

CREATE TABLE consumption_p1 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P1',
    consumo_kwh DECIMAL(12,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE consumption_p2 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P2',
    consumo_kwh DECIMAL(12,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE consumption_p3 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P3',
    consumo_kwh DECIMAL(12,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE consumption_p4 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P4',
    consumo_kwh DECIMAL(12,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE consumption_p5 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P5',
    consumo_kwh DECIMAL(12,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE consumption_p6 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P6',
    consumo_kwh DECIMAL(12,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLAS DE COSTOS POR PERÍODOS
-- =====================================================

CREATE TABLE cost_p1 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P1',
    coste_energia DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_p2 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P2',
    coste_energia DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_p3 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P3',
    coste_energia DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_p4 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P4',
    coste_energia DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_p5 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P5',
    coste_energia DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_p6 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P6',
    coste_energia DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLAS DE POTENCIA POR PERÍODOS
-- =====================================================

CREATE TABLE power_p1 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P1',
    potencia_demandada DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE power_p2 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P2',
    potencia_demandada DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE power_p3 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P3',
    potencia_demandada DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE power_p4 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P4',
    potencia_demandada DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE power_p5 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P5',
    potencia_demandada DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE power_p6 (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    periodo VARCHAR(10) DEFAULT 'P6',
    potencia_demandada DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLAS DE ENRIQUECIMIENTO
-- =====================================================

CREATE TABLE sustainability_base (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    mix_energetico JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sustainability_metrics (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    rating_sostenibilidad VARCHAR(5),
    recomendacion_mejora TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    metricas_calculadas JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- SISTEMA DE CUESTIONARIOS DINÁMICOS
-- =====================================================

CREATE TABLE questionnaire_questions (
    id SERIAL PRIMARY KEY,
    field_name VARCHAR(100) NOT NULL,
    question_text TEXT NOT NULL,
    field_type VARCHAR(50) NOT NULL,
    is_critical BOOLEAN DEFAULT FALSE,
    validation_rules JSONB,
    help_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE questionnaire_conditions (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questionnaire_questions(id) ON DELETE CASCADE,
    condition_field VARCHAR(100),
    condition_operator VARCHAR(20),
    condition_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE questionnaire_responses (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questionnaire_questions(id) ON DELETE CASCADE,
    response_value TEXT,
    response_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_session VARCHAR(100),
    is_validated BOOLEAN DEFAULT FALSE,
    validation_errors JSONB,
    UNIQUE(document_id, question_id)
);

CREATE TABLE questionnaire_sessions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    session_token VARCHAR(100) UNIQUE NOT NULL,
    cups VARCHAR(22) NOT NULL,
    missing_fields JSONB NOT NULL,
    total_questions INTEGER DEFAULT 0,
    answered_questions INTEGER DEFAULT 0,
    completion_percentage DECIMAL(5,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days')
);

CREATE TABLE questionnaire_analytics (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questionnaire_questions(id) ON DELETE CASCADE,
    total_shown INTEGER DEFAULT 0,
    total_answered INTEGER DEFAULT 0,
    total_skipped INTEGER DEFAULT 0,
    avg_response_time_seconds INTEGER DEFAULT 0,
    most_common_response TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =====================================================

-- Índices principales
CREATE INDEX idx_documents_cups ON documents(cups);
CREATE INDEX idx_documents_cliente ON documents(cliente);
CREATE INDEX idx_documents_fecha ON documents(fecha_procesamiento);

-- Índices para tablas base
CREATE INDEX idx_client_base_document ON client_base(document_id);
CREATE INDEX idx_contract_base_document ON contract_base(document_id);
CREATE INDEX idx_provider_base_document ON provider_base(document_id);
CREATE INDEX idx_billing_period_document ON billing_period(document_id);
CREATE INDEX idx_billing_base_document ON billing_base(document_id);

-- Índices para consumo
CREATE INDEX idx_consumption_p1_document ON consumption_p1(document_id);
CREATE INDEX idx_consumption_p2_document ON consumption_p2(document_id);
CREATE INDEX idx_consumption_p3_document ON consumption_p3(document_id);
CREATE INDEX idx_consumption_p4_document ON consumption_p4(document_id);
CREATE INDEX idx_consumption_p5_document ON consumption_p5(document_id);
CREATE INDEX idx_consumption_p6_document ON consumption_p6(document_id);

-- Índices para costos
CREATE INDEX idx_cost_p1_document ON cost_p1(document_id);
CREATE INDEX idx_cost_p2_document ON cost_p2(document_id);
CREATE INDEX idx_cost_p3_document ON cost_p3(document_id);
CREATE INDEX idx_cost_p4_document ON cost_p4(document_id);
CREATE INDEX idx_cost_p5_document ON cost_p5(document_id);
CREATE INDEX idx_cost_p6_document ON cost_p6(document_id);

-- Índices para potencia
CREATE INDEX idx_power_p1_document ON power_p1(document_id);
CREATE INDEX idx_power_p2_document ON power_p2(document_id);
CREATE INDEX idx_power_p3_document ON power_p3(document_id);
CREATE INDEX idx_power_p4_document ON power_p4(document_id);
CREATE INDEX idx_power_p5_document ON power_p5(document_id);
CREATE INDEX idx_power_p6_document ON power_p6(document_id);

-- Índices para enriquecimiento
CREATE INDEX idx_sustainability_base_document ON sustainability_base(document_id);
CREATE INDEX idx_sustainability_metrics_document ON sustainability_metrics(document_id);
CREATE INDEX idx_analytics_document ON analytics(document_id);

-- Índices para cuestionarios
CREATE INDEX idx_questionnaire_responses_document ON questionnaire_responses(document_id);
CREATE INDEX idx_questionnaire_responses_question ON questionnaire_responses(question_id);
CREATE INDEX idx_questionnaire_sessions_token ON questionnaire_sessions(session_token);
CREATE INDEX idx_questionnaire_sessions_cups ON questionnaire_sessions(cups);
CREATE INDEX idx_questionnaire_sessions_status ON questionnaire_sessions(status);
CREATE INDEX idx_questionnaire_conditions_question ON questionnaire_conditions(question_id);

-- =====================================================
-- DATOS INICIALES
-- =====================================================

INSERT INTO questionnaire_questions (field_name, question_text, field_type, is_critical, help_text) VALUES
('cups', '¿Cuál es el código CUPS de su punto de suministro?', 'text', TRUE, 'El CUPS es un código único de 20-22 caracteres que identifica su punto de suministro eléctrico. Lo puede encontrar en su factura.'),
('potencia_contratada', '¿Cuál es su potencia contratada en kW?', 'number', TRUE, 'La potencia contratada aparece en su factura eléctrica, normalmente expresada en kW.'),
('tarifa_acceso', '¿Qué tarifa de acceso tiene contratada?', 'select', FALSE, 'Ejemplos: 2.0TD, 3.0TD, 6.1TD. Esta información aparece en su factura eléctrica.'),
('tipo_contador', '¿Qué tipo de contador tiene instalado?', 'select', FALSE, 'Indique si tiene contador inteligente (telemedida) o contador convencional.');

-- Análisis final
ANALYZE;
