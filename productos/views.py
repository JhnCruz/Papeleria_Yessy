from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import F, Q, Sum
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from .models import Producto, Categoria
from .services import ProductoService, CategoriaService
from usuarios.services import UsuarioService
from inventario.models import MovimientoInventario
from django.views.decorators.http import require_http_methods
import json


@login_required
def listar_productos(request):
    """Lista todos los productos activos"""
    productos = Producto.objects.filter(activo=True).select_related('categoria').order_by('nombre')
    categorias = Categoria.objects.filter(activa=True).order_by('nombre')
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'titulo': 'Inventario de Productos',
    }
    return render(request, 'productos/listar.html', context)


@login_required
def inventario_general(request):
    """Vista del inventario general con resumen de stock"""
    # Obtener todos los productos
    productos = Producto.objects.select_related('categoria').order_by('nombre')
    
    # Calcular estadísticas
    total_productos = productos.count()
    stock_total = productos.aggregate(total=Sum('stock_actual'))['total'] or 0
    valor_total_inventario = 0
    
    # Calcular valor total del inventario
    for producto in productos:
        valor_total_inventario += float(producto.precio_pieza) * producto.stock_actual
    
    # Productos con stock bajo
    productos_bajo_stock = productos.filter(stock_actual__lte=F('stock_minimo')).count()
    
    # Productos sin stock
    productos_sin_stock = productos.filter(stock_actual=0).count()
    
    # Agrupar por categoría
    categorias_stats = []
    for categoria in Categoria.objects.filter(activa=True):
        prods_cat = productos.filter(categoria=categoria)
        stock_cat = prods_cat.aggregate(total=Sum('stock_actual'))['total'] or 0
        categorias_stats.append({
            'nombre': categoria.nombre,
            'total_productos': prods_cat.count(),
            'stock_total': stock_cat,
            'bajo_stock': prods_cat.filter(stock_actual__lte=F('stock_minimo')).count(),
        })
    
    context = {
        'total_productos': total_productos,
        'stock_total': stock_total,
        'valor_total': valor_total_inventario,
        'productos_bajo_stock': productos_bajo_stock,
        'productos_sin_stock': productos_sin_stock,
        'categorias_stats': categorias_stats,
        'productos': productos,
        'titulo': 'Inventario General',
    }
    return render(request, 'productos/inventario_general.html', context)


def buscar_producto_sku(request):
    """Busca un producto por SKU (para POS)"""
    sku = request.GET.get('sku', '').strip()
    
    if not sku:
        return JsonResponse({'error': 'SKU requerido'}, status=400)
    
    producto = ProductoService.obtener_por_sku(sku)
    
    if not producto:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)
    
    return JsonResponse({
        'id': producto.id,
        'sku': producto.sku,
        'nombre': producto.nombre,
        'precio_pieza': float(producto.precio_pieza),
        'precio_paquete': float(producto.precio_paquete) if producto.precio_paquete else None,
        'cantidad_paquete': producto.cantidad_paquete,
        'stock_actual': producto.stock_actual,
        'categoria': producto.categoria.nombre if producto.categoria else None,
    })


def buscar_producto_nombre(request):
    """Busca productos por nombre (busqueda de texto)"""
    query = request.GET.get('query', '').strip()
    
    if not query or len(query) < 1:
        return JsonResponse({'productos': []})
    
    # Buscar productos cuyo nombre contenga el query (case-insensitive)
    from django.db.models import Q
    productos = Producto.objects.filter(
        Q(nombre__icontains=query) | Q(sku__icontains=query),
        activo=True
    )[:10]  # Limitar a 10 resultados
    
    productos_json = [
        {
            'id': p.id,
            'sku': p.sku,
            'nombre': p.nombre,
            'precio_pieza': float(p.precio_pieza),
            'precio_paquete': float(p.precio_paquete) if p.precio_paquete else None,
            'cantidad_paquete': p.cantidad_paquete,
            'stock_actual': p.stock_actual,
        }
        for p in productos
    ]
    
    return JsonResponse({'productos': productos_json})


def api_listar_productos(request):
    """API endpoint que devuelve todos los productos en JSON"""
    productos = ProductoService.obtener_todos()
    
    productos_json = [
        {
            'id': p.id,
            'sku': p.sku,
            'nombre': p.nombre,
            'precio_pieza': float(p.precio_pieza),
            'precio_paquete': float(p.precio_paquete) if p.precio_paquete else None,
            'cantidad_paquete': p.cantidad_paquete,
            'stock_actual': p.stock_actual,
        }
        for p in productos
    ]
    
    return JsonResponse({'productos': productos_json})


@login_required
def productos_bajo_stock(request):
    """Vista de productos con stock bajo"""
    # Obtener productos donde stock_actual es menor o igual a stock_minimo
    productos = Producto.objects.filter(
        activo=True,
        stock_actual__lte=F('stock_minimo')
    ).order_by('stock_actual')
    
    context = {
        'productos': productos,
        'titulo': 'Productos con Stock Bajo',
    }
    return render(request, 'productos/bajo_stock.html', context)


@login_required
@require_http_methods(["POST"])
def validar_stock(request):
    """Valida si hay stock disponible para un producto"""
    try:
        data = json.loads(request.body)
        producto_id = data.get('producto_id')
        cantidad = data.get('cantidad')
        
        if not producto_id or not cantidad:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        hay_stock = ProductoService.validar_stock_disponible(producto_id, cantidad)
        
        return JsonResponse({'disponible': hay_stock})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def agregar_nuevo(request):
    """Vista para agregar un nuevo producto"""
    categorias = CategoriaService.obtener_todas()
    
    context = {
        'categorias': categorias,
        'titulo': 'Agregar Nuevo Producto',
    }
    return render(request, 'agregar_nuevo.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def agregar_stock(request):
    """Vista para agregar stock a un producto existente"""
    if request.method == 'POST':
        # Manejar POST de agregar stock (JSON)
        try:
            data = json.loads(request.body)
            sku = data.get('sku', '').strip()
            cantidad = data.get('cantidad', 0)
            
            if not sku or cantidad <= 0:
                return JsonResponse({
                    'exito': False,
                    'error': 'SKU y cantidad requeridos'
                }, status=400)
            
            producto = ProductoService.obtener_por_sku(sku)
            if not producto:
                return JsonResponse({
                    'exito': False,
                    'error': f'Producto con SKU {sku} no encontrado'
                }, status=404)
            
            # Actualizar stock
            producto.stock_actual += cantidad
            producto.save()
            
            # Registrar movimiento de inventario
            MovimientoInventario.objects.create(
                producto=producto,
                tipo_movimiento='entrada',
                cantidad=cantidad,
                referencia=f'Entrada manual - SKU {sku}',
                usuario=request.user
            )
            
            # Registrar en bitácora
            UsuarioService.registrar_acceso(
                usuario=request.user,
                accion='inventario',
                descripcion=f'Agregado stock: {producto.nombre} (+{cantidad}) = {producto.stock_actual}'
            )
            
            return JsonResponse({
                'exito': True,
                'nuevo_stock': producto.stock_actual,
                'mensaje': f'Stock actualizado para {producto.nombre}'
            })
        
        except json.JSONDecodeError:
            return JsonResponse({
                'exito': False,
                'error': 'Datos JSON inválidos'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'exito': False,
                'error': f'Error actualizando stock: {str(e)}'
            }, status=500)
    
    else:
        # GET - mostrar página
        productos = ProductoService.obtener_todos()
        
        context = {
            'productos': productos,
            'titulo': 'Agregar Stock',
        }
        return render(request, 'agregar_existente.html', context)




@login_required
@require_http_methods(["POST"])
@csrf_protect
def crear_categoria(request):
    """Crear una nueva categoría"""
    try:
        # Soportar JSON y form-data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        
        nombre = data.get('nombre', '').strip()
        descripcion = data.get('descripcion', '').strip()
        
        if not nombre:
            return JsonResponse({
                'exito': False,
                'error': 'El nombre de la categoría es obligatorio'
            }, status=400)
        
        # Validar que no exista
        if Categoria.objects.filter(nombre__iexact=nombre).exists():
            return JsonResponse({
                'exito': False,
                'error': f'La categoría "{nombre}" ya existe'
            }, status=400)
        
        # Crear categoría
        categoria = Categoria.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            activa=True
        )
        
        # Registrar en bitácora
        UsuarioService.registrar_acceso(
            usuario=request.user,
            accion='crear',
            descripcion=f'Nueva categoría: {nombre}'
        )
        
        return JsonResponse({
            'exito': True,
            'categoria_id': categoria.id,
            'categoria_nombre': categoria.nombre,
            'mensaje': f'✓ Categoría "{nombre}" creada'
        })
    
    except Exception as e:
        return JsonResponse({
            'exito': False,
            'error': f'Error creando categoría: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_protect
def crear_producto(request):
    """Crear un nuevo producto"""
    try:
        # Soportar JSON y form-data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        
        # Validar datos requeridos
        # Soportar tanto 'precio_costo'/'precio_venta' como 'precio_pieza'/'precio_paquete'
        sku = data.get('sku', '').strip()
        nombre = data.get('nombre', '').strip()
        precio_pieza = data.get('precio_pieza') or data.get('precio_venta')
        stock = int(data.get('stock', data.get('stock_actual', 0)) or 0)
        stock_minimo = data.get('stock_minimo')
        if stock_minimo is None or stock_minimo == '':
            stock_minimo = 5
        else:
            stock_minimo = int(stock_minimo)
        categoria_id = data.get('categoria_id') or data.get('categoria')
        precio_paquete = data.get('precio_paquete') or data.get('precio_costo')
        cantidad_paquete = data.get('cantidad_paquete', 1)
        
        if not all([sku, nombre, precio_pieza, categoria_id]):
            return JsonResponse({
                'exito': False,
                'error': 'Faltan campos obligatorios'
            }, status=400)
        
        # Validar que SKU sea único
        if Producto.objects.filter(sku=sku).exists():
            return JsonResponse({
                'exito': False,
                'error': f'El SKU {sku} ya existe'
            }, status=400)
        
        # Crear producto
        categoria = Categoria.objects.get(id=categoria_id)
        producto = Producto.objects.create(
            sku=sku,
            nombre=nombre,
            precio_pieza=precio_pieza,
            stock_actual=stock,
            stock_minimo=stock_minimo,
            categoria=categoria,
            precio_paquete=precio_paquete,
            cantidad_paquete=cantidad_paquete if precio_paquete else 1,
            activo=True
        )
        
        # Si hay stock inicial, registrar como movimiento de inventario
        if stock > 0:
            MovimientoInventario.objects.create(
                producto=producto,
                tipo_movimiento='entrada',
                cantidad=stock,
                referencia=f'Producto nuevo - Stock inicial',
                usuario=request.user
            )
        
        # Registrar en bitácora
        UsuarioService.registrar_acceso(
            usuario=request.user,
            accion='inventario',
            descripcion=f'Producto nuevo: {nombre} (SKU: {sku}) - Stock inicial: {stock}'
        )
        
        return JsonResponse({
            'exito': True,
            'producto_id': producto.id,
            'sku': producto.sku,
            'nombre': producto.nombre,
            'mensaje': f'Producto {nombre} creado exitosamente'
        })
    
    except Categoria.DoesNotExist:
        return JsonResponse({
            'exito': False,
            'error': 'Categoría no encontrada'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'exito': False,
            'error': f'Error creando producto: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
@login_required
def editar_precios(request):
    """Vista para editar precios de productos"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            producto_id = data.get('producto_id')
            precio_pieza = data.get('precio_pieza')
            precio_paquete = data.get('precio_paquete')
            
            if not producto_id or precio_pieza is None:
                return JsonResponse({
                    'exito': False,
                    'error': 'Producto y precio de pieza son requeridos'
                }, status=400)
            
            producto = get_object_or_404(Producto, id=producto_id)
            
            # Guardar precios antiguos para la bitácora
            precio_pieza_anterior = producto.precio_pieza
            precio_paquete_anterior = producto.precio_paquete
            
            # Actualizar precios
            producto.precio_pieza = precio_pieza
            if precio_paquete is not None and precio_paquete > 0:
                producto.precio_paquete = precio_paquete
            producto.save()
            
            # Registrar en bitácora
            UsuarioService.registrar_acceso(
                usuario=request.user,
                accion='precio',
                descripcion=f'Precios editados: {producto.nombre} | Pieza: ${precio_pieza_anterior} → ${precio_pieza}'
            )
            
            return JsonResponse({
                'exito': True,
                'mensaje': f'Precio de {producto.nombre} actualizado'
            })
        
        except json.JSONDecodeError:
            return JsonResponse({
                'exito': False,
                'error': 'Datos JSON inválidos'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'exito': False,
                'error': f'Error actualizando precio: {str(e)}'
            }, status=500)
    
    else:
        # GET - mostrar página
        productos = ProductoService.obtener_todos()
        
        context = {
            'productos': productos,
            'titulo': 'Editar Precios',
        }
        return render(request, 'productos/editar_precios.html', context)


# ==================== VISTAS ADMIN ====================

from usuarios.decorators import admin_required
from datetime import date


@admin_required
def admin_dashboard(request):
    """Dashboard principal para administradores"""
    from reportes.services import ReporteService
    from usuarios.models import PerfilUsuario
    
    hoy = date.today()
    
    # Estadísticas de productos
    total_productos = Producto.objects.filter(activo=True).count()
    productos_bajo_stock = Producto.objects.filter(activo=True, stock_actual__lte=F('stock_minimo')).count()
    sin_stock = Producto.objects.filter(activo=True, stock_actual=0).count()
    
    # Usuarios activos
    usuarios_activos = PerfilUsuario.objects.filter(activo=True).count()
    
    # Resumen de ventas hoy
    resumen = ReporteService.resumen_diario(hoy)
    
    context = {
        'hoy': hoy,
        'total_productos': total_productos,
        'productos_bajo_stock': productos_bajo_stock,
        'sin_stock': sin_stock,
        'usuarios_activos': usuarios_activos,
        'resumen': resumen,
    }
    return render(request, 'admin/dashboard.html', context)


@admin_required
def admin_productos(request):
    """Panel de administrador - Listado de productos"""
    productos = Producto.objects.all().order_by('nombre')
    inactivos = Producto.objects.filter(activo=False).count()
    categorias = Categoria.objects.all()
    
    context = {
        'productos': productos,
        'inactivos': inactivos,
        'categorias': categorias,
        'titulo': 'Panel de Administrador - Productos',
    }
    return render(request, 'admin/productos.html', context)


@admin_required
def admin_editar_producto(request, producto_id):
    """Editar un producto específico"""
    producto = get_object_or_404(Producto, id=producto_id)
    categorias = Categoria.objects.all()
    
    if request.method == 'POST':
        # Actualizar producto
        nombre_anterior = producto.nombre
        
        producto.nombre = request.POST.get('nombre', producto.nombre)
        producto.sku = request.POST.get('sku', producto.sku)
        producto.descripcion = request.POST.get('descripcion', producto.descripcion)
        producto.categoria_id = request.POST.get('categoria', producto.categoria_id)
        producto.precio_pieza = request.POST.get('precio_pieza', producto.precio_pieza)
        producto.precio_paquete = request.POST.get('precio_paquete', producto.precio_paquete) or None
        producto.cantidad_paquete = request.POST.get('cantidad_paquete', producto.cantidad_paquete)
        producto.stock_minimo = request.POST.get('stock_minimo', producto.stock_minimo)
        producto.stock_actual = request.POST.get('stock_actual', producto.stock_actual)
        producto.activo = request.POST.get('activo') == 'on'
        
        producto.save()
        
        # Registrar en bitácora
        UsuarioService.registrar_acceso(
            usuario=request.user,
            accion='editar',
            descripcion=f'Producto editado: {nombre_anterior} → {producto.nombre}'
        )
        
        messages = []
        messages.append(('success', f'✅ Producto {producto.nombre} actualizado correctamente'))
        
        return render(request, 'admin/editar_producto.html', {
            'producto': producto,
            'categorias': categorias,
            'messages': messages,
        })
    
    context = {
        'producto': producto,
        'categorias': categorias,
        'titulo': f'Editar - {producto.nombre}',
    }
    return render(request, 'admin/editar_producto.html', context)


@admin_required
def admin_crear_producto(request):
    """Crear un nuevo producto desde admin o reutilizar existente"""
    categorias = Categoria.objects.all()
    productos_existentes = Producto.objects.all().order_by('nombre')
    
    if request.method == 'POST':
        modo = request.POST.get('modo', 'nuevo')  # 'nuevo' o 'existente'
        
        if modo == 'existente':
            # Reutilizar producto existente - apenas agregar stock
            producto_id = request.POST.get('producto_existente')
            try:
                producto = Producto.objects.get(id=producto_id)
                stock_agregar = int(request.POST.get('stock_agregar', 0))
                
                if stock_agregar > 0:
                    # Registrar movimiento de inventario
                    stock_anterior = producto.stock_actual
                    producto.stock_actual += stock_agregar
                    producto.save()
                    
                    MovimientoInventario.objects.create(
                        producto=producto,
                        tipo='entrada',
                        cantidad=stock_agregar,
                        razon='Reabastecimiento desde admin'
                    )
                    
                    # Registrar en bitácora
                    UsuarioService.registrar_acceso(
                        usuario=request.user,
                        accion='reabastecimiento',
                        descripcion=f'Reabastecimiento: {producto.nombre} (+{stock_agregar} unidades, {stock_anterior} → {producto.stock_actual})'
                    )
                    
                    messages_list = [('success', f'✅ Stock de {producto.nombre} actualizado (+{stock_agregar} unidades)')]
                    return redirect('productos:admin_editar', producto_id=producto.id)
            except Producto.DoesNotExist:
                messages_list = [('error', '❌ Producto no encontrado')]
        
        else:
            # Crear nuevo producto
            sku = request.POST.get('sku', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            
            # Validar que SKU sea único
            if Producto.objects.filter(sku=sku).exists():
                messages_list = [('error', f'❌ El SKU {sku} ya existe')]
            else:
                # Crear producto
                producto = Producto.objects.create(
                    sku=sku,
                    nombre=nombre,
                    descripcion=request.POST.get('descripcion', ''),
                    categoria_id=request.POST.get('categoria'),
                    precio_pieza=request.POST.get('precio_pieza', 0),
                    precio_paquete=request.POST.get('precio_paquete') or None,
                    cantidad_paquete=request.POST.get('cantidad_paquete', 1),
                    stock_actual=request.POST.get('stock_actual', 0),
                    stock_minimo=request.POST.get('stock_minimo', 5),
                    activo=True
                )
                
                # Registrar movimiento de inventario si hay stock inicial
                stock_inicial = int(request.POST.get('stock_actual', 0))
                if stock_inicial > 0:
                    MovimientoInventario.objects.create(
                        producto=producto,
                        tipo='entrada',
                        cantidad=stock_inicial,
                        razon='Stock inicial al crear producto'
                    )
                
                # Registrar en bitácora
                UsuarioService.registrar_acceso(
                    usuario=request.user,
                    accion='crear',
                    descripcion=f'Nuevo producto: {nombre} (SKU: {sku}, stock inicial: {stock_inicial})'
                )
                
                messages_list = [('success', f'✅ Producto {nombre} creado correctamente')]
                return redirect('productos:admin_editar', producto_id=producto.id)
    
    context = {
        'categorias': categorias,
        'productos_existentes': productos_existentes,
        'titulo': 'Crear Nuevo Producto',
    }
    return render(request, 'admin/crear_producto.html', context)


@admin_required
def admin_eliminar_producto(request, producto_id):
    """Activar/Desactivar un producto (toggle)"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        nombre = producto.nombre
        # Toggle: si está activo, lo desactiva. Si está inactivo, lo activa
        producto.activo = not producto.activo
        nuevo_estado = "activado" if producto.activo else "desactivado"
        producto.save()
        
        # Registrar en bitácora
        UsuarioService.registrar_acceso(
            usuario=request.user,
            accion='editar',
            descripcion=f'Producto {nuevo_estado}: {nombre}'
        )
        
        messages.success(request, f'✅ Producto {nuevo_estado} correctamente')
        return redirect('admin_productos')
    
    context = {
        'producto': producto,
        'titulo': f'Eliminar - {producto.nombre}',
    }
    return render(request, 'admin/eliminar_producto.html', context)


# ==================== GESTIÓN DE PRODUCTOS ====================

from usuarios.permisos import requiere_grupo

@requiere_grupo('Admin', 'Gerente', 'Supervisor')
@login_required
def gestionar_productos(request):
    """Redireccionar a inventario_general (vista consolidada)"""
    return redirect('productos:inventario_general')


@requiere_grupo('Admin', 'Gerente', 'Supervisor')
@login_required
@require_http_methods(["GET", "POST"])
def editar_producto(request, producto_id):
    """Editar un producto existente"""
    producto = get_object_or_404(Producto, id=producto_id)
    categorias = Categoria.objects.filter(activa=True).order_by('nombre')
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            sku = request.POST.get('sku', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            categoria_id = request.POST.get('categoria')
            precio_pieza = request.POST.get('precio_pieza')
            precio_paquete = request.POST.get('precio_paquete')
            cantidad_paquete = request.POST.get('cantidad_paquete', 1)
            stock_actual = request.POST.get('stock_actual')
            stock_minimo = request.POST.get('stock_minimo', 5)
            
            # Validar datos
            if not all([sku, nombre, categoria_id, precio_pieza, stock_actual]):
                messages.error(request, '❌ Por favor completa todos los campos obligatorios')
                return redirect('productos:editar_producto', producto_id=producto.id)
            
            # Validar que SKU sea único (excepto para el mismo producto)
            if Producto.objects.filter(sku=sku).exclude(id=producto.id).exists():
                messages.error(request, f'❌ Ya existe un producto con el SKU "{sku}"')
                return redirect('productos:editar_producto', producto_id=producto.id)
            
            # Actualizar producto
            producto.sku = sku
            producto.nombre = nombre
            producto.descripcion = descripcion
            producto.categoria_id = categoria_id
            producto.precio_pieza = precio_pieza
            producto.precio_paquete = precio_paquete if precio_paquete else None
            producto.cantidad_paquete = int(cantidad_paquete)
            producto.stock_actual = int(stock_actual)
            producto.stock_minimo = int(stock_minimo)
            producto.save()
            
            # Registrar en bitácora
            UsuarioService.registrar_acceso(
                usuario=request.user,
                accion='editar',
                descripcion=f'Producto actualizado: {nombre}'
            )
            
            messages.success(request, f'✅ Producto "{nombre}" actualizado correctamente')
            return redirect('productos:inventario_general')
        
        except Exception as e:
            messages.error(request, f'❌ Error al actualizar producto: {str(e)}')
            return redirect('productos:editar_producto', producto_id=producto.id)
    
    context = {
        'producto': producto,
        'categorias': categorias,
        'titulo': f'Editar - {producto.nombre}',
    }
    return render(request, 'productos/editar.html', context)


@requiere_grupo('Admin', 'Gerente', 'Supervisor')
@login_required
@require_http_methods(["POST"])
def eliminar_producto(request, producto_id):
    """Eliminar un producto completamente"""
    producto = get_object_or_404(Producto, id=producto_id)
    nombre_producto = producto.nombre
    sku = producto.sku
    
    try:
        # Registrar en bitácora antes de eliminar
        UsuarioService.registrar_acceso(
            usuario=request.user,
            accion='eliminar',
            descripcion=f'Producto eliminado: {nombre_producto} (SKU: {sku})'
        )
        
        # Eliminar producto
        producto.delete()
        
        messages.success(request, f'✅ Producto "{nombre_producto}" eliminado correctamente')
    except Exception as e:
        messages.error(request, f'❌ Error al eliminar producto: {str(e)}')
    
    return redirect('productos:inventario_general')
