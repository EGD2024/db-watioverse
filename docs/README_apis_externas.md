<p align="center">
  <img src="assets/EGD.png" alt="Energy Green Data" width="400"/>
</p>

# 🌐 APIs Externas - Estado y Configuración

![Versión](https://img.shields.io/badge/versión-3.0.0-blue)
![Estado](https://img.shields.io/badge/estado-parcial-yellow)
![APIs Funcionales](https://img.shields.io/badge/APIs_funcionales-4/8-orange)
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

El sistema integra **8 APIs externas** para enriquecimiento de datos energéticos. **4 APIs están funcionales** y **4 están bloqueadas** o pendientes de implementación. Estado validado por auditoría MCP exhaustiva.

### Resumen Ejecutivo

| Métrica | Valor | Estado |
|---------|-------|--------|
| **APIs Totales** | 8 | 📊 INVENTARIADAS |
| **APIs Funcionales** | 4 | ✅ 50% OPERATIVO |
| **APIs Bloqueadas** | 4 | ❌ REQUIERE ACCIÓN |
| **Datos Poblados** | 4,087/11,830 zonas | 🔄 35% COMPLETO |

---

## ✅ APIs Funcionales

### 1. REE Mercados (PVPC)
- **Estado**: ✅ FUNCIONAL
- **Endpoint**: `mercados/precios-mercados-tiempo-real`
- **Datos**: Precios PVPC horarios
- **Implementación**: `core_precios_omie`
- **Rate Limit**: Sin restricciones detectadas
- **Última validación**: 9 Sept 2025

```python
# Ejemplo de uso
REE_MERCADOS_ENDPOINT = "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
```

### 2. Open-Meteo
- **Estado**: ✅ FUNCIONAL
- **Datos**: HDD, CDD, temperatura media, radiación
- **Implementación**: `core_zonas_climaticas`
- **Progreso**: 4,087/11,830 códigos postales (35%)
- **Rate Limit**: Generoso, sin bloqueos

```python
# Configuración
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
```

### 3. Nominatim (OpenStreetMap)
- **Estado**: ✅ FUNCIONAL
- **Datos**: Geocodificación de códigos postales
- **Uso**: Conversión CP → coordenadas GPS
- **Rate Limit**: 1 req/seg (respetado)
- **Timeouts**: Ocasionales pero manejados

### 4. PVGIS (Photovoltaic GIS)
- **Estado**: ✅ FUNCIONAL
- **Datos**: Radiación solar para fotovoltaica
- **Implementación**: `core_pvgis_radiacion`
- **Cobertura**: Europa completa

---

## ❌ APIs Bloqueadas

### 1. REE Generación Mix
- **Estado**: ❌ BLOQUEADA
- **Endpoint**: `generacion/estructura-generacion`
- **Error**: HTTP 403/500 - Incapsula/Cloudflare blocking
- **Datos**: Mix energético nacional por horas
- **Impacto**: ALTO - Crítico para scoring sostenibilidad

```bash
# Error típico
HTTP 403 Forbidden - Incapsula incident ID: xxx
```

### 2. REE Emisiones CO2
- **Estado**: ❌ BLOQUEADA
- **Endpoint**: `generacion/emisiones-co2`
- **Error**: HTTP 403/500 - Incapsula/Cloudflare blocking
- **Datos**: Emisiones CO2 por kWh
- **Impacto**: ALTO - Esencial para huella carbono

### 3. ESIOS (REE Oficial)
- **Estado**: ❌ BLOQUEADA
- **Token**: `511a5399534031be32848c7fbc85cafc0e618db32c6cbebe5b3d6dd103017ff9`
- **Error**: HTTP 403 Forbidden
- **Causa**: Token inválido/expirado o restricciones uso
- **Datos**: Datos oficiales sistema eléctrico español

### 4. Catastro OVC
- **Estado**: ⚠️ IMPLEMENTADO NO VALIDADO
- **Endpoints**: `Consulta_RCCOOR_Distancia`, `Consulta_DNPRC`
- **Datos**: Superficie construida, uso inmuebles
- **Impacto**: MEDIO - Para métricas kWh/m²

---

## 🔄 Plan de Contingencia

### Alternativas Implementadas

| API Bloqueada | Alternativa | Estado | Prioridad |
|---------------|-------------|--------|-----------|
| **REE Mix** | ENTSO-E Transparency | 🔄 PENDIENTE | 🔴 ALTA |
| **REE CO2** | ENTSO-E Transparency | 🔄 PENDIENTE | 🔴 ALTA |
| **ESIOS** | REE CSV manual | 🔄 PENDIENTE | 🟡 MEDIA |
| **REE Generación** | Mock data temporal | ✅ IMPLEMENTADO | 🟢 BAJA |

### ENTSO-E Transparency Platform
- **URL**: `https://transparency.entsoe.eu/api`
- **Datos**: Mix energético y CO2 Europa
- **Ventaja**: API oficial, sin bloqueos
- **Desventaja**: Requiere registro y token

### Mock Data Temporal
```python
# Datos simulados para testing
mock_co2_data = {
    "timestamp": "2025-09-09T12:00:00Z",
    "co2_intensity": 250,  # gCO2/kWh
    "renewable_percentage": 45.2
}
```

---

## ⚙️ Configuración

### Variables de Entorno

```bash
# APIs Funcionales
OPEN_METEO_API_KEY=libre
PVGIS_API_KEY=libre
NOMINATIM_USER_AGENT="EnergyGreenData/1.0"

# APIs Bloqueadas
ESIOS_API_TOKEN=511a5399534031be32848c7fbc85cafc0e618db32c6cbebe5b3d6dd103017ff9
REE_API_BASE=https://apidatos.ree.es/es/datos

# Alternativas
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

| API | Requests/día | Success Rate | Avg Response |
|-----|--------------|--------------|--------------|
| **REE Mercados** | ~24 | 95% | 1.2s |
| **Open-Meteo** | ~100 | 90% | 0.8s |
| **Nominatim** | ~50 | 85% | 2.1s |
| **PVGIS** | ~10 | 98% | 1.5s |

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
- [ ] Registro ENTSO-E Transparency
- [ ] Implementar fallback ENTSO-E
- [ ] Validar Catastro OVC
- [ ] Completar 7,743 zonas climáticas restantes

### Medio Plazo (1-2 meses)
- [ ] Renovar token ESIOS
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
