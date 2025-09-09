-- Tabla de vehículos España con datos IDAE
-- Fuente: https://coches.idae.es/storage/csv/idae-historico-202413.csv
-- Creado: 2025-09-09

CREATE TABLE IF NOT EXISTS core_vehiculos_espana (
    id SERIAL PRIMARY KEY,
    
    -- Metadatos temporales
    fecha_alta DATE,
    fecha_actualizacion DATE,
    fecha_comercializacion DATE,
    
    -- Identificación vehículo
    marca VARCHAR(100) NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    vehiculo TEXT NOT NULL, -- Descripción completa
    segmento VARCHAR(100),
    motorizacion VARCHAR(100) NOT NULL,
    categoria VARCHAR(10), -- M1, N1, N3, L6e, etc.
    mtma INTEGER, -- Masa Técnica Máxima Autorizada (kg)
    
    -- Consumos y emisiones NEDC (ciclo antiguo)
    consumo_nedc DECIMAL(5,2), -- L/100km
    emisiones_nedc DECIMAL(6,2), -- g CO2/km
    
    -- Consumos WLTP (ciclo actual)
    consumo_mixto_wltp_min DECIMAL(5,2), -- L/100km
    consumo_mixto_wltp_max DECIMAL(5,2), -- L/100km
    consumo_mixto_wltp DECIMAL(5,2), -- L/100km (valor medio)
    
    -- Emisiones CO2 WLTP
    emisiones_co2_mixto_wltp_min DECIMAL(6,2), -- g CO2/km
    emisiones_co2_mixto_wltp_max DECIMAL(6,2), -- g CO2/km
    
    -- Datos eléctricos
    autonomia_electrica INTEGER, -- km (0 si no es eléctrico)
    consumo_electrico DECIMAL(5,2), -- kWh/100km
    
    -- Observaciones
    observaciones TEXT,
    
    -- Columnas derivadas para scoring movilidad
    eficiencia_energetica VARCHAR(1), -- A, B, C, D, E, F, G (calculado)
    score_emisiones INTEGER, -- 0-100 (0=peor, 100=mejor)
    score_consumo INTEGER, -- 0-100 (0=peor, 100=mejor)
    score_autonomia INTEGER, -- 0-100 (0=peor, 100=mejor)
    score_movilidad_total INTEGER, -- 0-100 (promedio ponderado)
    
    -- Clasificaciones derivadas
    tipo_propulsion VARCHAR(20), -- COMBUSTION, HIBRIDO, ELECTRICO, HIBRIDO_ENCHUFABLE
    categoria_eficiencia VARCHAR(20), -- ALTA, MEDIA, BAJA
    segmento_normalizado VARCHAR(50), -- Segmento limpio y normalizado
    
    -- Métricas calculadas
    ratio_potencia_peso DECIMAL(8,4), -- kW/kg (si disponible)
    emisiones_por_litro DECIMAL(8,2), -- g CO2/L combustible
    coste_100km_estimado DECIMAL(8,2), -- EUR/100km (estimado)
    
    -- Metadatos
    fecha_insercion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion_score TIMESTAMP,
    
    -- Índices para búsquedas
    UNIQUE(marca, modelo, vehiculo, motorizacion)
);

-- Índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_vehiculos_marca_modelo ON core_vehiculos_espana(marca, modelo);
CREATE INDEX IF NOT EXISTS idx_vehiculos_motorizacion ON core_vehiculos_espana(motorizacion);
CREATE INDEX IF NOT EXISTS idx_vehiculos_segmento ON core_vehiculos_espana(segmento);
CREATE INDEX IF NOT EXISTS idx_vehiculos_emisiones ON core_vehiculos_espana(emisiones_co2_mixto_wltp_min, emisiones_co2_mixto_wltp_max);
CREATE INDEX IF NOT EXISTS idx_vehiculos_consumo ON core_vehiculos_espana(consumo_mixto_wltp);
CREATE INDEX IF NOT EXISTS idx_vehiculos_score ON core_vehiculos_espana(score_movilidad_total);
CREATE INDEX IF NOT EXISTS idx_vehiculos_tipo_propulsion ON core_vehiculos_espana(tipo_propulsion);

-- Comentarios de tabla
COMMENT ON TABLE core_vehiculos_espana IS 'Registro completo de vehículos comercializados en España con datos oficiales IDAE, consumos, emisiones y scoring de movilidad';
COMMENT ON COLUMN core_vehiculos_espana.score_movilidad_total IS 'Score 0-100 calculado: 40% emisiones + 30% consumo + 20% autonomía + 10% eficiencia';
COMMENT ON COLUMN core_vehiculos_espana.tipo_propulsion IS 'Clasificación: COMBUSTION, HIBRIDO, ELECTRICO, HIBRIDO_ENCHUFABLE basada en motorizacion';
COMMENT ON COLUMN core_vehiculos_espana.eficiencia_energetica IS 'Etiqueta A-G calculada según emisiones CO2 (A<50, B<75, C<100, D<120, E<140, F<160, G>=160)';
