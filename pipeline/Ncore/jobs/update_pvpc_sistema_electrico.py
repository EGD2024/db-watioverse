#!/usr/bin/env python3
"""
Actualiza precios_horarios_pvpc en db_sistema_electrico desde abril 2025 hasta hoy.
Basado en motor_mejora/src/utils/rellenar_precios_horarios_pvpc.py pero adaptado para:
- Conectar a db_sistema_electrico
- Procesar solo el rango faltante (abril-septiembre 2025)
- Usar las tablas correctas del sistema eléctrico
"""

import psycopg2
import psycopg2.extras
from datetime import datetime, date
from tqdm import tqdm
import sys

DB_SISTEMA_ELECTRICO = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'admin',
    'dbname': 'db_sistema_electrico',
}

# Rango a actualizar: desde donde está parado hasta hoy
FECHA_INICIO = date(2025, 4, 1)
FECHA_FIN = date.today()

def main():
    print(f"🔄 Actualizando precios_horarios_pvpc en db_sistema_electrico")
    print(f"   Rango: {FECHA_INICIO} hasta {FECHA_FIN}")
    
    conn = psycopg2.connect(**DB_SISTEMA_ELECTRICO)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Verificar si tenemos los datos fuente necesarios
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM omie_precios 
            WHERE fecha >= %s AND fecha <= %s
        """, (FECHA_INICIO, FECHA_FIN))
        omie_count = cur.fetchone()['total']
        
        if omie_count == 0:
            print("❌ No hay datos en omie_precios para el rango solicitado")
            print("   Necesitas actualizar primero omie_precios desde fuentes externas")
            sys.exit(1)
        
        print(f"✅ Encontrados {omie_count} registros en omie_precios")
        
        # Verificar calendario tarifario
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM calendario_tarifario 
            WHERE fecha >= %s AND fecha <= %s
        """, (FECHA_INICIO, FECHA_FIN))
        cal_count = cur.fetchone()['total']
        
        if cal_count == 0:
            print("⚠️  No hay calendario_tarifario para 2025, intentando con tablas anuales...")
            # Verificar tabla específica 2025
            cur.execute("""
                SELECT COUNT(*) as total 
                FROM calendario_tarifario_2025 
                WHERE fecha >= %s AND fecha <= %s
            """, (FECHA_INICIO, FECHA_FIN))
            cal_count = cur.fetchone()['total']
            
            if cal_count > 0:
                calendario_tabla = "calendario_tarifario_2025"
                print(f"✅ Usando {calendario_tabla}: {cal_count} registros")
            else:
                print("❌ No hay calendario tarifario disponible para 2025")
                sys.exit(1)
        else:
            calendario_tabla = "calendario_tarifario"
            print(f"✅ Usando calendario_tarifario: {cal_count} registros")
        
        # Consulta principal para obtener los datos
        consulta = f"""
            WITH calendario AS (
                SELECT fecha, hora_time as hora, periodo_tarifa
                FROM {calendario_tabla}
                WHERE fecha >= %s AND fecha <= %s
            ),
            energia AS (
                SELECT fecha, hora, precio_energia
                FROM omie_precios
                WHERE fecha >= %s AND fecha <= %s
                  AND zona::text = 'ES'
            ),
            peajes AS (
                SELECT DISTINCT ON (periodo)
                    LOWER(REPLACE(componente, 'consumo_peaje_', '')) as periodo,
                    precio as precio_peaje,
                    fecha_inicio,
                    COALESCE(fecha_fin, '9999-12-31'::date) as fecha_fin
                FROM precio_regulado_boe
                WHERE componente LIKE 'consumo_peaje_%'
                ORDER BY periodo, fecha_inicio DESC
            ),
            cargos AS (
                SELECT DISTINCT ON (periodo)
                    LOWER(REPLACE(componente, 'consumo_cargo_', '')) as periodo,
                    precio as precio_cargo,
                    fecha_inicio,
                    COALESCE(fecha_fin, '9999-12-31'::date) as fecha_fin
                FROM precio_regulado_boe
                WHERE componente LIKE 'consumo_cargo_%'
                ORDER BY periodo, fecha_inicio DESC
            )
            SELECT 
                c.fecha,
                c.hora,
                c.periodo_tarifa,
                COALESCE(e.precio_energia, 0.0) as precio_energia,
                COALESCE(p.precio_peaje, 0.0) as precio_peajes,
                COALESCE(cr.precio_cargo, 0.0) as precio_cargos,
                COALESCE(e.precio_energia, 0.0) + 
                COALESCE(p.precio_peaje, 0.0) + 
                COALESCE(cr.precio_cargo, 0.0) as precio_total_pvpc
            FROM calendario c
            LEFT JOIN energia e ON c.fecha = e.fecha AND c.hora = e.hora
            LEFT JOIN peajes p ON LOWER(c.periodo_tarifa) = p.periodo
                AND c.fecha BETWEEN p.fecha_inicio AND p.fecha_fin
            LEFT JOIN cargos cr ON LOWER(c.periodo_tarifa) = cr.periodo
                AND c.fecha BETWEEN cr.fecha_inicio AND cr.fecha_fin
            ORDER BY c.fecha, c.hora
        """
        
        print("📊 Ejecutando consulta de datos...")
        # Debug: verificar la consulta antes de ejecutar
        print(f"   Tabla calendario: {calendario_tabla}")
        print(f"   Parámetros: {FECHA_INICIO}, {FECHA_FIN}")
        
        try:
            # La consulta necesita 4 parámetros: 2 para calendario y 2 para energia
            cur.execute(consulta, (FECHA_INICIO, FECHA_FIN, FECHA_INICIO, FECHA_FIN))
            rows = cur.fetchall()
        except Exception as e:
            print(f"❌ Error en consulta SQL: {e}")
            print("   Verificando estructura de tablas...")
            
            # Verificar que las columnas existen
            cur.execute(f"SELECT * FROM {calendario_tabla} LIMIT 1")
            sample_cal = cur.fetchone()
            print(f"   Columnas calendario: {list(sample_cal.keys()) if sample_cal else 'N/A'}")
            
            cur.execute("SELECT * FROM omie_precios WHERE zona='ES' LIMIT 1")
            sample_omie = cur.fetchone()
            print(f"   Columnas omie: {list(sample_omie.keys()) if sample_omie else 'N/A'}")
            
            raise
        
        if not rows:
            print("❌ No se obtuvieron datos de la consulta")
            sys.exit(1)
        
        print(f"📝 Insertando {len(rows)} registros en precios_horarios_pvpc...")
        
        # Insertar/actualizar los datos
        inserted = 0
        updated = 0
        
        for row in tqdm(rows, desc="Actualizando PVPC"):
            cur.execute("""
                INSERT INTO precios_horarios_pvpc (
                    fecha, hora, periodo_tarifario,
                    precio_energia, precio_peajes, precio_cargos, precio_total_pvpc
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (fecha, hora) DO UPDATE SET
                    periodo_tarifario = EXCLUDED.periodo_tarifario,
                    precio_energia = EXCLUDED.precio_energia,
                    precio_peajes = EXCLUDED.precio_peajes,
                    precio_cargos = EXCLUDED.precio_cargos,
                    precio_total_pvpc = EXCLUDED.precio_total_pvpc
                RETURNING (xmax = 0) AS inserted
            """, (
                row['fecha'], row['hora'], row['periodo_tarifa'],
                row['precio_energia'], row['precio_peajes'], 
                row['precio_cargos'], row['precio_total_pvpc']
            ))
            
            result = cur.fetchone()
            if result and result['inserted']:
                inserted += 1
            else:
                updated += 1
        
        conn.commit()
        
        # Verificar resultado final
        cur.execute("""
            SELECT MIN(fecha) as min_fecha, MAX(fecha) as max_fecha, COUNT(*) as total
            FROM precios_horarios_pvpc
            WHERE fecha >= %s
        """, (FECHA_INICIO,))
        
        final = cur.fetchone()
        print(f"\n✅ Actualización completada:")
        print(f"   - Nuevos registros: {inserted}")
        print(f"   - Actualizados: {updated}")
        print(f"   - Rango final: {final['min_fecha']} hasta {final['max_fecha']}")
        print(f"   - Total registros desde abril: {final['total']}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
