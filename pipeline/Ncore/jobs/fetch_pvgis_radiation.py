#!/usr/bin/env python3
"""
Job de PVGIS: descarga irradiancia mensual (kWh/m2) por coordenadas y almacena:
- RAW por (lat, lon) en core_pvgis_raw
- Normalizado mensual en core_pvgis_radiacion (mes 1..12)

Fuente API: PVGIS Radiation (JSON). Sin API key.
Operativa estricta: sin valores por defecto. Si falla la API o no hay datos válidos, no insertamos.

Uso:
  --limit N           Número máximo de coordenadas a procesar (default: 100)
  --source zonas      Fuente de coordenadas: 'zonas' (core_zonas_climaticas) [default]
  --lat LAT --lon LON Procesa solo una coordenada (ignora source/limit)
"""
import os
import sys
import json
import argparse
import time
from typing import Iterable, Tuple

import requests
from datetime import datetime
import psycopg2

DB = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'admin',
    'dbname': 'db_Ncore',
}

PVGIS_URL = 'https://re.jrc.ec.europa.eu/api/v5_2/MRcalc'
HEADERS = {'User-Agent': 'VagalumeEnergia/1.0 (pvgis-ingest)'}


def get_coords(conn, limit: int) -> Iterable[Tuple[float, float]]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT latitud, longitud
        FROM core_zonas_climaticas
        WHERE latitud IS NOT NULL AND longitud IS NOT NULL
        ORDER BY latitud, longitud
        LIMIT %s
        """,
        (limit,)
    )
    for lat, lon in cur.fetchall():
        yield float(lat), float(lon)
    cur.close()


def fetch_pvgis(lat: float, lon: float) -> dict:
    params = {
        'lat': lat,
        'lon': lon,
        'outputformat': 'json',
        'horirrad': 1,
    }
    delay = 1.0
    last_err = None
    for _ in range(4):
        try:
            r = requests.get(PVGIS_URL, params=params, headers=HEADERS, timeout=30)
            r.raise_for_status()
            data = r.json()
            if 'outputs' not in data or 'monthly' not in data['outputs']:
                raise RuntimeError('PVGIS sin outputs.monthly')
            return data
        except Exception as e:
            last_err = e
            time.sleep(delay)
            delay *= 2
    raise last_err


def upsert_raw(conn, lat: float, lon: float, payload: dict):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO core_pvgis_raw (latitud, longitud, payload)
        VALUES (%s, %s, %s)
        ON CONFLICT (latitud, longitud) DO UPDATE SET
          payload = EXCLUDED.payload,
          fecha_carga = CURRENT_TIMESTAMP
        """,
        (lat, lon, json.dumps(payload))
    )
    cur.close()


def normalize_monthly(conn, lat: float, lon: float, payload: dict) -> int:
    monthly = payload['outputs']['monthly']
    rows = []
    # monthly puede ser lista de 12 dicts o un dict indexado por mes
    def add_row(month_idx: int, item: dict):
        # Campos típicos de PVGIS para irradiación mensual (kWh/m2)
        kwh_m2 = (
            item.get('G(h)_m') or  # Global sobre horizontal mensual
            item.get('H(h)_m') or  # Variante histórica
            item.get('Hh')         # Alternativa en algunas respuestas
        )
        if kwh_m2 is None:
            return
        rows.append((lat, lon, int(month_idx), float(kwh_m2)))

    if isinstance(monthly, list):
        for item in monthly:
            m = item.get('month') or item.get('m')
            if m is None:
                continue
            add_row(m, item)
    elif isinstance(monthly, dict):
        for m in range(1, 13):
            item = monthly.get(str(m)) or monthly.get(m)
            if not item:
                continue
            add_row(m, item)
    else:
        raise RuntimeError('Formato monthly no reconocido')
    if not rows:
        return 0
    cur = conn.cursor()
    cur.executemany(
        """
        INSERT INTO core_pvgis_radiacion (latitud, longitud, mes, kwh_m2)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (latitud, longitud, mes) DO UPDATE SET
          kwh_m2 = EXCLUDED.kwh_m2,
          fecha_actualizacion = CURRENT_TIMESTAMP
        """,
        rows
    )
    cur.close()
    return len(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--source', choices=['zonas'], default='zonas')
    parser.add_argument('--lat', type=float)
    parser.add_argument('--lon', type=float)
    args = parser.parse_args()

    conn = psycopg2.connect(**DB)

    coords = []
    if args.lat is not None and args.lon is not None:
        coords = [(args.lat, args.lon)]
    else:
        coords = list(get_coords(conn, args.limit))

    total_norm = 0
    for (lat, lon) in coords:
        data = fetch_pvgis(lat, lon)
        upsert_raw(conn, lat, lon, data)
        n = normalize_monthly(conn, lat, lon, data)
        total_norm += n
        # Respetar un poco al endpoint
        time.sleep(0.2)

    conn.commit()
    conn.close()

    print(f"✅ PVGIS coords={len(coords)} filas_norm={total_norm}")


if __name__ == '__main__':
    main()
