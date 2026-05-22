from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from datetime import date
import json
from decimal import Decimal

from .models import Venta, DetalleVenta
from .services import VentaService
from productos.models import Producto
from usuarios.services import UsuarioService
from usuarios.permisos import requiere_grupo


def index_inicio(request):
    """Página principal de inicio"""
    # Si no está autenticado, redirigir a login
    if not request.user.is_authenticated:
        return redirect('usuarios:login')
    
    # Obtener resumen del día
    from reportes.services import ReporteService
    from django.db.models import F
    resumen = ReporteService.resumen_diario(date.today())
    
    # Obtener productos con stock bajo (donde stock_actual <= stock_minimo)
    productos_bajo_stock = Producto.objects.filter(activo=True, stock_actual__lte=F('stock_minimo')).order_by('stock_actual')
    
    context = {
        'resumen': resumen,
        'productos_bajo_stock': productos_bajo_stock,
        'hay_stock_bajo': productos_bajo_stock.exists(),
    }
    return render(request, 'index.html', context)


@requiere_grupo('Vendedor', 'Gerente', 'Admin')
@login_required
def pos_venta(request):
    """Interfaz de POS - Crear venta"""
    context = {
        'usuario': request.user,
    }
    return render(request, 'venta.html', context)


@csrf_exempt
@requiere_grupo('Vendedor', 'Gerente', 'Admin')
@login_required
@require_http_methods(["POST"])
def crear_venta(request):
    """Crea una nueva venta"""
    try:
        data = json.loads(request.body)
        
        metodo_pago = data.get('metodo_pago')
        detalles = data.get('detalles', [])
        
        if not metodo_pago or not detalles:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        # Validar método de pago
        if metodo_pago not in ['efectivo', 'transferencia']:
            return JsonResponse({'error': 'Método de pago inválido'}, status=400)
        
        # Procesar detalles
        detalles_procesados = []
        for detalle in detalles:
            detalles_procesados.append({
                'producto_id': detalle.get('producto_id'),
                'cantidad': int(detalle.get('cantidad', 0)),
                'tipo_venta': detalle.get('tipo_venta', 'pieza'),
            })
        
        # Crear la venta
        exito, resultado = VentaService.crear_venta(
            usuario=request.user,
            metodo_pago=metodo_pago,
            detalles=detalles_procesados
        )
        
        if exito:
            # Registrar acceso en bitácora
            UsuarioService.registrar_acceso(
                usuario=request.user,
                accion='venta',
                descripcion=f'Venta #{resultado.id} - Total: ${resultado.total}'
            )
            
            # Obtener nombre completo del cajero
            nombre_cajero = f"{request.user.first_name} {request.user.last_name}".strip()
            if not nombre_cajero:
                nombre_cajero = request.user.username
            
            return JsonResponse({
                'exito': True,
                'venta_id': resultado.id,
                'total': float(resultado.total),
                'cajero': nombre_cajero,
                'mensaje': 'Venta registrada exitosamente'
            })
        else:
            return JsonResponse({
                'exito': False,
                'error': resultado
            }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'exito': False,
            'error': f'Error procesando venta: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def cancelar_venta(request):
    """Cancela una venta"""
    try:
        data = json.loads(request.body)
        venta_id = data.get('venta_id')
        
        if not venta_id:
            return JsonResponse({'error': 'ID de venta requerido'}, status=400)
        
        exito, resultado = VentaService.cancelar_venta(venta_id, request.user)
        
        if exito:
            UsuarioService.registrar_acceso(
                usuario=request.user,
                accion='cancelación',
                descripcion=f'Cancelación de venta #{venta_id}'
            )
            return JsonResponse({'exito': True, 'mensaje': 'Venta cancelada'})
        else:
            return JsonResponse({
                'exito': False,
                'error': resultado
            }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'exito': False,
            'error': str(e)
        }, status=500)


@login_required
def listar_ventas(request):
    """Lista todas las ventas"""
    fecha_filtro = request.GET.get('fecha', str(date.today()))
    
    try:
        fecha = date.fromisoformat(fecha_filtro)
    except:
        fecha = date.today()
    
    ventas = Venta.objects.filter(
        fecha_venta__date=fecha
    ).order_by('-fecha_venta')
    
    totales = VentaService.calcular_totales_del_dia(fecha)
    
    context = {
        'ventas': ventas,
        'fecha': fecha,
        'totales': totales,
    }
    return render(request, 'reportes/ventas.html', context)


@login_required
def detalle_venta(request, venta_id):
    """Detalle de una venta específica"""
    venta = get_object_or_404(Venta, id=venta_id)
    
    context = {
        'venta': venta,
        'detalles': venta.detalles.all(),
    }
    return render(request, 'ventas/detalle.html', context)


@login_required
@require_http_methods(["GET"])
def ticket_venta(request, venta_id):
    """Genera ticket de venta para imprimir"""
    venta = get_object_or_404(Venta, id=venta_id)
    
    context = {
        'venta': venta,
        'detalles': venta.detalles.all(),
    }
    return render(request, 'ventas/ticket.html', context)


@login_required
@require_http_methods(["GET"])
def resumen_ventas(request):
    """Resumen de ventas con filtros por fecha y método de pago"""
    from reportes.services import ReporteService
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Q

    # Obtener parámetros de filtro
    filtro_fecha = request.GET.get('fecha', 'today')
    filtro_pago = request.GET.get('pago', 'all')
    
    # Determinar el rango de fechas según el filtro
    hoy = date.today()
    if filtro_fecha == 'today':
        fecha_inicio = hoy
        fecha_fin = hoy
        label_fecha = 'Hoy'
    elif filtro_fecha == 'yesterday':
        ayer = hoy - timedelta(days=1)
        fecha_inicio = ayer
        fecha_fin = ayer
        label_fecha = 'Ayer'
    elif filtro_fecha == 'week':
        fecha_inicio = hoy - timedelta(days=hoy.weekday())
        fecha_fin = hoy
        label_fecha = 'Esta semana'
    elif filtro_fecha == 'month':
        fecha_inicio = date(hoy.year, hoy.month, 1)
        fecha_fin = hoy
        label_fecha = 'Este mes'
    else:
        fecha_inicio = hoy
        fecha_fin = hoy
        label_fecha = 'Hoy'
    
    # Filtrar ventas
    query = Venta.objects.filter(
        fecha_venta__date__gte=fecha_inicio,
        fecha_venta__date__lte=fecha_fin
    )
    
    # Aplicar filtro de método de pago
    if filtro_pago == 'efectivo':
        query = query.filter(metodo_pago='efectivo')
    elif filtro_pago == 'transferencia':
        query = query.filter(metodo_pago='transferencia')
    
    ventas = query.order_by('-fecha_venta')
    
    # Calcular totales según los filtros
    total_ventas = 0
    total_efectivo = 0
    total_transferencias = 0
    cantidad_ventas = 0
    
    for venta in ventas:
        total_ventas += float(venta.total)
        cantidad_ventas += 1
        
        if venta.metodo_pago == 'efectivo':
            total_efectivo += float(venta.total)
        elif venta.metodo_pago == 'transferencia':
            total_transferencias += float(venta.total)
    
    # Procesar ventas para el template
    ventas_procesadas = []
    for venta in ventas:
        ventas_procesadas.append({
            'id': venta.id,
            'folio': f'V{venta.id:03d}',
            'date': venta.fecha_venta.strftime('%Y-%m-%d %H:%M'),
            'total': float(venta.total),
            'payment': venta.metodo_pago,
            'items': venta.detalles.count(),
        })
    
    # Resumen filtrado
    resumen_filtrado = {
        'total_ventas': total_ventas,
        'total_efectivo': total_efectivo,
        'total_transferencias': total_transferencias,
        'cantidad_ventas': cantidad_ventas,
    }
    
    context = {
        'resumen': resumen_filtrado,
        'ventas': ventas_procesadas,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'label_fecha': label_fecha,
        'filtro_fecha': filtro_fecha,
        'filtro_pago': filtro_pago,
    }
    return render(request, 'resumen.html', context)


@requiere_grupo('Vendedor', 'Gerente', 'Admin')
@login_required
def devolucion(request):
    """Interfaz de devoluciones"""
    context = {
        'usuario': request.user,
    }
    return render(request, 'devolucion.html', context)


@require_http_methods(["GET"])
@login_required
def buscar_venta_devolucion(request):
    """Busca una venta por ID para procesar devolución"""
    try:
        venta_id = request.GET.get('venta_id')
        
        if not venta_id:
            return JsonResponse({'error': 'ID de venta requerido'}, status=400)
        
        exito, venta = VentaService.obtener_venta_por_id(int(venta_id))
        
        if not exito:
            return JsonResponse({
                'exito': False,
                'error': venta
            }, status=404)
        
        # Obtener detalles de la venta
        detalles = []
        for detalle in venta.detalles.all():
            detalles.append({
                'id': detalle.id,
                'producto_id': detalle.producto.id,
                'producto_nombre': detalle.producto.nombre,
                'cantidad': detalle.cantidad,
                'precio_unitario': float(detalle.precio_unitario),
                'subtotal': float(detalle.subtotal),
                'tipo_venta': detalle.tipo_venta,
            })
        
        return JsonResponse({
            'exito': True,
            'venta': {
                'id': venta.id,
                'fecha': venta.fecha_venta.strftime('%d/%m/%Y %H:%M'),
                'total': float(venta.total),
                'metodo_pago': venta.metodo_pago,
                'usuario': venta.usuario.get_full_name() or venta.usuario.username,
            },
            'detalles': detalles
        })
    
    except ValueError:
        return JsonResponse({'error': 'ID de venta inválido'}, status=400)
    except Exception as e:
        return JsonResponse({
            'exito': False,
            'error': f'Error: {str(e)}'
        }, status=500)


@csrf_exempt
@requiere_grupo('Vendedor', 'Gerente', 'Admin')
@require_http_methods(["POST"])
@login_required
def procesar_devolucion_api(request):
    """Procesa una devolución de productos"""
    try:
        data = json.loads(request.body)
        
        venta_id = data.get('venta_id')
        detalles = data.get('detalles', [])
        motivo = data.get('motivo')
        tipo_reembolso = data.get('tipo_reembolso')
        notas = data.get('notas', '')
        
        if not all([venta_id, detalles, motivo, tipo_reembolso]):
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        # Procesar devolución
        exito, resultado = VentaService.procesar_devolucion(
            venta_id=int(venta_id),
            detalles_devolucion=detalles,
            usuario=request.user,
            motivo=motivo,
            tipo_reembolso=tipo_reembolso,
            notas=notas
        )
        
        if exito:
            # Registrar en bitácora
            UsuarioService.registrar_acceso(
                usuario=request.user,
                accion='devolucion',
                descripcion=f'Devolución venta #{venta_id} - Total: ${resultado.total_devuelto}'
            )
            
            return JsonResponse({
                'exito': True,
                'devolucion_id': resultado.id,
                'total_devuelto': float(resultado.total_devuelto),
                'mensaje': 'Devolución procesada exitosamente'
            })
        else:
            return JsonResponse({
                'exito': False,
                'error': resultado
            }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'exito': False,
            'error': f'Error procesando devolución: {str(e)}'
        }, status=500)
