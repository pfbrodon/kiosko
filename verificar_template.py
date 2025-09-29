#!/usr/bin/env python
"""
Script para verificar que los templates no tienen errores de sintaxis
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
from django.template import Context

def verificar_template():
    print("=== VERIFICACIÓN DEL TEMPLATE ===\n")
    
    try:
        # Cargar el template
        template = get_template('registrar_movimientos.html')
        print("✅ Template cargado correctamente")
        
        # Crear un contexto de prueba básico
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
        
        # Intentar renderizar
        rendered = template.render(context)
        print("✅ Template renderizado correctamente")
        print(f"   Tamaño del HTML generado: {len(rendered)} caracteres")
        
        # Verificar que contiene las funciones JavaScript
        if 'handleEnterKey' in rendered:
            print("✅ Función handleEnterKey encontrada")
        else:
            print("❌ Función handleEnterKey NO encontrada")
            
        if 'DOMContentLoaded' in rendered:
            print("✅ Event listener DOMContentLoaded encontrado")
        else:
            print("❌ Event listener DOMContentLoaded NO encontrado")
            
        if 'onkeydown="handleEnterKey' in rendered:
            print("✅ Atributos onkeydown encontrados en formularios")
        else:
            print("❌ Atributos onkeydown NO encontrados")
        
    except Exception as e:
        print(f"❌ Error al verificar template: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = verificar_template()
    if success:
        print("\n🎉 ¡Todo verificado correctamente!")
    else:
        print("\n💥 Hay problemas que necesitan corrección")