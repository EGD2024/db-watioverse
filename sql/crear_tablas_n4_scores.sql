-- =====================================================
-- CREACIÓN DE TABLAS N4 PARA SCORES FINALES
-- Basado en nueva estructura de indicadores con APIs
-- Fecha: 2025-09-08
-- Base de datos: db_N4
-- =====================================================

-- =====================================================
-- 1. TABLA PRINCIPAL: SCORES CALCULADOS POR CLIENTE
-- =====================================================
CREATE TABLE IF NOT EXISTS score_cliente (
    id SERIAL PRIMARY KEY,
    
    -- Identificación
    cliente_id INT NOT NULL,
    cups VARCHAR(25) NOT NULL,
    periodo_mes VARCHAR(7) NOT NULL, -- YYYY-MM
    tipo_score VARCHAR(20) NOT NULL DEFAULT 'electricidad',
    
    -- Scores por indicador (nueva estructura de pesos)
    score_ic DECIMAL(5,2), -- Índice Consumo (18%)
    score_ip DECIMAL(5,2), -- Índice Potencia (22%)
    score_ief DECIMAL(5,2), -- Índice Eficiencia (20%)
    score_ir DECIMAL(5,2), -- Índice Renovables (16%)
    score_it DECIMAL(5,2), -- Índice Tarifario (10%)
    score_ie DECIMAL(5,2), -- Índice Estacionalidad (9%)
    score_ico DECIMAL(5,2), -- Índice Contratación (5%)
    
    -- Score total
    score_total DECIMAL(5,2) NOT NULL,
    score_total_normalizado DECIMAL(5,2), -- Normalizado por contexto
    
    -- Contexto de normalización
    zona_climatica_cte VARCHAR(10),
    sector_actividad VARCHAR(50),
    tamano_instalacion VARCHAR(20),
    
    -- Metadatos de cálculo
    version_calculo VARCHAR(10) DEFAULT 'v2.0',
    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tiempo_calculo_ms INT,
    
    UNIQUE(cliente_id, cups, periodo_mes, tipo_score)
);

-- =====================================================
-- 2. TABLA: DETALLE DE FACTORES Y SUBFACTORES
-- =====================================================
CREATE TABLE IF NOT EXISTS score_detalle_factores (
    id SERIAL PRIMARY KEY,
    score_cliente_id INT REFERENCES score_cliente(id) ON DELETE CASCADE,
    
    -- Jerarquía
    indicador_id VARCHAR(10) NOT NULL, -- IC, IP, etc.
    factor_id VARCHAR(50) NOT NULL,
    subfactor_id VARCHAR(50),
    
    -- Valores
    valor_original DECIMAL(15,4), -- Valor antes de normalización
    valor_normalizado DECIMAL(15,4), -- Valor después de normalización
    puntos_base DECIMAL(5,2), -- Puntos antes de ponderación
    puntos_ponderados DECIMAL(5,2), -- Puntos después de ponderación
    peso_aplicado DECIMAL(5,2), -- Peso usado en el cálculo
    
    -- Contexto de normalización aplicado
    normalizacion_aplicada JSONB, -- {"tipo": "percentil", "ventana": "12m", "percentil": 75}
    
    -- Fuente de datos
    origen_dato VARCHAR(50), -- 'factura', 'api_pvgis', 'api_catastro', etc.
    calidad_dato DECIMAL(3,2), -- 0-1 calidad del dato
    
    -- Señal
    tipo_senal VARCHAR(20) CHECK (tipo_senal IN ('accionable', 'exogena', 'mixta')),
    controlabilidad DECIMAL(3,2), -- 0-1 qué tanto puede el cliente controlarlo
    
    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 3. TABLA: DATOS DE APIs INTEGRADAS
-- =====================================================
CREATE TABLE IF NOT EXISTS score_datos_apis (
    id SERIAL PRIMARY KEY,
    score_cliente_id INT REFERENCES score_cliente(id) ON DELETE CASCADE,
    
    -- API origen
    api_origen VARCHAR(30) NOT NULL, -- 'nominatim', 'catastro', 'open_meteo', 'pvgis', 'eprel', 'omie', 'ree'
    
    -- Datos obtenidos (almacenamiento flexible)
    datos_json JSONB NOT NULL,
    
    -- Ejemplos de campos extraídos:
    -- Catastro
    superficie_m2 DECIMAL(10,2),
    antiguedad_anio INT,
    uso_suelo VARCHAR(50),
    
    -- Open-Meteo
    hdd_mensual DECIMAL(10,2),
    cdd_mensual DECIMAL(10,2),
    temp_media DECIMAL(5,2),
    
    -- PVGIS
    ghi_anual_kwh_m2 DECIMAL(10,2),
    kwh_kwp_sistema DECIMAL(10,2),
    tilt_optimo INT,
    azimuth_optimo INT,
    
    -- EPREL
    inventario_equipos JSONB, -- {"clase_A": 5, "clase_B": 3, "clase_C": 2}
    eei_medio DECIMAL(5,2),
    
    -- OMIE
    precio_medio_periodo DECIMAL(10,4),
    percentil_precio_p20 DECIMAL(10,4),
    percentil_precio_p80 DECIMAL(10,4),
    
    -- Metadata
    fecha_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    latencia_ms INT,
    estado_calidad VARCHAR(20) -- 'completo', 'parcial', 'fallback'
);

-- =====================================================
-- 4. TABLA: AGREGACIONES POR COHORTE
-- =====================================================
CREATE TABLE IF NOT EXISTS score_cohorte (
    id SERIAL PRIMARY KEY,
    
    -- Definición de cohorte
    tipo_cohorte VARCHAR(50) NOT NULL, -- 'sector', 'tarifa', 'zona_climatica', 'tamano', 'combinada'
    valor_cohorte VARCHAR(100) NOT NULL, -- 'residencial', '2.0TD', 'Csa', 'pequeño', etc.
    filtros_adicionales JSONB, -- {"provincia": "Madrid", "potencia_min": 10}
    
    -- Periodo
    periodo_mes VARCHAR(7) NOT NULL,
    tipo_score VARCHAR(20) NOT NULL DEFAULT 'electricidad',
    
    -- Estadísticas de la cohorte
    num_clientes INT NOT NULL,
    
    -- Scores agregados
    score_total_media DECIMAL(5,2),
    score_total_mediana DECIMAL(5,2),
    score_total_std DECIMAL(5,2),
    score_total_min DECIMAL(5,2),
    score_total_max DECIMAL(5,2),
    score_total_p10 DECIMAL(5,2),
    score_total_p25 DECIMAL(5,2),
    score_total_p75 DECIMAL(5,2),
    score_total_p90 DECIMAL(5,2),
    
    -- Scores por indicador (medias)
    score_ic_media DECIMAL(5,2),
    score_ip_media DECIMAL(5,2),
    score_ief_media DECIMAL(5,2),
    score_ir_media DECIMAL(5,2),
    score_it_media DECIMAL(5,2),
    score_ie_media DECIMAL(5,2),
    score_ico_media DECIMAL(5,2),
    
    -- Metadata
    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tipo_cohorte, valor_cohorte, periodo_mes, tipo_score)
);

-- =====================================================
-- 5. TABLA: RANKINGS Y PERCENTILES
-- =====================================================
CREATE TABLE IF NOT EXISTS score_ranking (
    id SERIAL PRIMARY KEY,
    
    cliente_id INT NOT NULL,
    cups VARCHAR(25) NOT NULL,
    periodo_mes VARCHAR(7) NOT NULL,
    
    -- Rankings absolutos
    ranking_global INT,
    total_clientes_global INT,
    percentil_global DECIMAL(5,2),
    
    -- Rankings por cohorte
    ranking_sector INT,
    total_clientes_sector INT,
    percentil_sector DECIMAL(5,2),
    
    ranking_tarifa INT,
    total_clientes_tarifa INT,
    percentil_tarifa DECIMAL(5,2),
    
    ranking_zona_climatica INT,
    total_clientes_zona INT,
    percentil_zona DECIMAL(5,2),
    
    ranking_tamano INT,
    total_clientes_tamano INT,
    percentil_tamano DECIMAL(5,2),
    
    -- Comparación con benchmarks
    vs_media_global DECIMAL(5,2), -- Diferencia % vs media
    vs_media_sector DECIMAL(5,2),
    vs_top_10_pct DECIMAL(5,2), -- Diferencia vs top 10%
    
    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(cliente_id, cups, periodo_mes)
);

-- =====================================================
-- 6. TABLA: CONTEXTO PARA LLM
-- =====================================================
CREATE TABLE IF NOT EXISTS score_contexto_llm (
    id SERIAL PRIMARY KEY,
    
    cliente_id INT NOT NULL,
    cups VARCHAR(25) NOT NULL,
    periodo_mes VARCHAR(7) NOT NULL,
    
    -- Resumen ejecutivo (pre-calculado para LLM)
    resumen_ejecutivo TEXT,
    
    -- Principales insights
    fortalezas JSONB, -- [{"indicador": "IP", "mensaje": "Excelente gestión de potencia", "score": 95}]
    debilidades JSONB, -- [{"indicador": "IR", "mensaje": "Sin renovables", "score": 45}]
    oportunidades JSONB, -- [{"accion": "Instalar FV", "impacto_estimado": "+15 puntos", "roi": "4 años"}]
    
    -- Comparativas relevantes
    comparativa_sector TEXT,
    comparativa_historica TEXT,
    tendencia_ultimos_12m TEXT,
    
    -- Recomendaciones priorizadas
    recomendaciones JSONB, -- [{"prioridad": 1, "accion": "...", "impacto": "...", "dificultad": "baja"}]
    
    -- Datos clave para contexto
    datos_clave JSONB, -- {"consumo_anual": 50000, "potencia": 15, "tarifa": "3.0TD", ...}
    
    -- Metadata
    version_modelo VARCHAR(20) DEFAULT 'v2.0',
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tokens_utilizados INT
);

-- =====================================================
-- 7. TABLA: EVOLUCIÓN TEMPORAL (SERIES)
-- =====================================================
CREATE TABLE IF NOT EXISTS score_evolucion (
    id SERIAL PRIMARY KEY,
    
    cliente_id INT NOT NULL,
    cups VARCHAR(25) NOT NULL,
    
    -- Series temporales (arrays ordenados por mes)
    periodos_array VARCHAR(7)[], -- ['2024-01', '2024-02', ...]
    score_total_array DECIMAL(5,2)[],
    score_ic_array DECIMAL(5,2)[],
    score_ip_array DECIMAL(5,2)[],
    score_ief_array DECIMAL(5,2)[],
    score_ir_array DECIMAL(5,2)[],
    score_it_array DECIMAL(5,2)[],
    score_ie_array DECIMAL(5,2)[],
    score_ico_array DECIMAL(5,2)[],
    
    -- Tendencias calculadas
    tendencia_12m VARCHAR(20), -- 'mejorando', 'estable', 'empeorando'
    pendiente_regresion DECIMAL(5,2), -- Pendiente de la línea de tendencia
    r2_tendencia DECIMAL(3,2), -- R² del ajuste
    volatilidad_score DECIMAL(5,2), -- Desviación estándar
    
    -- Cambios significativos
    max_mejora_mes VARCHAR(7),
    max_mejora_puntos DECIMAL(5,2),
    max_caida_mes VARCHAR(7),
    max_caida_puntos DECIMAL(5,2),
    
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(cliente_id, cups)
);

-- =====================================================
-- ÍNDICES OPTIMIZADOS
-- =====================================================

-- Índices para búsquedas frecuentes
CREATE INDEX idx_score_cliente_cups ON score_cliente(cups);
CREATE INDEX idx_score_cliente_periodo ON score_cliente(periodo_mes);
CREATE INDEX idx_score_cliente_total ON score_cliente(score_total DESC);
CREATE INDEX idx_score_cliente_cliente_periodo ON score_cliente(cliente_id, periodo_mes);

-- Índices para agregaciones
CREATE INDEX idx_score_cohorte_tipo ON score_cohorte(tipo_cohorte, valor_cohorte);
CREATE INDEX idx_score_cohorte_periodo ON score_cohorte(periodo_mes);

-- Índices para rankings
CREATE INDEX idx_score_ranking_percentiles ON score_ranking(percentil_global, percentil_sector);

-- Índices para contexto LLM
CREATE INDEX idx_score_contexto_llm_cliente ON score_contexto_llm(cliente_id, periodo_mes);

-- Índices para evolución
CREATE INDEX idx_score_evolucion_cliente ON score_evolucion(cliente_id);
CREATE INDEX idx_score_evolucion_tendencia ON score_evolucion(tendencia_12m);

-- =====================================================
-- COMENTARIOS DE TABLAS
-- =====================================================

COMMENT ON TABLE score_cliente IS 'Scores principales calculados por cliente y periodo';
COMMENT ON TABLE score_detalle_factores IS 'Detalle de factores y subfactores con normalización';
COMMENT ON TABLE score_datos_apis IS 'Datos obtenidos de APIs externas para el cálculo';
COMMENT ON TABLE score_cohorte IS 'Agregaciones de scores por grupos comparables';
COMMENT ON TABLE score_ranking IS 'Rankings y percentiles por diferentes dimensiones';
COMMENT ON TABLE score_contexto_llm IS 'Datos pre-procesados para contexto de LLM';
COMMENT ON TABLE score_evolucion IS 'Series temporales y tendencias de scores';
