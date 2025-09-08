-- Crear tablas REE (raw + normalizado) y PVGIS en db_Ncore

-- RAW REE mix
CREATE TABLE IF NOT EXISTS core_ree_mix_json (
  fecha DATE PRIMARY KEY,
  payload JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RAW REE CO2
CREATE TABLE IF NOT EXISTS core_ree_co2_json (
  fecha DATE PRIMARY KEY,
  payload JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Normalizado REE mix horario
CREATE TABLE IF NOT EXISTS core_ree_mix_horario (
  fecha_hora TIMESTAMP NOT NULL,
  tecnologia VARCHAR(64) NOT NULL,
  mwh NUMERIC(12,3),
  porcentaje NUMERIC(6,3),
  fuente VARCHAR(20) DEFAULT 'REE',
  fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (fecha_hora, tecnologia)
);
CREATE INDEX IF NOT EXISTS idx_ree_mix_fecha ON core_ree_mix_horario (fecha_hora);
CREATE INDEX IF NOT EXISTS idx_ree_mix_tec ON core_ree_mix_horario (tecnologia);

-- Normalizado REE emisiones horario
CREATE TABLE IF NOT EXISTS core_ree_emisiones_horario (
  fecha_hora TIMESTAMP PRIMARY KEY,
  gco2_kwh NUMERIC(8,3),
  fuente VARCHAR(20) DEFAULT 'REE',
  fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ree_emisiones_fecha ON core_ree_emisiones_horario (fecha_hora);

-- PVGIS radiación mensual (kWh/m²)
CREATE TABLE IF NOT EXISTS core_pvgis_radiacion (
  latitud NUMERIC(10,8) NOT NULL,
  longitud NUMERIC(11,8) NOT NULL,
  mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
  kwh_m2 NUMERIC(10,3),
  fuente VARCHAR(20) DEFAULT 'PVGIS',
  fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (latitud, longitud, mes)
);
CREATE INDEX IF NOT EXISTS idx_pvgis_coords ON core_pvgis_radiacion (latitud, longitud);

-- RAW PVGIS (por coordenadas)
CREATE TABLE IF NOT EXISTS core_pvgis_raw (
  latitud NUMERIC(10,8) NOT NULL,
  longitud NUMERIC(11,8) NOT NULL,
  payload JSONB NOT NULL,
  fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (latitud, longitud)
);
