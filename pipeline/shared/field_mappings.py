#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mapeos de campos y configuraciones comunes para pipeline N0 → N1
Centraliza la transformación de datos entre capas del sistema watioverse
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# =============================================================================
# MAPEOS DE CAMPOS N0 → N1
# =============================================================================

# Campos de metadatos N0 que se eliminan en N1
METADATA_FIELDS_TO_REMOVE = [
    'confianza_cliente',
    'confianza_direccion', 
    'confianza_cups',
    'confianza_nif',
    'confianza_periodo_facturacion',
    'confianza_fecha_emision',
    'confianza_fecha_inicio',
    'confianza_fecha_fin',
    'confianza_consumo_facturado_kwh',
    'confianza_importe_total',
    'patron_cliente',
    'patron_direccion',
    'patron_cups', 
    'patron_nif',
    'patron_periodo_facturacion',
    'patron_fecha_emision',
    'patron_fecha_inicio',
    'patron_fecha_fin',
    'patron_consumo_facturado_kwh',
    'patron_importe_total'
]

# Mapeo directo de campos N0 → N1 (estructura anidada → plana)
DIRECT_FIELD_MAPPING = {
    # Identificación - extraer de estructura anidada N0
    'cliente': 'client.nombre_cliente',
    'direccion': 'supply_point.datos_suministro.direccion_suministro',
    'cups': 'contract_2x3.cups_electricidad', 
    'nif': 'client.nif_titular.value',
    'comercializadora': 'contract_2x3.comercializadora',
    'tarifa_acceso': 'contract_2x3.tarifa_acceso',
    
    # Fechas - usar rutas reales del archivo N0
    'fecha_inicio_periodo': 'invoice_2x3.fecha_inicio_periodo',
    'fecha_fin_periodo': 'invoice_2x3.fecha_fin_periodo',
    'fecha_emision': 'invoice_2x3.fecha_emision',
    'fecha_cargo': 'invoice_2x3.fecha_cargo',
    'inicio_periodo_consumo': 'consumo_energia.inicio_periodo',
    'fin_periodo_consumo': 'consumo_energia.fin_periodo',
    
    # Facturación - datos reales de invoice_2x3
    'numero_factura': 'invoice_2x3.numero_factura',
    'total_a_pagar': 'invoice_2x3.total_a_pagar',
    'dias_periodo_facturado': 'invoice_2x3.dias_periodo_facturado',
    'coste_promedio_diario_eur': 'invoice_2x3.coste_promedio_diario_eur',
    'bono_social': 'invoice_2x3.bono_social',
    'alquiler_contador': 'invoice_2x3.alquiler_contador',
    
    # Consumo energía - datos reales de consumo_energia
    'consumo_medido_kwh': 'consumo_energia.consumo_medido_kwh',
    'consumo_facturado_kwh': 'consumo_energia.consumo_facturado_kwh',
    'precio_energia_eur_kwh': 'consumo_energia.precio_energia_eur_kwh',
    'precio_peaje_eur_kwh': 'consumo_energia.precio_peaje_eur_kwh',
    'coste_energia_eur': 'consumo_energia.coste_energia_eur',
    'coste_peaje_eur': 'consumo_energia.coste_peaje_eur',
    'coste_total_energia_eur': 'consumo_energia.coste_total_energia_eur',
    
    # Potencia - datos reales de termino_potencia
    'potencia_contratada_kw': 'termino_potencia.potencia_contratada_kw',
    'dias_facturacion': 'termino_potencia.dias_facturacion',
    'precio_potencia_eur_kw_dia': 'termino_potencia.precio_potencia_eur_kw_dia',
    'coste_potencia_eur': 'termino_potencia.coste_potencia_eur',
    'coste_total_potencia_eur': 'termino_potencia.coste_total_potencia_eur',
    
    # Lecturas contador - datos reales de metering_2x3
    'numero_contador': 'metering_2x3.numero_contador',
    'fecha_lectura_fin_contador': 'metering_2x3.fecha_lectura_fin_contador',
    'tipo_lectura_contador': 'metering_2x3.tipo_lectura_contador',
    'lectura_actual_contador_p1': 'metering_2x3.lectura_actual_contador_p1',
    'lectura_anterior_contador_p1': 'metering_2x3.lectura_anterior_contador_p1',
    'lectura_actual_contador_p2': 'metering_2x3.lectura_actual_contador_p2',
    'lectura_anterior_contador_p2': 'metering_2x3.lectura_anterior_contador_p2',
    'lectura_actual_contador_p3': 'metering_2x3.lectura_actual_contador_p3',
    'lectura_anterior_contador_p3': 'metering_2x3.lectura_anterior_contador_p3',
    
    # Potencias contratadas por período - datos reales de contract_2x3
    'potencia_contratada_p1': 'contract_2x3.potencia_contratada_p1',
    'potencia_contratada_p2': 'contract_2x3.potencia_contratada_p2',
    'precio_unitario_potencia_p1': 'contract_2x3.precio_unitario_potencia_p1',
    'precio_unitario_potencia_p2': 'contract_2x3.precio_unitario_potencia_p2',
    
    # Sostenibilidad base - si existen en el archivo
    'mix_energetico_renovable_pct': 'sustainability.mix_energetico_renovable_pct',
    'emisiones_co2_kg_kwh': 'sustainability.emisiones_co2_kg_kwh'
}

# =============================================================================
# CONFIGURACIÓN DE ENRIQUECIMIENTO
# =============================================================================

# Campos que se añaden en el enriquecimiento N1
ENRICHMENT_FIELDS = {
    # Geolocalización
    'latitud': None,
    'longitud': None,
    
    # Datos climáticos
    'precipitacion_mm': None,
    'temperatura_media_c': None,
    
    # Precios de mercado
    'precio_omie_kwh': None,
    'precio_omie_mwh': None,
    
    # KPIs calculados
    'ratio_precio_mercado': None,
    'eficiencia_energetica': None,
    'coste_kwh_promedio': None,
    
    # Métricas de sostenibilidad calculadas
    'huella_carbono_kg': None,
    'rating_sostenibilidad': None,
    'ahorro_potencial_eur': None,
    'recomendacion_mejora': None
}

# =============================================================================
# FUNCIONES DE MAPEO
# =============================================================================

def clean_n0_metadata(n0_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Elimina campos de metadatos de extracción de datos N0
    
    Args:
        n0_data: Diccionario con datos N0 originales
        
    Returns:
        Diccionario con datos N0 sin metadatos
    """
    cleaned_data = n0_data.copy()
    
    for field in METADATA_FIELDS_TO_REMOVE:
        if field in cleaned_data:
            del cleaned_data[field]
            logger.debug(f"Eliminado campo metadata: {field}")
    
    logger.info(f"Eliminados {len(METADATA_FIELDS_TO_REMOVE)} campos de metadatos N0")
    return cleaned_data

def get_nested_field(data: Dict[str, Any], field_path: str) -> Any:
    """
    Extrae un campo de una estructura anidada usando notación de puntos
    
    Args:
        data: Diccionario con datos anidados
        field_path: Ruta del campo usando puntos (ej: 'client.nombre_cliente')
        
    Returns:
        Valor del campo o None si no existe
    """
    try:
        keys = field_path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    except (KeyError, TypeError):
        return None

def map_n0_to_n1_base(cleaned_n0_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapea campos N0 limpios a estructura base N1 (solo un nivel de anidación)
    
    Args:
        cleaned_n0_data: Datos N0 sin metadatos
        
    Returns:
        Diccionario con estructura base N1 agrupada con todos los datos críticos
    """
    # Estructura N1 con grupos de un solo nivel
    n1_base = {
        'client': {},
        'contract': {},
        'invoice': {},
        'consumption': {},
        'sustainability': {},
        'metadata': {}
    }
    
    # === DATOS DEL CLIENTE ===
    n1_base['client']['nombre'] = get_nested_field(cleaned_n0_data, 'client.nombre_cliente')
    n1_base['client']['nif'] = get_nested_field(cleaned_n0_data, 'client.nif_titular.value')
    
    # Dirección como string concatenada
    direccion_obj = get_nested_field(cleaned_n0_data, 'supply_point.datos_suministro.direccion_suministro')
    if direccion_obj and isinstance(direccion_obj, dict):
        direccion_parts = []
        if direccion_obj.get('tipo_via'): direccion_parts.append(direccion_obj['tipo_via'])
        if direccion_obj.get('nombre_via'): direccion_parts.append(direccion_obj['nombre_via'])
        if direccion_obj.get('numero'): direccion_parts.append(str(direccion_obj['numero']))
        if direccion_obj.get('planta'): direccion_parts.append(direccion_obj['planta'])
        if direccion_obj.get('poblacion'): direccion_parts.append(direccion_obj['poblacion'])
        if direccion_obj.get('provincia'): direccion_parts.append(direccion_obj['provincia'])
        if direccion_obj.get('codigo_postal'): direccion_parts.append(direccion_obj['codigo_postal'])
        n1_base['client']['direccion'] = ', '.join(filter(None, direccion_parts))
    
    # === DATOS DEL CONTRATO ===
    n1_base['contract']['cups'] = get_nested_field(cleaned_n0_data, 'contract_2x3.cups_electricidad')
    n1_base['contract']['comercializadora'] = get_nested_field(cleaned_n0_data, 'contract_2x3.comercializadora')
    n1_base['contract']['tarifa_acceso'] = get_nested_field(cleaned_n0_data, 'contract_2x3.tarifa_acceso')
    n1_base['contract']['distribuidora'] = get_nested_field(cleaned_n0_data, 'contract_2x3.distribuidora')
    n1_base['contract']['numero_contrato_comercializadora'] = get_nested_field(cleaned_n0_data, 'contract_2x3.numero_contrato_comercializadora')
    n1_base['contract']['potencia_contratada_p1'] = get_nested_field(cleaned_n0_data, 'contract_2x3.potencia_contratada_p1')
    n1_base['contract']['potencia_contratada_p2'] = get_nested_field(cleaned_n0_data, 'contract_2x3.potencia_contratada_p2')
    
    # === DATOS DE FACTURACIÓN ===
    n1_base['invoice']['numero_factura'] = get_nested_field(cleaned_n0_data, 'invoice_2x3.numero_factura')
    n1_base['invoice']['total_a_pagar'] = get_nested_field(cleaned_n0_data, 'invoice_2x3.total_a_pagar')
    n1_base['invoice']['fecha_inicio_periodo'] = get_nested_field(cleaned_n0_data, 'invoice_2x3.fecha_inicio_periodo')
    n1_base['invoice']['fecha_fin_periodo'] = get_nested_field(cleaned_n0_data, 'invoice_2x3.fecha_fin_periodo')
    n1_base['invoice']['fecha_emision'] = get_nested_field(cleaned_n0_data, 'invoice_2x3.fecha_emision')
    n1_base['invoice']['fecha_cargo'] = get_nested_field(cleaned_n0_data, 'invoice_2x3.fecha_cargo')
    n1_base['invoice']['dias_periodo_facturado'] = get_nested_field(cleaned_n0_data, 'invoice_2x3.dias_periodo_facturado')
    n1_base['invoice']['coste_promedio_diario_eur'] = get_nested_field(cleaned_n0_data, 'invoice_2x3.coste_promedio_diario_eur')
    n1_base['invoice']['bono_social'] = get_nested_field(cleaned_n0_data, 'invoice_2x3.bono_social')
    n1_base['invoice']['alquiler_contador'] = get_nested_field(cleaned_n0_data, 'invoice_2x3.alquiler_contador')
    
    # === DATOS DE CONSUMO ===
    n1_base['consumption']['consumo_medido_kwh'] = get_nested_field(cleaned_n0_data, 'consumo_energia.consumo_medido_kwh')
    n1_base['consumption']['consumo_facturado_kwh'] = get_nested_field(cleaned_n0_data, 'consumo_energia.consumo_facturado_kwh')
    n1_base['consumption']['inicio_periodo'] = get_nested_field(cleaned_n0_data, 'consumo_energia.inicio_periodo')
    n1_base['consumption']['fin_periodo'] = get_nested_field(cleaned_n0_data, 'consumo_energia.fin_periodo')
    n1_base['consumption']['precio_energia_eur_kwh'] = get_nested_field(cleaned_n0_data, 'consumo_energia.precio_energia_eur_kwh')
    n1_base['consumption']['precio_peaje_eur_kwh'] = get_nested_field(cleaned_n0_data, 'consumo_energia.precio_peaje_eur_kwh')
    n1_base['consumption']['coste_energia_eur'] = get_nested_field(cleaned_n0_data, 'consumo_energia.coste_energia_eur')
    n1_base['consumption']['coste_peaje_eur'] = get_nested_field(cleaned_n0_data, 'consumo_energia.coste_peaje_eur')
    n1_base['consumption']['coste_total_energia_eur'] = get_nested_field(cleaned_n0_data, 'consumo_energia.coste_total_energia_eur')
    
    # === DATOS DE POTENCIA ===
    n1_base['consumption']['potencia_contratada_kw'] = get_nested_field(cleaned_n0_data, 'termino_potencia.potencia_contratada_kw')
    n1_base['consumption']['dias_facturacion'] = get_nested_field(cleaned_n0_data, 'termino_potencia.dias_facturacion')
    n1_base['consumption']['precio_potencia_eur_kw_dia'] = get_nested_field(cleaned_n0_data, 'termino_potencia.precio_potencia_eur_kw_dia')
    n1_base['consumption']['coste_potencia_eur'] = get_nested_field(cleaned_n0_data, 'termino_potencia.coste_potencia_eur')
    n1_base['consumption']['coste_total_potencia_eur'] = get_nested_field(cleaned_n0_data, 'termino_potencia.coste_total_potencia_eur')
    
    # === LECTURAS DE CONTADOR ===
    n1_base['consumption']['numero_contador'] = get_nested_field(cleaned_n0_data, 'metering_2x3.numero_contador')
    n1_base['consumption']['fecha_lectura_fin_contador'] = get_nested_field(cleaned_n0_data, 'metering_2x3.fecha_lectura_fin_contador')
    n1_base['consumption']['tipo_lectura_contador'] = get_nested_field(cleaned_n0_data, 'metering_2x3.tipo_lectura_contador')
    n1_base['consumption']['lectura_actual_contador_p1'] = get_nested_field(cleaned_n0_data, 'metering_2x3.lectura_actual_contador_p1')
    n1_base['consumption']['lectura_anterior_contador_p1'] = get_nested_field(cleaned_n0_data, 'metering_2x3.lectura_anterior_contador_p1')
    n1_base['consumption']['lectura_actual_contador_p2'] = get_nested_field(cleaned_n0_data, 'metering_2x3.lectura_actual_contador_p2')
    n1_base['consumption']['lectura_anterior_contador_p2'] = get_nested_field(cleaned_n0_data, 'metering_2x3.lectura_anterior_contador_p2')
    n1_base['consumption']['lectura_actual_contador_p3'] = get_nested_field(cleaned_n0_data, 'metering_2x3.lectura_actual_contador_p3')
    n1_base['consumption']['lectura_anterior_contador_p3'] = get_nested_field(cleaned_n0_data, 'metering_2x3.lectura_anterior_contador_p3')
    
    # === SOSTENIBILIDAD BASE ===
    # (Se añadirán datos si existen en el archivo N0)
    
    # Limpiar campos vacíos
    for group in n1_base:
        n1_base[group] = {k: v for k, v in n1_base[group].items() if v is not None}
    
    campos_mapeados = sum(len(group) for group in n1_base.values())
    logger.info(f"Mapeados {campos_mapeados} campos N0 → N1 base (estructura agrupada)")
    return n1_base

def add_enrichment_fields(n1_base: Dict[str, Any], enrichment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Añade campos de enriquecimiento a datos base N1
    
    Args:
        n1_base: Datos base N1
        enrichment_data: Datos de enriquecimiento calculados
        
    Returns:
        Diccionario N1 completo con enriquecimiento
    """
    n1_enriched = n1_base.copy()
    
    for field, default_value in ENRICHMENT_FIELDS.items():
        if field in enrichment_data:
            n1_enriched[field] = enrichment_data[field]
        else:
            n1_enriched[field] = default_value
            logger.debug(f"Campo enriquecimiento no disponible: {field}")
    
    logger.info(f"Añadidos {len(ENRICHMENT_FIELDS)} campos de enriquecimiento")
    return n1_enriched

def validate_n1_structure(n1_data: Dict[str, Any]) -> bool:
    """
    Valida que la estructura N1 tenga los campos mínimos requeridos
    
    Args:
        n1_data: Datos N1 a validar (estructura agrupada)
        
    Returns:
        True si la estructura es válida, False en caso contrario
    """
    # Campos mínimos requeridos en estructura agrupada
    required_checks = [
        ('client', 'nombre'),
        ('client', 'direccion'), 
        ('contract', 'cups'),
        ('client', 'nif'),
    ]
    
    missing_fields = []
    for group, field in required_checks:
        if group not in n1_data or field not in n1_data[group]:
            missing_fields.append(f"{group}.{field}")
    
    if missing_fields:
        logger.warning(f"Campos mínimos faltantes en N1: {missing_fields}")
        return len(missing_fields) <= 2  # Permitir hasta 2 campos faltantes
    
    logger.info("Estructura N1 validada correctamente")
    return True

# =============================================================================
# CONFIGURACIÓN DE CONEXIONES BD
# =============================================================================

# Configuración BD N0 (lectura)
N0_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'N0',
    'user': 'postgres',
    'password': 'postgres'
}

# Configuración BD N1 (escritura)
N1_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'N1',
    'user': 'postgres',
    'password': 'postgres'
}

# Tablas N1 para inserción
N1_TABLES = [
    'documents', 'metadata', 'client', 'contract', 'invoice',
    'consumption_p1', 'consumption_p2', 'consumption_p3',
    'consumption_p4', 'consumption_p5', 'consumption_p6',
    'cost_p1', 'cost_p2', 'cost_p3', 'cost_p4', 'cost_p5', 'cost_p6',
    'power_p1', 'power_p2', 'power_p3', 'power_p4', 'power_p5', 'power_p6',
    'sustainability_base', 'sustainability_metrics', 'analytics'
]

if __name__ == "__main__":
    # Test básico de funciones
    logging.basicConfig(level=logging.INFO)
    
    # Datos N0 de ejemplo con metadatos
    sample_n0 = {
        'cliente': 'EMPRESA TEST SL',
        'direccion': 'CALLE FALSA 123',
        'cups': 'ES0031408000000000001JN',
        'consumo_facturado_kwh': 1500.0,
        'confianza_cliente': 0.95,
        'patron_cliente': 'EMPRESA.*SL',
        'confianza_direccion': 0.88
    }
    
    # Test pipeline completo
    cleaned = clean_n0_metadata(sample_n0)
    n1_base = map_n0_to_n1_base(cleaned)
    
    sample_enrichment = {
        'latitud': 40.4168,
        'longitud': -3.7038,
        'precio_omie_kwh': 0.12
    }
    
    n1_final = add_enrichment_fields(n1_base, sample_enrichment)
    is_valid = validate_n1_structure(n1_final)
    
    print(f"Pipeline test: {'✓ ÉXITO' if is_valid else '✗ ERROR'}")
    print(f"Campos N1 final: {len(n1_final)}")
