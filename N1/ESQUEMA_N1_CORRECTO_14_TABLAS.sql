-- =====================================================
-- ESQUEMA N1 CORRECTO - 14 TABLAS N0 + 5 CUESTIONARIOS
-- Base de datos db_N1: Coherente con las 14 tablas reales de N0
-- Total: 19 tablas (14 N0 + 5 cuestionarios)
-- =====================================================

-- Eliminar TODAS las tablas existentes
DROP TABLE IF EXISTS questionnaire_analytics CASCADE;
DROP TABLE IF EXISTS questionnaire_responses CASCADE;
DROP TABLE IF EXISTS questionnaire_sessions CASCADE;
DROP TABLE IF EXISTS questionnaire_conditions CASCADE;
DROP TABLE IF EXISTS questionnaire_questions CASCADE;
DROP TABLE IF EXISTS sustainability CASCADE;
DROP TABLE IF EXISTS supply_point CASCADE;
DROP TABLE IF EXISTS supply_address CASCADE;
DROP TABLE IF EXISTS provider CASCADE;
DROP TABLE IF EXISTS power_term CASCADE;
DROP TABLE IF EXISTS power_p6 CASCADE;
DROP TABLE IF EXISTS power_p5 CASCADE;
DROP TABLE IF EXISTS power_p4 CASCADE;
DROP TABLE IF EXISTS power_p3 CASCADE;
DROP TABLE IF EXISTS power_p2 CASCADE;
DROP TABLE IF EXISTS power_p1 CASCADE;
DROP TABLE IF EXISTS metering CASCADE;
DROP TABLE IF EXISTS metadata CASCADE;
DROP TABLE IF EXISTS invoice_summary CASCADE;
DROP TABLE IF EXISTS invoice CASCADE;
DROP TABLE IF EXISTS energy_consumption CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS direccion_fiscal CASCADE;
DROP TABLE IF EXISTS contract CASCADE;
DROP TABLE IF EXISTS consumption_p6 CASCADE;
DROP TABLE IF EXISTS consumption_p5 CASCADE;
DROP TABLE IF EXISTS consumption_p4 CASCADE;
DROP TABLE IF EXISTS consumption_p3 CASCADE;
DROP TABLE IF EXISTS consumption_p2 CASCADE;
DROP TABLE IF EXISTS consumption_p1 CASCADE;
DROP TABLE IF EXISTS client CASCADE;

-- =====================================================
-- LAS 14 TABLAS REALES DE N0 (SEGÚN IMAGEN)
-- =====================================================

-- TABLA 1: DOCUMENTS
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) UNIQUE NOT NULL,
    cliente TEXT NOT NULL,
    direccion TEXT NOT NULL,
    nif VARCHAR(20),
    telefono VARCHAR(20),
    email VARCHAR(100),
    filename VARCHAR(255) NOT NULL,
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'processed',
    file_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 2: METADATA
CREATE TABLE metadata (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    extraction_date TIMESTAMP,
    extraction_method VARCHAR(100),
    file_size_bytes INTEGER,
    pages_processed INTEGER,
    confidence_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 3: CLIENT
CREATE TABLE client (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    nombre_cliente TEXT,
    nif VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 4: DIRECCION_FISCAL
CREATE TABLE direccion_fiscal (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    direccion TEXT,
    codigo_postal VARCHAR(10),
    poblacion VARCHAR(100),
    provincia VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 5: SUPPLY_POINT
CREATE TABLE supply_point (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 6: SUPPLY_ADDRESS
CREATE TABLE supply_address (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    direccion_suministro TEXT,
    codigo_postal VARCHAR(10),
    poblacion VARCHAR(100),
    provincia VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 7: CONTRACT
CREATE TABLE contract (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    tarifa VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 8: PROVIDER
CREATE TABLE provider (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    comercializadora TEXT,
    distribuidora TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 9: POWER_TERM
CREATE TABLE power_term (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    potencia_contratada_p1 DECIMAL(10,3),
    potencia_contratada_p2 DECIMAL(10,3),
    potencia_contratada_p3 DECIMAL(10,3),
    potencia_contratada_p4 DECIMAL(10,3),
    potencia_contratada_p5 DECIMAL(10,3),
    potencia_contratada_p6 DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 10: INVOICE
CREATE TABLE invoice (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    numero_factura VARCHAR(100),
    fecha_factura DATE,
    periodo_facturacion_inicio DATE,
    periodo_facturacion_fin DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 11: INVOICE_SUMMARY
CREATE TABLE invoice_summary (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    importe_total DECIMAL(10,2),
    importe_energia DECIMAL(10,2),
    importe_potencia DECIMAL(10,2),
    impuestos DECIMAL(10,2),
    descuentos DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 12: ENERGY_CONSUMPTION
CREATE TABLE energy_consumption (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    consumo_total_kwh DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 13: METERING
CREATE TABLE metering (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    lectura_anterior DECIMAL(10,3),
    lectura_actual DECIMAL(10,3),
    fecha_lectura_anterior DATE,
    fecha_lectura_actual DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 14: SUSTAINABILITY
CREATE TABLE sustainability (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    co2_emissions_kg DECIMAL(10,3),
    renewable_energy_percentage DECIMAL(5,2),
    energy_efficiency_rating VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- SISTEMA DE CUESTIONARIOS DINÁMICOS (5 TABLAS)
-- =====================================================

-- TABLA 15: QUESTIONNAIRE_QUESTIONS
CREATE TABLE questionnaire_questions (
    id SERIAL PRIMARY KEY,
    field_name VARCHAR(100) NOT NULL,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL,
    validation_regex VARCHAR(255),
    options JSONB,
    help_text TEXT,
    is_required BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 16: QUESTIONNAIRE_CONDITIONS
CREATE TABLE questionnaire_conditions (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questionnaire_questions(id) ON DELETE CASCADE,
    condition_field VARCHAR(100),
    condition_operator VARCHAR(20),
    condition_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 17: QUESTIONNAIRE_SESSIONS
CREATE TABLE questionnaire_sessions (
    id SERIAL PRIMARY KEY,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    cups VARCHAR(22) NOT NULL,
    document_id INTEGER REFERENCES documents(id),
    status VARCHAR(50) DEFAULT 'active',
    progress JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- TABLA 18: QUESTIONNAIRE_RESPONSES
CREATE TABLE questionnaire_responses (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES questionnaire_sessions(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questionnaire_questions(id),
    field_name VARCHAR(100) NOT NULL,
    response_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 19: QUESTIONNAIRE_ANALYTICS
CREATE TABLE questionnaire_analytics (
    id SERIAL PRIMARY KEY,
    field_name VARCHAR(100) NOT NULL,
    total_requests INTEGER DEFAULT 0,
    total_responses INTEGER DEFAULT 0,
    avg_response_time_minutes DECIMAL(10,2),
    last_requested TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =====================================================

-- Índices N0
CREATE INDEX idx_documents_cups ON documents(cups);
CREATE INDEX idx_documents_filename ON documents(filename);
CREATE INDEX idx_metadata_cups ON metadata(cups);
CREATE INDEX idx_client_cups ON client(cups);
CREATE INDEX idx_contract_cups ON contract(cups);
CREATE INDEX idx_provider_cups ON provider(cups);
CREATE INDEX idx_invoice_cups ON invoice(cups);
CREATE INDEX idx_energy_consumption_cups ON energy_consumption(cups);
CREATE INDEX idx_sustainability_cups ON sustainability(cups);

-- Índices cuestionarios
CREATE INDEX idx_questionnaire_sessions_token ON questionnaire_sessions(session_token);
CREATE INDEX idx_questionnaire_sessions_cups ON questionnaire_sessions(cups);
CREATE INDEX idx_questionnaire_responses_session ON questionnaire_responses(session_id);
CREATE INDEX idx_questionnaire_responses_field ON questionnaire_responses(field_name);

-- =====================================================
-- DATOS INICIALES - PREGUNTAS BÁSICAS
-- =====================================================

INSERT INTO questionnaire_questions (field_name, question_text, question_type, validation_regex, help_text) VALUES
('cups', '¿Cuál es el código CUPS de su punto de suministro?', 'text', '^ES\d{18}[A-Z]{2}\d{1}[A-Z]{1}$', 'Formato: ES + 18 dígitos + 2 letras + 1 dígito + 1 letra'),
('tarifa', '¿Qué tarifa eléctrica tiene contratada?', 'select', NULL, 'Seleccione su tarifa actual'),
('potencia_contratada_p1', '¿Cuál es su potencia contratada en P1 (kW)?', 'number', '^\d+(\.\d{1,3})?$', 'Introduzca la potencia en kW con hasta 3 decimales'),
('comercializadora', '¿Cuál es su comercializadora eléctrica?', 'text', NULL, 'Nombre de la empresa que le factura la electricidad'),
('distribuidora', '¿Cuál es su distribuidora eléctrica?', 'text', NULL, 'Empresa responsable de la red eléctrica en su zona');

-- Opciones para tarifa
UPDATE questionnaire_questions 
SET options = '["2.0TD", "3.0TD", "6.1TD", "6.2TD", "6.3TD", "6.4TD"]'::jsonb 
WHERE field_name = 'tarifa';

-- =====================================================
-- RESUMEN FINAL
-- =====================================================
-- TOTAL: 19 TABLAS
-- 
-- TABLAS N0 REALES (14 tablas):
-- 1-14: documents, metadata, client, direccion_fiscal, supply_point,
--       supply_address, contract, provider, power_term, invoice,
--       invoice_summary, energy_consumption, metering, sustainability
--
-- CUESTIONARIOS DINÁMICOS (5 tablas):
-- 15-19: questionnaire_questions, questionnaire_conditions,
--        questionnaire_sessions, questionnaire_responses,
--        questionnaire_analytics
-- =====================================================
