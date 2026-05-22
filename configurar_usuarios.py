#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, '/Users/johncruz/Desktop/Papeleria')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario

print("=" * 70)
print("CONFIGURANDO USUARIOS Y ROLES")
print("=" * 70 + "\n")

# 1. Crear usuario john si no existe
john, john_created = User.objects.get_or_create(
    username='john',
    defaults={'email': 'john@papeleria.local', 'first_name': 'John', 'is_staff': False}
)
if john_created:
    john.set_password('john123')
    john.save()
    print("[OK] Usuario 'john' creado")
else:
    print("[OK] Usuario 'john' ya existe")

# 2. Asignar perfil admin a john
perfil_john, _ = PerfilUsuario.objects.get_or_create(usuario=john)
perfil_john.rol = 'administrador'
perfil_john.activo = True
perfil_john.save()
print("[OK] john es ADMINISTRADOR\n")

# 3. Configurar Yessy como vendedor
try:
    yessy = User.objects.get(username='Yessy')
    perfil_yessy, _ = PerfilUsuario.objects.get_or_create(usuario=yessy)
    perfil_yessy.rol = 'vendedor'
    perfil_yessy.activo = True
    perfil_yessy.save()
    print("[OK] Yessy es VENDEDOR\n")
except User.DoesNotExist:
    print("[WARNING] Usuario Yessy no existe\n")

# 4. Mostrar resumen final
print("=" * 70)
print("RESUMEN DE USUARIOS")
print("=" * 70 + "\n")

usuarios = User.objects.all()
for user in usuarios:
    try:
        perfil = user.perfil
        rol = perfil.get_rol_display()
        activo = "[OK]" if perfil.activo else "[NO]"
    except PerfilUsuario.DoesNotExist:
        rol = "[NO PERFIL]"
        activo = "?"
    
    print("{:15} | {:15} | {}".format(user.username, rol, activo))

print("\n" + "=" * 70)
print("Configuracion completada!")
print("=" * 70)
