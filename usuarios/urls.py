from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('cambiar-contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),
    path('bitacora/', views.bitacora, name='bitacora'),
    path('agregar-vendedor/', views.agregar_vendedor, name='agregar_vendedor'),
    path('eliminar-vendedor/<int:vendedor_id>/', views.eliminar_vendedor, name='eliminar_vendedor'),
    path('cambiar-estado-vendedor/<int:vendedor_id>/', views.cambiar_estado_vendedor, name='cambiar_estado_vendedor'),
]
