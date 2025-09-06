#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificador de Preparación N0 para eSCORE
Enfoque pragmático: verifica si N0 tiene los campos críticos necesarios para eSCORE.
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CampoEscore:
    """Campo necesario para eSCORE."""
    nombre: str
    indicador: str
    factor: str
    criticidad: str  # 'critico', 'importante', 'opcional'
    descripcion: str
    rutas_posibles: List[str]

@dataclass
class ResultadoPreparacion:
    """Resultado de verificación de preparación N0."""
    n0_listo_para_escore: bool
    cobertura_campos_criticos: float
    cobertura_campos_importantes: float
    cobertura_total: float
    campos_encontrados: Dict[str, str]  # campo -> ruta_encontrada
    campos_faltantes_criticos: List[str]
    campos_faltantes_importantes: List[str]
    facturas_analizadas: int
    recomendaciones: List[str]

class N0ReadinessChecker:
    """Verificador pragmático de preparación N0 para eSCORE."""
    
    def __init__(self):
        # Campos críticos necesarios para eSCORE (basados en test_campos_electricidad.py)
        self.campos_escore = [
            # IDENTIFICACIÓN (CRÍTICOS)
            CampoEscore("numero_factura", "GENERAL", "identificacion", "critico", 
                       "Número único de factura", 
                       ["invoice.numero_factura", "factura.numero", "billing.numero_factura"]),
            
            CampoEscore("cups", "GENERAL", "identificacion", "critico", 
                       "Código CUPS del suministro", 
                       ["supply_point.cups", "contract_2x3.cups", "datos_suministro.cups"]),
            
            CampoEscore("fecha_factura", "GENERAL", "identificacion", "critico", 
                       "Fecha de emisión de la factura", 
                       ["invoice.fecha_emision", "billing.fecha_factura", "periodo.fecha_inicio"]),
            
            # CONSUMO (CRÍTICOS para IC, IE, IT)
            CampoEscore("consumo_facturado_kwh", "IC", "consumo_anual", "critico", 
                       "Consumo total facturado en kWh", 
                       ["consumption.total_kwh", "consumo.total", "energia.consumo_total"]),
            
            CampoEscore("consumo_p1", "IE", "variacion_estacional", "critico", 
                       "Consumo en periodo punta", 
                       ["consumption.punta_kwh", "periodos.p1.consumo", "energia.punta"]),
            
            CampoEscore("consumo_p2", "IE", "variacion_estacional", "critico", 
                       "Consumo en periodo llano", 
                       ["consumption.llano_kwh", "periodos.p2.consumo", "energia.llano"]),
            
            CampoEscore("consumo_p3", "IE", "variacion_estacional", "critico", 
                       "Consumo en periodo valle", 
                       ["consumption.valle_kwh", "periodos.p3.consumo", "energia.valle"]),
            
            # POTENCIA (CRÍTICOS para IP)
            CampoEscore("potencia_contratada_kw", "IP", "optimizacion_potencia", "critico", 
                       "Potencia contratada en kW", 
                       ["power.contratada_kw", "potencia.contratada", "contract_2x3.potencia_contratada"]),
            
            CampoEscore("potencia_maxima_p1", "IP", "excesos_potencia", "critico", 
                       "Potencia máxima en periodo 1", 
                       ["power.maxima_p1_kw", "potencia.maxima_punta"]),
            
            CampoEscore("potencia_maxima_p2", "IP", "excesos_potencia", "critico", 
                       "Potencia máxima en periodo 2", 
                       ["power.maxima_p2_kw", "potencia.maxima_llano"]),
            
            # COSTES (IMPORTANTES)
            CampoEscore("importe_total_factura", "GENERAL", "coste", "importante", 
                       "Importe total de la factura", 
                       ["billing.total_factura", "costes.total", "factura.importe_total"]),
            
            CampoEscore("termino_energia", "IT", "optimizacion_tarifaria", "importante", 
                       "Coste del término de energía", 
                       ["billing.termino_energia", "costes.energia"]),
            
            CampoEscore("termino_potencia", "IT", "optimizacion_tarifaria", "importante", 
                       "Coste del término de potencia", 
                       ["billing.termino_potencia", "costes.potencia"]),
            
            # DATOS TÉCNICOS (IMPORTANTES)
            CampoEscore("tarifa_acceso", "IT", "tipo_peaje", "importante", 
                       "Tarifa de acceso aplicada", 
                       ["contract_2x3.tarifa_acceso", "tarifa.acceso"]),
            
            CampoEscore("tipo_peaje", "IT", "tipo_peaje", "importante", 
                       "Tipo de peaje aplicado", 
                       ["contract_2x3.peaje", "tarifa.peaje"]),
            
            # UBICACIÓN (IMPORTANTES para IC)
            CampoEscore("provincia", "IC", "zona_geografica", "importante", 
                       "Provincia del suministro", 
                       ["supply_point.datos_suministro.direccion_suministro.provincia", "direccion.provincia"]),
            
            CampoEscore("codigo_postal", "IC", "zona_geografica", "importante", 
                       "Código postal del suministro", 
                       ["supply_point.datos_suministro.direccion_suministro.codigo_postal", "direccion.cp"]),
            
            # REACTIVA (OPCIONALES para IF)
            CampoEscore("energia_reactiva_p1", "IF", "factor_potencia_medio", "opcional", 
                       "Energía reactiva periodo 1", 
                       ["reactive.p1_kvarh", "reactiva.punta"]),
            
            CampoEscore("penalizacion_reactiva_p1", "IF", "penalizaciones_reactiva", "opcional", 
                       "Penalización reactiva P1", 
                       ["reactive.penalizacion_p1", "costes.reactiva_p1"]),
            
            # AUTOCONSUMO (OPCIONALES para IR)
            CampoEscore("autoconsumo_kwh", "IR", "cobertura_renovable", "opcional", 
                       "Energía de autoconsumo", 
                       ["self_consumption.total_kwh", "autoconsumo.generado"]),
            
            CampoEscore("excedentes_kwh", "IR", "aprovechamiento_excedentes", "opcional", 
                       "Excedentes de autoconsumo", 
                       ["self_consumption.excedentes_kwh", "autoconsumo.excedentes"])
        ]
    
    def extraer_valor_por_ruta(self, datos: dict, ruta: str) -> Optional[any]:
        """Extrae valor siguiendo una ruta con notación punto."""
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
    
    def buscar_campo_en_factura(self, datos_factura: dict, campo: CampoEscore) -> Optional[str]:
        """Busca un campo en la factura y devuelve la ruta donde lo encontró."""
        
        # 1. Intentar rutas específicas
        for ruta in campo.rutas_posibles:
            valor = self.extraer_valor_por_ruta(datos_factura, ruta)
            if valor is not None:
                return ruta
        
        # 2. Búsqueda recursiva por nombre
        ruta_encontrada = self._buscar_recursivo(datos_factura, campo.nombre)
        if ruta_encontrada:
            return ruta_encontrada
        
        # 3. Búsqueda por similitud
        ruta_similar = self._buscar_similar(datos_factura, campo.nombre)
        if ruta_similar:
            return ruta_similar
        
        return None
    
    def _buscar_recursivo(self, datos: dict, campo_objetivo: str, prefijo: str = "") -> Optional[str]:
        """Búsqueda recursiva por nombre exacto."""
        if isinstance(datos, dict):
            for key, value in datos.items():
                ruta_actual = f"{prefijo}.{key}" if prefijo else key
                
                # Coincidencia exacta
                if key == campo_objetivo:
                    if isinstance(value, dict) and 'value' in value:
                        return ruta_actual
                    elif not isinstance(value, dict):
                        return ruta_actual
                
                # Búsqueda recursiva
                if isinstance(value, dict):
                    resultado = self._buscar_recursivo(value, campo_objetivo, ruta_actual)
                    if resultado:
                        return resultado
        
        return None
    
    def _buscar_similar(self, datos: dict, campo_objetivo: str, prefijo: str = "") -> Optional[str]:
        """Búsqueda por similitud de nombres."""
        if isinstance(datos, dict):
            for key, value in datos.items():
                ruta_actual = f"{prefijo}.{key}" if prefijo else key
                
                # Similitud por palabras clave
                if self._son_similares(key, campo_objetivo):
                    if isinstance(value, dict) and 'value' in value:
                        return ruta_actual
                    elif not isinstance(value, dict):
                        return ruta_actual
                
                # Búsqueda recursiva
                if isinstance(value, dict):
                    resultado = self._buscar_similar(value, campo_objetivo, ruta_actual)
                    if resultado:
                        return resultado
        
        return None
    
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
        
        # Coincidencia de palabras clave importantes
        palabras_clave = ['consumo', 'potencia', 'factura', 'cups', 'fecha', 'tarifa', 'energia', 'reactiva']
        for palabra in palabras_clave:
            if palabra in campo1_clean and palabra in campo2_clean:
                return True
        
        return False
    
    def verificar_preparacion_n0(self, directorio_n0: str = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out") -> ResultadoPreparacion:
        """Verifica si N0 está preparado para eSCORE."""
        
        print("🔍 VERIFICANDO PREPARACIÓN N0 PARA eSCORE")
        print("=" * 60)
        
        data_dir = Path(directorio_n0)
        facturas_json = list(data_dir.glob("*.json"))
        
        print(f"📄 Analizando {len(facturas_json)} facturas...")
        
        # Contadores por criticidad
        campos_criticos = [c for c in self.campos_escore if c.criticidad == 'critico']
        campos_importantes = [c for c in self.campos_escore if c.criticidad == 'importante']
        campos_opcionales = [c for c in self.campos_escore if c.criticidad == 'opcional']
        
        campos_encontrados = {}
        campos_faltantes_criticos = []
        campos_faltantes_importantes = []
        
        # Analizar cada campo en todas las facturas
        for campo in self.campos_escore:
            encontrado_en_alguna = False
            ruta_encontrada = None
            
            for archivo_factura in facturas_json[:3]:  # Analizar las primeras 3
                try:
                    with open(archivo_factura, 'r', encoding='utf-8') as f:
                        datos_factura = json.load(f)
                    
                    ruta = self.buscar_campo_en_factura(datos_factura, campo)
                    if ruta:
                        encontrado_en_alguna = True
                        ruta_encontrada = ruta
                        break
                        
                except Exception as e:
                    continue
            
            if encontrado_en_alguna:
                campos_encontrados[campo.nombre] = ruta_encontrada
                print(f"  ✅ {campo.nombre} ({campo.criticidad}): {ruta_encontrada}")
            else:
                if campo.criticidad == 'critico':
                    campos_faltantes_criticos.append(campo.nombre)
                    print(f"  ❌ {campo.nombre} (CRÍTICO): NO ENCONTRADO")
                elif campo.criticidad == 'importante':
                    campos_faltantes_importantes.append(campo.nombre)
                    print(f"  ⚠️ {campo.nombre} (importante): no encontrado")
                else:
                    print(f"  ⏭️ {campo.nombre} (opcional): no encontrado")
        
        # Calcular coberturas
        criticos_encontrados = len([c for c in campos_criticos if c.nombre in campos_encontrados])
        importantes_encontrados = len([c for c in campos_importantes if c.nombre in campos_encontrados])
        
        cobertura_criticos = criticos_encontrados / len(campos_criticos) if campos_criticos else 1.0
        cobertura_importantes = importantes_encontrados / len(campos_importantes) if campos_importantes else 1.0
        cobertura_total = len(campos_encontrados) / len(self.campos_escore)
        
        # Determinar si N0 está listo
        n0_listo = cobertura_criticos >= 0.9 and cobertura_importantes >= 0.7
        
        # Generar recomendaciones
        recomendaciones = []
        if cobertura_criticos < 0.9:
            recomendaciones.append(f"🚨 CRÍTICO: Solo {cobertura_criticos:.1%} de campos críticos encontrados. Mínimo requerido: 90%")
        if cobertura_importantes < 0.7:
            recomendaciones.append(f"⚠️ IMPORTANTE: Solo {cobertura_importantes:.1%} de campos importantes encontrados. Recomendado: 70%")
        if n0_listo:
            recomendaciones.append("✅ N0 cumple requisitos mínimos para eSCORE")
            recomendaciones.append("🚀 Proceder con implementación N1")
        else:
            recomendaciones.append("🔧 Mejorar extracción antes de avanzar a N1")
        
        return ResultadoPreparacion(
            n0_listo_para_escore=n0_listo,
            cobertura_campos_criticos=cobertura_criticos,
            cobertura_campos_importantes=cobertura_importantes,
            cobertura_total=cobertura_total,
            campos_encontrados=campos_encontrados,
            campos_faltantes_criticos=campos_faltantes_criticos,
            campos_faltantes_importantes=campos_faltantes_importantes,
            facturas_analizadas=len(facturas_json),
            recomendaciones=recomendaciones
        )
    
    def generar_reporte_preparacion(self, resultado: ResultadoPreparacion) -> str:
        """Genera reporte detallado de preparación."""
        
        reporte = []
        reporte.append("# REPORTE PREPARACIÓN N0 PARA eSCORE")
        reporte.append("")
        reporte.append(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        reporte.append(f"**Facturas analizadas:** {resultado.facturas_analizadas}")
        reporte.append("")
        
        # Estado general
        estado = "✅ LISTO" if resultado.n0_listo_para_escore else "🔧 REQUIERE MEJORAS"
        reporte.append(f"**Estado N0:** {estado}")
        reporte.append("")
        
        # Métricas de cobertura
        reporte.append("## 📊 Métricas de Cobertura")
        reporte.append("")
        reporte.append(f"- **Campos críticos:** {resultado.cobertura_campos_criticos:.1%} (mínimo: 90%)")
        reporte.append(f"- **Campos importantes:** {resultado.cobertura_campos_importantes:.1%} (recomendado: 70%)")
        reporte.append(f"- **Cobertura total:** {resultado.cobertura_total:.1%}")
        reporte.append("")
        
        # Campos encontrados
        if resultado.campos_encontrados:
            reporte.append("## ✅ Campos Encontrados")
            reporte.append("")
            for campo, ruta in resultado.campos_encontrados.items():
                campo_info = next((c for c in self.campos_escore if c.nombre == campo), None)
                if campo_info:
                    reporte.append(f"- **{campo}** ({campo_info.criticidad})")
                    reporte.append(f"  - Indicador: {campo_info.indicador} → {campo_info.factor}")
                    reporte.append(f"  - Ruta: `{ruta}`")
            reporte.append("")
        
        # Campos faltantes críticos
        if resultado.campos_faltantes_criticos:
            reporte.append("## 🚨 Campos Críticos Faltantes")
            reporte.append("")
            for campo in resultado.campos_faltantes_criticos:
                campo_info = next((c for c in self.campos_escore if c.nombre == campo), None)
                if campo_info:
                    reporte.append(f"- **{campo}**")
                    reporte.append(f"  - {campo_info.descripcion}")
                    reporte.append(f"  - Indicador: {campo_info.indicador} → {campo_info.factor}")
                    reporte.append(f"  - Rutas esperadas: {', '.join(campo_info.rutas_posibles)}")
            reporte.append("")
        
        # Campos importantes faltantes
        if resultado.campos_faltantes_importantes:
            reporte.append("## ⚠️ Campos Importantes Faltantes")
            reporte.append("")
            for campo in resultado.campos_faltantes_importantes:
                campo_info = next((c for c in self.campos_escore if c.nombre == campo), None)
                if campo_info:
                    reporte.append(f"- **{campo}**: {campo_info.descripcion}")
            reporte.append("")
        
        # Recomendaciones
        reporte.append("## 💡 Recomendaciones")
        reporte.append("")
        for rec in resultado.recomendaciones:
            reporte.append(f"- {rec}")
        reporte.append("")
        
        return "\n".join(reporte)

def main():
    """Función principal."""
    checker = N0ReadinessChecker()
    
    # Verificar preparación
    resultado = checker.verificar_preparacion_n0()
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    print("📋 RESUMEN PREPARACIÓN N0")
    print("=" * 60)
    print(f"✅ Campos críticos: {resultado.cobertura_campos_criticos:.1%}")
    print(f"⚠️ Campos importantes: {resultado.cobertura_campos_importantes:.1%}")
    print(f"📊 Cobertura total: {resultado.cobertura_total:.1%}")
    print(f"🎯 N0 listo para eSCORE: {'SÍ' if resultado.n0_listo_para_escore else 'NO'}")
    
    # Generar reporte
    reporte = checker.generar_reporte_preparacion(resultado)
    archivo_reporte = f"reporte_preparacion_n0_escore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(archivo_reporte, 'w', encoding='utf-8') as f:
        f.write(reporte)
    
    print(f"📄 Reporte guardado: {archivo_reporte}")
    
    return resultado.n0_listo_para_escore

if __name__ == "__main__":
    main()
