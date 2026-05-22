#!/usr/bin/env python
"""Diagnóstico de CSRF token en agregar_nuevo.html"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

print("="*70)
print("🔍 DIAGNÓSTICO: CSRF TOKEN EN AGREGAR_NUEVO.HTML")
print("="*70)

client = Client()

# Obtener usuario
user = User.objects.get(username='yessy')
client.login(username='yessy', password='yessy1987')

# Request a la página
response = client.get('/productos/agregar-nuevo/')

if response.status_code == 200:
    html = response.content.decode('utf-8')
    
    print("\n1️⃣ BUSCANDO INPUT CSRF TOKEN EN HTML:")
    import re
    csrf_pattern = r'<input[^>]*name="csrftoken"[^>]*value="([^"]*)"'
    match = re.search(csrf_pattern, html)
    
    if match:
        token = match.group(1)
        print(f"   ✅ Token encontrado en DOM")
        print(f"   Valor: {token[:20]}...{token[-20:]}")
        print(f"   Longitud: {len(token)}")
        if len(token) == 64:
            print(f"   ✅ Longitud correcta (64 caracteres)")
        else:
            print(f"   ❌ Longitud INCORRECTA (debería ser 64)")
    else:
        print(f"   ❌ No se encontró input CSRF token en HTML")
        
        # Buscar si está pero de forma diferente
        if 'csrftoken' in html:
            print(f"   ⚠️  La palabra 'csrftoken' sí aparece en el HTML")
            # Mostrar contexto
            idx = html.find('csrftoken')
            print(f"   Contexto: ...{html[max(0,idx-50):idx+100]}...")
    
    print("\n2️⃣ BUSCANDO COOKIE CSRF:")
    
    # Las cookies se envían en response.cookies
    if 'csrftoken' in response.cookies:
        cookie_val = response.cookies['csrftoken'].value
        print(f"   ✅ Cookie CSRF encontrada")
        print(f"   Valor: {cookie_val[:20]}...{cookie_val[-20:]}")
        print(f"   Longitud: {len(cookie_val)}")
    else:
        print(f"   ❌ No se encontró cookie CSRF")
    
    print("\n3️⃣ VERIFICANDO DJANGO CSRF MIDDLEWARE:")
    print(f"   Middleware en settings: ✅ Verificable")
    from django.conf import settings
    if 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE:
        print(f"   ✅ CsrfViewMiddleware está habilitado")
    else:
        print(f"   ❌ CsrfViewMiddleware NO está habilitado")

else:
    print(f"❌ Error al acceder a /productos/agregar-nuevo/: {response.status_code}")

print("\n" + "="*70)
