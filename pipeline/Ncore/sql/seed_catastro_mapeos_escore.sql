-- Mapeo de usos oficiales Catastro → categorías eSCORE
-- Se ejecuta DESPUÉS de seed_catastro_usos_oficiales.sql

TRUNCATE TABLE public.core_catastro_map_uso_escore;

INSERT INTO public.core_catastro_map_uso_escore (uso_principal, categoria_escore, fecha_actualizacion) VALUES
-- RESIDENCIAL → vivienda_*
('Residencial', 'vivienda_plurifamiliar', NOW()),
('Vivienda colectiva de carácter urbano', 'vivienda_plurifamiliar', NOW()),
('Vivienda unifamiliar de carácter urbano', 'vivienda_unifamiliar', NOW()),
('Edificación rural de uso residencial', 'vivienda_unifamiliar', NOW()),

-- INDUSTRIAL → industrial/almacen/garaje
('Industrial', 'industrial', NOW()),
('Industrial. Fabricación', 'industrial', NOW()),
('Industrial. Almacenamiento', 'almacen', NOW()),
('Industrial. Garaje', 'garaje', NOW()),

-- OFICINAS → oficinas
('Oficinas', 'oficinas', NOW()),
('Oficinas múltiples', 'oficinas', NOW()),
('Oficinas unitarias', 'oficinas', NOW()),
('Banca y seguros', 'oficinas', NOW()),

-- COMERCIAL → comercial
('Comercial', 'comercial', NOW()),
('Comercial en edificio mixto', 'comercial', NOW()),
('Comercial en edificio exclusivo', 'comercial', NOW()),
('Mercados y supermercados', 'comercial', NOW()),

-- DEPORTIVO → deportivo
('Deportivo', 'deportivo', NOW()),
('Deportivo cubierto', 'deportivo', NOW()),
('Deportivo descubierto', 'deportivo', NOW()),
('Piscinas', 'deportivo', NOW()),

-- ESPECTÁCULOS → ocio_cultural
('Espectáculos', 'ocio_cultural', NOW()),
('Espectáculos cubierto', 'ocio_cultural', NOW()),
('Espectáculos al aire libre', 'ocio_cultural', NOW()),

-- OCIO Y HOSTELERÍA → hotelero/comercial
('Ocio y hostelería', 'hotelero', NOW()),
('Ocio y hostelería con residencia', 'hotelero', NOW()),
('Ocio y hostelería sin residencia', 'comercial', NOW()),
('Casinos, salas de juego', 'ocio_cultural', NOW()),
('Exposiciones y congresos', 'ocio_cultural', NOW()),

-- SANITARIO → sanitario
('Sanidad y beneficencia', 'sanitario', NOW()),
('Sanidad con internamiento', 'sanitario', NOW()),
('Sanidad sin internamiento', 'sanitario', NOW()),
('Beneficencia con internamiento', 'sanitario', NOW()),
('Beneficencia sin internamiento', 'sanitario', NOW()),

-- CULTURAL → ocio_cultural
('Cultural', 'ocio_cultural', NOW()),
('Cultural con espectáculos', 'ocio_cultural', NOW()),
('Cultural sin espectáculos', 'ocio_cultural', NOW()),

-- RELIGIOSO → equipamiento
('Religioso', 'equipamiento', NOW()),
('Religioso de una religión', 'equipamiento', NOW()),
('Religioso de varias religiones', 'equipamiento', NOW()),

-- EDIFICIOS SINGULARES → equipamiento
('Edificio singular', 'equipamiento', NOW()),
('Monumental', 'equipamiento', NOW()),
('Histórico artístico', 'equipamiento', NOW()),

-- ENSEÑANZA → educativo
('Enseñanza', 'educativo', NOW()),
('Enseñanza sin residencia', 'educativo', NOW()),
('Enseñanza con residencia', 'educativo', NOW()),

-- AGRARIO → agropecuario
('Agrario', 'agropecuario', NOW()),
('Agrícola', 'agropecuario', NOW()),
('Ganadería y pesca', 'agropecuario', NOW()),
('Forestal', 'agropecuario', NOW()),

-- SUELOS SIN EDIFICAR → suelo_sin_edificar
('Obras de urbanización y jardineria, suelos sin edificar', 'suelo_sin_edificar', NOW()),
('Suelo sin edificar', 'suelo_sin_edificar', NOW()),
('Obras de urbanización', 'suelo_sin_edificar', NOW()),
('Jardinería', 'suelo_sin_edificar', NOW()),

-- INFRAESTRUCTURAS → equipamiento
('Servicios de transporte', 'equipamiento', NOW()),
('Estaciones de transporte', 'equipamiento', NOW()),
('Servicios de carreteras', 'equipamiento', NOW()),
('Puertos y aeropuertos', 'equipamiento', NOW()),

-- SERVICIOS PÚBLICOS → equipamiento
('Servicios públicos', 'equipamiento', NOW()),
('Administrativo público', 'equipamiento', NOW()),
('Servicios de seguridad', 'equipamiento', NOW()),
('Cementerios', 'equipamiento', NOW()),

-- ALMACÉN-ESTACIONAMIENTO → almacen/garaje/trastero
('Almacén-Estacionamiento', 'almacen', NOW()),
('Almacén', 'trastero', NOW()),
('Estacionamiento', 'garaje', NOW());
