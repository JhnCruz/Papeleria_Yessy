# 🛒 Sistema POS Papelería

Sistema de Punto de Venta (POS) para papelerías con control de inventario, registro de ventas y corte de caja.

## Requisitos

- Python 3.10+
- pip (gestor de paquetes)

## Instalación

### 1. Crear entorno virtual (si no está creado)
```bash
python3 -m venv venv
```

### 2. Activar entorno virtual

**En macOS/Linux:**
```bash
source venv/bin/activate
```

**En Windows:**
```bash
venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

## Configuración

### 1. Aplicar migraciones (crear base de datos)
```bash
python manage.py migrate
```

### 2. Crear superusuario
```bash
python manage.py createsuperuser
```

Sigue las instrucciones para crear un usuario administrador.

## Ejecutar el servidor

```bash
python manage.py runserver
```

El sistema estará disponible en:
- **Aplicación**: http://localhost:8000
- **Panel Admin**: http://localhost:8000/admin

**Credenciales Admin:**
- Usuario: `admin`
- Contraseña: `admin123`

## Estructura del Proyecto

```
Papeleria/
├── manage.py                 # Script de gestión de Django
├── requirements.txt          # Dependencias del proyecto
├── db.sqlite3               # Base de datos SQLite
│
├── core/                     # Configuración principal
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── productos/                # App de productos
│   ├── models.py            # Modelos: Producto, Categoria
│   ├── services.py          # Lógica de negocio
│   ├── views.py             # Vistas
│   ├── admin.py             # Admin Django
│   └── migrations/
│
├── ventas/                   # App de ventas
│   ├── models.py            # Modelos: Venta, DetalleVenta
│   ├── services.py          # Lógica de ventas
│   ├── views.py             # Vistas
│   ├── admin.py             # Admin Django
│   └── migrations/
│
├── inventario/              # App de inventario
│   ├── models.py            # Modelos: MovimientoInventario
│   ├── services.py          # Lógica de inventario
│   ├── views.py             # Vistas
│   ├── admin.py             # Admin Django
│   └── migrations/
│
├── caja/                     # App de caja
│   ├── models.py            # Modelos: CorteCaja
│   ├── services.py          # Lógica de caja
│   ├── views.py             # Vistas
│   ├── admin.py             # Admin Django
│   └── migrations/
│
├── reportes/                 # App de reportes
│   ├── models.py            # Configuración de reportes
│   ├── services.py          # Generación de reportes
│   ├── views.py             # Vistas de reportes
│   └── migrations/
│
├── usuarios/                 # App de usuarios
│   ├── models.py            # PerfilUsuario, BitacoraAcceso
│   ├── services.py          # Lógica de usuarios
│   ├── views.py             # Vistas de usuarios
│   ├── admin.py             # Admin Django
│   └── migrations/
│
├── templates/                # Templates HTML
│   ├── index.html
│   ├── venta.html
│   ├── agregar_nuevo.html
│   ├── agregar_existente.html
│   ├── corte_caja.html
│   ├── reportes.html
│   ├── resumen.html
│   └── base.html
│
└── static/                   # Archivos estáticos (CSS, JS)
    ├── css/
    ├── js/
    └── images/
```

## Características Implementadas ✅

### Capa de Datos (Models)
- ✅ Producto (SKU, precios, stock)
- ✅ Categoría de productos
- ✅ Venta (con detalles de artículos)
- ✅ Movimiento de Inventario
- ✅ Corte de Caja
- ✅ Usuario y Perfil
- ✅ Bitácora de Accesos

### Capa de Lógica de Negocio (Services)
- ✅ Servicio de Productos (crear, buscar, validar stock)
- ✅ Servicio de Ventas (crear venta, cancelar venta)
- ✅ Servicio de Inventario (movimientos, ajustes)
- ✅ Servicio de Caja (corte diario)
- ✅ Servicio de Reportes (análisis de datos)
- ✅ Servicio de Usuarios (gestión de roles)

### Admin Django
- ✅ Gestión de productos y categorías
- ✅ Visualización de ventas
- ✅ Movimientos de inventario
- ✅ Cortes de caja
- ✅ Usuarios y perfiles
- ✅ Bitácora de accesos

## Próximos Pasos

1. **Crear Vistas (Views)**: Implementar las vistas para cada funcionalidad
2. **Configurar URLs**: Mapear rutas de la aplicación
3. **Integrar Templates**: Conectar las plantillas HTML con las vistas
4. **API REST**: Crear endpoints para operaciones del POS
5. **Autenticación**: Implementar login y control de permisos
6. **Testing**: Escribir tests unitarios e integración

## Notas de Desarrollo

- La base de datos usa SQLite para desarrollo local
- El sistema funciona 100% offline (sin necesidad de internet)
- Se puede migrar a PostgreSQL para producción sin cambios en el código
- El código sigue el patrón MVC + Arquitectura en Capas

## Soporte

Para más información sobre Django, consulta:
- [Documentación Oficial Django](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
# Papeleria_Yessy
# Papeleria_Yessy
