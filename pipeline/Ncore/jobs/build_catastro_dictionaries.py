#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Construye/puebla diccionarios Catastro en db_Ncore desde la cache db_enriquecimiento.
- Sin fallbacks: si algo crítico falla, exit != 0
- No normaliza: inserta usos tal y como aparecen, deduplicados
- Conexiones por nombres reales: db_Ncore y db_enriquecimiento

CRON one-liner sugerido:
  25 2 * * * DB_HOST=localhost DB_PORT=5432 DB_USER=postgres DB_PASSWORD=admin \
  python3 /Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/pipeline/Ncore/jobs/build_catastro_dictionaries.py
"""
import os
import sys
import psycopg2

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'admin')


def get_conn(dbname: str):
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=dbname)


def upsert_dic_uso():
    enr = get_conn('db_enriquecimiento')
    core = get_conn('db_Ncore')
    try:
        with enr.cursor() as c_src, core.cursor() as c_dst:
            c_src.execute("""
                SELECT DISTINCT TRIM(uso_principal) AS uso
                FROM public.catastro_inmuebles
                WHERE uso_principal IS NOT NULL AND TRIM(uso_principal) <> ''
            """)
            usos = [r[0] for r in c_src.fetchall()]
            if not usos:
                raise RuntimeError('No se encontraron usos en db_enriquecimiento.catastro_inmuebles')

            # Asegurar tabla y función updated_at existen (idempotente si ya se ejecutaron DDL)
            c_dst.execute("""
            CREATE TABLE IF NOT EXISTS public.core_catastro_dic_uso (
                uso_principal TEXT PRIMARY KEY,
                descripcion   TEXT NOT NULL,
                fuente        TEXT NOT NULL DEFAULT 'catastro_cache',
                fecha_actualizacion TIMESTAMP NOT NULL DEFAULT NOW(),
                created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at    TIMESTAMP NOT NULL DEFAULT NOW()
            );
            """)

            # Upsert uno a uno (lista pequeña)
            for uso in usos:
                c_dst.execute(
                    """
                    INSERT INTO public.core_catastro_dic_uso (uso_principal, descripcion)
                    VALUES (%s, %s)
                    ON CONFLICT (uso_principal)
                    DO UPDATE SET descripcion = EXCLUDED.descripcion,
                                  fecha_actualizacion = NOW(),
                                  updated_at = NOW()
                    """,
                    (uso, uso)
                )
        core.commit()
        print(f"✅ Diccionario de uso actualizado: {len(usos)} entradas")
    finally:
        enr.close(); core.close()


def main():
    try:
        upsert_dic_uso()
    except Exception as e:
        print(f"❌ Error construyendo diccionarios Catastro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
