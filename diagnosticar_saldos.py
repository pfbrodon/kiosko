#!/usr/bin/env python
"""
Script para diagnosticar los cálculos de saldo
"""

import os
import sys
import django

# Agregar el path del proyecto
project_path = r'C:\Users\Kiosko\Desktop\Desarrollo\kiosko'
sys.path.append(project_path)
os.chdir(project_path)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from caja.models import SaldoGeneral, SaldoElectronico, CajaDiaria
from decimal import Decimal

def diagnosticar_saldos():
    print("=== DIAGNÓSTICO DE SALDOS ===\n")
    
    # 1. Saldo General Efectivo
    saldo_general = SaldoGeneral.objects.first()
    if saldo_general:
        print(f"💰 Saldo General Efectivo: ${saldo_general.monto}")
    else:
        print("❌ No hay saldo general")
    
    # 2. Saldo Electrónico
    saldo_electronico = SaldoElectronico.objects.first()
    if saldo_electronico:
        print(f"💳 Saldo Electrónico: ${saldo_electronico.monto}")
    else:
        print("❌ No hay saldo electrónico")
    
    # 3. Saldo Total
    saldo_total = saldo_general.get_saldo_total() if saldo_general else Decimal('0')
    print(f"📊 Saldo Total (Efectivo + Electrónico): ${saldo_total}")
    print()
    
    # 4. Cajas Abiertas
    cajas_abiertas = CajaDiaria.objects.filter(cerrada=False)
    print(f"📦 Cajas Abiertas: {cajas_abiertas.count()}")
    
    saldo_inicial_total = Decimal('0')
    ingresos_total = Decimal('0')
    egresos_total = Decimal('0')
    
    for caja in cajas_abiertas:
        print(f"\n  📋 Caja {caja.get_nivel_display()} - {caja.get_turno_display()}")
        print(f"     Fecha: {caja.fecha}")
        print(f"     Saldo inicial BD: ${caja.saldo_inicial}")
        print(f"     Saldo inicial display: ${caja.get_saldo_inicial_display()}")
        print(f"     Ingresos: ${caja.get_total_ingresos()}")
        print(f"     Egresos: ${caja.get_total_egresos()}")
        print(f"     Saldo parcial calculado: ${caja.calcular_saldo_parcial()}")
        print(f"     Saldo parcial BD: ${caja.saldo_parcial}")
        
        # Actualizar saldo parcial
        caja.actualizar_saldo_parcial()
        
        # Sumar para totales (solo secundarias para saldo inicial)
        if caja.nivel == 'S':
            saldo_inicial_total += caja.saldo_inicial
            print(f"     ✅ Sumando saldo inicial: ${caja.saldo_inicial}")
        else:
            print(f"     ⏭️  No suma saldo inicial (es primaria)")
            
        ingresos_total += caja.get_total_ingresos()
        egresos_total += caja.get_total_egresos()
    
    # 5. Totales calculados
    saldo_parcial_calculado = saldo_inicial_total + ingresos_total - egresos_total
    print(f"\n=== TOTALES CALCULADOS ===")
    print(f"Saldo inicial total (solo secundarias): ${saldo_inicial_total}")
    print(f"Ingresos total: ${ingresos_total}")
    print(f"Egresos total: ${egresos_total}")
    print(f"Saldo parcial calculado: ${saldo_parcial_calculado}")
    
    # 6. Comparación final
    print(f"\n=== COMPARACIÓN ===")
    print(f"Saldo efectivo en BD: ${saldo_general.monto if saldo_general else 0}")
    print(f"Saldo parcial de cajas: ${saldo_parcial_calculado}")
    print(f"Saldo que debería tener el efectivo: ${Decimal('226500') - saldo_parcial_calculado}")
    print(f"Diferencia actual: ${saldo_total - Decimal('226500')}")
    
    # 7. Cajas cerradas del día
    from datetime import date
    today = date.today()
    cajas_cerradas_hoy = CajaDiaria.objects.filter(fecha=today, cerrada=True)
    print(f"\n📦 Cajas cerradas hoy: {cajas_cerradas_hoy.count()}")
    
    for caja in cajas_cerradas_hoy:
        print(f"  🔒 Caja {caja.get_nivel_display()} - {caja.get_turno_display()}")
        print(f"     Saldo inicial: ${caja.saldo_inicial}")
        print(f"     Saldo final: ${caja.saldo_parcial}")
        print(f"     Diferencia agregada al cierre: ${caja.saldo_parcial - caja.saldo_inicial}")

if __name__ == "__main__":
    diagnosticar_saldos()
