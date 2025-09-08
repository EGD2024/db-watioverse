<p align="center">
  <img src="docs/assets/EGD.png" alt="Energy Green Data" width="400"/>
</p>

# 🏗️ Arquitectura de Bases de Datos - Sistema Energético Integral

![Versión](https://img.shields.io/badge/versión-2.0.0-blue)
![Estado](https://img.shields.io/badge/estado-producción-green)
![Bases de Datos](https://img.shields.io/badge/bases_de_datos-23-purple)
![Pipeline](https://img.shields.io/badge/pipeline-N0→N1→N2-orange)

**Módulo:** Arquitectura de Datos  
**Proyecto interno de Energy Green Data**

---

## 📑 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Pipeline de Datos](#pipeline-de-datos)
- [Capa de Enriquecimiento](#capa-de-enriquecimiento)
- [Datos Maestros](#datos-maestros)
- [Motor eSCORE](#motor-escore)

## 🎯 Descripción General

El sistema gestiona 23 bases de datos especializadas organizadas en 5 capas funcionales que procesan, enriquecen y analizan datos energéticos desde facturas hasta scoring final. La arquitectura implementa un pipeline N0→N1→N2 con enriquecimiento asíncrono y cuestionarios dinámicos.

### Arquitectura del Sistema

```mermaid
graph TD
    subgraph "CAPA 1: Pipeline"
        A[db_N0<br/>14 tablas] --> B[db_N1<br/>14 tablas]
        B --> C[db_N2<br/>13 tablas]
    end
    
    subgraph "CAPA 2: Enriquecimiento"
        D[db_clima<br/>3-5 tablas] --> G[db_enriquecimiento<br/>3 tablas]
        E[db_catastro<br/>4 tablas] --> G
        F[db_sistema_electrico<br/>38 tablas OMIE] --> G
    end
    
    subgraph "CAPA 3: Interacción"
        H[db_encuesta<br/>5 tablas]
    end
    
    subgraph "CAPA 4: Maestros"
        I[db_cliente<br/>3 tablas]
        J[db_comercializadora<br/>11 tablas]
        K[db_distribuidora<br/>5 tablas]
        L[db_territorio<br/>7 tablas]
        M[db_calendario<br/>7 tablas]
        N[db_sistema_gas<br/>4 tablas]
    end
    
    subgraph "CAPA 5: eSCORE"
        O[db_eSCORE_def<br/>6 tablas]
        P[db_eSCORE_contx<br/>13 tablas]
        Q[db_eSCORE_master<br/>11 tablas]
        R[db_eSCORE_pesos<br/>37 tablas]
        S[db_eSCORE_watiodat<br/>20 tablas]
    end
    
    G --> B
    H --> B
    C --> O
    
    style A fill:#2C3E50,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style B fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style C fill:#F39C12,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style G fill:#9B59B6,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style H fill:#E74C3C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style O fill:#16A085,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

## 🔄 Pipeline de Datos

### Flujo Principal N0→N1→N2

```mermaid
sequenceDiagram
    participant PDF as Facturas PDF
    participant N0 as db_N0
    participant N1 as db_N1
    participant ENR as db_enriquecimiento
    participant ENC as db_encuesta
    participant N2 as db_N2
    participant SCR as eSCORE
    
    PDF->>N0: Extracción datos brutos
    N0->>N1: Limpieza y validación
    
    alt Datos incompletos
        N1->>ENC: Generar cuestionario
        ENC->>N1: Respuestas cliente
    end
    
    N1->>ENR: Solicitar enriquecimiento
    ENR->>N1: Datos clima, catastro, OMIE
    
    N1->>N2: Preparación scoring
    N2->>SCR: Cálculo score energético
```

### Descripción de Capas

| Capa | Base de Datos | Tablas | Función |
|------|---------------|--------|---------|
| **Pipeline** | db_N0 | 14 | Datos brutos extraídos |
| | db_N1 | 14 | Datos limpios validados |
| | db_N2 | 13 | Datos preparados scoring + superficie |
| **Enriquecimiento** | db_enriquecimiento | 3 | Cache multi-dimensional |
| | db_clima | 3-5 | Datos meteorológicos |
| | db_catastro | 4 | Datos catastrales |
| | db_sistema_electrico | 38 | Precios OMIE |
| **Interacción** | db_encuesta | 5 | Cuestionarios dinámicos |

## 💎 Capa de Enriquecimiento

### db_enriquecimiento - Arquitectura

```mermaid
graph LR
    subgraph "Fuentes Externas"
        A[AEMET API<br/>Clima]
        B[Catastro OVC<br/>Superficie/Uso]
        C[OMIE API<br/>Precios]
    end
    
    subgraph "db_enriquecimiento"
        D[enrichment_sources<br/>Control APIs]
        E[enrichment_queue<br/>Cola trabajos]
        F[enrichment_cache<br/>Cache datos]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    E --> F
    
    style D fill:#34495E,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style E fill:#F39C12,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style F fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

### Estructura de Cache Multi-dimensional

```sql
-- Cache enriquecido con Catastro OVC
SELECT 
    ec.cups,
    ec.tipo_dato,
    ci.referencia_catastral,
    ci.uso_principal,
    ci.superficie_construida_m2,  -- Clave para kWh/m²
    ec.datos_json
FROM enrichment_cache ec
LEFT JOIN catastro_inmuebles ci ON ci.cups = ec.cups
WHERE ec.is_active = true;
```

### Flujo Catastro OVC → N2

```mermaid
graph TD
    A[Coordenadas GPS<br/>desde N2] --> B[Catastro OVC API<br/>Consulta_RCCOOR_Distancia]
    B --> C[Referencia Catastral]
    C --> D[Catastro OVC API<br/>Consulta_DNPRC]
    D --> E[Cache en<br/>db_enriquecimiento]
    E --> F[Promoción a<br/>db_N2.n2_catastro_inmueble]
    F --> G[eSCORE calcula<br/>kWh/m² año]
    
    style A fill:#2C3E50,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style B fill:#E74C3C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style E fill:#9B59B6,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style F fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style G fill:#16A085,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

| Dimensión | Descripción | Ejemplo |
|-----------|-------------|---------|
| **CUPS** | Punto suministro | ES0022000008342444ND1P |
| **direccion_hash** | Hash dirección | SHA256 de dirección completa |
| **tarifa** | Tarifa contratada | 2.0TD, 3.0TD, 6.1TD |
| **periodo_mes** | Mes de datos | 2025-09 |

### APIs Integradas

| Fuente | Tipo | Datos | Rate Limit |
|--------|------|-------|------------|
| **AEMET** | API | Temperatura, humedad, predicción | 60/min |
| **Catastro** | API | Superficie, año construcción, tipo | 100/min |
| **OMIE** | API | Precios mercado, demanda | 100/min |
| **INE** | API | Datos territoriales | 50/min |
| **CNMC** | API | Tarifas reguladas | 30/min |

## 📊 Datos Maestros

### Bases de Datos de Referencia

```mermaid
graph TD
    subgraph "Entidades Energéticas"
        A[db_cliente<br/>3 tablas]
        B[db_comercializadora<br/>11 tablas]
        C[db_distribuidora<br/>5 tablas]
    end
    
    subgraph "Datos Geográficos"
        D[db_territorio<br/>7 tablas]
        E[db_calendario<br/>7 tablas]
    end
    
    subgraph "Infraestructura"
        F[db_sistema_gas<br/>4 tablas]
        G[db_sistema_electrico<br/>38 tablas]
    end
    
    style A fill:#2C3E50,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style B fill:#34495E,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style C fill:#34495E,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style D fill:#95A5A6,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style F fill:#8E44AD,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style G fill:#C0392B,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

### Relaciones entre Datos Maestros

| Base Origen | Base Destino | Relación | Campo Clave |
|-------------|--------------|----------|-------------|
| db_cliente | db_comercializadora | N:1 | id_comercializadora |
| db_cliente | db_distribuidora | N:1 | zona_distribución |
| db_territorio | db_clima | 1:N | codigo_postal |
| db_calendario | db_sistema_electrico | 1:N | fecha_periodo |

## 🎯 Motor eSCORE

### Arquitectura de Scoring

```mermaid
graph LR
    subgraph "Entrada"
        A[db_N2<br/>Datos preparados]
    end
    
    subgraph "Motor eSCORE"
        B[db_eSCORE_def<br/>Definiciones]
        C[db_eSCORE_contx<br/>Contexto]
        D[db_eSCORE_master<br/>Relaciones]
        E[db_eSCORE_pesos<br/>Ponderaciones]
        F[db_eSCORE_watiodat<br/>Agregados]
    end
    
    subgraph "Salida"
        G[Score<br/>Energético]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    
    style B fill:#16A085,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style C fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style D fill:#F39C12,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style E fill:#E74C3C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style F fill:#9B59B6,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style G fill:#2C3E50,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

### Componentes eSCORE

| Base de Datos | Tablas | Función Principal | Registros |
|---------------|--------|-------------------|-----------|
| **db_eSCORE_def** | 6 | Estructura de índices | ~1,000 |
| **db_eSCORE_contx** | 13 | Contexto y descripciones | ~5,000 |
| **db_eSCORE_master** | 11 | Relaciones lógicas | ~10,000 |
| **db_eSCORE_pesos** | 37 | Pesos y ponderaciones | ~50,000 |
| **db_eSCORE_watiodat** | 20 | Datos agregados cliente | ~100,000 |

## 📋 db_encuesta - Sistema de Cuestionarios

### Estructura de Cuestionarios Dinámicos

| Tabla | Función | Registros Actuales |
|-------|---------|-------------------|
| **questionnaire_questions** | Banco de preguntas | 5 |
| **questionnaire_conditions** | Lógica condicional | 0 |
| **questionnaire_sessions** | Sesiones activas | 0 |
| **questionnaire_responses** | Respuestas cliente | 0 |
| **questionnaire_analytics** | Métricas efectividad | 0 |

### Flujo de Cuestionarios

```mermaid
graph TD
    A[Validación N0→N1] --> B{¿Datos completos?}
    B -->|No| C[Generar cuestionario]
    C --> D[Sesión activa]
    D --> E[Cliente responde]
    E --> F[Validar respuestas]
    F --> G[Integrar en N1]
    B -->|Sí| G
    
    style B fill:#F39C12,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style C fill:#E74C3C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style G fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

## 🔧 Configuración del Sistema

### Variables de Entorno

```bash
# Pipeline N0→N1→N2
DB_N0=postgresql://postgres:admin@localhost:5432/db_N0
DB_N1=postgresql://postgres:admin@localhost:5432/db_N1
DB_N2=postgresql://postgres:admin@localhost:5432/db_N2

# Enriquecimiento
DB_ENRIQUECIMIENTO=postgresql://postgres:admin@localhost:5432/db_enriquecimiento
DB_CLIMA=postgresql://postgres:admin@localhost:5432/db_clima
DB_CATASTRO=postgresql://postgres:admin@localhost:5432/db_catastro

# eSCORE
DB_ESCORE_DEF=postgresql://postgres:admin@localhost:5432/db_eSCORE_def
DB_ESCORE_CONTX=postgresql://postgres:admin@localhost:5432/db_eSCORE_contx
DB_ESCORE_MASTER=postgresql://postgres:admin@localhost:5432/db_eSCORE_master
DB_ESCORE_PESOS=postgresql://postgres:admin@localhost:5432/db_eSCORE_pesos
DB_ESCORE_WATIODAT=postgresql://postgres:admin@localhost:5432/db_eSCORE_watiodat
```

### Métricas del Sistema

| Métrica | Valor | Objetivo |
|---------|-------|----------|
| **Bases de datos activas** | 23 | 23 |
| **Tablas totales** | ~250 | <300 |
| **Pipeline N0→N1** | <2 seg | <5 seg |
| **Cache hit rate** | 80% | >75% |
| **Cuestionarios necesarios** | 14.3% | <20% |

## 📈 Optimizaciones Planificadas

### Reorganización de Bases Vacías

| Base de Datos | Estado | Acción |
|---------------|--------|--------|
| db_N3, db_N4, db_N5 | Vacías | Eliminar |
| db_instalaciones | Vacía | Integrar en db_cliente |
| db_preferencias | Vacía | Integrar en db_cliente |
| db_usuario | Vacía | Usar db_cliente |
| db_memoria | Vacía | Usar MCP memory |
| db_rag | Vacía | Implementar cuando necesario |
| db_simulador | Vacía | Implementar cuando necesario |
| db_mails | 2 tablas | No pertenece al sistema |

### db_clima - Reestructuración

**Estado actual:** 87 tablas (fragmentación excesiva)

**Propuesta:**
- weather_historical (datos históricos)
- weather_forecast (predicciones)
- weather_stations (estaciones meteorológicas)
- weather_cache (cache temporal)

---

**Documento Confidencial y Propiedad de Energy Green Data.**

*La información contenida en este documento es de carácter reservado y para uso exclusivo de la organización. Queda prohibida su reproducción, distribución o comunicación pública, total o parcial, sin autorización expresa.*
