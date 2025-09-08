<p align="center">
  <img src="assets/EGD.png" alt="Energy Green Data" width="400"/>
</p>

# 🔄 Actualizaciones Automáticas de Precios y Referenciales

![Estado](https://img.shields.io/badge/estado-producción-green)

**Módulo:** db_watioverse (integración con Ncore y sistema eléctrico)

---

## 📑 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Planificación Automática (cron)](#-planificación-automática-cron)
- [Scripts y SQL implicados](#-scripts-y-sql-implicados)
- [Consultas de Verificación](#-consultas-de-verificación)
- [Notas de Operación](#-notas-de-operación)

## 🎯 Descripción General

Sistema automático para mantener actualizados los precios energéticos y referenciales asociados. El flujo integra la ingesta de precios OMIE (day-ahead), sincronización hacia Ncore, actualización de PVPC, calendario tarifario y BOE (peajes/cargos), con monitorización diaria.

## 🏗️ Arquitectura del Sistema

```mermaid
flowchart LR
    subgraph APIs[APIs Externas]
        A[[REE: Precios OMIE day-ahead]]
        CAT[[OVC Catastro]]
    end

    T1[18:18 Ingesta]
    T2[04:15 Fetch]
    T3[04:30 Sync]
    T4[18:36 Monitor]
    T5[02:15 PVPC]
    T6[03:00 Calendario]
    T7[03:15 BOE]
    T8[04:35 Monitor]

    A --> T1 --> B[(db_sistema_electrico.omie_precios)]
    B -->|FDW| C[(db_Ncore.core_precios_omie_diario)]
    
    CAT --> T2 --> ENR[(db_enriquecimiento.catastro_inmuebles)]
    ENR --> T3 --> CATMAP[(core_catastro_map_uso_escore)]

    subgraph Ncore[db_Ncore]
        C --> T4
        D[(core_precios_omie)]
        E[(core_calendario_horario)]
        F[(core_precio_regulado_boe)]
        G[(core_peajes_acceso)]
        CATMAP
        MV[[mv_tarifas_vigentes]]
    end

    T5 -.-> D
    T6 -.-> E
    T7 -.-> F
    F -->|recálculo| G --> MV
    CATMAP --> T8

    style A fill:#2C3E50,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style CAT fill:#2C3E50,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style B fill:#34495E,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style ENR fill:#34495E,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style C fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style CATMAP fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style D fill:#9B59B6,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style E fill:#95A5A6,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style F fill:#95A5A6,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style G fill:#9B59B6,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style MV fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    
    style T1 fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style T2 fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style T3 fill:#9B59B6,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style T4 fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style T5 fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style T6 fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style T7 fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
    style T8 fill:#1ABC9C,stroke:#ffffff,stroke-width:2px,color:#ffffff
```

## ⏱️ Planificación Automática (launchd)

| Proceso | Hora | LaunchAgent |
|---|---:|---|
| Ingesta OMIE day-ahead (origen) con 3 reintentos x5' y post-sync | 18:18 | `com.vagalume.omie.ingest_dayahead` |
| Sincronización OMIE (Ncore, incluye mañana) | 18:31 | `com.vagalume.omie.sync_1640` |
| Monitor OMIE day-ahead (24h + agregado) | 18:36 | `com.vagalume.omie.monitor_1645` |
| Verificación nocturna OMIE (agregado) | 02:10 | `com.vagalume.omie.sync_0210` |
| PVPC horario (30d incremental) | 02:15 | `com.vagalume.pvpc.sync_0215` |
| Calendario tarifario (14d incremental) | 03:00 | `com.vagalume.calendario.sync_0300` |
| BOE upsert + recálculo P1..P6 | 03:15 | `com.vagalume.boe.sync_0315` |
| Catastro cache OVC (50 CUPS/día con coord) | 04:15 | `com.vagalume.catastro.fetch_ovc` |
| Catastro diccionarios Ncore (64 usos oficiales) | 04:20 | `com.vagalume.catastro.build_dictionaries` |
| Catastro mapeo uso→categoría eSCORE | 04:25 | `com.vagalume.catastro.build_mapping` |
| Catastro promoción N2 (superficie kWh/m²) | 04:30 | `com.vagalume.catastro.fetch_n2` |
| <span style="color:#1ABC9C">**REE mix/CO2**</span> | <span style="color:#1ABC9C">**02:20**</span> | `com.vagalume.ree.mixco2.ingest` |
| <span style="color:#1ABC9C">**PVGIS irradiancia**</span> | <span style="color:#1ABC9C">**04:45**</span> | `com.vagalume.pvgis.ingest` |
| <span style="color:#1ABC9C">**Zonas climáticas HDD/CDD**</span> | <span style="color:#1ABC9C">**01:05**</span> | `com.vagalume.zonas_climaticas.load_overnight` |

Notas:
- OMIE publica los precios del día siguiente alrededor de las 16:30–17:00. Para evitar saturación, se programa la ingesta a las 18:18 con 3 intentos automáticos (cada 5 minutos) y sincronización inmediata a Ncore tras el primer intento exitoso.
- La sincronización de respaldo se ejecuta a las 18:31 y el monitor valida a las 18:36 (23–25 horas en origen y agregado en Ncore).
- La verificación nocturna a las 02:10 re-sincroniza por si hubiera revisiones.

## 🧩 Automatización instalada (LaunchAgents)

- Ingesta OMIE day-ahead (origen `db_sistema_electrico`) con 3 reintentos x5' y post-sync a Ncore:
  - `~/Library/LaunchAgents/com.vagalume.omie.ingest_dayahead.plist`

- Sincronización OMIE (Ncore):
  - `~/Library/LaunchAgents/com.vagalume.omie.sync_1640.plist` (18:31)
  - `~/Library/LaunchAgents/com.vagalume.omie.sync_0210.plist` (02:10)

- PVPC horario (Ncore):
  - `~/Library/LaunchAgents/com.vagalume.pvpc.sync_0215.plist`

- Calendario tarifario (Ncore):
  - `~/Library/LaunchAgents/com.vagalume.calendario.sync_0300.plist`

- BOE peajes/cargos (Ncore):
  - `~/Library/LaunchAgents/com.vagalume.boe.sync_0315.plist` (incluye recálculo y REFRESH `mv_tarifas_vigentes`)

- Catastro OVC (enriquecimiento → N2 + Ncore):
  - `~/Library/LaunchAgents/com.vagalume.catastro.fetch_ovc.plist` (04:15) - Cache OVC→db_enriquecimiento
  - `~/Library/LaunchAgents/com.vagalume.catastro.build_dictionaries.plist` (04:20) - 64 usos oficiales→Ncore
  - `~/Library/LaunchAgents/com.vagalume.catastro.build_mapping.plist` (04:25) - Mapeo uso→categoría eSCORE
  - `~/Library/LaunchAgents/com.vagalume.catastro.fetch_n2.plist` (04:30) - Promoción superficie→N2

- REE mix/CO2 (Ncore):
  - `~/Library/LaunchAgents/com.vagalume.ree.mixco2.ingest.plist` (02:20) - Mix generación y emisiones→Ncore

- PVGIS irradiancia (Ncore):
  - `~/Library/LaunchAgents/com.vagalume.pvgis.ingest.plist` (04:45) - Radiación mensual kWh/m²→Ncore

- Zonas climáticas HDD/CDD (Ncore):
  - `~/Library/LaunchAgents/com.vagalume.zonas_climaticas.load_overnight.plist` (01:05) - 11,830 CP con HDD/CDD→Ncore

Observación:
- Los LaunchAgents ejecutan one‑liners `psql`/`curl`/`jq` y no dependen de ficheros `.sh` o `.sql` del repositorio. Los nombres de BD y tablas son reales (sin alias) tal y como exige la operativa.

## ❓ ¿Por qué precargar en Ncore y no llamar a las APIs en tiempo real?

- Respuesta inmediata y estable: eSCORE (N3) lee N1+N2 locales, sin depender de latencias, timeouts o cuotas de terceros.
- Resiliencia: si REE/OMIE/OVC caen o limitan, el sistema sigue operativo con los datos ya precargados.
- Idempotencia y reproducibilidad: guardamos RAW+normalizado; mismo input ⇒ mismo resultado, con auditoría y re‑cálculo garantizado.
- Normalización multisource: unificamos unidades y reglas (p. ej., derivación CTE por altitud) antes de exponer a N3.
- Auditoría y trazabilidad: tablas `core_*` con timestamps explicables sin “viajar” a la API.
- Coste y gobernanza: menos llamadas repetidas; ventanas y frecuencias controladas por nosotros.
- Seguridad y cumplimiento: evitamos exponer PII a terceros en scoring; enriquecimiento controlado en N2.
- Escalabilidad: precómputo diario/horario sirve miles de scores concurrentes sin pegar a fuentes externas.
- Verificación automática: garantizamos cobertura (23–25 horas) y checks de integridad antes de publicar.
- Arquitectura por capas: N0→N1→N2→N3; N3 nunca habla con APIs, solo con datasets validados.

## 🔍 Consultas de Verificación

- Origen OMIE (day-ahead):

```sql
-- Debe devolver 23-25 filas para mañana (maneja DST)
SELECT fecha, COUNT(*)
FROM omie_precios
WHERE zona='ES' AND fecha = CURRENT_DATE + 1
GROUP BY fecha;
```

- Agregado diario Ncore (incluye mañana):

```sql
SELECT fecha, precio_medio_mwh, precio_max_mwh, precio_min_mwh
FROM core_precios_omie_diario
WHERE fecha BETWEEN CURRENT_DATE AND CURRENT_DATE + 1
ORDER BY fecha;
```

- Verificación PVPC (últimos 30 días):

```sql
-- Cobertura PVPC últimos 30 días (tabla de precio regulado en Ncore)
SELECT MIN(fecha_hora) AS min_ts, MAX(fecha_hora) AS max_ts, COUNT(*) AS registros
FROM core_precio_regulado_boe
WHERE fecha_hora >= CURRENT_DATE - INTERVAL '30 days';
```

- Verificación REE mix (tecnologías generación):

```sql
-- Mix horario por tecnología (ayer)
SELECT date(fecha_hora) AS dia, tecnologia, COUNT(*) AS horas, 
       ROUND(AVG(porcentaje),1) AS pct_medio
FROM core_ree_mix_horario
WHERE fecha_hora >= CURRENT_DATE - INTERVAL '1 day'
  AND fecha_hora < CURRENT_DATE
GROUP BY 1, 2
ORDER BY pct_medio DESC LIMIT 10;
```

- Verificación REE emisiones CO2:

```sql
-- Debe devolver 23-25 horas (maneja DST)
SELECT date_trunc('day', fecha_hora) AS dia, COUNT(*) AS horas,
       ROUND(AVG(gco2_kwh),1) AS gco2_medio
FROM core_ree_emisiones_horario
WHERE fecha_hora >= CURRENT_DATE - INTERVAL '1 day'
GROUP BY 1;
```

- Verificación PVGIS (irradiancia mensual):

```sql
-- Cobertura por mes y coords únicas
SELECT mes, COUNT(DISTINCT (latitud, longitud)) AS coords,
       ROUND(AVG(kwh_m2),1) AS kwh_m2_medio
FROM core_pvgis_radiacion
GROUP BY mes ORDER BY mes;
```

- Verificación zonas climáticas (HDD/CDD):

```sql
-- Distribución por provincia y zona CTE
SELECT provincia, zona_climatica_cte, COUNT(*) AS municipios,
       ROUND(AVG(hdd_anual_medio),0) AS hdd_medio,
       ROUND(AVG(cdd_anual_medio),0) AS cdd_medio
FROM core_zonas_climaticas
GROUP BY 1, 2
ORDER BY 1, 2;
```

## 🧭 Notas de Operación

- Bases de datos y tablas reales (sin alias):
  - Origen: `db_sistema_electrico.omie_precios` (EUR/kWh)
  - Ncore: `db_Ncore.core_precios_omie_diario` (EUR/MWh), `db_Ncore.core_precios_omie`, `db_Ncore.core_calendario_horario`, `db_Ncore.core_precio_regulado_boe`, `db_Ncore.core_peajes_acceso`, `db_Ncore.mv_tarifas_vigentes`.
- Unidades:
  - La API REE devuelve EUR/MWh. El origen se almacena en EUR/kWh (÷1000). Ncore agrega en EUR/MWh.
- Robustez:
  - Ingesta usa paquetes semanales con fallback diario y reintentos (backoff) + endpoint alternativo de REE.
- Seguridad de cron:
  - Todos los scripts `.sh` exportan PATH para ejecución correcta desde cron.

---

**Documento Confidencial y Propiedad de Energy Green Data.**

*La información contenida en este documento es de carácter reservado y para uso exclusivo de la organización. Queda prohibida su reproducción, distribución o comunicación pública, total o parcial, sin autorización expresa.*
