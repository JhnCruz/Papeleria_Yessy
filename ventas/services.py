"""
Servicios de Ventas - Capa de Dominio
"""
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import Venta, DetalleVenta, Devolucion, DetalleDevolucion
from productos.models import Producto
from inventario.services import InventarioService


class VentaService:
    """Servicio para operaciones de ventas"""
    
    @staticmethod
    @transaction.atomic
    def crear_venta(usuario, metodo_pago, detalles):
        """
        Crea una nueva venta
        detalles: lista de dicts con {producto_id, cantidad, tipo_venta}
        """
        try:
            venta = Venta.objects.create(
                usuario=usuario,
                metodo_pago=metodo_pago,
                estado='completada'
            )
            
            total_venta = Decimal('0.00')
            
            for detalle in detalles:
                producto = Producto.objects.get(id=detalle['producto_id'])
                cantidad = detalle['cantidad']
                tipo_venta = detalle['tipo_venta']
                
                # Validar stock
                if not InventarioService.hay_stock_disponible(producto.id, cantidad):
                    raise ValueError(f"Stock insuficiente para {producto.nombre}")
                
                # Determinar precio según tipo de venta
                if tipo_venta == 'paquete' and producto.precio_paquete:
                    precio_unitario = producto.precio_paquete
                else:
                    precio_unitario = producto.precio_pieza
                
                # Crear detalle de venta
                detalle_venta = DetalleVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    tipo_venta=tipo_venta,
                    precio_unitario=precio_unitario
                )
                
                # Calcular cantidad total de piezas a descontar
                if tipo_venta == 'paquete' and producto.cantidad_paquete:
                    cantidad_piezas_descontar = cantidad * producto.cantidad_paquete
                else:
                    cantidad_piezas_descontar = cantidad
                
                # Registrar movimiento en inventario (en piezas)
                # Nota: registrar_movimiento se encarga de actualizar el stock
                InventarioService.registrar_movimiento(
                    producto.id,
                    cantidad_piezas_descontar,
                    'venta',
                    f"Venta #{venta.id}",
                    usuario.id
                )
                
                total_venta += detalle_venta.subtotal
            
            # Actualizar total de venta
            venta.total = total_venta
            venta.save()
            
            return True, venta
        
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    @transaction.atomic
    def cancelar_venta(venta_id, usuario):
        """Cancela una venta y devuelve el stock"""
        try:
            venta = Venta.objects.get(id=venta_id)
            
            if venta.estado == 'cancelada':
                return False, "La venta ya está cancelada"
            
            # Devolver stock
            for detalle in venta.detalles.all():
                producto = detalle.producto
                producto.stock_actual += detalle.cantidad
                producto.save()
                
                # Registrar movimiento
                InventarioService.registrar_movimiento(
                    producto.id,
                    detalle.cantidad,
                    'cancelacion',
                    f"Cancelación venta #{venta.id}",
                    usuario.id
                )
            
            venta.estado = 'cancelada'
            venta.save()
            
            return True, venta
        
        except Venta.DoesNotExist:
            return False, "Venta no encontrada"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def obtener_ventas_del_dia(fecha):
        """Obtiene todas las ventas completadas del día"""
        return Venta.objects.filter(
            fecha_venta__date=fecha,
            estado='completada'
        )
    
    @staticmethod
    def calcular_totales_del_dia(fecha):
        """Calcula los totales de ventas y devoluciones del día por método de pago"""
        from datetime import timedelta
        desde = fecha
        hasta = fecha + timedelta(days=1)
        
        ventas = VentaService.obtener_ventas_del_dia(fecha)
        
        total_ventas = Decimal('0.00')
        total_efectivo = Decimal('0.00')
        total_transferencias = Decimal('0.00')
        cantidad_efectivo = 0
        cantidad_transferencias = 0
        total_items = 0
        
        for venta in ventas:
            total_ventas += venta.total
            
            if venta.metodo_pago == 'efectivo':
                total_efectivo += venta.total
                cantidad_efectivo += 1
            elif venta.metodo_pago == 'transferencia':
                total_transferencias += venta.total
                cantidad_transferencias += 1
            
            # Contar items (suma de cantidades, no de detalles)
            total_items += sum(detalle.cantidad for detalle in venta.detalles.all())
        
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
            
            if devolucion.tipo_reembolso == 'efectivo':
                devoluciones_efectivo += devolucion.total_devuelto
            elif devolucion.tipo_reembolso == 'transferencia':
                devoluciones_transferencias += devolucion.total_devuelto
        
        # Calcular neto
        total_neto = total_ventas - total_devoluciones
        efectivo_neto = total_efectivo - devoluciones_efectivo
        transferencias_neto = total_transferencias - devoluciones_transferencias
        
        return {
            # Totales brutos (ventas)
            'total': total_ventas,
            'total_ventas': total_ventas,
            'efectivo': total_efectivo,
            'total_efectivo': total_efectivo,
            'transferencias': total_transferencias,
            'total_transferencias': total_transferencias,
            'cantidad_ventas': ventas.count(),
            'cantidad_efectivo': cantidad_efectivo,
            'cantidad_transferencias': cantidad_transferencias,
            'cantidad_items': total_items,
            # Devoluciones
            'total_devoluciones': total_devoluciones,
            'devoluciones_efectivo': devoluciones_efectivo,
            'devoluciones_transferencias': devoluciones_transferencias,
            'cantidad_devoluciones': cantidad_devoluciones,
            # Neto (lo que importa)
            'total_neto': total_neto,
            'efectivo_neto': efectivo_neto,
            'transferencias_neto': transferencias_neto,
        }
    
    @staticmethod
    def obtener_venta_por_id(venta_id):
        """Obtiene una venta por su ID"""
        try:
            venta = Venta.objects.get(id=venta_id)
            return True, venta
        except Venta.DoesNotExist:
            return False, "Venta no encontrada"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    @transaction.atomic
    def procesar_devolucion(venta_id, detalles_devolucion, usuario, motivo, tipo_reembolso, notas=''):
        """
        Procesa una devolución parcial o total de una venta
        detalles_devolucion: lista de dicts con {detalle_venta_id, cantidad}
        """
        try:
            venta = Venta.objects.get(id=venta_id)
            
            # Crear registro de devolución (con auditoría: auto-aprobada al procesarse)
            devolucion = Devolucion.objects.create(
                venta=venta,
                motivo=motivo,
                tipo_reembolso=tipo_reembolso,
                usuario=usuario,
                notas=notas,
                estado='aprobada',
                usuario_aprobacion=usuario,
                fecha_aprobacion=timezone.now()
            )
            
            total_devuelto = Decimal('0.00')
            
            # Procesar cada detalle de devolución
            for detalle_info in detalles_devolucion:
                detalle_venta_id = detalle_info.get('detalle_venta_id')
                cantidad_devuelta = int(detalle_info.get('cantidad', 0))
                
                # Obtener detalle original
                detalle_venta = DetalleVenta.objects.get(id=detalle_venta_id)
                
                # Validar cantidad
                if cantidad_devuelta > detalle_venta.cantidad:
                    raise ValueError(f"No se pueden devolver más de {detalle_venta.cantidad} unidades")
                
                # Crear detalle de devolución
                detalle_dev = DetalleDevolucion.objects.create(
                    devolucion=devolucion,
                    detalle_venta=detalle_venta,
                    cantidad=cantidad_devuelta,
                    precio_unitario=detalle_venta.precio_unitario
                )
                
                # Sumar al total devuelto
                total_devuelto += detalle_dev.subtotal
                
                # Actualizar stock del producto (devolver al inventario)
                producto = detalle_venta.producto
                producto.stock_actual += cantidad_devuelta
                producto.save()
                
                # Registrar movimiento en inventario
                InventarioService.registrar_movimiento(
                    producto.id,
                    cantidad_devuelta,
                    'devolucion',
                    f"Devolución venta #{venta.id}",
                    usuario.id
                )
            
            # Actualizar total de devolución
            devolucion.total_devuelto = total_devuelto
            devolucion.save()
            
            return True, devolucion
        
        except Exception as e:
            return False, str(e)
