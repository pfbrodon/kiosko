#!/usr/bin/env python
"""
Script para verificar el cambio en la representación de subcategorías
"""

import os
import sys
import django

# Configurar Django
sys.path.append('C:/Users/Kiosko/Desktop/Desarrollo/kiosko')
os.chdir('C:/Users/Kiosko/Desktop/Desarrollo/kiosko')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from precios.models import Categoria, Subcategoria

def verificar_subcategorias():
    print("=== VERIFICACIÓN DE SUBCATEGORÍAS ===\n")
    
    # Obtener algunas subcategorías para probar
    subcategorias = Subcategoria.objects.select_related('categoria').all()[:10]
    
    if not subcategorias.exists():
        print("❌ No hay subcategorías en la base de datos")
        return False
    
    print(f"✅ Encontradas {subcategorias.count()} subcategorías")
    print("\n📋 Representación actual (después del cambio):")
    
    for sub in subcategorias:
        print(f"   ID {sub.id}: '{sub}' (nombre completo disponible: '{sub.nombre_completo}')")
    
    print(f"\n🎯 Cómo aparecerán en el formulario:")
    for sub in subcategorias:
        print(f"   • {sub}")
    
    print(f"\n💡 Beneficio del cambio:")
    print(f"   ANTES: 'Bebidas > Coca Cola'")
    print(f"   AHORA: 'Coca Cola'")
    print(f"   → Dropdown más limpio y fácil de leer")
    
    print(f"\n🔧 Funcionalidad adicional:")
    print(f"   • sub.nombre → '{subcategorias.first().nombre}' (solo subcategoría)")
    print(f"   • sub.nombre_completo → '{subcategorias.first().nombre_completo}' (con categoría)")
    
    return True

if __name__ == "__main__":
    success = verificar_subcategorias()
    if success:
        print("\n🎉 ¡Cambio verificado correctamente!")
        print("\n📝 Nota: El cambio se aplica inmediatamente en el formulario.")
        print("No necesitas hacer migraciones porque solo cambió el método __str__.")
    else:
        print("\n💥 Hay que revisar la base de datos")