#!/usr/bin/env python3
"""
Script para probar acceso a API ESIOS y encontrar datos disponibles
"""

import os
import requests
from datetime import datetime, timedelta, date
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('/Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/.env')

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_esios_api():
    """Probar diferentes endpoints y períodos de la API ESIOS"""
    
    token = os.getenv('ESIOS_API_TOKEN')
    if not token:
        logger.error("Token ESIOS_API_TOKEN no encontrado")
        return
    
    headers = {
        'Accept': 'application/json; application/vnd.esios-api-v1+json',
        'Content-Type': 'application/json',
        'Host': 'api.esios.ree.es',
        'Authorization': f'Token token="{token}"'
    }
    
    # 1. Probar datos recientes (últimos 7 días)
    logger.info("🔍 Probando datos recientes (últimos 7 días)...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    url = "https://api.esios.ree.es/indicators/600"  # OMIE
    params = {
        'start_date': start_date.strftime('%Y-%m-%dT00:00'),
        'end_date': end_date.strftime('%Y-%m-%dT23:59'),
        'time_trunc': 'hour'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        logger.info(f"Datos recientes - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'indicator' in data and 'values' in data['indicator']:
                values = data['indicator']['values']
                logger.info(f"✅ Datos recientes disponibles: {len(values)} registros")
                
                # Mostrar algunos ejemplos
                if values:
                    logger.info("Ejemplos de datos:")
                    for i, val in enumerate(values[:3]):
                        logger.info(f"  {val['datetime']}: {val['value']} €/MWh")
            else:
                logger.warning("Respuesta sin datos de valores")
        else:
            logger.error(f"Error: {response.text}")
    except Exception as e:
        logger.error(f"Error consultando datos recientes: {e}")
    
    # 2. Probar datos de 2021 (más antiguos pero no tanto como 2020)
    logger.info("\n🔍 Probando datos de 2021...")
    params_2021 = {
        'start_date': '2021-01-01T00:00',
        'end_date': '2021-01-07T23:59',
        'time_trunc': 'hour'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params_2021, timeout=30)
        logger.info(f"Datos 2021 - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'indicator' in data and 'values' in data['indicator']:
                values = data['indicator']['values']
                logger.info(f"✅ Datos 2021 disponibles: {len(values)} registros")
            else:
                logger.warning("Respuesta 2021 sin datos de valores")
        else:
            logger.error(f"Error 2021: {response.text}")
    except Exception as e:
        logger.error(f"Error consultando datos 2021: {e}")
    
    # 3. Probar datos de 2020
    logger.info("\n🔍 Probando datos de 2020...")
    params_2020 = {
        'start_date': '2020-01-01T00:00',
        'end_date': '2020-01-07T23:59',
        'time_trunc': 'hour'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params_2020, timeout=30)
        logger.info(f"Datos 2020 - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'indicator' in data and 'values' in data['indicator']:
                values = data['indicator']['values']
                logger.info(f"✅ Datos 2020 disponibles: {len(values)} registros")
            else:
                logger.warning("Respuesta 2020 sin datos de valores")
        elif response.status_code == 403:
            logger.warning("❌ Datos 2020 no accesibles (403 Forbidden)")
        else:
            logger.error(f"Error 2020: {response.text}")
    except Exception as e:
        logger.error(f"Error consultando datos 2020: {e}")
    
    # 4. Listar indicadores disponibles
    logger.info("\n🔍 Listando indicadores disponibles...")
    try:
        indicators_url = "https://api.esios.ree.es/indicators"
        response = requests.get(indicators_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'indicators' in data:
                indicators = data['indicators']
                logger.info(f"Indicadores disponibles: {len(indicators)}")
                
                # Buscar indicadores relacionados con OMIE
                omie_indicators = [ind for ind in indicators if 'omie' in ind.get('name', '').lower() or 'precio' in ind.get('name', '').lower()]
                
                logger.info("Indicadores relacionados con precios:")
                for ind in omie_indicators[:10]:  # Mostrar primeros 10
                    logger.info(f"  ID {ind['id']}: {ind['name']}")
        else:
            logger.error(f"Error listando indicadores: {response.text}")
    except Exception as e:
        logger.error(f"Error listando indicadores: {e}")

if __name__ == "__main__":
    logger.info("🔍 Probando acceso a API ESIOS...")
    logger.info("=" * 50)
    test_esios_api()
