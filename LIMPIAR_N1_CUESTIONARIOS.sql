-- =====================================================
-- ELIMINAR TABLAS DE CUESTIONARIOS DE db_N1
-- Ejecutar conectado a db_N1
-- =====================================================

-- Eliminar las 5 tablas de cuestionarios que ya están en db_encuesta
DROP TABLE IF EXISTS questionnaire_analytics CASCADE;
DROP TABLE IF EXISTS questionnaire_responses CASCADE;
DROP TABLE IF EXISTS questionnaire_sessions CASCADE;
DROP TABLE IF EXISTS questionnaire_conditions CASCADE;
DROP TABLE IF EXISTS questionnaire_questions CASCADE;

-- Verificar que db_N1 queda con 14 tablas
SELECT 'db_N1 limpia' as status, COUNT(*) as total_tablas 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Listar las tablas restantes (deberían ser 14)
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;
