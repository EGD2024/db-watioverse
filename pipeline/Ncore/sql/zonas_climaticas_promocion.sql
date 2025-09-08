-- Promoción segura de STAGING a CORE (db_Ncore.public.core_zonas_climaticas)
-- NO EJECUTAR sin pasar todas las validaciones y checklist del RUNBOOK.
-- Este script asume que la tabla final ya existe y NO la modifica.

BEGIN;

-- 0) Garantizar que STAGING existe y está poblada
-- (comprobar manualmente antes de ejecutar)

-- 1) Comprobaciones de integridad previas (informativas)
-- 1.1) Campos obligatorios no nulos
SELECT COUNT(*) AS filas_nulas
FROM public.stg_zonas_climaticas_cte
WHERE codigo_postal IS NULL 
   OR municipio IS NULL 
   OR provincia IS NULL 
   OR comunidad_autonoma IS NULL 
   OR zona_climatica_cte IS NULL;

-- 1.2) Formato de zona CTE
SELECT COUNT(*) AS zonas_formato_incorrecto
FROM public.stg_zonas_climaticas_cte
WHERE zona_climatica_cte !~ '^[A-E][0-9]$';

-- 1.3) Duplicados por (municipio, codigo_postal)
SELECT COUNT(*) AS duplicados
FROM (
  SELECT municipio, codigo_postal, COUNT(*)
  FROM public.stg_zonas_climaticas_cte
  GROUP BY municipio, codigo_postal
  HAVING COUNT(*) > 1
) d;

-- 2) Inserción/Actualización controlada
-- Nota: se asume que la clave operativa será (municipio, codigo_postal).
-- Si existe otra clave en su modelo (p.ej. municipio_ine), ajústese.

-- Recomendación previa (manual):
--   Crear índice/único en core si aplica: UNIQUE (municipio, codigo_postal)
--   NO incluido aquí por seguridad.

-- 2.1) Upsert de registros desde STAGING a CORE
--     - Inserta nuevas combinaciones (municipio, CP)
--     - Actualiza atributos de referencia y trazabilidad
INSERT INTO public.core_zonas_climaticas (
    codigo_postal,
    municipio,
    provincia,
    comunidad_autonoma,
    zona_climatica_cte,
    altitud,
    latitud,
    longitud,
    hdd_anual_medio,
    cdd_anual_medio,
    temperatura_media_anual,
    radiacion_global_anual,
    fecha_actualizacion,
    fuente
)
SELECT 
    s.codigo_postal,
    s.municipio,
    s.provincia,
    s.comunidad_autonoma,
    s.zona_climatica_cte,
    s.altitud,
    s.latitud,
    s.longitud,
    s.hdd_anual_medio,
    s.cdd_anual_medio,
    s.temperatura_media_anual,
    s.radiacion_global_anual,
    COALESCE(s.fecha_actualizacion, NOW()),
    s.fuente
FROM public.stg_zonas_climaticas_cte s
ON CONFLICT (municipio, codigo_postal)
DO UPDATE SET
    provincia = EXCLUDED.provincia,
    comunidad_autonoma = EXCLUDED.comunidad_autonoma,
    zona_climatica_cte = EXCLUDED.zona_climatica_cte,
    altitud = EXCLUDED.altitud,
    latitud = EXCLUDED.latitud,
    longitud = EXCLUDED.longitud,
    hdd_anual_medio = EXCLUDED.hdd_anual_medio,
    cdd_anual_medio = EXCLUDED.cdd_anual_medio,
    temperatura_media_anual = EXCLUDED.temperatura_media_anual,
    radiacion_global_anual = EXCLUDED.radiacion_global_anual,
    fecha_actualizacion = EXCLUDED.fecha_actualizacion,
    fuente = EXCLUDED.fuente;

-- 3) Post-validaciones (informativas)
-- 3.1) Cobertura por provincia/CCA tras promoción
SELECT provincia, COUNT(*) AS filas
FROM public.core_zonas_climaticas
GROUP BY provincia
ORDER BY provincia;

SELECT comunidad_autonoma, COUNT(*) AS filas
FROM public.core_zonas_climaticas
GROUP BY comunidad_autonoma
ORDER BY comunidad_autonoma;

-- 4) Limpiar STAGING (opcional, manual)
-- TRUNCATE TABLE public.stg_zonas_climaticas_cte;

COMMIT;
