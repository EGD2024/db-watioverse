#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Promociona datos desde db_enriquecimiento.public.catastro_inmuebles a db_N2.public.n2_catastro_inmueble
para CUPS pendientes o desactualizados.

- Sin fallbacks: si un CUPS no tiene fila en cache o carece de campos mínimos, se registra y el proceso devuelve exit 1
- Conexiones por nombres reales: db_enriquecimiento y db_N2
- Política de actualización: UPSERT por CUPS con updated_at = NOW()

Campos mínimos requeridos de cache:
- cups (TEXT no nulo)
- referencia_catastral (TEXT)
- uso_principal (TEXT)
- superficie_construida_m2 (NUMERIC >= 0)

CRON one-liner sugerido (ejemplo):
  25 2 * * * DB_HOST=localhost DB_PORT=5432 DB_USER=postgres DB_PASSWORD=admin \
  python3 /Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/pipeline/Ncore/jobs/fetch_catastro_for_n2.py --max 200
"""
import os
import sys
import argparse
import psycopg2

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'admin')


def get_conn(dbname: str):
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=dbname)


def find_pending_cups(conn_n2, max_rows: int):
    sql = """
    WITH pendientes AS (
      SELECT DISTINCT c.cups
      FROM db_enriquecimiento.public.catastro_inmuebles c
      WHERE c.cups IS NOT NULL AND TRIM(c.cups) <> ''
    )
    SELECT p.cups
    FROM pendientes p
    LEFT JOIN public.n2_catastro_inmueble n2 ON n2.cups = p.cups
    WHERE n2.cups IS NULL OR n2.updated_at < NOW() - INTERVAL '180 days'
    LIMIT %s
    """
    with conn_n2.cursor() as c:
        c.execute(sql, (max_rows,))
        return [r[0] for r in c.fetchall()]


def fetch_cache_row(conn_enr, cups: str):
    with conn_enr.cursor() as c:
        c.execute(
            """
            SELECT cups, referencia_catastral, uso_principal,
                   superficie_construida_m2, superficie_parcela_m2,
                   fecha_consulta
            FROM public.catastro_inmuebles
            WHERE cups = %s
            ORDER BY fecha_consulta DESC
            LIMIT 1
            """,
            (cups,)
        )
        row = c.fetchone()
        return row


def upsert_n2(conn_n2, row):
    cups, rc, uso, sup_const, sup_parc, fecha = row
    # Validaciones mínimas
    if not cups or not uso or sup_const is None or (sup_const is not None and sup_const < 0):
        raise ValueError(f"Datos insuficientes para CUPS {cups}: uso='{uso}', superficie_construida_m2='{sup_const}'")

    with conn_n2.cursor() as c:
        c.execute(
            """
            INSERT INTO public.n2_catastro_inmueble (
                cups, referencia_catastral, uso_principal,
                superficie_construida_total_m2, superficie_parcela_m2,
                fuente, fecha_extraccion, updated_at
            )
            VALUES (%s,%s,%s,%s,%s,'catastro_cache', COALESCE(%s, NOW()), NOW())
            ON CONFLICT (cups)
            DO UPDATE SET
                referencia_catastral = EXCLUDED.referencia_catastral,
                uso_principal = EXCLUDED.uso_principal,
                superficie_construida_total_m2 = EXCLUDED.superficie_construida_total_m2,
                superficie_parcela_m2 = EXCLUDED.superficie_parcela_m2,
                fecha_extraccion = EXCLUDED.fecha_extraccion,
                updated_at = NOW()
            """,
            (cups, rc, uso, sup_const, sup_parc, fecha)
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max', type=int, default=200, help='máximo de CUPS a procesar')
    args = parser.parse_args()

    enr = get_conn('db_enriquecimiento')
    n2 = get_conn('db_N2')
    try:
        pending = find_pending_cups(n2, args.max)
        if not pending:
            print('✅ No hay CUPS pendientes o desactualizados para Catastro (N2)')
            return
        failures = []
        for cups in pending:
            row = fetch_cache_row(enr, cups)
            if not row:
                failures.append((cups, 'sin_cache'))
                continue
            try:
                upsert_n2(n2, row)
            except Exception as e:
                failures.append((cups, str(e)))
        n2.commit()
        if failures:
            print('❌ Fallos en promoción a N2:')
            for cups, cause in failures:
                print(f' - {cups}: {cause}', file=sys.stderr)
            sys.exit(1)
        print(f"✅ Promoción a N2 completada. CUPS procesados: {len(pending)}")
    finally:
        enr.close(); n2.close()


if __name__ == '__main__':
    main()
