# REPORTE VALIDACIÓN SCHEMAS N0 vs ELECTRICIDAD ES

## 📊 Resumen General

- **Facturas N0 validadas**: 6
- **Campos definidos en schemas**: 368
- **Campos encontrados en N0**: 0
- **Porcentaje coincidencia**: 0.0%
- **Campos faltantes**: 368
- **Campos extra en N0**: 397

**Estado de coincidencia**: ❌ DEFICIENTE

## ❌ Campos Faltantes en N0

Los siguientes campos están definidos en los schemas pero no se encontraron en las facturas N0:

### 🚨 Campos Críticos (Requeridos)

- **base_imponible** (number)
  - Schema: `financial_summary.json`
- **consumo_facturado_kwh** (number)
  - Consumo de energía eléctrica facturado en la línea de factura en kWh para el período.
  - Schema: `consumo_energia.json`
- **coste_total_energia_eur** (number)
  - Importe total en euros para este periodo de consumo (suma de todos los componentes de coste).
  - Schema: `consumo_energia.json`
- **coste_total_potencia_eur** (number)
  - Importe total en euros para este periodo de potencia (suma de todos los componentes de coste).
  - Schema: `termino_potencia.json`
- **dias_facturacion** (integer)
  - Número total de días que cubre el período de facturación.
  - Schema: `termino_potencia.json`
- **excedente_kwh** (number)
  - Energía excedentaria vertida a la red en kilovatios-hora (kWh).
  - Schema: `autoconsumo.json`
- **exceso_potencia_kw** (number)
  - Exceso de potencia sobre la contratada en kilovatios (kW).
  - Schema: `excesos_potencia.json`
- **fecha_presupuesto** (string)
  - Schema: `budget_header.json`
- **importe_compensacion_eur** (number)
  - Importe total de la compensación en euros por los excedentes (excedente_kwh * precio_eur_kwh).
  - Schema: `autoconsumo.json`
- **importe_excesos_potencia_eur** (number)
  - Importe total en euros por el exceso de potencia.
  - Schema: `excesos_potencia.json`

### ⚠️ Campos Opcionales

- `ajuste_mecanismo_iberico`
- `alquiler_contador`
- `autoconsumo`
- `año`
- `bono_social`
- `comercializadora`
- `condiciones_ofertadas`
- `condiciones_ofertadas.descuentos`
- `condiciones_ofertadas.nombre_tarifa`
- `condiciones_ofertadas.permanencia_meses`
- `condiciones_ofertadas.precios_energia_eur_kwh`
- `condiciones_ofertadas.precios_potencia_eur_kw_dia`
- `consumo_facturado_capacitiva_kvarh`
- `consumo_facturado_capacitiva_p1`
- `consumo_facturado_capacitiva_p2`
- ... y 334 más

## ➕ Campos Extra en N0

Los siguientes campos están presentes en N0 pero no definidos en schemas:

- `client`
- `client.nif_titular`
- `client.nif_titular.confidence`
- `client.nif_titular.pattern`
- `client.nif_titular.source`
- `client.nif_titular.value`
- `client.nombre_cliente`
- `consumo_energia`
- `consumo_energia.consumo_facturado_kwh`
- `consumo_energia.consumo_medido_kwh`
- `consumo_energia.coste_cargos_eur`
- `consumo_energia.coste_energia_eur`
- `consumo_energia.coste_margen_comercializadora_eur`
- `consumo_energia.coste_peaje_eur`
- `consumo_energia.coste_total_energia_eur`
- `consumo_energia.fin_periodo`
- `consumo_energia.inicio_periodo`
- `consumo_energia.margen_comercializadora_eur_kwh`
- `consumo_energia.precio_cargos_eur_kwh`
- `consumo_energia.precio_energia_eur_kwh`
- ... y 376 más

## 💡 Recomendaciones

- 🚨 **CRÍTICO**: Baja coincidencia de campos. Revisar proceso de extracción.
- 🔧 **Mejora extracción**: Muchos campos faltantes. Actualizar parsers OCR.
- 📋 **Actualizar schemas**: Muchos campos extra. Considerar actualizar schemas.
- 🔄 **Monitorización continua**: Ejecutar validación regularmente para detectar mejoras.
- 📊 **Versionado N0**: Usar sistema de versionado para trackear mejoras en extracción.
