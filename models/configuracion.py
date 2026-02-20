"""
Modelo y lógica de negocio para Configuración del Sistema
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from database.connection import db

@dataclass
class Configuracion:
    tasa_dolar_bs: float = 35.50
    nombre_hotel: str = "Hotel Ejemplo"
    direccion: str = ""
    telefono: str = ""
    email: str = ""
    rif: str = ""
    fecha_actualizacion: Optional[datetime] = None
    id: int = 1
    
    @staticmethod
    def obtener() -> 'Configuracion':
        """Obtiene la configuración actual del sistema"""
        row = db.fetch_one('SELECT * FROM Configuracion WHERE ID = 1')
        if row:
            return Configuracion._from_row(row)
        # Si no existe, crear configuración por defecto
        config = Configuracion()
        config.guardar()
        return config
    
    def guardar(self) -> None:
        """Guarda la configuración"""
        self.fecha_actualizacion = datetime.now()
        db.execute('''
            INSERT OR REPLACE INTO Configuracion 
            (ID, Tasa_Dolar_BS, Nombre_Hotel, Direccion, Telefono, Email, RIF, Fecha_Actualizacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.id, self.tasa_dolar_bs, self.nombre_hotel, self.direccion,
            self.telefono, self.email, self.rif, self.fecha_actualizacion
        ))
    
    def actualizar_tasa(self, nueva_tasa: float) -> None:
        """Actualiza la tasa de cambio"""
        self.tasa_dolar_bs = nueva_tasa
        self.guardar()
    
    def convertir_usd_a_bs(self, monto_usd: float) -> float:
        """Convierte un monto de USD a BS según la tasa actual"""
        return monto_usd * self.tasa_dolar_bs
    
    def convertir_bs_a_usd(self, monto_bs: float) -> float:
        """Convierte un monto de BS a USD según la tasa actual"""
        if self.tasa_dolar_bs == 0:
            return 0.0
        return monto_bs / self.tasa_dolar_bs
    
    @staticmethod
    def _from_row(row: dict) -> 'Configuracion':
        """Crea un objeto Configuracion desde una fila de la base de datos"""
        return Configuracion(
            id=row['ID'],
            tasa_dolar_bs=row['Tasa_Dolar_BS'],
            nombre_hotel=row['Nombre_Hotel'],
            direccion=row['Direccion'] or "",
            telefono=row['Telefono'] or "",
            email=row['Email'] or "",
            rif=row['RIF'] or "",
            fecha_actualizacion=row['Fecha_Actualizacion']
        )

# Instancia global de configuración (lazy loading)
_config: Optional[Configuracion] = None

def get_config() -> Configuracion:
    """Obtiene la instancia global de configuración"""
    global _config
    if _config is None:
        _config = Configuracion.obtener()
    return _config

def refresh_config() -> Configuracion:
    """Refresca y retorna la configuración actual"""
    global _config
    _config = Configuracion.obtener()
    return _config
