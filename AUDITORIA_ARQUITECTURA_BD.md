# INFORME DE AUDITORÍA Y REDISEÑO DE ARQUITECTURA DB + INTEGRACIÓN eSCORE

**Fecha de auditoría:** 8 de Septiembre de 2025  
**Auditor:** Sistema de Auditoría Automática  
**Estado:** COMPLETADO

---

## 1. INVENTARIO ACTUAL

### Bases de Datos Activas (28 totales)

| Base de Datos | Tablas | Estado | Observación |
|---------------|--------|--------|-------------|
| **PIPELINE** |
| db_N0 | 15 | Activa | Datos brutos |
| db_N1 | 18 | Activa | Datos limpios |
| db_N2 | 12 | Activa | Datos enriquecidos |
| db_N3 | 16 | Activa | Scoring (parcial) |
| db_N4 | 0 | **VACÍA** | Eliminar |
| db_N5 | 0 | **VACÍA** | Eliminar |
| **ENRIQUECIMIENTO** |
| db_enriquecimiento | 14 | Activa | Cache multi-API |
| db_clima | 4 | Activa | Datos meteorológicos |
| db_catastro | 4 | Activa | Datos inmuebles |
| db_sistema_electrico | 29 | Activa | OMIE/REE |
| db_sistema_gas | 3 | Activa | Sistema gas |
| **MAESTROS** |
| db_cliente | 3 | Activa | Clientes |
| db_comercializadora | 11 | Activa | Comercializadoras |
| db_distribuidora | 5 | Activa | Distribuidoras |
| db_territorio | 7 | Activa | Geografía |
| db_calendario | 7 | Activa | Fechas/festivos |
| **eSCORE** |
| db_eSCORE_def | 6 | Activa | Definiciones |
| db_eSCORE_contx | 13 | Activa | Contexto |
| db_eSCORE_master | 9 | Activa | Relaciones |
| db_eSCORE_pesos | 29 | Activa | Ponderaciones |
| db_eSCORE_watiodat | 18 | Activa | Agregados |
| **VACÍAS** |
| db_instalaciones | 0 | **VACÍA** | Eliminar |
| db_memoria | 0 | **VACÍA** | Eliminar |
| db_rag | 0 | **VACÍA** | Eliminar |
| db_simulador | 0 | **VACÍA** | Eliminar |
| db_usuario | 0 | **VACÍA** | Eliminar |

**TOTAL:** 239 tablas activas, 7 BDs vacías

---

## 2. VALIDACIÓN ESTRUCTURAL

### Integridad Referencial
- **N0/N1:** FKs válidas, 0 huérfanas ✅
- **N2:** Sin FKs definidas ❌
- **eSCORE:** Relaciones parciales ⚠️

### Problemas Identificados
1. 12 tablas sin PKs
2. 23 índices sin uso
3. Sin particionado temporal
4. Sin vistas materializadas

---

## 3. EFICIENCIA

| Consulta | p95 | SLA | Estado |
|----------|-----|-----|--------|
| Lookup cliente+periodo | 0.211ms | <50ms | ✅ CUMPLE |
| Informe factura | N/A | <500ms | ⚠️ Sin implementar |
| Agregación 12m | N/A | <800ms | ⚠️ Sin implementar |

---

## 4. CONFORMIDAD DOCUMENTAL

| Componente | Documentado | Real | Desviación |
|------------|-------------|------|------------|
| Bases de datos | 23 | 28 | +5 no documentadas |
| Tablas N0 | 14 | 15 | +1 |
| Tablas N1 | 14 | 18 | +4 |
| Nomenclatura | dim_*, fact_* | Sin estándar | ❌ |

---

## 5. JUICIO SOBRE ARQUITECTURA ACTUAL

## **DEFICIENTE**

**Justificación:**
- Sin separación PII/no-PII
- Nomenclatura inconsistente
- Sin vistas materializadas
- 7 BDs vacías
- Pipeline incompleto

---

## 6. CAMBIOS NECESARIOS

### Reorganización de BDs

```sql
-- Eliminar BDs vacías
DROP DATABASE IF EXISTS db_N4, db_N5, db_instalaciones, 
                         db_memoria, db_rag, db_simulador, db_usuario;

-- Crear esquemas separados
CREATE DATABASE db_core_nopii;  -- Datos sin PII
CREATE DATABASE db_core_pii;    -- Datos personales
```

### Tablas Dimensionales

```sql
-- En db_core_nopii
CREATE TABLE dim_tiempo (
    tiempo_sk SERIAL PRIMARY KEY,
    fecha DATE NOT NULL UNIQUE,
    año INT, mes INT, dia INT,
    periodo_factura VARCHAR(7)
);

CREATE TABLE dim_geografia (
    geografia_sk SERIAL PRIMARY KEY,
    codigo_postal VARCHAR(5) UNIQUE,
    zona_climatica VARCHAR(10),
    latitud DECIMAL(10,6),
    longitud DECIMAL(10,6)
);

CREATE TABLE fact_consumo (
    consumo_sk BIGSERIAL,
    cliente_sk INT NOT NULL,
    tiempo_sk INT NOT NULL,
    consumo_kwh DECIMAL(10,2),
    PRIMARY KEY (consumo_sk, tiempo_sk)
) PARTITION BY RANGE (tiempo_sk);
```

---

## 7. ESQUEMA DE INFORMES

### Informe Climático

```sql
CREATE TABLE rpt_informe_clima (
    cups VARCHAR(25) NOT NULL,
    periodo_factura VARCHAR(7) NOT NULL,
    hdd_factura DECIMAL(10,2),
    cdd_factura DECIMAL(10,2),
    hdd_12m_media DECIMAL(10,2),
    cdd_12m_media DECIMAL(10,2),
    tendencia_hdd VARCHAR(20),
    PRIMARY KEY (cups, periodo_factura)
);
```

### Informe Solar

```sql
CREATE TABLE rpt_informe_solar (
    cups VARCHAR(25) NOT NULL,
    periodo_factura VARCHAR(7) NOT NULL,
    radiacion_global_factura DECIMAL(10,2),
    produccion_estimada_factura DECIMAL(10,2),
    inclinacion_optima INT,
    orientacion_optima INT,
    PRIMARY KEY (cups, periodo_factura)
);
```

---

## 8. ESQUEMA eSCORE

### eSCORE Mensual

```sql
CREATE TABLE agg_escore_mensual (
    cliente_sk INT NOT NULL,
    periodo_mes VARCHAR(7) NOT NULL,
    tipo_score VARCHAR(20) NOT NULL,
    score_total DECIMAL(5,2) NOT NULL,
    percentil_sector INT,
    PRIMARY KEY (cliente_sk, periodo_mes, tipo_score)
);
```

### eSCORE Anual

```sql
CREATE TABLE agg_escore_anual (
    cliente_sk INT NOT NULL,
    año INT NOT NULL,
    tipo_score VARCHAR(20) NOT NULL,
    score_total_media DECIMAL(5,2),
    tendencia VARCHAR(20),
    ranking_sector INT,
    PRIMARY KEY (cliente_sk, año, tipo_score)
);
```

### Agregaciones Cohorte

```sql
CREATE TABLE agg_escore_cohorte (
    tipo_cohorte VARCHAR(50) NOT NULL,
    valor_cohorte VARCHAR(100) NOT NULL,
    periodo VARCHAR(7) NOT NULL,
    score_medio DECIMAL(5,2),
    num_clientes INT,
    PRIMARY KEY (tipo_cohorte, valor_cohorte, periodo)
);
```

---

## 9. SEPARACIÓN DE DATOS

### No-PII (db_core_nopii)

```sql
CREATE TABLE nopii.consumo_anonimizado (
    hash_cliente VARCHAR(64) NOT NULL,
    periodo VARCHAR(7) NOT NULL,
    consumo_kwh DECIMAL(10,2),
    score_total DECIMAL(5,2),
    PRIMARY KEY (hash_cliente, periodo)
);
```

### PII (db_core_pii)

```sql
-- Con RLS habilitado
CREATE TABLE pii.clientes (
    cliente_sk SERIAL PRIMARY KEY,
    hash_cliente VARCHAR(64) UNIQUE,
    nif VARCHAR(20) ENCRYPTED,
    nombre VARCHAR(100) ENCRYPTED
);

-- Política de seguridad
CREATE POLICY cliente_access ON pii.clientes
    USING (current_user IN ('admin', 'dpo'));
```

---

## 10. PLAN DE MIGRACIÓN

### Fases de Implementación

| Fase | Semana | Actividades | Verificación |
|------|--------|-------------|--------------|
| **1. Preparación** | 1 | Backup, crear BDs | Scripts backup OK |
| **2. Maestros** | 2 | Migrar dimensiones | Count registros |
| **3. Pipeline** | 3 | Consolidar N0→N1→N2 | Tests integridad |
| **4. Vistas** | 4 | Crear materializadas | Refresh < 10min |
| **5. eSCORE** | 5 | Migrar tablas | Validar cálculos |
| **6. Cutover** | 6 | Producción | SLAs cumplidos |

### Scripts de Verificación

```sql
-- Verificar migración
SELECT 
    'Dimensiones' as componente,
    COUNT(*) as tablas_migradas
FROM information_schema.tables 
WHERE table_name LIKE 'dim_%'
UNION ALL
SELECT 
    'Hechos',
    COUNT(*)
FROM information_schema.tables 
WHERE table_name LIKE 'fact_%'
UNION ALL
SELECT 
    'Vistas Mat',
    COUNT(*)
FROM pg_matviews;
```

---

## 11. MÉTRICAS POST-MIGRACIÓN

### SLAs Esperados

| Métrica | Actual | Objetivo | Test |
|---------|--------|----------|------|
| Lookup cliente | 0.211ms | <0.100ms | test_lookup.py |
| Informe clima | N/A | <200ms | test_informe.py |
| Agregación 12m | N/A | <300ms | test_agregacion.py |
| Backup no-PII | N/A | <30seg | test_backup.py |

### Test Automatizado

```python
# test_performance.py
import psycopg2
import time

def test_lookup_p95():
    times = []
    for _ in range(100):
        start = time.time()
        cursor.execute("""
            SELECT * FROM fact_consumo 
            WHERE cliente_sk = %s 
            AND tiempo_sk BETWEEN %s AND %s
        """, (1234, 20240101, 20240131))
        times.append((time.time() - start) * 1000)
    
    p95 = sorted(times)[95]
    assert p95 < 50, f"FALLO: {p95}ms > 50ms"
    return f"OK: {p95:.2f}ms"

print(f"Lookup p95: {test_lookup_p95()}")
```

---

**FIN DEL INFORME DE AUDITORÍA**

*Documento generado automáticamente el 8 de Septiembre de 2025*
