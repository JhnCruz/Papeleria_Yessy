from django.contrib import admin
from .models import PerfilUsuario, BitacoraAcceso
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .services import UsuarioService


class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    readonly_fields = ('created_at', 'updated_at', 'ultimo_acceso')
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('rol', 'telefono')
        }),
        ('Estado', {
            'fields': ('activo',),
            'description': 'Marca como activo si el empleado puede acceder al sistema'
        }),
        ('Auditoría', {
            'fields': ('ultimo_acceso', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class UsuarioAdmin(BaseUserAdmin):
    inlines = [PerfilUsuarioInline]
    list_display = ('username', 'get_nombre_completo', 'get_rol', 'get_estado', 'email', 'get_ultimo_acceso')
    list_filter = ('perfil__rol', 'perfil__activo', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    actions = ['activar_empleados', 'desactivar_empleados']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'email'),
        }),
        ('Permisos', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )
    
    def get_nombre_completo(self, obj):
        """Muestra nombre completo del usuario"""
        nombre = obj.get_full_name() or obj.username
        return nombre
    get_nombre_completo.short_description = 'Nombre Completo'
    
    def get_rol(self, obj):
        """Muestra el rol del usuario con color"""
        try:
            rol = obj.perfil.get_rol_display()
            perfil = obj.perfil
            
            if perfil.rol == 'administrador':
                color = '#dc3545'  # Rojo
                icono = '👑'
            elif perfil.rol == 'supervisor':
                color = '#fd7e14'  # Naranja
                icono = '🔑'
            else:
                color = '#28a745'  # Verde
                icono = '👤'
            
            return format_html(
                '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold; white-space: nowrap;">{} {}</span>',
                color, icono, rol
            )
        except:
            return format_html('<span style="color: gray;">Sin rol</span>')
    get_rol.short_description = 'Rol'
    
    def get_estado(self, obj):
        """Muestra el estado del empleado (activo/inactivo)"""
        try:
            if obj.perfil.activo:
                return format_html(
                    '<span style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">✓ Activo</span>'
                )
            else:
                return format_html(
                    '<span style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">⊘ Inactivo</span>'
                )
        except:
            return format_html('<span style="color: gray;">Sin perfil</span>')
    get_estado.short_description = 'Estado'
    
    def get_ultimo_acceso(self, obj):
        """Muestra el último acceso del usuario"""
        try:
            if obj.perfil.ultimo_acceso:
                return obj.perfil.ultimo_acceso.strftime('%d/%m/%Y %H:%M')
            return 'Nunca'
        except:
            return 'N/A'
    get_ultimo_acceso.short_description = 'Último Acceso'
    
    def activar_empleados(self, request, queryset):
        """Acción de administración para activar empleados"""
        count = 0
        for usuario in queryset:
            try:
                if usuario.perfil.activo is False:
                    usuario.perfil.activo = True
                    usuario.perfil.save()
                    
                    # Registrar en bitácora
                    UsuarioService.registrar_acceso(
                        usuario=request.user,
                        accion='editar',
                        descripcion=f'Empleado activado: {usuario.username}'
                    )
                    count += 1
            except PerfilUsuario.DoesNotExist:
                pass
        
        self.message_user(
            request,
            f'✓ {count} empleado(s) activado(s) correctamente.'
        )
    activar_empleados.short_description = '✓ Activar empleados seleccionados'
    
    def desactivar_empleados(self, request, queryset):
        """Acción de administración para desactivar empleados"""
        # No permitir desactivar al usuario actual
        queryset = queryset.exclude(id=request.user.id)
        
        count = 0
        for usuario in queryset:
            try:
                if usuario.perfil.activo is True:
                    usuario.perfil.activo = False
                    usuario.perfil.save()
                    
                    # Registrar en bitácora
                    UsuarioService.registrar_acceso(
                        usuario=request.user,
                        accion='editar',
                        descripcion=f'Empleado desactivado: {usuario.username}'
                    )
                    count += 1
            except PerfilUsuario.DoesNotExist:
                pass
        
        self.message_user(
            request,
            f'⊘ {count} empleado(s) desactivado(s) correctamente.'
        )
    desactivar_empleados.short_description = '⊘ Desactivar empleados seleccionados'


# Re-register el admin para User
admin.site.unregister(User)
admin.site.register(User, UsuarioAdmin)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    """Admin para gestionar directamente perfiles de usuarios"""
    list_display = ('get_usuario', 'rol', 'get_estado', 'get_ultimo_acceso', 'created_at')
    list_filter = ('rol', 'activo', 'created_at')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')
    actions = ['activar_perfiles', 'desactivar_perfiles']
    
    readonly_fields = ('created_at', 'updated_at', 'ultimo_acceso')
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario',)
        }),
        ('Configuración', {
            'fields': ('rol', 'telefono', 'activo')
        }),
        ('Auditoría', {
            'fields': ('ultimo_acceso', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_usuario(self, obj):
        """Muestra el usuario con su nombre completo"""
        nombre = obj.usuario.get_full_name() or obj.usuario.username
        return f'{nombre} (@{obj.usuario.username})'
    get_usuario.short_description = 'Usuario'
    
    def get_estado(self, obj):
        """Muestra el estado del perfil"""
        if obj.activo:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">✓ Activo</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">⊘ Inactivo</span>'
            )
    get_estado.short_description = 'Estado'
    
    def get_ultimo_acceso(self, obj):
        """Muestra el último acceso"""
        if obj.ultimo_acceso:
            return obj.ultimo_acceso.strftime('%d/%m/%Y %H:%M')
        return 'Nunca'
    get_ultimo_acceso.short_description = 'Último Acceso'
    
    def activar_perfiles(self, request, queryset):
        """Activar perfiles seleccionados"""
        count = queryset.filter(activo=False).update(activo=True)
        
        # Registrar en bitácora
        for perfil in queryset:
            UsuarioService.registrar_acceso(
                usuario=request.user,
                accion='editar',
                descripcion=f'Perfil activado: {perfil.usuario.username}'
            )
        
        self.message_user(
            request,
            f'✓ {count} perfil(es) activado(s) correctamente.'
        )
    activar_perfiles.short_description = '✓ Activar perfiles seleccionados'
    
    def desactivar_perfiles(self, request, queryset):
        """Desactivar perfiles seleccionados"""
        # No permitir desactivar el perfil del usuario actual
        queryset = queryset.exclude(usuario_id=request.user.id)
        count = queryset.filter(activo=True).update(activo=False)
        
        # Registrar en bitácora
        for perfil in queryset:
            UsuarioService.registrar_acceso(
                usuario=request.user,
                accion='editar',
                descripcion=f'Perfil desactivado: {perfil.usuario.username}'
            )
        
        self.message_user(
            request,
            f'⊘ {count} perfil(es) desactivado(s) correctamente.'
        )
    desactivar_perfiles.short_description = '⊘ Desactivar perfiles seleccionados'


@admin.register(BitacoraAcceso)
class BitacoraAccesoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'accion', 'created_at', 'ip_address', 'get_descripcion_corta')
    search_fields = ('usuario__username', 'descripcion')
    list_filter = ('accion', 'created_at', 'usuario')
    readonly_fields = ('created_at', 'usuario', 'accion', 'descripcion', 'ip_address')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información', {
            'fields': ('usuario', 'accion', 'ip_address')
        }),
        ('Detalles', {
            'fields': ('descripcion', 'created_at')
        }),
    )
    
    def has_add_permission(self, request):
        """No permitir agregar bitácoras manualmente"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo superuser puede eliminar bitácoras"""
        return request.user.is_superuser
    
    def get_descripcion_corta(self, obj):
        """Muestra una versión corta de la descripción"""
        if obj.descripcion:
            return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
        return 'Sin descripción'
    get_descripcion_corta.short_description = 'Descripción'
