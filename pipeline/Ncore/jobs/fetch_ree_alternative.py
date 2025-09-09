#!/usr/bin/env python3
"""
Alternativa para datos REE usando fuentes públicas disponibles:
1. ENTSO-E Transparency Platform (mix europeo)
2. Datos REE descargables (CSV desde web oficial)
3. Carbon Intensity API (UK, pero tiene datos EU)

Uso:
  --source entso-e|csv|carbon    Fuente de datos
  --date YYYY-MM-DD              Fecha objetivo
"""

import argparse
import requests
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
import json

DB = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'admin',
    'dbname': 'db_Ncore',
}

def fetch_carbon_intensity_eu(date_str):
    """
    Carbon Intensity API tiene datos europeos limitados
    Más para referencia que para datos precisos de España
    """
    try:
        # API gratuita con datos de intensidad de carbono
        url = "https://api.carbonintensity.org.uk/intensity"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        
        # Estructura básica para demo
        return {
            'source': 'carbon-intensity-api',
            'data': data.get('data', []),
            'note': 'Datos UK como referencia - no específicos de España'
        }
    except Exception as e:
        print(f"❌ Carbon Intensity API error: {e}")
        return None

def fetch_entso_e_data(date_str):
    """
    ENTSO-E Transparency Platform
    Requiere registro para API key, pero datos públicos disponibles
    """
    print("ℹ️  ENTSO-E requiere API key - implementación pendiente")
    print("   Registro en: https://transparency.entsoe.eu/")
    return None

def insert_mock_ree_data(conn, date_str):
    """
    Inserta datos REE de ejemplo basados en mix típico español
    Solo para testing - NO usar en producción
    """
    cur = conn.cursor()
    
    # Mix típico español (porcentajes aproximados)
    mix_data = [
        ('nuclear', 20.5, 'Energía nuclear'),
        ('eolica', 23.1, 'Energía eólica'),
        ('solar_fotovoltaica', 8.2, 'Solar fotovoltaica'),
        ('hidraulica', 12.3, 'Energía hidráulica'),
        ('ciclo_combinado', 18.7, 'Ciclo combinado gas'),
        ('carbon', 2.1, 'Carbón'),
        ('cogeneracion', 8.9, 'Cogeneración'),
        ('otras_renovables', 6.2, 'Otras renovables')
    ]
    
    # Generar 24 horas de datos
    base_date = datetime.strptime(date_str, '%Y-%m-%d')
    
    for hour in range(24):
        timestamp = base_date + timedelta(hours=hour)
        
        for tech, base_pct, desc in mix_data:
            # Variación horaria simulada
            variation = 1.0 + (hour - 12) * 0.02  # Variación ±24%
            mwh = base_pct * 1000 * variation  # Simular MWh
            percentage = base_pct * variation
            
            cur.execute("""
                INSERT INTO core_ree_mix_horario (fecha_hora, tecnologia, mwh, porcentaje, fuente)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (fecha_hora, tecnologia) DO UPDATE SET
                  mwh = EXCLUDED.mwh,
                  porcentaje = EXCLUDED.porcentaje,
                  fecha_carga = CURRENT_TIMESTAMP
            """, (timestamp, tech, mwh, percentage, 'MOCK-DATA'))
        
        # Emisiones CO2 simuladas (300-450 gCO2/kWh típico España)
        co2_intensity = 380 + (hour - 12) * 5  # Variación horaria
        cur.execute("""
            INSERT INTO core_ree_emisiones_horario (fecha_hora, gco2_kwh, fuente)
            VALUES (%s, %s, %s)
            ON CONFLICT (fecha_hora) DO UPDATE SET
              gco2_kwh = EXCLUDED.gco2_kwh,
              fecha_carga = CURRENT_TIMESTAMP
        """, (timestamp, co2_intensity, 'MOCK-DATA'))
    
    conn.commit()
    cur.close()
    return len(mix_data) * 24, 24

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', choices=['entso-e', 'csv', 'carbon', 'mock'], 
                       default='mock', help='Fuente de datos')
    parser.add_argument('--date', help='YYYY-MM-DD (por defecto: ayer)')
    args = parser.parse_args()

    if args.date:
        date_str = args.date
    else:
        date_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    conn = psycopg2.connect(**DB)
    
    if args.source == 'mock':
        print(f"⚠️  Insertando datos MOCK para {date_str}")
        print("   SOLO PARA TESTING - No usar en producción")
        mix_rows, co2_rows = insert_mock_ree_data(conn, date_str)
        print(f"✅ Mock REE {date_str}: mix filas={mix_rows}, co2 filas={co2_rows}")
        
    elif args.source == 'carbon':
        data = fetch_carbon_intensity_eu(date_str)
        if data:
            print(f"✅ Carbon Intensity data disponible (referencia)")
        else:
            print("❌ No se pudieron obtener datos de Carbon Intensity")
            
    elif args.source == 'entso-e':
        fetch_entso_e_data(date_str)
        
    else:
        print(f"❌ Fuente '{args.source}' no implementada")

    conn.close()

if __name__ == '__main__':
    main()
