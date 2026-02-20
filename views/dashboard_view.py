"""
Vista del Dashboard Principal con Grid de Habitaciones
"""
import flet as ft
from typing import Callable
from models.habitacion import Habitacion, EstadoHabitacion
from models.configuracion import get_config
from components.room_card import RoomCard
from utils.session import session
from utils.helpers import format_money

class DashboardView(ft.View):
    """Vista principal con el grid de habitaciones"""
    
    def __init__(self, on_room_click: Callable, on_menu_click: Callable):
        super().__init__()
        self.route = "/dashboard"
        self.on_room_click = on_room_click
        self.on_menu_click = on_menu_click
        self.room_cards = {}
        self._build()
    
    def _build(self):
        self.appbar = ft.AppBar(
            title=ft.Text("Dashboard - Habitaciones"),
            center_title=True,
            bgcolor=ft.Colors.BLUE,
            actions=[
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Actualizar",
                    on_click=self._refresh
                ),
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(text="Check-in", on_click=lambda e: self.on_menu_click("checkin")),
                        ft.PopupMenuItem(text="Huéspedes", on_click=lambda e: self.on_menu_click("huespedes")),
                        ft.PopupMenuItem(),
                        ft.PopupMenuItem(text="Turno", on_click=lambda e: self.on_menu_click("turno")),
                        ft.PopupMenuItem(text="Configuración", on_click=lambda e: self.on_menu_click("config")),
                        ft.PopupMenuItem(),
                        ft.PopupMenuItem(text="Cerrar Sesión", on_click=lambda e: self.on_menu_click("logout")),
                    ]
                )
            ]
        )
        
        # Barra de información
        config = get_config()
        self.lbl_tasa = ft.Text(f"Tasa: ${config.tasa_dolar_bs:.2f} Bs/USD", size=12)
        self.lbl_usuario = ft.Text(f"Usuario: {session.usuario.nombre_completo if session.usuario else 'N/A'}", size=12)
        self.lbl_turno = ft.Text("Turno: Abierto" if session.tiene_turno_abierto else "Turno: Cerrado", 
                                  size=12, color=ft.Colors.GREEN if session.tiene_turno_abierto else ft.Colors.RED)
        
        # Leyenda de estados
        leyenda = ft.Row(
            [
                ft.Container(ft.Text("Libre", color=ft.Colors.WHITE, size=10), bgcolor=ft.Colors.GREEN, padding=5, border_radius=3),
                ft.Container(ft.Text("Ocupada", color=ft.Colors.WHITE, size=10), bgcolor=ft.Colors.RED, padding=5, border_radius=3),
                ft.Container(ft.Text("Reservada", color=ft.Colors.BLACK, size=10), bgcolor=ft.Colors.AMBER, padding=5, border_radius=3),
                ft.Container(ft.Text("Aseo", color=ft.Colors.WHITE, size=10), bgcolor=ft.Colors.GREY, padding=5, border_radius=3),
                ft.Container(ft.Text("Mantenimiento", color=ft.Colors.WHITE, size=10), bgcolor=ft.Colors.ORANGE, padding=5, border_radius=3),
            ],
            spacing=10
        )
        
        # Grid de habitaciones
        self.grid_habitaciones = ft.GridView(
            runs_count=6,
            max_extent=120,
            child_aspect_ratio=0.85,
            spacing=10,
            run_spacing=10,
            padding=10
        )
        
        # Contador de habitaciones
        self.lbl_contadores = ft.Text("", size=12, color=ft.Colors.GREY)
        
        # Controles de filtro
        self.filtro_estado = ft.Dropdown(
            label="Filtrar por estado",
            width=150,
            options=[
                ft.dropdown.Option("Todos", "Todos"),
                ft.dropdown.Option("Libre", "Libre"),
                ft.dropdown.Option("Ocupada", "Ocupada"),
                ft.dropdown.Option("Reservada", "Reservada"),
                ft.dropdown.Option("Aseo", "Aseo"),
                ft.dropdown.Option("Mantenimiento", "Mantenimiento"),
            ],
            value="Todos",
            on_change=self._filtrar_habitaciones
        )
        
        # Layout principal
        self.controls = [
            ft.Container(
                content=ft.Column([
                    # Barra superior
                    ft.Row([
                        self.lbl_usuario,
                        ft.VerticalDivider(width=1),
                        self.lbl_tasa,
                        ft.VerticalDivider(width=1),
                        self.lbl_turno,
                    ], spacing=10),
                    ft.Divider(),
                    # Filtros y leyenda
                    ft.Row([
                        self.filtro_estado,
                        ft.Container(content=leyenda, expand=True),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    # Grid
                    ft.Container(
                        content=self.grid_habitaciones,
                        expand=True,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=8,
                        padding=10
                    ),
                    # Contadores
                    self.lbl_contadores
                ]),
                padding=10,
                expand=True
            )
        ]
        
        # Cargar habitaciones
        self._cargar_habitaciones()
    
    def _cargar_habitaciones(self):
        """Carga las habitaciones en el grid"""
        self.grid_habitaciones.controls.clear()
        self.room_cards.clear()
        
        habitaciones = Habitacion.listar_todas()
        filtro = self.filtro_estado.value
        
        contadores = {estado.value: 0 for estado in EstadoHabitacion}
        
        for hab in habitaciones:
            contadores[hab.estado.value] += 1
            
            if filtro != "Todos" and hab.estado.value != filtro:
                continue
            
            card = RoomCard(hab, on_click=self.on_room_click)
            self.grid_habitaciones.controls.append(card)
            self.room_cards[hab.numero] = card
        
        # Actualizar contadores
        total = len(habitaciones)
        ocupadas = contadores[EstadoHabitacion.OCUPADA.value]
        libres = contadores[EstadoHabitacion.LIBRE.value]
        self.lbl_contadores.value = f"Total: {total} | Ocupadas: {ocupadas} | Libres: {libres} | Reservadas: {contadores[EstadoHabitacion.RESERVADA.value]} | Aseo: {contadores[EstadoHabitacion.ASEO.value]} | Mantenimiento: {contadores[EstadoHabitacion.MANTENIMIENTO.value]}"
        
        self.update()
    
    def _filtrar_habitaciones(self, e):
        """Filtra las habitaciones por estado"""
        self._cargar_habitaciones()
    
    def _refresh(self, e):
        """Refresca el dashboard"""
        # Actualizar tasa
        config = get_config()
        self.lbl_tasa.value = f"Tasa: ${config.tasa_dolar_bs:.2f} Bs/USD"
        
        # Actualizar turno
        self.lbl_turno.value = "Turno: Abierto" if session.tiene_turno_abierto else "Turno: Cerrado"
        self.lbl_turno.color = ft.Colors.GREEN if session.tiene_turno_abierto else ft.Colors.RED
        
        self._cargar_habitaciones()
    
    def actualizar_habitacion(self, numero: int):
        """Actualiza una habitación específica"""
        habitacion = Habitacion.buscar_por_numero(numero)
        if habitacion and numero in self.room_cards:
            self.room_cards[numero].update_habitacion(habitacion)
        else:
            self._cargar_habitaciones()
    
    def refresh_all(self):
        """Refresca toda la vista"""
        self._refresh(None)
