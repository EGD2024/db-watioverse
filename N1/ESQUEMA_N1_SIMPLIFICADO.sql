-- =====================================================
-- ESQUEMA N1 SIMPLIFICADO - SOLO LO ESENCIAL
-- Base de datos db_N1: Datos energéticos + cuestionarios
-- Reducido de 41 a 13 tablas eliminando duplicados
-- =====================================================

-- Eliminar todas las tablas existentes
DROP TABLE IF EXISTS questionnaire_analytics CASCADE;
DROP TABLE IF EXISTS questionnaire_responses CASCADE;
DROP TABLE IF EXISTS questionnaire_sessions CASCADE;
DROP TABLE IF EXISTS questionnaire_conditions CASCADE;
DROP TABLE IF EXISTS questionnaire_questions CASCADE;
DROP TABLE IF EXISTS sustainability_data CASCADE;
DROP TABLE IF EXISTS consumption_data CASCADE;
DROP TABLE IF EXISTS billing_data CASCADE;
DROP TABLE IF EXISTS contract_data CASCADE;
DROP TABLE IF EXISTS client_data CASCADE;
DROP TABLE IF EXISTS documents CASCADE;

-- Eliminar tablas duplicadas/innecesarias del esquema anterior
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
DROP TABLE IF EXISTS client CASCADE;
DROP TABLE IF EXISTS contract CASCADE;
DROP TABLE IF EXISTS provider CASCADE;
DROP TABLE IF EXISTS supply_point CASCADE;
DROP TABLE IF EXISTS supply_address CASCADE;
DROP TABLE IF EXISTS direccion_fiscal CASCADE;
DROP TABLE IF EXISTS invoice CASCADE;
DROP TABLE IF EXISTS invoice_summary CASCADE;
DROP TABLE IF EXISTS energy_consumption CASCADE;
DROP TABLE IF EXISTS metering CASCADE;
DROP TABLE IF EXISTS power_term CASCADE;
DROP TABLE IF EXISTS sustainability CASCADE;

-- =====================================================
-- TABLA 1: DOCUMENTS - Control principal
-- =====================================================
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) UNIQUE NOT NULL,
    filename VARCHAR(255) NOT NULL,
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'processed',
    file_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLA 2: CLIENT_DATA - Datos del cliente consolidados
-- =====================================================
CREATE TABLE client_data (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    nombre_cliente TEXT,
    nif VARCHAR(20),
    direccion_fiscal TEXT,
    telefono VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLA 3: CONTRACT_DATA - Datos del contrato consolidados
-- =====================================================
CREATE TABLE contract_data (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    tarifa VARCHAR(50),
    potencia_contratada_p1 DECIMAL(10,3),
    potencia_contratada_p2 DECIMAL(10,3),
    potencia_contratada_p3 DECIMAL(10,3),
    potencia_contratada_p4 DECIMAL(10,3),
    potencia_contratada_p5 DECIMAL(10,3),
    potencia_contratada_p6 DECIMAL(10,3),
    comercializadora TEXT,
    distribuidora TEXT,
    direccion_suministro TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLA 4: BILLING_DATA - Facturación consolidada
-- =====================================================
CREATE TABLE billing_data (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    periodo_facturacion_inicio DATE,
    periodo_facturacion_fin DATE,
    importe_total DECIMAL(10,2),
    importe_energia DECIMAL(10,2),
    importe_potencia DECIMAL(10,2),
    impuestos DECIMAL(10,2),
    descuentos DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLA 5: CONSUMPTION_DATA - Consumos por períodos
-- =====================================================
CREATE TABLE consumption_data (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    periodo VARCHAR(2) NOT NULL, -- P1, P2, P3, P4, P5, P6
    consumo_kwh DECIMAL(10,3),
    coste_energia DECIMAL(10,2),
    precio_kwh DECIMAL(6,4),
    potencia_maxima DECIMAL(10,3),
    coste_potencia DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLA 6: SUSTAINABILITY_DATA - Métricas sostenibilidad
-- =====================================================
CREATE TABLE sustainability_data (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    cups VARCHAR(22) NOT NULL,
    co2_emissions_kg DECIMAL(10,3),
    renewable_energy_percentage DECIMAL(5,2),
    energy_efficiency_rating VARCHAR(10),
    carbon_footprint DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- SISTEMA DE CUESTIONARIOS DINÁMICOS (5 TABLAS)
-- =====================================================

-- TABLA 7: QUESTIONNAIRE_QUESTIONS
CREATE TABLE questionnaire_questions (
    id SERIAL PRIMARY KEY,
    field_name VARCHAR(100) NOT NULL,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL, -- text, number, select, date
    validation_regex VARCHAR(255),
    options JSONB, -- Para preguntas tipo select
    help_text TEXT,
    is_required BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 8: QUESTIONNAIRE_CONDITIONS
CREATE TABLE questionnaire_conditions (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questionnaire_questions(id) ON DELETE CASCADE,
    condition_field VARCHAR(100),
    condition_operator VARCHAR(20), -- equals, not_equals, contains, etc.
    condition_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 9: QUESTIONNAIRE_SESSIONS
CREATE TABLE questionnaire_sessions (
    id SERIAL PRIMARY KEY,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    cups VARCHAR(22) NOT NULL,
    document_id INTEGER REFERENCES documents(id),
    status VARCHAR(50) DEFAULT 'active', -- active, completed, expired
    progress JSONB, -- Progreso de respuestas
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- TABLA 10: QUESTIONNAIRE_RESPONSES
CREATE TABLE questionnaire_responses (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES questionnaire_sessions(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questionnaire_questions(id),
    field_name VARCHAR(100) NOT NULL,
    response_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 11: QUESTIONNAIRE_ANALYTICS
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

-- Índices principales
CREATE INDEX idx_documents_cups ON documents(cups);
CREATE INDEX idx_documents_filename ON documents(filename);
CREATE INDEX idx_client_data_cups ON client_data(cups);
CREATE INDEX idx_contract_data_cups ON contract_data(cups);
CREATE INDEX idx_billing_data_cups ON billing_data(cups);
CREATE INDEX idx_consumption_data_cups ON consumption_data(cups);
CREATE INDEX idx_consumption_data_periodo ON consumption_data(periodo);
CREATE INDEX idx_sustainability_data_cups ON sustainability_data(cups);

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
-- RESUMEN DEL ESQUEMA SIMPLIFICADO
-- =====================================================
-- TOTAL: 11 TABLAS (vs 41 anteriores)
-- 
-- DATOS ENERGÉTICOS (6 tablas):
-- 1. documents - Control principal
-- 2. client_data - Datos cliente consolidados  
-- 3. contract_data - Datos contrato consolidados
-- 4. billing_data - Facturación consolidada
-- 5. consumption_data - Consumos por períodos
-- 6. sustainability_data - Métricas sostenibilidad
--
-- CUESTIONARIOS DINÁMICOS (5 tablas):
-- 7. questionnaire_questions - Preguntas disponibles
-- 8. questionnaire_conditions - Condiciones para mostrar preguntas
-- 9. questionnaire_sessions - Sesiones de cuestionarios
-- 10. questionnaire_responses - Respuestas de usuarios
-- 11. questionnaire_analytics - Analíticas del sistema
-- =====================================================
