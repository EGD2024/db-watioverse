#!/bin/bash
# Script de activación del entorno virtual db_watioverse

echo "🐍 Activando entorno virtual db_watioverse..."
source /Users/vagalumeenergiamovil/PROYECTOS/Entorno/motores/db_watioverse/venv/bin/activate

echo "✅ Entorno virtual activado"
echo "📦 Paquetes instalados:"
pip list | grep -E "(watchdog|psycopg2|pandas)"

echo ""
echo "🚀 Para usar el monitor N0:"
echo "   cd N0"
echo "   python3 monitor_n0_auto.py"
echo ""
echo "🔧 Para inserción manual N0:"
echo "   cd N0"
echo "   python3 insert_N0.py"
