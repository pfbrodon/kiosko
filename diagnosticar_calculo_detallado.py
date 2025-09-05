#!/usr/bin/env python
"""
Script para diagnosticar el cálculo específico de saldo parcial
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

from caja.models import CajaDiaria
from decimal import Decimal
from datetime import date

def diagnosticar_calculo_saldo():
    print("=== DIAGNÓSTICO DETALLADO SALDO PARCIAL ===\n")
    
    # Obtener cajas cerradas de hoy
    today = date.today()
    cajas_cerradas_hoy = CajaDiaria.objects.filter(fecha=today, cerrada=True)
    
    for caja in cajas_cerradas_hoy:
        print(f"🔍 Caja {caja.get_nivel_display()} - {caja.get_turno_display()}")
        print(f"   Fecha: {caja.fecha}")
        print(f"   Es extra: {caja.es_extra}")
        print(f"   Saldo inicial BD: ${caja.saldo_inicial}")
        print(f"   Saldo inicial display: ${caja.get_saldo_inicial_display()}")
        
        # Cálculo manual paso a paso
        ingresos_recreos = caja.recreo_set.aggregate(
            total=django.db.models.Sum('monto')
        )['total'] or Decimal('0')
        
        ingresos_eventos = Decimal('0')
        if not caja.es_extra:
            ingresos_eventos = caja.eventoespecial_set.aggregate(
                total=django.db.models.Sum('monto')
            )['total'] or Decimal('0')
        
        egresos_pagos = caja.pagoproveedor_set.aggregate(
            total=django.db.models.Sum('monto')
        )['total'] or Decimal('0')
        
        print(f"   Ingresos recreos: ${ingresos_recreos}")
        print(f"   Ingresos eventos: ${ingresos_eventos}")
        print(f"   Egresos pagos: ${egresos_pagos}")
        
        # Cálculo actual del método
        saldo_calculado_metodo = caja.calcular_saldo_parcial()
        saldo_bd = caja.saldo_parcial
        
        # Cálculo manual con saldo inicial BD
        calculo_con_saldo_bd = caja.saldo_inicial + ingresos_recreos + ingresos_eventos - egresos_pagos
        
        # Cálculo manual con saldo inicial display
        calculo_con_saldo_display = caja.get_saldo_inicial_display() + ingresos_recreos + ingresos_eventos - egresos_pagos
        
        print(f"   Cálculo método actual: ${saldo_calculado_metodo}")
        print(f"   Saldo en BD: ${saldo_bd}")
        print(f"   Cálculo con saldo BD: ${calculo_con_saldo_bd}")
        print(f"   Cálculo con saldo display: ${calculo_con_saldo_display}")
        
        # Diferencia que se aplicó al cerrar
        diferencia_aplicada = saldo_bd - caja.saldo_inicial
        print(f"   Diferencia aplicada al cerrar: ${diferencia_aplicada}")
        print()

if __name__ == "__main__":
    diagnosticar_calculo_saldo()
