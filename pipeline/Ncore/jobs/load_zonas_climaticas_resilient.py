#!/usr/bin/env python3
"""
Cargador resiliente de zonas climáticas con HDD/CDD:
- Maneja rate limiting de APIs con delays adaptativos
- Reintentos automáticos con backoff exponencial
- Continúa desde donde se quedó (resume desde último procesado)
- Geocodificación con fallbacks múltiples
- Logs detallados de progreso y errores
"""

import csv
import argparse
import psycopg2
import requests
from datetime import datetime, timedelta
import time
import sys
import json
import random
from typing import Optional, Tuple

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
    """Obtener zona CTE según provincia y altitud usando core_zonas_cte_reglas."""
    cursor = conn.cursor()
    
    # Mapeo de nombres de provincia para casos especiales
    provincia_normalizada = provincia
    if provincia in ["A Coruña", "La Coruña", "Coruña"]:
        provincia_normalizada = "Coruña, A"
    elif provincia in ["Alicante", "Alacant", "Alicante/Alacant"]:
        provincia_normalizada = "Alicante/Alacant"
    elif provincia in ["Castellón", "Castelló", "Castellón/Castelló"]:
        provincia_normalizada = "Castellón/Castelló"
    elif provincia in ["Valencia", "València", "Valencia/València"]:
        provincia_normalizada = "Valencia/València"
    elif provincia in ["Lleida", "Lérida"]:
        provincia_normalizada = "Lleida"
    elif provincia in ["Álava", "Alava", "Araba", "Araba/Álava"]:
        provincia_normalizada = "Araba/Álava"
    elif provincia in ["Vizcaya", "Bizkaia", "Viscaya"]:
        provincia_normalizada = "Bizkaia"
    elif provincia in ["Guipúzcoa", "Gipuzkoa", "Guipuzcoa"]:
        provincia_normalizada = "Gipuzkoa"
    elif provincia in ["Baleares", "Islas Baleares", "Illes Balears"]:
        provincia_normalizada = "Illes Balears"
    elif provincia in ["Las Palmas", "Palmas, Las"]:
        provincia_normalizada = "Las Palmas"
    elif provincia in ["Santa Cruz de Tenerife", "Tenerife", "S.C. Tenerife"]:
        provincia_normalizada = "Santa Cruz de Tenerife"
    elif provincia in ["Asturias", "Principado de Asturias"]:
        provincia_normalizada = "Asturias"
    elif provincia in ["Cantabria", "Santander"]:
        provincia_normalizada = "Cantabria"
    elif provincia in ["La Rioja", "Rioja", "Logroño"]:
        provincia_normalizada = "La Rioja"
    elif provincia in ["Navarra", "Nafarroa"]:
        provincia_normalizada = "Navarra"
    elif provincia in ["Ourense", "Orense"]:
        provincia_normalizada = "Ourense"
    
    cursor.execute("""
        SELECT zona_climatica_cte 
        FROM core_zonas_cte_reglas
        WHERE provincia = %s 
          AND %s >= h_min 
          AND %s <= h_max
        LIMIT 1
    """, (provincia_normalizada, altitud, altitud))
    
    result = cursor.fetchone()
    cursor.close()
    if not result:
        raise RuntimeError(f"No hay regla CTE para provincia={provincia} (normalizada: {provincia_normalizada}) altitud={altitud}")
    return result[0]

def get_coordinates_with_fallbacks(municipio: str, provincia: str) -> Optional[Tuple[float, float]]:
    """Obtener coordenadas con múltiples fallbacks."""
    
    # Fallback 1: Nominatim con query completa
    try:
        time.sleep(1.2)  # Rate limit Nominatim
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
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"  Fallback 1 (Nominatim completo) falló: {e}")
    
    # Fallback 2: Nominatim solo municipio
    try:
        time.sleep(1.2)
        params = {
            'q': f"{municipio}, España",
            'format': 'json',
            'limit': 1
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"  Fallback 2 (Nominatim solo municipio) falló: {e}")
    
    # Fallback 3: Coordenadas aproximadas por provincia (centro geográfico)
    coords_provincia = {
        'Madrid': (40.4168, -3.7038),
        'Barcelona': (41.3851, 2.1734),
        'Sevilla': (37.3886, -5.9823),
        'Valencia/València': (39.4699, -0.3763),
        'Gipuzkoa': (43.2630, -2.0016),
        'Bizkaia': (43.2627, -2.9253),
        'Araba/Álava': (42.8467, -2.6716),
        # Añadir más según necesidad
    }
    
    if provincia in coords_provincia:
        print(f"  Usando coordenadas aproximadas de {provincia}")
        return coords_provincia[provincia]
    
    return None

def get_hdd_cdd_open_meteo_resilient(lat: float, lon: float, max_retries: int = 5):
    """Obtener HDD/CDD con reintentos y backoff exponencial."""
    
    for attempt in range(max_retries):
        try:
            # Delay mucho más conservador para evitar rate limiting
            base_delay = 3.0  # Mínimo 3 segundos
            delay = base_delay + (attempt * 5.0) + random.uniform(0, 2)
            time.sleep(delay)
            
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
            
            # Si es 429 (rate limit), esperar mucho más tiempo
            if response.status_code == 429:
                wait_time = 120 + (attempt * 60)  # Mínimo 2 minutos, hasta 5 minutos
                print(f"  Rate limit detectado, esperando {wait_time}s...")
                time.sleep(wait_time)
                continue
                
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
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                wait_time = 60 + (attempt * 30)
                print(f"  Rate limit (intento {attempt + 1}/{max_retries}), esperando {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                raise RuntimeError(f"Open-Meteo HTTP error: {e}")
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Open-Meteo fallo tras {max_retries} intentos: {e}")
            print(f"  Intento {attempt + 1} falló: {e}")
            time.sleep(5 + attempt * 5)
    
    raise RuntimeError(f"Open-Meteo fallo tras {max_retries} intentos")

def get_last_processed_cp(conn) -> str:
    """Obtener el último CP procesado para continuar desde ahí."""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(codigo_postal) FROM core_zonas_climaticas")
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result[0] else "00000"

def main():
    parser = argparse.ArgumentParser(description='Carga resiliente de zonas climáticas')
    parser.add_argument('--limit', type=int, help='Límite de registros a procesar')
    parser.add_argument('--resume', action='store_true', help='Continuar desde último CP procesado')
    parser.add_argument('--start-cp', type=str, help='Empezar desde un CP específico')
    args = parser.parse_args()
    
    # Conexión a BD
    conn = psycopg2.connect(dbname='db_Ncore', **DB_CONFIG)
    
    # Determinar desde dónde empezar
    start_from_cp = "00000"
    if args.resume:
        start_from_cp = get_last_processed_cp(conn)
        print(f"🔄 Continuando desde CP: {start_from_cp}")
    elif args.start_cp:
        start_from_cp = args.start_cp
        print(f"🎯 Empezando desde CP: {start_from_cp}")
    
    # Leer CSV
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Filtrar desde el CP de inicio
    if start_from_cp != "00000":
        rows = [row for row in rows if row['codigo_postal'] > start_from_cp]
    
    if args.limit:
        rows = rows[:args.limit]
    
    total = len(rows)
    procesados = 0
    exitosos = 0
    errores = 0
    
    print(f"📊 Procesando {total} registros...")
    
    for i, row in enumerate(rows):
        cp = row['codigo_postal']
        municipio = row['municipio']
        
        try:
            # Obtener provincia
            provincia_codigo = cp[:2]
            if provincia_codigo not in PROVINCIA_POR_CP:
                raise RuntimeError(f"Código postal {cp} no válido")
            provincia = PROVINCIA_POR_CP[provincia_codigo]
            
            print(f"[{i+1:4d}/{total}] {municipio} ({cp}) - {provincia}")
            
            # Obtener coordenadas
            coords = get_coordinates_with_fallbacks(municipio, provincia)
            if not coords:
                raise RuntimeError("No se pudieron obtener coordenadas")
            
            lat, lon = coords
            
            # Obtener datos climáticos
            hdd, cdd, temp_media, altitud = get_hdd_cdd_open_meteo_resilient(lat, lon)
            
            # Obtener zona CTE
            zona_cte = get_zona_cte(conn, provincia, altitud)
            
            # Insertar en BD
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO core_zonas_climaticas 
                (codigo_postal, municipio, provincia, latitud, longitud, altitud, 
                 zona_climatica_cte, hdd_anual_medio, cdd_anual_medio, temperatura_media_anual,
                 fecha_actualizacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (codigo_postal) DO UPDATE SET
                    municipio = EXCLUDED.municipio,
                    provincia = EXCLUDED.provincia,
                    latitud = EXCLUDED.latitud,
                    longitud = EXCLUDED.longitud,
                    altitud = EXCLUDED.altitud,
                    zona_climatica_cte = EXCLUDED.zona_climatica_cte,
                    hdd_anual_medio = EXCLUDED.hdd_anual_medio,
                    cdd_anual_medio = EXCLUDED.cdd_anual_medio,
                    temperatura_media_anual = EXCLUDED.temperatura_media_anual,
                    fecha_actualizacion = NOW()
            """, (cp, municipio, provincia, lat, lon, altitud, zona_cte, hdd, cdd, temp_media))
            cursor.close()
            conn.commit()
            
            exitosos += 1
            print(f"  ✅ {zona_cte} | HDD:{hdd:.0f} CDD:{cdd:.0f} | Alt:{altitud:.0f}m")
            
        except Exception as e:
            errores += 1
            print(f"  ❌ Error: {e}")
            
        procesados += 1
        
        # Progreso cada 100 registros
        if procesados % 100 == 0:
            print(f"📈 Progreso: {procesados}/{total} ({exitosos} exitosos, {errores} errores)")
    
    conn.close()
    
    print(f"\n🏁 COMPLETADO:")
    print(f"   Total procesados: {procesados}")
    print(f"   Exitosos: {exitosos}")
    print(f"   Errores: {errores}")
    print(f"   Tasa éxito: {exitosos/procesados*100:.1f}%")

if __name__ == "__main__":
    main()
