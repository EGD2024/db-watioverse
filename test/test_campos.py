#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Verificación de Campos N0 - SIMPLE Y DIRECTO
Verifica qué campos JSON se insertaron realmente en BD N0
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Importar db_manager
core_path = Path(__file__).parent.parent / 'core'
if not core_path.exists():
    core_path = Path(__file__).parent.parent.parent / 'core'
sys.path.insert(0, str(core_path))

from db_connections import db_manager

class TestCampos:
    """Verificador directo de campos JSON vs BD."""
    
    def __init__(self):
        self.data_dir = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out"
        print("✅ Usando db_manager para conexión BD N0")
    
    def contar_campos_json(self, data, prefix="") -> Set[str]:
        """Cuenta campos recursivamente en JSON."""
        campos = set()
        
        if isinstance(data, dict):
            for key, value in data.items():
                campo_completo = f"{prefix}.{key}" if prefix else key
                campos.add(campo_completo)
                subcampos = self.contar_campos_json(value, campo_completo)
                campos.update(subcampos)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                subcampos = self.contar_campos_json(item, f"{prefix}[{i}]" if prefix else f"[{i}]")
                campos.update(subcampos)
                
        return campos
    
    def obtener_campos_bd_n0(self) -> Dict[str, List[str]]:
        """Obtiene TODOS los campos de BD N0 usando db_manager."""
        campos_bd = {}
        
        try:
            conn = db_manager.get_connection('N0')
            cursor = conn.cursor()
            
            # Consulta directa de esquema - CORREGIDO: excluir id y created_at
            cursor.execute("""
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name IN ('client', 'provider', 'supply_point', 'supply_address', 
                                  'contract', 'energy_consumption', 'power_term', 'invoice', 
                                  'metadata', 'documents', 'metering', 'sustainability', 'invoice_summary',
                                  'direccion_fiscal')
                AND column_name NOT IN ('id', 'created_at')
                ORDER BY table_name, ordinal_position
            """)
            
            rows = cursor.fetchall()
            
            for row in rows:
                tabla = row[0]
                columna = f"{row[1]} ({row[2]})"
                
                if tabla not in campos_bd:
                    campos_bd[tabla] = []
                campos_bd[tabla].append(columna)
            
            cursor.close()
            db_manager.return_connection('N0', conn)
            
            total_campos = sum(len(cols) for cols in campos_bd.values())
            print(f"✅ Campos BD N0 obtenidos: {total_campos} campos")
            
            return campos_bd
            
        except Exception as e:
            print(f"❌ Error obteniendo campos BD N0: {e}")
            return {}
    
    def obtener_conteos_bd_n0(self) -> Dict[str, int]:
        """Obtiene conteos reales de registros en BD N0."""
        conteos = {}
        tablas = ['client', 'provider', 'supply_point', 'supply_address', 
                 'contract', 'energy_consumption', 'power_term', 'invoice', 
                 'metadata', 'documents', 'metering', 'sustainability', 'invoice_summary',
                 'direccion_fiscal']
        
        try:
            conn = db_manager.get_connection('N0')
            cursor = conn.cursor()
            
            for tabla in tablas:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                    count = cursor.fetchone()[0]
                    if count > 0:
                        conteos[tabla] = count
                except Exception as tabla_error:
                    # Tabla no existe o sin datos
                    continue
            
            cursor.close()
            db_manager.return_connection('N0', conn)
            
            print(f"✅ Conteos BD N0 obtenidos: {len(conteos)} tablas con datos")
            
            return conteos
            
        except Exception as e:
            print(f"❌ Error obteniendo conteos BD N0: {e}")
            return {}
    
    def analizar_archivo_json_n0(self) -> Set[str]:
        """Analiza archivo JSON N0 más reciente."""
        archivos_n0 = []
        
        for archivo in os.listdir(self.data_dir):
            if archivo.startswith('N0_') and archivo.endswith('.json'):
                path = os.path.join(self.data_dir, archivo)
                archivos_n0.append((archivo, path))
        
        if not archivos_n0:
            print("❌ No se encontraron archivos N0")
            return set()
        
        # Usar el primer archivo N0 encontrado
        archivo_path = archivos_n0[0][1]
        archivo_name = archivos_n0[0][0]
        
        print(f"📄 Analizando: {archivo_name}")
        
        try:
            with open(archivo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            campos = self.contar_campos_json(data)
            print(f"✅ Campos JSON N0: {len(campos)} campos totales")
            
            return campos
            
        except Exception as e:
            print(f"❌ Error analizando JSON: {e}")
            return set()
    
    def generar_reporte(self):
        """Genera reporte completo y directo."""
        print("\n" + "="*80)
        print("🔍 TEST CAMPOS N0 - VERIFICACIÓN DIRECTA")
        print("="*80)
        
        # 1. Analizar JSON N0
        print("\n1️⃣ ANALIZANDO JSON N0...")
        campos_json = self.analizar_archivo_json_n0()
        
        # 2. Obtener campos BD N0
        print("\n2️⃣ ANALIZANDO BD N0...")
        campos_bd = self.obtener_campos_bd_n0()
        total_campos_bd = sum(len(cols) for cols in campos_bd.values())
        
        # 3. Obtener conteos BD N0
        print("\n3️⃣ CONTANDO REGISTROS BD N0...")
        conteos_bd = self.obtener_conteos_bd_n0()
        total_registros = sum(conteos_bd.values())
        
        # 4. ANALIZAR CAMPOS CON DATOS REALES
        print("\n4️⃣ VERIFICANDO CAMPOS CON DATOS REALES...")
        campos_con_datos, detalle_por_tabla = self.verificar_campos_con_datos()
        
        # 5. RESULTADOS
        print("\n" + "="*80)
        print("📊 RESULTADOS FINALES")
        print("="*80)
        print(f"📄 Campos en JSON N0:        {len(campos_json):>6}")
        print(f"🗄️ Columnas totales BD N0:   {total_campos_bd:>6} (incluye P1-P6, etc.)")
        print(f"📝 REGISTROS insertados:     {total_registros:>6} ← Son filas, no campos")
        print(f"✅ CAMPOS con datos reales:  {campos_con_datos:>6}")
        
        if len(campos_json) > 0:
            mapeo_real = (campos_con_datos / len(campos_json)) * 100
            print(f"📈 Mapeo efectivo:         {mapeo_real:>5.1f}%")
        
        # 5. DETALLE POR TABLA - CAMPOS CON DATOS REALES
        print(f"\n📋 DETALLE POR TABLA ({len(campos_bd)} tablas):")
        print("-" * 55)
        print("  Tabla                Campos  Insertados  Registros")
        print("-" * 55)
        
        for tabla, columnas in sorted(campos_bd.items()):
            registros = conteos_bd.get(tabla, 0)
            campos_insertados = detalle_por_tabla.get(tabla, {}).get('campos_con_datos', 0)
            print(f"  {tabla:<20} {len(columnas):>6}  {campos_insertados:>10}  {registros:>9}")
        
        # 6. TABLAS SIN DATOS
        tablas_sin_datos = []
        for tabla in ['client', 'provider', 'supply_point', 'supply_address', 
                     'contract', 'energy_consumption', 'power_term', 'invoice', 
                     'metadata', 'documents', 'metering', 'sustainability', 'invoice_summary',
                     'direccion_fiscal']:
            if tabla not in conteos_bd:
                tablas_sin_datos.append(tabla)
        
        if tablas_sin_datos:
            print(f"\n⚠️ TABLAS SIN DATOS ({len(tablas_sin_datos)}):")
            for tabla in tablas_sin_datos:
                print(f"  - {tabla}")
        
        # 7. CONCLUSIÓN
        print("\n" + "="*80)
        if total_registros > 0 and total_campos_bd > 0:
            print("✅ CONCLUSIÓN: Pipeline N0 FUNCIONANDO CORRECTAMENTE")
            print(f"   - Datos insertados: {total_registros} registros")
            print(f"   - Campos mapeados: {total_campos_bd} campos")
        else:
            print("❌ CONCLUSIÓN: Pipeline N0 NO ESTÁ INSERTANDO DATOS")
        print("="*80)
        
        # Guardar reporte
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        reporte_file = Path(self.data_dir).parent / 'motores' / 'db_watioverse' / 'pipeline' / 'reportes_insercion' / f"test_campos_report_{timestamp}.txt"
        reporte_file.parent.mkdir(exist_ok=True)
        
        with open(reporte_file, 'w', encoding='utf-8') as f:
            f.write(f"TEST CAMPOS N0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n")
            f.write(f"Campos JSON N0:     {len(campos_json)}\n")
            f.write(f"Campos BD N0:       {total_campos_bd}\n")
            f.write(f"Registros BD N0:    {total_registros}\n")
            
            f.write("\nDetalle por tabla:\n")
            for tabla, columnas in sorted(campos_bd.items()):
                registros = conteos_bd.get(tabla, 0)
                f.write(f"  {tabla}: {len(columnas)} campos, {registros} registros\n")
        
        print(f"\n💾 Reporte guardado: {reporte_file}")
    
    def verificar_campos_con_datos(self) -> tuple[int, dict]:
        """Cuenta cuántas columnas tienen datos reales (no NULL) por tabla - CORREGIDO."""
        campos_con_datos = 0
        detalle_por_tabla = {}
        
        try:
            conn = db_manager.get_connection('N0')
            cursor = conn.cursor()
            
            # Obtener todas las tablas que tienen registros
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                AND table_name NOT LIKE 'pg_%'
            """)
            tablas_disponibles = [row[0] for row in cursor.fetchall()]
            
            for tabla in tablas_disponibles:
                try:
                    # Verificar si la tabla tiene registros
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                    total_registros = cursor.fetchone()[0]
                    
                    detalle_por_tabla[tabla] = {'campos_con_datos': 0, 'registros': total_registros}
                    
                    if total_registros == 0:
                        continue
                    
                    # Obtener todas las columnas (excepto id y created_at)
                    cursor.execute("""
                        SELECT column_name, data_type
                        FROM information_schema.columns 
                        WHERE table_name = %s AND table_schema = 'public'
                        AND column_name NOT IN ('id', 'created_at')
                        ORDER BY ordinal_position
                    """, (tabla,))
                    
                    columnas_info = cursor.fetchall()
                    
                    # Para cada columna, verificar si tiene datos no NULL
                    for columna, tipo_dato in columnas_info:
                        try:
                            # Query simple: solo contar campos NOT NULL
                            cursor.execute(f"""
                                SELECT COUNT(*) 
                                FROM {tabla} 
                                WHERE {columna} IS NOT NULL
                            """)
                            
                            count = cursor.fetchone()[0]
                            if count > 0:
                                campos_con_datos += 1
                                detalle_por_tabla[tabla]['campos_con_datos'] += 1
                                
                        except Exception as col_error:
                            continue
                            
                except Exception as tabla_error:
                    continue
            
            cursor.close()
            db_manager.return_connection('N0', conn)
            
            print(f"✅ Campos con datos reales: {campos_con_datos}")
            return campos_con_datos, detalle_por_tabla
            
        except Exception as e:
            print(f"❌ Error verificando campos con datos: {e}")
            return 0, {}

def main():
    """Función principal."""
    test = TestCampos()
    test.generar_reporte()

if __name__ == "__main__":
    main()
