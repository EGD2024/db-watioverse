#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Mapeo Completo para Invoice
Crea mapeo automático de todos los campos JSON → BD
"""

def generar_mapeo_invoice_completo():
    """Genera mapeo completo para tabla invoice basado en campos reales."""
    
    # Campos BD invoice (208 columnas) - extraidos de la query anterior
    campos_bd = [
        'id', 'año', 'fecha_inicio_periodo', 'fecha_fin_periodo', 'dias_periodo_facturado',
        'numero_factura_rectificada', 'fecha_cargo', 'total_a_pagar', 'tipo_iva', 'importe_iva',
        'porcentaje_impuesto_electricidad', 'importe_impuesto_electricidad', 'bono_social',
        'coste_energia_total', 'coste_potencia_total', 'coste_otro_concepto', 'coste_otro_servicio',
        'coste_promedio_diario_eur', 'alquiler_contador', 'ajuste_mecanismo_iberico',
        'descuento_energia', 'descuento_potencia', 'descuento_servicio', 'descuento_otro_concepto',
        # Consumos P1-P6
        'consumo_kwh_p1', 'consumo_kwh_p2', 'consumo_kwh_p3', 'consumo_kwh_p4', 'consumo_kwh_p5', 'consumo_kwh_p6',
        # Precios peaje P1-P6
        'precio_peaje_p1', 'precio_peaje_p2', 'precio_peaje_p3', 'precio_peaje_p4', 'precio_peaje_p5', 'precio_peaje_p6',
        # Precios energia P1-P6
        'precio_energia_p1', 'precio_energia_p2', 'precio_energia_p3', 'precio_energia_p4', 'precio_energia_p5', 'precio_energia_p6',
        # Precios cargos energia P1-P6
        'precio_cargos_energia_p1', 'precio_cargos_energia_p2', 'precio_cargos_energia_p3', 'precio_cargos_energia_p4', 'precio_cargos_energia_p5', 'precio_cargos_energia_p6',
        # Margen comercializadora P1-P6
        'margen_comercializadora_p1', 'margen_comercializadora_p2', 'margen_comercializadora_p3', 'margen_comercializadora_p4', 'margen_comercializadora_p5', 'margen_comercializadora_p6',
        # Precio total energia P1-P6
        'precio_total_energia_p1', 'precio_total_energia_p2', 'precio_total_energia_p3', 'precio_total_energia_p4', 'precio_total_energia_p5', 'precio_total_energia_p6',
        # Coste peaje P1-P6
        'coste_peaje_p1', 'coste_peaje_p2', 'coste_peaje_p3', 'coste_peaje_p4', 'coste_peaje_p5', 'coste_peaje_p6',
        # Coste energia P1-P6
        'coste_energia_p1', 'coste_energia_p2', 'coste_energia_p3', 'coste_energia_p4', 'coste_energia_p5', 'coste_energia_p6',
        # Coste cargos energia P1-P6
        'coste_cargos_energia_p1', 'coste_cargos_energia_p2', 'coste_cargos_energia_p3', 'coste_cargos_energia_p4', 'coste_cargos_energia_p5', 'coste_cargos_energia_p6',
        # Coste margen comercializadora P1-P6
        'coste_margen_comercializadora_p1', 'coste_margen_comercializadora_p2', 'coste_margen_comercializadora_p3', 'coste_margen_comercializadora_p4', 'coste_margen_comercializadora_p5', 'coste_margen_comercializadora_p6',
        # Coste total energia P1-P6
        'coste_total_energia_p1', 'coste_total_energia_p2', 'coste_total_energia_p3', 'coste_total_energia_p4', 'coste_total_energia_p5', 'coste_total_energia_p6',
        # Precios peaje potencia P1-P6
        'precio_peaje_potencia_p1', 'precio_peaje_potencia_p2', 'precio_peaje_potencia_p3', 'precio_peaje_potencia_p4', 'precio_peaje_potencia_p5', 'precio_peaje_potencia_p6',
        # Precios potencia P1-P6
        'precio_potencia_p1', 'precio_potencia_p2', 'precio_potencia_p3', 'precio_potencia_p4', 'precio_potencia_p5', 'precio_potencia_p6',
        # Precios cargos potencia P1-P6
        'precio_cargos_potencia_p1', 'precio_cargos_potencia_p2', 'precio_cargos_potencia_p3', 'precio_cargos_potencia_p4', 'precio_cargos_potencia_p5', 'precio_cargos_potencia_p6',
        # Margen comercializadora potencia P1-P6
        'margen_comercializadora_potencia_p1', 'margen_comercializadora_potencia_p2', 'margen_comercializadora_potencia_p3', 'margen_comercializadora_potencia_p4', 'margen_comercializadora_potencia_p5', 'margen_comercializadora_potencia_p6',
        # Precio total potencia P1-P6
        'precio_total_potencia_p1', 'precio_total_potencia_p2', 'precio_total_potencia_p3', 'precio_total_potencia_p4', 'precio_total_potencia_p5', 'precio_total_potencia_p6',
        # Coste peaje potencia P1-P6
        'coste_peaje_potencia_p1', 'coste_peaje_potencia_p2', 'coste_peaje_potencia_p3', 'coste_peaje_potencia_p4', 'coste_peaje_potencia_p5', 'coste_peaje_potencia_p6',
        # Coste potencia P1-P6
        'coste_potencia_p1', 'coste_potencia_p2', 'coste_potencia_p3', 'coste_potencia_p4', 'coste_potencia_p5', 'coste_potencia_p6',
        # Coste cargos potencia P1-P6
        'coste_cargos_potencia_p1', 'coste_cargos_potencia_p2', 'coste_cargos_potencia_p3', 'coste_cargos_potencia_p4', 'coste_cargos_potencia_p5', 'coste_cargos_potencia_p6',
        # Coste margen comercializadora potencia P1-P6
        'coste_margen_comercializadora_potencia_p1', 'coste_margen_comercializadora_potencia_p2', 'coste_margen_comercializadora_potencia_p3', 'coste_margen_comercializadora_potencia_p4', 'coste_margen_comercializadora_potencia_p5', 'coste_margen_comercializadora_potencia_p6',
        # Coste total potencia P1-P6
        'coste_total_potencia_p1', 'coste_total_potencia_p2', 'coste_total_potencia_p3', 'coste_total_potencia_p4', 'coste_total_potencia_p5', 'coste_total_potencia_p6',
        # Otros campos
        'consumo_promedio_diario_kwh', 'potencia_facturada_p1', 'potencia_facturada_p2', 'potencia_facturada_p3', 'potencia_facturada_p4', 'potencia_facturada_p5', 'potencia_facturada_p6',
        'potencia_maxima_demandada_año_kw_p1', 'potencia_maxima_demandada_año_kw_p2', 'potencia_maxima_demandada_año_kw_p3', 'potencia_maxima_demandada_año_kw_p4', 'potencia_maxima_demandada_año_kw_p5', 'potencia_maxima_demandada_año_kw_p6',
        'coste_exceso_potencia_p1', 'coste_exceso_potencia_p2', 'coste_exceso_potencia_p3', 'coste_exceso_potencia_p4', 'coste_exceso_potencia_p5', 'coste_exceso_potencia_p6',
        'potencia_maxima_demandada_factura_p1', 'potencia_maxima_demandada_factura_p2', 'potencia_maxima_demandada_factura_p3', 'potencia_maxima_demandada_factura_p4', 'potencia_maxima_demandada_factura_p5', 'potencia_maxima_demandada_factura_p6',
        'autoconsumo', 'energia_vertida_kwh', 'importe_compensacion_excedentes',
        'consumo_reactiva_p1', 'consumo_reactiva_p2', 'consumo_reactiva_p3', 'consumo_reactiva_p4', 'consumo_reactiva_p5', 'consumo_reactiva_p6',
        'energia_reactiva_facturar_p1', 'energia_reactiva_facturar_p2', 'energia_reactiva_facturar_p3', 'energia_reactiva_facturar_p4', 'energia_reactiva_facturar_p5', 'energia_reactiva_facturar_p6',
        'penalizacion_reactiva_p1', 'penalizacion_reactiva_p2', 'penalizacion_reactiva_p3', 'penalizacion_reactiva_p4', 'penalizacion_reactiva_p5', 'penalizacion_reactiva_p6',
        'coste_excesos_energia_reactiva', 'consumo_reactiva_total', 'energia_reactiva_facturar_total',
        'url_qr_comparador_cnmc', 'created_at', 'numero_factura',
        'consumo_medido_kwh_p1', 'consumo_medido_kwh_p2', 'consumo_medido_kwh_p3', 'consumo_medido_kwh_p4', 'consumo_medido_kwh_p5', 'consumo_medido_kwh_p6'
    ]
    
    # Generar código de mapeo
    print("def mapear_datos_invoice(self, datos_json: dict) -> Dict[str, Any]:")
    print('    """Mapea datos de factura desde JSON a estructura BD - MAPEO COMPLETO."""')
    print('    # Buscar datos invoice en múltiples ubicaciones')
    print('    invoice_paths = ["invoice", "invoice_2x3", "factura"]')
    print('    invoice_data = {}')
    print('    for path in invoice_paths:')
    print('        if path in datos_json:')
    print('            invoice_data = datos_json[path]')
    print('            break')
    print()
    print('    return {')
    
    # Mapear campos excluyendo id y created_at (auto-generados)
    for campo in campos_bd:
        if campo in ['id', 'created_at']:
            continue
            
        # Casos especiales
        if campo == 'año':
            print(f"        '{campo}': self.extraer_valor_seguro(invoice_data, 'año') or self.extraer_valor_seguro(invoice_data, 'ano'),")
        elif campo == 'numero_factura':
            print(f"        '{campo}': self.extraer_valor_seguro(datos_json, 'numero_factura') or self.extraer_valor_seguro(invoice_data, 'numero_factura'),")
        elif campo.startswith('consumo_kwh_'):
            # Mapear consumo_kwh_p1 desde invoice_2x3.consumo_facturado_kwh_p1
            periodo = campo.split('_')[-1]  # p1, p2, etc
            print(f"        '{campo}': self.extraer_valor_seguro(invoice_data, 'consumo_facturado_kwh_{periodo}') or self.extraer_valor_seguro(invoice_data, 'consumo_medido_kwh_{periodo}'),")
        else:
            # Mapeo directo
            print(f"        '{campo}': self.extraer_valor_seguro(invoice_data, '{campo}'),")
    
    print('    }')

if __name__ == "__main__":
    generar_mapeo_invoice_completo()
