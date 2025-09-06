#!/usr/bin/env python
"""
Script para probar la creación automática de eventos en productos nuevos
"""
import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from precios.models import Producto, EventoProducto, Subcategoria, Proveedor, Marca
from django.utils import timezone

def probar_creacion_automatica():
    """
    Prueba que el sistema cree automáticamente eventos al crear productos
    """
    print("🧪 PRUEBA DE CREACIÓN AUTOMÁTICA DE EVENTOS")
    print("=" * 60)
    
    # Obtener datos necesarios para crear un producto de prueba
    subcategoria = Subcategoria.objects.first()
    proveedor = Proveedor.objects.first()
    marca = Marca.objects.first()
    
    if not subcategoria:
        print("❌ No hay subcategorías disponibles para la prueba")
        return
    
    # Crear un producto de prueba
    producto_prueba = Producto.objects.create(
        nombre="Producto de Prueba - Sistema de Eventos",
        subcategoria=subcategoria,
        proveedor=proveedor,
        marca=marca,
        descripcion="Producto creado para probar el sistema de eventos automáticos",
        tipo_compra='U',
        precio_compra_paquete=100.00,
        tipo_venta='U',
        margen_ganancia=50.00,
        precio_venta_final=150.00,
        cantidad_stock=10,
        stock_minimo=5
    )
    
    print(f"✅ Producto creado: {producto_prueba.nombre} (ID: {producto_prueba.id})")
    
    # Verificar que se creó el evento automáticamente
    evento_creacion = EventoProducto.objects.filter(
        producto=producto_prueba,
        tipo_evento='CREACION'
    ).first()
    
    if evento_creacion:
        print(f"✅ Evento de creación generado automáticamente:")
        print(f"   Fecha: {evento_creacion.fecha_evento.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"   Usuario: {evento_creacion.usuario}")
        print(f"   Descripción: {evento_creacion.descripcion}")
        
        # Verificar que el producto aparece como nuevo
        es_nuevo = producto_prueba.es_producto_nuevo(72)
        fecha_real = producto_prueba.fecha_creacion_real()
        
        print(f"\n🔍 VERIFICACIÓN DEL PRODUCTO:")
        print(f"   Es nuevo (72h): {es_nuevo}")
        print(f"   Fecha creación real: {fecha_real.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"   Diferencia con ahora: {(timezone.now() - fecha_real).total_seconds():.1f} segundos")
        
    else:
        print("❌ No se generó evento de creación automáticamente")
    
    # Probar modificación de precio
    print(f"\n🔧 PROBANDO MODIFICACIÓN DE PRECIO:")
    precio_original = producto_prueba.precio_venta_final
    producto_prueba.precio_venta_final = 175.00
    producto_prueba.save()
    
    # Verificar evento de modificación de precio
    evento_precio = EventoProducto.objects.filter(
        producto=producto_prueba,
        tipo_evento='MODIFICACION_PRECIO'
    ).first()
    
    if evento_precio:
        print(f"✅ Evento de modificación de precio generado:")
        print(f"   Precio anterior: ${evento_precio.valor_anterior}")
        print(f"   Precio nuevo: ${evento_precio.valor_nuevo}")
        print(f"   Descripción: {evento_precio.descripcion}")
    else:
        print("❌ No se generó evento de modificación de precio")
    
    # Limpiar: eliminar el producto de prueba
    print(f"\n🧹 LIMPIEZA:")
    eventos_relacionados = EventoProducto.objects.filter(producto=producto_prueba).count()
    print(f"   Eventos relacionados al producto: {eventos_relacionados}")
    
    producto_prueba.delete()
    print(f"   Producto de prueba eliminado")
    
    # Verificar que los eventos también se eliminaron (CASCADE)
    eventos_restantes = EventoProducto.objects.filter(producto_id=producto_prueba.id).count()
    print(f"   Eventos restantes: {eventos_restantes}")

def mostrar_estadisticas_eventos():
    """
    Mostrar estadísticas de eventos en el sistema
    """
    print(f"\n📊 ESTADÍSTICAS DE EVENTOS EN EL SISTEMA:")
    print("-" * 60)
    
    for tipo_evento, descripcion in EventoProducto.TIPO_EVENTO_CHOICES:
        count = EventoProducto.objects.filter(tipo_evento=tipo_evento).count()
        print(f"   {descripcion}: {count}")
    
    # Eventos por día en los últimos 7 días
    desde = timezone.now() - timezone.timedelta(days=7)
    eventos_recientes = EventoProducto.objects.filter(fecha_evento__gte=desde).order_by('fecha_evento')
    
    if eventos_recientes.exists():
        print(f"\n📅 EVENTOS EN LOS ÚLTIMOS 7 DÍAS:")
        for evento in eventos_recientes:
            print(f"   {evento.fecha_evento.strftime('%d/%m %H:%M')} - {evento.producto.nombre} - {evento.get_tipo_evento_display()}")
    else:
        print(f"\n📅 No hay eventos recientes en los últimos 7 días")

if __name__ == "__main__":
    probar_creacion_automatica()
    mostrar_estadisticas_eventos()
    print(f"\n✅ Pruebas completadas exitosamente!")
