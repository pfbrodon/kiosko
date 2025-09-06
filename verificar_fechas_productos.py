#!/usr/bin/env python
"""
Script para verificar las fechas de creación de productos
"""
import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from precios.models import Producto
from django.utils import timezone

def verificar_fechas_productos():
    """Mostrar las fechas de creación de todos los productos"""
    
    print("📅 FECHAS DE CREACIÓN DE PRODUCTOS")
    print("=" * 60)
    
    productos = Producto.objects.all().order_by('fecha_creacion')
    
    print(f"Total de productos: {productos.count()}")
    print("\nProductos ordenados por fecha de creación:")
    print("-" * 60)
    
    fechas_agrupadas = {}
    
    for producto in productos:
        fecha_str = producto.fecha_creacion.strftime('%d/%m/%Y')
        hora_str = producto.fecha_creacion.strftime('%H:%M')
        
        if fecha_str not in fechas_agrupadas:
            fechas_agrupadas[fecha_str] = []
        
        fechas_agrupadas[fecha_str].append({
            'nombre': producto.nombre,
            'hora': hora_str,
            'fecha_completa': producto.fecha_creacion
        })
    
    for fecha, productos_fecha in fechas_agrupadas.items():
        print(f"\n📅 {fecha} ({len(productos_fecha)} productos):")
        for producto in productos_fecha:
            print(f"   {producto['hora']} - {producto['nombre']}")
    
    # Verificar productos realmente nuevos (últimas 72 horas)
    fecha_limite = timezone.now() - timezone.timedelta(hours=72)
    productos_realmente_nuevos = productos.filter(fecha_creacion__gte=fecha_limite)
    
    print(f"\n🆕 PRODUCTOS REALMENTE NUEVOS (últimas 72 horas):")
    print("-" * 60)
    if productos_realmente_nuevos.exists():
        for producto in productos_realmente_nuevos:
            horas_transcurridas = (timezone.now() - producto.fecha_creacion).total_seconds() / 3600
            print(f"⭐ {producto.nombre}")
            print(f"   Creado: {producto.fecha_creacion.strftime('%d/%m/%Y %H:%M')}")
            print(f"   Hace: {horas_transcurridas:.1f} horas")
            print()
    else:
        print("   No hay productos nuevos en las últimas 72 horas")
    
    # Verificar productos que aparecen como nuevos actualmente
    print(f"\n🔍 PRODUCTOS QUE APARECEN COMO NUEVOS ACTUALMENTE:")
    print("-" * 60)
    productos_marcados_nuevos = 0
    for producto in productos:
        if producto.es_producto_nuevo():
            productos_marcados_nuevos += 1
            print(f"⭐ {producto.nombre}: {producto.fecha_creacion.strftime('%d/%m/%Y %H:%M')}")
    
    if productos_marcados_nuevos == 0:
        print("   No hay productos marcados como nuevos")
    
    print(f"\n📊 RESUMEN:")
    print(f"Total productos: {productos.count()}")
    print(f"Realmente nuevos (72h): {productos_realmente_nuevos.count()}")
    print(f"Marcados como nuevos: {productos_marcados_nuevos}")

if __name__ == "__main__":
    verificar_fechas_productos()
