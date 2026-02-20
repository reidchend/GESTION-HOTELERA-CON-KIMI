"""
Gestión de sesión de usuario
"""
from typing import Optional
from models.usuario import Usuario

class Session:
    """Clase singleton para gestionar la sesión del usuario actual"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Session, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._usuario: Optional[Usuario] = None
        self._turno_id: Optional[int] = None
    
    @property
    def usuario(self) -> Optional[Usuario]:
        return self._usuario
    
    @property
    def esta_autenticado(self) -> bool:
        return self._usuario is not None
    
    @property
    def usuario_id(self) -> Optional[int]:
        return self._usuario.id if self._usuario else None
    
    @property
    def es_admin(self) -> bool:
        return self._usuario.es_admin if self._usuario else False
    
    @property
    def turno_id(self) -> Optional[int]:
        return self._turno_id
    
    @property
    def tiene_turno_abierto(self) -> bool:
        return self._turno_id is not None
    
    def login(self, usuario: Usuario) -> None:
        """Inicia sesión con un usuario"""
        self._usuario = usuario
    
    def logout(self) -> None:
        """Cierra la sesión"""
        self._usuario = None
        self._turno_id = None
    
    def set_turno(self, turno_id: int) -> None:
        """Establece el turno activo"""
        self._turno_id = turno_id
    
    def clear_turno(self) -> None:
        """Limpia el turno activo"""
        self._turno_id = None

# Instancia global de sesión
session = Session()
