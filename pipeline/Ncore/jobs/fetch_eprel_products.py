#!/usr/bin/env python3
"""
Job de ingesta EPREL: consulta eficiencia energética de productos.
Requiere credenciales OAuth2 (client_id, client_secret) en variables de entorno.
Sin fallbacks: si falta auth o la API falla, lanza excepción.

Variables de entorno requeridas:
  EPREL_CLIENT_ID     - Client ID proporcionado por EPREL
  EPREL_CLIENT_SECRET - Client Secret
  EPREL_TOKEN_URL     - URL del endpoint OAuth2 (default: https://webgate.ec.europa.eu/uas/oauth/token)
  EPREL_API_BASE      - Base URL de la API (default: https://eprel.ec.europa.eu/api/products/v2)

Uso:
  --model MODEL       Buscar por modelo específico
  --ean EAN           Buscar por código EAN
  --limit N           Máximo de productos a procesar (default: 100)
  --input CSV         Archivo CSV con columna 'model' o 'ean'
"""
import os
import sys
import json
import csv
import time
import argparse
from datetime import datetime
from typing import List, Dict, Optional

import requests
import psycopg2

DB = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'admin',
    'dbname': 'db_Ncore',
}

# Variables de entorno para auth
CLIENT_ID = os.getenv('EPREL_CLIENT_ID')
CLIENT_SECRET = os.getenv('EPREL_CLIENT_SECRET')
TOKEN_URL = os.getenv('EPREL_TOKEN_URL', 'https://webgate.ec.europa.eu/uas/oauth/token')
API_BASE = os.getenv('EPREL_API_BASE', 'https://eprel.ec.europa.eu/api/products/v2')

if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError('EPREL_CLIENT_ID y EPREL_CLIENT_SECRET son obligatorios')


class EPRELClient:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.token_expires = 0
    
    def authenticate(self):
        """Obtener token OAuth2"""
        data = {
            'grant_type': 'client_credentials',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }
        r = self.session.post(TOKEN_URL, data=data, timeout=30)
        r.raise_for_status()
        token_data = r.json()
        self.token = token_data['access_token']
        self.token_expires = time.time() + token_data.get('expires_in', 3600) - 60
    
    def ensure_auth(self):
        """Renovar token si expira"""
        if not self.token or time.time() >= self.token_expires:
            self.authenticate()
    
    def search_product(self, model: str = None, ean: str = None) -> Optional[Dict]:
        """Buscar producto por modelo o EAN"""
        self.ensure_auth()
        
        headers = {'Authorization': f'Bearer {self.token}'}
        params = {}
        
        if model:
            params['model'] = model
        elif ean:
            params['ean'] = ean
        else:
            raise ValueError('Debe especificar model o ean')
        
        r = self.session.get(f'{API_BASE}/search', params=params, headers=headers, timeout=30)
        
        if r.status_code == 404:
            return None
        
        r.raise_for_status()
        return r.json()
    
    def get_product_details(self, product_id: str) -> Dict:
        """Obtener detalles completos del producto"""
        self.ensure_auth()
        
        headers = {'Authorization': f'Bearer {self.token}'}
        r = self.session.get(f'{API_BASE}/products/{product_id}', headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()


def create_tables(conn):
    """Crear tablas si no existen"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS core_eprel_products (
            id SERIAL PRIMARY KEY,
            product_id VARCHAR(100) UNIQUE NOT NULL,
            model VARCHAR(200),
            ean VARCHAR(20),
            brand VARCHAR(100),
            product_group VARCHAR(50),
            energy_class VARCHAR(10),
            energy_consumption_annual NUMERIC(10,2),
            efficiency_index NUMERIC(10,2),
            payload JSONB,
            fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_eprel_model ON core_eprel_products (model);
        CREATE INDEX IF NOT EXISTS idx_eprel_ean ON core_eprel_products (ean);
        CREATE INDEX IF NOT EXISTS idx_eprel_class ON core_eprel_products (energy_class);
    """)
    conn.commit()
    cursor.close()


def upsert_product(conn, data: Dict):
    """Guardar producto en BD"""
    cursor = conn.cursor()
    
    # Extraer campos principales del payload
    product_id = data.get('productId') or data.get('id')
    if not product_id:
        raise ValueError('productId no encontrado en respuesta')
    
    model = data.get('model') or data.get('modelName')
    ean = data.get('ean') or data.get('eanCode')
    brand = data.get('brand') or data.get('supplierName')
    product_group = data.get('productGroup') or data.get('category')
    energy_class = data.get('energyClass') or data.get('energyEfficiencyClass')
    energy_consumption = data.get('energyConsumptionAnnual') or data.get('annualEnergyConsumption')
    efficiency_index = data.get('efficiencyIndex') or data.get('eei')
    
    cursor.execute("""
        INSERT INTO core_eprel_products (
            product_id, model, ean, brand, product_group,
            energy_class, energy_consumption_annual, efficiency_index, payload
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (product_id) DO UPDATE SET
            model = EXCLUDED.model,
            ean = EXCLUDED.ean,
            brand = EXCLUDED.brand,
            product_group = EXCLUDED.product_group,
            energy_class = EXCLUDED.energy_class,
            energy_consumption_annual = EXCLUDED.energy_consumption_annual,
            efficiency_index = EXCLUDED.efficiency_index,
            payload = EXCLUDED.payload,
            fecha_carga = CURRENT_TIMESTAMP
    """, (
        product_id, model, ean, brand, product_group,
        energy_class, energy_consumption, efficiency_index,
        json.dumps(data)
    ))
    
    cursor.close()


def load_from_csv(filepath: str, column: str) -> List[str]:
    """Cargar lista de modelos/EANs desde CSV"""
    items = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if column in row and row[column]:
                items.append(row[column].strip())
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', help='Buscar por modelo específico')
    parser.add_argument('--ean', help='Buscar por código EAN')
    parser.add_argument('--limit', type=int, default=100, help='Máximo de productos')
    parser.add_argument('--input', help='Archivo CSV con modelos/EANs')
    args = parser.parse_args()
    
    # Conectar BD
    conn = psycopg2.connect(**DB)
    create_tables(conn)
    
    # Cliente EPREL
    client = EPRELClient()
    
    # Determinar lista de búsqueda
    searches = []
    
    if args.input:
        # Detectar columna (model o ean)
        if 'model' in args.input.lower():
            models = load_from_csv(args.input, 'model')
            searches = [('model', m) for m in models[:args.limit]]
        elif 'ean' in args.input.lower():
            eans = load_from_csv(args.input, 'ean')
            searches = [('ean', e) for e in eans[:args.limit]]
        else:
            raise ValueError('CSV debe tener columna "model" o "ean"')
    elif args.model:
        searches = [('model', args.model)]
    elif args.ean:
        searches = [('ean', args.ean)]
    else:
        raise ValueError('Especifique --model, --ean o --input')
    
    # Procesar búsquedas
    found = 0
    errors = 0
    
    for search_type, search_value in searches:
        try:
            # Buscar producto
            if search_type == 'model':
                result = client.search_product(model=search_value)
            else:
                result = client.search_product(ean=search_value)
            
            if not result:
                print(f"⚠️ No encontrado: {search_type}={search_value}")
                continue
            
            # Si hay múltiples resultados, tomar el primero
            products = result.get('products', [result])
            
            for product in products[:1]:  # Solo primer resultado
                # Obtener detalles completos si hay ID
                product_id = product.get('productId') or product.get('id')
                if product_id:
                    details = client.get_product_details(product_id)
                    upsert_product(conn, details)
                else:
                    upsert_product(conn, product)
                
                found += 1
                print(f"✅ {search_type}={search_value} → {product_id}")
            
            # Respetar rate limits
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Error con {search_type}={search_value}: {e}")
            errors += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Resumen: {found} productos encontrados, {errors} errores")


if __name__ == '__main__':
    main()
