from django.contrib import admin
from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activa', 'created_at')
    search_fields = ('nombre',)
    list_filter = ('activa', 'created_at')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('sku', 'nombre', 'categoria', 'precio_pieza', 'stock_actual', 'activo')
    search_fields = ('sku', 'nombre')
    list_filter = ('categoria', 'activo', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Información General', {
            'fields': ('sku', 'nombre', 'descripcion', 'categoria')
        }),
        ('Precios', {
            'fields': ('precio_pieza', 'precio_paquete', 'cantidad_paquete')
        }),
        ('Inventario', {
            'fields': ('stock_actual', 'stock_minimo')
        }),
        ('Estado', {
            'fields': ('activo', 'created_at', 'updated_at')
        }),
    )
