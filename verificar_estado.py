#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from precios.models import Producto, HistorialPrecio

def verificar_estado():
    """Verificar el estado actual de productos e historial"""
    
    print("=== VERIFICACIÓN DE ESTADO ===")
    print(f"Total de productos: {Producto.objects.count()}")
    print(f"Total de historiales de precio: {HistorialPrecio.objects.count()}")
    print()
    
    if Producto.objects.exists():
        print("Primeros 5 productos:")
        for p in Producto.objects.all()[:5]:
            tiene_cambio = p.tiene_cambio_precio_reciente()
            print(f"- {p.nombre}: ${p.precio_venta_final} | Cambio reciente: {'✅ SÍ' if tiene_cambio else '❌ NO'}")
        print()
    
    if HistorialPrecio.objects.exists():
        print("Últimos 5 cambios de precio:")
        for h in HistorialPrecio.objects.all()[:5]:
            print(f"- {h.producto.nombre}: ${h.precio_anterior} → ${h.precio_nuevo} ({h.fecha_cambio})")
    else:
        print("No hay historial de cambios de precio.")

if __name__ == "__main__":
    verificar_estado()
