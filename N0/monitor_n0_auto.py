#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor Automático N0
Monitorea la carpeta Data_out y dispara inserción automática cuando detecta nuevos archivos N0.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Set, Dict, Any
from datetime import datetime
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Importar el insertador N0
from insert_N0 import N0Inserter

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

class N0FileHandler(FileSystemEventHandler):
    """Manejador de eventos para archivos N0."""
    
    def __init__(self, modo_prueba: bool = True):
        super().__init__()
        self.modo_prueba = modo_prueba
        self.archivos_procesados: Set[str] = set()
        self.inserter = N0Inserter(modo_prueba=modo_prueba)
        self.cooldown_segundos = 5  # Evitar procesamiento múltiple
        self.ultimo_procesamiento: Dict[str, float] = {}
        
        # Cargar archivos ya existentes para evitar reprocesamiento
        self._cargar_archivos_existentes()
        
        logger.info(f"🔍 Monitor N0 iniciado - MODO {'PRUEBA' if modo_prueba else 'PRODUCCIÓN'}")
    
    def _cargar_archivos_existentes(self):
        """Carga archivos N0 existentes para evitar reprocesarlos."""
        data_path = Path(self.inserter.directorio_data)
        archivos_existentes = list(data_path.glob("N0_*.json"))
        
        for archivo in archivos_existentes:
            self.archivos_procesados.add(archivo.name)
        
        logger.info(f"📋 Archivos N0 existentes registrados: {len(archivos_existentes)}")
    
    def _es_archivo_n0_valido(self, archivo_path: str) -> bool:
        """Verifica si es un archivo N0 válido."""
        archivo_name = Path(archivo_path).name
        
        # Debe ser JSON y empezar con N0_
        if not (archivo_name.startswith("N0_") and archivo_name.endswith(".json")):
            return False
        
        # Verificar que el archivo existe y no está vacío
        try:
            if not Path(archivo_path).exists():
                return False
            
            # Verificar que es JSON válido
            with open(archivo_path, 'r', encoding='utf-8') as f:
                json.load(f)
            
            return True
            
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"⚠️ Archivo N0 inválido {archivo_name}: {e}")
            return False
    
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
    
    def _procesar_archivo_n0(self, archivo_path: str):
        """Procesa un archivo N0 nuevo."""
        archivo_name = Path(archivo_path).name
        
        try:
            logger.info(f"🚀 NUEVO ARCHIVO N0 DETECTADO: {archivo_name}")
            
            # Marcar tiempo de procesamiento
            self.ultimo_procesamiento[archivo_name] = time.time()
            
            # Procesar archivo
            resultado = self.inserter.procesar_archivo_json(Path(archivo_path))
            
            if resultado.exito:
                logger.info(f"✅ Procesamiento exitoso: {archivo_name}")
                logger.info(f"   📊 {resultado.registros_insertados} tablas insertadas")
                logger.info(f"   ⏱️ Tiempo: {resultado.tiempo_procesamiento:.2f}s")
                
                # Marcar como procesado
                self.archivos_procesados.add(archivo_name)
                
                # Generar notificación
                self._generar_notificacion_exito(resultado)
                
            else:
                logger.error(f"❌ Error procesando {archivo_name}:")
                for error in resultado.errores:
                    logger.error(f"   • {error}")
                
                # Generar notificación de error
                self._generar_notificacion_error(resultado)
            
        except Exception as e:
            logger.error(f"💥 Error crítico procesando {archivo_name}: {e}")
    
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
        
        # Guardar notificación
        archivo_notif = f"notificacion_n0_exito_{timestamp}.json"
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
        
        # Guardar notificación de error
        archivo_notif = f"notificacion_n0_error_{timestamp}.json"
        with open(archivo_notif, 'w', encoding='utf-8') as f:
            json.dump(notificacion, f, indent=2, ensure_ascii=False)
        
        logger.error(f"📄 Notificación de error guardada: {archivo_notif}")
    
    def on_created(self, event):
        """Evento: archivo creado."""
        if event.is_directory:
            return
        
        archivo_path = event.src_path
        
        # Verificar si es archivo N0 válido
        if not self._es_archivo_n0_valido(archivo_path):
            return
        
        # Verificar si debe procesarse
        if not self._debe_procesar_archivo(archivo_path):
            return
        
        # Esperar un momento para asegurar que el archivo está completo
        time.sleep(1)
        
        # Procesar archivo
        self._procesar_archivo_n0(archivo_path)
    
    def on_moved(self, event):
        """Evento: archivo movido."""
        if event.is_directory:
            return
        
        # Tratar como archivo nuevo
        self.on_created(event)
    
    def generar_reporte_estado(self) -> str:
        """Genera reporte del estado actual del monitor."""
        reporte = []
        reporte.append("=" * 60)
        reporte.append("📊 ESTADO MONITOR N0")
        reporte.append("=" * 60)
        reporte.append(f"🔍 Modo: {'PRUEBA' if self.modo_prueba else 'PRODUCCIÓN'}")
        reporte.append(f"📁 Directorio monitoreado: {self.inserter.directorio_data}")
        reporte.append(f"📋 Archivos procesados: {len(self.archivos_procesados)}")
        reporte.append(f"⏱️ Cooldown: {self.cooldown_segundos}s")
        reporte.append("")
        
        if self.archivos_procesados:
            reporte.append("✅ ARCHIVOS PROCESADOS:")
            for archivo in sorted(self.archivos_procesados):
                reporte.append(f"  - {archivo}")
        
        reporte.append("")
        reporte.append(f"🕐 Último reporte: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        reporte.append("=" * 60)
        
        return "\n".join(reporte)

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
    
    # Crear monitor en modo prueba
    monitor = N0Monitor(modo_prueba=True)
    
    # Procesar archivos pendientes primero
    if hasattr(monitor, 'handler') and monitor.handler:
        monitor.procesar_archivos_pendientes()
    
    # Ejecutar monitor
    monitor.ejecutar()

if __name__ == "__main__":
    main()
