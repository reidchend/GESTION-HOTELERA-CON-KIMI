"""
Vista de Login
"""
import flet as ft
from models.usuario import Usuario
from models.turno import Turno
from utils.session import session
from utils.helpers import format_money

class LoginView(ft.View):
    """Vista de inicio de sesión"""
    
    def __init__(self, on_login_success):
        super().__init__()
        self.route = "/login"
        self.on_login_success = on_login_success
        self._build()
    
    def _build(self):
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.padding = 50
        
        # Campos de entrada
        self.txt_username = ft.TextField(
            label="Usuario",
            prefix_icon=ft.Icons.PERSON,
            width=300,
            on_submit=self._on_login
        )
        
        self.txt_password = ft.TextField(
            label="Contraseña",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            width=300,
            on_submit=self._on_login
        )
        
        # Mensaje de error
        self.lbl_error = ft.Text(
            "",
            color=ft.Colors.RED,
            size=12,
            text_align=ft.TextAlign.CENTER
        )
        
        # Botón de login
        btn_login = ft.ElevatedButton(
            "Iniciar Sesión",
            icon=ft.Icons.LOGIN,
            width=300,
            on_click=self._on_login
        )
        
        # Card de login
        login_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.HOTEL, size=64, color=ft.Colors.BLUE),
                    ft.Text("Sistema de Gestión Hotelera", 
                           size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("Inicie sesión para continuar", 
                           size=14, color=ft.Colors.GREY),
                    ft.Divider(height=20),
                    self.txt_username,
                    self.txt_password,
                    self.lbl_error,
                    btn_login,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=30
            ),
            elevation=5
        )
        
        self.controls = [
            ft.Container(
                content=login_card,
                alignment=ft.alignment.center
            )
        ]
    
    def _on_login(self, e):
        """Maneja el intento de login"""
        username = self.txt_username.value.strip()
        password = self.txt_password.value
        
        if not username or not password:
            self.lbl_error.value = "Ingrese usuario y contraseña"
            self.update()
            return
        
        # Autenticar
        usuario = Usuario.autenticar(username, password)
        
        if usuario:
            session.login(usuario)
            self.lbl_error.value = ""
            
            # Verificar si hay turno abierto
            turno_abierto = Turno.buscar_turno_abierto_global()
            if turno_abierto and turno_abierto.usuario_id != usuario.id:
                # Hay un turno abierto de otro usuario
                self.lbl_error.value = f"Hay un turno abierto de {turno_abierto.usuario_nombre}. Cierre ese turno primero."
                self.update()
                session.logout()
                return
            
            self.on_login_success()
        else:
            self.lbl_error.value = "Usuario o contraseña incorrectos"
            self.txt_password.value = ""
            self.update()
