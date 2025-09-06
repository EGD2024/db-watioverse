"""
Gestor centralizado de conexiones a todas las bases de datos del sistema.
Usa variables de entorno desde .env para proteger credenciales.
"""
import os
import psycopg2
import psycopg2.extras
from psycopg2 import pool
from typing import Dict, Optional, Any, List
from contextlib import contextmanager
from pathlib import Path
import threading
import logging
from dotenv import load_dotenv

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info(f'Variables de entorno cargadas desde: {env_path}')
else:
    logger.warning(f'Archivo .env no encontrado en {env_path}')


class DatabaseManager:
    """
    Gestor singleton de conexiones a todas las bases de datos del sistema.
    Usa nombres reales de bases de datos sin equivalencias ni fallbacks.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Implementación singleton thread-safe."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Inicializa las configuraciones de conexión."""
        if self._initialized:
            return

        self.connection_pools = {}
        self._initialized = True
        
        # Configuración base desde .env
        self.base_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'admin')
        }
        
        # Configuración de TODAS las bases de datos del sistema
        self.db_configs = {
            # Pipeline de datos N0→N1→N2
            'N0': {**self.base_config, 'database': f"db_{os.getenv('DB_N0', 'N0')}"},
            'N1': {**self.base_config, 'database': f"db_{os.getenv('DB_N1', 'N1')}"},
            'N2': {**self.base_config, 'database': f"db_{os.getenv('DB_N2', 'N2')}"},
            'N3': {**self.base_config, 'database': f"db_{os.getenv('DB_N3', 'N3')}"},
            'N4': {**self.base_config, 'database': f"db_{os.getenv('DB_N4', 'N4')}"},
            'N5': {**self.base_config, 'database': f"db_{os.getenv('DB_N5', 'N5')}"},
            
            # Datos maestros
            'usuario': {**self.base_config, 'database': f"db_{os.getenv('DB_USUARIO', 'usuario')}"},
            'cliente': {**self.base_config, 'database': f"db_{os.getenv('DB_CLIENTE', 'cliente')}"},
            'distribuidora': {**self.base_config, 'database': f"db_{os.getenv('DB_DISTRIBUIDORA', 'distribuidora')}"},
            'comercializadora': {**self.base_config, 'database': f"db_{os.getenv('DB_COMERCIALIZADORA', 'comercializadora')}"},
            'instalaciones': {**self.base_config, 'database': f"db_{os.getenv('DB_INSTALACIONES', 'instalaciones')}"},
            
            # Sistemas y territorio
            'sistema_electrico': {**self.base_config, 'database': f"db_{os.getenv('DB_SISTEMA_ELECTRICO', 'sistema_electrico')}"},
            'sistema_gas': {**self.base_config, 'database': f"db_{os.getenv('DB_SISTEMA_GAS', 'sistema_gas')}"},
            'territorio': {**self.base_config, 'database': f"db_{os.getenv('DB_TERRITORIO', 'territorio')}"},
            'calendario': {**self.base_config, 'database': f"db_{os.getenv('DB_CALENDARIO', 'calendario')}"},
            
            # Enriquecimiento externo
            'clima': {**self.base_config, 'database': f"db_{os.getenv('DB_CLIMA', 'clima')}"},
            'encuesta': {**self.base_config, 'database': f"db_{os.getenv('DB_ENCUESTA', 'encuesta')}"},
            'enriquecimiento': {**self.base_config, 'database': f"db_{os.getenv('DB_ENRIQUECIMIENTO', 'enriquecimiento')}"},
            'catastro': {**self.base_config, 'database': f"db_{os.getenv('DB_CATASTRO', 'catastro')}"},
            
            # Motor eSCORE - NOMBRES REALES SIN EQUIVALENCIAS
            'eSCORE_pesos': {**self.base_config, 'database': f"db_{os.getenv('DB_ESCORE_PESOS', 'eSCORE_pesos')}"},
            'eSCORE_contx': {**self.base_config, 'database': f"db_{os.getenv('DB_ESCORE_CONTX', 'eSCORE_contx')}"},
            'eSCORE_def': {**self.base_config, 'database': f"db_{os.getenv('DB_ESCORE_DEF', 'eSCORE_def')}"},
            'eSCORE_master': {**self.base_config, 'database': f"db_{os.getenv('DB_ESCORE_MASTER', 'eSCORE_master')}"},
            'eSCORE_watiodat': {**self.base_config, 'database': f"db_{os.getenv('DB_ESCORE_WATIODAT', 'eSCORE_watiodat')}"},
            
            # Otros sistemas
            'simulador': {**self.base_config, 'database': f"db_{os.getenv('DB_SIMULADOR', 'simulador')}"},
            'rag': {**self.base_config, 'database': f"db_{os.getenv('DB_RAG', 'rag')}"},
            'memoria': {**self.base_config, 'database': f"db_{os.getenv('DB_MEMORIA', 'memoria')}"},
            'preferencias': {**self.base_config, 'database': f"db_{os.getenv('DB_PREFERENCIAS', 'preferencias')}"},
        }
        
        self._init_connection_pools()

    def _init_connection_pools(self):
        """
        Inicializa pools de conexiones para cada base de datos.
        NO hay fallback - si falla una conexión crítica, lanza excepción.
        """
        # Bases de datos críticas que DEBEN existir
        critical_dbs = ['N0', 'N1', 'eSCORE_pesos', 'eSCORE_def', 'eSCORE_master', 
                       'eSCORE_contx', 'eSCORE_watiodat']
        
        for db_name, config in self.db_configs.items():
            try:
                # Tamaño del pool según tipo de BD
                if 'eSCORE' in db_name:
                    min_conn, max_conn = 1, 50  # eSCORE: consultas frecuentes
                elif db_name in ['N0', 'N1', 'N2']:
                    min_conn, max_conn = 2, 100  # Pipeline: alta carga
                else:
                    min_conn, max_conn = 1, 20  # Auxiliares: baja carga
                
                self.connection_pools[db_name] = psycopg2.pool.ThreadedConnectionPool(
                    minconn=min_conn,
                    maxconn=max_conn,
                    **config
                )
                logger.info(f"✅ Pool creado para '{db_name}' ({min_conn}-{max_conn} conexiones)")
                
            except psycopg2.Error as e:
                if db_name in critical_dbs:
                    # Base de datos crítica - NO hay fallback
                    error_msg = f"❌ ERROR CRÍTICO: No se pudo conectar a '{db_name}': {e}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                else:
                    # Base de datos no crítica - solo warning
                    logger.warning(f"⚠️ No se pudo conectar a '{db_name}' (no crítica): {e}")
                    self.connection_pools[db_name] = None

    def get_connection(self, db_name: str) -> psycopg2.extensions.connection:
        """
        Obtiene una conexión del pool de la base de datos especificada.
        
        Args:
            db_name: Nombre de la base de datos (ver lista en db_configs)
            
        Returns:
            Conexión PostgreSQL del pool
            
        Raises:
            KeyError: Si el nombre de DB no es válido
            RuntimeError: Si no hay conexión disponible (NO HAY FALLBACK)
        """
        if db_name not in self.db_configs:
            raise KeyError(f"Base de datos '{db_name}' no configurada. Disponibles: {list(self.db_configs.keys())}")
        
        if db_name not in self.connection_pools or self.connection_pools[db_name] is None:
            raise RuntimeError(f"Pool de conexiones no disponible para '{db_name}' - NO HAY FALLBACK")
        
        try:
            conn = self.connection_pools[db_name].getconn()
            if conn:
                logger.debug(f"Conexión obtenida del pool '{db_name}'")
                return conn
            else:
                raise RuntimeError(f"No hay conexiones disponibles en el pool de '{db_name}'")
        except Exception as e:
            logger.error(f"Error obteniendo conexión del pool '{db_name}': {e}")
            raise

    def return_connection(self, db_name: str, conn: psycopg2.extensions.connection):
        """Devuelve una conexión al pool."""
        if db_name in self.connection_pools and self.connection_pools[db_name]:
            try:
                self.connection_pools[db_name].putconn(conn)
                logger.debug(f"Conexión devuelta al pool '{db_name}'")
            except Exception as e:
                logger.error(f"Error al devolver conexión al pool '{db_name}': {e}")
                if conn:
                    conn.close()

    @contextmanager
    def transaction(self, db_name: str):
        """
        Context manager para manejo de transacciones.
        
        Args:
            db_name: Nombre de la base de datos
            
        Yields:
            cursor: Cursor de la base de datos
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection(db_name)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            yield cursor
            conn.commit()
            logger.debug(f"Transacción confirmada en '{db_name}'")
        except Exception as e:
            if conn:
                conn.rollback()
                logger.error(f"Rollback ejecutado en '{db_name}' debido a: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.return_connection(db_name, conn)

    def query(self, db_name: str, sql: str, params: Optional[tuple] = None) -> List[Dict]:
        """
        Ejecuta una consulta SELECT y devuelve los resultados.
        
        Args:
            db_name: Nombre de la base de datos
            sql: Consulta SQL
            params: Parámetros opcionales
            
        Returns:
            Lista de diccionarios con los resultados
        """
        with self.transaction(db_name) as cursor:
            cursor.execute(sql, params)
            results = cursor.fetchall()
            logger.debug(f"Consulta en '{db_name}': {len(results)} filas")
            return results

    def execute(self, db_name: str, sql: str, params: Optional[tuple] = None) -> int:
        """
        Ejecuta una consulta INSERT/UPDATE/DELETE.
        
        Args:
            db_name: Nombre de la base de datos
            sql: Consulta SQL
            params: Parámetros opcionales
            
        Returns:
            Número de filas afectadas
        """
        with self.transaction(db_name) as cursor:
            cursor.execute(sql, params)
            affected = cursor.rowcount
            logger.debug(f"Ejecución en '{db_name}': {affected} filas afectadas")
            return affected

    def test_connections(self) -> Dict[str, bool]:
        """
        Prueba todas las conexiones configuradas.
        
        Returns:
            Diccionario con el estado de cada conexión
        """
        results = {}
        for db_name in self.db_configs.keys():
            try:
                with self.transaction(db_name) as cursor:
                    cursor.execute('SELECT 1')
                    result = cursor.fetchone()
                    results[db_name] = result is not None
                logger.info(f"Conexión a '{db_name}': ✅ OK")
            except Exception as e:
                results[db_name] = False
                logger.error(f"Conexión a '{db_name}': ❌ FALLO - {e}")
        
        # Resumen
        total = len(results)
        success = sum(1 for v in results.values() if v)
        logger.info(f"\n{'='*50}")
        logger.info(f"RESUMEN: {success}/{total} conexiones exitosas")
        logger.info(f"{'='*50}\n")
        
        return results

    def get_pool_status(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene el estado de todos los pools de conexiones."""
        status = {}
        for db_name, pool in self.connection_pools.items():
            if pool:
                status[db_name] = {
                    'activo': not pool.closed,
                    'conexiones_min': pool.minconn,
                    'conexiones_max': pool.maxconn
                }
            else:
                status[db_name] = {'error': 'Pool no disponible'}
        return status

    def close_all(self):
        """Cierra todos los pools de conexiones."""
        for db_name, pool in self.connection_pools.items():
            try:
                if pool and not pool.closed:
                    pool.closeall()
                    logger.info(f"Pool cerrado: '{db_name}'")
            except Exception as e:
                logger.error(f"Error cerrando pool '{db_name}': {e}")
        self.connection_pools.clear()
        logger.info("Todos los pools cerrados")

    def __del__(self):
        """Destructor para cerrar pools."""
        self.close_all()


# Instancia singleton global
db_manager = DatabaseManager()


# Funciones de conveniencia para acceso rápido
def get_connection(db_name: str):
    """Obtiene una conexión a la base de datos especificada."""
    return db_manager.get_connection(db_name)


def query(db_name: str, sql: str, params=None):
    """Ejecuta una consulta SELECT."""
    return db_manager.query(db_name, sql, params)


def execute(db_name: str, sql: str, params=None):
    """Ejecuta una consulta INSERT/UPDATE/DELETE."""
    return db_manager.execute(db_name, sql, params)


def test_all_connections():
    """Prueba todas las conexiones configuradas."""
    return db_manager.test_connections()


# Script de prueba si se ejecuta directamente
if __name__ == "__main__":
    print("=" * 60)
    print("PRUEBA DE CONEXIONES A BASES DE DATOS")
    print("=" * 60)
    
    # Probar todas las conexiones
    results = test_all_connections()
    
    # Mostrar estado de pools
    print("\n" + "=" * 60)
    print("ESTADO DE POOLS DE CONEXIONES")
    print("=" * 60)
    pool_status = db_manager.get_pool_status()
    for db_name, status in pool_status.items():
        if 'error' in status:
            print(f"❌ {db_name}: {status['error']}")
        else:
            print(f"✅ {db_name}: {status}")
    
    # Ejemplo de uso
    print("\n" + "=" * 60)
    print("EJEMPLO DE USO")
    print("=" * 60)
    
    # Consulta a N0
    try:
        result = query('N0', 'SELECT COUNT(*) as total FROM documents')
        print(f"Documentos en N0: {result[0]['total'] if result else 0}")
    except Exception as e:
        print(f"Error consultando N0: {e}")
    
    # Consulta a eSCORE_pesos
    try:
        result = query('eSCORE_pesos', 'SELECT COUNT(*) as total FROM information_schema.tables')
        print(f"Tablas en eSCORE_pesos: {result[0]['total'] if result else 0}")
    except Exception as e:
        print(f"Error consultando eSCORE_pesos: {e}")
    
    print("\n" + "=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)
