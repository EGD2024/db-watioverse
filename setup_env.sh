#!/bin/bash
# ============================================================================
# SCRIPT DE CONFIGURACIÓN AUTOMÁTICA - db_watioverse
# Genera archivo .env con configuración por defecto para desarrollo local
# ============================================================================

echo "🚀 CONFIGURANDO ENTORNO db_watioverse..."
echo "=" * 60

# Verificar si ya existe .env
if [ -f ".env" ]; then
    echo "⚠️  Archivo .env ya existe. ¿Sobrescribir? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ Configuración cancelada"
        exit 1
    fi
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backup creado: .env.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Generar salts aleatorios
echo "🔐 Generando salts de seguridad..."
SALT_NIF=$(openssl rand -hex 32)
SALT_DIR=$(openssl rand -hex 32)
SALT_CUPS=$(openssl rand -hex 32)

# Crear archivo .env
cat > .env << EOF
# =============================================================================
# CONFIGURACIÓN AUTOMÁTICA - db_watioverse
# Generado: $(date)
# =============================================================================

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE BASES DE DATOS PRINCIPALES
# -----------------------------------------------------------------------------
# eSCORE - Bases de datos del motor de scoring
DB_ESCORE_PESOS_HOST=localhost
DB_ESCORE_PESOS_PORT=5432
DB_ESCORE_PESOS_NAME=db_eSCORE_pesos
DB_ESCORE_PESOS_USER=postgres
DB_ESCORE_PESOS_PASSWORD=tu_password_aqui

DB_ESCORE_MASTER_HOST=localhost
DB_ESCORE_MASTER_PORT=5432
DB_ESCORE_MASTER_NAME=db_eSCORE_master
DB_ESCORE_MASTER_USER=postgres
DB_ESCORE_MASTER_PASSWORD=tu_password_aqui

# Pipeline N0-N5 - Capas de procesamiento
DB_N0_HOST=localhost
DB_N0_PORT=5432
DB_N0_NAME=db_N0
DB_N0_USER=postgres
DB_N0_PASSWORD=tu_password_aqui

DB_N1_HOST=localhost
DB_N1_PORT=5432
DB_N1_NAME=db_N1
DB_N1_USER=postgres
DB_N1_PASSWORD=tu_password_aqui

DB_N2_HOST=localhost
DB_N2_PORT=5432
DB_N2_NAME=db_N2
DB_N2_USER=postgres
DB_N2_PASSWORD=tu_password_aqui

# Bases auxiliares críticas
DB_CATASTRO_HOST=localhost
DB_CATASTRO_PORT=5432
DB_CATASTRO_NAME=db_catastro
DB_CATASTRO_USER=postgres
DB_CATASTRO_PASSWORD=tu_password_aqui

DB_ENRIQUECIMIENTO_HOST=localhost
DB_ENRIQUECIMIENTO_PORT=5432
DB_ENRIQUECIMIENTO_NAME=db_enriquecimiento
DB_ENRIQUECIMIENTO_USER=postgres
DB_ENRIQUECIMIENTO_PASSWORD=tu_password_aqui

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE SEGURIDAD - SALTS GENERADOS AUTOMÁTICAMENTE
# -----------------------------------------------------------------------------
HASH_SALT_NIF_CIF=$SALT_NIF
HASH_SALT_DIRECCION=$SALT_DIR
HASH_SALT_CUPS=$SALT_CUPS

# TTL para datos temporales (en segundos)
TTL_ENRIQUECIMIENTO_CACHE=86400  # 24 horas
TTL_AUDIT_LOG=2592000            # 30 días

# -----------------------------------------------------------------------------
# CONFIGURACIÓN APIS EXTERNAS - DESARROLLO
# -----------------------------------------------------------------------------
# AEMET - Clima (solicitar clave en opendata.aemet.es)
AEMET_API_KEY=tu_clave_aemet_aqui
AEMET_BASE_URL=https://opendata.aemet.es/opendata/api

# CATASTRO - Datos catastrales
CATASTRO_BASE_URL=http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx
CATASTRO_TIMEOUT=10

# Mercados energéticos
OMIE_BASE_URL=https://www.omie.es/es/file-download
OMIE_TIMEOUT=15
REE_BASE_URL=https://apidatos.ree.es/es/datos
REE_TIMEOUT=15

# Rate limiting (requests por minuto)
RATE_LIMIT_AEMET=60
RATE_LIMIT_CATASTRO=30
RATE_LIMIT_OMIE=20
RATE_LIMIT_REE=40

# -----------------------------------------------------------------------------
# CONFIGURACIÓN ENTORNO DE DESARROLLO
# -----------------------------------------------------------------------------
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Timeouts
DEFAULT_API_TIMEOUT=10
DEFAULT_DB_TIMEOUT=30
EOF

echo "✅ Archivo .env creado con configuración por defecto"
echo ""
echo "📋 PASOS SIGUIENTES:"
echo "1. Editar .env y configurar passwords reales de BD"
echo "2. Obtener clave AEMET en: https://opendata.aemet.es/centrodedescargas/inicio"
echo "3. Ejecutar: source venv/bin/activate"
echo "4. Probar: python3 test/test_security_system.py"
echo ""
echo "🔐 SALTS DE SEGURIDAD GENERADOS:"
echo "- NIF/CIF: ${SALT_NIF:0:16}..."
echo "- Direcciones: ${SALT_DIR:0:16}..."
echo "- CUPS: ${SALT_CUPS:0:16}..."
echo ""
echo "🎯 Configuración completada exitosamente"
EOF
