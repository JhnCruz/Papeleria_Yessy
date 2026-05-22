#!/usr/bin/env python
"""Test final: crear categoría con CSRF token"""
import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client

print("="*70)
print("🧪 TEST FINAL: Crear categoría con CSRF")
print("="*70)

# Login y obtener sesión
client = Client()
response = client.post('/usuarios/login/', {
    'username': 'yessy',
    'password': 'yessy1987'
})

# GET a la página para obtener token
response = client.get('/productos/agregar-nuevo/')
html = response.content.decode('utf-8')

# Extraer token
match = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', html)
if match:
    token = match.group(1)
    print(f"\n✅ Token CSRF encontrado:")
    print(f"   {token[:30]}...{token[-30:]}")
    print(f"   Longitud: {len(token)}")
    
    # POST para crear categoría
    response = client.post('/productos/crear-categoria/', 
        {'nombre': 'Test Papelería', 'descripcion': 'Test'},
        HTTP_X_CSRFTOKEN=token,
        content_type='application/json'
    )
    
    print(f"\n📤 POST /productos/crear-categoria/")
    print(f"   Status: {response.status_code}")
    try:
        import json
        data = json.loads(response.content)
        print(f"   Respuesta: {data}")
        if response.status_code == 200:
            print(f"   ✅ CATEGORÍA CREADA EXITOSAMENTE")
    except:
        print(f"   Respuesta (raw): {response.content.decode()[:150]}")
else:
    print("❌ Token no encontrado")

print("\n" + "="*70)
