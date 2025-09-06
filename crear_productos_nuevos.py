#!/usr/bin/env python
"""
Script para crear productos nuevos y testear el indicador de producto nuevo
"""
import os
import sys
import django
from datetime import timedelta

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from precios.models import Producto, Categoria, Subcategoria, Proveedor
from django.utils import timezone
from decimal import Decimal

def crear_productos_nuevos():
    """Crear productos nuevos para probar el indicador"""
    
    # Obtener o crear categoría y subcategoría
    categoria, _ = Categoria.objects.get_or_create(nombre="Snacks")
    subcategoria, _ = Subcategoria.objects.get_or_create(
        categoria=categoria,
        nombre="Chocolates"
    )
    proveedor, _ = Proveedor.objects.get_or_create(nombre="Distribuidora Nueva")
    
    productos_nuevos = [
        {"nombre": "Chocolate Milka Oreo", "precio": Decimal("450.00")},
        {"nombre": "Bon o Bon Blanco", "precio": Decimal("280.00")},
    ]
    
    productos_creados = []
    
    for datos in productos_nuevos:
        # Verificar si ya existe
        if not Producto.objects.filter(nombre=datos["nombre"]).exists():
            producto = Producto.objects.create(
                nombre=datos["nombre"],
                subcategoria=subcategoria,
                proveedor=proveedor,
                tipo_compra='U',
                precio_compra_paquete=datos["precio"] * Decimal("0.6"),
                tipo_venta='U',
                margen_ganancia=Decimal("40.00"),
                precio_venta_final=datos["precio"],
                cantidad_stock=25,
                stock_minimo=5,
            )
            productos_creados.append(producto)
            print(f"⭐ Producto nuevo creado: {producto.nombre}")
            print(f"   Precio: ${producto.precio_venta_final}")
            print(f"   Fecha creación: {producto.fecha_creacion.strftime('%d/%m/%Y %H:%M')}")
            print()
    
    # También crear un producto "viejo" modificando la fecha
    if productos_creados:
        producto_viejo = productos_creados[0]
        # Cambiar fecha de creación a hace 5 días
        producto_viejo.fecha_creacion = timezone.now() - timedelta(days=5)
        producto_viejo.save()
        print(f"📅 {producto_viejo.nombre} marcado como producto antiguo (5 días)")
    
    print("\n=== VERIFICACIÓN ===")
    todos_productos = Producto.objects.all()[:5]
    for producto in todos_productos:
        es_nuevo = producto.es_producto_nuevo()
        tiene_cambio = producto.tiene_cambio_precio_reciente()
        
        iconos = []
        if es_nuevo:
            iconos.append("⭐ NUEVO")
        if tiene_cambio:
            iconos.append("🟡 MODIFICADO")
        if not iconos:
            iconos.append("⚪ NORMAL")
            
        print(f"{' '.join(iconos)} {producto.nombre}")
    
    print(f"\n✅ Productos nuevos creados.")
    print("🔄 Refresca la página para ver las estrellas verdes titilando en los productos nuevos")

if __name__ == "__main__":
    crear_productos_nuevos()
