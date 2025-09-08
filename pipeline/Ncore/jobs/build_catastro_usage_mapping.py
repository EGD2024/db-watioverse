#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Construye el mapeo uso_principal (Catastro) -> categoria_escore en db_Ncore.

- Lee todos los usos desde db_Ncore.public.core_catastro_dic_uso
- Asigna categoria_escore por reglas deterministas (sin heurística difusa)
- Si queda algún uso sin mapear, el script falla (exit 1) listando los pendientes
- Upsert en public.core_catastro_map_uso_escore (PRIMARY KEY: uso_principal)

CRON one-liner sugerido (ejemplo):
  27 2 * * * DB_HOST=localhost DB_PORT=5432 DB_USER=postgres DB_PASSWORD=admin \
  python3 /Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/pipeline/Ncore/jobs/build_catastro_usage_mapping.py
"""
import os
import sys
import re
import unicodedata
import psycopg2

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'admin')


def get_conn(dbname: str):
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=dbname)


def _normalize(s: str) -> str:
    s = s.strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r"\s+", " ", s)
    return s

# Reglas deterministas: patrones contenidos obligatorios
RULES = [
    (['vivienda unifamiliar', 'unifamiliar', 'adosado', 'pareado', 'chalet'], 'vivienda_unifamiliar'),
    (['vivienda plurifamiliar', 'plurifamiliar', 'residencial colectivo', 'vivienda colectiva', 'bloque'], 'vivienda_plurifamiliar'),
    (['local', 'comercial', 'tienda', 'hosteleria', 'restaurante', 'bar'], 'comercial'),
    (['oficina', 'oficinas'], 'oficinas'),
    (['nave', 'industrial', 'fabrica'], 'industrial'),
    (['almacen', 'almacenaje'], 'almacen'),
    (['garaje', 'aparcamiento'], 'garaje'),
    (['trastero'], 'trastero'),
    (['hotel', 'hostal', 'alojamiento'], 'hotelero'),
    (['sanitario', 'hospital', 'clinica', 'centro de salud'], 'sanitario'),
    (['educativo', 'colegio', 'universidad', 'escuela', 'instituto'], 'educativo'),
    (['deportivo', 'polideportivo'], 'deportivo'),
    (['equipamiento', 'dotacional', 'religioso', 'administrativo', 'cuartel', 'ayuntamiento', 'juzgado'], 'equipamiento'),
    (['agrario', 'agricola', 'ganadero', 'explotacion'], 'agropecuario'),
    (['ocio', 'espectaculo', 'cultural', 'teatro', 'cine', 'museo'], 'ocio_cultural'),
]

# Mapeos exactos conocidos (antes de reglas por patrones)
EXACT = {
    'residencial': 'vivienda_plurifamiliar',
    'residencial unifamiliar': 'vivienda_unifamiliar',
    'residencial colectivo': 'vivienda_plurifamiliar',
}


def categorize(uso: str) -> str | None:
    n = _normalize(uso)
    if n in EXACT:
        return EXACT[n]
    for pats, cat in RULES:
        if all(p in n for p in pats):
            return cat
        # También consideramos coincidencia de cualquiera de los términos (más laxa pero explícita)
        if any(p in n for p in pats):
            return cat
    return None


def main():
    core = get_conn('db_Ncore')
    try:
        with core.cursor() as c:
            # Obtener usos
            c.execute("SELECT uso_principal FROM public.core_catastro_dic_uso ORDER BY uso_principal")
            usos = [r[0] for r in c.fetchall()]
            if not usos:
                raise RuntimeError('No hay usos en core_catastro_dic_uso. Ejecute build_catastro_dictionaries.py primero.')

            pendientes = []
            mapped = {}
            for uso in usos:
                categoria = categorize(uso)
                if not categoria:
                    pendientes.append(uso)
                else:
                    mapped[uso] = categoria

            if pendientes:
                # Sin fallbacks: listamos y fallamos para que se complete el mapeo explícitamente
                print('❌ Usos sin mapeo (complete las reglas o EXACT en el script):', file=sys.stderr)
                for u in pendientes:
                    print(f' - {u}', file=sys.stderr)
                sys.exit(1)

            # Asegurar tabla existe (idempotente)
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS public.core_catastro_map_uso_escore (
                    uso_principal TEXT PRIMARY KEY,
                    categoria_escore TEXT NOT NULL,
                    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            # Upserts
            for uso, cat in mapped.items():
                c.execute(
                    """
                    INSERT INTO public.core_catastro_map_uso_escore (uso_principal, categoria_escore)
                    VALUES (%s, %s)
                    ON CONFLICT (uso_principal)
                    DO UPDATE SET categoria_escore = EXCLUDED.categoria_escore,
                                  fecha_actualizacion = NOW(),
                                  updated_at = NOW()
                    """,
                    (uso, cat)
                )
        core.commit()
        print(f"✅ core_catastro_map_uso_escore actualizado: {len(mapped)} usos mapeados")
    finally:
        core.close()


if __name__ == '__main__':
    main()
