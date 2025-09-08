-- db_Ncore.public.core_catastro_dic_uso
-- Diccionario de usos Catastro (no-PII). Clave: uso_principal (literal tal y como llega del origen/cache)
-- Política: sin duplicados, sin nulls, sin normalizar silenciosamente.

CREATE TABLE IF NOT EXISTS public.core_catastro_dic_uso (
    uso_principal              TEXT PRIMARY KEY,
    descripcion                TEXT NOT NULL,
    fuente                     TEXT NOT NULL DEFAULT 'catastro_cache',
    fecha_actualizacion        TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at                 TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                 TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Trigger opcional para updated_at
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_core_catastro_dic_uso_updated_at ON public.core_catastro_dic_uso;
CREATE TRIGGER trg_core_catastro_dic_uso_updated_at
BEFORE UPDATE ON public.core_catastro_dic_uso
FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Índice para búsquedas por texto (si procede)
CREATE INDEX IF NOT EXISTS idx_core_catastro_dic_uso_desc ON public.core_catastro_dic_uso (LOWER(descripcion));
