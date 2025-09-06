#!/usr/bin/env python
"""
Script para investigar si hay información adicional sobre fechas de productos
"""
import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from precios.models import Producto
from django.db import connection
from django.utils import timezone

def investigar_fechas_productos():
    """Investigar información adicional sobre fechas de productos"""
    
    print("🔍 INVESTIGACIÓN DE FECHAS DE PRODUCTOS")
    print("=" * 60)
    
    # 1. Verificar la estructura de la tabla
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(precios_producto);")
        columnas = cursor.fetchall()
        
        print("📋 COLUMNAS DE LA TABLA precios_producto:")
        print("-" * 40)
        for columna in columnas:
            print(f"  {columna[1]} ({columna[2]})")
        
        # 2. Verificar si SQLite tiene metadatos adicionales
        print(f"\n🔍 VERIFICANDO METADATOS DE LA BASE DE DATOS:")
        print("-" * 40)
        
        # Verificar el esquema de la tabla
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='precios_producto';")
        esquema = cursor.fetchone()
        if esquema:
            print("Esquema de la tabla:")
            print(esquema[0])
        
        # 3. Verificar IDs y orden de creación
        print(f"\n📊 ANÁLISIS DE IDs (orden probable de creación):")
        print("-" * 40)
        
        productos = Producto.objects.all().order_by('id')
        
        # Mostrar productos agrupados por rangos de ID
        rangos = [
            (1, 20, "Primeros 20 productos"),
            (21, 50, "Productos 21-50"),
            (51, 100, "Productos 51-100"),
            (101, 151, "Productos 101-151"),
        ]
        
        for inicio, fin, descripcion in rangos:
            productos_rango = productos.filter(id__gte=inicio, id__lt=fin)
            if productos_rango.exists():
                print(f"\n{descripcion} (IDs {inicio}-{fin-1}):")
                for producto in productos_rango[:5]:  # Solo mostrar los primeros 5
                    print(f"  ID {producto.id}: {producto.nombre}")
                if productos_rango.count() > 5:
                    print(f"  ... y {productos_rango.count() - 5} más")
        
        # 4. Verificar patrones en los nombres
        print(f"\n🏷️ ANÁLISIS DE PATRONES EN NOMBRES:")
        print("-" * 40)
        
        # Buscar productos que podrían haber sido agregados después
        productos_posiblemente_nuevos = []
        for producto in productos:
            nombre = producto.nombre.lower()
            # Buscar indicadores de que podrían ser más nuevos
            if any(palabra in nombre for palabra in ['chocolate milka', 'bon o bon', 'nuevo', 'especial']):
                productos_posiblemente_nuevos.append(producto)
        
        if productos_posiblemente_nuevos:
            print("Productos que podrían ser más recientes:")
            for producto in productos_posiblemente_nuevos:
                print(f"  ID {producto.id}: {producto.nombre}")
        
        # 5. Ver los últimos productos por ID
        print(f"\n🆕 ÚLTIMOS PRODUCTOS POR ID (probablemente más recientes):")
        print("-" * 40)
        ultimos_productos = productos.order_by('-id')[:10]
        for producto in ultimos_productos:
            print(f"  ID {producto.id}: {producto.nombre} (fecha: {producto.fecha_creacion.strftime('%d/%m/%Y %H:%M')})")

if __name__ == "__main__":
    investigar_fechas_productos()
