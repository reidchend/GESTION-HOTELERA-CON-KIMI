"""
Modelo y lógica de negocio para Habitaciones
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum
from database.connection import db

class EstadoHabitacion(str, Enum):
    LIBRE = 'Libre'
    OCUPADA = 'Ocupada'
    RESERVADA = 'Reservada'
    ASEO = 'Aseo'
    MANTENIMIENTO = 'Mantenimiento'

@dataclass
class Habitacion:
    numero: int
    tipo: str = ""
    descripcion: str = ""
    precio_usd: float = 0.0
    capacidad: int = 2
    estado: EstadoHabitacion = EstadoHabitacion.LIBRE
    ultima_limpieza: Optional[datetime] = None
    notas: str = ""
    
    @property
    def color_estado(self) -> str:
        """Retorna el color asociado al estado de la habitación"""
        colores = {
            EstadoHabitacion.LIBRE: '#4CAF50',      # Verde
            EstadoHabitacion.OCUPADA: '#F44336',    # Rojo
            EstadoHabitacion.RESERVADA: '#FFC107',  # Amarillo
            EstadoHabitacion.ASEO: '#9E9E9E',       # Gris
            EstadoHabitacion.MANTENIMIENTO: '#FF9800'  # Naranja
        }
        return colores.get(self.estado, '#9E9E9E')
    
    @property
    def icono_estado(self) -> str:
        """Retorna el icono asociado al estado"""
        iconos = {
            EstadoHabitacion.LIBRE: 'check_circle',
            EstadoHabitacion.OCUPADA: 'person',
            EstadoHabitacion.RESERVADA: 'bookmark',
            EstadoHabitacion.ASEO: 'cleaning_services',
            EstadoHabitacion.MANTENIMIENTO: 'build'
        }
        return iconos.get(self.estado, 'help')
    
    @property
    def esta_disponible(self) -> bool:
        """Retorna True si la habitación está disponible para check-in"""
        return self.estado == EstadoHabitacion.LIBRE
    
    def cambiar_estado(self, nuevo_estado: EstadoHabitacion) -> None:
        """Cambia el estado de la habitación"""
        self.estado = nuevo_estado
        if nuevo_estado == EstadoHabitacion.ASEO:
            self.ultima_limpieza = datetime.now()
        db.execute(
            'UPDATE Habitaciones SET Estado = ?, Ultima_Limpieza = ? WHERE Numero = ?',
            (self.estado.value, self.ultima_limpieza, self.numero)
        )
    
    def guardar(self) -> None:
        """Guarda o actualiza la habitación"""
        db.execute('''
            INSERT OR REPLACE INTO Habitaciones 
            (Numero, Tipo, Descripcion, Precio_USD, Capacidad, Estado, Ultima_Limpieza, Notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.numero, self.tipo, self.descripcion, self.precio_usd,
            self.capacidad, self.estado.value, self.ultima_limpieza, self.notas
        ))
    
    @staticmethod
    def buscar_por_numero(numero: int) -> Optional['Habitacion']:
        """Busca una habitación por su número"""
        row = db.fetch_one('SELECT * FROM Habitaciones WHERE Numero = ?', (numero,))
        return Habitacion._from_row(row) if row else None
    
    @staticmethod
    def listar_todas() -> List['Habitacion']:
        """Lista todas las habitaciones ordenadas por número"""
        rows = db.fetch_all('SELECT * FROM Habitaciones ORDER BY Numero')
        return [Habitacion._from_row(row) for row in rows]
    
    @staticmethod
    def listar_por_estado(estado: EstadoHabitacion) -> List['Habitacion']:
        """Lista habitaciones por estado"""
        rows = db.fetch_all(
            'SELECT * FROM Habitaciones WHERE Estado = ? ORDER BY Numero',
            (estado.value,)
        )
        return [Habitacion._from_row(row) for row in rows]
    
    @staticmethod
    def listar_disponibles() -> List['Habitacion']:
        """Lista habitaciones disponibles (Libres)"""
        return Habitacion.listar_por_estado(EstadoHabitacion.LIBRE)
    
    @staticmethod
    def contar_por_estado() -> dict:
        """Retorna un conteo de habitaciones por estado"""
        rows = db.fetch_all('''
            SELECT Estado, COUNT(*) as cantidad 
            FROM Habitaciones 
            GROUP BY Estado
        ''')
        return {row['Estado']: row['cantidad'] for row in rows}
    
    @staticmethod
    def _from_row(row: dict) -> 'Habitacion':
        """Crea un objeto Habitacion desde una fila de la base de datos"""
        return Habitacion(
            numero=row['Numero'],
            tipo=row['Tipo'],
            descripcion=row['Descripcion'],
            precio_usd=row['Precio_USD'],
            capacidad=row['Capacidad'],
            estado=EstadoHabitacion(row['Estado']),
            ultima_limpieza=row['Ultima_Limpieza'],
            notas=row['Notas']
        )
