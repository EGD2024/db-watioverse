-- Épocas constructivas oficiales según normativa CTE
-- Basado en las normativas de eficiencia energética españolas

TRUNCATE TABLE public.core_catastro_dic_epoca_construccion;

INSERT INTO public.core_catastro_dic_epoca_construccion (rango_anio_min, rango_anio_max, etiqueta_epoca) VALUES
(0, 1979, 'Pre-NBE-CT-79'),           -- Sin normativa térmica
(1980, 2006, 'NBE-CT-79'),            -- Primera normativa térmica
(2007, 2013, 'CTE-2006'),              -- Código Técnico de la Edificación
(2014, 2019, 'CTE-2013'),              -- Actualización CTE DB-HE 2013
(2020, 9999, 'CTE-2019');              -- CTE DB-HE 2019 (nZEB)
