-- =====================================================
-- LIMPIEZA DE DIRECCIONES N0 - ESTRUCTURA DIFERENTE A N1
-- BD N0 tiene estructura más simple y limpia
-- =====================================================

-- 1. VERIFICAR ESTRUCTURA ACTUAL N0
SELECT 
    table_name,
    COUNT(*) as total_columns
FROM information_schema.columns 
WHERE table_name IN ('supply_address', 'provider', 'client', 'documents')
    AND table_schema = 'public'
GROUP BY table_name
ORDER BY table_name;

-- 2. VERIFICAR DATOS EN supply_address N0 (solo campos que existen)
SELECT 
    'N0_supply_address' as tabla,
    COUNT(*) as total_registros,
    COUNT(CASE WHEN codigo_postal IS NOT NULL AND codigo_postal != '' THEN 1 END) as con_cp,
    COUNT(CASE WHEN nombre_via IS NOT NULL AND nombre_via != '' THEN 1 END) as con_nombre_via,
    COUNT(CASE WHEN tipo_via IS NOT NULL AND tipo_via != '' THEN 1 END) as con_tipo_via,
    COUNT(CASE WHEN poblacion IS NOT NULL AND poblacion != '' THEN 1 END) as con_poblacion,
    COUNT(CASE WHEN provincia IS NOT NULL AND provincia != '' THEN 1 END) as con_provincia
FROM supply_address;

-- 3. MOSTRAR ESTRUCTURA COMPLETA N0
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
-- RESULTADO N0:
-- - supply_address: 12 campos, estructura limpia
-- - provider: 7 campos básicos
-- - NO tiene direccion_fiscal (más limpio que N1)
-- - NO tiene documents.direccion
-- =====================================================
