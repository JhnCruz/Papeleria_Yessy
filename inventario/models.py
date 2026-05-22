from django.db import models
from django.contrib.auth.models import User
from productos.models import Producto


class MovimientoInventario(models.Model):
    """Registro de movimientos en el inventario"""
    TIPO_MOVIMIENTO_CHOICES = [
        ('venta', 'Venta'),
        ('ajuste', 'Ajuste Manual'),
        ('cancelacion', 'Cancelación de Venta'),
        ('entrada', 'Entrada de Stock'),
        ('devolucion', 'Devolución'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='movimientos')
    cantidad = models.IntegerField()  # Puede ser negativo
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO_CHOICES)
    referencia = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="ID de venta o ajuste relacionado"
    )
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Movimientos de Inventario"
        indexes = [
            models.Index(fields=['producto']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} - {self.producto.nombre} ({self.cantidad})"
