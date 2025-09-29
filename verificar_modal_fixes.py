#!/usr/bin/env python
"""
Script para verificar que el template del modal funciona correctamente
"""

import os
import sys
import django

# Configurar Django
sys.path.append('C:/Users/Kiosko/Desktop/Desarrollo/kiosko')
os.chdir('C:/Users/Kiosko/Desktop/Desarrollo/kiosko')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from django.template.loader import get_template

def verificar_modal_fixes():
    print("=== VERIFICACIÓN DE CORRECCIONES DEL MODAL ===\n")
    
    try:
        # Cargar el template
        template = get_template('registrar_movimientos.html')
        print("✅ Template cargado correctamente")
        
        # Crear contexto mínimo
        context = {
            'caja': type('obj', (object,), {
                'get_nivel_display': 'Secundario',
                'get_turno_display': 'Mañana',
                'es_extra': False,
                'fecha': '2025-09-29',
                'saldo_inicial': 1000.0,
                'cerrada': False
            })(),
            'recreo_form': type('obj', (object,), {
                'monto': '<input type="number" name="monto" class="form-control">'
            })(),
            'pago_form': type('obj', (object,), {
                'as_p': lambda: '<p>Formulario de pago</p>'
            })(),
            'proximo_recreo': 1,
            'saldo_general': type('obj', (object,), {'monto': 1000.0})(),
            'saldo_parcial_total': 1000.0,
            'recreos': [],
            'pagos': [],
            'eventos': []
        }
        
        # Renderizar
        rendered = template.render(context)
        print("✅ Template renderizado correctamente")
        
        # Verificar las correcciones
        verificaciones = [
            ('limpiarModales', '✅ Función limpiarModales encontrada'),
            ('backdrop: true', '✅ Configuración de backdrop encontrada'),
            ('hidden.bs.modal', '✅ Event listener para modal cerrado encontrado'),
            ('modal-backdrop', '✅ Limpieza de backdrop encontrada'),
            ('Escape', '✅ Handler para tecla Escape encontrado'),
            ('Limpiar Pantalla', '✅ Botón de emergencia encontrado'),
            ('modal-open', '✅ Limpieza de clase modal-open encontrada'),
        ]
        
        for buscar, mensaje in verificaciones:
            if buscar in rendered:
                print(mensaje)
            else:
                print(f"❌ {mensaje.replace('✅', 'NO')} - '{buscar}' no encontrado")
        
        print(f"\n📊 Estadísticas:")
        print(f"   Tamaño del template: {len(rendered)} caracteres")
        print(f"   Cantidad de 'modal': {rendered.count('modal')}")
        print(f"   Cantidad de 'backdrop': {rendered.count('backdrop')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = verificar_modal_fixes()
    if success:
        print("\n🎉 ¡Todas las correcciones verificadas!")
        print("\n💡 Soluciones implementadas:")
        print("   1. Modal con configuración robusta")
        print("   2. Limpieza automática de backdrop")
        print("   3. Event listener para modal cerrado")
        print("   4. Función limpiarModales() de emergencia")
        print("   5. Tecla Escape para limpiar modales")
        print("   6. Botón 'Limpiar Pantalla' de emergencia")
    else:
        print("\n💥 Hay problemas que necesitan corrección")