-- =====================================================
-- LIMPIEZA COMPLETA DE db_clima
-- Eliminar las 87 tablas actuales
-- EJECUTAR ESTE SCRIPT CONECTADO A db_clima
-- =====================================================

-- Generar comando para eliminar TODAS las tablas de manera segura
DO $$ 
DECLARE 
    r RECORD;
BEGIN
    -- Recorrer todas las tablas del esquema public
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') 
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
        RAISE NOTICE 'Tabla eliminada: %', r.tablename;
    END LOOP;
END $$;

-- Verificar que no quedan tablas
SELECT COUNT(*) as tablas_restantes FROM information_schema.tables WHERE table_schema = 'public';

-- =====================================================
-- CREAR NUEVA ESTRUCTURA SIMPLIFICADA (OPCIONAL)
-- Solo 3-5 tablas esenciales para clima
-- =====================================================

-- TABLA 1: Estaciones meteorológicas
CREATE TABLE weather_stations (
    id SERIAL PRIMARY KEY,
    station_code VARCHAR(20) UNIQUE NOT NULL,
    station_name VARCHAR(100) NOT NULL,
    provincia VARCHAR(100),
    latitude DECIMAL(10,6),
    longitude DECIMAL(10,6),
    altitude INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 2: Datos históricos
CREATE TABLE weather_historical (
    id SERIAL PRIMARY KEY,
    station_id INTEGER REFERENCES weather_stations(id),
    fecha DATE NOT NULL,
    temperatura_media DECIMAL(5,2),
    temperatura_max DECIMAL(5,2),
    temperatura_min DECIMAL(5,2),
    humedad_relativa DECIMAL(5,2),
    precipitacion DECIMAL(10,2),
    viento_velocidad DECIMAL(5,2),
    viento_direccion INTEGER,
    presion_atmosferica DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(station_id, fecha)
);

-- TABLA 3: Predicciones meteorológicas
CREATE TABLE weather_forecast (
    id SERIAL PRIMARY KEY,
    station_id INTEGER REFERENCES weather_stations(id),
    fecha_prediccion DATE NOT NULL,
    fecha_generacion TIMESTAMP NOT NULL,
    temperatura_media DECIMAL(5,2),
    temperatura_max DECIMAL(5,2),
    temperatura_min DECIMAL(5,2),
    probabilidad_lluvia DECIMAL(5,2),
    estado_cielo VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA 4: Cache de consultas por código postal
CREATE TABLE weather_cache (
    id SERIAL PRIMARY KEY,
    codigo_postal VARCHAR(10) NOT NULL,
    fecha DATE NOT NULL,
    datos_clima JSONB NOT NULL,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(codigo_postal, fecha)
);

-- Índices para optimización
CREATE INDEX idx_weather_historical_fecha ON weather_historical(fecha);
CREATE INDEX idx_weather_historical_station ON weather_historical(station_id);
CREATE INDEX idx_weather_forecast_fecha ON weather_forecast(fecha_prediccion);
CREATE INDEX idx_weather_cache_cp ON weather_cache(codigo_postal);
CREATE INDEX idx_weather_cache_expires ON weather_cache(expires_at);

-- Verificación final
SELECT 'db_clima reestructurada' as status, COUNT(*) as total_tablas 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- =====================================================
-- RESULTADO ESPERADO:
-- De 87 tablas a 4 tablas optimizadas
-- =====================================================
