#!/usr/bin/env python3
"""
Script para cargar datos de vehículos IDAE en la base de datos
Fuente: https://coches.idae.es/storage/csv/idae-historico-202413.csv
"""

import pandas as pd
import psycopg2
import requests
from datetime import datetime
import sys
import os

# Configuración BD
DB_CONFIG = {
    'host': 'localhost',
    'database': 'db_N2',  # Base de datos de enriquecimiento
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': 5432
}

def download_idae_csv(url="https://coches.idae.es/storage/csv/idae-historico-202413.csv"):
    """Descarga el CSV más reciente de IDAE"""
    print(f"📥 Descargando datos IDAE desde: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Guardar archivo temporal
        temp_file = "/tmp/idae_vehiculos.csv"
        with open(temp_file, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Descarga completada: {len(response.content)} bytes")
        return temp_file
        
    except Exception as e:
        print(f"❌ Error descargando CSV: {e}")
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

def calculate_scores(df):
    """Calcula scores de movilidad 0-100"""
    
    # Score emisiones (invertido: menos emisiones = mejor score)
    max_emisiones = df['emisiones_co2_mixto_wltp_min'].max()
    df['score_emisiones'] = ((max_emisiones - df['emisiones_co2_mixto_wltp_min']) / max_emisiones * 100).fillna(100).round().astype(int)
    
    # Score consumo (invertido: menos consumo = mejor score)
    max_consumo = df['consumo_mixto_wltp'].max()
    df['score_consumo'] = ((max_consumo - df['consumo_mixto_wltp']) / max_consumo * 100).fillna(100).round().astype(int)
    
    # Score autonomía (directo: más autonomía = mejor score)
    max_autonomia = df['autonomia_electrica'].max()
    df['score_autonomia'] = (df['autonomia_electrica'] / max_autonomia * 100).fillna(0).round().astype(int)
    
    # Score total ponderado: 40% emisiones + 30% consumo + 20% autonomía + 10% eficiencia
    eficiencia_scores = {'A': 100, 'B': 85, 'C': 70, 'D': 55, 'E': 40, 'F': 25, 'G': 10}
    df['score_eficiencia'] = df['eficiencia_energetica'].map(eficiencia_scores).fillna(50)
    
    df['score_movilidad_total'] = (
        df['score_emisiones'] * 0.4 +
        df['score_consumo'] * 0.3 +
        df['score_autonomia'] * 0.2 +
        df['score_eficiencia'] * 0.1
    ).round().astype(int)
    
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
        
        # Convertir fechas
        date_cols = ['fecha_alta', 'fecha_actualizacion', 'fecha_comercializacion']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
        
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

def load_to_database(df):
    """Carga datos procesados en la base de datos"""
    print("💾 Cargando datos en base de datos...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Crear tabla si no existe
        with open('/Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/sql/create_vehiculos_espana.sql', 'r') as f:
            create_sql = f.read()
            cur.execute(create_sql)
        
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
            score_autonomia, score_movilidad_total, tipo_propulsion, segmento_normalizado
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (marca, modelo, vehiculo, motorizacion) 
        DO UPDATE SET
            fecha_actualizacion_score = CURRENT_TIMESTAMP,
            score_emisiones = EXCLUDED.score_emisiones,
            score_consumo = EXCLUDED.score_consumo,
            score_autonomia = EXCLUDED.score_autonomia,
            score_movilidad_total = EXCLUDED.score_movilidad_total
        """
        
        # Insertar por lotes
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            values = []
            for _, row in batch.iterrows():
                values.append((
                    row.get('fecha_alta'), row.get('fecha_actualizacion'), row.get('fecha_comercializacion'),
                    row['marca'], row['modelo'], row['vehiculo'], row.get('segmento'), 
                    row['motorizacion'], row.get('categoria'), row.get('mtma'),
                    row.get('consumo_nedc'), row.get('emisiones_nedc'),
                    row.get('consumo_mixto_wltp_min'), row.get('consumo_mixto_wltp_max'), row.get('consumo_mixto_wltp'),
                    row.get('emisionies_co2_mixto_wltp_min'), row.get('emisionies_co2_mixto_wltp_max'),
                    row.get('autonomia_electrica'), row.get('consumo_electrico'), row.get('observaciones'),
                    row['eficiencia_energetica'], row['score_emisiones'], row['score_consumo'],
                    row['score_autonomia'], row['score_movilidad_total'], row['tipo_propulsion'], row['segmento_normalizado']
                ))
            
            cur.executemany(insert_sql, values)
            total_inserted += len(values)
            print(f"📥 Insertados: {total_inserted}/{len(df)} registros")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Carga completada: {total_inserted} registros en core_vehiculos_espana")
        return total_inserted
        
    except Exception as e:
        print(f"❌ Error cargando en BD: {e}")
        return 0

def main():
    """Función principal"""
    print("🚗 Iniciando carga de datos IDAE vehículos España")
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
    print(f"   • Registros procesados: {len(df)}")
    print(f"   • Registros cargados: {total_loaded}")
    print(f"   • Tipos propulsión: {df['tipo_propulsion'].value_counts().to_dict()}")
    print(f"   • Etiquetas eficiencia: {df['eficiencia_energetica'].value_counts().to_dict()}")
    print(f"✅ Proceso completado exitosamente")

if __name__ == "__main__":
    main()
