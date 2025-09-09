#!/usr/bin/env python3
"""
Script simplificado para actualizar precios_horarios_pvpc en db_sistema_electrico.
Enfoque directo: lee OMIE y calendario, calcula PVPC, inserta.
Migrado para usar datos de ESIOS API en lugar de REE.
"""

import psycopg2
from datetime import date
import sys

DB = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'admin',
    'dbname': 'db_sistema_electrico',
}

FECHA_INICIO = date(2025, 4, 1)
FECHA_FIN = date.today()

def main():
    print(f"🔄 Actualizando precios_horarios_pvpc: {FECHA_INICIO} hasta {FECHA_FIN}")
    
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    
    try:
        # 1. Verificar datos OMIE disponibles
        cur.execute("""
            SELECT COUNT(*) FROM omie_precios 
            WHERE fecha >= %s AND fecha <= %s AND zona::text = 'ES'
        """, (FECHA_INICIO, FECHA_FIN))
        omie_count = cur.fetchone()[0]
        print(f"✅ Datos OMIE disponibles: {omie_count} registros")
        
        if omie_count == 0:
            print("❌ No hay datos OMIE para actualizar")
            sys.exit(1)
        
        # 2. Obtener precios BOE vigentes (simplificado)
        sql_peajes = """
            SELECT DISTINCT ON (LOWER(REPLACE(componente, 'consumo_peaje_', '')))
                LOWER(REPLACE(componente, 'consumo_peaje_', '')) as periodo,
                precio
            FROM precio_regulado_boe
            WHERE componente LIKE 'consumo_peaje_%%'
              AND fecha_inicio <= %s
            ORDER BY LOWER(REPLACE(componente, 'consumo_peaje_', '')), fecha_inicio DESC
        """
        cur.execute(sql_peajes, (FECHA_FIN,))
        peajes = {row[0]: float(row[1]) for row in cur.fetchall()}
        
        sql_cargos = """
            SELECT DISTINCT ON (LOWER(REPLACE(componente, 'consumo_cargo_', '')))
                LOWER(REPLACE(componente, 'consumo_cargo_', '')) as periodo,
                precio
            FROM precio_regulado_boe
            WHERE componente LIKE 'consumo_cargo_%%'
              AND fecha_inicio <= %s
            ORDER BY LOWER(REPLACE(componente, 'consumo_cargo_', '')), fecha_inicio DESC
        """
        cur.execute(sql_cargos, (FECHA_FIN,))
        cargos = {row[0]: float(row[1]) for row in cur.fetchall()}
        
        print(f"   Peajes encontrados: {list(peajes.keys())}")
        print(f"   Cargos encontrados: {list(cargos.keys())}")
        
        # 3. Insertar datos combinados
        print("📝 Insertando datos PVPC...")
        
        # Query simplificada que combina todo
        cur.execute("""
            INSERT INTO precios_horarios_pvpc (fecha, hora, periodo_tarifario, 
                precio_energia, precio_peajes, precio_cargos, precio_total_pvpc)
            SELECT 
                o.fecha,
                o.hora,
                COALESCE(
                    (SELECT periodo_tarifa FROM calendario_tarifario_2025 
                     WHERE fecha = o.fecha AND hora_time = o.hora LIMIT 1),
                    CASE 
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 10 AND 13 THEN 'P1'
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 18 AND 21 THEN 'P1'
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 8 AND 9 THEN 'P2'
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 14 AND 17 THEN 'P2'
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 22 AND 23 THEN 'P2'
                        ELSE 'P3'
                    END
                ) as periodo,
                o.precio_energia,
                COALESCE(
                    CASE 
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 10 AND 13 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 18 AND 21 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 8 AND 9 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 14 AND 17 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 22 AND 23 THEN %s
                        ELSE %s
                    END, 0.0
                ) as precio_peajes,
                COALESCE(
                    CASE 
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 10 AND 13 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 18 AND 21 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 8 AND 9 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 14 AND 17 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 22 AND 23 THEN %s
                        ELSE %s
                    END, 0.0
                ) as precio_cargos,
                o.precio_energia + 
                COALESCE(
                    CASE 
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 10 AND 13 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 18 AND 21 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 8 AND 9 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 14 AND 17 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 22 AND 23 THEN %s
                        ELSE %s
                    END, 0.0
                ) + 
                COALESCE(
                    CASE 
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 10 AND 13 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 18 AND 21 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 8 AND 9 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 14 AND 17 THEN %s
                        WHEN EXTRACT(hour FROM o.hora) BETWEEN 22 AND 23 THEN %s
                        ELSE %s
                    END, 0.0
                ) as precio_total
            FROM omie_precios o
            WHERE o.fecha >= %s AND o.fecha <= %s
              AND o.zona::text = 'ES'
            ON CONFLICT (fecha, hora) DO UPDATE SET
                periodo_tarifario = EXCLUDED.periodo_tarifario,
                precio_energia = EXCLUDED.precio_energia,
                precio_peajes = EXCLUDED.precio_peajes,
                precio_cargos = EXCLUDED.precio_cargos,
                precio_total_pvpc = EXCLUDED.precio_total_pvpc
        """, (
            # Peajes P1, P1, P2, P2, P2, P3
            peajes.get('p1', 0.0), peajes.get('p1', 0.0),
            peajes.get('p2', 0.0), peajes.get('p2', 0.0), peajes.get('p2', 0.0),
            peajes.get('p3', 0.0),
            # Cargos P1, P1, P2, P2, P2, P3  
            cargos.get('p1', 0.0), cargos.get('p1', 0.0),
            cargos.get('p2', 0.0), cargos.get('p2', 0.0), cargos.get('p2', 0.0),
            cargos.get('p3', 0.0),
            # Peajes para suma total
            peajes.get('p1', 0.0), peajes.get('p1', 0.0),
            peajes.get('p2', 0.0), peajes.get('p2', 0.0), peajes.get('p2', 0.0),
            peajes.get('p3', 0.0),
            # Cargos para suma total
            cargos.get('p1', 0.0), cargos.get('p1', 0.0),
            cargos.get('p2', 0.0), cargos.get('p2', 0.0), cargos.get('p2', 0.0),
            cargos.get('p3', 0.0),
            # Fechas
            FECHA_INICIO, FECHA_FIN
        ))
        
        filas = cur.rowcount
        conn.commit()
        
        # Verificar resultado
        cur.execute("""
            SELECT MIN(fecha), MAX(fecha), COUNT(*) 
            FROM precios_horarios_pvpc 
            WHERE fecha >= %s
        """, (FECHA_INICIO,))
        min_f, max_f, total = cur.fetchone()
        
        print(f"\n✅ Actualización completada:")
        print(f"   - Filas procesadas: {filas}")
        print(f"   - Rango actualizado: {min_f} hasta {max_f}")
        print(f"   - Total registros desde abril: {total}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
