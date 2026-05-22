#!/usr/bin/env python
"""Debug CorteCaja"""
import os
import sys
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from caja.models import CorteCaja

usuario = User.objects.get(id=1)

try:
    # Probar con diferentes turnos
    for turno in [1, 2]:
        print(f"\nIntentando crear corte con turno={turno}")
        try:
            corte = CorteCaja.objects.create(
                turno=turno,
                total_ventas=Decimal('500.00'),
                total_efectivo=Decimal('350.00'),
                total_transferencias=Decimal('150.00'),
                monto_efectivo_ingresado=Decimal('350.00'),
                usuario=usuario,
                notas=f'Test turno {turno}'
            )
            print(f"✅ Corte creado: {corte.id}")
        except Exception as e:
            print(f"❌ Error: {e}")
            
except Exception as e:
    print(f"❌ Error general: {e}")
    import traceback
    traceback.print_exc()
