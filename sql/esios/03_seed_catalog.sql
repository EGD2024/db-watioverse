-- =====================================================
-- ESIOS Catalog Seed - Indicadores Confirmados
-- Base: db_Ncore
-- Fecha: 2025-09-09
-- =====================================================

-- Insertar indicadores ESIOS confirmados y acordados
-- Fuente: README Sistema Eléctrico - Cobertura completa SCORE y Redes Sociales

INSERT INTO core_esios_indicador (indicator_id, nombre, unidad, geo_id, descripcion, activo) VALUES
-- Precios y Costes Energéticos
(1001, 'PVPC 2.0TD', 'EUR/MWh', 8741, 'PVPC 2.0TD (término de energía activa)', true),
(1002, 'PVPC 3.0TD', 'EUR/MWh', 8741, 'PVPC 3.0TD con discriminación horaria avanzada', true),
(600, 'Precio mercado diario', 'EUR/MWh', 8741, 'Precio mercado diario OMIE', true),
(601, 'Precio mercado intradiario', 'EUR/MWh', 8741, 'Precio mercado intradiario - volatilidad tiempo real', true),
(1900, 'Peajes de transporte', 'EUR/MWh', 8741, 'Peajes de transporte regulados', true),
(1901, 'Cargos del sistema', 'EUR/MWh', 8741, 'Cargos del sistema - políticas energéticas', true),

-- Calidad y Eficiencia del Suministro
(1295, 'Pérdidas en transporte', '%', 8741, 'Pérdidas en transporte - eficiencia red eléctrica', true),
(1296, 'Pérdidas en distribución', '%', 8741, 'Pérdidas en distribución - calidad técnica suministro', true),
(1350, 'TIEPI', 'min/año', 8741, 'Tiempo de interrupción equivalente - fiabilidad suministro', true),
(1351, 'NIEPI', 'interrupciones/año', 8741, 'Frecuencia de interrupción equivalente - estabilidad red', true),
(1400, 'Factor de potencia', 'adimensional', 8741, 'Factor de potencia - eficiencia energética consumo', true),

-- Mix Energético Detallado
(1433, 'Generación renovable', 'MW', 8741, 'Generación renovable total - sostenibilidad', true),
(1434, 'Generación no renovable', 'MW', 8741, 'Generación no renovable - huella carbono', true),
(1435, 'Generación eólica', 'MW', 8741, 'Generación eólica específica', true),
(1436, 'Generación solar fotovoltaica', 'MW', 8741, 'Generación solar fotovoltaica específica', true),
(1437, 'Generación hidráulica', 'MW', 8741, 'Generación hidráulica - estabilidad renovable', true),
(1438, 'Generación nuclear', 'MW', 8741, 'Generación nuclear - estabilidad base sistema', true),
(1440, 'Generación cogeneración', 'MW', 8741, 'Generación cogeneración - eficiencia energética industrial', true),

-- Demanda y Patrones de Consumo
(1293, 'Demanda tiempo real', 'MW', 8741, 'Demanda eléctrica en tiempo real - patrones consumo', true),
(1294, 'Demanda prevista', 'MW', 8741, 'Demanda prevista - predictibilidad consumo', true),
(1310, 'Demanda industrial', 'MW', 8741, 'Demanda industrial - benchmarking sectorial', true),
(1311, 'Demanda residencial', 'MW', 8741, 'Demanda residencial - score específico hogares', true),
(1312, 'Demanda servicios', 'MW', 8741, 'Demanda servicios - score específico terciario', true),
(1320, 'Punta de demanda diaria', 'MW', 8741, 'Punta de demanda diaria - eficiencia en picos', true),

-- Almacenamiento y Flexibilidad
(1500, 'Bombeo hidráulico', 'MW', 8741, 'Bombeo hidráulico - flexibilidad del sistema', true),
(1501, 'Baterías sistema', 'MW', 8741, 'Baterías del sistema - modernización red', true),
(1502, 'Gestión de demanda', 'MW', 8741, 'Gestión de demanda - participación flexibilidad', true),
(1510, 'Servicios de ajuste', 'MW', 8741, 'Servicios de ajuste - calidad técnica suministro', true),

-- Emisiones y Transición
(1739, 'Emisiones CO2', 'gCO2/kWh', 8741, 'Emisiones de CO2 del sistema eléctrico', true),
(1460, 'Cierre centrales carbón', 'MW', 8741, 'Cierre centrales carbón - transición energética', true),
(1461, 'Nueva potencia renovable', 'MW', 8741, 'Nueva potencia renovable instalada', true),

-- Autoconsumo y Movilidad
(1450, 'Autoproducción solar', 'MW', 8741, 'Autoproducción solar distribuida', true),
(1470, 'Electrolineras', 'unidades', 8741, 'Red de electrolineras - movilidad eléctrica', true),
(1480, 'Autoconsumo residencial', 'MW', 8741, 'Autoconsumo residencial - prosumidores', true),

-- Interconexiones y Comparativas
(1800, 'Intercambios Francia', 'MW', 8741, 'Intercambios eléctricos con Francia', true),
(1801, 'Intercambios Portugal', 'MW', 8741, 'Intercambios eléctricos con Portugal', true),
(1802, 'Intercambios Marruecos', 'MW', 8741, 'Intercambios eléctricos con Marruecos', true),

-- Eventos Estacionales
(1600, 'Demanda navideña', 'MW', 8741, 'Demanda eléctrica periodo navideño', true),
(1601, 'Demanda verano', 'MW', 8741, 'Demanda eléctrica periodo estival', true),
(1602, 'Generación durante eclipse', 'MW', 8741, 'Generación solar durante eclipses', true),
(1603, 'Temporal y eólica', 'MW', 8741, 'Generación eólica durante temporales', true)

ON CONFLICT (indicator_id) DO UPDATE SET
    nombre = EXCLUDED.nombre,
    unidad = EXCLUDED.unidad,
    descripcion = EXCLUDED.descripcion,
    activo = EXCLUDED.activo;

-- =====================================================
-- VERIFICACIÓN DE INSERCIÓN
-- =====================================================

-- Mostrar resumen de indicadores insertados
SELECT 
    COUNT(*) as total_indicadores,
    COUNT(*) FILTER (WHERE activo = true) as activos,
    COUNT(*) FILTER (WHERE unidad = 'EUR/MWh') as precios,
    COUNT(*) FILTER (WHERE unidad = 'MW') as potencia,
    COUNT(*) FILTER (WHERE unidad = 'gCO2/kWh') as emisiones
FROM core_esios_indicador;

-- Mostrar indicadores críticos para PVPC (★)
SELECT indicator_id, nombre, unidad, descripcion 
FROM core_esios_indicador 
WHERE indicator_id IN (1001, 1002, 600, 601, 1900, 1901)
ORDER BY indicator_id;

-- =====================================================
-- COMENTARIOS FINALES
-- =====================================================

COMMENT ON TABLE core_esios_indicador IS 'Catálogo completo de indicadores ESIOS para SCORE y Redes Sociales - Actualizado 2025-09-09';
