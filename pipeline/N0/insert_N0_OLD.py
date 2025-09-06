#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Inserción N0 - Modo Prueba
Inserta datos JSON de facturas en la base de datos N0 sin ensuciar la BD real.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Importar conexiones centralizadas - desde pipeline/N0 ir a motores/db_watioverse/core
core_path = Path(__file__).parent.parent / 'core'  # ../core desde pipeline/N0
if not core_path.exists():
    core_path = Path(__file__).parent.parent.parent / 'core'  # ../../core como fallback
sys.path.insert(0, str(core_path))

# Import con manejo de errores
try:
    from db_connections import db_manager
    logger = logging.getLogger(__name__)
    logger.info("✅ Conexiones centralizadas cargadas correctamente")
except ImportError as e:
    logging.error(f"❌ Error importando db_connections: {e}")
    logging.error(f"Buscando en: {core_path}")
    logging.error(f"Archivo existe: {(core_path / 'db_connections.py').exists()}")
    raise

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class InsercionResult:
    """Resultado de una inserción."""
    archivo: str
    exito: bool
    registros_insertados: int
    errores: List[str]
    tiempo_procesamiento: float

class N0Inserter:
    """Insertador de datos N0 con conexiones centralizadas."""
    
    def __init__(self, modo_prueba: bool = True):
        self.modo_prueba = modo_prueba
        self.directorio_data = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out"
        self.resultados = []
        
        if not modo_prueba:
            logger.warning("⚠️ MODO PRODUCCIÓN ACTIVADO - Se insertará en BD real")
            # Verificar conexión N0
            self._verificar_conexion_n0()
        else:
            logger.info("✅ MODO PRUEBA ACTIVADO - Solo simulación")
    
    def _verificar_conexion_n0(self):
        """Verifica que la conexión N0 esté disponible."""
        try:
            with db_manager.transaction('N0') as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                if result:
                    logger.info("✅ Conexión BD N0 verificada")
        except Exception as e:
            logger.error(f"❌ Error verificando conexión BD N0: {e}")
            raise
    
    def extraer_valor_seguro(self, datos: dict, ruta: str, valor_defecto: Any = None) -> Any:
        """Extrae valor de un diccionario anidado de forma segura."""
        try:
            partes = ruta.split('.')
            valor_actual = datos
            
            for parte in partes:
                if isinstance(valor_actual, dict) and parte in valor_actual:
                    valor_actual = valor_actual[parte]
                else:
                    return valor_defecto
            
            # Si es un dict con 'value', extraer el valor
            if isinstance(valor_actual, dict) and 'value' in valor_actual:
                return valor_actual['value']
            
            resultado = valor_actual if valor_actual is not None else valor_defecto
            
            # Limpiar espacios en CUPS para cumplir límite de longitud
            if isinstance(resultado, str) and ('ES' in resultado and len(resultado) > 22):
                resultado = resultado.replace(' ', '')
            
            return resultado
            
        except Exception as e:
            logger.debug(f"Error extrayendo {ruta}: {e}")
            return valor_defecto
    
    def _convertir_fecha(self, fecha_str: str) -> str:
        """Convierte string de fecha a formato PostgreSQL (YYYY-MM-DD)."""
        if not fecha_str:
            return None
        try:
            # Si ya está en formato YYYY-MM-DD, devolverla
            if isinstance(fecha_str, str) and len(fecha_str) >= 8:
                if '/' in fecha_str:
                    # Convertir DD/MM/YYYY a YYYY-MM-DD
                    partes = fecha_str.split('/')
                    if len(partes) == 3:
                        dia, mes, año = partes
                        return f"{año}-{mes.zfill(2)}-{dia.zfill(2)}"
                elif '-' in fecha_str and fecha_str.count('-') == 2:
                    # Ya está en formato correcto
                    return fecha_str
            return None
        except Exception:
            return None
    
    def mapear_datos_client(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos de cliente desde JSON a estructura BD - MAPEO EXPANDIDO."""
        client_data = self.extraer_valor_seguro(datos_json, 'client', {})
        nif_data = self.extraer_valor_seguro(client_data, 'nif_titular', {})
        
        return {
            'nombre_cliente': self.extraer_valor_seguro(client_data, 'nombre_cliente') or 
                            self.extraer_valor_seguro(client_data, 'titular') or
                            self.extraer_valor_seguro(client_data, 'nombre_titular') or
                            self.extraer_valor_seguro(datos_json, 'titular_contrato'),
            'nif_titular_value': self.extraer_valor_seguro(nif_data, 'value') or
                               self.extraer_valor_seguro(client_data, 'nif_titular_value') or
                               self.extraer_valor_seguro(client_data, 'nif') or
                               self.extraer_valor_seguro(datos_json, 'nif_titular'),
            'nif_titular_confidence': self.extraer_valor_seguro(nif_data, 'confidence') or
                                    self.extraer_valor_seguro(client_data, 'nif_titular_confidence'),
            'nif_titular_pattern': self.extraer_valor_seguro(nif_data, 'pattern') or
                                 self.extraer_valor_seguro(client_data, 'nif_titular_pattern'),
            'nif_titular_source': self.extraer_valor_seguro(nif_data, 'source') or
                                self.extraer_valor_seguro(client_data, 'nif_titular_source')
        }
    
    def mapear_datos_provider(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos del proveedor desde JSON a estructura BD."""
        return {
            'email_proveedor': self.extraer_valor_seguro(datos_json, 'provider.email_proveedor'),
            'web_proveedor': self.extraer_valor_seguro(datos_json, 'provider.web_proveedor'),
            'entidad_bancaria': self.extraer_valor_seguro(datos_json, 'provider.entidad_bancaria'),
            'datos_bancarios_iban': self.extraer_valor_seguro(datos_json, 'provider.datos_bancarios_iban')
        }
    
    def mapear_datos_supply_point(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos del punto de suministro desde JSON a estructura BD - MAPEO EXPANDIDO."""
        supply_point_data = self.extraer_valor_seguro(datos_json, 'supply_point', {})
        
        return {
            'cups': self.extraer_valor_seguro(supply_point_data, 'cups') or 
                   self.extraer_valor_seguro(datos_json, 'contract.cups_electricidad') or
                   self.extraer_valor_seguro(datos_json, 'contract_3x3.cups_electricidad') or
                   self.extraer_valor_seguro(datos_json, 'contract_2x3.cups_electricidad') or
                   self.extraer_valor_seguro(datos_json, 'cups'),
            'numero_contrato_poliza': self.extraer_valor_seguro(supply_point_data, 'numero_contrato_poliza') or
                                    self.extraer_valor_seguro(supply_point_data, 'poliza') or
                                    self.extraer_valor_seguro(datos_json, 'numero_poliza')
        }
    
    def mapear_datos_supply_address(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea dirección de suministro desde JSON a estructura BD - MAPEO EXPANDIDO."""
        # Buscar datos de dirección en múltiples ubicaciones
        address_paths = [
            'supply_point.datos_suministro.direccion_suministro',
            'supply_address',
            'direccion_suministro', 
            'address',
            'supply_point.address'
        ]
        
        address_data = {}
        for path in address_paths:
            data = self.extraer_valor_seguro(datos_json, path, {})
            if data:
                address_data = data
                break
        
        return {
            'codigo_postal': self.extraer_valor_seguro(address_data, 'codigo_postal') or
                           self.extraer_valor_seguro(address_data, 'cp') or
                           self.extraer_valor_seguro(address_data, 'postal_code'),
            'comunidad_autonoma': self.extraer_valor_seguro(address_data, 'comunidad_autonoma') or
                                self.extraer_valor_seguro(address_data, 'ca') or
                                self.extraer_valor_seguro(address_data, 'autonomous_community'),
            'municipio': self.extraer_valor_seguro(address_data, 'municipio') or
                        self.extraer_valor_seguro(address_data, 'municipality'),
            'nombre_via': self.extraer_valor_seguro(address_data, 'nombre_via') or
                         self.extraer_valor_seguro(address_data, 'calle') or
                         self.extraer_valor_seguro(address_data, 'street_name'),
            'numero': self.extraer_valor_seguro(address_data, 'numero') or
                     self.extraer_valor_seguro(address_data, 'number'),
            'pais': self.extraer_valor_seguro(address_data, 'pais') or
                   self.extraer_valor_seguro(address_data, 'country'),
            'planta': self.extraer_valor_seguro(address_data, 'planta') or
                     self.extraer_valor_seguro(address_data, 'floor'),
            'poblacion': self.extraer_valor_seguro(address_data, 'poblacion') or
                        self.extraer_valor_seguro(address_data, 'city') or
                        self.extraer_valor_seguro(address_data, 'town'),
            'provincia': self.extraer_valor_seguro(address_data, 'provincia') or
                        self.extraer_valor_seguro(address_data, 'province'),
            'puerta': self.extraer_valor_seguro(address_data, 'puerta') or
                     self.extraer_valor_seguro(address_data, 'door'),
            'tipo_via': self.extraer_valor_seguro(address_data, 'tipo_via') or
                       self.extraer_valor_seguro(address_data, 'street_type')
        }
    
    def mapear_datos_contract(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos del contrato desde JSON a estructura BD."""
        # Intentar diferentes rutas para los datos del contrato
        contract_paths = ['contract_3x3', 'contract_2x3', 'contract']
        
        datos_contract = {}
        for path in contract_paths:
            if path in datos_json:
                datos_contract = datos_json[path]
                break
        
        return {
            'comercializadora': self.extraer_valor_seguro(datos_contract, 'comercializadora') or
                              self.extraer_valor_seguro(datos_json, 'comercializadora'),
            'numero_contrato_comercializadora': self.extraer_valor_seguro(datos_contract, 'numero_contrato_comercializadora') or
                                               self.extraer_valor_seguro(datos_contract, 'numero_contrato'),
            'fecha_inicio_contrato': self._convertir_fecha(self.extraer_valor_seguro(datos_contract, 'fecha_inicio_contrato')),
            'fecha_fin_contrato': self._convertir_fecha(self.extraer_valor_seguro(datos_contract, 'fecha_fin_contrato')),
            'distribuidora': self.extraer_valor_seguro(datos_contract, 'distribuidora') or
                           self.extraer_valor_seguro(datos_json, 'distribuidora'),
            'numero_contrato_distribuidora': self.extraer_valor_seguro(datos_contract, 'numero_contrato_distribuidora'),
            'cups_electricidad': self.extraer_valor_seguro(datos_contract, 'cups_electricidad') or 
                               self.extraer_valor_seguro(datos_contract, 'cups') or
                               self.extraer_valor_seguro(datos_json, 'cups'),
            'nombre_producto': self.extraer_valor_seguro(datos_contract, 'nombre_producto') or
                             self.extraer_valor_seguro(datos_contract, 'producto'),
            'mercado': self.extraer_valor_seguro(datos_contract, 'mercado') or
                      self.extraer_valor_seguro(datos_contract, 'tipo_mercado'),
            'tarifa_acceso': self.extraer_valor_seguro(datos_contract, 'tarifa_acceso') or
                           self.extraer_valor_seguro(datos_contract, 'tarifa'),
            # Potencias contratadas P1-P6
            'potencia_contratada_p1': self.extraer_valor_seguro(datos_contract, 'potencia_contratada_p1') or
                                    self.extraer_valor_seguro(datos_contract, 'potencia_p1'),
            'potencia_contratada_p2': self.extraer_valor_seguro(datos_contract, 'potencia_contratada_p2') or
                                    self.extraer_valor_seguro(datos_contract, 'potencia_p2'),
            'potencia_contratada_p3': self.extraer_valor_seguro(datos_contract, 'potencia_contratada_p3') or
                                    self.extraer_valor_seguro(datos_contract, 'potencia_p3'),
            'potencia_contratada_p4': self.extraer_valor_seguro(datos_contract, 'potencia_contratada_p4') or
                                    self.extraer_valor_seguro(datos_contract, 'potencia_p4'),
            'potencia_contratada_p5': self.extraer_valor_seguro(datos_contract, 'potencia_contratada_p5') or
                                    self.extraer_valor_seguro(datos_contract, 'potencia_p5'),
            'potencia_contratada_p6': self.extraer_valor_seguro(datos_contract, 'potencia_contratada_p6') or
                                    self.extraer_valor_seguro(datos_contract, 'potencia_p6'),
            # Precios unitarios de potencia P1-P6
            'precio_unitario_potencia_p1': self.extraer_valor_seguro(datos_contract, 'precio_unitario_potencia_p1') or
                                         self.extraer_valor_seguro(datos_contract, 'precio_potencia_p1'),
            'precio_unitario_potencia_p2': self.extraer_valor_seguro(datos_contract, 'precio_unitario_potencia_p2') or
                                         self.extraer_valor_seguro(datos_contract, 'precio_potencia_p2'),
            'precio_unitario_potencia_p3': self.extraer_valor_seguro(datos_contract, 'precio_unitario_potencia_p3') or
                                         self.extraer_valor_seguro(datos_contract, 'precio_potencia_p3'),
            'precio_unitario_potencia_p4': self.extraer_valor_seguro(datos_contract, 'precio_unitario_potencia_p4') or
                                         self.extraer_valor_seguro(datos_contract, 'precio_potencia_p4'),
            'precio_unitario_potencia_p5': self.extraer_valor_seguro(datos_contract, 'precio_unitario_potencia_p5') or
                                         self.extraer_valor_seguro(datos_contract, 'precio_potencia_p5'),
            'precio_unitario_potencia_p6': self.extraer_valor_seguro(datos_contract, 'precio_unitario_potencia_p6') or
                                         self.extraer_valor_seguro(datos_contract, 'precio_potencia_p6'),
        }
    
    def mapear_datos_energy_consumption(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos de consumo energético desde JSON a estructura BD - MAPEO EXPANDIDO."""
        # Buscar datos de consumo en múltiples ubicaciones
        consumo_paths = ['energy_consumption', 'consumo_energia', 'consumption']
        consumo_data = {}
        
        for path in consumo_paths:
            if path in datos_json:
                consumo_data = datos_json[path]
                break
        
        return {
            'inicio_periodo': self._convertir_fecha(self.extraer_valor_seguro(consumo_data, 'inicio_periodo') or
                                                   self.extraer_valor_seguro(consumo_data, 'fecha_inicio')),
            'fin_periodo': self._convertir_fecha(self.extraer_valor_seguro(consumo_data, 'fin_periodo') or
                                                self.extraer_valor_seguro(consumo_data, 'fecha_fin')),
            'consumo_medido_kwh': self.extraer_valor_seguro(consumo_data, 'consumo_medido_kwh') or
                                 self.extraer_valor_seguro(consumo_data, 'consumo_real_kwh'),
            'consumo_facturado_kwh': self.extraer_valor_seguro(consumo_data, 'consumo_facturado_kwh') or
                                    self.extraer_valor_seguro(consumo_data, 'consumo_kwh'),
            'consumo_kwh': self.extraer_valor_seguro(consumo_data, 'consumo_kwh') or
                          self.extraer_valor_seguro(consumo_data, 'consumo_facturado_kwh') or
                          self.extraer_valor_seguro(consumo_data, 'consumo_medido_kwh'),
            # Precios por componente
            'precio_peaje_eur_kwh': self.extraer_valor_seguro(consumo_data, 'precio_peaje_eur_kwh') or
                                   self.extraer_valor_seguro(consumo_data, 'precio_peaje'),
            'precio_energia_eur_kwh': self.extraer_valor_seguro(consumo_data, 'precio_energia_eur_kwh') or
                                     self.extraer_valor_seguro(consumo_data, 'precio_energia'),
            'precio_cargos_eur_kwh': self.extraer_valor_seguro(consumo_data, 'precio_cargos_eur_kwh') or
                                    self.extraer_valor_seguro(consumo_data, 'precio_cargos'),
            'margen_comercializadora_eur_kwh': self.extraer_valor_seguro(consumo_data, 'margen_comercializadora_eur_kwh') or
                                              self.extraer_valor_seguro(consumo_data, 'margen_comercializadora'),
            'precio_total_energia_eur_kwh': self.extraer_valor_seguro(consumo_data, 'precio_total_energia_eur_kwh') or
                                           self.extraer_valor_seguro(consumo_data, 'precio_total'),
            # Costes por componente
            'coste_peaje_eur': self.extraer_valor_seguro(consumo_data, 'coste_peaje_eur') or
                              self.extraer_valor_seguro(consumo_data, 'coste_peaje'),
            'coste_energia_eur': self.extraer_valor_seguro(consumo_data, 'coste_energia_eur') or
                                self.extraer_valor_seguro(consumo_data, 'coste_energia'),
            'coste_cargos_eur': self.extraer_valor_seguro(consumo_data, 'coste_cargos_eur') or
                               self.extraer_valor_seguro(consumo_data, 'coste_cargos'),
            'coste_margen_comercializadora_eur': self.extraer_valor_seguro(consumo_data, 'coste_margen_comercializadora_eur') or
                                                self.extraer_valor_seguro(consumo_data, 'coste_margen_comercializadora'),
            'coste_total_energia_eur': self.extraer_valor_seguro(consumo_data, 'coste_total_energia_eur') or
                                      self.extraer_valor_seguro(consumo_data, 'coste_total')
        }
    
    def mapear_datos_power_term(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos del término de potencia desde JSON a estructura BD."""
        potencia_data = self.extraer_valor_seguro(datos_json, 'termino_potencia', {})
        
        return {
            'periodo': self.extraer_valor_seguro(potencia_data, 'periodo', 'P1'),
            'potencia_contratada_kw': self.extraer_valor_seguro(potencia_data, 'potencia_contratada_kw'),
            'dias_facturacion': self.extraer_valor_seguro(potencia_data, 'dias_facturacion'),
            'precio_potencia_eur_kw_dia': self.extraer_valor_seguro(potencia_data, 'precio_potencia_eur_kw_dia'),
            'coste_potencia_eur': self.extraer_valor_seguro(potencia_data, 'coste_potencia_eur')
        }
    
    def mapear_datos_invoice(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos de factura desde JSON a estructura BD - MAPEO COMPLETO."""
        # Buscar datos invoice en múltiples ubicaciones
        invoice_paths = ["invoice", "invoice_2x3", "factura"]
        invoice_data = {}
        for path in invoice_paths:
            if path in datos_json:
                invoice_data = datos_json[path]
                break

        return {
            'año': self.extraer_valor_seguro(invoice_data, 'año') or self.extraer_valor_seguro(invoice_data, 'ano'),
            'fecha_inicio_periodo': self._convertir_fecha(self.extraer_valor_seguro(invoice_data, 'fecha_inicio_periodo')),
            'fecha_fin_periodo': self._convertir_fecha(self.extraer_valor_seguro(invoice_data, 'fecha_fin_periodo')),
            'dias_periodo_facturado': self.extraer_valor_seguro(invoice_data, 'dias_periodo_facturado'),
            'numero_factura_rectificada': self.extraer_valor_seguro(invoice_data, 'numero_factura_rectificada'),
            'fecha_cargo': self._convertir_fecha(self.extraer_valor_seguro(invoice_data, 'fecha_cargo')),
            'total_a_pagar': self.extraer_valor_seguro(invoice_data, 'total_a_pagar'),
            'tipo_iva': self.extraer_valor_seguro(invoice_data, 'tipo_iva'),
            'importe_iva': self.extraer_valor_seguro(invoice_data, 'importe_iva'),
            'porcentaje_impuesto_electricidad': self.extraer_valor_seguro(invoice_data, 'porcentaje_impuesto_electricidad'),
            'importe_impuesto_electricidad': self.extraer_valor_seguro(invoice_data, 'importe_impuesto_electricidad'),
            'bono_social': self.extraer_valor_seguro(invoice_data, 'bono_social'),
            'coste_energia_total': self.extraer_valor_seguro(invoice_data, 'coste_energia_total'),
            'coste_potencia_total': self.extraer_valor_seguro(invoice_data, 'coste_potencia_total'),
            'coste_otro_concepto': self.extraer_valor_seguro(invoice_data, 'coste_otro_concepto'),
            'coste_otro_servicio': self.extraer_valor_seguro(invoice_data, 'coste_otro_servicio'),
            'coste_promedio_diario_eur': self.extraer_valor_seguro(invoice_data, 'coste_promedio_diario_eur'),
            'alquiler_contador': self.extraer_valor_seguro(invoice_data, 'alquiler_contador'),
            'ajuste_mecanismo_iberico': self.extraer_valor_seguro(invoice_data, 'ajuste_mecanismo_iberico'),
            'descuento_energia': self.extraer_valor_seguro(invoice_data, 'descuento_energia'),
            'descuento_potencia': self.extraer_valor_seguro(invoice_data, 'descuento_potencia'),
            'descuento_servicio': self.extraer_valor_seguro(invoice_data, 'descuento_servicio'),
            'descuento_otro_concepto': self.extraer_valor_seguro(invoice_data, 'descuento_otro_concepto'),
            # Consumos P1-P6 - mapeo expandido
            'consumo_kwh_p1': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_kwh_p1') or self.extraer_valor_seguro(invoice_data, 'consumo_medido_kwh_p1'),
            'consumo_kwh_p2': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_kwh_p2') or self.extraer_valor_seguro(invoice_data, 'consumo_medido_kwh_p2'),
            'consumo_kwh_p3': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_kwh_p3') or self.extraer_valor_seguro(invoice_data, 'consumo_medido_kwh_p3'),
            'consumo_kwh_p4': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_kwh_p4') or self.extraer_valor_seguro(invoice_data, 'consumo_medido_kwh_p4'),
            'consumo_kwh_p5': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_kwh_p5') or self.extraer_valor_seguro(invoice_data, 'consumo_medido_kwh_p5'),
            'consumo_kwh_p6': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_kwh_p6') or self.extraer_valor_seguro(invoice_data, 'consumo_medido_kwh_p6'),
            # Precios P1-P6
            'precio_peaje_p1': self.extraer_valor_seguro(invoice_data, 'precio_peaje_p1'),
            'precio_peaje_p2': self.extraer_valor_seguro(invoice_data, 'precio_peaje_p2'),
            'precio_peaje_p3': self.extraer_valor_seguro(invoice_data, 'precio_peaje_p3'),
            'precio_energia_p1': self.extraer_valor_seguro(invoice_data, 'precio_energia_p1'),
            'precio_energia_p2': self.extraer_valor_seguro(invoice_data, 'precio_energia_p2'),
            'precio_energia_p3': self.extraer_valor_seguro(invoice_data, 'precio_energia_p3'),
            'precio_cargos_energia_p1': self.extraer_valor_seguro(invoice_data, 'precio_cargos_energia_p1'),
            'precio_cargos_energia_p2': self.extraer_valor_seguro(invoice_data, 'precio_cargos_energia_p2'),
            'precio_cargos_energia_p3': self.extraer_valor_seguro(invoice_data, 'precio_cargos_energia_p3'),
            'margen_comercializadora_p1': self.extraer_valor_seguro(invoice_data, 'margen_comercializadora_p1'),
            'margen_comercializadora_p2': self.extraer_valor_seguro(invoice_data, 'margen_comercializadora_p2'),
            'margen_comercializadora_p3': self.extraer_valor_seguro(invoice_data, 'margen_comercializadora_p3'),
            # Costes P1-P3
            'coste_peaje_p1': self.extraer_valor_seguro(invoice_data, 'coste_peaje_p1'),
            'coste_peaje_p2': self.extraer_valor_seguro(invoice_data, 'coste_peaje_p2'),
            'coste_peaje_p3': self.extraer_valor_seguro(invoice_data, 'coste_peaje_p3'),
            'coste_energia_p1': self.extraer_valor_seguro(invoice_data, 'coste_energia_p1'),
            'coste_energia_p2': self.extraer_valor_seguro(invoice_data, 'coste_energia_p2'),
            'coste_energia_p3': self.extraer_valor_seguro(invoice_data, 'coste_energia_p3'),
            'coste_cargos_energia_p1': self.extraer_valor_seguro(invoice_data, 'coste_cargos_energia_p1'),
            'coste_cargos_energia_p2': self.extraer_valor_seguro(invoice_data, 'coste_cargos_energia_p2'),
            'coste_cargos_energia_p3': self.extraer_valor_seguro(invoice_data, 'coste_cargos_energia_p3'),
            'coste_margen_comercializadora_p1': self.extraer_valor_seguro(invoice_data, 'coste_margen_comercializadora_p1'),
            'coste_margen_comercializadora_p2': self.extraer_valor_seguro(invoice_data, 'coste_margen_comercializadora_p2'),
            'coste_margen_comercializadora_p3': self.extraer_valor_seguro(invoice_data, 'coste_margen_comercializadora_p3'),
            'coste_total_energia_p1': self.extraer_valor_seguro(invoice_data, 'coste_total_energia_p1'),
            'coste_total_energia_p2': self.extraer_valor_seguro(invoice_data, 'coste_total_energia_p2'),
            'coste_total_energia_p3': self.extraer_valor_seguro(invoice_data, 'coste_total_energia_p3'),
            # Potencia
            'consumo_promedio_diario_kwh': self.extraer_valor_seguro(invoice_data, 'consumo_promedio_diario_kwh'),
            'potencia_maxima_demandada_factura_p1': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_factura_p1'),
            'potencia_maxima_demandada_factura_p2': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_factura_p2'),
            'potencia_maxima_demandada_factura_p3': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_factura_p3'),
            'potencia_maxima_demandada_factura_p4': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_factura_p4'),
            'potencia_maxima_demandada_factura_p5': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_factura_p5'),
            'potencia_maxima_demandada_factura_p6': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_factura_p6'),
            # Reactiva
            'energia_reactiva_facturar_p1': self.extraer_valor_seguro(invoice_data, 'energia_reactiva_facturar_p1'),
            'penalizacion_reactiva_p1': self.extraer_valor_seguro(invoice_data, 'penalizacion_reactiva_p1'),
            'energia_reactiva_facturar_p2': self.extraer_valor_seguro(invoice_data, 'energia_reactiva_facturar_p2'),
            'penalizacion_reactiva_p2': self.extraer_valor_seguro(invoice_data, 'penalizacion_reactiva_p2'),
            'energia_reactiva_facturar_p3': self.extraer_valor_seguro(invoice_data, 'energia_reactiva_facturar_p3'),
            'penalizacion_reactiva_p3': self.extraer_valor_seguro(invoice_data, 'penalizacion_reactiva_p3'),
            'energia_reactiva_facturar_p4': self.extraer_valor_seguro(invoice_data, 'energia_reactiva_facturar_p4'),
            'penalizacion_reactiva_p4': self.extraer_valor_seguro(invoice_data, 'penalizacion_reactiva_p4'),
            'energia_reactiva_facturar_p5': self.extraer_valor_seguro(invoice_data, 'energia_reactiva_facturar_p5'),
            'penalizacion_reactiva_p5': self.extraer_valor_seguro(invoice_data, 'penalizacion_reactiva_p5'),
            'energia_reactiva_facturar_p6': self.extraer_valor_seguro(invoice_data, 'energia_reactiva_facturar_p6'),
            'penalizacion_reactiva_p6': self.extraer_valor_seguro(invoice_data, 'penalizacion_reactiva_p6'),
            # Autoconsumo
            'autoconsumo': self.extraer_valor_seguro(invoice_data, 'autoconsumo'),
            'energia_vertida_kwh': self.extraer_valor_seguro(invoice_data, 'energia_vertida_kwh'),
            'importe_compensacion_excedentes': self.extraer_valor_seguro(invoice_data, 'importe_compensacion_excedentes'),
            # Número factura
            'numero_factura': self.extraer_valor_seguro(datos_json, 'numero_factura') or self.extraer_valor_seguro(invoice_data, 'numero_factura'),
        }
    
    def mapear_datos_metadata(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea metadatos desde JSON a estructura BD - MAPEO EXPANDIDO."""
        metadata_data = self.extraer_valor_seguro(datos_json, 'metadata', {})
        
        return {
            'extraction_timestamp': self.extraer_valor_seguro(metadata_data, 'extraction_timestamp') or
                                  self.extraer_valor_seguro(metadata_data, 'timestamp') or
                                  self.extraer_valor_seguro(datos_json, 'timestamp'),
            'extraction_method': self.extraer_valor_seguro(metadata_data, 'extraction_method') or
                               self.extraer_valor_seguro(metadata_data, 'method') or
                               'N0_pipeline',
            'migration_applied': self.extraer_valor_seguro(metadata_data, 'migration_applied', False),
            'ai_fields_in_automejora': self.extraer_valor_seguro(metadata_data, 'ai_fields_in_automejora', False),
            'detectors_available': self.extraer_valor_seguro(metadata_data, 'detectors_available', True),
            'tables_processed': self.extraer_valor_seguro(metadata_data, 'tables_processed') or
                              self.extraer_valor_seguro(metadata_data, 'processed_tables'),
            'text_length': self.extraer_valor_seguro(metadata_data, 'text_length') or
                         self.extraer_valor_seguro(metadata_data, 'total_text_length'),
            'duration_ms': self.extraer_valor_seguro(metadata_data, 'duration_ms') or
                         self.extraer_valor_seguro(metadata_data, 'processing_time_ms'),
            'total_time': self.extraer_valor_seguro(metadata_data, 'total_time') or
                        self.extraer_valor_seguro(metadata_data, 'total_processing_time'),
            'reading_time': self.extraer_valor_seguro(metadata_data, 'reading_time') or
                          self.extraer_valor_seguro(metadata_data, 'file_reading_time'),
            'classification_time': self.extraer_valor_seguro(metadata_data, 'classification_time') or
                                 self.extraer_valor_seguro(metadata_data, 'document_classification_time'),
            'metadata_extraction_time': self.extraer_valor_seguro(metadata_data, 'metadata_extraction_time') or
                                      self.extraer_valor_seguro(metadata_data, 'meta_extraction_time'),
            'schema_loading_time': self.extraer_valor_seguro(metadata_data, 'schema_loading_time') or
                                 self.extraer_valor_seguro(metadata_data, 'schema_load_time'),
            'data_extraction_time': self.extraer_valor_seguro(metadata_data, 'data_extraction_time') or
                                  self.extraer_valor_seguro(metadata_data, 'extraction_time'),
            'data_normalization_time': self.extraer_valor_seguro(metadata_data, 'data_normalization_time') or
                                     self.extraer_valor_seguro(metadata_data, 'normalization_time'),
            'data_transformation_time': self.extraer_valor_seguro(metadata_data, 'data_transformation_time') or
                                      self.extraer_valor_seguro(metadata_data, 'transformation_time'),
            'json_construction_time': self.extraer_valor_seguro(metadata_data, 'json_construction_time') or
                                    self.extraer_valor_seguro(metadata_data, 'json_build_time'),
            'extraction_confidence': self.extraer_valor_seguro(metadata_data, 'extraction_confidence') or
                                   self.extraer_valor_seguro(metadata_data, 'confidence_score'),
            'llm_provider': self.extraer_valor_seguro(metadata_data, 'llm_provider') or
                          self.extraer_valor_seguro(metadata_data, 'ai_provider') or
                          'N0_system',
            'llm_model': self.extraer_valor_seguro(metadata_data, 'llm_model') or
                       self.extraer_valor_seguro(metadata_data, 'ai_model') or
                       'N0_model'
        }
    
    def mapear_datos_documents(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos del documento principal desde JSON a estructura BD - MAPEO EXPANDIDO."""
        # Los IDs de foreign keys se asignarán después de las inserciones
        return {
            'id_cups': self.extraer_valor_seguro(datos_json, 'cups') or
                     self.extraer_valor_seguro(datos_json, 'contract.cups_electricidad') or  
                     self.extraer_valor_seguro(datos_json, 'contract_3x3.cups_electricidad') or
                     self.extraer_valor_seguro(datos_json, 'contract_2x3.cups_electricidad'),
            'id_cups_confianza': self.extraer_valor_seguro(datos_json, 'cups_confidence') or
                               self.extraer_valor_seguro(datos_json, 'contract.cups_confidence') or
                               0.95,  # Valor por defecto alto para N0
            'id_cups_pais': self.extraer_valor_seguro(datos_json, 'cups_country') or
                          self.extraer_valor_seguro(datos_json, 'country') or
                          'ES'  # España por defecto
        }

    def insertar_en_tabla(self, tabla: str, datos: Dict[str, Any]) -> bool:
        # Log detallado para depuración
        logger.info(f"[DEBUG] Intentando insertar en tabla '{tabla}': {datos}")
        """Inserta datos en tabla BD (real o simulación)."""
        if self.modo_prueba:
            logger.info(f"  📝 SIMULANDO inserción en tabla '{tabla}':")
            campos_no_nulos = {k: v for k, v in datos.items() if v is not None}
            for campo, valor in campos_no_nulos.items():
                logger.info(f"    - {campo}: {valor}")
            logger.info(f"  ✅ Simulación exitosa - {len(campos_no_nulos)} campos")
            return True
        else:
            # Inserción real en BD
            return self._insertar_real(tabla, datos)
    
    def _insertar_real(self, tabla: str, datos: Dict[str, Any]) -> bool:
        """Ejecuta inserción real usando conexiones centralizadas."""
        try:
            # Filtrar campos no nulos
            campos_no_nulos = {k: v for k, v in datos.items() if v is not None and v != ''}
            
            if not campos_no_nulos:
                logger.warning(f"  ⚠️ Tabla {tabla}: Sin datos válidos para insertar")
                return True
            
            # Construir consulta INSERT con ON CONFLICT para evitar duplicados
            campos = list(campos_no_nulos.keys())
            valores = list(campos_no_nulos.values())
            placeholders = ', '.join(['%s'] * len(valores))
            campos_str = ', '.join(campos)
            
            # Usar UPSERT para evitar errores de duplicado
            query = f"""INSERT INTO {tabla} ({campos_str}) 
                         VALUES ({placeholders})
                         ON CONFLICT DO NOTHING"""
            
            with db_manager.transaction('N0') as cursor:
                cursor.execute(query, valores)
                affected = cursor.rowcount
                if affected > 0:
                    logger.info(f"  ✅ INSERTADO en tabla '{tabla}': {len(campos)} campos")
                else:
                    logger.info(f"  🔄 DUPLICADO ignorado en tabla '{tabla}'")
                return True
                
        except Exception as e:
            logger.error(f"  ❌ Error insertando en tabla '{tabla}': {e}")
            return False
    
    def procesar_archivo_json(self, archivo_path: Path) -> InsercionResult:
        """Procesa un archivo JSON individual."""
        inicio_tiempo = datetime.now()
        errores = []
        registros_insertados = 0
        
        try:
            logger.info(f"📄 Procesando: {archivo_path.name}")
            
            # Cargar JSON
            with open(archivo_path, 'r', encoding='utf-8') as f:
                datos_json = json.load(f)
            
            # Mapear y simular inserción de cada tabla
            tablas_datos = {
                'client': self.mapear_datos_client(datos_json),
                'provider': self.mapear_datos_provider(datos_json),
                'supply_point': self.mapear_datos_supply_point(datos_json),
                'supply_address': self.mapear_datos_supply_address(datos_json),
                'contract': self.mapear_datos_contract(datos_json),
                'energy_consumption': self.mapear_datos_energy_consumption(datos_json),
                'power_term': self.mapear_datos_power_term(datos_json),
                'invoice': self.mapear_datos_invoice(datos_json)
            }
            
            # Insertar en cada tabla (las transacciones las maneja db_manager)
            for tabla, datos in tablas_datos.items():
                if self.insertar_en_tabla(tabla, datos):
                    registros_insertados += 1
                else:
                    errores.append(f"Error insertando en tabla {tabla}")
            
            tiempo_procesamiento = (datetime.now() - inicio_tiempo).total_seconds()
            
            return InsercionResult(
                archivo=archivo_path.name,
                exito=len(errores) == 0,
                registros_insertados=registros_insertados,
                errores=errores,
                tiempo_procesamiento=tiempo_procesamiento
            )
            
        except Exception as e:
            tiempo_procesamiento = (datetime.now() - inicio_tiempo).total_seconds()
            error_msg = f"Error procesando {archivo_path.name}: {str(e)}"
            logger.error(error_msg)
            
            return InsercionResult(
                archivo=archivo_path.name,
                exito=False,
                registros_insertados=0,
                errores=[error_msg],
                tiempo_procesamiento=tiempo_procesamiento
            )
    
    def procesar_directorio(self, limite_archivos: int = 3) -> List[InsercionResult]:
        """Procesa archivos JSON del directorio Data_out."""
        logger.info(f"🚀 INICIANDO PROCESAMIENTO N0 - MODO {'PRUEBA' if self.modo_prueba else 'PRODUCCIÓN'}")
        logger.info(f"📁 Directorio: {self.directorio_data}")
        
        # Buscar archivos JSON N0
        data_path = Path(self.directorio_data)
        archivos_json = list(data_path.glob("N0_*.json"))
        
        logger.info(f"📊 Encontrados {len(archivos_json)} archivos N0")
        
        if limite_archivos:
            archivos_json = archivos_json[:limite_archivos]
            logger.info(f"🎯 Procesando primeros {len(archivos_json)} archivos (modo prueba)")
        
        # Procesar cada archivo
        resultados = []
        for archivo in archivos_json:
            resultado = self.procesar_archivo_json(archivo)
            resultados.append(resultado)
            self.resultados.append(resultado)
        
        return resultados
    
    def generar_reporte(self) -> str:
        """Genera reporte de resultados."""
        if not self.resultados:
            return "No hay resultados para reportar."
        
        exitosos = [r for r in self.resultados if r.exito]
        fallidos = [r for r in self.resultados if not r.exito]
        
        reporte = []
        reporte.append("=" * 60)
        reporte.append("📋 REPORTE INSERCIÓN N0")
        reporte.append("=" * 60)
        reporte.append(f"📊 Total archivos procesados: {len(self.resultados)}")
        reporte.append(f"✅ Exitosos: {len(exitosos)}")
        reporte.append(f"❌ Fallidos: {len(fallidos)}")
        reporte.append(f"📈 Tasa de éxito: {len(exitosos)/len(self.resultados)*100:.1f}%")
        reporte.append("")
        
        if exitosos:
            reporte.append("✅ ARCHIVOS PROCESADOS EXITOSAMENTE:")
            for resultado in exitosos:
                reporte.append(f"  - {resultado.archivo}: {resultado.registros_insertados} tablas ({resultado.tiempo_procesamiento:.2f}s)")
        
        if fallidos:
            reporte.append("")
            reporte.append("❌ ARCHIVOS CON ERRORES:")
            for resultado in fallidos:
                reporte.append(f"  - {resultado.archivo}:")
                for error in resultado.errores:
                    reporte.append(f"    • {error}")
        
        tiempo_total = sum(r.tiempo_procesamiento for r in self.resultados)
        registros_total = sum(r.registros_insertados for r in self.resultados)
        
        reporte.append("")
        reporte.append(f"⏱️ Tiempo total: {tiempo_total:.2f} segundos")
        reporte.append(f"📝 Total registros insertados: {registros_total}")
        reporte.append("=" * 60)
        
        return "\n".join(reporte)

def main():
    """Función principal."""
    # Determinar modo según argumento
    modo_prueba = '--produccion' not in sys.argv
    
    print(f"🚀 INSERTADOR N0 - MODO {'PRUEBA' if modo_prueba else 'PRODUCCIÓN'}")
    print("=" * 50)
    
    # Crear insertador
    inserter = N0Inserter(modo_prueba=modo_prueba)
    
    try:
        # Procesar archivos
        limite = 3 if modo_prueba else None
        resultados = inserter.procesar_directorio(limite_archivos=limite)
        
        # Mostrar reporte
        reporte = inserter.generar_reporte()
        print(reporte)
        
        # Guardar reporte
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        modo_str = 'prueba' if modo_prueba else 'produccion'
        archivo_reporte = f"reporte_insercion_n0_{modo_str}_{timestamp}.txt"
        
        with open(archivo_reporte, 'w', encoding='utf-8') as f:
            f.write(reporte)
        
        print(f"\n📄 Reporte guardado: {archivo_reporte}")
        
        return len([r for r in resultados if r.exito]) == len(resultados)
    
    finally:
        # Las conexiones las maneja db_manager automáticamente
        pass

if __name__ == "__main__":
    main()
