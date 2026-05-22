from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import date, timedelta
import json

from .services import ReporteService
from productos.models import Producto, Categoria
from usuarios.permisos import requiere_grupo


@requiere_grupo('Gerente', 'Contable', 'Admin')
@login_required
def dashboard(request):
    """Dashboard principal con opción de reportes"""
    from usuarios.models import BitacoraAcceso
    
    hoy = date.today()
    
    # Soportar filtros de fecha desde URL
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    
    if fecha_inicio_str and fecha_fin_str:
        try:
            fecha_inicio = date.fromisoformat(fecha_inicio_str)
            fecha_fin = date.fromisoformat(fecha_fin_str)
        except:
            fecha_inicio = hoy - timedelta(days=30)
            fecha_fin = hoy
    else:
        fecha_inicio = hoy - timedelta(days=30)
        fecha_fin = hoy
    
    resumen = ReporteService.resumen_diario(hoy)
    movimientos = ReporteService.resumen_movimientos_diarios(hoy)
    
    # Productos más vendidos (período especificado)
    productos_vendidos = ReporteService.reporte_productos_vendidos_periodo(fecha_inicio, fecha_fin)
    
    # Productos bajo stock
    productos_bajo_stock = Producto.objects.filter(
        activo=True,
        stock_actual__lt=10
    ).values('nombre', 'stock_actual', 'stock_minimo')[:5]
    
    # Bitácora de acciones (últimos 5 registros)
    bitacora = BitacoraAcceso.objects.all().order_by('-created_at')[:5]
    
    context = {
        'hoy': hoy,
        'resumen': resumen,
        'movimientos': movimientos,
        'productos_vendidos': productos_vendidos[:5],
        'productos_bajo_stock': list(productos_bajo_stock),
        'bitacora': bitacora,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'reportes.html', context)


@requiere_grupo('Gerente', 'Contable', 'Admin')
@login_required
def reporte_ventas(request):
    """Reporte de ventas por período"""
    fecha_inicio_str = request.GET.get('fecha_inicio', str(date.today() - timedelta(days=30)))
    fecha_fin_str = request.GET.get('fecha_fin', str(date.today()))
    
    try:
        fecha_inicio = date.fromisoformat(fecha_inicio_str)
        fecha_fin = date.fromisoformat(fecha_fin_str)
    except:
        fecha_inicio = date.today() - timedelta(days=30)
        fecha_fin = date.today()
    
    reporte = ReporteService.reporte_ventas_periodo(fecha_inicio, fecha_fin)
    
    context = {
        'reporte': reporte,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'reportes/ventas.html', context)


@requiere_grupo('Gerente', 'Contable', 'Admin')
@login_required
def reporte_productos_vendidos(request):
    """Reporte de productos más vendidos"""
    fecha_inicio_str = request.GET.get('fecha_inicio', str(date.today() - timedelta(days=30)))
    fecha_fin_str = request.GET.get('fecha_fin', str(date.today()))
    categoria_id = request.GET.get('categoria_id')
    
    try:
        fecha_inicio = date.fromisoformat(fecha_inicio_str)
        fecha_fin = date.fromisoformat(fecha_fin_str)
    except:
        fecha_inicio = date.today() - timedelta(days=30)
        fecha_fin = date.today()
    
    # Obtener todas las categorías para el filtro
    categorias = Categoria.objects.all().order_by('nombre')
    
    # Convertir categoria_id a int si viene del GET
    if categoria_id:
        try:
            categoria_id = int(categoria_id)
        except (ValueError, TypeError):
            categoria_id = None
    
    reporte = ReporteService.reporte_productos_vendidos_periodo(fecha_inicio, fecha_fin, categoria_id)
    
    context = {
        'reporte': reporte,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'categorias': categorias,
        'categoria_id_selected': categoria_id,
    }
    return render(request, 'reportes/productos_vendidos.html', context)


@requiere_grupo('Gerente', 'Admin')
@login_required
def reporte_inventario(request):
    """Reporte de estado actual de inventario"""
    # Filtro por categoría opcional
    categoria_id = request.GET.get('categoria')
    
    productos = ReporteService.reporte_productos()
    bajo_stock = [p for p in productos if p['bajo_stock']]
    
    # Si hay filtro de categoría, aplicarlo
    if categoria_id:
        try:
            categoria_id = int(categoria_id)
            productos = [p for p in productos if p.get('categoria_id') == categoria_id]
            bajo_stock = [p for p in bajo_stock if p.get('categoria_id') == categoria_id]
        except:
            pass
    
    context = {
        'productos': productos,
        'bajo_stock': bajo_stock,
        'total_productos': len(productos),
        'productos_bajo_stock': len(bajo_stock),
        'categoria_id': categoria_id,
    }
    return render(request, 'reportes/inventario.html', context)


@requiere_grupo('Gerente', 'Admin')
@login_required
def reporte_movimientos_inventario(request):
    """Reporte de movimientos de inventario"""
    fecha_inicio_str = request.GET.get('fecha_inicio', str(date.today() - timedelta(days=30)))
    fecha_fin_str = request.GET.get('fecha_fin', str(date.today()))
    tipo_movimiento = request.GET.get('tipo_movimiento')
    
    try:
        fecha_inicio = date.fromisoformat(fecha_inicio_str)
        fecha_fin = date.fromisoformat(fecha_fin_str)
    except:
        fecha_inicio = date.today() - timedelta(days=30)
        fecha_fin = date.today()
    
    if not tipo_movimiento:
        tipo_movimiento = None
    
    reporte = ReporteService.reporte_inventario_movimientos(
        fecha_inicio, fecha_fin, tipo_movimiento
    )
    
    context = {
        'reporte': reporte,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'tipo_movimiento': tipo_movimiento,
    }
    return render(request, 'reportes/movimientos.html', context)


@requiere_grupo('Gerente', 'Admin')
@login_required
def reporte_stock_bajo(request):
    """Reporte detallado de productos con stock bajo"""
    # Filtro opcional por categoría
    categoria_id = request.GET.get('categoria')
    
    productos_bajo_stock = ReporteService.reporte_productos_bajo_stock()
    
    # Si hay filtro de categoría, aplicarlo
    if categoria_id:
        try:
            categoria_id = int(categoria_id)
            productos_bajo_stock = [p for p in productos_bajo_stock if p.get('categoria_id') == categoria_id]
        except:
            pass
    
    # Ordenar por faltante (descendente)
    productos_bajo_stock = sorted(productos_bajo_stock, key=lambda x: x['faltante'], reverse=True)
    
    # Obtener categorías para el filtro
    from productos.models import Categoria
    categorias = Categoria.objects.all()
    
    context = {
        'productos': productos_bajo_stock,
        'total_bajo_stock': len(productos_bajo_stock),
        'categorias': categorias,
        'categoria_id': categoria_id,
    }
    return render(request, 'reportes/stock_bajo.html', context)


@login_required
def resumen(request):
    """Página de resumen general"""
    hoy = date.today()
    resumen_hoy = ReporteService.resumen_diario(hoy)
    
    # Resumen de últimos 7 días
    ultimos_7_dias = []
    for i in range(6, -1, -1):
        fecha = hoy - timedelta(days=i)
        datos = ReporteService.resumen_diario(fecha)
        ultimos_7_dias.append(datos)
    
    context = {
        'resumen_hoy': resumen_hoy,
        'ultimos_7_dias': ultimos_7_dias,
    }
    return render(request, 'resumen.html', context)


# ============
# EXPORTACIONES
# ============

@requiere_grupo('Gerente', 'Contable', 'Admin')
@login_required
def exportar_reporte_ventas(request):
    """Exportar reporte de ventas a CSV"""
    from .exportar import exportar_reporte_csv
    
    fecha_inicio_str = request.GET.get('fecha_inicio', str(date.today() - timedelta(days=30)))
    fecha_fin_str = request.GET.get('fecha_fin', str(date.today()))
    
    try:
        fecha_inicio = date.fromisoformat(fecha_inicio_str)
        fecha_fin = date.fromisoformat(fecha_fin_str)
    except:
        fecha_inicio = date.today() - timedelta(days=30)
        fecha_fin = date.today()
    
    reporte = ReporteService.reporte_ventas_periodo(fecha_inicio, fecha_fin)
    
    # Preparar datos para exportar
    datos = reporte['datos']
    headers = ['id', 'fecha', 'total', 'metodo_pago', 'usuario', 'cantidad_articulos']
    
    return exportar_reporte_csv(
        f"ventas_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}",
        headers,
        datos
    )


@requiere_grupo('Gerente', 'Contable', 'Admin')
@login_required
def exportar_reporte_productos_vendidos(request):
    """Exportar reporte de productos vendidos a CSV"""
    from .exportar import exportar_reporte_csv
    
    fecha_inicio_str = request.GET.get('fecha_inicio', str(date.today() - timedelta(days=30)))
    fecha_fin_str = request.GET.get('fecha_fin', str(date.today()))
    categoria_id = request.GET.get('categoria_id')
    
    try:
        fecha_inicio = date.fromisoformat(fecha_inicio_str)
        fecha_fin = date.fromisoformat(fecha_fin_str)
    except:
        fecha_inicio = date.today() - timedelta(days=30)
        fecha_fin = date.today()
    
    if categoria_id:
        try:
            categoria_id = int(categoria_id)
        except (ValueError, TypeError):
            categoria_id = None
    
    reporte = ReporteService.reporte_productos_vendidos_periodo(fecha_inicio, fecha_fin, categoria_id)
    
    # Preparar datos
    headers = ['producto', 'sku', 'tipo_venta', 'cantidad_total', 'cantidad_transacciones', 'monto_total']
    
    return exportar_reporte_csv(
        f"productos_vendidos_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}",
        headers,
        reporte
    )


@requiere_grupo('Gerente', 'Admin')
@login_required
def exportar_reporte_inventario(request):
    """Exportar reporte de inventario a CSV"""
    from .exportar import exportar_reporte_csv
    
    categoria_id = request.GET.get('categoria_id')
    
    datos = ReporteService.reporte_productos()
    
    # Filtrar por categoría si es necesario
    if categoria_id:
        try:
            categoria_id = int(categoria_id)
            datos = [d for d in datos if Producto.objects.filter(id=d.get('id')).first().categoria_id == categoria_id]
        except (ValueError, TypeError):
            pass
    
    # Preparar datos
    headers = ['sku', 'nombre', 'categoria', 'precio_pieza', 'precio_paquete', 'stock_actual', 'stock_minimo', 'bajo_stock']
    
    return exportar_reporte_csv(
        f"inventario_{date.today().strftime('%Y%m%d')}",
        headers,
        datos
    )
