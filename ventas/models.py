from django.db import models
from django.contrib.auth.models import User
from productos.models import Producto
from decimal import Decimal


class Venta(models.Model):
    """Modelo de Venta"""
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    fecha_venta = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ventas')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_venta']
        indexes = [
            models.Index(fields=['-fecha_venta']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f"Venta #{self.id} - {self.fecha_venta.strftime('%d/%m/%Y %H:%M')}"

    @property
    def cantidad_articulos(self):
        """Retorna la cantidad total de artículos en la venta"""
        return sum(detalle.cantidad for detalle in self.detalles.all())


class DetalleVenta(models.Model):
    """Detalle de cada artículo en una venta"""
    TIPO_VENTA_CHOICES = [
        ('pieza', 'Por Pieza'),
        ('paquete', 'Por Paquete'),
    ]
    
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    tipo_venta = models.CharField(max_length=20, choices=TIPO_VENTA_CHOICES)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Detalles de Venta"

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

    def save(self, *args, **kwargs):
        """Calcula automáticamente el subtotal"""
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)


class Devolucion(models.Model):
    """Modelo de Devolución de productos con auditoría completa"""
    MOTIVO_CHOICES = [
        ('defectuoso', 'Producto Defectuoso'),
        ('cambio_idea', 'Cambio de Idea'),
        ('producto_incorrecto', 'Producto Incorrecto'),
        ('dañado', 'Producto Dañado'),
        ('no_solicitado', 'No Solicitado'),
        ('otro', 'Otro'),
    ]
    
    TIPO_REEMBOLSO_CHOICES = [
        ('efectivo', 'Reembolso en Efectivo'),
        ('transferencia', 'Devolución a Transferencia'),
        ('credito', 'Crédito para Próximas Compras'),
    ]
    
    ESTADO_DEVOLUCION_CHOICES = [
        ('pendiente_aprobacion', 'Pendiente de Aprobación'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    
    venta = models.ForeignKey(Venta, on_delete=models.PROTECT, related_name='devoluciones')
    motivo = models.CharField(max_length=20, choices=MOTIVO_CHOICES)
    tipo_reembolso = models.CharField(max_length=20, choices=TIPO_REEMBOLSO_CHOICES)
    total_devuelto = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    notas = models.TextField(blank=True, null=True)
    
    # Usuario que liquidó la devolución
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='devoluciones_procesadas')
    fecha_devolucion = models.DateTimeField(auto_now_add=True)
    
    # Auditoría: Aprobación
    estado = models.CharField(max_length=20, choices=ESTADO_DEVOLUCION_CHOICES, default='pendiente_aprobacion')
    usuario_aprobacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='devoluciones_aprobadas')
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    razon_rechazo = models.TextField(blank=True, null=True, help_text="Razón del rechazo (si aplica)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_devolucion']
        indexes = [
            models.Index(fields=['-fecha_devolucion']),
            models.Index(fields=['venta']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f"Devolución Venta #{self.venta.id} - ${self.total_devuelto} ({self.get_estado_display()})"

    @property
    def cantidad_articulos(self):
        """Retorna la cantidad total de artículos devueltos"""
        return sum(detalle.cantidad for detalle in self.detalles.all())


class DetalleDevolucion(models.Model):
    """Detalle de cada artículo devuelto"""
    devolucion = models.ForeignKey(Devolucion, on_delete=models.CASCADE, related_name='detalles')
    detalle_venta = models.ForeignKey(DetalleVenta, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Detalles de Devolución"

    def __str__(self):
        return f"{self.detalle_venta.producto.nombre} x {self.cantidad}"

    def save(self, *args, **kwargs):
        """Calcula automáticamente el subtotal"""
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
