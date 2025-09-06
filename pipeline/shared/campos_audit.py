#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Auditoría de Campos - Pipeline N0→N1
Analiza diferencias entre campos JSON y campos insertados en BD
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Set
from dataclasses import dataclass
from datetime import datetime
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Importar conexiones centralizadas
core_path = Path(__file__).parent.parent / 'core'
if not core_path.exists():
    core_path = Path(__file__).parent.parent.parent / 'core'
sys.path.insert(0, str(core_path))

try:
    from db_connections import db_manager
    logger = logging.getLogger(__name__)
except ImportError as e:
    logging.error(f"❌ Error importando db_connections: {e}")
    raise

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CamposAnalysis:
    """Resultado del análisis de campos."""
    json_total: int
    bd_total: int
    campos_perdidos: List[str]
    campos_insertados: List[str]
    porcentaje_conservado: float

class CamposAuditor:
    """Auditor de campos JSON vs BD."""
    
    def __init__(self):
        self.data_dir = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out"
        
    def _contar_campos_recursivo(self, data: Any, prefix: str = "") -> Set[str]:
        """Cuenta todos los campos de forma recursiva en un JSON."""
        campos = set()
        
        if isinstance(data, dict):
            for key, value in data.items():
                campo_completo = f"{prefix}.{key}" if prefix else key
                campos.add(campo_completo)
                
                # Recursivamente contar subcampos
                subcampos = self._contar_campos_recursivo(value, campo_completo)
                campos.update(subcampos)
                
        elif isinstance(data, list):
            for i, item in enumerate(data):
                subcampos = self._contar_campos_recursivo(item, f"{prefix}[{i}]" if prefix else f"[{i}]")
                campos.update(subcampos)
                
        return campos
    
    def analizar_archivo_json(self, archivo_path: str) -> Set[str]:
        """Analiza un archivo JSON y cuenta todos sus campos."""
        try:
            with open(archivo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            campos = self._contar_campos_recursivo(data)
            logger.info(f"📄 Archivo {Path(archivo_path).name}: {len(campos)} campos totales")
            return campos
            
        except Exception as e:
            logger.error(f"❌ Error analizando {archivo_path}: {e}")
            return set()
    
    def obtener_campos_bd_n0(self) -> Dict[str, List[str]]:
        """Obtiene todos los campos de todas las tablas en BD N0."""
        campos_bd = {}
        
        try:
            with db_manager.transaction('N0') as cursor:
                # Obtener todas las tablas
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                tablas = [row[0] for row in cursor.fetchall()]
                
                for tabla in tablas:
                    # Obtener columnas de cada tabla
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_name = %s AND table_schema = 'public'
                        ORDER BY ordinal_position
                    """, (tabla,))
                    
                    columnas = []
                    for col_name, data_type, is_nullable in cursor.fetchall():
                        columnas.append(f"{col_name} ({data_type})")
                    
                    campos_bd[tabla] = columnas
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo campos BD N0: {e}")
            
        return campos_bd
    
    def obtener_campos_bd_n1(self) -> Dict[str, List[str]]:
        """Obtiene todos los campos de todas las tablas en BD N1."""
        campos_bd = {}
        
        try:
            with db_manager.transaction('N1') as cursor:
                # Obtener todas las tablas
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                tablas = [row[0] for row in cursor.fetchall()]
                
                for tabla in tablas:
                    # Obtener columnas de cada tabla
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_name = %s AND table_schema = 'public'
                        ORDER BY ordinal_position
                    """, (tabla,))
                    
                    columnas = []
                    for col_name, data_type, is_nullable in cursor.fetchall():
                        columnas.append(f"{col_name} ({data_type})")
                    
                    campos_bd[tabla] = columnas
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo campos BD N1: {e}")
            
        return campos_bd
    
    def obtener_registros_recientes(self, bd_name: str, limite: int = 5) -> Dict[str, int]:
        """Obtiene conteo de registros recientes por tabla."""
        registros = {}
        
        try:
            with db_manager.transaction(bd_name) as cursor:
                # Obtener todas las tablas
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                tablas = [row[0] for row in cursor.fetchall()]
                
                for tabla in tablas:
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                    count = cursor.fetchone()[0]
                    registros[tabla] = count
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo registros {bd_name}: {e}")
            
        return registros
    
    def generar_reporte_completo(self):
        """Genera reporte completo de auditoría de campos."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        reporte_file = f"campos_audit_report_{timestamp}.txt"
        
        logger.info("🔍 Iniciando auditoría completa de campos...")
        
        # 1. Analizar archivos JSON N0
        archivos_n0 = []
        for archivo in os.listdir(self.data_dir):
            if archivo.startswith('N0_') and archivo.endswith('.json'):
                path = os.path.join(self.data_dir, archivo)
                archivos_n0.append((archivo, path))
        
        logger.info(f"📂 Encontrados {len(archivos_n0)} archivos N0")
        
        # 2. Analizar primer archivo N0 como muestra
        if archivos_n0:
            archivo_muestra = archivos_n0[0]
            campos_json = self.analizar_archivo_json(archivo_muestra[1])
        else:
            logger.error("❌ No se encontraron archivos N0")
            return
        
        # 3. Obtener esquemas BD
        logger.info("🗄️ Analizando esquemas BD N0...")
        campos_n0 = self.obtener_campos_bd_n0()
        total_campos_n0 = sum(len(cols) for cols in campos_n0.values())
        
        logger.info("🗄️ Analizando esquemas BD N1...")
        campos_n1 = self.obtener_campos_bd_n1()
        total_campos_n1 = sum(len(cols) for cols in campos_n1.values())
        
        # 4. Obtener conteos de registros
        registros_n0 = self.obtener_registros_recientes('N0')
        registros_n1 = self.obtener_registros_recientes('N1')
        
        # 5. Generar reporte
        with open(reporte_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"AUDITORÍA DE CAMPOS - PIPELINE N0→N1\n")
            f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            # Resumen ejecutivo
            f.write("📊 RESUMEN EJECUTIVO\n")
            f.write("-"*50 + "\n")
            f.write(f"📄 Campos en JSON N0 (muestra): {len(campos_json)}\n")
            f.write(f"🗄️ Campos en BD N0: {total_campos_n0}\n")
            f.write(f"🗄️ Campos en BD N1: {total_campos_n1}\n")
            f.write(f"⚠️ Pérdida N0: {len(campos_json) - total_campos_n0} campos ({100 - (total_campos_n0/len(campos_json)*100):.1f}%)\n")
            f.write(f"⚠️ Pérdida N1: {len(campos_json) - total_campos_n1} campos ({100 - (total_campos_n1/len(campos_json)*100):.1f}%)\n\n")
            
            # Detalles BD N0
            f.write("🗄️ DETALLE BD N0\n")
            f.write("-"*50 + "\n")
            for tabla, columnas in campos_n0.items():
                registros = registros_n0.get(tabla, 0)
                f.write(f"📋 {tabla}: {len(columnas)} campos, {registros} registros\n")
                for col in columnas:
                    f.write(f"   • {col}\n")
                f.write("\n")
            
            # Detalles BD N1
            f.write("🗄️ DETALLE BD N1\n")
            f.write("-"*50 + "\n")
            for tabla, columnas in campos_n1.items():
                registros = registros_n1.get(tabla, 0)
                f.write(f"📋 {tabla}: {len(columnas)} campos, {registros} registros\n")
                for col in columnas:
                    f.write(f"   • {col}\n")
                f.write("\n")
            
            # Campos JSON (primeros 100)
            f.write("📄 CAMPOS EN JSON N0 (muestra primeros 100)\n")
            f.write("-"*50 + "\n")
            for i, campo in enumerate(sorted(campos_json)):
                if i >= 100:
                    f.write(f"   ... y {len(campos_json) - 100} campos más\n")
                    break
                f.write(f"   • {campo}\n")
        
        logger.info(f"📋 Reporte generado: {reporte_file}")
        
        # Mostrar resumen en consola
        print("\n" + "="*80)
        print("📊 RESUMEN AUDITORÍA DE CAMPOS")
        print("="*80)
        print(f"📄 Campos JSON N0: {len(campos_json)}")
        print(f"🗄️ Campos BD N0: {total_campos_n0}")
        print(f"🗄️ Campos BD N1: {total_campos_n1}")
        print(f"⚠️ Pérdida N0: {len(campos_json) - total_campos_n0} ({100 - (total_campos_n0/len(campos_json)*100):.1f}%)")
        print(f"⚠️ Pérdida N1: {len(campos_json) - total_campos_n1} ({100 - (total_campos_n1/len(campos_json)*100):.1f}%)")
        
        print(f"\n📋 Reporte completo guardado en: {reporte_file}")
        return reporte_file

def main():
    """Función principal."""
    auditor = CamposAuditor()
    auditor.generar_reporte_completo()

if __name__ == "__main__":
    main()
