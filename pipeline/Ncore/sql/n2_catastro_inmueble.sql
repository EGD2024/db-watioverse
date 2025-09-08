-- db_N2.public.n2_catastro_inmueble (versionado aquí, ejecutado en db_N2)
-- Consolidación de atributos Catastro por CUPS (sin PII)

CREATE TABLE IF NOT EXISTS public.n2_catastro_inmueble (
    cups                              TEXT PRIMARY KEY,
    referencia_catastral              TEXT,
    uso_principal                     TEXT,
    superficie_construida_total_m2    NUMERIC CHECK (superficie_construida_total_m2 IS NULL OR superficie_construida_total_m2 >= 0),
    superficie_parcela_m2             NUMERIC,
    anio_construccion                 INT,
    anio_reforma                      INT,
    numero_plantas                    INT,
    tipologia_constructiva            TEXT,
    clase_inmueble                    TEXT CHECK (clase_inmueble IS NULL OR clase_inmueble IN ('urbano','rustico')),
    municipio                         TEXT,
    provincia                         TEXT,
    codigo_ine                        TEXT,
    latitud_verificada                NUMERIC,
    longitud_verificada               NUMERIC,
    fuente                            TEXT NOT NULL DEFAULT 'catastro_cache',
    fecha_extraccion                  TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at                        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                        TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Índices de apoyo
CREATE INDEX IF NOT EXISTS idx_n2_catastro_inmueble_prov_mun ON public.n2_catastro_inmueble (provincia, municipio);
CREATE INDEX IF NOT EXISTS idx_n2_catastro_inmueble_uso ON public.n2_catastro_inmueble (uso_principal);
