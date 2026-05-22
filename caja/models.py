from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class CorteCaja(models.Model):
    """Corte de caja diario - permite 2 cortes por día (turno 1 y 2)"""
    TURNO_CHOICES = [
        (1, 'Turno 1 (Mediodía - 1 PM)'),
        (2, 'Turno 2 (Noche - 9 PM)'),
    ]
    
    ESTADO_CUADRATURA_CHOICES = [
        ('cuadrado', 'Cuadrado'),
        ('diferencia', 'Con Diferencia'),
        ('pendiente', 'Pendiente Validación'),
    ]
    
    fecha_corte = models.DateField(auto_now_add=True)
    turno = models.IntegerField(choices=TURNO_CHOICES, default=1)
    
    # Totales esperados (del sistema)
    total_ventas = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_efectivo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_transferencias = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Montos reales ingresados
    monto_efectivo_ingresado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monto_transferencias_ingresado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Validación de cuadratura
    estado_cuadratura = models.CharField(max_length=20, choices=ESTADO_CUADRATURA_CHOICES, default='pendiente')
    diferencia_efectivo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    notas_discrepancia = models.TextField(blank=True, null=True, help_text="Explicar discrepancias encontradas")
    
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notas = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_corte', '-turno']
        verbose_name = "Corte de caja"
        verbose_name_plural = "Cortes de caja"
        unique_together = ['fecha_corte', 'turno']  # Un corte por turno por día
    
    def calcular_diferencia(self):
        """Calcula la diferencia entre lo esperado y lo ingresado"""
        if self.monto_efectivo_ingresado is not None:
            self.diferencia_efectivo = self.total_efectivo - self.monto_efectivo_ingresado
            
            # Determinar estado
            if abs(self.diferencia_efectivo) < Decimal('0.01'):  # 1 centavo de tolerancia
                self.estado_cuadratura = 'cuadrado'
            else:
                self.estado_cuadratura = 'diferencia'
    
    def obtener_estado_display_color(self):
        """Retorna color para el estado de cuadratura"""
        if self.estado_cuadratura == 'cuadrado':
            return 'success'  # Verde
        elif self.estado_cuadratura == 'diferencia':
            return 'warning'  # Amarillo/Naranja
        else:
            return 'info'  # Azul

    def __str__(self):
        return f"Corte {self.get_turno_display()} - {self.fecha_corte.strftime('%d/%m/%Y')} ({self.get_estado_cuadratura_display()})"
