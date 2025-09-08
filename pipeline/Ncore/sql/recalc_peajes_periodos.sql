-- Recalcular precios de energía por periodo (P1..P6) en core_peajes_acceso
-- Origen: v_precios_pvpc_horario (peaje/cargo por hora) + core_calendario_horario (periodo por hora)
-- Vigencias: f_tarifa_peaje_actual
-- Nota: usa la fecha de referencia vigente (día actual acotado a la vigencia)

WITH t AS (
  SELECT tpa.tarifa_peaje,
         tpa.fecha_inicio,
         COALESCE(tpa.fecha_fin, DATE '9999-12-31') AS fecha_fin,
         tpa.num_periodos_energia AS periodos
  FROM f_tarifa_peaje_actual tpa
),
ref AS (
  SELECT tarifa_peaje,
         GREATEST(fecha_inicio, LEAST(CURRENT_DATE, fecha_fin)) AS ref_date
  FROM t
),
rates AS (
  SELECT p.tarifa_peaje,
         c.periodo_tarifario AS periodo,
         AVG(COALESCE(p.precio_peaje_cte,0) + COALESCE(p.precio_cargo_cte,0)) AS precio_energia_kwh
  FROM f_v_precios_pvpc_horario p
  JOIN core_calendario_horario c
    ON c.fecha = p.fecha
   AND c.hora  = p.hora::smallint
   AND c.provincia = 'Madrid'  -- referencia reproducible; ajustar si se requiere otra lógica
  JOIN ref r ON r.tarifa_peaje = p.tarifa_peaje
  WHERE p.fecha = r.ref_date
  GROUP BY 1,2
),
pivot AS (
  SELECT tarifa_peaje,
         MAX(CASE WHEN periodo='P1' THEN precio_energia_kwh END) AS e_p1,
         MAX(CASE WHEN periodo='P2' THEN precio_energia_kwh END) AS e_p2,
         MAX(CASE WHEN periodo='P3' THEN precio_energia_kwh END) AS e_p3,
         MAX(CASE WHEN periodo='P4' THEN precio_energia_kwh END) AS e_p4,
         MAX(CASE WHEN periodo='P5' THEN precio_energia_kwh END) AS e_p5,
         MAX(CASE WHEN periodo='P6' THEN precio_energia_kwh END) AS e_p6
  FROM rates
  GROUP BY 1
)
INSERT INTO core_peajes_acceso (
  codigo_tarifa, descripcion, tension, periodos,
  precio_energia_p1, precio_energia_p2, precio_energia_p3,
  precio_energia_p4, precio_energia_p5, precio_energia_p6,
  vigente_desde, vigente_hasta, fuente
)
SELECT
  t.tarifa_peaje AS codigo_tarifa,
  NULL::varchar  AS descripcion,
  NULL::varchar  AS tension,
  t.periodos     AS periodos,
  pv.e_p1, pv.e_p2, pv.e_p3, pv.e_p4, pv.e_p5, pv.e_p6,
  t.fecha_inicio AS vigente_desde,
  t.fecha_fin    AS vigente_hasta,
  'BOE+PVPC'     AS fuente
FROM t
JOIN pivot pv ON pv.tarifa_peaje = t.tarifa_peaje
ON CONFLICT (codigo_tarifa, vigente_desde) DO UPDATE
SET precio_energia_p1 = EXCLUDED.precio_energia_p1,
    precio_energia_p2 = EXCLUDED.precio_energia_p2,
    precio_energia_p3 = EXCLUDED.precio_energia_p3,
    precio_energia_p4 = EXCLUDED.precio_energia_p4,
    precio_energia_p5 = EXCLUDED.precio_energia_p5,
    precio_energia_p6 = EXCLUDED.precio_energia_p6;

REFRESH MATERIALIZED VIEW mv_tarifas_vigentes;
