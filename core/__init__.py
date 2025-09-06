"""
Módulo core de db_watioverse - Infraestructura central del sistema.

Contiene:
- db_connections: Gestor centralizado de conexiones a todas las BDs
- data_security: Sistema de hashing, versionado y protección de datos
- external_apis: Cliente para APIs externas con rate limiting
"""

from .db_connections import DatabaseManager, db_manager
from .data_security import (
    DataHasher, DataVersionManager, EnrichmentQueue, TTLManager, AuditLogger,
    data_hasher, version_manager, enrichment_queue, ttl_manager, audit_logger
)
from .external_apis import (
    ExternalAPIManager, WeatherAPI, CatastroAPI, MarketPriceAPI,
    api_manager, weather_api, catastro_api, market_api
)

__all__ = [
    # Gestores principales
    'DatabaseManager', 'db_manager',
    'DataHasher', 'DataVersionManager', 'EnrichmentQueue', 'TTLManager', 'AuditLogger',
    'ExternalAPIManager', 'WeatherAPI', 'CatastroAPI', 'MarketPriceAPI',
    
    # Instancias globales
    'data_hasher', 'version_manager', 'enrichment_queue', 'ttl_manager', 'audit_logger',
    'api_manager', 'weather_api', 'catastro_api', 'market_api'
]
