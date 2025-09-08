# Prompt Mejorado · Auditoría y Rediseño de Arquitectura DB + Integración eSCORE

## Ámbito
- Motores y repos: `db_enriquecimiento`, `db_watioverse`, **motor `eSCORE`**.
- Fuentes: TODOS los README y código asociado; inspección directa de DBs accesibles vía **MCP** (esquemas, tablas, relaciones, vistas, índices, funciones).
- Objetivo global: validar si **diseño de DB, relaciones, carpetas, campos y datos** son correctos o deben reestructurarse para:
  - Generar **informes contextuales por ámbito** (p. ej., climatológico, solar) a partir de datos reales.
  - Cubrir **periodo de factura** y **últimos 12 meses** (rolling) con comparación de tendencias, máximos, mínimos y extremos.
  - Producir **eSCORE mensual** y **eSCORE anual**, con **agregaciones entre clientes** (cohortes).
  - Exponer **tablas de acceso muy rápido** para ingestión por LLM.
  - Mantener **separación estricta** entre datos de **backup rápida (no‑PII)** y **datos personales** derivados por cliente.
  - Asegurar que **estructura de scripts y archivos de código** soporta todo lo anterior.

## Tareas (ejecutar en este orden)
1. **Revisión documental**: leer en detalle todos los README de `db_enriquecimiento`, `db_watioverse` y del motor `eSCORE`. Extraer supuestos, contratos de datos, catálogos y SLAs declarados.
2. **Inventario MCP (exhaustivo)** de cada DB accesible:
   - Listar esquemas, tablas, columnas (tipo, nullability, default), PK, UK, FK, índices, vistas (normales/materializadas), funciones, triggers, particiones.
   - Volumen por tabla (filas), fechas min/max, cardinalidades y selectividad estimada de índices.
3. **Validación de relaciones**:
   - Comprobar integridad referencial efectiva (FK válidas, orfandad 0%), consistencia de dominios y claves sustitutas.
   - Detectar solapamientos/duplicidades entre tablas de contexto y tablas por cliente.
4. **Revisión de código** (ETL/ELT, jobs, scripts, orquestación):
   - Entradas/salidas, dependencias, rutas y **nomenclatura de carpetas**. Verificar que reflejan la arquitectura objetivo.
   - Identificar pasos costosos (full scans, cross joins, desnormalizaciones innecesarias).
5. **Bench básico** (sobre SELECTs críticas):
   - Lookup por cliente + periodo (p95 < 50 ms).
   - Generación informe ámbito factura (p95 < 500 ms).
   - Agregación 12m por cohorte (p95 < 800 ms).
6. **Diagnóstico**: evaluar corrección y eficiencia de arquitectura actual vs. objetivos.
7. **Rediseño propuesto** (si aplica): DDL exacto, planes de migración, índices/particiones/vistas materializadas, y cambios en carpetas/scripts.

## Requisitos funcionales (obligatorios)
- **Informes por ámbito** (al menos “clima” y “solar”), para:
  - **Periodo factura** y **últimos 12 meses** del mismo cliente.
  - Métricas: tendencias, picos, valles, extremos, percentiles (p10/p50/p90), medias móviles (7/30 días), anomalías básicas.
- **eSCORE**:
  - Cálculo **mensual** por cliente.
  - Cálculo **anual** por cliente (agregación de los 12 meses, definiendo reglas claras: media ponderada/mediana/p95 según indicador).
  - **Agregaciones entre clientes** por cohortes: sector/actividad, peaje, zona climática, potencia contratada, tamaño/segmento, geografía.
- **Tablas rápidas para LLM** (read‑only, serialización directa):
  - Una por cliente/ámbito/periodo con features ya agregadas y diccionario de campos.
  - Una por **cohorte** con features agregadas de referencia (“contexto agregado”).
- **Separación de datos**:
  - **Backup rápida / contexto no‑PII** en un esquema/DB separado.
  - **Datos personales** (PII, derivados) en esquema/DB aislado con join solo por claves sustitutas/hashed.

## Requisitos técnicos (obligatorios)
- **Modelado**: claves sustitutas (`*_sk`), tablas de hechos y dimensiones temporales; evitar PII en hechos.
- **Particionado**: por mes (`yyyymm`) en hechos históricos de alto volumen; **indexación compuesta** (cliente_sk, periodo).
- **Índices**: B‑tree en PK/joins y GIN/BRIN donde aplique. Documentar justificación.
- **Vistas materializadas** para informes 12m y eSCORE anual; **refresh** incremental (<= 1 h) o tras ingesta diaria.
- **Nomenclatura** consistente (`dim_*`, `fact_*`, `agg_*`, `rpt_*`, `mv_*`). 
- **Versionado de supuestos** (tabla `cfg_supuestos` con `version`, `desde`, `hasta`).
- **Seguridad**: RLS en datos personales; mascarado PII; logs de acceso.
- **Observabilidad**: logs estructurados, métricas SQL (tiempo, filas), linaje (origen → destino).

## Validaciones MCP (debes ejecutar y reportar)
- Enumeración completa de objetos por esquema y conteos de filas.
- Comprobación de FKs/PKs/UKs, índices no usados, tablas sin PK, columnas sin uso.
- Top 10 consultas por tiempo/lecturas si hay métricas disponibles.
- Verificación de tamaños/particiones y fechas min/max por tabla de hechos.
- Coherencia entre README ↔ DDL ↔ Código (nombres, tipos, contratos).

## Criterios de aceptación (SLAs)
- Lookup cliente+periodo: **p95 < 50 ms**.
- Informe factura (ámbito): **p95 < 500 ms**.
- Agregación 12m por cohorte: **p95 < 800 ms**.
- Refresh MV 12m: **< 10 min** incremental; **< 60 min** full.

## Salida (formato ESTRICTO, sin razonamientos)
Devuelve un único `.md` con las secciones siguientes y contenido **100% concreto**:

1. **Inventario actual**
   - Listado exacto de DB/esquemas/tablas/vistas/índices/funciones (con conteos, fechas min/max).
2. **Validación estructural**
   - Matriz PK/FK/UK por tabla (OK/KO), FKs huérfanas (conteo exacto), índices sin uso.
3. **Eficiencia**
   - Tiempos medidos (p50/p95) de las 3 consultas SLA. Recursos y observaciones.
4. **Conformidad documental**
   - Desviaciones README↔DDL↔Código (lista exacta).
5. **Juicio sobre arquitectura actual**: **CORRECTA** o **DEFICIENTE** (elige una). 
6. **Cambios necesarios (si DEFICIENTE)** 
   - **DDL exacto** (CREATE/ALTER/DROP) para tablas, índices, particiones, FKs.
   - **Vistas materializadas** con definición y políticas de refresh.
   - **Refactor de carpetas/scripts** (árbol de directorios final exacto).
7. **Esquema de informes**
   - Definición de tablas de informe por ámbito (clima, solar) para periodo factura y 12m: nombres, columnas (tipo, unidad, descripción), PK/índices.
8. **Esquema eSCORE**
   - Definición de tablas para eSCORE **mensual** y **anual** por cliente, y de **agregaciones por cohorte** (nombres, columnas, reglas de agregación).
9. **Separación de datos**
   - Esquemas/DB para **backup no‑PII** y **datos personales** (nombres exactos) y claves de cruce.
10. **Plan de migración**
    - Pasos atómicos con orden exacto, ventanas, verificaciones y rollback.
11. **Métricas post‑migración**
    - SLAs esperados y tests de validación automatizables.

## Notas finales
- **Dedica el tiempo necesario**: prioriza exactitud sobre velocidad.
- Si falta algún dato para completar una sección, **indica explícitamente el gap** y propone el **script/consulta MCP** para obtenerlo.
