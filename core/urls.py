"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from ventas.views import index_inicio
from productos.views import admin_productos

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Usuarios (auth)
    path('usuarios/', include('usuarios.urls')),
    
    # Apps
    path('productos/', include('productos.urls')),
    path('ventas/', include('ventas.urls')),
    path('caja/', include('caja.urls')),
    path('reportes/', include('reportes.urls')),
    
    # Página de inicio principal
    path('', index_inicio, name='index'),
    
    # Panel de administrador
    path('admin-panel/', admin_productos, name='admin_productos'),
]
