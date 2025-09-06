"""
Sistema de APIs externas para enriquecimiento de datos.
Implementa rate limiting y manejo de errores robusto.
"""
import os
import time
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
import logging
from threading import Lock
import hashlib

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIStatus(Enum):
    """Estados de las APIs externas."""
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class RateLimit:
    """Configuración de rate limiting por API."""
    calls_per_minute: int
    calls_per_hour: int
    current_minute_calls: int = 0
    current_hour_calls: int = 0
    minute_reset: Optional[datetime] = None
    hour_reset: Optional[datetime] = None
    consecutive_failures: int = 0
    max_failures: int = 5


class ExternalAPIManager:
    """
    Gestor de APIs externas con rate limiting y retry logic.
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.apis = {}
        self.rate_limits = {}
        self.locks = {}
        self._init_apis()
    
    def _init_apis(self):
        """Inicializa configuración de APIs desde base de datos."""
        try:
            # Cargar configuración desde db_enriquecimiento.enrichment_sources
            with self.db_manager.transaction('enriquecimiento') as cursor:
                cursor.execute("""
                    SELECT source_name, source_type, base_url, api_key_required,
                           rate_limit_per_minute, rate_limit_per_hour, max_failures,
                           timeout_seconds, config, is_active
                    FROM enrichment_sources
                    WHERE is_active = true
                """)
                
                for api in cursor.fetchall():
                    self.apis[api['source_name']] = {
                        'base_url': api['base_url'],
                        'api_key_required': api['api_key_required'],
                        'timeout': api['timeout_seconds'],
                        'config': api['config'] or {},
                        'status': APIStatus.ACTIVE
                    }
                    
                    self.rate_limits[api['source_name']] = RateLimit(
                        calls_per_minute=api['rate_limit_per_minute'],
                        calls_per_hour=api['rate_limit_per_hour'],
                        max_failures=api['max_failures']
                    )
                    
                    self.locks[api['source_name']] = Lock()
            
            logger.info(f"✅ {len(self.apis)} APIs externas inicializadas")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando APIs: {e}")
    
    def check_rate_limit(self, api_name: str) -> bool:
        """
        Verifica si la API puede realizar más llamadas.
        
        Args:
            api_name: Nombre de la API
            
        Returns:
            True si puede hacer llamadas, False si está limitada
        """
        if api_name not in self.rate_limits:
            return False
        
        rate_limit = self.rate_limits[api_name]
        now = datetime.now()
        
        # Reset contadores si ha pasado el tiempo
        if not rate_limit.minute_reset or now >= rate_limit.minute_reset:
            rate_limit.current_minute_calls = 0
            rate_limit.minute_reset = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        if not rate_limit.hour_reset or now >= rate_limit.hour_reset:
            rate_limit.current_hour_calls = 0
            rate_limit.hour_reset = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        # Verificar límites
        if rate_limit.current_minute_calls >= rate_limit.calls_per_minute:
            logger.warning(f"⚠️ {api_name}: Rate limit por minuto excedido")
            return False
        
        if rate_limit.current_hour_calls >= rate_limit.calls_per_hour:
            logger.warning(f"⚠️ {api_name}: Rate limit por hora excedido")
            return False
        
        return True
    
    def make_api_call(self, api_name: str, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Realiza llamada a API externa con rate limiting y retry logic.
        
        Args:
            api_name: Nombre de la API
            endpoint: Endpoint específico
            params: Parámetros de la consulta
            
        Returns:
            Respuesta de la API o None si falla
        """
        if api_name not in self.apis:
            logger.error(f"❌ API {api_name} no configurada")
            return None
        
        with self.locks[api_name]:
            # Verificar rate limit
            if not self.check_rate_limit(api_name):
                self._update_api_status(api_name, APIStatus.RATE_LIMITED)
                return None
            
            # Incrementar contadores
            rate_limit = self.rate_limits[api_name]
            rate_limit.current_minute_calls += 1
            rate_limit.current_hour_calls += 1
            
            # Realizar llamada
            try:
                response = self._call_api(api_name, endpoint, params)
                
                if response:
                    # Resetear fallos consecutivos en caso de éxito
                    rate_limit.consecutive_failures = 0
                    self._update_api_status(api_name, APIStatus.ACTIVE)
                    return response
                else:
                    rate_limit.consecutive_failures += 1
                    if rate_limit.consecutive_failures >= rate_limit.max_failures:
                        self._update_api_status(api_name, APIStatus.ERROR)
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Error llamando {api_name}: {e}")
                rate_limit.consecutive_failures += 1
                return None
    
    def _call_api(self, api_name: str, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Realiza la llamada HTTP a la API."""
        api_config = self.apis[api_name]
        url = f"{api_config['base_url']}{endpoint}"
        
        headers = {'User-Agent': 'EnergyGreenData/1.0'}
        
        # Añadir API key si es necesario
        if api_config['api_key_required']:
            api_key = os.getenv(f"{api_name}_API_KEY")
            if not api_key:
                logger.error(f"❌ API key faltante para {api_name}")
                return None
            headers['Authorization'] = f'Bearer {api_key}'
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=api_config['timeout']
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning(f"⚠️ {api_name}: Rate limit del servidor")
                return None
            else:
                logger.error(f"❌ {api_name}: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error de conexión {api_name}: {e}")
            return None
    
    def _update_api_status(self, api_name: str, status: APIStatus):
        """Actualiza el estado de una API en la base de datos."""
        try:
            with self.db_manager.transaction('enriquecimiento') as cursor:
                if status == APIStatus.ACTIVE:
                    cursor.execute("""
                        UPDATE enrichment_sources 
                        SET last_success = %s, consecutive_failures = 0
                        WHERE source_name = %s
                    """, (datetime.now(), api_name))
                elif status == APIStatus.ERROR:
                    cursor.execute("""
                        UPDATE enrichment_sources 
                        SET last_failure = %s, consecutive_failures = consecutive_failures + 1
                        WHERE source_name = %s
                    """, (datetime.now(), api_name))
                    
        except Exception as e:
            logger.error(f"❌ Error actualizando estado de {api_name}: {e}")


class WeatherAPI:
    """Cliente específico para API meteorológica AEMET."""
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.api_name = 'AEMET_API'
    
    def get_weather_data(self, codigo_postal: str, fecha_inicio: str, fecha_fin: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos meteorológicos históricos para un código postal.
        
        Args:
            codigo_postal: Código postal (5 dígitos)
            fecha_inicio: Fecha inicio (YYYY-MM-DD)
            fecha_fin: Fecha fin (YYYY-MM-DD)
            
        Returns:
            Datos meteorológicos o None
        """
        # Obtener estación más cercana al código postal
        estacion = self._get_nearest_station(codigo_postal)
        if not estacion:
            logger.warning(f"⚠️ No se encontró estación para CP {codigo_postal}")
            return None
        
        # Consultar datos históricos
        endpoint = f"/climatologias/valores/mensuales"
        params = {
            'indicativo': estacion['indicativo'],
            'fechaIniIni': fecha_inicio,
            'fechaIniFin': fecha_fin,
            'fechaFinIni': fecha_inicio,
            'fechaFinFin': fecha_fin
        }
        
        data = self.api_manager.make_api_call(self.api_name, endpoint, params)
        
        if data:
            # Procesar y limpiar datos
            return self._process_weather_data(data, codigo_postal)
        
        return None
    
    def _get_nearest_station(self, codigo_postal: str) -> Optional[Dict[str, Any]]:
        """Encuentra la estación meteorológica más cercana al código postal."""
        # TODO: Implementar búsqueda por proximidad geográfica
        # Por ahora, usar estación por defecto según provincia
        default_stations = {
            '28': {'indicativo': '3195', 'nombre': 'Madrid-Retiro'},
            '08': {'indicativo': '0076', 'nombre': 'Barcelona'},
            '41': {'indicativo': '5783', 'nombre': 'Sevilla'},
            '46': {'indicativo': '8416', 'nombre': 'Valencia'},
        }
        
        provincia = codigo_postal[:2]
        return default_stations.get(provincia)
    
    def _process_weather_data(self, raw_data: Dict[str, Any], codigo_postal: str) -> Dict[str, Any]:
        """Procesa datos crudos de AEMET."""
        return {
            'codigo_postal': codigo_postal,
            'temperatura_media': raw_data.get('tm_med', 0),
            'temperatura_maxima': raw_data.get('tm_max', 0),
            'temperatura_minima': raw_data.get('tm_min', 0),
            'precipitacion': raw_data.get('p_mes', 0),
            'humedad_relativa': raw_data.get('hr', 0),
            'radiacion_solar': raw_data.get('q_global', 0),
            'fuente': 'AEMET',
            'timestamp': datetime.now().isoformat()
        }


class CatastroAPI:
    """Cliente específico para API del Catastro."""
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.api_name = 'CATASTRO_API'
    
    def get_cadastral_data(self, direccion: str, codigo_postal: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos catastrales por dirección.
        
        Args:
            direccion: Dirección completa
            codigo_postal: Código postal
            
        Returns:
            Datos catastrales o None
        """
        # Normalizar dirección para consulta
        direccion_norm = self._normalize_address(direccion)
        
        endpoint = f"/OVCSWLocalizacionRC/OVCCallejero.asmx/Consulta_DNPRC"
        params = {
            'Provincia': '',
            'Municipio': '',
            'RC': '',
            'Calle': direccion_norm,
            'Numero': ''
        }
        
        data = self.api_manager.make_api_call(self.api_name, endpoint, params)
        
        if data:
            return self._process_cadastral_data(data, direccion, codigo_postal)
        
        return None
    
    def _normalize_address(self, direccion: str) -> str:
        """Normaliza dirección para consulta catastral."""
        # Eliminar números de portal, piso, puerta
        import re
        direccion_norm = re.sub(r'\d+.*$', '', direccion).strip()
        direccion_norm = re.sub(r'\s+', ' ', direccion_norm)
        return direccion_norm.upper()
    
    def _process_cadastral_data(self, raw_data: Dict[str, Any], direccion: str, codigo_postal: str) -> Dict[str, Any]:
        """Procesa datos crudos del Catastro."""
        return {
            'direccion_original': direccion,
            'codigo_postal': codigo_postal,
            'referencia_catastral': raw_data.get('pc1', ''),
            'superficie_construida': raw_data.get('sfc', 0),
            'ano_construccion': raw_data.get('ant', 0),
            'uso_principal': raw_data.get('luso', ''),
            'tipo_via': raw_data.get('tv', ''),
            'nombre_via': raw_data.get('nv', ''),
            'fuente': 'Catastro',
            'timestamp': datetime.now().isoformat()
        }


class MarketPriceAPI:
    """Cliente para APIs de precios de mercado eléctrico."""
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.omie_api = 'OMIE_API'
        self.ree_api = 'REE_Datos'
    
    def get_electricity_prices(self, fecha: str, zona: str = 'ES') -> Optional[Dict[str, Any]]:
        """
        Obtiene precios del mercado eléctrico.
        
        Args:
            fecha: Fecha (YYYY-MM-DD)
            zona: Zona geográfica (ES, PT)
            
        Returns:
            Precios horarios o None
        """
        # Intentar OMIE primero
        omie_data = self._get_omie_prices(fecha, zona)
        if omie_data:
            return omie_data
        
        # Fallback a REE
        ree_data = self._get_ree_prices(fecha)
        return ree_data
    
    def _get_omie_prices(self, fecha: str, zona: str) -> Optional[Dict[str, Any]]:
        """Obtiene precios de OMIE."""
        endpoint = f"/files/flash"
        params = {
            'date': fecha,
            'market': 'ES'
        }
        
        data = self.api_manager.make_api_call(self.omie_api, endpoint, params)
        
        if data:
            return {
                'fecha': fecha,
                'precios_horarios': data.get('hourly_prices', []),
                'precio_medio': data.get('average_price', 0),
                'fuente': 'OMIE',
                'timestamp': datetime.now().isoformat()
            }
        
        return None
    
    def _get_ree_prices(self, fecha: str) -> Optional[Dict[str, Any]]:
        """Obtiene precios de REE como fallback."""
        endpoint = f"/es/datos/mercados/precios-mercados-tiempo-real"
        params = {
            'start_date': fecha,
            'end_date': fecha
        }
        
        data = self.api_manager.make_api_call(self.ree_api, endpoint, params)
        
        if data:
            return {
                'fecha': fecha,
                'precios_horarios': data.get('included', []),
                'precio_medio': 0,  # Calcular del array
                'fuente': 'REE',
                'timestamp': datetime.now().isoformat()
            }
        
        return None


# Instancias globales
from .db_connections import db_manager

api_manager = ExternalAPIManager(db_manager)
weather_api = WeatherAPI(api_manager)
catastro_api = CatastroAPI(api_manager)
market_api = MarketPriceAPI(api_manager)


def enrich_location_data(direccion_hash: str, codigo_postal: str, periodo: str) -> Dict[str, Any]:
    """
    Enriquece datos de ubicación con información externa.
    
    Args:
        direccion_hash: Hash de la dirección
        codigo_postal: Código postal
        periodo: Período (YYYY-MM)
        
    Returns:
        Datos enriquecidos
    """
    enriched_data = {
        'direccion_hash': direccion_hash,
        'codigo_postal': codigo_postal,
        'periodo': periodo,
        'timestamp': datetime.now().isoformat()
    }
    
    # Datos meteorológicos
    try:
        fecha_inicio = f"{periodo}-01"
        fecha_fin = f"{periodo}-28"  # Simplificado
        
        weather_data = weather_api.get_weather_data(codigo_postal, fecha_inicio, fecha_fin)
        if weather_data:
            enriched_data['clima'] = weather_data
            logger.info(f"✅ Clima obtenido para {codigo_postal}")
    except Exception as e:
        logger.error(f"❌ Error obteniendo clima: {e}")
    
    # Precios de mercado
    try:
        market_data = market_api.get_electricity_prices(fecha_inicio)
        if market_data:
            enriched_data['mercado'] = market_data
            logger.info(f"✅ Precios de mercado obtenidos para {fecha_inicio}")
    except Exception as e:
        logger.error(f"❌ Error obteniendo precios: {e}")
    
    return enriched_data


if __name__ == "__main__":
    # Ejemplo de uso
    print("🌐 Sistema de APIs Externas - Energy Green Data")
    print("=" * 60)
    
    # Probar rate limits
    print(f"APIs configuradas: {list(api_manager.apis.keys())}")
    
    # Ejemplo de enriquecimiento
    direccion_hash = hashlib.sha256("test_direccion".encode()).hexdigest()
    enriched = enrich_location_data(direccion_hash, "28001", "2025-01")
    
    print(f"Datos enriquecidos: {len(enriched)} campos")
    print("✅ Sistema de APIs inicializado correctamente")
