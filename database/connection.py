"""
Módulo de conexión y gestión de la base de datos SQLite
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

# Ruta de la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'hotel.db')

class Database:
    """Clase singleton para gestionar la conexión a la base de datos"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._init_database()
    
    def _init_database(self):
        """Inicializa la base de datos con el esquema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla de Configuración
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Configuracion (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Tasa_Dolar_BS REAL NOT NULL DEFAULT 35.50,
                    Nombre_Hotel TEXT NOT NULL DEFAULT 'Hotel Ejemplo',
                    Direccion TEXT,
                    Telefono TEXT,
                    Email TEXT,
                    RIF TEXT,
                    Fecha_Actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de Usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Usuarios (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Username TEXT UNIQUE NOT NULL,
                    Password_Hash TEXT NOT NULL,
                    Nombre_Completo TEXT NOT NULL,
                    Rol TEXT NOT NULL CHECK(Rol IN ('admin', 'recepcionista', 'gerente')),
                    Activo INTEGER DEFAULT 1,
                    Ultimo_Acceso TIMESTAMP,
                    Fecha_Creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de Huéspedes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Huespedes (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Documento TEXT UNIQUE NOT NULL,
                    Nombres TEXT NOT NULL,
                    Apellidos TEXT NOT NULL,
                    Telefono TEXT,
                    Email TEXT,
                    Fecha_Nacimiento DATE,
                    Nacionalidad TEXT DEFAULT 'Venezolano',
                    Profesion TEXT,
                    Vehiculo TEXT,
                    Placa_Vehiculo TEXT,
                    Saldo_Acumulado REAL DEFAULT 0.0,
                    Fecha_Registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    Ultima_Visita TIMESTAMP
                )
            ''')
            
            # Tabla de Habitaciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Habitaciones (
                    Numero INTEGER PRIMARY KEY,
                    Tipo TEXT NOT NULL,
                    Descripcion TEXT,
                    Precio_USD REAL NOT NULL,
                    Capacidad INTEGER DEFAULT 2,
                    Estado TEXT DEFAULT 'Libre' CHECK(Estado IN ('Libre', 'Ocupada', 'Reservada', 'Aseo', 'Mantenimiento')),
                    Ultima_Limpieza TIMESTAMP,
                    Notas TEXT
                )
            ''')
            
            # Tabla de Registros (Check-ins)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Registros (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Huesped_Principal_ID INTEGER NOT NULL,
                    Habitacion_Numero INTEGER NOT NULL,
                    Fecha_Entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    Fecha_Salida_Prevista TIMESTAMP NOT NULL,
                    Fecha_Salida_Real TIMESTAMP,
                    Estado TEXT DEFAULT 'Activo' CHECK(Estado IN ('Activo', 'Cerrado', 'Cancelado')),
                    Total_Habitacion_USD REAL DEFAULT 0.0,
                    Total_Extras_USD REAL DEFAULT 0.0,
                    Total_Descuentos_USD REAL DEFAULT 0.0,
                    Total_Pagado_USD REAL DEFAULT 0.0,
                    Saldo_Pendiente_USD REAL DEFAULT 0.0,
                    Notas TEXT,
                    Usuario_Checkin_ID INTEGER,
                    Usuario_Checkout_ID INTEGER,
                    FOREIGN KEY (Huesped_Principal_ID) REFERENCES Huespedes(ID),
                    FOREIGN KEY (Habitacion_Numero) REFERENCES Habitaciones(Numero),
                    FOREIGN KEY (Usuario_Checkin_ID) REFERENCES Usuarios(ID),
                    FOREIGN KEY (Usuario_Checkout_ID) REFERENCES Usuarios(ID)
                )
            ''')
            
            # Tabla de Acompañantes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Acompanantes (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Registro_ID INTEGER NOT NULL,
                    Huesped_ID INTEGER NOT NULL,
                    Fecha_Agregado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (Registro_ID) REFERENCES Registros(ID) ON DELETE CASCADE,
                    FOREIGN KEY (Huesped_ID) REFERENCES Huespedes(ID)
                )
            ''')
            
            # Tabla de Transacciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Transacciones (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Registro_ID INTEGER,
                    Huesped_ID INTEGER,
                    Monto_USD REAL NOT NULL,
                    Tasa_Cambio REAL NOT NULL,
                    Monto_BS REAL NOT NULL,
                    Metodo_Pago TEXT NOT NULL CHECK(Metodo_Pago IN ('Efectivo_USD', 'Efectivo_BS', 'Pago_Movil', 'Transferencia', 'Tarjeta', 'Zelle', 'Binance', 'Ajuste')),
                    Referencia TEXT,
                    Tipo TEXT NOT NULL CHECK(Tipo IN ('Pago', 'Cargo', 'Ajuste', 'Reembolso')),
                    Concepto TEXT,
                    Fecha_Hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    Usuario_ID INTEGER NOT NULL,
                    Turno_ID INTEGER,
                    FOREIGN KEY (Registro_ID) REFERENCES Registros(ID),
                    FOREIGN KEY (Huesped_ID) REFERENCES Huespedes(ID),
                    FOREIGN KEY (Usuario_ID) REFERENCES Usuarios(ID)
                )
            ''')
            
            # Tabla de Turnos (Cierres de Caja)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Turnos (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Usuario_ID INTEGER NOT NULL,
                    Fecha_Apertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    Fecha_Cierre TIMESTAMP,
                    Tasa_Apertura REAL NOT NULL,
                    Tasa_Cierre REAL,
                    Efectivo_USD_Apertura REAL DEFAULT 0.0,
                    Efectivo_USD_Cierre REAL,
                    Efectivo_BS_Apertura REAL DEFAULT 0.0,
                    Efectivo_BS_Cierre REAL,
                    Total_Ventas_USD REAL DEFAULT 0.0,
                    Total_Ventas_BS REAL DEFAULT 0.0,
                    Total_Pagos_USD REAL DEFAULT 0.0,
                    Total_Pagos_BS REAL DEFAULT 0.0,
                    Estado TEXT DEFAULT 'Abierto' CHECK(Estado IN ('Abierto', 'Cerrado')),
                    Observaciones TEXT,
                    FOREIGN KEY (Usuario_ID) REFERENCES Usuarios(ID)
                )
            ''')
            
            # Tabla de Extras (cargos adicionales)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Extras (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Registro_ID INTEGER NOT NULL,
                    Descripcion TEXT NOT NULL,
                    Monto_USD REAL NOT NULL,
                    Cantidad INTEGER DEFAULT 1,
                    Fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    Usuario_ID INTEGER NOT NULL,
                    FOREIGN KEY (Registro_ID) REFERENCES Registros(ID),
                    FOREIGN KEY (Usuario_ID) REFERENCES Usuarios(ID)
                )
            ''')
            
            # Insertar configuración inicial si no existe
            cursor.execute('SELECT COUNT(*) FROM Configuracion')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO Configuracion (Tasa_Dolar_BS, Nombre_Hotel, Direccion, Telefono)
                    VALUES (35.50, 'Hotel Ejemplo', 'Dirección del Hotel', '+58 000-0000000')
                ''')
            
            # Insertar usuario admin por defecto si no existe (password: admin123)
            cursor.execute('SELECT COUNT(*) FROM Usuarios')
            if cursor.fetchone()[0] == 0:
                import hashlib
                password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
                cursor.execute('''
                    INSERT INTO Usuarios (Username, Password_Hash, Nombre_Completo, Rol)
                    VALUES ('admin', ?, 'Administrador Principal', 'admin')
                ''', (password_hash,))
            
            # Insertar habitaciones de ejemplo (1-39) si no existen
            cursor.execute('SELECT COUNT(*) FROM Habitaciones')
            if cursor.fetchone()[0] == 0:
                habitaciones = [
                    # Habitaciones sencillas (1-15)
                    (i, 'Sencilla', f'Habitación Sencilla #{i}', 25.0, 2) for i in range(1, 16)
                ] + [
                    # Habitaciones dobles (16-30)
                    (i, 'Doble', f'Habitación Doble #{i}', 40.0, 4) for i in range(16, 31)
                ] + [
                    # Suites (31-35)
                    (i, 'Suite', f'Suite #{i}', 80.0, 4) for i in range(31, 36)
                ] + [
                    # Suites Presidenciales (36-39)
                    (i, 'Presidencial', f'Suite Presidencial #{i}', 150.0, 6) for i in range(36, 40)
                ]
                
                cursor.executemany('''
                    INSERT INTO Habitaciones (Numero, Tipo, Descripcion, Precio_USD, Capacidad)
                    VALUES (?, ?, ?, ?, ?)
                ''', habitaciones)
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Context manager para obtener una conexión a la base de datos"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def execute(self, query: str, params: Tuple = ()) -> int:
        """Ejecuta una consulta y retorna el ID de la última fila insertada"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> None:
        """Ejecuta una consulta múltiple"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
    
    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """Obtiene una sola fila como diccionario"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def fetch_all(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Obtiene todas las filas como lista de diccionarios"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def fetch_scalar(self, query: str, params: Tuple = ()) -> Any:
        """Obtiene un valor escalar"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else None

# Instancia global de la base de datos
db = Database()
