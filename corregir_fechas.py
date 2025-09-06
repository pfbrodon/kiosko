#!/usr/bin/env python
"""
Script para corregir las fechas de creación de productos existentes
"""
import os
import sys
import django
from datetime import timedelta

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from precios.models import Producto
from django.utils import timezone

def corregir_fechas_productos():
    """Corregir fechas de productos para que solo los nuevos tengan estrella verde"""
    
    productos = Producto.objects.all().order_by('id')
    
    print("🔧 Corrigiendo fechas de productos...")
    
    # Los productos que queremos que aparezcan como "nuevos" (últimos 2)
    productos_realmente_nuevos = [
        "Chocolate Milka Oreo",
        "Bon o Bon Blanco"
    ]
    
    for producto in productos:
        if producto.nombre in productos_realmente_nuevos:
            # Estos productos mantienen fecha reciente (últimas 24 horas)
            producto.fecha_creacion = timezone.now() - timedelta(hours=12)
            estado = "✅ NUEVO"
        else:
            # Los demás productos se marcan como creados hace más de 72 horas
            producto.fecha_creacion = timezone.now() - timedelta(days=10)
            estado = "📅 ANTIGUO"
        
        producto.save()
        print(f"{estado} {producto.nombre}: {producto.fecha_creacion.strftime('%d/%m/%Y %H:%M')}")
    
    print("\n=== VERIFICACIÓN FINAL ===")
    for producto in productos:
        es_nuevo = producto.es_producto_nuevo()
        icono = "⭐" if es_nuevo else "⚪"
        print(f"{icono} {producto.nombre} - Nuevo: {es_nuevo}")
    
    print(f"\n✅ Fechas corregidas.")
    print("🔄 Refresca la página - solo deberían aparecer estrellas verdes en:")
    for nombre in productos_realmente_nuevos:
        print(f"   ⭐ {nombre}")

if __name__ == "__main__":
    corregir_fechas_productos()
