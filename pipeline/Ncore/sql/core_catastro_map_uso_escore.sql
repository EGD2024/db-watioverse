-- db_Ncore.public.core_catastro_map_uso_escore
-- Mapa de uso Catastro -> categoría eSCORE (no-PII)

CREATE TABLE IF NOT EXISTS public.core_catastro_map_uso_escore (
    uso_principal              TEXT PRIMARY KEY REFERENCES public.core_catastro_dic_uso(uso_principal) ON UPDATE CASCADE ON DELETE RESTRICT,
    categoria_escore           TEXT NOT NULL,
    fecha_actualizacion        TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at                 TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                 TIMESTAMP NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_core_catastro_map_uso_escore_updated_at ON public.core_catastro_map_uso_escore;
CREATE TRIGGER trg_core_catastro_map_uso_escore_updated_at
BEFORE UPDATE ON public.core_catastro_map_uso_escore
FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
