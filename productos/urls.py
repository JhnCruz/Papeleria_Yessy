from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    path('', views.listar_productos, name='listar'),
    path('inventario-general/', views.inventario_general, name='inventario_general'),
    path('api/listar/', views.api_listar_productos, name='api_listar'),
    path('buscar-sku/', views.buscar_producto_sku, name='buscar_sku'),
    path('buscar-nombre/', views.buscar_producto_nombre, name='buscar_nombre'),
    path('validar-stock/', views.validar_stock, name='validar_stock'),
    path('bajo-stock/', views.productos_bajo_stock, name='bajo_stock'),
    path('agregar-nuevo/', views.agregar_nuevo, name='agregar_nuevo'),
    path('agregar-stock/', views.agregar_stock, name='agregar_stock'),
    path('editar-precios/', views.editar_precios, name='editar_precios'),
    path('crear/', views.crear_producto, name='crear'),
    path('crear-categoria/', views.crear_categoria, name='crear_categoria'),
    
    # Gestión de Productos
    path('gestionar/', views.gestionar_productos, name='gestionar_productos'),
    path('<int:producto_id>/editar/', views.editar_producto, name='editar_producto'),
    path('<int:producto_id>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    
    # Admin URLs
    path('admin/', views.admin_productos, name='admin_productos'),
    path('admin/<int:producto_id>/editar/', views.admin_editar_producto, name='admin_editar'),
    path('admin/crear/', views.admin_crear_producto, name='admin_crear'),
    path('admin/<int:producto_id>/eliminar/', views.admin_eliminar_producto, name='admin_eliminar'),
]
