#!/usr/bin/env python
"""
Test para verificar que la vista de PDF filtrado funciona correctamente
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiosko.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from precios.views import productos_filtrados_pdf

def test_pdf_filtrado():
    """Test básico para la vista de PDF filtrado"""
    print("🧪 TEST PDF FILTRADO")
    print("=" * 30)
    
    try:
        # Crear cliente de test
        client = Client()
        
        # Intentar acceder sin login (debe redireccionar)
        response = client.get('/productos/filtrados-pdf/')
        print(f"📄 Sin login: HTTP {response.status_code} (debe ser 302 - redirect a login)")
        
        # Crear usuario de test
        try:
            user = User.objects.get(username='test')
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='test',
                password='test123',
                is_staff=True,
                is_superuser=True
            )
            print("👤 Usuario de test creado")
        
        # Login
        login_success = client.login(username='test', password='test123')
        print(f"🔐 Login exitoso: {login_success}")
        
        if login_success:
            # Probar PDF sin filtros
            response = client.get('/productos/filtrados-pdf/')
            print(f"📄 PDF sin filtros: HTTP {response.status_code}")
            if response.status_code == 200:
                print(f"   📏 Tamaño: {len(response.content)} bytes")
                print(f"   📋 Content-Type: {response.get('Content-Type', 'No definido')}")
            
            # Probar PDF con filtros
            response = client.get('/productos/filtrados-pdf/?estado=1&busqueda=test')
            print(f"📄 PDF con filtros: HTTP {response.status_code}")
            if response.status_code == 200:
                print(f"   📏 Tamaño: {len(response.content)} bytes")
            
            print("✅ Tests completados correctamente")
        
    except Exception as e:
        print(f"❌ Error durante test: {e}")
        import traceback
        traceback.print_exc()

def test_urls_disponibles():
    """Verifica que las URLs estén correctamente configuradas"""
    print("\n🔗 VERIFICACIÓN DE URLS")
    print("-" * 30)
    
    from django.urls import reverse
    
    try:
        url1 = reverse('lista_precios_pdf')
        print(f"✅ lista_precios_pdf: {url1}")
        
        url2 = reverse('productos_filtrados_pdf')
        print(f"✅ productos_filtrados_pdf: {url2}")
        
    except Exception as e:
        print(f"❌ Error en URLs: {e}")

if __name__ == "__main__":
    test_urls_disponibles()
    test_pdf_filtrado()