-- db_Ncore.public.core_catastro_dic_clase
-- Diccionario de clase catastral (urbano/rústico)

-- Asegurar función de trigger disponible
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS public.core_catastro_dic_clase (
    clase_codigo               TEXT PRIMARY KEY CHECK (clase_codigo IN ('urbano','rustico')),
    descripcion                TEXT NOT NULL,
    fecha_actualizacion        TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at                 TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                 TIMESTAMP NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_core_catastro_dic_clase_updated_at ON public.core_catastro_dic_clase;
CREATE TRIGGER trg_core_catastro_dic_clase_updated_at
BEFORE UPDATE ON public.core_catastro_dic_clase
FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
