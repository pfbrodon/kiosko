#!/usr/bin/env python
"""
Script para verificar el funcionamiento del nuevo sistema de eventos
"""
import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from precios.models import Producto, EventoProducto
from django.utils import timezone

def verificar_nuevo_sistema():
    """Verificar que el nuevo sistema funciona correctamente"""
    
    print("🔍 VERIFICACIÓN DEL NUEVO SISTEMA DE EVENTOS")
    print("=" * 60)
    
    # Verificar eventos existentes
    total_eventos = EventoProducto.objects.count()
    eventos_creacion = EventoProducto.objects.filter(tipo_evento='CREACION').count()
    
    print(f"Total de eventos: {total_eventos}")
    print(f"Eventos de creación: {eventos_creacion}")
    
    # Verificar productos nuevos con el nuevo sistema
    productos_nuevos_72h = []
    productos_nuevos_48h = []
    productos_nuevos_24h = []
    
    for producto in Producto.objects.all():
        if producto.es_producto_nuevo(72):
            productos_nuevos_72h.append(producto)
        if producto.es_producto_nuevo(48):
            productos_nuevos_48h.append(producto)
        if producto.es_producto_nuevo(24):
            productos_nuevos_24h.append(producto)
    
    print(f"\n📊 PRODUCTOS NUEVOS CON NUEVO SISTEMA:")
    print(f"Últimas 72 horas: {len(productos_nuevos_72h)}")
    print(f"Últimas 48 horas: {len(productos_nuevos_48h)}")
    print(f"Últimas 24 horas: {len(productos_nuevos_24h)}")
    
    if productos_nuevos_72h:
        print(f"\n🆕 PRODUCTOS NUEVOS (72h):")
        for producto in productos_nuevos_72h:
            fecha_real = producto.fecha_creacion_real()
            horas = (timezone.now() - fecha_real).total_seconds() / 3600
            print(f"   ⭐ {producto.nombre}")
            print(f"      Creado: {fecha_real.strftime('%d/%m/%Y %H:%M')}")
            print(f"      Hace: {horas:.1f} horas")
    else:
        print(f"\n✅ No hay productos nuevos en las últimas 72 horas")
    
    # Mostrar algunos ejemplos de fechas distribuidas
    print(f"\n📅 EJEMPLOS DE FECHAS DISTRIBUIDAS:")
    print("-" * 40)
    
    productos_muestra = Producto.objects.all().order_by('id')[::30]  # Cada 30 productos
    for producto in productos_muestra:
        fecha_real = producto.fecha_creacion_real()
        print(f"ID {producto.id}: {producto.nombre[:30]}...")
        print(f"   Fecha: {fecha_real.strftime('%d/%m/%Y %H:%M')}")

if __name__ == "__main__":
    verificar_nuevo_sistema()
