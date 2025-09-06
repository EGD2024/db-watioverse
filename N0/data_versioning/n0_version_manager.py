#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Versionado y Monitorización N0
Gestiona versiones de facturas, detecta mejoras en extracción y controla actualizaciones.
"""

import os
import json
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import logging

@dataclass
class FacturaVersion:
    """Información de versión de una factura."""
    numero_factura: str
    cups: str
    fecha_factura: str
    archivo_original: str
    hash_contenido: str
    numero_campos: int
    campos_principales: List[str]
    campos_nuevos: List[str]
    version: int
    fecha_procesamiento: str
    tamano_archivo: int
    calidad_extraccion: float  # 0.0 - 1.0

@dataclass
class EstadisticasExtraccion:
    """Estadísticas de mejora en extracción."""
    total_facturas: int
    facturas_actualizadas: int
    campos_nuevos_detectados: int
    mejora_promedio_calidad: float
    facturas_por_calidad: Dict[str, int]  # excelente, buena, regular, mala

class N0VersionManager:
    """Gestor de versiones y monitorización para datos N0."""
    
    def __init__(self, db_path: str = "n0_versions.db", data_dir: str = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out"):
        self.db_path = db_path
        self.data_dir = Path(data_dir)
        self.logger = logging.getLogger(__name__)
        
        # Campos críticos que deben existir en electricidad
        self.campos_criticos_electricidad = {
            'identificacion': ['numero_factura', 'cups', 'fecha_factura', 'comercializadora'],
            'consumo': ['consumo_facturado_kwh', 'consumo_facturado_mes'],
            'potencia': ['potencia_contratada_kw', 'potencia_maxima_p1', 'potencia_maxima_p2'],
            'costes': ['importe_total_factura', 'termino_energia', 'termino_potencia'],
            'periodos': ['consumo_p1', 'consumo_p2', 'consumo_p3'],
            'datos_tecnicos': ['tarifa_acceso', 'tipo_peaje', 'zona_geografica']
        }
        
        self._inicializar_bd()
    
    def _inicializar_bd(self):
        """Inicializa la base de datos de versiones."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS facturas_versiones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_factura TEXT NOT NULL,
                    cups TEXT,
                    fecha_factura TEXT,
                    archivo_original TEXT NOT NULL,
                    hash_contenido TEXT NOT NULL,
                    numero_campos INTEGER NOT NULL,
                    campos_principales TEXT NOT NULL,  -- JSON array
                    campos_nuevos TEXT,  -- JSON array
                    version INTEGER NOT NULL,
                    fecha_procesamiento TEXT NOT NULL,
                    tamano_archivo INTEGER NOT NULL,
                    calidad_extraccion REAL NOT NULL,
                    UNIQUE(numero_factura, cups, fecha_factura, version)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS mejoras_extraccion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_analisis TEXT NOT NULL,
                    total_facturas INTEGER NOT NULL,
                    facturas_actualizadas INTEGER NOT NULL,
                    campos_nuevos_detectados INTEGER NOT NULL,
                    mejora_promedio_calidad REAL NOT NULL,
                    detalle_mejoras TEXT NOT NULL,  -- JSON
                    fecha_creacion TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_factura_version 
                ON facturas_versiones(numero_factura, version DESC)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_fecha_procesamiento 
                ON facturas_versiones(fecha_procesamiento DESC)
            ''')
    
    def calcular_hash_factura(self, datos_factura: dict) -> str:
        """Calcula hash del contenido relevante de la factura."""
        # Extraer campos clave para el hash (excluyendo metadatos de procesamiento)
        campos_hash = {
            k: v for k, v in datos_factura.items() 
            if k not in ['fecha_procesamiento', 'archivo_origen', 'timestamp_extraccion']
        }
        
        contenido_str = json.dumps(campos_hash, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(contenido_str.encode('utf-8')).hexdigest()
    
    def extraer_campos_principales(self, datos_factura: dict) -> List[str]:
        """Extrae lista de campos principales presentes en la factura."""
        campos = []
        
        def extraer_campos_recursivo(obj, prefijo=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    campo_completo = f"{prefijo}.{k}" if prefijo else k
                    if isinstance(v, (str, int, float, bool)) and v is not None:
                        campos.append(campo_completo)
                    elif isinstance(v, dict):
                        extraer_campos_recursivo(v, campo_completo)
                    elif isinstance(v, list) and v:
                        campos.append(f"{campo_completo}[]")
        
        extraer_campos_recursivo(datos_factura)
        return sorted(campos)
    
    def calcular_calidad_extraccion(self, campos_presentes: List[str]) -> float:
        """Calcula la calidad de extracción basada en campos críticos presentes."""
        total_criticos = sum(len(campos) for campos in self.campos_criticos_electricidad.values())
        criticos_presentes = 0
        
        for categoria, campos_categoria in self.campos_criticos_electricidad.items():
            for campo in campos_categoria:
                # Buscar el campo en cualquier nivel de la estructura
                if any(campo in cp for cp in campos_presentes):
                    criticos_presentes += 1
        
        # Calidad base por campos críticos
        calidad_base = criticos_presentes / total_criticos
        
        # Bonificación por campos adicionales (máximo +0.2)
        campos_adicionales = max(0, len(campos_presentes) - total_criticos)
        bonificacion = min(0.2, campos_adicionales * 0.01)
        
        return min(1.0, calidad_base + bonificacion)
    
    def obtener_version_actual(self, numero_factura: str, cups: str, fecha_factura: str) -> Optional[FacturaVersion]:
        """Obtiene la versión más reciente de una factura."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM facturas_versiones 
                WHERE numero_factura = ? AND cups = ? AND fecha_factura = ?
                ORDER BY version DESC LIMIT 1
            ''', (numero_factura, cups, fecha_factura))
            
            row = cursor.fetchone()
            if row:
                return FacturaVersion(
                    numero_factura=row['numero_factura'],
                    cups=row['cups'],
                    fecha_factura=row['fecha_factura'],
                    archivo_original=row['archivo_original'],
                    hash_contenido=row['hash_contenido'],
                    numero_campos=row['numero_campos'],
                    campos_principales=json.loads(row['campos_principales']),
                    campos_nuevos=json.loads(row['campos_nuevos'] or '[]'),
                    version=row['version'],
                    fecha_procesamiento=row['fecha_procesamiento'],
                    tamano_archivo=row['tamano_archivo'],
                    calidad_extraccion=row['calidad_extraccion']
                )
        return None
    
    def debe_actualizar_factura(self, archivo_factura: Path, datos_factura: dict) -> Tuple[bool, str]:
        """Determina si una factura debe actualizarse."""
        # Extraer identificadores de la factura
        numero_factura = datos_factura.get('numero_factura', 'UNKNOWN')
        cups = datos_factura.get('cups', datos_factura.get('codigo_cups', 'UNKNOWN'))
        fecha_factura = datos_factura.get('fecha_factura', datos_factura.get('fecha_inicio_periodo', ''))
        
        # Obtener versión actual
        version_actual = self.obtener_version_actual(numero_factura, cups, fecha_factura)
        
        if not version_actual:
            return True, "Nueva factura - primera vez"
        
        # Calcular métricas de la nueva versión
        hash_nuevo = self.calcular_hash_factura(datos_factura)
        campos_nuevos = self.extraer_campos_principales(datos_factura)
        calidad_nueva = self.calcular_calidad_extraccion(campos_nuevos)
        
        # Criterios de actualización
        if hash_nuevo != version_actual.hash_contenido:
            if len(campos_nuevos) > version_actual.numero_campos:
                return True, f"Nuevos campos detectados: {len(campos_nuevos)} vs {version_actual.numero_campos}"
            elif calidad_nueva > version_actual.calidad_extraccion + 0.05:  # Mejora significativa
                return True, f"Mejora en calidad: {calidad_nueva:.2f} vs {version_actual.calidad_extraccion:.2f}"
            elif len(campos_nuevos) == version_actual.numero_campos:
                return False, "Mismo número de campos y calidad similar - no actualizar"
            else:
                return True, "Contenido diferente detectado"
        
        return False, "Factura idéntica - no actualizar"
    
    def registrar_version_factura(self, archivo_factura: Path, datos_factura: dict) -> FacturaVersion:
        """Registra una nueva versión de factura."""
        # Extraer identificadores
        numero_factura = datos_factura.get('numero_factura', 'UNKNOWN')
        cups = datos_factura.get('cups', datos_factura.get('codigo_cups', 'UNKNOWN'))
        fecha_factura = datos_factura.get('fecha_factura', datos_factura.get('fecha_inicio_periodo', ''))
        
        # Calcular métricas
        hash_contenido = self.calcular_hash_factura(datos_factura)
        campos_principales = self.extraer_campos_principales(datos_factura)
        calidad = self.calcular_calidad_extraccion(campos_principales)
        
        # Obtener versión anterior para detectar campos nuevos
        version_anterior = self.obtener_version_actual(numero_factura, cups, fecha_factura)
        nueva_version = (version_anterior.version + 1) if version_anterior else 1
        
        campos_nuevos = []
        if version_anterior:
            campos_nuevos = [c for c in campos_principales if c not in version_anterior.campos_principales]
        
        # Crear registro de versión
        factura_version = FacturaVersion(
            numero_factura=numero_factura,
            cups=cups,
            fecha_factura=fecha_factura,
            archivo_original=str(archivo_factura.name),
            hash_contenido=hash_contenido,
            numero_campos=len(campos_principales),
            campos_principales=campos_principales,
            campos_nuevos=campos_nuevos,
            version=nueva_version,
            fecha_procesamiento=datetime.now().isoformat(),
            tamano_archivo=archivo_factura.stat().st_size,
            calidad_extraccion=calidad
        )
        
        # Guardar en BD
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO facturas_versiones (
                    numero_factura, cups, fecha_factura, archivo_original,
                    hash_contenido, numero_campos, campos_principales, campos_nuevos,
                    version, fecha_procesamiento, tamano_archivo, calidad_extraccion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                factura_version.numero_factura,
                factura_version.cups,
                factura_version.fecha_factura,
                factura_version.archivo_original,
                factura_version.hash_contenido,
                factura_version.numero_campos,
                json.dumps(factura_version.campos_principales),
                json.dumps(factura_version.campos_nuevos),
                factura_version.version,
                factura_version.fecha_procesamiento,
                factura_version.tamano_archivo,
                factura_version.calidad_extraccion
            ))
        
        return factura_version
    
    def procesar_directorio_facturas(self) -> Dict[str, any]:
        """Procesa todas las facturas del directorio y actualiza versiones."""
        print(f"\n🔍 Procesando facturas en: {self.data_dir}")
        print("=" * 80)
        
        facturas_json = list(self.data_dir.glob("*.json"))
        resultados = {
            'total_facturas': len(facturas_json),
            'facturas_nuevas': 0,
            'facturas_actualizadas': 0,
            'facturas_ignoradas': 0,
            'errores': 0,
            'mejoras_detectadas': [],
            'estadisticas_calidad': {'excelente': 0, 'buena': 0, 'regular': 0, 'mala': 0}
        }
        
        for i, archivo_factura in enumerate(facturas_json, 1):
            print(f"\n📄 [{i}/{len(facturas_json)}] {archivo_factura.name}")
            
            try:
                # Cargar factura
                with open(archivo_factura, 'r', encoding='utf-8') as f:
                    datos_factura = json.load(f)
                
                # Verificar si debe actualizarse
                debe_actualizar, razon = self.debe_actualizar_factura(archivo_factura, datos_factura)
                
                if debe_actualizar:
                    # Registrar nueva versión
                    version = self.registrar_version_factura(archivo_factura, datos_factura)
                    
                    if version.version == 1:
                        resultados['facturas_nuevas'] += 1
                        print(f"  ✅ Nueva factura registrada (v{version.version})")
                    else:
                        resultados['facturas_actualizadas'] += 1
                        print(f"  🔄 Factura actualizada (v{version.version})")
                        
                        if version.campos_nuevos:
                            mejora = {
                                'factura': archivo_factura.name,
                                'version_anterior': version.version - 1,
                                'version_nueva': version.version,
                                'campos_nuevos': version.campos_nuevos,
                                'mejora_calidad': version.calidad_extraccion
                            }
                            resultados['mejoras_detectadas'].append(mejora)
                    
                    print(f"     📊 Campos: {version.numero_campos}")
                    print(f"     🎯 Calidad: {version.calidad_extraccion:.2f}")
                    
                    # Clasificar calidad
                    if version.calidad_extraccion >= 0.9:
                        resultados['estadisticas_calidad']['excelente'] += 1
                    elif version.calidad_extraccion >= 0.7:
                        resultados['estadisticas_calidad']['buena'] += 1
                    elif version.calidad_extraccion >= 0.5:
                        resultados['estadisticas_calidad']['regular'] += 1
                    else:
                        resultados['estadisticas_calidad']['mala'] += 1
                        
                else:
                    resultados['facturas_ignoradas'] += 1
                    print(f"  ⏭️ Ignorada: {razon}")
                
            except Exception as e:
                resultados['errores'] += 1
                print(f"  ❌ Error: {str(e)[:100]}...")
        
        # Guardar estadísticas de mejora
        self._guardar_estadisticas_mejora(resultados)
        
        return resultados
    
    def _guardar_estadisticas_mejora(self, resultados: dict):
        """Guarda estadísticas de mejora en la BD."""
        estadisticas = EstadisticasExtraccion(
            total_facturas=resultados['total_facturas'],
            facturas_actualizadas=resultados['facturas_actualizadas'],
            campos_nuevos_detectados=sum(len(m['campos_nuevos']) for m in resultados['mejoras_detectadas']),
            mejora_promedio_calidad=sum(m['mejora_calidad'] for m in resultados['mejoras_detectadas']) / max(1, len(resultados['mejoras_detectadas'])),
            facturas_por_calidad=resultados['estadisticas_calidad']
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO mejoras_extraccion (
                    fecha_analisis, total_facturas, facturas_actualizadas,
                    campos_nuevos_detectados, mejora_promedio_calidad,
                    detalle_mejoras, fecha_creacion
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().strftime('%Y-%m-%d'),
                estadisticas.total_facturas,
                estadisticas.facturas_actualizadas,
                estadisticas.campos_nuevos_detectados,
                estadisticas.mejora_promedio_calidad,
                json.dumps(resultados['mejoras_detectadas']),
                datetime.now().isoformat()
            ))
    
    def generar_reporte_mejoras(self) -> dict:
        """Genera reporte de mejoras en extracción."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Estadísticas generales
            cursor = conn.execute('''
                SELECT 
                    COUNT(DISTINCT numero_factura) as total_facturas_unicas,
                    COUNT(*) as total_versiones,
                    AVG(calidad_extraccion) as calidad_promedio,
                    MAX(version) as version_maxima
                FROM facturas_versiones
            ''')
            stats_generales = cursor.fetchone()
            
            # Mejoras recientes (último mes)
            cursor = conn.execute('''
                SELECT * FROM mejoras_extraccion 
                WHERE fecha_creacion >= date('now', '-30 days')
                ORDER BY fecha_creacion DESC
            ''')
            mejoras_recientes = cursor.fetchall()
            
            # Top facturas con más versiones
            cursor = conn.execute('''
                SELECT numero_factura, cups, COUNT(*) as num_versiones,
                       MAX(calidad_extraccion) as mejor_calidad
                FROM facturas_versiones 
                GROUP BY numero_factura, cups
                HAVING num_versiones > 1
                ORDER BY num_versiones DESC, mejor_calidad DESC
                LIMIT 10
            ''')
            top_actualizadas = cursor.fetchall()
        
        return {
            'estadisticas_generales': dict(stats_generales),
            'mejoras_recientes': [dict(row) for row in mejoras_recientes],
            'facturas_mas_actualizadas': [dict(row) for row in top_actualizadas],
            'fecha_reporte': datetime.now().isoformat()
        }
    
    def imprimir_reporte_completo(self):
        """Imprime reporte completo de estado N0."""
        print("\n" + "=" * 80)
        print("📊 REPORTE ESTADO N0 - SISTEMA DE VERSIONADO")
        print("=" * 80)
        
        reporte = self.generar_reporte_mejoras()
        stats = reporte['estadisticas_generales']
        
        print(f"\n📈 ESTADÍSTICAS GENERALES:")
        print(f"  • Facturas únicas: {stats['total_facturas_unicas']}")
        print(f"  • Total versiones: {stats['total_versiones']}")
        print(f"  • Calidad promedio: {stats['calidad_promedio']:.2f}")
        print(f"  • Versión máxima: {stats['version_maxima']}")
        
        if reporte['mejoras_recientes']:
            print(f"\n🔄 MEJORAS RECIENTES (último mes):")
            for mejora in reporte['mejoras_recientes'][:5]:
                print(f"  • {mejora['fecha_analisis']}: {mejora['facturas_actualizadas']} facturas actualizadas")
                print(f"    - {mejora['campos_nuevos_detectados']} campos nuevos detectados")
                print(f"    - Mejora calidad promedio: {mejora['mejora_promedio_calidad']:.2f}")
        
        if reporte['facturas_mas_actualizadas']:
            print(f"\n🏆 FACTURAS MÁS ACTUALIZADAS:")
            for factura in reporte['facturas_mas_actualizadas'][:5]:
                print(f"  • {factura['numero_factura']} ({factura['cups']})")
                print(f"    - Versiones: {factura['num_versiones']}")
                print(f"    - Mejor calidad: {factura['mejor_calidad']:.2f}")

def main():
    """Función principal para ejecutar el sistema de versionado."""
    manager = N0VersionManager()
    
    # Procesar todas las facturas
    resultados = manager.procesar_directorio_facturas()
    
    # Mostrar resultados
    print("\n" + "=" * 80)
    print("📋 RESUMEN PROCESAMIENTO")
    print("=" * 80)
    print(f"✅ Facturas nuevas: {resultados['facturas_nuevas']}")
    print(f"🔄 Facturas actualizadas: {resultados['facturas_actualizadas']}")
    print(f"⏭️ Facturas ignoradas: {resultados['facturas_ignoradas']}")
    print(f"❌ Errores: {resultados['errores']}")
    
    if resultados['mejoras_detectadas']:
        print(f"\n🎯 MEJORAS DETECTADAS: {len(resultados['mejoras_detectadas'])}")
        for mejora in resultados['mejoras_detectadas'][:3]:
            print(f"  • {mejora['factura']}: +{len(mejora['campos_nuevos'])} campos")
    
    print(f"\n📊 DISTRIBUCIÓN CALIDAD:")
    for nivel, cantidad in resultados['estadisticas_calidad'].items():
        print(f"  • {nivel.capitalize()}: {cantidad}")
    
    # Generar reporte completo
    manager.imprimir_reporte_completo()

if __name__ == "__main__":
    main()
