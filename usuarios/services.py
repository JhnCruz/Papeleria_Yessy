"""
Servicios de Usuarios - Capa de Dominio
"""
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from .models import PerfilUsuario, BitacoraAcceso


class UsuarioService:
    """Servicio para operaciones con usuarios"""
    
    @staticmethod
    @transaction.atomic
    def crear_usuario(username, password, first_name='', last_name='', 
                     email='', rol='vendedor', telefono=''):
        """Crea un nuevo usuario con perfil"""
        try:
            # Verificar si el usuario ya existe
            if User.objects.filter(username=username).exists():
                return False, "El usuario ya existe"
            
            # Crear usuario
            usuario = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            
            # Crear perfil
            PerfilUsuario.objects.create(
                usuario=usuario,
                rol=rol,
                telefono=telefono
            )
            
            return True, usuario
        
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def obtener_usuarios_activos():
        """Obtiene todos los usuarios activos"""
        return User.objects.filter(
            is_active=True,
            perfil__activo=True
        ).order_by('first_name')
    
    @staticmethod
    def obtener_usuario_por_username(username):
        """Obtiene un usuario por username"""
        try:
            return User.objects.get(username=username, is_active=True)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    @transaction.atomic
    def registrar_acceso(usuario, accion, descripcion='', ip_address=None):
        """Registra un acceso en la bitácora"""
        try:
            BitacoraAcceso.objects.create(
                usuario=usuario,
                accion=accion,
                descripcion=descripcion,
                ip_address=ip_address
            )
            
            # Actualizar último acceso en el perfil
            if accion == 'login':
                usuario.perfil.ultimo_acceso = timezone.now()
                usuario.perfil.save()
            
            return True, "Acceso registrado"
        
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def obtener_bitacora(usuario_id=None, accion=None, fecha_inicio=None, fecha_fin=None):
        """Obtiene registros de bitácora con filtros"""
        queryset = BitacoraAcceso.objects.all()
        
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)
        
        if accion:
            queryset = queryset.filter(accion=accion)
        
        if fecha_inicio:
            queryset = queryset.filter(created_at__gte=fecha_inicio)
        
        if fecha_fin:
            queryset = queryset.filter(created_at__lte=fecha_fin)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def cambiar_rol(usuario_id, nuevo_rol):
        """Cambia el rol de un usuario"""
        try:
            usuario = User.objects.get(id=usuario_id)
            usuario.perfil.rol = nuevo_rol
            usuario.perfil.save()
            return True, usuario
        except User.DoesNotExist:
            return False, "Usuario no encontrado"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def desactivar_usuario(usuario_id):
        """Desactiva un usuario"""
        try:
            usuario = User.objects.get(id=usuario_id)
            usuario.is_active = False
            usuario.save()
            usuario.perfil.activo = False
            usuario.perfil.save()
            return True, usuario
        except User.DoesNotExist:
            return False, "Usuario no encontrado"
        except Exception as e:
            return False, str(e)
