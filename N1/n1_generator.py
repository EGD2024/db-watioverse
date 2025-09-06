#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generador de JSON N1 desde datos N0
Orquesta el pipeline completo: N0 → Limpieza → Enriquecimiento → N1
"""

import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Añadir directorio shared al path
sys.path.append(str(Path(__file__).parent.parent / 'shared'))

from field_mappings import validate_n1_structure
from integrity_validator import IntegrityValidator
from n0_cleaner import N0Cleaner
from enrichment_engine import EnrichmentEngine

logger = logging.getLogger(__name__)

class N1Generator:
    """
    Generador de archivos JSON N1 desde datos N0
    Integra limpieza y enriquecimiento en pipeline único
    """
    
    def __init__(self, enable_validation: bool = True):
        """
        Inicializa el generador N1 con componentes necesarios
        
        Args:
            enable_validation: Si activar validación de integridad automática
        """
        self.cleaner = N0Cleaner()
        self.enricher = EnrichmentEngine()
        self.validator = IntegrityValidator() if enable_validation else None
        self.processed_count = 0
        self.error_count = 0
        self.enable_validation = enable_validation
    
    def generate_n1_from_file(self, n0_json_path: str, output_path: str = None) -> Optional[str]:
        """
        Genera archivo JSON N1 desde archivo JSON N0
        
        Args:
            n0_json_path: Ruta al archivo JSON N0
            output_path: Ruta de salida JSON N1 (opcional)
            
        Returns:
            Ruta del archivo N1 generado o None si hay error
        """
        try:
            logger.info(f"Generando N1 desde archivo: {n0_json_path}")
            
            # Cargar datos N0
            with open(n0_json_path, 'r', encoding='utf-8') as f:
                n0_data = json.load(f)
            
            # Generar N1 desde datos
            n1_data = self.generate_n1_from_data(n0_data)
            
            if n1_data is None:
                logger.error(f"Error generando N1 desde: {n0_json_path}")
                return None
            
            # Determinar ruta de salida
            if output_path is None:
                output_path = self._generate_output_path(n0_json_path)
            
            # Guardar JSON N1
            if self._save_n1_json(n1_data, output_path):
                logger.info(f"JSON N1 generado exitosamente: {output_path}")
                
                # Validar integridad si está habilitado
                if self.enable_validation and self.validator:
                    self._validate_integrity(n0_json_path, output_path)
                
                return output_path
            else:
                return None
                
        except FileNotFoundError:
            logger.error(f"Archivo N0 no encontrado: {n0_json_path}")
            self.error_count += 1
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON N0: {e}")
            self.error_count += 1
            return None
            
        except Exception as e:
            logger.error(f"Error inesperado generando N1: {e}", exc_info=True)
            self.error_count += 1
            return None
    
    def generate_n1_from_data(self, n0_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Genera datos JSON N1 desde datos N0 en memoria
        
        Args:
            n0_data: Diccionario con datos N0 originales
            
        Returns:
            Diccionario con datos N1 completos o None si hay error
        """
        try:
            logger.info("Iniciando pipeline N0 → N1")
            
            # Paso 1: Limpiar metadatos N0
            logger.info("Paso 1/3: Limpiando metadatos N0...")
            n1_base = self.cleaner.clean_json_data(n0_data)
            
            if n1_base is None:
                logger.error("Error en limpieza de datos N0")
                self.error_count += 1
                return None
            
            # Paso 2: Enriquecer datos
            logger.info("Paso 2/3: Enriqueciendo datos...")
            n1_enriched = self.enricher.enrich_n1_data(n1_base)
            
            # Paso 3: Validar estructura final
            logger.info("Paso 3/3: Validando estructura N1...")
            if not validate_n1_structure(n1_enriched):
                logger.error("Estructura N1 no válida")
                self.error_count += 1
                return None
            
            # Añadir metadatos de generación
            n1_enriched['_metadata_n1'] = {
                'generated_at': datetime.now().isoformat(),
                'pipeline_version': '1.0',
                'source': 'N0_to_N1_pipeline',
                'fields_count': len(n1_enriched),
                'enrichment_applied': True
            }
            
            self.processed_count += 1
            logger.info(f"Pipeline N0→N1 completado exitosamente: {len(n1_enriched)} campos")
            
            return n1_enriched
            
        except Exception as e:
            logger.error(f"Error en pipeline N0→N1: {e}", exc_info=True)
            self.error_count += 1
            return None
    
    def _generate_output_path(self, n0_json_path: str) -> str:
        """
        Genera ruta de salida para archivo N1 basada en ruta N0
        
        Args:
            n0_json_path: Ruta del archivo N0
            
        Returns:
            Ruta sugerida para archivo N1 en Data_out/
        """
        n0_path = Path(n0_json_path)
        
        # Cambiar N0 por N1 en el nombre del archivo
        n0_filename = n0_path.stem
        if n0_filename.startswith('N0_'):
            n1_filename = n0_filename.replace('N0_', 'N1_', 1) + n0_path.suffix
        else:
            n1_filename = f"N1_{n0_filename}{n0_path.suffix}"
        
        # Guardar en el mismo directorio Data_out/
        return str(n0_path.parent / n1_filename)
    
    def _validate_integrity(self, n0_path: str, n1_path: str) -> None:
        """
        Valida la integridad de la conversión N0→N1
        
        Args:
            n0_path: Ruta del archivo N0 original
            n1_path: Ruta del archivo N1 generado
        """
        try:
            logger.info("🔍 Validando integridad N0→N1...")
            result = self.validator.validate_conversion(n0_path, n1_path)
            
            if result['validation_passed']:
                logger.info("✅ Validación de integridad exitosa")
                if result.get('field_analysis'):
                    analysis = result['field_analysis']
                    logger.info(f"📊 Preservación: {analysis.get('preservation_rate', 0)}% | "
                              f"Enriquecimiento: {analysis.get('enrichment_rate', 0)}%")
            else:
                logger.error("❌ Fallos en validación de integridad:")
                for issue in result.get('critical_issues', []):
                    logger.error(f"  • {issue}")
                    
                # Generar reporte detallado en caso de error
                report_path = str(Path(n1_path).parent / f"integrity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                self.validator.generate_report(result, report_path)
                logger.error(f"📄 Reporte detallado guardado en: {report_path}")
                
        except Exception as e:
            logger.warning(f"Error en validación de integridad: {e}")
    
    def _save_n1_json(self, n1_data: Dict[str, Any], output_path: str) -> bool:
        """
        Guarda datos N1 en archivo JSON
        
        Args:
            n1_data: Datos N1 a guardar
            output_path: Ruta donde guardar
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(n1_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON N1 guardado: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando JSON N1: {e}", exc_info=True)
            return False
    
    def process_directory(self, n0_directory: str, output_directory: str = None) -> Dict[str, Any]:
        """
        Procesa todos los archivos JSON N0 de un directorio
        
        Args:
            n0_directory: Directorio con archivos JSON N0
            output_directory: Directorio de salida (opcional)
            
        Returns:
            Diccionario con resultados del procesamiento
        """
        results = {
            'processed': [],
            'errors': [],
            'total_files': 0,
            'success_count': 0,
            'error_count': 0
        }
        
        try:
            n0_dir = Path(n0_directory)
            
            if not n0_dir.exists():
                logger.error(f"Directorio N0 no existe: {n0_directory}")
                return results
            
            # Buscar archivos JSON
            json_files = list(n0_dir.glob('*.json'))
            results['total_files'] = len(json_files)
            
            logger.info(f"Procesando {len(json_files)} archivos JSON N0...")
            
            for json_file in json_files:
                try:
                    # Determinar ruta de salida
                    if output_directory:
                        output_path = Path(output_directory) / f"{json_file.stem}_N1.json"
                    else:
                        output_path = None
                    
                    # Generar N1
                    n1_path = self.generate_n1_from_file(str(json_file), str(output_path) if output_path else None)
                    
                    if n1_path:
                        results['processed'].append({
                            'n0_file': str(json_file),
                            'n1_file': n1_path,
                            'status': 'success'
                        })
                        results['success_count'] += 1
                    else:
                        results['errors'].append({
                            'n0_file': str(json_file),
                            'error': 'Generation failed'
                        })
                        results['error_count'] += 1
                        
                except Exception as e:
                    logger.error(f"Error procesando {json_file}: {e}")
                    results['errors'].append({
                        'n0_file': str(json_file),
                        'error': str(e)
                    })
                    results['error_count'] += 1
            
            logger.info(f"Procesamiento completado: {results['success_count']} éxitos, {results['error_count']} errores")
            
        except Exception as e:
            logger.error(f"Error procesando directorio: {e}", exc_info=True)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estadísticas combinadas del generador
        
        Returns:
            Diccionario con estadísticas completas
        """
        cleaner_stats = self.cleaner.get_statistics()
        enricher_stats = self.enricher.get_statistics()
        
        stats = {
            'generator': {
                'processed': self.processed_count,
                'errors': self.error_count,
                'success_rate': (self.processed_count / (self.processed_count + self.error_count) * 100) 
                               if (self.processed_count + self.error_count) > 0 else 0
            },
            'cleaner': cleaner_stats,
            'enricher': enricher_stats
        }
        
        # Añadir estadísticas del validador si está habilitado
        if self.enable_validation and self.validator:
            stats['validator'] = self.validator.get_validator_statistics()
        
        return stats

def generate_n1_file(n0_path: str, n1_path: str = None) -> bool:
    """
    Función de conveniencia para generar un archivo N1
    
    Args:
        n0_path: Ruta al archivo JSON N0
        n1_path: Ruta de salida JSON N1 (opcional)
        
    Returns:
        True si se generó exitosamente, False en caso contrario
    """
    generator = N1Generator()
    result_path = generator.generate_n1_from_file(n0_path, n1_path)
    return result_path is not None

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test con datos completos N0
    sample_n0_complete = {
        "cliente": "EMPRESA EJEMPLO SL",
        "direccion": "GRAN VIA 28, MADRID",
        "cups": "ES0031408000000000002JN",
        "nif": "B12345678",
        "periodo_facturacion": "2024-08",
        "fecha_emision": "2024-09-01",
        "fecha_inicio": "2024-08-01",
        "fecha_fin": "2024-08-31",
        "consumo_facturado_kwh": 2500.75,
        "importe_total": 450.30,
        "consumo_facturado_kwh_p1": 800.25,
        "consumo_facturado_kwh_p2": 1200.50,
        "consumo_facturado_kwh_p3": 300.00,
        "coste_energia_p1": 120.15,
        "coste_energia_p2": 180.20,
        "coste_energia_p3": 45.00,
        "potencia_contratada_p1": 5.5,
        "potencia_contratada_p2": 5.5,
        "potencia_contratada_p3": 5.5,
        "mix_energetico_renovable_pct": 45.2,
        "mix_energetico_cogeneracion_pct": 15.8,
        "emisiones_co2_kg_kwh": 0.25,
        "residuos_radiactivos_mg_kwh": 3.2,
        # Metadatos que se eliminarán
        "confianza_cliente": 0.95,
        "confianza_direccion": 0.88,
        "patron_cliente": "EMPRESA.*SL",
        "patron_cups": "ES[0-9]{18}[A-Z]{2}"
    }
    
    print("=== Test N1 Generator ===")
    
    generator = N1Generator()
    n1_data = generator.generate_n1_from_data(sample_n0_complete)
    
    if n1_data:
        print(f"✓ Generación N1 exitosa")
        print(f"  Campos N0 originales: {len(sample_n0_complete)}")
        print(f"  Campos N1 finales: {len(n1_data)}")
        
        # Verificar metadatos N1
        metadata = n1_data.get('_metadata_n1', {})
        print(f"  Pipeline version: {metadata.get('pipeline_version')}")
        print(f"  Enriquecimiento aplicado: {metadata.get('enrichment_applied')}")
        
        # Verificar algunos campos clave
        key_fields = ['cliente', 'consumo_facturado_kwh', 'coste_kwh_promedio', 'rating_sostenibilidad']
        for field in key_fields:
            value = n1_data.get(field)
            if value is not None:
                print(f"  {field}: {value}")
        
        # Verificar que se eliminaron metadatos N0
        metadata_removed = all(
            field not in n1_data 
            for field in ['confianza_cliente', 'patron_cliente']
        )
        print(f"  Metadatos N0 eliminados: {'✓' if metadata_removed else '✗'}")
        
        # Estadísticas
        stats = generator.get_statistics()
        print(f"  Estadísticas generador: {stats['generator']}")
        
    else:
        print("✗ Error en generación N1")
    
    print("\n=== Test completado ===")
