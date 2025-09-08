#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mapeos centralizados para N0 - Extrae la lógica de mapeo del insertador
para mantener el código más limpio y mantenible.
"""
from typing import Dict, Any
import logging
import re

logger = logging.getLogger(__name__)

class MapeosN0:
    """Clase con todos los mapeos de datos N0."""
    
    def __init__(self):
        """Inicializa la clase de mapeos."""
        pass
    
    def _buscar_clave_con_sufijo(self, datos_json: dict, nombre_base: str) -> tuple:
        """
        Busca una clave con sufijo numérico (NxM) en el JSON.
        
        Args:
            datos_json: Diccionario JSON donde buscar
            nombre_base: Nombre base (ej: 'contract', 'invoice', 'metering')
            
        Returns:
            tuple: (clave_encontrada, datos) o (None, {})
        """
        # Primero buscar patrones con sufijos NxM
        patron = re.compile(rf'^{nombre_base}_\d+x\d+$')
        claves_con_sufijo = [k for k in datos_json.keys() if patron.match(k)]
        
        if claves_con_sufijo:
            # Ordenar para priorizar (opcional, usar primera coincidencia)
            clave = claves_con_sufijo[0]
            return clave, datos_json[clave]
        
        # Si no encuentra con sufijo, buscar sin sufijo
        if nombre_base in datos_json:
            return nombre_base, datos_json[nombre_base]
            
        # No encontrado
        return None, {}
    
    def extraer_valor_seguro(self, diccionario: dict, ruta: str, default=None) -> Any:
        """
        Extrae valor de diccionario anidado de forma segura.
        Soporta notación de puntos para rutas anidadas.
        """
        try:
            partes = ruta.split('.')
            valor = diccionario
            
            for parte in partes:
                if isinstance(valor, dict) and parte in valor:
                    valor = valor[parte]
                else:
                    return default
                    
            # Limpiar cadenas de espacios extra
            if isinstance(valor, str):
                valor = valor.strip()
                # Validación especial para CUPS - máximo 22 caracteres
                if 'cups' in ruta.lower() and len(valor) > 22:
                    logger.warning(f"CUPS excede 22 caracteres: {valor[:10]}... (largo: {len(valor)})")
                    valor = valor[:22]
                    
            return valor if valor else default
            
        except Exception:
            return default
    
    def _convertir_fecha(self, fecha_str: str) -> str:
        """Convierte fecha de DD/MM/YYYY a YYYY-MM-DD."""
        if not fecha_str:
            return None
            
        try:
            fecha_str = str(fecha_str).strip()
            if '/' in fecha_str:
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
        """Mapea datos de cliente - CORREGIDO para datos aplanados por flattener."""
        client_data = self.extraer_valor_seguro(datos_json, 'client', {})
        
        return {
            'nombre_cliente': client_data.get('nombre_cliente') or 
                            client_data.get('titular') or
                            client_data.get('nombre_titular') or
                            self.extraer_valor_seguro(datos_json, 'titular_contrato'),
            # Usar campos aplanados directamente (flattener ya procesó nif_titular)
            'nif_titular_value': client_data.get('nif_titular_value') or
                               client_data.get('nif') or
                               self.extraer_valor_seguro(datos_json, 'nif_titular'),
            'nif_titular_confidence': client_data.get('nif_titular_confidence'),
            'nif_titular_pattern': client_data.get('nif_titular_pattern'),
            'nif_titular_source': client_data.get('nif_titular_source')
        }
    
    def mapear_datos_provider(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos del proveedor - CORREGIDO para esquema BD real."""
        provider_data = self.extraer_valor_seguro(datos_json, 'provider', {})
        
        return {
            'nif_proveedor': provider_data.get('nif_proveedor'),
            'email_proveedor': provider_data.get('email_proveedor'),
            'web_proveedor': provider_data.get('web_proveedor'),
            'entidad_bancaria': provider_data.get('entidad_bancaria'),
            'datos_bancarios_iban': provider_data.get('datos_bancarios_iban')
        }
    
    def mapear_datos_direccion_fiscal(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea dirección fiscal desde JSON a tabla direccion_fiscal - CREADO."""
        provider_data = self.extraer_valor_seguro(datos_json, 'provider', {})
        direccion_data = self.extraer_valor_seguro(provider_data, 'direccion_fiscal', {})
        
        return {
            'provider_id': None,  # Se asociará posteriormente
            'codigo_postal': direccion_data.get('codigo_postal'),
            'comunidad_autonoma': direccion_data.get('comunidad_autonoma'),
            'municipio': direccion_data.get('municipio'),
            'nombre_via': direccion_data.get('nombre_via'),
            'numero': direccion_data.get('numero'),
            'pais': direccion_data.get('pais'),
            'planta': direccion_data.get('planta'),
            'poblacion': direccion_data.get('poblacion'),
            'provincia': direccion_data.get('provincia'),
            'puerta': direccion_data.get('puerta'),
            'tipo_via': direccion_data.get('tipo_via')
        }
    
    def mapear_datos_supply_point(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos del punto de suministro - CORREGIDO para esquema BD real."""
        supply_point_data = self.extraer_valor_seguro(datos_json, 'supply_point', {})
        contract_data = self.extraer_valor_seguro(datos_json, 'contract', {})
        
        return {
            'cups': supply_point_data.get('cups') or 
                   contract_data.get('cups_electricidad') or
                   self.extraer_valor_seguro(datos_json, 'cups'),
            # Campo aplanado por flattener desde datos_suministro
            'numero_contrato_poliza': supply_point_data.get('numero_contrato_poliza') or
                                    supply_point_data.get('poliza') or
                                    self.extraer_valor_seguro(datos_json, 'numero_poliza')
            # NOTA: direccion_suministro_* NO existe en esquema BD real - datos van a tabla supply_address
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
        """Mapea datos del contrato desde JSON a estructura BD.
        NOTA: Busca datos con sufijos XxX pero los inserta en tabla 'contract' sin sufijo."""
        # Buscar contract con cualquier sufijo numérico (NxM)
        clave_encontrada, datos_contract = self._buscar_clave_con_sufijo(datos_json, 'contract')
        
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
        """Mapea datos de factura desde JSON a estructura BD - MAPEO COMPLETO.
        NOTA: Busca datos con sufijos XxX pero los inserta en tabla 'invoice' sin sufijo."""
        # Buscar invoice con cualquier sufijo numérico (NxM)
        clave_encontrada, invoice_data = self._buscar_clave_con_sufijo(datos_json, 'invoice')
        
        # Si no encuentra invoice, buscar 'factura'
        if not invoice_data and 'factura' in datos_json:
            invoice_data = datos_json['factura']

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
            # Precios P1-P6 - EXPANDIDO COMPLETO
            'precio_peaje_p1': self.extraer_valor_seguro(invoice_data, 'precio_peaje_p1'),
            'precio_peaje_p2': self.extraer_valor_seguro(invoice_data, 'precio_peaje_p2'),
            'precio_peaje_p3': self.extraer_valor_seguro(invoice_data, 'precio_peaje_p3'),
            'precio_peaje_p4': self.extraer_valor_seguro(invoice_data, 'precio_peaje_p4'),
            'precio_peaje_p5': self.extraer_valor_seguro(invoice_data, 'precio_peaje_p5'),
            'precio_peaje_p6': self.extraer_valor_seguro(invoice_data, 'precio_peaje_p6'),
            'precio_energia_p1': self.extraer_valor_seguro(invoice_data, 'precio_energia_p1'),
            'precio_energia_p2': self.extraer_valor_seguro(invoice_data, 'precio_energia_p2'),
            'precio_energia_p3': self.extraer_valor_seguro(invoice_data, 'precio_energia_p3'),
            'precio_energia_p4': self.extraer_valor_seguro(invoice_data, 'precio_energia_p4'),
            'precio_energia_p5': self.extraer_valor_seguro(invoice_data, 'precio_energia_p5'),
            'precio_energia_p6': self.extraer_valor_seguro(invoice_data, 'precio_energia_p6'),
            'precio_cargos_energia_p1': self.extraer_valor_seguro(invoice_data, 'precio_cargos_energia_p1'),
            'precio_cargos_energia_p2': self.extraer_valor_seguro(invoice_data, 'precio_cargos_energia_p2'),
            'precio_cargos_energia_p3': self.extraer_valor_seguro(invoice_data, 'precio_cargos_energia_p3'),
            'precio_cargos_energia_p4': self.extraer_valor_seguro(invoice_data, 'precio_cargos_energia_p4'),
            'precio_cargos_energia_p5': self.extraer_valor_seguro(invoice_data, 'precio_cargos_energia_p5'),
            'precio_cargos_energia_p6': self.extraer_valor_seguro(invoice_data, 'precio_cargos_energia_p6'),
            'margen_comercializadora_p1': self.extraer_valor_seguro(invoice_data, 'margen_comercializadora_p1'),
            'margen_comercializadora_p2': self.extraer_valor_seguro(invoice_data, 'margen_comercializadora_p2'),
            'margen_comercializadora_p3': self.extraer_valor_seguro(invoice_data, 'margen_comercializadora_p3'),
            'margen_comercializadora_p4': self.extraer_valor_seguro(invoice_data, 'margen_comercializadora_p4'),
            'margen_comercializadora_p5': self.extraer_valor_seguro(invoice_data, 'margen_comercializadora_p5'),
            'margen_comercializadora_p6': self.extraer_valor_seguro(invoice_data, 'margen_comercializadora_p6'),
            # Costes P1-P6 EXPANDIDO
            'coste_peaje_p1': self.extraer_valor_seguro(invoice_data, 'coste_peaje_p1'),
            'coste_peaje_p2': self.extraer_valor_seguro(invoice_data, 'coste_peaje_p2'),
            'coste_peaje_p3': self.extraer_valor_seguro(invoice_data, 'coste_peaje_p3'),
            'coste_peaje_p4': self.extraer_valor_seguro(invoice_data, 'coste_peaje_p4'),
            'coste_peaje_p5': self.extraer_valor_seguro(invoice_data, 'coste_peaje_p5'),
            'coste_peaje_p6': self.extraer_valor_seguro(invoice_data, 'coste_peaje_p6'),
            'coste_energia_p1': self.extraer_valor_seguro(invoice_data, 'coste_energia_p1'),
            'coste_energia_p2': self.extraer_valor_seguro(invoice_data, 'coste_energia_p2'),
            'coste_energia_p3': self.extraer_valor_seguro(invoice_data, 'coste_energia_p3'),
            'coste_energia_p4': self.extraer_valor_seguro(invoice_data, 'coste_energia_p4'),
            'coste_energia_p5': self.extraer_valor_seguro(invoice_data, 'coste_energia_p5'),
            'coste_energia_p6': self.extraer_valor_seguro(invoice_data, 'coste_energia_p6'),
            'coste_cargos_energia_p1': self.extraer_valor_seguro(invoice_data, 'coste_cargos_energia_p1'),
            'coste_cargos_energia_p2': self.extraer_valor_seguro(invoice_data, 'coste_cargos_energia_p2'),
            'coste_cargos_energia_p3': self.extraer_valor_seguro(invoice_data, 'coste_cargos_energia_p3'),
            'coste_cargos_energia_p4': self.extraer_valor_seguro(invoice_data, 'coste_cargos_energia_p4'),
            'coste_cargos_energia_p5': self.extraer_valor_seguro(invoice_data, 'coste_cargos_energia_p5'),
            'coste_cargos_energia_p6': self.extraer_valor_seguro(invoice_data, 'coste_cargos_energia_p6'),
            'coste_margen_comercializadora_p1': self.extraer_valor_seguro(invoice_data, 'coste_margen_comercializadora_p1'),
            'coste_margen_comercializadora_p2': self.extraer_valor_seguro(invoice_data, 'coste_margen_comercializadora_p2'),
            'coste_margen_comercializadora_p3': self.extraer_valor_seguro(invoice_data, 'coste_margen_comercializadora_p3'),
            'coste_margen_comercializadora_p4': self.extraer_valor_seguro(invoice_data, 'coste_margen_comercializadora_p4'),
            'coste_margen_comercializadora_p5': self.extraer_valor_seguro(invoice_data, 'coste_margen_comercializadora_p5'),
            'coste_margen_comercializadora_p6': self.extraer_valor_seguro(invoice_data, 'coste_margen_comercializadora_p6'),
            'coste_total_energia_p1': self.extraer_valor_seguro(invoice_data, 'coste_total_energia_p1'),
            'coste_total_energia_p2': self.extraer_valor_seguro(invoice_data, 'coste_total_energia_p2'),
            'coste_total_energia_p3': self.extraer_valor_seguro(invoice_data, 'coste_total_energia_p3'),
            'coste_total_energia_p4': self.extraer_valor_seguro(invoice_data, 'coste_total_energia_p4'),
            'coste_total_energia_p5': self.extraer_valor_seguro(invoice_data, 'coste_total_energia_p5'),
            'coste_total_energia_p6': self.extraer_valor_seguro(invoice_data, 'coste_total_energia_p6'),
            # Potencia y Reactiva/Capacitiva EXPANDIDO
            'consumo_promedio_diario_kwh': self.extraer_valor_seguro(invoice_data, 'consumo_promedio_diario_kwh'),
            'potencia_facturada_p1': self.extraer_valor_seguro(invoice_data, 'potencia_facturada_p1'),
            'potencia_facturada_p2': self.extraer_valor_seguro(invoice_data, 'potencia_facturada_p2'),
            'potencia_facturada_p3': self.extraer_valor_seguro(invoice_data, 'potencia_facturada_p3'),
            'potencia_facturada_p4': self.extraer_valor_seguro(invoice_data, 'potencia_facturada_p4'),
            'potencia_facturada_p5': self.extraer_valor_seguro(invoice_data, 'potencia_facturada_p5'),
            'potencia_facturada_p6': self.extraer_valor_seguro(invoice_data, 'potencia_facturada_p6'),
            'potencia_maxima_demandada_factura_p1': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_factura_p1'),
            'potencia_maxima_demandada_factura_p2': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_factura_p2'),
            'potencia_maxima_demandada_factura_p3': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_factura_p3'),
            'potencia_maxima_demandada_factura_p4': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_factura_p4'),
            'potencia_maxima_demandada_factura_p5': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_factura_p5'),
            'potencia_maxima_demandada_factura_p6': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_factura_p6'),
            'potencia_maxima_demandada_año_kw_p1': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_año_kw_p1'),
            'potencia_maxima_demandada_año_kw_p2': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_año_kw_p2'),
            'potencia_maxima_demandada_año_kw_p3': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_año_kw_p3'),
            'potencia_maxima_demandada_año_kw_p4': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_año_kw_p4'),
            'potencia_maxima_demandada_año_kw_p5': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_año_kw_p5'),
            'potencia_maxima_demandada_año_kw_p6': self.extraer_valor_seguro(invoice_data, 'potencia_maxima_demandada_año_kw_p6'),
            # Consumos reactiva y capacitiva P1-P6
            'consumo_medido_reactiva_p1': self.extraer_valor_seguro(invoice_data, 'consumo_medido_reactiva_p1'),
            'consumo_medido_reactiva_p2': self.extraer_valor_seguro(invoice_data, 'consumo_medido_reactiva_p2'),
            'consumo_medido_reactiva_p3': self.extraer_valor_seguro(invoice_data, 'consumo_medido_reactiva_p3'),
            'consumo_medido_reactiva_p4': self.extraer_valor_seguro(invoice_data, 'consumo_medido_reactiva_p4'),
            'consumo_medido_reactiva_p5': self.extraer_valor_seguro(invoice_data, 'consumo_medido_reactiva_p5'),
            'consumo_medido_reactiva_p6': self.extraer_valor_seguro(invoice_data, 'consumo_medido_reactiva_p6'),
            'consumo_facturado_reactiva_p1': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_reactiva_p1'),
            'consumo_facturado_reactiva_p2': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_reactiva_p2'),
            'consumo_facturado_reactiva_p3': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_reactiva_p3'),
            'consumo_facturado_reactiva_p4': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_reactiva_p4'),
            'consumo_facturado_reactiva_p5': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_reactiva_p5'),
            'consumo_facturado_reactiva_p6': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_reactiva_p6'),
            'consumo_medido_capacitiva_p1': self.extraer_valor_seguro(invoice_data, 'consumo_medido_capacitiva_p1'),
            'consumo_medido_capacitiva_p2': self.extraer_valor_seguro(invoice_data, 'consumo_medido_capacitiva_p2'),
            'consumo_medido_capacitiva_p3': self.extraer_valor_seguro(invoice_data, 'consumo_medido_capacitiva_p3'),
            'consumo_medido_capacitiva_p4': self.extraer_valor_seguro(invoice_data, 'consumo_medido_capacitiva_p4'),
            'consumo_medido_capacitiva_p5': self.extraer_valor_seguro(invoice_data, 'consumo_medido_capacitiva_p5'),
            'consumo_medido_capacitiva_p6': self.extraer_valor_seguro(invoice_data, 'consumo_medido_capacitiva_p6'),
            'consumo_facturado_capacitiva_p1': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_capacitiva_p1'),
            'consumo_facturado_capacitiva_p2': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_capacitiva_p2'),
            'consumo_facturado_capacitiva_p3': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_capacitiva_p3'),
            'consumo_facturado_capacitiva_p4': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_capacitiva_p4'),
            'consumo_facturado_capacitiva_p5': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_capacitiva_p5'),
            'consumo_facturado_capacitiva_p6': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_capacitiva_p6'),
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
            # Autoconsumo y otros - CORREGIDO: campo real es 'autoconsumo'
            'autoconsumo': self.extraer_valor_seguro(invoice_data, 'autoconsumo') or
                          self.extraer_valor_seguro(invoice_data, 'self_consumption'),
            'energia_vertida_kwh': self.extraer_valor_seguro(invoice_data, 'energia_vertida_kwh'),
            'importe_compensacion_excedentes': self.extraer_valor_seguro(invoice_data, 'importe_compensacion_excedentes'),
            'url_qr_comparador_cnmc': self.extraer_valor_seguro(invoice_data, 'url_qr_comparador_cnmc'),
            # Potencia por período P1-P6 - precios y costes
            'precio_peaje_potencia_p1': self.extraer_valor_seguro(invoice_data, 'precio_peaje_potencia_p1'),
            'precio_peaje_potencia_p2': self.extraer_valor_seguro(invoice_data, 'precio_peaje_potencia_p2'),
            'precio_peaje_potencia_p3': self.extraer_valor_seguro(invoice_data, 'precio_peaje_potencia_p3'),
            'precio_peaje_potencia_p4': self.extraer_valor_seguro(invoice_data, 'precio_peaje_potencia_p4'),
            'precio_peaje_potencia_p5': self.extraer_valor_seguro(invoice_data, 'precio_peaje_potencia_p5'),
            'precio_peaje_potencia_p6': self.extraer_valor_seguro(invoice_data, 'precio_peaje_potencia_p6'),
            'precio_potencia_p1': self.extraer_valor_seguro(invoice_data, 'precio_potencia_p1'),
            'precio_potencia_p2': self.extraer_valor_seguro(invoice_data, 'precio_potencia_p2'),
            'precio_potencia_p3': self.extraer_valor_seguro(invoice_data, 'precio_potencia_p3'),
            'precio_potencia_p4': self.extraer_valor_seguro(invoice_data, 'precio_potencia_p4'),
            'precio_potencia_p5': self.extraer_valor_seguro(invoice_data, 'precio_potencia_p5'),
            'precio_potencia_p6': self.extraer_valor_seguro(invoice_data, 'precio_potencia_p6'),
            'precio_cargos_potencia_p1': self.extraer_valor_seguro(invoice_data, 'precio_cargos_potencia_p1'),
            'precio_cargos_potencia_p2': self.extraer_valor_seguro(invoice_data, 'precio_cargos_potencia_p2'),
            'precio_cargos_potencia_p3': self.extraer_valor_seguro(invoice_data, 'precio_cargos_potencia_p3'),
            'precio_cargos_potencia_p4': self.extraer_valor_seguro(invoice_data, 'precio_cargos_potencia_p4'),
            'precio_cargos_potencia_p5': self.extraer_valor_seguro(invoice_data, 'precio_cargos_potencia_p5'),
            'precio_cargos_potencia_p6': self.extraer_valor_seguro(invoice_data, 'precio_cargos_potencia_p6'),
            'margen_comercializadora_potencia_p1': self.extraer_valor_seguro(invoice_data, 'margen_comercializadora_potencia_p1'),
            'margen_comercializadora_potencia_p2': self.extraer_valor_seguro(invoice_data, 'margen_comercializadora_potencia_p2'),
            'margen_comercializadora_potencia_p3': self.extraer_valor_seguro(invoice_data, 'margen_comercializadora_potencia_p3'),
            'margen_comercializadora_potencia_p4': self.extraer_valor_seguro(invoice_data, 'margen_comercializadora_potencia_p4'),
            'margen_comercializadora_potencia_p5': self.extraer_valor_seguro(invoice_data, 'margen_comercializadora_potencia_p5'),
            'margen_comercializadora_potencia_p6': self.extraer_valor_seguro(invoice_data, 'margen_comercializadora_potencia_p6'),
            'precio_total_potencia_p1': self.extraer_valor_seguro(invoice_data, 'precio_total_potencia_p1'),
            'precio_total_potencia_p2': self.extraer_valor_seguro(invoice_data, 'precio_total_potencia_p2'),
            'precio_total_potencia_p3': self.extraer_valor_seguro(invoice_data, 'precio_total_potencia_p3'),
            'precio_total_potencia_p4': self.extraer_valor_seguro(invoice_data, 'precio_total_potencia_p4'),
            'precio_total_potencia_p5': self.extraer_valor_seguro(invoice_data, 'precio_total_potencia_p5'),
            'precio_total_potencia_p6': self.extraer_valor_seguro(invoice_data, 'precio_total_potencia_p6'),
            'coste_peaje_potencia_p1': self.extraer_valor_seguro(invoice_data, 'coste_peaje_potencia_p1'),
            'coste_peaje_potencia_p2': self.extraer_valor_seguro(invoice_data, 'coste_peaje_potencia_p2'),
            'coste_peaje_potencia_p3': self.extraer_valor_seguro(invoice_data, 'coste_peaje_potencia_p3'),
            'coste_peaje_potencia_p4': self.extraer_valor_seguro(invoice_data, 'coste_peaje_potencia_p4'),
            'coste_peaje_potencia_p5': self.extraer_valor_seguro(invoice_data, 'coste_peaje_potencia_p5'),
            'coste_peaje_potencia_p6': self.extraer_valor_seguro(invoice_data, 'coste_peaje_potencia_p6'),
            'coste_potencia_p1': self.extraer_valor_seguro(invoice_data, 'coste_potencia_p1'),
            'coste_potencia_p2': self.extraer_valor_seguro(invoice_data, 'coste_potencia_p2'),
            'coste_potencia_p3': self.extraer_valor_seguro(invoice_data, 'coste_potencia_p3'),
            'coste_potencia_p4': self.extraer_valor_seguro(invoice_data, 'coste_potencia_p4'),
            'coste_potencia_p5': self.extraer_valor_seguro(invoice_data, 'coste_potencia_p5'),
            'coste_potencia_p6': self.extraer_valor_seguro(invoice_data, 'coste_potencia_p6'),
            'coste_cargos_potencia_p1': self.extraer_valor_seguro(invoice_data, 'coste_cargos_potencia_p1'),
            'coste_cargos_potencia_p2': self.extraer_valor_seguro(invoice_data, 'coste_cargos_potencia_p2'),
            'coste_cargos_potencia_p3': self.extraer_valor_seguro(invoice_data, 'coste_cargos_potencia_p3'),
            'coste_cargos_potencia_p4': self.extraer_valor_seguro(invoice_data, 'coste_cargos_potencia_p4'),
            'coste_cargos_potencia_p5': self.extraer_valor_seguro(invoice_data, 'coste_cargos_potencia_p5'),
            'coste_cargos_potencia_p6': self.extraer_valor_seguro(invoice_data, 'coste_cargos_potencia_p6'),
            'coste_margen_comercializadora_potencia_p1': self.extraer_valor_seguro(invoice_data, 'coste_margen_comercializadora_potencia_p1'),
            'coste_margen_comercializadora_potencia_p2': self.extraer_valor_seguro(invoice_data, 'coste_margen_comercializadora_potencia_p2'),
            'coste_margen_comercializadora_potencia_p3': self.extraer_valor_seguro(invoice_data, 'coste_margen_comercializadora_potencia_p3'),
            'coste_margen_comercializadora_potencia_p4': self.extraer_valor_seguro(invoice_data, 'coste_margen_comercializadora_potencia_p4'),
            'coste_margen_comercializadora_potencia_p5': self.extraer_valor_seguro(invoice_data, 'coste_margen_comercializadora_potencia_p5'),
            'coste_margen_comercializadora_potencia_p6': self.extraer_valor_seguro(invoice_data, 'coste_margen_comercializadora_potencia_p6'),
            'coste_total_potencia_p1': self.extraer_valor_seguro(invoice_data, 'coste_total_potencia_p1'),
            'coste_total_potencia_p2': self.extraer_valor_seguro(invoice_data, 'coste_total_potencia_p2'),
            'coste_total_potencia_p3': self.extraer_valor_seguro(invoice_data, 'coste_total_potencia_p3'),
            'coste_total_potencia_p4': self.extraer_valor_seguro(invoice_data, 'coste_total_potencia_p4'),
            'coste_total_potencia_p5': self.extraer_valor_seguro(invoice_data, 'coste_total_potencia_p5'),
            'coste_total_potencia_p6': self.extraer_valor_seguro(invoice_data, 'coste_total_potencia_p6'),
            # Otros campos adicionales
            'fecha_emision': self._convertir_fecha(self.extraer_valor_seguro(invoice_data, 'fecha_emision')),
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

    def mapear_datos_metering(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos de medición de contadores desde JSON a estructura BD.
        NOTA: Busca datos con sufijos XxX pero los inserta en tabla 'metering' sin sufijo."""
        # Buscar metering con cualquier sufijo numérico (NxM)
        clave_encontrada, metering_data = self._buscar_clave_con_sufijo(datos_json, 'metering')
        
        # Si no encuentra metering, buscar 'medicion'
        if not metering_data and 'medicion' in datos_json:
            metering_data = datos_json['medicion']
        
        return {
            'fecha_lectura_inicio_contador': self._convertir_fecha(self.extraer_valor_seguro(metering_data, 'fecha_lectura_inicio_contador')),
            'fecha_lectura_fin_contador': self._convertir_fecha(self.extraer_valor_seguro(metering_data, 'fecha_lectura_fin_contador')),
            'numero_contador': self.extraer_valor_seguro(metering_data, 'numero_contador'),
            'tipo_lectura_contador': self.extraer_valor_seguro(metering_data, 'tipo_lectura_contador'),
            'lectura_anterior_contador_p1': self.extraer_valor_seguro(metering_data, 'lectura_anterior_contador_p1'),
            'lectura_anterior_contador_p2': self.extraer_valor_seguro(metering_data, 'lectura_anterior_contador_p2'),
            'lectura_anterior_contador_p3': self.extraer_valor_seguro(metering_data, 'lectura_anterior_contador_p3'),
            'lectura_actual_contador_p1': self.extraer_valor_seguro(metering_data, 'lectura_actual_contador_p1'),
            'lectura_actual_contador_p2': self.extraer_valor_seguro(metering_data, 'lectura_actual_contador_p2'),
            'lectura_actual_contador_p3': self.extraer_valor_seguro(metering_data, 'lectura_actual_contador_p3'),
        }

    def mapear_datos_sustainability(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos de sostenibilidad desde JSON a estructura BD."""
        sustainability_data = self.extraer_valor_seguro(datos_json, 'sustainability', {})
        
        return {
            'emisiones_co2_equivalente': self.extraer_valor_seguro(sustainability_data, 'emisiones_co2_equivalente'),
            'letra_escala_medioambiental': self.extraer_valor_seguro(sustainability_data, 'letra_escala_medioambiental'),
            'energia_origen_renovable': self.extraer_valor_seguro(sustainability_data, 'energia_origen_renovable'),
            'energia_origen_nuclear': self.extraer_valor_seguro(sustainability_data, 'energia_origen_nuclear'),
            'energia_origen_carbon': self.extraer_valor_seguro(sustainability_data, 'energia_origen_carbon'),
            'energia_origen_cc_gas_natural': self.extraer_valor_seguro(sustainability_data, 'energia_origen_cc_gas_natural'),
            'energia_origen_cogeneracion_alta_eficiencia': self.extraer_valor_seguro(sustainability_data, 'energia_origen_cogeneracion_alta_eficiencia'),
            'energia_origen_fuel_gas': self.extraer_valor_seguro(sustainability_data, 'energia_origen_fuel_gas'),
            'energia_origen_otras_no_renovables': self.extraer_valor_seguro(sustainability_data, 'energia_origen_otras_no_renovables'),
        }

    def mapear_datos_invoice_summary(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos de resumen de factura desde JSON a estructura BD."""
        summary_data = self.extraer_valor_seguro(datos_json, 'invoice_summary', {})
        impuestos = self.extraer_valor_seguro(summary_data, 'impuestos', [])
        
        # Extraer datos de impuestos (hasta 2 elementos)
        impuesto_1 = impuestos[0] if len(impuestos) > 0 else {}
        impuesto_2 = impuestos[1] if len(impuestos) > 1 else {}
        
        return {
            'subtotal_factura': self.extraer_valor_seguro(summary_data, 'subtotal_factura'),
            'total_factura': self.extraer_valor_seguro(summary_data, 'total_factura'),
            # Mapeo castellano → inglés para campos específicos BD
            'importe_total_potencia': self.extraer_valor_seguro(summary_data, 'importe_total_potencia'),
            'importe_total_energia': self.extraer_valor_seguro(summary_data, 'importe_total_energia'),
            'importe_total_reactiva': self.extraer_valor_seguro(summary_data, 'importe_total_reactiva'),
            'importe_total_excesos_potencia': self.extraer_valor_seguro(summary_data, 'importe_total_excesos_potencia'),
            'importe_total_autoconsumo': self.extraer_valor_seguro(summary_data, 'importe_total_autoconsumo'),
            'importe_impuesto_electrico': self.extraer_valor_seguro(summary_data, 'importe_impuesto_electrico'),
            'importe_alquiler_equipos': self.extraer_valor_seguro(summary_data, 'importe_alquiler_equipos'),
            'importe_otros_conceptos': self.extraer_valor_seguro(summary_data, 'importe_otros_conceptos'),
            'importe_total_iva': self.extraer_valor_seguro(summary_data, 'importe_total_iva'),
            # Impuesto 1
            'impuesto_1_base_imponible': self.extraer_valor_seguro(impuesto_1, 'base_imponible'),
            'impuesto_1_porcentaje': self.extraer_valor_seguro(impuesto_1, 'porcentaje'),
            'impuesto_1_importe': self.extraer_valor_seguro(impuesto_1, 'importe'),
            # Impuesto 2
            'impuesto_2_base_imponible': self.extraer_valor_seguro(impuesto_2, 'base_imponible'),
            'impuesto_2_porcentaje': self.extraer_valor_seguro(impuesto_2, 'porcentaje'),
            'impuesto_2_importe': self.extraer_valor_seguro(impuesto_2, 'importe'),
        }

    