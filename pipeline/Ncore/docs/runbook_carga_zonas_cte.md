# RUNBOOK · Carga Segura Zonas Climáticas CTE en db_Ncore

Estado: aprobado para preparación offline. No ejecutar en producción sin checklist completo.

## 1) Fuente y formato
- Fuente oficial: Catálogo CTE DB-HE por municipio (MITMA) y relación CP↔Municipio (INE/Correos).
- Formato recomendado de importación: CSV UTF-8 con cabecera, delimitador `,` y columnas mínimas:
  - `codigo_postal`, `municipio`, `provincia`, `comunidad_autonoma`, `zona_climatica_cte`
  - Opcionales: `altitud`, `latitud`, `longitud`, `hdd_anual_medio`, `cdd_anual_medio`, `temperatura_media_anual`, `radiacion_global_anual`
  - Metadatos: `fecha_actualizacion`, `fuente`

## 2) Staging y validaciones (offline)
1. Crear STAGING (no toca tabla CORE):
   - SQL: `pipeline/Ncore/sql/zonas_climaticas_staging.sql`
   - Crea `public.stg_zonas_climaticas_cte` e índices para revisión.
2. Cargar CSV a STAGING (opciones):
   - Opción A: `\COPY public.stg_zonas_climaticas_cte (...) FROM 'zonas_cte.csv' CSV HEADER;`
   - Opción B: Script Python `pipeline/Ncore/scripts/import_zonas_cte.py --csv zonas_cte.csv --dry-run`
3. Ejecutar validaciones (contenidas en el SQL de staging):
   - Formato zona CTE: `^[A-E][0-9]$`
   - Obligatorios no nulos
   - Duplicados por `(municipio, codigo_postal)`
   - Cobertura por provincia/CCAA

Checklist de validación:
- [ ] 0 filas con `zona_climatica_cte` fuera de patrón
- [ ] 0 filas con obligatorios nulos
- [ ] 0 duplicados por `(municipio, codigo_postal)` o justificados
- [ ] Cobertura esperada por provincia/CCAA

## 3) Cobertura operativa
Comparar contra universo real consultado por el motor (no ejecutar en prod):
- Extraer CP/municipio_ine efectivos desde `db_N2.coordenadas_geograficas_enriquecidas`.
- Cruce con `stg_zonas_climaticas_cte` para medir misses.
- Objetivo: 100% cobertura de CP/municipio en uso; cualquier miss se corrige en catálogo antes de promoción.

## 4) Promoción a CORE (controlada)
1. Asegurar (manual) única de negocio en CORE:
   - Recomendación: `UNIQUE (municipio, codigo_postal)` sobre `public.core_zonas_climaticas`.
2. Ejecutar SQL de promoción:
   - `pipeline/Ncore/sql/zonas_climaticas_promocion.sql`
   - Inserta nuevas combinaciones y actualiza atributos con `ON CONFLICT` (si existe unique).
3. Post-validaciones:
   - Cobertura por provincia/CCAA en CORE
   - Spot-checks frente a fuente oficial

## 5) Operación y gobierno
- Uso en tiempo de ejecución:
  - Entrada: coordenadas → resolver `codigo_postal` + `municipio_ine` desde `db_N2.coordenadas_geograficas_enriquecidas`
  - Lookup: `db_Ncore.public.core_zonas_climaticas` por `(codigo_postal, municipio_ine)`
  - Política: sin fallbacks. Si falta, registrar incidencia y corregir catálogo, no estimar.
- Auditoría:
  - Todos los registros con `fuente` y `fecha_actualizacion`.
  - Job diario de misses para control de calidad.

## 6) Rollback
- Si la promoción introduce errores:
  - Revertir transacción si no se ha confirmado.
  - Si ya se confirmó: snapshot previo y `DELETE` selectivo por provincia/CCAA; volver a promover tras corregir STAGING.

## 7) Contactos
- Owner: Equipo Datos Core (db_Ncore)
- Revisión: Arquitectura y Cumplimiento

## 8) Versionado
- Mantener versión y fecha del catálogo CTE en `fuente` y `fecha_actualizacion`.
- Registrar cambios significativos en CHANGELOG del módulo CORE.
