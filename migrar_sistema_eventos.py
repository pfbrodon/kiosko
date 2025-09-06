#!/usr/bin/env python
"""
Script para migrar datos existentes al nuevo sistema de eventos
y establecer fechas de creación más realistas basadas en IDs
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
from datetime import timedelta
import json

def migrar_datos_a_eventos():
    """
    Migra los datos existentes al nuevo sistema de eventos
    """
    print("🔄 MIGRACIÓN DE DATOS AL SISTEMA DE EVENTOS")
    print("=" * 60)
    
    # Obtener todos los productos ordenados por ID
    productos = Producto.objects.all().order_by('id')
    total_productos = productos.count()
    
    print(f"Total de productos a procesar: {total_productos}")
    
    # Establecer fecha base (hace un mes desde hoy)
    fecha_base = timezone.now() - timedelta(days=30)
    
    # Calcular intervalo entre productos para distribuir las fechas
    # Distribuyendo 149 productos en 25 días (dejando 5 días para productos realmente nuevos)
    intervalo_horas = (25 * 24) / max(total_productos - 5, 1)  # Excluir los últimos 5 productos
    
    eventos_creados = 0
    eventos_actualizados = 0
    
    for i, producto in enumerate(productos):
        
        # Verificar si ya existe un evento de creación
        evento_existente = EventoProducto.objects.filter(
            producto=producto, 
            tipo_evento='CREACION'
        ).first()
        
        if evento_existente:
            print(f"⏭️  Producto {producto.id}: {producto.nombre} - Ya tiene evento de creación")
            eventos_actualizados += 1
            continue
        
        # Calcular fecha de creación basada en el ID
        if producto.id <= total_productos - 2:  # Los productos más antiguos
            # Distribuir fechas hacia atrás desde la fecha base
            horas_atras = i * intervalo_horas
            fecha_creacion = fecha_base + timedelta(hours=horas_atras)
        else:
            # Los últimos productos mantienen su fecha real (son realmente nuevos)
            fecha_creacion = producto.fecha_creacion
        
        # Crear el evento de creación
        evento = EventoProducto.objects.create(
            producto=producto,
            tipo_evento='CREACION',
            descripcion=f'Producto "{producto.nombre}" creado en migración de datos',
            valor_nuevo=json.dumps({
                'nombre': producto.nombre,
                'precio_venta_final': str(producto.precio_venta_final),
                'categoria': str(producto.subcategoria.categoria.nombre),
                'subcategoria': str(producto.subcategoria.nombre),
                'id_original': producto.id,
            }),
            usuario='Sistema - Migración'
        )
        
        # Actualizar la fecha del evento manualmente (ya que auto_now_add=True)
        EventoProducto.objects.filter(id=evento.id).update(fecha_evento=fecha_creacion)
        
        eventos_creados += 1
        
        if eventos_creados % 20 == 0:
            print(f"✅ Procesados {eventos_creados} productos...")
    
    print(f"\n📊 RESUMEN DE MIGRACIÓN:")
    print(f"Eventos de creación nuevos: {eventos_creados}")
    print(f"Eventos existentes (no modificados): {eventos_actualizados}")
    print(f"Total productos procesados: {eventos_creados + eventos_actualizados}")
    
    # Verificar algunos productos como muestra
    print(f"\n🔍 VERIFICACIÓN DE FECHAS MIGRADAS:")
    print("-" * 60)
    
    # Mostrar los primeros 5 productos
    for producto in productos[:5]:
        evento = EventoProducto.objects.filter(
            producto=producto, 
            tipo_evento='CREACION'
        ).first()
        
        if evento:
            print(f"ID {producto.id}: {producto.nombre}")
            print(f"   Fecha evento: {evento.fecha_evento.strftime('%d/%m/%Y %H:%M')}")
            print(f"   Diferencia con fecha modelo: {(producto.fecha_creacion - evento.fecha_evento).days} días")
    
    # Mostrar los últimos 5 productos
    print(f"\nÚltimos productos:")
    for producto in productos.reverse()[:5]:
        evento = EventoProducto.objects.filter(
            producto=producto, 
            tipo_evento='CREACION'
        ).first()
        
        if evento:
            print(f"ID {producto.id}: {producto.nombre}")
            print(f"   Fecha evento: {evento.fecha_evento.strftime('%d/%m/%Y %H:%M')}")
            horas_diff = (timezone.now() - evento.fecha_evento).total_seconds() / 3600
            print(f"   Hace: {horas_diff:.1f} horas")

def verificar_sistema_nuevo():
    """
    Verificar que el nuevo sistema funciona correctamente
    """
    print(f"\n✅ VERIFICACIÓN DEL NUEVO SISTEMA:")
    print("-" * 60)
    
    # Probar con algunos productos
    productos_prueba = Producto.objects.all()[:3]
    
    for producto in productos_prueba:
        fecha_real = producto.fecha_creacion_real()
        es_nuevo = producto.es_producto_nuevo(72)
        
        print(f"🔍 {producto.nombre}:")
        print(f"   Fecha creación real: {fecha_real.strftime('%d/%m/%Y %H:%M')}")
        print(f"   Es nuevo (72h): {es_nuevo}")
        print()

if __name__ == "__main__":
    migrar_datos_a_eventos()
    verificar_sistema_nuevo()
    print(f"\n🎉 ¡Migración completada exitosamente!")
    print("Ahora el sistema usará las fechas de eventos para determinar productos nuevos.")
