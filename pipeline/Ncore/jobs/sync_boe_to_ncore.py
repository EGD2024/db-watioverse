#!/usr/bin/env python3
"""
Ejecuta el upsert de BOE regulado en db_Ncore usando el SQL existente:
  pipeline/Ncore/sql/sync_boe_upsert.sql

- Usa nombres reales de BD (db_Ncore) sin fallbacks.
- Idempotente: el SQL hace ON CONFLICT por (tarifa_peaje, componente, fecha_inicio).
- Requiere que exista la foreign table `f_precio_regulado_boe` apuntando a db_sistema_electrico.
"""
import os
import sys
import psycopg2
from pathlib import Path

DB = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'admin',
    'dbname': 'db_Ncore',
}

SQL_PATH = Path(__file__).resolve().parents[1] / 'sql' / 'sync_boe_upsert.sql'

def main():
    if not SQL_PATH.exists():
        print(f"❌ No se encuentra el SQL: {SQL_PATH}")
        sys.exit(2)

    sql = SQL_PATH.read_text(encoding='utf-8')

    conn = psycopg2.connect(**DB)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
        print("✅ BOE upsert ejecutado correctamente")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error ejecutando upsert BOE: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
