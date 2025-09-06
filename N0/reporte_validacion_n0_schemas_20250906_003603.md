# REPORTE VALIDACIÓN SCHEMAS N0 vs ELECTRICIDAD ES

## 📊 Resumen General

- **Facturas N0 validadas**: 6
- **Campos definidos en schemas**: 368
- **Campos encontrados en N0**: 5
- **Porcentaje coincidencia**: 1.4%
- **Campos faltantes**: 363
- **Campos extra en N0**: 15

**Estado de coincidencia**: ❌ DEFICIENTE

## ❌ Campos Faltantes en N0

Los siguientes campos están definidos en los schemas pero no se encontraron en las facturas N0:

### 🚨 Campos Críticos (Requeridos)

- **base_imponible** (number)
  - Schema: `financial_summary.json`
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
- **numero_presupuesto** (string)
  - Schema: `budget_header.json`

### ⚠️ Campos Opcionales

- `ajuste_mecanismo_iberico`
- `alquiler_contador`
- `autoconsumo`
- `año`
- `bono_social`
- `condiciones_ofertadas`
- `condiciones_ofertadas.descuentos`
- `condiciones_ofertadas.nombre_tarifa`
- `condiciones_ofertadas.permanencia_meses`
- `condiciones_ofertadas.precios_energia_eur_kwh`
- `condiciones_ofertadas.precios_potencia_eur_kw_dia`
- `consumo_facturado_capacitiva_kvarh`
- `consumo_facturado_capacitiva_p1`
- `consumo_facturado_capacitiva_p2`
- `consumo_facturado_capacitiva_p3`
- ... y 330 más

## ➕ Campos Extra en N0

Los siguientes campos están presentes en N0 pero no definidos en schemas:

- `codigo_postal`
- `consumo_p1`
- `consumo_p2`
- `consumo_p3`
- `cups`
- `fecha_factura`
- `importe_total_factura`
- `nif_titular`
- `nombre_cliente`
- `potencia_maxima_p1`
- `potencia_maxima_p2`
- `provincia`
- `termino_energia`
- `termino_potencia`
- `tipo_peaje`

## 💡 Recomendaciones

- 🚨 **CRÍTICO**: Baja coincidencia de campos. Revisar proceso de extracción.
- 🔧 **Mejora extracción**: Muchos campos faltantes. Actualizar parsers OCR.
- 🔄 **Monitorización continua**: Ejecutar validación regularmente para detectar mejoras.
- 📊 **Versionado N0**: Usar sistema de versionado para trackear mejoras en extracción.
