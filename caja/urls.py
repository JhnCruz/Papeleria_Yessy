from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    path('', views.corte_caja, name='corte'),
    path('realizar/', views.realizar_corte, name='realizar'),
    path('historial/', views.historial_cortes, name='historial'),
    path('detalle/<int:corte_id>/', views.detalle_corte, name='detalle'),
    path('resumen-horas/', views.resumen_hora_x_hora, name='resumen_horas'),
]
