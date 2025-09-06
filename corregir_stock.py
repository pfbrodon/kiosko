#!/usr/bin/env python
"""
Script para corregir el stock de productos que podrían haber perdido su stock
"""
import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from precios.models import Producto

def corregir_stock_productos():
    """Corregir el stock de productos que tienen stock en 0"""
    
    print("🔧 CORRECCIÓN DE STOCK DE PRODUCTOS")
    print("=" * 50)
    
    productos_sin_stock = Producto.objects.filter(cantidad_stock=0)
    
    print(f"Productos encontrados con stock 0: {productos_sin_stock.count()}")
    
    if productos_sin_stock.count() == 0:
        print("✅ No hay productos con stock 0")
        return
    
    opcion = input(f"\n¿Deseas actualizar el stock de estos {productos_sin_stock.count()} productos? (s/n): ")
    
    if opcion.lower() != 's':
        print("❌ Operación cancelada")
        return
    
    stock_nuevo = input("¿Qué stock asignar a estos productos? (recomendado: 10): ")
    
    try:
        stock_nuevo = int(stock_nuevo)
        if stock_nuevo < 0:
            print("❌ El stock no puede ser negativo")
            return
    except ValueError:
        print("❌ Valor inválido")
        return
    
    productos_actualizados = 0
    
    for producto in productos_sin_stock:
        producto.cantidad_stock = stock_nuevo
        producto.save()  # Esto también actualizará alerta_stock automáticamente
        productos_actualizados += 1
        print(f"✅ {producto.nombre}: Stock actualizado a {stock_nuevo}")
    
    print(f"\n🎉 {productos_actualizados} productos actualizados con stock {stock_nuevo}")
    
    # Verificar resultado
    productos_stock_bajo_despues = Producto.objects.filter(alerta_stock=True).count()
    print(f"📊 Productos con stock bajo después de la corrección: {productos_stock_bajo_despues}")

def solo_mostrar_productos_sin_stock():
    """Solo mostrar los productos sin stock sin corregir"""
    
    productos_sin_stock = Producto.objects.filter(cantidad_stock=0)
    
    print("📋 PRODUCTOS CON STOCK 0:")
    print("-" * 40)
    
    for i, producto in enumerate(productos_sin_stock, 1):
        print(f"{i:2d}. {producto.nombre}")
    
    print(f"\nTotal: {productos_sin_stock.count()} productos")

if __name__ == "__main__":
    print("1. Solo mostrar productos sin stock")
    print("2. Corregir stock de productos")
    
    opcion = input("\nSelecciona una opción (1 o 2): ")
    
    if opcion == "1":
        solo_mostrar_productos_sin_stock()
    elif opcion == "2":
        corregir_stock_productos()
    else:
        print("❌ Opción inválida")
