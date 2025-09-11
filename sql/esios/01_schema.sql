-- =====================================================
-- ESIOS Schema Migration - Core Tables
-- Base: db_Ncore
-- Fecha: 2025-09-09
-- =====================================================

-- Catálogo de indicadores ESIOS
CREATE TABLE IF NOT EXISTS core_esios_indicador (
  indicator_id integer PRIMARY KEY,
  nombre text NOT NULL,
  unidad text,
  geo_id integer DEFAULT 8741,
  descripcion text,
  activo boolean DEFAULT true,
  ultima_actualizacion timestamptz,
  created_at timestamptz DEFAULT now()
);

-- Valores horarios ESIOS (genérico)
CREATE TABLE IF NOT EXISTS core_esios_valor_horario (
  indicator_id integer NOT NULL REFERENCES core_esios_indicador(indicator_id),
  fecha_hora timestamptz NOT NULL,
  geo_id integer NOT NULL DEFAULT 8741,
  valor numeric,
  raw jsonb,
  fuente text DEFAULT 'ESIOS',
  created_at timestamptz DEFAULT now(),
  PRIMARY KEY (indicator_id, fecha_hora, geo_id)
);

-- Seguimiento de ejecuciones y versionado de ingestas (obligatorio)
CREATE TABLE IF NOT EXISTS core_esios_ingesta_ejecucion (
  id_ingesta bigserial PRIMARY KEY,
  indicator_id integer NOT NULL REFERENCES core_esios_indicador(indicator_id),
  geo_id integer NOT NULL DEFAULT 8741,
  ts_inicio timestamptz NOT NULL DEFAULT now(),
  ts_fin timestamptz,
  version_fuente text,
  filas_afectadas integer,
  estado text NOT NULL DEFAULT 'ok', -- ok|warning|error
  mensaje text,
  created_at timestamptz DEFAULT now()
);

-- Agregados diarios - PVPC
CREATE TABLE IF NOT EXISTS core_esios_pvpc_diario (
  dia date PRIMARY KEY,
  pvpc_medio_kwh numeric,
  pvpc_min_kwh numeric,
  pvpc_max_kwh numeric,
  created_at timestamptz DEFAULT now()
);

-- Agregados diarios - Mix energético
CREATE TABLE IF NOT EXISTS core_esios_mix_diario (
  dia date PRIMARY KEY,
  renovable_mwh numeric,
  no_renovable_mwh numeric,
  renovable_pct_medio numeric,
  created_at timestamptz DEFAULT now()
);

-- Agregados diarios - Emisiones
CREATE TABLE IF NOT EXISTS core_esios_emisiones_diario (
  dia date PRIMARY KEY,
  gco2_medio numeric,
  created_at timestamptz DEFAULT now()
);

-- Agregados diarios - Demanda
CREATE TABLE IF NOT EXISTS core_esios_demanda_diario (
  dia date PRIMARY KEY,
  demanda_max_mw numeric,
  demanda_media_mw numeric,
  created_at timestamptz DEFAULT now()
);

-- Modelo para publicaciones sociales - Resumen diario
CREATE TABLE IF NOT EXISTS core_esios_resumen_diario (
  dia date PRIMARY KEY,
  pvpc_medio_kwh numeric,
  pvpc_min_kwh numeric,
  pvpc_max_kwh numeric,
  gco2_medio numeric,
  renovable_pct_medio numeric,
  demanda_max_mw numeric,
  created_at timestamptz DEFAULT now()
);

-- Modelo para publicaciones sociales - Eventos
CREATE TABLE IF NOT EXISTS core_esios_evento_social (
  id_evento bigserial PRIMARY KEY,
  dia date NOT NULL,
  tipo text NOT NULL,
  indicator_id integer,
  valor numeric,
  unidad text,
  descripcion text,
  detalles jsonb,
  created_at timestamptz DEFAULT now()
);

-- =====================================================
-- ÍNDICES PARA RENDIMIENTO
-- =====================================================

-- Índice principal por fecha_hora
CREATE INDEX IF NOT EXISTS idx_esios_valor_hora 
ON core_esios_valor_horario (fecha_hora);

-- Índice compuesto para consultas por indicador
CREATE INDEX IF NOT EXISTS idx_esios_valor_indicator_fecha 
ON core_esios_valor_horario (indicator_id, fecha_hora DESC);

-- Índice para eventos sociales por día
CREATE INDEX IF NOT EXISTS idx_evento_social_dia 
ON core_esios_evento_social (dia);

-- Índice para ejecuciones por indicador
CREATE INDEX IF NOT EXISTS idx_ingesta_indicator_ts 
ON core_esios_ingesta_ejecucion (indicator_id, ts_inicio DESC);

-- =====================================================
-- COMENTARIOS EN TABLAS
-- =====================================================

COMMENT ON TABLE core_esios_indicador IS 'Catálogo maestro de indicadores ESIOS válidos';
COMMENT ON TABLE core_esios_valor_horario IS 'Valores horarios por indicador ESIOS (UTC)';
COMMENT ON TABLE core_esios_ingesta_ejecucion IS 'Registro de ejecuciones de ingesta con versionado';
COMMENT ON TABLE core_esios_pvpc_diario IS 'Agregados diarios de PVPC (indicador 1001)';
COMMENT ON TABLE core_esios_mix_diario IS 'Agregados diarios de mix energético (1433/1434)';
COMMENT ON TABLE core_esios_emisiones_diario IS 'Agregados diarios de emisiones CO2 (1739)';
COMMENT ON TABLE core_esios_demanda_diario IS 'Agregados diarios de demanda (1293)';
COMMENT ON TABLE core_esios_resumen_diario IS 'Resumen diario para publicaciones RRSS';
COMMENT ON TABLE core_esios_evento_social IS 'Eventos destacados para contenido social';
