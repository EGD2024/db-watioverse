# RUNBOOK · Integración Catastro (OVC) → N2 y Diccionarios Ncore

Estado: listo para despliegue controlado (no ejecutar en prod sin checklist).

## 1) Alcance
- Cache de extracción: `db_enriquecimiento.public.catastro_inmuebles` (existente)
- Consolidado por CUPS: `db_N2.public.n2_catastro_inmueble`
- Diccionarios (no-PII) en `db_Ncore.public`:
  - `core_catastro_dic_uso`
  - `core_catastro_dic_tipologia`
  - `core_catastro_dic_clase`
  - `core_catastro_dic_epoca_construccion`
  - `core_catastro_map_uso_escore`

## 2) DDL (one-liners)
```bash
# Ncore
psql -U postgres -d db_Ncore -f ".../pipeline/Ncore/sql/core_catastro_dic_uso.sql" && \
psql -U postgres -d db_Ncore -f ".../pipeline/Ncore/sql/core_catastro_dic_tipologia.sql" && \
psql -U postgres -d db_Ncore -f ".../pipeline/Ncore/sql/core_catastro_dic_clase.sql" && \
psql -U postgres -d db_Ncore -f ".../pipeline/Ncore/sql/core_catastro_dic_epoca_construccion.sql" && \
psql -U postgres -d db_Ncore -f ".../pipeline/Ncore/sql/core_catastro_map_uso_escore.sql"

# N2
psql -U postgres -d db_N2 -f ".../pipeline/Ncore/sql/n2_catastro_inmueble.sql"
```

## 3) Jobs (one-liners cron)
```cron
# Diccionario de usos desde cache → Ncore
25 2 * * * DB_HOST=localhost DB_PORT=5432 DB_USER=postgres DB_PASSWORD=admin python3 /Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/pipeline/Ncore/jobs/build_catastro_dictionaries.py

# Mapeo uso → categoria_escore (falla si quedan usos sin mapear)
27 2 * * * DB_HOST=localhost DB_PORT=5432 DB_USER=postgres DB_PASSWORD=admin python3 /Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/pipeline/Ncore/jobs/build_catastro_usage_mapping.py

# Promoción cache → N2 (consolidado por CUPS)
30 2 * * * DB_HOST=localhost DB_PORT=5432 DB_USER=postgres DB_PASSWORD=admin python3 /Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/pipeline/Ncore/jobs/fetch_catastro_for_n2.py --max 200
```

## 4) Flujo operativo
1. `build_catastro_dictionaries.py` lee usos de `db_enriquecimiento.catastro_inmuebles` y pobla `core_catastro_dic_uso`.
2. `build_catastro_usage_mapping.py` categoriza usos → `core_catastro_map_uso_escore`. Si hay pendientes, falla para forzar mapeo explícito.
3. `fetch_catastro_for_n2.py` toma CUPS pendientes o desactualizados en N2 y promociona desde la cache, con validaciones.

## 5) Validaciones y políticas
- Sin fallbacks: si falta `uso_principal` o `superficie_construida_m2` < 0, se rechaza.
- Auditoría: `fuente`, `fecha_extraccion`, `updated_at` en N2; timestamps y updated_at en diccionarios.
- Integridad:
  - `clase_inmueble` ∈ {`urbano`,`rustico`} cuando se informe.
  - Superficies ≥ 0.
- Seguridad: conexiones por nombres reales de BD; sin alias.

## 6) Troubleshooting
- Usos sin mapear: revisar salida de `build_catastro_usage_mapping.py` y añadir reglas o EXACT.
- Campos nulos en cache: revisar `db_enriquecimiento.catastro_inmuebles` y reintentar extracción OVC.
- Errores de permisos: validar roles en db_Ncore y db_N2.

## 7) Contacto
- Owner: Equipo Datos CORE
- Integración: Equipo db_watioverse
