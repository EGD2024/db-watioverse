-- Upsert normalizado de BOE (precio regulado) en db_Ncore
-- Requiere FDW y foreign table: f_precio_regulado_boe
-- Normaliza unidades y elimina duplicados por (tarifa_peaje, componente, fecha_inicio)

WITH norm AS (
  SELECT
    id,
    tarifa_peaje,
    componente,
    CASE
      WHEN unidad IN ('€/kWh','EUR/kWh') THEN 'EUR/kWh'
      WHEN unidad IN ('€/kW·día','EUR/kW·día','EUR/kW/día','€/kW·dia','EUR/kW·dia') THEN 'EUR/kW·día'
      ELSE unidad
    END AS unidad,
    precio,
    fecha_inicio,
    fecha_fin,
    ROW_NUMBER() OVER (
      PARTITION BY tarifa_peaje, componente, fecha_inicio
      ORDER BY COALESCE(fecha_fin, DATE '9999-12-31') DESC, id DESC
    ) AS rn
  FROM f_precio_regulado_boe
)
INSERT INTO core_precio_regulado_boe (id, tarifa_peaje, componente, unidad, precio, fecha_inicio, fecha_fin)
SELECT id, tarifa_peaje, componente, unidad, precio, fecha_inicio, fecha_fin
FROM norm
WHERE rn = 1
ON CONFLICT (tarifa_peaje, componente, fecha_inicio) DO UPDATE
SET precio = EXCLUDED.precio,
    fecha_fin = EXCLUDED.fecha_fin,
    unidad = EXCLUDED.unidad;
