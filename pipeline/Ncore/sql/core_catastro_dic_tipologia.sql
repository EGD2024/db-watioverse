-- db_Ncore.public.core_catastro_dic_tipologia
-- Diccionario de tipologías constructivas Catastro (no-PII)

-- Asegurar función de trigger disponible
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS public.core_catastro_dic_tipologia (
    tipologia_constructiva     TEXT PRIMARY KEY,
    descripcion                TEXT NOT NULL,
    fuente                     TEXT NOT NULL DEFAULT 'catastro_cache',
    fecha_actualizacion        TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at                 TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                 TIMESTAMP NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_core_catastro_dic_tipologia_updated_at ON public.core_catastro_dic_tipologia;
CREATE TRIGGER trg_core_catastro_dic_tipologia_updated_at
BEFORE UPDATE ON public.core_catastro_dic_tipologia
FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
