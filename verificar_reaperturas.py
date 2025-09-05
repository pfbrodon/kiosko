#!/usr/bin/env python
"""
Script para verificar reaperturas
"""

import os
import sys
import django

project_path = r'C:\Users\Kiosko\Desktop\Desarrollo\kiosko'
sys.path.append(project_path)
os.chdir(project_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from caja.models import CajaDiaria
from datetime import date

def verificar_reaperturas():
    print("=== VERIFICACIÓN DE REAPERTURAS ===\n")
    
    today = date.today()
    cajas_hoy = CajaDiaria.objects.filter(fecha=today)
    
    for caja in cajas_hoy:
        print(f"📦 Caja {caja.get_nivel_display()} - {caja.get_turno_display()}")
        print(f"   Cerrada: {caja.cerrada}")
        print(f"   Fue reabierta: {caja.fue_reabierta}")
        if caja.fue_reabierta:
            print(f"   Usuario reapertura: {caja.usuario_reapertura}")
            print(f"   Fecha reapertura: {caja.fecha_reapertura}")
        print()

if __name__ == "__main__":
    verificar_reaperturas()
