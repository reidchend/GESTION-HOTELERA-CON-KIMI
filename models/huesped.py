"""
Modelo y lógica de negocio para Huéspedes
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List
from database.connection import db

@dataclass
class Huesped:
    id: Optional[int] = None
    documento: str = ""
    nombres: str = ""
    apellidos: str = ""
    telefono: str = ""
    email: str = ""
    fecha_nacimiento: Optional[date] = None
    nacionalidad: str = "Venezolano"
    profesion: str = ""
    vehiculo: str = ""
    placa_vehiculo: str = ""
    saldo_acumulado: float = 0.0
    fecha_registro: Optional[datetime] = None
    ultima_visita: Optional[datetime] = None
    
    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}".strip()
    
    @property
    def tiene_saldo_favor(self) -> bool:
        return self.saldo_acumulado > 0
    
    @property
    def tiene_deuda(self) -> bool:
        return self.saldo_acumulado < 0
    
    def guardar(self) -> int:
        """Guarda o actualiza el huésped en la base de datos"""
        if self.id:
            db.execute('''
                UPDATE Huespedes SET
                    Documento = ?,
                    Nombres = ?,
                    Apellidos = ?,
                    Telefono = ?,
                    Email = ?,
                    Fecha_Nacimiento = ?,
                    Nacionalidad = ?,
                    Profesion = ?,
                    Vehiculo = ?,
                    Placa_Vehiculo = ?,
                    Saldo_Acumulado = ?,
                    Ultima_Visita = ?
                WHERE ID = ?
            ''', (
                self.documento, self.nombres, self.apellidos, self.telefono,
                self.email, self.fecha_nacimiento, self.nacionalidad,
                self.profesion, self.vehiculo, self.placa_vehiculo,
                self.saldo_acumulado, datetime.now(), self.id
            ))
            return self.id
        else:
            self.id = db.execute('''
                INSERT INTO Huespedes (
                    Documento, Nombres, Apellidos, Telefono, Email,
                    Fecha_Nacimiento, Nacionalidad, Profesion, Vehiculo,
                    Placa_Vehiculo, Saldo_Acumulado, Fecha_Registro
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.documento, self.nombres, self.apellidos, self.telefono,
                self.email, self.fecha_nacimiento, self.nacionalidad,
                self.profesion, self.vehiculo, self.placa_vehiculo,
                self.saldo_acumulado, datetime.now()
            ))
            return self.id
    
    @staticmethod
    def buscar_por_id(huesped_id: int) -> Optional['Huesped']:
        """Busca un huésped por su ID"""
        row = db.fetch_one('SELECT * FROM Huespedes WHERE ID = ?', (huesped_id,))
        return Huesped._from_row(row) if row else None
    
    @staticmethod
    def buscar_por_documento(documento: str) -> Optional['Huesped']:
        """Busca un huésped por su documento (cédula/pasaporte)"""
        row = db.fetch_one('SELECT * FROM Huespedes WHERE Documento = ?', (documento,))
        return Huesped._from_row(row) if row else None
    
    @staticmethod
    def buscar_por_nombre(nombre: str) -> List['Huesped']:
        """Busca huéspedes por nombre (búsqueda parcial)"""
        rows = db.fetch_all('''
            SELECT * FROM Huespedes 
            WHERE Nombres LIKE ? OR Apellidos LIKE ?
            ORDER BY Apellidos, Nombres
        ''', (f'%{nombre}%', f'%{nombre}%'))
        return [Huesped._from_row(row) for row in rows]
    
    @staticmethod
    def listar_todos() -> List['Huesped']:
        """Lista todos los huéspedes ordenados por apellido"""
        rows = db.fetch_all('SELECT * FROM Huespedes ORDER BY Apellidos, Nombres')
        return [Huesped._from_row(row) for row in rows]
    
    @staticmethod
    def listar_con_saldo() -> List['Huesped']:
        """Lista huéspedes con saldo a favor o deuda"""
        rows = db.fetch_all('''
            SELECT * FROM Huespedes 
            WHERE Saldo_Acumulado != 0
            ORDER BY Saldo_Acumulado DESC
        ''')
        return [Huesped._from_row(row) for row in rows]
    
    def ajustar_saldo(self, monto: float, tipo: str = 'Ajuste') -> None:
        """
        Ajusta el saldo del huésped
        - monto positivo: aumenta saldo a favor
        - monto negativo: aumenta deuda
        """
        self.saldo_acumulado += monto
        self.guardar()
    
    @staticmethod
    def _from_row(row: dict) -> 'Huesped':
        """Crea un objeto Huesped desde una fila de la base de datos"""
        return Huesped(
            id=row['ID'],
            documento=row['Documento'],
            nombres=row['Nombres'],
            apellidos=row['Apellidos'],
            telefono=row['Telefono'],
            email=row['Email'],
            fecha_nacimiento=row['Fecha_Nacimiento'],
            nacionalidad=row['Nacionalidad'],
            profesion=row['Profesion'],
            vehiculo=row['Vehiculo'],
            placa_vehiculo=row['Placa_Vehiculo'],
            saldo_acumulado=row['Saldo_Acumulado'],
            fecha_registro=row['Fecha_Registro'],
            ultima_visita=row['Ultima_Visita']
        )
