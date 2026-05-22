"""
Servicios de Reportes - Capa de Dominio
"""
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Q, F
from productos.models import Producto
from ventas.models import Venta, DetalleVenta, Devolucion
from inventario.models import MovimientoInventario


class ReporteService:
    """Servicio para generación de reportes"""
    
    @staticmethod
    def reporte_productos():
        """Reporte de productos con stock actual"""
        productos = Producto.objects.filter(activo=True)
        
        datos = []
        for producto in productos:
            datos.append({
                'sku': producto.sku,
                'nombre': producto.nombre,
                'categoria': producto.categoria.nombre,
                'precio_pieza': float(producto.precio_pieza),
                'precio_paquete': float(producto.precio_paquete) if producto.precio_paquete else None,
                'stock_actual': producto.stock_actual,
                'stock_minimo': producto.stock_minimo,
                'bajo_stock': producto.bajo_stock,
            })
        
        return datos
    
    @staticmethod
    def reporte_ventas_periodo(fecha_inicio, fecha_fin):
        """Reporte de ventas en un período"""
        ventas = Venta.objects.filter(
            fecha_venta__date__gte=fecha_inicio,
            fecha_venta__date__lte=fecha_fin,
            estado='completada'
        )
        
        total_general = Decimal('0.00')
        total_efectivo = Decimal('0.00')
        total_transferencias = Decimal('0.00')
        
        datos = []
        for venta in ventas:
            total_general += venta.total
            
            if venta.metodo_pago == 'efectivo':
                total_efectivo += venta.total
            else:
                total_transferencias += venta.total
            
            datos.append({
                'id': venta.id,
                'fecha': venta.fecha_venta.strftime('%d/%m/%Y %H:%M'),
                'total': float(venta.total),
                'metodo_pago': venta.get_metodo_pago_display(),
                'usuario': venta.usuario.get_full_name() or venta.usuario.username,
                'cantidad_articulos': venta.cantidad_articulos,
            })
        
        return {
            'datos': datos,
            'total_general': float(total_general),
            'total_efectivo': float(total_efectivo),
            'total_transferencias': float(total_transferencias),
            'cantidad_ventas': len(datos),
        }
    
    @staticmethod
    def reporte_productos_vendidos_periodo(fecha_inicio, fecha_fin, categoria_id=None):
        """Reporte de productos más vendidos - Separando Piezas y Paquetes"""
        queryset = DetalleVenta.objects.filter(
            venta__fecha_venta__date__gte=fecha_inicio,
            venta__fecha_venta__date__lte=fecha_fin,
            venta__estado='completada'
        )
        
        # Filtrar por categoría si se proporciona
        if categoria_id:
            queryset = queryset.filter(producto__categoria_id=categoria_id)
        
        detalles = queryset.values('producto__nombre', 'producto__sku', 'tipo_venta').annotate(
            cantidad_total=Sum('cantidad'),
            monto_total=Sum('subtotal'),
            cantidad_ventas=Count('venta', distinct=True)
        ).order_by('-cantidad_total')
        
        datos = []
        for detalle in detalles:
            tipo_venta_display = 'Paquete' if detalle['tipo_venta'] == 'paquete' else 'Pieza'
            datos.append({
                'producto': detalle['producto__nombre'],
                'sku': detalle['producto__sku'],
                'tipo_venta': tipo_venta_display,
                'cantidad_total': detalle['cantidad_total'],
                'monto_total': float(detalle['monto_total']),
                'cantidad_transacciones': detalle['cantidad_ventas'],
            })
        
        return datos
    
    @staticmethod
    def reporte_inventario_movimientos(fecha_inicio, fecha_fin, tipo_movimiento=None):
        """Reporte de movimientos de inventario"""
        queryset = MovimientoInventario.objects.filter(
            created_at__date__gte=fecha_inicio,
            created_at__date__lte=fecha_fin
        )
        
        if tipo_movimiento:
            queryset = queryset.filter(tipo_movimiento=tipo_movimiento)
        
        datos = []
        for movimiento in queryset:
            datos.append({
                'producto': movimiento.producto.nombre,
                'sku': movimiento.producto.sku,
                'tipo': movimiento.get_tipo_movimiento_display(),
                'cantidad': movimiento.cantidad,
                'referencia': movimiento.referencia,
                'fecha': movimiento.created_at.strftime('%d/%m/%Y %H:%M'),
                'usuario': movimiento.usuario.get_full_name() if movimiento.usuario else 'N/A',
            })
        
        return datos
    
    @staticmethod
    def reporte_productos_bajo_stock():
        """Reporte de productos con stock bajo - usando stock_minimo de cada producto"""
        productos = Producto.objects.filter(
            activo=True,
            stock_actual__lte=F('stock_minimo')
        )
        
        datos = []
        for producto in productos:
            datos.append({
                'sku': producto.sku,
                'nombre': producto.nombre,
                'stock_actual': producto.stock_actual,
                'stock_minimo': producto.stock_minimo,
                'faltante': producto.stock_minimo - producto.stock_actual,
            })
        
        return datos
    
    @staticmethod
    def resumen_diario(fecha):
        """Resumen completo del día con devoluciones"""
        desde = fecha
        hasta = fecha + timedelta(days=1)
        
        ventas = Venta.objects.filter(
            fecha_venta__gte=desde,
            fecha_venta__lt=hasta,
            estado='completada'
        )
        
        total = Decimal('0.00')
        efectivo = Decimal('0.00')
        transferencias = Decimal('0.00')
        cantidad_efectivo = 0
        cantidad_transferencias = 0
        
        for venta in ventas:
            total += venta.total
            if venta.metodo_pago == 'efectivo':
                efectivo += venta.total
                cantidad_efectivo += 1
            else:
                transferencias += venta.total
                cantidad_transferencias += 1
        
        # Calcular devoluciones del día
        devoluciones = Devolucion.objects.filter(
            fecha_devolucion__gte=desde,
            fecha_devolucion__lt=hasta
        )
        
        total_devoluciones = Decimal('0.00')
        devoluciones_efectivo = Decimal('0.00')
        devoluciones_transferencias = Decimal('0.00')
        cantidad_devoluciones = 0
        
        for devolucion in devoluciones:
            total_devoluciones += devolucion.total_devuelto
            cantidad_devoluciones += 1
            
            # Categorizar por método de reembolso
            if devolucion.tipo_reembolso == 'efectivo':
                devoluciones_efectivo += devolucion.total_devuelto
            elif devolucion.tipo_reembolso == 'transferencia':
                devoluciones_transferencias += devolucion.total_devuelto
            # Los créditos no se cuentan como devoluciones de dinero
        
        # Calcular neto (ventas - devoluciones)
        total_neto = total - total_devoluciones
        efectivo_neto = efectivo - devoluciones_efectivo
        transferencias_neto = transferencias - devoluciones_transferencias
        
        return {
            'fecha': fecha.strftime('%d/%m/%Y'),
            # Ventas brutas
            'total_ventas': float(total),
            'total_efectivo': float(efectivo),
            'total_transferencias': float(transferencias),
            'cantidad_ventas': ventas.count(),
            'cantidad_efectivo': cantidad_efectivo,
            'cantidad_transferencias': cantidad_transferencias,
            # Devoluciones
            'total_devoluciones': float(total_devoluciones),
            'devoluciones_efectivo': float(devoluciones_efectivo),
            'devoluciones_transferencias': float(devoluciones_transferencias),
            'cantidad_devoluciones': cantidad_devoluciones,
            # Neto (lo importante para cierre de caja)
            'total_neto': float(total_neto),
            'efectivo_neto': float(efectivo_neto),
            'transferencias_neto': float(transferencias_neto),
        }
    
    @staticmethod
    def resumen_movimientos_diarios(fecha):
        """Resumen de movimientos de inventario del día"""
        desde = fecha
        hasta = fecha + timedelta(days=1)
        
        movimientos = MovimientoInventario.objects.filter(
            created_at__gte=desde,
            created_at__lt=hasta
        )
        
        entradas = 0
        salidas = 0
        ajustes = 0
        cancelaciones = 0
        
        for mov in movimientos:
            if mov.tipo_movimiento == 'entrada':
                entradas += mov.cantidad
            elif mov.tipo_movimiento == 'venta':
                salidas += mov.cantidad  # Generalmente negativo
            elif mov.tipo_movimiento == 'ajuste':
                ajustes += mov.cantidad
            elif mov.tipo_movimiento == 'cancelacion':
                cancelaciones += mov.cantidad
        
        return {
            'entradas': entradas,
            'salidas': salidas,
            'ajustes': ajustes,
            'cancelaciones': cancelaciones,
        }
