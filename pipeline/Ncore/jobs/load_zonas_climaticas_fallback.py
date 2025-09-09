#!/usr/bin/env python3
"""
Script de carga de zonas climáticas con datos aproximados cuando Open-Meteo está limitado.
Usa valores HDD/CDD típicos por zona climática CTE para completar registros pendientes.
"""

import psycopg2
import argparse
from datetime import datetime

# Valores HDD/CDD aproximados por zona CTE (basados en normativa)
VALORES_APROXIMADOS_CTE = {
    'A3': {'hdd': 0, 'cdd': 1200},      # Canarias costa
    'A4': {'hdd': 0, 'cdd': 1500},      # Canarias interior
    'B3': {'hdd': 200, 'cdd': 800},     # Mediterráneo costa
    'B4': {'hdd': 300, 'cdd': 1000},    # Mediterráneo interior bajo
    'C1': {'hdd': 800, 'cdd': 200},     # Atlántico norte
    'C2': {'hdd': 1000, 'cdd': 300},    # Atlántico interior
    'C3': {'hdd': 600, 'cdd': 600},     # Mediterráneo templado
    'C4': {'hdd': 800, 'cdd': 800},     # Mediterráneo continental
    'D1': {'hdd': 1500, 'cdd': 100},    # Continental norte
    'D2': {'hdd': 1800, 'cdd': 200},    # Continental medio
    'D3': {'hdd': 1200, 'cdd': 400},    # Continental sur
    'E1': {'hdd': 2500, 'cdd': 50},     # Montaña
}

def get_db_connection():
    """Crear conexión a db_Ncore."""
    return psycopg2.connect(
        host="localhost",
        database="db_Ncore",
        user="postgres",
        password="Judini2024!"
    )

def get_zona_cte(conn, provincia: str, altitud: float) -> str:
    """Obtener zona CTE según provincia y altitud."""
    cursor = conn.cursor()
    
    # Mapeo de nombres de provincia (mismo que script original)
    provincia_normalizada = provincia
    if provincia in ["A Coruña", "La Coruña", "Coruña"]:
        provincia_normalizada = "Coruña, A"
    elif provincia in ["Alicante", "Alacant", "Alicante/Alacant"]:
        provincia_normalizada = "Alicante/Alacant"
    elif provincia in ["Castellón", "Castelló", "Castellón/Castelló"]:
        provincia_normalizada = "Castellón/Castelló"
    elif provincia in ["Valencia", "València", "Valencia/València"]:
        provincia_normalizada = "Valencia/València"
    elif provincia in ["Lleida", "Lérida"]:
        provincia_normalizada = "Lleida"
    elif provincia in ["Álava", "Alava", "Araba", "Araba/Álava"]:
        provincia_normalizada = "Araba/Álava"
    elif provincia in ["Vizcaya", "Bizkaia", "Viscaya"]:
        provincia_normalizada = "Bizkaia"
    elif provincia in ["Guipúzcoa", "Gipuzkoa", "Guipuzcoa"]:
        provincia_normalizada = "Gipuzkoa"
    elif provincia in ["Baleares", "Islas Baleares", "Illes Balears"]:
        provincia_normalizada = "Illes Balears"
    elif provincia in ["Las Palmas", "Palmas, Las"]:
        provincia_normalizada = "Las Palmas"
    elif provincia in ["Santa Cruz de Tenerife", "Tenerife", "S.C. Tenerife"]:
        provincia_normalizada = "Santa Cruz de Tenerife"
    elif provincia in ["Asturias", "Principado de Asturias"]:
        provincia_normalizada = "Asturias"
    elif provincia in ["Cantabria", "Santander"]:
        provincia_normalizada = "Cantabria"
    elif provincia in ["La Rioja", "Rioja", "Logroño"]:
        provincia_normalizada = "La Rioja"
    elif provincia in ["Navarra", "Nafarroa"]:
        provincia_normalizada = "Navarra"
    elif provincia in ["Ourense", "Orense"]:
        provincia_normalizada = "Ourense"
    
    cursor.execute("""
        SELECT zona_climatica_cte 
        FROM core_zonas_cte_reglas
        WHERE provincia = %s 
          AND %s >= h_min 
          AND %s <= h_max
        LIMIT 1
    """, (provincia_normalizada, altitud, altitud))
    
    result = cursor.fetchone()
    cursor.close()
    
    if not result:
        raise RuntimeError(f"No hay regla CTE para provincia '{provincia_normalizada}' altitud {altitud}m")
    
    return result[0]

def load_fallback_data():
    """Cargar datos aproximados para CPs sin procesar."""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener CPs sin datos climáticos
        cursor.execute("""
            SELECT cp.codigo_postal, cp.municipio, cp.provincia, 
                   COALESCE(cp.altitud_media, 200) as altitud
            FROM core_codigos_postales cp
            LEFT JOIN core_zonas_climaticas zc ON cp.codigo_postal = zc.codigo_postal
            WHERE zc.codigo_postal IS NULL
            ORDER BY cp.codigo_postal
        """)
        
        cps_pendientes = cursor.fetchall()
        total = len(cps_pendientes)
        
        if total == 0:
            print("✅ Todos los CPs ya tienen datos climáticos")
            return
            
        print(f"📊 Procesando {total} CPs con datos aproximados...")
        
        procesados = 0
        errores = 0
        
        for cp, municipio, provincia, altitud in cps_pendientes:
            try:
                # Obtener zona CTE
                zona_cte = get_zona_cte(conn, provincia, altitud)
                
                # Obtener valores aproximados
                if zona_cte not in VALORES_APROXIMADOS_CTE:
                    print(f"⚠️  Zona CTE desconocida: {zona_cte} para {cp}")
                    zona_cte = 'C3'  # Fallback a zona templada
                
                valores = VALORES_APROXIMADOS_CTE[zona_cte]
                
                # Insertar datos aproximados
                cursor.execute("""
                    INSERT INTO core_zonas_climaticas 
                    (codigo_postal, municipio, provincia, latitud, longitud, 
                     altitud_real, hdd_18, cdd_18, zona_climatica_cte, 
                     fecha_calculo, metodo_calculo)
                    VALUES (%s, %s, %s, 0, 0, %s, %s, %s, %s, %s, 'aproximado')
                """, (
                    cp, municipio, provincia, altitud,
                    valores['hdd'], valores['cdd'], zona_cte,
                    datetime.now(), 
                ))
                
                procesados += 1
                
                if procesados % 100 == 0:
                    conn.commit()
                    print(f"📈 Procesados: {procesados}/{total} ({procesados/total*100:.1f}%)")
                    
            except Exception as e:
                errores += 1
                print(f"❌ Error {cp} ({municipio}): {e}")
                continue
        
        conn.commit()
        
        print(f"\n✅ Proceso completado:")
        print(f"   Procesados: {procesados}")
        print(f"   Errores: {errores}")
        print(f"   Total: {procesados + errores}")
        print(f"\n⚠️  NOTA: Datos aproximados basados en zona CTE")
        print(f"   Ejecutar script real mañana para datos precisos")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Carga datos climáticos aproximados')
    parser.add_argument('--confirmar', action='store_true', 
                       help='Confirmar carga de datos aproximados')
    
    args = parser.parse_args()
    
    if not args.confirmar:
        print("⚠️  Este script carga datos APROXIMADOS por límite Open-Meteo")
        print("   Usar solo temporalmente hasta mañana")
        print("   Ejecutar con --confirmar para proceder")
        return
    
    load_fallback_data()

if __name__ == "__main__":
    main()
