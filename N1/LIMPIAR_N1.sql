-- =====================================================
-- SCRIPT PARA LIMPIAR BD N1 ANTES DE RECREAR
-- Elimina todas las tablas existentes con dependencias
-- =====================================================

-- Eliminar tablas en orden inverso de dependencias
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

-- Mensaje de confirmación
SELECT 'BD N1 limpiada - Lista para recrear esquema' as status;
