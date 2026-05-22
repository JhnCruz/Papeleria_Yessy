#!/usr/bin/env python3
"""
Script para compilar Papelería Yessy a ejecutable (.exe en Windows)
Funciona en Windows, macOS y Linux
"""

import os
import sys
import subprocess
from pathlib import Path

def build_exe():
    """Construir el ejecutable usando PyInstaller"""
    
    project_dir = Path(__file__).parent
    
    # Cambiar al directorio del proyecto
    os.chdir(str(project_dir))
    
    print("=" * 70)
    print("🔨 COMPILACIÓN: Papelería Yessy - PRODUCCIÓN")
    print("=" * 70)
    
    # Verificar que PyInstaller esté instalado
    try:
        import PyInstaller
        print("✅ PyInstaller detectado")
    except ImportError:
        print("❌ PyInstaller no está instalado")
        print("   Instalando PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller', '-q'])
    
    # Configurar variables de entorno
    os.environ['ENVIRONMENT'] = 'production'
    
    # Archivos y directorios a incluir
    data_dirs = [
        'manage.py',
        'core',
        'productos',
        'ventas',
        'caja',
        'reportes',
        'usuarios',
        'inventario',
        'templates',
        'static',
        'pape',  # Archivos HTML estáticos
    ]
    
    # Construir comando PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name', 'Papeleria-Yessy',
        '--onefile',
        '--windowed',
        '--distpath', str(project_dir / 'dist'),
        '--buildpath', str(project_dir / 'build'),
        '--specpath', str(project_dir),
        '--noconfirm',
    ]
    
    # Agregar datos
    for data_dir in data_dirs:
        if Path(data_dir).exists():
            cmd.append('--add-data')
            cmd.append(f'{data_dir}:{data_dir}')
    
    # Archivo principal
    cmd.append('launcher.py')
    
    print("\n🔨 Compilando...")
    print(f"   Comando: {' '.join(cmd)}")
    print("\n")
    
    # Ejecutar PyInstaller
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("✅ COMPILACIÓN EXITOSA")
        print("=" * 70)
        print("\n📦 Archivos generados:")
        dist_dir = project_dir / 'dist'
        if dist_dir.exists():
            for exe in dist_dir.glob('Papeleria-Yessy*'):
                print(f"   → {exe}")
        print("\n🚀 El ejecutable está listo para usar en PRODUCCIÓN")
        print("\n✨ Nuevo: Modo Gunicorn (servidor web optimizado)")
        print("   - DEBUG=False")
        print("   - 4 workers con 2 threads cada uno")
        print("   - Puerto: 8000")
        print("\n" + "=" * 70)
    else:
        print("\n❌ Error durante la compilación")
        sys.exit(1)

if __name__ == '__main__':
    build_exe()
