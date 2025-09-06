#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Limpiador de metadatos N0 para pipeline N0 → N1
Elimina campos de confianza y patrones de extracción de datos N0
"""

import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Añadir directorio shared al path
sys.path.append(str(Path(__file__).parent.parent / 'shared'))

from field_mappings import clean_n0_metadata, map_n0_to_n1_base, validate_n1_structure

logger = logging.getLogger(__name__)

class N0Cleaner:
    """
    Limpiador de datos N0 para preparar transformación a N1
    """
    
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        
    def clean_json_file(self, n0_json_path: str) -> Optional[Dict[str, Any]]:
        """
        Limpia un archivo JSON N0 eliminando metadatos de extracción
        
        Args:
            n0_json_path: Ruta al archivo JSON N0
            
        Returns:
            Diccionario con datos N0 limpios o None si hay error
        """
        try:
            logger.info(f"Procesando archivo N0: {n0_json_path}")
            
            # Cargar JSON N0
            with open(n0_json_path, 'r', encoding='utf-8') as f:
                n0_data = json.load(f)
            
            if not isinstance(n0_data, dict):
                logger.error(f"Archivo N0 no contiene un objeto JSON válido: {n0_json_path}")
                self.error_count += 1
                return None
            
            # Limpiar metadatos
            cleaned_data = clean_n0_metadata(n0_data)
            
            # Mapear a estructura base N1
            n1_base = map_n0_to_n1_base(cleaned_data)
            
            # Validar estructura mínima
            if not self._validate_minimum_fields(n1_base):
                logger.error(f"Datos N0 no contienen campos mínimos requeridos: {n0_json_path}")
                self.error_count += 1
                return None
            
            self.processed_count += 1
            logger.info(f"Archivo N0 limpiado exitosamente: {len(n1_base)} campos")
            
            return n1_base
            
        except FileNotFoundError:
            logger.error(f"Archivo N0 no encontrado: {n0_json_path}")
            self.error_count += 1
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON N0: {e}")
            self.error_count += 1
            return None
            
        except Exception as e:
            logger.error(f"Error inesperado procesando N0: {e}", exc_info=True)
            self.error_count += 1
            return None
    
    def clean_json_data(self, n0_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Limpia datos N0 ya cargados en memoria
        
        Args:
            n0_data: Diccionario con datos N0 originales
            
        Returns:
            Diccionario con datos N0 limpios o None si hay error
        """
        try:
            logger.info("Procesando datos N0 en memoria")
            
            if not isinstance(n0_data, dict):
                logger.error("Datos N0 no son un diccionario válido")
                self.error_count += 1
                return None
            
            # Limpiar metadatos
            cleaned_data = clean_n0_metadata(n0_data)
            
            # Mapear a estructura base N1
            n1_base = map_n0_to_n1_base(cleaned_data)
            
            # Validar estructura mínima
            if not self._validate_minimum_fields(n1_base):
                logger.error("Datos N0 no contienen campos mínimos requeridos")
                self.error_count += 1
                return None
            
            self.processed_count += 1
            logger.info(f"Datos N0 limpiados exitosamente: {len(n1_base)} campos")
            
            return n1_base
            
        except Exception as e:
            logger.error(f"Error inesperado procesando datos N0: {e}", exc_info=True)
            self.error_count += 1
            return None
    
    def _validate_minimum_fields(self, n1_base: Dict[str, Any]) -> bool:
        """
        Valida que los datos base N1 tengan campos mínimos para continuar pipeline
        
        Args:
            n1_base: Datos base N1 a validar (estructura agrupada)
            
        Returns:
            True si tiene campos mínimos, False en caso contrario
        """
        # Verificar estructura agrupada N1
        required_checks = [
            ('client', 'nombre'),
            ('contract', 'cups'),
            ('client', 'direccion')
        ]
        
        missing_fields = []
        for group, field in required_checks:
            if group not in n1_base or not n1_base[group].get(field):
                missing_fields.append(f"{group}.{field}")
        
        if missing_fields:
            logger.warning(f"Campos mínimos faltantes: {missing_fields}")
            # Permitir continuar si tiene al menos algunos campos básicos
            return len(missing_fields) < len(required_checks)  # Al menos 1 campo debe existir
        
        return True
    
    def save_cleaned_data(self, cleaned_data: Dict[str, Any], output_path: str) -> bool:
        """
        Guarda datos N0 limpios en archivo JSON
        
        Args:
            cleaned_data: Datos N0 limpios
            output_path: Ruta donde guardar el archivo
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Datos limpios guardados en: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando datos limpios: {e}", exc_info=True)
            return False
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Retorna estadísticas de procesamiento
        
        Returns:
            Diccionario con contadores de procesamiento
        """
        return {
            'processed': self.processed_count,
            'errors': self.error_count,
            'success_rate': (self.processed_count / (self.processed_count + self.error_count) * 100) 
                           if (self.processed_count + self.error_count) > 0 else 0
        }

def clean_n0_file(input_path: str, output_path: str = None) -> bool:
    """
    Función de conveniencia para limpiar un archivo N0
    
    Args:
        input_path: Ruta al archivo JSON N0
        output_path: Ruta de salida (opcional)
        
    Returns:
        True si se procesó exitosamente, False en caso contrario
    """
    cleaner = N0Cleaner()
    cleaned_data = cleaner.clean_json_file(input_path)
    
    if cleaned_data is None:
        return False
    
    if output_path:
        return cleaner.save_cleaned_data(cleaned_data, output_path)
    
    return True

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test con datos de ejemplo
    sample_n0_data = {
        "cliente": "EMPRESA EJEMPLO SL",
        "direccion": "CALLE REAL 456, MADRID",
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
        "coste_energia_p1": 120.15,
        "coste_energia_p2": 180.20,
        "potencia_contratada_p1": 5.5,
        "potencia_contratada_p2": 5.5,
        "mix_energetico_renovable_pct": 45.2,
        "emisiones_co2_kg_kwh": 0.25,
        # Metadatos que se deben eliminar
        "confianza_cliente": 0.95,
        "confianza_direccion": 0.88,
        "confianza_cups": 0.99,
        "patron_cliente": "EMPRESA.*SL",
        "patron_direccion": "CALLE.*MADRID",
        "patron_cups": "ES[0-9]{18}[A-Z]{2}"
    }
    
    print("=== Test N0 Cleaner ===")
    
    cleaner = N0Cleaner()
    cleaned_data = cleaner.clean_json_data(sample_n0_data)
    
    if cleaned_data:
        print(f"✓ Limpieza exitosa")
        print(f"  Campos originales: {len(sample_n0_data)}")
        print(f"  Campos limpios: {len(cleaned_data)}")
        print(f"  Campos eliminados: {len(sample_n0_data) - len(cleaned_data)}")
        
        # Verificar que se eliminaron metadatos
        metadata_removed = all(
            field not in cleaned_data 
            for field in ['confianza_cliente', 'patron_cliente', 'confianza_direccion']
        )
        print(f"  Metadatos eliminados: {'✓' if metadata_removed else '✗'}")
        
        # Mostrar estadísticas
        stats = cleaner.get_statistics()
        print(f"  Estadísticas: {stats}")
        
    else:
        print("✗ Error en limpieza")
    
    print("\n=== Test completado ===")
