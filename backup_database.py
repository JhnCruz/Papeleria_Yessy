#!/usr/bin/env python
"""
Script standalone para backup de base de datos SQLite
Uso: python backup_database.py
"""

import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# Configuración
PROJECT_DIR = Path(__file__).parent
DB_PATH = PROJECT_DIR / 'db.sqlite3'
BACKUP_DIR = PROJECT_DIR / 'backups'
KEEP_DAYS = 30

def create_backup():
    """Crea un backup de la base de datos"""
    
    if not DB_PATH.exists():
        print(f'❌ Base de datos no encontrada: {DB_PATH}')
        return False
    
    # Crear carpeta de backups
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Nombre del archivo con timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = BACKUP_DIR / f'db_backup_{timestamp}.sqlite3'
    
    try:
        # SQL dump de la base de datos
        conn = sqlite3.connect(str(DB_PATH))
        with open(str(backup_file), 'w') as f:
            for line in conn.iterdump():
                f.write(f'{line}\n')
        conn.close()
        
        file_size = backup_file.stat().st_size / (1024 * 1024)
        print(f'✅ Backup creado: {backup_file.name} ({file_size:.2f} MB)')
        
        # Limpiar backups antiguos
        cleanup_old_backups()
        
        return True
        
    except Exception as e:
        print(f'❌ Error creando backup: {e}')
        return False

def cleanup_old_backups():
    """Elimina backups más antiguos que KEEP_DAYS"""
    
    cutoff_date = datetime.now() - timedelta(days=KEEP_DAYS)
    deleted_count = 0
    
    for backup_file in BACKUP_DIR.glob('db_backup_*.sqlite3'):
        file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
        
        if file_mtime < cutoff_date:
            try:
                backup_file.unlink()
                deleted_count += 1
            except Exception as e:
                print(f'⚠️  No se pudo eliminar {backup_file.name}: {e}')
    
    if deleted_count > 0:
        print(f'🗑️  {deleted_count} backup(s) antiguo(s) eliminado(s)')

if __name__ == '__main__':
    import sys
    
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Iniciando backup...')
    
    if create_backup():
        print('✅ Proceso completado exitosamente')
        sys.exit(0)
    else:
        print('❌ Proceso falló')
        sys.exit(1)
