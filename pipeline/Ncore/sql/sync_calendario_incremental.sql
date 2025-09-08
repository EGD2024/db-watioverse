-- Sincronización incremental de calendario (últimos 14 días)
-- Requiere FDW y foreign tables: f_calendario_tarifario_2020..2025

-- 2024
INSERT INTO core_calendario_horario
  (fecha, hora, provincia, periodo_tarifario, año, mes, dia, dia_semana, semana_año, trimestre,
   es_festivo, es_festivo_local, tipo_dia, temporada)
SELECT
  fecha,
  hora::smallint,
  provincia,
  periodo_tarifa,
  EXTRACT(YEAR FROM fecha)::int,
  EXTRACT(MONTH FROM fecha)::int,
  EXTRACT(DAY FROM fecha)::int,
  EXTRACT(DOW FROM fecha)::int,
  EXTRACT(WEEK FROM fecha)::int,
  EXTRACT(QUARTER FROM fecha)::int,
  es_festivo,
  es_festivo_local,
  tipo_dia,
  temporada
FROM f_calendario_tarifario_2024
WHERE fecha >= CURRENT_DATE - INTERVAL '14 days'
ON CONFLICT (fecha, hora, provincia) DO UPDATE
SET periodo_tarifario = EXCLUDED.periodo_tarifario;

-- 2025
INSERT INTO core_calendario_horario
  (fecha, hora, provincia, periodo_tarifario, año, mes, dia, dia_semana, semana_año, trimestre,
   es_festivo, es_festivo_local, tipo_dia, temporada)
SELECT
  fecha,
  hora::smallint,
  provincia,
  periodo_tarifa,
  EXTRACT(YEAR FROM fecha)::int,
  EXTRACT(MONTH FROM fecha)::int,
  EXTRACT(DAY FROM fecha)::int,
  EXTRACT(DOW FROM fecha)::int,
  EXTRACT(WEEK FROM fecha)::int,
  EXTRACT(QUARTER FROM fecha)::int,
  es_festivo,
  es_festivo_local,
  tipo_dia,
  temporada
FROM f_calendario_tarifario_2025
WHERE fecha >= CURRENT_DATE - INTERVAL '14 days'
ON CONFLICT (fecha, hora, provincia) DO UPDATE
SET periodo_tarifario = EXCLUDED.periodo_tarifario;
