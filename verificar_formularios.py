#!/usr/bin/env python
"""
Script para verificar el estado de los botones y formularios
"""

import os
import sys
import django

# Configurar Django
sys.path.append('C:/Users/Kiosko/Desktop/Desarrollo/kiosko')
os.chdir('C:/Users/Kiosko/Desktop/Desarrollo/kiosko')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from caja.models import CajaDiaria
from caja.forms import RecreoForm, PagoProveedorForm
from datetime import date

def verificar_formularios():
    print("=== VERIFICACIÓN DE FORMULARIOS ===\n")
    
    # Verificar formulario de recreo
    recreo_form = RecreoForm()
    print("✅ Formulario de recreo creado correctamente")
    print(f"   Campos: {list(recreo_form.fields.keys())}")
    
    # Verificar formulario de pago
    pago_form = PagoProveedorForm()
    print("✅ Formulario de pago creado correctamente")
    print(f"   Campos: {list(pago_form.fields.keys())}")
    
    # Verificar caja del día
    today = date.today()
    cajas = CajaDiaria.objects.filter(fecha=today)
    
    if cajas.exists():
        print(f"\n✅ Se encontraron {cajas.count()} cajas para hoy")
        for caja in cajas:
            print(f"   - {caja.get_nivel_display()} {caja.get_turno_display()}")
            puede_hacer_pagos = caja.nivel == 'S' or (caja.nivel == 'P' and not caja.es_extra)
            print(f"     Puede hacer pagos: {'✅ SÍ' if puede_hacer_pagos else '❌ NO'}")
    else:
        print("❌ No se encontraron cajas para hoy")

if __name__ == "__main__":
    verificar_formularios()
