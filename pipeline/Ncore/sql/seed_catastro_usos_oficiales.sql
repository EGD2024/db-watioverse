-- Seed de usos oficiales del Catastro español para db_Ncore
-- Fuente: Dirección General del Catastro - Normativa técnica de valoración

-- Limpiar y poblar diccionario de usos
TRUNCATE TABLE public.core_catastro_dic_uso CASCADE;

INSERT INTO public.core_catastro_dic_uso (uso_principal, descripcion, fuente, fecha_actualizacion) VALUES
-- RESIDENCIAL
('Residencial', 'Uso residencial genérico', 'DGC', NOW()),
('Vivienda colectiva de carácter urbano', 'Edificios de viviendas en régimen colectivo', 'DGC', NOW()),
('Vivienda unifamiliar de carácter urbano', 'Vivienda unifamiliar aislada, pareada o adosada', 'DGC', NOW()),
('Edificación rural de uso residencial', 'Vivienda en entorno rural', 'DGC', NOW()),

-- INDUSTRIAL
('Industrial', 'Uso industrial genérico', 'DGC', NOW()),
('Industrial. Fabricación', 'Instalaciones de producción y fabricación', 'DGC', NOW()),
('Industrial. Almacenamiento', 'Naves y almacenes industriales', 'DGC', NOW()),
('Industrial. Garaje', 'Garajes y aparcamientos', 'DGC', NOW()),

-- OFICINAS
('Oficinas', 'Oficinas genéricas', 'DGC', NOW()),
('Oficinas múltiples', 'Edificios de oficinas', 'DGC', NOW()),
('Oficinas unitarias', 'Oficina individual', 'DGC', NOW()),
('Banca y seguros', 'Entidades financieras', 'DGC', NOW()),

-- COMERCIAL
('Comercial', 'Uso comercial genérico', 'DGC', NOW()),
('Comercial en edificio mixto', 'Local comercial en edificio residencial', 'DGC', NOW()),
('Comercial en edificio exclusivo', 'Centro comercial o edificio comercial', 'DGC', NOW()),
('Mercados y supermercados', 'Comercio alimentación', 'DGC', NOW()),

-- DEPORTIVO
('Deportivo', 'Instalaciones deportivas', 'DGC', NOW()),
('Deportivo cubierto', 'Pabellones y polideportivos cubiertos', 'DGC', NOW()),
('Deportivo descubierto', 'Campos deportivos al aire libre', 'DGC', NOW()),
('Piscinas', 'Piscinas públicas y privadas', 'DGC', NOW()),

-- ESPECTÁCULOS
('Espectáculos', 'Locales de espectáculos', 'DGC', NOW()),
('Espectáculos cubierto', 'Teatros, cines, auditorios', 'DGC', NOW()),
('Espectáculos al aire libre', 'Anfiteatros, plazas de toros', 'DGC', NOW()),

-- OCIO Y HOSTELERÍA
('Ocio y hostelería', 'Establecimientos de ocio y hostelería', 'DGC', NOW()),
('Ocio y hostelería con residencia', 'Hoteles, hostales, residencias', 'DGC', NOW()),
('Ocio y hostelería sin residencia', 'Bares, restaurantes, cafeterías', 'DGC', NOW()),
('Casinos, salas de juego', 'Establecimientos de juego', 'DGC', NOW()),
('Exposiciones y congresos', 'Palacios de congresos y exposiciones', 'DGC', NOW()),

-- SANITARIO
('Sanidad y beneficencia', 'Uso sanitario y asistencial', 'DGC', NOW()),
('Sanidad con internamiento', 'Hospitales y clínicas con camas', 'DGC', NOW()),
('Sanidad sin internamiento', 'Centros de salud, ambulatorios', 'DGC', NOW()),
('Beneficencia con internamiento', 'Residencias de mayores', 'DGC', NOW()),
('Beneficencia sin internamiento', 'Centros de día', 'DGC', NOW()),

-- CULTURAL
('Cultural', 'Equipamientos culturales', 'DGC', NOW()),
('Cultural con espectáculos', 'Auditorios culturales', 'DGC', NOW()),
('Cultural sin espectáculos', 'Museos, bibliotecas', 'DGC', NOW()),

-- RELIGIOSO
('Religioso', 'Edificios de culto', 'DGC', NOW()),
('Religioso de una religión', 'Templo de culto específico', 'DGC', NOW()),
('Religioso de varias religiones', 'Centro ecuménico', 'DGC', NOW()),

-- EDIFICIOS SINGULARES
('Edificio singular', 'Edificio de características especiales', 'DGC', NOW()),
('Monumental', 'Edificio con protección patrimonial', 'DGC', NOW()),
('Histórico artístico', 'Edificio de valor histórico-artístico', 'DGC', NOW()),

-- ENSEÑANZA
('Enseñanza', 'Centros educativos', 'DGC', NOW()),
('Enseñanza sin residencia', 'Colegios, institutos, universidades', 'DGC', NOW()),
('Enseñanza con residencia', 'Colegios mayores, internados', 'DGC', NOW()),

-- AGRARIO
('Agrario', 'Construcciones agrarias', 'DGC', NOW()),
('Agrícola', 'Almacenes y naves agrícolas', 'DGC', NOW()),
('Ganadería y pesca', 'Instalaciones ganaderas y piscifactorías', 'DGC', NOW()),
('Forestal', 'Instalaciones forestales', 'DGC', NOW()),

-- OBRAS DE URBANIZACIÓN
('Obras de urbanización y jardineria, suelos sin edificar', 'Suelos sin edificar', 'DGC', NOW()),
('Suelo sin edificar', 'Parcelas sin construcción', 'DGC', NOW()),
('Obras de urbanización', 'Urbanización en proceso', 'DGC', NOW()),
('Jardinería', 'Zonas ajardinadas', 'DGC', NOW()),

-- INFRAESTRUCTURAS
('Servicios de transporte', 'Estaciones y terminales', 'DGC', NOW()),
('Estaciones de transporte', 'Estaciones tren, autobús, metro', 'DGC', NOW()),
('Servicios de carreteras', 'Áreas de servicio', 'DGC', NOW()),
('Puertos y aeropuertos', 'Instalaciones portuarias y aeroportuarias', 'DGC', NOW()),

-- SERVICIOS PÚBLICOS
('Servicios públicos', 'Equipamientos públicos', 'DGC', NOW()),
('Administrativo público', 'Edificios administrativos públicos', 'DGC', NOW()),
('Servicios de seguridad', 'Comisarías, cuarteles, bomberos', 'DGC', NOW()),
('Cementerios', 'Cementerios y tanatorios', 'DGC', NOW()),

-- ALMACÉN-ESTACIONAMIENTO
('Almacén-Estacionamiento', 'Almacenes y garajes', 'DGC', NOW()),
('Almacén', 'Almacén o trastero', 'DGC', NOW()),
('Estacionamiento', 'Plaza de garaje', 'DGC', NOW());
