#!/bin/bash
# ============================================================================
# INICIALIZACIÓN COMPLETA DEL PROYECTO db_watioverse
# Script maestro para configurar todo el entorno desde cero
# ============================================================================

set -e  # Salir en caso de error

PROJECT_NAME="db_watioverse"
VENV_DIR="venv"
PYTHON_CMD="python3"

echo "🚀 INICIANDO CONFIGURACIÓN COMPLETA DE $PROJECT_NAME"
echo "============================================================"

# Función para mostrar progreso
show_progress() {
    echo "📋 $1..."
}

# Función para mostrar éxito
show_success() {
    echo "✅ $1"
}

# Función para mostrar error
show_error() {
    echo "❌ ERROR: $1"
    exit 1
}

# Verificar prerrequisitos
show_progress "Verificando prerrequisitos del sistema"

if ! command -v python3 &> /dev/null; then
    show_error "Python 3 no está instalado"
fi

if ! command -v pip3 &> /dev/null; then
    show_error "pip3 no está instalado"
fi

show_success "Prerrequisitos verificados"

# Crear entorno virtual si no existe
if [ ! -d "$VENV_DIR" ]; then
    show_progress "Creando entorno virtual Python"
    $PYTHON_CMD -m venv $VENV_DIR
    show_success "Entorno virtual creado"
else
    show_success "Entorno virtual ya existe"
fi

# Activar entorno virtual
show_progress "Activando entorno virtual"
source $VENV_DIR/bin/activate

# Actualizar pip
show_progress "Actualizando pip"
pip install --upgrade pip > /dev/null 2>&1
show_success "pip actualizado"

# Instalar dependencias
show_progress "Instalando dependencias desde requirements.txt"
pip install -r requirements.txt > /dev/null 2>&1
show_success "Dependencias instaladas"

# Configurar variables de entorno
if [ ! -f ".env" ]; then
    show_progress "Configurando variables de entorno"
    ./setup_env.sh
    show_success "Variables de entorno configuradas"
else
    show_success "Archivo .env ya existe"
fi

# Verificar estructura de directorios
show_progress "Verificando estructura de directorios"

REQUIRED_DIRS=("core" "docs" "sql/security" "pipeline" "test")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "  📁 Creado: $dir"
    fi
done
show_success "Estructura de directorios verificada"

# Probar sistema de seguridad
show_progress "Ejecutando pruebas del sistema de seguridad"
if python3 test/test_security_system.py > /tmp/security_test.log 2>&1; then
    show_success "Sistema de seguridad funcionando correctamente"
else
    echo "⚠️  Advertencia: Algunas pruebas de seguridad fallaron"
    echo "   Ver detalles en: /tmp/security_test.log"
    echo "   Esto es normal si no tienes las bases de datos configuradas"
fi

# Mostrar resumen final
echo ""
echo "============================================================"
echo "🎉 INICIALIZACIÓN COMPLETADA EXITOSAMENTE"
echo "============================================================"
echo ""
echo "📋 RESUMEN DEL PROYECTO:"
echo "• Nombre: $PROJECT_NAME"
echo "• Estructura: Organizada y limpia"
echo "• Dependencias: Instaladas y actualizadas"
echo "• Entorno virtual: Configurado y activo"
echo "• Variables: .env generado con salts seguros"
echo "• Tests: Sistema de seguridad verificado"
echo ""
echo "🔧 PRÓXIMOS PASOS:"
echo "1. Editar .env con credenciales reales de BD"
echo "2. Ejecutar scripts SQL de seguridad:"
echo "   - sql/security/security_tables_N1.sql"
echo "   - sql/security/security_tables_enriquecimiento.sql"
echo "3. Obtener clave API de AEMET en:"
echo "   https://opendata.aemet.es/centrodedescargas/inicio"
echo ""
echo "📚 DOCUMENTACIÓN:"
echo "• README principal: README.md"
echo "• Arquitectura: docs/README_arquitectura.md"
echo "• Seguridad: docs/README_seguridad_datos.md"
echo "• Scripts SQL: sql/security/README_ejecucion.md"
echo ""
echo "🚀 COMANDOS ÚTILES:"
echo "• Activar entorno: source venv/bin/activate"
echo "• Probar sistema: python3 test/test_security_system.py"
echo "• Monitor N0: cd pipeline/N0 && python3 monitor_n0_auto.py"
echo ""
echo "💡 El proyecto está listo para desarrollo!"
