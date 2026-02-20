"""
Modelo y lógica de negocio para Turnos (Cierres de Caja)
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum
from database.connection import db

class EstadoTurno(str, Enum):
    ABIERTO = 'Abierto'
    CERRADO = 'Cerrado'

@dataclass
class Turno:
    usuario_id: int
    tasa_apertura: float
    fecha_apertura: datetime = None
    fecha_cierre: Optional[datetime] = None
    efectivo_usd_apertura: float = 0.0
    efectivo_usd_cierre: Optional[float] = None
    efectivo_bs_apertura: float = 0.0
    efectivo_bs_cierre: Optional[float] = None
    total_ventas_usd: float = 0.0
    total_ventas_bs: float = 0.0
    total_pagos_usd: float = 0.0
    total_pagos_bs: float = 0.0
    estado: EstadoTurno = EstadoTurno.ABIERTO
    observaciones: str = ""
    id: Optional[int] = None
    
    # Campos relacionados
    usuario_nombre: str = ""
    
    def __post_init__(self):
        if self.fecha_apertura is None:
            self.fecha_apertura = datetime.now()
    
    @property
    def diferencia_efectivo_usd(self) -> float:
        """Calcula la diferencia de efectivo USD"""
        if self.efectivo_usd_cierre is None:
            return 0.0
        return self.efectivo_usd_cierre - self.efectivo_usd_apertura
    
    @property
    def diferencia_efectivo_bs(self) -> float:
        """Calcula la diferencia de efectivo BS"""
        if self.efectivo_bs_cierre is None:
            return 0.0
        return self.efectivo_bs_cierre - self.efectivo_bs_apertura
    
    @property
    def esta_abierto(self) -> bool:
        return self.estado == EstadoTurno.ABIERTO
    
    def calcular_totales(self) -> None:
        """Calcula los totales del turno basado en transacciones"""
        from models.transaccion import Transaccion, TipoTransaccion
        
        transacciones = Transaccion.listar_por_turno(self.id) if self.id else []
        
        self.total_ventas_usd = 0.0
        self.total_ventas_bs = 0.0
        self.total_pagos_usd = 0.0
        self.total_pagos_bs = 0.0
        
        for t in transacciones:
            if t.tipo == TipoTransaccion.PAGO:
                self.total_pagos_usd += t.monto_usd
                self.total_pagos_bs += t.monto_bs
            elif t.tipo == TipoTransaccion.CARGO:
                self.total_ventas_usd += t.monto_usd
                self.total_ventas_bs += t.monto_bs
    
    def cerrar(self, efectivo_usd_cierre: float, efectivo_bs_cierre: float, 
               tasa_cierre: float, observaciones: str = "") -> None:
        """Cierra el turno"""
        self.fecha_cierre = datetime.now()
        self.efectivo_usd_cierre = efectivo_usd_cierre
        self.efectivo_bs_cierre = efectivo_bs_cierre
        self.tasa_cierre = tasa_cierre
        self.observaciones = observaciones
        self.estado = EstadoTurno.CERRADO
        
        # Calcular totales finales
        self.calcular_totales()
        
        db.execute('''
            UPDATE Turnos SET
                Fecha_Cierre = ?,
                Tasa_Cierre = ?,
                Efectivo_USD_Cierre = ?,
                Efectivo_BS_Cierre = ?,
                Total_Ventas_USD = ?,
                Total_Ventas_BS = ?,
                Total_Pagos_USD = ?,
                Total_Pagos_BS = ?,
                Estado = ?,
                Observaciones = ?
            WHERE ID = ?
        ''', (
            self.fecha_cierre, tasa_cierre, efectivo_usd_cierre, efectivo_bs_cierre,
            self.total_ventas_usd, self.total_ventas_bs,
            self.total_pagos_usd, self.total_pagos_bs,
            self.estado.value, observaciones, self.id
        ))
    
    def guardar(self) -> int:
        """Guarda el turno"""
        if self.id:
            db.execute('''
                UPDATE Turnos SET
                    Efectivo_USD_Apertura = ?,
                    Efectivo_BS_Apertura = ?,
                    Observaciones = ?
                WHERE ID = ?
            ''', (self.efectivo_usd_apertura, self.efectivo_bs_apertura, 
                  self.observaciones, self.id))
            return self.id
        else:
            self.id = db.execute('''
                INSERT INTO Turnos (
                    Usuario_ID, Fecha_Apertura, Tasa_Apertura,
                    Efectivo_USD_Apertura, Efectivo_BS_Apertura,
                    Estado, Observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.usuario_id, self.fecha_apertura, self.tasa_apertura,
                self.efectivo_usd_apertura, self.efectivo_bs_apertura,
                self.estado.value, self.observaciones
            ))
            return self.id
    
    @staticmethod
    def buscar_por_id(turno_id: int) -> Optional['Turno']:
        """Busca un turno por su ID"""
        row = db.fetch_one('''
            SELECT t.*, u.Nombre_Completo as Usuario_Nombre
            FROM Turnos t
            JOIN Usuarios u ON t.Usuario_ID = u.ID
            WHERE t.ID = ?
        ''', (turno_id,))
        return Turno._from_row(row) if row else None
    
    @staticmethod
    def buscar_turno_abierto(usuario_id: int) -> Optional['Turno']:
        """Busca si un usuario tiene un turno abierto"""
        row = db.fetch_one('''
            SELECT t.*, u.Nombre_Completo as Usuario_Nombre
            FROM Turnos t
            JOIN Usuarios u ON t.Usuario_ID = u.ID
            WHERE t.Usuario_ID = ? AND t.Estado = 'Abierto'
            ORDER BY t.Fecha_Apertura DESC
            LIMIT 1
        ''', (usuario_id,))
        return Turno._from_row(row) if row else None
    
    @staticmethod
    def buscar_turno_abierto_global() -> Optional['Turno']:
        """Busca cualquier turno abierto en el sistema"""
        row = db.fetch_one('''
            SELECT t.*, u.Nombre_Completo as Usuario_Nombre
            FROM Turnos t
            JOIN Usuarios u ON t.Usuario_ID = u.ID
            WHERE t.Estado = 'Abierto'
            ORDER BY t.Fecha_Apertura DESC
            LIMIT 1
        ''')
        return Turno._from_row(row) if row else None
    
    @staticmethod
    def listar_todos() -> List['Turno']:
        """Lista todos los turnos"""
        rows = db.fetch_all('''
            SELECT t.*, u.Nombre_Completo as Usuario_Nombre
            FROM Turnos t
            JOIN Usuarios u ON t.Usuario_ID = u.ID
            ORDER BY t.Fecha_Apertura DESC
        ''')
        return [Turno._from_row(row) for row in rows]
    
    @staticmethod
    def listar_por_usuario(usuario_id: int) -> List['Turno']:
        """Lista turnos de un usuario"""
        rows = db.fetch_all('''
            SELECT t.*, u.Nombre_Completo as Usuario_Nombre
            FROM Turnos t
            JOIN Usuarios u ON t.Usuario_ID = u.ID
            WHERE t.Usuario_ID = ?
            ORDER BY t.Fecha_Apertura DESC
        ''', (usuario_id,))
        return [Turno._from_row(row) for row in rows]
    
    @staticmethod
    def listar_por_fecha(fecha_desde: datetime, fecha_hasta: datetime) -> List['Turno']:
        """Lista turnos por rango de fechas"""
        rows = db.fetch_all('''
            SELECT t.*, u.Nombre_Completo as Usuario_Nombre
            FROM Turnos t
            JOIN Usuarios u ON t.Usuario_ID = u.ID
            WHERE t.Fecha_Apertura BETWEEN ? AND ?
            ORDER BY t.Fecha_Apertura DESC
        ''', (fecha_desde, fecha_hasta))
        return [Turno._from_row(row) for row in rows]
    
    @staticmethod
    def _from_row(row: dict) -> 'Turno':
        """Crea un objeto Turno desde una fila de la base de datos"""
        return Turno(
            id=row['ID'],
            usuario_id=row['Usuario_ID'],
            fecha_apertura=row['Fecha_Apertura'],
            fecha_cierre=row['Fecha_Cierre'],
            tasa_apertura=row['Tasa_Apertura'],
            tasa_cierre=row.get('Tasa_Cierre'),
            efectivo_usd_apertura=row['Efectivo_USD_Apertura'],
            efectivo_usd_cierre=row['Efectivo_USD_Cierre'],
            efectivo_bs_apertura=row['Efectivo_BS_Apertura'],
            efectivo_bs_cierre=row['Efectivo_BS_Cierre'],
            total_ventas_usd=row['Total_Ventas_USD'],
            total_ventas_bs=row['Total_Ventas_BS'],
            total_pagos_usd=row['Total_Pagos_USD'],
            total_pagos_bs=row['Total_Pagos_BS'],
            estado=EstadoTurno(row['Estado']),
            observaciones=row['Observaciones'] or "",
            usuario_nombre=row.get('Usuario_Nombre', '')
        )
