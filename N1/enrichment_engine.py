#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Motor de enriquecimiento básico para pipeline N0 → N1
FASE 1: Integra APIs directas (clima, geolocalización, OMIE)
FASE 2: Se actualizará para usar BD cache asíncrona
"""

import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

# Añadir rutas necesarias
sys.path.append(str(Path(__file__).parent.parent / 'shared'))
sys.path.append('/Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/motor_mejora/src')

# Importar módulos de enriquecimiento existentes
try:
    from enriquecimiento.clima import calcular_precipitacion_y_temperatura
    from enriquecimiento.geolocalizacion import get_lat_lon
    from enriquecimiento.omie import obtener_precio_medio
except ImportError as e:
    logging.warning(f"No se pudieron importar módulos de enriquecimiento: {e}")
    # Funciones mock para desarrollo
    def calcular_precipitacion_y_temperatura(fecha, lat, lon):
        return None, None
    def get_lat_lon(address):
        return None, None
    def obtener_precio_medio(fecha):
        return None

from field_mappings import add_enrichment_fields

logger = logging.getLogger(__name__)

class EnrichmentEngine:
    """
    Motor de enriquecimiento para datos N1
    Integra geolocalización, clima y precios OMIE
    """
    
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.cache_hits = 0
        self.api_calls = 0
        
        # Cache temporal en memoria para sesión actual
        self._geo_cache = {}
        self._clima_cache = {}
        self._omie_cache = {}
    
    def enrich_n1_data(self, n1_base: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece datos base N1 con información externa
        
        Args:
            n1_base: Datos N1 base (sin enriquecimiento)
            
        Returns:
            Datos N1 enriquecidos
        """
        try:
            logger.info("Iniciando enriquecimiento de datos N1")
            
            enrichment_data = {}
            
            # 1. Geolocalización
            lat, lon = self._get_coordinates(n1_base.get('direccion', ''))
            if lat and lon:
                enrichment_data['latitud'] = lat
                enrichment_data['longitud'] = lon
                logger.info(f"Coordenadas obtenidas: ({lat:.6f}, {lon:.6f})")
                
                # 2. Datos climáticos (requiere coordenadas)
                precip, temp = self._get_climate_data(n1_base, lat, lon)
                if precip is not None:
                    enrichment_data['precipitacion_mm'] = precip
                if temp is not None:
                    enrichment_data['temperatura_media_c'] = temp
                
            else:
                logger.warning("No se pudieron obtener coordenadas para enriquecimiento climático")
            
            # 3. Precios OMIE
            precio_kwh, precio_mwh = self._get_omie_prices(n1_base)
            if precio_kwh:
                enrichment_data['precio_omie_kwh'] = precio_kwh
                enrichment_data['precio_omie_mwh'] = precio_mwh
            
            # 4. KPIs calculados
            kpis = self._calculate_kpis(n1_base, enrichment_data)
            enrichment_data.update(kpis)
            
            # 5. Métricas de sostenibilidad
            sustainability = self._calculate_sustainability_metrics(n1_base, enrichment_data)
            enrichment_data.update(sustainability)
            
            # Combinar datos base con enriquecimiento
            n1_enriched = add_enrichment_fields(n1_base, enrichment_data)
            
            self.processed_count += 1
            logger.info(f"Enriquecimiento completado: {len(enrichment_data)} campos añadidos")
            
            return n1_enriched
            
        except Exception as e:
            logger.error(f"Error en enriquecimiento N1: {e}", exc_info=True)
            self.error_count += 1
            # Retornar datos base sin enriquecimiento en caso de error
            return add_enrichment_fields(n1_base, {})
    
    def _get_coordinates(self, direccion: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Obtiene coordenadas geográficas de una dirección
        
        Args:
            direccion: Dirección postal
            
        Returns:
            Tupla (latitud, longitud) o (None, None)
        """
        if not direccion:
            return None, None
        
        # Verificar cache
        if direccion in self._geo_cache:
            self.cache_hits += 1
            return self._geo_cache[direccion]
        
        try:
            self.api_calls += 1
            lat, lon = get_lat_lon(direccion)
            
            # Guardar en cache
            self._geo_cache[direccion] = (lat, lon)
            
            return lat, lon
            
        except Exception as e:
            logger.error(f"Error obteniendo coordenadas: {e}")
            return None, None
    
    def _get_climate_data(self, n1_base: Dict[str, Any], lat: float, lon: float) -> Tuple[Optional[float], Optional[float]]:
        """
        Obtiene datos climáticos para ubicación y período
        
        Args:
            n1_base: Datos N1 base
            lat: Latitud
            lon: Longitud
            
        Returns:
            Tupla (precipitación_mm, temperatura_media_c)
        """
        try:
            # Usar fecha de fin de facturación
            fecha_str = n1_base.get('fecha_fin')
            if not fecha_str:
                logger.warning("No hay fecha_fin para obtener datos climáticos")
                return None, None
            
            # Convertir fecha string a datetime
            if isinstance(fecha_str, str):
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
            else:
                fecha = fecha_str
            
            # Crear clave de cache
            cache_key = f"{lat:.4f}_{lon:.4f}_{fecha.strftime('%Y-%m')}"
            
            if cache_key in self._clima_cache:
                self.cache_hits += 1
                return self._clima_cache[cache_key]
            
            self.api_calls += 1
            precip, temp = calcular_precipitacion_y_temperatura(fecha, lat, lon)
            
            # Guardar en cache
            self._clima_cache[cache_key] = (precip, temp)
            
            return precip, temp
            
        except Exception as e:
            logger.error(f"Error obteniendo datos climáticos: {e}")
            return None, None
    
    def _get_omie_prices(self, n1_base: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        """
        Obtiene precios OMIE para el período de facturación
        
        Args:
            n1_base: Datos N1 base
            
        Returns:
            Tupla (precio_kwh, precio_mwh)
        """
        try:
            fecha_str = n1_base.get('fecha_fin')
            if not fecha_str:
                logger.warning("No hay fecha_fin para obtener precios OMIE")
                return None, None
            
            # Convertir fecha
            if isinstance(fecha_str, str):
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
            else:
                fecha = fecha_str
            
            # Crear clave de cache por mes
            cache_key = fecha.strftime('%Y-%m')
            
            if cache_key in self._omie_cache:
                self.cache_hits += 1
                precio_kwh = self._omie_cache[cache_key]
            else:
                self.api_calls += 1
                precio_kwh = obtener_precio_medio(fecha)
                self._omie_cache[cache_key] = precio_kwh
            
            if precio_kwh:
                precio_mwh = precio_kwh * 1000
                return precio_kwh, precio_mwh
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error obteniendo precios OMIE: {e}")
            return None, None
    
    def _calculate_kpis(self, n1_base: Dict[str, Any], enrichment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula KPIs energéticos
        
        Args:
            n1_base: Datos base N1
            enrichment_data: Datos de enriquecimiento parciales
            
        Returns:
            Diccionario con KPIs calculados
        """
        kpis = {}
        
        try:
            consumo = n1_base.get('consumo_facturado_kwh', 0)
            importe = n1_base.get('importe_total', 0)
            precio_omie = enrichment_data.get('precio_omie_kwh')
            
            # Coste promedio por kWh
            if consumo > 0 and importe > 0:
                coste_kwh = importe / consumo
                kpis['coste_kwh_promedio'] = round(coste_kwh, 6)
                
                # Ratio vs precio de mercado
                if precio_omie:
                    ratio = coste_kwh / precio_omie
                    kpis['ratio_precio_mercado'] = round(ratio, 4)
            
            # Eficiencia energética (consumo/día)
            fecha_inicio = n1_base.get('fecha_inicio')
            fecha_fin = n1_base.get('fecha_fin')
            
            if fecha_inicio and fecha_fin and consumo > 0:
                if isinstance(fecha_inicio, str):
                    inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                    fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
                else:
                    inicio = fecha_inicio
                    fin = fecha_fin
                
                dias = (fin - inicio).days + 1
                if dias > 0:
                    consumo_diario = consumo / dias
                    kpis['eficiencia_energetica'] = round(consumo_diario, 2)
            
        except Exception as e:
            logger.error(f"Error calculando KPIs: {e}")
        
        return kpis
    
    def _calculate_sustainability_metrics(self, n1_base: Dict[str, Any], enrichment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula métricas de sostenibilidad
        
        Args:
            n1_base: Datos base N1
            enrichment_data: Datos de enriquecimiento parciales
            
        Returns:
            Diccionario con métricas de sostenibilidad
        """
        sustainability = {}
        
        try:
            consumo = n1_base.get('consumo_facturado_kwh', 0)
            emisiones_kg_kwh = n1_base.get('emisiones_co2_kg_kwh', 0)
            renovable_pct = n1_base.get('mix_energetico_renovable_pct', 0)
            
            # Huella de carbono total
            if consumo > 0 and emisiones_kg_kwh > 0:
                huella_carbono = consumo * emisiones_kg_kwh
                sustainability['huella_carbono_kg'] = round(huella_carbono, 2)
            
            # Rating de sostenibilidad (0-100)
            if renovable_pct is not None:
                # Rating basado en % renovable (simplificado)
                if renovable_pct >= 80:
                    rating = 'A'
                elif renovable_pct >= 60:
                    rating = 'B'
                elif renovable_pct >= 40:
                    rating = 'C'
                elif renovable_pct >= 20:
                    rating = 'D'
                else:
                    rating = 'E'
                
                sustainability['rating_sostenibilidad'] = rating
            
            # Ahorro potencial (estimación básica)
            coste_kwh = enrichment_data.get('coste_kwh_promedio')
            if coste_kwh and consumo > 0:
                # Estimación: 10% ahorro con mejoras básicas
                ahorro_potencial = (consumo * coste_kwh * 0.10)
                sustainability['ahorro_potencial_eur'] = round(ahorro_potencial, 2)
            
            # Recomendación básica
            if renovable_pct is not None and renovable_pct < 50:
                sustainability['recomendacion_mejora'] = 'Considerar tarifa con mayor % renovable'
            elif enrichment_data.get('ratio_precio_mercado', 1) > 1.2:
                sustainability['recomendacion_mejora'] = 'Revisar tarifa energética - precio elevado vs mercado'
            else:
                sustainability['recomendacion_mejora'] = 'Mantener hábitos de consumo eficiente'
            
        except Exception as e:
            logger.error(f"Error calculando métricas sostenibilidad: {e}")
        
        return sustainability
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del motor de enriquecimiento
        
        Returns:
            Diccionario con estadísticas
        """
        total_requests = self.cache_hits + self.api_calls
        cache_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'processed': self.processed_count,
            'errors': self.error_count,
            'api_calls': self.api_calls,
            'cache_hits': self.cache_hits,
            'cache_rate_pct': round(cache_rate, 1),
            'success_rate': (self.processed_count / (self.processed_count + self.error_count) * 100) 
                           if (self.processed_count + self.error_count) > 0 else 0
        }

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test con datos N1 base
    sample_n1_base = {
        "cliente": "EMPRESA EJEMPLO SL",
        "direccion": "PLAZA MAYOR 1, MADRID",
        "cups": "ES0031408000000000002JN",
        "nif": "B12345678",
        "fecha_inicio": "2024-08-01",
        "fecha_fin": "2024-08-31",
        "consumo_facturado_kwh": 2500.75,
        "importe_total": 450.30,
        "mix_energetico_renovable_pct": 45.2,
        "emisiones_co2_kg_kwh": 0.25
    }
    
    print("=== Test Enrichment Engine ===")
    
    engine = EnrichmentEngine()
    enriched_data = engine.enrich_n1_data(sample_n1_base)
    
    print(f"✓ Enriquecimiento completado")
    print(f"  Campos base: {len(sample_n1_base)}")
    print(f"  Campos enriquecidos: {len(enriched_data)}")
    print(f"  Campos añadidos: {len(enriched_data) - len(sample_n1_base)}")
    
    # Mostrar algunos campos enriquecidos
    enrichment_fields = ['latitud', 'longitud', 'coste_kwh_promedio', 'rating_sostenibilidad']
    for field in enrichment_fields:
        value = enriched_data.get(field)
        if value is not None:
            print(f"  {field}: {value}")
    
    # Estadísticas
    stats = engine.get_statistics()
    print(f"  Estadísticas: {stats}")
    
    print("\n=== Test completado ===")
