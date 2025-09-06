#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
N0 Semi-Flattener - Desanidador de datos N0 a estructura semi-plana EN MEMORIA
Convierte estructura N0 anidada en estructura agrupada (1 nivel) manteniendo metadata
Permite inserción directa en BD N0 y procesamiento para N1
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class N0SemiFlattener:
    """
    Desanida estructura N0 anidada a formato semi-plano EN MEMORIA.
    Mantiene agrupación por sectores (client, contract_2x3, etc.) con 1 nivel de anidación.
    Conserva TODA la metadata para BD N0, permite limpieza posterior para N1.
    """
    
    def __init__(self):
        """Inicializa el desanidador semi-plano N0."""
        self.processed_sections = 0
        self.processed_fields = 0
    
    def semi_flatten_n0_data(self, n0_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Desanida datos N0 a estructura semi-plana EN MEMORIA.
        Mantiene agrupación por sectores con 1 nivel de anidación.
        CORRIGE mapeos anidados y renombra grupos _2x3.
        
        Args:
            n0_data: Datos N0 anidados originales
            
        Returns:
            Diccionario con estructura N0 semi-plana agrupada CON metadata
        """
        semi_flattened = {}
        self.processed_sections = 0
        self.processed_fields = 0
        
        try:
            # Procesar secciones principales con mapeo corregido
            section_mappings = {
                # Secciones sin cambio
                'client': 'client',
                'provider': 'provider', 
                'supply_point': 'supply_point',
                'consumo_energia': 'consumo_energia',
                'termino_potencia': 'termino_potencia',
                # Renombrar grupos _2x3 → sin sufijo
                'contract_2x3': 'contract',
                'contract_3x3': 'contract', 
                'invoice_2x3': 'invoice',
                'invoice_3x3': 'invoice',
                'metering_2x3': 'metering',
                'metering_3x3': 'metering'
            }
            
            # Procesar con mapeo corregido
            for original_section, target_section in section_mappings.items():
                if original_section in n0_data:
                    processed_data = self._process_section_with_flattening(n0_data[original_section], original_section)
                    semi_flattened[target_section] = processed_data
                    self.processed_sections += 1
            
            # Procesar secciones especiales con anidamiento complejo
            if 'resumen_factura' in n0_data:
                semi_flattened['resumen_factura'] = self._process_resumen_factura(n0_data['resumen_factura'])
                self.processed_sections += 1
            
            # Añadir campos sueltos que no estén en secciones mapeadas
            processed_keys = list(section_mappings.keys()) + ['resumen_factura']
            for key, value in n0_data.items():
                if key not in processed_keys:
                    semi_flattened[key] = value
                    self.processed_fields += 1
            
            logger.info(f"✅ N0 semi-desanidado CON MAPEO CORREGIDO: {self.processed_sections} secciones, {self.processed_fields} campos")
            return semi_flattened
            
        except Exception as e:
            logger.error(f"❌ Error semi-desanidando N0: {e}")
            return n0_data  # Retornar original si falla
    
    def _process_section_with_flattening(self, section_data: Any, section_name: str) -> Any:
        """
        Procesa una sección con aplanado inteligente según tipo de sección.
        CORRIGE campos anidados para evitar pérdida de datos.
        
        Args:
            section_data: Datos de la sección a procesar
            section_name: Nombre de la sección original
            
        Returns:
            Sección procesada con campos aplanados correctamente
        """
        if isinstance(section_data, dict):
            processed = {}
            
            for key, value in section_data.items():
                # CASOS ESPECIALES de campos anidados críticos
                if key == 'nif_titular' and isinstance(value, dict):
                    # client.nif_titular: extraer value pero mantener metadata
                    processed['nif_titular_value'] = value.get('value')
                    processed['nif_titular_confidence'] = value.get('confidence')
                    processed['nif_titular_pattern'] = value.get('pattern')
                    processed['nif_titular_source'] = value.get('source')
                    self.processed_fields += 4
                    
                elif key == 'direccion_fiscal' and isinstance(value, dict):
                    # provider.direccion_fiscal: aplanar con prefijo
                    for subkey, subvalue in value.items():
                        processed[f'direccion_fiscal_{subkey}'] = subvalue
                    self.processed_fields += len(value)
                    
                elif key == 'datos_suministro' and isinstance(value, dict):
                    # supply_point.datos_suministro: aplanar contenido
                    for subkey, subvalue in value.items():
                        if subkey == 'direccion_suministro' and isinstance(subvalue, dict):
                            # Direccion suministro: aplanar con prefijo específico
                            for dir_key, dir_value in subvalue.items():
                                processed[f'direccion_suministro_{dir_key}'] = dir_value
                            self.processed_fields += len(subvalue)
                        else:
                            processed[subkey] = subvalue
                            self.processed_fields += 1
                            
                elif isinstance(value, dict) and len(value) <= 10:
                    # Diccionarios pequeños: aplanar con prefijo de clave
                    for subkey, subvalue in value.items():
                        processed[f'{key}_{subkey}'] = subvalue
                    self.processed_fields += len(value)
                    
                elif isinstance(value, list):
                    # Listas: mantener estructura pero procesarlas especialmente
                    processed[key] = value
                    self.processed_fields += 1
                    
                else:
                    # Valor simple o diccionario complejo: mantener
                    processed[key] = value
                    self.processed_fields += 1
                    
            return processed
        else:
            # No es diccionario, retornar tal como está
            self.processed_fields += 1
            return section_data
    
    def _process_resumen_factura(self, resumen_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa sección resumen_factura con manejo especial de arrays impuestos.
        
        Args:
            resumen_data: Datos de resumen_factura
            
        Returns:
            Resumen procesado con impuestos aplanados
        """
        processed = {}
        
        for key, value in resumen_data.items():
            if key == 'impuestos' and isinstance(value, list):
                # Aplanar array de impuestos
                for i, impuesto in enumerate(value):
                    if isinstance(impuesto, dict):
                        for imp_key, imp_value in impuesto.items():
                            processed[f'impuesto_{i+1}_{imp_key}'] = imp_value
                        self.processed_fields += len(impuesto)
            else:
                processed[key] = value
                self.processed_fields += 1
                
        return processed
    
    def clean_metadata_for_n1(self, n0_semi_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpia metadata de estructura semi-plana para crear datos N1.
        Elimina RECURSIVAMENTE todos los campos de metadata.
        
        Args:
            n0_semi_data: Datos N0 semi-planos con metadata
            
        Returns:
            Datos limpios sin metadata para N1
        """
        metadata_fields = [
            'confidence', 'pattern', 'source', 'confianza_cliente',
            'confianza_direccion', 'confianza_cups', 'confianza_nif',
            'confianza_periodo_facturacion', 'confianza_fecha_emision',
            'confianza_fecha_inicio', 'confianza_fecha_fin',
            'confianza_consumo_facturado_kwh', 'confianza_importe_total',
            'patron_cliente', 'patron_direccion', 'patron_cups', 'patron_nif',
            'patron_periodo_facturacion', 'patron_fecha_emision',
            'patron_fecha_inicio', 'patron_fecha_fin',
            'patron_consumo_facturado_kwh', 'patron_importe_total'
        ]
        
        def clean_recursive(data):
            """Limpia metadata recursivamente."""
            if isinstance(data, dict):
                cleaned = {}
                for k, v in data.items():
                    if k not in metadata_fields:
                        cleaned_value = clean_recursive(v)
                        if cleaned_value is not None:
                            cleaned[k] = cleaned_value
                return cleaned if cleaned else None
            elif isinstance(data, list):
                cleaned_list = []
                for item in data:
                    cleaned_item = clean_recursive(item)
                    if cleaned_item is not None:
                        cleaned_list.append(cleaned_item)
                return cleaned_list if cleaned_list else None
            else:
                return data
        
        cleaned_data = {}
        fields_removed = 0
        
        for section_key, section_data in n0_semi_data.items():
            # No procesar sección metadata completa
            if section_key == 'metadata':
                continue
                
            # Limpiar campos con sufijos de metadata
            if any(section_key.endswith(suffix) for suffix in ['_confianza', '_patron']):
                fields_removed += 1
                continue
            
            cleaned_section = clean_recursive(section_data)
            if cleaned_section is not None:
                cleaned_data[section_key] = cleaned_section
            else:
                fields_removed += 1
        
        logger.info(f"✅ Metadata limpiada para N1: {len(cleaned_data)} secciones, {fields_removed} campos eliminados")
        return cleaned_data
    
    def get_nested_field(self, data: Dict[str, Any], field_path: str, default=None) -> Any:
        """
        Extrae campo usando notación punto desde datos anidados.
        
        Args:
            data: Datos anidados
            field_path: Ruta del campo (ej: 'client.nombre_cliente')
            default: Valor por defecto si no existe
            
        Returns:
            Valor del campo o default
        """
        try:
            keys = field_path.split('.')
            value = data
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
                    
            return value
            
        except Exception:
            return default
    
    def validate_semi_flattened_structure(self, semi_flattened_data: Dict[str, Any]) -> bool:
        """
        Valida que la estructura semi-desanidada sea correcta.
        
        Args:
            semi_flattened_data: Datos N0 semi-desanidados
            
        Returns:
            True si la estructura es válida
        """
        required_sections = [
            'client', 'contract', 'invoice', 'consumo_energia'
        ]
        
        found_sections = 0
        for section in required_sections:
            if section in semi_flattened_data:
                found_sections += 1
                logger.debug(f"✅ Sección '{section}' encontrada")
            else:
                logger.warning(f"⚠️ Sección '{section}' no encontrada")
        
        is_valid = found_sections >= len(required_sections) * 0.75  # Al menos 75% de secciones
        
        if is_valid:
            logger.info(f"✅ Estructura N0 semi-desanidada válida: {found_sections}/{len(required_sections)} secciones")
        else:
            logger.error(f"❌ Estructura N0 semi-desanidada inválida: {found_sections}/{len(required_sections)} secciones")
        
        return is_valid

def process_n0_to_memory(n0_data: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Procesa datos N0 anidados a formato semi-plano EN MEMORIA.
    Retorna datos para BD N0 (con metadata) y datos limpios para N1.
    
    Args:
        n0_data: Datos N0 anidados originales
        
    Returns:
        Tupla (datos_n0_con_metadata, datos_n1_limpios)
    """
    try:
        flattener = N0SemiFlattener()
        
        # Crear estructura semi-plana con metadata
        n0_semi_data = flattener.semi_flatten_n0_data(n0_data)
        
        if not flattener.validate_semi_flattened_structure(n0_semi_data):
            logger.error("❌ Estructura semi-desanidada inválida")
            return n0_data, {}
        
        # Crear datos limpios para N1 (sin metadata)
        n1_clean_data = flattener.clean_metadata_for_n1(n0_semi_data)
        
        logger.info("✅ Procesamiento N0→memoria exitoso")
        return n0_semi_data, n1_clean_data
        
    except Exception as e:
        logger.error(f"❌ Error procesando N0 a memoria: {e}")
        return n0_data, {}

if __name__ == "__main__":
    # Ejemplo de uso
    logging.basicConfig(level=logging.INFO)
    
    import sys
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        result = flatten_n0_file(input_file, output_file)
        if result:
            print(f"✅ Archivo desanidado: {result}")
        else:
            print("❌ Error desanidando archivo")
    else:
        print("Uso: python n0_flattener.py <archivo_n0.json> [archivo_salida.json]")
