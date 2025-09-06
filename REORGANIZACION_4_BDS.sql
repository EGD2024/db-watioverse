-- =====================================================
-- REORGANIZACIÓN COMPLETA: 4 BASES DE DATOS ESPECIALIZADAS
-- 1. db_N0: 14 tablas datos brutos
-- 2. db_N1: 14 tablas datos cliente (sin cuestionarios)
-- 3. db_encuesta: 5 tablas cuestionarios dinámicos
-- 4. db_enriquecimiento: 3 tablas cache y enriquecimiento
-- =====================================================

-- =====================================================
-- PASO 1: CREAR ESQUEMA db_encuesta
-- =====================================================

-- Conectar a db_encuesta y crear tablas
\c db_encuesta;

-- TABLA 1: QUESTIONNAIRE_QUESTIONS
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

-- TABLA 2: QUESTIONNAIRE_CONDITIONS
CREATE TABLE questionnaire_conditions (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questionnaire_questions(id) ON DELETE CASCADE,
    condition_field VARCHAR(100),
    condition_operator VARCHAR(20),
    condition_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 3: QUESTIONNAIRE_SESSIONS
CREATE TABLE questionnaire_sessions (
    id SERIAL PRIMARY KEY,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    cups VARCHAR(22) NOT NULL,
    document_id INTEGER,
    status VARCHAR(50) DEFAULT 'active',
    progress JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- TABLA 4: QUESTIONNAIRE_RESPONSES
CREATE TABLE questionnaire_responses (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES questionnaire_sessions(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questionnaire_questions(id),
    field_name VARCHAR(100) NOT NULL,
    response_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 5: QUESTIONNAIRE_ANALYTICS
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

-- Índices para optimización
CREATE INDEX idx_questionnaire_sessions_token ON questionnaire_sessions(session_token);
CREATE INDEX idx_questionnaire_sessions_cups ON questionnaire_sessions(cups);
CREATE INDEX idx_questionnaire_responses_session ON questionnaire_responses(session_id);
CREATE INDEX idx_questionnaire_responses_field ON questionnaire_responses(field_name);

-- =====================================================
-- PASO 2: MIGRAR DATOS DE db_N1 A db_encuesta
-- =====================================================

-- Migrar questionnaire_questions
INSERT INTO questionnaire_questions (field_name, question_text, question_type, validation_regex, options, help_text, is_required, created_at)
SELECT field_name, question_text, question_type, validation_regex, options, help_text, is_required, created_at
FROM db_N1.questionnaire_questions;

-- Migrar questionnaire_conditions
INSERT INTO questionnaire_conditions (question_id, condition_field, condition_operator, condition_value, created_at)
SELECT question_id, condition_field, condition_operator, condition_value, created_at
FROM db_N1.questionnaire_conditions;

-- Migrar questionnaire_sessions
INSERT INTO questionnaire_sessions (session_token, cups, document_id, status, progress, created_at, expires_at, completed_at)
SELECT session_token, cups, document_id, status, progress, created_at, expires_at, completed_at
FROM db_N1.questionnaire_sessions;

-- Migrar questionnaire_responses
INSERT INTO questionnaire_responses (session_id, question_id, field_name, response_value, created_at)
SELECT session_id, question_id, field_name, response_value, created_at
FROM db_N1.questionnaire_responses;

-- Migrar questionnaire_analytics
INSERT INTO questionnaire_analytics (field_name, total_requests, total_responses, avg_response_time_minutes, last_requested, created_at, updated_at)
SELECT field_name, total_requests, total_responses, avg_response_time_minutes, last_requested, created_at, updated_at
FROM db_N1.questionnaire_analytics;

-- =====================================================
-- PASO 3: CREAR ESQUEMA db_enriquecimiento
-- =====================================================

-- Conectar a db_enriquecimiento y crear tablas
\c db_enriquecimiento;

-- TABLA 1: ENRICHMENT_CACHE - Cache multi-dimensional
CREATE TABLE enrichment_cache (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL,
    direccion_hash VARCHAR(64) NOT NULL,
    provincia VARCHAR(100),
    codigo_postal VARCHAR(10),
    tarifa VARCHAR(50),
    periodo_mes VARCHAR(7), -- YYYY-MM
    
    -- Datos enriquecidos
    datos_clima JSONB,
    datos_sostenibilidad JSONB,
    datos_mercado JSONB,
    datos_territorio JSONB,
    
    -- Control temporal
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    
    -- Índice único compuesto
    UNIQUE(cups, direccion_hash, tarifa, periodo_mes)
);

-- TABLA 2: ENRICHMENT_QUEUE - Cola de trabajos asíncronos
CREATE TABLE enrichment_queue (
    id SERIAL PRIMARY KEY,
    cups VARCHAR(22) NOT NULL,
    direccion_hash VARCHAR(64) NOT NULL,
    provincia VARCHAR(100),
    codigo_postal VARCHAR(10),
    tarifa VARCHAR(50),
    periodo_mes VARCHAR(7),
    
    -- Control de procesamiento
    priority VARCHAR(20) DEFAULT 'medium', -- high, medium, low
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    
    -- Timestamps
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    next_retry_at TIMESTAMP
);

-- TABLA 3: ENRICHMENT_SOURCES - Control de APIs externas
CREATE TABLE enrichment_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL, -- api, database, file
    base_url VARCHAR(255),
    api_key_required BOOLEAN DEFAULT false,
    
    -- Control de estado
    is_active BOOLEAN DEFAULT true,
    last_success TIMESTAMP,
    last_failure TIMESTAMP,
    consecutive_failures INTEGER DEFAULT 0,
    max_failures INTEGER DEFAULT 5,
    
    -- Rate limiting
    rate_limit_per_minute INTEGER DEFAULT 60,
    rate_limit_per_hour INTEGER DEFAULT 1000,
    current_minute_calls INTEGER DEFAULT 0,
    current_hour_calls INTEGER DEFAULT 0,
    rate_reset_minute TIMESTAMP,
    rate_reset_hour TIMESTAMP,
    
    -- Configuración
    timeout_seconds INTEGER DEFAULT 30,
    retry_delay_seconds INTEGER DEFAULT 60,
    config JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimización
CREATE INDEX idx_enrichment_cache_cups ON enrichment_cache(cups);
CREATE INDEX idx_enrichment_cache_hash ON enrichment_cache(direccion_hash);
CREATE INDEX idx_enrichment_cache_expires ON enrichment_cache(expires_at);
CREATE INDEX idx_enrichment_queue_status ON enrichment_queue(status);
CREATE INDEX idx_enrichment_queue_priority ON enrichment_queue(priority, requested_at);
CREATE INDEX idx_enrichment_sources_active ON enrichment_sources(is_active);

-- =====================================================
-- PASO 4: POBLAR db_enriquecimiento CON DATOS INICIALES
-- =====================================================

-- Fuentes de enriquecimiento iniciales
INSERT INTO enrichment_sources (source_name, source_type, base_url, api_key_required, rate_limit_per_minute, rate_limit_per_hour, config) VALUES
('AEMET_API', 'api', 'https://opendata.aemet.es/opendata/api', true, 60, 1000, '{"description": "API meteorológica oficial de España"}'),
('CNMC_Tarifas', 'api', 'https://www.cnmc.es/api', false, 30, 500, '{"description": "Comisión Nacional de Mercados y Competencia"}'),
('REE_Datos', 'api', 'https://apidatos.ree.es', false, 100, 2000, '{"description": "Red Eléctrica de España - datos del sistema"}'),
('INE_Territorio', 'api', 'https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA', false, 50, 1000, '{"description": "Instituto Nacional de Estadística"}'),
('MITECO_Sostenibilidad', 'api', 'https://www.miteco.gob.es/api', false, 20, 200, '{"description": "Ministerio para la Transición Ecológica"}');

-- =====================================================
-- PASO 5: LIMPIAR db_N1 - ELIMINAR TABLAS DE CUESTIONARIOS
-- =====================================================

-- Conectar a db_N1 y eliminar tablas de cuestionarios
\c db_N1;

-- Eliminar tablas de cuestionarios (ahora están en db_encuesta)
DROP TABLE IF EXISTS questionnaire_analytics CASCADE;
DROP TABLE IF EXISTS questionnaire_responses CASCADE;
DROP TABLE IF EXISTS questionnaire_sessions CASCADE;
DROP TABLE IF EXISTS questionnaire_conditions CASCADE;
DROP TABLE IF EXISTS questionnaire_questions CASCADE;

-- =====================================================
-- PASO 6: VERIFICACIÓN FINAL
-- =====================================================

-- Verificar db_N0 (debe tener 14 tablas)
\c db_N0;
SELECT 'db_N0' as database, COUNT(*) as total_tablas FROM information_schema.tables WHERE table_schema = 'public';

-- Verificar db_N1 (debe tener 14 tablas, sin cuestionarios)
\c db_N1;
SELECT 'db_N1' as database, COUNT(*) as total_tablas FROM information_schema.tables WHERE table_schema = 'public';

-- Verificar db_encuesta (debe tener 5 tablas)
\c db_encuesta;
SELECT 'db_encuesta' as database, COUNT(*) as total_tablas FROM information_schema.tables WHERE table_schema = 'public';

-- Verificar db_enriquecimiento (debe tener 3 tablas)
\c db_enriquecimiento;
SELECT 'db_enriquecimiento' as database, COUNT(*) as total_tablas FROM information_schema.tables WHERE table_schema = 'public';

-- =====================================================
-- RESUMEN FINAL DE LA REORGANIZACIÓN
-- =====================================================
-- 
-- ARQUITECTURA FINAL:
-- 
-- db_N0 (14 tablas):
-- - documents, metadata, client, direccion_fiscal, supply_point,
--   supply_address, contract, provider, power_term, invoice,
--   invoice_summary, energy_consumption, metering, sustainability
-- 
-- db_N1 (14 tablas):
-- - Mismas tablas que N0 pero sin metadatos de extracción
-- - Datos limpios y enriquecidos del cliente
-- 
-- db_encuesta (5 tablas):
-- - questionnaire_questions, questionnaire_conditions,
--   questionnaire_sessions, questionnaire_responses,
--   questionnaire_analytics
-- 
-- db_enriquecimiento (3 tablas):
-- - enrichment_cache, enrichment_queue, enrichment_sources
-- 
-- TOTAL: 36 tablas distribuidas en 4 bases de datos especializadas
-- =====================================================
