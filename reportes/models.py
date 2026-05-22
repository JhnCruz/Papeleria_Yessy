from django.db import models


class ConfiguracionReportes(models.Model):
    """Configuración global para reportes"""
    formato_moneda = models.CharField(max_length=5, default='MXN')
    mostrar_detalles_texto = models.BooleanField(default=True)
    margen_ganancias = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Porcentaje de margen para análisis"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de Reportes"
        verbose_name_plural = "Configuración de Reportes"

    def __str__(self):
        return "Configuración de Reportes"
