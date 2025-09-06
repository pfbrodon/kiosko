#!/usr/bin/env python
"""
Script para revisar el estado del stock de los productos
"""
import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from precios.models import Producto

def revisar_stock():
    """Revisar el estado del stock de todos los productos"""
    
    print("🔍 REVISIÓN DEL STOCK DE PRODUCTOS")
    print("=" * 60)
    
    productos_stock_bajo = Producto.objects.filter(alerta_stock=True).order_by('cantidad_stock')
    productos_normales = Producto.objects.filter(alerta_stock=False).order_by('cantidad_stock')
    
    print(f"\n❌ PRODUCTOS CON STOCK BAJO ({productos_stock_bajo.count()}):")
    print("-" * 60)
    for producto in productos_stock_bajo:
        print(f"🟥 {producto.nombre}")
        print(f"   Stock actual: {producto.cantidad_stock}")
        print(f"   Stock mínimo: {producto.stock_minimo}")
        print(f"   Alerta activa: {producto.alerta_stock}")
        print(f"   Condición: {producto.cantidad_stock} <= {producto.stock_minimo} = {producto.cantidad_stock <= producto.stock_minimo}")
        print()
    
    if not productos_stock_bajo:
        print("   ✅ No hay productos con stock bajo")
    
    print(f"\n✅ PRODUCTOS CON STOCK NORMAL (primeros 10 de {productos_normales.count()}):")
    print("-" * 60)
    for producto in productos_normales[:10]:
        print(f"🟢 {producto.nombre}: Stock {producto.cantidad_stock} (mín: {producto.stock_minimo})")
    
    # Buscar productos con inconsistencias
    print(f"\n🔧 VERIFICACIÓN DE INCONSISTENCIAS:")
    print("-" * 60)
    inconsistencias = 0
    
    for producto in Producto.objects.all():
        deberia_tener_alerta = producto.cantidad_stock <= producto.stock_minimo
        tiene_alerta = producto.alerta_stock
        
        if deberia_tener_alerta != tiene_alerta:
            inconsistencias += 1
            print(f"❌ INCONSISTENCIA en {producto.nombre}:")
            print(f"   Stock: {producto.cantidad_stock}, Mínimo: {producto.stock_minimo}")
            print(f"   Debería tener alerta: {deberia_tener_alerta}")
            print(f"   Tiene alerta: {tiene_alerta}")
            print()
    
    if inconsistencias == 0:
        print("✅ No se encontraron inconsistencias")
    else:
        print(f"⚠️ Se encontraron {inconsistencias} inconsistencias")
    
    print(f"\n📊 RESUMEN:")
    print(f"Total productos: {Producto.objects.count()}")
    print(f"Con stock bajo: {productos_stock_bajo.count()}")
    print(f"Con stock normal: {productos_normales.count()}")

if __name__ == "__main__":
    revisar_stock()
