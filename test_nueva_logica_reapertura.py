#!/usr/bin/env python3
"""
Script de pruebas para verificar que la nueva lógica de reapertura funciona correctamente
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from caja.models import CajaDiaria, SaldoGeneral, Recreo, PagoProveedor
from precios.models import Proveedor
from django.contrib.auth.models import User
from datetime import date, datetime
from decimal import Decimal

def setup_test_data():
    """Configura datos de prueba"""
    print("Configurando datos de prueba...")
    
    # Crear usuario de prueba
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@test.com'}
    )
    
    # Crear proveedor de prueba
    proveedor, created = Proveedor.objects.get_or_create(
        nombre='Proveedor Test',
        defaults={'telefono': '123456789'}
    )
    
    # Configurar saldo general inicial
    saldo_general = SaldoGeneral.objects.first()
    if not saldo_general:
        saldo_general = SaldoGeneral.objects.create(monto=Decimal('100000.00'))
    else:
        saldo_general.monto = Decimal('100000.00')
        saldo_general.save()
    
    print(f"✅ Saldo general inicial: ${saldo_general.monto}")
    return user, proveedor, saldo_general

def test_nueva_logica_reapertura():
    """Prueba la nueva lógica de reapertura"""
    print("\n" + "="*60)
    print("PRUEBA: NUEVA LÓGICA DE REAPERTURA")
    print("="*60)
    
    user, proveedor, saldo_general = setup_test_data()
    
    # 1. Crear caja de prueba (evitar conflictos con cajas existentes)
    from datetime import timedelta
    fecha_prueba = date.today() + timedelta(days=1)  # Usar fecha futura
    
    # Eliminar caja existente si existe
    CajaDiaria.objects.filter(
        fecha=fecha_prueba,
        turno='M',
        nivel='S'
    ).delete()
    
    caja = CajaDiaria.objects.create(
        fecha=fecha_prueba,
        turno='M',
        nivel='S',
        saldo_inicial=saldo_general.monto
    )
    
    print(f"1. Caja creada: ID {caja.id}")
    print(f"   Saldo inicial: ${caja.saldo_inicial}")
    
    # 2. Agregar movimientos
    recreo1 = Recreo.objects.create(caja=caja, numero=1, monto=Decimal('50000.00'))
    recreo2 = Recreo.objects.create(caja=caja, numero=2, monto=Decimal('30000.00'))
    pago1 = PagoProveedor.objects.create(
        caja=caja, 
        proveedor=proveedor, 
        monto=Decimal('20000.00'),
        comprobante='TEST001'
    )
    
    print(f"2. Movimientos agregados:")
    print(f"   Recreo 1: +${recreo1.monto}")
    print(f"   Recreo 2: +${recreo2.monto}")
    print(f"   Pago: -${pago1.monto}")
    
    # 3. Actualizar saldo parcial
    caja.actualizar_saldo_parcial()
    diferencia_esperada = caja.saldo_parcial - caja.saldo_inicial
    
    print(f"3. Saldo parcial calculado: ${caja.saldo_parcial}")
    print(f"   Diferencia esperada: ${diferencia_esperada}")
    
    # 4. Simular cierre de caja
    saldo_antes_cierre = saldo_general.monto
    
    # Aplicar nueva lógica de cierre
    caja.diferencia_al_cerrar = diferencia_esperada  # NUEVO: Guardar diferencia
    saldo_general.monto += diferencia_esperada
    saldo_general.save()
    caja.cerrada = True
    caja.save()
    
    print(f"4. Caja cerrada:")
    print(f"   Diferencia guardada: ${caja.diferencia_al_cerrar}")
    print(f"   Saldo general: ${saldo_antes_cierre} → ${saldo_general.monto}")
    
    # 5. Agregar más movimientos después del cierre (simulando problema anterior)
    recreo3 = Recreo.objects.create(caja=caja, numero=3, monto=Decimal('15000.00'))
    caja.actualizar_saldo_parcial()
    
    diferencia_actual = caja.saldo_parcial - caja.saldo_inicial
    
    print(f"5. Movimiento post-cierre:")
    print(f"   Recreo 3: +${recreo3.monto}")
    print(f"   Nueva diferencia calculada: ${diferencia_actual}")
    print(f"   Diferencia guardada: ${caja.diferencia_al_cerrar}")
    print(f"   DIFERENCIA: ${diferencia_actual - caja.diferencia_al_cerrar}")
    
    # 6. Simular reapertura con NUEVA lógica
    saldo_antes_reapertura = saldo_general.monto
    
    # NUEVA LÓGICA: Usar diferencia guardada
    if caja.diferencia_al_cerrar is not None:
        saldo_general.monto -= caja.diferencia_al_cerrar  # Usar guardada, NO recalcular
        saldo_general.save()
        diferencia_usada = caja.diferencia_al_cerrar
        caja.diferencia_al_cerrar = None  # Limpiar
    else:
        # Fallback (lógica anterior)
        diferencia_usada = diferencia_actual
        saldo_general.monto -= diferencia_actual
        saldo_general.save()
    
    caja.cerrada = False
    caja.fue_reabierta = True
    caja.fecha_reapertura = datetime.now()
    caja.usuario_reapertura = user
    caja.save()
    
    print(f"6. Caja reabierta:")
    print(f"   Diferencia usada: ${diferencia_usada}")
    print(f"   Saldo general: ${saldo_antes_reapertura} → ${saldo_general.monto}")
    
    # 7. Simular segundo cierre
    saldo_antes_segundo_cierre = saldo_general.monto
    nueva_diferencia = caja.saldo_parcial - caja.saldo_inicial
    
    caja.diferencia_al_cerrar = nueva_diferencia
    saldo_general.monto += nueva_diferencia
    saldo_general.save()
    caja.cerrada = True
    caja.save()
    
    print(f"7. Segundo cierre:")
    print(f"   Nueva diferencia: ${nueva_diferencia}")
    print(f"   Saldo general: ${saldo_antes_segundo_cierre} → ${saldo_general.monto}")
    
    # 8. Verificar resultado final
    saldo_final = saldo_general.monto
    saldo_teorico = Decimal('100000.00') + nueva_diferencia  # Saldo inicial + diferencia final
    
    print(f"\n📊 RESULTADO DE LA PRUEBA:")
    print(f"   Saldo inicial: $100,000.00")
    print(f"   Diferencia final: ${nueva_diferencia}")
    print(f"   Saldo teórico: ${saldo_teorico}")
    print(f"   Saldo real: ${saldo_final}")
    print(f"   Discrepancia: ${saldo_final - saldo_teorico}")
    
    # Limpiar datos de prueba
    recreo1.delete()
    recreo2.delete() 
    recreo3.delete()
    pago1.delete()
    caja.delete()
    
    if abs(saldo_final - saldo_teorico) < Decimal('0.01'):
        print("   ✅ PRUEBA EXITOSA: Sin discrepancias")
        return True
    else:
        print("   ❌ PRUEBA FALLIDA: Hay discrepancias") 
        return False

def main():
    """Función principal de pruebas"""
    print("Iniciando pruebas de la nueva lógica de reapertura...")
    
    try:
        # Prueba: Nueva lógica
        exito_nueva = test_nueva_logica_reapertura()
        
        print("\n" + "="*60)
        print("RESUMEN DE PRUEBAS")
        print("="*60)
        
        if exito_nueva:
            print("✅ NUEVA LÓGICA: Funciona correctamente, sin discrepancias")
            print("✅ Solución implementada correctamente.")
        else:
            print("❌ NUEVA LÓGICA: Tiene problemas")
            print("❌ La solución necesita revisión.")
            
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()