#!/usr/bin/env python
"""
Stress Test Debug - Para investigar los errores
"""
import os
import sys
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from productos.models import Producto
from ventas.models import Venta, DetalleVenta

# Test simple
usuario = User.objects.get(username='vendedor1')
productos = list(Producto.objects.all().values_list('id', flat=True)[:5])

print(f"Usuario: {usuario}")
print(f"Productos: {productos}\n")

try:
    venta = Venta.objects.create(
        usuario=usuario,
        metodo_pago='efectivo',
        estado='completada',
        monto_efectivo=Decimal('50.00'),
        referencia_transferencia='TEST'
    )
    print(f"✅ Venta creada: {venta.id}")
    
    # Agregar detalles
    producto = Producto.objects.get(id=productos[0])
    print(f"✅ Producto: {producto}")
    
    detalle = DetalleVenta.objects.create(
        venta=venta,
        producto=producto,
        cantidad=2,
        tipo_venta='pieza',
        precio_unitario=producto.precio_pieza,
        subtotal=Decimal('20.00')
    )
    print(f"✅ Detalle creado: {detalle.id}")
    
    venta.total = Decimal('20.00')
    venta.save()
    print(f"✅ Venta guardada")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
