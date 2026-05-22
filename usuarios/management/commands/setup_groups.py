"""
Management command para crear grupos de roles con permisos
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

# Mapear de tipos de contenido a modelos
MODELS_MAP = {
    'venta': 'ventas.venta',
    'devolucion': 'ventas.devolucion',
    'producto': 'productos.producto',
    'inventario': 'inventario.movimientoinventario',
    'empleado': 'usuarios.empleado',
    'corte_caja': 'caja.cortecaja',
}

ROLES = {
    'Admin': {
        'permissions': ['add', 'change', 'delete', 'view'],
        'models': ['venta', 'devolucion', 'producto', 'inventario', 'empleado', 'corte_caja'],
        'description': 'Acceso total a todas las funciones'
    },
    'Gerente': {
        'permissions': ['add', 'change', 'view'],
        'models': ['venta', 'devolucion', 'producto', 'inventario', 'corte_caja'],
        'description': 'Ventas, devoluciones, reportes, inventario'
    },
    'Vendedor': {
        'permissions': ['add', 'view'],
        'models': ['venta', 'devolucion', 'producto'],
        'description': 'POS, devoluciones, consultar inventario'
    },
    'Contable': {
        'permissions': ['view'],
        'models': ['venta', 'devolucion', 'producto', 'inventario', 'corte_caja'],
        'description': 'Solo visualización de reportes y auditoría'
    }
}


class Command(BaseCommand):
    help = 'Crea grupos de roles con permisos'

    def handle(self, *args, **options):
        for role_name, role_config in ROLES.items():
            group, created = Group.objects.get_or_create(name=role_name)
            
            if created:
                self.stdout.write(f"✓ Grupo '{role_name}' creado")
            else:
                self.stdout.write(f"⚠ Grupo '{role_name}' ya existe")
                group.permissions.clear()
            
            # Agregar permisos
            for model_key in role_config['models']:
                model_str = MODELS_MAP.get(model_key)
                if not model_str:
                    self.stderr.write(f"Modelo {model_key} no encontrado")
                    continue
                
                app_label, model_name = model_str.split('.')
                
                try:
                    content_type = ContentType.objects.get(app_label=app_label, model=model_name)
                    
                    for perm_type in role_config['permissions']:
                        codename = f'{perm_type}_{model_name}'
                        try:
                            permission = Permission.objects.get(
                                content_type=content_type,
                                codename=codename
                            )
                            group.permissions.add(permission)
                        except Permission.DoesNotExist:
                            self.stderr.write(f"Permiso {codename} no encontrado")
                
                except ContentType.DoesNotExist:
                    self.stderr.write(f"Modelo {app_label}.{model_name} no encontrado")
            
            self.stdout.write(f"  → {group.permissions.count()} permisos asignados")
        
        self.stdout.write(self.style.SUCCESS('\n✓ Grupos y permisos configurados exitosamente'))
