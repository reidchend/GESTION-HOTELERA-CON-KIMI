"""
Modelo y lógica de negocio para Usuarios y Autenticación
"""
import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum
from database.connection import db

class RolUsuario(str, Enum):
    ADMIN = 'admin'
    RECEPCIONISTA = 'recepcionista'
    GERENTE = 'gerente'

@dataclass
class Usuario:
    username: str
    nombre_completo: str
    rol: RolUsuario
    password_hash: str = ""
    activo: bool = True
    ultimo_acceso: Optional[datetime] = None
    fecha_creacion: Optional[datetime] = None
    id: Optional[int] = None
    
    @property
    def es_admin(self) -> bool:
        return self.rol == RolUsuario.ADMIN
    
    @property
    def es_gerente(self) -> bool:
        return self.rol == RolUsuario.GERENTE
    
    @property
    def puede_cerrar_turno(self) -> bool:
        return self.rol in [RolUsuario.ADMIN, RolUsuario.GERENTE]
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Genera el hash SHA-256 de una contraseña"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verificar_password(self, password: str) -> bool:
        """Verifica si la contraseña coincide"""
        return self.password_hash == self.hash_password(password)
    
    def cambiar_password(self, nueva_password: str) -> None:
        """Cambia la contraseña del usuario"""
        self.password_hash = self.hash_password(nueva_password)
        db.execute(
            'UPDATE Usuarios SET Password_Hash = ? WHERE ID = ?',
            (self.password_hash, self.id)
        )
    
    def guardar(self) -> int:
        """Guarda o actualiza el usuario"""
        if self.id:
            db.execute('''
                UPDATE Usuarios SET
                    Username = ?,
                    Nombre_Completo = ?,
                    Rol = ?,
                    Activo = ?
                WHERE ID = ?
            ''', (self.username, self.nombre_completo, self.rol.value, 
                  1 if self.activo else 0, self.id))
            return self.id
        else:
            self.id = db.execute('''
                INSERT INTO Usuarios (Username, Password_Hash, Nombre_Completo, Rol, Activo, Fecha_Creacion)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.username, self.password_hash, self.nombre_completo, 
                  self.rol.value, 1 if self.activo else 0, datetime.now()))
            return self.id
    
    def registrar_acceso(self) -> None:
        """Registra el último acceso del usuario"""
        self.ultimo_acceso = datetime.now()
        db.execute(
            'UPDATE Usuarios SET Ultimo_Acceso = ? WHERE ID = ?',
            (self.ultimo_acceso, self.id)
        )
    
    def desactivar(self) -> None:
        """Desactiva el usuario"""
        self.activo = False
        db.execute('UPDATE Usuarios SET Activo = 0 WHERE ID = ?', (self.id,))
    
    @staticmethod
    def autenticar(username: str, password: str) -> Optional['Usuario']:
        """Autentica un usuario y retorna el objeto si es válido"""
        usuario = Usuario.buscar_por_username(username)
        if usuario and usuario.activo and usuario.verificar_password(password):
            usuario.registrar_acceso()
            return usuario
        return None
    
    @staticmethod
    def buscar_por_id(usuario_id: int) -> Optional['Usuario']:
        """Busca un usuario por su ID"""
        row = db.fetch_one('SELECT * FROM Usuarios WHERE ID = ?', (usuario_id,))
        return Usuario._from_row(row) if row else None
    
    @staticmethod
    def buscar_por_username(username: str) -> Optional['Usuario']:
        """Busca un usuario por su nombre de usuario"""
        row = db.fetch_one('SELECT * FROM Usuarios WHERE Username = ?', (username,))
        return Usuario._from_row(row) if row else None
    
    @staticmethod
    def listar_todos() -> List['Usuario']:
        """Lista todos los usuarios"""
        rows = db.fetch_all('SELECT * FROM Usuarios ORDER BY Nombre_Completo')
        return [Usuario._from_row(row) for row in rows]
    
    @staticmethod
    def listar_activos() -> List['Usuario']:
        """Lista usuarios activos"""
        rows = db.fetch_all('SELECT * FROM Usuarios WHERE Activo = 1 ORDER BY Nombre_Completo')
        return [Usuario._from_row(row) for row in rows]
    
    @staticmethod
    def _from_row(row: dict) -> 'Usuario':
        """Crea un objeto Usuario desde una fila de la base de datos"""
        return Usuario(
            id=row['ID'],
            username=row['Username'],
            password_hash=row['Password_Hash'],
            nombre_completo=row['Nombre_Completo'],
            rol=RolUsuario(row['Rol']),
            activo=bool(row['Activo']),
            ultimo_acceso=row['Ultimo_Acceso'],
            fecha_creacion=row['Fecha_Creacion']
        )
