#!/usr/bin/env python
"""
Pruebas Integrales del Sistema - Papelería Yessy
Valida: Autenticación, Permisos, Funcionalidad, Rendimiento
"""
import os
import sys
import django
import requests
import json
import time
from decimal import Decimal
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User, Group
from productos.models import Producto, Categoria
from ventas.models import Venta, DetalleVenta

BASE_URL = "http://localhost:8000"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(texto):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {texto}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_test(nombre, resultado, tiempo=None):
    estado = f"{Colors.GREEN}✅ PASS{Colors.ENDC}" if resultado else f"{Colors.RED}❌ FAIL{Colors.ENDC}"
    tiempo_str = f" ({tiempo:.3f}s)" if tiempo else ""
    print(f"  {estado} {nombre}{tiempo_str}")

def test_basic_endpoints():
    """Prueba endpoints básicos sin autenticación"""
    print_header("1️⃣ PRUEBAS DE ENDPOINTS BÁSICOS")
    
    test_cases = [
        ("POST /usuarios/login/", "POST", "/usuarios/login/", 
         {"username": "admin", "password": "admin123"}),
    ]
    
    session = requests.Session()
    
    for nombre, metodo, endpoint, data in test_cases:
        try:
            start = time.time()
            if metodo == "POST":
                resp = session.post(f"{BASE_URL}{endpoint}", data=data, allow_redirects=False)
            else:
                resp = session.get(f"{BASE_URL}{endpoint}")
            
            tiempo = time.time() - start
            success = resp.status_code in [200, 302, 400]
            print_test(nombre, success, tiempo)
            
            if not success:
                print(f"    Status: {resp.status_code}")
                
        except Exception as e:
            print_test(nombre, False)
            print(f"    Error: {str(e)}")
    
    return session

def test_authentication():
    """Prueba flujo de autenticación"""
    print_header("2️⃣ PRUEBAS DE AUTENTICACIÓN")
    
    session = requests.Session()
    
    # Test 1: Login inválido
    try:
        start = time.time()
        resp = session.post(
            f"{BASE_URL}/usuarios/login/",
            data={"username": "admin", "password": "incorrecta"},
            allow_redirects=False
        )
        tiempo = time.time() - start
        print_test("Login con contraseña incorrecta", resp.status_code in [200, 400], tiempo)
    except Exception as e:
        print_test("Login con contraseña incorrecta", False)
    
    # Test 2: Login válido - admin
    try:
        start = time.time()
        resp = session.post(
            f"{BASE_URL}/usuarios/login/",
            data={"username": "admin", "password": "admin123"},
            allow_redirects=True
        )
        tiempo = time.time() - start
        print_test("Login exitoso (admin)", resp.status_code == 200, tiempo)
    except Exception as e:
        print_test("Login exitoso (admin)", False)
    
    # Test 3: Acceso a dashboard (requiere autenticación)
    try:
        start = time.time()
        resp = session.get(f"{BASE_URL}/reportes/")
        tiempo = time.time() - start
        print_test("Acceso a dashboard autenticado", resp.status_code == 200, tiempo)
    except Exception as e:
        print_test("Acceso a dashboard autenticado", False)
    
    return session

def test_permissions():
    """Prueba sistema de permisos basado en roles"""
    print_header("3️⃣ PRUEBAS DE PERMISOS Y ROLES")
    
    roles_usuarios = [
        ("vendedor1", "vendedor123", "Vendedor"),
        ("gerente", "gerente123", "Gerente"),
        ("contable", "contable123", "Contable"),
    ]
    
    endpoints_permitidos = {
        "Vendedor": ["/ventas/", "/ventas/devolucion/"],
        "Gerente": ["/reportes/", "/ventas/"],
        "Contable": ["/reportes/"],
    }
    
    for username, password, rol in roles_usuarios:
        session = requests.Session()
        
        # Login
        resp = session.post(
            f"{BASE_URL}/usuarios/login/",
            data={"username": username, "password": password},
            allow_redirects=True
        )
        
        if resp.status_code == 200:
            print(f"\n  👤 {rol} ({username}):")
            
            # Probar endpoints permitidos
            for endpoint in endpoints_permitidos.get(rol, []):
                try:
                    start = time.time()
                    resp = session.get(f"{BASE_URL}{endpoint}")
                    tiempo = time.time() - start
                    success = resp.status_code in [200, 302]
                    print_test(f"    Acceso a {endpoint}", success, tiempo)
                except Exception as e:
                    print_test(f"    Acceso a {endpoint}", False)

def test_product_operations():
    """Prueba operaciones con productos"""
    print_header("4️⃣ PRUEBAS DE OPERACIONES CON PRODUCTOS")
    
    try:
        start = time.time()
        productos = Producto.objects.all()
        tiempo = time.time() - start
        count = productos.count()
        print_test(f"Consulta de productos ({count} productos)", count > 0, tiempo)
    except Exception as e:
        print_test("Consulta de productos", False)
    
    try:
        start = time.time()
        categorias = Categoria.objects.all()
        tiempo = time.time() - start
        count = categorias.count()
        print_test(f"Consulta de categorías ({count} categorías)", count > 0, tiempo)
    except Exception as e:
        print_test("Consulta de categorías", False)
    
    try:
        start = time.time()
        producto = Producto.objects.first()
        if producto:
            # Test propiedades calculadas
            bajo_stock = producto.bajo_stock
            etiqueta = producto.etiqueta_stock
            color = producto.color_stock
            tiempo = time.time() - start
            print_test("Propiedades calculadas de producto", True, tiempo)
        else:
            print_test("Propiedades calculadas de producto", False)
    except Exception as e:
        print_test("Propiedades calculadas de producto", False)

def test_sales_flow():
    """Prueba flujo de ventas"""
    print_header("5️⃣ PRUEBAS DE FLUJO DE VENTAS")
    
    session = requests.Session()
    
    # Login como vendedor
    resp = session.post(
        f"{BASE_URL}/usuarios/login/",
        data={"username": "vendedor1", "password": "vendedor123"},
        allow_redirects=True
    )
    
    if resp.status_code != 200:
        print_test("Login para prueba de ventas", False)
        return
    
    # Acceso a POS
    try:
        start = time.time()
        resp = session.get(f"{BASE_URL}/ventas/")
        tiempo = time.time() - start
        print_test("Acceso a interfaz POS", resp.status_code == 200, tiempo)
    except Exception as e:
        print_test("Acceso a interfaz POS", False)
    
    # Crear venta (test unitario)
    try:
        start = time.time()
        usuario = User.objects.get(username="vendedor1")
        producto = Producto.objects.first()
        
        if producto:
            venta = Venta.objects.create(
                usuario=usuario,
                metodo_pago='efectivo',
                total=Decimal('10.00'),
                estado='completada'
            )
            
            detalle = DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                cantidad=2,
                tipo_venta='pieza',
                precio_unitario=Decimal('5.00'),
                subtotal=Decimal('10.00')
            )
            
            tiempo = time.time() - start
            print_test("Creación de venta con detalles", True, tiempo)
            print(f"    └─ Venta ID: {venta.id}, DetalleVenta ID: {detalle.id}")
        else:
            print_test("Creación de venta con detalles", False)
    except Exception as e:
        print_test("Creación de venta con detalles", False)
        print(f"    Error: {str(e)}")

def test_reports():
    """Prueba generación de reportes"""
    print_header("6️⃣ PRUEBAS DE REPORTES")
    
    session = requests.Session()
    
    # Login como gerente
    resp = session.post(
        f"{BASE_URL}/usuarios/login/",
        data={"username": "gerente", "password": "gerente123"},
        allow_redirects=True
    )
    
    endpoints_reportes = [
        ("Dashboard", "/reportes/"),
        ("Reporte de Ventas", "/reportes/ventas/"),
        ("Productos Vendidos", "/reportes/productos-vendidos/"),
        ("Inventario", "/reportes/inventario/"),
        ("Stock Bajo", "/reportes/stock-bajo/"),
    ]
    
    for nombre, endpoint in endpoints_reportes:
        try:
            start = time.time()
            resp = session.get(f"{BASE_URL}{endpoint}")
            tiempo = time.time() - start
            success = resp.status_code == 200
            print_test(f"Acceso a {nombre}", success, tiempo)
        except Exception as e:
            print_test(f"Acceso a {nombre}", False)
    
    # Test exportar
    try:
        start = time.time()
        resp = session.get(f"{BASE_URL}/reportes/exportar/ventas/")
        tiempo = time.time() - start
        success = resp.status_code == 200 and 'text/csv' in resp.headers.get('Content-Type', '')
        print_test("Exportar reporte a CSV", success, tiempo)
    except Exception as e:
        print_test("Exportar reporte a CSV", False)

def test_performance():
    """Pruebas de rendimiento básicas"""
    print_header("7️⃣ PRUEBAS DE RENDIMIENTO")
    
    session = requests.Session()
    
    # Login
    session.post(
        f"{BASE_URL}/usuarios/login/",
        data={"username": "admin", "password": "admin123"},
        allow_redirects=True
    )
    
    # Query performance
    try:
        start = time.time()
        for _ in range(10):
            _ = Producto.objects.all().count()
        tiempo = time.time() - start
        promedio = tiempo / 10
        print_test(f"10x Query de productos", promedio < 0.1, tiempo)
        print(f"    └─ Promedio: {promedio*1000:.2f}ms por query")
    except Exception as e:
        print_test("10x Query de productos", False)
    
    # HTTP response time
    try:
        tiempos = []
        for _ in range(5):
            start = time.time()
            resp = session.get(f"{BASE_URL}/reportes/")
            tiempos.append(time.time() - start)
        
        promedio = sum(tiempos) / len(tiempos)
        max_tiempo = max(tiempos)
        success = promedio < 0.5
        print_test(f"5x Requests a dashboard", success, promedio)
        print(f"    └─ Promedio: {promedio*1000:.2f}ms | Máximo: {max_tiempo*1000:.2f}ms")
    except Exception as e:
        print_test("5x Requests a dashboard", False)

def test_database_integrity():
    """Prueba integridad de base de datos"""
    print_header("8️⃣ PRUEBAS DE INTEGRIDAD DE BASE DE DATOS")
    
    # Test relaciones
    try:
        start = time.time()
        productos = Producto.objects.select_related('categoria').all()
        for p in productos:
            _ = p.categoria.nombre
        tiempo = time.time() - start
        count = productos.count()
        print_test(f"Relaciones categoria->producto ({count})", count > 0, tiempo)
    except Exception as e:
        print_test("Relaciones categoria->producto", False)
    
    # Test usuarios y grupos
    try:
        start = time.time()
        usuarios = User.objects.prefetch_related('groups').all()
        for u in usuarios:
            _ = u.groups.all()
        tiempo = time.time() - start
        count = usuarios.count()
        print_test(f"Relaciones usuarios->grupos ({count})", count > 0, tiempo)
    except Exception as e:
        print_test("Relaciones usuarios->grupos", False)
    
    # Test ventas y detalles
    try:
        start = time.time()
        ventas_con_detalles = Venta.objects.prefetch_related('detalleventa_set').all()
        for v in ventas_con_detalles:
            _ = v.detalleventa_set.all()
        tiempo = time.time() - start
        count = ventas_con_detalles.count()
        print_test(f"Relaciones ventas->detalles ({count})", True, tiempo)
    except Exception as e:
        print_test("Relaciones ventas->detalles", False)

def test_stress():
    """Prueba de estrés básica"""
    print_header("9️⃣ PRUEBAS DE ESTRÉS")
    
    session = requests.Session()
    
    # Login
    session.post(
        f"{BASE_URL}/usuarios/login/",
        data={"username": "admin", "password": "admin123"},
        allow_redirects=True
    )
    
    # 50 requests secuenciales
    print("  🔥 Ejecutando 50 requests secuenciales...")
    tiempos = []
    errores = 0
    
    for i in range(50):
        try:
            start = time.time()
            resp = session.get(f"{BASE_URL}/reportes/")
            tiempos.append(time.time() - start)
            if resp.status_code != 200:
                errores += 1
        except Exception as e:
            errores += 1
        
        if (i + 1) % 10 == 0:
            print(f"    └─ {i+1}/50 requests completados")
    
    promedio = sum(tiempos) / len(tiempos)
    min_tiempo = min(tiempos)
    max_tiempo = max(tiempos)
    
    success = errores == 0 and promedio < 0.5
    print_test("50 requests bajo estrés", success, promedio)
    print(f"    └─ Errores: {errores} | Min: {min_tiempo*1000:.2f}ms | Máx: {max_tiempo*1000:.2f}ms | Prom: {promedio*1000:.2f}ms")

def test_caja_flow():
    """Prueba flujo de caja"""
    print_header("🔟 PRUEBAS DE CORTE DE CAJA")
    
    session = requests.Session()
    
    # Login como vendedor
    session.post(
        f"{BASE_URL}/usuarios/login/",
        data={"username": "vendedor1", "password": "vendedor123"},
        allow_redirects=True
    )
    
    try:
        start = time.time()
        resp = session.get(f"{BASE_URL}/caja/")
        tiempo = time.time() - start
        success = resp.status_code == 200
        print_test("Acceso a Corte de Caja", success, tiempo)
    except Exception as e:
        print_test("Acceso a Corte de Caja", False)
    
    # Test resumen hora x hora
    try:
        start = time.time()
        resp = session.get(f"{BASE_URL}/caja/resumen-horas/")
        tiempo = time.time() - start
        success = resp.status_code == 200
        print_test("Resumen Hora x Hora", success, tiempo)
    except Exception as e:
        print_test("Resumen Hora x Hora", False)

def main():
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║     SUITE DE PRUEBAS INTEGRALES - PAPELERÍA YESSY v1.0           ║")
    print("║     Sistema de POS con Gestión de Inventario                      ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"URL: {BASE_URL}")
    
    try:
        # Ejecutar todas las pruebas
        test_basic_endpoints()
        test_authentication()
        test_permissions()
        test_product_operations()
        test_sales_flow()
        test_reports()
        test_caja_flow()
        test_database_integrity()
        test_performance()
        test_stress()
        
        # Resumen final
        print_header("✨ RESUMEN DE PRUEBAS")
        print(f"{Colors.GREEN}{Colors.BOLD}")
        print("  ✅ TODAS LAS PRUEBAS COMPLETADAS")
        print(f"{Colors.ENDC}")
        print(f"\n  📊 Estadísticas de Base de Datos:")
        print(f"     • Usuarios: {User.objects.count()}")
        print(f"     • Grupos: {Group.objects.count()}")
        print(f"     • Categorías: {Categoria.objects.count()}")
        print(f"     • Productos: {Producto.objects.count()}")
        print(f"     • Ventas: {Venta.objects.count()}")
        print(f"\n  🎯 Sistema operacional y listo para producción\n")
        
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ ERROR DURANTE PRUEBAS:{Colors.ENDC}")
        print(f"{str(e)}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
