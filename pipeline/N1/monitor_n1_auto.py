#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Monitor automático N1 - Detección y procesamiento de archivos JSON N1
Monitorea directorio de archivos N1 generados y los inserta automáticamente en BD N1
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Añadir directorio shared al path
sys.path.append(str(Path(__file__).parent.parent / 'shared'))

# Importar módulos N1
from insert_N1 import N1Inserter, insertar_n1_file

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor_n1_auto.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class N1FileHandler(FileSystemEventHandler):
    """Manejador de eventos para archivos N1."""
    
    def __init__(self, monitor):
        self.monitor = monitor
        self.processed_files = set()
        
    def on_created(self, event):
        """Se ejecuta cuando se crea un archivo."""
        if not event.is_directory and self._is_n1_file(event.src_path):
            logger.info(f"📄 Nuevo archivo N1 detectado: {event.src_path}")
            self.monitor.procesar_archivo_n1(event.src_path)
    
    def on_modified(self, event):
        """Se ejecuta cuando se modifica un archivo."""
        if not event.is_directory and self._is_n1_file(event.src_path):
            # Evitar procesamiento múltiple del mismo archivo
            if event.src_path not in self.processed_files:
                logger.info(f"📝 Archivo N1 modificado: {event.src_path}")
                self.monitor.procesar_archivo_n1(event.src_path)
                self.processed_files.add(event.src_path)
    
    def _is_n1_file(self, file_path: str) -> bool:
        """Verifica si un archivo es un JSON N0 para procesar a N1."""
        path = Path(file_path)
        
        # Verificar extensión
        if path.suffix.lower() != '.json':
            return False
        
        # Verificar patrón de nombre N0 (archivos de entrada para N1)
        name = path.name.lower()
        if not name.startswith('n0_'):
            return False
        
        # Verificar que no sea archivo temporal
        if name.startswith('.') or name.endswith('.tmp'):
            return False
        
        return True

class N1Monitor:
    """Monitor automático para archivos JSON N1."""
    
    def __init__(self, directorio_monitoreo: str, modo_prueba: bool = True):
        self.directorio_monitoreo = Path(directorio_monitoreo)
        self.modo_prueba = modo_prueba
        self.inserter = N1Inserter(modo_prueba=modo_prueba)
        self.observer = None
        self.archivos_procesados = 0
        self.archivos_error = 0
        self.inicio_monitoreo = None
        
        # Crear directorio si no existe
        self.directorio_monitoreo.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🔍 Monitor N1 inicializado")
        logger.info(f"📁 Directorio: {self.directorio_monitoreo}")
        logger.info(f"🎯 Modo: {'PRUEBA' if modo_prueba else 'PRODUCCIÓN'}")
    
    def procesar_archivo_n1(self, archivo_path: str):
        """Procesa un archivo N1 individual."""
        try:
            # Esperar un momento para asegurar que el archivo esté completamente escrito
            time.sleep(0.5)
            
            # Verificar que el archivo existe y es válido
            if not self._validar_archivo_n1(archivo_path):
                logger.warning(f"⚠️ Archivo N1 no válido: {archivo_path}")
                return
            
            logger.info(f"🚀 Procesando archivo N1: {Path(archivo_path).name}")
            
            # Insertar en BD N1
            exito = insertar_n1_file(archivo_path, self.modo_prueba)
            
            if exito:
                self.archivos_procesados += 1
                logger.info(f"✅ Archivo N1 procesado exitosamente: {Path(archivo_path).name}")
                
                # Mover archivo a directorio procesados
                self._mover_archivo_procesado(archivo_path)
                
            else:
                self.archivos_error += 1
                logger.error(f"❌ Error procesando archivo N1: {Path(archivo_path).name}")
                
                # Mover archivo a directorio errores
                self._mover_archivo_error(archivo_path)
        
        except Exception as e:
            self.archivos_error += 1
            logger.error(f"💥 Error inesperado procesando {archivo_path}: {e}", exc_info=True)
            self._mover_archivo_error(archivo_path)
    
    def _validar_archivo_n1(self, archivo_path: str) -> bool:
        """Valida que un archivo sea un JSON N0 correcto para procesar a N1."""
        try:
            with open(archivo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verificar estructura mínima N0
            required_fields = ['cups', 'cliente']
            if not all(field in data for field in required_fields):
                logger.warning(f"Archivo N0 sin campos requeridos: {archivo_path}")
                return False
            
            # Verificar metadatos N0
            if '_metadata' not in data:
                logger.warning(f"Archivo sin metadatos N0: {archivo_path}")
                # Aún es válido, solo advertencia
            
            return True
            
        except json.JSONDecodeError:
            logger.error(f"Archivo N0 con JSON inválido: {archivo_path}")
            return False
        except Exception as e:
            logger.error(f"Error validando archivo N0 {archivo_path}: {e}")
            return False
    
    def _mover_archivo_procesado(self, archivo_path: str):
        """Mueve archivo procesado a directorio correspondiente."""
        try:
            archivo = Path(archivo_path)
            directorio_procesados = self.directorio_monitoreo / 'procesados'
            directorio_procesados.mkdir(exist_ok=True)
            
            destino = directorio_procesados / archivo.name
            archivo.rename(destino)
            
            logger.debug(f"📦 Archivo movido a procesados: {destino}")
            
        except Exception as e:
            logger.error(f"Error moviendo archivo procesado: {e}")
    
    def _mover_archivo_error(self, archivo_path: str):
        """Mueve archivo con error a directorio correspondiente."""
        try:
            archivo = Path(archivo_path)
            directorio_errores = self.directorio_monitoreo / 'errores'
            directorio_errores.mkdir(exist_ok=True)
            
            # Añadir timestamp al nombre para evitar conflictos
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_error = f"{archivo.stem}_ERROR_{timestamp}{archivo.suffix}"
            destino = directorio_errores / nombre_error
            
            archivo.rename(destino)
            
            logger.debug(f"🗂️ Archivo movido a errores: {destino}")
            
        except Exception as e:
            logger.error(f"Error moviendo archivo con error: {e}")
    
    def procesar_archivos_existentes(self):
        """Procesa archivos N1 existentes en el directorio."""
        logger.info("🔍 Buscando archivos N1 existentes...")
        
        archivos_n1 = []
        for archivo in self.directorio_monitoreo.glob('*.json'):
            if self._is_n1_file(str(archivo)):
                archivos_n1.append(archivo)
        
        if archivos_n1:
            logger.info(f"📊 Encontrados {len(archivos_n1)} archivos N1 existentes")
            
            for archivo in archivos_n1:
                self.procesar_archivo_n1(str(archivo))
        else:
            logger.info("📭 No hay archivos N1 existentes para procesar")
    
    def _is_n1_file(self, file_path: str) -> bool:
        """Verifica si un archivo es un JSON N0 para procesar a N1."""
        path = Path(file_path)
        name = path.name.lower()
        
        return (path.suffix.lower() == '.json' and 
                name.startswith('n0_') and
                not name.startswith('.') and 
                not name.endswith('.tmp'))
    
    def iniciar_monitoreo(self):
        """Inicia el monitoreo automático."""
        try:
            logger.info("🚀 INICIANDO MONITOR AUTOMÁTICO N1")
            self.inicio_monitoreo = datetime.now()
            
            # Procesar archivos existentes primero
            self.procesar_archivos_existentes()
            
            # Configurar observer para monitoreo en tiempo real
            event_handler = N1FileHandler(self)
            self.observer = Observer()
            self.observer.schedule(event_handler, str(self.directorio_monitoreo), recursive=False)
            
            # Iniciar monitoreo
            self.observer.start()
            logger.info(f"👁️ Monitoreo activo en: {self.directorio_monitoreo}")
            logger.info("⏸️ Presiona Ctrl+C para detener el monitoreo")
            
            # Mantener el proceso activo
            try:
                while True:
                    time.sleep(10)  # Revisar cada 10 segundos
                    self._mostrar_estadisticas()
                    
            except KeyboardInterrupt:
                logger.info("⏹️ Deteniendo monitor por solicitud del usuario...")
                
        except Exception as e:
            logger.error(f"💥 Error en monitoreo automático: {e}", exc_info=True)
            
        finally:
            self.detener_monitoreo()
    
    def detener_monitoreo(self):
        """Detiene el monitoreo automático."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("🛑 Monitor N1 detenido")
        
        self._generar_reporte_final()
    
    def _mostrar_estadisticas(self):
        """Muestra estadísticas periódicas del monitoreo."""
        if self.inicio_monitoreo:
            tiempo_activo = datetime.now() - self.inicio_monitoreo
            horas = int(tiempo_activo.total_seconds() // 3600)
            minutos = int((tiempo_activo.total_seconds() % 3600) // 60)
            
            logger.info(f"📊 Estadísticas - Activo: {horas:02d}:{minutos:02d}h | "
                       f"Procesados: {self.archivos_procesados} | "
                       f"Errores: {self.archivos_error}")
    
    def _generar_reporte_final(self):
        """Genera reporte final del monitoreo."""
        if self.inicio_monitoreo:
            tiempo_total = datetime.now() - self.inicio_monitoreo
            
            reporte = []
            reporte.append("=" * 60)
            reporte.append("📋 REPORTE FINAL MONITOR N1")
            reporte.append("=" * 60)
            reporte.append(f"⏱️ Tiempo activo: {tiempo_total}")
            reporte.append(f"📁 Directorio monitoreado: {self.directorio_monitoreo}")
            reporte.append(f"🎯 Modo: {'PRUEBA' if self.modo_prueba else 'PRODUCCIÓN'}")
            reporte.append(f"✅ Archivos procesados: {self.archivos_procesados}")
            reporte.append(f"❌ Archivos con error: {self.archivos_error}")
            
            total = self.archivos_procesados + self.archivos_error
            if total > 0:
                tasa_exito = (self.archivos_procesados / total) * 100
                reporte.append(f"📈 Tasa de éxito: {tasa_exito:.1f}%")
            
            reporte.append("=" * 60)
            
            reporte_texto = "\n".join(reporte)
            logger.info(f"\n{reporte_texto}")
            
            # Guardar reporte
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archivo_reporte = f"reporte_monitor_n1_{timestamp}.txt"
            
            with open(archivo_reporte, 'w', encoding='utf-8') as f:
                f.write(reporte_texto)
            
            logger.info(f"📄 Reporte guardado: {archivo_reporte}")

def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor automático archivos N1')
    parser.add_argument('--directorio', '-d', 
                       default='./generated_jsons',
                       help='Directorio a monitorear (default: ./generated_jsons)')
    parser.add_argument('--produccion', '-p', 
                       action='store_true',
                       help='Ejecutar en modo producción (default: modo prueba)')
    
    args = parser.parse_args()
    
    # Crear monitor
    monitor = N1Monitor(
        directorio_monitoreo=args.directorio,
        modo_prueba=not args.produccion
    )
    
    # Iniciar monitoreo
    monitor.iniciar_monitoreo()

if __name__ == "__main__":
    main()
