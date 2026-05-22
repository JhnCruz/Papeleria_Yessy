#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Papelería Yessy - Verificación Final de Producción v2.1
Script para validar que todo está configurado correctamente para deployment
"""

import os
import sys
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check(condition, message):
    status = "✓" if condition else "✗"
    color = "\033[92m" if condition else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {message}")
    return condition

def main():
    os.chdir(Path(__file__).parent)
    all_passed = True
    
    print_header("VERIFICACIÓN DE PRODUCCIÓN v2.1")
    
    # ==================== ARCHIVOS ====================
    print("\n📁 VERIFICACIÓN DE ARCHIVOS:")
    files_to_check = [
        ("core/settings.py", "Archivo de configuración"),
        ("manage.py", "Django management script"),
        ("requirements.txt", "Dependencias Python"),
        ("launcher_gui.py", "Launcher GUI"),
        ("Papeleria-Yessy-v2.0.nsi", "Instalador NSIS"),
        ("db.sqlite3", "Base de datos SQLite"),
        ("staticfiles", "Static files compilados"),
        ("logs", "Directorio de logs"),
    ]
    
    for file_path, description in files_to_check:
        exists = Path(file_path).exists()
        all_passed &= check(exists, f"{description}: {file_path}")
    
    # ==================== SEGURIDAD ====================
    print("\n🔒 VERIFICACIÓN DE SEGURIDAD:")
    
    try:
        from core.settings import SECRET_KEY, DEBUG, ALLOWED_HOSTS, MIDDLEWARE
        
        # Check SECRET_KEY
        secret_ok = len(SECRET_KEY) >= 50 and SECRET_KEY != 'django-insecure-'
        all_passed &= check(secret_ok, f"SECRET_KEY configurado (longitud: {len(SECRET_KEY)})")
        
        # Check DEBUG
        debug_ok = DEBUG == False
        all_passed &= check(debug_ok, f"DEBUG mode: {DEBUG} (debe ser False)")
        
        # Check ALLOWED_HOSTS
        hosts_ok = 'localhost' in ALLOWED_HOSTS and '127.0.0.1' in ALLOWED_HOSTS
        all_passed &= check(hosts_ok, f"ALLOWED_HOSTS configurado: {ALLOWED_HOSTS[:3]}...")
        
        # Check GZIP middleware
        gzip_ok = 'django.middleware.gzip.GZipMiddleware' in MIDDLEWARE
        all_passed &= check(gzip_ok, "GZipMiddleware habilitado")
        
    except Exception as e:
        all_passed &= check(False, f"Error importando settings: {e}")
    
    # ==================== STATIC FILES ====================
    print("\n📦 VERIFICACIÓN DE STATIC FILES:")
    
    static_dir = Path("staticfiles")
    if static_dir.exists():
        static_count = len(list(static_dir.rglob("*")))
        all_passed &= check(static_count > 100, f"Static files compilados: {static_count} archivos")
    else:
        all_passed &= check(False, "Directorio staticfiles no existe")
    
    # ==================== DATABASE ====================
    print("\n🗄️  VERIFICACIÓN DE BASE DE DATOS:")
    
    db_file = Path("db.sqlite3")
    all_passed &= check(db_file.exists(), f"Base de datos existe: {db_file}")
    
    if db_file.exists():
        db_size_mb = db_file.stat().st_size / (1024 * 1024)
        all_passed &= check(db_size_mb > 0.1, f"Tamaño DB: {db_size_mb:.2f}MB")
    
    # ==================== LOGGING ====================
    print("\n📝 VERIFICACIÓN DE LOGGING:")
    
    logs_dir = Path("logs")
    logs_expected = ["papeleria.log", "security.log", "errors.log"]
    
    if logs_dir.exists():
        existing_logs = [f.name for f in logs_dir.glob("*.log")]
        for log_file in logs_expected:
            exists = log_file in existing_logs
            all_passed &= check(exists or not logs_dir.exists(), f"Log file: {log_file}")
    else:
        check(True, "Logs directory will be created on first run")
    
    # ==================== DJANGO CHECK ====================
    print("\n✅ VERIFICACIÓN DE DJANGO:")
    
    try:
        import subprocess
        result = subprocess.run(
            ["python3", "manage.py", "check"],
            capture_output=True,
            text=True,
            timeout=10
        )
        django_ok = result.returncode == 0
        all_passed &= check(django_ok, "Django check: PASSED" if django_ok else f"FAILED: {result.stderr[:100]}")
    except Exception as e:
        all_passed &= check(False, f"Django check error: {str(e)[:50]}")
    
    # ==================== USUARIOS ====================
    print("\n👥 VERIFICACIÓN DE USUARIOS:")
    
    try:
        import django
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
        django.setup()
        
        from django.contrib.auth.models import User
        from usuarios.models import PerfilUsuario
        
        users = User.objects.all()
        all_passed &= check(users.exists(), f"Usuarios en sistema: {users.count()}")
        
        # Check for Yessy user
        yessy = User.objects.filter(username="Yessy").first()
        
        if yessy is None:
            # Create Yessy user
            print("  → Creando usuario Yessy...")
            yessy = User.objects.create_superuser(username="Yessy", email="yessy@papeleria.local", password="Yessy1987")
            all_passed &= check(True, "Usuario Yessy creado exitosamente")
        else:
            all_passed &= check(True, "Usuario Yessy existe")
            all_passed &= check(yessy.is_superuser, "Yessy es superuser")
        
    except Exception as e:
        all_passed &= check(False, f"Error verificando usuarios: {str(e)[:50]}")
    
    # ==================== RESUMEN ====================
    print_header("RESUMEN FINAL")
    
    if all_passed:
        print("✓ ¡Sistema listo para producción!")
        print("\nPara iniciar el servidor, ejecuta:")
        print("  python manage.py runserver 0.0.0.0:8000")
        print("\nO usa el script automatizado:")
        print("  bash deploy_production.sh")
        return 0
    else:
        print("✗ Se encontraron problemas. Revisa los errores arriba.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
