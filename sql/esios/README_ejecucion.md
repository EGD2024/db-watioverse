# Scripts de Migración ESIOS

Orden de ejecución para la remodelación de bases de datos según README Sistema Eléctrico.

## Prerrequisitos

- PostgreSQL 12+ con extensiones habilitadas
- Acceso a base de datos `db_Ncore` 
- Usuario con permisos CREATE TABLE, CREATE VIEW, CREATE INDEX

## Orden de Ejecución

### 1. Schema Principal
```bash
psql -d db_Ncore -f 01_schema.sql
```
Crea:
- `core_esios_indicador` (catálogo)
- `core_esios_valor_horario` (valores UTC)
- `core_esios_ingesta_ejecucion` (versionado)
- Tablas agregados diarios
- Tablas modelo RRSS
- Índices de rendimiento

### 2. Vistas Canónicas
```bash
psql -d db_Ncore -f 02_views.sql
```
Crea:
- `v_esios_ind_{ID}` para todos los indicadores
- Vistas alias descriptivos (pvpc_horario, mercado_diario, etc.)
- Vista combinada mix renovable/no renovable

### 3. Catálogo de Indicadores
```bash
psql -d db_Ncore -f 03_seed_catalog.sql
```
Inserta:
- 39 indicadores ESIOS confirmados
- Metadatos (nombre, unidad, descripción)
- Verificación de inserción

## Verificación Post-Migración

```sql
-- Verificar tablas creadas
\dt core_esios*

-- Verificar vistas creadas
\dv v_esios*

-- Verificar indicadores insertados
SELECT COUNT(*) FROM core_esios_indicador;

-- Verificar indicadores críticos PVPC
SELECT indicator_id, nombre FROM core_esios_indicador 
WHERE indicator_id IN (1001,1002,600,601,1900,1901);
```

## Rollback (si necesario)

```sql
-- CUIDADO: Esto borra todo
DROP TABLE IF EXISTS core_esios_evento_social CASCADE;
DROP TABLE IF EXISTS core_esios_resumen_diario CASCADE;
DROP TABLE IF EXISTS core_esios_demanda_diario CASCADE;
DROP TABLE IF EXISTS core_esios_emisiones_diario CASCADE;
DROP TABLE IF EXISTS core_esios_mix_diario CASCADE;
DROP TABLE IF EXISTS core_esios_pvpc_diario CASCADE;
DROP TABLE IF EXISTS core_esios_ingesta_ejecucion CASCADE;
DROP TABLE IF EXISTS core_esios_valor_horario CASCADE;
DROP TABLE IF EXISTS core_esios_indicador CASCADE;
```

## Próximos Pasos

1. Crear job de ingesta ESIOS genérico
2. Configurar agregados diarios automáticos  
3. Implementar generador eventos sociales
4. Conectar con db_sistema_electrico para PVPC
