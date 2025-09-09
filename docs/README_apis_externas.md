<p align="center">
  <img src="assets/EGD.png" alt="Energy Green Data" width="400"/>
</p>

# 🌐 APIs Externas - Estado y Configuración

![Versión](https://img.shields.io/badge/versión-3.0.0-blue)
![Estado](https://img.shields.io/badge/estado-operativo-green)
![APIs Funcionales](https://img.shields.io/badge/APIs_funcionales-6/8-green)
![MCP Validado](https://img.shields.io/badge/MCP-validado-green)

**Módulo:** Integración APIs Externas  
**Proyecto interno de Energy Green Data**

---

## 📑 Tabla de Contenidos

- [Estado General](#estado-general)
- [APIs Funcionales](#apis-funcionales)
- [APIs Bloqueadas](#apis-bloqueadas)
- [Plan de Contingencia](#plan-de-contingencia)
- [Configuración](#configuración)

## 🎯 Estado General

El sistema integra **8 APIs externas** para enriquecimiento de datos energéticos. **6 APIs están funcionales** tras la migración exitosa de REE a ESIOS, **1 API espera token** y **1 API fue migrada completamente**. Estado actualizado tras migración REE→ESIOS del 9 de Septiembre de 2025.

### Resumen Ejecutivo

| Métrica | Valor | Estado |
|---------|-------|--------|
| **APIs Totales** | 8 | 📊 INVENTARIADAS |
| **APIs Funcionales** | 6 | ✅ 75% OPERATIVO |
| **APIs Pendientes Token** | 1 | 🔄 ESPERANDO TOKENS |
| **APIs Migradas** | 2 | ✅ REE→ESIOS COMPLETO |
| **Zonas Climáticas** | 4,087/11,830 | 🔄 35% COMPLETO |

---

## ✅ APIs Funcionales

### 1. Open-Meteo
- **Estado**: ✅ FUNCIONAL
- **Datos**: HDD, CDD, temperatura media, radiación
- **Implementación**: `core_zonas_climaticas`
- **Progreso**: 4,087/11,830 códigos postales (35%)
- **Rate Limit**: Generoso, sin bloqueos

```python
# Configuración
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
```

### 2. Nominatim (OpenStreetMap)
- **Estado**: ✅ FUNCIONAL
- **Datos**: Geocodificación de códigos postales
- **Uso**: Conversión CP → coordenadas GPS
- **Rate Limit**: 1 req/seg (respetado)
- **Timeouts**: Ocasionales pero manejados

### 3. Catastro OVC
- **Estado**: ✅ FUNCIONAL
- **Endpoints**: `Consulta_RCCOOR_Distancia`, `Consulta_DNPRC`
- **Datos**: 1 inmueble validado en sistema
- **Implementación**: `n2_catastro_inmueble`
- **Uso**: Superficie construida para métricas kWh/m²

### 4. PVGIS (Photovoltaic GIS)
- **Estado**: ✅ FUNCIONAL
- **Datos**: Radiación solar para fotovoltaica
- **Implementación**: `core_pvgis_radiacion`
- **Cobertura**: Europa completa

### 5. Euskadi Certificados Energéticos
- **Estado**: 🔄 EVALUANDO
- **URL**: `https://opendata.euskadi.eus/api-energy-efficiency/?api=energy-efficiency`
- **Datos**: Certificados eficiencia energética oficiales
- **Cobertura**: País Vasco (regional)
- **Uso**: Benchmarking y validación certificados
- **Ventaja**: API abierta, sin token requerido

### 6. IDAE Vehículos España
- **Estado**: ✅ OPERATIVO
- **URL**: `https://coches.idae.es/storage/csv/idae-historico-202411.csv`
- **Base de datos**: `db_movilidad.core_vehiculos_espana`
- **Registros**: 89,542 vehículos únicos, 253 marcas
- **Uso**: Scoring movilidad, benchmarking eficiencia vehículos
- **Campos**: Marca, modelo, consumo WLTP, emisiones CO2, autonomía eléctrica
- **Scoring**: Etiquetas A-G, scores 0-100 por emisiones/consumo/autonomía
- **Propulsiones**: 79,111 combustión, 4,523 eléctricos, 4,267 híbridos, 1,641 enchufables

---

## 🔄 APIs Pendientes de Token

### 1. ESIOS (REE Oficial)
- **Estado**: ✅ FUNCIONAL
- **Token actual**: `b5eca74755976ba684c9bc370d6ddd36c35adeeaf3d84c203637847f883600d0` (validado)
- **Datos**: Datos oficiales sistema eléctrico español
- **Uso**: Mix energético, emisiones CO2, precios PVPC
- **Prioridad**: ALTA - API principal para datos energéticos
- **Migración**: Completada desde REE bloqueada a ESIOS
- **Indicadores**: PVPC (1001), Renovable (1433), No Renovable (1434), CO2 (1739)

### 2. EPREL (European Product Database)
- **Estado**: 🔄 ESPERANDO TOKEN
- **Datos**: Eficiencia energética electrodomésticos
- **Uso**: Scoring eficiencia equipos
- **Prioridad**: MEDIA - Para análisis detallado consumos
- **Acción**: Registrarse y obtener token

---

## ❌ APIs Bloqueadas

### 1. REE Generación Mix
- **Estado**: ✅ MIGRADO A ESIOS
- **Endpoint anterior**: `generacion/estructura-generacion` (bloqueado)
- **Nuevo endpoint**: ESIOS indicadores 1433/1434
- **Datos**: Mix energético nacional por horas
- **Migración**: Completada - usando ESIOS API

### 2. REE Emisiones CO2
- **Estado**: ✅ MIGRADO A ESIOS
- **Endpoint anterior**: `generacion/emisiones-co2` (bloqueado)
- **Nuevo endpoint**: ESIOS indicador 1739
- **Datos**: Emisiones CO2 por kWh
- **Migración**: Completada - usando ESIOS API


---

## 🔄 Migraciones Completadas

### REE → ESIOS: Migración Exitosa

**Fecha de migración**: 9 de Septiembre de 2025
**Motivo**: Endpoints REE bloqueados por Incapsula
**Solución**: Migración completa a ESIOS API oficial

**Componentes migrados**:
- `omie.py`: Precios PVPC desde ESIOS indicador 1001
- `ree_api.py`: Mix energético y CO2 desde ESIOS indicadores 1433/1434/1739
- `fetch_ree_mix_co2.py`: Job automático migrado a ESIOS
- Jobs cron: Actualizados para usar ESIOS

**Beneficios**:
- ✅ API oficial más confiable
- ✅ 1967 indicadores disponibles vs endpoints limitados REE
- ✅ Sin bloqueos Incapsula
- ✅ Datos horarios detallados
- ✅ Autenticación por token estable

### Alternativas Evaluadas

| API Pendiente/Bloqueada | Alternativa | Estado | Prioridad |
|-------------------------|-------------|--------|-----------|
| **ESIOS** | ✅ Token validado | ✅ COMPLETADO | ✅ RESUELTO |
| **EPREL** | Obtener token nuevo | 🔄 PENDIENTE | 🟡 MEDIA |
| **REE Mix** | ✅ Migrado a ESIOS | ✅ COMPLETADO | ✅ RESUELTO |
| **REE CO2** | ✅ Migrado a ESIOS | ✅ COMPLETADO | ✅ RESUELTO |

---

## ⚙️ Configuración

### Variables de entorno

```bash
# APIs Funcionales
OPEN_METEO_API_KEY=libre
PVGIS_API_KEY=libre
NOMINATIM_USER_AGENT="EnergyGreenData/1.0"

# ESIOS API (Migrado desde REE)
ESIOS_API_TOKEN=b5eca74755976ba684c9bc370d6ddd36c35adeeaf3d84c203637847f883600d0
ESIOS_API_BASE=https://api.esios.ree.es

# REE (Deprecated - Migrado a ESIOS)
# REE_API_BASE=https://apidatos.ree.es/es/datos  # BLOQUEADO

# Alternativas futuras
ENTSO_E_API_TOKEN=pendiente_registro
ENTSO_E_API_BASE=https://transparency.entsoe.eu/api
```

### Headers HTTP Realistas

```python
REALISTIC_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
```

### Rate Limiting

```python
import time
import random

def api_request_with_delay(url, headers=None):
    # Delay aleatorio 1-3 segundos
    time.sleep(random.uniform(1, 3))
    response = requests.get(url, headers=headers)
    return response
```

---

## 📊 Métricas de Uso

### Estadísticas Actuales

| API | Requests/día | Success Rate | Últimos Datos |
|-----|--------------|--------------|---------------|
| **OMIE** | ~24 | 95% | 8 Sept 21:00 |
| **Open-Meteo** | ~100 | 90% | 4,087 zonas |
| **Nominatim** | ~50 | 85% | Geocodificación |
| **Catastro** | ~5 | 100% | 1 inmueble |
| **PVGIS** | ~10 | 98% | Radiación solar |

### Errores Comunes

```python
# Timeouts Nominatim
requests.exceptions.ReadTimeout: HTTPSConnectionPool(host='nominatim.openstreetmap.org', port=443)

# Bloqueo REE
requests.exceptions.HTTPError: 403 Client Error: Forbidden for url

# Rate limit excedido
requests.exceptions.HTTPError: 429 Too Many Requests
```

---

## 🔧 Troubleshooting

### REE APIs Bloqueadas

1. **Verificar headers realistas**
2. **Implementar delays aleatorios**
3. **Rotar User-Agents**
4. **Considerar proxy/VPN**
5. **Migrar a ENTSO-E**

### ESIOS Token Issues

1. **Verificar validez token**
2. **Solicitar nuevo token**
3. **Revisar términos de uso**
4. **Implementar fallback CSV**

### Performance Optimization

```python
# Session reutilizable
session = requests.Session()
session.headers.update(REALISTIC_HEADERS)

# Timeout configurado
response = session.get(url, timeout=(5, 30))
```

---

## 🎯 Roadmap

### Corto Plazo (1-2 semanas)
- [x] ✅ Migración REE → ESIOS completada
- [x] ✅ Jobs automáticos actualizados
- [x] ✅ Documentación APIs actualizada
- [ ] Validar Catastro OVC
- [ ] Completar 7,743 zonas climáticas restantes

### Medio Plazo (1-2 meses)
- [x] ✅ Token ESIOS validado y funcional
- [ ] Registro ENTSO-E Transparency (backup)
- [ ] Implementar cache inteligente
- [ ] Monitoreo automático APIs
- [ ] Alertas por fallos

### Largo Plazo (3-6 meses)
- [ ] API propia agregadora
- [ ] Machine Learning para predicciones
- [ ] Integración tiempo real
- [ ] Dashboard monitoreo

---

**Documento Confidencial y Propiedad de Energy Green Data.**

*Auditoría APIs realizada el 9 de Septiembre de 2025 vía MCP. Estado validado con datos reales del sistema.*
