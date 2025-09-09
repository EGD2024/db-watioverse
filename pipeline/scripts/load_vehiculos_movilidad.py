#!/usr/bin/env python3
"""
Script para cargar datos de vehículos IDAE en db_movilidad
Fuente: https://coches.idae.es/storage/csv/idae-historico-202413.csv
"""

import pandas as pd
import psycopg2
import requests
from datetime import datetime
import sys
import os

# Configuración BD movilidad
DB_CONFIG = {
    'host': 'localhost',
    'database': 'db_movilidad',
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': 5432
}

def download_idae_csv(local_file="/tmp/idae-historico-202411.csv"):
    """Usa el archivo CSV local de IDAE"""
    print(f"📁 Usando archivo local IDAE: {local_file}")
    
    try:
        if os.path.exists(local_file):
            print(f"✅ Archivo encontrado: {os.path.getsize(local_file)} bytes")
            return local_file
        else:
            print(f"❌ Archivo no encontrado: {local_file}")
            return None
        
    except Exception as e:
        print(f"❌ Error accediendo archivo local: {e}")
        return None

def classify_propulsion(motorizacion):
    """Clasifica el tipo de propulsión basado en motorización"""
    if not motorizacion:
        return 'DESCONOCIDO'
    
    mot = motorizacion.upper()
    
    if 'ELÉCTRICOS PUROS' in mot or 'ELECTRICO' in mot:
        return 'ELECTRICO'
    elif 'HÍBRIDOS ENCHUFABLES' in mot or 'PLUG-IN' in mot:
        return 'HIBRIDO_ENCHUFABLE'
    elif 'HÍBRIDO' in mot or 'HIBRIDO' in mot:
        return 'HIBRIDO'
    else:
        return 'COMBUSTION'

def calculate_efficiency_label(emisiones_co2):
    """Calcula etiqueta eficiencia A-G según emisiones CO2"""
    if pd.isna(emisiones_co2) or emisiones_co2 == 0:
        return 'A'  # Eléctricos puros
    
    if emisiones_co2 < 50:
        return 'A'
    elif emisiones_co2 < 75:
        return 'B'
    elif emisiones_co2 < 100:
        return 'C'
    elif emisiones_co2 < 120:
        return 'D'
    elif emisiones_co2 < 140:
        return 'E'
    elif emisiones_co2 < 160:
        return 'F'
    else:
        return 'G'

def calculate_category_efficiency(score_total):
    """Calcula categoría de eficiencia basada en score total"""
    if score_total >= 80:
        return 'ALTA'
    elif score_total >= 50:
        return 'MEDIA'
    else:
        return 'BAJA'

def calculate_scores(df):
    """Calcula scores de movilidad 0-100"""
    
    # Limpiar datos para cálculos
    df['emisiones_co2_mixto_wltp_min'] = pd.to_numeric(df['emisionies_co2_mixto_wltp_min'], errors='coerce').fillna(0)
    df['consumo_mixto_wltp'] = pd.to_numeric(df['consumo_mixto_wltp'], errors='coerce').fillna(0)
    df['autonomia_electrica'] = pd.to_numeric(df['autonomia_electrica'], errors='coerce').fillna(0)
    
    # Score emisiones (invertido: menos emisiones = mejor score)
    max_emisiones = df['emisiones_co2_mixto_wltp_min'].max()
    if max_emisiones > 0:
        df['score_emisiones'] = ((max_emisiones - df['emisiones_co2_mixto_wltp_min']) / max_emisiones * 100).round().astype(int)
    else:
        df['score_emisiones'] = 100
    
    # Score consumo (invertido: menos consumo = mejor score)
    max_consumo = df['consumo_mixto_wltp'].max()
    if max_consumo > 0:
        df['score_consumo'] = ((max_consumo - df['consumo_mixto_wltp']) / max_consumo * 100).round().astype(int)
    else:
        df['score_consumo'] = 100
    
    # Score autonomía (directo: más autonomía = mejor score)
    max_autonomia = df['autonomia_electrica'].max()
    if max_autonomia > 0:
        df['score_autonomia'] = (df['autonomia_electrica'] / max_autonomia * 100).round().astype(int)
    else:
        df['score_autonomia'] = 0
    
    # Score total ponderado: 40% emisiones + 30% consumo + 20% autonomía + 10% eficiencia
    eficiencia_scores = {'A': 100, 'B': 85, 'C': 70, 'D': 55, 'E': 40, 'F': 25, 'G': 10}
    df['score_eficiencia'] = df['eficiencia_energetica'].map(eficiencia_scores).fillna(50)
    
    df['score_movilidad_total'] = (
        df['score_emisiones'] * 0.4 +
        df['score_consumo'] * 0.3 +
        df['score_autonomia'] * 0.2 +
        df['score_eficiencia'] * 0.1
    ).round().astype(int)
    
    # Categoría eficiencia basada en score total
    df['categoria_eficiencia'] = df['score_movilidad_total'].apply(calculate_category_efficiency)
    
    return df

def process_csv_data(csv_file):
    """Procesa el CSV y calcula campos derivados"""
    print("🔄 Procesando datos CSV...")
    
    try:
        # Leer CSV
        df = pd.read_csv(csv_file, encoding='utf-8')
        print(f"📊 Registros leídos: {len(df)}")
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Convertir fechas (manejar NaT correctamente)
        date_cols = ['fecha_alta', 'fecha_actualizacion', 'fecha_comercializacion']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
                # Convertir NaT a None para PostgreSQL
                df[col] = df[col].where(pd.notnull(df[col]), None)
        
        # Calcular campos derivados
        df['tipo_propulsion'] = df['motorizacion'].apply(classify_propulsion)
        df['eficiencia_energetica'] = df['emisionies_co2_mixto_wltp_min'].apply(calculate_efficiency_label)
        
        # Normalizar segmento
        df['segmento_normalizado'] = df['segmento'].str.upper().str.strip()
        
        # Calcular scores
        df = calculate_scores(df)
        
        # Limpiar valores nulos críticos
        df['marca'] = df['marca'].fillna('DESCONOCIDO')
        df['modelo'] = df['modelo'].fillna('DESCONOCIDO')
        df['vehiculo'] = df['vehiculo'].fillna('DESCONOCIDO')
        df['motorizacion'] = df['motorizacion'].fillna('DESCONOCIDO')
        
        print(f"✅ Procesamiento completado: {len(df)} registros")
        return df
        
    except Exception as e:
        print(f"❌ Error procesando CSV: {e}")
        return None

def create_table_if_not_exists(conn):
    """Crea la tabla si no existe"""
    print("🗄️ Verificando/creando tabla core_vehiculos_espana...")
    
    try:
        cur = conn.cursor()
        
        # Leer y ejecutar script de creación
        sql_file = '/Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/sql/create_vehiculos_movilidad.sql'
        with open(sql_file, 'r', encoding='utf-8') as f:
            create_sql = f.read()
            cur.execute(create_sql)
        
        conn.commit()
        cur.close()
        print("✅ Tabla verificada/creada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error creando tabla: {e}")
        return False

def load_to_database(df):
    """Carga datos procesados en db_movilidad"""
    print("💾 Cargando datos en db_movilidad...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Crear tabla si no existe
        if not create_table_if_not_exists(conn):
            return 0
        
        cur = conn.cursor()
        
        # Preparar datos para inserción
        insert_sql = """
        INSERT INTO core_vehiculos_espana (
            fecha_alta, fecha_actualizacion, fecha_comercializacion,
            marca, modelo, vehiculo, segmento, motorizacion, categoria, mtma,
            consumo_nedc, emisiones_nedc,
            consumo_mixto_wltp_min, consumo_mixto_wltp_max, consumo_mixto_wltp,
            emisiones_co2_mixto_wltp_min, emisiones_co2_mixto_wltp_max,
            autonomia_electrica, consumo_electrico, observaciones,
            eficiencia_energetica, score_emisiones, score_consumo, 
            score_autonomia, score_movilidad_total, tipo_propulsion, 
            categoria_eficiencia, segmento_normalizado
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (marca, modelo, vehiculo, motorizacion) 
        DO UPDATE SET
            fecha_actualizacion_score = CURRENT_TIMESTAMP,
            score_emisiones = EXCLUDED.score_emisiones,
            score_consumo = EXCLUDED.score_consumo,
            score_autonomia = EXCLUDED.score_autonomia,
            score_movilidad_total = EXCLUDED.score_movilidad_total,
            categoria_eficiencia = EXCLUDED.categoria_eficiencia
        """
        
        # Insertar por lotes
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            values = []
            for _, row in batch.iterrows():
                # Convertir valores None/NaN a None explícitamente
                def safe_get(key, default=None):
                    val = row.get(key, default)
                    return None if pd.isna(val) else val
                
                values.append((
                    safe_get('fecha_alta'), safe_get('fecha_actualizacion'), safe_get('fecha_comercializacion'),
                    safe_get('marca', 'DESCONOCIDO'), safe_get('modelo', 'DESCONOCIDO'), 
                    safe_get('vehiculo', 'DESCONOCIDO'), safe_get('segmento'), 
                    safe_get('motorizacion', 'DESCONOCIDO'), safe_get('categoria'), safe_get('mtma'),
                    safe_get('consumo_nedc'), safe_get('emisiones_nedc'),
                    safe_get('consumo_mixto_wltp_min'), safe_get('consumo_mixto_wltp_max'), safe_get('consumo_mixto_wltp'),
                    safe_get('emisiones_co2_mixto_wltp_min'), safe_get('emisionies_co2_mixto_wltp_max'),
                    safe_get('autonomia_electrica'), safe_get('consumo_electrico'), safe_get('observaciones'),
                    safe_get('eficiencia_energetica', 'G'), safe_get('score_emisiones', 0), safe_get('score_consumo', 0),
                    safe_get('score_autonomia', 0), safe_get('score_movilidad_total', 0), safe_get('tipo_propulsion', 'DESCONOCIDO'),
                    safe_get('categoria_eficiencia', 'BAJA'), safe_get('segmento_normalizado')
                ))
            
            cur.executemany(insert_sql, values)
            total_inserted += len(values)
            print(f"📥 Insertados: {total_inserted}/{len(df)} registros")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Carga completada: {total_inserted} registros en db_movilidad.core_vehiculos_espana")
        return total_inserted
        
    except Exception as e:
        print(f"❌ Error cargando en BD: {e}")
        return 0

def main():
    """Función principal"""
    print("🚗 Iniciando carga de datos IDAE vehículos en db_movilidad")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Descargar CSV
    csv_file = download_idae_csv()
    if not csv_file:
        sys.exit(1)
    
    # Procesar datos
    df = process_csv_data(csv_file)
    if df is None:
        sys.exit(1)
    
    # Cargar en BD
    total_loaded = load_to_database(df)
    
    # Limpiar archivo temporal
    if os.path.exists(csv_file):
        os.remove(csv_file)
    
    print(f"🎯 RESUMEN FINAL:")
    print(f"   • Base de datos: db_movilidad")
    print(f"   • Tabla: core_vehiculos_espana")
    print(f"   • Registros procesados: {len(df)}")
    print(f"   • Registros cargados: {total_loaded}")
    print(f"   • Tipos propulsión: {df['tipo_propulsion'].value_counts().to_dict()}")
    print(f"   • Etiquetas eficiencia: {df['eficiencia_energetica'].value_counts().to_dict()}")
    print(f"   • Categorías eficiencia: {df['categoria_eficiencia'].value_counts().to_dict()}")
    print(f"✅ Proceso completado exitosamente en db_movilidad")

if __name__ == "__main__":
    main()
