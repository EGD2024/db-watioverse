#!/usr/bin/env python3
"""
Script para probar ambos tokens ESIOS disponibles
"""

import os
import sys
import logging
import requests
from datetime import datetime, timedelta
import json

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/pipeline/logs/test_both_tokens.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_token(token, token_name):
    """Prueba un token específico"""
    logger.info(f"🔍 Probando {token_name}: {token[:10]}...{token[-4:]}")
    
    headers = {
        'Accept': 'application/json; application/vnd.esios-api-v1+json',
        'Content-Type': 'application/json',
        'Host': 'api.esios.ree.es',
        'Authorization': f'Token token={token}'
    }
    
    results = {}
    
    # TEST 1: Lista de indicadores
    try:
        response = requests.get("https://api.esios.ree.es/indicators", headers=headers, timeout=10)
        logger.info(f"   Lista indicadores: {response.status_code}")
        results['indicators_list'] = response.status_code
    except Exception as e:
        logger.error(f"   Error lista indicadores: {e}")
        results['indicators_list'] = 'ERROR'
    
    # TEST 2: Indicadores específicos
    test_indicators = [600, 460, 1293, 1001]
    
    for ind_id in test_indicators:
        try:
            url = f"https://api.esios.ree.es/indicators/{ind_id}"
            response = requests.get(url, headers=headers, timeout=10)
            logger.info(f"   Indicador {ind_id}: {response.status_code}")
            results[f'indicator_{ind_id}'] = response.status_code
        except Exception as e:
            logger.error(f"   Error indicador {ind_id}: {e}")
            results[f'indicator_{ind_id}'] = 'ERROR'
    
    # TEST 3: Descarga de datos pequeña
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        url = "https://api.esios.ree.es/indicators/600"
        params = {
            'start_date': f'{yesterday}T00:00',
            'end_date': f'{yesterday}T01:00'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        logger.info(f"   Descarga datos: {response.status_code}")
        results['data_download'] = response.status_code
        
        if response.status_code == 200:
            data = response.json()
            values = data.get('indicator', {}).get('values', [])
            logger.info(f"   ✅ Datos obtenidos: {len(values)} valores")
            results['data_count'] = len(values)
        
    except Exception as e:
        logger.error(f"   Error descarga: {e}")
        results['data_download'] = 'ERROR'
    
    return results

def main():
    """Función principal"""
    print("🔍 PRUEBA DE AMBOS TOKENS ESIOS")
    print("=" * 60)
    
    # Tokens a probar
    tokens = {
        'TOKEN_1': 'b5eca74755976ba684c9bc370d6ddd36c35adeeaf3d84c203637847f883600d0',
        'TOKEN_2': '511a5399534031be32848c7fbc85cafc0e618db32c6cbebe5b3d6dd103017ff9'
    }
    
    all_results = {}
    
    for token_name, token in tokens.items():
        logger.info(f"\n{'='*50}")
        logger.info(f"🔑 PROBANDO {token_name}")
        logger.info(f"{'='*50}")
        
        results = test_token(token, token_name)
        all_results[token_name] = results
    
    # COMPARACIÓN FINAL
    print("\n" + "=" * 60)
    print("📊 COMPARACIÓN DE TOKENS")
    print("=" * 60)
    
    logger.info("🎯 Resumen comparativo:")
    
    for token_name, results in all_results.items():
        logger.info(f"\n🔑 {token_name}:")
        
        # Contar éxitos
        success_count = sum(1 for status in results.values() 
                          if isinstance(status, int) and status == 200)
        total_tests = len([k for k in results.keys() if k != 'data_count'])
        
        logger.info(f"   ✅ Éxitos: {success_count}/{total_tests}")
        
        # Detalles
        if results.get('indicators_list') == 200:
            logger.info(f"   ✅ Lista de indicadores: OK")
        
        accessible_indicators = [k.split('_')[1] for k, v in results.items() 
                               if k.startswith('indicator_') and v == 200]
        if accessible_indicators:
            logger.info(f"   ✅ Indicadores accesibles: {accessible_indicators}")
        
        if results.get('data_download') == 200:
            count = results.get('data_count', 0)
            logger.info(f"   ✅ Descarga de datos: OK ({count} valores)")
    
    # RECOMENDACIÓN
    print("\n🎯 RECOMENDACIÓN:")
    
    best_token = None
    best_score = -1
    
    for token_name, results in all_results.items():
        score = sum(1 for status in results.values() 
                   if isinstance(status, int) and status == 200)
        
        if score > best_score:
            best_score = score
            best_token = token_name
    
    if best_score > 0:
        logger.info(f"✅ USAR {best_token} - {best_score} funciones disponibles")
        logger.info(f"   → Actualizar .env con el token funcional")
    else:
        logger.info("❌ AMBOS TOKENS BLOQUEADOS")
        logger.info("   → Solicitar nuevo token a REE")
        logger.info("   → Usar fuentes alternativas públicas")
    
    print(f"\n📊 Prueba completada")

if __name__ == "__main__":
    main()
