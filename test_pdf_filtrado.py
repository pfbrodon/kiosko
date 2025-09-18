#!/usr/bin/env python
"""
Script de prueba para la funcionalidad de PDF filtrado
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from precios.models import Producto, Categoria, Subcategoria, Proveedor

def mostrar_estadisticas():
    """Muestra estadísticas de productos para testear filtros"""
    print("📊 ESTADÍSTICAS PARA PRUEBAS DE PDF")
    print("=" * 50)
    
    # Contar productos totales
    total_productos = Producto.objects.count()
    print(f"📦 Total de productos: {total_productos}")
    
    # Productos por categoría
    print("\n📂 Productos por categoría:")
    categorias = Categoria.objects.all()
    for categoria in categorias:
        count = Producto.objects.filter(subcategoria__categoria=categoria).count()
        print(f"   • {categoria.nombre}: {count} productos")
    
    # Productos por proveedor
    print("\n🏪 Productos por proveedor:")
    proveedores = Proveedor.objects.all()[:5]  # Solo los primeros 5
    for proveedor in proveedores:
        count = Producto.objects.filter(proveedor=proveedor).count()
        print(f"   • {proveedor.nombre}: {count} productos")
    
    # Productos activos vs inactivos
    activos = Producto.objects.filter(activo=True).count()
    inactivos = Producto.objects.filter(activo=False).count()
    print(f"\n✅ Productos activos: {activos}")
    print(f"❌ Productos inactivos: {inactivos}")
    
    # Productos con stock bajo
    stock_bajo = Producto.objects.filter(alerta_stock=True).count()
    print(f"⚠️  Productos con stock bajo: {stock_bajo}")
    
    print("\n🔗 URLs de prueba:")
    print(f"📄 Lista completa PDF: http://127.0.0.1:8000/productos/lista-precios-pdf/")
    print(f"🔍 PDF filtrado (sin filtros): http://127.0.0.1:8000/productos/filtrados-pdf/")
    print(f"🔍 PDF filtrado (solo activos): http://127.0.0.1:8000/productos/filtrados-pdf/?estado=1")
    print(f"🔍 PDF filtrado (stock bajo): http://127.0.0.1:8000/productos/filtrados-pdf/?estado=B")
    
    if categorias:
        primera_categoria = categorias.first()
        print(f"🔍 PDF filtrado (primera categoría): http://127.0.0.1:8000/productos/filtrados-pdf/?categoria={primera_categoria.id}")
    
    print("\n" + "=" * 50)
    print("✅ Estadísticas mostradas. Puedes usar estas URLs para probar.")

if __name__ == "__main__":
    mostrar_estadisticas()