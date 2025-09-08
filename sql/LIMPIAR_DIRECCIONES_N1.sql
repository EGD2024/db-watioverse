-- =====================================================
-- LIMPIEZA DE DIRECCIONES N1 - ELIMINAR CAMPOS OBSOLETOS
-- Preparación para nueva estructura de direcciones optimizada
-- =====================================================

-- 1. ELIMINAR TABLA direccion_fiscal (VACÍA - 0 registros)
DROP TABLE IF EXISTS direccion_fiscal CASCADE;

-- 2. ELIMINAR CAMPO direccion de documents (campo suelto sin usar)
ALTER TABLE documents DROP COLUMN IF EXISTS direccion;

-- 3. LIMPIAR supply_address - Eliminar campos de referencia obsoletos
ALTER TABLE supply_address DROP COLUMN IF EXISTS supply_point_id;

-- 4. VERIFICAR DATOS ACTUALES EN supply_address
-- Primero verificar qué columnas existen realmente
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'supply_address' 
ORDER BY ordinal_position;

-- Luego verificar datos con todas las columnas existentes
SELECT 
    'supply_address' as tabla,
    COUNT(*) as total_registros,
    COUNT(CASE WHEN direccion_suministro IS NOT NULL AND direccion_suministro != '' THEN 1 END) as con_direccion,
    COUNT(CASE WHEN codigo_postal IS NOT NULL AND codigo_postal != '' THEN 1 END) as con_cp,
    COUNT(CASE WHEN nombre_via IS NOT NULL AND nombre_via != '' THEN 1 END) as con_nombre_via,
    COUNT(CASE WHEN tipo_via IS NOT NULL AND tipo_via != '' THEN 1 END) as con_tipo_via,
    COUNT(CASE WHEN poblacion IS NOT NULL AND poblacion != '' THEN 1 END) as con_poblacion,
    COUNT(CASE WHEN provincia IS NOT NULL AND provincia != '' THEN 1 END) as con_provincia
FROM supply_address;

-- 5. MOSTRAR ESTRUCTURA LIMPIA RESULTANTE
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('supply_address', 'provider', 'client')
    AND table_schema = 'public'
ORDER BY table_name, ordinal_position;

-- =====================================================
-- RESULTADO ESPERADO:
-- - direccion_fiscal eliminada (liberando espacio)
-- - documents.direccion eliminado (campo sin usar)
-- - supply_address limpia y lista para expansión
-- =====================================================
