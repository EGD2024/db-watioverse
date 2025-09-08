#!/usr/bin/env python3
"""
Job de ingesta REE: mix de generación y factor de emisiones CO2 (horario).
- Almacena RAW por fecha (jsonb) para resiliencia ante cambios de esquema.
- Normaliza a tablas horarias cuando el payload incluye la estructura esperada.
- Idempotente: upsert por claves primarias.
- Estricto: nombres reales de BD/tablas; si falla la consulta remota, no se inventan datos.

Uso:
  --date YYYY-MM-DD   Fecha de referencia (por defecto: ayer)
"""
import os
import sys
import json
import time
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
# Mix de generación (Estructura de generación)
REE_MIX_ENDPOINT = f"{REE_BASE}/generacion/estructura-generacion"
# Factor de emisión horario (intensidad de carbono del mix)
# Dataset puede variar; se usa emisiones-co2 como recurso horario
REE_CO2_ENDPOINT = f"{REE_BASE}/generacion/emisiones-co2"

HEADERS = {
    'User-Agent': 'VagalumeEnergia/1.0 (ree-mix-co2-ingest)'
}


def iso_day_bounds(day: datetime):
    start = day.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    # REE requiere ISO con zona; usamos UTC para estabilidad
    return start.isoformat().replace('+00:00', 'Z'), end.isoformat().replace('+00:00', 'Z')


def fetch_json(url: str, params: dict) -> dict:
    """Descarga JSON con hasta 4 reintentos (1s, 2s, 4s)."""
    delay = 1.0
    last_err = None
    for _ in range(4):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            time.sleep(delay)
            delay *= 2
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

    n_mix = 0
    n_co2 = 0

    # 1) MIX
    try:
        mix_payload = fetch_json(REE_MIX_ENDPOINT, params)
        upsert_raw(conn, 'core_ree_mix_json', day.isoformat(), mix_payload)
        n_mix = normalize_mix(conn, mix_payload)
    except Exception as e:
        print(f"❌ REE MIX error: {e}")

    # 2) CO2
    try:
        co2_payload = fetch_json(REE_CO2_ENDPOINT, params)
        upsert_raw(conn, 'core_ree_co2_json', day.isoformat(), co2_payload)
        n_co2 = normalize_co2(conn, co2_payload)
    except Exception as e:
        print(f"❌ REE CO2 error: {e}")

    conn.commit()
    conn.close()

    print(f"✅ REE {day}: mix filas={n_mix}, co2 filas={n_co2}")


if __name__ == '__main__':
    main()
