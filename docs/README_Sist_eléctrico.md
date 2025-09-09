<p align="center">
  <img src="assets/EGD.png" alt="Energy Green Data" width="320"/>
</p>

# ⚡ Sistema Eléctrico — Modelo de Datos y Fuentes

Módulo: db_sistema_electrico  
Estado: producción  
Fecha de generación: 2025-09-09

---

## 📑 Tabla de Contenidos

- Descripción General
- Arquitectura del Sistema
- Base de Datos — Esquema actual (MCP)
- Elementos críticos para simulación PVPC/Indexado
- Propuesta final (sin cambios estructurales)
- Próximos pasos

---

## 🎯 Descripción General

Este documento describe el modelo de datos del sistema eléctrico usado en el ecosistema db_watioverse para cálculo y simulación de precios eléctricos, tanto en contratos indexados como PVPC. La información aquí reflejada proviene de la base de datos real `db_sistema_electrico` (consultada vía MCP) y de los procesos de ingesta existentes. No se incluyen elementos ficticios.

### Arquitectura del Sistema

```mermaid
flowchart LR
    subgraph Fuentes[Fuentes Externas]
        OMIE[OMIE - Precios day-ahead]
        BOE[BOE - Peajes/Cargos]
        ESIOS[ESIOS - Datos oficiales (mix/CO2/demanda)]
    end

    subgraph SE[db_sistema_electrico]
        OM[(omie_precios)]
        PVPC[(precios_horarios_pvpc)]
        BOE_TAB[(precio_regulado_boe)]
        CAL[(calendario_tarifario_2025)]
        IVA[(historico_iva)]
        IE[(historico_impuesto_electrico)]
    end

    subgraph NCORE[db_Ncore]
        MIX[(core_ree_mix_horario)]
        CO2[(core_ree_emisiones_horario)]
    end

    OMIE --> OM
    BOE --> BOE_TAB
    ESIOS --> MIX
    ESIOS --> CO2

    OM --> PVPC
    BOE_TAB --> PVPC
    CAL --> PVPC

    style Fuentes fill:#2C3E50,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style SE fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style NCORE fill:#34495E,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

---

## 💾 Base de Datos — Esquema actual (consultado por MCP)

A continuación se listan las tablas y vistas relevantes del esquema `public` en `db_sistema_electrico`. Se muestran los campos principales (máx. 10 por tabla para legibilidad). Donde aplica, se indica con ★ los elementos críticos para simulación PVPC/Indexado.

### Tablas principales

- `omie_precios` (fuente OMIE)
  - Campos: 
    - **id** (integer)
    - **fecha** (date) ★
    - **hora** (time) ★
    - **periodo** (integer)
    - **precio_energia** (numeric) ★
    - **zona** (char, por defecto 'ES')
    - **fuente_id** (integer)
    - **created_at** (timestamp)

- `precio_regulado_boe` (componentes regulados)
  - Campos:
    - **id** (integer)
    - **tarifa_peaje** (text) ★
    - **componente** (text) ★
    - **precio** (numeric) ★
    - **fecha_inicio** (date) ★
    - **fecha_fin** (date)
    - **unidad** (text)

- `precios_horarios_pvpc` (PVPC consolidado horario)
  - Campos:
    - **fecha** (date) ★
    - **hora** (time) ★
    - **periodo_tarifario** (varchar)
    - **precio_energia** (numeric)
    - **precio_peajes** (numeric)
    - **precio_cargos** (numeric)
    - **precio_total_pvpc** (numeric) ★

- `calendario_tarifario_2025` (periodificación horaria)
  - Campos:
    - **fecha** (date) ★
    - **hora** (bigint)
    - **comunidad** (text)
    - **provincia** (text)
    - **es_festivo** (boolean)
    - **es_festivo_local** (boolean)
    - **tipo_dia** (text)
    - **temporada** (text)
    - **periodo_tarifa** (text) ★
    - **hora_time** (time)

- `historico_iva` (tipos impositivos IVA)
  - Campos:
    - **id_iva** (integer)
    - **tipo_iva** (text)
    - **ambito_aplicacion** (text)
    - **fecha_inicio** (date)
    - **fecha_fin** (date)

- `historico_impuesto_electrico` (impuesto especial electricidad)
  - Campos:
    - **id** (integer)
    - **tipo_impositivo** (numeric)
    - **ambito_aplicacion** (text)
    - **fecha_inicio** (date)
    - **fecha_fin** (date)

> Nota: Además existen tablas/series históricas de `calendario_tarifario_20XX` y otras tablas parametrizadoras (p. ej., `param_*`, `reglas_*`) no detalladas aquí por brevedad.

### Vistas relevantes

- `tarifa_peaje_actual` (vista)
  - **tarifa_peaje**, **tarifa_comercial**, **segmento_aplicacion**, **fecha_inicio**, **fecha_fin**, **num_periodos_potencia**, **num_periodos_energia**

- `v_precios_potencia` (vista)
  - **tarifa_peaje**, **fecha_inicio**, **fecha_fin**, **precio_kw_dia**

- `v_precios_pvpc_horario` (vista)
  - **fecha**, **hora**, **precio_energia**, **tarifa_peaje**, **precio_peaje_cte**, **precio_cargo_cte**, **precio_kwh_pvpc**

- Otras vistas: `calendario_global`, `curvas_horarias`, `vista_consumo_periodo_peaje`, `vista_consumo_tarifado`, `vista_tarifa_peaje_vigente`.

---

## ★ Elementos críticos para simulación PVPC / Indexado

- ★ `omie_precios.precio_energia` — Precio horario base (indexado)
- ★ `omie_precios.fecha`, `omie_precios.hora` — Llave temporal para emparejar con consumo/periodificación
- ★ `precio_regulado_boe.(tarifa_peaje, componente, precio, fecha_inicio, fecha_fin)` — Peajes y cargos vigentes
- ★ `calendario_tarifario_2025.periodo_tarifa` — Clasificación P1/P2/P3 por hora/fecha/provincia
- ★ `precios_horarios_pvpc.precio_total_pvpc` — PVPC ya calculado (energía + peajes + cargos)

Notas:
- Para simulación de factura final pueden ser necesarios `historico_iva` e `historico_impuesto_electrico` (impuestos). No son imprescindibles para el precio energético sin impuestos.
- El margen comercial, pérdidas o ajustes específicos de indexado no están almacenados como tabla en `db_sistema_electrico`; deben parametrizarse externamente si se usan.

---

## 📐 Propuesta final (sin cambios estructurales)

Sin introducir nuevas tablas, se recomienda:

- Índices sugeridos (rendimiento consultas horarias):
  - `omie_precios (fecha, hora)`
  - `precios_horarios_pvpc (fecha, hora)`
  - `precio_regulado_boe (tarifa_peaje, fecha_inicio, fecha_fin)`
  - `calendario_tarifario_2025 (fecha, hora_time)`

- Uso de vistas para consumo analítico:
  - `v_precios_pvpc_horario` para lecturas directas de PVPC horario
  - `tarifa_peaje_actual` para resolver metadatos de tarifa vigente

- Normalización temporal:
  - Asegurar consistencia de zona horaria y manejo DST (23–25h) en inserciones y consultas

- Trazabilidad y auditoría:
  - Mantener `created_at`/`fecha_carga` donde aplique
  - Documentar fuente y versión normativa en `precio_regulado_boe`

> Esta propuesta refleja únicamente mejoras operativas de consulta y trazabilidad, sin alterar el modelo real existente.

---

## ✅ Próximos pasos

1. Verificar y, en su caso, crear índices sugeridos en tablas clave
2. Validar cobertura temporal (últimos 12 meses) en `omie_precios` y `precios_horarios_pvpc`
3. Revisar vigencias y solapes en `precio_regulado_boe`
4. Validar consistencia de `calendario_tarifario_2025` con periodificación P1/P2/P3
5. Concretar parámetros externos (margen, pérdidas) para simulación indexada cuando aplique

---

**Documento Confidencial y Propiedad de Energy Green Data.**

*La información contenida en este documento es de carácter reservado y para uso exclusivo de la organización. Queda prohibida su reproducción, distribución o comunicación pública, total o parcial, sin autorización expresa.*
