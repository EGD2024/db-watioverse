#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Insertador N0 REFACTORIZADO - Versión simplificada usando mapeos externos
========================================================================
Inserta datos desde archivos JSON N0 en base de datos PostgreSQL N0.

Características:
- Usa mapeos externos desde mapeos_N0.py
- Gestión eficiente de conexiones (bajo demanda)
- Código más limpio y mantenible
- Modo prueba y producción
"""
import os
import sys
import json
import logging
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import psycopg2

# Configurar path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Import centralizado de mapeos
from mapeos_N0 import MapeosN0

# Import de módulos compartidos
from core.db_connections import db_manager
from pipeline.shared.n0_flattener import N0SemiFlattener

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Directorio de archivos N0
DATA_OUT_DIR = Path(__file__).parent.parent.parent.parent.parent

@dataclass
class ResultadoInsercion:
    """Resultado de inserción de un archivo."""
    archivo: str
    exitoso: bool
    registros_insertados: int
    errores: List[str]
    tiempo_procesamiento: float

class N0Inserter:
    """
    Insertador de datos N0 en BD PostgreSQL - VERSIÓN REFACTORIZADA.
    Usa mapeos externos para mantener código limpio.
    """
    
    def __init__(self, modo_prueba: bool = True):
        """
        Inicializa el insertador.
        
        Args:
            modo_prueba: Si True, solo simula inserciones. Si False, inserta en BD real.
        """
        self.modo_prueba = modo_prueba
        self.n0_flattener = N0SemiFlattener()
        self.mapeos = MapeosN0()  # Instancia de mapeos externos
        self.resultados = []
        
        logger.info(f"🚀 Insertador N0 inicializado - Modo: {'PRUEBA' if modo_prueba else 'PRODUCCIÓN'}")
        
        # Mapeo de tablas a funciones de mapeo
        self.tabla_mapper = {
            'client': self.mapeos.mapear_datos_client,
            'provider': self.mapeos.mapear_datos_provider,
            'supply_point': self.mapeos.mapear_datos_supply_point,
            'supply_address': self.mapeos.mapear_datos_supply_address,
            'contract': self.mapeos.mapear_datos_contract,
            'energy_consumption': self.mapeos.mapear_datos_energy_consumption,
            'power_term': self.mapeos.mapear_datos_power_term,
            'invoice': self.mapeos.mapear_datos_invoice,
            'metadata': self.mapeos.mapear_datos_metadata,
            'documents': self.mapeos.mapear_datos_documents
        }
    
    def procesar_archivo(self, archivo_path: Path) -> ResultadoInsercion:
        """Procesa un archivo JSON N0 e inserta en BD."""
        inicio = datetime.now()
        errores = []
        registros_insertados = 0
        
        try:
            logger.info(f"\n📄 Procesando: {archivo_path.name}")
            
            # 1. Cargar y aplanar JSON
            with open(archivo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 2. Aplanar datos
            datos_aplanados = self.n0_flattener.semi_flatten_n0_data(data)
            
            # 3. Validar estructura semi-aplanada
            if not self.n0_flattener.validate_semi_flattened_structure(datos_aplanados):
                errores.append("Estructura semi-aplanada inválida")
                return ResultadoInsercion(
                    archivo=archivo_path.name,
                    exitoso=False,
                    registros_insertados=0,
                    errores=errores,
                    tiempo_procesamiento=(datetime.now() - inicio).total_seconds()
                )
            
            # 4. Insertar en orden específico para relaciones FK
            orden_insercion = [
                'client', 'provider', 'supply_point', 'contract',
                'metering', 'energy_consumption', 'power_term',
                'invoice', 'invoice_summary', 'sustainability',
                'metadata', 'supply_address', 'direccion_fiscal',
                'documents'
            ]
            
            # IDs insertados para referencias FK
            ids_insertados = {}
            
            for tabla in orden_insercion:
                # Solo procesar tablas que tenemos mapeador
                if tabla not in self.tabla_mapper:
                    continue
                    
                try:
                    # Obtener función de mapeo
                    mapper_func = self.tabla_mapper[tabla]
                    
                    # Mapear datos
                    datos_mapeados = mapper_func(datos_aplanados)
                    
                    # Agregar FK si es necesario
                    if tabla == 'supply_address' and 'supply_point' in ids_insertados:
                        datos_mapeados['supply_point_id'] = ids_insertados['supply_point']
                    
                    # Insertar
                    if self.insertar_en_tabla(tabla, datos_mapeados):
                        registros_insertados += 1
                        # Guardar ID si es necesario (en modo real)
                        if not self.modo_prueba:
                            # Aquí obtendríamos el ID real de la inserción
                            ids_insertados[tabla] = 1  # Placeholder
                            
                except Exception as e:
                    error_msg = f"Error en tabla {tabla}: {str(e)}"
                    logger.error(error_msg)
                    errores.append(error_msg)
            
            # Actualizar tabla documents con FKs
            if 'documents' in self.tabla_mapper and not self.modo_prueba:
                self._actualizar_documents_fks(datos_aplanados, ids_insertados)
            
            exitoso = registros_insertados > 0 and len(errores) == 0
            
        except Exception as e:
            error_msg = f"Error procesando archivo: {str(e)}"
            logger.error(error_msg)
            errores.append(error_msg)
            exitoso = False
            
        tiempo_total = (datetime.now() - inicio).total_seconds()
        
        return ResultadoInsercion(
            archivo=archivo_path.name,
            exitoso=exitoso,
            registros_insertados=registros_insertados,
            errores=errores,
            tiempo_procesamiento=tiempo_total
        )
    
    def insertar_en_tabla(self, tabla: str, datos: Dict[str, Any]) -> bool:
        """Inserta datos en tabla BD (real o simulación)."""
        if self.modo_prueba:
            logger.info(f"  📝 SIMULANDO inserción en tabla '{tabla}':")
            campos_no_nulos = {k: v for k, v in datos.items() if v is not None}
            for campo, valor in campos_no_nulos.items():
                logger.info(f"    - {campo}: {valor}")
            logger.info(f"  ✅ Simulación exitosa - {len(campos_no_nulos)} campos")
            return True
        else:
            # Inserción real en BD
            return self._insertar_real(tabla, datos)
    
    def _insertar_real(self, tabla: str, datos: Dict[str, Any]) -> bool:
        """Ejecuta inserción real en BD N0."""
        conn = None
        cursor = None
        
        try:
            # Obtener conexión solo a N0
            conn = db_manager.get_connection('N0')
            cursor = conn.cursor()
            
            # Filtrar campos no nulos
            campos_no_nulos = {k: v for k, v in datos.items() if v is not None and v != ''}
            
            if not campos_no_nulos:
                logger.warning(f"  ⚠️ No hay datos para insertar en '{tabla}'")
                return False
            
            # Construir query
            campos = list(campos_no_nulos.keys())
            valores = list(campos_no_nulos.values())
            placeholders = ', '.join(['%s'] * len(campos))
            
            query = f"""
                INSERT INTO {tabla} ({', '.join(campos)})
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING
            """
            
            # Ejecutar
            cursor.execute(query, valores)
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"  ✅ Insertado en '{tabla}' - {len(campos_no_nulos)} campos")
                return True
            else:
                logger.info(f"  ⚠️ Registro duplicado en '{tabla}' - ignorado")
                return False
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"  ❌ Error insertando en '{tabla}': {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                db_manager.return_connection('N0', conn)
    
    def procesar_directorio(self, limite_archivos: Optional[int] = None) -> List[ResultadoInsercion]:
        """Procesa todos los archivos N0 del directorio."""
        archivos = list(DATA_OUT_DIR.glob("N0_*.json"))
        
        if limite_archivos:
            archivos = archivos[:limite_archivos]
            
        logger.info(f"\n🎯 Procesando {len(archivos)} archivos N0...")
        
        for archivo in archivos:
            resultado = self.procesar_archivo(archivo)
            self.resultados.append(resultado)
            
        return self.resultados
    
    def _actualizar_documents_fks(self, datos_json: dict, ids_insertados: dict):
        """Actualiza foreign keys en tabla documents."""
        # Placeholder - implementar si es necesario
        pass
    
    def generar_reporte(self) -> str:
        """Genera reporte de procesamiento."""
        reporte = [
            "\n" + "=" * 60,
            "📊 REPORTE DE INSERCIÓN N0",
            "=" * 60,
            f"Total archivos procesados: {len(self.resultados)}"
        ]
        
        exitosos = [r for r in self.resultados if r.exitoso]
        fallidos = [r for r in self.resultados if not r.exitoso]
        
        if exitosos:
            reporte.append("✅ ARCHIVOS PROCESADOS EXITOSAMENTE:")
            for resultado in exitosos:
                reporte.append(f"  - {resultado.archivo}: {resultado.registros_insertados} tablas ({resultado.tiempo_procesamiento:.2f}s)")
        
        if fallidos:
            reporte.append("")
            reporte.append("❌ ARCHIVOS CON ERRORES:")
            for resultado in fallidos:
                reporte.append(f"  - {resultado.archivo}:")
                for error in resultado.errores:
                    reporte.append(f"    • {error}")
        
        tiempo_total = sum(r.tiempo_procesamiento for r in self.resultados)
        registros_total = sum(r.registros_insertados for r in self.resultados)
        
        reporte.append("")
        reporte.append(f"⏱️ Tiempo total: {tiempo_total:.2f} segundos")
        reporte.append(f"📝 Total registros insertados: {registros_total}")
        reporte.append("=" * 60)
        
        return "\n".join(reporte)

def main():
    """Función principal."""
    # Determinar modo según argumento
    modo_prueba = '--produccion' not in sys.argv
    
    print(f"🚀 INSERTADOR N0 REFACTORIZADO - MODO {'PRUEBA' if modo_prueba else 'PRODUCCIÓN'}")
    print("=" * 50)
    
    # Crear insertador
    inserter = N0Inserter(modo_prueba=modo_prueba)
    
    try:
        # Procesar archivos
        limite = 3 if modo_prueba else None
        resultados = inserter.procesar_directorio(limite_archivos=limite)
        
        # Mostrar reporte
        reporte = inserter.generar_reporte()
        print(reporte)
        
        # Guardar reporte
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        modo_str = 'prueba' if modo_prueba else 'produccion'
        reportes_dir = Path("/Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/pipeline/reportes_insercion")
        reportes_dir.mkdir(exist_ok=True)
        archivo_reporte = reportes_dir / f"reporte_insercion_n0_{modo_str}_{timestamp}.txt"
        
        with open(archivo_reporte, 'w', encoding='utf-8') as f:
            f.write(reporte)
        
        print(f"\n💾 Reporte guardado en: {archivo_reporte}")
        
    except Exception as e:
        logger.error(f"❌ Error en procesamiento: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
