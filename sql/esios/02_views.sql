-- =====================================================
-- ESIOS Views Migration - Vistas Canónicas
-- Base: db_Ncore
-- Fecha: 2025-09-09
-- =====================================================

-- =====================================================
-- VISTAS CANÓNICAS POR INDICADOR (v_esios_ind_{ID})
-- =====================================================

-- PVPC 2.0TD (★ crítico para simulación)
CREATE OR REPLACE VIEW v_esios_ind_1001 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1001;

-- PVPC 3.0TD
CREATE OR REPLACE VIEW v_esios_ind_1002 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1002;

-- Precio mercado diario
CREATE OR REPLACE VIEW v_esios_ind_600 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 600;

-- Precio mercado intradiario
CREATE OR REPLACE VIEW v_esios_ind_601 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 601;

-- Peajes de transporte
CREATE OR REPLACE VIEW v_esios_ind_1900 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1900;

-- Cargos del sistema
CREATE OR REPLACE VIEW v_esios_ind_1901 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1901;

-- Demanda en tiempo real (YA USADO)
CREATE OR REPLACE VIEW v_esios_ind_1293 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1293;

-- Demanda prevista
CREATE OR REPLACE VIEW v_esios_ind_1294 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1294;

-- Generación renovable (YA USADO)
CREATE OR REPLACE VIEW v_esios_ind_1433 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1433;

-- Generación no renovable (YA USADO)
CREATE OR REPLACE VIEW v_esios_ind_1434 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1434;

-- Generación eólica
CREATE OR REPLACE VIEW v_esios_ind_1435 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1435;

-- Generación solar fotovoltaica
CREATE OR REPLACE VIEW v_esios_ind_1436 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1436;

-- Emisiones de CO2 (YA USADO)
CREATE OR REPLACE VIEW v_esios_ind_1739 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1739;

-- =====================================================
-- VISTAS ALIAS DESCRIPTIVOS
-- =====================================================

-- PVPC horario (★ crítico)
CREATE OR REPLACE VIEW v_esios_pvpc_horario AS
SELECT fecha_hora, geo_id, valor as pvpc_eur_mwh, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1001;

-- PVPC 3 periodos
CREATE OR REPLACE VIEW v_esios_pvpc_3p AS
SELECT fecha_hora, geo_id, valor as pvpc_3p_eur_mwh, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1002;

-- Mercado diario
CREATE OR REPLACE VIEW v_esios_mercado_diario AS
SELECT fecha_hora, geo_id, valor as precio_diario_eur_mwh, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 600;

-- Mercado intradiario
CREATE OR REPLACE VIEW v_esios_intradiario AS
SELECT fecha_hora, geo_id, valor as precio_intradiario_eur_mwh, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 601;

-- Peajes de transporte
CREATE OR REPLACE VIEW v_esios_peajes_transporte AS
SELECT fecha_hora, geo_id, valor as peajes_eur_mwh, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1900;

-- Cargos del sistema
CREATE OR REPLACE VIEW v_esios_cargos_sistema AS
SELECT fecha_hora, geo_id, valor as cargos_eur_mwh, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1901;

-- Demanda horaria
CREATE OR REPLACE VIEW v_esios_demanda_horaria AS
SELECT fecha_hora, geo_id, valor as demanda_mw, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1293;

-- Emisiones horarias
CREATE OR REPLACE VIEW v_esios_emisiones_horarias AS
SELECT fecha_hora, geo_id, valor as gco2_kwh, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1739;

-- Mix renovable vs no renovable
CREATE OR REPLACE VIEW v_esios_mix_ren_no_ren AS
SELECT 
    COALESCE(r.fecha_hora, nr.fecha_hora) as fecha_hora,
    COALESCE(r.geo_id, nr.geo_id) as geo_id,
    r.valor as renovable_mw,
    nr.valor as no_renovable_mw,
    CASE 
        WHEN (COALESCE(r.valor,0) + COALESCE(nr.valor,0)) > 0 
        THEN (COALESCE(r.valor,0) * 100.0) / (COALESCE(r.valor,0) + COALESCE(nr.valor,0))
        ELSE NULL 
    END as renovable_pct,
    GREATEST(COALESCE(r.created_at, '1900-01-01'), COALESCE(nr.created_at, '1900-01-01')) as created_at
FROM 
    (SELECT * FROM core_esios_valor_horario WHERE indicator_id = 1433) r
    FULL OUTER JOIN 
    (SELECT * FROM core_esios_valor_horario WHERE indicator_id = 1434) nr
    ON r.fecha_hora = nr.fecha_hora AND r.geo_id = nr.geo_id;

-- =====================================================
-- VISTAS ADICIONALES PARA INDICADORES COMPLETOS
-- =====================================================

-- Pérdidas en transporte
CREATE OR REPLACE VIEW v_esios_ind_1295 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1295;

-- Pérdidas en distribución
CREATE OR REPLACE VIEW v_esios_ind_1296 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1296;

-- TIEPI
CREATE OR REPLACE VIEW v_esios_ind_1350 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1350;

-- NIEPI
CREATE OR REPLACE VIEW v_esios_ind_1351 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1351;

-- Factor de potencia
CREATE OR REPLACE VIEW v_esios_ind_1400 AS
SELECT fecha_hora, geo_id, valor, raw, created_at 
FROM core_esios_valor_horario
WHERE indicator_id = 1400;

-- =====================================================
-- COMENTARIOS EN VISTAS
-- =====================================================

COMMENT ON VIEW v_esios_pvpc_horario IS 'PVPC 2.0TD horario (★ crítico para simulación)';
COMMENT ON VIEW v_esios_mercado_diario IS 'Precios mercado diario OMIE';
COMMENT ON VIEW v_esios_intradiario IS 'Precios mercado intradiario';
COMMENT ON VIEW v_esios_peajes_transporte IS 'Peajes de transporte regulados';
COMMENT ON VIEW v_esios_cargos_sistema IS 'Cargos del sistema eléctrico';
COMMENT ON VIEW v_esios_mix_ren_no_ren IS 'Mix energético renovable vs no renovable con porcentajes';
