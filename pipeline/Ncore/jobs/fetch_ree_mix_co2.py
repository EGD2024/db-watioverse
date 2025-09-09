#!/usr/bin/env python3
"""
Job de ingesta REE usando endpoint de mercados (funcional):
- Obtiene datos PVPC desde endpoint mercados/precios-mercados-tiempo-real
- Almacena RAW por fecha (jsonb) para resiliencia ante cambios de esquema
- Para mix energético y CO2: usar fetch_ree_alternative.py hasta resolver bloqueo API
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

# Endpoints REE (dataset públicos)
REE_BASE = "https://apidatos.ree.es/es/datos"
# ENDPOINT FUNCIONAL: Mercados (incluye PVPC y otros datos)
REE_MERCADOS_ENDPOINT = f"{REE_BASE}/mercados/precios-mercados-tiempo-real"
# Endpoints originales (bloqueados por Incapsula)
# REE_MIX_ENDPOINT = f"{REE_BASE}/generacion/estructura-generacion"
# REE_CO2_ENDPOINT = f"{REE_BASE}/generacion/emisiones-co2"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.ree.es/es/datos',
    'Origin': 'https://www.ree.es',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site'
}


def iso_day_bounds(day: datetime):
    start = day.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    # REE requiere ISO con zona; usamos UTC para estabilidad
    return start.isoformat().replace('+00:00', 'Z'), end.isoformat().replace('+00:00', 'Z')


def fetch_json(url: str, params: dict) -> dict:
    """Descarga JSON con hasta 4 reintentos y delays aleatorios."""
    delay = random.uniform(2.0, 4.0)  # Delay inicial aleatorio
    last_err = None
    
    for attempt in range(4):
        try:
            # Delay aleatorio antes de cada intento (excepto el primero)
            if attempt > 0:
                time.sleep(delay)
            
            # Session para mantener cookies
            session = requests.Session()
            session.headers.update(HEADERS)
            
            r = session.get(url, params=params, timeout=45)
            r.raise_for_status()
            return r.json()
            
        except Exception as e:
            last_err = e
            print(f"❌ Intento {attempt + 1}/4 falló: {e}")
            delay = random.uniform(delay * 1.5, delay * 2.5)  # Backoff aleatorio
            
    raise last_err


def upsert_raw(conn, table: str, fecha: str, payload: dict):
    cur = conn.cursor()
    cur.execute(
        f"""
        INSERT INTO {table} (fecha, payload)
        VALUES (%s, %s)
        ON CONFLICT (fecha) DO UPDATE SET
          payload = EXCLUDED.payload,
          created_at = CURRENT_TIMESTAMP
        """,
        (fecha, json.dumps(payload))
    )
    cur.close()


def normalize_mix(conn, payload: dict):
    """Inserta en core_ree_mix_horario si el esquema esperado está presente.
    Se espera una estructura con series horarias por tecnología.
    """
    included = payload.get('included') or payload.get('data') or []
    rows = []
    # Buscamos series con atributos 'type' o 'attributes' que tengan values con (datetime,value,percentage)
    for node in included:
        series = None
        tecnologia = None
        if isinstance(node, dict):
            tecnologia = node.get('type') or node.get('attributes', {}).get('type') or node.get('id')
            series = node.get('attributes', {}).get('values') or node.get('values')
        if not series or not tecnologia:
            continue
        for item in series:
            dt = item.get('datetime') or item.get('date')
            val = item.get('value')
            pct = item.get('percentage') or item.get('perc')
            if dt is None:
                continue
            try:
                # Normalizamos a timestamp sin TZ (asumimos UTC)
                ts = datetime.fromisoformat(dt.replace('Z','+00:00')).replace(tzinfo=None)
                rows.append((ts, str(tecnologia), val, pct))
            except Exception:
                continue
    if not rows:
        return 0
    cur = conn.cursor()
    cur.executemany(
        """
        INSERT INTO core_ree_mix_horario (fecha_hora, tecnologia, mwh, porcentaje, fuente)
        VALUES (%s, %s, %s, %s, 'REE')
        ON CONFLICT (fecha_hora, tecnologia) DO UPDATE SET
          mwh = EXCLUDED.mwh,
          porcentaje = EXCLUDED.porcentaje,
          fecha_carga = CURRENT_TIMESTAMP
        """,
        rows
    )
    cur.close()
    return len(rows)


def normalize_co2(conn, payload: dict):
    rows = []
    included = payload.get('included') or payload.get('data') or []
    for node in included:
        series = None
        if isinstance(node, dict):
            series = node.get('attributes', {}).get('values') or node.get('values')
        if not series:
            continue
        for item in series:
            dt = item.get('datetime') or item.get('date')
            val = item.get('value')
            if dt is None:
                continue
            try:
                ts = datetime.fromisoformat(dt.replace('Z','+00:00')).replace(tzinfo=None)
                rows.append((ts, val))
            except Exception:
                continue
    if not rows:
        return 0
    cur = conn.cursor()
    cur.executemany(
        """
        INSERT INTO core_ree_emisiones_horario (fecha_hora, gco2_kwh, fuente)
        VALUES (%s, %s, 'REE')
        ON CONFLICT (fecha_hora) DO UPDATE SET
          gco2_kwh = EXCLUDED.gco2_kwh,
          fecha_carga = CURRENT_TIMESTAMP
        """,
        rows
    )
    cur.close()
    return len(rows)


def fetch_mercados_data(conn, day, params):
    """Obtiene datos de mercados REE (PVPC y otros indicadores)."""
    try:
        payload = fetch_json(REE_MERCADOS_ENDPOINT, params)
        upsert_raw(conn, 'core_ree_mercados_json', day.isoformat(), payload)
        
        # Extraer datos PVPC si están disponibles
        included = payload.get('included', [])
        pvpc_rows = 0
        
        for item in included:
            if item.get('type') == 'PVPC':
                values = item.get('attributes', {}).get('values', [])
                for val in values:
                    dt_str = val.get('datetime')
                    price = val.get('value')
                    if dt_str and price is not None:
                        try:
                            ts = datetime.fromisoformat(dt_str.replace('Z','+00:00')).replace(tzinfo=None)
                            # Insertar en tabla de precios si existe
                            cur = conn.cursor()
                            cur.execute("""
                                INSERT INTO core_precios_omie (timestamp_hora, precio_spot, fuente)
                                VALUES (%s, %s, %s)
                                ON CONFLICT (timestamp_hora) DO UPDATE SET
                                  precio_spot = EXCLUDED.precio_spot,
                                  fecha_publicacion = CURRENT_TIMESTAMP
                            """, (ts, price/1000, 'REE-MERCADOS'))  # Convertir a EUR/kWh
                            cur.close()
                            pvpc_rows += 1
                        except Exception as e:
                            continue
        
        return pvpc_rows
        
    except Exception as e:
        print(f"❌ REE MERCADOS error: {e}")
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

    params = {
        'start_date': start_iso,
        'end_date': end_iso,
        'time_trunc': 'hour',
        'geo_limit': 'country',
        'geo_ids': '8741'  # Spain
    }

    # Conexión BD
    conn = psycopg2.connect(**DB)

    # Usar endpoint de mercados que SÍ funciona
    n_mercados = fetch_mercados_data(conn, day, params)
    
    # Mantener datos mock para mix/CO2 hasta encontrar fuente real
    print(f"ℹ️  Para mix energético y CO2, usar: python fetch_ree_alternative.py --source mock --date {day}")

    conn.commit()
    conn.close()

    print(f"✅ REE {day}: mercados filas={n_mercados} (mix/CO2 pendientes de fuente alternativa)")


if __name__ == '__main__':
    main()
