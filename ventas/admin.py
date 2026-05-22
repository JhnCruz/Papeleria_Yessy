from django.contrib import admin
from .models import Venta, DetalleVenta, Devolucion, DetalleDevolucion


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ('subtotal', 'created_at')


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_venta', 'total', 'metodo_pago', 'estado', 'usuario')
    search_fields = ('id', 'usuario__username')
    list_filter = ('estado', 'metodo_pago', 'fecha_venta')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [DetalleVentaInline]
    fieldsets = (
        ('Información General', {
            'fields': ('fecha_venta', 'usuario', 'estado')
        }),
        ('Pago', {
            'fields': ('metodo_pago', 'total')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'producto', 'cantidad', 'tipo_venta', 'precio_unitario', 'subtotal')
    readonly_fields = ('subtotal', 'created_at')
    list_filter = ('tipo_venta', 'venta__estado')


class DetalleDevolucionInline(admin.TabularInline):
    model = DetalleDevolucion
    extra = 0
    readonly_fields = ('subtotal', 'created_at')


@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display = ('id', 'venta', 'total_devuelto', 'estado', 'usuario', 'fecha_devolucion')
    search_fields = ('id', 'venta__id', 'usuario__username', 'usuario_aprobacion__username')
    list_filter = ('estado', 'motivo', 'tipo_reembolso', 'fecha_devolucion')
    readonly_fields = ('created_at', 'updated_at', 'fecha_devolucion')
    inlines = [DetalleDevolucionInline]
    
    fieldsets = (
        ('Información de Devolución', {
            'fields': ('venta', 'total_devuelto', 'motivo', 'tipo_reembolso', 'notas')
        }),
        ('Auditoría - Liquidación', {
            'fields': ('usuario', 'fecha_devolucion'),
            'classes': ('collapse',)
        }),
        ('Auditoría - Aprobación', {
            'fields': ('estado', 'usuario_aprobacion', 'fecha_aprobacion', 'razon_rechazo'),
            'classes': ('collapse',),
            'description': 'Seguimiento de aprobación y rechazo de devoluciones'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Permitir editar estado y aprobación solo a gerentes/admin"""
        readonly = list(self.readonly_fields)
        if obj and obj.estado != 'pendiente_aprobacion':
            # Una vez aprobada o rechazada, no cambiar
            readonly.extend(['estado', 'usuario_aprobacion', 'fecha_aprobacion', 'razon_rechazo'])
        return readonly
