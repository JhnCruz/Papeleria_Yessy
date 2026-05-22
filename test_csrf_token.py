#!/usr/bin/env python
"""Test específico: ver HTML completo de agregar_nuevo"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

client = Client()
user = User.objects.get(username='yessy')
client.login(username='yessy', password='yessy1987')

response = client.get('/productos/agregar-nuevo/')
html = response.content.decode('utf-8')

# Guardar a archivo para revisar
with open('/tmp/agregar_nuevo_debug.html', 'w') as f:
    f.write(html)

# Buscar CSRF token
import re
csrf_pattern = r'<input[^>]*name="csrftoken"[^>]*value="([^"]*)"[^>]*>'
match = re.search(csrf_pattern, html)

print("="*70)
print("Token CSRF en HTML:")
if match:
    token = match.group(1)
    print(f"✅ Encontrado")
    print(f"   Valor: {token}")
    print(f"   Longitud: {len(token)}")
    print(f"   Primeros 10: {token[:10]}")
    print(f"   Últimos 10: {token[-10:]}")
else:
    print("❌ No encontrado")
    
    # Buscar cualquier input con csrftoken
    if '<input' in html and 'csrftoken' in html:
        idx = html.find('csrftoken')
        print(f"Contexto donde aparece csrftoken:")
        print(html[max(0, idx-100):idx+150])

print("\nArchivo guardado: /tmp/agregar_nuevo_debug.html")
