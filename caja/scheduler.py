"""
Programador de tareas - Corte automático de caja a las 1 PM
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date, datetime
from .services import CajaService
from usuarios.models import User
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def realizar_corte_automatico():
    """Realiza el corte automático del Turno 1 a las 1 PM"""
    try:
        # Obtener usuario de sistema o el primer admin
        usuario_sistema = User.objects.filter(is_superuser=True).first() or User.objects.first()
        
        if not usuario_sistema:
            logger.warning("No hay usuarios en el sistema para realizar corte automático")
            return
        
        # Verificar que no exista corte para hoy (Turno 1)
        corte_existente = CajaService.obtener_corte_del_dia(date.today(), turno=1)
        
        if corte_existente:
            logger.info(f"Corte Turno 1 ya realizado para {date.today()}")
            return
        
        # Realizar corte automático
        exito, resultado = CajaService.realizar_corte(
            usuario=usuario_sistema,
            fecha=date.today(),
            turno=1,
            notas="Corte automático - Turno 1 (1 PM)"
        )
        
        if exito:
            logger.info(f"✅ Corte automático Turno 1 realizado - Total: ${resultado.total_ventas}")
        else:
            logger.warning(f"❌ Error en corte automático: {resultado}")
    
    except Exception as e:
        logger.error(f"Error en corte automático: {str(e)}")


def iniciar_scheduler():
    """Inicia el scheduler con la tarea programada"""
    try:
        # Programar corte a las 1 PM todos los días
        scheduler.add_job(
            realizar_corte_automatico,
            'cron',
            hour=13,  # 1 PM (13:00)
            minute=0,
            id='corte_automatico_turno1',
            name='Corte automático Turno 1',
            replace_existing=True
        )
        
        if not scheduler.running:
            scheduler.start()
            logger.info("✅ Scheduler iniciado - Corte automático programado para las 1 PM")
        else:
            logger.info("Scheduler ya está corriendo")
    
    except Exception as e:
        logger.error(f"Error iniciando scheduler: {str(e)}")


def detener_scheduler():
    """Detiene el scheduler"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler detenido")
    except Exception as e:
        logger.error(f"Error deteniendo scheduler: {str(e)}")
