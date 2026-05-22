from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import PerfilUsuario


def admin_required(view_func):
    """Decorador que requiere que el usuario sea administrador"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('usuarios:login')
        
        try:
            perfil = request.user.perfil
            if perfil.rol != 'administrador':
                messages.error(request, '❌ Acceso denegado. Solo administradores.')
                return redirect('index')
        except PerfilUsuario.DoesNotExist:
            messages.error(request, '❌ Acceso denegado. Perfil no encontrado.')
            return redirect('index')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
