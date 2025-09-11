#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de enriquecimiento de perfiles de consumo horario para pipeline N0 → N1
Integra datos de perfiles de consumo ESIOS (indicadores 526-532) en el proceso de enriquecimiento
"""

import logging
import sys
import os
import psycopg2
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)

class PerfilesConsumoEnrichment:
    """
    Enriquecedor de perfiles de consumo horario
    Integra datos de ESIOS para análisis de patrones de consumo
    """
    
    def __init__(self, db_url_sistema_electrico: str):
        self.db_url = db_url_sistema_electrico
        self._perfil_cache = {}
        
        # Mapeo de tipos de perfil a descripciones
        self.tipos_perfil = {
            'PVPC_2.0A_PEAJE': 'Tarifa 2.0 A (peaje por defecto)',
            'PVPC_2.0DHA_EFICIENCIA': 'Tarifa 2.0 DHA (Eficiencia 2 períodos)',
            'PVPC_2.0DHS_VEHICULO': 'Tarifa 2.0 DHS (vehículo eléctrico)',
            'PERFIL_FINAL_A': 'Perfil final de consumo A',
            'PERFIL_FINAL_B': 'Perfil final de consumo B',
            'PERFIL_FINAL_C': 'Perfil final de consumo C',
            'PERFIL_FINAL_D': 'Perfil final de consumo D'
        }
    
    def get_db_connection(self):
        """Crear conexión a base de datos sistema_electrico"""
        return psycopg2.connect(self.db_url)
    
    def enrich_with_consumption_profiles(self, n1_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece datos N1 con perfiles de consumo horario
        
        Args:
            n1_data: Datos N1 base
            
        Returns:
            Datos N1 enriquecidos con perfiles de consumo
        """
        try:
            logger.info("Iniciando enriquecimiento con perfiles de consumo")
            
            # Extraer período de facturación
            fecha_inicio = n1_data.get('fecha_inicio')
            fecha_fin = n1_data.get('fecha_fin')
            
            if not fecha_inicio or not fecha_fin:
                logger.warning("No hay fechas de facturación para obtener perfiles")
                return n1_data
            
            # Convertir fechas si son strings
            if isinstance(fecha_inicio, str):
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            if isinstance(fecha_fin, str):
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            
            # Obtener perfiles de consumo para el período
            perfiles_data = self._get_consumption_profiles_for_period(fecha_inicio, fecha_fin)
            
            if perfiles_data:
                # Calcular métricas de perfiles
                perfil_metrics = self._calculate_profile_metrics(perfiles_data, n1_data)
                
                # Añadir datos de perfiles al N1
                n1_data.update(perfil_metrics)
                
                logger.info(f"Enriquecimiento con perfiles completado: {len(perfil_metrics)} métricas añadidas")
            else:
                logger.warning("No se encontraron perfiles de consumo para el período")
            
            return n1_data
            
        except Exception as e:
            logger.error(f"Error en enriquecimiento con perfiles: {e}", exc_info=True)
            return n1_data
    
    def _get_consumption_profiles_for_period(self, fecha_inicio, fecha_fin) -> List[Dict[str, Any]]:
        """
        Obtiene perfiles de consumo para un período específico
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            
        Returns:
            Lista de registros de perfiles de consumo
        """
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                        SELECT 
                            fecha,
                            hora,
                            periodo,
                            indicador_id,
                            tipo_perfil,
                            valor_perfil,
                            unidad
                        FROM perfiles_consumo
                        WHERE fecha BETWEEN %s AND %s
                        ORDER BY fecha, periodo, indicador_id
                    """
                    
                    cur.execute(query, (fecha_inicio, fecha_fin))
                    rows = cur.fetchall()
                    
                    perfiles = []
                    for row in rows:
                        perfiles.append({
                            'fecha': row[0],
                            'hora': row[1],
                            'periodo': row[2],
                            'indicador_id': row[3],
                            'tipo_perfil': row[4],
                            'valor_perfil': float(row[5]) if row[5] else 0,
                            'unidad': row[6]
                        })
                    
                    logger.info(f"Obtenidos {len(perfiles)} registros de perfiles para período {fecha_inicio} - {fecha_fin}")
                    return perfiles
                    
        except Exception as e:
            logger.error(f"Error obteniendo perfiles de consumo: {e}")
            return []
    
    def _calculate_profile_metrics(self, perfiles_data: List[Dict[str, Any]], n1_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula métricas basadas en perfiles de consumo
        
        Args:
            perfiles_data: Datos de perfiles de consumo
            n1_data: Datos N1 base
            
        Returns:
            Diccionario con métricas calculadas
        """
        metrics = {}
        
        try:
            if not perfiles_data:
                return metrics
            
            # Agrupar por tipo de perfil
            perfiles_por_tipo = {}
            for perfil in perfiles_data:
                tipo = perfil['tipo_perfil']
                if tipo not in perfiles_por_tipo:
                    perfiles_por_tipo[tipo] = []
                perfiles_por_tipo[tipo].append(perfil)
            
            # Calcular métricas por tipo de perfil
            for tipo_perfil, datos in perfiles_por_tipo.items():
                prefix = f"perfil_{tipo_perfil.lower()}"
                
                # Estadísticas básicas
                valores = [d['valor_perfil'] for d in datos if d['valor_perfil'] > 0]
                if valores:
                    metrics[f"{prefix}_promedio"] = round(sum(valores) / len(valores), 4)
                    metrics[f"{prefix}_maximo"] = round(max(valores), 4)
                    metrics[f"{prefix}_minimo"] = round(min(valores), 4)
                    metrics[f"{prefix}_total"] = round(sum(valores), 4)
                    metrics[f"{prefix}_registros"] = len(valores)
            
            # Análisis de patrones horarios
            patrones_horarios = self._analyze_hourly_patterns(perfiles_data)
            metrics.update(patrones_horarios)
            
            # Comparación con consumo facturado
            consumo_facturado = n1_data.get('consumo_facturado_kwh', 0)
            if consumo_facturado > 0:
                comparacion = self._compare_with_billed_consumption(perfiles_data, consumo_facturado)
                metrics.update(comparacion)
            
            # Recomendaciones de tarifa
            recomendacion = self._recommend_tariff(perfiles_data, n1_data)
            if recomendacion:
                metrics['recomendacion_tarifa'] = recomendacion
            
        except Exception as e:
            logger.error(f"Error calculando métricas de perfiles: {e}")
        
        return metrics
    
    def _analyze_hourly_patterns(self, perfiles_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza patrones de consumo por horas
        
        Args:
            perfiles_data: Datos de perfiles
            
        Returns:
            Métricas de patrones horarios
        """
        patterns = {}
        
        try:
            # Agrupar por período (hora)
            consumo_por_hora = {}
            for perfil in perfiles_data:
                periodo = perfil['periodo']
                valor = perfil['valor_perfil']
                
                if periodo not in consumo_por_hora:
                    consumo_por_hora[periodo] = []
                consumo_por_hora[periodo].append(valor)
            
            # Calcular promedios por hora
            promedios_horarios = {}
            for periodo, valores in consumo_por_hora.items():
                if valores:
                    promedios_horarios[periodo] = sum(valores) / len(valores)
            
            if promedios_horarios:
                # Identificar picos y valles
                max_consumo = max(promedios_horarios.values())
                min_consumo = min(promedios_horarios.values())
                
                hora_pico = max(promedios_horarios, key=promedios_horarios.get)
                hora_valle = min(promedios_horarios, key=promedios_horarios.get)
                
                patterns['patron_hora_pico'] = hora_pico
                patterns['patron_hora_valle'] = hora_valle
                patterns['patron_consumo_pico'] = round(max_consumo, 4)
                patterns['patron_consumo_valle'] = round(min_consumo, 4)
                patterns['patron_ratio_pico_valle'] = round(max_consumo / min_consumo, 2) if min_consumo > 0 else 0
                
                # Clasificar tipo de consumidor
                tipo_consumidor = self._classify_consumer_type(promedios_horarios)
                patterns['tipo_consumidor'] = tipo_consumidor
        
        except Exception as e:
            logger.error(f"Error analizando patrones horarios: {e}")
        
        return patterns
    
    def _classify_consumer_type(self, promedios_horarios: Dict[int, float]) -> str:
        """
        Clasifica el tipo de consumidor basado en patrones horarios
        
        Args:
            promedios_horarios: Consumo promedio por hora
            
        Returns:
            Tipo de consumidor
        """
        try:
            # Definir períodos
            horas_laborales = list(range(8, 18))  # 8:00 - 17:59
            horas_nocturnas = list(range(22, 24)) + list(range(0, 7))  # 22:00 - 06:59
            horas_residenciales = list(range(18, 22))  # 18:00 - 21:59
            
            # Calcular consumo por período
            consumo_laboral = sum(promedios_horarios.get(h, 0) for h in horas_laborales)
            consumo_nocturno = sum(promedios_horarios.get(h, 0) for h in horas_nocturnas)
            consumo_residencial = sum(promedios_horarios.get(h, 0) for h in horas_residenciales)
            
            total_consumo = consumo_laboral + consumo_nocturno + consumo_residencial
            
            if total_consumo == 0:
                return "INDETERMINADO"
            
            # Calcular porcentajes
            pct_laboral = (consumo_laboral / total_consumo) * 100
            pct_nocturno = (consumo_nocturno / total_consumo) * 100
            pct_residencial = (consumo_residencial / total_consumo) * 100
            
            # Clasificar
            if pct_laboral > 50:
                return "COMERCIAL_INDUSTRIAL"
            elif pct_residencial > 40:
                return "RESIDENCIAL"
            elif pct_nocturno > 30:
                return "NOCTURNO_INTENSIVO"
            else:
                return "MIXTO"
                
        except Exception as e:
            logger.error(f"Error clasificando tipo de consumidor: {e}")
            return "INDETERMINADO"
    
    def _compare_with_billed_consumption(self, perfiles_data: List[Dict[str, Any]], consumo_facturado: float) -> Dict[str, Any]:
        """
        Compara perfiles con consumo facturado
        
        Args:
            perfiles_data: Datos de perfiles
            consumo_facturado: Consumo facturado en kWh
            
        Returns:
            Métricas de comparación
        """
        comparison = {}
        
        try:
            # Sumar todos los perfiles (promedio de todos los tipos)
            total_perfiles = sum(p['valor_perfil'] for p in perfiles_data if p['valor_perfil'] > 0)
            num_registros = len([p for p in perfiles_data if p['valor_perfil'] > 0])
            
            if num_registros > 0 and total_perfiles > 0:
                promedio_perfiles = total_perfiles / num_registros
                
                # Estimar consumo total basado en perfiles (simplificado)
                # Asumiendo que tenemos datos horarios para el período
                dias_periodo = len(set(p['fecha'] for p in perfiles_data))
                if dias_periodo > 0:
                    estimado_total = promedio_perfiles * 24 * dias_periodo
                    
                    comparison['consumo_estimado_perfiles'] = round(estimado_total, 2)
                    comparison['diferencia_vs_facturado'] = round(abs(estimado_total - consumo_facturado), 2)
                    comparison['ratio_estimado_facturado'] = round(estimado_total / consumo_facturado, 4) if consumo_facturado > 0 else 0
                    
                    # Evaluación de precisión
                    diferencia_pct = abs(estimado_total - consumo_facturado) / consumo_facturado * 100 if consumo_facturado > 0 else 100
                    
                    if diferencia_pct < 5:
                        precision = "ALTA"
                    elif diferencia_pct < 15:
                        precision = "MEDIA"
                    else:
                        precision = "BAJA"
                    
                    comparison['precision_estimacion'] = precision
                    comparison['diferencia_porcentual'] = round(diferencia_pct, 2)
        
        except Exception as e:
            logger.error(f"Error comparando con consumo facturado: {e}")
        
        return comparison
    
    def _recommend_tariff(self, perfiles_data: List[Dict[str, Any]], n1_data: Dict[str, Any]) -> Optional[str]:
        """
        Recomienda tarifa óptima basada en perfiles de consumo
        
        Args:
            perfiles_data: Datos de perfiles
            n1_data: Datos N1 base
            
        Returns:
            Recomendación de tarifa
        """
        try:
            if not perfiles_data:
                return None
            
            # Analizar distribución horaria
            consumo_por_hora = {}
            for perfil in perfiles_data:
                periodo = perfil['periodo']
                valor = perfil['valor_perfil']
                
                if periodo not in consumo_por_hora:
                    consumo_por_hora[periodo] = []
                consumo_por_hora[periodo].append(valor)
            
            # Calcular promedios
            promedios = {h: sum(v)/len(v) for h, v in consumo_por_hora.items() if v}
            
            if not promedios:
                return None
            
            # Definir períodos tarifarios típicos
            horas_punta = list(range(10, 14)) + list(range(18, 22))  # 10-14h y 18-22h
            horas_valle = list(range(0, 8)) + list(range(22, 24))    # 0-8h y 22-24h
            horas_llano = [h for h in range(24) if h not in horas_punta and h not in horas_valle]
            
            # Calcular consumo por período
            consumo_punta = sum(promedios.get(h, 0) for h in horas_punta)
            consumo_valle = sum(promedios.get(h, 0) for h in horas_valle)
            consumo_llano = sum(promedios.get(h, 0) for h in horas_llano)
            
            total = consumo_punta + consumo_valle + consumo_llano
            
            if total == 0:
                return None
            
            # Calcular porcentajes
            pct_punta = (consumo_punta / total) * 100
            pct_valle = (consumo_valle / total) * 100
            
            # Recomendar tarifa
            if pct_valle > 40:
                return "Tarifa con discriminación horaria - Alto consumo nocturno"
            elif pct_punta > 60:
                return "Revisar horarios de consumo - Alto consumo en horas punta"
            elif pct_valle > 25 and pct_punta < 40:
                return "Tarifa 2.0 DHA recomendada - Buen perfil nocturno"
            else:
                return "Tarifa actual adecuada - Perfil de consumo equilibrado"
                
        except Exception as e:
            logger.error(f"Error recomendando tarifa: {e}")
            return None

if __name__ == "__main__":
    # Test básico del módulo
    logging.basicConfig(level=logging.INFO)
    
    # Datos de prueba
    sample_n1 = {
        'fecha_inicio': '2024-08-01',
        'fecha_fin': '2024-08-31',
        'consumo_facturado_kwh': 2500.75
    }
    
    print("=== Test Perfiles Consumo Enrichment ===")
    print("Módulo creado para integración con pipeline N0→N1")
    print("Requiere datos en tabla 'perfiles_consumo' para funcionar")
