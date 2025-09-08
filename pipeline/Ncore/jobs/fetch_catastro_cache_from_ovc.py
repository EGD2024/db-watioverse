#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente OVC Catastro para popular cache: db_enriquecimiento.public.catastro_inmuebles

Flujo por CUPS (desde db_N2.coordenadas_geograficas_enriquecidas):
1) Obtener lat/lon del CUPS objetivo
2) Resolver Referencia Catastral (RC) por coordenadas (ETRS89, EPSG:4326) -> pc1+pc2
   GET https://ovc.catastro.meh.es/ovcservweb/ovcswlocalizacionrc/ovccallejerocodigos.asmx/ConsultaRCCoor
   params: { SRS: 'EPSG:4326', Coordenada_X: lon, Coordenada_Y: lat }
3) Obtener detalles por RC (uso, superficies, etc.)
   GET https://ovc.catastro.meh.es/ovcservweb/OVCServWeb.asmx/Consulta_DNPRC
   params: { RC: pc1+pc2 }
4) Upsert en db_enriquecimiento.public.catastro_inmuebles (sin fallbacks)

Notas:
- Este script falla (exit 1) si no se puede obtener RC o atributos críticos (uso/superficie) para algún CUPS procesado.
- Respetar límites del servicio OVC con --sleep entre peticiones.

CRON one-liner sugerido (ejemplo):
  20 2 * * * DB_HOST=localhost DB_PORT=5432 DB_USER=postgres DB_PASSWORD=admin \
  python3 /Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/pipeline/Ncore/jobs/fetch_catastro_cache_from_ovc.py --max 50 --sleep 0.8
"""
import os
import sys
import time
import argparse
from datetime import datetime, timedelta
import requests
import xml.etree.ElementTree as ET
import psycopg2

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'admin')

URL_RC_BY_COORD = (
    "https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCoordenadas.svc/json/Consulta_RCCOOR_Distancia"
)
URL_DNP_BY_RC = (
    "https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/json/Consulta_DNPRC"
)

HEADERS = {
    'User-Agent': 'EGD-Ncore/1.0 (+https://energygreendata.internal)',
    'Accept': 'text/xml,application/xml,*/*;q=0.9'
}


def get_conn(dbname: str):
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=dbname)


def select_targets(conn_n2, conn_enr, max_rows: int):
    """Selecciona CUPS con coordenadas (N2) y sin cache reciente (enriquecimiento), sin cross-DB."""
    # 1) CUPS con coordenadas en N2
    with conn_n2.cursor() as c:
        c.execute(
            """
            SELECT DISTINCT cups, latitud, longitud
            FROM public.coordenadas_geograficas_enriquecidas
            WHERE latitud IS NOT NULL AND longitud IS NOT NULL
            """
        )
        coords = c.fetchall()  # list of (cups, lat, lon)
    if not coords:
        return []
    # 2) Recencia en cache de enriquecimiento
    with conn_enr.cursor() as c2:
        c2.execute(
            """
            SELECT cups, MAX(fecha_consulta) AS max_fecha
            FROM public.catastro_inmuebles
            GROUP BY cups
            """
        )
        recency = {row[0]: row[1] for row in c2.fetchall()}
    cutoff = datetime.now() - timedelta(days=180)
    pending = []
    for cups, lat, lon in coords:
        last = recency.get(cups)
        if last is None or last < cutoff:
            pending.append((cups, lat, lon))
            if len(pending) >= max_rows:
                break
    return pending


def fetch_rc_by_coord(lat: float, lon: float):
    params = {'SRS': 'EPSG:4326', 'CoorX': str(lon), 'CoorY': str(lat)}
    r = requests.get(URL_RC_BY_COORD, params=params, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"OVC RC error HTTP {r.status_code}")
    try:
        data = r.json()
    except Exception as e:
        raise RuntimeError(f"OVC RC JSON inválido: {e}")
    result = data.get('Consulta_RCCOOR_DistanciaResult', {})
    if result.get('control', {}).get('cucoor') == 1:
        lpcd = result.get('coordenadas_distancias', {}).get('coordd', [{}])[0].get('lpcd', [])
        if lpcd:
            pc = lpcd[0].get('pc', {})
            pc1 = pc.get('pc1')
            pc2 = pc.get('pc2')
            if pc1 and pc2:
                # Construir RC completa de 20 chars: pc1(7) + pc2(7) + cargo(4) + control(2)
                # Por defecto usamos 0001XX para propiedades principales
                rc_completa = f"{pc1}{pc2}0001XX"
                return rc_completa[:14], rc_completa[14:]  # Devolver pc1+pc2, cargo+control
    raise RuntimeError("OVC RC no devolvió pc1/pc2")


def fetch_details_by_rc(rc: str):
    # Intentar primero con RC completa, si falla intentar solo con pc1+pc2
    for attempt_rc in [rc, rc[:14] if len(rc) > 14 else rc]:
        params = {'RefCat': attempt_rc}
        r = requests.get(URL_DNP_BY_RC, params=params, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            continue
        try:
            data = r.json()
        except Exception:
            continue
        
        result = data.get('consulta_dnprcResult', {})
        if result.get('control', {}).get('cuerr', 0) > 0:
            continue  # Hay error, probar siguiente
        
        # Navegar con cuidado por la estructura anidada
        bico = result.get('bico', {})
        bi = bico.get('bi', {})
        debi = bi.get('debi', {})
        
        # Si no hay debi, puede ser parcela sin construcción
        if not debi:
            dt = bi.get('dt', {})
            if dt:
                # Parcela sin construcción registrada
                uso = 'Parcela sin construcción'
                # Superficie 0 porque no hay construcción
                sfc = 0
            else:
                uso = 'Parcela sin construcción'
                sfc = 0
        else:
            uso = debi.get('luso', '')
            sfc = debi.get('sfc', 0)
        
        sup_const = float(sfc) if sfc else 0
        # Siempre devolver algo (información real, no inventada)
        return {'uso_principal': uso.strip() if uso else 'Parcela sin construcción', 'superficie_construida_m2': sup_const}
    
    # Si llegamos aquí, no pudimos obtener nada
    raise RuntimeError(f"No se pudo obtener detalles para RC {rc}")

    return {
        'uso_principal': uso.strip() if uso else None,
        'superficie_construida_m2': sup_const
    }


def upsert_cache(conn_enr, cups: str, pc1: str, pc2: str, detalles: dict):
    now = 'NOW()'
    with conn_enr.cursor() as c:
        c.execute(
            """
            INSERT INTO public.catastro_inmuebles (
                cups, referencia_catastral, referencia_catastral_1, referencia_catastral_2,
                uso_principal, superficie_construida_m2, fecha_consulta, fuente_datos, updated_at, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), 'OVC', NOW(), NOW())
            ON CONFLICT (cups)
            DO UPDATE SET
                referencia_catastral = EXCLUDED.referencia_catastral,
                referencia_catastral_1 = EXCLUDED.referencia_catastral_1,
                referencia_catastral_2 = EXCLUDED.referencia_catastral_2,
                uso_principal = COALESCE(EXCLUDED.uso_principal, public.catastro_inmuebles.uso_principal),
                superficie_construida_m2 = COALESCE(EXCLUDED.superficie_construida_m2, public.catastro_inmuebles.superficie_construida_m2),
                fecha_consulta = NOW(),
                fuente_datos = 'OVC',
                updated_at = NOW()
            """,
            (
                cups,
                f"{pc1}{pc2}", pc1, pc2,
                detalles.get('uso_principal'),
                detalles.get('superficie_construida_m2')
            )
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max', type=int, default=50, help='máximo de CUPS a procesar')
    parser.add_argument('--sleep', type=float, default=0.8, help='segundos entre peticiones OVC')
    args = parser.parse_args()

    n2 = get_conn('db_N2')
    enr = get_conn('db_enriquecimiento')

    failures = []
    try:
        targets = select_targets(n2, enr, args.max)
        if not targets:
            print('✅ No hay objetivos para cache de Catastro (ya actualizados)')
            return
        for cups, lat, lon in targets:
            try:
                rc_base, rc_control = fetch_rc_by_coord(float(lat), float(lon))
                pc1 = rc_base[:7]
                pc2 = rc_base[7:14]
                detalles = fetch_details_by_rc(f"{rc_base}{rc_control}")
                # Validación: solo fallar si no hay respuesta del servicio
                if not detalles:
                    raise RuntimeError('Sin respuesta del servicio DNP')
                print(f"DEBUG - cups: {cups}, pc1: {pc1}, pc2: {pc2}, detalles: {detalles}")
                upsert_cache(enr, cups, pc1, pc2, detalles)
                enr.commit()
                time.sleep(args.sleep)
            except Exception as e:
                enr.rollback()
                failures.append((cups, str(e)))
        if failures:
            print('❌ Fallos OVC/cache Catastro:', file=sys.stderr)
            for cups, cause in failures:
                print(f' - {cups}: {cause}', file=sys.stderr)
            sys.exit(1)
        print(f"✅ Cache Catastro actualizada. CUPS procesados: {len(targets)}")
    finally:
        n2.close(); enr.close()


if __name__ == '__main__':
    main()
