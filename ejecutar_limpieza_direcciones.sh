#!/bin/bash

# =====================================================
# SCRIPT EJECUTABLE - LIMPIEZA DIRECCIONES BD N1
# Ejecuta los comandos SQL de limpieza usando psql
# =====================================================

# Cargar variables de entorno
source .env

# Configuración de conexión BD N1
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME="N1"
DB_USER=${DB_USER:-postgres}

echo "🧹 INICIANDO LIMPIEZA DE DIRECCIONES EN BD N1"
echo "================================================"

# 1. ELIMINAR TABLA direccion_fiscal (VACÍA)
echo "❌ Eliminando tabla direccion_fiscal..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "DROP TABLE IF EXISTS direccion_fiscal CASCADE;"

# 2. ELIMINAR CAMPO direccion de documents
echo "❌ Eliminando campo documents.direccion..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "ALTER TABLE documents DROP COLUMN IF EXISTS direccion;"

# 3. LIMPIAR supply_address
echo "🧹 Limpiando supply_address..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "ALTER TABLE supply_address DROP COLUMN IF EXISTS supply_point_id;"

# 4. VERIFICAR DATOS ACTUALES
echo "📊 Verificando datos en supply_address..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT 
    'supply_address' as tabla,
    COUNT(*) as total_registros,
    COUNT(CASE WHEN direccion_suministro IS NOT NULL AND direccion_suministro != '' THEN 1 END) as con_direccion,
    COUNT(CASE WHEN codigo_postal IS NOT NULL AND codigo_postal != '' THEN 1 END) as con_cp,
    COUNT(CASE WHEN nombre_via IS NOT NULL AND nombre_via != '' THEN 1 END) as con_nombre_via,
    COUNT(CASE WHEN tipo_via IS NOT NULL AND tipo_via != '' THEN 1 END) as con_tipo_via
FROM supply_address;"

# 5. MOSTRAR ESTRUCTURA RESULTANTE
echo "📋 Mostrando estructura limpia..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('supply_address', 'provider', 'client')
    AND table_schema = 'public'
ORDER BY table_name, ordinal_position;"

echo "✅ LIMPIEZA COMPLETADA"
echo "================================================"
echo "📋 SIGUIENTE PASO: Ejecutar crear_direcciones_optimizadas.sh"
