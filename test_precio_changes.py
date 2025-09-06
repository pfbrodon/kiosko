#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from precios.models import Producto, HistorialPrecio
from django.utils import timezone
from decimal import Decimal

def crear_datos_prueba():
    """Crear datos de prueba para verificar el indicador de cambios de precio"""
    
    print("Verificando productos existentes...")
    productos = Producto.objects.all()[:3]  # Tomar los primeros 3 productos
    
    if not productos:
        print("No hay productos en la base de datos.")
        return
    
    # Crear cambios de precio recientes (últimas 73 horas)
    fecha_reciente = timezone.now() - timedelta(hours=24)  # 24 horas atrás
    
    for i, producto in enumerate(productos):
        precio_anterior = producto.precio_venta_final
        precio_nuevo = precio_anterior + Decimal('10.00')  # Aumentar $10
        
        # Crear historial de cambio reciente
        historial = HistorialPrecio.objects.create(
            producto=producto,
            precio_anterior=precio_anterior,
            precio_nuevo=precio_nuevo,
            motivo=f"Prueba de cambio reciente - Producto {i+1}"
        )
        
        # Modificar la fecha para que sea reciente
        historial.fecha_cambio = fecha_reciente
        historial.save()
        
        print(f"✅ Creado cambio reciente para: {producto.nombre}")
        print(f"   Precio: ${precio_anterior} → ${precio_nuevo}")
        print(f"   Fecha: {fecha_reciente}")
        print()
    
    # Verificar que los productos detecten cambios recientes
    print("Verificando detección de cambios recientes:")
    for producto in productos:
        tiene_cambio = producto.tiene_cambio_precio_reciente()
        print(f"- {producto.nombre}: {'✅ SÍ' if tiene_cambio else '❌ NO'} tiene cambios recientes")

if __name__ == "__main__":
    crear_datos_prueba()
