-- =====================================================
-- MIGRACIÓN DE CUESTIONARIOS DE db_N1 A db_encuesta
-- Traslada 5 tablas de cuestionarios y elimina de N1
-- =====================================================

-- =====================================================
-- PARTE 1: CREAR ESTRUCTURA EN db_encuesta
-- Ejecutar conectado a db_encuesta
-- =====================================================

-- TABLA 1: QUESTIONNAIRE_QUESTIONS
CREATE TABLE IF NOT EXISTS questionnaire_questions (
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
CREATE TABLE IF NOT EXISTS questionnaire_conditions (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questionnaire_questions(id) ON DELETE CASCADE,
    condition_field VARCHAR(100),
    condition_operator VARCHAR(20),
    condition_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 3: QUESTIONNAIRE_SESSIONS
CREATE TABLE IF NOT EXISTS questionnaire_sessions (
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
CREATE TABLE IF NOT EXISTS questionnaire_responses (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES questionnaire_sessions(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questionnaire_questions(id),
    field_name VARCHAR(100) NOT NULL,
    response_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 5: QUESTIONNAIRE_ANALYTICS
CREATE TABLE IF NOT EXISTS questionnaire_analytics (
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
CREATE INDEX IF NOT EXISTS idx_questionnaire_sessions_token ON questionnaire_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_questionnaire_sessions_cups ON questionnaire_sessions(cups);
CREATE INDEX IF NOT EXISTS idx_questionnaire_responses_session ON questionnaire_responses(session_id);
CREATE INDEX IF NOT EXISTS idx_questionnaire_responses_field ON questionnaire_responses(field_name);

-- =====================================================
-- PARTE 2: MIGRAR DATOS USANDO dblink
-- Requiere extensión dblink instalada
-- =====================================================

-- Instalar extensión si no existe
CREATE EXTENSION IF NOT EXISTS dblink;

-- Migrar questionnaire_questions
INSERT INTO questionnaire_questions (field_name, question_text, question_type, validation_regex, options, help_text, is_required, created_at)
SELECT * FROM dblink('dbname=db_N1 host=localhost user=postgres password=admin',
    'SELECT field_name, question_text, question_type, validation_regex, options, help_text, is_required, created_at FROM questionnaire_questions')
AS t(field_name VARCHAR(100), question_text TEXT, question_type VARCHAR(50), validation_regex VARCHAR(255), 
     options JSONB, help_text TEXT, is_required BOOLEAN, created_at TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Verificar migración
SELECT 'questionnaire_questions migradas' as tabla, COUNT(*) as registros FROM questionnaire_questions;

-- =====================================================
-- PARTE 3: LIMPIAR db_N1
-- Ejecutar conectado a db_N1
-- =====================================================

-- Script para ejecutar en db_N1:
/*
DROP TABLE IF EXISTS questionnaire_analytics CASCADE;
DROP TABLE IF EXISTS questionnaire_responses CASCADE;
DROP TABLE IF EXISTS questionnaire_sessions CASCADE;
DROP TABLE IF EXISTS questionnaire_conditions CASCADE;
DROP TABLE IF EXISTS questionnaire_questions CASCADE;

-- Verificar que db_N1 queda con 14 tablas
SELECT 'db_N1 limpia' as status, COUNT(*) as total_tablas 
FROM information_schema.tables 
WHERE table_schema = 'public';
*/

-- =====================================================
-- VERIFICACIÓN FINAL
-- =====================================================

-- En db_encuesta debería haber 5 tablas:
SELECT 'db_encuesta' as database, COUNT(*) as total_tablas 
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE 'questionnaire%';

-- En db_N1 deberían quedar 14 tablas (sin cuestionarios)
