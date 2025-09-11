#!/usr/bin/env python3
"""
Script para probar descarga específica de datos OMIE con token actual
Verifica si podemos obtener precios de mercado que usábamos antes
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
        logging.FileHandler('/Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/pipeline/logs/test_omie_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_esios_token():
    """Obtiene el token ESIOS"""
    return os.getenv('ESIOS_API_TOKEN')

def test_omie_price_download(token, days_back=7):
    """Prueba descarga de precios OMIE con indicador 600"""
    logger.info(f"🔍 Probando descarga OMIE últimos {days_back} días...")
    
    headers = {
        'Accept': 'application/json; application/vnd.esios-api-v1+json',
        'Content-Type': 'application/json',
        'Host': 'api.esios.ree.es',
        'Authorization': f'Token token={token}'
    }
    
    # Fechas para prueba
    end_date = datetime.now() - timedelta(days=1)  # Ayer
    start_date = end_date - timedelta(days=days_back)
    
    try:
        # Indicador 600: Precio mercado diario (€/MWh)
        url = "https://api.esios.ree.es/indicators/600"
        params = {
            'start_date': start_date.strftime('%Y-%m-%dT00:00'),
            'end_date': end_date.strftime('%Y-%m-%dT23:59')
        }
        
        logger.info(f"   Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
        logger.info(f"   URL: {url}")
        logger.info(f"   Parámetros: {params}")
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        logger.info(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            indicator_data = data.get('indicator', {})
            values = indicator_data.get('values', [])
            
            logger.info(f"✅ Descarga exitosa:")
            logger.info(f"   • Indicador: {indicator_data.get('name', 'N/A')}")
            logger.info(f"   • Valores obtenidos: {len(values)}")
            logger.info(f"   • Unidad: {indicator_data.get('magnitude', 'N/A')}")
            
            # Mostrar algunos valores de ejemplo
            if values:
                logger.info("📈 Primeros 5 valores:")
                for i, value in enumerate(values[:5]):
                    logger.info(f"   {i+1}. {value.get('datetime', 'N/A')}: {value.get('value', 'N/A')} €/MWh")
                
                # Estadísticas básicas
                prices = [float(v.get('value', 0)) for v in values if v.get('value') is not None]
                if prices:
                    logger.info(f"📊 Estadísticas:")
                    logger.info(f"   • Precio mínimo: {min(prices):.2f} €/MWh")
                    logger.info(f"   • Precio máximo: {max(prices):.2f} €/MWh")
                    logger.info(f"   • Precio medio: {sum(prices)/len(prices):.2f} €/MWh")
            
            return {
                'status': 'SUCCESS',
                'values_count': len(values),
                'data': values[:3],  # Solo primeros 3 para ejemplo
                'indicator_name': indicator_data.get('name', 'N/A')
            }
            
        elif response.status_code == 403:
            logger.error("❌ Sin permisos para indicador 600")
            return {'status': 'FORBIDDEN', 'error': response.text}
        else:
            logger.error(f"❌ Error {response.status_code}: {response.text}")
            return {'status': 'ERROR', 'code': response.status_code, 'error': response.text}
            
    except Exception as e:
        logger.error(f"❌ Excepción: {e}")
        return {'status': 'EXCEPTION', 'error': str(e)}

def test_demand_download(token, days_back=3):
    """Prueba descarga de demanda con indicador 460"""
    logger.info(f"🔍 Probando descarga demanda últimos {days_back} días...")
    
    headers = {
        'Accept': 'application/json; application/vnd.esios-api-v1+json',
        'Content-Type': 'application/json',
        'Host': 'api.esios.ree.es',
        'Authorization': f'Token token={token}'
    }
    
    # Fechas para prueba
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=days_back)
    
    try:
        # Indicador 460: Demanda b.c. peninsular
        url = "https://api.esios.ree.es/indicators/460"
        params = {
            'start_date': start_date.strftime('%Y-%m-%dT00:00'),
            'end_date': end_date.strftime('%Y-%m-%dT23:59')
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        logger.info(f"📊 Demanda Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            indicator_data = data.get('indicator', {})
            values = indicator_data.get('values', [])
            
            logger.info(f"✅ Demanda descargada:")
            logger.info(f"   • Valores: {len(values)}")
            logger.info(f"   • Indicador: {indicator_data.get('name', 'N/A')}")
            
            return {
                'status': 'SUCCESS',
                'values_count': len(values),
                'indicator_name': indicator_data.get('name', 'N/A')
            }
        else:
            logger.error(f"❌ Error demanda {response.status_code}")
            return {'status': 'ERROR', 'code': response.status_code}
            
    except Exception as e:
        logger.error(f"❌ Excepción demanda: {e}")
        return {'status': 'EXCEPTION', 'error': str(e)}

def test_historical_data(token):
    """Prueba descarga de datos históricos (2020)"""
    logger.info("🔍 Probando descarga datos históricos 2020...")
    
    headers = {
        'Accept': 'application/json; application/vnd.esios-api-v1+json',
        'Content-Type': 'application/json',
        'Host': 'api.esios.ree.es',
        'Authorization': f'Token token={token}'
    }
    
    try:
        # Probar solo 1 día de enero 2020
        url = "https://api.esios.ree.es/indicators/600"
        params = {
            'start_date': '2020-01-01T00:00',
            'end_date': '2020-01-01T23:59'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        logger.info(f"📊 Histórico 2020 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            values = data.get('indicator', {}).get('values', [])
            logger.info(f"✅ Datos históricos 2020 accesibles: {len(values)} valores")
            return {'status': 'SUCCESS', 'values_count': len(values)}
        else:
            logger.error(f"❌ Sin acceso a datos históricos: {response.status_code}")
            return {'status': 'ERROR', 'code': response.status_code}
            
    except Exception as e:
        logger.error(f"❌ Error históricos: {e}")
        return {'status': 'EXCEPTION', 'error': str(e)}

def main():
    """Función principal"""
    print("🔍 PRUEBA DESCARGA OMIE CON TOKEN ACTUAL")
    print("=" * 60)
    
    logger.info("🚀 Verificando capacidades de descarga OMIE...")
    
    token = get_esios_token()
    if not token:
        logger.error("❌ Token no disponible")
        return
    
    logger.info(f"🔑 Token: {token[:10]}...{token[-4:]}")
    
    # Ejecutar pruebas
    omie_result = test_omie_price_download(token, days_back=7)
    demand_result = test_demand_download(token, days_back=3)
    historical_result = test_historical_data(token)
    
    # RESUMEN FINAL
    print("\n" + "=" * 60)
    print("📋 RESUMEN CAPACIDADES TOKEN")
    print("=" * 60)
    
    logger.info("🎯 Resultados de descarga:")
    
    # OMIE
    if omie_result['status'] == 'SUCCESS':
        logger.info(f"   ✅ PRECIOS OMIE: Funciona ({omie_result['values_count']} valores)")
        logger.info(f"      → Indicador: {omie_result['indicator_name']}")
    else:
        logger.info(f"   ❌ PRECIOS OMIE: {omie_result['status']}")
    
    # Demanda
    if demand_result['status'] == 'SUCCESS':
        logger.info(f"   ✅ DEMANDA: Funciona ({demand_result['values_count']} valores)")
        logger.info(f"      → Indicador: {demand_result['indicator_name']}")
    else:
        logger.info(f"   ❌ DEMANDA: {demand_result['status']}")
    
    # Históricos
    if historical_result['status'] == 'SUCCESS':
        logger.info(f"   ✅ DATOS 2020: Accesibles ({historical_result['values_count']} valores)")
    else:
        logger.info(f"   ❌ DATOS 2020: {historical_result['status']}")
    
    # CONCLUSIONES
    print("\n🎯 CONCLUSIONES:")
    
    if omie_result['status'] == 'SUCCESS':
        print("✅ TOKEN SIGUE FUNCIONANDO para precios OMIE")
        print("   → Podemos continuar descargando precios de mercado")
        
        if historical_result['status'] == 'SUCCESS':
            print("✅ ACCESO A DATOS HISTÓRICOS 2020 disponible")
            print("   → Podemos completar huecos históricos")
    
    if demand_result['status'] == 'SUCCESS':
        print("✅ DEMANDA PENINSULAR disponible")
        print("   → Alternativa a demanda nacional (indicador 1293)")
    
    if (omie_result['status'] != 'SUCCESS' and 
        demand_result['status'] != 'SUCCESS' and 
        historical_result['status'] != 'SUCCESS'):
        print("❌ TOKEN COMPLETAMENTE INÚTIL")
        print("   → Necesario solicitar nuevo token a REE")
    else:
        print("🔄 TOKEN PARCIALMENTE FUNCIONAL")
        print("   → Adaptar scripts para usar solo indicadores disponibles")
    
    print(f"\n📊 Verificación completada")

if __name__ == "__main__":
    main()
