#!/usr/bin/env python3
"""
Job automático para continuar carga de zonas climáticas cuando se resetee el límite de Open-Meteo.
Se ejecuta automáticamente a las 02:00 AM (después del reset UTC medianoche).
"""

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

def log_message(message):
    """Log con timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def check_remaining_cps():
    """Verificar si quedan CPs por procesar."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="db_Ncore", 
            user="postgres",
            password="Judini2024!"
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM core_codigos_postales cp
            LEFT JOIN core_zonas_climaticas zc ON cp.codigo_postal = zc.codigo_postal
            WHERE zc.codigo_postal IS NULL
        """)
        
        pendientes = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return pendientes
        
    except Exception as e:
        log_message(f"❌ Error verificando CPs pendientes: {e}")
        return -1

def main():
    """Ejecutar continuación automática de carga zonas climáticas."""
    
    log_message("🌡️  Iniciando continuación automática carga zonas climáticas")
    
    # Verificar CPs pendientes
    pendientes = check_remaining_cps()
    
    if pendientes == -1:
        log_message("❌ Error conectando a base de datos")
        sys.exit(1)
    elif pendientes == 0:
        log_message("✅ No hay CPs pendientes - proceso ya completado")
        sys.exit(0)
    else:
        log_message(f"📊 CPs pendientes: {pendientes}")
    
    # Directorio del script
    script_dir = Path(__file__).parent
    resilient_script = script_dir / "load_zonas_climaticas_resilient.py"
    
    if not resilient_script.exists():
        log_message(f"❌ Script resiliente no encontrado: {resilient_script}")
        sys.exit(1)
    
    # Ejecutar script resiliente con --resume
    log_message("🚀 Ejecutando script resiliente con --resume")
    
    try:
        # Cambiar al directorio de trabajo correcto
        os.chdir(script_dir.parent.parent.parent)  # Volver a db_watioverse/
        
        # Ejecutar con Python3 y --resume
        cmd = [
            sys.executable,
            str(resilient_script),
            "--resume"
        ]
        
        log_message(f"Comando: {' '.join(cmd)}")
        log_message(f"Directorio: {os.getcwd()}")
        
        # Ejecutar el proceso
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=28800  # 8 horas máximo
        )
        
        # Log de salida
        if result.stdout:
            log_message("📋 STDOUT:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    log_message(f"   {line}")
        
        if result.stderr:
            log_message("⚠️  STDERR:")
            for line in result.stderr.split('\n'):
                if line.strip():
                    log_message(f"   {line}")
        
        # Verificar resultado
        if result.returncode == 0:
            log_message("✅ Script resiliente completado exitosamente")
            
            # Verificar CPs restantes
            pendientes_final = check_remaining_cps()
            if pendientes_final == 0:
                log_message("🎉 PROCESO COMPLETADO - Todos los CPs procesados")
            else:
                log_message(f"📊 CPs aún pendientes: {pendientes_final}")
                
        else:
            log_message(f"❌ Script resiliente falló con código: {result.returncode}")
            sys.exit(1)
            
    except subprocess.TimeoutExpired:
        log_message("⏰ Script resiliente excedió tiempo límite (8h)")
        sys.exit(1)
    except Exception as e:
        log_message(f"❌ Error ejecutando script resiliente: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
