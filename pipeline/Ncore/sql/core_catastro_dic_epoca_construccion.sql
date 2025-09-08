-- db_Ncore.public.core_catastro_dic_epoca_construccion
-- Rangos de épocas constructivas para análisis (no-PII)

CREATE TABLE IF NOT EXISTS public.core_catastro_dic_epoca_construccion (
    rango_anio_min             INT NOT NULL,
    rango_anio_max             INT NOT NULL,
    etiqueta_epoca             TEXT NOT NULL,
    PRIMARY KEY (rango_anio_min, rango_anio_max),
    CHECK (rango_anio_min <= rango_anio_max)
);
