from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User, Group

from .services import UsuarioService
from .models import PerfilUsuario


def es_administrador(user):
    """Verifica si el usuario es administrador"""
    try:
        return user.perfil.rol == 'administrador'
    except PerfilUsuario.DoesNotExist:
        return False


def es_admin_o_supervisor(user):
    """Verifica si el usuario es administrador o supervisor"""
    try:
        return user.perfil.rol in ['administrador', 'supervisor']
    except PerfilUsuario.DoesNotExist:
        return False


def login_view(request):
    """Página de login"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        usuario = authenticate(request, username=username, password=password)
        
        if usuario is not None:
            # Verificar si el usuario está activo en el perfil
            try:
                if not usuario.perfil.activo:
                    messages.error(request, '❌ Tu cuenta ha sido desactivada. Contacta con un administrador.')
                    UsuarioService.registrar_acceso(
                        usuario=usuario,
                        accion='login',
                        descripcion=f'Intento de login fallido - Cuenta desactivada desde {request.META.get("REMOTE_ADDR", "Unknown")}'
                    )
                    return render(request, 'login.html')
            except PerfilUsuario.DoesNotExist:
                messages.error(request, '⚠️ Error: Perfil de usuario no configurado. Contacta con un administrador.')
                return render(request, 'login.html')
            
            # Asignar grupo de Django si no lo tiene
            try:
                rol_mapa = {
                    'administrador': 'Admin',
                    'vendedor': 'Vendedor',
                    'supervisor': 'Supervisor',
                    'gerente': 'Gerente'
                }
                nombre_grupo = rol_mapa.get(usuario.perfil.rol, 'Vendedor')
                grupo, _ = Group.objects.get_or_create(name=nombre_grupo)
                if not usuario.groups.filter(id=grupo.id).exists():
                    usuario.groups.add(grupo)
            except Exception as e:
                print(f"Advertencia: No se pudo asignar grupo al usuario {usuario.username}: {e}")
            
            login(request, usuario)
            UsuarioService.registrar_acceso(
                usuario=usuario,
                accion='login',
                descripcion=f'Login desde {request.META.get("REMOTE_ADDR", "Unknown")}'
            )
            messages.success(request, f'¡Bienvenido {usuario.first_name or usuario.username}!')
            
            return redirect('index')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'login.html')


@login_required
def logout_view(request):
    """Logout del usuario - muestra página de despedida"""
    username = request.user.username
    UsuarioService.registrar_acceso(
        usuario=request.user,
        accion='logout',
        descripcion='Logout'
    )
    logout(request)
    
    # Consumir (limpiar) todos los mensajes para que no aparezcan después
    storage = messages.get_messages(request)
    for _ in storage:
        pass
    
    # Renderizar página de despedida elegante
    return render(request, 'usuarios/logout.html', {
        'user': type('obj', (object,), {'username': username})()
    })


@login_required
def perfil_usuario(request):
    """Página del perfil del usuario"""
    try:
        perfil = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        # Si no existe perfil, crear uno
        perfil = PerfilUsuario.objects.create(usuario=request.user)
    
    context = {
        'usuario': request.user,
        'perfil': perfil,
    }
    return render(request, 'usuarios/perfil.html', context)


@login_required
def cambiar_contrasena(request):
    """Cambiar contraseña del usuario"""
    if request.method == 'POST':
        contrasena_actual = request.POST.get('contrasena_actual')
        contrasena_nueva = request.POST.get('contrasena_nueva')
        contrasena_confirma = request.POST.get('contrasena_confirma')
        
        # Validar contraseña actual
        usuario = authenticate(request, username=request.user.username, password=contrasena_actual)
        
        if usuario is None:
            messages.error(request, 'Contraseña actual incorrecta')
        elif contrasena_nueva != contrasena_confirma:
            messages.error(request, 'Las contraseñas no coinciden')
        elif len(contrasena_nueva) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
        else:
            request.user.set_password(contrasena_nueva)
            request.user.save()
            messages.success(request, 'Contraseña cambiada correctamente')
            return redirect('perfil_usuario')
    
    return render(request, 'usuarios/cambiar_contrasena.html')


@login_required
@require_http_methods(["GET"])
def bitacora(request):
    """Bitácora de accesos del usuario actual"""
    bitacora = UsuarioService.obtener_bitacora(usuario_id=request.user.id).order_by('-created_at')[:100]
    
    context = {
        'bitacora': bitacora,
    }
    return render(request, 'usuarios/bitacora.html', context)


@login_required
def agregar_vendedor(request):
    """Agregar un nuevo vendedor (administrador o supervisor)"""
    # Verificar permisos
    if not es_admin_o_supervisor(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('index')
    
    vendedores = User.objects.filter(perfil__rol='vendedor').select_related('perfil')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        rol = request.POST.get('rol', 'vendedor')
        
        # Validaciones
        if not username:
            messages.error(request, 'El nombre de usuario es requerido')
        elif not password or len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
        elif rol not in ['vendedor', 'supervisor']:
            messages.error(request, 'Rol inválido')
        elif User.objects.filter(username=username).exists():
            messages.error(request, f'El usuario "{username}" ya existe')
        else:
            try:
                # Crear usuario
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=nombre,
                    last_name=apellido
                )
                
                # Crear perfil
                PerfilUsuario.objects.create(
                    usuario=user,
                    rol=rol,
                    activo=True
                )
                
                # Asignar grupo de Django basado en el rol
                nombre_grupo = 'Vendedor' if rol == 'vendedor' else 'Supervisor' if rol == 'supervisor' else 'Admin'
                grupo, _ = Group.objects.get_or_create(name=nombre_grupo)
                user.groups.add(grupo)
                
                # Registrar en bitácora
                UsuarioService.registrar_acceso(
                    usuario=request.user,
                    accion='crear',
                    descripcion=f'Nuevo {rol}: {username}'
                )
                
                messages.success(request, f'✓ ¡Vendedor "{nombre or username}" creado exitosamente!')
                return redirect('usuarios:agregar_vendedor')
            
            except Exception as e:
                messages.error(request, f'Error al crear vendedor: {str(e)}')
    
    context = {
        'vendedores': vendedores,
    }
    return render(request, 'usuarios/agregar_vendedor.html', context)


@login_required
@require_http_methods(["POST"])
@csrf_protect
def eliminar_vendedor(request, vendedor_id):
    """Eliminar un vendedor (administrador o supervisor)"""
    if not es_admin_o_supervisor(request.user):
        return JsonResponse({'exito': False, 'error': 'Sin permisos'}, status=403)
    
    try:
        user = User.objects.get(id=vendedor_id)
        username = user.username
        
        # No permitir eliminar al usuario actual
        if user.id == request.user.id:
            return JsonResponse({'exito': False, 'error': 'No puedes eliminar tu propia cuenta'}, status=400)
        
        # Registrar antes de eliminar
        UsuarioService.registrar_acceso(
            usuario=request.user,
            accion='eliminar',
            descripcion=f'Eliminado usuario: {username}'
        )
        
        user.delete()
        
        return JsonResponse({'exito': True, 'mensaje': f'Vendedor "{username}" eliminado'})
    
    except User.DoesNotExist:
        return JsonResponse({'exito': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'exito': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_protect
def cambiar_estado_vendedor(request, vendedor_id):
    """Activar/desactivar vendedor (administrador o supervisor)"""
    if not es_admin_o_supervisor(request.user):
        return JsonResponse({'exito': False, 'error': 'Sin permisos'}, status=403)
    
    try:
        perfil = PerfilUsuario.objects.get(usuario_id=vendedor_id)
        perfil.activo = not perfil.activo
        perfil.save()
        
        estado = 'activado' if perfil.activo else 'desactivado'
        
        UsuarioService.registrar_acceso(
            usuario=request.user,
            accion='editar',
            descripcion=f'Vendedor {estado}: {perfil.usuario.username}'
        )
        
        return JsonResponse({
            'exito': True,
            'activo': perfil.activo,
            'mensaje': f'Vendedor {estado}'
        })
    
    except PerfilUsuario.DoesNotExist:
        return JsonResponse({'exito': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'exito': False, 'error': str(e)}, status=500)
