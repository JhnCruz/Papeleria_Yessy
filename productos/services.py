"""
Servicios de Productos - Capa de Dominio
"""
from django.db import transaction
from .models import Producto, Categoria


class ProductoService:
    """Servicio para operaciones con productos"""
    
    @staticmethod
    def obtener_por_sku(sku):
        """Obtiene un producto por su código de barras"""
        try:
            return Producto.objects.get(sku=sku, activo=True)
        except Producto.DoesNotExist:
            return None
    
    @staticmethod
    def obtener_todos():
        """Obtiene todos los productos activos"""
        return Producto.objects.filter(activo=True)
    
    @staticmethod
    def obtener_bajo_stock():
        """Obtiene productos con stock bajo"""
        return Producto.objects.filter(
            activo=True,
            stock_actual__lte=models.F('stock_minimo')
        )
    
    @staticmethod
    @transaction.atomic
    def crear_producto(sku, nombre, categoria_id, precio_pieza, 
                       descripcion='', precio_paquete=None, cantidad_paquete=1):
        """Crea un nuevo producto"""
        try:
            categoria = Categoria.objects.get(id=categoria_id)
            producto = Producto.objects.create(
                sku=sku,
                nombre=nombre,
                categoria=categoria,
                precio_pieza=precio_pieza,
                precio_paquete=precio_paquete,
                cantidad_paquete=cantidad_paquete,
                descripcion=descripcion
            )
            return True, producto
        except Categoria.DoesNotExist:
            return False, "Categoría no encontrada"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def actualizar_stock(producto_id, nueva_cantidad):
        """Actualiza el stock de un producto"""
        try:
            producto = Producto.objects.get(id=producto_id)
            producto.stock_actual = nueva_cantidad
            producto.save()
            return True, producto
        except Producto.DoesNotExist:
            return False, "Producto no encontrado"
    
    @staticmethod
    def validar_stock_disponible(producto_id, cantidad):
        """Valida si hay suficiente stock"""
        try:
            producto = Producto.objects.get(id=producto_id)
            return producto.stock_actual >= cantidad
        except Producto.DoesNotExist:
            return False


class CategoriaService:
    """Servicio para operaciones con categorías"""
    
    @staticmethod
    def obtener_todas():
        """Obtiene todas las categorías activas"""
        return Categoria.objects.filter(activa=True)
    
    @staticmethod
    def crear_categoria(nombre, descripcion=''):
        """Crea una nueva categoría"""
        try:
            categoria = Categoria.objects.create(
                nombre=nombre,
                descripcion=descripcion
            )
            return True, categoria
        except Exception as e:
            return False, str(e)
