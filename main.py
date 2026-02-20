"""
Sistema de Gestión Hotelera (SGH)
=================================
Aplicación de escritorio desarrollada con Python y Flet v0.80.5

Características principales:
- Gestión de 39 habitaciones con estados visuales
- Check-in/Check-out con pre-facturación
- Sistema de pagos multimoneda (USD/BS)
- Gestión de saldos a favor y deudas
- Control de turnos (apertura/cierre de caja)
- Gestión de huéspedes y usuarios

Autor: Sistema Automatizado
Versión: 1.0.0
"""

import flet as ft
import os
import sys

# Asegurar que el directorio del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar vistas
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.checkin_view import CheckinView
from views.checkout_view import CheckoutView
from views.huespedes_view import HuespedesView
from views.turno_view import TurnoView
from views.config_view import ConfigView

# Importar modelos y utilidades
from models.habitacion import Habitacion, EstadoHabitacion
from models.registro import Registro
from models.turno import Turno
from utils.session import session

class HotelApp:
    """Clase principal de la aplicación del hotel"""
    
    def __init__(self):
        self.page: ft.Page = None
        self.current_view = None
    
    def main(self, page: ft.Page):
        """Punto de entrada principal de la aplicación"""
        self.page = page
        
        # Configuración de la página
        page.title = "Sistema de Gestión Hotelera"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window_width = 1200
        page.window_height = 800
        page.window_min_width = 800
        page.window_min_height = 600
        page.padding = 0
        page.spacing = 0
        
        # Tema personalizado
        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=ft.Colors.BLUE,
                primary_container=ft.Colors.BLUE_100,
                secondary=ft.Colors.ORANGE,
                surface=ft.Colors.WHITE,
                background=ft.Colors.GREY_50,
                error=ft.Colors.RED,
            )
        )
        
        # Verificar autenticación inicial
        self._check_auth()
    
    def _check_auth(self):
        """Verifica si hay una sesión activa"""
        if session.esta_autenticado:
            self._show_dashboard()
        else:
            self._show_login()
    
    def _show_login(self):
        """Muestra la vista de login"""
        login_view = LoginView(on_login_success=self._on_login_success)
        self.page.views.clear()
        self.page.views.append(login_view)
        self.page.update()
    
    def _on_login_success(self):
        """Maneja el éxito del login"""
        # Verificar si el usuario tiene turno abierto
        turno_abierto = Turno.buscar_turno_abierto(session.usuario_id)
        if turno_abierto:
            session.set_turno(turno_abierto.id)
        
        self._show_dashboard()
    
    def _show_dashboard(self):
        """Muestra el dashboard principal"""
        dashboard = DashboardView(
            on_room_click=self._on_room_click,
            on_menu_click=self._on_menu_click
        )
        self._navigate_to(dashboard)
    
    def _on_room_click(self, habitacion: Habitacion):
        """Maneja el clic en una habitación"""
        if habitacion.estado == EstadoHabitacion.LIBRE:
            # Verificar turno abierto
            if not session.tiene_turno_abierto:
                self._show_turno_required()
                return
            # Ir a check-in
            self._show_checkin(habitacion.numero)
        
        elif habitacion.estado == EstadoHabitacion.OCUPADA:
            # Verificar turno abierto
            if not session.tiene_turno_abierto:
                self._show_turno_required()
                return
            # Buscar registro activo y hacer checkout
            registro = Registro.buscar_activo_por_habitacion(habitacion.numero)
            if registro:
                self._show_checkout(registro.id)
        
        elif habitacion.estado == EstadoHabitacion.ASEO:
            # Opción para marcar como libre
            self._show_limpieza_dialog(habitacion)
        
        elif habitacion.estado == EstadoHabitacion.MANTENIMIENTO:
            # Opción para marcar como libre
            self._show_mantenimiento_dialog(habitacion)
        
        elif habitacion.estado == EstadoHabitacion.RESERVADA:
            # Mostrar info de reserva o convertir a ocupada
            self._show_reserva_dialog(habitacion)
    
    def _show_limpieza_dialog(self, habitacion: Habitacion):
        """Muestra diálogo para habitación en aseo"""
        def marcar_lista(e):
            habitacion.cambiar_estado(EstadoHabitacion.LIBRE)
            dialog.open = False
            self._show_dashboard()
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Habitación {habitacion.numero:03d} - En Aseo"),
            content=ft.Text("¿Marcar habitación como lista?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Marcar como Lista", on_click=marcar_lista)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_mantenimiento_dialog(self, habitacion: Habitacion):
        """Muestra diálogo para habitación en mantenimiento"""
        def marcar_reparada(e):
            habitacion.cambiar_estado(EstadoHabitacion.LIBRE)
            dialog.open = False
            self._show_dashboard()
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Habitación {habitacion.numero:03d} - En Mantenimiento"),
            content=ft.Text("¿Marcar habitación como reparada y lista?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Marcar como Reparada", on_click=marcar_reparada)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_reserva_dialog(self, habitacion: Habitacion):
        """Muestra diálogo para habitación reservada"""
        def convertir_ocupada(e):
            habitacion.cambiar_estado(EstadoHabitacion.LIBRE)
            dialog.open = False
            self._show_checkin(habitacion.numero)
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Habitación {habitacion.numero:03d} - Reservada"),
            content=ft.Text("¿Convertir reserva a ocupada?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Convertir a Ocupada", on_click=convertir_ocupada)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_turno_required(self):
        """Muestra mensaje de que se requiere turno abierto"""
        def ir_a_turno(e):
            dialog.open = False
            self._show_turno()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Turno Cerrado"),
            content=ft.Text("Debe abrir un turno para realizar esta operación."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Abrir Turno", on_click=ir_a_turno)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _on_menu_click(self, option: str):
        """Maneja las opciones del menú"""
        if option == "checkin":
            self._show_checkin()
        elif option == "huespedes":
            self._show_huespedes()
        elif option == "turno":
            self._show_turno()
        elif option == "config":
            self._show_config()
        elif option == "logout":
            self._logout()
    
    def _show_checkin(self, habitacion_numero: int = None):
        """Muestra la vista de check-in"""
        checkin = CheckinView(
            on_complete=self._show_dashboard,
            on_cancel=self._show_dashboard,
            habitacion_numero=habitacion_numero
        )
        self._navigate_to(checkin)
    
    def _show_checkout(self, registro_id: int):
        """Muestra la vista de check-out"""
        checkout = CheckoutView(
            on_complete=self._show_dashboard,
            on_cancel=self._show_dashboard,
            registro_id=registro_id
        )
        self._navigate_to(checkout)
    
    def _show_huespedes(self):
        """Muestra la vista de gestión de huéspedes"""
        huespedes = HuespedesView(
            on_back=self._show_dashboard
        )
        self._navigate_to(huespedes)
    
    def _show_turno(self):
        """Muestra la vista de gestión de turnos"""
        turno = TurnoView(on_complete=self._show_dashboard)
        self._navigate_to(turno)
    
    def _show_config(self):
        """Muestra la vista de configuración"""
        config = ConfigView(on_back=self._show_dashboard)
        self._navigate_to(config)
    
    def _logout(self):
        """Cierra la sesión del usuario"""
        # Verificar si tiene turno abierto
        if session.tiene_turno_abierto:
            def confirmar(e):
                dialog.open = False
                session.logout()
                self._show_login()
            
            dialog = ft.AlertDialog(
                title=ft.Text("Turno Abierto"),
                content=ft.Text("Tiene un turno abierto. ¿Desea cerrar sesión de todos modos?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                    ft.ElevatedButton("Cerrar Sesión", on_click=confirmar, bgcolor=ft.Colors.RED)
                ]
            )
            
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
        else:
            session.logout()
            self._show_login()
    
    def _navigate_to(self, view):
        """Navega a una nueva vista"""
        self.page.views.clear()
        self.page.views.append(view)
        self.page.update()


def main():
    """Función principal de entrada"""
    app = HotelApp()
    ft.app(target=app.main)


if __name__ == "__main__":
    main()
