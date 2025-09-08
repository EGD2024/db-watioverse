-- db_Ncore.public.core_zonas_cte_reglas + función determinista
-- Este script crea la tabla de REGLAS del Anejo B (Provincia x Altitud -> Zona CTE)
-- y una función de consulta sin fallbacks. No inserta datos.

BEGIN;

-- 1) Tabla de reglas Anejo B
CREATE TABLE IF NOT EXISTS public.core_zonas_cte_reglas (
    id SERIAL PRIMARY KEY,
    provincia              VARCHAR NOT NULL,
    h_min                  INTEGER NOT NULL,
    h_max                  INTEGER NOT NULL,
    zona_climatica_cte     VARCHAR NOT NULL,
    fuente                 VARCHAR,
    fecha_actualizacion    TIMESTAMP,
    CONSTRAINT chk_zona_cte_format CHECK (zona_climatica_cte ~ '^[A-E][0-9]$'),
    CONSTRAINT uk_regla UNIQUE (provincia, h_min, h_max)
);

-- Índices de ayuda
CREATE INDEX IF NOT EXISTS idx_reglas_provincia ON public.core_zonas_cte_reglas (provincia);
CREATE INDEX IF NOT EXISTS idx_reglas_altura ON public.core_zonas_cte_reglas (h_min, h_max);

-- 2) Función determinista
--    Dado (provincia, altitud_msnm) devuelve la zona CTE.
--    - Sin fallbacks: si no hay match único, lanza excepción.
--    - Inclusivo en el límite superior (<= h_max) para soportar rangos exactos.

CREATE OR REPLACE FUNCTION public.get_zona_climatica_cte(
    p_provincia TEXT,
    p_altitud_msnm INTEGER
) RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    v_zona TEXT;
    v_count INTEGER;
BEGIN
    IF p_provincia IS NULL OR p_altitud_msnm IS NULL THEN
        RAISE EXCEPTION 'get_zona_climatica_cte: provincia y altitud son obligatorias';
    END IF;

    SELECT COUNT(*)
      INTO v_count
      FROM public.core_zonas_cte_reglas r
     WHERE r.provincia = p_provincia
       AND p_altitud_msnm >= r.h_min
       AND p_altitud_msnm <= r.h_max;

    IF v_count = 0 THEN
        RAISE EXCEPTION 'get_zona_climatica_cte: no hay regla para provincia=%, altitud=%', p_provincia, p_altitud_msnm;
    ELSIF v_count > 1 THEN
        RAISE EXCEPTION 'get_zona_climatica_cte: múltiples reglas para provincia=%, altitud=%', p_provincia, p_altitud_msnm;
    END IF;

    SELECT r.zona_climatica_cte
      INTO v_zona
      FROM public.core_zonas_cte_reglas r
     WHERE r.provincia = p_provincia
       AND p_altitud_msnm >= r.h_min
       AND p_altitud_msnm <= r.h_max
     LIMIT 1;

    RETURN v_zona;
END;
$$;

COMMIT;
