"""
Middleware para validar estado de usuarios activos
"""
from django.shortcuts import redirect
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.contrib import messages
from .models import PerfilUsuario


class VerificarUsuarioActivoMiddleware:
    """
    Middleware que verifica si un usuario autenticado sigue siendo activo.
    Si el usuario ha sido desactivado mientras estaba conectado, lo desconecta.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Rutas que se permiten sin verificación de estado
        self.rutas_permitidas = [
            reverse('usuarios:logout'),
            reverse('usuarios:perfil'),
        ]
    
    def __call__(self, request):
        # Verificar si el usuario está autenticado y no es anónimo
        if request.user and not isinstance(request.user, AnonymousUser) and request.user.is_authenticated:
            try:
                perfil = request.user.perfil
                
                # Si el usuario está inactivo, desconectarlo
                if not perfil.activo:
                    from django.contrib.auth import logout
                    logout(request)
                    messages.warning(
                        request,
                        '⚠️ Tu cuenta ha sido desactivada. Por favor, contacta con un administrador.'
                    )
                    return redirect('usuarios:login')
            
            except PerfilUsuario.DoesNotExist:
                # Si no existe perfil, permitir continuar pero con advertencia
                pass
        
        response = self.get_response(request)
        return response
