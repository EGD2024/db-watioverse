# Ejecución de Scripts SQL de Seguridad

## Scripts Preparados

### 1. security_tables_N1.sql
**Base de datos objetivo:** `db_N1`
**Descripción:** Crea tablas de versionado, auditoría y registro de hashes
**Tablas creadas:**
- `client_versions` - Versionado completo de datos de cliente
- `data_audit_log` - Auditoría de acceso a datos personales
- `hash_registry` - Registro de hashes para trazabilidad

### 2. security_tables_enriquecimiento.sql
**Base de datos objetivo:** `db_enriquecimiento`
**Descripción:** Actualiza tablas existentes y añade logs de enriquecimiento
**Modificaciones:**
- Actualiza `enrichment_queue` con campos hash
- Actualiza `enrichment_cache` con campos hash y TTL
- Crea `enrichment_log` para auditoría de APIs

## Comandos de Ejecución

### Opción 1: Usando psql directamente
```bash
# Para db_N1
psql -h localhost -U tu_usuario -d db_N1 -f sql/security/security_tables_N1.sql

# Para db_enriquecimiento
psql -h localhost -U tu_usuario -d db_enriquecimiento -f sql/security/security_tables_enriquecimiento.sql
```

### Opción 2: Usando pgAdmin
1. Conectar a la base de datos correspondiente
2. Abrir Query Tool
3. Cargar el archivo SQL
4. Ejecutar

### Opción 3: Usando DBeaver/DataGrip
1. Conectar a la base de datos
2. Abrir archivo SQL
3. Ejecutar script completo

## Verificación Post-Ejecución

### Verificar tablas en db_N1
```sql
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('client_versions', 'data_audit_log', 'hash_registry');
```

### Verificar tablas en db_enriquecimiento
```sql
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('enrichment_queue', 'enrichment_cache', 'enrichment_log');

-- Verificar nuevos campos
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'enrichment_queue' 
AND column_name IN ('cups_hash', 'direccion_hash');
```

## Funciones TTL Creadas

### db_N1: cleanup_audit_logs()
- Limpia logs de auditoría > 2 años
- Mantiene datos de versionado permanentes

### db_enriquecimiento: cleanup_expired_data()
- Cache: 90 días de retención
- Cola completada: 30 días
- Logs: 180 días

## Configuración Automática TTL

Para ejecutar limpieza automática, configurar cron jobs:

```bash
# Limpiar cada domingo a las 2:00 AM
0 2 * * 0 psql -d db_N1 -c "SELECT cleanup_audit_logs();"
0 3 * * 0 psql -d db_enriquecimiento -c "SELECT cleanup_expired_data();"
```

## Seguridad Post-Instalación

1. **Verificar permisos de usuario**
2. **Configurar backups de tablas de seguridad**
3. **Monitorear crecimiento de logs**
4. **Probar funciones TTL manualmente**

## Rollback (si necesario)

```sql
-- db_N1
DROP TABLE IF EXISTS client_versions CASCADE;
DROP TABLE IF EXISTS data_audit_log CASCADE;
DROP TABLE IF EXISTS hash_registry CASCADE;
DROP FUNCTION IF EXISTS cleanup_audit_logs();

-- db_enriquecimiento
ALTER TABLE enrichment_queue DROP COLUMN IF EXISTS cups_hash;
ALTER TABLE enrichment_queue DROP COLUMN IF EXISTS direccion_hash;
ALTER TABLE enrichment_cache DROP COLUMN IF EXISTS direccion_hash;
ALTER TABLE enrichment_cache DROP COLUMN IF EXISTS cups_hash;
DROP TABLE IF EXISTS enrichment_log CASCADE;
DROP FUNCTION IF EXISTS cleanup_expired_data();
```
