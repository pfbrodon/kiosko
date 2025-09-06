#!/usr/bin/env python
"""
Script para crear datos de prueba de cambios de precio
"""
import os
import sys
import django
from datetime import timedelta

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from precios.models import Producto, HistorialPrecio, Categoria, Subcategoria, Proveedor
from django.utils import timezone
from decimal import Decimal

def crear_productos_prueba():
    """Crear productos de prueba si no existen"""
    
    # Crear categoría de prueba
    categoria, created = Categoria.objects.get_or_create(nombre="Bebidas")
    subcategoria, created = Subcategoria.objects.get_or_create(
        categoria=categoria,
        nombre="Gaseosas"
    )
    proveedor, created = Proveedor.objects.get_or_create(nombre="Proveedor Test")
    
    productos_datos = [
        {"nombre": "Coca Cola 500ml", "precio": Decimal("250.00")},
        {"nombre": "Pepsi 500ml", "precio": Decimal("240.00")},
        {"nombre": "Sprite 500ml", "precio": Decimal("230.00")},
    ]
    
    productos_creados = []
    for datos in productos_datos:
        producto, created = Producto.objects.get_or_create(
            nombre=datos["nombre"],
            defaults={
                'subcategoria': subcategoria,
                'proveedor': proveedor,
                'tipo_compra': 'U',
                'precio_compra_paquete': datos["precio"] * Decimal("0.6"),
                'tipo_venta': 'U',
                'margen_ganancia': Decimal("40.00"),
                'precio_venta_final': datos["precio"],
                'cantidad_stock': 50,
                'stock_minimo': 10,
            }
        )
        productos_creados.append(producto)
        if created:
            print(f"✅ Producto creado: {producto.nombre}")
    
    return productos_creados

def crear_cambios_recientes():
    """Crear cambios de precio recientes"""
    
    productos = crear_productos_prueba()
    
    # Crear cambios recientes para los primeros 2 productos
    fecha_cambio = timezone.now() - timedelta(hours=12)  # 12 horas atrás
    
    for i, producto in enumerate(productos[:2]):
        precio_anterior = producto.precio_venta_final - Decimal("20.00")
        
        historial = HistorialPrecio.objects.create(
            producto=producto,
            precio_anterior=precio_anterior,
            precio_nuevo=producto.precio_venta_final,
            motivo=f"Aumento de precio por inflación"
        )
        
        # Establecer fecha reciente
        historial.fecha_cambio = fecha_cambio
        historial.save()
        
        print(f"💰 Cambio de precio creado: {producto.nombre}")
        print(f"   ${precio_anterior} → ${producto.precio_venta_final}")
        print(f"   Fecha: {fecha_cambio.strftime('%d/%m/%Y %H:%M')}")
        
    print("\n=== VERIFICACIÓN ===")
    for producto in productos:
        tiene_cambio = producto.tiene_cambio_precio_reciente()
        icono = "🟡" if tiene_cambio else "⚪"
        print(f"{icono} {producto.nombre}: Cambio reciente = {tiene_cambio}")

if __name__ == "__main__":
    print("Creando datos de prueba para cambios de precio...")
    crear_cambios_recientes()
    print("\n✅ Datos de prueba creados. Refresca la página de productos para ver los cambios.")
