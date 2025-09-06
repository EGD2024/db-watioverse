-- =====================================================
-- SCRIPT DE LIMPIEZA COMPLETA BD N1
-- Elimina TODAS las tablas de la BD db_N1
-- =====================================================

-- Desactivar restricciones de claves foráneas temporalmente
SET session_replication_role = replica;

-- Eliminar TODAS las tablas una por una (las 45 detectadas)
DROP TABLE IF EXISTS analytics CASCADE;
DROP TABLE IF EXISTS billing_base CASCADE;
DROP TABLE IF EXISTS billing_period CASCADE;
DROP TABLE IF EXISTS client CASCADE;
DROP TABLE IF EXISTS client_base CASCADE;
DROP TABLE IF EXISTS consumption_p1 CASCADE;
DROP TABLE IF EXISTS consumption_p2 CASCADE;
DROP TABLE IF EXISTS consumption_p3 CASCADE;
DROP TABLE IF EXISTS consumption_p4 CASCADE;
DROP TABLE IF EXISTS consumption_p5 CASCADE;
DROP TABLE IF EXISTS consumption_p6 CASCADE;
DROP TABLE IF EXISTS contract CASCADE;
DROP TABLE IF EXISTS contract_base CASCADE;
DROP TABLE IF EXISTS cost_p1 CASCADE;
DROP TABLE IF EXISTS cost_p2 CASCADE;
DROP TABLE IF EXISTS cost_p3 CASCADE;
DROP TABLE IF EXISTS cost_p4 CASCADE;
DROP TABLE IF EXISTS cost_p5 CASCADE;
DROP TABLE IF EXISTS cost_p6 CASCADE;
DROP TABLE IF EXISTS direccion_fiscal CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS energy_consumption CASCADE;
DROP TABLE IF EXISTS invoice CASCADE;
DROP TABLE IF EXISTS invoice_summary CASCADE;
DROP TABLE IF EXISTS metadata CASCADE;
DROP TABLE IF EXISTS metering CASCADE;
DROP TABLE IF EXISTS power_p1 CASCADE;
DROP TABLE IF EXISTS power_p2 CASCADE;
DROP TABLE IF EXISTS power_p3 CASCADE;
DROP TABLE IF EXISTS power_p4 CASCADE;
DROP TABLE IF EXISTS power_p5 CASCADE;
DROP TABLE IF EXISTS power_p6 CASCADE;
DROP TABLE IF EXISTS power_term CASCADE;
DROP TABLE IF EXISTS provider CASCADE;
DROP TABLE IF EXISTS provider_base CASCADE;
DROP TABLE IF EXISTS questionnaire_analytics CASCADE;
DROP TABLE IF EXISTS questionnaire_conditions CASCADE;
DROP TABLE IF EXISTS questionnaire_questions CASCADE;
DROP TABLE IF EXISTS questionnaire_responses CASCADE;
DROP TABLE IF EXISTS questionnaire_sessions CASCADE;
DROP TABLE IF EXISTS supply_address CASCADE;
DROP TABLE IF EXISTS supply_point CASCADE;
DROP TABLE IF EXISTS sustainability CASCADE;
DROP TABLE IF EXISTS sustainability_base CASCADE;
DROP TABLE IF EXISTS sustainability_metrics CASCADE;

-- Reactivar restricciones de claves foráneas
SET session_replication_role = DEFAULT;

-- Verificar que no queden tablas
SELECT COUNT(*) as tablas_restantes FROM information_schema.tables WHERE table_schema = 'public';
