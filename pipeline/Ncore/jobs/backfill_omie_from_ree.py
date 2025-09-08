#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backfill de precios OMIE horarios en db_sistema_electrico.omie_precios usando API REE.
- Convierte valores de EUR/MWh a EUR/kWh (÷1000) para encajar con el diseño existente.
- Evita duplicados: si el día ya tiene >= 20 registros (23/24/25 según DST), se salta.
- Inserta vía psql \copy para no depender de librerías de BD.

Uso:
  python3 backfill_omie_from_ree.py --start 2025-04-01 --end 2025-09-08
Si no se pasan fechas, calculará start = (MAX(fecha) en omie_precios) + 1 día, end = hoy.
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, date, timedelta, UTC
from typing import Optional, List, Dict
import time

import requests

REE_URL = "https://apidatos.ree.es/es/datos/mercados/precios-mercados"
# Endpoint alternativo (tiempo real) por si el principal devuelve 5xx
REE_URL_ALT = "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
# Parámetros típicos para pool peninsular ES. Si es necesario ajustar, lo dejamos centralizado aquí.
REE_PARAMS_BASE = {
    "time_trunc": "hour",
    "geo_limit": "country",
    "geo_ids": "8741",  # España peninsular (habitual en REE)
}

PSQL_BIN = os.getenv("PSQL_BIN", "psql")
DB_NAME = os.getenv("DB_SISTEMA_ELECTRICO", "db_sistema_electrico")
DB_USER = os.getenv("DB_USER", "postgres")
ZONA = "ES"
FUENTE_ID = 1


def run_psql_scalar(sql: str) -> Optional[str]:
    """Ejecuta psql y devuelve la salida en una sola línea (strip)."""
    try:
        res = subprocess.run(
            [PSQL_BIN, "-U", DB_USER, "-d", DB_NAME, "-tAc", sql],
            check=True,
            capture_output=True,
            text=True,
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] psql scalar failed: {e.stderr}", file=sys.stderr)
        return None


def day_already_loaded(target_date: date) -> bool:
    sql = f"SELECT COUNT(*) FROM omie_precios WHERE zona='ES' AND fecha = DATE '{target_date.isoformat()}';"
    out = run_psql_scalar(sql)
    try:
        n = int(out) if out is not None and out != '' else 0
    except ValueError:
        n = 0
    # Si hay >=20 registros ya consideramos que ese día está cargado (maneja 23/24/25 horas por DST)
    return n >= 20


def get_max_fecha() -> Optional[date]:
    out = run_psql_scalar("SELECT MAX(fecha) FROM omie_precios WHERE zona='ES';")
    if not out:
        return None
    try:
        return datetime.strptime(out, "%Y-%m-%d").date()
    except Exception:
        return None


def _extract_values_from_response(j: Dict) -> List[Dict]:
    """Extrae la lista de values horarios de la respuesta REE."""
    values: List[Dict] = []
    try:
        data = j.get("included", [])
        if not data:
            data = j.get("data", [])
        # Buscar el primer bloque con attributes.values
        for blk in data:
            attrs = blk.get("attributes", {})
            vals = attrs.get("values", [])
            if vals:
                values = vals
                break
    except Exception:
        values = []
    return values


def fetch_ree_day(d: date) -> List[Dict]:
    """Descarga valores horarios para un día, con reintentos y endpoint alternativo.
    Devuelve lista de dicts con keys típicas: datetime, value.
    """
    start_dt = d.strftime("%Y-%m-%dT00:00")
    end_dt = (d + timedelta(days=1)).strftime("%Y-%m-%dT00:00")
    params = {
        **REE_PARAMS_BASE,
        "start_date": start_dt,
        "end_date": end_dt,
    }
    headers = {"Accept": "application/json"}

    urls = [REE_URL, REE_URL_ALT]
    last_err: Optional[Exception] = None
    for url in urls:
        # Reintentos con backoff: 3 intentos: 2s, 5s, 10s
        for attempt, delay in [(1, 2), (2, 5), (3, 10)]:
            try:
                r = requests.get(url, params=params, headers=headers, timeout=60)
                r.raise_for_status()
                j = r.json()
                vals = _extract_values_from_response(j)
                if vals:
                    return vals
                # Si la respuesta es válida pero sin valores, probamos siguiente URL o intentos
                last_err = None
            except Exception as e:
                last_err = e
                time.sleep(delay)
        # probar siguiente URL
    if last_err:
        raise last_err
    return []


def write_csv_for_day(d: date, values: List[Dict], csv_path: str) -> int:
    # Columnas: fecha, hora (HH:MM:SS), periodo(int 1..24 aprox), precio_energia(€/kWh), zona, fuente_id, created_at
    rows = 0
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        for idx, v in enumerate(values):
            val_mwh = v.get("value")
            ts = v.get("datetime")  # ej: 2025-04-01T01:00:00.000+01:00
            if val_mwh is None or ts is None:
                continue
            # Convertir a €/kWh
            try:
                precio_kwh = float(val_mwh) / 1000.0
            except Exception:
                continue
            # Normalizar hora HH:MM:SS
            try:
                # Cortar sólo la parte de hora en formato HH:MM:SS
                hh = ts.split("T")[1].split("+")[0].split("-")[0]
                if len(hh) == 5:
                    hh = hh + ":00"
            except Exception:
                hh = "00:00:00"
            periodo = idx + 1  # índice 1..24 aprox (puede ser 23/25 DST)
            created_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
            w.writerow([d.isoformat(), hh, periodo, f"{precio_kwh:.6f}", ZONA, FUENTE_ID, created_at])
            rows += 1
    return rows


def copy_csv_into_db(csv_path: str):
    sql = ("\\copy omie_precios (fecha, hora, periodo, precio_energia, zona, fuente_id, created_at) "
           f"FROM '{csv_path}' WITH (FORMAT csv)")
    # Ejecutar psql -c "\copy ..."
    subprocess.run([PSQL_BIN, "-U", DB_USER, "-d", DB_NAME, "-c", sql], check=True)


def daterange(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur = cur + timedelta(days=1)


def week_chunks(start_d: date, end_d: date):
    """Genera rangos [s, e) de 7 días desde start_d hasta end_d inclusive."""
    cur = start_d
    while cur <= end_d:
        e = min(cur + timedelta(days=7), end_d + timedelta(days=1))
        yield cur, e
        cur = cur + timedelta(days=7)


def fetch_ree_range(start_d: date, end_d_exclusive: date) -> List[Dict]:
    """Descarga valores horarios para un rango semiabierto [start, end) con backoff/URL alt.
    Devuelve la lista plana de valores horarios (cada uno con datetime/value).
    """
    params = {
        **REE_PARAMS_BASE,
        "start_date": start_d.strftime("%Y-%m-%dT00:00"),
        "end_date": end_d_exclusive.strftime("%Y-%m-%dT00:00"),
    }
    headers = {"Accept": "application/json"}

    urls = [REE_URL, REE_URL_ALT]
    last_err: Optional[Exception] = None
    for url in urls:
        for attempt, delay in [(1, 2), (2, 5), (3, 10)]:
            try:
                r = requests.get(url, params=params, headers=headers, timeout=90)
                r.raise_for_status()
                j = r.json()
                vals = _extract_values_from_response(j)
                if vals:
                    return vals
                last_err = None
            except Exception as e:
                last_err = e
                time.sleep(delay)
    if last_err:
        raise last_err
    return []


def group_values_by_day(values: List[Dict]) -> Dict[date, List[Dict]]:
    by_day: Dict[date, List[Dict]] = {}
    for v in values:
        ts = v.get("datetime")
        if not ts:
            continue
        try:
            d_str = ts.split("T")[0]
            d_obj = datetime.strptime(d_str, "%Y-%m-%d").date()
        except Exception:
            continue
        by_day.setdefault(d_obj, []).append(v)
    return by_day


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=str, default=None)
    parser.add_argument("--end", type=str, default=None)
    args = parser.parse_args()

    today = date.today()
    if args.start:
        start_d = datetime.strptime(args.start, "%Y-%m-%d").date()
    else:
        max_d = get_max_fecha()
        start_d = (max_d + timedelta(days=1)) if max_d else date(2025, 4, 1)

    end_d = datetime.strptime(args.end, "%Y-%m-%d").date() if args.end else today

    if start_d > end_d:
        print(f"[INFO] Nada que backfillear. start={start_d} > end={end_d}")
        return

    print(f"[INFO] Backfill OMIE desde {start_d} hasta {end_d} (ambos inclusive)")

    # Proceso por paquetes semanales con fallback a diario
    for week_s, week_e_excl in week_chunks(start_d, end_d):
        label = f"{week_s}..{(week_e_excl - timedelta(days=1))}"
        try:
            print(f"[INFO] Paquete semanal {label}: descargando desde REE")
            vals = fetch_ree_range(week_s, week_e_excl)
            by_day = group_values_by_day(vals)
            # iterar días del paquete
            for d in daterange(week_s, week_e_excl - timedelta(days=1)):
                if d < start_d or d > end_d:
                    continue
                if day_already_loaded(d):
                    print(f"[SKIP] {d}: día ya cargado")
                    continue
                day_vals = by_day.get(d, [])
                if not day_vals:
                    print(f"[WARN] {d}: sin datos REE en paquete semanal, intento diario")
                    try:
                        day_vals = fetch_ree_day(d)
                    except Exception as e:
                        print(f"[ERROR] {d}: fallo fetch diario tras paquete semanal: {e}", file=sys.stderr)
                        continue
                    if not day_vals:
                        print(f"[WARN] {d}: sin datos en fetch diario")
                        continue
                with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".csv") as tmp:
                    tmp_path = tmp.name
                nrows = write_csv_for_day(d, day_vals, tmp_path)
                if nrows == 0:
                    print(f"[WARN] {d}: 0 filas para insertar")
                    os.unlink(tmp_path)
                    continue
                copy_csv_into_db(tmp_path)
                os.unlink(tmp_path)
                print(f"[OK] {d}: insertadas {nrows} filas en omie_precios")
        except Exception as e:
            print(f"[ERROR] Paquete semanal {label}: {e}. Fallback a procesamiento diario.", file=sys.stderr)
            # Fallback: recorrer cada día del paquete
            for d in daterange(week_s, week_e_excl - timedelta(days=1)):
                if d < start_d or d > end_d:
                    continue
                if day_already_loaded(d):
                    print(f"[SKIP] {d}: día ya cargado")
                    continue
                try:
                    day_vals = fetch_ree_day(d)
                    if not day_vals:
                        print(f"[WARN] {d}: sin datos REE")
                        continue
                    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".csv") as tmp:
                        tmp_path = tmp.name
                    nrows = write_csv_for_day(d, day_vals, tmp_path)
                    if nrows == 0:
                        print(f"[WARN] {d}: 0 filas para insertar")
                        os.unlink(tmp_path)
                        continue
                    copy_csv_into_db(tmp_path)
                    os.unlink(tmp_path)
                    print(f"[OK] {d}: insertadas {nrows} filas en omie_precios")
                except Exception as e2:
                    print(f"[ERROR] {d}: {e2}", file=sys.stderr)
                    continue


if __name__ == "__main__":
    main()
