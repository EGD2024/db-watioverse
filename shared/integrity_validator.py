#!/usr/bin/env python3
"""
Validador de Integridad N0→N1
============================

Script para validar que no se está perdiendo información crítica
en la conversión de archivos N0 a N1.

Funcionalidades:
- Detecta campos críticos faltantes en N1
- Compara completitud de datos N0 vs N1
- Genera reportes de integridad detallados
- Se integra en el pipeline automático
- Alertas por pérdida de información importante

Autor: Sistema de Validación Watioverse
Fecha: 2025-09-06
"""

import json
import logging
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrityValidator:
    """
    Validador de integridad para conversiones N0→N1
    """
    
    def __init__(self):
        """
        Inicializa el validador con campos críticos definidos
        """
        # Campos críticos que DEBEN estar presentes en N1
        self.critical_fields = {
            'client': [
                'nombre', 'nif', 'direccion'
            ],
            'contract': [
                'cups', 'comercializadora', 'tarifa_acceso'
            ],
            'invoice': [
                'numero_factura', 'total_a_pagar', 'fecha_inicio_periodo', 
                'fecha_fin_periodo', 'fecha_emision'
            ],
            'consumption': [
                'consumo_facturado_kwh', 'precio_energia_eur_kwh', 
                'coste_energia_eur', 'coste_total_energia_eur'
            ]
        }
        
        # Campos importantes (no críticos pero deseables)
        self.important_fields = {
            'contract': [
                'distribuidora', 'numero_contrato_comercializadora',
                'potencia_contratada_p1', 'potencia_contratada_p2'
            ],
            'invoice': [
                'dias_periodo_facturado', 'coste_promedio_diario_eur',
                'bono_social', 'alquiler_contador'
            ],
            'consumption': [
                'consumo_medido_kwh', 'precio_peaje_eur_kwh', 'coste_peaje_eur',
                'potencia_contratada_kw', 'numero_contador', 'tipo_lectura_contador',
                'lectura_actual_contador_p1', 'lectura_actual_contador_p2', 'lectura_actual_contador_p3'
            ]
        }
        
        # Campos de metadatos N0 que deben eliminarse
        self.metadata_fields_to_ignore = [
            'extraction_metadata', 'processing_timestamp', 'source_file',
            'extraction_version', 'validation_status', 'error_log',
            'processing_duration', 'file_size_bytes', 'checksum_md5'
        ]
        
        self.validation_count = 0
        self.error_count = 0
        self.warning_count = 0
    
    def validate_conversion(self, n0_file_path: str, n1_file_path: str) -> Dict[str, Any]:
        """
        Valida la integridad de una conversión N0→N1
        
        Args:
            n0_file_path: Ruta al archivo N0 original
            n1_file_path: Ruta al archivo N1 generado
            
        Returns:
            Diccionario con resultado de validación detallado
        """
        try:
            self.validation_count += 1
            
            # Cargar archivos
            with open(n0_file_path, 'r', encoding='utf-8') as f:
                n0_data = json.load(f)
            
            with open(n1_file_path, 'r', encoding='utf-8') as f:
                n1_data = json.load(f)
            
            # Realizar validaciones
            result = {
                'timestamp': datetime.now().isoformat(),
                'n0_file': Path(n0_file_path).name,
                'n1_file': Path(n1_file_path).name,
                'validation_passed': True,
                'critical_issues': [],
                'warnings': [],
                'statistics': {},
                'field_analysis': {}
            }
            
            # 1. Validar campos críticos
            critical_issues = self._validate_critical_fields(n1_data)
            result['critical_issues'] = critical_issues
            
            # 2. Validar campos importantes
            warnings = self._validate_important_fields(n1_data)
            result['warnings'] = warnings
            
            # 3. Análisis de completitud
            field_analysis = self._analyze_field_completeness(n0_data, n1_data)
            result['field_analysis'] = field_analysis
            
            # 4. Estadísticas generales
            stats = self._calculate_statistics(n0_data, n1_data, critical_issues, warnings)
            result['statistics'] = stats
            
            # Determinar si la validación pasó
            if critical_issues:
                result['validation_passed'] = False
                self.error_count += 1
                logger.error(f"❌ Validación FALLÓ: {len(critical_issues)} problemas críticos")
            elif warnings:
                self.warning_count += 1
                logger.warning(f"⚠️ Validación con advertencias: {len(warnings)} campos importantes faltantes")
            else:
                logger.info("✅ Validación exitosa: integridad completa")
            
            # Generar cuestionario automáticamente si hay campos críticos faltantes
            if critical_issues:
                try:
                    from .questionnaire_manager import QuestionnaireManager
                    questionnaire_manager = QuestionnaireManager()
                    session_token = questionnaire_manager.generate_questionnaire_from_validation(result)
                    if session_token:
                        result['questionnaire_session'] = session_token
                        logger.info(f"🎯 Cuestionario generado automáticamente: {session_token}")
                except Exception as qe:
                    logger.warning(f"No se pudo generar cuestionario automático: {qe}")
            
            return result
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error en validación de integridad: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'validation_passed': False,
                'error': str(e),
                'critical_issues': [f"Error de validación: {e}"]
            }
    
    def _validate_critical_fields(self, n1_data: Dict[str, Any]) -> List[str]:
        """
        Valida que todos los campos críticos estén presentes en N1
        
        Args:
            n1_data: Datos N1 a validar
            
        Returns:
            Lista de problemas críticos encontrados
        """
        issues = []
        
        for group, fields in self.critical_fields.items():
            if group not in n1_data:
                issues.append(f"Grupo crítico faltante: '{group}'")
                continue
                
            group_data = n1_data[group]
            if not isinstance(group_data, dict):
                issues.append(f"Grupo '{group}' no es un diccionario")
                continue
            
            for field in fields:
                if field not in group_data or group_data[field] is None:
                    issues.append(f"Campo crítico faltante: '{group}.{field}'")
        
        return issues
    
    def _validate_important_fields(self, n1_data: Dict[str, Any]) -> List[str]:
        """
        Valida campos importantes (no críticos) en N1
        
        Args:
            n1_data: Datos N1 a validar
            
        Returns:
            Lista de advertencias por campos importantes faltantes
        """
        warnings = []
        
        for group, fields in self.important_fields.items():
            if group not in n1_data:
                continue
                
            group_data = n1_data[group]
            if not isinstance(group_data, dict):
                continue
            
            for field in fields:
                if field not in group_data or group_data[field] is None:
                    warnings.append(f"Campo importante faltante: '{group}.{field}'")
        
        return warnings
    
    def _analyze_field_completeness(self, n0_data: Dict[str, Any], n1_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza la completitud de campos entre N0 y N1
        
        Args:
            n0_data: Datos N0 originales
            n1_data: Datos N1 generados
            
        Returns:
            Análisis detallado de completitud
        """
        # Contar campos no-metadata en N0
        n0_fields = self._count_meaningful_fields(n0_data)
        
        # Contar campos en N1 (excluyendo enriquecimiento)
        n1_base_fields = 0
        n1_enrichment_fields = 0
        
        for group in ['client', 'contract', 'invoice', 'consumption', 'sustainability', 'metadata']:
            if group in n1_data and isinstance(n1_data[group], dict):
                n1_base_fields += len([v for v in n1_data[group].values() if v is not None])
        
        # Contar campos de enriquecimiento
        enrichment_keys = [
            'latitud', 'longitud', 'precipitacion_mm', 'temperatura_media_c',
            'precio_omie_kwh', 'precio_omie_mwh', 'ratio_precio_mercado',
            'eficiencia_energetica', 'coste_kwh_promedio', 'huella_carbono_kg',
            'rating_sostenibilidad', 'ahorro_potencial_eur', 'recomendacion_mejora'
        ]
        
        for key in enrichment_keys:
            if key in n1_data and n1_data[key] is not None:
                n1_enrichment_fields += 1
        
        return {
            'n0_meaningful_fields': n0_fields,
            'n1_base_fields': n1_base_fields,
            'n1_enrichment_fields': n1_enrichment_fields,
            'n1_total_fields': n1_base_fields + n1_enrichment_fields,
            'preservation_rate': round((n1_base_fields / n0_fields * 100), 2) if n0_fields > 0 else 0,
            'enrichment_rate': round((n1_enrichment_fields / (n1_base_fields + n1_enrichment_fields) * 100), 2) if (n1_base_fields + n1_enrichment_fields) > 0 else 0
        }
    
    def _count_meaningful_fields(self, data: Dict[str, Any], prefix: str = '') -> int:
        """
        Cuenta campos significativos (no metadata) en estructura anidada
        
        Args:
            data: Datos a analizar
            prefix: Prefijo para campos anidados
            
        Returns:
            Número de campos significativos
        """
        count = 0
        
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            # Ignorar campos de metadata
            if key in self.metadata_fields_to_ignore:
                continue
            
            if isinstance(value, dict):
                count += self._count_meaningful_fields(value, full_key)
            elif value is not None:
                count += 1
        
        return count
    
    def _calculate_statistics(self, n0_data: Dict[str, Any], n1_data: Dict[str, Any], 
                            critical_issues: List[str], warnings: List[str]) -> Dict[str, Any]:
        """
        Calcula estadísticas de la validación
        
        Args:
            n0_data: Datos N0
            n1_data: Datos N1  
            critical_issues: Problemas críticos
            warnings: Advertencias
            
        Returns:
            Estadísticas calculadas
        """
        return {
            'critical_issues_count': len(critical_issues),
            'warnings_count': len(warnings),
            'validation_score': max(0, 100 - (len(critical_issues) * 20) - (len(warnings) * 5)),
            'n0_file_size_kb': round(len(json.dumps(n0_data)) / 1024, 2),
            'n1_file_size_kb': round(len(json.dumps(n1_data)) / 1024, 2),
            'compression_ratio': round(len(json.dumps(n1_data)) / len(json.dumps(n0_data)), 3)
        }
    
    def generate_report(self, validation_result: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Genera reporte detallado de validación
        
        Args:
            validation_result: Resultado de validación
            output_path: Ruta donde guardar el reporte (opcional)
            
        Returns:
            Reporte como string
        """
        report_lines = [
            "=" * 60,
            "REPORTE DE INTEGRIDAD N0→N1",
            "=" * 60,
            f"Timestamp: {validation_result['timestamp']}",
            f"Archivo N0: {validation_result.get('n0_file', 'N/A')}",
            f"Archivo N1: {validation_result.get('n1_file', 'N/A')}",
            f"Validación: {'✅ EXITOSA' if validation_result['validation_passed'] else '❌ FALLÓ'}",
            ""
        ]
        
        # Problemas críticos
        if validation_result.get('critical_issues'):
            report_lines.extend([
                "🚨 PROBLEMAS CRÍTICOS:",
                "-" * 30
            ])
            for issue in validation_result['critical_issues']:
                report_lines.append(f"  • {issue}")
            report_lines.append("")
        
        # Advertencias
        if validation_result.get('warnings'):
            report_lines.extend([
                "⚠️  ADVERTENCIAS:",
                "-" * 20
            ])
            for warning in validation_result['warnings']:
                report_lines.append(f"  • {warning}")
            report_lines.append("")
        
        # Estadísticas
        if 'statistics' in validation_result:
            stats = validation_result['statistics']
            report_lines.extend([
                "📊 ESTADÍSTICAS:",
                "-" * 20,
                f"  • Puntuación de validación: {stats.get('validation_score', 0)}/100",
                f"  • Problemas críticos: {stats.get('critical_issues_count', 0)}",
                f"  • Advertencias: {stats.get('warnings_count', 0)}",
                f"  • Tamaño N0: {stats.get('n0_file_size_kb', 0)} KB",
                f"  • Tamaño N1: {stats.get('n1_file_size_kb', 0)} KB",
                f"  • Ratio compresión: {stats.get('compression_ratio', 0)}",
                ""
            ])
        
        # Análisis de campos
        if 'field_analysis' in validation_result:
            analysis = validation_result['field_analysis']
            report_lines.extend([
                "🔍 ANÁLISIS DE CAMPOS:",
                "-" * 25,
                f"  • Campos N0 significativos: {analysis.get('n0_meaningful_fields', 0)}",
                f"  • Campos N1 base: {analysis.get('n1_base_fields', 0)}",
                f"  • Campos N1 enriquecimiento: {analysis.get('n1_enrichment_fields', 0)}",
                f"  • Tasa preservación: {analysis.get('preservation_rate', 0)}%",
                f"  • Tasa enriquecimiento: {analysis.get('enrichment_rate', 0)}%",
                ""
            ])
        
        report_lines.append("=" * 60)
        report = "\n".join(report_lines)
        
        # Guardar reporte si se especifica ruta
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Reporte guardado en: {output_path}")
        
        return report
    
    def get_validator_statistics(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del validador
        
        Returns:
            Estadísticas del validador
        """
        return {
            'total_validations': self.validation_count,
            'errors': self.error_count,
            'warnings': self.warning_count,
            'success_rate': round((self.validation_count - self.error_count) / max(1, self.validation_count) * 100, 2)
        }

def main():
    """
    Función principal para pruebas del validador
    """
    validator = IntegrityValidator()
    
    # Ejemplo de uso
    n0_file = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out/N0_ES0022000001348639QK_20250314_211043.json"
    n1_file = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out/N1_ES0022000001348639QK_20250314_211043.json"
    
    print("🔍 VALIDADOR DE INTEGRIDAD N0→N1")
    print("=" * 40)
    
    # Validar conversión
    result = validator.validate_conversion(n0_file, n1_file)
    
    # Generar y mostrar reporte
    report = validator.generate_report(result)
    print(report)
    
    # Estadísticas del validador
    stats = validator.get_validator_statistics()
    print(f"\n📈 Estadísticas del validador: {stats}")

if __name__ == "__main__":
    main()
