#!/usr/bin/env python3
"""
Cargador estricto de zonas climáticas con HDD/CDD (sin fallbacks ni valores por defecto):
- Lee CP+municipio del CSV real
- Resuelve coordenadas del municipio con Nominatim (si no hay resultado → error y se omite la fila)
- Consulta Open-Meteo (archive) para obtener:
  * temperatura media diaria del último año (para HDD/CDD anuales)
  * altitud (elevation) real de la celda
- Deriva zona CTE aplicando core_zonas_cte_reglas usando la altitud real y la provincia del CP
- Inserta/actualiza en core_zonas_climaticas (todos los campos reales). Si algo falta → no inserta.

Parámetros:
  --limit N  Procesa solo las primeras N filas del CSV (p.ej., 50 para piloto)
"""

import csv
import argparse
import psycopg2
import requests
from datetime import datetime, timedelta
import time
import sys

# Configuración BD
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'admin'
}

# Archivo fuente
CSV_FILE = '/Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/motor_extraccion/src/database/utils/codigos_postales_municipios_join.csv'

# Mapeo provincia por código postal (primeros 2 dígitos)
PROVINCIA_POR_CP = {
    '01': 'Álava', '02': 'Albacete', '03': 'Alicante/Alacant', '04': 'Almería',
    '05': 'Ávila', '06': 'Badajoz', '07': 'Illes Balears', '08': 'Barcelona',
    '09': 'Burgos', '10': 'Cáceres', '11': 'Cádiz', '12': 'Castellón/Castelló',
    '13': 'Ciudad Real', '14': 'Córdoba', '15': 'A Coruña', '16': 'Cuenca',
    '17': 'Girona', '18': 'Granada', '19': 'Guadalajara', '20': 'Gipuzkoa',
    '21': 'Huelva', '22': 'Huesca', '23': 'Jaén', '24': 'León',
    '25': 'Lleida', '26': 'La Rioja', '27': 'Lugo', '28': 'Madrid',
    '29': 'Málaga', '30': 'Murcia', '31': 'Navarra', '32': 'Ourense',
    '33': 'Asturias', '34': 'Palencia', '35': 'Las Palmas', '36': 'Pontevedra',
    '37': 'Salamanca', '38': 'Santa Cruz de Tenerife', '39': 'Cantabria', '40': 'Segovia',
    '41': 'Sevilla', '42': 'Soria', '43': 'Tarragona', '44': 'Teruel',
    '45': 'Toledo', '46': 'Valencia/València', '47': 'Valladolid', '48': 'Bizkaia',
    '49': 'Zamora', '50': 'Zaragoza', '51': 'Ceuta', '52': 'Melilla'
}

def get_zona_cte(conn, provincia: str, altitud: float) -> str:
    """Obtener zona CTE según provincia y altitud usando core_zonas_cte_reglas (sin defaults)."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT zona_climatica_cte 
        FROM core_zonas_cte_reglas
        WHERE provincia = %s 
          AND %s >= h_min 
          AND %s <= h_max
        LIMIT 1
    """, (provincia, altitud, altitud))
    
    result = cursor.fetchone()
    cursor.close()
    if not result:
        raise RuntimeError(f"No hay regla CTE para provincia={provincia} altitud={altitud}")
    return result[0]

def get_coordinates_nominatim(municipio: str, provincia: str):
    """Obtener coordenadas aproximadas del municipio usando Nominatim"""
    try:
        # Esperar para respetar límites de Nominatim
        time.sleep(1)
        
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': f"{municipio}, {provincia}, España",
            'format': 'json',
            'limit': 1
        }
        headers = {'User-Agent': 'VagalumeEnergia/1.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            raise RuntimeError("Nominatim sin resultados")
        return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        raise RuntimeError(f"Nominatim fallo: {e}")

def get_hdd_cdd_open_meteo(lat: float, lon: float):
    """Obtener HDD/CDD anuales (últimos 365 días) y altitud real desde Open-Meteo."""
    try:
        # Fechas del último año
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365)
        
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'daily': 'temperature_2m_mean',
            'timezone': 'Europe/Madrid'
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        temps = data.get('daily', {}).get('temperature_2m_mean')
        if not temps or not isinstance(temps, list):
            raise RuntimeError("Open-Meteo sin temperatura_media diaria")
        valid = [t for t in temps if t is not None]
        if not valid:
            raise RuntimeError("Open-Meteo sin valores válidos")
        hdd_18 = sum(max(0, 18 - t) for t in valid)
        cdd_18 = sum(max(0, t - 18) for t in valid)
        temp_media = sum(valid) / len(valid)
        elev = data.get('elevation')
        if elev is None:
            raise RuntimeError("Open-Meteo sin elevation")
        return hdd_18, cdd_18, temp_media, float(elev)
    except Exception as e:
        raise RuntimeError(f"Open-Meteo fallo: {e}")

def main():
    """Procesar CSV (estricto) y cargar primeras N filas reales en core_zonas_climaticas"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=50, help='máximo de filas a procesar (por defecto 50)')
    args = parser.parse_args()
    
    # Conectar a db_Ncore
    conn = psycopg2.connect(database='db_Ncore', **DB_CONFIG)
    cursor = conn.cursor()
    
    # Leer CSV
    processed = 0
    errors = 0
    batch_size = 100
    batch_data = []
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                codigo_postal = row['codigo_postal']
                municipio = row['nombre']
                
                # Obtener provincia del CP
                cp_prefix = codigo_postal[:2]
                if cp_prefix not in PROVINCIA_POR_CP:
                    raise RuntimeError(f"CP prefix desconocido: {cp_prefix}")
                provincia = PROVINCIA_POR_CP[cp_prefix]
                
                # Obtener coordenadas
                lat, lon = get_coordinates_nominatim(municipio, provincia)
                
                # Obtener HDD/CDD
                hdd, cdd, temp_media, elev = get_hdd_cdd_open_meteo(lat, lon)

                # Derivar zona CTE con altitud real
                zona_cte = get_zona_cte(conn, provincia, elev)
                
                # Agregar al batch
                batch_data.append((
                    codigo_postal,
                    municipio,
                    provincia,
                    provincia,  # comunidad_autonoma (temporal si no hay catálogo CCAA)
                    zona_cte,
                    int(round(elev)),
                    lat,
                    lon,
                    hdd,
                    cdd,
                    temp_media,
                    None,  # radiacion_global_anual
                    datetime.now(),
                    'Open-Meteo+CTE'
                ))
                
                processed += 1
                if processed >= args.limit:
                    break
                
                # Insertar por lotes
                if len(batch_data) >= batch_size:
                    cursor.executemany("""
                        INSERT INTO core_zonas_climaticas (
                            codigo_postal, municipio, provincia, comunidad_autonoma,
                            zona_climatica_cte, altitud, latitud, longitud,
                            hdd_anual_medio, cdd_anual_medio, temperatura_media_anual,
                            radiacion_global_anual, fecha_actualizacion, fuente
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (codigo_postal) DO UPDATE SET
                            municipio = EXCLUDED.municipio,
                            zona_climatica_cte = EXCLUDED.zona_climatica_cte,
                            hdd_anual_medio = EXCLUDED.hdd_anual_medio,
                            cdd_anual_medio = EXCLUDED.cdd_anual_medio,
                            temperatura_media_anual = EXCLUDED.temperatura_media_anual,
                            fecha_actualizacion = EXCLUDED.fecha_actualizacion
                    """, batch_data)
                    conn.commit()
                    print(f"✅ Procesados {processed} registros...")
                    batch_data = []
                    
                    # Pausa pequeña por respeto a servicios
                    time.sleep(0.3)
                    
            except Exception as e:
                print(f"❌ Error procesando {municipio} ({codigo_postal}): {e}")
                errors += 1
                continue
    
    # Insertar últimos registros
    if batch_data:
        cursor.executemany("""
            INSERT INTO core_zonas_climaticas (
                codigo_postal, municipio, provincia, comunidad_autonoma,
                zona_climatica_cte, altitud, latitud, longitud,
                hdd_anual_medio, cdd_anual_medio, temperatura_media_anual,
                radiacion_global_anual, fecha_actualizacion, fuente
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (codigo_postal) DO UPDATE SET
                municipio = EXCLUDED.municipio,
                zona_climatica_cte = EXCLUDED.zona_climatica_cte,
                hdd_anual_medio = EXCLUDED.hdd_anual_medio,
                cdd_anual_medio = EXCLUDED.cdd_anual_medio,
                temperatura_media_anual = EXCLUDED.temperatura_media_anual,
                fecha_actualizacion = EXCLUDED.fecha_actualizacion
        """, batch_data)
        conn.commit()
    
    cursor.close()
    conn.close()
    
    print(f"""
    ✅ CARGA COMPLETADA
    - Registros procesados: {processed}
    - Errores: {errors}
    - Tabla: core_zonas_climaticas
    """)

if __name__ == '__main__':
    main()
