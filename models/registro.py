"""
Modelo y lógica de negocio para Registros (Check-ins/Check-outs)
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum
from database.connection import db

class EstadoRegistro(str, Enum):
    ACTIVO = 'Activo'
    CERRADO = 'Cerrado'
    CANCELADO = 'Cancelado'

@dataclass
class Registro:
    huesped_principal_id: int
    habitacion_numero: int
    fecha_entrada: datetime = field(default_factory=datetime.now)
    fecha_salida_prevista: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=1))
    fecha_salida_real: Optional[datetime] = None
    estado: EstadoRegistro = EstadoRegistro.ACTIVO
    total_habitacion_usd: float = 0.0
    total_extras_usd: float = 0.0
    total_descuentos_usd: float = 0.0
    total_pagado_usd: float = 0.0
    saldo_pendiente_usd: float = 0.0
    notas: str = ""
    usuario_checkin_id: Optional[int] = None
    usuario_checkout_id: Optional[int] = None
    id: Optional[int] = None
    
    # Campos relacionados (no persistidos directamente)
    huesped_nombre: str = ""
    habitacion_tipo: str = ""
    
    @property
    def noches_estadia(self) -> int:
        """Calcula el número de noches de estadía"""
        if self.fecha_salida_real:
            delta = self.fecha_salida_real - self.fecha_entrada
        else:
            delta = datetime.now() - self.fecha_entrada
        return max(1, delta.days)
    
    @property
    def noches_restantes(self) -> int:
        """Calcula las noches restantes hasta la salida prevista"""
        delta = self.fecha_salida_prevista - datetime.now()
        return max(0, delta.days)
    
    @property
    def total_estadia_usd(self) -> float:
        """Calcula el total de la estadía (habitación + extras - descuentos)"""
        return self.total_habitacion_usd + self.total_extras_usd - self.total_descuentos_usd
    
    @property
    def saldo_actual_usd(self) -> float:
        """Calcula el saldo actual (total - pagado)"""
        return self.total_estadia_usd - self.total_pagado_usd
    
    @property
    def esta_activo(self) -> bool:
        return self.estado == EstadoRegistro.ACTIVO
    
    def calcular_total_habitacion(self, precio_noche: float) -> float:
        """Calcula el total de la habitación según noches y precio"""
        self.total_habitacion_usd = self.noches_estadia * precio_noche
        return self.total_habitacion_usd
    
    def agregar_extra(self, descripcion: str, monto_usd: float, cantidad: int = 1) -> None:
        """Agrega un cargo extra al registro"""
        monto_total = monto_usd * cantidad
        self.total_extras_usd += monto_total
        self._actualizar_totales()
        
        # Guardar en tabla Extras
        db.execute('''
            INSERT INTO Extras (Registro_ID, Descripcion, Monto_USD, Cantidad, Usuario_ID)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.id, descripcion, monto_usd, cantidad, self.usuario_checkin_id or 1))
    
    def aplicar_descuento(self, monto_usd: float) -> None:
        """Aplica un descuento al registro"""
        self.total_descuentos_usd += monto_usd
        self._actualizar_totales()
    
    def registrar_pago(self, monto_usd: float) -> None:
        """Registra un pago en el registro"""
        self.total_pagado_usd += monto_usd
        self._actualizar_totales()
    
    def _actualizar_totales(self) -> None:
        """Actualiza los totales en la base de datos"""
        if self.id:
            db.execute('''
                UPDATE Registros SET
                    Total_Habitacion_USD = ?,
                    Total_Extras_USD = ?,
                    Total_Descuentos_USD = ?,
                    Total_Pagado_USD = ?,
                    Saldo_Pendiente_USD = ?
                WHERE ID = ?
            ''', (
                self.total_habitacion_usd, self.total_extras_usd,
                self.total_descuentos_usd, self.total_pagado_usd,
                self.saldo_actual_usd, self.id
            ))
    
    def realizar_checkout(self, usuario_id: int) -> None:
        """Realiza el checkout del huésped"""
        self.fecha_salida_real = datetime.now()
        self.estado = EstadoRegistro.CERRADO
        self.usuario_checkout_id = usuario_id
        
        # Liberar habitación
        from models.habitacion import Habitacion, EstadoHabitacion
        habitacion = Habitacion.buscar_por_numero(self.habitacion_numero)
        if habitacion:
            habitacion.cambiar_estado(EstadoHabitacion.ASEO)
        
        db.execute('''
            UPDATE Registros SET
                Fecha_Salida_Real = ?,
                Estado = ?,
                Usuario_Checkout_ID = ?,
                Saldo_Pendiente_USD = ?
            WHERE ID = ?
        ''', (self.fecha_salida_real, self.estado.value, usuario_id, 
              self.saldo_actual_usd, self.id))
    
    def guardar(self) -> int:
        """Guarda o actualiza el registro"""
        if self.id:
            db.execute('''
                UPDATE Registros SET
                    Huesped_Principal_ID = ?,
                    Habitacion_Numero = ?,
                    Fecha_Entrada = ?,
                    Fecha_Salida_Prevista = ?,
                    Estado = ?,
                    Total_Habitacion_USD = ?,
                    Total_Extras_USD = ?,
                    Total_Descuentos_USD = ?,
                    Total_Pagado_USD = ?,
                    Saldo_Pendiente_USD = ?,
                    Notas = ?,
                    Usuario_Checkin_ID = ?
                WHERE ID = ?
            ''', (
                self.huesped_principal_id, self.habitacion_numero,
                self.fecha_entrada, self.fecha_salida_prevista,
                self.estado.value, self.total_habitacion_usd,
                self.total_extras_usd, self.total_descuentos_usd,
                self.total_pagado_usd, self.saldo_pendiente_usd,
                self.notas, self.usuario_checkin_id, self.id
            ))
            return self.id
        else:
            self.id = db.execute('''
                INSERT INTO Registros (
                    Huesped_Principal_ID, Habitacion_Numero, Fecha_Entrada,
                    Fecha_Salida_Prevista, Estado, Total_Habitacion_USD,
                    Total_Extras_USD, Total_Descuentos_USD, Total_Pagado_USD,
                    Saldo_Pendiente_USD, Notas, Usuario_Checkin_ID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.huesped_principal_id, self.habitacion_numero,
                self.fecha_entrada, self.fecha_salida_prevista,
                self.estado.value, self.total_habitacion_usd,
                self.total_extras_usd, self.total_descuentos_usd,
                self.total_pagado_usd, self.saldo_pendiente_usd,
                self.notas, self.usuario_checkin_id
            ))
            
            # Actualizar estado de habitación a Ocupada
            from models.habitacion import Habitacion, EstadoHabitacion
            habitacion = Habitacion.buscar_por_numero(self.habitacion_numero)
            if habitacion:
                habitacion.cambiar_estado(EstadoHabitacion.OCUPADA)
            
            # Actualizar última visita del huésped
            db.execute(
                'UPDATE Huespedes SET Ultima_Visita = ? WHERE ID = ?',
                (datetime.now(), self.huesped_principal_id)
            )
            
            return self.id
    
    @staticmethod
    def buscar_por_id(registro_id: int) -> Optional['Registro']:
        """Busca un registro por su ID con información relacionada"""
        row = db.fetch_one('''
            SELECT r.*, h.Nombres || ' ' || h.Apellidos as Huesped_Nombre,
                   hb.Tipo as Habitacion_Tipo
            FROM Registros r
            JOIN Huespedes h ON r.Huesped_Principal_ID = h.ID
            JOIN Habitaciones hb ON r.Habitacion_Numero = hb.Numero
            WHERE r.ID = ?
        ''', (registro_id,))
        return Registro._from_row(row) if row else None
    
    @staticmethod
    def buscar_activo_por_habitacion(numero_habitacion: int) -> Optional['Registro']:
        """Busca el registro activo de una habitación"""
        row = db.fetch_one('''
            SELECT r.*, h.Nombres || ' ' || h.Apellidos as Huesped_Nombre,
                   hb.Tipo as Habitacion_Tipo
            FROM Registros r
            JOIN Huespedes h ON r.Huesped_Principal_ID = h.ID
            JOIN Habitaciones hb ON r.Habitacion_Numero = hb.Numero
            WHERE r.Habitacion_Numero = ? AND r.Estado = 'Activo'
        ''', (numero_habitacion,))
        return Registro._from_row(row) if row else None
    
    @staticmethod
    def listar_activos() -> List['Registro']:
        """Lista todos los registros activos"""
        rows = db.fetch_all('''
            SELECT r.*, h.Nombres || ' ' || h.Apellidos as Huesped_Nombre,
                   hb.Tipo as Habitacion_Tipo
            FROM Registros r
            JOIN Huespedes h ON r.Huesped_Principal_ID = h.ID
            JOIN Habitaciones hb ON r.Habitacion_Numero = hb.Numero
            WHERE r.Estado = 'Activo'
            ORDER BY r.Fecha_Entrada DESC
        ''')
        return [Registro._from_row(row) for row in rows]
    
    @staticmethod
    def listar_por_huesped(huesped_id: int) -> List['Registro']:
        """Lista todos los registros de un huésped"""
        rows = db.fetch_all('''
            SELECT r.*, h.Nombres || ' ' || h.Apellidos as Huesped_Nombre,
                   hb.Tipo as Habitacion_Tipo
            FROM Registros r
            JOIN Huespedes h ON r.Huesped_Principal_ID = h.ID
            JOIN Habitaciones hb ON r.Habitacion_Numero = hb.Numero
            WHERE r.Huesped_Principal_ID = ?
            ORDER BY r.Fecha_Entrada DESC
        ''', (huesped_id,))
        return [Registro._from_row(row) for row in rows]
    
    @staticmethod
    def listar_historico(fecha_desde: datetime = None, fecha_hasta: datetime = None) -> List['Registro']:
        """Lista registros históricos con filtro opcional de fechas"""
        query = '''
            SELECT r.*, h.Nombres || ' ' || h.Apellidos as Huesped_Nombre,
                   hb.Tipo as Habitacion_Tipo
            FROM Registros r
            JOIN Huespedes h ON r.Huesped_Principal_ID = h.ID
            JOIN Habitaciones hb ON r.Habitacion_Numero = hb.Numero
            WHERE 1=1
        '''
        params = []
        
        if fecha_desde:
            query += ' AND r.Fecha_Entrada >= ?'
            params.append(fecha_desde)
        if fecha_hasta:
            query += ' AND r.Fecha_Entrada <= ?'
            params.append(fecha_hasta)
        
        query += ' ORDER BY r.Fecha_Entrada DESC'
        
        rows = db.fetch_all(query, tuple(params))
        return [Registro._from_row(row) for row in rows]
    
    @staticmethod
    def _from_row(row: dict) -> 'Registro':
        """Crea un objeto Registro desde una fila de la base de datos"""
        return Registro(
            id=row['ID'],
            huesped_principal_id=row['Huesped_Principal_ID'],
            habitacion_numero=row['Habitacion_Numero'],
            fecha_entrada=row['Fecha_Entrada'],
            fecha_salida_prevista=row['Fecha_Salida_Prevista'],
            fecha_salida_real=row['Fecha_Salida_Real'],
            estado=EstadoRegistro(row['Estado']),
            total_habitacion_usd=row['Total_Habitacion_USD'],
            total_extras_usd=row['Total_Extras_USD'],
            total_descuentos_usd=row['Total_Descuentos_USD'],
            total_pagado_usd=row['Total_Pagado_USD'],
            saldo_pendiente_usd=row['Saldo_Pendiente_USD'],
            notas=row['Notas'],
            usuario_checkin_id=row['Usuario_Checkin_ID'],
            usuario_checkout_id=row['Usuario_Checkout_ID'],
            huesped_nombre=row.get('Huesped_Nombre', ''),
            habitacion_tipo=row.get('Habitacion_Tipo', '')
        )
