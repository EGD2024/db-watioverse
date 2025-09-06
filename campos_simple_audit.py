#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditoría Simple de Campos - Sin dependencias complejas
"""

import json
import os
from pathlib import Path
from typing import Dict, Set, Any

def contar_campos_recursivo(data: Any, prefix: str = "") -> Set[str]:
    """Cuenta todos los campos de forma recursiva en un JSON."""
    campos = set()
    
    if isinstance(data, dict):
        for key, value in data.items():
            campo_completo = f"{prefix}.{key}" if prefix else key
            campos.add(campo_completo)
            
            # Recursivamente contar subcampos
            subcampos = contar_campos_recursivo(value, campo_completo)
            campos.update(subcampos)
            
    elif isinstance(data, list):
        for i, item in enumerate(data):
            subcampos = contar_campos_recursivo(item, f"{prefix}[{i}]" if prefix else f"[{i}]")
            campos.update(subcampos)
            
    return campos

def analizar_json(archivo_path: str) -> Set[str]:
    """Analiza un archivo JSON y cuenta todos sus campos."""
    try:
        with open(archivo_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        campos = contar_campos_recursivo(data)
        print(f"📄 {Path(archivo_path).name}: {len(campos)} campos")
        return campos
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return set()

def main():
    """Función principal."""
    data_dir = "/Users/vagalumeenergiamovil/PROYECTOS/Entorno/Data_out"
    
    print("🔍 AUDITORÍA SIMPLE DE CAMPOS")
    print("="*50)
    
    # Buscar archivos N0
    archivos_n0 = []
    if os.path.exists(data_dir):
        for archivo in os.listdir(data_dir):
            if archivo.startswith('N0_') and archivo.endswith('.json'):
                archivos_n0.append(os.path.join(data_dir, archivo))
    
    if not archivos_n0:
        print("❌ No se encontraron archivos N0")
        return
    
    print(f"📂 Encontrados {len(archivos_n0)} archivos N0")
    
    # Analizar primer archivo como muestra
    archivo_muestra = archivos_n0[0]
    campos_json = analizar_json(archivo_muestra)
    
    print(f"\n📊 RESULTADO:")
    print(f"📄 Total campos en JSON: {len(campos_json)}")
    
    # Mostrar algunos campos como muestra
    print(f"\n📋 MUESTRA DE CAMPOS (primeros 50):")
    for i, campo in enumerate(sorted(campos_json)):
        if i >= 50:
            print(f"   ... y {len(campos_json) - 50} campos más")
            break
        print(f"   • {campo}")
    
    # Crear archivo con todos los campos
    with open("campos_json_completos.txt", "w", encoding="utf-8") as f:
        f.write(f"TODOS LOS CAMPOS JSON N0 ({len(campos_json)} total)\n")
        f.write("="*50 + "\n")
        for campo in sorted(campos_json):
            f.write(f"{campo}\n")
    
    print(f"\n📋 Lista completa guardada en: campos_json_completos.txt")

if __name__ == "__main__":
    main()
