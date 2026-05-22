#!/usr/bin/env python
"""Test para verificar qué categorías se muestran en agregar_nuevo.html"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from productos.models import Categoria

print("="*60)
print("🔍 TEST: Verificar categorías en agregar_nuevo.html")
print("="*60 + "\n")

# 1. Ver categorías en BD
print("1️⃣ CATEGORÍAS EN BASE DE DATOS:")
categorias = Categoria.objects.filter(activa=True)
print(f"   Total: {categorias.count()}")
for cat in categorias:
    print(f"     - {cat.id}: {cat.nombre}")

# 2. Hacer request a la página
print("\n2️⃣ HACER REQUEST A /productos/agregar-nuevo/:")
client = Client()

# Obtener o crear usuario
user, _ = User.objects.get_or_create(username='testuser', defaults={'is_staff': True, 'is_superuser': True})
if _ :
    user.set_password('test123')
    user.save()

# Login
client.login(username='testuser', password='test123')

# Request
response = client.get('/productos/agregar-nuevo/')
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    html = response.content.decode('utf-8')
    
    # Buscar opciones del select
    print("\n3️⃣ OPCIONES DE CATEGORÍA EN HTML:")
    import re
    pattern = r'<option value="(\d+)">([^<]+)</option>'
    matches = re.findall(pattern, html)
    
    if matches:
        print(f"   Total opciones encontradas: {len(matches)}")
        for cat_id, cat_name in matches:
            if cat_id:  # Skip el "-- Seleccionar --"
                print(f"     - ID: {cat_id}, Nombre: {cat_name}")
    else:
        print("   ✅ No hay opciones (correcto - BD limpia)")
        
        # Verificar que está el placeholder
        if '-- Seleccionar categoría --' in html:
            print("   ✅ Placeholder presente")
else:
    print(f"   ❌ Error: {response.status_code}")

print("\n" + "="*60)
