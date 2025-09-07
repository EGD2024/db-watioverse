#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script para validar el procesamiento N0 en memoria
Prueba la función process_n0_to_memory con archivo real
"""

import json
import logging
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar procesador
from n0_flattener import process_n0_to_memory

def test_n0_memory_processing(file_path: str):
    """
    Prueba el procesamiento N0 en memoria con archivo real.
    
    Args:
        file_path: Ruta del archivo N0 a procesar
    """
    try:
        logger.info(f"🔍 Iniciando prueba con archivo: {file_path}")
        
        # Cargar archivo N0
        with open(file_path, 'r', encoding='utf-8') as f:
            n0_original = json.load(f)
        
        logger.info(f"📂 Archivo N0 cargado: {len(n0_original)} secciones principales")
        
        # Procesar en memoria
        n0_for_bd, n1_clean = process_n0_to_memory(n0_original)
        
        # Validar resultados
        logger.info("📊 RESULTADOS DEL PROCESAMIENTO:")
        logger.info(f"  • N0 para BD (con metadata): {len(n0_for_bd)} secciones")
        logger.info(f"  • N1 limpio (sin metadata): {len(n1_clean)} secciones")
        
        # Mostrar estructura N0 para BD
        logger.info("\n📋 ESTRUCTURA N0 PARA BD (con metadata):")
        for section, data in n0_for_bd.items():
            if isinstance(data, dict):
                logger.info(f"  • {section}: {len(data)} campos")
                # Mostrar algunos campos con metadata
                metadata_fields = [k for k in data.keys() if 'confidence' in k or 'pattern' in k]
                if metadata_fields:
                    logger.info(f"    - Metadata: {metadata_fields[:3]}...")
            else:
                logger.info(f"  • {section}: valor simple")
        
        # Mostrar estructura N1 limpia
        logger.info("\n🧹 ESTRUCTURA N1 LIMPIA (sin metadata):")
        for section, data in n1_clean.items():
            if isinstance(data, dict):
                logger.info(f"  • {section}: {len(data)} campos")
            else:
                logger.info(f"  • {section}: valor simple")
        
        # Verificar que N0 mantiene metadata y N1 no
        n0_has_metadata = any('confidence' in str(data) or 'pattern' in str(data) 
                             for data in n0_for_bd.values())
        n1_has_metadata = any('confidence' in str(data) or 'pattern' in str(data) 
                             for data in n1_clean.values())
        
        logger.info(f"\n✅ VALIDACIÓN METADATA:")
        logger.info(f"  • N0 mantiene metadata: {'SÍ' if n0_has_metadata else 'NO'}")
        logger.info(f"  • N1 sin metadata: {'SÍ' if not n1_has_metadata else 'NO (ERROR)'}")
        
        # Verificar que ambos mantienen estructura agrupada
        main_sections = ['client', 'contract_2x3', 'invoice_2x3', 'consumo_energia']
        n0_sections = [s for s in main_sections if s in n0_for_bd]
        n1_sections = [s for s in main_sections if s in n1_clean]
        
        logger.info(f"\n📊 SECCIONES PRINCIPALES:")
        logger.info(f"  • N0: {len(n0_sections)}/{len(main_sections)} ({n0_sections})")
        logger.info(f"  • N1: {len(n1_sections)}/{len(main_sections)} ({n1_sections})")
        
        # Mostrar ejemplo de campo anidado en N0
        if 'client' in n0_for_bd and isinstance(n0_for_bd['client'], dict):
            logger.info(f"\n🔍 EJEMPLO CAMPO ANIDADO N0 (client):")
            for key, value in list(n0_for_bd['client'].items())[:3]:
                if isinstance(value, dict):
                    logger.info(f"  • {key}: {value}")
                else:
                    logger.info(f"  • {key}: {value}")
        
        # Mostrar ejemplo de campo limpio en N1
        if 'client' in n1_clean and isinstance(n1_clean['client'], dict):
            logger.info(f"\n🧹 EJEMPLO CAMPO LIMPIO N1 (client):")
            for key, value in list(n1_clean['client'].items())[:3]:
                logger.info(f"  • {key}: {value}")
        
        logger.info(f"\n🎉 PRUEBA COMPLETADA EXITOSAMENTE")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en prueba: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Usar archivo específico solicitado por usuario
        default_file = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out/N0_ES0022000001348639QK_20250314_211043.json"
        if Path(default_file).exists():
            file_path = default_file
        else:
            logger.error("❌ Especifica la ruta del archivo N0: python test_n0_memory_processor.py <archivo_n0.json>")
            sys.exit(1)
    else:
        file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        logger.error(f"❌ Archivo no encontrado: {file_path}")
        sys.exit(1)
    
    success = test_n0_memory_processing(file_path)
    sys.exit(0 if success else 1)
