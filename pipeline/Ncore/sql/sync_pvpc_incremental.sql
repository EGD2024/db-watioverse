-- Sincronización PVPC horario (incremental 30 días) desde db_sistema_electrico → db_Ncore
-- Requiere FDW y foreign table: f_precios_horarios_pvpc
-- Unidades origen: €/kWh; destino: €/MWh (×1000)

INSERT INTO core_precios_omie (timestamp_hora, precio_spot, precio_ajuste, precio_final)
SELECT
  (p.fecha + p.hora)::timestamp                 AS timestamp_hora,
  (p.precio_energia*1000)::numeric             AS precio_spot,
  ((COALESCE(p.precio_peajes,0)
    + COALESCE(p.precio_cargos,0))*1000)::numeric AS precio_ajuste,
  (p.precio_total_pvpc*1000)::numeric          AS precio_final
FROM f_precios_horarios_pvpc p
WHERE p.fecha >= CURRENT_DATE - INTERVAL '30 days'
ON CONFLICT (timestamp_hora) DO UPDATE
SET precio_spot   = EXCLUDED.precio_spot,
    precio_ajuste = EXCLUDED.precio_ajuste,
    precio_final  = EXCLUDED.precio_final;
