"""
Modelo y lógica de negocio para Transacciones (Pagos/Cargos/Ajustes)
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum
from database.connection import db

class MetodoPago(str, Enum):
    EFECTIVO_USD = 'Efectivo_USD'
    EFECTIVO_BS = 'Efectivo_BS'
    PAGO_MOVIL = 'Pago_Movil'
    TRANSFERENCIA = 'Transferencia'
    TARJETA = 'Tarjeta'
    ZELLE = 'Zelle'
    BINANCE = 'Binance'
    AJUSTE = 'Ajuste'

class TipoTransaccion(str, Enum):
    PAGO = 'Pago'
    CARGO = 'Cargo'
    AJUSTE = 'Ajuste'
    REEMBOLSO = 'Reembolso'

@dataclass
class Transaccion:
    monto_usd: float
    tasa_cambio: float
    monto_bs: float
    metodo_pago: MetodoPago
    tipo: TipoTransaccion
    usuario_id: int
    registro_id: Optional[int] = None
    huesped_id: Optional[int] = None
    referencia: str = ""
    concepto: str = ""
    turno_id: Optional[int] = None
    fecha_hora: Optional[datetime] = None
    id: Optional[int] = None
    
    @property
    def requiere_referencia(self) -> bool:
        """Determina si el método de pago requiere referencia"""
        return self.metodo_pago in [
            MetodoPago.PAGO_MOVIL,
            MetodoPago.TRANSFERENCIA,
            MetodoPago.ZELLE,
            MetodoPago.BINANCE
        ]
    
    @property
    def es_efectivo(self) -> bool:
        """Retorna True si es pago en efectivo"""
        return self.metodo_pago in [MetodoPago.EFECTIVO_USD, MetodoPago.EFECTIVO_BS]
    
    def guardar(self) -> int:
        """Guarda la transacción en la base de datos"""
        if not self.fecha_hora:
            self.fecha_hora = datetime.now()
        
        self.id = db.execute('''
            INSERT INTO Transacciones (
                Registro_ID, Huesped_ID, Monto_USD, Tasa_Cambio, Monto_BS,
                Metodo_Pago, Referencia, Tipo, Concepto, Fecha_Hora, Usuario_ID, Turno_ID
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.registro_id, self.huesped_id, self.monto_usd, self.tasa_cambio,
            self.monto_bs, self.metodo_pago.value, self.referencia,
            self.tipo.value, self.concepto, self.fecha_hora, self.usuario_id, self.turno_id
        ))
        
        # Si es un pago, actualizar el registro
        if self.tipo == TipoTransaccion.PAGO and self.registro_id:
            from models.registro import Registro
            registro = Registro.buscar_por_id(self.registro_id)
            if registro:
                registro.registrar_pago(self.monto_usd)
        
        # Si es un ajuste de saldo de huésped
        if self.tipo == TipoTransaccion.AJUSTE and self.huesped_id:
            from models.huesped import Huesped
            huesped = Huesped.buscar_por_id(self.huesped_id)
            if huesped:
                huesped.ajustar_saldo(self.monto_usd)
        
        return self.id
    
    @staticmethod
    def buscar_por_id(transaccion_id: int) -> Optional['Transaccion']:
        """Busca una transacción por su ID"""
        row = db.fetch_one('SELECT * FROM Transacciones WHERE ID = ?', (transaccion_id,))
        return Transaccion._from_row(row) if row else None
    
    @staticmethod
    def listar_por_registro(registro_id: int) -> List['Transaccion']:
        """Lista todas las transacciones de un registro"""
        rows = db.fetch_all('''
            SELECT * FROM Transacciones 
            WHERE Registro_ID = ?
            ORDER BY Fecha_Hora DESC
        ''', (registro_id,))
        return [Transaccion._from_row(row) for row in rows]
    
    @staticmethod
    def listar_por_huesped(huesped_id: int) -> List['Transaccion']:
        """Lista todas las transacciones de un huésped"""
        rows = db.fetch_all('''
            SELECT * FROM Transacciones 
            WHERE Huesped_ID = ?
            ORDER BY Fecha_Hora DESC
        ''', (huesped_id,))
        return [Transaccion._from_row(row) for row in rows]
    
    @staticmethod
    def listar_por_turno(turno_id: int) -> List['Transaccion']:
        """Lista todas las transacciones de un turno"""
        rows = db.fetch_all('''
            SELECT * FROM Transacciones 
            WHERE Turno_ID = ?
            ORDER BY Fecha_Hora DESC
        ''', (turno_id,))
        return [Transaccion._from_row(row) for row in rows]
    
    @staticmethod
    def listar_por_fecha(fecha_desde: datetime, fecha_hasta: datetime) -> List['Transaccion']:
        """Lista transacciones por rango de fechas"""
        rows = db.fetch_all('''
            SELECT * FROM Transacciones 
            WHERE Fecha_Hora BETWEEN ? AND ?
            ORDER BY Fecha_Hora DESC
        ''', (fecha_desde, fecha_hasta))
        return [Transaccion._from_row(row) for row in rows]
    
    @staticmethod
    def resumen_por_metodo(turno_id: int) -> dict:
        """Retorna un resumen de transacciones agrupadas por método de pago"""
        rows = db.fetch_all('''
            SELECT Metodo_Pago, Tipo, SUM(Monto_USD) as Total_USD, SUM(Monto_BS) as Total_BS, COUNT(*) as Cantidad
            FROM Transacciones 
            WHERE Turno_ID = ?
            GROUP BY Metodo_Pago, Tipo
        ''', (turno_id,))
        
        resumen = {}
        for row in rows:
            metodo = row['Metodo_Pago']
            if metodo not in resumen:
                resumen[metodo] = {'pagos': 0, 'cargos': 0, 'total_usd': 0, 'total_bs': 0, 'cantidad': 0}
            
            if row['Tipo'] == 'Pago':
                resumen[metodo]['pagos'] += row['Total_USD']
            else:
                resumen[metodo]['cargos'] += row['Total_USD']
            
            resumen[metodo]['total_usd'] += row['Total_USD']
            resumen[metodo]['total_bs'] += row['Total_BS']
            resumen[metodo]['cantidad'] += row['Cantidad']
        
        return resumen
    
    @staticmethod
    def _from_row(row: dict) -> 'Transaccion':
        """Crea un objeto Transaccion desde una fila de la base de datos"""
        return Transaccion(
            id=row['ID'],
            registro_id=row['Registro_ID'],
            huesped_id=row['Huesped_ID'],
            monto_usd=row['Monto_USD'],
            tasa_cambio=row['Tasa_Cambio'],
            monto_bs=row['Monto_BS'],
            metodo_pago=MetodoPago(row['Metodo_Pago']),
            referencia=row['Referencia'] or "",
            tipo=TipoTransaccion(row['Tipo']),
            concepto=row['Concepto'] or "",
            fecha_hora=row['Fecha_Hora'],
            usuario_id=row['Usuario_ID'],
            turno_id=row['Turno_ID']
        )
