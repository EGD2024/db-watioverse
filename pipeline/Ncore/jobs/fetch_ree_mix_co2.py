#!/usr/bin/env python3
"""
Job de ingesta ESIOS (migrado desde REE por bloqueos Incapsula):
- Obtiene datos PVPC, mix energético y CO2 desde ESIOS API
- Almacena datos normalizados en tablas específicas
- Idempotente: upsert por claves primarias
- Estricto: nombres reales de BD/tablas; si falla la consulta remota, no se inventan datos

Uso:
  --date YYYY-MM-DD   Fecha de referencia (por defecto: ayer)
"""
import os
import sys
import json
import time
import random
import argparse
from datetime import datetime, timedelta, timezone

import requests
import psycopg2

DB = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'admin',
    'dbname': 'db_Ncore',
}

# Migrado a ESIOS API - más confiable que REE
ESIOS_API_TOKEN = os.getenv("ESIOS_API_TOKEN")
if not ESIOS_API_TOKEN:
    raise ValueError("El token ESIOS_API_TOKEN no está configurado.")

ESIOS_BASE = "https://api.esios.ree.es"

# Indicadores ESIOS para diferentes tipos de datos
INDICADORES = {
    'pvpc': 1001,  # Término de facturación de energía activa del PVPC 2.0TD
    'generacion_renovable': 1433,  # Generación renovable
    'generacion_no_renovable': 1434,  # Generación no renovable
    'demanda_real': 1293,  # Demanda eléctrica en tiempo real
    'emisiones_co2': 1739,  # Emisiones CO2 del sistema
}

HEADERS = {
    'Accept': 'application/json; application/vnd.esios-api-v1+json',
    'Content-Type': 'application/json',
    'x-api-key': ESIOS_API_TOKEN
}


def iso_day_bounds(day: datetime):
    start = day.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    # REE requiere ISO con zona; usamos UTC para estabilidad
    return start.isoformat().replace('+00:00', 'Z'), end.isoformat().replace('+00:00', 'Z')


def fetch_esios_indicator(indicator_id: int, start_date: str, end_date: str) -> dict:
    """Obtiene datos de un indicador ESIOS con reintentos."""
    delay = random.uniform(1.0, 2.0)  # Delay inicial aleatorio
    last_err = None
    
    url = f"{ESIOS_BASE}/indicators/{indicator_id}"
    params = {
        'start_date': start_date,
        'end_date': end_date,
        'geo_ids[]': 8741  # Península
    }
    
    for attempt in range(3):
        try:
            # Delay aleatorio antes de cada intento (excepto el primero)
            if attempt > 0:
                time.sleep(delay)
            
            session = requests.Session()
            session.headers.update(HEADERS)
            
            r = session.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
            
        except Exception as e:
            last_err = e
            print(f"❌ Intento {attempt + 1}/3 falló para indicador {indicator_id}: {e}")
            delay = random.uniform(delay * 1.5, delay * 2.0)  # Backoff aleatorio
            
    raise last_err


# Función eliminada - ya no necesitamos almacenar JSON raw


# Función eliminada - reemplazada por fetch_mix_data que usa ESIOS directamente


# Función eliminada - reemplazada por fetch_co2_data que usa ESIOS directamente


def fetch_pvpc_data(conn, day, start_iso, end_iso):
    """Obtiene datos PVPC desde ESIOS."""
    try:
        payload = fetch_esios_indicator(INDICADORES['pvpc'], start_iso, end_iso)
        
        if 'indicator' not in payload or 'values' not in payload['indicator']:
            print(f"⚠️ Estructura inesperada en PVPC: {list(payload.keys())}")
            return 0
        
        values = payload['indicator']['values']
        pvpc_rows = 0
        
        cur = conn.cursor()
        for val in values:
            dt_str = val.get('datetime')
            price = val.get('value')
            if dt_str and price is not None:
                try:
                    ts = datetime.fromisoformat(dt_str.replace('Z','+00:00')).replace(tzinfo=None)
                    cur.execute("""
                        INSERT INTO core_precios_omie (timestamp_hora, precio_spot, fuente)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (timestamp_hora) DO UPDATE SET
                          precio_spot = EXCLUDED.precio_spot,
                          fecha_publicacion = CURRENT_TIMESTAMP
                    """, (ts, price/1000, 'ESIOS'))  # Convertir a EUR/kWh
                    pvpc_rows += 1
                except Exception as e:
                    continue
        cur.close()
        
        return pvpc_rows
        
    except Exception as e:
        print(f"❌ ESIOS PVPC error: {e}")
        return 0

def fetch_mix_data(conn, day, start_iso, end_iso):
    """Obtiene datos de mix energético desde ESIOS."""
    try:
        # Obtener generación renovable
        renovable_payload = fetch_esios_indicator(INDICADORES['generacion_renovable'], start_iso, end_iso)
        no_renovable_payload = fetch_esios_indicator(INDICADORES['generacion_no_renovable'], start_iso, end_iso)
        
        mix_rows = 0
        cur = conn.cursor()
        
        # Procesar datos renovables
        if 'indicator' in renovable_payload and 'values' in renovable_payload['indicator']:
            for val in renovable_payload['indicator']['values']:
                dt_str = val.get('datetime')
                mwh = val.get('value')
                if dt_str and mwh is not None:
                    try:
                        ts = datetime.fromisoformat(dt_str.replace('Z','+00:00')).replace(tzinfo=None)
                        cur.execute("""
                            INSERT INTO core_ree_mix_horario (fecha_hora, tecnologia, mwh, porcentaje, fuente)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (fecha_hora, tecnologia) DO UPDATE SET
                              mwh = EXCLUDED.mwh,
                              fecha_carga = CURRENT_TIMESTAMP
                        """, (ts, 'Renovable', mwh, None, 'ESIOS'))
                        mix_rows += 1
                    except Exception:
                        continue
        
        # Procesar datos no renovables
        if 'indicator' in no_renovable_payload and 'values' in no_renovable_payload['indicator']:
            for val in no_renovable_payload['indicator']['values']:
                dt_str = val.get('datetime')
                mwh = val.get('value')
                if dt_str and mwh is not None:
                    try:
                        ts = datetime.fromisoformat(dt_str.replace('Z','+00:00')).replace(tzinfo=None)
                        cur.execute("""
                            INSERT INTO core_ree_mix_horario (fecha_hora, tecnologia, mwh, porcentaje, fuente)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (fecha_hora, tecnologia) DO UPDATE SET
                              mwh = EXCLUDED.mwh,
                              fecha_carga = CURRENT_TIMESTAMP
                        """, (ts, 'No Renovable', mwh, None, 'ESIOS'))
                        mix_rows += 1
                    except Exception:
                        continue
        
        cur.close()
        return mix_rows
        
    except Exception as e:
        print(f"❌ ESIOS MIX error: {e}")
        return 0

def fetch_co2_data(conn, day, start_iso, end_iso):
    """Obtiene datos de emisiones CO2 desde ESIOS."""
    try:
        payload = fetch_esios_indicator(INDICADORES['emisiones_co2'], start_iso, end_iso)
        
        if 'indicator' not in payload or 'values' not in payload['indicator']:
            print(f"⚠️ Estructura inesperada en CO2: {list(payload.keys())}")
            return 0
        
        values = payload['indicator']['values']
        co2_rows = 0
        
        cur = conn.cursor()
        for val in values:
            dt_str = val.get('datetime')
            gco2_kwh = val.get('value')
            if dt_str and gco2_kwh is not None:
                try:
                    ts = datetime.fromisoformat(dt_str.replace('Z','+00:00')).replace(tzinfo=None)
                    cur.execute("""
                        INSERT INTO core_ree_emisiones_horario (fecha_hora, gco2_kwh, fuente)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (fecha_hora) DO UPDATE SET
                          gco2_kwh = EXCLUDED.gco2_kwh,
                          fecha_carga = CURRENT_TIMESTAMP
                    """, (ts, gco2_kwh, 'ESIOS'))
                    co2_rows += 1
                except Exception:
                    continue
        cur.close()
        
        return co2_rows
        
    except Exception as e:
        print(f"❌ ESIOS CO2 error: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', help='YYYY-MM-DD (por defecto: ayer)')
    args = parser.parse_args()

    if args.date:
        day = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        day = (datetime.utcnow() - timedelta(days=1)).date()
    start_iso, end_iso = iso_day_bounds(datetime.combine(day, datetime.min.time()))

    # Conexión BD
    conn = psycopg2.connect(**DB)

    # Obtener datos desde ESIOS API
    n_pvpc = fetch_pvpc_data(conn, day, start_iso, end_iso)
    n_mix = fetch_mix_data(conn, day, start_iso, end_iso)
    n_co2 = fetch_co2_data(conn, day, start_iso, end_iso)

    conn.commit()
    conn.close()

    print(f"✅ ESIOS {day}: PVPC={n_pvpc}, Mix={n_mix}, CO2={n_co2} filas insertadas")


if __name__ == '__main__':
    main()
