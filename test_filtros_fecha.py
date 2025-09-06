#!/usr/bin/env python
"""
Script para crear cambios de precio en diferentes períodos para probar los filtros
"""
import os
import sys
import django
from datetime import timedelta

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from precios.models import Producto, HistorialPrecio
from django.utils import timezone
from decimal import Decimal

def crear_cambios_diferentes_fechas():
    """Crear cambios de precio en diferentes períodos"""
    
    productos = Producto.objects.all()[:3]  # Usar los 3 productos existentes
    
    if len(productos) < 3:
        print("❌ Se necesitan al menos 3 productos. Ejecuta primero crear_datos_prueba.py")
        return
    
    # Limpiar historial anterior
    HistorialPrecio.objects.all().delete()
    print("🧹 Historial anterior limpiado")
    
    # Crear cambios en diferentes períodos
    fechas_y_productos = [
        (timezone.now() - timedelta(hours=12), productos[0], "12 horas atrás"),  # Coca Cola - 24h
        (timezone.now() - timedelta(hours=36), productos[1], "36 horas atrás"),  # Pepsi - 48h
        (timezone.now() - timedelta(hours=60), productos[2], "60 horas atrás"),  # Sprite - 72h
    ]
    
    for fecha, producto, descripcion in fechas_y_productos:
        precio_anterior = producto.precio_venta_final - Decimal("15.00")
        
        historial = HistorialPrecio.objects.create(
            producto=producto,
            precio_anterior=precio_anterior,
            precio_nuevo=producto.precio_venta_final,
            motivo=f"Cambio de prueba - {descripcion}"
        )
        
        # Establecer la fecha específica
        historial.fecha_cambio = fecha
        historial.save()
        
        print(f"💰 {producto.nombre}: Cambio {descripcion}")
        print(f"   ${precio_anterior} → ${producto.precio_venta_final}")
        print(f"   Fecha: {fecha.strftime('%d/%m/%Y %H:%M')}")
        print()
    
    print("=== VERIFICACIÓN DE FILTROS ===")
    print("Filtro 24h:", [p.nombre for p in productos if p.tiene_cambio_precio_reciente(24)])
    print("Filtro 48h:", [p.nombre for p in productos if p.tiene_cambio_precio_reciente(48)])
    print("Filtro 72h:", [p.nombre for p in productos if p.tiene_cambio_precio_reciente(72)])
    
    print("\n✅ Datos de prueba creados para diferentes períodos.")
    print("🔍 Prueba los filtros:")
    print("   - Últimas 24h: debería mostrar solo Coca Cola")
    print("   - Últimas 48h: debería mostrar Coca Cola y Pepsi")
    print("   - Últimas 72h: debería mostrar los 3 productos")

if __name__ == "__main__":
    crear_cambios_diferentes_fechas()
