from django.db import models
from django.contrib.auth.models import User


class PerfilUsuario(models.Model):
    """Perfil extendido de usuario"""
    ROL_CHOICES = [
        ('vendedor', 'Vendedor'),
        ('supervisor', 'Supervisor'),
        ('administrador', 'Administrador'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='vendedor')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    activo = models.BooleanField(default=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} ({self.get_rol_display()})"


class BitacoraAcceso(models.Model):
    """Registro de acceso de usuarios"""
    ACCION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('crear', 'Crear'),
        ('editar', 'Editar'),
        ('eliminar', 'Eliminar'),
        ('venta', 'Venta Completada'),
        ('corte', 'Corte de Caja'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES)
    descripcion = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Bitácora de Acceso"
        verbose_name_plural = "Bitácoras de Acceso"
        indexes = [
            models.Index(fields=['usuario', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.usuario} - {self.get_accion_display()} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
