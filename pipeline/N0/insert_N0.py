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
            
            return valor_actual if valor_actual is not None else valor_defecto
            
        except Exception as e:
            logger.debug(f"Error extrayendo {ruta}: {e}")
            return valor_defecto
    
    def mapear_datos_client(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos del cliente desde JSON a estructura BD."""
        return {
            'nombre_cliente': self.extraer_valor_seguro(datos_json, 'client.nombre_cliente'),
            'nif_titular_value': self.extraer_valor_seguro(datos_json, 'client.nif_titular.value'),
            'nif_titular_confidence': self.extraer_valor_seguro(datos_json, 'client.nif_titular.confidence'),
            'nif_titular_pattern': self.extraer_valor_seguro(datos_json, 'client.nif_titular.pattern'),
            'nif_titular_source': self.extraer_valor_seguro(datos_json, 'client.nif_titular.source')
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
        """Mapea datos del punto de suministro desde JSON a estructura BD."""
        return {
            'cups': self.extraer_valor_seguro(datos_json, 'supply_point.cups') or 
                   self.extraer_valor_seguro(datos_json, 'contract_3x3.cups_electricidad') or
                   self.extraer_valor_seguro(datos_json, 'contract_2x3.cups')
        }
    
    def mapear_datos_supply_address(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea dirección de suministro desde JSON a estructura BD."""
        base_path = 'supply_point.datos_suministro.direccion_suministro'
        return {
            'codigo_postal': self.extraer_valor_seguro(datos_json, f'{base_path}.codigo_postal'),
            'comunidad_autonoma': self.extraer_valor_seguro(datos_json, f'{base_path}.comunidad_autonoma'),
            'municipio': self.extraer_valor_seguro(datos_json, f'{base_path}.municipio'),
            'nombre_via': self.extraer_valor_seguro(datos_json, f'{base_path}.nombre_via'),
            'numero': self.extraer_valor_seguro(datos_json, f'{base_path}.numero'),
            'pais': self.extraer_valor_seguro(datos_json, f'{base_path}.pais'),
            'planta': self.extraer_valor_seguro(datos_json, f'{base_path}.planta'),
            'poblacion': self.extraer_valor_seguro(datos_json, f'{base_path}.poblacion'),
            'provincia': self.extraer_valor_seguro(datos_json, f'{base_path}.provincia'),
            'puerta': self.extraer_valor_seguro(datos_json, f'{base_path}.puerta'),
            'tipo_via': self.extraer_valor_seguro(datos_json, f'{base_path}.tipo_via')
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
            'comercializadora': self.extraer_valor_seguro(datos_contract, 'comercializadora'),
            'numero_contrato_comercializadora': self.extraer_valor_seguro(datos_contract, 'numero_contrato_comercializadora'),
            'fecha_inicio_contrato': self.extraer_valor_seguro(datos_contract, 'fecha_inicio_contrato'),
            'fecha_fin_contrato': self.extraer_valor_seguro(datos_contract, 'fecha_fin_contrato'),
            'distribuidora': self.extraer_valor_seguro(datos_contract, 'distribuidora'),
            'numero_contrato_distribuidora': self.extraer_valor_seguro(datos_contract, 'numero_contrato_distribuidora'),
            'cups_electricidad': self.extraer_valor_seguro(datos_contract, 'cups_electricidad') or 
                               self.extraer_valor_seguro(datos_contract, 'cups'),
            'nombre_producto': self.extraer_valor_seguro(datos_contract, 'nombre_producto'),
            'mercado': self.extraer_valor_seguro(datos_contract, 'mercado'),
            'potencia_contratada_p1': self.extraer_valor_seguro(datos_contract, 'potencia_contratada_p1'),
            'potencia_contratada_p2': self.extraer_valor_seguro(datos_contract, 'potencia_contratada_p2'),
            'potencia_contratada_p3': self.extraer_valor_seguro(datos_contract, 'potencia_contratada_p3'),
            'potencia_contratada_p4': self.extraer_valor_seguro(datos_contract, 'potencia_contratada_p4'),
            'potencia_contratada_p5': self.extraer_valor_seguro(datos_contract, 'potencia_contratada_p5'),
            'potencia_contratada_p6': self.extraer_valor_seguro(datos_contract, 'potencia_contratada_p6'),
            'tarifa_acceso': self.extraer_valor_seguro(datos_contract, 'tarifa_acceso')
        }
    
    def mapear_datos_energy_consumption(self, datos_json: dict) -> Dict[str, Any]:
        """Mapea datos de consumo energético desde JSON a estructura BD."""
        consumo_data = self.extraer_valor_seguro(datos_json, 'consumo_energia', {})
        
        return {
            'inicio_periodo': self.extraer_valor_seguro(consumo_data, 'inicio_periodo'),
            'fin_periodo': self.extraer_valor_seguro(consumo_data, 'fin_periodo'),
            'consumo_facturado_mes': self.extraer_valor_seguro(consumo_data, 'consumo_facturado_kwh'),
            'precio_energia_eur_kwh': self.extraer_valor_seguro(consumo_data, 'precio_energia_eur_kwh'),
            'coste_energia_eur': self.extraer_valor_seguro(consumo_data, 'coste_energia_eur')
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
        """Mapea datos de la factura desde JSON a estructura BD."""
        invoice_data = {}
        
        # Buscar datos de factura en diferentes rutas
        invoice_paths = ['invoice_3x3', 'invoice_2x3', 'invoice', 'billing']
        factura_data = {}
        
        for path in invoice_paths:
            if path in datos_json:
                factura_data = datos_json[path]
                break
        
        # Mapear campos principales de factura
        invoice_data.update({
            'numero_factura': self.extraer_valor_seguro(factura_data, 'numero_factura'),
            'fecha_inicio_periodo': self.extraer_valor_seguro(factura_data, 'fecha_inicio_periodo'),
            'fecha_fin_periodo': self.extraer_valor_seguro(factura_data, 'fecha_fin_periodo'),
            'dias_periodo_facturado': self.extraer_valor_seguro(factura_data, 'dias_periodo_facturado'),
            'total_a_pagar': self.extraer_valor_seguro(factura_data, 'total_a_pagar') or 
                           self.extraer_valor_seguro(factura_data, 'importe_total_factura'),
            'tipo_iva': self.extraer_valor_seguro(factura_data, 'tipo_iva'),
            'importe_iva': self.extraer_valor_seguro(factura_data, 'importe_iva')
        })
        
        # Mapear consumos por períodos
        for periodo in range(1, 7):
            consumo_key = f'consumo_kwh_p{periodo}'
            invoice_data[consumo_key] = self.extraer_valor_seguro(
                datos_json, f'consumo_energia.consumo_p{periodo}') or \
                self.extraer_valor_seguro(datos_json, f'consumption.p{periodo}_kwh')
        
        # Mapear potencias máximas
        for periodo in range(1, 7):
            potencia_key = f'potencia_maxima_demandada_factura_p{periodo}'
            invoice_data[potencia_key] = self.extraer_valor_seguro(
                datos_json, f'power.maxima_p{periodo}_kw')
        
        # Mapear energía reactiva
        for periodo in range(1, 7):
            reactiva_key = f'energia_reactiva_facturar_p{periodo}'
            invoice_data[reactiva_key] = self.extraer_valor_seguro(
                datos_json, f'reactive.p{periodo}_kvarh')
            
            penalizacion_key = f'penalizacion_reactiva_p{periodo}'
            invoice_data[penalizacion_key] = self.extraer_valor_seguro(
                datos_json, f'reactive.penalizacion_p{periodo}')
        
        # Autoconsumo
        invoice_data.update({
            'autoconsumo': self.extraer_valor_seguro(datos_json, 'self_consumption.tipo'),
            'energia_vertida_kwh': self.extraer_valor_seguro(datos_json, 'self_consumption.excedentes_kwh'),
            'importe_compensacion_excedentes': self.extraer_valor_seguro(datos_json, 'self_consumption.compensacion_eur')
        })
        
        return invoice_data
    
    def insertar_en_tabla(self, tabla: str, datos: Dict[str, Any]) -> bool:
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
