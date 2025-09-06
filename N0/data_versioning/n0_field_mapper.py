#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mapeador de Campos N0 a Schemas Electricidad
Mapea la estructura jerárquica de N0 a los campos esperados en schemas.
"""

from typing import Dict, List, Set, Any, Optional
import json
from pathlib import Path

class N0FieldMapper:
    """Mapea campos de facturas N0 a estructura esperada por schemas."""
    
    def __init__(self):
        # Mapeo de rutas N0 a campos esperados en schemas
        self.mapeo_campos = {
            # Identificación básica
            'numero_factura': ['invoice.numero_factura', 'factura.numero', 'billing.numero_factura'],
            'cups': ['supply_point.cups', 'contract_2x3.cups', 'datos_suministro.cups'],
            'fecha_factura': ['invoice.fecha_emision', 'billing.fecha_factura', 'periodo.fecha_inicio'],
            'comercializadora': ['contract_2x3.comercializadora', 'provider.nombre_proveedor'],
            
            # Cliente
            'nombre_cliente': ['client.nombre_cliente', 'titular.nombre'],
            'nif_titular': ['client.nif_titular.value', 'client.nif_titular', 'titular.nif'],
            
            # Consumo
            'consumo_facturado_kwh': ['consumption.total_kwh', 'consumo.total', 'energia.consumo_total'],
            'consumo_facturado_mes': ['consumption.periodo_kwh', 'consumo.mensual'],
            'consumo_p1': ['consumption.punta_kwh', 'periodos.p1.consumo', 'energia.punta'],
            'consumo_p2': ['consumption.llano_kwh', 'periodos.p2.consumo', 'energia.llano'],
            'consumo_p3': ['consumption.valle_kwh', 'periodos.p3.consumo', 'energia.valle'],
            
            # Potencia
            'potencia_contratada_kw': ['power.contratada_kw', 'potencia.contratada', 'contract_2x3.potencia_contratada'],
            'potencia_maxima_p1': ['power.maxima_p1_kw', 'potencia.maxima_punta'],
            'potencia_maxima_p2': ['power.maxima_p2_kw', 'potencia.maxima_llano'],
            'potencia_maxima_p3': ['power.maxima_p3_kw', 'potencia.maxima_valle'],
            
            # Costes
            'importe_total_factura': ['billing.total_factura', 'costes.total', 'factura.importe_total'],
            'termino_energia': ['billing.termino_energia', 'costes.energia'],
            'termino_potencia': ['billing.termino_potencia', 'costes.potencia'],
            
            # Datos técnicos
            'tarifa_acceso': ['contract_2x3.tarifa_acceso', 'tarifa.acceso'],
            'tipo_peaje': ['contract_2x3.peaje', 'tarifa.peaje'],
            'zona_geografica': ['supply_point.zona', 'ubicacion.zona'],
            'provincia': ['supply_point.datos_suministro.direccion_suministro.provincia', 'direccion.provincia'],
            'codigo_postal': ['supply_point.datos_suministro.direccion_suministro.codigo_postal', 'direccion.cp'],
            
            # Reactiva
            'energia_reactiva_p1': ['reactive.p1_kvarh', 'reactiva.punta'],
            'energia_reactiva_p2': ['reactive.p2_kvarh', 'reactiva.llano'],
            'energia_reactiva_p3': ['reactive.p3_kvarh', 'reactiva.valle'],
            'penalizacion_reactiva_p1': ['reactive.penalizacion_p1', 'costes.reactiva_p1'],
            'penalizacion_reactiva_p2': ['reactive.penalizacion_p2', 'costes.reactiva_p2'],
            'penalizacion_reactiva_p3': ['reactive.penalizacion_p3', 'costes.reactiva_p3'],
            
            # Autoconsumo
            'autoconsumo_kwh': ['self_consumption.total_kwh', 'autoconsumo.generado'],
            'excedentes_kwh': ['self_consumption.excedentes_kwh', 'autoconsumo.excedentes'],
            'compensacion_excedentes': ['self_consumption.compensacion', 'autoconsumo.compensacion'],
            
            # Sostenibilidad
            'mix_energetico_renovable': ['sustainability.mix_renovable', 'sostenibilidad.renovable_pct'],
            'emisiones_co2': ['sustainability.emisiones_co2', 'sostenibilidad.co2_kwh'],
            'etiqueta_energetica': ['sustainability.etiqueta', 'sostenibilidad.clase']
        }
        
        # Patrones de búsqueda flexibles
        self.patrones_busqueda = {
            'consumo': ['consumo', 'consumption', 'energia', 'kwh'],
            'potencia': ['potencia', 'power', 'kw', 'maxima'],
            'coste': ['coste', 'importe', 'precio', 'billing', 'factura'],
            'fecha': ['fecha', 'date', 'periodo', 'inicio', 'fin'],
            'direccion': ['direccion', 'address', 'ubicacion', 'suministro'],
            'tarifa': ['tarifa', 'peaje', 'acceso', 'modalidad'],
            'reactiva': ['reactiva', 'reactive', 'kvarh', 'penalizacion'],
            'autoconsumo': ['autoconsumo', 'self_consumption', 'excedentes', 'generacion']
        }
    
    def extraer_valor_por_ruta(self, datos: dict, ruta: str) -> Any:
        """Extrae valor de datos siguiendo una ruta con notación punto."""
        partes = ruta.split('.')
        valor_actual = datos
        
        for parte in partes:
            if isinstance(valor_actual, dict) and parte in valor_actual:
                valor_actual = valor_actual[parte]
            else:
                return None
        
        # Si es un dict con 'value', extraer el valor
        if isinstance(valor_actual, dict) and 'value' in valor_actual:
            return valor_actual['value']
        
        return valor_actual
    
    def buscar_campo_flexible(self, datos: dict, campo_objetivo: str) -> Optional[Any]:
        """Busca un campo usando patrones flexibles."""
        
        # 1. Intentar mapeo directo
        if campo_objetivo in self.mapeo_campos:
            for ruta in self.mapeo_campos[campo_objetivo]:
                valor = self.extraer_valor_por_ruta(datos, ruta)
                if valor is not None:
                    return valor
        
        # 2. Búsqueda por patrones
        for categoria, patrones in self.patrones_busqueda.items():
            if any(patron in campo_objetivo.lower() for patron in patrones):
                valor = self._buscar_por_patron(datos, patrones, campo_objetivo)
                if valor is not None:
                    return valor
        
        # 3. Búsqueda recursiva por nombre exacto
        return self._buscar_recursivo(datos, campo_objetivo)
    
    def _buscar_por_patron(self, datos: dict, patrones: List[str], campo_objetivo: str) -> Optional[Any]:
        """Busca usando patrones específicos."""
        def buscar_en_nivel(obj, nivel_actual=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    key_lower = key.lower()
                    
                    # Verificar si la clave contiene algún patrón
                    if any(patron in key_lower for patron in patrones):
                        # Si el campo objetivo también está en la clave, es una buena coincidencia
                        if any(parte in key_lower for parte in campo_objetivo.lower().split('_')):
                            if isinstance(value, dict) and 'value' in value:
                                return value['value']
                            elif not isinstance(value, dict):
                                return value
                    
                    # Búsqueda recursiva
                    if isinstance(value, dict):
                        resultado = buscar_en_nivel(value, f"{nivel_actual}.{key}" if nivel_actual else key)
                        if resultado is not None:
                            return resultado
            
            return None
        
        return buscar_en_nivel(datos)
    
    def _buscar_recursivo(self, datos: dict, campo_objetivo: str) -> Optional[Any]:
        """Búsqueda recursiva por nombre exacto o similar."""
        def buscar_en_nivel(obj):
            if isinstance(obj, dict):
                # Búsqueda exacta
                if campo_objetivo in obj:
                    valor = obj[campo_objetivo]
                    if isinstance(valor, dict) and 'value' in valor:
                        return valor['value']
                    return valor
                
                # Búsqueda por similitud
                for key, value in obj.items():
                    if self._son_similares(key, campo_objetivo):
                        if isinstance(value, dict) and 'value' in value:
                            return value['value']
                        elif not isinstance(value, dict):
                            return value
                
                # Búsqueda recursiva
                for value in obj.values():
                    if isinstance(value, dict):
                        resultado = buscar_en_nivel(value)
                        if resultado is not None:
                            return resultado
            
            return None
        
        return buscar_en_nivel(datos)
    
    def _son_similares(self, campo1: str, campo2: str) -> bool:
        """Determina si dos campos son similares."""
        campo1_clean = campo1.lower().replace('_', '').replace('-', '')
        campo2_clean = campo2.lower().replace('_', '').replace('-', '')
        
        # Coincidencia exacta sin separadores
        if campo1_clean == campo2_clean:
            return True
        
        # Uno contiene al otro
        if campo1_clean in campo2_clean or campo2_clean in campo1_clean:
            return True
        
        # Coincidencia de palabras clave
        palabras1 = set(campo1.lower().split('_'))
        palabras2 = set(campo2.lower().split('_'))
        
        # Al menos 2 palabras en común
        if len(palabras1.intersection(palabras2)) >= 2:
            return True
        
        return False
    
    def mapear_factura_completa(self, datos_factura: dict) -> Dict[str, Any]:
        """Mapea una factura completa a estructura esperada por schemas."""
        factura_mapeada = {}
        
        # Lista de campos críticos que debemos intentar mapear
        campos_criticos = [
            'numero_factura', 'cups', 'fecha_factura', 'comercializadora',
            'nombre_cliente', 'nif_titular',
            'consumo_facturado_kwh', 'consumo_p1', 'consumo_p2', 'consumo_p3',
            'potencia_contratada_kw', 'potencia_maxima_p1', 'potencia_maxima_p2',
            'importe_total_factura', 'termino_energia', 'termino_potencia',
            'tarifa_acceso', 'tipo_peaje', 'provincia', 'codigo_postal'
        ]
        
        for campo in campos_criticos:
            valor = self.buscar_campo_flexible(datos_factura, campo)
            if valor is not None:
                factura_mapeada[campo] = valor
        
        return factura_mapeada
    
    def generar_reporte_mapeo(self, facturas_n0: List[dict]) -> Dict[str, Any]:
        """Genera reporte de efectividad del mapeo."""
        total_facturas = len(facturas_n0)
        campos_encontrados = {}
        campos_faltantes = {}
        
        for factura in facturas_n0:
            factura_mapeada = self.mapear_factura_completa(factura)
            
            for campo in self.mapeo_campos.keys():
                if campo in factura_mapeada:
                    campos_encontrados[campo] = campos_encontrados.get(campo, 0) + 1
                else:
                    campos_faltantes[campo] = campos_faltantes.get(campo, 0) + 1
        
        # Calcular estadísticas
        campos_con_alta_cobertura = {k: v for k, v in campos_encontrados.items() if v >= total_facturas * 0.8}
        campos_con_baja_cobertura = {k: v for k, v in campos_encontrados.items() if v < total_facturas * 0.5}
        
        return {
            'total_facturas': total_facturas,
            'campos_evaluados': len(self.mapeo_campos),
            'campos_encontrados': campos_encontrados,
            'campos_faltantes': campos_faltantes,
            'cobertura_alta': campos_con_alta_cobertura,
            'cobertura_baja': campos_con_baja_cobertura,
            'porcentaje_cobertura_promedio': sum(campos_encontrados.values()) / (len(self.mapeo_campos) * total_facturas) if total_facturas > 0 else 0
        }

def main():
    """Función principal para probar el mapeo."""
    mapper = N0FieldMapper()
    
    # Cargar facturas de prueba
    data_dir = Path("/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out")
    facturas_json = list(data_dir.glob("*.json"))
    
    facturas_datos = []
    for archivo in facturas_json[:3]:  # Solo las primeras 3 para prueba
        with open(archivo, 'r', encoding='utf-8') as f:
            facturas_datos.append(json.load(f))
    
    # Generar reporte
    reporte = mapper.generar_reporte_mapeo(facturas_datos)
    
    print("📊 REPORTE MAPEO N0 → SCHEMAS")
    print("=" * 50)
    print(f"Facturas analizadas: {reporte['total_facturas']}")
    print(f"Campos evaluados: {reporte['campos_evaluados']}")
    print(f"Cobertura promedio: {reporte['porcentaje_cobertura_promedio']:.1%}")
    
    print(f"\n✅ Campos con alta cobertura (>80%):")
    for campo, count in reporte['cobertura_alta'].items():
        print(f"  • {campo}: {count}/{reporte['total_facturas']} ({count/reporte['total_facturas']:.1%})")
    
    print(f"\n⚠️ Campos con baja cobertura (<50%):")
    for campo, count in reporte['cobertura_baja'].items():
        print(f"  • {campo}: {count}/{reporte['total_facturas']} ({count/reporte['total_facturas']:.1%})")

if __name__ == "__main__":
    main()
