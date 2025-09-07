#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test End-to-End del Pipeline Completo N0→BD N0→N1→BD N1
Simula la llegada del archivo N0_ES0022000001348639QK_20250314_211043 y valida todo el pipeline
"""

import json
import time
import shutil
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Añadir rutas necesarias
sys.path.append(str(Path(__file__).parent / 'shared'))
sys.path.append(str(Path(__file__).parent / 'N0'))

# Importar componentes del pipeline
from shared.n0_to_n1_processor import N0ToN1Processor
from shared.n0_flattener import process_n0_to_memory

class PipelineEndToEndTest:
    """Clase para probar el pipeline completo end-to-end."""
    
    def __init__(self):
        """Inicializa el test end-to-end."""
        self.test_file = "N0_ES0022000001348639QK_20250314_211043.json"
        self.source_dir = Path("/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out")
        self.test_dir = Path("/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out_test")
        self.processor = N0ToN1Processor(modo_prueba=True)
        self.test_results = {}
    
    def setup_test_environment(self):
        """Prepara el entorno de prueba."""
        logger.info("🔧 Preparando entorno de prueba...")
        
        # Crear directorio de prueba si no existe
        self.test_dir.mkdir(exist_ok=True)
        
        # Verificar que el archivo fuente existe
        source_file = self.source_dir / self.test_file
        if not source_file.exists():
            raise FileNotFoundError(f"❌ Archivo N0 no encontrado: {source_file}")
        
        # Copiar archivo a directorio de prueba
        test_file_path = self.test_dir / f"TEST_{self.test_file}"
        shutil.copy2(source_file, test_file_path)
        
        logger.info(f"✅ Archivo copiado para prueba: {test_file_path.name}")
        return test_file_path
    
    def test_step1_load_and_validate(self, file_path: Path) -> bool:
        """Paso 1: Cargar y validar archivo N0."""
        logger.info("\n🔍 PASO 1: Cargando y validando archivo N0...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                n0_data = json.load(f)
            
            # Validar estructura básica
            required_sections = ['client', 'contract_2x3', 'invoice_2x3', 'consumo_energia']
            found_sections = [s for s in required_sections if s in n0_data]
            
            if len(found_sections) >= 3:  # Al menos 75% de secciones
                logger.info(f"✅ Estructura N0 válida: {len(found_sections)}/{len(required_sections)} secciones")
                self.test_results['step1'] = {'success': True, 'sections': found_sections}
                return True
            else:
                logger.error(f"❌ Estructura N0 inválida: solo {len(found_sections)} secciones")
                self.test_results['step1'] = {'success': False, 'sections': found_sections}
                return False
                
        except Exception as e:
            logger.error(f"❌ Error cargando N0: {e}")
            self.test_results['step1'] = {'success': False, 'error': str(e)}
            return False
    
    def test_step2_memory_processing(self, file_path: Path) -> bool:
        """Paso 2: Procesar N0 a memoria (semi-plano)."""
        logger.info("\n🔍 PASO 2: Procesando N0 a estructura semi-plana en memoria...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                n0_data = json.load(f)
            
            # Procesar a memoria
            n0_for_bd, n1_clean = process_n0_to_memory(n0_data)
            
            # Validar que ambas estructuras se generaron
            if n0_for_bd and n1_clean:
                logger.info(f"✅ Procesamiento en memoria exitoso:")
                logger.info(f"   • N0 para BD: {len(n0_for_bd)} secciones")
                logger.info(f"   • N1 limpio: {len(n1_clean)} secciones")
                
                # Verificar que N0 tiene metadata y N1 no
                n0_has_metadata = any('confidence' in str(n0_for_bd.get(s, {})) for s in n0_for_bd)
                n1_has_metadata = any('confidence' in str(n1_clean.get(s, {})) for s in n1_clean)
                
                logger.info(f"   • N0 con metadata: {'SÍ' if n0_has_metadata else 'NO'}")
                logger.info(f"   • N1 sin metadata: {'SÍ' if not n1_has_metadata else 'NO'}")
                
                self.test_results['step2'] = {
                    'success': True,
                    'n0_sections': len(n0_for_bd),
                    'n1_sections': len(n1_clean),
                    'metadata_correct': n0_has_metadata and not n1_has_metadata
                }
                return True
            else:
                logger.error("❌ Error en procesamiento a memoria")
                self.test_results['step2'] = {'success': False}
                return False
                
        except Exception as e:
            logger.error(f"❌ Error procesando a memoria: {e}")
            self.test_results['step2'] = {'success': False, 'error': str(e)}
            return False
    
    def test_step3_pipeline_complete(self, file_path: Path) -> bool:
        """Paso 3: Ejecutar pipeline completo N0→BD N0→N1→BD N1."""
        logger.info("\n🔍 PASO 3: Ejecutando pipeline completo...")
        
        try:
            # Ejecutar pipeline completo
            result = self.processor.process_n0_file(
                str(file_path),
                enable_n0_insert=True,
                enable_n1_insert=True
            )
            
            if result['success']:
                logger.info("✅ Pipeline completo exitoso:")
                logger.info(f"   • N0 insertado: {'SÍ' if result['n0_insert_success'] else 'NO'}")
                logger.info(f"   • N1 insertado: {'SÍ' if result['n1_insert_success'] else 'NO'}")
                logger.info(f"   • N0 registros: {result['stats'].get('n0_inserted_records', 0)}")
                logger.info(f"   • N1 registros: {result['stats'].get('n1_inserted_records', 0)}")
                
                self.test_results['step3'] = {
                    'success': True,
                    'n0_success': result['n0_insert_success'],
                    'n1_success': result['n1_insert_success'],
                    'stats': result['stats']
                }
                return True
            else:
                logger.error(f"❌ Pipeline falló: {result.get('error', 'Error desconocido')}")
                self.test_results['step3'] = {
                    'success': False,
                    'error': result.get('error')
                }
                return False
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando pipeline: {e}")
            self.test_results['step3'] = {'success': False, 'error': str(e)}
            return False
    
    def test_step4_monitor_simulation(self, file_path: Path) -> bool:
        """Paso 4: Simular monitor automático."""
        logger.info("\n🔍 PASO 4: Simulando monitor automático...")
        
        try:
            # Simular detección de archivo nuevo
            logger.info(f"   📂 Simulando detección de archivo: {file_path.name}")
            time.sleep(1)  # Simular delay de detección
            
            # Simular cooldown
            logger.info("   ⏱️ Aplicando cooldown de 5 segundos...")
            time.sleep(2)  # Simulación reducida
            
            # Simular procesamiento automático
            logger.info("   🔄 Procesamiento automático iniciado...")
            
            # El monitor real usaría el procesador completo
            result = self.processor.process_n0_file(
                str(file_path),
                enable_n0_insert=True,
                enable_n1_insert=True
            )
            
            if result['success']:
                logger.info("   ✅ Monitor simulado procesó archivo exitosamente")
                
                # Simular generación de notificación
                notif_file = f"test_notificacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                notificacion = {
                    'timestamp': datetime.now().isoformat(),
                    'archivo': file_path.name,
                    'estado': 'PIPELINE_COMPLETO_EXITO',
                    'stats': result['stats']
                }
                
                with open(notif_file, 'w', encoding='utf-8') as f:
                    json.dump(notificacion, f, indent=2, ensure_ascii=False)
                
                logger.info(f"   📄 Notificación generada: {notif_file}")
                
                self.test_results['step4'] = {
                    'success': True,
                    'notification': notif_file
                }
                return True
            else:
                logger.error("   ❌ Monitor simulado falló")
                self.test_results['step4'] = {'success': False}
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en simulación de monitor: {e}")
            self.test_results['step4'] = {'success': False, 'error': str(e)}
            return False
    
    def cleanup_test_environment(self):
        """Limpia el entorno de prueba."""
        logger.info("\n🧹 Limpiando entorno de prueba...")
        
        try:
            # Limpiar archivos temporales
            for temp_file in self.test_dir.glob("TEST_*.json"):
                temp_file.unlink()
            for temp_file in Path.cwd().glob("test_notificacion_*.json"):
                temp_file.unlink()
            for temp_file in Path.cwd().glob("*_TEMP_*.json"):
                temp_file.unlink()
            
            logger.info("✅ Entorno limpiado")
        except Exception as e:
            logger.warning(f"⚠️ Error limpiando: {e}")
    
    def generate_report(self):
        """Genera reporte final del test."""
        logger.info("\n" + "="*60)
        logger.info("📊 REPORTE FINAL DEL TEST END-TO-END")
        logger.info("="*60)
        
        total_steps = len(self.test_results)
        successful_steps = sum(1 for r in self.test_results.values() if r.get('success'))
        
        for step_name, result in self.test_results.items():
            status = "✅" if result.get('success') else "❌"
            logger.info(f"{status} {step_name.upper()}: {'EXITOSO' if result.get('success') else 'FALLIDO'}")
            
            if result.get('error'):
                logger.info(f"   Error: {result['error']}")
            if result.get('stats'):
                logger.info(f"   Stats: {result['stats']}")
        
        logger.info("-"*60)
        logger.info(f"RESULTADO GLOBAL: {successful_steps}/{total_steps} pasos exitosos")
        
        if successful_steps == total_steps:
            logger.info("🎉 ¡PIPELINE COMPLETO VALIDADO EXITOSAMENTE!")
        else:
            logger.error("❌ Pipeline tiene errores que corregir")
        
        return successful_steps == total_steps
    
    def run_full_test(self):
        """Ejecuta el test completo end-to-end."""
        logger.info("🚀 INICIANDO TEST END-TO-END DEL PIPELINE N0→N1")
        logger.info(f"📄 Archivo de prueba: {self.test_file}")
        logger.info("="*60)
        
        try:
            # Preparar entorno
            test_file_path = self.setup_test_environment()
            
            # Ejecutar pasos del test
            if self.test_step1_load_and_validate(test_file_path):
                if self.test_step2_memory_processing(test_file_path):
                    if self.test_step3_pipeline_complete(test_file_path):
                        self.test_step4_monitor_simulation(test_file_path)
            
            # Generar reporte
            success = self.generate_report()
            
            # Limpiar
            self.cleanup_test_environment()
            
            return success
            
        except Exception as e:
            logger.error(f"💥 Error crítico en test: {e}")
            self.cleanup_test_environment()
            return False

def main():
    """Función principal."""
    tester = PipelineEndToEndTest()
    success = tester.run_full_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
