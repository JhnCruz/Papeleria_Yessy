from django.contrib import admin
from .models import MovimientoInventario


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'cantidad', 'tipo_movimiento', 'usuario', 'created_at')
    search_fields = ('producto__nombre', 'producto__sku')
    list_filter = ('tipo_movimiento', 'created_at')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('producto', 'cantidad', 'tipo_movimiento')
        }),
        ('Detalles', {
            'fields': ('referencia', 'descripcion', 'usuario', 'created_at')
        }),
    )
