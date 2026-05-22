"""
Decoradores y utilidades para permisos basados en roles
"""
from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required


def requiere_grupo(*grupos):
    """
    Decorador que verifica que el usuario pertenece a uno de los grupos especificados
    
    Uso:
        @requiere_grupo('Admin', 'Gerente')
        def mi_vista(request):
            ...
    """
    def decorador(vista):
        @wraps(vista)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Permitir superusuarios
            if request.user.is_superuser:
                return vista(request, *args, **kwargs)
            
            # Verificar si el usuario pertenece a uno de los grupos
            if request.user.groups.filter(name__in=grupos).exists():
                return vista(request, *args, **kwargs)
            
            return HttpResponseForbidden(
                '<h1>403 - Acceso Denegado</h1><p>No tienes permisos para acceder a esta página.</p>'
            )
        return wrapper
    return decorador


def requiere_permiso(permiso):
    """
    Decorador que verifica que el usuario tiene un permiso específico
    
    Uso:
        @requiere_permiso('productos.add_producto')
        def mi_vista(request):
            ...
    """
    def decorador(vista):
        @wraps(vista)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Permitir superusuarios
            if request.user.is_superuser:
                return vista(request, *args, **kwargs)
            
            # Verificar si el usuario tiene el permiso
            if request.user.has_perm(permiso):
                return vista(request, *args, **kwargs)
            
            return HttpResponseForbidden(
                '<h1>403 - Acceso Denegado</h1><p>No tienes el permiso requerido para esta acción.</p>'
            )
        return wrapper
    return decorador


def obtener_grupo_usuario(usuario):
    """Obtiene el nombre del grupo principal del usuario"""
    grupos = usuario.groups.all()
    if grupos:
        # Prioridad: Admin > Gerente > Vendedor > Contable
        nombres_grupos = [g.name for g in grupos]
        prioridad = {'Admin': 0, 'Gerente': 1, 'Vendedor': 2, 'Contable': 3}
        grupo_principal = min(nombres_grupos, key=lambda x: prioridad.get(x, 999))
        return grupo_principal
    return 'Sin grupo'
