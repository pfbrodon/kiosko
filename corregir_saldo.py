#!/usr/bin/env python
"""
Script para corregir el saldo general
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

from caja.models import SaldoGeneral
from decimal import Decimal

def corregir_saldo():
    print("=== CORRECCIÓN DE SALDO GENERAL ===\n")
    
    saldo_general = SaldoGeneral.objects.first()
    if not saldo_general:
        print("❌ No hay saldo general")
        return
    
    print(f"💰 Saldo actual: ${saldo_general.monto}")
    print(f"💰 Saldo esperado: $226500.00")
    print(f"💰 Diferencia: ${saldo_general.monto - Decimal('226500')}")
    
    print("\n🔧 Corrigiendo saldo automáticamente...")
    saldo_general.monto = Decimal('226500')
    saldo_general.save()
    print("✅ Saldo corregido exitosamente")
    print(f"💰 Nuevo saldo: ${saldo_general.monto}")

if __name__ == "__main__":
    corregir_saldo()
