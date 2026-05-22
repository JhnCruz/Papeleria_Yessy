from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('ventas/', views.reporte_ventas, name='ventas'),
    path('productos-vendidos/', views.reporte_productos_vendidos, name='productos_vendidos'),
    path('inventario/', views.reporte_inventario, name='inventario'),
    path('stock-bajo/', views.reporte_stock_bajo, name='stock_bajo'),
    path('movimientos/', views.reporte_movimientos_inventario, name='movimientos'),
    path('resumen/', views.resumen, name='resumen'),
    
    # Exportación de reportes
    path('exportar/ventas/', views.exportar_reporte_ventas, name='exportar_ventas'),
    path('exportar/productos-vendidos/', views.exportar_reporte_productos_vendidos, name='exportar_productos_vendidos'),
    path('exportar/inventario/', views.exportar_reporte_inventario, name='exportar_inventario'),
]
