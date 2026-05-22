#!/usr/bin/env python
"""Debug Movimientos Inventario"""
import os
import sys
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from productos.models import Producto
from inventario.services import InventarioService

productos = list(Producto.objects.all().values_list('id', flat=True)[:3])
print(f"Productos: {productos}\n")

for prod_id in productos:
    try:
        print(f"\n=== Registrando movimiento para producto {prod_id} ===")
        success, result = InventarioService.registrar_movimiento(
            producto_id=prod_id,
            cantidad=5,
            tipo_movimiento='compra',
            referencia='DEBUG-TEST',
            usuario_id=1,
            descripcion='Test debug'
        )
        print(f"Success: {success}")
        print(f"Result: {result}")
        
        if success:
            print(f"✅ Movimiento registrado")
        else:
            print(f"❌ Error: {result}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
