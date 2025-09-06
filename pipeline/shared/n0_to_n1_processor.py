#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
N0 to N1 Complete Processor - Procesador completo del pipeline N0→BD N0 + N1→BD N1
Implementa la arquitectura final: N0 anidado → N0 semi-plano (memoria) → BD N0 + N1 limpio → BD N1
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar módulos del pipeline
sys.path.append(str(Path(__file__).parent.parent.parent))
from pipeline.shared.n0_flattener import process_n0_to_memory
from pipeline.N0.insert_N0 import N0Inserter
from pipeline.N1.insert_N1 import N1Inserter

class N0ToN1Processor:
    """
    Procesador completo del pipeline N0→N1 con arquitectura final.
    Procesar datos N0 anidados → insertar en BD N0 → generar N1 limpio → insertar en BD N1.
    """
    
    def __init__(self, modo_prueba: bool = True):
        """Inicializa el procesador completo."""
        self.insert_n0 = N0Inserter(modo_prueba=modo_prueba)
        self.insert_n1 = N1Inserter(modo_prueba=modo_prueba)
        self.processed_files = 0
        self.successful_insertions = 0
        self.failed_insertions = 0
    
    def process_n0_file(self, file_path: str, enable_n0_insert: bool = True, enable_n1_insert: bool = True) -> Dict[str, Any]:
        """
        Procesa archivo N0 completo siguiendo arquitectura final.
        
        Args:
            file_path: Ruta del archivo N0 anidado
            enable_n0_insert: Si insertar en BD N0
            enable_n1_insert: Si insertar en BD N1
            
        Returns:
            Diccionario con resultados del procesamiento
        """
        result = {
            'file_path': file_path,
            'success': False,
            'n0_insert_success': False,
            'n1_insert_success': False,
            'error': None,
            'stats': {}
        }
        
        try:
            logger.info(f"🔄 Iniciando procesamiento: {Path(file_path).name}")
            
            # 1. Cargar archivo N0 anidado original
            with open(file_path, 'r', encoding='utf-8') as f:
                n0_original = json.load(f)
            
            logger.info(f"📂 N0 original cargado: {len(n0_original)} secciones")
            
            # 2. Procesar a estructura semi-plana EN MEMORIA
            n0_for_bd, n1_clean = process_n0_to_memory(n0_original)
            
            if not n0_for_bd or not n1_clean:
                raise Exception("Error en procesamiento a memoria")
            
            result['stats']['n0_sections'] = len(n0_for_bd)
            result['stats']['n1_sections'] = len(n1_clean)
            
            # 3. Crear archivo temporal N0 semi-plano para insertador
            if enable_n0_insert:
                logger.info("📥 Procesando N0 semi-plano...")
                
                # Crear archivo temporal con datos semi-planos
                temp_n0_path = file_path.replace('.json', '_TEMP_SEMI.json')
                with open(temp_n0_path, 'w', encoding='utf-8') as f:
                    json.dump(n0_for_bd, f, indent=2, ensure_ascii=False)
                
                # Usar insertador N0 con archivo temporal
                n0_insert_result = self.insert_n0.procesar_archivo_json(Path(temp_n0_path))
                result['n0_insert_success'] = n0_insert_result.exito
                result['stats']['n0_inserted_records'] = n0_insert_result.registros_insertados
                
                # NO mover archivos N1 aquí - se hace después de la inserción N1
                
                # Limpiar archivo temporal N0
                if os.path.exists(temp_n0_path):
                    os.unlink(temp_n0_path)
                
                if result['n0_insert_success']:
                    logger.info("✅ N0 semi-plano insertado exitosamente en BD N0")
                else:
                    logger.error(f"❌ Error insertando N0: {n0_insert_result.errores}")
            else:
                logger.info("⏭️ Inserción N0 deshabilitada")
                result['n0_insert_success'] = True  # Para no bloquear pipeline
            
            # 4. Crear archivo temporal N1 limpio para insertador
            if enable_n1_insert:
                logger.info("📥 Procesando N1 limpio...")
                
                # Crear archivo N1 final para usuario
                n1_final_path = file_path.replace('N0_', 'N1_')
                with open(n1_final_path, 'w', encoding='utf-8') as f:
                    json.dump(n1_clean, f, indent=2, ensure_ascii=False)
                logger.info(f"📄 Archivo N1 guardado: {n1_final_path}")
                
                # Usar insertador N1 con archivo N1 final
                n1_insert_result = self.insert_n1.procesar_archivo_json(Path(n1_final_path))
                result['n1_insert_success'] = n1_insert_result.exito
                result['stats']['n1_inserted_records'] = n1_insert_result.registros_insertados
                
                if result['n1_insert_success']:
                    logger.info("✅ N1 limpio insertado exitosamente en BD N1")
                else:
                    logger.error(f"❌ Error insertando N1: {n1_insert_result.errores}")
            else:
                logger.info("⏭️ Inserción N1 deshabilitada")
                result['n1_insert_success'] = True  # Para no bloquear pipeline
            
            # 5. Evaluar éxito general
            result['success'] = result['n0_insert_success'] and result['n1_insert_success']
            
            if result['success']:
                self.successful_insertions += 1
                logger.info(f"🎉 Pipeline completado exitosamente: {Path(file_path).name}")
            else:
                self.failed_insertions += 1
                logger.error(f"❌ Pipeline falló para: {Path(file_path).name}")
            
            self.processed_files += 1
            
        except Exception as e:
            logger.error(f"❌ Error procesando {file_path}: {e}")
            result['error'] = str(e)
            self.failed_insertions += 1
            self.processed_files += 1
        
        return result
    
    def process_multiple_files(self, file_paths: list, enable_n0_insert: bool = True, enable_n1_insert: bool = True) -> Dict[str, Any]:
        """
        Procesa múltiples archivos N0 en lote.
        
        Args:
            file_paths: Lista de rutas de archivos N0
            enable_n0_insert: Si insertar en BD N0
            enable_n1_insert: Si insertar en BD N1
            
        Returns:
            Diccionario con resultados de todos los procesamientos
        """
        logger.info(f"🚀 Iniciando procesamiento en lote: {len(file_paths)} archivos")
        
        batch_results = {
            'total_files': len(file_paths),
            'successful_files': 0,
            'failed_files': 0,
            'file_results': [],
            'summary': {}
        }
        
        for file_path in file_paths:
            if not Path(file_path).exists():
                logger.error(f"❌ Archivo no encontrado: {file_path}")
                batch_results['failed_files'] += 1
                continue
            
            result = self.process_n0_file(file_path, enable_n0_insert, enable_n1_insert)
            batch_results['file_results'].append(result)
            
            if result['success']:
                batch_results['successful_files'] += 1
            else:
                batch_results['failed_files'] += 1
        
        # Generar resumen
        batch_results['summary'] = {
            'success_rate': (batch_results['successful_files'] / len(file_paths)) * 100 if file_paths else 0,
            'total_processed': self.processed_files,
            'total_successful': self.successful_insertions,
            'total_failed': self.failed_insertions
        }
        
        logger.info(f"📊 RESUMEN LOTE: {batch_results['successful_files']}/{len(file_paths)} exitosos ({batch_results['summary']['success_rate']:.1f}%)")
        
        return batch_results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del procesador.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'processed_files': self.processed_files,
            'successful_insertions': self.successful_insertions,
            'failed_insertions': self.failed_insertions,
            'success_rate': (self.successful_insertions / self.processed_files * 100) if self.processed_files > 0 else 0
        }

def main():
    """Función principal para uso CLI."""
    if len(sys.argv) < 2:
        # Usar archivo por defecto para prueba
        default_file = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out/N0_ES0022000001348639QK_20250314_211043.json"
        if Path(default_file).exists():
            file_path = default_file
        else:
            logger.error("❌ Especifica la ruta del archivo N0: python n0_to_n1_processor.py <archivo_n0.json>")
            sys.exit(1)
    else:
        file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        logger.error(f"❌ Archivo no encontrado: {file_path}")
        sys.exit(1)
    
    # Procesar archivo
    processor = N0ToN1Processor(modo_prueba=True)
    
    # Procesar con insertores habilitados en modo prueba
    logger.info("🧪 MODO PRUEBA: Insertores habilitados (simulación)")
    result = processor.process_n0_file(file_path, enable_n0_insert=True, enable_n1_insert=True)
    
    # Mostrar resultado
    if result['success']:
        logger.info("🎉 PRUEBA EXITOSA - Pipeline completo funcionando")
        stats = processor.get_stats()
        logger.info(f"📊 Estadísticas: {stats}")
    else:
        logger.error(f"❌ PRUEBA FALLIDA: {result.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
