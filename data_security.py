"""
Sistema de seguridad y protección de datos personales.
Implementa hashing, versionado y separación de datos sensibles.
"""
import os
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Jerarquía de fuentes de datos por prioridad."""
    FACTURA = 1      # Más confiable
    CUESTIONARIO = 2 # Validado por cliente
    ENRIQUECIMIENTO = 3  # APIs externas
    ESTIMACION = 4   # Menos confiable


@dataclass
class DataVersion:
    """Información de versión de datos de cliente."""
    version_id: str
    source_priority: DataSource
    enrichment_timestamp: Optional[datetime]
    data_quality_score: float
    created_at: datetime
    updated_at: datetime
    changes_summary: Dict[str, Any]


class DataHasher:
    """
    Genera hashes seguros para anonimización de datos personales.
    Usa salts únicos por tipo de dato para evitar rainbow tables.
    """
    
    def __init__(self):
        # Cargar salts desde variables de entorno
        self.direccion_salt = os.getenv('HASH_SALT_DIRECCION', self._generate_salt())
        self.cups_salt = os.getenv('HASH_SALT_CUPS', self._generate_salt())
        self.client_salt = os.getenv('HASH_SALT_CLIENT', self._generate_salt())
        
        # Advertir si se usan salts por defecto
        if not os.getenv('HASH_SALT_DIRECCION'):
            logger.warning("⚠️ Usando salt por defecto para direcciones - Configurar HASH_SALT_DIRECCION")
    
    def _generate_salt(self) -> str:
        """Genera un salt aleatorio de 256 bits."""
        return hashlib.sha256(uuid.uuid4().bytes + datetime.now().isoformat().encode()).hexdigest()
    
    def hash_direccion(self, direccion_completa: str, codigo_postal: str) -> str:
        """
        Genera hash de dirección para enriquecimiento anónimo.
        
        Args:
            direccion_completa: Dirección completa del cliente
            codigo_postal: Código postal
            
        Returns:
            Hash SHA256 de 64 caracteres
        """
        data = f"{direccion_completa.lower().strip()}|{codigo_postal}|{self.direccion_salt}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def hash_cups(self, cups: str, fecha_vinculacion: str) -> str:
        """
        Genera hash de CUPS para identificación anónima.
        
        Args:
            cups: Código Universal de Punto de Suministro
            fecha_vinculacion: Fecha de vinculación cliente-CUPS
            
        Returns:
            Hash SHA256 de 64 caracteres
        """
        data = f"{cups.upper().strip()}|{fecha_vinculacion}|{self.cups_salt}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def hash_client(self, nif_cif: str, nombre_fiscal: str) -> str:
        """
        Genera hash de cliente para identificación interna.
        
        Args:
            nif_cif: NIF o CIF del cliente
            nombre_fiscal: Nombre fiscal del cliente
            
        Returns:
            Hash SHA256 de 64 caracteres
        """
        data = f"{nif_cif.upper().strip()}|{nombre_fiscal.lower().strip()}|{self.client_salt}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()


class DataVersionManager:
    """
    Gestiona el versionado completo de datos de cliente en db_N1.
    Mantiene histórico de cambios y fuentes de información.
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.hasher = DataHasher()
    
    def create_version(self, client_data: Dict[str, Any], source: DataSource) -> str:
        """
        Crea nueva versión de datos de cliente.
        
        Args:
            client_data: Datos del cliente
            source: Fuente de los datos
            
        Returns:
            version_id generado
        """
        version_id = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}_{source.name.lower()}"
        
        # Calcular score de calidad basado en completitud
        quality_score = self._calculate_quality_score(client_data)
        
        version = DataVersion(
            version_id=version_id,
            source_priority=source,
            enrichment_timestamp=datetime.now() if source == DataSource.ENRIQUECIMIENTO else None,
            data_quality_score=quality_score,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            changes_summary=self._detect_changes(client_data)
        )
        
        # Guardar versión en db_N1
        self._save_version_to_db(version, client_data)
        
        logger.info(f"✅ Nueva versión creada: {version_id} (calidad: {quality_score:.1f}%)")
        return version_id
    
    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """Calcula score de calidad basado en campos críticos completos."""
        critical_fields = [
            'cups', 'nif_cif', 'nombre_fiscal', 'direccion_suministro',
            'codigo_postal', 'tarifa', 'potencia_contratada'
        ]
        
        completed = sum(1 for field in critical_fields if data.get(field))
        return (completed / len(critical_fields)) * 100
    
    def _detect_changes(self, new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detecta cambios respecto a la versión anterior."""
        # TODO: Implementar comparación con versión anterior
        return {"new_fields": len(new_data), "timestamp": datetime.now().isoformat()}
    
    def _save_version_to_db(self, version: DataVersion, data: Dict[str, Any]):
        """Guarda versión en la tabla de versionado de db_N1."""
        with self.db_manager.transaction('N1') as cursor:
            cursor.execute("""
                INSERT INTO client_versions (
                    version_id, client_hash, source_priority, enrichment_timestamp,
                    data_quality_score, created_at, updated_at, changes_summary
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                version.version_id,
                self.hasher.hash_client(data.get('nif_cif', ''), data.get('nombre_fiscal', '')),
                version.source_priority.value,
                version.enrichment_timestamp,
                version.data_quality_score,
                version.created_at,
                version.updated_at,
                json.dumps(version.changes_summary)
            ))


class EnrichmentQueue:
    """
    Gestiona la cola de enriquecimiento asíncrono de datos.
    Procesa solicitudes de APIs externas sin bloquear el pipeline principal.
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.hasher = DataHasher()
    
    def enqueue_enrichment(self, client_data: Dict[str, Any], priority: str = 'medium') -> bool:
        """
        Añade solicitud de enriquecimiento a la cola.
        
        Args:
            client_data: Datos del cliente
            priority: Prioridad (high, medium, low)
            
        Returns:
            True si se añadió correctamente
        """
        direccion_hash = self.hasher.hash_direccion(
            client_data.get('direccion_suministro', ''),
            client_data.get('codigo_postal', '')
        )
        
        cups_hash = self.hasher.hash_cups(
            client_data.get('cups', ''),
            client_data.get('fecha_vinculacion', datetime.now().strftime('%Y-%m-%d'))
        )
        
        try:
            with self.db_manager.transaction('enriquecimiento') as cursor:
                cursor.execute("""
                    INSERT INTO enrichment_queue (
                        cups_hash, direccion_hash, provincia, codigo_postal,
                        tarifa, periodo_mes, priority, status, requested_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (cups_hash, direccion_hash, periodo_mes) DO NOTHING
                """, (
                    cups_hash,
                    direccion_hash,
                    client_data.get('provincia', ''),
                    client_data.get('codigo_postal', ''),
                    client_data.get('tarifa', ''),
                    datetime.now().strftime('%Y-%m'),
                    priority,
                    'pending',
                    datetime.now()
                ))
            
            logger.info(f"📋 Enriquecimiento encolado: {direccion_hash[:8]}... (prioridad: {priority})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error encolando enriquecimiento: {e}")
            return False
    
    def process_queue(self, max_items: int = 10) -> int:
        """
        Procesa elementos de la cola de enriquecimiento.
        
        Args:
            max_items: Máximo número de elementos a procesar
            
        Returns:
            Número de elementos procesados
        """
        processed = 0
        
        try:
            with self.db_manager.transaction('enriquecimiento') as cursor:
                # Obtener elementos pendientes por prioridad
                cursor.execute("""
                    SELECT id, cups_hash, direccion_hash, provincia, codigo_postal
                    FROM enrichment_queue 
                    WHERE status = 'pending' 
                    ORDER BY 
                        CASE priority 
                            WHEN 'high' THEN 1 
                            WHEN 'medium' THEN 2 
                            WHEN 'low' THEN 3 
                        END,
                        requested_at ASC
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                """, (max_items,))
                
                items = cursor.fetchall()
                
                for item in items:
                    if self._process_enrichment_item(item):
                        processed += 1
                        
                        # Marcar como completado
                        cursor.execute("""
                            UPDATE enrichment_queue 
                            SET status = 'completed', completed_at = %s
                            WHERE id = %s
                        """, (datetime.now(), item['id']))
        
        except Exception as e:
            logger.error(f"❌ Error procesando cola de enriquecimiento: {e}")
        
        logger.info(f"✅ Procesados {processed} elementos de enriquecimiento")
        return processed
    
    def _process_enrichment_item(self, item: Dict[str, Any]) -> bool:
        """Procesa un elemento individual de enriquecimiento."""
        try:
            # TODO: Implementar llamadas a APIs externas
            # - AEMET para datos climáticos
            # - Catastro para características del inmueble
            # - OMIE para precios de mercado
            
            # Por ahora, simular procesamiento exitoso
            logger.info(f"🔄 Procesando: {item['direccion_hash'][:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error procesando item {item['id']}: {e}")
            return False


class TTLManager:
    """
    Gestiona la limpieza automática de datos temporales con TTL.
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def cleanup_expired_data(self):
        """Limpia datos expirados de todas las bases temporales."""
        cleanup_tasks = [
            ('N0', 'documents', 30),  # 30 días
            ('enriquecimiento', 'enrichment_cache', 90),  # 90 días
            ('clima', 'weather_cache', 30),  # 30 días
            ('encuesta', 'questionnaire_sessions', 365),  # 1 año
        ]
        
        for db_name, table, days in cleanup_tasks:
            try:
                deleted = self._cleanup_table(db_name, table, days)
                logger.info(f"🗑️ {db_name}.{table}: {deleted} registros eliminados (TTL: {days} días)")
            except Exception as e:
                logger.error(f"❌ Error limpiando {db_name}.{table}: {e}")
    
    def _cleanup_table(self, db_name: str, table: str, ttl_days: int) -> int:
        """Limpia registros expirados de una tabla específica."""
        cutoff_date = datetime.now() - timedelta(days=ttl_days)
        
        with self.db_manager.transaction(db_name) as cursor:
            cursor.execute(f"""
                DELETE FROM {table} 
                WHERE created_at < %s
            """, (cutoff_date,))
            
            return cursor.rowcount


class AuditLogger:
    """
    Sistema de auditoría y trazabilidad para operaciones sensibles.
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def log_data_access(self, user: str, operation: str, table: str, 
                       client_hash: Optional[str] = None, details: Dict[str, Any] = None):
        """
        Registra acceso a datos personales para auditoría.
        
        Args:
            user: Usuario que realiza la operación
            operation: Tipo de operación (SELECT, INSERT, UPDATE, DELETE)
            table: Tabla accedida
            client_hash: Hash del cliente (si aplica)
            details: Detalles adicionales
        """
        try:
            # TODO: Crear tabla de auditoría si no existe
            audit_record = {
                'timestamp': datetime.now().isoformat(),
                'user': user,
                'operation': operation,
                'table': table,
                'client_hash': client_hash,
                'details': details or {}
            }
            
            logger.info(f"📋 AUDIT: {user} - {operation} on {table}")
            # TODO: Guardar en tabla de auditoría
            
        except Exception as e:
            logger.error(f"❌ Error registrando auditoría: {e}")


# Instancia global para uso en toda la aplicación
from db_connections import db_manager

data_hasher = DataHasher()
version_manager = DataVersionManager(db_manager)
enrichment_queue = EnrichmentQueue(db_manager)
ttl_manager = TTLManager(db_manager)
audit_logger = AuditLogger(db_manager)


# Funciones de conveniencia
def hash_client_data(nif_cif: str, nombre_fiscal: str) -> str:
    """Hash de cliente para identificación segura."""
    return data_hasher.hash_client(nif_cif, nombre_fiscal)


def hash_direccion_data(direccion: str, codigo_postal: str) -> str:
    """Hash de dirección para enriquecimiento anónimo."""
    return data_hasher.hash_direccion(direccion, codigo_postal)


def create_data_version(client_data: Dict[str, Any], source: DataSource) -> str:
    """Crea nueva versión de datos de cliente."""
    return version_manager.create_version(client_data, source)


def enqueue_data_enrichment(client_data: Dict[str, Any], priority: str = 'medium') -> bool:
    """Encola solicitud de enriquecimiento asíncrono."""
    return enrichment_queue.enqueue_enrichment(client_data, priority)


if __name__ == "__main__":
    # Ejemplo de uso
    print("🔒 Sistema de Seguridad de Datos - Energy Green Data")
    print("=" * 60)
    
    # Datos de ejemplo (NO REALES)
    ejemplo_cliente = {
        'nif_cif': '12345678A',
        'nombre_fiscal': 'Empresa Ejemplo SL',
        'direccion_suministro': 'Calle Mayor 123, 3º A',
        'codigo_postal': '28001',
        'cups': 'ES0022000008342444ND1P',
        'tarifa': '2.0TD',
        'potencia_contratada': 4.6
    }
    
    # Generar hashes
    client_hash = hash_client_data(ejemplo_cliente['nif_cif'], ejemplo_cliente['nombre_fiscal'])
    direccion_hash = hash_direccion_data(ejemplo_cliente['direccion_suministro'], ejemplo_cliente['codigo_postal'])
    
    print(f"Cliente hash: {client_hash[:16]}...")
    print(f"Dirección hash: {direccion_hash[:16]}...")
    
    # Crear versión
    version_id = create_data_version(ejemplo_cliente, DataSource.FACTURA)
    print(f"Versión creada: {version_id}")
    
    # Encolar enriquecimiento
    enqueued = enqueue_data_enrichment(ejemplo_cliente, 'high')
    print(f"Enriquecimiento encolado: {enqueued}")
    
    print("\n✅ Sistema de seguridad inicializado correctamente")
