<p align="center">
  <img src="../../../motor_eSCORE/docs/assets/EGD.png" alt="Energy Green Data" width="400"/>
</p>

# 🔄 Base de Datos N1 - Capa de Enriquecimiento Energético

![Versión](https://img.shields.io/badge/versión-1.0.0-blue)
![Estado](https://img.shields.io/badge/estado-desarrollo-yellow)
![Tipo](https://img.shields.io/badge/tipo-PostgreSQL-336791)
![Capa](https://img.shields.io/badge/capa-N1_Enriched-green)

**Módulo:** db_watioverse/N1  
**Proyecto interno de Energy Green Data**

---

## 📑 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Estructura de Base de Datos](#-estructura-de-base-de-datos)
- [Separación de Datos](#-separación-de-datos)
- [Flujo de Datos](#-flujo-de-datos)
- [Scripts de Creación](#-scripts-de-creación)

---

## 🎯 Descripción General

La **Base de Datos N1** constituye la capa de enriquecimiento del ecosistema de datos energéticos, transformando los datos en bruto de N0 en información analítica lista para el cliente. Elimina metadatos de extracción y añade KPIs, métricas de sostenibilidad y análisis comparativos para alimentar el sistema eSCORE.

### 🏗️ Arquitectura del Sistema

```mermaid
graph TD
    A[Base de Datos N0] --> B[Proceso de Limpieza]
    B --> C[Datos Base N1]
    C --> D[Motor Enriquecimiento]
    
    D --> E[Sustainability Metrics]
    D --> F[Analytics & KPIs]
    D --> G[Performance Benchmarks]
    
    C --> H[Base de Datos N1]
    E --> H
    F --> H
    G --> H
    
    H --> I[Sistema eSCORE]
    H --> J[Capa N2 Análisis]
    
    style A fill:#F39C12,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style B fill:#2C3E50,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style C fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style D fill:#9B59B6,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style H fill:#27AE60,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style I fill:#E74C3C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style J fill:#8E44AD,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

---

## 💾 Estructura de Base de Datos

### Arquitectura de Separación N1

La base de datos N1 implementa una **arquitectura de separación limpia** entre datos base y enriquecimiento:

| Categoría | Tablas | Propósito |
|-----------|--------|-----------|
| **📊 Datos Base** | 12 tablas | Datos limpios provenientes de N0 sin metadatos |
| **🌱 Sostenibilidad** | 2 tablas | Mix energético (base) + métricas calculadas |
| **📈 Enriquecimiento** | 1 tabla | KPIs, ratios y análisis comparativos |
| **🗂️ Control** | 2 tablas | Tabla maestra + control de traslado |

### Tablas de Datos Base (desde N0)

| Tabla | Campos Principales | Propósito |
|-------|-------------------|-----------|
| **`client`** | `nombre_cliente`, `nif_titular`, `tipo_cliente` | Datos del cliente sin metadatos |
| **`provider`** | `nombre_comercializadora`, `cif_comercializadora` | Información del proveedor |
| **`contract`** | `numero_contrato`, `tarifa_acceso`, `modalidad_contrato` | Datos contractuales |
| **`energy_consumption`** | `consumo_kwh_p1-p6`, `consumo_total_kwh` | Consumos energéticos base |
| **`invoice`** | `numero_factura`, `importe_total`, `precios_por_periodo` | Facturación completa |
| **`power_term`** | `potencia_contratada_p1-p6`, `potencia_facturada_p1-p6` | Términos de potencia |
| **`supply_point`** | `cups`, `numero_contador`, `tipo_contador` | Punto de suministro |
| **`metering`** | `lectura_anterior`, `lectura_actual`, `consumo_total_kwh` | Medición contadores |

### Tablas de Sostenibilidad (Mixto)

```mermaid
graph LR
    subgraph "Sustainability Base (Factura)"
        A[energia_origen_renovable]
        B[energia_origen_nuclear]
        C[emisiones_co2_equivalente]
        D[letra_escala_medioambiental]
    end
    
    subgraph "Sustainability Metrics (Calculado)"
        E[huella_carbono_kg_co2]
        F[porcentaje_renovable]
        G[rating_sostenibilidad]
        H[equivalencia_arboles_plantados]
        I[recomendaciones_sostenibilidad]
    end
    
    A --> E
    B --> F
    C --> G
    
    style A fill:#27AE60,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style B fill:#27AE60,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style E fill:#9B59B6,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style F fill:#9B59B6,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

### Tabla de Enriquecimiento Puro

| Campo | Tipo | Propósito |
|-------|------|-----------|
| **`consumo_promedio_diario_kwh`** | DECIMAL | Promedio diario de consumo |
| **`coste_promedio_diario_eur`** | DECIMAL | Coste medio diario |
| **`eficiencia_energetica_ratio`** | DECIMAL | Ratio de eficiencia energética |
| **`ratio_coste_energia_potencia`** | DECIMAL | Relación coste energía/potencia |
| **`variacion_consumo_vs_mes_anterior`** | DECIMAL | Variación temporal consumo |
| **`periodo_mayor_consumo`** | VARCHAR | Período de mayor consumo (P1-P6) |
| **`alertas_consumo`** | TEXT[] | Alertas automáticas |
| **`recomendaciones_ahorro`** | TEXT[] | Recomendaciones personalizadas |
| **`percentil_consumo_sector`** | DECIMAL | Benchmarking sectorial |

---

## 🔄 Separación de Datos

### Filosofía de Arquitectura

```mermaid
graph TD
    subgraph "N0 - Datos Brutos"
        A[Datos + Metadatos Extracción]
        B[Campos Confianza]
        C[Patrones Reconocimiento]
    end
    
    subgraph "N1 - Datos Limpios"
        D[Solo Datos Energéticos]
        E[Sin Metadatos]
        F[Campos Enriquecimiento]
    end
    
    subgraph "N1 - Enriquecimiento"
        G[KPIs Calculados]
        H[Métricas Sostenibilidad]
        I[Análisis Comparativo]
    end
    
    A --> D
    B -.-> |Eliminado| E
    C -.-> |Eliminado| E
    
    D --> G
    D --> H
    D --> I
    
    style A fill:#F39C12,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style D fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style G fill:#9B59B6,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

### Ventajas de la Separación

- **🧹 Claridad**: Datos originales vs calculados claramente diferenciados
- **⚡ Performance**: Consultas rápidas en datos base sin campos adicionales
- **🔧 Mantenimiento**: Regenerar enriquecimiento sin tocar datos base
- **📊 Auditoría**: Trazabilidad clara de origen vs cálculo
- **📈 Escalabilidad**: Enriquecimiento independiente y evolutivo

---

## 🔄 Flujo de Datos

### Pipeline Completo N0 → N1

```mermaid
sequenceDiagram
    participant N0 as Base Datos N0
    participant P as Proceso Limpieza
    participant N1B as N1 Base
    participant E as Motor Enriquecimiento
    participant N1M as N1 Metrics
    participant S as Sistema eSCORE
    
    N0->>P: Datos brutos + metadatos
    P->>P: Eliminar metadatos extracción
    P->>N1B: Datos energéticos limpios
    
    N1B->>E: Datos base para cálculos
    E->>E: Calcular KPIs y métricas
    E->>N1M: Sustainability metrics
    E->>N1M: Analytics & ratios
    
    N1B->>S: Datos base energéticos
    N1M->>S: Métricas enriquecidas
    
    Note over P: Filtrado de campos confianza
    Note over E: Cálculos de sostenibilidad y eficiencia
    Note over S: Datos listos para eSCORE
```

### Transformaciones Clave

| Transformación | N0 → N1 | Propósito |
|----------------|---------|-----------|
| **Eliminación Metadatos** | `confianza_*`, `patron_*` → ❌ | Limpiar datos de extracción |
| **Campos Sostenibilidad** | Mix energético → `sustainability_base` | Datos directos de factura |
| **KPIs Calculados** | Consumos → Ratios y métricas | Enriquecimiento analítico |
| **Benchmarking** | Datos individuales → Comparativas | Análisis sectorial |

---

## 🛠️ Scripts de Creación

### Scripts Disponibles

| Script | Propósito | Estado |
|--------|-----------|--------|
| **`RECREAR_N1_SEPARADO.sql`** | Esquema con separación limpia | ✅ Listo |
| **`RECREAR_N1_UNIFICADO.sql`** | Esquema unificado (legacy) | ✅ Disponible |

### Ejecutar Creación de BD N1

```bash
# Opción 1: Esquema separado (recomendado)
psql -d db_N1 -f RECREAR_N1_SEPARADO.sql

# Opción 2: Esquema unificado
psql -d db_N1 -f RECREAR_N1_UNIFICADO.sql
```

### Resultado Esperado

```
✅ 17 tablas creadas:
   📊 12 tablas base (datos limpios)
   🌱 2 tablas sostenibilidad (base + métricas)
   📈 1 tabla analytics (enriquecimiento)
   🗂️ 2 tablas control (maestra + metadata)

✅ 8 índices de optimización
✅ Referencias y constraints
```

### Validación Post-Creación

```sql
-- Verificar tablas creadas
SELECT COUNT(*) as total_tables 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Verificar separación correcta
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

---

## 🎯 Integración con eSCORE

La capa N1 alimenta directamente:

- **Sistema eSCORE**: Datos limpios + métricas enriquecidas
- **N2 (Análisis)**: Agregaciones y comparativas avanzadas
- **Dashboards Cliente**: KPIs y recomendaciones personalizadas

### Campos Críticos para eSCORE

```mermaid
pie title Distribución de Campos N1 por Indicador
    "IC - Índice Consumo" : 30
    "IP - Índice Potencia" : 25
    "IE - Índice Eficiencia" : 20
    "IT - Índice Tarifario" : 15
    "IR - Índice Renovable" : 10
```

---

**Documento Confidencial y Propiedad de Energy Green Data.**

*La información contenida en este documento es de carácter reservado y para uso exclusivo de la organización. Queda prohibida su reproducción, distribución o comunicación pública, total o parcial, sin autorización expresa.*
