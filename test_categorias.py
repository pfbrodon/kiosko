#!/usr/bin/env python
"""
Script de prueba para las funcionalidades de edición y eliminación de categorías
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from precios.models import Categoria, Subcategoria, Producto

def mostrar_estado_categorias():
    """Muestra el estado actual de categorías, subcategorías y productos"""
    print("🏷️  ESTADO ACTUAL DE CATEGORÍAS")
    print("=" * 50)
    
    categorias = Categoria.objects.all()
    
    if not categorias:
        print("❌ No hay categorías registradas")
        return
    
    for categoria in categorias:
        subcategorias_count = categoria.subcategorias.count()
        
        # Contar productos asociados
        productos_count = 0
        for subcategoria in categoria.subcategorias.all():
            productos_count += subcategoria.producto_set.count()
        
        print(f"📂 {categoria.nombre} (ID: {categoria.id})")
        print(f"   📝 Subcategorías: {subcategorias_count}")
        print(f"   📦 Productos: {productos_count}")
        
        # Mostrar si se puede eliminar
        puede_eliminar = subcategorias_count == 0 and productos_count == 0
        estado = "✅ Puede eliminarse" if puede_eliminar else "❌ No puede eliminarse"
        print(f"   {estado}")
        print()

def crear_categoria_prueba():
    """Crea una categoría de prueba"""
    try:
        categoria, created = Categoria.objects.get_or_create(
            nombre="Categoría de Prueba"
        )
        if created:
            print("✅ Categoría de prueba creada exitosamente")
        else:
            print("ℹ️  La categoría de prueba ya existe")
        return categoria
    except Exception as e:
        print(f"❌ Error al crear categoría de prueba: {e}")
        return None

def main():
    print("🧪 SCRIPT DE PRUEBA - CATEGORÍAS")
    print("=" * 40)
    
    # Mostrar estado actual
    mostrar_estado_categorias()
    
    # Crear categoría de prueba si no existe
    print("\n🛠️  CREANDO CATEGORÍA DE PRUEBA")
    print("-" * 30)
    categoria_prueba = crear_categoria_prueba()
    
    if categoria_prueba:
        print(f"📂 Categoría creada: {categoria_prueba.nombre} (ID: {categoria_prueba.id})")
        print(f"🔗 URL de edición: http://127.0.0.1:8000/categoria/{categoria_prueba.id}/editar/")
        print(f"🗑️  URL de eliminación: http://127.0.0.1:8000/categoria/{categoria_prueba.id}/eliminar/")
    
    print("\n" + "=" * 50)
    print("✅ Script completado. Puedes probar las URLs en el navegador.")

if __name__ == "__main__":
    main()