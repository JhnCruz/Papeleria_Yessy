from django.contrib import admin
from .models import CorteCaja


@admin.register(CorteCaja)
class CorteCajaAdmin(admin.ModelAdmin):
    list_display = ('fecha_corte', 'total_ventas', 'total_efectivo', 'total_transferencias', 'usuario')
    search_fields = ('fecha_corte', 'usuario__username')
    list_filter = ('fecha_corte',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Fecha', {
            'fields': ('fecha_corte',)
        }),
        ('Totales', {
            'fields': ('total_ventas', 'total_efectivo', 'total_transferencias')
        }),
        ('Información', {
            'fields': ('usuario', 'notas')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
