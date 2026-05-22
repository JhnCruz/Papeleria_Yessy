#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Diagnóstico específico para crear producto
"""

import os
import django
import json
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from productos.models import Categoria

print("\n" + "="*60)
print("  🔍 DIAGNÓSTICO: CREAR PRODUCTO")
print("="*60 + "\n")

# Login
client = Client()
client.login(username='Yessy', password='Yessy1987')

# Crear categoría de prueba
print("1. Creando categoría de prueba...")
try:
    cat, created = Categoria.objects.get_or_create(
        nombre='Test Papelería',
        defaults={'descripcion': 'Categoría de test', 'activa': True}
    )
    print(f"   ✓ Categoría ID: {cat.id}, Nombre: {cat.nombre}\n")
except Exception as e:
    print(f"   ✗ Error: {e}\n")
    traceback.print_exc()

# Intentar crear producto
print("2. Enviando datos para crear producto...")
datos = {
    'nombre': 'Test Producto',
    'sku': 'TEST-001',
    'categoria': str(cat.id),
    'precio_costo': '50.00',
    'precio_venta': '100.00',
    'stock_minimo': '10',
    'stock_actual': '100',
}
print(f"   Datos: {datos}\n")

try:
    response = client.post('/productos/crear/', data=datos)
    print(f"3. Respuesta:")
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.get('content-type')}\n")
    
    if response.status_code != 200:
        print(f"4. Contenido de error:")
        print(f"   {response.content[:500]}\n")
        
        # Intentar parsear error
        try:
            if 'application/json' in response.get('content-type', ''):
                data = response.json()
                print(f"   JSON Error: {data}\n")
        except:
            pass
            
except Exception as e:
    print(f"   ✗ Error al enviar: {e}\n")
    traceback.print_exc()

print("="*60 + "\n")
