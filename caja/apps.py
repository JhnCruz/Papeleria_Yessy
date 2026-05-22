from django.apps import AppConfig


class CajaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'caja'
    
    def ready(self):
        """Se ejecuta cuando Django está listo"""
        try:
            from .scheduler import iniciar_scheduler
            iniciar_scheduler()
        except Exception as e:
            print(f"Error iniciando scheduler de caja: {e}")
