#!/usr/bin/env python3
"""
Script automático para corregir la discrepancia de saldos aplicando la Opción 1
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from caja.models import CajaDiaria, SaldoGeneral
from datetime import date
from decimal import Decimal

def aplicar_correccion_automatica():
    """Aplica la corrección automáticamente"""
    
    print("="*60)
    print("CORRECCIÓN AUTOMÁTICA DE DISCREPANCIA DE SALDOS")
    print("="*60)
    
    # Valores identificados
    discrepancia = Decimal('58000.00')
    fecha_23 = date(2025, 10, 23)
    saldo_correcto_23 = Decimal('317500.00')
    
    try:
        # Obtener la caja secundaria mañana del 23/10
        caja_23 = CajaDiaria.objects.get(fecha=fecha_23, nivel='S', turno='M')
        print(f"\n✅ Caja encontrada: {caja_23.get_nivel_display()} {caja_23.get_turno_display()} del {caja_23.fecha}")
        print(f"   Saldo inicial actual: ${caja_23.saldo_inicial}")
        
        # Obtener saldo general
        saldo_general = SaldoGeneral.objects.first()
        saldo_general_actual = saldo_general.monto
        print(f"   Saldo general actual: ${saldo_general_actual}")
        
        # Aplicar correcciones
        print(f"\n🔧 APLICANDO CORRECCIONES...")
        
        # 1. Corregir saldo inicial de la caja
        caja_23.saldo_inicial = saldo_correcto_23
        caja_23.save()
        print(f"   ✅ Saldo inicial corregido: ${caja_23.saldo_inicial}")
        
        # 2. Recalcular saldo parcial
        caja_23.actualizar_saldo_parcial()
        print(f"   ✅ Saldo parcial recalculado: ${caja_23.saldo_parcial}")
        
        # 3. Corregir saldo general
        saldo_general.monto = saldo_general_actual - discrepancia
        saldo_general.save()
        print(f"   ✅ Saldo general corregido: ${saldo_general.monto}")
        
        # Verificar la corrección
        print(f"\n🔍 VERIFICANDO CORRECCIÓN...")
        
        # Calcular saldo final del 22/10
        fecha_22 = date(2025, 10, 22)
        cajas_22 = CajaDiaria.objects.filter(fecha=fecha_22)
        
        saldo_inicial_22 = Decimal('0')
        total_diferencias_22 = Decimal('0')
        
        for caja in cajas_22:
            if caja.nivel == 'S' and caja.turno == 'M':
                saldo_inicial_22 = caja.saldo_inicial
            diferencia = caja.saldo_parcial - caja.saldo_inicial
            total_diferencias_22 += diferencia
        
        saldo_final_22 = saldo_inicial_22 + total_diferencias_22
        
        # Verificar consistencia
        caja_23_actualizada = CajaDiaria.objects.get(fecha=fecha_23, nivel='S', turno='M')
        diferencia_final = caja_23_actualizada.saldo_inicial - saldo_final_22
        
        print(f"\n📊 RESULTADO DE LA VERIFICACIÓN:")
        print(f"   Saldo final 22/10: ${saldo_final_22}")
        print(f"   Saldo inicial 23/10: ${caja_23_actualizada.saldo_inicial}")
        print(f"   Diferencia: ${diferencia_final}")
        
        if diferencia_final == Decimal('0'):
            print(f"\n🎉 ¡CORRECCIÓN EXITOSA!")
            print(f"   ✅ Los saldos son ahora consistentes")
            print(f"   ✅ No hay discrepancia entre días")
            print(f"   ✅ Saldo general ajustado correctamente")
            return True
        else:
            print(f"\n⚠️  Aún existe una discrepancia de: ${diferencia_final}")
            return False
            
    except CajaDiaria.DoesNotExist:
        print("❌ Error: No se encontró la caja Secundario Mañana del 23/10")
        return False
    except Exception as e:
        print(f"❌ Error durante la corrección: {e}")
        return False

def main():
    """Función principal"""
    print("Iniciando corrección automática de discrepancia de saldos...")
    
    try:
        exito = aplicar_correccion_automatica()
        
        if exito:
            print(f"\n" + "="*60)
            print("✅ CORRECCIÓN COMPLETADA EXITOSAMENTE")
            print("="*60)
            print("• La discrepancia de $58,000 ha sido corregida")
            print("• Los saldos entre días son ahora consistentes")
            print("• El saldo general ha sido ajustado apropiadamente")
            print("\n💡 RECOMENDACIÓN:")
            print("   Revisar la lógica de reapertura de cajas para")
            print("   evitar futuros problemas similares.")
        else:
            print(f"\n" + "="*60)
            print("❌ LA CORRECCIÓN NO FUE COMPLETAMENTE EXITOSA")
            print("="*60)
            print("Por favor revise los resultados y contacte al desarrollador.")
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()