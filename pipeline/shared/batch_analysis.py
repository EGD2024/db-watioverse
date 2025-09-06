#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Análisis masivo de archivos N0 para detectar patrones y generar cuestionarios inteligentes
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Set
from collections import defaultdict, Counter
from datetime import datetime
import logging

# Añadir directorio shared al path
sys.path.append(str(Path(__file__).parent))

from integrity_validator import IntegrityValidator
from field_mappings import get_nested_field

logger = logging.getLogger(__name__)

class BatchAnalyzer:
    """
    Analizador masivo de archivos N0 para detectar patrones y generar cuestionarios
    """
    
    def __init__(self):
        self.validator = IntegrityValidator()
        self.results = []
        self.field_frequency = defaultdict(int)
        self.missing_critical_fields = defaultdict(int)
        self.unique_field_values = defaultdict(set)
        self.provider_patterns = defaultdict(list)
        
    def analyze_all_n0_files(self, n0_directory: str) -> Dict[str, Any]:
        """
        Analiza todos los archivos N0 en un directorio
        
        Args:
            n0_directory: Directorio con archivos N0
            
        Returns:
            Diccionario con análisis consolidado
        """
        n0_files = list(Path(n0_directory).glob("N0_*.json"))
        
        if not n0_files:
            logger.warning(f"No se encontraron archivos N0 en: {n0_directory}")
            return {}
            
        logger.info(f"🔍 Analizando {len(n0_files)} archivos N0...")
        
        for n0_file in n0_files:
            try:
                result = self._analyze_single_file(str(n0_file))
                if result:
                    self.results.append(result)
                    self._update_global_stats(result)
                    
            except Exception as e:
                logger.error(f"Error analizando {n0_file}: {e}")
                
        return self._generate_consolidated_report()
    
    def _analyze_single_file(self, n0_path: str) -> Dict[str, Any]:
        """
        Analiza un archivo N0 individual
        
        Args:
            n0_path: Ruta al archivo N0
            
        Returns:
            Diccionario con análisis del archivo
        """
        try:
            with open(n0_path, 'r', encoding='utf-8') as f:
                n0_data = json.load(f)
                
            # Análisis básico del archivo
            analysis = {
                'file_path': n0_path,
                'file_name': Path(n0_path).name,
                'provider': self._extract_provider(n0_data),
                'cups': self._extract_cups(n0_data),
                'contract_type': self._extract_contract_type(n0_data),
                'date_range': self._extract_date_range(n0_data),
                'field_count': self._count_fields(n0_data),
                'critical_fields_present': self._check_critical_fields(n0_data),
                'missing_critical_fields': [],
                'unique_fields': self._extract_unique_fields(n0_data),
                'data_quality_score': 0
            }
            
            # Calcular campos críticos faltantes
            analysis['missing_critical_fields'] = self._find_missing_critical_fields(n0_data)
            
            # Calcular puntuación de calidad
            analysis['data_quality_score'] = self._calculate_quality_score(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error procesando {n0_path}: {e}")
            return None
    
    def _extract_provider(self, n0_data: Dict[str, Any]) -> str:
        """Extrae el proveedor energético"""
        provider_paths = [
            'contract_2x3.comercializadora',
            'provider.nombre_comercial',
            'provider.razon_social', 
            'provider',
            'proveedor.nombre_comercial',
            'proveedor.razon_social'
        ]
        
        for path in provider_paths:
            provider = get_nested_field(n0_data, path)
            if provider:
                return str(provider)
        return "DESCONOCIDO"
    
    def _extract_cups(self, n0_data: Dict[str, Any]) -> str:
        """Extrae el CUPS"""
        cups_paths = [
            'contract_2x3.cups_electricidad',
            'id_cups',
            'supply_point.cups',
            'supply_point.datos_suministro.cups',
            'punto_suministro.cups',
            'contrato.cups'
        ]
        
        for path in cups_paths:
            cups = get_nested_field(n0_data, path)
            if cups:
                return str(cups)
        return "DESCONOCIDO"
    
    def _extract_contract_type(self, n0_data: Dict[str, Any]) -> str:
        """Extrae el tipo de contrato"""
        type_paths = [
            'contrato.tipo_contrato',
            'contract_2x3.tipo_contrato',
            'facturacion.tipo_tarifa'
        ]
        
        for path in type_paths:
            contract_type = get_nested_field(n0_data, path)
            if contract_type:
                return str(contract_type)
        return "DESCONOCIDO"
    
    def _extract_date_range(self, n0_data: Dict[str, Any]) -> Dict[str, str]:
        """Extrae el rango de fechas de facturación"""
        date_paths = {
            'fecha_inicio': [
                'consumo_energia.inicio_periodo',
                'termino_potencia.inicio_periodo', 
                'facturacion.fecha_inicio', 
                'periodo.fecha_inicio'
            ],
            'fecha_fin': [
                'consumo_energia.fin_periodo',
                'termino_potencia.fin_periodo',
                'facturacion.fecha_fin', 
                'periodo.fecha_fin'
            ]
        }
        
        dates = {}
        for date_type, paths in date_paths.items():
            for path in paths:
                date_val = get_nested_field(n0_data, path)
                if date_val:
                    dates[date_type] = str(date_val)
                    break
            if date_type not in dates:
                dates[date_type] = "DESCONOCIDO"
                
        return dates
    
    def _count_fields(self, data: Any, prefix: str = "") -> int:
        """Cuenta recursivamente todos los campos en el JSON"""
        if isinstance(data, dict):
            count = 0
            for key, value in data.items():
                current_path = f"{prefix}.{key}" if prefix else key
                count += 1  # Contar el campo actual
                count += self._count_fields(value, current_path)
            return count
        elif isinstance(data, list) and data:
            return self._count_fields(data[0], prefix)  # Solo contar el primer elemento de listas
        else:
            return 0
    
    def _check_critical_fields(self, n0_data: Dict[str, Any]) -> List[str]:
        """Verifica qué campos críticos están presentes"""
        critical_fields = {
            'cliente_nombre': ['client.nombre_cliente', 'cliente.nombre_cliente', 'titular.nombre'],
            'cliente_nif': ['client.nif_titular.value', 'client.nif_titular', 'cliente.nif', 'titular.nif'],
            'cups': ['contract_2x3.cups_electricidad', 'id_cups', 'supply_point.cups', 'punto_suministro.cups'],
            'proveedor': ['contract_2x3.comercializadora', 'provider', 'provider.nombre_comercial', 'proveedor.nombre_comercial'],
            'fecha_inicio': ['consumo_energia.inicio_periodo', 'invoice_2x3.fecha_inicio_periodo', 'facturacion.fecha_inicio'],
            'fecha_fin': ['consumo_energia.fin_periodo', 'invoice_2x3.fecha_fin_periodo', 'facturacion.fecha_fin'],
            'importe_total': ['resumen_factura.total_factura', 'invoice_2x3.total_a_pagar', 'facturacion.importe_total'],
            'consumo_kwh': ['consumo_energia.consumo_medido_kwh', 'consumo.energia_activa_kwh', 'lecturas.consumo_kwh']
        }
        
        present_fields = []
        for field_name, paths in critical_fields.items():
            for path in paths:
                if get_nested_field(n0_data, path) is not None:
                    present_fields.append(field_name)
                    break
                    
        return present_fields
    
    def _find_missing_critical_fields(self, n0_data: Dict[str, Any]) -> List[str]:
        """Encuentra campos críticos faltantes"""
        critical_fields = {
            'cliente_nombre': ['client.nombre_cliente', 'cliente.nombre_cliente', 'titular.nombre'],
            'cliente_nif': ['client.nif_titular.value', 'client.nif_titular', 'cliente.nif', 'titular.nif'],
            'cups': ['contract_2x3.cups_electricidad', 'id_cups', 'supply_point.cups', 'punto_suministro.cups'],
            'proveedor': ['contract_2x3.comercializadora', 'provider', 'provider.nombre_comercial', 'proveedor.nombre_comercial'],
            'fecha_inicio': ['consumo_energia.inicio_periodo', 'invoice_2x3.fecha_inicio_periodo', 'facturacion.fecha_inicio'],
            'fecha_fin': ['consumo_energia.fin_periodo', 'invoice_2x3.fecha_fin_periodo', 'facturacion.fecha_fin'],
            'importe_total': ['resumen_factura.total_factura', 'invoice_2x3.total_a_pagar', 'facturacion.importe_total'],
            'consumo_kwh': ['consumo_energia.consumo_medido_kwh', 'consumo.energia_activa_kwh', 'lecturas.consumo_kwh']
        }
        
        missing_fields = []
        for field_name, paths in critical_fields.items():
            found = False
            for path in paths:
                if get_nested_field(n0_data, path) is not None:
                    found = True
                    break
            if not found:
                missing_fields.append(field_name)
                
        return missing_fields
    
    def _extract_unique_fields(self, data: Any, prefix: str = "", max_depth: int = 4) -> Set[str]:
        """Extrae todos los campos únicos del JSON con profundidad limitada"""
        fields = set()
        
        if max_depth <= 0:
            return fields
            
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{prefix}.{key}" if prefix else key
                fields.add(current_path)
                fields.update(self._extract_unique_fields(value, current_path, max_depth - 1))
        elif isinstance(data, list) and data:
            fields.update(self._extract_unique_fields(data[0], prefix, max_depth - 1))
            
        return fields
    
    def _calculate_quality_score(self, analysis: Dict[str, Any]) -> float:
        """Calcula una puntuación de calidad de datos (0-100)"""
        total_critical = 8  # Número total de campos críticos
        present_critical = len(analysis['critical_fields_present'])
        
        # Puntuación base por campos críticos presentes
        base_score = (present_critical / total_critical) * 70
        
        # Bonificación por cantidad de campos totales
        field_bonus = min(analysis['field_count'] / 100, 1) * 20
        
        # Bonificación por tener fechas válidas
        date_bonus = 10 if (analysis['date_range']['fecha_inicio'] != "DESCONOCIDO" and 
                           analysis['date_range']['fecha_fin'] != "DESCONOCIDO") else 0
        
        return round(base_score + field_bonus + date_bonus, 1)
    
    def _update_global_stats(self, analysis: Dict[str, Any]) -> None:
        """Actualiza estadísticas globales con el análisis de un archivo"""
        # Contar frecuencia de campos
        for field in analysis['unique_fields']:
            self.field_frequency[field] += 1
            
        # Contar campos críticos faltantes
        for missing_field in analysis['missing_critical_fields']:
            self.missing_critical_fields[missing_field] += 1
            
        # Agrupar por proveedor
        provider = analysis['provider']
        self.provider_patterns[provider].append({
            'file': analysis['file_name'],
            'cups': analysis['cups'],
            'quality_score': analysis['data_quality_score'],
            'missing_fields': analysis['missing_critical_fields']
        })
    
    def _generate_consolidated_report(self) -> Dict[str, Any]:
        """Genera reporte consolidado de todos los análisis"""
        total_files = len(self.results)
        
        if total_files == 0:
            return {}
            
        # Estadísticas generales
        avg_quality = sum(r['data_quality_score'] for r in self.results) / total_files
        total_fields = sum(r['field_count'] for r in self.results)
        
        # Campos más comunes
        common_fields = dict(Counter(self.field_frequency).most_common(20))
        
        # Campos críticos más faltantes
        critical_missing = dict(Counter(self.missing_critical_fields).most_common())
        
        # Patrones por proveedor
        provider_summary = {}
        for provider, files in self.provider_patterns.items():
            provider_summary[provider] = {
                'total_files': len(files),
                'avg_quality': round(sum(f['quality_score'] for f in files) / len(files), 1),
                'common_missing_fields': list(set().union(*[f['missing_fields'] for f in files]))
            }
        
        return {
            'summary': {
                'total_files_analyzed': total_files,
                'average_quality_score': round(avg_quality, 1),
                'total_unique_fields': len(self.field_frequency),
                'total_field_instances': total_fields,
                'analysis_timestamp': datetime.now().isoformat()
            },
            'field_analysis': {
                'most_common_fields': common_fields,
                'critical_missing_fields': critical_missing,
                'field_coverage': {field: (count/total_files)*100 
                                 for field, count in self.field_frequency.items()}
            },
            'provider_patterns': provider_summary,
            'questionnaire_suggestions': self._generate_questionnaire_suggestions(critical_missing),
            'detailed_results': self.results
        }
    
    def _generate_questionnaire_suggestions(self, critical_missing: Dict[str, int]) -> List[Dict[str, Any]]:
        """Genera sugerencias para cuestionario basado en campos faltantes"""
        total_files = len(self.results)
        
        suggestions = []
        
        # Mapeo de campos críticos a preguntas del cuestionario
        field_to_question = {
            'cliente_nombre': {
                'question': '¿Cuál es el nombre completo del titular del contrato?',
                'type': 'text',
                'required': True,
                'category': 'datos_personales'
            },
            'cliente_nif': {
                'question': '¿Cuál es el NIF/CIF del titular?',
                'type': 'text',
                'required': True,
                'category': 'datos_personales',
                'validation': 'nif_format'
            },
            'cups': {
                'question': '¿Cuál es el código CUPS de su punto de suministro?',
                'type': 'text',
                'required': True,
                'category': 'suministro',
                'validation': 'cups_format'
            },
            'proveedor': {
                'question': '¿Cuál es su compañía eléctrica actual?',
                'type': 'select',
                'required': True,
                'category': 'contrato',
                'options': list(self.provider_patterns.keys())
            },
            'fecha_inicio': {
                'question': '¿Desde qué fecha tiene el contrato actual?',
                'type': 'date',
                'required': True,
                'category': 'contrato'
            },
            'fecha_fin': {
                'question': '¿Hasta qué fecha es válido su contrato?',
                'type': 'date',
                'required': False,
                'category': 'contrato'
            },
            'importe_total': {
                'question': '¿Cuál fue el importe de su última factura?',
                'type': 'number',
                'required': True,
                'category': 'facturacion',
                'unit': 'euros'
            },
            'consumo_kwh': {
                'question': '¿Cuál fue su consumo en kWh en la última factura?',
                'type': 'number',
                'required': True,
                'category': 'consumo',
                'unit': 'kWh'
            }
        }
        
        for field, missing_count in critical_missing.items():
            if field in field_to_question:
                question_data = field_to_question[field].copy()
                question_data.update({
                    'field_name': field,
                    'missing_frequency': missing_count,
                    'missing_percentage': round((missing_count / total_files) * 100, 1),
                    'priority': 'high' if missing_count > total_files * 0.5 else 'medium'
                })
                suggestions.append(question_data)
        
        # Ordenar por frecuencia de falta (más faltante = mayor prioridad)
        suggestions.sort(key=lambda x: x['missing_frequency'], reverse=True)
        
        return suggestions
    
    def save_report(self, report: Dict[str, Any], output_path: str) -> None:
        """Guarda el reporte en un archivo JSON"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"📄 Reporte guardado en: {output_path}")
        except Exception as e:
            logger.error(f"Error guardando reporte: {e}")
    
    def print_summary(self, report: Dict[str, Any]) -> None:
        """Imprime un resumen del análisis por consola"""
        if not report:
            print("❌ No hay datos para mostrar")
            return
            
        summary = report['summary']
        field_analysis = report['field_analysis']
        questionnaire = report['questionnaire_suggestions']
        
        print("\n" + "="*60)
        print("📊 ANÁLISIS MASIVO DE ARCHIVOS N0")
        print("="*60)
        
        print(f"\n📈 RESUMEN GENERAL:")
        print(f"  • Archivos analizados: {summary['total_files_analyzed']}")
        print(f"  • Puntuación promedio: {summary['average_quality_score']}/100")
        print(f"  • Campos únicos encontrados: {summary['total_unique_fields']}")
        
        print(f"\n🚨 CAMPOS CRÍTICOS MÁS FALTANTES:")
        for field, count in list(field_analysis['critical_missing_fields'].items())[:5]:
            percentage = (count / summary['total_files_analyzed']) * 100
            print(f"  • {field}: {count} archivos ({percentage:.1f}%)")
        
        print(f"\n📋 SUGERENCIAS PARA CUESTIONARIO:")
        for i, suggestion in enumerate(questionnaire[:5], 1):
            print(f"  {i}. {suggestion['question']}")
            print(f"     Falta en {suggestion['missing_percentage']}% de archivos")
        
        print(f"\n🏢 PROVEEDORES DETECTADOS:")
        for provider, data in report['provider_patterns'].items():
            print(f"  • {provider}: {data['total_files']} archivos (calidad: {data['avg_quality']}/100)")


def main():
    """Función principal para ejecutar análisis masivo"""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    
    # Directorio con archivos N0
    n0_directory = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out"
    
    # Crear analizador y ejecutar
    analyzer = BatchAnalyzer()
    report = analyzer.analyze_all_n0_files(n0_directory)
    
    if report:
        # Mostrar resumen por consola
        analyzer.print_summary(report)
        
        # Guardar reporte completo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"/Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/batch_analysis_report_{timestamp}.json"
        analyzer.save_report(report, report_path)
        
        # Guardar cuestionario separado
        questionnaire_path = f"/Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/questionnaire_suggestions_{timestamp}.json"
        questionnaire_data = {
            'generated_at': datetime.now().isoformat(),
            'based_on_files': report['summary']['total_files_analyzed'],
            'questions': report['questionnaire_suggestions']
        }
        analyzer.save_report(questionnaire_data, questionnaire_path)
        
        print(f"\n📄 Reportes guardados:")
        print(f"  • Análisis completo: {report_path}")
        print(f"  • Cuestionario: {questionnaire_path}")
    else:
        print("❌ No se pudo generar el reporte")


if __name__ == "__main__":
    main()
