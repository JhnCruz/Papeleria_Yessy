"""
Servicios de Inventario - Capa de Dominio
"""
from django.db import transaction
from .models import MovimientoInventario
from productos.models import Producto


class InventarioService:
    """Servicio para operaciones de inventario"""
    
    @staticmethod
    @transaction.atomic
    def registrar_movimiento(producto_id, cantidad, tipo_movimiento, 
                           referencia='', usuario_id=None, descripcion=''):
        """Registra un movimiento en el inventario"""
        try:
            producto = Producto.objects.get(id=producto_id)
            
            movimiento = MovimientoInventario.objects.create(
                producto=producto,
                cantidad=cantidad,
                tipo_movimiento=tipo_movimiento,
                referencia=referencia,
                usuario_id=usuario_id,
                descripcion=descripcion
            )
            
            # Actualizar stock según tipo de movimiento
            if tipo_movimiento in ('entrada', 'compra', 'ajuste_positivo'):
                producto.stock_actual += cantidad
            elif tipo_movimiento in ('salida', 'venta', 'ajuste_negativo'):
                producto.stock_actual -= cantidad
            
            producto.save()
            
            return True, movimiento
        
        except Producto.DoesNotExist:
            return False, "Producto no encontrado"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def obtener_movimientos_producto(producto_id):
        """Obtiene todos los movimientos de un producto"""
        return MovimientoInventario.objects.filter(
            producto_id=producto_id
        ).order_by('-created_at')
    
    @staticmethod
    def obtener_movimientos_por_tipo(tipo_movimiento, fecha_inicio=None, fecha_fin=None):
        """Obtiene movimientos por tipo en un rango de fechas"""
        queryset = MovimientoInventario.objects.filter(
            tipo_movimiento=tipo_movimiento
        )
        
        if fecha_inicio:
            queryset = queryset.filter(created_at__gte=fecha_inicio)
        
        if fecha_fin:
            queryset = queryset.filter(created_at__lte=fecha_fin)
        
        return queryset
    
    @staticmethod
    def hay_stock_disponible(producto_id, cantidad):
        """Verifica si hay stock disponible"""
        try:
            producto = Producto.objects.get(id=producto_id)
            return producto.stock_actual >= cantidad
        except Producto.DoesNotExist:
            return False
    
    @staticmethod
    @transaction.atomic
    def ajuste_manual_stock(producto_id, nueva_cantidad, usuario_id, descripcion=''):
        """Realiza un ajuste manual de stock"""
        try:
            producto = Producto.objects.get(id=producto_id)
            diferencia = nueva_cantidad - producto.stock_actual
            
            # Registrar movimiento
            MovimientoInventario.objects.create(
                producto=producto,
                cantidad=diferencia,
                tipo_movimiento='ajuste',
                usuario_id=usuario_id,
                descripcion=descripcion
            )
            
            # Actualizar stock
            producto.stock_actual = nueva_cantidad
            producto.save()
            
            return True, producto
        
        except Producto.DoesNotExist:
            return False, "Producto no encontrado"
        except Exception as e:
            return False, str(e)
