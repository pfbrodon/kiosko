#!/usr/bin/env python
"""
Script para verificar el estado actual del sistema
"""

import os
import sys
import django

# Configurar Django
sys.path.append('C:/Users/Kiosko/Desktop/Desarrollo/kiosko')
os.chdir('C:/Users/Kiosko/Desktop/Desarrollo/kiosko')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from caja.models import CajaDiaria, PagoProveedor
from caja.forms import PagoProveedorForm
from precios.models import Proveedor
from datetime import date

def verificar_sistema():
    print("=== VERIFICACIÓN DEL SISTEMA ===\n")
    
    # Verificar proveedores
    proveedores = Proveedor.objects.all()
    print(f"✅ Proveedores en sistema: {proveedores.count()}")
    for p in proveedores[:5]:
        print(f"   - {p.nombre}")
    if proveedores.count() > 5:
        print(f"   ... y {proveedores.count() - 5} más")
    
    # Verificar cajas del día
    today = date.today()
    cajas = CajaDiaria.objects.filter(fecha=today)
    print(f"\n✅ Cajas de hoy: {cajas.count()}")
    
    for caja in cajas:
        puede_pagos = caja.nivel == 'S' or (caja.nivel == 'P' and not caja.es_extra)
        print(f"   - {caja.get_nivel_display()} {caja.get_turno_display()}")
        print(f"     Puede hacer pagos: {'✅ SÍ' if puede_pagos else '❌ NO'}")
        
        # Pagos existentes
        pagos = PagoProveedor.objects.filter(caja=caja)
        print(f"     Pagos registrados: {pagos.count()}")
    
    # Probar formulario
    print(f"\n✅ Probando formulario de pago...")
    form = PagoProveedorForm()
    print(f"   Campos: {list(form.fields.keys())}")
    
    # Datos de prueba
    if proveedores.exists():
        test_data = {
            'proveedor': proveedores.first().id,
            'monto': 1500.00,
            'comprobante': 'COMP-001',
            'observacion': 'Pago de prueba'
        }
        
        form = PagoProveedorForm(data=test_data)
        if form.is_valid():
            print("   ✅ Formulario válido con datos de prueba")
        else:
            print("   ❌ Formulario inválido:")
            for field, errors in form.errors.items():
                print(f"     {field}: {errors}")

if __name__ == "__main__":
    verificar_sistema()
