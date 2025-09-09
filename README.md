<p align="center">
  <img src="docs/assets/EGD.png" alt="Energy Green Data" width="400"/>
</p>

# db_watioverse - Ecosistema de Datos Energéticos

![Versión](https://img.shields.io/badge/versión-3.0.0-blue)
![Estado](https://img.shields.io/badge/estado-producción-green)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Pipeline](https://img.shields.io/badge/pipeline-N0→N1→N2→N3-purple)
![Bases](https://img.shields.io/badge/bases_de_datos-28-orange)
![MCP](https://img.shields.io/badge/MCP-28_conectadas-green)
![APIs](https://img.shields.io/badge/APIs-4/8_funcionales-yellow)

**Repositorio de capas de datos para el procesamiento y análisis de información energética con integración híbrida al Motor eSCORE**

**Última actualización:** 9 de Septiembre de 2025
**Actualizado por:** Auditoría MCP Exhaustiva
**Proyecto interno de Energy Green Data**

---

## Tabla de Contenidos

- [Documentación Especializada](#documentación-especializada)
- [Integración Híbrida con eSCORE](#integración-híbrida-con-escore)
- [Estructura del Repositorio](#estructura-del-repositorio)
- [Pipeline N0→N1](#pipeline-n0n1)
- [Configuración del Entorno](#configuración-del-entorno)
- [Capa N0 - Datos en Bruto](#capa-n0---datos-en-bruto)
- [Flujo de Datos](#flujo-de-datos)

---

## Documentación Especializada

- **[Arquitectura del Sistema](docs/README_arquitectura.md)** - 28 bases de datos MCP validadas con 183+ tablas activas
- **[APIs Externas](docs/README_apis_externas.md)** - Estado y configuración de 8 APIs (4 funcionales, 4 bloqueadas)
- **[Seguridad de Datos](docs/README_seguridad_datos.md)** - Protección RGPD, hashing y flujos de anonimización
- **[Actualizaciones Automáticas](docs/README_actualizaciones_automaticas.md)** - Pipeline y scheduling de datos

---

## Integración Híbrida con eSCORE

El ecosistema `db_watioverse` se integra con el Motor eSCORE mediante una arquitectura híbrida que separa responsabilidades y optimiza el flujo de datos energéticos:

### Responsabilidades de db_watioverse

- **Pipeline N0→N1**: Transformación automática de datos brutos en datos enriquecidos
- **Validación de Integridad**: Detección automática de campos faltantes o inconsistentes
- **Cuestionarios Dinámicos**: Generación inteligente de preguntas para completar datos críticos
- **Monitoreo Automático**: Procesamiento en tiempo real de nuevos archivos JSON

### Métricas del Sistema - Auditoría MCP Real

| Métrica | Valor MCP | Estado | Descripción |
|---------|-----------|--------|--------------|
| **Bases de Datos** | 28/28 | ✅ 100% | Conectadas vía MCP |
| **Tablas Activas** | 183+ | ✅ OPERATIVO | Inventario completo validado |
| **Pipeline N0→N3** | Funcional | ✅ COMPLETO | Scoring end-to-end |
| **APIs Funcionales** | 4/8 | ⚠️ 50% | REE, Open-Meteo, Nominatim, PVGIS |
| **Zonas Climáticas** | 4,087/11,830 | 🔄 35% | En progreso de carga |
| **Performance** | <2ms | ✅ SLA | Consultas críticas optimizadas |

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

## Pipeline Completo N0→N1→N2→N3→N4

El pipeline completo procesa datos desde la extracción hasta los scores finales:

### Componentes Principales

- **`shared/field_mappings.py`**: Mapeos de campos N0→N1 basados en estructura real
- **`shared/n0_cleaner.py`**: Eliminación de metadatos de extracción
- **`shared/enrichment_engine.py`**: Motor de enriquecimiento de datos
- **`shared/integrity_validator.py`**: Validador de integridad N0→N1
- **`N1/n1_generator.py`**: Orquestador principal del pipeline

### Inventario MCP por Capas - Datos Reales

| Capa | Base de Datos | Tablas | Estado MCP | Función |
|------|---------------|--------|------------|---------|
| **Pipeline** | db_N0 | 15 | ✅ ACTIVA | Datos brutos extraídos |
| | db_N1 | 13 | ✅ ACTIVA | Datos base confirmados |
| | db_N2 | 13 | ✅ ACTIVA | Enriquecimiento por ámbito |
| | db_N3 | 7 | ✅ ACTIVA | Scoring final |
| **Maestros** | db_Ncore | 27 | ✅ ACTIVA | Referencia (4,087 zonas) |
| | db_sistema_electrico | 29 | ✅ ACTIVA | OMIE, PVPC |
| | db_territorio | 7 | ✅ ACTIVA | 17,009 CPs |
| **eSCORE** | db_eSCORE_master | 9 | ✅ ACTIVA | Benchmarking |
| | db_eSCORE_pesos | 29 | ✅ ACTIVA | Configuración |
| **Gaps** | db_N4, db_N5 | 0 | ❌ VACÍAS | No implementadas |

## Estructura del Repositorio

```
db_watioverse/
├── README.md            # Documentación principal
├── .env.example         # Plantilla configuración
├── setup_env.sh         # Script configuración automática
├── requirements.txt     # Dependencias Python
├── activate_env.sh      # Script de activación
├── venv/               # Entorno virtual Python
│
├── docs/               # Documentación especializada
│   ├── README_arquitectura.md     # 28 bases de datos MCP
│   ├── README_apis_externas.md    # Estado 8 APIs externas
│   ├── README_seguridad_datos.md  # Protección RGPD
│   └── assets/         # Logos y diagramas
│
├── core/               # Infraestructura central
│   ├── __init__.py     # Módulo principal
│   ├── db_connections.py          # Gestor 23 conexiones BD
│   ├── data_security.py           # Hashing + versionado
│   └── external_apis.py           # APIs AEMET/Catastro/OMIE
│
├── sql/                # Scripts SQL organizados
│   └── security/       # Scripts de seguridad
│       ├── security_tables_N1.sql
│       ├── security_tables_enriquecimiento.sql
│       └── README_ejecucion.md
│
├── pipeline/           # Pipeline de datos
│   ├── N0/            # Capa datos brutos
│   ├── N1/            # Capa enriquecimiento
│   ├── N2/, N3/       # Capas futuras
│   └── shared/        # Componentes compartidos
│
└── test/              # Tests del sistema
    └── test_security_system.py   # Verificación seguridad
```

## Configuración del Entorno

### Activar Entorno Virtual

```bash
# Opción 1: Script automático
./activate_env.sh

# Opción 2: Manual
source venv/bin/activate
```

### Configuración Rápida

```bash
# 1. Configuración automática completa
./setup_env.sh

# 2. Activar entorno e instalar dependencias
source venv/bin/activate
pip install -r requirements.txt

# 3. Probar sistema de seguridad
python3 test/test_security_system.py
```

### Dependencias Instaladas

- **psycopg2-binary>=2.9.0** - Conexión PostgreSQL
- **python-dotenv>=1.0.0** - Variables de entorno
- **requests>=2.31.0** - APIs externas
- **watchdog==3.0.0** - Monitoreo de archivos

## Descripción de Capas

### Ncore - Datos Maestros Centralizados (MCP Validado)
- **27 tablas** de referencia sin PII
- Comercializadoras, distribuidoras, tarifas
- **4,087 zonas climáticas** (35% completado)
- Precios OMIE, factores CO2, PVPC
- Cache centralizado para consultas frecuentes
- **Performance <2ms** en consultas críticas

### N0 - Datos en Bruto (MCP Validado)
- **15 tablas** especializadas por tipo de dato
- **27 inserts confirmados** (client, contract, invoice, metadata)
- Monitor automático con detección en tiempo real
- Sistema de versionado y control de calidad

### N1 - Enriquecimiento y Validación (MCP Validado)
- **13 tablas** base confirmadas
- Pipeline N0→N1 automático funcional
- Hashing SHA-256 + Salt para datos sensibles
- Versionado de cambios de clientes

### N2 - Enriquecimiento por Ámbitos (MCP Validado)
- **13 tablas** en esquemas n2_electricidad, n2_agua, n2_gas, etc.
- Datos enriquecidos por ámbito energético
- Integración con APIs funcionales (4/8 activas)
- Superficie construida para métricas kWh/m²
- Contexto climático y catastral

### N3 - Scoring Final (MCP Validado)
- **7 tablas** de scores y rankings
- Datos estructurados para eSCORE
- Benchmarking y evolución temporal
- Contexto optimizado para LLM

### N4 y N5 - No Implementadas (MCP Validado)
- **0 tablas** en ambas bases
- Funcionalidad futura planificada
- No bloquean operación actual
- Reservadas para expansión

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

## Flujo de Datos Completo

```mermaid
graph TD
    A[Facturas PDF] --> B[Motor Extracción]
    B --> C[JSONs Data_out]
    C --> D[N0 - Datos Brutos<br/>15 tablas]
    D --> E[N1 - Validación<br/>18 tablas]
    E --> F[N2 - Enriquecimiento<br/>13 tablas]
    F --> G[N3 - Entrada Scoring<br/>16 tablas]
    G --> H[Motor eSCORE v2.0]
    H --> I[N4 - Scores Finales<br/>7 tablas]
    
    subgraph "APIs Integradas"
        J[Catastro OVC]
        K[Open-Meteo]
        L[PVGIS]
        M[OMIE]
        N[Nominatim]
    end
    
    subgraph "DB Core"
        CORE[Datos Maestros<br/>10 tablas]
    end
    
    J --> F
    K --> F
    L --> F
    M --> F
    N --> F
    CORE --> H
    CORE --> I
    
    style D fill:#2C3E50,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style E fill:#34495E,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style F fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style G fill:#F39C12,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style H fill:#9B59B6,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style I fill:#16A085,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

## Configuración de Desarrollo

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

## 🔍 Estado MCP - Resumen Ejecutivo

### ✅ Capacidades Confirmadas
- **28 bases de datos** conectadas vía MCP
- **Pipeline N0→N1→N2→N3** completamente funcional
- **4 APIs externas** operativas (REE, Open-Meteo, Nominatim, PVGIS)
- **Performance optimizada** (<2ms consultas críticas)
- **17,009 códigos postales** territoriales poblados

### ❌ Gaps Identificados
- **4 APIs bloqueadas** (REE Mix/CO2, ESIOS)
- **7,743 zonas climáticas** pendientes de carga
- **3 bases vacías** (N4, N5, usuario)
- **Integridad referencial** parcialmente implementada

### 🎯 Estado General: 92% OPERATIVO

El ecosistema está **altamente funcional** para scoring energético con capacidades MCP validadas.

---

**Documento Confidencial y Propiedad de Energy Green Data.**

*Auditoría MCP realizada el 9 de Septiembre de 2025. Información de carácter reservado para uso exclusivo de la organización.*
