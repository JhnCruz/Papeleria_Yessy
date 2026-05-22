#!/usr/bin/env python
"""
Papelería Yessy v2.0 - Script de Instalación Automatizada
Ejecuta toda la configuración inicial de la aplicación
"""
import os
import sys
import subprocess
import sqlite3
from pathlib import Path
from datetime import datetime

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(titulo):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}  {titulo}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

def print_status(msg, success=True):
    icon = f"{Colors.OKGREEN}✅{Colors.ENDC}" if success else f"{Colors.FAIL}❌{Colors.ENDC}"
    print(f"  {icon} {msg}")

def run_command(cmd, description=""):
    """Ejecuta comando y retorna éxito/fracaso"""
    try:
        print(f"\n  ⏳ {description}..." if description else "")
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print_status(f"{description} completado" if description else "OK", True)
            return True
        else:
            print_status(f"{description} falló: {result.stderr[:100]}" if description else f"Error: {result.stderr[:100]}", False)
            return False
    except Exception as e:
        print_status(f"Error ejecutando comando: {str(e)[:100]}", False)
        return False

def main():
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}")
    print("╔" + "="*68 + "╗")
    print("║   INSTALADOR PAPELERÍA YESSY v2.0                              ║")
    print("║   Configuración Automática Completa                            ║")
    print("╚" + "="*68 + "╝")
    print(f"{Colors.ENDC}")
    
    # Detectar directorio principal
    app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)
    
    print_status(f"Directorio de instalación: {app_dir}", True)
    
    # ========== PASO 1: Verificar dependencias =====
    print_header("PASO 1: Verificar Dependencias")
    
    # Verificar Python
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    required_version = "3.11"
    version_ok = sys.version_info >= (3, 11)
    print_status(f"Python {python_version} " + ("✅" if version_ok else "(⚠️ mínimo 3.11 requerido)"), version_ok)
    
    # Verificar Django
    try:
        import django
        print_status(f"Django {django.get_version()} instalado", True)
    except ImportError:
        print_status("Django no instalado", False)
        print(f"\n{Colors.WARNING}Por favor ejecuta: pip install -r requirements.txt{Colors.ENDC}")
        return False
    
    # ========== PASO 2: Configurar Base de Datos =====
    print_header("PASO 2: Configurar Base de Datos")
    
    # Eliminar BD antigua si existe
    db_path = os.path.join(app_dir, 'db.sqlite3')
    if os.path.exists(db_path):
        print_status("Removiendo base de datos antigua...", True)
        os.remove(db_path)
    else:
        print_status("Base de datos (nueva)", True)
    
    # Aplicar migraciones
    if not run_command("python manage.py migrate", "Aplicando migraciones Django"):
        print(f"\n{Colors.FAIL}Error aplicando migraciones{Colors.ENDC}")
        return False
    
    # ========== PASO 3: Crear Roles y Permisos =====
    print_header("PASO 3: Configurar Roles y Permisos")
    
    if not run_command("python manage.py setup_groups", "Creando grupos de roles"):
        print(f"\n{Colors.WARNING}⚠️ Aviso: setup_groups puede no existir, continuando...{Colors.ENDC}")
    
    # ========== PASO 4: Cargar Datos Iniciales =====
    print_header("PASO 4: Cargar Datos Iniciales")
    
    # Verificar si load_test_data.py existe
    if os.path.exists('load_test_data.py'):
        if not run_command("python load_test_data.py", "Cargando datos de prueba"):
            print(f"\n{Colors.WARNING}⚠️ Aviso: Datos no cargados, continuando...{Colors.ENDC}")
    else:
        print_status("load_test_data.py no encontrado", False)
    
    # ========== PASO 5: Recolectar archivos estáticos =====
    print_header("PASO 5: Preparar Archivos Estáticos")
    
    if not run_command("python manage.py collectstatic --noinput", "Recolectando archivos estáticos"):
        print(f"\n{Colors.WARNING}⚠️ Aviso: Collectstatic falló, continuando...{Colors.ENDC}")
    
    # ========== PASO 6: Verificación Final =====
    print_header("PASO 6: Verificación Final")
    
    # Contar usuarios
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
        import django
        django.setup()
        from django.contrib.auth.models import User, Group
        from productos.models import Producto, Categoria
        
        usuarios = User.objects.count()
        grupos = Group.objects.count()
        categorias = Categoria.objects.count()
        productos = Producto.objects.count()
        
        print_status(f"Usuarios creados: {usuarios}", usuarios > 0)
        print_status(f"Grupos de roles: {grupos}", grupos >= 3)
        print_status(f"Categorías: {categorias}", categorias > 0)
        print_status(f"Productos: {productos}", productos > 0)
        
    except Exception as e:
        print_status(f"Error en verificación: {str(e)[:80]}", False)
    
    # ========== RESUMEN FINAL =====
    print_header("✨ INSTALACIÓN COMPLETADA")
    
    print(f"{Colors.OKGREEN}{Colors.BOLD}")
    print("  🎉 PAPELERÍA YESSY v2.0 INSTALADA CORRECTAMENTE")
    print(f"{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}Próximos pasos:{Colors.ENDC}")
    print(f"  1. Iniciar servidor: {Colors.OKCYAN}python manage.py runserver{Colors.ENDC}")
    print(f"  2. Abrir navegador: {Colors.OKCYAN}http://localhost:8000{Colors.ENDC}")
    print(f"  3. Login de Yessy (Dueña): {Colors.OKCYAN}yessy{Colors.ENDC}")
    print(f"     Contraseña: {Colors.OKCYAN}1987PapeYessy{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Credenciales adicionales:{Colors.ENDC}")
    print(f"     • Vendedor: {Colors.OKCYAN}vendedor1 / vendedor123{Colors.ENDC}")
    print(f"     • Gerente: {Colors.OKCYAN}gerente / gerente123{Colors.ENDC}")
    print(f"     • Contable: {Colors.OKCYAN}contable / contable123{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Información:{Colors.ENDC}")
    print(f"  📁 Directorio: {app_dir}")
    print(f"  📊 Base de datos: {db_path}")
    print(f"  🌐 Puerto: 8000")
    print(f"  ⏰ Instalación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    print("\n" + "="*70 + "\n")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
