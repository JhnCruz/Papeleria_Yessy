from django.db import models
from django.core.validators import MinValueValidator


class Categoria(models.Model):
    """Categoría de productos"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """Modelo de Producto con control de inventario"""
    sku = models.CharField(max_length=50, unique=True, help_text="Código de barras")
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    
    # Precios
    precio_pieza = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    precio_paquete = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        null=True,
        blank=True
    )
    cantidad_paquete = models.PositiveIntegerField(
        default=1,
        help_text="Cantidad de piezas por paquete"
    )
    
    # Inventario
    stock_actual = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
    
    # Status
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['categoria']),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.sku})"

    @property
    def bajo_stock(self):
        """Verifica si el producto está bajo stock (comparando con su stock_minimo)"""
        return self.stock_actual < self.stock_minimo

    @property
    def estado_stock(self):
        """Retorna el estado del stock con 3 niveles: sin_stock, urgente, ok"""
        if self.stock_actual == 0:
            return 'sin_stock'
        elif self.stock_actual < self.stock_minimo:
            return 'urgente'
        else:
            return 'ok'

    @property
    def etiqueta_stock(self):
        """Retorna la etiqueta legible del estado del stock"""
        estado_map = {
            'sin_stock': 'Sin Stock',
            'urgente': 'Urgente',
            'ok': 'OK'
        }
        return estado_map.get(self.estado_stock, 'Desconocido')

    @property
    def color_stock(self):
        """Retorna el color CSS para el estado del stock"""
        color_map = {
            'sin_stock': '#ffcccc',  # Rojo
            'urgente': '#ffe0b2',     # Naranja
            'ok': '#ccf2dd'           # Verde
        }
        return color_map.get(self.estado_stock, '#ffffff')
