#!/usr/bin/env python3
"""
Script para corregir la discrepancia de saldos aplicando la Opción 1:
- Corregir el saldo inicial del 23/10 de $375,500 a $317,500
- Ajustar el saldo general restando $58,000
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from caja.models import CajaDiaria, SaldoGeneral
from datetime import date
from decimal import Decimal

def aplicar_correccion():
    """Aplica la corrección de la discrepancia de saldos"""
    
    print("="*60)
    print("CORRECCIÓN DE DISCREPANCIA DE SALDOS - OPCIÓN 1")
    print("="*60)
    
    # Valores identificados
    discrepancia = Decimal('58000.00')
    fecha_23 = date(2025, 10, 23)
    saldo_correcto_23 = Decimal('317500.00')
    
    print(f"\n1. VALORES IDENTIFICADOS:")
    print(f"   Discrepancia: ${discrepancia}")
    print(f"   Saldo inicial correcto para el 23/10: ${saldo_correcto_23}")
    
    # Obtener la caja secundaria mañana del 23/10
    try:
        caja_23 = CajaDiaria.objects.get(fecha=fecha_23, nivel='S', turno='M')
        print(f"\n2. CAJA A CORREGIR:")
        print(f"   Fecha: {caja_23.fecha}")
        print(f"   Nivel: {caja_23.get_nivel_display()}")
        print(f"   Turno: {caja_23.get_turno_display()}")
        print(f"   Saldo inicial actual: ${caja_23.saldo_inicial}")
        print(f"   Saldo inicial correcto: ${saldo_correcto_23}")
        
    except CajaDiaria.DoesNotExist:
        print("❌ Error: No se encontró la caja Secundario Mañana del 23/10")
        return False
    
    # Obtener el saldo general
    saldo_general = SaldoGeneral.objects.first()
    if not saldo_general:
        print("❌ Error: No se encontró el saldo general")
        return False
    
    saldo_general_actual = saldo_general.monto
    saldo_general_correcto = saldo_general_actual - discrepancia
    
    print(f"\n3. SALDO GENERAL:")
    print(f"   Saldo actual: ${saldo_general_actual}")
    print(f"   Saldo correcto: ${saldo_general_correcto}")
    print(f"   Ajuste a aplicar: -${discrepancia}")
    
    # Mostrar resumen de cambios
    print(f"\n4. RESUMEN DE CAMBIOS A APLICAR:")
    print(f"   ┌─ Caja Secundario Mañana 23/10:")
    print(f"   │  Saldo inicial: ${caja_23.saldo_inicial} → ${saldo_correcto_23}")
    print(f"   └─ Diferencia: -${discrepancia}")
    print(f"   ")
    print(f"   ┌─ Saldo General:")
    print(f"   │  Monto: ${saldo_general_actual} → ${saldo_general_correcto}")
    print(f"   └─ Diferencia: -${discrepancia}")
    
    # Solicitar confirmación
    print(f"\n⚠️  CONFIRMACIÓN REQUERIDA")
    print(f"Esta operación modificará datos críticos del sistema.")
    print(f"¿Está seguro de que desea continuar? (escriba 'CONFIRMAR' para proceder)")
    
    confirmacion = input("\nRespuesta: ").strip()
    
    if confirmacion != 'CONFIRMAR':
        print("\n❌ Operación cancelada por el usuario.")
        return False
    
    # Aplicar correcciones
    print(f"\n5. APLICANDO CORRECCIONES...")
    
    try:
        # Corregir el saldo inicial de la caja del 23/10
        caja_23.saldo_inicial = saldo_correcto_23
        caja_23.save()
        print(f"   ✅ Saldo inicial de la caja corregido")
        
        # Recalcular el saldo parcial de la caja
        saldo_parcial_anterior = caja_23.saldo_parcial
        caja_23.actualizar_saldo_parcial()
        print(f"   ✅ Saldo parcial recalculado: ${saldo_parcial_anterior} → ${caja_23.saldo_parcial}")
        
        # Corregir el saldo general
        saldo_general.monto = saldo_general_correcto
        saldo_general.save()
        print(f"   ✅ Saldo general corregido")
        
        print(f"\n6. CORRECCIÓN COMPLETADA EXITOSAMENTE")
        print(f"   ┌─ Caja 23/10 actualizada")
        print(f"   ├─ Saldo general ajustado")
        print(f"   └─ Consistencia restaurada")
        
        # Verificar la corrección
        return verificar_correccion()
        
    except Exception as e:
        print(f"❌ Error al aplicar las correcciones: {e}")
        return False

def verificar_correccion():
    """Verifica que la corrección se aplicó correctamente"""
    
    print(f"\n" + "="*60)
    print("VERIFICACIÓN DE LA CORRECCIÓN")
    print("="*60)
    
    try:
        # Verificar cajas del 22/10 y 23/10
        fecha_22 = date(2025, 10, 22)
        fecha_23 = date(2025, 10, 23)
        
        # Calcular saldo final del 22/10
        cajas_22 = CajaDiaria.objects.filter(fecha=fecha_22)
        saldo_inicial_22 = Decimal('0')
        total_diferencias_22 = Decimal('0')
        
        for caja in cajas_22:
            if caja.nivel == 'S' and caja.turno == 'M':
                saldo_inicial_22 = caja.saldo_inicial
            diferencia = caja.saldo_parcial - caja.saldo_inicial
            total_diferencias_22 += diferencia
        
        saldo_final_22 = saldo_inicial_22 + total_diferencias_22
        
        # Obtener saldo inicial del 23/10
        caja_23 = CajaDiaria.objects.get(fecha=fecha_23, nivel='S', turno='M')
        saldo_inicial_23 = caja_23.saldo_inicial
        
        # Obtener saldo general
        saldo_general = SaldoGeneral.objects.first()
        
        print(f"\n1. VERIFICACIÓN DE CONSISTENCIA:")
        print(f"   Saldo final 22/10: ${saldo_final_22}")
        print(f"   Saldo inicial 23/10: ${saldo_inicial_23}")
        print(f"   Diferencia: ${saldo_inicial_23 - saldo_final_22}")
        
        print(f"\n2. ESTADO ACTUAL:")
        print(f"   Saldo general: ${saldo_general.monto}")
        
        # Verificar si la corrección fue exitosa
        if saldo_inicial_23 == saldo_final_22:
            print(f"\n✅ CORRECCIÓN EXITOSA")
            print(f"   Los saldos son ahora consistentes")
            print(f"   No hay discrepancia entre días")
            return True
        else:
            diferencia = saldo_inicial_23 - saldo_final_22
            print(f"\n⚠️  ADVERTENCIA")
            print(f"   Aún existe una discrepancia de: ${diferencia}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        return False

def main():
    """Función principal"""
    print("Iniciando corrección de discrepancia de saldos...")
    print("OPCIÓN 1: Corregir los datos para mantener consistencia")
    
    try:
        exito = aplicar_correccion()
        
        if exito:
            print(f"\n" + "="*60)
            print("✅ CORRECCIÓN COMPLETADA EXITOSAMENTE")
            print("="*60)
            print("La discrepancia ha sido corregida y los saldos son consistentes.")
            print("Se recomienda revisar la lógica de reapertura de cajas para")
            print("evitar futuros problemas similares.")
        else:
            print(f"\n" + "="*60)
            print("❌ CORRECCIÓN NO COMPLETADA")
            print("="*60)
            print("Por favor revise los errores y vuelva a intentar.")
        
    except KeyboardInterrupt:
        print(f"\n\n❌ Operación interrumpida por el usuario.")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()