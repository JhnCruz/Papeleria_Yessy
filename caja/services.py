"""
Servicios de Caja - Capa de Dominio
"""
from django.db import transaction
from datetime import date, datetime
from .models import CorteCaja
from ventas.services import VentaService


class CajaService:
    """Servicio para operaciones de caja"""
    
    @staticmethod
    def obtener_turno_actual():
        """Obtiene el turno actual basado en la hora"""
        hora_actual = datetime.now().hour
        # Turno 1: antes de las 5 PM (17:00)
        # Turno 2: desde las 5 PM en adelante
        return 1 if hora_actual < 17 else 2
    
    @staticmethod
    def obtener_corte_del_dia(fecha=None, turno=None):
        """Obtiene el corte de caja del día especificado (y opcionalmente por turno)"""
        if fecha is None:
            fecha = date.today()
        
        try:
            if turno is not None:
                return CorteCaja.objects.get(fecha_corte=fecha, turno=turno)
            else:
                # Obtener el último corte del día
                return CorteCaja.objects.filter(fecha_corte=fecha).latest('turno')
        except CorteCaja.DoesNotExist:
            return None
    
    @staticmethod
    def contar_cortes_del_dia(fecha=None):
        """Cuenta cuántos cortes se han realizado en el día"""
        if fecha is None:
            fecha = date.today()
        
        return CorteCaja.objects.filter(fecha_corte=fecha).count()
    
    @staticmethod
    @transaction.atomic
    def realizar_corte(usuario, fecha=None, notas='', turno=None):
        """Realiza un corte de caja"""
        if fecha is None:
            fecha = date.today()
        
        if turno is None:
            turno = CajaService.obtener_turno_actual()
        
        # Validar que el turno sea válido
        if turno not in [1, 2]:
            return False, "Turno inválido (debe ser 1 o 2)"
        
        # Verificar si ya existe corte para este turno
        corte_existente = CajaService.obtener_corte_del_dia(fecha, turno)
        if corte_existente:
            return False, f"Ya existe un corte para el {corte_existente.get_turno_display()}"
        
        # Verificar que no haya más de 2 cortes en el día
        cortes_hoy = CajaService.contar_cortes_del_dia(fecha)
        if cortes_hoy >= 2:
            return False, "Ya se han realizado los 2 cortes permitidos para hoy"
        
        try:
            # Calcular totales
            totales = VentaService.calcular_totales_del_dia(fecha)
            
            # Crear corte
            corte = CorteCaja.objects.create(
                fecha_corte=fecha,
                turno=turno,
                total_ventas=totales['total'],
                total_efectivo=totales['efectivo'],
                total_transferencias=totales['transferencias'],
                usuario=usuario,
                notas=notas
            )
            
            return True, corte
        
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def obtener_cortes(fecha_inicio=None, fecha_fin=None):
        """Obtiene cortes en un rango de fechas"""
        queryset = CorteCaja.objects.all()
        
        if fecha_inicio:
            queryset = queryset.filter(fecha_corte__gte=fecha_inicio)
        
        if fecha_fin:
            queryset = queryset.filter(fecha_corte__lte=fecha_fin)
        
        return queryset.order_by('-fecha_corte', '-turno')
    
    @staticmethod
    def obtener_resumen_caja(fecha, turno=None):
        """Obtiene un resumen completo de la caja para una fecha (y opcionalmente un turno)"""
        corte = CajaService.obtener_corte_del_dia(fecha, turno)
        
        if not corte:
            return None
        
        return {
            'fecha': corte.fecha_corte,
            'turno': corte.turno,
            'turno_display': corte.get_turno_display(),
            'total_ventas': corte.total_ventas,
            'total_efectivo': corte.total_efectivo,
            'total_transferencias': corte.total_transferencias,
            'diferencia': corte.total_ventas - (corte.total_efectivo + corte.total_transferencias),
            'usuario': corte.usuario.get_full_name() if corte.usuario else 'N/A',
            'notas': corte.notas
        }
