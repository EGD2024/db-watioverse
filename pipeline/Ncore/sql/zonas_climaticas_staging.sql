-- db_Ncore.public.core_zonas_climaticas · Carga segura por STAGING
-- NO EJECUTAR en producción sin revisión. Este script crea tablas de staging y ayudas de validación.
-- No modifica la tabla final `core_zonas_climaticas`.

-- 1) Tabla de STAGING (solo para importación temporal)
CREATE TABLE IF NOT EXISTS public.stg_zonas_climaticas_cte (
    -- Claves de búsqueda
    codigo_postal              VARCHAR NOT NULL,
    municipio                  VARCHAR NOT NULL,
    provincia                  VARCHAR NOT NULL,
    comunidad_autonoma         VARCHAR NOT NULL,
    zona_climatica_cte         VARCHAR NOT NULL,

    -- Atributos de referencia (opcionales si no están en la fuente)
    altitud                    INTEGER,
    latitud                    NUMERIC,
    longitud                   NUMERIC,
    hdd_anual_medio            NUMERIC,
    cdd_anual_medio            NUMERIC,
    temperatura_media_anual    NUMERIC,
    radiacion_global_anual     NUMERIC,

    -- Metadatos de trazabilidad
    fecha_actualizacion        TIMESTAMP,
    fuente                     VARCHAR,

    -- Campo auxiliar de validación (no existe en core)
    municipio_ine              VARCHAR
);

-- 2) Índices para validación y velocidad de comprobaciones
CREATE INDEX IF NOT EXISTS idx_stg_zonas_cte_cp ON public.stg_zonas_climaticas_cte(codigo_postal);
CREATE INDEX IF NOT EXISTS idx_stg_zonas_cte_mun ON public.stg_zonas_climaticas_cte(municipio);
CREATE INDEX IF NOT EXISTS idx_stg_zonas_cte_mun_cp ON public.stg_zonas_climaticas_cte(municipio, codigo_postal);

-- 3) Checks de formato (informativos; no constraints para permitir revisión previa)
--    Validación patrón zona CTE (A-E + dígito)
--    Use bajo su criterio: SELECT que devuelve filas no conformes

-- Zonas CTE con formato inesperado
SELECT *
FROM public.stg_zonas_climaticas_cte
WHERE zona_climatica_cte !~ '^[A-E][0-9]$';

-- Filas con obligatorios nulos
SELECT *
FROM public.stg_zonas_climaticas_cte
WHERE codigo_postal IS NULL OR municipio IS NULL OR provincia IS NULL OR comunidad_autonoma IS NULL OR zona_climatica_cte IS NULL;

-- Posibles duplicados por (municipio, CP)
SELECT municipio, codigo_postal, COUNT(*) AS n
FROM public.stg_zonas_climaticas_cte
GROUP BY municipio, codigo_postal
HAVING COUNT(*) > 1
ORDER BY n DESC;

-- Cobertura por provincia / CCAA
SELECT provincia, COUNT(*) AS filas
FROM public.stg_zonas_climaticas_cte
GROUP BY provincia
ORDER BY provincia;

SELECT comunidad_autonoma, COUNT(*) AS filas
FROM public.stg_zonas_climaticas_cte
GROUP BY comunidad_autonoma
ORDER BY comunidad_autonoma;
