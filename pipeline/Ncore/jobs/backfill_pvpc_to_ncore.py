#!/usr/bin/env python3
"""
Backfill horario PVPC → Ncore desde db_sistema_electrico vía FDW `f_precios_horarios_pvpc`.
- Copia TODO el rango solicitado (por defecto: desde el mínimo disponible hasta hoy).
- Idempotente: ON CONFLICT por (timestamp_hora).
- Unidades: origen €/kWh → destino €/MWh (×1000) como en `sync_pvpc_incremental.sql`.

Uso:
  python backfill_pvpc_to_ncore.py --start 2025-04-01 --end 2025-09-08 --step-days 7

Notas:
- Conecta directamente a 'db_Ncore' con nombres reales (sin fallbacks), siguiendo patrón de `fetch_ree_mix_co2.py`.
- Requiere que en db_Ncore existan las foreign tables al origen: `f_precios_horarios_pvpc`.
- No calcula columnas derivadas (demanda_*, métricas diarias). Solo spot/ajuste/final.
"""
import argparse
from datetime import date, datetime, timedelta
import sys
import psycopg2

DB = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'admin',
    'dbname': 'db_Ncore',
}

UPSERT_SQL = """
INSERT INTO core_precios_omie (timestamp_hora, precio_spot, precio_ajuste, precio_final)
SELECT
  (p.fecha + p.hora)::timestamp                 AS timestamp_hora,
  (p.precio_energia*1000)::numeric             AS precio_spot,
  ((COALESCE(p.precio_peajes,0)
    + COALESCE(p.precio_cargos,0))*1000)::numeric AS precio_ajuste,
  (p.precio_total_pvpc*1000)::numeric          AS precio_final
FROM f_precios_horarios_pvpc p
WHERE p.fecha >= %(start)s AND p.fecha < %(end)s
ON CONFLICT (timestamp_hora) DO UPDATE
SET precio_spot   = EXCLUDED.precio_spot,
    precio_ajuste = EXCLUDED.precio_ajuste,
    precio_final  = EXCLUDED.precio_final;
"""

MINMAX_SRC_SQL = """
SELECT MIN(fecha) AS min_fecha, MAX(fecha) AS max_fecha FROM f_precios_horarios_pvpc;
"""

MAX_DST_SQL = """
SELECT COALESCE(MAX(timestamp_hora)::date, NULL) AS max_dst FROM core_precios_omie;
"""

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', help='YYYY-MM-DD (por defecto: min(fecha) en origen)')
    ap.add_argument('--end', help='YYYY-MM-DD (exclusiva, por defecto: hoy+1)')
    ap.add_argument('--step-days', type=int, default=7, help='Tamaño de lote en días (por defecto: 7)')
    return ap.parse_args()


def to_date(s: str) -> date:
    return datetime.strptime(s, '%Y-%m-%d').date()


def main():
    args = parse_args()

    conn = psycopg2.connect(**DB)
    conn.autocommit = False
    cur = conn.cursor()

    # Descubrir rango origen si no se especifica
    cur.execute(MINMAX_SRC_SQL)
    row = cur.fetchone()
    min_src, max_src = row[0], row[1]
    if min_src is None:
        print('❌ Origen f_precios_horarios_pvpc vacío. Abortando.')
        conn.close()
        sys.exit(2)

    start = to_date(args.start) if args.start else min_src
    # Por defecto end = hoy + 1 (exclusiva)
    end = to_date(args.end) if args.end else (date.today() + timedelta(days=1))

    # Ajustar a rango disponible origen
    if start < min_src:
        start = min_src
    if end > (max_src + timedelta(days=1)):
        end = max_src + timedelta(days=1)

    step = timedelta(days=max(1, args.step_days))

    print(f"🔎 Backfill PVPC: rango [{start} .. {end}) en pasos de {step.days}d")

    total_batches = 0
    total_rows = 0
    try:
        d0 = start
        while d0 < end:
            d1 = min(d0 + step, end)
            print(f"➡️  Lote: [{d0} .. {d1})")
            cur.execute(UPSERT_SQL, {'start': d0, 'end': d1})
            affected = cur.rowcount  # número de filas afectadas (no fiable con ON CONFLICT, informativo)
            conn.commit()
            total_batches += 1
            total_rows += max(0, affected or 0)
            print(f"   ✅ Confirmado lote {total_batches} (filas afectadas aprox: {affected})")
            d0 = d1
    except Exception as e:
        conn.rollback()
        print(f"❌ Error en backfill: {e}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

    print(f"✅ Backfill completado. Lotes: {total_batches}, filas afectadas aprox: {total_rows}")

if __name__ == '__main__':
    main()
