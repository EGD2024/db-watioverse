-- Sincronización OMIE diario desde db_sistema_electrico → db_Ncore
-- Requiere FDW y foreign table: f_omie_precios
-- Unidades origen: €/kWh; destino: €/MWh (×1000)

WITH daily AS (
  SELECT
    fecha,
    (AVG(precio_energia)*1000)::numeric       AS precio_medio_mwh,
    (MAX(precio_energia)*1000)::numeric       AS precio_max_mwh,
    (MIN(precio_energia)*1000)::numeric       AS precio_min_mwh,
    (STDDEV(precio_energia*1000))::numeric    AS volatilidad_mwh
  FROM f_omie_precios
  WHERE zona = 'ES'
    AND fecha BETWEEN CURRENT_DATE - INTERVAL '1 day' AND CURRENT_DATE + INTERVAL '1 day'
  GROUP BY fecha
)
INSERT INTO core_precios_omie_diario (fecha, precio_medio_mwh, precio_max_mwh, precio_min_mwh, volatilidad_mwh)
SELECT fecha, precio_medio_mwh, precio_max_mwh, precio_min_mwh, volatilidad_mwh
FROM daily
ON CONFLICT (fecha) DO UPDATE
SET precio_medio_mwh = EXCLUDED.precio_medio_mwh,
    precio_max_mwh   = EXCLUDED.precio_max_mwh,
    precio_min_mwh   = EXCLUDED.precio_min_mwh,
    volatilidad_mwh  = EXCLUDED.volatilidad_mwh;
