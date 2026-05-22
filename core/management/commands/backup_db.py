import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Realiza una copia de seguridad de la base de datos SQLite'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-days',
            type=int,
            default=30,
            help='Días de backups a mantener (por defecto: 30)',
        )

    def handle(self, *args, **options):
        """Crea un backup de la base de datos y limpia backups antiguos"""
        
        # Obtener ruta de la BD
        db_path = settings.DATABASES['default']['NAME']
        
        if not os.path.exists(db_path):
            self.stdout.write(
                self.style.ERROR(f'❌ Base de datos no encontrada: {db_path}')
            )
            return
        
        # Crear carpeta de backups si no existe
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Nombre del archivo backup con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'db_backup_{timestamp}.sqlite3'
        backup_path = backup_dir / backup_filename
        
        try:
            # Hacer conexión a BD original
            conn = sqlite3.connect(str(db_path))
            
            # Crear backup usando dump
            with open(str(backup_path), 'w') as f:
                for line in conn.iterdump():
                    f.write(f'{line}\n')
            
            conn.close()
            
            file_size = backup_path.stat().st_size / (1024 * 1024)  # MB
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Backup creado exitosamente: {backup_filename} ({file_size:.2f} MB)'
                )
            )
            
            # Limpiar backups antiguos
            self._cleanup_old_backups(backup_dir, options['keep_days'])
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creando backup: {str(e)}')
            )
            return
    
    def _cleanup_old_backups(self, backup_dir, keep_days):
        """Elimina backups más antiguos que keep_days"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0
        
        for backup_file in backup_dir.glob('db_backup_*.sqlite3'):
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            if file_mtime < cutoff_date:
                try:
                    backup_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  No se pudo eliminar {backup_file.name}: {str(e)}'
                        )
                    )
        
        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'🗑️  {deleted_count} backup(s) antiguo(s) eliminado(s)'
                )
            )
