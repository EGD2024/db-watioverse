# 🌊 db_watioverse - Ecosistema de Datos Energéticos

![Versión](https://img.shields.io/badge/versión-1.0.0-blue)
![Estado](https://img.shields.io/badge/estado-producción-green)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Pipeline](https://img.shields.io/badge/pipeline-N0→N1-purple)
![Integración](https://img.shields.io/badge/integración-eSCORE-orange)

**Repositorio de capas de datos para el procesamiento y análisis de información energética con integración híbrida al Motor eSCORE**

**Última actualización:** 6 de Septiembre de 2025
**Actualizado por:** Sistema Integración Híbrida
**Proyecto interno de Energy Green Data**

---

## 📑 Tabla de Contenidos

- [Documentación Especializada](#-documentación-especializada)
- [Integración Híbrida con eSCORE](#-integración-híbrida-con-escore)
- [Estructura del Repositorio](#-estructura-del-repositorio)
- [Pipeline N0→N1](#-pipeline-n0n1)
- [Configuración del Entorno](#-configuración-del-entorno)
- [Capa N0 - Datos en Bruto](#-capa-n0---datos-en-bruto)
- [Flujo de Datos](#-flujo-de-datos)

---

## 📑 Documentación Especializada

- 🏗️ **[Arquitectura del Sistema](docs/README_arquitectura.md)** - Detalles técnicos de las 23 bases de datos especializadas
- 🔒 **[Seguridad de Datos](docs/README_seguridad_datos.md)** - Protección RGPD, hashing y flujos de anonimización
- 💾 **[Base de Datos N0](N0/README_N0.md)** - Capa de datos en bruto y sistema de versionado
- ⚡ **[Base de Datos N1](N1/README_N1.md)** - Capa de enriquecimiento y pipeline automático

---

## 🔗 Integración Híbrida con eSCORE

El ecosistema `db_watioverse` se integra con el Motor eSCORE mediante una arquitectura híbrida que separa responsabilidades y optimiza el flujo de datos energéticos:

### Responsabilidades de db_watioverse

- **Pipeline N0→N1**: Transformación automática de datos brutos en datos enriquecidos
- **Validación de Integridad**: Detección automática de campos faltantes o inconsistentes
- **Cuestionarios Dinámicos**: Generación inteligente de preguntas para completar datos críticos
- **Monitoreo Automático**: Procesamiento en tiempo real de nuevos archivos JSON

### Métricas de Calidad Reales

Basado en análisis masivo de archivos N0 reales:
- **Calidad de Datos**: 98.7/100
- **Campos Críticos Completos**: 85.7%
- **Campo Más Faltante**: CUPS (14.3% de casos)
- **Tiempo Promedio Pipeline**: < 2 segundos por archivo

### Flujo de Integración

```mermaid
graph TD
    A[Archivo N0 Detectado] --> B[Pipeline N0→N1]
    B --> C[Validación Integridad]
    C --> D{¿Datos Suficientes?}
    D -->|SÍ| E[Envío a eSCORE]
    D -->|NO| F[Cuestionario Dinámico]
    F --> G[Cliente Completa Datos]
    G --> H[Reintegración Pipeline]
    H --> E
    E --> I[Score Energético]
    
    style A fill:#2C3E50,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style B fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style D fill:#F39C12,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style I fill:#16A085,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

## 🔄 Pipeline N0→N1

El pipeline N0→N1 es el núcleo de la transformación de datos, implementado con validación automática y enriquecimiento inteligente:

### Componentes Principales

- **`shared/field_mappings.py`**: Mapeos de campos N0→N1 basados en estructura real
- **`shared/n0_cleaner.py`**: Eliminación de metadatos de extracción
- **`shared/enrichment_engine.py`**: Motor de enriquecimiento de datos
- **`shared/integrity_validator.py`**: Validador de integridad N0→N1
- **`N1/n1_generator.py`**: Orquestador principal del pipeline

### Proceso de Transformación

1. **Limpieza**: Eliminación de metadatos de extracción del JSON N0
2. **Mapeo**: Transformación de estructura anidada N0 a estructura plana N1
3. **Enriquecimiento**: Adición de datos calculados y externos
4. **Validación**: Verificación de integridad y completitud
5. **Guardado**: Almacenamiento en `Data_out/` con sufijo N1

## 📑 Estructura del Repositorio

```
db_watioverse/
├── N0/                    # 💾 Capa de datos en bruto
│   ├── data_versioning/   # 🔄 Herramientas de versionado
│   ├── insert_N0.py      # 📥 Insertador de datos
│   ├── monitor_n0_auto.py # 🔍 Monitor automático
│   └── README.md         # 📋 Documentación N0
├── N1/                   # ⚡ Capa de enriquecimiento
│   ├── n1_generator.py   # 🔄 Generador pipeline N0→N1
│   ├── insert_N1.py     # 📥 Insertador datos N1
│   ├── monitor_n1_auto.py # 🔍 Monitor automático N1
│   └── README.md        # 📋 Documentación N1
├── N2/                  # 📊 Capa de análisis
├── N3/                  # 🎯 Capa de métricas avanzadas
├── shared/              # 🔧 Componentes compartidos
│   ├── field_mappings.py # 🗺️ Mapeos N0→N1
│   ├── n0_cleaner.py    # 🧹 Limpieza metadatos
│   ├── enrichment_engine.py # 💎 Motor enriquecimiento
│   ├── integrity_validator.py # ✅ Validador integridad
│   └── batch_analysis.py # 📈 Análisis masivo
├── venv/                # 🐍 Entorno virtual Python
└── activate_env.sh      # 🚀 Script de activación
```

## 🚀 Configuración del Entorno

### Activar Entorno Virtual

```bash
# Opción 1: Script automático
./activate_env.sh

# Opción 2: Manual
source venv/bin/activate
```

### Dependencias Instaladas

- **watchdog==3.0.0** - Monitoreo de sistema de archivos
- **requests** - Comunicación HTTP con eSCORE
- **Python 3.8+** - Entorno de ejecución

## 💾 Capa N0 - Datos en Bruto

La capa N0 almacena datos extraídos directamente de facturas energéticas sin procesamiento adicional.

### Características Principales

- **14 tablas especializadas** con estructura completa
- **Sistema de versionado** automático
- **Monitor en tiempo real** para nuevos archivos
- **Validación eSCORE** integrada

### Uso Rápido

```bash
# Activar entorno
source venv/bin/activate

# Pipeline completo N0→N1 (recomendado)
cd N0
python3 monitor_n0_auto.py  # Dispara automáticamente pipeline N1

# Inserción manual N0 (modo prueba)
cd N0
python3 insert_N0.py

# Generación manual N1 desde N0
cd N1
python3 n1_generator.py

# Análisis masivo de calidad
cd shared
python3 batch_analysis.py
```

## 🔄 Flujo de Datos

```mermaid
graph TD
    A[Facturas PDF] --> B[Motor Extracción]
    B --> C[JSONs Data_out]
    C --> D[N0 - Datos Brutos]
    D --> E[Pipeline N0→N1]
    E --> F[Validación Integridad]
    F --> G{¿Completo?}
    G -->|SÍ| H[N1 - Enriquecimiento]
    G -->|NO| I[Cuestionario Dinámico]
    I --> J[Completar Datos]
    J --> H
    H --> K[eSCORE Motor]
    K --> L[Score Energético]
    
    style D fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style E fill:#F39C12,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style H fill:#9B59B6,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style K fill:#E74C3C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style L fill:#16A085,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

## ⚙️ Configuración de Desarrollo

### Variables de Entorno

```bash
# Base de datos (configurar según necesidad)
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=usuario
export DB_PASSWORD=password
```

### Estructura de Archivos N0

Los archivos JSON deben seguir el patrón:
```
N0_[CUPS]_[TIMESTAMP].json
```

Ejemplo: `N0_ES0022000008342444ND1P_20250214_211038.json`

---

**Documento Confidencial y Propiedad de Energy Green Data.**

*La información contenida en este documento es de carácter reservado y para uso exclusivo de la organización. Queda prohibida su reproducción, distribución o comunicación pública, total o parcial, sin autorización expresa.*
