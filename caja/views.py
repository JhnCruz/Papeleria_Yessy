from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from datetime import date
import json

from .models import CorteCaja
from .services import CajaService
from ventas.services import VentaService
from usuarios.services import UsuarioService


@login_required
def corte_caja(request):
    """Página de corte de caja"""
    hoy = date.today()
    turno_actual = CajaService.obtener_turno_actual()
    
    # Obtener cortes del día (turno 1 y turno 2, si existen)
    corte_turno1 = CajaService.obtener_corte_del_dia(hoy, turno=1)
    corte_turno2 = CajaService.obtener_corte_del_dia(hoy, turno=2)
    
    totales = VentaService.calcular_totales_del_dia(hoy)
    cortes_anteriores = CajaService.obtener_cortes().exclude(fecha_corte=hoy)[:10]
    
    context = {
        'hoy': hoy,
        'turno_actual': turno_actual,
        'corte_turno1': corte_turno1,
        'corte_turno2': corte_turno2,
        'totales': totales,
        'cortes': cortes_anteriores,
    }
    return render(request, 'corte_caja.html', context)


@login_required
@require_http_methods(["POST"])
def realizar_corte(request):
    """Realiza el corte de caja"""
    try:
        data = json.loads(request.body)
        notas = data.get('notas', '')
        
        exito, resultado = CajaService.realizar_corte(
            usuario=request.user,
            notas=notas
        )
        
        if exito:
            UsuarioService.registrar_acceso(
                usuario=request.user,
                accion='corte',
                descripcion=f'Corte de caja - Total: ${resultado.total_ventas}'
            )
            
            return JsonResponse({
                'exito': True,
                'corte_id': resultado.id,
                'turno': resultado.turno,
                'total_ventas': float(resultado.total_ventas),
                'total_efectivo': float(resultado.total_efectivo),
                'total_transferencias': float(resultado.total_transferencias),
                'mensaje': 'Corte realizado exitosamente'
            })
        else:
            return JsonResponse({
                'exito': False,
                'error': resultado
            }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'exito': False,
            'error': f'Error realizando corte: {str(e)}'
        }, status=500)


@login_required
def historial_cortes(request):
    """Historial de cortes de caja"""
    cortes = CajaService.obtener_cortes().order_by('-fecha_corte')
    
    context = {
        'cortes': cortes,
    }
    return render(request, 'caja/historial.html', context)


@login_required
def detalle_corte(request, corte_id):
    """Detalle de un corte específico"""
    corte = CorteCaja.objects.get(id=corte_id)
    resumen = CajaService.obtener_resumen_caja(corte.fecha_corte)
    
    context = {
        'corte': corte,
        'resumen': resumen,
    }
    return render(request, 'caja/detalle.html', context)


@login_required
def resumen_hora_x_hora(request):
    """Reporte de ventas - Resumen hora x hora"""
    from datetime import datetime, timedelta
    from ventas.models import Venta
    from decimal import Decimal
    from django.db.models import Sum, Count
    
    # Obtener fecha del parámetro GET o usar hoy
    fecha_str = request.GET.get('fecha', str(date.today()))
    try:
        fecha = date.fromisoformat(fecha_str)
    except:
        fecha = date.today()
    
    # Obtener todas las ventas del día
    ventas_del_dia = Venta.objects.filter(
        fecha_venta__date=fecha,
        estado='completada'
    ).order_by('fecha_venta')
    
    # Agrupar por hora
    resumen_por_hora = {}
    for hora in range(0, 24):
        resumen_por_hora[hora] = {
            'hora': f"{hora:02d}:00",
            'total_ventas': Decimal('0.00'),
            'total_efectivo': Decimal('0.00'),
            'total_transferencias': Decimal('0.00'),
            'cantidad_transacciones': 0,
        }
    
    # Procesar ventas
    for venta in ventas_del_dia:
        hora = venta.fecha_venta.hour
        resumen_por_hora[hora]['total_ventas'] += venta.total
        
        if venta.metodo_pago == 'efectivo':
            resumen_por_hora[hora]['total_efectivo'] += venta.total
        else:
            resumen_por_hora[hora]['total_transferencias'] += venta.total
        
        resumen_por_hora[hora]['cantidad_transacciones'] += 1
    
    # Conver a lista y eliminar horas vacías
    resumen_lista = []
    total_general = Decimal('0.00')
    total_efectivo_general = Decimal('0.00')
    total_transferencias_general = Decimal('0.00')
    
    for hora, datos in resumen_por_hora.items():
        if datos['cantidad_transacciones'] > 0 or datos['total_ventas'] > 0:
            resumen_lista.append({
                'hora': datos['hora'],
                'total_ventas': float(datos['total_ventas']),
                'total_efectivo': float(datos['total_efectivo']),
                'total_transferencias': float(datos['total_transferencias']),
                'cantidad_transacciones': datos['cantidad_transacciones'],
            })
            total_general += datos['total_ventas']
            total_efectivo_general += datos['total_efectivo']
            total_transferencias_general += datos['total_transferencias']
    
    context = {
        'fecha': fecha,
        'resumen': resumen_lista,
        'total_general': float(total_general),
        'total_efectivo': float(total_efectivo_general),
        'total_transferencias': float(total_transferencias_general),
        'todas_las_horas': [f"{i:02d}:00" for i in range(24)],
    }
    return render(request, 'caja/resumen_horas.html', context)
