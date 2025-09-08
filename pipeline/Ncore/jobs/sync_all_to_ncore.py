#!/usr/bin/env python3
"""
Script maestro de sincronización completa db_sistema_electrico → db_Ncore.
Ejecuta todos los jobs de sincronización en orden óptimo.

FRECUENCIA RECOMENDADA: Diario a las 06:00 AM

Uso:
    python sync_all_to_ncore.py [--full]
    
    --full: Sincroniza todo el histórico (más lento)
    Sin --full: Sincroniza solo últimos 30 días (incremental)
"""

import subprocess
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Directorio de jobs
JOBS_DIR = Path(__file__).parent
VENV_PATH = Path(__file__).parents[2] / 'venv'

def run_job(script_name, args=None):
    """Ejecuta un job Python con el entorno virtual activado."""
    cmd = [
        sys.executable,
        str(JOBS_DIR / script_name)
    ]
    if args:
        cmd.extend(args)
    
    print(f"\n{'='*60}")
    print(f"🚀 Ejecutando: {script_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print(f"⚠️  Advertencias: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {script_name}: {e}")
        print(f"   Salida: {e.stdout}")
        print(f"   Error: {e.stderr}")
        return False

def main():
    start_time = datetime.now()
    is_full = '--full' in sys.argv
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║     SINCRONIZACIÓN COMPLETA SISTEMA_ELÉCTRICO → NCORE    ║
╚══════════════════════════════════════════════════════════╝
    
Fecha: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
Modo: {'COMPLETO (histórico)' if is_full else 'INCREMENTAL (30 días)'}
""")
    
    success_count = 0
    total_count = 0
    
    # 1. Actualizar PVPC en sistema_electrico (origen)
    # NOTA: Solo si no existe un job externo que ya lo haga
    print("\n📊 PASO 1: Actualizar PVPC en sistema_eléctrico")
    if is_full:
        print("   ⏭️  Saltando - asumiendo que datos históricos ya existen")
    else:
        total_count += 1
        if run_job('update_pvpc_simple.py'):
            success_count += 1
    
    # 2. Sincronizar BOE regulado → Ncore
    print("\n📋 PASO 2: Sincronizar BOE regulado")
    total_count += 1
    if run_job('sync_boe_to_ncore.py'):
        success_count += 1
    
    # 3. Backfill PVPC horario → core_precios_omie
    print("\n⚡ PASO 3: Sincronizar PVPC horario")
    total_count += 1
    if is_full:
        # Sincronización completa desde 2020
        args = ['--start', '2020-01-01', '--step-days', '30']
    else:
        # Solo últimos 30 días
        start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        args = ['--start', start, '--step-days', '7']
    
    if run_job('backfill_pvpc_to_ncore.py', args):
        success_count += 1
    
    # 4. Sincronizar OMIE diario (usando SQL existente)
    print("\n📈 PASO 4: Sincronizar OMIE diario")
    total_count += 1
    # Ejecutar SQL directamente ya que no tenemos job Python específico
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='admin',
            dbname='db_Ncore'
        )
        with conn:
            with conn.cursor() as cur:
                sql_path = JOBS_DIR.parent / 'sql' / 'sync_omie_daily.sql'
                if sql_path.exists():
                    cur.execute(sql_path.read_text())
                    print(f"   ✅ OMIE diario sincronizado: {cur.rowcount} filas")
                    success_count += 1
                else:
                    print(f"   ⚠️  No se encuentra {sql_path}")
        conn.close()
    except Exception as e:
        print(f"   ❌ Error sincronizando OMIE diario: {e}")
    
    # 5. REE Mix/CO2 (si está programado)
    print("\n🌱 PASO 5: Actualizar REE Mix/CO2")
    total_count += 1
    # Por defecto actualiza el día anterior
    if run_job('fetch_ree_mix_co2.py'):
        success_count += 1
    
    # 6. PVGIS radiación (si existe)
    pvgis_job = JOBS_DIR / 'fetch_pvgis_radiation.py'
    if pvgis_job.exists():
        print("\n☀️  PASO 6: Actualizar PVGIS radiación")
        total_count += 1
        if run_job('fetch_pvgis_radiation.py'):
            success_count += 1
    
    # Resumen final
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                    RESUMEN DE EJECUCIÓN                   ║
╚══════════════════════════════════════════════════════════╝

✅ Jobs exitosos: {success_count}/{total_count}
⏱️  Tiempo total: {duration:.1f} segundos
🏁 Finalizado: {end_time.strftime('%Y-%m-%d %H:%M:%S')}

{'✅ SINCRONIZACIÓN COMPLETA' if success_count == total_count else '⚠️  SINCRONIZACIÓN PARCIAL - Revisar errores'}
""")
    
    sys.exit(0 if success_count == total_count else 1)

if __name__ == '__main__':
    main()
