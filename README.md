# Sistema de Gestión Hotelera (SGH)

Sistema completo de gestión hotelera desarrollado con **Python** y **Flet v0.80.5**.

## Características Principales

### Gestión de Habitaciones
- Grid visual de 39 habitaciones organizadas por tipo:
  - 15 Habitaciones Sencillas
  - 15 Habitaciones Dobles
  - 5 Suites
  - 4 Suites Presidenciales
- Estados visuales con colores:
  - 🟢 Verde: Libre
  - 🔴 Rojo: Ocupada
  - 🟡 Amarillo: Reservada
  - ⚪ Gris: En Aseo
  - 🟠 Naranja: En Mantenimiento

### Check-in / Check-out
- Búsqueda de huéspedes por documento
- Registro de nuevos huéspedes
- Pre-facturación automática
- Cálculo de noches de estadía
- Gestión de acompañantes

### Sistema de Pagos Multimoneda
- Soporte para múltiples métodos de pago:
  - Efectivo (USD/BS)
  - Pago Móvil
  - Transferencia bancaria
  - Tarjeta de crédito/débito
  - Zelle
  - Binance
- Conversión automática USD ↔ BS
- Validación de referencias para pagos electrónicos

### Gestión de Saldos y Deudas
- Saldo a favor de huéspedes
- Deudas pendientes
- Aplicación automática en check-in
- Historial de transacciones

### Control de Turnos
- Apertura de caja con conteo inicial
- Cierre de caja con arqueo
- Seguimiento de movimientos por turno
- Reporte de ventas y pagos

### Gestión de Usuarios y Seguridad
- Roles: Admin, Gerente, Recepcionista
- Control de acceso por contraseña
- Registro de último acceso
- Gestión de permisos

## Requisitos del Sistema

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## Instalación

### 1. Clonar o descargar el proyecto

```bash
cd /mnt/okcomputer/output/sgh
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv
```

### 3. Activar entorno virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

## Uso

### Iniciar la aplicación

```bash
python main.py
```

### Credenciales por defecto

- **Usuario:** admin
- **Contraseña:** admin123

> ⚠️ **Importante:** Cambie la contraseña por defecto después del primer inicio de sesión.

## Estructura del Proyecto

```
sgh/
├── main.py                 # Punto de entrada principal
├── requirements.txt        # Dependencias del proyecto
├── README.md              # Este archivo
├── database/
│   ├── __init__.py
│   └── connection.py      # Conexión y esquema de SQLite
├── models/
│   ├── __init__.py
│   ├── huesped.py         # Modelo de huéspedes
│   ├── habitacion.py      # Modelo de habitaciones
│   ├── registro.py        # Modelo de check-ins/outs
│   ├── transaccion.py     # Modelo de pagos
│   ├── usuario.py         # Modelo de usuarios
│   ├── turno.py           # Modelo de turnos
│   └── configuracion.py   # Modelo de configuración
├── views/
│   ├── __init__.py
│   ├── login_view.py      # Vista de login
│   ├── dashboard_view.py  # Dashboard principal
│   ├── checkin_view.py    # Vista de check-in
│   ├── checkout_view.py   # Vista de check-out
│   ├── huespedes_view.py  # Gestión de huéspedes
│   ├── turno_view.py      # Gestión de turnos
│   └── config_view.py     # Configuración del sistema
├── components/
│   ├── __init__.py
│   ├── room_card.py       # Tarjeta de habitación
│   └── payment_form.py    # Formulario de pagos
└── utils/
    ├── __init__.py
    ├── helpers.py         # Funciones auxiliares
    └── session.py         # Gestión de sesión
```

## Flujo de Trabajo

### 1. Inicio de Sesión
- Ingrese con las credenciales de administrador
- El sistema verificará si hay un turno abierto

### 2. Apertura de Turno
- Si no hay turno abierto, el sistema solicitará abrir uno
- Ingrese la tasa de cambio actual
- Registre el efectivo inicial en caja

### 3. Check-in de Huésped
- Haga clic en una habitación libre (verde)
- Busque el huésped por documento o cree uno nuevo
- Seleccione la fecha de salida
- Revise la pre-factura (incluye deudas/saldos anteriores)
- Registre el pago (puede ser multimoneda)
- Complete el check-in

### 4. Check-out de Huésped
- Haga clic en una habitación ocupada (roja)
- Revise el detalle de cargos
- Si hay saldo pendiente, registre el pago
- Si hay saldo a favor, se transferirá al huésped
- Complete el check-out

### 5. Cierre de Turno
- Acceda a "Turno" desde el menú
- Verifique los movimientos del día
- Cuente el efectivo en caja
- Registre la tasa de cierre
- Complete el cierre

## Configuración

### Datos del Hotel
- Nombre del hotel
- Dirección
- Teléfono
- Email
- RIF

### Configuración Financiera
- Tasa de cambio USD/BS (actualizable en tiempo real)

### Gestión de Usuarios
- Crear/editar usuarios
- Asignar roles
- Cambiar contraseñas
- Activar/desactivar usuarios

### Gestión de Habitaciones
- Editar tipos de habitaciones
- Modificar precios
- Cambiar capacidad
- Actualizar descripciones

## Base de Datos

El sistema utiliza **SQLite** como base de datos local. El archivo `hotel.db` se creará automáticamente en el directorio raíz del proyecto.

### Tablas principales:
- `Huespedes`: Información de huéspedes y saldos
- `Habitaciones`: Catálogo de habitaciones
- `Registros`: Check-ins y check-outs
- `Transacciones`: Pagos y cargos
- `Turnos`: Aperturas y cierres de caja
- `Usuarios`: Usuarios del sistema
- `Configuracion`: Parámetros del sistema

## Notas Técnicas

### Versión de Flet
Este sistema está desarrollado y probado con **Flet v0.80.5**. Se recomienda usar esta versión específica para garantizar la compatibilidad.

### Escalabilidad
El código está modularizado para facilitar:
- Migración a PostgreSQL para entornos multiusuario
- Integración con sistemas de facturación
- Desarrollo de APIs REST
- Despliegue en la nube

## Soporte

Para reportar problemas o solicitar características adicionales, contacte al administrador del sistema.

## Licencia

Este software es propiedad del hotel. Uso exclusivo para operaciones internas.

---

**Versión:** 1.0.0  
**Fecha de desarrollo:** 2024  
**Tecnología:** Python + Flet
