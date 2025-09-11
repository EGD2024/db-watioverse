#!/usr/bin/env python3
# ==========================================
# MIGRADO AL SISTEMA CENTRALIZADO
# ==========================================
# Este script ha sido migrado al Motor de Actualizaciones Centralizado
# Nuevo sistema: /motores/motor_actualizaciones/
# Scheduler unificado: core/unified_scheduler.py
# Configuración: config/master_config.yaml
# 
# Para ejecutar: python master_main.py --category watioverse
# Para scheduling: python core/unified_scheduler.py
# ==========================================
# -*- coding: utf-8 -*-
"""
Monitor Automático N0
Monitorea la carpeta Data_out y dispara inserción automática cuando detecta nuevos archivos N0.
"""

import json
import time
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor_n0_auto.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Importar el procesador completo N0→N1
shared_path = Path(__file__).parent.parent / 'shared'
sys.path.insert(0, str(shared_path))
try:
    from n0_to_n1_processor import N0ToN1Processor
    PROCESSOR_DISPONIBLE = True
    logger.info("✅ Procesador completo N0→N1 disponible")
except ImportError as e:
    PROCESSOR_DISPONIBLE = False
    logger.error(f"❌ Procesador N0→N1 no disponible: {e}")
    
    # Fallback a insertador N0 solo
    from insert_N0 import N0Inserter

class N0FileHandler(FileSystemEventHandler):
    """Manejador de eventos para archivos N0."""
    
    def __init__(self, modo_prueba: bool = True):
        super().__init__()
        self.modo_prueba = modo_prueba
        self.archivos_procesados: Set[str] = set()
        self.cooldown_segundos = 5  # Evitar procesamiento múltiple
        self.ultimo_procesamiento: Dict[str, float] = {}
        
        # Configurar procesador completo N0→N1
        if PROCESSOR_DISPONIBLE:
            self.processor = N0ToN1Processor(modo_prueba=modo_prueba)
            self.pipeline_completo_activo = True
            logger.info("🚀 Procesador completo N0→N1 configurado")
        else:
            # Fallback a insertador N0 solo
            self.inserter = N0Inserter(modo_prueba=modo_prueba)
            self.pipeline_completo_activo = False
            logger.warning("⚠️ Usando solo insertador N0 (sin pipeline N1)")
        
        # Configurar directorio de monitoreo
        if PROCESSOR_DISPONIBLE:
            self.directorio_data = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out"
        else:
            self.directorio_data = self.inserter.directorio_data
        
        # Cargar archivos ya existentes para evitar reprocesamiento
        self._cargar_archivos_existentes()
        
        logger.info(f"🔍 Monitor N0 iniciado - MODO {'PRUEBA' if modo_prueba else 'PRODUCCIÓN'}")
        if self.pipeline_completo_activo:
            logger.info("🚀 Pipeline automático N0→BD N0→N1→BD N1 ACTIVADO")
        else:
            logger.info("📊 Solo insertador N0 disponible")
    
    def _cargar_archivos_existentes(self):
        """Carga archivos N0 existentes para evitar reprocesarlos."""
        data_path = Path(self.directorio_data)
        archivos_existentes = list(data_path.glob("N0_*.json"))
        
        for archivo in archivos_existentes:
            self.archivos_procesados.add(archivo.name)
        
        logger.info(f"📋 Archivos N0 existentes registrados: {len(archivos_existentes)}")
    
    def _es_archivo_n0(self, archivo_path: str) -> bool:
        """Verifica si es un archivo N0 válido."""
        nombre = os.path.basename(archivo_path)
        return (
            nombre.endswith('.json') and 
            nombre.startswith('N0_') and
            not nombre.startswith('.') and
            '_TEMP_' not in nombre and  # IGNORAR archivos temporales
            '_CLEAN' not in nombre and  # IGNORAR archivos N1 limpios
            os.path.getsize(archivo_path) > 100  # Mínimo 100 bytes
        )
    
    def _debe_procesar_archivo(self, archivo_path: str) -> bool:
        """Determina si debe procesar el archivo."""
        archivo_name = Path(archivo_path).name
        
        # Ya fue procesado
        if archivo_name in self.archivos_procesados:
            return False
        
        # Cooldown para evitar procesamiento múltiple
        ahora = time.time()
        if archivo_name in self.ultimo_procesamiento:
            tiempo_transcurrido = ahora - self.ultimo_procesamiento[archivo_name]
            if tiempo_transcurrido < self.cooldown_segundos:
                return False
        
        return True
    
    def _procesar_archivo(self, archivo_path: str):
        """Procesa un archivo N0 detectado."""
        archivo_name = Path(archivo_path).name
        
        try:
            logger.info(f" Procesando archivo: {archivo_name}")
            
            if self.pipeline_completo_activo:
                # Usar procesador completo N0→N1
                resultado = self.processor.process_n0_file(
                    archivo_path, 
                    enable_n0_insert=True, 
                    enable_n1_insert=True
                )
                
                if resultado['success']:
                    logger.info(f" Pipeline completo exitoso: {archivo_name}")
                    logger.info(f"   N0: {resultado['stats'].get('n0_inserted_records', 0)} registros")
                    logger.info(f"   N1: {resultado['stats'].get('n1_inserted_records', 0)} registros")
                    
                    # Marcar como procesado
                    self.archivos_procesados.add(archivo_name)
                    
                    # Generar notificación de éxito completo
                    self._generar_notificacion_pipeline_exito(resultado)
                    
                else:
                    logger.error(f" Error en pipeline completo {archivo_name}:")
                    logger.error(f"   • {resultado.get('error', 'Error desconocido')}")
                    
                    # Generar notificación de error
                    self._generar_notificacion_pipeline_error(resultado)
            
            else:
                # Fallback: usar solo insertador N0
                resultado = self.inserter.procesar_archivo(Path(archivo_path))
                
                if resultado.exito:
                    logger.info(f" Procesamiento N0 exitoso: {archivo_name}")
                    logger.info(f"   {resultado.registros_insertados} tablas insertadas")
                    logger.info(f"   Tiempo: {resultado.tiempo_procesamiento:.2f}s")
                    
                    # Marcar como procesado
                    self.archivos_procesados.add(archivo_name)
                    
                    # Generar notificación
                    self._generar_notificacion_exito(resultado)
                    
                else:
                    logger.error(f" Error procesando {archivo_name}:")
                    for error in resultado.errores:
                        logger.error(f"   • {error}")
                    
                    # Generar notificación de error
                    self._generar_notificacion_error(resultado)
            
        except Exception as e:
            logger.error(f" Error crítico procesando {archivo_name}: {e}")
    
    def _generar_notificacion_pipeline_exito(self, resultado):
        """Genera notificación de pipeline completo exitoso."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        notificacion = {
            'timestamp': timestamp,
            'archivo': Path(resultado['file_path']).name,
            'estado': 'PIPELINE_COMPLETO_EXITO',
            'n0_insertado': resultado.get('n0_insert_success', False),
            'n1_insertado': resultado.get('n1_insert_success', False),
            'stats': resultado.get('stats', {}),
            'modo': 'PRUEBA' if self.modo_prueba else 'PRODUCCION'
        }
        
        # Guardar notificación en directorio errors
        directorio_errors = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out/errors"
        archivo_notif = f"{directorio_errors}/notificacion_pipeline_exito_{timestamp}.json"
        with open(archivo_notif, 'w', encoding='utf-8') as f:
            json.dump(notificacion, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Notificación pipeline guardada: {archivo_notif}")
    
    def _generar_notificacion_pipeline_error(self, resultado):
        """Genera notificación de error en pipeline completo."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        notificacion = {
            'timestamp': timestamp,
            'archivo': Path(resultado['file_path']).name,
            'estado': 'PIPELINE_COMPLETO_ERROR',
            'n0_insertado': resultado.get('n0_insert_success', False),
            'n1_insertado': resultado.get('n1_insert_success', False),
            'error': resultado.get('error', 'Error desconocido'),
            'stats': resultado.get('stats', {}),
            'modo': 'PRUEBA' if self.modo_prueba else 'PRODUCCION'
        }
        
        # Guardar notificación en directorio errors
        directorio_errors = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out/errors"
        archivo_notif = f"{directorio_errors}/notificacion_pipeline_error_{timestamp}.json"
        with open(archivo_notif, 'w', encoding='utf-8') as f:
            json.dump(notificacion, f, indent=2, ensure_ascii=False)
        
        logger.error(f"📄 Notificación error guardada: {archivo_notif}")
    
    def _disparar_insercion_n1(self, archivo_n1_path: str):
        """Dispara inserción automática del archivo N1 generado."""
        try:
            # Importar insertador N1
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'N1'))
            from insert_N1 import N1Inserter
            
            # Crear insertador N1 en el mismo modo que N0
            inserter_n1 = N1Inserter(modo_prueba=self.modo_prueba)
            
            # Procesar archivo N1
            resultado_insercion = inserter_n1.procesar_archivo(Path(archivo_n1_path))
            
            if resultado_insercion.exito:
                logger.info(f"✅ Inserción N1 exitosa: {Path(archivo_n1_path).name}")
                logger.info(f"   📊 {resultado_insercion.registros_insertados} tablas insertadas")
            else:
                logger.error(f"❌ Error en inserción N1: {Path(archivo_n1_path).name}")
                for error in resultado_insercion.errores:
                    logger.error(f"   • {error}")
                    
        except ImportError:
            logger.warning("⚠️ Insertador N1 no disponible - archivo N1 generado pero no insertado")
        except Exception as e:
            logger.error(f"💥 Error en inserción N1: {e}")
    
    def _generar_notificacion_exito(self, resultado):
        """Genera notificación de procesamiento exitoso."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        notificacion = {
            'timestamp': timestamp,
            'archivo': resultado.archivo,
            'estado': 'EXITO',
            'tablas_insertadas': resultado.registros_insertados,
            'tiempo_procesamiento': resultado.tiempo_procesamiento,
            'modo': 'PRUEBA' if self.modo_prueba else 'PRODUCCION'
        }
        
        # Guardar notificación en directorio errors
        directorio_errors = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out/errors"
        archivo_notif = f"{directorio_errors}/notificacion_n0_exito_{timestamp}.json"
        with open(archivo_notif, 'w', encoding='utf-8') as f:
            json.dump(notificacion, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Notificación guardada: {archivo_notif}")
    
    def _generar_notificacion_error(self, resultado):
        """Genera notificación de error."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        notificacion = {
            'timestamp': timestamp,
            'archivo': resultado.archivo,
            'estado': 'ERROR',
            'errores': resultado.errores,
            'tiempo_procesamiento': resultado.tiempo_procesamiento,
            'modo': 'PRUEBA' if self.modo_prueba else 'PRODUCCION'
        }
        
        # Guardar notificación de error en directorio errors
        directorio_errors = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out/errors"
        archivo_notif = f"{directorio_errors}/notificacion_n0_error_{timestamp}.json"
        with open(archivo_notif, 'w', encoding='utf-8') as f:
            json.dump(notificacion, f, indent=2, ensure_ascii=False)
        
        logger.error(f"📄 Notificación de error guardada: {archivo_notif}")
    
    def on_created(self, event):
        """Evento: archivo creado."""
        if event.is_directory:
            return
        
        archivo_path = event.src_path
        
        # Verificar si es archivo N0 válido
        if not self._es_archivo_n0(archivo_path):
            return
        
        # Verificar si debe procesarse
        if not self._debe_procesar_archivo(archivo_path):
            return
        
        # Esperar un momento para asegurar que el archivo está completo
        time.sleep(1)
        
        # Procesar archivo
        self._procesar_archivo(archivo_path)
    
    def on_moved(self, event):
        """Evento: archivo movido."""
        if event.is_directory:
            return
        
        # Si es un archivo N0 movido, procesarlo
        if event.dest_path.endswith('.json') and 'N0_' in os.path.basename(event.dest_path):
            logger.info(f"📂 Archivo N0 movido: {event.dest_path}")
            self._procesar_nuevo_archivo(event.dest_path)
    
    def generar_reporte_estado(self) -> List[str]:
        """Genera reporte del estado actual del monitor."""
        reporte = []
        reporte.append(f"📊 ESTADO DEL MONITOR N0")
        reporte.append(f"{'='*50}")
        reporte.append(f"⚙️ Modo: {'PRUEBA' if self.modo_prueba else 'PRODUCCIÓN'}")
        reporte.append(f"📁 Directorio monitoreado: {self.directorio_data}")
        reporte.append(f"📋 Archivos procesados: {len(self.archivos_procesados)}")
        
        if self.archivos_procesados:
            reporte.append(f"\n📂 Últimos archivos procesados:")
            for archivo in sorted(list(self.archivos_procesados)[-5:]):
                reporte.append(f"   • {archivo}")
        
        return reporte

class N0Monitor:
    """Monitor principal para archivos N0."""
    
    def __init__(self, modo_prueba: bool = True):
        self.modo_prueba = modo_prueba
        self.directorio_data = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out"
        self.observer = None
        self.handler = None
        self.ejecutando = False
    
    def iniciar(self):
        """Inicia el monitor."""
        logger.info("🚀 INICIANDO MONITOR N0")
        logger.info("=" * 50)
        
        # Verificar que el directorio existe
        if not Path(self.directorio_data).exists():
            logger.error(f"❌ Directorio no existe: {self.directorio_data}")
            return False
        
        # Crear handler y observer
        self.handler = N0FileHandler(modo_prueba=self.modo_prueba)
        self.observer = Observer()
        
        # Configurar monitoreo
        self.observer.schedule(
            self.handler, 
            self.directorio_data, 
            recursive=False
        )
        
        # Iniciar observer
        self.observer.start()
        self.ejecutando = True
        
        logger.info(f"✅ Monitor iniciado en: {self.directorio_data}")
        logger.info(f"🔍 Modo: {'PRUEBA' if self.modo_prueba else 'PRODUCCIÓN'}")
        logger.info("⏳ Esperando archivos N0 nuevos...")
        
        return True
    
    def detener(self):
        """Detiene el monitor."""
        if self.observer and self.ejecutando:
            logger.info("🛑 Deteniendo monitor N0...")
            self.observer.stop()
            self.observer.join()
            self.ejecutando = False
            logger.info("✅ Monitor detenido")
    
    def ejecutar(self):
        """Ejecuta el monitor indefinidamente."""
        if not self.iniciar():
            return
        
        try:
            while self.ejecutando:
                time.sleep(10)  # Generar reporte cada 10 segundos
                
                # Generar reporte de estado periódico
                if hasattr(self.handler, 'generar_reporte_estado'):
                    reporte = self.handler.generar_reporte_estado()
                    # Solo mostrar reporte si hay cambios significativos
                    if len(self.handler.archivos_procesados) > 0:
                        logger.debug("📊 Estado del monitor actualizado")
        
        except KeyboardInterrupt:
            logger.info("⌨️ Interrupción por teclado detectada")
        
        finally:
            self.detener()
    
    def procesar_archivos_pendientes(self):
        """Procesa archivos N0 que puedan estar pendientes."""
        logger.info("🔄 Verificando archivos pendientes...")
        
        data_path = Path(self.directorio_data)
        archivos_n0 = list(data_path.glob("N0_*.json"))
        
        archivos_nuevos = []
        for archivo in archivos_n0:
            if archivo.name not in self.handler.archivos_procesados:
                archivos_nuevos.append(archivo)
        
        if archivos_nuevos:
            logger.info(f"📋 Encontrados {len(archivos_nuevos)} archivos pendientes")
            for archivo in archivos_nuevos:
                self.handler._procesar_archivo_n0(str(archivo))
        else:
            logger.info("✅ No hay archivos pendientes")

def main():
    """Función principal."""
    print("🔍 MONITOR AUTOMÁTICO N0")
    print("=" * 50)
    print("Monitorea Data_out y procesa automáticamente nuevos archivos N0")
    print("Presiona Ctrl+C para detener")
    print()
    
    # Crear monitor en MODO REAL
    monitor = N0Monitor(modo_prueba=False)
    
    # Procesar archivos pendientes primero
    if hasattr(monitor, 'handler') and monitor.handler:
        monitor.procesar_archivos_pendientes()
    
    # Ejecutar monitor
    monitor.ejecutar()

if __name__ == "__main__":
    main()
