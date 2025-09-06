#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador de Schemas N0 para Electricidad
Verifica que todos los campos de los schemas ES electricity existen en N0 con nombres correctos.
"""

import os
import json
import glob
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from n0_field_mapper import N0FieldMapper

@dataclass
class CampoSchema:
    """Información de un campo del schema."""
    nombre: str
    tipo: str
    requerido: bool
    descripcion: str
    archivo_schema: str
    ruta_completa: str

@dataclass
class ResultadoValidacion:
    """Resultado de validación de campos."""
    campos_schema_total: int
    campos_encontrados_n0: int
    campos_faltantes: List[str]
    campos_extra_n0: List[str]
    coincidencia_nombres: float
    facturas_validadas: int
    errores_validacion: List[str]

class N0SchemaValidator:
    """Validador de schemas N0 contra schemas de electricidad ES."""
    
    def __init__(self, 
                 schemas_path: str = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/motor_extraccion/schemas/data/ES/electricity",
                 n0_data_path: str = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out"):
        self.schemas_path = Path(schemas_path)
        self.n0_data_path = Path(n0_data_path)
        self.logger = logging.getLogger(__name__)
        
        # Campos del schema cargados
        self.campos_schema: Dict[str, CampoSchema] = {}
        self.campos_n0_encontrados: Set[str] = set()
        
        # Inicializar mapeador inteligente
        self.field_mapper = N0FieldMapper()
        
        # Mapeo de nombres alternativos conocidos
        self.mapeo_nombres = {
            'codigo_cups': 'cups',
            'fecha_inicio_periodo': 'fecha_factura',
            'importe_total': 'importe_total_factura',
            'consumo_kwh': 'consumo_facturado_kwh',
            'potencia_contratada': 'potencia_contratada_kw'
        }
    
    def cargar_schemas_electricidad(self) -> bool:
        """Carga todos los schemas de electricidad ES."""
        print(f"🔍 Cargando schemas desde: {self.schemas_path}")
        
        if not self.schemas_path.exists():
            print(f"❌ Directorio de schemas no encontrado: {self.schemas_path}")
            return False
        
        # Buscar todos los archivos JSON de schema
        patron_schemas = self.schemas_path / "**/*.json"
        archivos_schema = list(self.schemas_path.glob("**/*.json"))
        
        print(f"📄 Encontrados {len(archivos_schema)} archivos de schema")
        
        for archivo_schema in archivos_schema:
            try:
                with open(archivo_schema, 'r', encoding='utf-8') as f:
                    schema_data = json.load(f)
                
                # Extraer campos del schema
                self._extraer_campos_schema(schema_data, archivo_schema)
                
            except Exception as e:
                print(f"⚠️ Error cargando schema {archivo_schema.name}: {e}")
        
        print(f"✅ Cargados {len(self.campos_schema)} campos únicos de schemas")
        return len(self.campos_schema) > 0
    
    def _extraer_campos_schema(self, schema_data: dict, archivo_schema: Path, prefijo: str = ""):
        """Extrae campos de un schema JSON recursivamente."""
        
        if isinstance(schema_data, dict):
            # Si tiene 'properties', es un objeto con campos definidos
            if 'properties' in schema_data:
                for campo_nombre, campo_def in schema_data['properties'].items():
                    nombre_completo = f"{prefijo}.{campo_nombre}" if prefijo else campo_nombre
                    
                    # Extraer información del campo
                    tipo = campo_def.get('type', 'unknown')
                    requerido = campo_nombre in schema_data.get('required', [])
                    descripcion = campo_def.get('description', campo_def.get('title', ''))
                    
                    # Crear objeto CampoSchema
                    campo_schema = CampoSchema(
                        nombre=nombre_completo,
                        tipo=tipo,
                        requerido=requerido,
                        descripcion=descripcion,
                        archivo_schema=archivo_schema.name,
                        ruta_completa=str(archivo_schema.relative_to(self.schemas_path))
                    )
                    
                    self.campos_schema[nombre_completo] = campo_schema
                    
                    # Si el campo es un objeto, extraer subcampos
                    if tipo == 'object' and 'properties' in campo_def:
                        self._extraer_campos_schema(campo_def, archivo_schema, nombre_completo)
            
            # Buscar en otras estructuras del schema
            for key, value in schema_data.items():
                if key not in ['properties', 'required', 'type', 'description', 'title']:
                    if isinstance(value, dict):
                        self._extraer_campos_schema(value, archivo_schema, prefijo)
    
    def validar_facturas_n0(self) -> ResultadoValidacion:
        """Valida todas las facturas N0 contra los schemas usando mapeo inteligente."""
        print(f"\n🔍 Validando facturas N0 en: {self.n0_data_path}")
        
        facturas_json = list(self.n0_data_path.glob("*.json"))
        print(f"📄 Encontradas {len(facturas_json)} facturas N0")
        
        campos_n0_mapeados = set()
        errores_validacion = []
        facturas_procesadas = 0
        facturas_datos = []
        
        # Cargar y procesar facturas
        for i, archivo_factura in enumerate(facturas_json, 1):
            try:
                with open(archivo_factura, 'r', encoding='utf-8') as f:
                    datos_factura = json.load(f)
                
                facturas_datos.append(datos_factura)
                facturas_procesadas += 1
                
                if i <= 5:  # Mostrar progreso para las primeras 5
                    print(f"  📄 {archivo_factura.name}: cargada")
                
            except Exception as e:
                error_msg = f"Error procesando {archivo_factura.name}: {str(e)[:100]}"
                errores_validacion.append(error_msg)
                print(f"  ❌ {error_msg}")
        
        # Usar mapeo inteligente para encontrar campos
        print(f"🧠 Aplicando mapeo inteligente de campos...")
        
        for datos_factura in facturas_datos:
            factura_mapeada = self.field_mapper.mapear_factura_completa(datos_factura)
            campos_n0_mapeados.update(factura_mapeada.keys())
        
        self.campos_n0_encontrados = campos_n0_mapeados
        print(f"✅ Campos mapeados encontrados: {len(campos_n0_mapeados)}")
        
        # Analizar coincidencias
        return self._analizar_coincidencias(facturas_procesadas, errores_validacion)
    
    def _extraer_campos_factura(self, datos_factura: dict, prefijo: str = "") -> Set[str]:
        """Extrae todos los campos de una factura recursivamente."""
        campos = set()
        
        if isinstance(datos_factura, dict):
            for key, value in datos_factura.items():
                nombre_completo = f"{prefijo}.{key}" if prefijo else key
                
                if value is not None:
                    campos.add(nombre_completo)
                    
                    # Si es un diccionario, extraer subcampos
                    if isinstance(value, dict):
                        subcampos = self._extraer_campos_factura(value, nombre_completo)
                        campos.update(subcampos)
                    elif isinstance(value, list) and value and isinstance(value[0], dict):
                        # Para arrays de objetos, tomar el primer elemento como muestra
                        subcampos = self._extraer_campos_factura(value[0], f"{nombre_completo}[]")
                        campos.update(subcampos)
        
        return campos
    
    def _analizar_coincidencias(self, facturas_procesadas: int, errores: List[str]) -> ResultadoValidacion:
        """Analiza las coincidencias entre schemas y datos N0."""
        
        # Aplicar mapeo de nombres alternativos
        campos_n0_normalizados = set()
        for campo in self.campos_n0_encontrados:
            # Buscar mapeo directo
            campo_normalizado = self.mapeo_nombres.get(campo, campo)
            campos_n0_normalizados.add(campo_normalizado)
            
            # También mantener el original
            campos_n0_normalizados.add(campo)
        
        # Encontrar coincidencias
        campos_schema_nombres = set(self.campos_schema.keys())
        campos_encontrados = campos_schema_nombres.intersection(campos_n0_normalizados)
        campos_faltantes = campos_schema_nombres - campos_n0_normalizados
        campos_extra = campos_n0_normalizados - campos_schema_nombres
        
        # Calcular porcentaje de coincidencia
        coincidencia = len(campos_encontrados) / len(campos_schema_nombres) if campos_schema_nombres else 0
        
        return ResultadoValidacion(
            campos_schema_total=len(campos_schema_nombres),
            campos_encontrados_n0=len(campos_encontrados),
            campos_faltantes=sorted(list(campos_faltantes)),
            campos_extra_n0=sorted(list(campos_extra)),
            coincidencia_nombres=coincidencia,
            facturas_validadas=facturas_procesadas,
            errores_validacion=errores
        )
    
    def generar_reporte_validacion(self, resultado: ResultadoValidacion) -> str:
        """Genera reporte detallado de validación."""
        
        reporte = []
        reporte.append("# REPORTE VALIDACIÓN SCHEMAS N0 vs ELECTRICIDAD ES")
        reporte.append("")
        reporte.append("## 📊 Resumen General")
        reporte.append("")
        reporte.append(f"- **Facturas N0 validadas**: {resultado.facturas_validadas}")
        reporte.append(f"- **Campos definidos en schemas**: {resultado.campos_schema_total}")
        reporte.append(f"- **Campos encontrados en N0**: {resultado.campos_encontrados_n0}")
        reporte.append(f"- **Porcentaje coincidencia**: {resultado.coincidencia_nombres:.1%}")
        reporte.append(f"- **Campos faltantes**: {len(resultado.campos_faltantes)}")
        reporte.append(f"- **Campos extra en N0**: {len(resultado.campos_extra_n0)}")
        reporte.append("")
        
        # Estado general
        if resultado.coincidencia_nombres >= 0.8:
            estado = "✅ EXCELENTE"
        elif resultado.coincidencia_nombres >= 0.6:
            estado = "🟡 BUENO"
        elif resultado.coincidencia_nombres >= 0.4:
            estado = "🟠 REGULAR"
        else:
            estado = "❌ DEFICIENTE"
        
        reporte.append(f"**Estado de coincidencia**: {estado}")
        reporte.append("")
        
        # Campos faltantes críticos
        if resultado.campos_faltantes:
            reporte.append("## ❌ Campos Faltantes en N0")
            reporte.append("")
            reporte.append("Los siguientes campos están definidos en los schemas pero no se encontraron en las facturas N0:")
            reporte.append("")
            
            # Agrupar por criticidad (campos requeridos vs opcionales)
            faltantes_criticos = []
            faltantes_opcionales = []
            
            for campo_faltante in resultado.campos_faltantes:
                if campo_faltante in self.campos_schema:
                    campo_info = self.campos_schema[campo_faltante]
                    if campo_info.requerido:
                        faltantes_criticos.append(campo_faltante)
                    else:
                        faltantes_opcionales.append(campo_faltante)
            
            if faltantes_criticos:
                reporte.append("### 🚨 Campos Críticos (Requeridos)")
                reporte.append("")
                for campo in faltantes_criticos[:10]:  # Máximo 10
                    campo_info = self.campos_schema[campo]
                    reporte.append(f"- **{campo}** ({campo_info.tipo})")
                    if campo_info.descripcion:
                        reporte.append(f"  - {campo_info.descripcion}")
                    reporte.append(f"  - Schema: `{campo_info.archivo_schema}`")
                reporte.append("")
            
            if faltantes_opcionales:
                reporte.append("### ⚠️ Campos Opcionales")
                reporte.append("")
                for campo in faltantes_opcionales[:15]:  # Máximo 15
                    reporte.append(f"- `{campo}`")
                if len(faltantes_opcionales) > 15:
                    reporte.append(f"- ... y {len(faltantes_opcionales) - 15} más")
                reporte.append("")
        
        # Campos extra en N0
        if resultado.campos_extra_n0:
            reporte.append("## ➕ Campos Extra en N0")
            reporte.append("")
            reporte.append("Los siguientes campos están presentes en N0 pero no definidos en schemas:")
            reporte.append("")
            
            # Mostrar solo los más relevantes (no metadatos)
            campos_relevantes = [c for c in resultado.campos_extra_n0 
                               if not any(meta in c.lower() for meta in ['timestamp', 'fecha_procesamiento', 'archivo_origen', 'version'])]
            
            for campo in sorted(campos_relevantes)[:20]:  # Máximo 20
                reporte.append(f"- `{campo}`")
            
            if len(campos_relevantes) > 20:
                reporte.append(f"- ... y {len(campos_relevantes) - 20} más")
            reporte.append("")
        
        # Errores de validación
        if resultado.errores_validacion:
            reporte.append("## ⚠️ Errores de Validación")
            reporte.append("")
            for error in resultado.errores_validacion[:5]:
                reporte.append(f"- {error}")
            if len(resultado.errores_validacion) > 5:
                reporte.append(f"- ... y {len(resultado.errores_validacion) - 5} errores más")
            reporte.append("")
        
        # Recomendaciones
        reporte.append("## 💡 Recomendaciones")
        reporte.append("")
        
        if resultado.coincidencia_nombres < 0.6:
            reporte.append("- 🚨 **CRÍTICO**: Baja coincidencia de campos. Revisar proceso de extracción.")
        
        if len(resultado.campos_faltantes) > 10:
            reporte.append("- 🔧 **Mejora extracción**: Muchos campos faltantes. Actualizar parsers OCR.")
        
        if len(resultado.campos_extra_n0) > 50:
            reporte.append("- 📋 **Actualizar schemas**: Muchos campos extra. Considerar actualizar schemas.")
        
        reporte.append("- 🔄 **Monitorización continua**: Ejecutar validación regularmente para detectar mejoras.")
        reporte.append("- 📊 **Versionado N0**: Usar sistema de versionado para trackear mejoras en extracción.")
        reporte.append("")
        
        return "\n".join(reporte)
    
    def ejecutar_validacion_completa(self) -> bool:
        """Ejecuta validación completa y genera reporte."""
        print("🚀 INICIANDO VALIDACIÓN COMPLETA N0 vs SCHEMAS")
        print("=" * 80)
        
        # 1. Cargar schemas
        if not self.cargar_schemas_electricidad():
            print("❌ Error cargando schemas. Abortando validación.")
            return False
        
        # 2. Validar facturas N0
        resultado = self.validar_facturas_n0()
        
        # 3. Mostrar resumen en consola
        print("\n" + "=" * 80)
        print("📋 RESUMEN VALIDACIÓN")
        print("=" * 80)
        print(f"✅ Facturas procesadas: {resultado.facturas_validadas}")
        print(f"📊 Campos en schemas: {resultado.campos_schema_total}")
        print(f"🎯 Campos encontrados: {resultado.campos_encontrados_n0}")
        print(f"📈 Coincidencia: {resultado.coincidencia_nombres:.1%}")
        print(f"❌ Campos faltantes: {len(resultado.campos_faltantes)}")
        print(f"➕ Campos extra: {len(resultado.campos_extra_n0)}")
        
        # 4. Generar reporte detallado
        reporte_contenido = self.generar_reporte_validacion(resultado)
        
        # 5. Guardar reporte
        archivo_reporte = f"reporte_validacion_n0_schemas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(archivo_reporte, 'w', encoding='utf-8') as f:
            f.write(reporte_contenido)
        
        print(f"📄 Reporte guardado: {archivo_reporte}")
        
        # 6. Determinar si N0 está listo para N1
        n0_listo = resultado.coincidencia_nombres >= 0.7 and len(resultado.errores_validacion) == 0
        
        if n0_listo:
            print("\n✅ N0 LISTO PARA AVANZAR A N1")
            print("   - Coincidencia de campos suficiente")
            print("   - Sin errores críticos de validación")
        else:
            print("\n⚠️ N0 REQUIERE MEJORAS ANTES DE N1")
            print("   - Mejorar extracción de campos faltantes")
            print("   - Resolver errores de validación")
        
        return n0_listo

def main():
    """Función principal."""
    from datetime import datetime
    
    validator = N0SchemaValidator()
    
    # Ejecutar validación completa
    n0_listo = validator.ejecutar_validacion_completa()
    
    print("\n" + "=" * 80)
    if n0_listo:
        print("🎉 VALIDACIÓN COMPLETADA - N0 PREPARADO PARA N1")
    else:
        print("🔧 VALIDACIÓN COMPLETADA - N0 REQUIERE MEJORAS")
    print("=" * 80)
    
    return n0_listo

if __name__ == "__main__":
    main()
