#!/usr/bin/env python3
"""
Script para probar endpoints alternativos de ESIOS y fuentes alternativas
Identifica qué datos podemos obtener con el token actual
"""

import os
import sys
import logging
import requests
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

# Cargar variables de entorno
env_path = '/Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/motor_actualizaciones/config/migrated/watioverse.env'
load_dotenv(env_path)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/pipeline/logs/test_esios_alternatives.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_esios_token():
    """Obtiene el token ESIOS"""
    return os.getenv('ESIOS_API_TOKEN')

def test_public_endpoints():
    """Prueba endpoints públicos sin autenticación"""
    logger.info("🔍 Probando endpoints públicos (sin token)...")
    
    public_endpoints = [
        {
            'url': 'https://api.esios.ree.es/indicators',
            'name': 'Lista de indicadores'
        },
        {
            'url': 'https://api.esios.ree.es/archives',
            'name': 'Archivos disponibles'
        }
    ]
    
    results = {}
    
    for endpoint in public_endpoints:
        try:
            response = requests.get(endpoint['url'], timeout=10)
            logger.info(f"   {endpoint['name']}: Status {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results[endpoint['name']] = {'status': 'OK', 'data': data}
                logger.info(f"   ✅ Datos disponibles")
            else:
                results[endpoint['name']] = {'status': 'ERROR', 'code': response.status_code}
                
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            results[endpoint['name']] = {'status': 'EXCEPTION', 'error': str(e)}
    
    return results

def test_basic_indicators_with_token(token):
    """Prueba indicadores básicos con token"""
    logger.info("🔍 Probando indicadores básicos con token...")
    
    headers = {
        'Accept': 'application/json; application/vnd.esios-api-v1+json',
        'Content-Type': 'application/json',
        'Host': 'api.esios.ree.es',
        'Authorization': f'Token token={token}'
    }
    
    # Indicadores más básicos (posiblemente públicos)
    basic_indicators = [
        {'id': 1, 'name': 'Precio mercado OMIE'},
        {'id': 600, 'name': 'Precio mercado diario'},
        {'id': 1001, 'name': 'Generación programada'},
        {'id': 1293, 'name': 'Demanda b.c. nacional'},
        {'id': 460, 'name': 'Demanda b.c. peninsular'}
    ]
    
    results = {}
    
    for indicator in basic_indicators:
        try:
            url = f"https://api.esios.ree.es/indicators/{indicator['id']}"
            response = requests.get(url, headers=headers, timeout=10)
            
            logger.info(f"   Indicador {indicator['id']} ({indicator['name']}): Status {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results[indicator['id']] = {'status': 'OK', 'name': indicator['name']}
                logger.info(f"   ✅ Accesible")
            elif response.status_code == 403:
                results[indicator['id']] = {'status': 'FORBIDDEN', 'name': indicator['name']}
                logger.info(f"   ❌ Sin permisos")
            else:
                results[indicator['id']] = {'status': 'ERROR', 'code': response.status_code}
                
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            results[indicator['id']] = {'status': 'EXCEPTION', 'error': str(e)}
    
    return results

def test_archives_endpoint(token):
    """Prueba endpoint de archivos (posible alternativa)"""
    logger.info("🔍 Probando endpoint de archivos...")
    
    headers = {
        'Accept': 'application/json; application/vnd.esios-api-v1+json',
        'Content-Type': 'application/json',
        'Host': 'api.esios.ree.es',
        'Authorization': f'Token token={token}'
    }
    
    try:
        response = requests.get('https://api.esios.ree.es/archives', headers=headers, timeout=10)
        logger.info(f"   Archives endpoint: Status {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            archives = data.get('archives', [])
            logger.info(f"   ✅ {len(archives)} archivos disponibles")
            
            # Mostrar algunos archivos relevantes
            relevant_archives = [arch for arch in archives[:10] 
                               if any(keyword in arch.get('name', '').lower() 
                                     for keyword in ['demanda', 'precio', 'omie', 'mercado'])]
            
            for arch in relevant_archives:
                logger.info(f"   📁 {arch.get('name', 'N/A')}")
            
            return {'status': 'OK', 'count': len(archives), 'relevant': relevant_archives}
        else:
            logger.error(f"   ❌ Error {response.status_code}")
            return {'status': 'ERROR', 'code': response.status_code}
            
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return {'status': 'EXCEPTION', 'error': str(e)}

def test_alternative_data_sources():
    """Prueba fuentes alternativas de datos"""
    logger.info("🔍 Probando fuentes alternativas...")
    
    # REE Datos Abiertos (sin autenticación)
    alternative_sources = [
        {
            'name': 'REE Datos Abiertos',
            'url': 'https://apidatos.ree.es/en/datos/mercados/precios-mercados-tiempo-real',
            'description': 'API pública REE'
        },
        {
            'name': 'OMIE Datos Públicos',
            'url': 'https://www.omie.es/es/file-access-list',
            'description': 'Archivos CSV públicos OMIE'
        }
    ]
    
    results = {}
    
    for source in alternative_sources:
        try:
            response = requests.get(source['url'], timeout=10)
            logger.info(f"   {source['name']}: Status {response.status_code}")
            
            if response.status_code == 200:
                results[source['name']] = {'status': 'OK', 'url': source['url']}
                logger.info(f"   ✅ Disponible: {source['description']}")
            else:
                results[source['name']] = {'status': 'ERROR', 'code': response.status_code}
                
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            results[source['name']] = {'status': 'EXCEPTION', 'error': str(e)}
    
    return results

def test_minimal_data_request(token):
    """Prueba solicitud mínima de datos"""
    logger.info("🔍 Probando solicitud mínima de datos...")
    
    headers = {
        'Accept': 'application/json; application/vnd.esios-api-v1+json',
        'Content-Type': 'application/json',
        'Host': 'api.esios.ree.es',
        'Authorization': f'Token token={token}'
    }
    
    # Intentar obtener solo 1 hora de datos del indicador más básico
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    try:
        url = "https://api.esios.ree.es/indicators/600"  # Precio mercado diario
        params = {
            'start_date': f'{yesterday}T00:00',
            'end_date': f'{yesterday}T01:00'  # Solo 1 hora
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        logger.info(f"   Solicitud mínima: Status {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            values = data.get('indicator', {}).get('values', [])
            logger.info(f"   ✅ Datos obtenidos: {len(values)} valores")
            return {'status': 'OK', 'values': len(values)}
        else:
            logger.error(f"   ❌ Error {response.status_code}: {response.text}")
            return {'status': 'ERROR', 'code': response.status_code, 'error': response.text}
            
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return {'status': 'EXCEPTION', 'error': str(e)}

def main():
    """Función principal"""
    print("🔍 PRUEBA DE ALTERNATIVAS ESIOS")
    print("=" * 50)
    
    logger.info("🚀 Iniciando pruebas de alternativas...")
    
    token = get_esios_token()
    if not token:
        logger.error("❌ Token no disponible")
        return
    
    # Ejecutar todas las pruebas
    public_results = test_public_endpoints()
    basic_indicators = test_basic_indicators_with_token(token)
    archives_result = test_archives_endpoint(token)
    alternatives = test_alternative_data_sources()
    minimal_request = test_minimal_data_request(token)
    
    # RESUMEN
    print("\n" + "=" * 50)
    print("📋 RESUMEN DE ALTERNATIVAS")
    print("=" * 50)
    
    logger.info("🎯 Resultados:")
    
    # Endpoints públicos
    public_ok = [name for name, result in public_results.items() if result['status'] == 'OK']
    if public_ok:
        logger.info(f"   ✅ Endpoints públicos disponibles: {public_ok}")
    
    # Indicadores accesibles
    accessible_indicators = [ind_id for ind_id, result in basic_indicators.items() if result['status'] == 'OK']
    forbidden_indicators = [ind_id for ind_id, result in basic_indicators.items() if result['status'] == 'FORBIDDEN']
    
    logger.info(f"   ✅ Indicadores accesibles: {accessible_indicators}")
    logger.info(f"   ❌ Indicadores prohibidos: {forbidden_indicators}")
    
    # Archivos
    if archives_result.get('status') == 'OK':
        logger.info(f"   ✅ Archivos disponibles: {archives_result.get('count', 0)}")
    
    # Fuentes alternativas
    alt_ok = [name for name, result in alternatives.items() if result['status'] == 'OK']
    if alt_ok:
        logger.info(f"   ✅ Fuentes alternativas: {alt_ok}")
    
    # Solicitud mínima
    if minimal_request.get('status') == 'OK':
        logger.info(f"   ✅ Solicitudes mínimas funcionan")
    else:
        logger.info(f"   ❌ Solicitudes mínimas fallan: {minimal_request.get('error', 'N/A')}")
    
    # RECOMENDACIONES
    print("\n🎯 RECOMENDACIONES:")
    
    if accessible_indicators:
        print(f"✅ Usar indicadores accesibles: {accessible_indicators}")
        print("   → Implementar carga con estos indicadores únicamente")
    
    if archives_result.get('status') == 'OK':
        print("✅ Usar endpoint de archivos como alternativa")
        print("   → Descargar archivos CSV/Excel en lugar de API en tiempo real")
    
    if alt_ok:
        print(f"✅ Considerar fuentes alternativas: {alt_ok}")
        print("   → REE Datos Abiertos y OMIE archivos públicos")
    
    if not accessible_indicators and minimal_request.get('status') != 'OK':
        print("❌ Token completamente restringido")
        print("   → Solicitar nuevo token a REE con permisos ampliados")
        print("   → Usar exclusivamente fuentes alternativas públicas")
    
    print(f"\n📊 Pruebas completadas - Ver logs para detalles")

if __name__ == "__main__":
    main()
