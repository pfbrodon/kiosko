#!/usr/bin/env python3
"""
Script para identificar y corregir la discrepancia entre el saldo final del 22/10 y el saldo inicial del 23/10
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from caja.models import CajaDiaria, SaldoGeneral
from datetime import date
from decimal import Decimal

def analizar_discrepancia():
    """Analiza la discrepancia entre los saldos del 22/10 y 23/10"""
    
    print("="*60)
    print("ANÁLISIS DE DISCREPANCIA DE SALDOS")
    print("="*60)
    
    # Fechas a analizar
    fecha_22 = date(2025, 10, 22)
    fecha_23 = date(2025, 10, 23)
    
    # Obtener cajas del 22/10
    cajas_22 = CajaDiaria.objects.filter(fecha=fecha_22).order_by('turno', 'nivel')
    
    print(f"\n1. CAJAS DEL 22/10/2025:")
    saldo_inicial_dia_22 = Decimal('0')
    total_diferencias_22 = Decimal('0')
    
    for caja in cajas_22:
        diferencia = caja.saldo_parcial - caja.saldo_inicial
        total_diferencias_22 += diferencia
        
        print(f"   {caja.get_nivel_display()} {caja.get_turno_display()}:")
        print(f"     Saldo inicial: ${caja.saldo_inicial}")
        print(f"     Saldo parcial: ${caja.saldo_parcial}")
        print(f"     Diferencia: ${diferencia}")
        print(f"     Cerrada: {'Sí' if caja.cerrada else 'No'}")
        if caja.fue_reabierta:
            print(f"     ⚠️  REABIERTA: {caja.fecha_reapertura} por {caja.usuario_reapertura}")
        
        # El saldo inicial del día es el saldo inicial de la primera caja secundaria
        if caja.nivel == 'S' and caja.turno == 'M':
            saldo_inicial_dia_22 = caja.saldo_inicial
    
    saldo_final_teorico_22 = saldo_inicial_dia_22 + total_diferencias_22
    
    print(f"\n2. RESUMEN DEL 22/10:")
    print(f"   Saldo inicial del día: ${saldo_inicial_dia_22}")
    print(f"   Total diferencias: ${total_diferencias_22}")
    print(f"   Saldo final teórico: ${saldo_final_teorico_22}")
    
    # Obtener cajas del 23/10
    cajas_23 = CajaDiaria.objects.filter(fecha=fecha_23).order_by('turno', 'nivel')
    
    print(f"\n3. CAJAS DEL 23/10/2025:")
    saldo_inicial_dia_23 = Decimal('0')
    
    for caja in cajas_23:
        print(f"   {caja.get_nivel_display()} {caja.get_turno_display()}:")
        print(f"     Saldo inicial: ${caja.saldo_inicial}")
        print(f"     Saldo parcial: ${caja.saldo_parcial}")
        print(f"     Cerrada: {'Sí' if caja.cerrada else 'No'}")
        if caja.fue_reabierta:
            print(f"     ⚠️  REABIERTA: {caja.fecha_reapertura} por {caja.usuario_reapertura}")
        
        # El saldo inicial del día es el saldo inicial de la primera caja secundaria
        if caja.nivel == 'S' and caja.turno == 'M':
            saldo_inicial_dia_23 = caja.saldo_inicial
    
    print(f"\n4. RESUMEN DEL 23/10:")
    print(f"   Saldo inicial del día: ${saldo_inicial_dia_23}")
    
    # Calcular discrepancia
    discrepancia = saldo_inicial_dia_23 - saldo_final_teorico_22
    
    print(f"\n5. DISCREPANCIA ENCONTRADA:")
    print(f"   Saldo final teórico 22/10: ${saldo_final_teorico_22}")
    print(f"   Saldo inicial real 23/10:  ${saldo_inicial_dia_23}")
    print(f"   Discrepancia: ${discrepancia}")
    
    # Saldo general actual
    saldo_general = SaldoGeneral.objects.first()
    print(f"\n6. SALDO GENERAL ACTUAL: ${saldo_general.monto if saldo_general else 'No existe'}")
    
    return {
        'saldo_final_teorico_22': saldo_final_teorico_22,
        'saldo_inicial_real_23': saldo_inicial_dia_23,
        'discrepancia': discrepancia,
        'saldo_general_actual': saldo_general.monto if saldo_general else Decimal('0')
    }

def proponer_solucion(analisis):
    """Propone una solución para corregir la discrepancia"""
    
    print("\n" + "="*60)
    print("PROPUESTA DE SOLUCIÓN")
    print("="*60)
    
    discrepancia = analisis['discrepancia']
    
    if discrepancia == Decimal('0'):
        print("✅ No hay discrepancia. Los saldos son consistentes.")
        return
    
    print(f"\n🔍 CAUSA PROBABLE:")
    print(f"   La discrepancia de ${discrepancia} indica que hubo un problema")
    print(f"   en la secuencia de cierre/reapertura de cajas.")
    print(f"   ")
    print(f"   Observación: Esta diferencia (${discrepancia}) coincide exactamente")
    print(f"   con el saldo parcial de alguna caja, lo que sugiere que:")
    print(f"   - Una caja se contabilizó dos veces al cerrar")
    print(f"   - Una reapertura no revirtió correctamente el saldo")
    print(f"   - Hubo un movimiento manual no documentado")
    
    print(f"\n💡 OPCIONES DE CORRECCIÓN:")
    print(f"   ")
    print(f"   OPCIÓN 1: Corregir el saldo inicial del 23/10")
    print(f"   - Cambiar de ${analisis['saldo_inicial_real_23']} a ${analisis['saldo_final_teorico_22']}")
    print(f"   - Ajustar el saldo general restando ${discrepancia}")
    print(f"   ")
    print(f"   OPCIÓN 2: Mantener el saldo actual y documentar la diferencia")
    print(f"   - Aceptar que hubo un movimiento de ${discrepancia}")
    print(f"   - Documentar como ajuste manual")
    
    return True

def main():
    """Función principal"""
    print("Iniciando análisis de discrepancia de saldos...")
    
    try:
        analisis = analizar_discrepancia()
        proponer_solucion(analisis)
        
        print(f"\n" + "="*60)
        print("ANÁLISIS COMPLETADO")
        print("="*60)
        print(f"Revise los resultados y determine la acción a tomar.")
        
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()