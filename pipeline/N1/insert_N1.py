#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de Inserción N1 - Datos Enriquecidos
Inserta datos JSON N1 enriquecidos en la base de datos N1 con estructura separada
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

# Importar conexiones centralizadas - desde pipeline/N1 ir a motores/db_watioverse/core
core_path = Path(__file__).parent.parent / 'core'  # ../core desde pipeline/N1
if not core_path.exists():
    core_path = Path(__file__).parent.parent.parent / 'core'  # ../../core como fallback
sys.path.insert(0, str(core_path))

# Import con manejo de errores
try:
    from db_connections import db_manager
    logger = logging.getLogger(__name__)
    logger.info("✅ Conexiones centralizadas N1 cargadas correctamente")
except ImportError as e:
    logging.error(f"❌ Error importando db_connections: {e}")
    logging.error(f"Buscando en: {core_path}")
    logging.error(f"Archivo existe: {(core_path / 'db_connections.py').exists()}")
    raise

# Añadir directorio shared al path
sys.path.append(str(Path(__file__).parent.parent / 'shared'))
from field_mappings import N1_DB_CONFIG, N1_TABLES

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class InsercionN1Result:
    """Resultado de una inserción N1."""
    archivo: str
    exito: bool
    tablas_insertadas: int
    registros_insertados: int
    errores: List[str]
    tiempo_procesamiento: float

class N1Inserter:
    """Insertador de datos N1 enriquecidos con conexiones centralizadas."""
    
    def __init__(self, modo_prueba: bool = True):
        self.modo_prueba = modo_prueba
        self.resultados = []
        
        if not modo_prueba:
            logger.warning("⚠️ MODO PRODUCCIÓN ACTIVADO - Se insertará en BD N1 real")
            self._verificar_conexion_n1()
        else:
            logger.info("✅ MODO PRUEBA ACTIVADO - Solo simulación")
    
    def _verificar_conexion_n1(self):
        """Verifica que la conexión N1 esté disponible."""
        try:
            with db_manager.transaction('N1') as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                if result:
                    logger.info("✅ Conexión BD N1 verificada")
        except Exception as e:
            logger.error(f"❌ Error verificando conexión BD N1: {e}")
            raise
    
    def extraer_valor_seguro(self, datos: dict, campo: str, valor_defecto: Any = None) -> Any:
        """Extrae valor de un diccionario con notación punto."""
        try:
            if '.' in campo:
                # Navegar por campos anidados usando notación punto
                partes = campo.split('.')
                valor = datos
                for parte in partes:
                    if isinstance(valor, dict):
                        valor = valor.get(parte)
                    else:
                        return valor_defecto
                resultado = valor if valor is not None else valor_defecto
            else:
                resultado = datos.get(campo, valor_defecto)
            
            # Limpiar CUPS eliminando espacios para cumplir límite de 22 caracteres
            if isinstance(resultado, str) and ('ES' in resultado and len(resultado) > 22):
                resultado = resultado.replace(' ', '')
            
            return resultado
        except Exception as e:
            logger.debug(f"Error extrayendo {campo}: {e}")
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
    
    def mapear_datos_documents(self, datos_json: dict, archivo_nombre: str = None) -> Dict[str, Any]:
        """Mapea datos para tabla documents (maestra)."""
        # Extraer CUPS desde múltiples ubicaciones posibles
        cups = (self.extraer_valor_seguro(datos_json, 'contract.cups_electricidad') or
               self.extraer_valor_seguro(datos_json, 'contract_2x3.cups_electricidad') or  
               self.extraer_valor_seguro(datos_json, 'cups'))
        
        cliente = self.extraer_valor_seguro(datos_json, 'client.nombre_cliente')
        nif = (self.extraer_valor_seguro(datos_json, 'client.nif_titular.value') or
              self.extraer_valor_seguro(datos_json, 'client.nif_titular_value'))
        
        # Construir dirección completa a partir de campos aplanados
        sp_data = self.extraer_valor_seguro(datos_json, 'supply_point', {})
        direccion_parts = [
            sp_data.get('direccion_suministro_tipo_via', ''),
            sp_data.get('direccion_suministro_nombre_via', ''),
            sp_data.get('direccion_suministro_numero', ''),
            sp_data.get('direccion_suministro_planta', ''),
            sp_data.get('direccion_suministro_puerta', '')
        ]
        direccion = ' '.join(filter(None, direccion_parts)).strip()
        
        return {
            'cups': cups,
            'filename': archivo_nombre or 'unknown',
            'cliente': cliente,
            'direccion': direccion,
            'nif': nif,
            'processed_date': datetime.now(),
            # 'version_pipeline': '2.0' # Campo para futura implementación
        }
    
    def mapear_datos_metadata(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos para tabla metadata (control)."""
        cups = (self.extraer_valor_seguro(datos_json, 'contract.cups_electricidad') or
               self.extraer_valor_seguro(datos_json, 'contract_2x3.cups_electricidad') or  
               self.extraer_valor_seguro(datos_json, 'cups'))
        metadata_json = self.extraer_valor_seguro(datos_json, 'metadata', {})
        
        return {
            'cups': cups,
            'extraction_date': self.extraer_valor_seguro(metadata_json, 'extraction_timestamp'),
            'extraction_method': self.extraer_valor_seguro(metadata_json, 'extraction_method'), 
            'confidence_score': self.extraer_valor_seguro(metadata_json, 'processing_metrics.extraction_confidence'),
            'file_size_bytes': self.extraer_valor_seguro(metadata_json, 'text_length')
        }
    
    def mapear_datos_client(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos del cliente desde JSON a estructura BD."""
        cups = (self.extraer_valor_seguro(datos_json, 'contract.cups_electricidad') or
               self.extraer_valor_seguro(datos_json, 'contract_2x3.cups_electricidad') or
               self.extraer_valor_seguro(datos_json, 'cups'))
        
        client_data = self.extraer_valor_seguro(datos_json, 'client', {})
        nif_data = self.extraer_valor_seguro(client_data, 'nif_titular', {})
        
        return {
            'cups': cups,
            'nombre_cliente': self.extraer_valor_seguro(client_data, 'nombre_cliente'),
            'nif_titular_value': (self.extraer_valor_seguro(nif_data, 'value') or 
                                self.extraer_valor_seguro(client_data, 'nif_titular_value')),
            'nif_titular_confidence': (self.extraer_valor_seguro(nif_data, 'confidence') or
                                     self.extraer_valor_seguro(client_data, 'nif_titular_confidence')),
            'nif_titular_pattern': (self.extraer_valor_seguro(nif_data, 'pattern') or
                                  self.extraer_valor_seguro(client_data, 'nif_titular_pattern')),
            'nif_titular_source': (self.extraer_valor_seguro(nif_data, 'source') or
                                 self.extraer_valor_seguro(client_data, 'nif_titular_source'))
        }
    
    def mapear_datos_contract(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos del contrato desde JSON a estructura BD."""
        cups = (self.extraer_valor_seguro(datos_json, 'contract.cups_electricidad') or
               self.extraer_valor_seguro(datos_json, 'contract_2x3.cups_electricidad') or
               self.extraer_valor_seguro(datos_json, 'cups'))
        
        # Probar múltiples ubicaciones para contract
        contract_data = (self.extraer_valor_seguro(datos_json, 'contract', {}) or 
                        self.extraer_valor_seguro(datos_json, 'contract_2x3', {}))
        return {
            'cups': cups,
            'comercializadora': self.extraer_valor_seguro(contract_data, 'comercializadora'),
            'numero_contrato_comercializadora': self.extraer_valor_seguro(contract_data, 'numero_contrato_comercializadora'),
            'fecha_inicio_contrato': self._convertir_fecha(self.extraer_valor_seguro(contract_data, 'fecha_inicio_contrato')),
            'fecha_fin_contrato': self._convertir_fecha(self.extraer_valor_seguro(contract_data, 'fecha_fin_contrato')),
            'distribuidora': self.extraer_valor_seguro(contract_data, 'distribuidora'),
            'numero_contrato_distribuidora': self.extraer_valor_seguro(contract_data, 'numero_contrato_distribuidora'),
            'cups_electricidad': self.extraer_valor_seguro(contract_data, 'cups_electricidad'),
            'nombre_producto': self.extraer_valor_seguro(contract_data, 'nombre_producto'),
            'mercado': self.extraer_valor_seguro(contract_data, 'mercado'),
            'potencia_contratada_p1': self.extraer_valor_seguro(contract_data, 'potencia_contratada_p1'),
            'potencia_contratada_p2': self.extraer_valor_seguro(contract_data, 'potencia_contratada_p2'),
            'potencia_contratada_p3': self.extraer_valor_seguro(contract_data, 'potencia_contratada_p3'),
            'potencia_contratada_p4': self.extraer_valor_seguro(contract_data, 'potencia_contratada_p4'),
            'potencia_contratada_p5': self.extraer_valor_seguro(contract_data, 'potencia_contratada_p5'),
            'potencia_contratada_p6': self.extraer_valor_seguro(contract_data, 'potencia_contratada_p6'),
            'precio_unitario_potencia_p1': self.extraer_valor_seguro(contract_data, 'precio_unitario_potencia_p1'),
            'precio_unitario_potencia_p2': self.extraer_valor_seguro(contract_data, 'precio_unitario_potencia_p2'),
            'precio_unitario_potencia_p3': self.extraer_valor_seguro(contract_data, 'precio_unitario_potencia_p3'),
            'precio_unitario_potencia_p4': self.extraer_valor_seguro(contract_data, 'precio_unitario_potencia_p4'),
            'precio_unitario_potencia_p5': self.extraer_valor_seguro(contract_data, 'precio_unitario_potencia_p5'),
            'precio_unitario_potencia_p6': self.extraer_valor_seguro(contract_data, 'precio_unitario_potencia_p6'),
            'tarifa_acceso': self.extraer_valor_seguro(contract_data, 'tarifa_acceso')
        }
    
    def mapear_datos_energy_consumption(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos para la tabla normalizada energy_consumption."""
        cups = (self.extraer_valor_seguro(datos_json, 'contract.cups_electricidad') or
               self.extraer_valor_seguro(datos_json, 'contract_2x3.cups_electricidad') or
               self.extraer_valor_seguro(datos_json, 'cups'))
        invoice_data = self.extraer_valor_seguro(datos_json, 'invoice', {})
        
        # Calcular consumo total sumando todos los períodos
        consumo_total = 0
        for periodo in range(1, 7):
            campo_consumo = f'consumo_facturado_kwh_p{periodo}'
            consumo_periodo = self.extraer_valor_seguro(invoice_data, campo_consumo, 0)
            if consumo_periodo:
                consumo_total += float(consumo_periodo)

        return {
            'cups': cups,
            'consumo_total_kwh': consumo_total if consumo_total > 0 else None
        }

    def mapear_datos_invoice(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos completos para tabla invoice."""
        cups = (self.extraer_valor_seguro(datos_json, 'contract.cups_electricidad') or
               self.extraer_valor_seguro(datos_json, 'contract_2x3.cups_electricidad') or
               self.extraer_valor_seguro(datos_json, 'cups'))
        invoice_data = self.extraer_valor_seguro(datos_json, 'invoice', {})
        
        return {
            'cups': cups,
            'numero_factura': self.extraer_valor_seguro(invoice_data, 'numero_factura'),
            'fecha_emision': self._convertir_fecha(self.extraer_valor_seguro(invoice_data, 'fecha_emision')),
            'fecha_factura': self._convertir_fecha(self.extraer_valor_seguro(invoice_data, 'fecha_factura')),
            'fecha_inicio_periodo': self._convertir_fecha(self.extraer_valor_seguro(invoice_data, 'fecha_inicio_periodo')),
            'fecha_fin_periodo': self._convertir_fecha(self.extraer_valor_seguro(invoice_data, 'fecha_fin_periodo')),
            'periodo_facturacion_inicio': self._convertir_fecha(self.extraer_valor_seguro(invoice_data, 'periodo_facturacion_inicio')),
            'periodo_facturacion_fin': self._convertir_fecha(self.extraer_valor_seguro(invoice_data, 'periodo_facturacion_fin')),
            'total_a_pagar': self.extraer_valor_seguro(invoice_data, 'total_a_pagar'),
            'dias_periodo_facturado': self.extraer_valor_seguro(invoice_data, 'dias_periodo_facturado'),
            'año': self.extraer_valor_seguro(invoice_data, 'año'),
            # Consumos por periodo
            'consumo_kwh_p1': self.extraer_valor_seguro(invoice_data, 'consumo_kwh_p1'),
            'consumo_kwh_p2': self.extraer_valor_seguro(invoice_data, 'consumo_kwh_p2'),
            'consumo_kwh_p3': self.extraer_valor_seguro(invoice_data, 'consumo_kwh_p3'),
            'consumo_kwh_p4': self.extraer_valor_seguro(invoice_data, 'consumo_kwh_p4'),
            'consumo_kwh_p5': self.extraer_valor_seguro(invoice_data, 'consumo_kwh_p5'),
            'consumo_kwh_p6': self.extraer_valor_seguro(invoice_data, 'consumo_kwh_p6'),
            # Costes por periodo
            'coste_energia_p1': self.extraer_valor_seguro(invoice_data, 'coste_energia_p1'),
            'coste_energia_p2': self.extraer_valor_seguro(invoice_data, 'coste_energia_p2'),
            'coste_energia_p3': self.extraer_valor_seguro(invoice_data, 'coste_energia_p3'),
            'coste_energia_p4': self.extraer_valor_seguro(invoice_data, 'coste_energia_p4'),
            'coste_energia_p5': self.extraer_valor_seguro(invoice_data, 'coste_energia_p5'),
            'coste_energia_p6': self.extraer_valor_seguro(invoice_data, 'coste_energia_p6'),
            'coste_energia_total': self.extraer_valor_seguro(invoice_data, 'coste_energia_total'),
            'coste_potencia_total': self.extraer_valor_seguro(invoice_data, 'coste_potencia_total'),
            # Potencias facturadas
            'potencia_facturada_p1': self.extraer_valor_seguro(invoice_data, 'potencia_facturada_p1'),
            'potencia_facturada_p2': self.extraer_valor_seguro(invoice_data, 'potencia_facturada_p2'),
            'potencia_facturada_p3': self.extraer_valor_seguro(invoice_data, 'potencia_facturada_p3'),
            'potencia_facturada_p4': self.extraer_valor_seguro(invoice_data, 'potencia_facturada_p4'),
            'potencia_facturada_p5': self.extraer_valor_seguro(invoice_data, 'potencia_facturada_p5'),
            'potencia_facturada_p6': self.extraer_valor_seguro(invoice_data, 'potencia_facturada_p6'),
            # Precios energia
            'precio_energia_p1': self.extraer_valor_seguro(invoice_data, 'precio_energia_p1'),
            'precio_energia_p2': self.extraer_valor_seguro(invoice_data, 'precio_energia_p2'),
            'precio_energia_p3': self.extraer_valor_seguro(invoice_data, 'precio_energia_p3'),
            'precio_energia_p4': self.extraer_valor_seguro(invoice_data, 'precio_energia_p4'),
            'precio_energia_p5': self.extraer_valor_seguro(invoice_data, 'precio_energia_p5'),
            'precio_energia_p6': self.extraer_valor_seguro(invoice_data, 'precio_energia_p6'),
            # Otros campos importantes
            'consumo_promedio_diario_kwh': self.extraer_valor_seguro(invoice_data, 'consumo_promedio_diario_kwh'),
            'coste_promedio_diario_eur': self.extraer_valor_seguro(invoice_data, 'coste_promedio_diario_eur'),
            'importe_impuesto_electricidad': self.extraer_valor_seguro(invoice_data, 'importe_impuesto_electricidad'),
            'porcentaje_impuesto_electricidad': self.extraer_valor_seguro(invoice_data, 'porcentaje_impuesto_electricidad')
        }
    
    def mapear_datos_consumption_px(self, datos_json: dict, periodo: int) -> Dict[str, Any]:
        """Mapea datos para tablas consumption_p1 a consumption_p6."""
        campo_consumo = f'consumo_facturado_kwh_p{periodo}'
        return {
            'cups': self.extraer_valor_seguro(datos_json, 'cups'),
            'periodo': f'P{periodo}',
            'consumo_kwh': self.extraer_valor_seguro(datos_json, campo_consumo)
        }
    
    def mapear_datos_cost_px(self, datos_json: dict, periodo: int) -> Dict[str, Any]:
        """Mapea datos para tablas cost_p1 a cost_p6."""
        campo_coste = f'coste_energia_p{periodo}'
        return {
            'cups': self.extraer_valor_seguro(datos_json, 'cups'),
            'periodo': f'P{periodo}',
            'coste_energia': self.extraer_valor_seguro(datos_json, campo_coste)
        }
    
    def mapear_datos_power_px(self, datos_json: dict, periodo: int) -> Dict[str, Any]:
        """Mapea datos para tablas power_p1 a power_p6."""
        campo_potencia = f'potencia_contratada_p{periodo}'
        return {
            'cups': self.extraer_valor_seguro(datos_json, 'cups'),
            'periodo': f'P{periodo}',
            'potencia_contratada': self.extraer_valor_seguro(datos_json, campo_potencia)
        }
    
    def mapear_datos_sustainability_base(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos para tabla sustainability_base (datos directos de factura).
        
        NOTA: Unificado con arquitectura híbrida LLM + automejora.
        Los campos se mapean desde el módulo 'sostenibilidad' extraído por LLM
        y validado/enriquecido por automejora_sostenibilidad.py
        """
        # Buscar datos en el módulo 'sostenibilidad' (arquitectura híbrida)
        sustainability_data = self.extraer_valor_seguro(datos_json, 'sostenibilidad', {})
        
        return {
            'cups': self.extraer_valor_seguro(datos_json, 'cups'),
            # Mapeo unificado con campos estándar de sostenibilidad
            'energia_origen_renovable': self.extraer_valor_seguro(sustainability_data, 'energia_origen_renovable'),
            'energia_origen_nuclear': self.extraer_valor_seguro(sustainability_data, 'energia_origen_nuclear'),
            'energia_origen_carbon': self.extraer_valor_seguro(sustainability_data, 'energia_origen_carbon'),
            'energia_origen_cc_gas_natural': self.extraer_valor_seguro(sustainability_data, 'energia_origen_cc_gas_natural'),
            'energia_origen_cogeneracion_alta_eficiencia': self.extraer_valor_seguro(sustainability_data, 'energia_origen_cogeneracion_alta_eficiencia'),
            'energia_origen_fuel_gas': self.extraer_valor_seguro(sustainability_data, 'energia_origen_fuel_gas'),
            'energia_origen_otras_no_renovables': self.extraer_valor_seguro(sustainability_data, 'energia_origen_otras_no_renovables'),
            'emisiones_co2_equivalente': self.extraer_valor_seguro(sustainability_data, 'emisiones_co2_equivalente'),
            'letra_escala_medioambiental': self.extraer_valor_seguro(sustainability_data, 'letra_escala_medioambiental')
        }
    
    def mapear_datos_sustainability_metrics(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos para tabla sustainability_metrics (datos calculados)."""
        return {
            'cups': self.extraer_valor_seguro(datos_json, 'cups'),
            'huella_carbono_kg': self.extraer_valor_seguro(datos_json, 'huella_carbono_kg'),
            'rating_sostenibilidad': self.extraer_valor_seguro(datos_json, 'rating_sostenibilidad'),
            'ahorro_potencial_eur': self.extraer_valor_seguro(datos_json, 'ahorro_potencial_eur'),
            'recomendacion_mejora': self.extraer_valor_seguro(datos_json, 'recomendacion_mejora')
        }
    
    def mapear_datos_analytics(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos para tabla analytics (KPIs y enriquecimiento)."""
        return {
            'cups': self.extraer_valor_seguro(datos_json, 'cups'),
            'latitud': self.extraer_valor_seguro(datos_json, 'latitud'),
            'longitud': self.extraer_valor_seguro(datos_json, 'longitud'),
            'precipitacion_mm': self.extraer_valor_seguro(datos_json, 'precipitacion_mm'),
            'temperatura_media_c': self.extraer_valor_seguro(datos_json, 'temperatura_media_c'),
            'precio_omie_kwh': self.extraer_valor_seguro(datos_json, 'precio_omie_kwh'),
            'precio_omie_mwh': self.extraer_valor_seguro(datos_json, 'precio_omie_mwh'),
            'ratio_precio_mercado': self.extraer_valor_seguro(datos_json, 'ratio_precio_mercado'),
            'eficiencia_energetica': self.extraer_valor_seguro(datos_json, 'eficiencia_energetica'),
            'coste_kwh_promedio': self.extraer_valor_seguro(datos_json, 'coste_kwh_promedio')
        }
    
    def simular_insercion_tabla(self, tabla: str, datos: Dict[str, Any]) -> bool:
        """Simula inserción en tabla (modo prueba)."""
        if self.modo_prueba:
            logger.info(f"  📝 SIMULANDO inserción en tabla N1 '{tabla}':")
            campos_no_nulos = {k: v for k, v in datos.items() if v is not None}
            for campo, valor in campos_no_nulos.items():
                logger.info(f"    - {campo}: {valor}")
            logger.info(f"  ✅ Simulación exitosa - {len(campos_no_nulos)} campos")
            return True
        else:
            return self._insertar_real_tabla(tabla, datos)
    
    def _insertar_real_tabla(self, tabla: str, datos: Dict[str, Any]) -> bool:
        """Inserción real en BD N1 usando conexiones centralizadas."""
        try:
            # Filtrar campos nulos
            campos_no_nulos = {k: v for k, v in datos.items() if v is not None and v != ''}
            
            if not campos_no_nulos:
                logger.warning(f"  ⚠️ Tabla {tabla}: Sin datos válidos para insertar")
                return True
            
            # Construir query INSERT con UPSERT
            campos = list(campos_no_nulos.keys())
            valores = list(campos_no_nulos.values())
            placeholders = ', '.join(['%s'] * len(campos))
            campos_str = ', '.join(campos)
            
            # Usar UPSERT para evitar errores de duplicado (misma lógica que N0)
            conflict_clause = "ON CONFLICT DO NOTHING"
            
            query = f"""INSERT INTO {tabla} ({campos_str}) 
                         VALUES ({placeholders})
                         {conflict_clause}"""
            
            with db_manager.transaction('N1') as cursor:
                cursor.execute(query, valores)
                affected = cursor.rowcount
                if affected > 0:
                    logger.info(f"  ✅ INSERTADO en tabla N1 '{tabla}': {len(campos)} campos")
                else:
                    logger.info(f"  🔄 DUPLICADO ignorado en tabla N1 '{tabla}'")
                return True
                
        except Exception as e:
            logger.error(f"  ❌ Error insertando en tabla N1 '{tabla}': {e}")
            return False
    
    def procesar_archivo(self, archivo_path: Path) -> InsercionN1Result:
        """Procesa un archivo JSON N1 individual."""
        inicio_tiempo = datetime.now()
        errores = []
        tablas_insertadas = 0
        registros_insertados = 0
        
        try:
            logger.info(f"📄 Procesando N1: {archivo_path.name}")
            
            # Cargar JSON N1
            with open(archivo_path, 'r', encoding='utf-8') as f:
                datos_json = json.load(f)
            
            # Verificar que es un JSON N1 válido
            if '_metadata_n1' not in datos_json:
                logger.warning(f"Archivo no parece ser JSON N1: {archivo_path.name}")
            
            # Mapear datos para todas las tablas N1
            tablas_datos = {}
            
            # Tablas principales
            tablas_datos['documents'] = self.mapear_datos_documents(datos_json, archivo_path.name)
            tablas_datos['metadata'] = self.mapear_datos_metadata(datos_json)
            tablas_datos['client'] = self.mapear_datos_client(datos_json)
            tablas_datos['contract'] = self.mapear_datos_contract(datos_json)
            tablas_datos['invoice'] = self.mapear_datos_invoice(datos_json)
            
            
            # Tablas de sostenibilidad y analytics
            tablas_datos['sustainability_base'] = self.mapear_datos_sustainability_base(datos_json)
            tablas_datos['sustainability_metrics'] = self.mapear_datos_sustainability_metrics(datos_json)
            tablas_datos['analytics'] = self.mapear_datos_analytics(datos_json)
            
            # Insertar en cada tabla
            for tabla, datos in tablas_datos.items():
                if self.simular_insercion_tabla(tabla, datos):
                    tablas_insertadas += 1
                    registros_insertados += 1
                else:
                    errores.append(f"Error insertando en tabla {tabla}")
            
            tiempo_procesamiento = (datetime.now() - inicio_tiempo).total_seconds()
            
            return InsercionN1Result(
                archivo=archivo_path.name,
                exito=len(errores) == 0,
                tablas_insertadas=tablas_insertadas,
                registros_insertados=registros_insertados,
                errores=errores,
                tiempo_procesamiento=tiempo_procesamiento
            )
            
        except Exception as e:
            tiempo_procesamiento = (datetime.now() - inicio_tiempo).total_seconds()
            error_msg = f"Error procesando {archivo_path.name}: {str(e)}"
            logger.error(error_msg)
            
            return InsercionN1Result(
                archivo=archivo_path.name,
                exito=False,
                tablas_insertadas=0,
                registros_insertados=0,
                errores=[error_msg],
                tiempo_procesamiento=tiempo_procesamiento
            )
    
    def procesar_directorio(self, directorio_n1: str, limite_archivos: int = None) -> List[InsercionN1Result]:
        """Procesa archivos JSON N1 de un directorio."""
        logger.info(f"🚀 INICIANDO PROCESAMIENTO N1 - MODO {'PRUEBA' if self.modo_prueba else 'PRODUCCIÓN'}")
        logger.info(f"📁 Directorio: {directorio_n1}")
        
        # Buscar archivos JSON N1
        data_path = Path(directorio_n1)
        archivos_json = list(data_path.glob("*_N1.json")) + list(data_path.glob("N1_*.json"))
        
        logger.info(f"📊 Encontrados {len(archivos_json)} archivos N1")
        
        if limite_archivos:
            archivos_json = archivos_json[:limite_archivos]
            logger.info(f"🎯 Procesando primeros {len(archivos_json)} archivos")
        
        # Procesar cada archivo
        resultados = []
        for archivo in archivos_json:
            resultado = self.procesar_archivo(archivo)
            resultados.append(resultado)
            self.resultados.append(resultado)
        
        return resultados
    
    def generar_reporte(self) -> str:
        """Genera reporte de resultados N1."""
        if not self.resultados:
            return "No hay resultados N1 para reportar."
        
        exitosos = [r for r in self.resultados if r.exito]
        fallidos = [r for r in self.resultados if not r.exito]
        
        reporte = []
        reporte.append("=" * 60)
        reporte.append("📋 REPORTE INSERCIÓN N1 (DATOS ENRIQUECIDOS)")
        reporte.append("=" * 60)
        reporte.append(f"📊 Total archivos procesados: {len(self.resultados)}")
        reporte.append(f"✅ Exitosos: {len(exitosos)}")
        reporte.append(f"❌ Fallidos: {len(fallidos)}")
        reporte.append(f"📈 Tasa de éxito: {len(exitosos)/len(self.resultados)*100:.1f}%")
        reporte.append("")
        
        if exitosos:
            reporte.append("✅ ARCHIVOS N1 PROCESADOS EXITOSAMENTE:")
            for resultado in exitosos:
                reporte.append(f"  - {resultado.archivo}: {resultado.tablas_insertadas}/17 tablas ({resultado.tiempo_procesamiento:.2f}s)")
        
        if fallidos:
            reporte.append("")
            reporte.append("❌ ARCHIVOS N1 CON ERRORES:")
            for resultado in fallidos:
                reporte.append(f"  - {resultado.archivo}:")
                for error in resultado.errores:
                    reporte.append(f"    • {error}")
        
        tiempo_total = sum(r.tiempo_procesamiento for r in self.resultados)
        registros_total = sum(r.registros_insertados for r in self.resultados)
        
        reporte.append("")
        reporte.append(f"⏱️ Tiempo total: {tiempo_total:.2f} segundos")
        reporte.append(f"📝 Total registros insertados: {registros_total}")
        reporte.append(f"🗂️ Tablas N1 objetivo: {len(N1_TABLES)}")
        reporte.append("=" * 60)
        
        return "\n".join(reporte)
    
    def __del__(self):
        """Destructor - conexiones manejadas por db_manager."""
        pass

def insertar_n1_file(n1_json_path: str, modo_prueba: bool = True) -> bool:
    """
    Función de conveniencia para insertar un archivo N1
    
    Args:
        n1_json_path: Ruta al archivo JSON N1
        modo_prueba: Si True, solo simula inserción
        
    Returns:
        True si se insertó exitosamente, False en caso contrario
    """
    inserter = N1Inserter(modo_prueba=modo_prueba)
    resultado = inserter.procesar_archivo(Path(n1_json_path))
    return resultado.exito

if __name__ == "__main__":
    # Test con datos N1 simulados
    print("🚀 INSERTADOR N1 - MODO PRUEBA")
    print("=" * 50)
    
    # Crear datos N1 de ejemplo
    sample_n1_data = {
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
        "coste_energia_p1": 120.15,
        "coste_energia_p2": 180.20,
        "potencia_contratada_p1": 5.5,
        "potencia_contratada_p2": 5.5,
        "mix_energetico_renovable_pct": 45.2,
        "emisiones_co2_kg_kwh": 0.25,
        "latitud": 40.4168,
        "longitud": -3.7038,
        "coste_kwh_promedio": 0.180066,
        "rating_sostenibilidad": "C",
        "huella_carbono_kg": 625.19,
        "_metadata_n1": {
            "generated_at": "2024-09-06T16:00:00",
            "pipeline_version": "1.0",
            "source": "N0_to_N1_pipeline",
            "fields_count": 23,
            "enrichment_applied": True
        }
    }
    
    # Crear archivo temporal para test
    test_file = Path("test_n1_sample.json")
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(sample_n1_data, f, indent=2, ensure_ascii=False)
    
    # Crear insertador y procesar
    inserter = N1Inserter(modo_prueba=True)
    resultado = inserter.procesar_archivo(test_file)
    
    # Mostrar resultado
    print(f"✅ Test inserción N1: {'ÉXITO' if resultado.exito else 'ERROR'}")
    print(f"📊 Tablas procesadas: {resultado.tablas_insertadas}/17")
    print(f"⏱️ Tiempo: {resultado.tiempo_procesamiento:.2f}s")
    
    if resultado.errores:
        print("❌ Errores:")
        for error in resultado.errores:
            print(f"  - {error}")
    
    # Limpiar archivo temporal
    test_file.unlink()
    
    print("\n=== Test completado ===")
