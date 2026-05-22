from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('', views.pos_venta, name='index'),
    path('crear/', views.crear_venta, name='crear'),
    path('cancelar/', views.cancelar_venta, name='cancelar'),
    path('listar/', views.listar_ventas, name='listar'),
    path('detalle/<int:venta_id>/', views.detalle_venta, name='detalle'),
    path('ticket/<int:venta_id>/', views.ticket_venta, name='ticket'),
    path('resumen/', views.resumen_ventas, name='resumen'),
    path('devolucion/', views.devolucion, name='devolucion'),
    path('buscar_devolucion/', views.buscar_venta_devolucion, name='buscar_devolucion'),
    path('procesar_devolucion/', views.procesar_devolucion_api, name='procesar_devolucion'),
]
