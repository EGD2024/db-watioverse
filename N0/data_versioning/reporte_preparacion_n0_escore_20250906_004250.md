# REPORTE PREPARACIÓN N0 PARA eSCORE

**Fecha:** 2025-09-06 00:42:50
**Facturas analizadas:** 6

**Estado N0:** ✅ LISTO

## 📊 Métricas de Cobertura

- **Campos críticos:** 100.0% (mínimo: 90%)
- **Campos importantes:** 85.7% (recomendado: 70%)
- **Cobertura total:** 90.5%

## ✅ Campos Encontrados

- **numero_factura** (critico)
  - Indicador: GENERAL → identificacion
  - Ruta: `invoice_3x3.numero_factura`
- **cups** (critico)
  - Indicador: GENERAL → identificacion
  - Ruta: `contract_3x3.cups_electricidad`
- **fecha_factura** (critico)
  - Indicador: GENERAL → identificacion
  - Ruta: `contract_3x3.fecha_inicio_contrato`
- **consumo_facturado_kwh** (critico)
  - Indicador: IC → consumo_anual
  - Ruta: `consumo_energia.consumo_facturado_kwh`
- **consumo_p1** (critico)
  - Indicador: IE → variacion_estacional
  - Ruta: `consumo_energia.consumo_medido_kwh`
- **consumo_p2** (critico)
  - Indicador: IE → variacion_estacional
  - Ruta: `consumo_energia.consumo_medido_kwh`
- **consumo_p3** (critico)
  - Indicador: IE → variacion_estacional
  - Ruta: `consumo_energia.consumo_medido_kwh`
- **potencia_contratada_kw** (critico)
  - Indicador: IP → optimizacion_potencia
  - Ruta: `termino_potencia.potencia_contratada_kw`
- **potencia_maxima_p1** (critico)
  - Indicador: IP → excesos_potencia
  - Ruta: `contract_3x3.potencia_contratada_p1`
- **potencia_maxima_p2** (critico)
  - Indicador: IP → excesos_potencia
  - Ruta: `contract_3x3.potencia_contratada_p1`
- **importe_total_factura** (importante)
  - Indicador: GENERAL → coste
  - Ruta: `consumo_energia.consumo_facturado_kwh`
- **termino_energia** (importante)
  - Indicador: IT → optimizacion_tarifaria
  - Ruta: `consumo_energia.precio_energia_eur_kwh`
- **termino_potencia** (importante)
  - Indicador: IT → optimizacion_tarifaria
  - Ruta: `contract_3x3.potencia_contratada_p1`
- **tarifa_acceso** (importante)
  - Indicador: IT → tipo_peaje
  - Ruta: `contract_3x3.tarifa_acceso`
- **provincia** (importante)
  - Indicador: IC → zona_geografica
  - Ruta: `supply_point.datos_suministro.direccion_suministro.provincia`
- **codigo_postal** (importante)
  - Indicador: IC → zona_geografica
  - Ruta: `supply_point.datos_suministro.direccion_suministro.codigo_postal`
- **energia_reactiva_p1** (opcional)
  - Indicador: IF → factor_potencia_medio
  - Ruta: `consumo_energia.precio_energia_eur_kwh`
- **penalizacion_reactiva_p1** (opcional)
  - Indicador: IF → penalizaciones_reactiva
  - Ruta: `invoice_3x3.penalizacion_reactiva_p1`
- **autoconsumo_kwh** (opcional)
  - Indicador: IR → cobertura_renovable
  - Ruta: `consumo_energia.consumo_medido_kwh`

## ⚠️ Campos Importantes Faltantes

- **tipo_peaje**: Tipo de peaje aplicado

## 💡 Recomendaciones

- ✅ N0 cumple requisitos mínimos para eSCORE
- 🚀 Proceder con implementación N1
