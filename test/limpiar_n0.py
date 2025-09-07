#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpiar completamente BD N0
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno - CORREGIDO: .env está en directorio padre
load_dotenv(Path(__file__).parent.parent / '.env')

# Importar conexiones centralizadas - CORREGIDO path
core_path = Path(__file__).resolve().parent.parent / 'core'
sys.path.insert(0, str(core_path))

from db_connections import db_manager

def limpiar_bd_n0():
    """Elimina todos los registros de todas las tablas N0."""
    
    tablas_n0 = [
        'documents',        # Sin FK
        'metadata',         # Sin FK  
        'supply_address',   # Sin FK
        'direccion_fiscal', # Sin FK - AGREGADA
        'invoice_summary',  # Con FK a invoice - AGREGADA
        'invoice',          # Con FK a contract
        'power_term',       # Con FK a contract
        'energy_consumption', # Con FK a contract
        'metering',         # Con FK a contract - AGREGADA
        'sustainability',   # Con FK a contract - AGREGADA
        'contract',         # Con FK a supply_point, client, provider
        'supply_point',     # Sin FK (excepto posibles self-references)
        'provider',         # Sin FK
        'client'            # Sin FK
    ]
    
    print("🗑️ Limpiando BD N0...")
    
    try:
        with db_manager.get_connection('N0') as conn:
            with conn.cursor() as cursor:
                for tabla in tablas_n0:
                    try:
                        cursor.execute(f"DELETE FROM {tabla}")
                        affected = cursor.rowcount
                        print(f"  ✅ {tabla}: {affected} registros eliminados")
                    except Exception as e:
                        print(f"  ❌ Error eliminando {tabla}: {e}")
                
                # Commit los cambios
                conn.commit()
                print("✅ BD N0 limpiada completamente")
                
    except Exception as e:
        print(f"❌ Error limpiando BD N0: {e}")

if __name__ == "__main__":
    limpiar_bd_n0()
